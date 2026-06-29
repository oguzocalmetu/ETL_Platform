import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Connection(Base):
    __tablename__ = "etl_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)       # POSTGRESQL, MYSQL, MSSQL, CSV, EXCEL, SFTP
    host = Column(String(255))
    port = Column(Integer)
    database_name = Column(String(255))
    username = Column(String(255))
    encrypted_password = Column(Text)               # Fernet encrypted
    extra_config = Column(JSONB, default=dict)      # ssl, charset, schema path, etc.
    is_active = Column(Boolean, default=True, nullable=False)

    # Test results
    last_tested_at = Column(DateTime(timezone=True))
    last_test_status = Column(String(20))           # SUCCESS, FAILED
    last_test_error = Column(Text)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    creator = relationship("User", foreign_keys=[created_by])
    # Pipelines that use this connection as source or target
    source_pipelines = relationship("Pipeline", foreign_keys="Pipeline.source_connection_id", back_populates="source_connection")
    target_pipelines = relationship("Pipeline", foreign_keys="Pipeline.target_connection_id", back_populates="target_connection")
