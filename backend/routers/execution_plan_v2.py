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
from schemas.operational_resource_readiness import OperationalResourceReadinessResult
from schemas.resource_state_configuration import (
    ResourceDomainConfigurationCommand,
    ResourceDomainConfigurationResult,
)
from schemas.resource_state_read import TaskResourceStateResult
from schemas.resource_state_machine_run import (
    AddMachineRunParticipantCommand,
    CancelMachineRunCommand,
    CompleteMachineRunCommand,
    ConfirmMachineRunCommand,
    CreateMachineRunCommand,
    CreateMachineRunResult,
    ReleaseMachineRunCommand,
    RemoveMachineRunParticipantCommand,
    RescheduleMachineRunCommand,
    StartMachineRunCommand,
)
from schemas.resource_state_reservation import (
    CancelReservationCommand,
    ConfirmReservationCommand,
    CreateReservationCommand,
    ReleaseReservationCommand,
    ReservationCommandResult,
    SupersedeReservationCommand,
)
from schemas.resource_state_capacity_allocation import (
    AdjustAllocationCommand,
    AllocationCommandResult,
    CancelAllocationCommand,
    CreateAllocationCommand,
    ReleaseAllocationCommand,
    SupersedeAllocationCommand,
)
from schemas.resource_state_capacity_source import (
    AdjustWorkcenterCapacityCommand,
    CreateWorkcenterCapacityCommand,
    DisableWorkcenterCapacityCommand,
    SupersedeWorkcenterCapacityCommand,
    WorkcenterCapacitySourceResult,
)
from schemas.resource_state_schedule import (
    CancelScheduleCommand,
    ConfirmScheduleCommand,
    CreateScheduleCommand,
    RescheduleCommand,
    ScheduleCommandResult,
    SupersedeScheduleCommand,
)
from schemas.task_resource_requirement_projection import (
    PlanResourceRequirementProjection,
)
from services.assignment_readiness_audit_service import (
    build_assignment_readiness_audit,
)
from services.execution_task_capacity_allocation_command_service import (
    adjust_allocation,
    cancel_allocation,
    create_allocation,
    release_allocation,
    supersede_allocation,
)
from services.execution_task_machine_reservation_command_service import (
    cancel_reservation,
    confirm_reservation,
    create_reservation,
    release_reservation,
    supersede_reservation,
)
from services.machine_run_command_service import (
    add_machine_run_participant,
    cancel_machine_run,
    complete_machine_run,
    confirm_machine_run,
    create_machine_run,
    release_machine_run,
    remove_machine_run_participant,
    reschedule_machine_run,
    start_machine_run,
)
from services.execution_task_schedule_command_service import (
    cancel_schedule,
    confirm_schedule,
    create_schedule,
    reschedule_schedule,
    supersede_schedule,
)
from services.workcenter_capacity_source_command_service import (
    adjust_workcenter_capacity,
    create_workcenter_capacity,
    disable_workcenter_capacity,
    supersede_workcenter_capacity,
)
from services.resource_domain_configuration_command_service import (
    ResourceDomainConfigurationActivationBlockedError,
    ResourceDomainConfigurationCasConflictError,
    ResourceDomainConfigurationConflictError,
    ResourceDomainConfigurationDisableBlockedError,
    ResourceDomainConfigurationValidationError,
    configure_resource_domain,
)
from services.resource_state_read_service import (
    ResourceStatePlanNotFoundError,
    ResourceStateTaskNotFoundError,
    evaluate_task_resource_state,
)
from services.resource_state_write_common import ResourceStateWriteError
from services.employee_eligibility_read_model_service import (
    build_employee_eligibility_read_model,
)
from services.task_resource_requirement_projection_service import (
    TaskResourceRequirementPlanNotFoundError,
    TaskResourceRequirementTaskNotFoundError,
    project_plan_resource_requirements,
)
from services.operational_resource_readiness_service import (
    build_operational_resource_readiness,
)
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


@router.get("/plan-v2/from-order/{order_id}/employee-eligibility")
async def employee_eligibility_read_model_by_order_id(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.plan_generate")),
) -> dict:
    """DEC-015 — read-only employee eligibility for materialized operational_tasks[].

    Never assigns, claims, starts, or creates sessions/actuals.
    """
    logger.info(
        "GET /api/v1/execution/plan-v2/from-order/%s/employee-eligibility", order_id
    )
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    return await build_employee_eligibility_read_model(db, order_id)


@router.get("/plan-v2/from-order/{order_id}/assignment-readiness")
async def assignment_readiness_audit_by_order_id(
    order_id: int,
    candidate_employee_id: int | None = None,
    task_key: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.plan_generate")),
) -> dict:
    """Wave 5 — read-only assignment readiness audit + command-contract inventory.

    Never executes PATCH assign, never writes tasks_json, never creates sessions.
    assignment_authorized remains false (OWNER_GO_FOR_REAL_ASSIGNMENT_NOT_GRANTED).
    Optional query params evaluate a hypothetical candidate without persistence.
    """
    logger.info(
        "GET /api/v1/execution/plan-v2/from-order/%s/assignment-readiness", order_id
    )
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    if candidate_employee_id is not None and candidate_employee_id <= 0:
        raise HTTPException(
            status_code=422, detail={"error": "candidate_employee_id_invalid"}
        )
    return await build_assignment_readiness_audit(
        db,
        order_id,
        candidate_employee_id=candidate_employee_id,
        task_key=task_key,
    )


@router.post(
    "/resource-state/configurations/{domain}",
    response_model=ResourceDomainConfigurationResult,
)
async def post_resource_domain_configuration(
    domain: str,
    body: ResourceDomainConfigurationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.resource_domain.configure")
    ),
) -> ResourceDomainConfigurationResult:
    """R7 — configure / activate / disable a Resource State domain.

    Does not write schedules, reservations, or capacity.
    Does not wire Phase B. QA activation remains Owner-gated separately —
    do not invoke against live QA without an explicit activation GO.
    """
    logger.info(
        "POST /api/v1/execution/resource-state/configurations/%s "
        "target=%s expected_version=%s actor=%s",
        domain,
        body.target_status,
        body.expected_version,
        current_user.id,
    )
    try:
        result = await configure_resource_domain(
            db,
            domain=domain,
            command=body,
            actor_user_id=str(current_user.id),
        )
        await db.commit()
        return result
    except ResourceDomainConfigurationValidationError as exc:
        raise HTTPException(
            status_code=422, detail={"error": exc.code, "message": exc.message}
        ) from None
    except ResourceDomainConfigurationCasConflictError as exc:
        raise HTTPException(
            status_code=409, detail={"error": exc.code, "message": exc.message}
        ) from None
    except ResourceDomainConfigurationConflictError as exc:
        raise HTTPException(
            status_code=409, detail={"error": exc.code, "message": exc.message}
        ) from None
    except ResourceDomainConfigurationActivationBlockedError as exc:
        raise HTTPException(
            status_code=409, detail={"error": exc.code, "message": exc.message}
        ) from None
    except ResourceDomainConfigurationDisableBlockedError as exc:
        raise HTTPException(
            status_code=409, detail={"error": exc.code, "message": exc.message}
        ) from None


def _raise_rs_write(exc: ResourceStateWriteError) -> None:
    raise HTTPException(
        status_code=exc.http_status,
        detail={"error": exc.code, "message": exc.message},
    ) from None


@router.post(
    "/resource-state/schedules",
    response_model=ScheduleCommandResult,
)
async def post_create_schedule(
    body: CreateScheduleCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.schedule.manage")
    ),
) -> ScheduleCommandResult:
    """R9 — CREATE_SCHEDULE (isolated writers; do not call against QA)."""
    try:
        return await create_schedule(
            db, command=body, actor_user_id=str(current_user.id)
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/schedules/{schedule_id}/reschedule",
    response_model=ScheduleCommandResult,
)
async def post_reschedule_schedule(
    schedule_id: int,
    body: RescheduleCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.schedule.manage")
    ),
) -> ScheduleCommandResult:
    try:
        return await reschedule_schedule(
            db,
            schedule_id=schedule_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/schedules/{schedule_id}/confirm",
    response_model=ScheduleCommandResult,
)
async def post_confirm_schedule(
    schedule_id: int,
    body: ConfirmScheduleCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.schedule.manage")
    ),
) -> ScheduleCommandResult:
    try:
        return await confirm_schedule(
            db,
            schedule_id=schedule_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/schedules/{schedule_id}/cancel",
    response_model=ScheduleCommandResult,
)
async def post_cancel_schedule(
    schedule_id: int,
    body: CancelScheduleCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.schedule.manage")
    ),
) -> ScheduleCommandResult:
    try:
        return await cancel_schedule(
            db,
            schedule_id=schedule_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/schedules/{schedule_id}/supersede",
    response_model=ScheduleCommandResult,
)
async def post_supersede_schedule(
    schedule_id: int,
    body: SupersedeScheduleCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.schedule.manage")
    ),
) -> ScheduleCommandResult:
    try:
        return await supersede_schedule(
            db,
            schedule_id=schedule_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/reservations",
    response_model=ReservationCommandResult,
)
async def post_create_reservation(
    body: CreateReservationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_reservation.manage")
    ),
) -> ReservationCommandResult:
    """R9 — CREATE_RESERVATION (isolated writers; do not call against QA)."""
    try:
        return await create_reservation(
            db, command=body, actor_user_id=str(current_user.id)
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/machine-runs",
    response_model=CreateMachineRunResult,
)
async def post_create_machine_run(
    body: CreateMachineRunCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_run.manage")
    ),
) -> CreateMachineRunResult:
    """CREATE_MACHINE_RUN (isolated writers; do not call against QA)."""
    try:
        return await create_machine_run(
            db, command=body, actor_user_id=str(current_user.id)
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/machine-runs/{machine_run_id}/confirm",
    response_model=CreateMachineRunResult,
)
async def post_confirm_machine_run(
    machine_run_id: int,
    body: ConfirmMachineRunCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_run.manage")
    ),
) -> CreateMachineRunResult:
    """CONFIRM_MACHINE_RUN — HELD→RESERVED (isolated; do not call against QA)."""
    try:
        return await confirm_machine_run(
            db,
            machine_run_id=machine_run_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/machine-runs/{machine_run_id}/release",
    response_model=CreateMachineRunResult,
)
async def post_release_machine_run(
    machine_run_id: int,
    body: ReleaseMachineRunCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_run.manage")
    ),
) -> CreateMachineRunResult:
    """RELEASE_MACHINE_RUN — RESERVED|COMPLETED→RELEASED (isolated; not QA)."""
    try:
        return await release_machine_run(
            db,
            machine_run_id=machine_run_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/machine-runs/{machine_run_id}/start",
    response_model=CreateMachineRunResult,
)
async def post_start_machine_run(
    machine_run_id: int,
    body: StartMachineRunCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_run.execute")
    ),
) -> CreateMachineRunResult:
    """START_MACHINE_RUN — RESERVED→RUNNING (reservation stays RESERVED; not QA)."""
    try:
        return await start_machine_run(
            db,
            machine_run_id=machine_run_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/machine-runs/{machine_run_id}/complete",
    response_model=CreateMachineRunResult,
)
async def post_complete_machine_run(
    machine_run_id: int,
    body: CompleteMachineRunCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_run.execute")
    ),
) -> CreateMachineRunResult:
    """COMPLETE_MACHINE_RUN — RUNNING→COMPLETED (reservation stays RESERVED; not QA)."""
    try:
        return await complete_machine_run(
            db,
            machine_run_id=machine_run_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/machine-runs/{machine_run_id}/cancel",
    response_model=CreateMachineRunResult,
)
async def post_cancel_machine_run(
    machine_run_id: int,
    body: CancelMachineRunCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_run.manage")
    ),
) -> CreateMachineRunResult:
    """CANCEL_MACHINE_RUN — HELD|RESERVED→CANCELLED (isolated; do not call against QA)."""
    try:
        return await cancel_machine_run(
            db,
            machine_run_id=machine_run_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/machine-runs/{machine_run_id}/reschedule",
    response_model=CreateMachineRunResult,
)
async def post_reschedule_machine_run(
    machine_run_id: int,
    body: RescheduleMachineRunCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_run.manage")
    ),
) -> CreateMachineRunResult:
    """RESCHEDULE_MACHINE_RUN — same status/machine; new window (isolated; not QA)."""
    try:
        return await reschedule_machine_run(
            db,
            machine_run_id=machine_run_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/machine-runs/{machine_run_id}/add-participant",
    response_model=CreateMachineRunResult,
)
async def post_add_machine_run_participant(
    machine_run_id: int,
    body: AddMachineRunParticipantCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_run.manage")
    ),
) -> CreateMachineRunResult:
    """ADD_MACHINE_RUN_PARTICIPANT — HELD only (isolated; not QA)."""
    try:
        return await add_machine_run_participant(
            db,
            machine_run_id=machine_run_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/machine-runs/{machine_run_id}/remove-participant",
    response_model=CreateMachineRunResult,
)
async def post_remove_machine_run_participant(
    machine_run_id: int,
    body: RemoveMachineRunParticipantCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_run.manage")
    ),
) -> CreateMachineRunResult:
    """REMOVE_MACHINE_RUN_PARTICIPANT — HELD only, soft REMOVED (isolated; not QA)."""
    try:
        return await remove_machine_run_participant(
            db,
            machine_run_id=machine_run_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/reservations/{reservation_id}/confirm",
    response_model=ReservationCommandResult,
)
async def post_confirm_reservation(
    reservation_id: int,
    body: ConfirmReservationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_reservation.manage")
    ),
) -> ReservationCommandResult:
    try:
        return await confirm_reservation(
            db,
            reservation_id=reservation_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/reservations/{reservation_id}/release",
    response_model=ReservationCommandResult,
)
async def post_release_reservation(
    reservation_id: int,
    body: ReleaseReservationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_reservation.manage")
    ),
) -> ReservationCommandResult:
    try:
        return await release_reservation(
            db,
            reservation_id=reservation_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/reservations/{reservation_id}/cancel",
    response_model=ReservationCommandResult,
)
async def post_cancel_reservation(
    reservation_id: int,
    body: CancelReservationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_reservation.manage")
    ),
) -> ReservationCommandResult:
    try:
        return await cancel_reservation(
            db,
            reservation_id=reservation_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/reservations/{reservation_id}/supersede",
    response_model=ReservationCommandResult,
)
async def post_supersede_reservation(
    reservation_id: int,
    body: SupersedeReservationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.machine_reservation.manage")
    ),
) -> ReservationCommandResult:
    try:
        return await supersede_reservation(
            db,
            reservation_id=reservation_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/workcenter-capacity",
    response_model=WorkcenterCapacitySourceResult,
)
async def post_create_workcenter_capacity(
    body: CreateWorkcenterCapacityCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.capacity_source.manage")
    ),
) -> WorkcenterCapacitySourceResult:
    """Stage 1 — CREATE_WORKCENTER_CAPACITY (isolated; do not call against QA)."""
    try:
        return await create_workcenter_capacity(
            db, command=body, actor_user_id=str(current_user.id)
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/workcenter-capacity/{source_id}/adjust",
    response_model=WorkcenterCapacitySourceResult,
)
async def post_adjust_workcenter_capacity(
    source_id: int,
    body: AdjustWorkcenterCapacityCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.capacity_source.manage")
    ),
) -> WorkcenterCapacitySourceResult:
    try:
        return await adjust_workcenter_capacity(
            db,
            source_id=source_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/workcenter-capacity/{source_id}/disable",
    response_model=WorkcenterCapacitySourceResult,
)
async def post_disable_workcenter_capacity(
    source_id: int,
    body: DisableWorkcenterCapacityCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.capacity_source.manage")
    ),
) -> WorkcenterCapacitySourceResult:
    try:
        return await disable_workcenter_capacity(
            db,
            source_id=source_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/workcenter-capacity/{source_id}/supersede",
    response_model=WorkcenterCapacitySourceResult,
)
async def post_supersede_workcenter_capacity(
    source_id: int,
    body: SupersedeWorkcenterCapacityCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.capacity_source.manage")
    ),
) -> WorkcenterCapacitySourceResult:
    try:
        return await supersede_workcenter_capacity(
            db,
            source_id=source_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/allocations",
    response_model=AllocationCommandResult,
)
async def post_create_allocation(
    body: CreateAllocationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.capacity_allocation.manage")
    ),
) -> AllocationCommandResult:
    """Stage 1 — CREATE_ALLOCATION WORKCENTER/DAY (isolated; do not call against QA)."""
    try:
        return await create_allocation(
            db, command=body, actor_user_id=str(current_user.id)
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/allocations/{allocation_id}/adjust",
    response_model=AllocationCommandResult,
)
async def post_adjust_allocation(
    allocation_id: int,
    body: AdjustAllocationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.capacity_allocation.manage")
    ),
) -> AllocationCommandResult:
    try:
        return await adjust_allocation(
            db,
            allocation_id=allocation_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/allocations/{allocation_id}/release",
    response_model=AllocationCommandResult,
)
async def post_release_allocation(
    allocation_id: int,
    body: ReleaseAllocationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.capacity_allocation.manage")
    ),
) -> AllocationCommandResult:
    try:
        return await release_allocation(
            db,
            allocation_id=allocation_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/allocations/{allocation_id}/cancel",
    response_model=AllocationCommandResult,
)
async def post_cancel_allocation(
    allocation_id: int,
    body: CancelAllocationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.capacity_allocation.manage")
    ),
) -> AllocationCommandResult:
    try:
        return await cancel_allocation(
            db,
            allocation_id=allocation_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.post(
    "/resource-state/allocations/{allocation_id}/supersede",
    response_model=AllocationCommandResult,
)
async def post_supersede_allocation(
    allocation_id: int,
    body: SupersedeAllocationCommand,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(
        require_permission("execution.capacity_allocation.manage")
    ),
) -> AllocationCommandResult:
    try:
        return await supersede_allocation(
            db,
            allocation_id=allocation_id,
            command=body,
            actor_user_id=str(current_user.id),
        )
    except ResourceStateWriteError as exc:
        _raise_rs_write(exc)


@router.get(
    "/resource-state/plans/{plan_id}/tasks",
    response_model=TaskResourceStateResult,
)
async def get_task_resource_state(
    plan_id: int,
    task_key: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.plan_generate")),
) -> TaskResourceStateResult:
    """R6 — read-only Resource State evaluation for one plan task.

    ``task_key`` is a query parameter so keys with ``:`` remain unambiguous.
    Does not write configurations/schedules/reservations/capacity.
    Does not wire Phase B reassignment consumers.
    """
    logger.info(
        "GET /api/v1/execution/resource-state/plans/%s/tasks?task_key=%s",
        plan_id,
        task_key,
    )
    if plan_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "plan_id_invalid"})
    try:
        return await evaluate_task_resource_state(
            db, plan_id=plan_id, task_key=task_key
        )
    except ResourceStatePlanNotFoundError:
        raise HTTPException(
            status_code=404, detail={"error": "execution_plan_not_found"}
        ) from None
    except ResourceStateTaskNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail={"error": str(exc) or "task_key_not_found"}
        ) from None


@router.get(
    "/plans/{plan_id}/resource-requirements",
    response_model=PlanResourceRequirementProjection,
)
async def get_plan_resource_requirements(
    plan_id: int,
    task_key: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.plan_generate")),
) -> PlanResourceRequirementProjection:
    """Read-only task resource requirement projection (demand visibility).

    Does not mutate tasks_json, does not write reservations/schedules/capacity,
    does not select employees or book workspaces, does not gate Phase B.
    """
    logger.info(
        "GET /api/v1/execution/plans/%s/resource-requirements task_key=%s",
        plan_id,
        task_key,
    )
    if plan_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "plan_id_invalid"})
    try:
        return await project_plan_resource_requirements(
            db, plan_id=plan_id, task_key=task_key
        )
    except TaskResourceRequirementPlanNotFoundError:
        raise HTTPException(
            status_code=404, detail={"error": "execution_plan_not_found"}
        ) from None
    except TaskResourceRequirementTaskNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail={"error": str(exc) or "task_key_not_found"}
        ) from None


@router.get(
    "/plan-v2/from-order/{order_id}/resource-readiness",
    response_model=OperationalResourceReadinessResult,
)
async def operational_resource_readiness_by_order_id(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.plan_generate")),
) -> OperationalResourceReadinessResult:
    """F7C — read-only ORR allow-list ∩ machines registry resource readiness.

    Never assigns machine_code, never mutates operational_tasks, never touches
    sessions/assignment/pricing, never reopens the DEC-009 materialization gate.
    """
    logger.info(
        "GET /api/v1/execution/plan-v2/from-order/%s/resource-readiness", order_id
    )
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    return await build_operational_resource_readiness(db, order_id)
