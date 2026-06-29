from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.pipeline import Pipeline, ColumnMapping, TransformRule, ValidationRule
from app.models.user import User
from app.schemas.pipeline import (
    PipelineCreate, PipelineUpdate, PipelineOut, PipelineDetail,
    ColumnMappingSchema, ValidationRuleSchema, ScheduleSchema,
)
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])


def _load_opts():
    return [
        selectinload(Pipeline.column_mappings).selectinload(ColumnMapping.transform_rules),
        selectinload(Pipeline.validation_rules),
        selectinload(Pipeline.schedule),
        selectinload(Pipeline.source_connection),
        selectinload(Pipeline.target_connection),
    ]


@router.get("", response_model=List[PipelineOut])
async def list_pipelines(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Pipeline)
    if status:
        query = query.where(Pipeline.status == status.upper())
    query = query.order_by(Pipeline.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=PipelineOut, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    body: PipelineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = Pipeline(
        name=body.name,
        description=body.description,
        source_connection_id=body.source_connection_id,
        target_connection_id=body.target_connection_id,
        source_config=body.source_config,
        target_config=body.target_config,
        load_strategy=body.load_strategy,
        upsert_keys=body.upsert_keys or [],
        batch_size=body.batch_size,
        retry_count=body.retry_count,
        retry_delay_seconds=body.retry_delay_seconds,
        schema_drift_action=body.schema_drift_action,
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)
    return pipeline


@router.get("/{pipeline_id}", response_model=PipelineDetail)
async def get_pipeline(
    pipeline_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Pipeline).options(*_load_opts()).where(Pipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline bulunamadı")
    return pipeline


@router.put("/{pipeline_id}", response_model=PipelineOut)
async def update_pipeline(
    pipeline_id: UUID,
    body: PipelineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline bulunamadı")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(pipeline, field, value)

    await db.commit()
    await db.refresh(pipeline)
    return pipeline


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline bulunamadı")
    pipeline.status = "DISABLED"
    await db.commit()


@router.post("/{pipeline_id}/publish", response_model=PipelineOut)
async def publish_pipeline(
    pipeline_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline bulunamadı")
    pipeline.status = "ACTIVE"
    await db.commit()
    await db.refresh(pipeline)
    return pipeline


@router.put("/{pipeline_id}/mappings")
async def upsert_mappings(
    pipeline_id: UUID,
    mappings: List[ColumnMappingSchema],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Replace all column mappings for a pipeline."""
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline bulunamadı")

    # Delete existing mappings
    result = await db.execute(select(ColumnMapping).where(ColumnMapping.pipeline_id == pipeline_id))
    for m in result.scalars().all():
        await db.delete(m)
    await db.flush()

    # Insert new ones
    for m_data in mappings:
        mapping = ColumnMapping(
            pipeline_id=pipeline_id,
            source_column=m_data.source_column,
            target_column=m_data.target_column,
            source_type=m_data.source_type,
            target_type=m_data.target_type,
            is_constant=m_data.is_constant,
            constant_value=m_data.constant_value,
            default_value=m_data.default_value,
            is_nullable=m_data.is_nullable,
            is_excluded=m_data.is_excluded,
            ordinal_position=m_data.ordinal_position,
        )
        db.add(mapping)
        await db.flush()

        for rule in m_data.transform_rules:
            db.add(TransformRule(
                mapping_id=mapping.id,
                transform_type=rule.transform_type,
                params=rule.params,
                apply_order=rule.apply_order,
            ))

    await db.commit()
    return {"message": f"{len(mappings)} mapping kaydedildi"}


@router.put("/{pipeline_id}/validations")
async def upsert_validations(
    pipeline_id: UUID,
    rules: List[ValidationRuleSchema],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline bulunamadı")

    result = await db.execute(select(ValidationRule).where(ValidationRule.pipeline_id == pipeline_id))
    for r in result.scalars().all():
        await db.delete(r)
    await db.flush()

    for r_data in rules:
        db.add(ValidationRule(
            pipeline_id=pipeline_id,
            mapping_id=r_data.mapping_id,
            rule_type=r_data.rule_type,
            params=r_data.params,
            action_on_fail=r_data.action_on_fail,
        ))

    await db.commit()
    return {"message": f"{len(rules)} validation kuralı kaydedildi"}
