import uuid
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    String, Text, Float, BigInteger, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Pipeline(Base):
    __tablename__ = "etl_pipelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    source_connection_id = Column(UUID(as_uuid=True), ForeignKey("etl_connections.id"))
    target_connection_id = Column(UUID(as_uuid=True), ForeignKey("etl_connections.id"))
    source_config = Column(JSONB, default=dict)    # {table, query, checkpoint_col}
    target_config = Column(JSONB, default=dict)    # {table, create_if_not_exists}
    load_strategy = Column(String(50), nullable=False, default="FULL_LOAD")
    upsert_keys = Column(ARRAY(String))
    status = Column(String(20), default="DRAFT", nullable=False)  # DRAFT, ACTIVE, DISABLED
    schema_drift_action = Column(String(20), default="WARN")       # WARN, STOP, IGNORE
    batch_size = Column(Integer, default=10000)
    retry_count = Column(Integer, default=0)
    retry_delay_seconds = Column(Integer, default=60)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    source_connection = relationship("Connection", foreign_keys=[source_connection_id], back_populates="source_pipelines")
    target_connection = relationship("Connection", foreign_keys=[target_connection_id], back_populates="target_pipelines")
    creator = relationship("User", foreign_keys=[created_by])
    column_mappings = relationship("ColumnMapping", back_populates="pipeline", cascade="all, delete-orphan", order_by="ColumnMapping.ordinal_position")
    validation_rules = relationship("ValidationRule", back_populates="pipeline", cascade="all, delete-orphan")
    job_runs = relationship("JobRun", back_populates="pipeline", order_by="desc(JobRun.created_at)")
    schedule = relationship("Schedule", back_populates="pipeline", uselist=False, cascade="all, delete-orphan")
    checkpoint = relationship("Checkpoint", back_populates="pipeline", uselist=False, cascade="all, delete-orphan")


class ColumnMapping(Base):
    __tablename__ = "etl_column_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("etl_pipelines.id", ondelete="CASCADE"), nullable=False)
    source_column = Column(String(255))
    target_column = Column(String(255), nullable=False)
    source_type = Column(String(50))
    target_type = Column(String(50))
    is_constant = Column(Boolean, default=False)
    constant_value = Column(Text)
    default_value = Column(Text)
    is_nullable = Column(Boolean, default=True)
    is_excluded = Column(Boolean, default=False)
    ordinal_position = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pipeline = relationship("Pipeline", back_populates="column_mappings")
    transform_rules = relationship("TransformRule", back_populates="mapping", cascade="all, delete-orphan", order_by="TransformRule.apply_order")


class TransformRule(Base):
    __tablename__ = "etl_transform_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mapping_id = Column(UUID(as_uuid=True), ForeignKey("etl_column_mappings.id", ondelete="CASCADE"), nullable=False)
    transform_type = Column(String(50), nullable=False)  # TRIM, UPPER, LOWER, CAST, TO_DATE, etc.
    params = Column(JSONB, default=dict)
    apply_order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    mapping = relationship("ColumnMapping", back_populates="transform_rules")


class ValidationRule(Base):
    __tablename__ = "etl_validation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("etl_pipelines.id", ondelete="CASCADE"), nullable=False)
    mapping_id = Column(UUID(as_uuid=True), ForeignKey("etl_column_mappings.id", ondelete="CASCADE"))
    rule_type = Column(String(50), nullable=False)  # NOT_NULL, UNIQUE, REGEX, RANGE, DATE_FORMAT
    params = Column(JSONB, default=dict)
    action_on_fail = Column(String(20), default="REJECT")  # REJECT, WARN, STOP
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pipeline = relationship("Pipeline", back_populates="validation_rules")
    mapping = relationship("ColumnMapping")


class Schedule(Base):
    __tablename__ = "etl_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("etl_pipelines.id", ondelete="CASCADE"), nullable=False, unique=True)
    cron_expr = Column(String(100))
    interval_secs = Column(Integer)
    is_active = Column(Boolean, default=True)
    next_run_at = Column(DateTime(timezone=True))
    last_run_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    pipeline = relationship("Pipeline", back_populates="schedule")


class Checkpoint(Base):
    __tablename__ = "etl_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("etl_pipelines.id", ondelete="CASCADE"), nullable=False, unique=True)
    checkpoint_column = Column(String(255), nullable=False)
    checkpoint_value = Column(Text)
    checkpoint_type = Column(String(20))  # TIMESTAMP, INTEGER, STRING
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    pipeline = relationship("Pipeline", back_populates="checkpoint")
