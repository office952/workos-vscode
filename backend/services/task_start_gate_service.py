"""Unified task start gate — all execution start paths must pass through here."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import HTTPException
from models.execution_plan import ExecutionPlan
from services.employee_mobile_tasks_service import build_procurement_enriched_context
from services.execution_plan_operational_readiness_service import (
    assert_operational_mutation_allowed,
)
from services.execution_plan_task_parser import operational_tasks_only
from services.task_preparation_readiness_service import extract_quote_input_from_snapshot
from services.task_readiness_service import (
    READINESS_WAITING_FILE,
    READINESS_WAITING_MATERIAL,
    READINESS_WAITING_PREDECESSOR,
    READINESS_WAITING_TEMPLATE_DECISION,
    build_readiness_context,
    evaluate_task_readiness,
)
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

OVERRIDE_ALLOWED_ROLES = frozenset({"admin", "operator"})


def _parse_json_list(raw: Any) -> list:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _parse_json_object(raw: Any) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def readiness_block_message(readiness: dict) -> str:
    status = str(readiness.get("readiness_status") or "")
    if status == READINESS_WAITING_MATERIAL:
        return "Taskul așteaptă material."
    if status == READINESS_WAITING_FILE:
        return "Așteaptă pregătirea fișierelor/vectorilor — finalizează vector_prep înainte de CNC."
    if status == READINESS_WAITING_TEMPLATE_DECISION:
        return "Așteaptă decizia tipului de șablon sau datele Forex necesare."
    if status == READINESS_WAITING_PREDECESSOR:
        return "Taskul așteaptă finalizarea unor operații anterioare."
    reasons = readiness.get("readiness_reasons") or []
    if reasons and isinstance(reasons[0], dict):
        msg = str(reasons[0].get("message") or "").strip()
        if msg:
            return msg
    return "Taskul nu este eligibil pentru start."


def task_not_ready_http_exception(readiness: dict) -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={
            "code": "task_not_ready",
            "error": "task_not_ready",
            "message": readiness_block_message(readiness),
            "readiness_status": readiness.get("readiness_status"),
            "readiness_label": readiness.get("readiness_label"),
            "blocking_task_ids": readiness.get("blocking_task_ids") or [],
            "readiness_reasons": readiness.get("readiness_reasons") or [],
            "blocking_reasons": readiness.get("blocking_reasons") or [],
        },
    )


def _override_is_valid(
    *,
    override_readiness: bool,
    override_reason: Optional[str],
    user_role: Optional[str],
) -> bool:
    if not override_readiness:
        return False
    reason = str(override_reason or "").strip()
    if len(reason) < 3:
        return False
    role = str(user_role or "").strip().lower()
    return role in OVERRIDE_ALLOWED_ROLES


def build_readiness_override_metadata(
    *,
    user_id: str,
    user_name: str,
    reason: str,
    readiness_status: str,
) -> dict[str, Any]:
    return {
        "readiness_override": True,
        "readiness_override_reason": reason,
        "readiness_override_by_user_id": user_id,
        "readiness_override_by_user_name": user_name,
        "readiness_override_at_status": readiness_status,
    }


async def load_order_quote_input(db: AsyncSession, order_id: int) -> dict[str, Any]:
    row = (
        await db.execute(
            text("SELECT snapshot_line_items FROM orders WHERE id = :oid LIMIT 1"),
            {"oid": order_id},
        )
    ).mappings().first()
    if not row:
        return {}
    return extract_quote_input_from_snapshot(_parse_json_object(row.get("snapshot_line_items")))


async def evaluate_task_start_readiness(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: Optional[int] = None,
) -> tuple[dict, dict, dict]:
    """Return (plan_task, readiness, quote_input)."""
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "execution_plan_not_found"})

    assert_operational_mutation_allowed(plan)

    plan_tasks = operational_tasks_only(plan.tasks_json)
    plan_task = next(
        (pt for pt in plan_tasks if isinstance(pt, dict) and pt.get("task_id") == task_id),
        None,
    )
    if plan_task is None:
        raise HTTPException(status_code=404, detail={"error": "task_not_in_plan"})

    reality_row = (
        await db.execute(
            text("SELECT tasks_json FROM execution_reality WHERE order_id = :oid LIMIT 1"),
            {"oid": order_id},
        )
    ).mappings().first()
    raw_reality = _parse_json_list(reality_row.get("tasks_json") if reality_row else "[]")

    _enriched, material_by_task, _ = await build_procurement_enriched_context(
        db,
        order_id=order_id,
        plan_tasks=plan_tasks,
        product_context=None,
    )
    quote_input = await load_order_quote_input(db, order_id)
    context = build_readiness_context(plan_tasks, raw_reality)
    readiness = evaluate_task_readiness(
        plan_task,
        context,
        employee_id=employee_id,
        material_by_task=material_by_task,
        quote_input=quote_input,
    )
    return plan_task, readiness, quote_input


async def assert_task_startable(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: Optional[int] = None,
    override_readiness: bool = False,
    override_reason: Optional[str] = None,
    override_user_id: Optional[str] = None,
    override_user_name: Optional[str] = None,
    override_user_role: Optional[str] = None,
) -> Dict[str, Any]:
    """Raise HTTP 409 when task cannot start; return readiness + optional override metadata."""
    _plan_task, readiness, _quote_input = await evaluate_task_start_readiness(
        db,
        order_id=order_id,
        task_id=task_id,
        employee_id=employee_id,
    )

    if readiness.get("is_startable"):
        return {"readiness": readiness, "override_metadata": None}

    if _override_is_valid(
        override_readiness=override_readiness,
        override_reason=override_reason,
        user_role=override_user_role,
    ):
        override_metadata = build_readiness_override_metadata(
            user_id=str(override_user_id or ""),
            user_name=str(override_user_name or ""),
            reason=str(override_reason or "").strip(),
            readiness_status=str(readiness.get("readiness_status") or ""),
        )
        return {"readiness": readiness, "override_metadata": override_metadata}

    raise task_not_ready_http_exception(readiness)
