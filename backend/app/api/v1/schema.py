from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import decrypt_value
from app.models.connection import Connection
from app.models.user import User
from app.api.v1.deps import get_current_user
from app.connectors.factory import create_connector

router = APIRouter(prefix="/schema", tags=["Schema"])


class SchemaColumnOut(BaseModel):
    name: str
    data_type: str
    is_nullable: bool
    precision: Optional[int] = None
    scale: Optional[int] = None
    max_length: Optional[int] = None


def _build_config(conn: Connection) -> dict:
    password = None
    if conn.encrypted_password:
        try:
            password = decrypt_value(conn.encrypted_password)
        except Exception:
            password = conn.encrypted_password
    return {
        "host": conn.host, "port": conn.port,
        "database_name": conn.database_name,
        "username": conn.username, "password": password,
        "extra_config": conn.extra_config or {},
    }


@router.get("/{connection_id}/tables")
async def list_tables(
    connection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = await db.get(Connection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Bağlantı bulunamadı")

    try:
        connector = create_connector(conn.type, _build_config(conn))
        tables = connector.list_tables()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{connection_id}/columns", response_model=list[SchemaColumnOut])
async def get_columns(
    connection_id: UUID,
    table: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = await db.get(Connection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Bağlantı bulunamadı")

    try:
        connector = create_connector(conn.type, _build_config(conn))
        columns = connector.get_schema(table)
        return [SchemaColumnOut(**c.__dict__) for c in columns]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{connection_id}/preview")
async def preview_data(
    connection_id: UUID,
    table: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = await db.get(Connection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Bağlantı bulunamadı")

    try:
        connector = create_connector(conn.type, _build_config(conn))
        df = connector.preview_data(table, limit=min(limit, 100))
        return {
            "columns": df.columns,
            "rows": df.to_dicts(),
            "total_preview": len(df),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
