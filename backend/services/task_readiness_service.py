"""Task readiness evaluation — dependencies, manual blocks, employee assignment."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from services.material_procurement_status_service import (
    blocking_materials_for_task,
    material_block_reason,
    split_reality_task_entries,
)
from services.task_preparation_readiness_service import (
    MOUNTING_TEMPLATE_CNC_PROCESS_ID,
    VINYL_APPLICATION_PROCESS_ID,
    classify_predecessor_readiness_status,
    evaluate_mounting_template_cnc_gate,
    evaluate_vinyl_application_gate,
)
from services.task_work_session_service import derive_task_status_from_sessions, sessions_for_task

READINESS_DONE = "done"
READINESS_IN_PROGRESS = "in_progress"
READINESS_BLOCKED_MANUAL = "blocked_manual"
READINESS_WAITING_PREDECESSOR = "waiting_predecessor"
READINESS_WAITING_MATERIAL = "waiting_material"
READINESS_WAITING_FILE = "waiting_file"
READINESS_WAITING_TEMPLATE_DECISION = "waiting_template_decision"
READINESS_WAITING_DOCUMENT = "waiting_document"
READINESS_WAITING_WORKSHOP_INFO = "waiting_workshop_info"
READINESS_ELIGIBLE = "eligible"
READINESS_ASSIGNED_NOT_MINE = "assigned_not_mine"
READINESS_UNASSIGNED = "unassigned"

READINESS_LABELS: Dict[str, str] = {
    READINESS_DONE: "Finalizat",
    READINESS_IN_PROGRESS: "În lucru",
    READINESS_BLOCKED_MANUAL: "Blocat",
    READINESS_WAITING_PREDECESSOR: "Așteaptă task anterior",
    READINESS_WAITING_MATERIAL: "Așteaptă material",
    READINESS_WAITING_FILE: "Așteaptă pregătire fișiere/vectori",
    READINESS_WAITING_TEMPLATE_DECISION: "Așteaptă decizie șablon",
    READINESS_WAITING_DOCUMENT: "Așteaptă documente",
    READINESS_WAITING_WORKSHOP_INFO: "Așteaptă info atelier",
    READINESS_ELIGIBLE: "Eligibil acum",
    READINESS_ASSIGNED_NOT_MINE: "Alt post",
    READINESS_UNASSIGNED: "Neatribuit",
}

CODE_PREDECESSOR_NOT_DONE = "predecessor_not_done"
CODE_PREDECESSOR_NOT_DONE_IN_PROGRESS = "predecessor_not_done_while_in_progress"
CODE_MATERIAL_PROCUREMENT_BLOCK = "material_procurement_block"


def _normalize_employee_id(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _task_display_name(plan_task: dict) -> str:
    for key in ("display_name", "name", "title"):
        val = str(plan_task.get(key) or "").strip()
        if val and ":" not in val:
            return val
        if val:
            return val.split(":")[-1]
    return str(plan_task.get("task_id") or "")


def build_readiness_context(
    plan_tasks: List[dict],
    reality_tasks: List[dict],
) -> Dict[str, Any]:
    """Build shared lookup maps for readiness evaluation on one order."""
    work_reality_tasks, _ = split_reality_task_entries(reality_tasks)
    plan_by_id: Dict[str, dict] = {}
    name_by_id: Dict[str, str] = {}
    status_by_id: Dict[str, str] = {}

    for pt in plan_tasks:
        if not isinstance(pt, dict):
            continue
        task_id = str(pt.get("task_id") or "").strip()
        if not task_id:
            continue
        plan_by_id[task_id] = pt
        name_by_id[task_id] = _task_display_name(pt)

    for task_id in plan_by_id:
        sessions = sessions_for_task(work_reality_tasks, task_id)
        status_by_id[task_id] = derive_task_status_from_sessions(sessions)

    return {
        "plan_by_id": plan_by_id,
        "name_by_id": name_by_id,
        "status_by_id": status_by_id,
    }


def _unsatisfied_predecessors(
    plan_task: dict,
    context: Dict[str, Any],
) -> Tuple[List[str], List[dict]]:
    status_by_id: Dict[str, str] = context["status_by_id"]
    name_by_id: Dict[str, str] = context["name_by_id"]
    blocking_ids: List[str] = []
    reasons: List[dict] = []

    for pred_id in plan_task.get("depends_on_task_ids") or []:
        key = str(pred_id or "").strip()
        if not key:
            continue
        pred_status = status_by_id.get(key, "assigned")
        if pred_status != "done":
            blocking_ids.append(key)
            pred_name = name_by_id.get(key, key)
            reasons.append(
                {
                    "code": CODE_PREDECESSOR_NOT_DONE,
                    "label": "Task anterior nefinalizat",
                    "blocking": True,
                    "responsible_domain": "other",
                    "task_id": key,
                    "depends_on_task_id": key,
                    "task_name": pred_name,
                    "missing_item": key,
                    "message": f"Așteaptă finalizarea: {pred_name}",
                }
            )
    return blocking_ids, reasons


def _material_warning_for_task(
    task_id: str,
    material_by_task: Optional[Dict[str, List[dict]]],
) -> Optional[str]:
    if not material_by_task:
        return None
    blocking = blocking_materials_for_task(task_id, material_by_task)
    if not blocking:
        return None
    first = blocking[0]
    return str(material_block_reason(first).get("message") or "")


def _preparation_gate_reasons(
    plan_task: dict,
    *,
    quote_input: Optional[dict] = None,
) -> List[dict]:
    process_id = str(plan_task.get("process_id") or "").strip().lower()
    qi = quote_input or {}
    if process_id == MOUNTING_TEMPLATE_CNC_PROCESS_ID:
        return evaluate_mounting_template_cnc_gate(qi)
    if process_id == VINYL_APPLICATION_PROCESS_ID:
        return evaluate_vinyl_application_gate(qi)
    return []


def _enrich_reasons_with_labels(reasons: List[dict]) -> List[dict]:
    enriched: List[dict] = []
    for reason in reasons:
        if not isinstance(reason, dict):
            continue
        row = dict(reason)
        if not row.get("label"):
            row["label"] = str(row.get("code") or "blocking")
        if "blocking" not in row:
            row["blocking"] = True
        enriched.append(row)
    return enriched


def evaluate_task_readiness(
    plan_task: dict,
    context: Dict[str, Any],
    *,
    employee_id: Optional[int] = None,
    material_by_task: Optional[Dict[str, List[dict]]] = None,
    quote_input: Optional[dict] = None,
) -> dict[str, Any]:
    """Evaluate readiness for one planned task."""
    task_id = str(plan_task.get("task_id") or "").strip()
    status = context["status_by_id"].get(task_id, "assigned")
    assigned_id = _normalize_employee_id(plan_task.get("assigned_employee_id"))
    blocking_ids, pred_reasons = _unsatisfied_predecessors(plan_task, context)
    material_blocking = blocking_materials_for_task(task_id, material_by_task or {})
    material_reasons = _enrich_reasons_with_labels(
        [material_block_reason(item) for item in material_blocking]
    )
    prep_reasons = _enrich_reasons_with_labels(
        _preparation_gate_reasons(plan_task, quote_input=quote_input)
    )
    material_warning = _material_warning_for_task(task_id, material_by_task)

    blocking_tasks = [
        {"task_id": bid, "name": context["name_by_id"].get(bid, bid)} for bid in blocking_ids
    ]

    base: Dict[str, Any] = {
        "readiness_reasons": [],
        "blocking_reasons": [],
        "blocking_task_ids": blocking_ids,
        "blocking_tasks": blocking_tasks,
        "blocking_materials": [
            {
                "code": item.get("code"),
                "name": item.get("name"),
                "status": item.get("procurement_status"),
                "label": item.get("procurement_label"),
            }
            for item in material_blocking
        ],
        "dependency_warning": None,
        "material_warning": material_warning,
        "is_startable": False,
    }

    def _blocked(status: str, label: str, reasons: List[dict]) -> dict[str, Any]:
        merged = _enrich_reasons_with_labels(reasons)
        return {
            **base,
            "readiness_status": status,
            "readiness_label": label,
            "readiness_reasons": merged,
            "blocking_reasons": merged,
            "is_startable": False,
        }

    if status == "done":
        return {
            **base,
            "readiness_status": READINESS_DONE,
            "readiness_label": READINESS_LABELS[READINESS_DONE],
            "is_startable": False,
        }

    if status == "blocked":
        return {
            **base,
            "readiness_status": READINESS_BLOCKED_MANUAL,
            "readiness_label": READINESS_LABELS[READINESS_BLOCKED_MANUAL],
            "is_startable": False,
        }

    if status == "in_progress":
        reasons = list(pred_reasons)
        dependency_warning = None
        if blocking_ids:
            dependency_warning = "A pornit înainte de finalizarea dependențelor"
            for reason in reasons:
                copy = dict(reason)
                copy["code"] = CODE_PREDECESSOR_NOT_DONE_IN_PROGRESS
                base["readiness_reasons"].append(copy)
        return {
            **base,
            "readiness_status": READINESS_IN_PROGRESS,
            "readiness_label": READINESS_LABELS[READINESS_IN_PROGRESS],
            "readiness_reasons": base["readiness_reasons"],
            "dependency_warning": dependency_warning,
            "is_startable": False,
        }

    if blocking_ids:
        file_status = classify_predecessor_readiness_status(
            pred_reasons,
            context.get("plan_by_id") or {},
        )
        if file_status == READINESS_WAITING_FILE:
            file_reasons = []
            for reason in pred_reasons:
                copy = dict(reason)
                copy["code"] = "vector_prep_not_done"
                copy["label"] = "Pregătire vector nefinalizată"
                copy["responsible_domain"] = "instrumentation"
                copy["message"] = (
                    "Finalizează vector_prep înainte de debitare CNC / execuție fizică."
                )
                file_reasons.append(copy)
            return _blocked(
                READINESS_WAITING_FILE,
                READINESS_LABELS[READINESS_WAITING_FILE],
                file_reasons,
            )
        return _blocked(
            READINESS_WAITING_PREDECESSOR,
            READINESS_LABELS[READINESS_WAITING_PREDECESSOR],
            pred_reasons,
        )

    if prep_reasons:
        return _blocked(
            READINESS_WAITING_TEMPLATE_DECISION
            if any(
                str(r.get("code", "")).startswith("template_") for r in prep_reasons
            )
            else READINESS_WAITING_FILE,
            READINESS_LABELS[
                READINESS_WAITING_TEMPLATE_DECISION
                if any(str(r.get("code", "")).startswith("template_") for r in prep_reasons)
                else READINESS_WAITING_FILE
            ],
            prep_reasons,
        )

    if material_blocking:
        return _blocked(
            READINESS_WAITING_MATERIAL,
            READINESS_LABELS[READINESS_WAITING_MATERIAL],
            material_reasons,
        )

    if employee_id is not None:
        if assigned_id is None:
            return {
                **base,
                "readiness_status": READINESS_UNASSIGNED,
                "readiness_label": READINESS_LABELS[READINESS_UNASSIGNED],
                "is_startable": False,
            }
        if assigned_id != employee_id:
            return {
                **base,
                "readiness_status": READINESS_ASSIGNED_NOT_MINE,
                "readiness_label": READINESS_LABELS[READINESS_ASSIGNED_NOT_MINE],
                "is_startable": False,
            }

    return {
        **base,
        "readiness_status": READINESS_ELIGIBLE,
        "readiness_label": READINESS_LABELS[READINESS_ELIGIBLE],
        "readiness_reasons": [],
        "blocking_reasons": [],
        "is_startable": True,
    }


def evaluate_all_task_readiness(
    plan_tasks: List[dict],
    reality_tasks: List[dict],
    *,
    employee_id: Optional[int] = None,
    material_by_task: Optional[Dict[str, List[dict]]] = None,
    quote_input: Optional[dict] = None,
) -> Dict[str, dict]:
    context = build_readiness_context(plan_tasks, reality_tasks)
    result: Dict[str, dict] = {}
    for pt in plan_tasks:
        if not isinstance(pt, dict):
            continue
        tid = str(pt.get("task_id") or "").strip()
        if not tid:
            continue
        result[tid] = evaluate_task_readiness(
            pt,
            context,
            employee_id=employee_id,
            material_by_task=material_by_task,
            quote_input=quote_input,
        )
    return result


def employee_safe_readiness_payload(readiness: dict) -> dict:
    """Strip any fields that must not leak to employee mobile."""
    safe_reasons = []
    for reason in readiness.get("readiness_reasons") or []:
        if not isinstance(reason, dict):
            continue
        safe_reasons.append(
            {
                "code": reason.get("code"),
                "label": reason.get("label"),
                "task_id": reason.get("task_id"),
                "depends_on_task_id": reason.get("depends_on_task_id"),
                "task_name": reason.get("task_name"),
                "material_code": reason.get("material_code"),
                "material_name": reason.get("material_name"),
                "status": reason.get("status"),
                "missing_item": reason.get("missing_item"),
                "message": reason.get("message"),
            }
        )
    return {
        "readiness_status": str(readiness.get("readiness_status") or ""),
        "readiness_label": str(readiness.get("readiness_label") or ""),
        "is_startable": bool(readiness.get("is_startable")),
        "readiness_reasons": safe_reasons,
        "blocking_reasons": safe_reasons,
        "blocking_task_ids": readiness.get("blocking_task_ids") or [],
        "blocking_tasks": readiness.get("blocking_tasks") or [],
        "dependency_warning": readiness.get("dependency_warning"),
        "material_warning": readiness.get("material_warning"),
    }
