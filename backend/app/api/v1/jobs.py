from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.job import JobRun, JobRunLog, RejectedRecord
from app.models.pipeline import Pipeline
from app.models.user import User
from app.schemas.job import JobRunRequest, JobRunOut, JobRunLogOut, JobStatusOut, RejectedRecordOut
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/run", response_model=JobRunOut, status_code=status.HTTP_202_ACCEPTED)
async def run_job(
    body: JobRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a pipeline run. Returns immediately with job_run_id. Execution is async via Celery."""
    from app.tasks.pipeline_tasks import run_pipeline_task, test_run_pipeline_task

    pipeline = await db.get(Pipeline, body.pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline bulunamadı")
    if pipeline.status != "ACTIVE" and body.run_type != "TEST":
        raise HTTPException(status_code=400, detail="Pipeline aktif değil. Önce publish edin.")

    job_run = JobRun(
        pipeline_id=body.pipeline_id,
        status="PENDING",
        run_type=body.run_type or "MANUAL",
        executed_by=current_user.id,
    )
    db.add(job_run)
    await db.commit()
    await db.refresh(job_run)

    # Dispatch to Celery
    if body.run_type == "TEST":
        test_run_pipeline_task.delay(str(pipeline.id), str(job_run.id), body.test_limit or 100)
    else:
        run_pipeline_task.delay(str(pipeline.id), str(job_run.id), "MANUAL")

    return job_run


@router.get("", response_model=List[JobRunOut])
async def list_jobs(
    pipeline_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(JobRun).order_by(desc(JobRun.created_at)).limit(limit).offset(offset)
    if pipeline_id:
        query = query.where(JobRun.pipeline_id == pipeline_id)
    if status:
        query = query.where(JobRun.status == status.upper())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobRunOut)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await db.get(JobRun, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job bulunamadı")
    return job


@router.get("/{job_id}/status", response_model=JobStatusOut)
async def get_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lightweight poll endpoint — frontend polls this every 2s during execution."""
    job = await db.get(JobRun, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job bulunamadı")
    return JobStatusOut(
        job_run_id=str(job.id),
        status=job.status,
        source_count=job.source_count,
        success_count=job.success_count,
    )


@router.get("/{job_id}/logs", response_model=List[JobRunLogOut])
async def get_job_logs(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(JobRunLog)
        .where(JobRunLog.job_run_id == job_id)
        .order_by(JobRunLog.created_at)
    )
    return result.scalars().all()


@router.get("/{job_id}/rejected", response_model=List[RejectedRecordOut])
async def get_rejected_records(
    job_id: UUID,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RejectedRecord)
        .where(RejectedRecord.job_run_id == job_id)
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/{job_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.core.celery_app import celery_app

    job = await db.get(JobRun, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job bulunamadı")
    if job.status not in ("PENDING", "RUNNING"):
        raise HTTPException(status_code=400, detail=f"Job iptal edilemez — mevcut durum: {job.status}")

    if job.celery_task_id:
        celery_app.control.revoke(job.celery_task_id, terminate=True)

    job.status = "CANCELLED"
    await db.commit()
    return {"message": "Job iptal edildi"}
