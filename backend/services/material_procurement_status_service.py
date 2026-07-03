"""Manual procurement status for material planning — operator-controlled readiness gates."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from models.execution_reality import ExecutionReality
from services.material_planning_service import (
    CATEGORY_INDIRECT,
    CATEGORY_PROJECT_CRITICAL,
    CATEGORY_STANDARD_LOW_COST,
    IMPACT_CAN_BLOCK,
    IMPACT_SUGGEST_REPLENISH,
    derive_material_planning_items,
    derive_task_material_hints,
)
from services.execution_plan_task_parser import operational_tasks_only
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

PROCUREMENT_META_TASK_ID = "__workos_material_procurement__"

STATUS_NOT_CHECKED = "not_checked"
STATUS_CHECK_REQUIRED = "check_required"
STATUS_SUGGEST_REPLENISH = "suggest_replenish"
STATUS_AWAITING_ADVANCE = "awaiting_advance"
STATUS_TO_ORDER = "to_order"
STATUS_ORDERED = "ordered"
STATUS_RECEIVED = "received"
STATUS_AVAILABLE = "available"
STATUS_NOT_REQUIRED = "not_required"

PROCUREMENT_STATUSES = frozenset(
    {
        STATUS_NOT_CHECKED,
        STATUS_CHECK_REQUIRED,
        STATUS_SUGGEST_REPLENISH,
        STATUS_AWAITING_ADVANCE,
        STATUS_TO_ORDER,
        STATUS_ORDERED,
        STATUS_RECEIVED,
        STATUS_AVAILABLE,
        STATUS_NOT_REQUIRED,
    }
)

BLOCKING_PROCUREMENT_STATUSES = frozenset(
    {STATUS_AWAITING_ADVANCE, STATUS_TO_ORDER, STATUS_ORDERED}
)

STATUSES_REQUIRING_NOTE = frozenset({STATUS_AWAITING_ADVANCE, STATUS_TO_ORDER})

PROCUREMENT_LABELS: Dict[str, str] = {
    STATUS_NOT_CHECKED: "Neverificat",
    STATUS_CHECK_REQUIRED: "Verificare necesară",
    STATUS_SUGGEST_REPLENISH: "Reaprovizionare sugerată",
    STATUS_AWAITING_ADVANCE: "Așteaptă avans",
    STATUS_TO_ORDER: "De comandat",
    STATUS_ORDERED: "Comandat",
    STATUS_RECEIVED: "Primit",
    STATUS_AVAILABLE: "Disponibil",
    STATUS_NOT_REQUIRED: "Nu este necesar",
}

PLANNING_ACTIONS: Dict[str, str] = {
    STATUS_NOT_CHECKED: "verify",
    STATUS_CHECK_REQUIRED: "verify",
    STATUS_SUGGEST_REPLENISH: "suggest_replenish",
    STATUS_AWAITING_ADVANCE: "await_advance",
    STATUS_TO_ORDER: "order",
    STATUS_ORDERED: "wait_delivery",
    STATUS_RECEIVED: "confirm_available",
    STATUS_AVAILABLE: "ready",
    STATUS_NOT_REQUIRED: "none",
}

EMPLOYEE_SAFE_STATUS_LABELS: Dict[str, str] = {
    STATUS_NOT_CHECKED: "Verifică material",
    STATUS_CHECK_REQUIRED: "Verifică material",
    STATUS_SUGGEST_REPLENISH: "Verificare preventivă",
    STATUS_AWAITING_ADVANCE: "Așteaptă confirmare achiziție",
    STATUS_TO_ORDER: "Așteaptă material",
    STATUS_ORDERED: "Așteaptă material",
    STATUS_RECEIVED: "Material primit",
    STATUS_AVAILABLE: "Material disponibil",
    STATUS_NOT_REQUIRED: "Verifică material",
}


def _parse_json_list(raw: Any) -> List[Any]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def split_reality_task_entries(entries: List[Any]) -> Tuple[List[dict], Dict[str, dict]]:
    """Separate work sessions from procurement meta record in execution_reality.tasks_json."""
    work_tasks: List[dict] = []
    statuses: Dict[str, dict] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        if str(item.get("task_id") or "") == PROCUREMENT_META_TASK_ID:
            raw = item.get("material_procurement_statuses")
            if isinstance(raw, dict):
                statuses = {str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)}
            continue
        work_tasks.append(item)
    return work_tasks, statuses


def embed_procurement_in_reality_tasks(
    work_tasks: List[dict],
    statuses: Dict[str, dict],
) -> List[dict]:
    if not statuses:
        return list(work_tasks)
    meta = {
        "task_id": PROCUREMENT_META_TASK_ID,
        "material_procurement_statuses": statuses,
    }
    return list(work_tasks) + [meta]


def is_material_status_blocking(item: dict) -> bool:
    if str(item.get("category") or "") != CATEGORY_PROJECT_CRITICAL:
        return False
    if str(item.get("readiness_impact") or "") != IMPACT_CAN_BLOCK:
        return False
    status = str(item.get("procurement_status") or STATUS_NOT_CHECKED)
    return status in BLOCKING_PROCUREMENT_STATUSES


def _effective_task_ids(item: dict) -> List[str]:
    ids: List[str] = []
    for task_id in item.get("required_for_task_ids") or []:
        key = str(task_id or "").strip()
        if key and key not in ids:
            ids.append(key)
    override = item.get("procurement_override") or {}
    for task_id in override.get("affected_task_ids") or []:
        key = str(task_id or "").strip()
        if key and key not in ids:
            ids.append(key)
    return ids


def _employee_label_for_item(item: dict) -> str:
    category = str(item.get("category") or "")
    if category in (CATEGORY_STANDARD_LOW_COST, CATEGORY_INDIRECT):
        if str(item.get("readiness_impact") or "") == IMPACT_SUGGEST_REPLENISH:
            return "Verificare preventivă"
        return "Checklist"
    status = str(item.get("procurement_status") or STATUS_NOT_CHECKED)
    return EMPLOYEE_SAFE_STATUS_LABELS.get(status, "Verifică material")


def employee_safe_procurement_hint(item: dict) -> dict:
    return {
        "name": str(item.get("name") or ""),
        "category": str(item.get("category") or ""),
        "label": _employee_label_for_item(item),
        "status": str(item.get("procurement_status") or STATUS_NOT_CHECKED),
        "display_note": str(item.get("display_note") or ""),
    }


def apply_procurement_statuses(
    items: List[dict],
    statuses: Optional[Dict[str, dict]] = None,
) -> List[dict]:
    statuses = statuses or {}
    enriched: List[dict] = []
    for item in items:
        code = str(item.get("code") or "")
        override = dict(statuses.get(code) or {})
        status = str(override.get("status") or STATUS_NOT_CHECKED)
        if status not in PROCUREMENT_STATUSES:
            status = STATUS_NOT_CHECKED
        procurement_label = PROCUREMENT_LABELS.get(status, status)
        planning_action = PLANNING_ACTIONS.get(status, "verify")
        affects_start = is_material_status_blocking({**item, "procurement_status": status})
        employee_safe_label = _employee_label_for_item({**item, "procurement_status": status})
        operator_note = str(override.get("note") or "").strip()
        enriched.append(
            {
                **item,
                "procurement_status": status,
                "procurement_label": procurement_label,
                "planning_action": planning_action,
                "affects_start": affects_start,
                "employee_safe_label": employee_safe_label,
                "operator_note": operator_note,
                "procurement_override": override or None,
            }
        )
    return enriched


def derive_procurement_summary(items: List[dict]) -> Dict[str, Any]:
    critical_not_checked = sum(
        1
        for item in items
        if item.get("category") == CATEGORY_PROJECT_CRITICAL
        and str(item.get("procurement_status") or STATUS_NOT_CHECKED) == STATUS_NOT_CHECKED
    )
    awaiting_advance = sum(
        1
        for item in items
        if str(item.get("procurement_status") or "") == STATUS_AWAITING_ADVANCE
    )
    suggest_replenish = sum(
        1
        for item in items
        if str(item.get("procurement_status") or "") == STATUS_SUGGEST_REPLENISH
        or item.get("readiness_impact") == IMPACT_SUGGEST_REPLENISH
    )
    blocking_items = [item for item in items if item.get("affects_start")]
    return {
        "critical_materials_not_checked": critical_not_checked,
        "awaiting_advance_items": awaiting_advance,
        "suggest_replenishment_items": suggest_replenish,
        "blocking_items_count": len(blocking_items),
        "blocking_material_codes": [str(i.get("code") or "") for i in blocking_items if i.get("code")],
    }


def derive_production_planning_summary(
    readiness_by_id: Dict[str, dict],
    procurement_items: List[dict],
) -> Dict[str, Any]:
    proc_summary = derive_procurement_summary(procurement_items)
    eligible = sum(1 for r in readiness_by_id.values() if r.get("readiness_status") == "eligible")
    waiting_predecessor = sum(
        1 for r in readiness_by_id.values() if r.get("readiness_status") == "waiting_predecessor"
    )
    waiting_material = sum(
        1 for r in readiness_by_id.values() if r.get("readiness_status") == "waiting_material"
    )
    waiting_file = sum(
        1 for r in readiness_by_id.values() if r.get("readiness_status") == "waiting_file"
    )
    waiting_template = sum(
        1
        for r in readiness_by_id.values()
        if r.get("readiness_status") == "waiting_template_decision"
    )
    waiting_document = sum(
        1 for r in readiness_by_id.values() if r.get("readiness_status") == "waiting_document"
    )
    waiting_workshop = sum(
        1
        for r in readiness_by_id.values()
        if r.get("readiness_status") == "waiting_workshop_info"
    )
    manual_blocked = sum(
        1 for r in readiness_by_id.values() if r.get("readiness_status") == "blocked_manual"
    )

    suggested = "Verifică materialele critice înainte de producție."
    if waiting_file > 0:
        suggested = "Finalizează pregătirea fișierelor/vectorilor (vector_prep) înainte de CNC."
    elif waiting_template > 0:
        suggested = "Clarifică tipul de șablon și datele Forex înainte de CNC șablon."
    elif waiting_material > 0:
        suggested = "Rezolvă materialele blocate înainte de start pe taskurile afectate."
    elif proc_summary["awaiting_advance_items"] > 0:
        suggested = "Confirmă avansul / achiziția pentru materialele marcate awaiting advance."
    elif proc_summary["critical_materials_not_checked"] > 0:
        suggested = "Verifică materialele critice și setează statusul de aprovizionare."

    return {
        "eligible_tasks": eligible,
        "waiting_predecessor_tasks": waiting_predecessor,
        "waiting_material_tasks": waiting_material,
        "waiting_file_tasks": waiting_file,
        "waiting_template_tasks": waiting_template,
        "waiting_document_tasks": waiting_document,
        "waiting_workshop_info_tasks": waiting_workshop,
        "manual_blocked_tasks": manual_blocked,
        "critical_materials_not_checked": proc_summary["critical_materials_not_checked"],
        "awaiting_advance_items": proc_summary["awaiting_advance_items"],
        "suggest_replenishment_items": proc_summary["suggest_replenishment_items"],
        "suggested_next_action": suggested,
    }


def material_items_by_task(enriched_items: List[dict]) -> Dict[str, List[dict]]:
    by_task: Dict[str, List[dict]] = {}
    for item in enriched_items:
        for task_id in _effective_task_ids(item):
            by_task.setdefault(task_id, []).append(dict(item))
    return by_task


def blocking_materials_for_task(task_id: str, material_by_task: Dict[str, List[dict]]) -> List[dict]:
    return [item for item in material_by_task.get(task_id, []) if is_material_status_blocking(item)]


def employee_safe_material_hints_for_task(items: List[dict]) -> List[dict]:
    """Employee-safe hints (max 2) with procurement labels — no price/supplier/qty."""
    if not items:
        return []

    critical = [item for item in items if item.get("category") == CATEGORY_PROJECT_CRITICAL]
    low_cost = [
        item
        for item in items
        if item.get("category") in (CATEGORY_STANDARD_LOW_COST, CATEGORY_INDIRECT)
    ]

    hints: List[dict] = []
    for item in critical[:1]:
        hints.append(employee_safe_procurement_hint(item))

    if low_cost:
        if len(low_cost) == 1:
            hints.append(employee_safe_procurement_hint(low_cost[0]))
        else:
            hints.append(
                {
                    "name": "Consumabile montaj",
                    "category": CATEGORY_STANDARD_LOW_COST,
                    "label": "Verificare preventivă",
                    "status": STATUS_SUGGEST_REPLENISH,
                    "display_note": (
                        "Verifică consumabile montaj: adeziv, șuruburi, cablu, conectori — "
                        "alimentare preventivă dacă nivel scăzut."
                    ),
                }
            )

    return hints[:2]


def task_material_status_label(task_id: str, material_by_task: Dict[str, List[dict]]) -> Optional[str]:
    blocking = blocking_materials_for_task(task_id, material_by_task)
    if blocking:
        return str(blocking[0].get("employee_safe_label") or "Așteaptă material")
    critical = [
        item
        for item in material_by_task.get(task_id, [])
        if item.get("category") == CATEGORY_PROJECT_CRITICAL
    ]
    if critical:
        return str(critical[0].get("employee_safe_label") or "Verifică material")
    return None


async def load_material_procurement_statuses(
    db: AsyncSession,
    order_id: int,
) -> Dict[str, dict]:
    reality = (
        await db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
    ).scalar_one_or_none()
    if reality is None:
        return {}
    _, statuses = split_reality_task_entries(_parse_json_list(reality.tasks_json))
    return statuses


async def load_work_reality_tasks(db: AsyncSession, order_id: int) -> List[dict]:
    reality = (
        await db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
    ).scalar_one_or_none()
    if reality is None:
        return []
    work_tasks, _ = split_reality_task_entries(_parse_json_list(reality.tasks_json))
    return work_tasks


async def build_procurement_enriched_context(
    db: AsyncSession,
    *,
    order_id: int,
    plan_tasks: List[dict],
    product_context: Optional[str] = None,
) -> Tuple[List[dict], Dict[str, List[dict]], Dict[str, dict]]:
    statuses = await load_material_procurement_statuses(db, order_id)
    base_items = derive_material_planning_items(plan_tasks, product_context=product_context)
    enriched = apply_procurement_statuses(base_items, statuses)
    by_task = material_items_by_task(enriched)
    return enriched, by_task, statuses


def material_block_reason(item: dict) -> dict:
    status = str(item.get("procurement_status") or "")
    name = str(item.get("name") or item.get("code") or "Material")
    messages = {
        STATUS_AWAITING_ADVANCE: f"Așteaptă avans / confirmare achiziție pentru {name}.",
        STATUS_TO_ORDER: f"Material de comandat: {name}.",
        STATUS_ORDERED: f"Material comandat — așteaptă livrare: {name}.",
    }
    return {
        "code": "material_procurement_block",
        "material_code": str(item.get("code") or ""),
        "material_name": name,
        "status": status,
        "message": messages.get(status, f"Așteaptă material: {name}."),
    }


async def update_material_procurement_status(
    db: AsyncSession,
    *,
    order_id: int,
    material_code: str,
    status: str,
    note: Optional[str] = None,
    affected_task_ids: Optional[List[str]] = None,
    updated_by_user_id: Optional[str] = None,
    product_context: Optional[str] = None,
) -> dict[str, Any]:
    code = str(material_code or "").strip()
    if not code:
        raise HTTPException(status_code=422, detail={"error": "material_code_invalid"})
    normalized_status = str(status or "").strip()
    if normalized_status not in PROCUREMENT_STATUSES:
        raise HTTPException(status_code=422, detail={"error": "procurement_status_invalid"})

    if normalized_status in STATUSES_REQUIRING_NOTE and not str(note or "").strip():
        raise HTTPException(status_code=422, detail={"error": "procurement_note_required"})

    from models.execution_plan import ExecutionPlan

    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "execution_plan_not_found"})

    plan_tasks = operational_tasks_only(plan.tasks_json)
    plan_tasks = [pt for pt in plan_tasks if isinstance(pt, dict)]
    base_items = derive_material_planning_items(plan_tasks, product_context=product_context)
    known_codes = {str(item.get("code") or "") for item in base_items}
    if code not in known_codes:
        raise HTTPException(status_code=404, detail={"error": "material_code_not_in_planning"})

    plan_task_ids = {str(pt.get("task_id") or "") for pt in plan_tasks if pt.get("task_id")}
    cleaned_affected: List[str] = []
    for task_id in affected_task_ids or []:
        key = str(task_id or "").strip()
        if not key:
            continue
        if key not in plan_task_ids:
            raise HTTPException(status_code=422, detail={"error": "affected_task_id_invalid", "task_id": key})
        cleaned_affected.append(key)

    if not cleaned_affected:
        for item in base_items:
            if str(item.get("code") or "") == code:
                cleaned_affected = list(item.get("required_for_task_ids") or [])
                break

    reality = (
        await db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
    ).scalar_one_or_none()
    if reality is None:
        raise HTTPException(status_code=404, detail={"error": "execution_reality_not_found"})

    work_tasks, statuses = split_reality_task_entries(_parse_json_list(reality.tasks_json))
    now_iso = datetime.now(timezone.utc).isoformat()
    statuses[code] = {
        "status": normalized_status,
        "note": str(note or "").strip(),
        "affected_task_ids": cleaned_affected,
        "updated_by_user_id": str(updated_by_user_id or ""),
        "updated_at": now_iso,
    }
    reality.tasks_json = json.dumps(embed_procurement_in_reality_tasks(work_tasks, statuses))
    await db.commit()
    await db.refresh(reality)

    enriched = apply_procurement_statuses(base_items, statuses)
    updated_item = next((item for item in enriched if str(item.get("code") or "") == code), None)
    by_task = material_items_by_task(enriched)
    from services.task_readiness_service import evaluate_all_task_readiness

    readiness_by_id = evaluate_all_task_readiness(
        plan_tasks,
        work_tasks,
        material_by_task=by_task,
    )

    return {
        "order_id": order_id,
        "material_code": code,
        "material_item": updated_item,
        "procurement_summary": derive_procurement_summary(enriched),
        "production_planning_summary": derive_production_planning_summary(
            readiness_by_id,
            enriched,
        ),
        "readiness_snapshot": {
            task_id: {
                "readiness_status": payload.get("readiness_status"),
                "readiness_label": payload.get("readiness_label"),
                "is_startable": payload.get("is_startable"),
            }
            for task_id, payload in readiness_by_id.items()
        },
    }
