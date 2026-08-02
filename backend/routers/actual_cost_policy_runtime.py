"""Management-only APIs for standard internal actual-cost policy and job closure."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.actual_cost_policy_runtime_service import ActualCostPolicyRuntimeService

router = APIRouter(prefix="/api/v1/actual-cost-policy", tags=["actual-cost-policy-runtime"])


class StandardInternalCostPolicyInput(BaseModel):
    role_code: str
    skill_code: str | None = None
    standard_internal_rate: float = Field(ge=0)
    currency: str = "RON"
    effective_from: datetime
    effective_to: datetime | None = None
    rate_unit: str = "hour"
    provenance: str = "manager_confirmed"
    reason: str


class ClosureInput(BaseModel):
    checklist: dict[str, Any]


class ReopenInput(BaseModel):
    reason: str = Field(min_length=1)


@router.post("/labor-policies")
async def create_standard_internal_labor_policy(
    payload: StandardInternalCostPolicyInput,
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
    _permission: UserResponse = Depends(require_permission("actual_cost_policy.manage")),
):
    policy = await ActualCostPolicyRuntimeService(db).create_policy(payload.model_dump(), str(user.id))
    await db.commit()
    return {"id": policy.id, "version": policy.version, "rate_unit": policy.rate_unit}


@router.post("/orders/{order_id}/finalize-labor")
async def finalize_labor(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _permission: UserResponse = Depends(require_permission("actual_cost_policy.manage")),
):
    result = await ActualCostPolicyRuntimeService(db).finalize_labor_lines(order_id)
    await db.commit()
    return result


@router.get("/orders/{order_id}/closure-readiness")
async def closure_readiness(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _permission: UserResponse = Depends(require_permission("execution.closure_readiness")),
):
    return await ActualCostPolicyRuntimeService(db).closure_readiness(order_id)


@router.post("/orders/{order_id}/close")
async def close_job(
    order_id: int,
    payload: ClosureInput,
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
    _permission: UserResponse = Depends(require_permission("execution.job_close")),
):
    closure = await ActualCostPolicyRuntimeService(db).close_job(order_id, str(user.id), payload.checklist)
    await db.commit()
    return {"order_id": closure.order_id, "status": closure.status, "closed_at": closure.closed_at}


@router.post("/orders/{order_id}/reopen")
async def reopen_job(
    order_id: int,
    payload: ReopenInput,
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
    _permission: UserResponse = Depends(require_permission("execution.job_close")),
):
    closure = await ActualCostPolicyRuntimeService(db).reopen_job(order_id, str(user.id), payload.reason)
    await db.commit()
    return {"order_id": closure.order_id, "status": closure.status, "reopen_at": closure.reopen_at}
