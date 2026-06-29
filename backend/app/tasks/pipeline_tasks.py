"""
Celery tasks for pipeline execution.
Uses a synchronous SQLAlchemy session (Celery workers are sync).
"""
import uuid
from datetime import datetime, timezone

from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.job import JobRun
from app.services.execution_engine import run_pipeline

# Sync engine for Celery workers
sync_engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine)


def get_sync_db() -> Session:
    return SyncSession()


@celery_app.task(
    bind=True,
    name="app.tasks.pipeline_tasks.run_pipeline_task",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    queue="etl",
)
def run_pipeline_task(self: Task, pipeline_id: str, job_run_id: str, run_type: str = "MANUAL"):
    """
    Main Celery task to execute an ETL pipeline.
    Called by the API when user clicks "Run Now".
    """
    db = get_sync_db()
    try:
        # Update celery task ID on the job run
        job_run = db.get(JobRun, job_run_id)
        if job_run:
            job_run.celery_task_id = self.request.id
            db.commit()

        run_pipeline(db, pipeline_id, job_run_id, run_type=run_type)

    except Exception as exc:
        db.rollback()
        try:
            self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            # Max retries — mark as failed
            db2 = get_sync_db()
            try:
                jr = db2.get(JobRun, job_run_id)
                if jr and jr.status not in ("SUCCESS", "FAILED"):
                    jr.status = "FAILED"
                    jr.error_message = f"Max retry aşıldı: {str(exc)}"
                    jr.finished_at = datetime.now(timezone.utc)
                    db2.commit()
            finally:
                db2.close()
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.pipeline_tasks.test_run_pipeline_task",
    queue="etl",
)
def test_run_pipeline_task(self: Task, pipeline_id: str, job_run_id: str, test_limit: int = 100):
    """Test run — only reads up to test_limit rows, does NOT write to target."""
    db = get_sync_db()
    try:
        job_run = db.get(JobRun, job_run_id)
        if job_run:
            job_run.celery_task_id = self.request.id
            db.commit()
        run_pipeline(db, pipeline_id, job_run_id, run_type="TEST", test_limit=test_limit)
    finally:
        db.close()
