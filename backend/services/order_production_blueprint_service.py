"""Read-only production blueprint — plan + reality merged for operator/admin visibility."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from models.execution_plan import ExecutionPlan
from models.auth import User
from models.task_clarification_request import TaskClarificationRequest
from models.inventory_materials import Inventory_materials
from services.employee_mobile_production_documents_service import load_intake_work_files_for_order
from services.employee_mobile_tasks_service import (
    _normalize_employee_id,
    _normalize_task_documents,
)
from services.task_work_session_service import (
    aggregate_task_work_metrics,
    derive_task_status_from_sessions,
    merge_reality_fields_for_task,
)
from services.production_document_handoff_service import merge_production_documents
from services.material_planning_service import (
    derive_material_planning_items,
    summarize_material_planning,
)
from services.material_procurement_status_service import (
    apply_procurement_statuses,
    derive_production_planning_summary,
    derive_procurement_summary,
    load_material_procurement_statuses,
    material_items_by_task,
    split_reality_task_entries,
)
from services.execution_plan_operational_readiness_service import (
    evaluate_execution_plan_operational_readiness,
    readiness_result_to_api_fields,
)
from services.execution_plan_task_parser import operational_tasks_only
from services.task_readiness_service import evaluate_all_task_readiness
from services.preparation_domain_service import (
    derive_preparation_domain,
    group_tasks_by_preparation_domain,
)
from services.volumetric_execution_dispatch import (
    extract_order_snapshot_context,
    resolve_execution_task_display_name,
)
from services.volumetric_quote_input_policy import (
    MAT_MOUNTING_TEMPLATE_FOREX,
    MAT_MOUNTING_TEMPLATE_PAPER,
    normalize_mounting_template_material_type,
    resolve_mounting_template_material_code,
)
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

OPEN_CLARIFICATION_STATUS = "open"

STATUS_DISPLAY: Dict[str, str] = {
    "done": "Finalizat",
    "blocked": "Blocat",
    "in_progress": "În lucru",
    "todo": "De făcut",
    "unassigned": "Neatribuit",
}


def _parse_json(val: Any) -> list:
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _parse_json_object(val: Any) -> dict:
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _extract_quote_input_from_snapshot(snapshot: dict) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        return {}
    direct = snapshot.get("quote_input")
    if isinstance(direct, dict):
        return direct
    quote_snapshot = snapshot.get("quote_snapshot")
    if isinstance(quote_snapshot, dict):
        nested = quote_snapshot.get("quote_input")
        if isinstance(nested, dict):
            return nested
    return {}


async def _load_material_registry_costs(
    db: AsyncSession,
    codes: List[str],
) -> Dict[str, Dict[str, Any]]:
    if not codes:
        return {}
    rows = (
        await db.execute(
            select(Inventory_materials).where(Inventory_materials.code.in_(codes))
        )
    ).scalars().all()
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        code = str(row.code or "").strip()
        if not code:
            continue
        out[code] = {
            "code": code,
            "name": str(row.name or code),
            "unit": str(row.unit or ""),
            "unit_cost": float(row.unit_cost) if row.unit_cost is not None else None,
            "currency": str(row.currency or "EUR"),
        }
    return out


def _build_mounting_template_summary(
    quote_input: dict[str, Any],
    registry: Dict[str, Dict[str, Any]],
) -> dict[str, Any]:
    material_type = normalize_mounting_template_material_type(quote_input)
    material_code = resolve_mounting_template_material_code(quote_input)
    area_raw = quote_input.get("mounting_template_area_m2")
    area_m2: Optional[float]
    try:
        area_m2 = float(area_raw) if area_raw not in (None, "") else None
    except (TypeError, ValueError):
        area_m2 = None

    registry_row = registry.get(material_code or "") if material_code else None
    rate_display: Optional[str] = None
    if registry_row and registry_row.get("unit_cost") is not None:
        unit = str(registry_row.get("unit") or "mp")
        currency = str(registry_row.get("currency") or "EUR")
        rate_display = f"{registry_row['unit_cost']} {currency}/{unit}"

    return {
        "material_type": material_type,
        "material_code": material_code,
        "material_name": (registry_row or {}).get("name"),
        "unit": (registry_row or {}).get("unit") or "mp",
        "registry_rate_display": rate_display,
        "area_m2": area_m2,
        "forex_material_code": MAT_MOUNTING_TEMPLATE_FOREX,
        "paper_material_code": MAT_MOUNTING_TEMPLATE_PAPER,
    }


def blueprint_status_bucket(
    derived_status: str,
    assigned_employee_id: Optional[int],
) -> Tuple[str, str]:
    if derived_status == "done":
        return "done", STATUS_DISPLAY["done"]
    if derived_status == "blocked":
        return "blocked", STATUS_DISPLAY["blocked"]
    if derived_status in ("in_progress", "paused"):
        return "in_progress", STATUS_DISPLAY["in_progress"]
    if assigned_employee_id is None:
        return "unassigned", STATUS_DISPLAY["unassigned"]
    return "todo", STATUS_DISPLAY["todo"]


def _progress_percent(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return round((done / total) * 100)


async def get_order_production_blueprint(db: AsyncSession, order_id: int) -> dict[str, Any]:
    """Build read-only blueprint payload for a single order. Does not write to DB."""
    if not isinstance(order_id, int) or order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})

    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "execution_plan_not_found"})

    reality_sql = text(
        "SELECT tasks_json FROM execution_reality WHERE order_id = :oid LIMIT 1"
    )
    reality_row = (await db.execute(reality_sql, {"oid": order_id})).mappings().first()
    raw_reality_tasks = _parse_json(reality_row.get("tasks_json") if reality_row else "[]")
    reality_tasks, _procurement_meta = split_reality_task_entries(raw_reality_tasks)
    reality_sessions_by_task: Dict[str, List[dict]] = {}
    for rt in reality_tasks:
        if not isinstance(rt, dict):
            continue
        task_key = str(rt.get("task_id") or "")
        if not task_key:
            continue
        reality_sessions_by_task.setdefault(task_key, []).append(rt)

    order_sql = text(
        "SELECT o.id, o.code, o.status, o.client_name, o.quote_code, o.snapshot_line_items, "
        "q.intake_code "
        "FROM orders o "
        "LEFT JOIN quotes q ON q.id = o.quote_id "
        "WHERE o.id = :oid LIMIT 1"
    )
    order_row = (await db.execute(order_sql, {"oid": order_id})).mappings().first()
    order_code = str(plan.order_code or (order_row.get("code") if order_row else "") or "")
    order_label = f"Comandă #{order_id}"
    if order_code:
        order_label = f"{order_code} (#{order_id})"

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

    quote_input = _extract_quote_input_from_snapshot(snapshot_dict)
    material_registry = await _load_material_registry_costs(
        db,
        [MAT_MOUNTING_TEMPLATE_FOREX, MAT_MOUNTING_TEMPLATE_PAPER],
    )
    mounting_template = _build_mounting_template_summary(quote_input, material_registry)

    prepared_by_user_id = str(getattr(plan, "prepared_by_user_id", None) or "").strip() or None
    prepared_by_user_name: Optional[str] = None
    if prepared_by_user_id:
        user_row = await db.get(User, prepared_by_user_id)
        if user_row and user_row.name:
            prepared_by_user_name = str(user_row.name).strip() or None

    employees_sql = text("SELECT id, name FROM employees")
    employee_names: Dict[int, str] = {
        int(row[0]): str(row[1])
        for row in (await db.execute(employees_sql)).all()
        if row[0] is not None and row[1]
    }

    open_clarifications = (
        await db.execute(
            select(TaskClarificationRequest).where(
                TaskClarificationRequest.order_id == order_id,
                TaskClarificationRequest.status == OPEN_CLARIFICATION_STATUS,
            )
        )
    ).scalars().all()
    open_clarification_tasks = {row.task_id for row in open_clarifications}

    order_work_files = await load_intake_work_files_for_order(
        db,
        order_id=order_id,
        intake_code=str(order_info.get("intake_code") or ""),
    )

    plan_tasks = operational_tasks_only(plan.tasks_json)
    product_template = str(order_info.get("product_template") or "").strip() or None
    procurement_statuses = await load_material_procurement_statuses(db, order_id)
    material_planning_items = apply_procurement_statuses(
        derive_material_planning_items(plan_tasks, product_context=product_template),
        procurement_statuses,
    )
    material_planning_by_task = material_items_by_task(material_planning_items)
    material_planning_summary = summarize_material_planning(material_planning_items)
    procurement_summary = derive_procurement_summary(material_planning_items)
    readiness_by_id = evaluate_all_task_readiness(
        plan_tasks,
        raw_reality_tasks,
        material_by_task=material_planning_by_task,
        quote_input=quote_input,
    )
    production_planning_summary = derive_production_planning_summary(
        readiness_by_id,
        material_planning_items,
    )
    blueprint_tasks: List[dict[str, Any]] = []
    summary = {
        "total_tasks": 0,
        "done": 0,
        "in_progress": 0,
        "blocked": 0,
        "todo": 0,
        "unassigned": 0,
        "progress_percent": 0,
    }
    active_workers: List[dict[str, Any]] = []
    next_tasks: List[dict[str, str]] = []

    for plan_task in plan_tasks:
        if not isinstance(plan_task, dict):
            continue
        task_id = str(plan_task.get("task_id") or "")
        if not task_id:
            continue

        task_sessions = reality_sessions_by_task.get(task_id, [])
        rt = merge_reality_fields_for_task(task_sessions)
        derived = derive_task_status_from_sessions(task_sessions)
        assigned_employee_id = _normalize_employee_id(plan_task.get("assigned_employee_id"))
        status_key, status_display = blueprint_status_bucket(derived, assigned_employee_id)

        summary["total_tasks"] += 1
        summary[status_key] = summary.get(status_key, 0) + 1

        process_id = str(plan_task.get("process_id") or "")
        process_type = str(plan_task.get("process_type") or "")
        display_name = plan_task.get("display_name") or plan_task.get("name") or ""
        if not display_name or ":" in str(display_name):
            display_name = resolve_execution_task_display_name(
                process_id=process_id or str(display_name).split(":")[-1],
                process_type=process_type,
                product_id=order_info.get("product_template") or None,
            )

        instructions = str(plan_task.get("instructions") or "").strip()
        task_documents = _normalize_task_documents(
            plan_task.get("documents"),
            order_id=order_id,
        )
        documents = merge_production_documents(task_documents, order_work_files)

        work_metrics = aggregate_task_work_metrics(task_sessions, employee_names=employee_names)
        readiness = readiness_by_id.get(task_id, {})

        active_worker_id: Optional[int] = None
        active_worker_name: Optional[str] = None
        if work_metrics["active_workers"]:
            primary_worker = next(
                (worker for worker in work_metrics["active_workers"] if worker.get("role") == "primary"),
                work_metrics["active_workers"][0],
            )
            active_worker_id = _normalize_employee_id(primary_worker.get("employee_id"))
            active_worker_name = str(primary_worker.get("employee_name") or "").strip() or None
            for worker in work_metrics["active_workers"]:
                active_workers.append(
                    {
                        "employee_id": worker.get("employee_id"),
                        "employee_name": worker.get("employee_name") or "",
                        "role": worker.get("role"),
                        "session_type": worker.get("session_type"),
                        "task_id": task_id,
                        "task_name": str(display_name),
                        "started_at": worker.get("started_at"),
                    }
                )

        assigned_name = (
            employee_names.get(assigned_employee_id) if assigned_employee_id else None
        )

        if status_key in ("todo", "unassigned"):
            next_tasks.append({"task_id": task_id, "name": str(display_name)})

        blueprint_tasks.append(
            {
                "task_id": task_id,
                "name": str(display_name),
                "status": status_key,
                "status_display": status_display,
                "process_type": process_type,
                "process_id": process_id,
                "machine_type": str(plan_task.get("machine_type") or ""),
                "preparation_domain": derive_preparation_domain(plan_task),
                "assigned_employee_id": assigned_employee_id,
                "assigned_employee_name": assigned_name,
                "active_worker_id": active_worker_id,
                "active_worker_name": active_worker_name,
                "started_at": rt.get("started_at"),
                "completed_at": rt.get("ended_at"),
                "blocked_at": rt.get("blocked_at"),
                "block_reason": rt.get("block_reason") or rt.get("blocked_reason"),
                "documents_count": len(documents),
                "has_instructions": bool(instructions),
                "has_open_clarification": task_id in open_clarification_tasks,
                "active_workers": work_metrics["active_workers"],
                "participants_count": work_metrics["participants_count"],
                "work_sessions_count": work_metrics["work_sessions_count"],
                "total_logged_minutes": work_metrics["total_logged_minutes"],
                "last_worked_at": work_metrics["last_worked_at"],
                "readiness_status": readiness.get("readiness_status"),
                "readiness_label": readiness.get("readiness_label"),
                "is_startable": bool(readiness.get("is_startable")),
                "readiness_reasons": readiness.get("readiness_reasons") or [],
                "blocking_reasons": readiness.get("blocking_reasons") or [],
                "blocking_tasks": readiness.get("blocking_tasks") or [],
                "blocking_task_ids": readiness.get("blocking_task_ids") or [],
                "dependency_warning": readiness.get("dependency_warning"),
                "material_warning": readiness.get("material_warning"),
                "blocking_materials": readiness.get("blocking_materials") or [],
                "material_planning_items": material_planning_by_task.get(task_id, []),
            }
        )

    summary["progress_percent"] = _progress_percent(summary["done"], summary["total_tasks"])

    preparation_groups = group_tasks_by_preparation_domain(blueprint_tasks)
    cnc_tasks = preparation_groups.get("cnc") or []

    return {
        "order_id": order_id,
        "order_label": order_label,
        "order_code": order_code,
        "product_template": product_template,
        **readiness_result_to_api_fields(evaluate_execution_plan_operational_readiness(plan)),
        "prepared_by_user_id": prepared_by_user_id,
        "prepared_by_user_name": prepared_by_user_name,
        "preparation_ownership": {
            "instrumentation": {
                "prepared_by_user_id": prepared_by_user_id,
                "prepared_by_user_name": prepared_by_user_name,
                "source_field": "execution_plan.prepared_by_user_id",
            },
            "cnc": {
                "registry_operation_hint": "cnc_cutting",
                "task_count": len(cnc_tasks),
            },
            "mounting_template": mounting_template,
        },
        "preparation_groups": {
            key: [
                {
                    "task_id": task.get("task_id"),
                    "name": task.get("name"),
                    "status": task.get("status"),
                    "status_display": task.get("status_display"),
                    "preparation_domain": task.get("preparation_domain"),
                    "assigned_employee_id": task.get("assigned_employee_id"),
                    "assigned_employee_name": task.get("assigned_employee_name"),
                    "process_id": task.get("process_id"),
                    "machine_type": task.get("machine_type"),
                    "documents_count": task.get("documents_count"),
                    "has_instructions": task.get("has_instructions"),
                }
                for task in tasks_in_group
            ]
            for key, tasks_in_group in preparation_groups.items()
        },
        "material_planning_summary": material_planning_summary,
        "procurement_summary": procurement_summary,
        "production_planning_summary": production_planning_summary,
        "material_procurement_statuses": procurement_statuses,
        "summary": summary,
        "active_workers": active_workers,
        "next_tasks": next_tasks[:10],
        "tasks": blueprint_tasks,
    }
