from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.models.job import JobRun
from app.models.pipeline import Pipeline
from app.models.user import User
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Total pipelines
    total_pipelines = (await db.execute(select(func.count(Pipeline.id)))).scalar()
    active_pipelines = (await db.execute(select(func.count(Pipeline.id)).where(Pipeline.status == "ACTIVE"))).scalar()

    # Today's job stats
    today_jobs = select(JobRun).where(JobRun.created_at >= today_start)
    today_success = (await db.execute(select(func.count(JobRun.id)).where(
        JobRun.created_at >= today_start, JobRun.status == "SUCCESS"
    ))).scalar()
    today_failed = (await db.execute(select(func.count(JobRun.id)).where(
        JobRun.created_at >= today_start, JobRun.status == "FAILED"
    ))).scalar()

    # Total rows transferred today
    total_rows_result = await db.execute(
        select(func.sum(JobRun.success_count)).where(
            JobRun.created_at >= today_start, JobRun.status == "SUCCESS"
        )
    )
    total_rows = total_rows_result.scalar() or 0

    # Average duration
    avg_duration_result = await db.execute(
        select(func.avg(JobRun.duration_seconds)).where(JobRun.status == "SUCCESS")
    )
    avg_duration = avg_duration_result.scalar() or 0

    return {
        "total_pipelines": total_pipelines,
        "active_pipelines": active_pipelines,
        "today_success_jobs": today_success,
        "today_failed_jobs": today_failed,
        "today_rows_transferred": total_rows,
        "avg_duration_seconds": round(avg_duration, 1),
    }


@router.get("/recent-jobs")
async def get_recent_jobs(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(JobRun)
        .options(selectinload(JobRun.pipeline))
        .order_by(desc(JobRun.created_at))
        .limit(limit)
    )
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "pipeline_name": j.pipeline.name if j.pipeline else "—",
            "status": j.status,
            "run_type": j.run_type,
            "started_at": j.started_at,
            "finished_at": j.finished_at,
            "duration_seconds": j.duration_seconds,
            "source_count": j.source_count,
            "success_count": j.success_count,
            "error_count": j.error_count,
        }
        for j in jobs
    ]
