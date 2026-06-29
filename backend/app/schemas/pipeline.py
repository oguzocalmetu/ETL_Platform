from typing import Optional, Any
from pydantic import BaseModel
from datetime import datetime


LOAD_STRATEGIES = ["APPEND", "FULL_LOAD", "TRUNCATE_INSERT", "UPSERT", "INCREMENTAL", "OVERWRITE"]
TRANSFORM_TYPES = ["TRIM", "UPPER", "LOWER", "REPLACE", "CAST", "TO_DATE", "TO_TIMESTAMP",
                   "CONCAT", "SUBSTRING", "COALESCE", "DEFAULT_VALUE", "CASE_WHEN", "NULL_HANDLING"]
VALIDATION_RULES = ["NOT_NULL", "UNIQUE", "REGEX", "RANGE", "DATE_FORMAT", "DUPLICATE_CHECK"]


class TransformRuleSchema(BaseModel):
    id: Optional[str] = None
    transform_type: str
    params: dict[str, Any] = {}
    apply_order: int


class ColumnMappingSchema(BaseModel):
    id: Optional[str] = None
    source_column: Optional[str] = None
    target_column: str
    source_type: Optional[str] = None
    target_type: Optional[str] = None
    is_constant: bool = False
    constant_value: Optional[str] = None
    default_value: Optional[str] = None
    is_nullable: bool = True
    is_excluded: bool = False
    ordinal_position: int
    transform_rules: list[TransformRuleSchema] = []


class ValidationRuleSchema(BaseModel):
    id: Optional[str] = None
    mapping_id: Optional[str] = None
    rule_type: str
    params: dict[str, Any] = {}
    action_on_fail: str = "REJECT"


class ScheduleSchema(BaseModel):
    cron_expr: Optional[str] = None
    interval_secs: Optional[int] = None
    is_active: bool = True


class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source_connection_id: str
    target_connection_id: str
    source_config: dict[str, Any] = {}
    target_config: dict[str, Any] = {}
    load_strategy: str = "FULL_LOAD"
    upsert_keys: list[str] = []
    batch_size: int = 10000
    retry_count: int = 0
    retry_delay_seconds: int = 60
    schema_drift_action: str = "WARN"


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    source_connection_id: Optional[str] = None
    target_connection_id: Optional[str] = None
    source_config: Optional[dict[str, Any]] = None
    target_config: Optional[dict[str, Any]] = None
    load_strategy: Optional[str] = None
    upsert_keys: Optional[list[str]] = None
    batch_size: Optional[int] = None
    schema_drift_action: Optional[str] = None


class PipelineOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    source_connection_id: Optional[str]
    target_connection_id: Optional[str]
    source_config: dict
    target_config: dict
    load_strategy: str
    upsert_keys: Optional[list[str]]
    status: str
    batch_size: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineDetail(PipelineOut):
    column_mappings: list[ColumnMappingSchema] = []
    validation_rules: list[ValidationRuleSchema] = []
    schedule: Optional[ScheduleSchema] = None

    model_config = {"from_attributes": True}
