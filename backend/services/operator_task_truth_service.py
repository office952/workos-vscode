"""Canonical operator task truth composition service (W6-T01)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from pydantic import ValidationError
from schemas.auth import UserResponse
from schemas.execution_owner_decision_release import ProductionReleaseEvaluation, ReleaseStatus
from schemas.execution_plan_v2_frozen_task_identity import (
    FROZEN_TASK_IDENTITY_VERSION,
    FrozenTaskIdentity,
)
from schemas.operator_task_truth import (
    OPERATOR_TASK_TRUTH_VERSION,
    InternalCostSummary,
    OperatorTaskTruthResponse,
    OperatorTaskTruthTask,
    OwnerDecisionSummaryItem,
    RoleCapabilities,
    TaskAuthorityTruth,
    TaskIdentityTruth,
    TaskRuntimeTruth,
)
from schemas.order_snapshot_v2 import OrderSnapshotV2
from services.execution_owner_decision_production_release_service import (
    OWNER_DECISION_RESOLUTIONS_KEY,
    RESOLVE_ALLOWED_ROLES,
    _ensure_resolution_state,
    _operator_label,
    _parse_readiness_snapshot,
    classify_frozen_decision_code,
    evaluate_production_release,
    load_frozen_owner_decisions,
)
from services.execution_plan_v2_guard_service import order_has_v2_snapshot_fields
from services.execution_plan_task_parser import operational_tasks_only
from services.material_planning_service import derive_material_planning_items
from services.material_procurement_status_service import (
    apply_procurement_statuses,
    load_material_procurement_statuses,
    material_items_by_task,
    split_reality_task_entries,
)
from services.order_production_blueprint_service import (
    _extract_quote_input_from_snapshot,
    _parse_json,
    _parse_json_object,
    blueprint_status_bucket,
)
from services.task_readiness_service import evaluate_all_task_readiness
from services.task_work_session_service import (
    derive_task_status_from_sessions,
    merge_reality_fields_for_task,
)
from services.volumetric_execution_dispatch import (
    extract_order_snapshot_context,
    resolve_execution_task_display_name,
)
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

COMPONENT_ROLE_LABELS: dict[str, str] = {
    "root_product": "Produs principal",
    "mounting_panel": "Panou montaj",
    "premount_structure": "Structură premontaj",
    "linked_segment": "Segment legat",
}

MANAGER_ROLES = frozenset({"admin", "manager"})


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


def _resolve_role(user: UserResponse | None) -> str:
    role = str(getattr(user, "role", None) or "").strip().lower()
    if role in MANAGER_ROLES:
        return role
    if role == "operator":
        return "operator"
    return role or "viewer"


def _role_capabilities(role: str) -> RoleCapabilities:
    is_manager = role in MANAGER_ROLES
    return RoleCapabilities(
        can_resolve_owner_decisions=is_manager,
        can_view_internal_cost=is_manager,
        can_view_owner_decision_notes=is_manager,
    )


def _fail_closed_v2(*, error: str, message: str, order_id: int) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error": error,
            "message": message,
            "order_id": order_id,
            "contract_version": OPERATOR_TASK_TRUTH_VERSION,
            "readiness_authority": "BLOCKED_MISSING_ORDER_SNAPSHOT_V2",
        },
    )


def _parse_v2_snapshot(order: Orders) -> OrderSnapshotV2 | None:
    raw = getattr(order, "snapshot_v2_json", None)
    if raw is None:
        return None
    if isinstance(raw, str) and not raw.strip():
        return None
    try:
        if isinstance(raw, str):
            return OrderSnapshotV2.model_validate_json(raw)
        return OrderSnapshotV2.model_validate(raw)
    except (ValidationError, ValueError, TypeError):
        return None


def _component_label(role: str | None, segment_key: str | None) -> str | None:
    if segment_key:
        return f"Logo segment ({segment_key})"
    if role and role in COMPONENT_ROLE_LABELS:
        return COMPONENT_ROLE_LABELS[role]
    if role:
        return role.replace("_", " ").title()
    return None


def _parse_frozen_identity(raw: Any) -> FrozenTaskIdentity | None:
    if raw is None:
        return None
    if isinstance(raw, FrozenTaskIdentity):
        return raw
    if isinstance(raw, dict):
        try:
            return FrozenTaskIdentity.model_validate(raw)
        except ValidationError:
            return None
    return None


def _build_identity(
    plan_task: dict[str, Any],
    *,
    order_info: dict[str, Any],
    canonical_v2: bool,
) -> TaskIdentityTruth:
    task_id = str(plan_task.get("task_id") or "")
    frozen = _parse_frozen_identity(plan_task.get("frozen_identity"))

    process_id = str(plan_task.get("process_id") or "")
    process_type = str(plan_task.get("process_type") or "")
    display_name = plan_task.get("display_name") or plan_task.get("name") or ""
    if not display_name or ":" in str(display_name):
        display_name = resolve_execution_task_display_name(
            process_id=process_id or str(display_name).split(":")[-1],
            process_type=process_type,
            product_id=order_info.get("product_template") or None,
        )

    if frozen is not None and canonical_v2:
        role = frozen.source_component_role
        segment = frozen.source_segment_key
        return TaskIdentityTruth(
            task_id=task_id,
            deterministic_task_key=frozen.deterministic_task_key,
            display_label=str(display_name),
            identity_classification=frozen.identity_classification,
            source_graph_node_id=frozen.source_graph_node_id,
            source_component_instance_id=frozen.source_component_instance_id,
            component_role=role,
            component_label=_component_label(role, segment),
            component_template_code=frozen.source_template_code,
            source_operation_code=frozen.source_operation_code,
            source_task_rule_code=frozen.source_task_rule_code,
            parent_graph_node_id=frozen.parent_graph_node_id,
            task_scope=frozen.operation_scope,
            logo_segment_key=segment,
            identity_source="frozen_task_identity/v1",
        )

    return TaskIdentityTruth(
        task_id=task_id,
        deterministic_task_key=str(plan_task.get("task_key") or task_id) or task_id,
        display_label=str(display_name),
        identity_classification="LEGACY_NAME_BASED_IDENTITY" if not canonical_v2 else "NOT_PROVEN",
        component_role=None,
        component_label=None,
        component_template_code=order_info.get("product_template"),
        source_operation_code=process_type or None,
        source_task_rule_code=process_id or None,
        identity_source="legacy_plan_task",
    )


def _sanitize_reasons(reasons: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for reason in reasons or []:
        if not isinstance(reason, dict):
            continue
        out.append(
            {
                "code": reason.get("code"),
                "label": reason.get("label"),
                "message": reason.get("message"),
                "task_id": reason.get("task_id"),
                "depends_on_task_id": reason.get("depends_on_task_id"),
                "task_name": reason.get("task_name"),
                "missing_item": reason.get("missing_item"),
                "blocking": reason.get("blocking"),
                "responsible_domain": reason.get("responsible_domain"),
            }
        )
    return out


def _owner_decisions_summary(
    order: Orders,
    *,
    role: str,
) -> list[OwnerDecisionSummaryItem]:
    frozen_decisions = load_frozen_owner_decisions(order)
    if not frozen_decisions:
        return []

    readiness = _parse_readiness_snapshot(getattr(order, "readiness_snapshot", None))
    resolution_state = _ensure_resolution_state(readiness, frozen_decisions)
    decisions_map = resolution_state.get(OWNER_DECISION_RESOLUTIONS_KEY, {}).get(
        "decisions", {}
    )
    can_resolve = role in RESOLVE_ALLOWED_ROLES

    items: list[OwnerDecisionSummaryItem] = []
    for decision in frozen_decisions:
        code = str(decision.code or "").strip()
        if not code:
            continue
        classification = classify_frozen_decision_code(code)
        entry = decisions_map.get(code) if isinstance(decisions_map, dict) else None
        if not isinstance(entry, dict):
            entry = {}

        operational_status = str(entry.get("operational_status") or "unresolved")
        note = str(entry.get("resolution_note") or "").strip()
        items.append(
            OwnerDecisionSummaryItem(
                code=code,
                label=_operator_label(decision),
                category=classification,
                blocking=classification == "production_blocking",
                operational_status=operational_status,
                required_action=str(entry.get("required_action") or "")
                or ("resolve_owner_decision" if classification == "production_blocking" else None),
                acknowledgement_sufficient=bool(entry.get("acknowledgement_sufficient", False)),
                requires_resolution=bool(entry.get("requires_resolution", classification == "production_blocking")),
                can_resolve=can_resolve and classification == "production_blocking",
                resolved_at=entry.get("resolved_at"),
                resolved_by_user_name=entry.get("resolved_by_user_name"),
                has_resolution_note=bool(note) and role in RESOLVE_ALLOWED_ROLES,
            )
        )
    return items


def _internal_cost_summary(
    snapshot: OrderSnapshotV2 | None,
    *,
    role: str,
    release_status: ReleaseStatus,
) -> InternalCostSummary:
    if role not in MANAGER_ROLES or snapshot is None:
        return InternalCostSummary(visibility="restricted")

    eic = snapshot.estimated_internal_cost_snapshot
    return InternalCostSummary(
        visibility="available",
        status=str(eic.status) if eic else None,
        estimated_total_internal_cost=(
            float(eic.estimated_total_internal_cost) if eic and eic.estimated_total_internal_cost is not None else None
        ),
        accepted_commercial_total=float(snapshot.accepted_commercial_total)
        if snapshot.accepted_commercial_total is not None
        else None,
        execution_blocked=release_status != "RELEASE_ALLOWED",
    )


def _blocking_owner_codes(evaluation: ProductionReleaseEvaluation) -> list[str]:
    return [str(item.code) for item in evaluation.blockers if item.code]


async def build_operator_task_truth(
    db: AsyncSession,
    order_id: int,
    *,
    current_user: UserResponse | None = None,
) -> OperatorTaskTruthResponse:
    if not isinstance(order_id, int) or order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})

    order = (
        await db.execute(select(Orders).where(Orders.id == order_id))
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})

    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "execution_plan_not_found"})

    role = _resolve_role(current_user)
    capabilities = _role_capabilities(role)

    is_v2 = order_has_v2_snapshot_fields(order)
    legacy_order = not is_v2
    readiness_authority: str
    task_identity_version: str | None = None
    v2_snapshot: OrderSnapshotV2 | None = None

    if is_v2:
        v2_snapshot = _parse_v2_snapshot(order)
        if v2_snapshot is None:
            _fail_closed_v2(
                error="ORDER_SNAPSHOT_V2_CORRUPT",
                message="V2 order snapshot_v2_json is missing or corrupt.",
                order_id=order_id,
            )
        readiness_authority = "FROZEN_ORDER_SNAPSHOT_V2"
        task_identity_version = FROZEN_TASK_IDENTITY_VERSION
    else:
        readiness_authority = "LEGACY_READ_MODEL_EXPLICIT"

    release_eval = evaluate_production_release(order)
    production_release_blocked = release_eval.release_status != "RELEASE_ALLOWED"
    blocking_owner_codes = _blocking_owner_codes(release_eval)

    order_sql = text(
        "SELECT o.code, o.client_name, o.quote_code, o.snapshot_line_items, q.intake_code "
        "FROM orders o LEFT JOIN quotes q ON q.id = o.quote_id WHERE o.id = :oid LIMIT 1"
    )
    order_row = (await db.execute(order_sql, {"oid": order_id})).mappings().first()
    order_code = str(plan.order_code or (order_row.get("code") if order_row else "") or "") or None

    order_info: dict[str, Any] = {}
    snapshot_dict: dict[str, Any] = {}
    if order_row:
        snapshot_dict = _parse_json_object(order_row.get("snapshot_line_items"))
        order_info = extract_order_snapshot_context(
            snapshot_dict,
            client_name=str(order_row.get("client_name") or ""),
            quote_code=str(order_row.get("quote_code") or ""),
            intake_code=str(order_row.get("intake_code") or ""),
        )

    reality_sql = text(
        "SELECT tasks_json FROM execution_reality WHERE order_id = :oid LIMIT 1"
    )
    reality_row = (await db.execute(reality_sql, {"oid": order_id})).mappings().first()
    raw_reality_tasks = _parse_json(reality_row.get("tasks_json") if reality_row else "[]")
    reality_tasks, _procurement_meta = split_reality_task_entries(raw_reality_tasks)

    employees_sql = text("SELECT id, name FROM employees")
    employee_names: dict[int, str] = {
        int(row[0]): str(row[1])
        for row in (await db.execute(employees_sql)).all()
        if row[0] is not None and row[1]
    }

    plan_tasks = operational_tasks_only(plan.tasks_json)
    product_template = str(order_info.get("product_template") or "").strip() or None
    quote_input = _extract_quote_input_from_snapshot(snapshot_dict)
    procurement_statuses = await load_material_procurement_statuses(db, order_id)
    material_planning_items = apply_procurement_statuses(
        derive_material_planning_items(plan_tasks, product_context=product_template),
        procurement_statuses,
    )
    material_by_task = material_items_by_task(material_planning_items)
    readiness_by_id = evaluate_all_task_readiness(
        plan_tasks,
        raw_reality_tasks,
        material_by_task=material_by_task,
        quote_input=quote_input,
    )

    reality_sessions_by_task: dict[str, list[dict]] = {}
    for rt in reality_tasks:
        if isinstance(rt, dict):
            key = str(rt.get("task_id") or "")
            if key:
                reality_sessions_by_task.setdefault(key, []).append(rt)

    truth_tasks: list[OperatorTaskTruthTask] = []
    for plan_task in plan_tasks:
        if not isinstance(plan_task, dict):
            continue
        task_id = str(plan_task.get("task_id") or "")
        if not task_id:
            continue

        task_sessions = reality_sessions_by_task.get(task_id, [])
        rt = merge_reality_fields_for_task(task_sessions)
        derived_status = derive_task_status_from_sessions(task_sessions)
        assigned_employee_id = _normalize_employee_id(plan_task.get("assigned_employee_id"))
        status_key, _status_display = blueprint_status_bucket(derived_status, assigned_employee_id)

        readiness = readiness_by_id.get(task_id, {})
        operational_startable = bool(readiness.get("is_startable"))
        is_startable = operational_startable and not production_release_blocked
        is_completeable = derived_status == "in_progress"
        is_blocked = derived_status == "blocked" or (
            not is_startable and derived_status in ("assigned", "created")
        )

        identity = _build_identity(
            plan_task,
            order_info=order_info,
            canonical_v2=is_v2,
        )
        runtime = TaskRuntimeTruth(
            current_status=status_key,
            assigned_employee_id=assigned_employee_id,
            assigned_employee_name=employee_names.get(assigned_employee_id)
            if assigned_employee_id
            else None,
            is_startable=is_startable,
            is_completeable=is_completeable,
            is_blocked=is_blocked,
            readiness_status=readiness.get("readiness_status"),
            readiness_label=readiness.get("readiness_label"),
            readiness_reasons=_sanitize_reasons(readiness.get("readiness_reasons") or []),
            blocking_reasons=_sanitize_reasons(readiness.get("blocking_reasons") or []),
            blocking_task_ids=list(readiness.get("blocking_task_ids") or []),
            blocking_tasks=list(readiness.get("blocking_tasks") or []),
            production_release_blocked=production_release_blocked,
            production_release_status=release_eval.release_status,
            blocking_owner_decision_codes=blocking_owner_codes if production_release_blocked else [],
            last_started_at=rt.get("started_at"),
            last_ended_at=rt.get("ended_at"),
        )
        authority = TaskAuthorityTruth(
            frozen_source=FROZEN_TASK_IDENTITY_VERSION if identity.identity_source == "frozen_task_identity/v1" else None,
            legacy_fallback_active=identity.identity_source == "legacy_plan_task",
        )
        truth_tasks.append(
            OperatorTaskTruthTask(
                identity=identity,
                runtime=runtime,
                authority=authority,
            )
        )

    return OperatorTaskTruthResponse(
        contract_version=OPERATOR_TASK_TRUTH_VERSION,
        order_id=order_id,
        order_code=order_code,
        execution_plan_id=int(plan.id) if plan.id is not None else None,
        order_snapshot_v2_id=getattr(order, "quote_snapshot_v2_id", None),
        quote_snapshot_v2_id=(
            v2_snapshot.quote_snapshot_v2_id if v2_snapshot is not None else None
        ),
        task_identity_version=task_identity_version,
        readiness_authority=readiness_authority,  # type: ignore[arg-type]
        production_release_policy=release_eval.policy,
        production_release_status=release_eval.release_status,
        production_release_blocked=production_release_blocked,
        owner_decisions_summary=_owner_decisions_summary(order, role=role),
        role_capabilities=capabilities,
        internal_cost_summary=_internal_cost_summary(
            v2_snapshot,
            role=role,
            release_status=release_eval.release_status,
        ),
        tasks=truth_tasks,
        generated_at=_utc_now_iso(),
        legacy_order=legacy_order,
    )
