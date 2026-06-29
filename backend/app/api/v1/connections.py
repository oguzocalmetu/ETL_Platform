from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import encrypt_value
from app.models.connection import Connection
from app.models.user import User
from app.schemas.connection import ConnectionCreate, ConnectionUpdate, ConnectionOut, ConnectionTestResult
from app.api.v1.deps import get_current_user
from app.connectors.factory import create_connector

router = APIRouter(prefix="/connections", tags=["Connections"])


@router.get("", response_model=List[ConnectionOut])
async def list_connections(
    type: Optional[str] = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Connection).where(Connection.is_active == is_active)
    if type:
        query = query.where(Connection.type == type.upper())
    query = query.order_by(Connection.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ConnectionOut, status_code=status.HTTP_201_CREATED)
async def create_connection(
    body: ConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    encrypted_pw = None
    if body.password:
        encrypted_pw = encrypt_value(body.password)

    conn = Connection(
        name=body.name,
        type=body.type.upper(),
        host=body.host,
        port=body.port,
        database_name=body.database_name,
        username=body.username,
        encrypted_password=encrypted_pw,
        extra_config=body.extra_config,
        created_by=current_user.id,
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return conn


@router.get("/{conn_id}", response_model=ConnectionOut)
async def get_connection(
    conn_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = await db.get(Connection, conn_id)
    if not conn or not conn.is_active:
        raise HTTPException(status_code=404, detail="Bağlantı bulunamadı")
    return conn


@router.put("/{conn_id}", response_model=ConnectionOut)
async def update_connection(
    conn_id: UUID,
    body: ConnectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = await db.get(Connection, conn_id)
    if not conn or not conn.is_active:
        raise HTTPException(status_code=404, detail="Bağlantı bulunamadı")

    if body.name is not None:
        conn.name = body.name
    if body.host is not None:
        conn.host = body.host
    if body.port is not None:
        conn.port = body.port
    if body.database_name is not None:
        conn.database_name = body.database_name
    if body.username is not None:
        conn.username = body.username
    if body.password is not None:
        conn.encrypted_password = encrypt_value(body.password)
    if body.extra_config is not None:
        conn.extra_config = body.extra_config

    await db.commit()
    await db.refresh(conn)
    return conn


@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    conn_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = await db.get(Connection, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Bağlantı bulunamadı")
    conn.is_active = False  # Soft delete
    await db.commit()


@router.post("/{conn_id}/test", response_model=ConnectionTestResult)
async def test_connection(
    conn_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.core.security import decrypt_value

    conn = await db.get(Connection, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Bağlantı bulunamadı")

    # Build config with decrypted password
    password = None
    if conn.encrypted_password:
        try:
            password = decrypt_value(conn.encrypted_password)
        except Exception:
            password = conn.encrypted_password

    config = {
        "host": conn.host,
        "port": conn.port,
        "database_name": conn.database_name,
        "username": conn.username,
        "password": password,
        "extra_config": conn.extra_config or {},
    }

    try:
        connector = create_connector(conn.type, config)
        result = connector.test_connection()
    except ValueError as e:
        result_obj = type("R", (), {"success": False, "error": str(e), "latency_ms": None, "server_version": None})()
        result = result_obj

    # Persist test result
    conn.last_tested_at = datetime.now(timezone.utc)
    conn.last_test_status = "SUCCESS" if result.success else "FAILED"
    conn.last_test_error = result.error if not result.success else None
    await db.commit()

    return ConnectionTestResult(
        success=result.success,
        latency_ms=result.latency_ms,
        error=result.error,
        server_version=result.server_version,
    )
