"""Employee-safe read-only order blueprint — limited view for mobile workers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from services.task_work_session_service import employee_safe_helper_count
from services.employee_mobile_tasks_service import _load_plan_and_reality_tasks, list_my_tasks
from services.material_procurement_status_service import (
    build_procurement_enriched_context,
    employee_safe_material_hints_for_task,
    task_material_status_label,
)
from services.order_production_blueprint_service import get_order_production_blueprint
from services.task_readiness_service import (
    READINESS_IN_PROGRESS,
    employee_safe_readiness_payload,
    evaluate_all_task_readiness,
)
from sqlalchemy.ext.asyncio import AsyncSession


def _stage_label(process_type: str, machine_type: str) -> str:
    machine = (machine_type or "").upper()
    process = (process_type or "").lower()
    if machine in ("ASSEMBLY", "ASSEMBLY_TABLE") or "assembly" in process:
        return "Asamblare"
    if "RETURN_PROFILE" in machine or process == "edge_bending":
        return "Pregătire / Canturi"
    if "LED" in machine or process in ("led_assembly", "led_wiring"):
        return "LED / Electric"
    if "CNC" in machine or process == "cnc_routing":
        return "Prelucrare CNC"
    if "QC" in machine or process == "quality_control":
        return "Control calitate"
    if process == "print" or "PREPRESS" in machine:
        return "Grafică / Prepress"
    if "PACK" in machine or process == "packaging":
        return "Ambalare"
    return "Execuție"


def _employee_status_display(*, is_mine: bool, status_key: str) -> str:
    if is_mine:
        if status_key == "done":
            return "Finalizat"
        if status_key == "blocked":
            return "Blocat"
        if status_key == "in_progress":
            return "În lucru"
        return "Alocat"
    if status_key == "unassigned":
        return "Neatribuit"
    if status_key == "done":
        return "Finalizat"
    if status_key == "blocked":
        return "Blocat"
    if status_key == "in_progress":
        return "În lucru"
    return "De făcut"


async def get_employee_my_order_blueprint(
    db: AsyncSession,
    *,
    order_id: int,
    employee_id: int,
) -> dict[str, Any]:
    """Read-only employee blueprint for one order where the worker has assigned tasks."""
    my_rows = await list_my_tasks(db, employee_id)
    my_on_order = [row for row in my_rows if int(row["order_id"]) == order_id]
    if not my_on_order:
        raise HTTPException(status_code=403, detail={"error": "order_not_accessible_to_employee"})

    my_task_ids = {str(row["task_id"]) for row in my_on_order}
    my_by_task = {str(row["task_id"]): row for row in my_on_order}
    client_label = str(my_on_order[0].get("client") or "").strip()

    full = await get_order_production_blueprint(db, order_id)
    order_code = str(full.get("order_code") or full.get("order_label") or f"Comandă #{order_id}")

    plan_tasks, reality_tasks = await _load_plan_and_reality_tasks(db, order_id)
    product_template = str(full.get("product_template") or "").strip() or None
    _enriched, material_by_task, _statuses = await build_procurement_enriched_context(
        db,
        order_id=order_id,
        plan_tasks=plan_tasks,
        product_context=product_template,
    )
    readiness_by_id = evaluate_all_task_readiness(
        plan_tasks,
        reality_tasks,
        employee_id=employee_id,
        material_by_task=material_by_task,
    )

    my_done = 0
    my_in_progress = 0
    my_blocked = 0
    mobile_tasks: list[dict[str, Any]] = []
    current_task_id: str | None = None

    for task in full["tasks"]:
        task_id = str(task["task_id"])
        is_mine = task_id in my_task_ids
        status_key = str(task.get("status") or "")

        if is_mine:
            if status_key == "done":
                my_done += 1
            elif status_key == "blocked":
                my_blocked += 1
            elif status_key == "in_progress":
                my_in_progress += 1

        active_workers = task.get("active_workers") or []
        readiness = employee_safe_readiness_payload(readiness_by_id.get(task_id, {}))
        is_startable = bool(readiness.get("is_startable"))
        readiness_status = str(readiness.get("readiness_status") or "")
        mine_row = my_by_task.get(task_id) or {}
        mobile_tasks.append(
            {
                "task_id": task_id,
                "name": task.get("name") or task_id,
                "status_display": _employee_status_display(is_mine=is_mine, status_key=status_key),
                "is_mine": is_mine,
                "is_current": False,
                "is_eligible_for_me": is_mine
                and (
                    is_startable
                    or readiness_status == READINESS_IN_PROGRESS
                ),
                # Phase 2: split flags — never overload a single can_assist boolean.
                "can_assist": False,
                "visible_as_principal": bool(mine_row.get("visible_as_principal", is_mine)),
                "visible_as_helper": bool(mine_row.get("visible_as_helper", False)),
                "can_view_help": bool(mine_row.get("can_view_help", False)),
                "can_accept_help": bool(mine_row.get("can_accept_help", False)),
                "can_start_helper_work": bool(mine_row.get("can_start_helper_work", False)),
                "can_stop_own_session": bool(mine_row.get("can_stop_own_session", False)),
                "can_complete_operation": bool(
                    mine_row.get("can_complete_operation", is_mine and mine_row.get("visible_as_principal", is_mine))
                )
                if is_mine
                else False,
                "eligibility_reason": "assigned_to_me"
                if mine_row.get("visible_as_principal")
                else ("helper_member" if mine_row.get("visible_as_helper") else "other_post"),
                "active_helper_count": employee_safe_helper_count(
                    active_workers,
                    viewer_employee_id=employee_id,
                )
                if is_mine
                else 0,
                "stage_label": _stage_label(
                    str(task.get("process_type") or ""),
                    str(task.get("machine_type") or ""),
                ),
                "has_documents": bool(task.get("documents_count", 0)),
                "has_instructions": bool(task.get("has_instructions")),
                "material_hints": employee_safe_material_hints_for_task(
                    material_by_task.get(task_id, [])
                ),
                "material_status_label": task_material_status_label(
                    task_id,
                    material_by_task,
                ),
                **readiness,
            }
        )

    for task in mobile_tasks:
        if not task["is_mine"]:
            continue
        if task.get("readiness_status") == READINESS_IN_PROGRESS:
            current_task_id = str(task["task_id"])
            break

    if not current_task_id:
        for task in mobile_tasks:
            if task["is_mine"] and task.get("is_startable"):
                current_task_id = str(task["task_id"])
                break

    if current_task_id:
        for task in mobile_tasks:
            task["is_current"] = task["task_id"] == current_task_id

    overall = full.get("summary") or {}
    my_tasks_count = len(my_task_ids)
    my_progress = round((my_done / my_tasks_count) * 100) if my_tasks_count > 0 else 0

    return {
        "order_id": order_id,
        "order_label": order_code,
        "client_label": client_label,
        "summary": {
            "total_tasks": int(overall.get("total_tasks") or 0),
            "my_tasks": my_tasks_count,
            "my_done": my_done,
            "overall_progress_percent": int(overall.get("progress_percent") or 0),
            "my_progress_percent": my_progress,
            "blocked": my_blocked,
            "in_progress": my_in_progress,
        },
        "current_task_id": current_task_id,
        "tasks": mobile_tasks,
    }
