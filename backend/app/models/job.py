import uuid
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class JobRun(Base):
    __tablename__ = "etl_job_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("etl_pipelines.id"), nullable=False)
    celery_task_id = Column(String(255))
    status = Column(String(20), nullable=False, default="PENDING")
    # PENDING, RUNNING, SUCCESS, FAILED, CANCELLED
    run_type = Column(String(20), nullable=False)  # MANUAL, SCHEDULED, TEST
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)
    source_count = Column(BigInteger)
    target_count = Column(BigInteger)
    success_count = Column(BigInteger)
    error_count = Column(BigInteger)
    rejected_count = Column(BigInteger)
    error_message = Column(Text)      # User-friendly error
    error_detail = Column(Text)       # Technical stack trace (internal only)
    executed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pipeline = relationship("Pipeline", back_populates="job_runs")
    executor = relationship("User", foreign_keys=[executed_by])
    logs = relationship("JobRunLog", back_populates="job_run", cascade="all, delete-orphan", order_by="JobRunLog.created_at")
    rejected_records = relationship("RejectedRecord", back_populates="job_run", cascade="all, delete-orphan")


class JobRunLog(Base):
    __tablename__ = "etl_job_run_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_run_id = Column(UUID(as_uuid=True), ForeignKey("etl_job_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(String(10), nullable=False)   # INFO, WARN, ERROR
    stage = Column(String(50))                   # SOURCE_READ, TRANSFORM, VALIDATE, etc.
    message = Column(Text, nullable=False)
    detail = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job_run = relationship("JobRun", back_populates="logs")


class RejectedRecord(Base):
    __tablename__ = "etl_rejected_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_run_id = Column(UUID(as_uuid=True), ForeignKey("etl_job_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("etl_pipelines.id"), nullable=False, index=True)
    row_number = Column(BigInteger)
    source_data = Column(JSONB, nullable=False)
    error_column = Column(String(255))
    error_rule = Column(String(50))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job_run = relationship("JobRun", back_populates="rejected_records")
