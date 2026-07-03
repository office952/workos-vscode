"""Employee-mobile self-only execution task endpoints."""

from __future__ import annotations

from typing import List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.employee_mobile import EmployeeMobileContext, require_employee_self_user
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from schemas.auth import UserResponse
from services.employee_mobile_order_blueprint_service import get_employee_my_order_blueprint
from services.employee_mobile_production_documents_service import (
    download_order_work_file_for_employee,
)
from services.employee_mobile_tasks_service import (
    block_my_task,
    claim_my_task,
    complete_my_task,
    get_employee_mobile_task,
    list_available_tasks,
    list_my_tasks,
    pause_my_task,
    resume_my_task,
    start_available_task,
    start_my_task,
    unblock_my_task,
)
from services.task_clarification_request_service import create_clarification_request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/api/v1/employee-mobile",
    tags=["employee-mobile"],
    dependencies=[Depends(get_current_user)],
)


class EmployeeMobileTaskResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    task_id: str
    order_id: int
    order_code: str = ""
    title: str = ""
    description: str = ""
    instructions: str = ""
    status: str
    process_type: str = ""
    machine_type: str = ""
    estimated_time_minutes: float = 0
    assigned_employee_id: Optional[int] = None
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    client: str = ""
    product: str = ""
    quote_code: str = ""
    intake_code: str = ""
    order_status: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    blocked_at: Optional[str] = None
    blocked_reason: Optional[str] = None
    documents: List[dict] = Field(default_factory=list)
    clarification_request: Optional[dict] = None
    readiness_status: Optional[str] = None
    readiness_label: Optional[str] = None
    is_startable: Optional[bool] = None
    readiness_reasons: List[dict] = Field(default_factory=list)
    blocking_task_ids: List[str] = Field(default_factory=list)
    blocking_tasks: List[dict] = Field(default_factory=list)
    dependency_warning: Optional[str] = None
    preparation_domain: Optional[str] = None
    eligibility_reason: Optional[str] = None
    claimable: Optional[bool] = None
    access_mode: Optional[str] = None
    preview_only: Optional[bool] = None


class EmployeeMobileClaimResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    action: str
    task_id: str
    order_id: int
    assigned_employee_id: int
    assigned_employee_name: Optional[str] = None
    already_claimed: bool = False


class TaskOrderRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: int = Field(..., gt=0)


class TaskClarificationCreateBody(TaskOrderRef):
    message: str = Field(..., min_length=1, max_length=4000)


class TaskClarificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    order_id: int
    task_id: str
    employee_id: int
    employee_name: str = ""
    message: str = ""
    status: str
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by_user_id: Optional[str] = None
    target_user_id: Optional[str] = None
    target_user_name: Optional[str] = None
    routed_to_responsible: bool = False


class TaskBlockBody(TaskOrderRef):
    reason: Optional[str] = None


class EmployeeMobileOrderBlueprintSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_tasks: int
    my_tasks: int
    my_done: int
    overall_progress_percent: int
    my_progress_percent: int
    blocked: int
    in_progress: int


class EmployeeMobileMaterialHint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: str
    label: str
    status: str = ""
    display_note: str = ""


class EmployeeMobileOrderBlueprintTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    name: str
    status_display: str
    is_mine: bool
    is_current: bool
    is_eligible_for_me: bool = False
    can_assist: bool = False
    eligibility_reason: str = ""
    active_helper_count: int = 0
    stage_label: str
    has_documents: bool
    has_instructions: bool
    readiness_status: str = ""
    readiness_label: str = ""
    is_startable: bool = False
    readiness_reasons: List[dict] = Field(default_factory=list)
    blocking_reasons: List[dict] = Field(default_factory=list)
    blocking_task_ids: List[str] = Field(default_factory=list)
    blocking_tasks: List[dict] = Field(default_factory=list)
    dependency_warning: Optional[str] = None
    material_warning: Optional[str] = None
    material_hints: List[EmployeeMobileMaterialHint] = Field(default_factory=list)
    material_status_label: Optional[str] = None


class EmployeeMobileOrderBlueprintResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: int
    order_label: str
    client_label: str = ""
    summary: EmployeeMobileOrderBlueprintSummary
    current_task_id: Optional[str] = None
    tasks: List[EmployeeMobileOrderBlueprintTask]


@router.get("/tasks", response_model=List[EmployeeMobileTaskResponse])
async def get_my_tasks(
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    """List execution tasks owned by or assigned to the authenticated employee."""
    rows = await list_my_tasks(db, ctx.employee.id)
    return rows


@router.get("/tasks/available", response_model=List[EmployeeMobileTaskResponse])
async def get_available_tasks(
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    """List unassigned execution tasks the authenticated employee may claim."""
    rows = await list_available_tasks(db, ctx.employee.id)
    return rows


@router.get(
    "/orders/{order_id}/tasks/{task_id}",
    response_model=EmployeeMobileTaskResponse,
)
async def get_order_task(
    order_id: int,
    task_id: str,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    """Read-only task detail scoped to order_id + task_id (owned or available preview)."""
    return await get_employee_mobile_task(
        db,
        order_id=order_id,
        task_id=task_id,
        employee_id=ctx.employee.id,
    )


@router.post("/tasks/{task_id}/claim", response_model=EmployeeMobileClaimResponse)
async def claim_task(
    task_id: str,
    body: TaskOrderRef,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    """Claim an unassigned plan task — assigns to self without starting work."""
    payload = await claim_my_task(
        db,
        order_id=body.order_id,
        task_id=task_id,
        employee_id=ctx.employee.id,
    )
    return EmployeeMobileClaimResponse(**payload)


@router.post("/tasks/{task_id}/start-from-available")
async def start_task_from_available(
    task_id: str,
    body: TaskOrderRef,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    """Assign (if unassigned) and start an eligible available task in one atomic flow."""
    return await start_available_task(
        db,
        order_id=body.order_id,
        task_id=task_id,
        employee_id=ctx.employee.id,
    )


@router.get(
    "/orders/{order_id}/my-blueprint",
    response_model=EmployeeMobileOrderBlueprintResponse,
)
async def get_my_order_blueprint(
    order_id: int,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    """Read-only order blueprint for the authenticated employee — own tasks highlighted."""
    payload = await get_employee_my_order_blueprint(
        db,
        order_id=order_id,
        employee_id=ctx.employee.id,
    )
    return EmployeeMobileOrderBlueprintResponse(**payload)


@router.post(
    "/tasks/{task_id}/clarification-requests",
    response_model=TaskClarificationResponse,
)
async def create_task_clarification_request(
    task_id: str,
    body: TaskClarificationCreateBody,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    """Employee asks for production clarification without blocking the task."""
    row = await create_clarification_request(
        db,
        employee_id=ctx.employee.id,
        order_id=body.order_id,
        task_id=task_id,
        message=body.message,
    )
    return TaskClarificationResponse(**row)


@router.get("/orders/{order_id}/work-files/{file_id}/download")
async def download_assigned_order_work_file(
    order_id: int,
    file_id: str,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    """Download an intake production work file for an order where the employee has assigned tasks."""
    return await download_order_work_file_for_employee(
        db,
        order_id=order_id,
        file_id=file_id,
        employee_id=ctx.employee.id,
    )


@router.patch("/tasks/{task_id}/start")
async def start_task(
    task_id: str,
    body: TaskOrderRef,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    return await start_my_task(
        db,
        order_id=body.order_id,
        task_id=task_id,
        employee_id=ctx.employee.id,
    )


@router.patch("/tasks/{task_id}/block")
async def block_task(
    task_id: str,
    body: TaskBlockBody,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    return await block_my_task(
        db,
        order_id=body.order_id,
        task_id=task_id,
        employee_id=ctx.employee.id,
        reason=body.reason,
    )


@router.patch("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    body: TaskOrderRef,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    return await complete_my_task(
        db,
        order_id=body.order_id,
        task_id=task_id,
        employee_id=ctx.employee.id,
    )


@router.patch("/tasks/{task_id}/unblock")
async def unblock_task(
    task_id: str,
    body: TaskOrderRef,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    return await unblock_my_task(
        db,
        order_id=body.order_id,
        task_id=task_id,
        employee_id=ctx.employee.id,
    )


@router.patch("/tasks/{task_id}/pause")
async def pause_task(
    task_id: str,
    body: TaskOrderRef,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    """Interrupt work on the employee's session without blocking the task."""
    return await pause_my_task(
        db,
        order_id=body.order_id,
        task_id=task_id,
        employee_id=ctx.employee.id,
    )


@router.patch("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str,
    body: TaskOrderRef,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused session for the authenticated employee."""
    return await resume_my_task(
        db,
        order_id=body.order_id,
        task_id=task_id,
        employee_id=ctx.employee.id,
    )
