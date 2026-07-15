"""Employee Mobile — self-only execution task list and actions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from models.orders import Orders
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.employee_mobile_production_documents_service import load_intake_work_files_for_order
from services.production_document_handoff_service import merge_production_documents
from services.execution_reality_service import ExecutionRealityService, RealityInputError
from services.task_work_session_service import (
    active_session_for_employee,
    aggregate_task_work_metrics,
    derive_task_status_for_employee,
    derive_task_status_from_sessions,
    employee_safe_helper_count,
    is_session_active,
    merge_reality_fields_for_task,
    sessions_for_task,
)
from services.preparation_domain_service import derive_preparation_domain
from services.operational_registry_service import OperationalRegistryService
from services.execution_task_assignment_service import assign_plan_task, clear_plan_task_assignment
from services.operator_employee_guard import OperatorEmployeeGuard
from services.material_procurement_status_service import build_procurement_enriched_context
from services.task_readiness_service import (
    build_readiness_context,
    employee_safe_readiness_payload,
    evaluate_all_task_readiness,
    evaluate_task_readiness,
)
from services.execution_owner_decision_production_release_service import (
    evaluate_production_release,
)
from services.execution_plan_v2_guard_service import order_has_v2_snapshot_fields
from services.volumetric_execution_dispatch import extract_order_snapshot_context

logger = logging.getLogger(__name__)

_ORDER_SNAPSHOT_READINESS_BLOCK_ERRORS = frozenset(
    {"ORDER_SNAPSHOT_V2_CORRUPT", "ORDER_SNAPSHOT_V2_MISSING"}
)


def _planning_readiness_order_block_detail(exc: HTTPException) -> Optional[dict[str, Any]]:
    """Return structured fail-closed detail when snapshot readiness blocks an order."""
    if exc.status_code != 422:
        return None
    detail = exc.detail
    if not isinstance(detail, dict):
        return None
    if detail.get("error") not in _ORDER_SNAPSHOT_READINESS_BLOCK_ERRORS:
        return None
    return detail


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


def derive_task_status(reality_task: dict) -> str:
    if isinstance(reality_task, list):
        return derive_task_status_from_sessions(reality_task)
    if not reality_task:
        return "assigned"
    return derive_task_status_from_sessions([reality_task])


def _normalize_employee_id(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _normalize_task_documents(
    raw: Any,
    *,
    order_id: int | None = None,
    default_source: str = "task",
) -> List[dict]:
    """Pass through task-attached documents from plan JSON — read-only metadata only."""
    if not isinstance(raw, list):
        return []

    from services.production_document_handoff_service import (
        employee_mobile_work_file_download_path,
    )

    documents: List[dict] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        name = str(
            item.get("name")
            or item.get("label")
            or item.get("filename")
            or f"Document {index + 1}"
        ).strip()
        doc_type = str(
            item.get("type") or item.get("document_type") or item.get("mime_type") or "file"
        ).strip()
        source = str(item.get("source") or default_source).strip()
        doc_id = str(item.get("id") or item.get("file_id") or f"{default_source}-{index + 1}")

        url_raw = item.get("url") or item.get("href") or item.get("download_url")
        url = str(url_raw).strip() if isinstance(url_raw, str) and url_raw.strip() else None
        if not url and order_id and source == "intake_work_file" and doc_id:
            url = employee_mobile_work_file_download_path(order_id, doc_id)

        payload: Dict[str, Any] = {
            "id": doc_id,
            "name": name,
            "type": doc_type,
            "source": source,
        }
        if url:
            payload["url"] = url
            payload["downloadable"] = True
        documents.append(payload)

    return documents


def task_belongs_to_employee(
    plan_task: dict,
    reality_task: dict,
    employee_id: int,
) -> bool:
    rt = reality_task or {}
    if _normalize_employee_id(rt.get("employee_id")) == employee_id:
        return True
    if _normalize_employee_id(rt.get("completed_by_employee_id")) == employee_id:
        return True
    planned_assignee = _normalize_employee_id(plan_task.get("assigned_employee_id"))
    if planned_assignee == employee_id:
        return True
    return False


def _task_owned_by_other(reality_task: dict, employee_id: int) -> bool:
    owner = _normalize_employee_id(reality_task.get("employee_id"))
    return owner is not None and owner != employee_id


async def _load_enriched_tasks(db: AsyncSession) -> Tuple[List[dict], Dict[int, dict]]:
    plans_sql = text(
        "SELECT ep.id, ep.order_id, ep.order_code, ep.tasks_json "
        "FROM execution_plan ep ORDER BY ep.order_id ASC"
    )
    plans = list((await db.execute(plans_sql)).mappings())

    reality_sql = text("SELECT er.order_id, er.tasks_json FROM execution_reality er")
    reality_map: Dict[int, list] = {}
    for row in (await db.execute(reality_sql)).mappings():
        reality_map[int(row["order_id"])] = _parse_json(row.get("tasks_json"))

    orders_sql = text(
        "SELECT o.id, o.code, o.status, o.client_name, o.quote_code, o.snapshot_line_items, "
        "o.quote_snapshot_v2_id, o.snapshot_v2_json, q.intake_code "
        "FROM orders o "
        "LEFT JOIN quotes q ON q.id = o.quote_id "
        "WHERE o.id IN (SELECT DISTINCT order_id FROM execution_plan)"
    )
    orders_map: Dict[int, dict] = {}
    orders_models: Dict[int, Orders] = {}
    for row in (await db.execute(orders_sql)).mappings():
        order_id = int(row["id"])
        snapshot = _parse_json_object(row.get("snapshot_line_items"))
        ctx = extract_order_snapshot_context(
            snapshot,
            client_name=str(row.get("client_name") or ""),
            quote_code=str(row.get("quote_code") or ""),
            intake_code=str(row.get("intake_code") or ""),
        )
        orders_map[order_id] = {
            "code": row["code"],
            "status": row["status"],
            "client": ctx.get("client") or str(row.get("client_name") or ""),
            "product": ctx.get("product") or "",
            "product_template": ctx.get("product_template") or "",
            "quote_code": ctx.get("quote_code") or str(row.get("quote_code") or ""),
            "intake_code": ctx.get("intake_code") or "",
        }
        orders_models[order_id] = Orders(
            id=order_id,
            code=row.get("code"),
            client_name=row.get("client_name"),
            quote_code=row.get("quote_code"),
            status=row.get("status"),
            quote_snapshot_v2_id=row.get("quote_snapshot_v2_id"),
            snapshot_v2_json=row.get("snapshot_v2_json"),
            snapshot_line_items=row.get("snapshot_line_items"),
        )

    order_work_files: Dict[int, List[dict]] = {}
    for order_id, info in orders_map.items():
        order_work_files[order_id] = await load_intake_work_files_for_order(
            db,
            order_id=order_id,
            intake_code=str(info.get("intake_code") or ""),
        )

    enriched: List[dict] = []
    from schemas.execution_plan_v2_frozen_task_identity import FROZEN_TASK_IDENTITY_VERSION
    from services.employee_mobile_task_truth_service import (
        _identity_to_mobile_fields,
        _production_blocker_summary,
        resolve_operational_plan_tasks,
    )

    for plan in plans:
        order_id = int(plan["order_id"])
        order_code = plan["order_code"] or ""
        order_info = orders_map.get(order_id, {})
        order_model = orders_models.get(order_id)
        resolved = resolve_operational_plan_tasks(
            plan.get("tasks_json"),
            order_id=order_id,
            order=order_model,
            execution_plan_id=int(plan["id"]) if plan.get("id") is not None else None,
            fail_closed=order_model is not None and order_has_v2_snapshot_fields(order_model),
        )
        plan_tasks = resolved.tasks
        canonical_v2 = resolved.canonical_v2
        legacy_mode = resolved.legacy_mode
        release_eval = (
            evaluate_production_release(order_model) if order_model is not None else None
        )
        production_release_blocked = (
            release_eval.release_status != "RELEASE_ALLOWED" if release_eval else False
        )
        blocking_owner_codes = (
            [str(item.code) for item in release_eval.blockers if item.code]
            if release_eval and production_release_blocked
            else []
        )
        readiness_authority = (
            "FROZEN_ORDER_SNAPSHOT_V2" if canonical_v2 else "LEGACY_READ_MODEL_EXPLICIT"
        )
        task_identity_version = FROZEN_TASK_IDENTITY_VERSION if canonical_v2 else None

        reality_tasks = reality_map.get(order_id, [])
        reality_by_task: Dict[str, List[dict]] = {}
        for rt in reality_tasks:
            if not isinstance(rt, dict):
                continue
            task_key = str(rt.get("task_id") or "")
            if not task_key:
                continue
            reality_by_task.setdefault(task_key, []).append(rt)

        for plan_task in plan_tasks:
            if not isinstance(plan_task, dict):
                continue
            task_id = str(plan_task.get("task_id") or "")
            if not task_id:
                continue
            task_sessions = reality_by_task.get(task_id, [])
            rt = merge_reality_fields_for_task(task_sessions)
            status = derive_task_status_from_sessions(task_sessions)

            process_id = str(plan_task.get("process_id") or "")
            process_type = str(plan_task.get("process_type") or "")
            identity_fields = _identity_to_mobile_fields(
                plan_task,
                order_info=order_info,
                canonical_v2=canonical_v2,
            )
            display_name = identity_fields.display_label

            instructions = str(plan_task.get("instructions") or "").strip()
            description = str(plan_task.get("description") or plan_task.get("notes") or "").strip()
            if not description and instructions:
                description = instructions

            task_documents = _normalize_task_documents(
                plan_task.get("documents"),
                order_id=order_id,
            )
            order_documents = order_work_files.get(order_id, [])
            documents = merge_production_documents(task_documents, order_documents)

            assigned_employee_id = _normalize_employee_id(plan_task.get("assigned_employee_id"))
            operational_startable = False
            readiness_label = None
            readiness_status = None
            safe_reasons: list = []

            enriched.append(
                {
                    "contract_version": "employee_mobile_task_truth/v1",
                    "task_id": task_id,
                    "order_id": order_id,
                    "order_code": order_code,
                    "title": display_name,
                    "display_label": display_name,
                    "description": description,
                    "instructions": instructions,
                    "status": status,
                    "process_id": process_id,
                    "process_type": process_type,
                    "machine_type": plan_task.get("machine_type") or "",
                    "estimated_time_minutes": plan_task.get("estimated_time_minutes") or 0,
                    "assigned_employee_id": assigned_employee_id,
                    "employee_id": _normalize_employee_id(rt.get("employee_id")),
                    "employee_name": rt.get("employee_name"),
                    "client": order_info.get("client", ""),
                    "product": order_info.get("product", ""),
                    "quote_code": order_info.get("quote_code", ""),
                    "intake_code": order_info.get("intake_code", ""),
                    "order_status": order_info.get("status", ""),
                    "started_at": rt.get("started_at"),
                    "completed_at": rt.get("ended_at"),
                    "blocked_at": rt.get("blocked_at"),
                    "blocked_reason": rt.get("block_reason") or rt.get("blocked_reason"),
                    "completed_by_employee_id": _normalize_employee_id(
                        rt.get("completed_by_employee_id")
                    ),
                    "active_helper_count": max(
                        0,
                        len(
                            [
                                session
                                for session in task_sessions
                                if session.get("started_at")
                                and not session.get("ended_at")
                                and _normalize_employee_id(session.get("employee_id"))
                                not in (
                                    None,
                                    assigned_employee_id,
                                    _normalize_employee_id(rt.get("employee_id")),
                                )
                            ]
                        ),
                    ),
                    "documents": documents,
                    "deterministic_task_key": identity_fields.deterministic_task_key,
                    "component_label": identity_fields.component_label,
                    "component_role": identity_fields.component_role,
                    "operation_label": identity_fields.operation_label,
                    "logo_segment_label": identity_fields.logo_segment_label,
                    "identity_source": identity_fields.identity_source,
                    "identity_classification": identity_fields.identity_classification,
                    "execution_plan_id": resolved.execution_plan_id,
                    "plan_sequence": plan_task.get("sequence_index"),
                    "legacy_mode": legacy_mode,
                    "legacy_fallback_active": legacy_mode,
                    "task_identity_version": task_identity_version,
                    "readiness_authority": readiness_authority,
                    "release_authority": "execution_owner_decision_production_release_service",
                    "execution_source": "execution_plan_v2_operational_tasks"
                    if canonical_v2
                    else "legacy_execution_plan_list",
                    "production_release_blocked": production_release_blocked,
                    "production_blocker_summary": _production_blocker_summary(
                        production_release_blocked,
                        blocking_owner_codes,
                    ),
                    "is_startable": operational_startable,
                    "readiness_label": readiness_label,
                    "readiness_status": readiness_status,
                    "readiness_reasons": safe_reasons,
                    "can_start": False,
                    "can_complete": status == "in_progress",
                    "is_assigned_to_current_employee": False,
                    "is_available_for_claim": False,
                    "assignment_source": "execution_plan",
                }
            )

    return enriched, orders_map


async def _load_plan_and_reality_tasks(
    db: AsyncSession,
    order_id: int,
) -> Tuple[List[dict], List[dict]]:
    plan_sql = text(
        "SELECT ep.id, ep.tasks_json, o.quote_snapshot_v2_id, o.snapshot_v2_json "
        "FROM execution_plan ep "
        "LEFT JOIN orders o ON o.id = ep.order_id "
        "WHERE ep.order_id = :oid LIMIT 1"
    )
    plan_row = (await db.execute(plan_sql, {"oid": order_id})).mappings().first()
    from services.employee_mobile_task_truth_service import resolve_operational_plan_tasks

    order_model: Orders | None = None
    if plan_row is not None:
        order_model = Orders(
            id=order_id,
            quote_snapshot_v2_id=plan_row.get("quote_snapshot_v2_id"),
            snapshot_v2_json=plan_row.get("snapshot_v2_json"),
        )
    resolved = resolve_operational_plan_tasks(
        plan_row.get("tasks_json") if plan_row else None,
        order_id=order_id,
        order=order_model,
        execution_plan_id=int(plan_row["id"]) if plan_row and plan_row.get("id") else None,
        fail_closed=order_model is not None and order_has_v2_snapshot_fields(order_model),
    )
    plan_tasks = resolved.tasks
    reality_sql = text("SELECT tasks_json FROM execution_reality WHERE order_id = :oid LIMIT 1")
    reality_row = (await db.execute(reality_sql, {"oid": order_id})).mappings().first()
    raw_reality = _parse_json(reality_row.get("tasks_json") if reality_row else [])
    return plan_tasks, raw_reality


async def _attach_readiness_to_tasks(
    db: AsyncSession,
    tasks: List[dict],
    employee_id: int,
    *,
    for_available_pool: bool = False,
) -> List[dict]:
    """Attach readiness payload.

    For the available pool, orders blocked by corrupt/missing V2 snapshot readiness
    input are excluded locally (ORDER_LOCAL_FAIL_CLOSED) so unrelated valid tasks
    remain visible. Assigned-task projections still fail closed per order.
    """
    by_order: Dict[int, List[dict]] = {}
    for task in tasks:
        by_order.setdefault(int(task["order_id"]), []).append(task)

    readiness_employee_id: Optional[int] = None if for_available_pool else employee_id
    excluded_task_keys: set[int] = set()
    projection_exclusions: List[dict] = []

    for order_id, order_tasks in by_order.items():
        try:
            plan_tasks, raw_reality = await _load_plan_and_reality_tasks(db, order_id)
            plan_sequence: Dict[str, int] = {}
            for idx, pt in enumerate(plan_tasks):
                if isinstance(pt, dict) and pt.get("task_id"):
                    plan_sequence[str(pt["task_id"])] = idx
            product_template = None
            _enriched, material_by_task, _ = await build_procurement_enriched_context(
                db,
                order_id=order_id,
                plan_tasks=plan_tasks,
                product_context=product_template,
            )
            from services.task_start_gate_service import load_order_quote_input

            quote_input = await load_order_quote_input(db, order_id)
            readiness_map = evaluate_all_task_readiness(
                plan_tasks,
                raw_reality,
                employee_id=readiness_employee_id,
                material_by_task=material_by_task,
                quote_input=quote_input,
            )
            plan_by_id = {str(pt.get("task_id")): pt for pt in plan_tasks if pt.get("task_id")}
            for task in order_tasks:
                tid = str(task["task_id"])
                task["plan_sequence"] = plan_sequence.get(tid, 9999)
                plan_task = plan_by_id.get(tid, {})
                readiness = readiness_map.get(tid)
                if readiness is None and plan_task:
                    context = build_readiness_context(plan_tasks, raw_reality)
                    readiness = evaluate_task_readiness(
                        plan_task,
                        context,
                        employee_id=readiness_employee_id,
                        material_by_task=material_by_task,
                        quote_input=quote_input,
                    )
                if readiness:
                    task.update(employee_safe_readiness_payload(readiness))
                task["can_start"] = bool(
                    task.get("is_startable")
                    and not task.get("production_release_blocked")
                    and task.get("status") in ("assigned", "paused")
                )
                task["can_complete"] = task.get("status") == "in_progress"
        except HTTPException as exc:
            block_detail = _planning_readiness_order_block_detail(exc)
            if for_available_pool and block_detail is not None:
                excluded_task_keys.update(id(task) for task in order_tasks)
                exclusion = {
                    "code": block_detail.get("error"),
                    "order_id": order_id,
                    "excluded_task_count": len(order_tasks),
                    "projection_scope": "available",
                    "operator_safe_message": (
                        "Order planning snapshot unavailable; tasks excluded from available pool."
                    ),
                }
                projection_exclusions.append(exclusion)
                logger.warning(
                    "employee_mobile available projection excluded order "
                    "order_id=%s code=%s excluded_task_count=%s",
                    order_id,
                    block_detail.get("error"),
                    len(order_tasks),
                )
                continue
            raise

    if excluded_task_keys:
        tasks[:] = [task for task in tasks if id(task) not in excluded_task_keys]

    return projection_exclusions


async def list_my_tasks(db: AsyncSession, employee_id: int) -> List[dict]:
    from services.task_clarification_request_service import get_open_clarification_map

    enriched, _ = await _load_enriched_tasks(db)
    owned: List[dict] = []
    for task in enriched:
        plan_task = {"assigned_employee_id": task.get("assigned_employee_id")}
        reality_task = {
            "employee_id": task.get("employee_id"),
            "completed_by_employee_id": task.get("completed_by_employee_id"),
        }
        if task_belongs_to_employee(plan_task, reality_task, employee_id):
            owned.append(task)

    if owned:
        order_ids = sorted({int(task["order_id"]) for task in owned})
        placeholders = ", ".join(f":oid{i}" for i in range(len(order_ids)))
        params = {f"oid{i}": oid for i, oid in enumerate(order_ids)}
        reality_sql = text(
            f"SELECT order_id, tasks_json FROM execution_reality WHERE order_id IN ({placeholders})"
        )
        reality_rows = (await db.execute(reality_sql, params)).mappings()
        reality_by_order: Dict[int, List[dict]] = {}
        for row in reality_rows:
            reality_by_order[int(row["order_id"])] = _parse_json(row.get("tasks_json"))

        for task in owned:
            order_id = int(task["order_id"])
            task_id = str(task["task_id"])
            task_sessions = sessions_for_task(reality_by_order.get(order_id, []), task_id)
            task["status"] = derive_task_status_for_employee(task_sessions, employee_id)
            my_active = active_session_for_employee(task_sessions, employee_id)
            rt = my_active if my_active else merge_reality_fields_for_task(task_sessions)
            metrics = aggregate_task_work_metrics(task_sessions)
            task["employee_id"] = _normalize_employee_id(rt.get("employee_id"))
            task["employee_name"] = rt.get("employee_name")
            task["started_at"] = rt.get("started_at")
            task["completed_at"] = rt.get("ended_at") if task["status"] == "done" else None
            task["blocked_at"] = rt.get("blocked_at")
            task["blocked_reason"] = rt.get("block_reason") or rt.get("blocked_reason")
            task["active_helper_count"] = employee_safe_helper_count(
                metrics["active_workers"],
                viewer_employee_id=employee_id,
            )

    open_map = await get_open_clarification_map(
        db,
        employee_id=employee_id,
        task_keys=[(t["order_id"], t["task_id"]) for t in owned],
    )
    for task in owned:
        key = (task["order_id"], task["task_id"])
        open_req = open_map.get(key)
        task["clarification_request"] = open_req if open_req else None

    await _attach_readiness_to_tasks(db, owned, employee_id)
    for task in owned:
        task["is_assigned_to_current_employee"] = True
        task["is_available_for_claim"] = False
        task["can_claim"] = False
        task["can_start_from_available"] = False
    return owned


async def _get_task_context(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
) -> Tuple[dict, dict, dict, List[dict]]:
    enriched, _ = await _load_enriched_tasks(db)
    match = next(
        (t for t in enriched if t["order_id"] == order_id and t["task_id"] == task_id),
        None,
    )
    if match is None:
        raise HTTPException(status_code=404, detail={"error": "task_not_found"})

    plan_task = {"assigned_employee_id": match.get("assigned_employee_id")}
    reality_task = {
        "employee_id": match.get("employee_id"),
        "completed_by_employee_id": match.get("completed_by_employee_id"),
    }
    if not task_belongs_to_employee(plan_task, reality_task, employee_id):
        raise HTTPException(status_code=403, detail={"error": "task_not_assigned_to_employee"})

    reality_sql = text(
        "SELECT tasks_json FROM execution_reality WHERE order_id = :oid LIMIT 1"
    )
    row = (await db.execute(reality_sql, {"oid": order_id})).mappings().first()
    all_tasks = _parse_json(row.get("tasks_json") if row else [])
    task_sessions = sessions_for_task(all_tasks, task_id)
    rt = merge_reality_fields_for_task(task_sessions)
    my_active = active_session_for_employee(task_sessions, employee_id)
    if my_active:
        rt = my_active
    elif rt and _task_owned_by_other(rt, employee_id):
        raise HTTPException(status_code=403, detail={"error": "task_owned_by_other_employee"})

    plan_sql = text(
        "SELECT ep.id, ep.tasks_json, o.quote_snapshot_v2_id, o.snapshot_v2_json "
        "FROM execution_plan ep "
        "LEFT JOIN orders o ON o.id = ep.order_id "
        "WHERE ep.order_id = :oid LIMIT 1"
    )
    plan_row = (await db.execute(plan_sql, {"oid": order_id})).mappings().first()
    from services.employee_mobile_task_truth_service import resolve_operational_plan_tasks

    order_model: Orders | None = None
    if plan_row is not None:
        order_model = Orders(
            id=order_id,
            quote_snapshot_v2_id=plan_row.get("quote_snapshot_v2_id"),
            snapshot_v2_json=plan_row.get("snapshot_v2_json"),
        )
    resolved = resolve_operational_plan_tasks(
        plan_row.get("tasks_json") if plan_row else None,
        order_id=order_id,
        order=order_model,
        fail_closed=order_model is not None and order_has_v2_snapshot_fields(order_model),
    )
    plan_lookup = {
        str(pt.get("task_id")): pt
        for pt in resolved.tasks
        if isinstance(pt, dict) and pt.get("task_id")
    }
    return match, rt, plan_lookup.get(task_id, {}), task_sessions


async def start_my_task(db: AsyncSession, *, order_id: int, task_id: str, employee_id: int) -> dict:
    task, rt, plan_task, task_sessions = await _get_task_context(
        db, order_id=order_id, task_id=task_id, employee_id=employee_id
    )
    status = derive_task_status_from_sessions(task_sessions) if task_sessions else derive_task_status(rt)
    if status == "done":
        raise HTTPException(status_code=409, detail={"error": "task_already_completed"})
    if active_session_for_employee(task_sessions, employee_id):
        return {"status": "ok", "action": "start", "task_id": task_id, "already_started": True}
    if status == "blocked":
        raise HTTPException(status_code=409, detail={"error": "task_is_blocked"})

    plan_tasks, raw_reality = await _load_plan_and_reality_tasks(db, order_id)
    from services.task_start_gate_service import assert_task_startable

    gate = await assert_task_startable(
        db,
        order_id=order_id,
        task_id=task_id,
        employee_id=employee_id,
    )
    readiness = gate["readiness"]

    process_type = str(plan_task.get("process_type") or task.get("process_type") or "")
    machine_type = str(plan_task.get("machine_type") or task.get("machine_type") or "")

    guard = OperatorEmployeeGuard(db)
    guard_result = await guard.validate_for_task_start(
        employee_id=employee_id,
        process_type=process_type,
        machine_type=machine_type,
    )
    if not guard_result.allowed:
        raise HTTPException(
            status_code=422,
            detail={
                "error": guard_result.errors[0] if guard_result.errors else "employee_invalid",
                "errors": guard_result.errors,
            },
        )

    order_sql = text("SELECT code FROM orders WHERE id = :oid")
    order_row = (await db.execute(order_sql, {"oid": order_id})).first()
    if order_row:
        order_code = order_row[0]
    else:
        plan_code_sql = text(
            "SELECT order_code FROM execution_plan WHERE order_id = :oid LIMIT 1"
        )
        plan_code_row = (await db.execute(plan_code_sql, {"oid": order_id})).first()
        if not plan_code_row or not plan_code_row[0]:
            raise HTTPException(status_code=404, detail={"error": "order_not_found"})
        order_code = plan_code_row[0]

    now_iso = datetime.now(timezone.utc).isoformat()
    svc = ExecutionRealityService(db)
    try:
        await svc.start_task(
            order_id=order_id,
            order_code=order_code,
            task_id=task_id,
            timestamp=now_iso,
            initial_fields={
                "employee_id": guard_result.employee_id,
                "employee_name": guard_result.employee_name,
                "operator_name": guard_result.employee_name,
                "source": "employee_mobile",
                "role": "primary",
                "session_type": "work",
            },
        )
    except RealityInputError as exc:
        if exc.code == "task_already_started":
            if active_session_for_employee(task_sessions, employee_id):
                return {"status": "ok", "action": "start", "task_id": task_id, "already_started": True}
            raise HTTPException(status_code=403, detail={"error": "task_owned_by_other_employee"})
        raise HTTPException(status_code=422, detail={"error": exc.code, "detail": exc.detail})

    return {"status": "ok", "action": "start", "task_id": task_id, "timestamp": now_iso}


async def block_my_task(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
    reason: Optional[str],
) -> dict:
    task, rt, _, task_sessions = await _get_task_context(
        db, order_id=order_id, task_id=task_id, employee_id=employee_id
    )
    my_session = active_session_for_employee(task_sessions, employee_id)
    status = derive_task_status_from_sessions(task_sessions) if task_sessions else derive_task_status(rt)
    if not my_session or not my_session.get("started_at"):
        raise HTTPException(
            status_code=422,
            detail={"error": "task_not_started", "detail": "Taskul trebuie pornit înainte de blocare."},
        )
    if status == "done":
        raise HTTPException(status_code=422, detail={"error": "task_already_completed"})
    if my_session.get("blocked_at") and not my_session.get("unblocked_at"):
        return {"status": "ok", "action": "block", "task_id": task_id, "already_blocked": True}

    from models.execution_reality import ExecutionReality
    from sqlalchemy import select

    stmt = select(ExecutionReality).where(ExecutionReality.order_id == order_id)
    reality = (await db.execute(stmt)).scalar_one_or_none()
    if reality is None:
        raise HTTPException(status_code=404, detail={"error": "reality_not_found"})

    tasks = _parse_json(reality.tasks_json)
    now_iso = datetime.now(timezone.utc).isoformat()
    updated = False
    for entry in tasks:
        if not isinstance(entry, dict) or entry.get("task_id") != task_id:
            continue
        if entry.get("ended_at"):
            continue
        if _normalize_employee_id(entry.get("employee_id")) not in (None, employee_id):
            continue
        if not entry.get("started_at"):
            raise HTTPException(status_code=422, detail={"error": "task_not_started"})
        entry["blocked_at"] = now_iso
        entry["unblocked_at"] = None
        entry["status"] = "blocked"
        if reason:
            entry["block_reason"] = reason.strip()
        updated = True
        break

    if not updated:
        raise HTTPException(status_code=404, detail={"error": "task_not_found_in_reality"})

    reality.tasks_json = json.dumps(tasks)
    await db.commit()
    return {"status": "ok", "action": "block", "task_id": task_id, "timestamp": now_iso}


async def complete_my_task(db: AsyncSession, *, order_id: int, task_id: str, employee_id: int) -> dict:
    task, rt, _, task_sessions = await _get_task_context(
        db, order_id=order_id, task_id=task_id, employee_id=employee_id
    )
    status = derive_task_status_for_employee(task_sessions, employee_id)
    if status == "done":
        return {"status": "ok", "action": "complete", "task_id": task_id, "already_completed": True}

    my_session = active_session_for_employee(task_sessions, employee_id)
    if not my_session or not my_session.get("started_at"):
        raise HTTPException(
            status_code=422,
            detail={"error": "task_not_started", "detail": "Taskul trebuie pornit înainte de finalizare."},
        )
    if my_session.get("blocked_at") and not my_session.get("unblocked_at"):
        raise HTTPException(status_code=409, detail={"error": "task_is_blocked"})
    if my_session.get("paused_at") and not my_session.get("resumed_at"):
        raise HTTPException(status_code=409, detail={"error": "task_is_paused"})

    emp_sql = text("SELECT name FROM employees WHERE id = :eid LIMIT 1")
    emp_row = (await db.execute(emp_sql, {"eid": employee_id})).first()
    employee_name = emp_row[0] if emp_row else task.get("employee_name")

    now_iso = datetime.now(timezone.utc).isoformat()
    svc = ExecutionRealityService(db)
    try:
        await svc.end_task(
            order_id=order_id,
            task_id=task_id,
            timestamp=now_iso,
            employee_id=employee_id,
            completion_fields={
                "completed_by_employee_id": employee_id,
                "completed_by_employee_name": employee_name,
            },
        )
    except RealityInputError as exc:
        if exc.code == "task_not_started":
            _, _, _, task_sessions_after = await _get_task_context(
                db, order_id=order_id, task_id=task_id, employee_id=employee_id
            )
            if derive_task_status_for_employee(task_sessions_after, employee_id) == "done":
                return {
                    "status": "ok",
                    "action": "complete",
                    "task_id": task_id,
                    "already_completed": True,
                }
        raise HTTPException(status_code=422, detail={"error": exc.code, "detail": exc.detail})

    return {"status": "ok", "action": "complete", "task_id": task_id, "timestamp": now_iso}


async def unblock_my_task(db: AsyncSession, *, order_id: int, task_id: str, employee_id: int) -> dict:
    task, rt, _, task_sessions = await _get_task_context(
        db, order_id=order_id, task_id=task_id, employee_id=employee_id
    )
    my_session = active_session_for_employee(task_sessions, employee_id)
    status = derive_task_status_from_sessions(task_sessions) if task_sessions else derive_task_status(rt)
    if not my_session or not my_session.get("blocked_at") or my_session.get("unblocked_at"):
        if status == "done":
            raise HTTPException(status_code=422, detail={"error": "task_already_completed"})
        raise HTTPException(status_code=422, detail={"error": "task_not_blocked"})

    from models.execution_reality import ExecutionReality
    from sqlalchemy import select

    stmt = select(ExecutionReality).where(ExecutionReality.order_id == order_id)
    reality = (await db.execute(stmt)).scalar_one_or_none()
    if reality is None:
        raise HTTPException(status_code=404, detail={"error": "reality_not_found"})

    tasks = _parse_json(reality.tasks_json)
    now_iso = datetime.now(timezone.utc).isoformat()
    updated = False
    for entry in tasks:
        if not isinstance(entry, dict) or entry.get("task_id") != task_id:
            continue
        if entry.get("ended_at"):
            continue
        if _normalize_employee_id(entry.get("employee_id")) not in (None, employee_id):
            continue
        if not entry.get("blocked_at") or entry.get("unblocked_at"):
            raise HTTPException(status_code=422, detail={"error": "task_not_blocked"})
        entry["unblocked_at"] = now_iso
        entry["status"] = "in_progress"
        updated = True
        break

    if not updated:
        raise HTTPException(status_code=404, detail={"error": "task_not_found_in_reality"})

    reality.tasks_json = json.dumps(tasks)
    await db.commit()
    return {"status": "ok", "action": "unblock", "task_id": task_id, "timestamp": now_iso}


async def pause_my_task(db: AsyncSession, *, order_id: int, task_id: str, employee_id: int) -> dict:
    """Pause the authenticated employee's active session — not a block."""
    task, rt, _, task_sessions = await _get_task_context(
        db, order_id=order_id, task_id=task_id, employee_id=employee_id
    )
    my_session = active_session_for_employee(task_sessions, employee_id)
    if not my_session or not my_session.get("started_at"):
        raise HTTPException(
            status_code=422,
            detail={"error": "task_not_started", "detail": "Taskul trebuie pornit înainte de întrerupere."},
        )
    if my_session.get("paused_at") and not my_session.get("resumed_at"):
        return {"status": "ok", "action": "pause", "task_id": task_id, "already_paused": True}
    if my_session.get("blocked_at") and not my_session.get("unblocked_at"):
        raise HTTPException(status_code=409, detail={"error": "task_is_blocked"})

    from models.execution_reality import ExecutionReality
    from sqlalchemy import select

    stmt = select(ExecutionReality).where(ExecutionReality.order_id == order_id)
    reality = (await db.execute(stmt)).scalar_one_or_none()
    if reality is None:
        raise HTTPException(status_code=404, detail={"error": "reality_not_found"})

    tasks = _parse_json(reality.tasks_json)
    now_iso = datetime.now(timezone.utc).isoformat()
    updated = False
    for entry in tasks:
        if not isinstance(entry, dict) or entry.get("task_id") != task_id:
            continue
        if entry.get("ended_at"):
            continue
        if _normalize_employee_id(entry.get("employee_id")) not in (None, employee_id):
            continue
        if not entry.get("started_at"):
            raise HTTPException(status_code=422, detail={"error": "task_not_started"})
        entry["paused_at"] = now_iso
        entry["resumed_at"] = None
        updated = True
        break

    if not updated:
        raise HTTPException(status_code=404, detail={"error": "task_not_found_in_reality"})

    reality.tasks_json = json.dumps(tasks)
    await db.commit()
    return {"status": "ok", "action": "pause", "task_id": task_id, "timestamp": now_iso}


async def resume_my_task(db: AsyncSession, *, order_id: int, task_id: str, employee_id: int) -> dict:
    """Resume the authenticated employee's paused session."""
    task, rt, _, task_sessions = await _get_task_context(
        db, order_id=order_id, task_id=task_id, employee_id=employee_id
    )
    my_session = active_session_for_employee(task_sessions, employee_id)
    if not my_session or not my_session.get("started_at"):
        raise HTTPException(status_code=422, detail={"error": "task_not_started"})
    if not my_session.get("paused_at") or my_session.get("resumed_at"):
        raise HTTPException(status_code=409, detail={"error": "task_not_paused"})

    from models.execution_reality import ExecutionReality
    from sqlalchemy import select

    stmt = select(ExecutionReality).where(ExecutionReality.order_id == order_id)
    reality = (await db.execute(stmt)).scalar_one_or_none()
    if reality is None:
        raise HTTPException(status_code=404, detail={"error": "reality_not_found"})

    tasks = _parse_json(reality.tasks_json)
    now_iso = datetime.now(timezone.utc).isoformat()
    updated = False
    for entry in tasks:
        if not isinstance(entry, dict) or entry.get("task_id") != task_id:
            continue
        if entry.get("ended_at"):
            continue
        if _normalize_employee_id(entry.get("employee_id")) not in (None, employee_id):
            continue
        if not entry.get("paused_at") or entry.get("resumed_at"):
            raise HTTPException(status_code=409, detail={"error": "task_not_paused"})
        entry["resumed_at"] = now_iso
        entry["status"] = "in_progress"
        updated = True
        break

    if not updated:
        raise HTTPException(status_code=404, detail={"error": "task_not_found_in_reality"})

    reality.tasks_json = json.dumps(tasks)
    await db.commit()
    return {"status": "ok", "action": "resume", "task_id": task_id, "timestamp": now_iso}


_TERMINAL_ORDER_STATUSES = frozenset({"completed", "cancelled"})


def _is_order_active_for_claim(order_status: str) -> bool:
    normalized = (order_status or "").strip().lower()
    return normalized not in _TERMINAL_ORDER_STATUSES


def _has_active_session_by_other(sessions: List[dict], employee_id: int) -> bool:
    for entry in sessions:
        if not isinstance(entry, dict) or not is_session_active(entry):
            continue
        owner = _normalize_employee_id(entry.get("employee_id"))
        if owner is not None and owner != employee_id:
            return True
    return False


async def list_available_tasks(db: AsyncSession, employee_id: int) -> List[dict]:
    """Unassigned plan tasks the employee may claim (eligible + no foreign active session)."""
    enriched, _ = await _load_enriched_tasks(db)
    if not enriched:
        return []

    order_ids = sorted({int(task["order_id"]) for task in enriched})
    placeholders = ", ".join(f":oid{i}" for i in range(len(order_ids)))
    params = {f"oid{i}": oid for i, oid in enumerate(order_ids)}
    reality_sql = text(
        f"SELECT order_id, tasks_json FROM execution_reality WHERE order_id IN ({placeholders})"
    )
    reality_rows = (await db.execute(reality_sql, params)).mappings()
    reality_by_order: Dict[int, List[dict]] = {}
    for row in reality_rows:
        reality_by_order[int(row["order_id"])] = _parse_json(row.get("tasks_json"))

    registry = OperationalRegistryService(db)
    available: List[dict] = []

    for task in enriched:
        order_id = int(task["order_id"])
        task_id = str(task["task_id"])
        assigned_id = _normalize_employee_id(task.get("assigned_employee_id"))

        plan_task = {"assigned_employee_id": assigned_id}
        reality_task = {
            "employee_id": task.get("employee_id"),
            "completed_by_employee_id": task.get("completed_by_employee_id"),
        }
        if task_belongs_to_employee(plan_task, reality_task, employee_id):
            continue
        if assigned_id is not None and assigned_id != employee_id:
            continue

        if not _is_order_active_for_claim(str(task.get("order_status") or "")):
            continue

        task_sessions = sessions_for_task(reality_by_order.get(order_id, []), task_id)
        status = derive_task_status_from_sessions(task_sessions) if task_sessions else str(task.get("status") or "assigned")
        if status == "done":
            continue
        if _has_active_session_by_other(task_sessions, employee_id):
            continue

        process_type = str(task.get("process_type") or "")
        machine_type = str(task.get("machine_type") or "")
        eligibility = await registry.check_employee_operation_eligibility(
            employee_id,
            process_type,
            machine_type=machine_type or None,
        )
        if not eligibility.get("eligible"):
            continue

        row = dict(task)
        row["status"] = status
        row["preparation_domain"] = derive_preparation_domain(
            {
                "process_id": task.get("process_id") or process_type,
                "process_type": process_type,
                "machine_type": machine_type,
                "documents": task.get("documents") or [],
            }
        )
        row["eligibility_reason"] = str(eligibility.get("authorization_status") or "authorized")
        row["claimable"] = True
        available.append(row)

    await _attach_readiness_to_tasks(
        db,
        available,
        employee_id,
        for_available_pool=True,
    )
    for row in available:
        row["is_assigned_to_current_employee"] = False
        row["is_available_for_claim"] = True
        row["can_claim"] = bool(row.get("claimable"))
        row["can_start_from_available"] = bool(row.get("can_start"))
    return available


_TASK_NOT_ACCESSIBLE_MESSAGE = (
    "Taskul nu este disponibil pentru acest angajat sau nu mai poate fi accesat."
)


async def get_employee_mobile_task(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
) -> dict:
    """Read-only task lookup scoped to order_id + task_id for Employee Mobile detail/preview."""
    my_tasks = await list_my_tasks(db, employee_id)
    owned = next(
        (
            t
            for t in my_tasks
            if int(t["order_id"]) == order_id and str(t["task_id"]) == task_id
        ),
        None,
    )
    if owned is not None:
        row = dict(owned)
        row["access_mode"] = "owned"
        row["preview_only"] = False
        return row

    available = await list_available_tasks(db, employee_id)
    preview = next(
        (
            t
            for t in available
            if int(t["order_id"]) == order_id and str(t["task_id"]) == task_id
        ),
        None,
    )
    if preview is not None:
        row = dict(preview)
        row["access_mode"] = "available_preview"
        row["preview_only"] = True
        return row

    enriched, _ = await _load_enriched_tasks(db)
    exists = any(
        int(t["order_id"]) == order_id and str(t["task_id"]) == task_id for t in enriched
    )
    if exists:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "task_not_accessible_to_employee",
                "message": _TASK_NOT_ACCESSIBLE_MESSAGE,
            },
        )
    raise HTTPException(status_code=404, detail={"error": "task_not_found"})


async def claim_my_task(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
) -> dict:
    """Assign an unclaimed plan task to the authenticated employee without starting work."""
    enriched, _ = await _load_enriched_tasks(db)
    match = next(
        (t for t in enriched if t["order_id"] == order_id and t["task_id"] == task_id),
        None,
    )
    if match is None:
        raise HTTPException(status_code=404, detail={"error": "task_not_found"})

    if not _is_order_active_for_claim(str(match.get("order_status") or "")):
        raise HTTPException(status_code=409, detail={"error": "task_not_claimable", "message": "Comanda nu este activă."})

    reality_sql = text("SELECT tasks_json FROM execution_reality WHERE order_id = :oid LIMIT 1")
    row = (await db.execute(reality_sql, {"oid": order_id})).mappings().first()
    all_reality = _parse_json(row.get("tasks_json") if row else [])
    task_sessions = sessions_for_task(all_reality, task_id)
    status = derive_task_status_from_sessions(task_sessions) if task_sessions else "assigned"
    if status == "done":
        raise HTTPException(status_code=409, detail={"error": "task_not_claimable", "message": "Taskul este finalizat."})

    if _has_active_session_by_other(task_sessions, employee_id):
        raise HTTPException(
            status_code=409,
            detail={"error": "task_has_active_session", "message": "Un coleg lucrează deja la acest task."},
        )

    assigned_id = _normalize_employee_id(match.get("assigned_employee_id"))
    if assigned_id is not None and assigned_id != employee_id:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "task_already_assigned",
                "message": "Taskul este deja preluat de alt coleg.",
            },
        )

    process_type = str(match.get("process_type") or "")
    machine_type = str(match.get("machine_type") or "")
    registry = OperationalRegistryService(db)
    eligibility = await registry.check_employee_operation_eligibility(
        employee_id,
        process_type,
        machine_type=machine_type or None,
    )
    if not eligibility.get("eligible"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "employee_not_eligible",
                "message": "Nu ești eligibil pentru acest task.",
            },
        )

    result = await assign_plan_task(
        db,
        order_id=order_id,
        task_id=task_id,
        assigned_employee_id=employee_id,
        assignment_source="employee_claim",
    )
    return {
        "status": "ok",
        "action": "claim",
        "task_id": task_id,
        "order_id": order_id,
        "assigned_employee_id": employee_id,
        "assigned_employee_name": result.get("assigned_employee_name"),
        "already_claimed": bool(result.get("already_assigned")),
    }


async def start_available_task(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
) -> dict:
    """Assign (if needed) and start an available plan task — eligibility + readiness before assign."""
    enriched, _ = await _load_enriched_tasks(db)
    match = next(
        (t for t in enriched if t["order_id"] == order_id and t["task_id"] == task_id),
        None,
    )
    if match is None:
        raise HTTPException(status_code=404, detail={"error": "task_not_found"})

    if not _is_order_active_for_claim(str(match.get("order_status") or "")):
        raise HTTPException(
            status_code=409,
            detail={"error": "task_not_claimable", "message": "Comanda nu este activă."},
        )

    reality_sql = text("SELECT tasks_json FROM execution_reality WHERE order_id = :oid LIMIT 1")
    row = (await db.execute(reality_sql, {"oid": order_id})).mappings().first()
    all_reality = _parse_json(row.get("tasks_json") if row else [])
    task_sessions = sessions_for_task(all_reality, task_id)
    status = derive_task_status_from_sessions(task_sessions) if task_sessions else "assigned"
    if status == "done":
        raise HTTPException(
            status_code=409,
            detail={"error": "task_not_claimable", "message": "Taskul este finalizat."},
        )

    if _has_active_session_by_other(task_sessions, employee_id):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "task_has_active_session",
                "message": "Un coleg lucrează deja la acest task.",
            },
        )

    assigned_id = _normalize_employee_id(match.get("assigned_employee_id"))
    if assigned_id is not None and assigned_id != employee_id:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "task_already_assigned",
                "message": "Taskul este deja preluat de alt coleg.",
            },
        )

    process_type = str(match.get("process_type") or "")
    machine_type = str(match.get("machine_type") or "")
    registry = OperationalRegistryService(db)
    eligibility = await registry.check_employee_operation_eligibility(
        employee_id,
        process_type,
        machine_type=machine_type or None,
    )
    if not eligibility.get("eligible"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "employee_not_eligible",
                "message": "Nu ești eligibil pentru acest task.",
            },
        )

    if assigned_id == employee_id:
        return await start_my_task(
            db,
            order_id=order_id,
            task_id=task_id,
            employee_id=employee_id,
        )

    from services.task_start_gate_service import assert_task_startable

    # Evaluate dependency/material gates without assignment requirement — assign happens next.
    await assert_task_startable(
        db,
        order_id=order_id,
        task_id=task_id,
        employee_id=None,
    )

    await assign_plan_task(
        db,
        order_id=order_id,
        task_id=task_id,
        assigned_employee_id=employee_id,
        assignment_source="start_from_available",
    )
    try:
        return await start_my_task(
            db,
            order_id=order_id,
            task_id=task_id,
            employee_id=employee_id,
        )
    except HTTPException:
        await clear_plan_task_assignment(db, order_id=order_id, task_id=task_id)
        raise
