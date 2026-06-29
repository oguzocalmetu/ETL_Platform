from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class JobRunRequest(BaseModel):
    pipeline_id: str
    run_type: str = "MANUAL"   # MANUAL, TEST
    test_limit: Optional[int] = None  # Only for TEST run_type


class JobRunOut(BaseModel):
    id: str
    pipeline_id: str
    celery_task_id: Optional[str]
    status: str
    run_type: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_seconds: Optional[float]
    source_count: Optional[int]
    target_count: Optional[int]
    success_count: Optional[int]
    error_count: Optional[int]
    rejected_count: Optional[int]
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class JobRunLogOut(BaseModel):
    id: int
    level: str
    stage: Optional[str]
    message: str
    detail: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class JobStatusOut(BaseModel):
    job_run_id: str
    status: str
    progress_pct: Optional[float] = None
    current_stage: Optional[str] = None
    source_count: Optional[int] = None
    success_count: Optional[int] = None


class RejectedRecordOut(BaseModel):
    id: int
    row_number: Optional[int]
    source_data: dict
    error_column: Optional[str]
    error_rule: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
