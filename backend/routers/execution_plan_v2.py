"""ExecutionPlan V2 preview, persist, and materialize router (Step 9.3.2 / 9.3.3 / 9.3.4.a)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from schemas.execution_plan_v2 import ExecutionPlanV2PersistResult, ExecutionPlanV2Preview
from schemas.execution_plan_v2_materialize import ExecutionPlanV2MaterializeResult
from schemas.execution_plan_v2_materialization_audit import ExecutionPlanV2MaterializationAudit
from services.execution_plan_v2_materialization_audit_service import (
    ExecutionPlanV2MaterializationAuditOrderNotFound,
    ExecutionPlanV2MaterializationAuditPlanNotFound,
    build_execution_plan_v2_materialization_audit_by_order_id,
    build_execution_plan_v2_materialization_audit_by_plan_id,
)
from services.execution_plan_v2_materialize_service import (
    ExecutionPlanV2MaterializeOrderNotFound,
    ExecutionPlanV2MaterializePlanNotFound,
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import (
    ExecutionPlanV2PersistOrderNotFound,
    create_execution_plan_v2_from_order,
)
from services.execution_plan_v2_preview_service import (
    ExecutionPlanV2PreviewOrderNotFound,
    build_execution_plan_v2_preview,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/execution",
    tags=["execution-plan-v2"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/plan-v2/preview/{order_id}",
    response_model=ExecutionPlanV2Preview,
)
async def preview_execution_plan_v2(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.plan_generate")),
) -> ExecutionPlanV2Preview:
    """Build and return a read-only ExecutionPlan V2 preview from OrderSnapshotV2."""
    logger.info("POST /api/v1/execution/plan-v2/preview/%s", order_id)
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})

    try:
        preview = await build_execution_plan_v2_preview(db, order_id)
    except ExecutionPlanV2PreviewOrderNotFound:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})

    return preview


@router.post(
    "/plan-v2/from-order/{order_id}",
    response_model=ExecutionPlanV2PersistResult,
    status_code=201,
)
async def persist_execution_plan_v2_from_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    _user=Depends(require_permission("execution.plan_generate")),
) -> ExecutionPlanV2PersistResult:
    """Persist one ExecutionPlan row from validated V2 preview — no task sessions."""
    logger.info("POST /api/v1/execution/plan-v2/from-order/%s", order_id)
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})

    prepared_by_user_id: str | None = None
    if current_user.id:
        uid = str(current_user.id).strip()
        if uid:
            prepared_by_user_id = uid

    try:
        result = await create_execution_plan_v2_from_order(
            db,
            order_id,
            prepared_by_user_id=prepared_by_user_id,
        )
    except ExecutionPlanV2PersistOrderNotFound:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})

    if result.status == "already_exists":
        return JSONResponse(
            status_code=200,
            content=result.model_dump(mode="json"),
        )
    return result


@router.post(
    "/plan-v2/materialize-tasks/{order_id}",
    response_model=ExecutionPlanV2MaterializeResult,
    status_code=201,
)
async def materialize_execution_plan_v2_tasks(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    _user=Depends(require_permission("execution.plan_generate")),
) -> ExecutionPlanV2MaterializeResult:
    """Materialize operational_tasks[] into V2 plan envelope — no sessions."""
    logger.info("POST /api/v1/execution/plan-v2/materialize-tasks/%s", order_id)
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})

    prepared_by_user_id: str | None = None
    if current_user.id:
        uid = str(current_user.id).strip()
        if uid:
            prepared_by_user_id = uid

    try:
        return await materialize_execution_plan_v2_operational_tasks(
            db,
            order_id,
            prepared_by_user_id=prepared_by_user_id,
        )
    except ExecutionPlanV2MaterializeOrderNotFound:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})
    except ExecutionPlanV2MaterializePlanNotFound:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})


@router.get(
    "/plan-v2/{execution_plan_id}/materialization-audit",
    response_model=ExecutionPlanV2MaterializationAudit,
)
async def materialization_audit_by_plan_id(
    execution_plan_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.plan_generate")),
) -> ExecutionPlanV2MaterializationAudit:
    """Read-only audit of V2 plan materialization mapping — no DB writes."""
    logger.info("GET /api/v1/execution/plan-v2/%s/materialization-audit", execution_plan_id)
    if execution_plan_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "execution_plan_id_invalid"})
    try:
        return await build_execution_plan_v2_materialization_audit_by_plan_id(
            db,
            execution_plan_id,
        )
    except ExecutionPlanV2MaterializationAuditPlanNotFound:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})


@router.get(
    "/plan-v2/from-order/{order_id}/materialization-audit",
    response_model=ExecutionPlanV2MaterializationAudit,
)
async def materialization_audit_by_order_id(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.plan_generate")),
) -> ExecutionPlanV2MaterializationAudit:
    """Read-only materialization audit for an order's persisted V2 plan."""
    logger.info("GET /api/v1/execution/plan-v2/from-order/%s/materialization-audit", order_id)
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    try:
        return await build_execution_plan_v2_materialization_audit_by_order_id(db, order_id)
    except ExecutionPlanV2MaterializationAuditOrderNotFound:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})
    except ExecutionPlanV2MaterializationAuditPlanNotFound:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})
