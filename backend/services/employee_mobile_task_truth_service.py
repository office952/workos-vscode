"""Employee Mobile canonical task truth composition (MOBILE-T01)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from pydantic import ValidationError
from schemas.employee_mobile_task_truth import (
    EMPLOYEE_MOBILE_TASK_TRUTH_VERSION,
    EmployeeMobileTaskAssignment,
    EmployeeMobileTaskAuthority,
    EmployeeMobileTaskIdentity,
    EmployeeMobileTaskReadiness,
    EmployeeMobileTaskTruthCapabilities,
    EmployeeMobileTaskTruthResponse,
    EmployeeMobileTaskTruthSummary,
    EmployeeMobileTruthTask,
)
from schemas.execution_plan_v2_frozen_task_identity import FROZEN_TASK_IDENTITY_VERSION
from schemas.order_snapshot_v2 import OrderSnapshotV2
from services.execution_owner_decision_production_release_service import (
    evaluate_production_release,
)
from services.execution_plan_task_parser import (
    ParsedExecutionPlanTasks,
    parse_tasks_json_raw,
)
from services.execution_plan_v2_guard_service import order_has_v2_snapshot_fields
from services.material_procurement_status_service import (
    apply_procurement_statuses,
    load_material_procurement_statuses,
    material_items_by_task,
    split_reality_task_entries,
)
from services.material_planning_service import derive_material_planning_items
from services.operator_task_truth_service import (
    _build_identity,
    _sanitize_reasons,
)
from services.order_production_blueprint_service import (
    _extract_quote_input_from_snapshot,
    _parse_json,
    _parse_json_object,
    blueprint_status_bucket,
)
from services.task_readiness_service import (
    employee_safe_readiness_payload,
    evaluate_all_task_readiness,
)
from services.task_work_session_service import (
    derive_task_status_for_employee,
    derive_task_status_from_sessions,
    merge_reality_fields_for_task,
    sessions_for_task,
)
from services.volumetric_execution_dispatch import extract_order_snapshot_context
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class ResolvedOperationalPlan:
    tasks: list[dict[str, Any]]
    parsed: ParsedExecutionPlanTasks
    canonical_v2: bool
    legacy_mode: bool
    execution_plan_id: int | None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_employee_id(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _mobile_fail_closed(
    *,
    error: str,
    message: str,
    order_id: int,
    extra: dict[str, Any] | None = None,
) -> None:
    detail: dict[str, Any] = {
        "error": error,
        "message": message,
        "order_id": order_id,
        "contract_version": EMPLOYEE_MOBILE_TASK_TRUTH_VERSION,
    }
    if extra:
        detail.update(extra)
    raise HTTPException(status_code=422, detail=detail)


def _order_is_canonical_v2(order: Orders | None, parsed: ParsedExecutionPlanTasks) -> bool:
    if order is not None and order_has_v2_snapshot_fields(order):
        return True
    return parsed.format == "v2_envelope"


def resolve_operational_plan_tasks(
    tasks_json_raw: str | None,
    *,
    order_id: int,
    order: Orders | None,
    execution_plan_id: int | None = None,
    fail_closed: bool = False,
) -> ResolvedOperationalPlan:
    """Parse execution_plan.tasks_json via shared parser — V2 fail-closed when requested."""
    parsed = parse_tasks_json_raw(tasks_json_raw)
    canonical_v2 = _order_is_canonical_v2(order, parsed)

    if parsed.format == "invalid":
        if fail_closed and canonical_v2:
            _mobile_fail_closed(
                error="MOBILE_V2_TASK_ENVELOPE_CORRUPT",
                message="Execution plan tasks_json is corrupt for a canonical V2 order.",
                order_id=order_id,
                extra={"parse_errors": parsed.parse_errors},
            )
        return ResolvedOperationalPlan(
            tasks=[],
            parsed=parsed,
            canonical_v2=canonical_v2,
            legacy_mode=False,
            execution_plan_id=execution_plan_id,
        )

    if parsed.format == "v2_envelope":
        envelope = parsed.envelope or {}
        operational = list(parsed.operational_tasks)
        if not operational:
            planned = envelope.get("planned_tasks") or []
            materialized = bool(envelope.get("execution_tasks_created"))
            if fail_closed and (materialized or planned):
                _mobile_fail_closed(
                    error="MOBILE_V2_TASK_ENVELOPE_MISSING",
                    message="Canonical V2 plan is missing operational_tasks[] materialization.",
                    order_id=order_id,
                    extra={
                        "execution_tasks_created": materialized,
                        "planned_task_count": len(planned) if isinstance(planned, list) else 0,
                    },
                )
        return ResolvedOperationalPlan(
            tasks=operational,
            parsed=parsed,
            canonical_v2=True,
            legacy_mode=False,
            execution_plan_id=execution_plan_id,
        )

    if parsed.format == "legacy_list":
        return ResolvedOperationalPlan(
            tasks=list(parsed.operational_tasks),
            parsed=parsed,
            canonical_v2=False,
            legacy_mode=True,
            execution_plan_id=execution_plan_id,
        )

    if fail_closed and canonical_v2:
        _mobile_fail_closed(
            error="MOBILE_V2_TASK_CONTRACT_UNSUPPORTED",
            message="Unsupported execution plan tasks_json shape for canonical V2 order.",
            order_id=order_id,
        )
    return ResolvedOperationalPlan(
        tasks=[],
        parsed=parsed,
        canonical_v2=canonical_v2,
        legacy_mode=False,
        execution_plan_id=execution_plan_id,
    )


def _production_blocker_summary(blocked: bool, blocking_codes: list[str]) -> str | None:
    if not blocked:
        return None
    if not blocking_codes:
        return "Productie blocata — decizie manager necesara pe desktop."
    labels = ", ".join(blocking_codes[:3])
    suffix = "…" if len(blocking_codes) > 3 else ""
    return f"Productie blocata ({labels}{suffix}). Rezolvare pe desktop."




def _identity_to_mobile_fields(
    plan_task: dict[str, Any],
    *,
    order_info: dict[str, Any],
    canonical_v2: bool,
) -> EmployeeMobileTaskIdentity:
    identity = _build_identity(plan_task, order_info=order_info, canonical_v2=canonical_v2)
    logo_label = None
    if identity.logo_segment_key:
        logo_label = f"Logo segment ({identity.logo_segment_key})"
    return EmployeeMobileTaskIdentity(
        task_id=identity.task_id,
        deterministic_task_key=identity.deterministic_task_key,
        display_label=identity.display_label,
        component_label=identity.component_label,
        component_role=identity.component_role,
        operation_label=identity.source_operation_code or plan_task.get("process_type"),
        operation_code=identity.source_operation_code,
        logo_segment_label=logo_label,
        identity_source=identity.identity_source,  # type: ignore[arg-type]
        identity_classification=identity.identity_classification,
    )


def project_truth_task_to_mobile_dict(task: EmployeeMobileTruthTask) -> dict[str, Any]:
    """Flatten truth task into legacy Employee Mobile API dict + contract extensions."""
    ident = task.identity
    assign = task.assignment
    ready = task.readiness
    auth = task.authority
    row: dict[str, Any] = {
        "contract_version": EMPLOYEE_MOBILE_TASK_TRUTH_VERSION,
        "legacy_mode": auth.legacy_fallback_active,
        "task_id": ident.task_id,
        "order_id": task.order_id,
        "order_code": task.order_code,
        "title": ident.display_label,
        "description": "",
        "instructions": "",
        "status": task.status,
        "process_type": ident.operation_code or "",
        "process_id": ident.operation_code or "",
        "machine_type": "",
        "assigned_employee_id": assign.assigned_employee_id,
        "employee_id": assign.assigned_employee_id if assign.is_assigned_to_current_employee else None,
        "employee_name": assign.assigned_employee_name,
        "client": task.client_label,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "blocked_at": task.blocked_at,
        "blocked_reason": task.blocked_reason,
        "deterministic_task_key": ident.deterministic_task_key,
        "display_label": ident.display_label,
        "component_label": ident.component_label,
        "component_role": ident.component_role,
        "operation_label": ident.operation_label,
        "logo_segment_label": ident.logo_segment_label,
        "identity_source": ident.identity_source,
        "identity_classification": ident.identity_classification,
        "is_assigned_to_current_employee": assign.is_assigned_to_current_employee,
        "is_available_for_claim": assign.is_available_for_claim,
        "can_claim": assign.can_claim,
        "assignment_source": assign.assignment_source,
        "readiness_status": ready.readiness_status,
        "readiness_label": ready.readiness_label,
        "is_startable": ready.is_startable,
        "readiness_reasons": ready.readiness_reasons,
        "blocking_task_ids": ready.blocking_task_ids,
        "blocking_tasks": ready.blocking_tasks,
        "dependency_warning": ready.dependency_warning,
        "material_warning": ready.material_warning,
        "production_release_blocked": ready.production_release_blocked,
        "production_blocker_summary": ready.production_blocker_summary,
        "can_start": ready.can_start,
        "can_complete": ready.can_complete,
        "task_identity_version": auth.task_identity_version,
        "readiness_authority": auth.readiness_authority,
        "release_authority": auth.release_authority,
        "legacy_fallback_active": auth.legacy_fallback_active,
        "execution_source": auth.execution_source,
        "execution_plan_id": task.execution_plan_id,
        "plan_sequence": task.plan_sequence,
        "access_mode": task.access_mode,
        "preview_only": task.preview_only,
        "claimable": assign.can_claim,
    }
    return row


async def _load_order_context(
    db: AsyncSession,
    order_ids: list[int],
) -> tuple[dict[int, Orders], dict[int, dict[str, Any]]]:
    if not order_ids:
        return {}, {}
    placeholders = ", ".join(f":oid{i}" for i in range(len(order_ids)))
    params = {f"oid{i}": oid for i, oid in enumerate(order_ids)}
    order_sql = text(
        "SELECT o.id, o.code, o.status, o.client_name, o.quote_code, o.snapshot_line_items, "
        "o.quote_snapshot_v2_id, o.snapshot_v2_json, q.intake_code "
        f"FROM orders o LEFT JOIN quotes q ON q.id = o.quote_id WHERE o.id IN ({placeholders})"
    )
    orders_by_id: dict[int, Orders] = {}
    order_info_by_id: dict[int, dict[str, Any]] = {}
    for row in (await db.execute(order_sql, params)).mappings():
        order_id = int(row["id"])
        orders_by_id[order_id] = Orders(
            id=order_id,
            code=row.get("code"),
            client_name=row.get("client_name"),
            quote_code=row.get("quote_code"),
            status=row.get("status"),
            quote_snapshot_v2_id=row.get("quote_snapshot_v2_id"),
            snapshot_v2_json=row.get("snapshot_v2_json"),
            snapshot_line_items=row.get("snapshot_line_items"),
        )
        snapshot = _parse_json_object(row.get("snapshot_line_items"))
        order_info_by_id[order_id] = extract_order_snapshot_context(
            snapshot,
            client_name=str(row.get("client_name") or ""),
            quote_code=str(row.get("quote_code") or ""),
            intake_code=str(row.get("intake_code") or ""),
        )
        order_info_by_id[order_id]["code"] = row.get("code")
        order_info_by_id[order_id]["status"] = row.get("status")
    return orders_by_id, order_info_by_id


async def build_employee_mobile_task_truth(
    db: AsyncSession,
    *,
    employee_id: int,
    employee_name: str = "",
    category: str = "all",
) -> EmployeeMobileTaskTruthResponse:
    """Compose employee-safe task truth across all execution plans."""
    from services.employee_mobile_tasks_service import (
        _load_enriched_tasks,
        list_available_tasks,
        list_my_tasks,
    )

    if category == "assigned":
        mobile_rows = await list_my_tasks(db, employee_id)
    elif category == "available":
        mobile_rows = await list_available_tasks(db, employee_id)
    else:
        assigned = await list_my_tasks(db, employee_id)
        available = await list_available_tasks(db, employee_id)
        mobile_rows = assigned + available

    truth_tasks: list[EmployeeMobileTruthTask] = []
    for row in mobile_rows:
        truth_tasks.append(
            EmployeeMobileTruthTask(
                identity=EmployeeMobileTaskIdentity(
                    task_id=str(row.get("task_id") or ""),
                    deterministic_task_key=row.get("deterministic_task_key"),
                    display_label=str(row.get("display_label") or row.get("title") or ""),
                    component_label=row.get("component_label"),
                    component_role=row.get("component_role"),
                    operation_label=row.get("operation_label"),
                    operation_code=row.get("operation_label"),
                    logo_segment_label=row.get("logo_segment_label"),
                    identity_source=row.get("identity_source") or "not_proven",
                    identity_classification=row.get("identity_classification"),
                ),
                assignment=EmployeeMobileTaskAssignment(
                    assigned_employee_id=row.get("assigned_employee_id"),
                    assigned_employee_name=row.get("employee_name"),
                    is_assigned_to_current_employee=bool(row.get("is_assigned_to_current_employee")),
                    is_available_for_claim=bool(row.get("is_available_for_claim")),
                    can_claim=bool(row.get("can_claim") or row.get("claimable")),
                    assignment_source=str(row.get("assignment_source") or "execution_plan"),
                ),
                readiness=EmployeeMobileTaskReadiness(
                    is_startable=bool(row.get("is_startable")),
                    readiness_label=row.get("readiness_label"),
                    readiness_status=row.get("readiness_status"),
                    readiness_reasons=list(row.get("readiness_reasons") or []),
                    blocking_task_ids=list(row.get("blocking_task_ids") or []),
                    blocking_tasks=list(row.get("blocking_tasks") or []),
                    material_warning=row.get("material_warning"),
                    dependency_warning=row.get("dependency_warning"),
                    production_release_blocked=bool(row.get("production_release_blocked")),
                    production_blocker_summary=row.get("production_blocker_summary"),
                    can_start=bool(row.get("can_start")),
                    can_complete=bool(row.get("can_complete")),
                ),
                authority=EmployeeMobileTaskAuthority(
                    task_identity_version=row.get("task_identity_version"),
                    readiness_authority=row.get("readiness_authority") or "LEGACY_READ_MODEL_EXPLICIT",
                    release_authority=str(row.get("release_authority") or "execution_owner_decision_production_release_service"),
                    legacy_fallback_active=bool(row.get("legacy_fallback_active")),
                    execution_source=str(row.get("execution_source") or "execution_plan_v2_operational_tasks"),
                ),
                order_id=int(row["order_id"]),
                order_code=str(row.get("order_code") or ""),
                client_label=str(row.get("client") or ""),
                execution_plan_id=row.get("execution_plan_id"),
                plan_sequence=row.get("plan_sequence"),
                status=str(row.get("status") or "assigned"),
                started_at=row.get("started_at"),
                completed_at=row.get("completed_at"),
                blocked_at=row.get("blocked_at"),
                blocked_reason=row.get("blocked_reason"),
                access_mode=row.get("access_mode"),
                preview_only=bool(row.get("preview_only")),
            )
        )

    assigned_count = sum(1 for t in truth_tasks if t.assignment.is_assigned_to_current_employee)
    available_count = sum(1 for t in truth_tasks if t.assignment.is_available_for_claim)
    return EmployeeMobileTaskTruthResponse(
        contract_version=EMPLOYEE_MOBILE_TASK_TRUTH_VERSION,
        employee_id=employee_id,
        employee_display_name=employee_name,
        generated_at=_utc_now_iso(),
        legacy_mode=any(t.authority.legacy_fallback_active for t in truth_tasks),
        tasks=truth_tasks,
        summary=EmployeeMobileTaskTruthSummary(
            total_tasks=len(truth_tasks),
            assigned_count=assigned_count,
            available_count=available_count,
            startable_count=sum(1 for t in truth_tasks if t.readiness.is_startable),
            blocked_count=sum(1 for t in truth_tasks if t.readiness.production_release_blocked),
        ),
        capabilities=EmployeeMobileTaskTruthCapabilities(),
    )
