from typing import Optional, Any
from pydantic import BaseModel, field_validator
from datetime import datetime


CONNECTION_TYPES = ["POSTGRESQL", "MYSQL", "MSSQL", "CSV", "EXCEL", "SFTP"]


class ConnectionCreate(BaseModel):
    name: str
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Plaintext — encrypted before storage
    extra_config: dict[str, Any] = {}

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v.upper() not in CONNECTION_TYPES:
            raise ValueError(f"Unsupported connection type. Choose from: {CONNECTION_TYPES}")
        return v.upper()


class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    extra_config: Optional[dict[str, Any]] = None


class ConnectionOut(BaseModel):
    id: str
    name: str
    type: str
    host: Optional[str]
    port: Optional[int]
    database_name: Optional[str]
    username: Optional[str]
    extra_config: dict
    is_active: bool
    last_tested_at: Optional[datetime]
    last_test_status: Optional[str]
    last_test_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConnectionTestResult(BaseModel):
    success: bool
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    server_version: Optional[str] = None
