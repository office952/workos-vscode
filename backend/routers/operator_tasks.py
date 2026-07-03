"""
Operator Tasks router — lightweight endpoints for Shop Floor + Operator View.

Provides:
  GET  /api/v1/operator/tasks                              → all tasks from execution plans, enriched
  GET  /api/v1/operator/tasks/mine                         → tasks for a specific operator (query param)
  GET  /api/v1/operator/orders/{order_id}/production-blueprint → read-only order task blueprint
  POST /api/v1/operator/task-action                        → start / pause / complete / block a task
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import has_permission, require_permission, resolve_effective_role
from schemas.auth import UserResponse
from models.execution_plan import ExecutionPlan
from services.execution_plan_operational_readiness_service import (
    evaluate_execution_plan_operational_readiness,
    readiness_result_to_api_fields,
)
from services.execution_plan_task_parser import operational_tasks_only
from services.material_procurement_status_service import (
    PROCUREMENT_STATUSES,
    update_material_procurement_status,
)
from services.order_production_blueprint_service import get_order_production_blueprint
from services.volumetric_execution_dispatch import (
    extract_order_snapshot_context,
    resolve_execution_task_display_name,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/operator",
    tags=["operator"],
    dependencies=[Depends(get_current_user)],
)


class TaskActionRequest(BaseModel):
    order_id: int
    task_id: str
    action: str  # "start" | "pause" | "complete" | "block"
    operator_name: Optional[str] = None
    employee_id: Optional[int] = None  # canonical Employee.id from operational registry
    reason: Optional[str] = None
    completion_notes: Optional[str] = None
    override_readiness: bool = False
    override_reason: Optional[str] = None


class MaterialProcurementPatchBody(BaseModel):
    status: str
    note: Optional[str] = None
    affected_task_ids: Optional[List[str]] = Field(default=None)


_TASK_ACTION_PERMISSION_MAP: Dict[str, str] = {
    "start": "execution.task_start",
    "complete": "execution.task_complete",
    "pause": "execution.task_block",
    "block": "execution.task_block",
    "resume": "execution.task_start",
    "unblock": "execution.task_block",
}


def _assert_task_action_permission(current_user: UserResponse, action: str) -> None:
    permission_key = _TASK_ACTION_PERMISSION_MAP.get(action)
    if not permission_key:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    effective_role = resolve_effective_role(current_user.role)
    if not has_permission(effective_role, permission_key):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "permission_denied",
                "permission": permission_key,
                "role": effective_role,
                "message": f"Role '{effective_role}' does not have permission '{permission_key}'",
            },
        )


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


def _parse_json(val: Any) -> list:
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return []
    return []


@router.get("/tasks")
async def list_all_tasks(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Return all tasks from all execution plans, enriched with order info and reality status."""
    try:
        # Get all execution plans
        plans_sql = text(
            "SELECT ep.id, ep.order_id, ep.order_code, ep.tasks_json, "
            "ep.total_estimated_time_minutes "
            "FROM execution_plan ep "
            "ORDER BY ep.order_id ASC"
        )
        plans_result = await db.execute(plans_sql)
        plans = list(plans_result.mappings())

        # Get all execution realities
        reality_sql = text(
            "SELECT er.order_id, er.tasks_json "
            "FROM execution_reality er"
        )
        reality_result = await db.execute(reality_sql)
        reality_map: Dict[int, list] = {}
        for r in reality_result.mappings():
            reality_map[r["order_id"]] = _parse_json(r["tasks_json"])

        # Get orders for client/product context
        orders_sql = text(
            "SELECT o.id, o.code, o.status, o.client_name, o.quote_code, o.snapshot_line_items, "
            "q.intake_code "
            "FROM orders o "
            "LEFT JOIN quotes q ON q.id = o.quote_id "
            "WHERE o.id IN (SELECT DISTINCT order_id FROM execution_plan)"
        )
        orders_result = await db.execute(orders_sql)
        orders_map: Dict[int, dict] = {}
        for o in orders_result.mappings():
            snapshot = _parse_json_object(o.get("snapshot_line_items"))
            ctx = extract_order_snapshot_context(
                snapshot,
                client_name=str(o.get("client_name") or ""),
                quote_code=str(o.get("quote_code") or ""),
                intake_code=str(o.get("intake_code") or ""),
            )
            orders_map[int(o["id"])] = {
                "code": o["code"],
                "status": o["status"],
                "client": ctx.get("client") or str(o.get("client_name") or ""),
                "product": ctx.get("product") or "",
                "product_template": ctx.get("product_template") or "",
                "quote_code": ctx.get("quote_code") or str(o.get("quote_code") or ""),
                "intake_code": ctx.get("intake_code") or "",
                "layer_context": ctx.get("layer_context") or [],
                "work_intake_v2": bool(ctx.get("intake_code")),
            }

        employees_sql = text("SELECT id, name FROM employees WHERE status = 'active'")
        employee_names: Dict[int, str] = {
            int(row[0]): str(row[1])
            for row in (await db.execute(employees_sql)).all()
            if row[0] is not None
        }

        # Build enriched task list
        all_tasks: List[Dict[str, Any]] = []
        order_operational_readiness: Dict[int, Dict[str, Any]] = {}
        for plan in plans:
            order_id = int(plan["order_id"])
            order_code = plan["order_code"] or ""
            plan_row = ExecutionPlan(
                id=int(plan["id"]),
                order_id=order_id,
                order_code=order_code,
                snapshot_version=1,
                tasks_json=plan["tasks_json"],
                total_estimated_time_minutes=float(plan.get("total_estimated_time_minutes") or 0),
            )
            order_operational_readiness[order_id] = readiness_result_to_api_fields(
                evaluate_execution_plan_operational_readiness(plan_row)
            )
            tasks = operational_tasks_only(plan["tasks_json"])
            reality_tasks = reality_map.get(order_id, [])

            # Build reality lookup by task_id
            reality_lookup: Dict[str, dict] = {}
            for rt in reality_tasks:
                if isinstance(rt, dict):
                    reality_lookup[rt.get("task_id", "")] = rt

            order_info = orders_map.get(order_id, {})

            for t in tasks:
                if not isinstance(t, dict):
                    continue
                task_id = t.get("task_id", "")
                rt = reality_lookup.get(task_id, {})

                # AUDIT FIX (Task 11 + 12): Derive status correctly from
                # reality timestamps including pause/block states.
                # Priority: ended_at > blocked_at > paused_at > started_at > assigned
                started_at = rt.get("started_at")
                ended_at = rt.get("ended_at")
                blocked_at = rt.get("blocked_at")
                unblocked_at = rt.get("unblocked_at")
                paused_at = rt.get("paused_at")
                resumed_at = rt.get("resumed_at")
                block_reason = rt.get("block_reason") or rt.get("blocked_reason")

                if ended_at:
                    status = "done"
                elif blocked_at and not unblocked_at:
                    status = "blocked"
                elif paused_at and not resumed_at:
                    status = "paused"
                elif started_at:
                    status = "in_progress"
                else:
                    status = "assigned"

                # AUDIT FIX (Task 12): Calculate actual_minutes from
                # started_at and ended_at at read time. Never hardcode 0.
                actual_minutes = rt.get("actual_minutes")
                if actual_minutes is None or actual_minutes == 0:
                    if started_at and ended_at:
                        try:
                            from datetime import datetime as _dt
                            _start = _dt.fromisoformat(started_at.replace("Z", "+00:00"))
                            _end = _dt.fromisoformat(ended_at.replace("Z", "+00:00"))
                            actual_minutes = round((_end - _start).total_seconds() / 60.0, 2)
                        except (ValueError, TypeError):
                            actual_minutes = None
                    else:
                        actual_minutes = None

                employee_id = rt.get("employee_id")
                operator_name = rt.get("operator_name")
                employee_name = rt.get("employee_name")
                assigned_employee_id = t.get("assigned_employee_id")
                if assigned_employee_id is not None:
                    try:
                        assigned_employee_id = int(assigned_employee_id)
                    except (TypeError, ValueError):
                        assigned_employee_id = None

                process_id = str(t.get("process_id") or "")
                process_type = str(t.get("process_type") or "")
                display_name = t.get("display_name") or t.get("name") or ""
                if not display_name or ":" in display_name:
                    display_name = resolve_execution_task_display_name(
                        process_id=process_id or display_name.split(":")[-1],
                        process_type=process_type,
                        product_id=order_info.get("product_template") or None,
                    )

                layer_context = order_info.get("layer_context") or []
                primary_layer = layer_context[0] if layer_context else {}

                all_tasks.append({
                    "task_id": task_id,
                    "order_id": order_id,
                    "order_code": order_code,
                    "name": display_name,
                    "display_name": display_name,
                    "technical_name": t.get("technical_name") or t.get("name", ""),
                    "process_id": process_id,
                    "process_type": process_type,
                    "machine_type": t.get("machine_type", ""),
                    "estimated_time_minutes": t.get("estimated_time_minutes", 0),
                    "quantity": t.get("quantity", 0),
                    "layer_id": t.get("layer_id", ""),
                    "status": status,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "blocked_at": blocked_at,
                    "block_reason": block_reason,
                    "paused_at": paused_at,
                    "actual_minutes": actual_minutes,
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "operator_name": operator_name,
                    "assigned_employee_id": assigned_employee_id,
                    "assigned_employee_name": employee_names.get(assigned_employee_id)
                    if assigned_employee_id
                    else None,
                    "client": order_info.get("client", ""),
                    "product": order_info.get("product", ""),
                    "product_template": order_info.get("product_template", ""),
                    "quote_code": order_info.get("quote_code", ""),
                    "intake_code": order_info.get("intake_code", ""),
                    "work_intake_v2": order_info.get("work_intake_v2", False),
                    "material": primary_layer.get("material") or "",
                    "finish": primary_layer.get("finish") or "",
                    "order_status": order_info.get("status", ""),
                    "instructions": str(t.get("instructions") or "").strip(),
                })

        return {
            "tasks": all_tasks,
            "total": len(all_tasks),
            "order_operational_readiness": order_operational_readiness,
        }

    except Exception as e:
        logger.error(f"Error listing operator tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task-action")
async def perform_task_action(
    req: TaskActionRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("operator.task_action")),
    current_user: UserResponse = Depends(get_current_user),
) -> Dict[str, Any]:
    """Perform a task action: start, pause, complete, or block.

    This is a lightweight wrapper that delegates to the execution reality service
    for start/end, and handles pause/block as status annotations.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    _assert_task_action_permission(current_user, req.action)

    if req.action == "start":
        from services.execution_reality_service import ExecutionRealityService, RealityInputError
        from services.execution_reality_workforce import resolve_task_workforce_context
        from services.operator_employee_guard import OperatorEmployeeGuard

        process_type = ""
        machine_type = ""
        plan_sql = text(
            "SELECT tasks_json FROM execution_plan WHERE order_id = :oid LIMIT 1"
        )
        plan_row = (await db.execute(plan_sql, {"oid": req.order_id})).mappings().first()
        if plan_row:
            for pt in operational_tasks_only(plan_row.get("tasks_json")):
                if isinstance(pt, dict) and pt.get("task_id") == req.task_id:
                    process_type = str(pt.get("process_type") or "")
                    machine_type = str(pt.get("machine_type") or "")
                    break

        guard = OperatorEmployeeGuard(db)
        guard_result = await guard.validate_for_task_start(
            employee_id=req.employee_id,
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

        from services.task_start_gate_service import assert_task_startable

        override_reason = req.override_reason or (
            req.reason if req.override_readiness else None
        )
        gate = await assert_task_startable(
            db,
            order_id=req.order_id,
            task_id=req.task_id,
            employee_id=guard_result.employee_id,
            override_readiness=req.override_readiness,
            override_reason=override_reason,
            override_user_id=str(current_user.id or ""),
            override_user_name=str(current_user.name or ""),
            override_user_role=str(current_user.role or ""),
        )

        operator_name = req.operator_name or guard_result.employee_name

        order_sql = text("SELECT code FROM orders WHERE id = :oid")
        result = await db.execute(order_sql, {"oid": req.order_id})
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="order_not_found")

        workforce_ctx = await resolve_task_workforce_context(
            db,
            process_type=process_type,
            machine_type=machine_type,
        )
        initial_fields = {
            **workforce_ctx,
            "employee_id": guard_result.employee_id,
            "employee_name": guard_result.employee_name,
            "operator_name": operator_name,
        }
        if gate.get("override_metadata"):
            initial_fields.update(gate["override_metadata"])

        svc = ExecutionRealityService(db)
        try:
            await svc.start_task(
                order_id=req.order_id,
                order_code=row[0],
                task_id=req.task_id,
                timestamp=now_iso,
                initial_fields=initial_fields,
            )
        except RealityInputError as e:
            raise HTTPException(status_code=422, detail={"error": e.code, "detail": e.detail})

        response: Dict[str, Any] = {
            "status": "ok",
            "action": "start",
            "task_id": req.task_id,
            "timestamp": now_iso,
            "employee_id": guard_result.employee_id,
            "employee_name": guard_result.employee_name,
            "authorization_status": guard_result.authorization_status,
        }
        if guard_result.legacy_operator:
            response["legacy_operator"] = True
        if guard_result.warnings:
            response["warnings"] = guard_result.warnings
        if gate.get("override_metadata"):
            response["readiness_override"] = True
            response["readiness_override_reason"] = gate["override_metadata"].get(
                "readiness_override_reason"
            )
        return response

    elif req.action == "complete":
        # Validate: cannot complete if task is actively blocked or paused
        from models.execution_reality import ExecutionReality
        from sqlalchemy import select as sa_select
        from services.execution_reality_service import ExecutionRealityService, RealityInputError
        from services.operator_employee_guard import OperatorEmployeeGuard

        stmt = sa_select(ExecutionReality).where(ExecutionReality.order_id == req.order_id)
        res = await db.execute(stmt)
        reality = res.scalar_one_or_none()

        if reality is not None:
            tasks = _parse_json(reality.tasks_json)
            for t in tasks:
                if isinstance(t, dict) and t.get("task_id") == req.task_id:
                    # Reject if actively blocked
                    if t.get("blocked_at") and not t.get("unblocked_at"):
                        raise HTTPException(
                            status_code=409,
                            detail={
                                "error": "task_is_blocked",
                                "detail": "Cannot complete a blocked task. Unblock it first.",
                            },
                        )
                    # Reject if actively paused
                    if t.get("paused_at") and not t.get("resumed_at"):
                        raise HTTPException(
                            status_code=409,
                            detail={
                                "error": "task_is_paused",
                                "detail": "Cannot complete a paused task. Resume it first.",
                            },
                        )
                    break

        completion_fields: Dict[str, Any] = {}
        if req.completion_notes:
            completion_fields["completion_notes"] = req.completion_notes

        if req.employee_id is not None:
            guard = OperatorEmployeeGuard(db)
            guard_result = await guard.validate_for_task_start(
                employee_id=req.employee_id,
                process_type="",
                machine_type="",
            )
            if not guard_result.allowed:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": guard_result.errors[0] if guard_result.errors else "employee_invalid",
                        "errors": guard_result.errors,
                    },
                )
            completion_fields["completed_by_employee_id"] = guard_result.employee_id
            if guard_result.employee_name:
                completion_fields["completed_by_employee_name"] = guard_result.employee_name

        svc = ExecutionRealityService(db)
        try:
            await svc.end_task(
                order_id=req.order_id,
                task_id=req.task_id,
                timestamp=now_iso,
                completion_fields=completion_fields or None,
            )
        except RealityInputError as e:
            raise HTTPException(status_code=422, detail={"error": e.code, "detail": e.detail})

        return {
            "status": "ok",
            "action": "complete",
            "task_id": req.task_id,
            "timestamp": now_iso,
            "completion_notes": req.completion_notes,
            "completed_by_employee_id": completion_fields.get("completed_by_employee_id"),
        }

    elif req.action in ("pause", "block"):
        # For pause/block we annotate the reality tasks_json
        # This is a lightweight approach — we update the task entry in reality
        from models.execution_reality import ExecutionReality
        from sqlalchemy import select as sa_select

        stmt = sa_select(ExecutionReality).where(ExecutionReality.order_id == req.order_id)
        res = await db.execute(stmt)
        reality = res.scalar_one_or_none()

        if reality is None:
            raise HTTPException(status_code=404, detail="reality_not_found")

        tasks = _parse_json(reality.tasks_json)
        updated = False
        for t in tasks:
            if isinstance(t, dict) and t.get("task_id") == req.task_id:
                if req.action == "pause":
                    # Validate: task must be started and not already paused/blocked/ended
                    if not t.get("started_at"):
                        raise HTTPException(
                            status_code=422,
                            detail={"error": "task_not_started", "detail": "Cannot pause a task that has not been started"},
                        )
                    if t.get("ended_at"):
                        raise HTTPException(
                            status_code=422,
                            detail={"error": "task_already_ended", "detail": "Cannot pause a completed task"},
                        )
                    if t.get("paused_at") and not t.get("resumed_at"):
                        raise HTTPException(
                            status_code=409,
                            detail={"error": "task_already_paused", "detail": "Task is already paused"},
                        )
                    if t.get("blocked_at") and not t.get("unblocked_at"):
                        raise HTTPException(
                            status_code=409,
                            detail={"error": "task_is_blocked", "detail": "Cannot pause a blocked task"},
                        )
                    t["paused_at"] = now_iso
                    # Clear any previous resumed_at so status derivation sees active pause
                    t["resumed_at"] = None
                elif req.action == "block":
                    # Validate: task must be started and not already blocked/ended
                    if not t.get("started_at"):
                        raise HTTPException(
                            status_code=422,
                            detail={"error": "task_not_started", "detail": "Cannot block a task that has not been started"},
                        )
                    if t.get("ended_at"):
                        raise HTTPException(
                            status_code=422,
                            detail={"error": "task_already_ended", "detail": "Cannot block a completed task"},
                        )
                    if t.get("blocked_at") and not t.get("unblocked_at"):
                        raise HTTPException(
                            status_code=409,
                            detail={"error": "task_already_blocked", "detail": "Task is already blocked"},
                        )
                    t["blocked_at"] = now_iso
                    # Clear any previous unblocked_at so status derivation sees active block
                    t["unblocked_at"] = None
                    if req.reason:
                        t["block_reason"] = req.reason
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=404, detail="task_not_found_in_reality")

        reality.tasks_json = json.dumps(tasks)
        await db.commit()

        return {"status": "ok", "action": req.action, "task_id": req.task_id, "timestamp": now_iso}

    elif req.action == "resume":
        # Resume: only valid when task is actively paused
        from models.execution_reality import ExecutionReality
        from sqlalchemy import select as sa_select

        stmt = sa_select(ExecutionReality).where(ExecutionReality.order_id == req.order_id)
        res = await db.execute(stmt)
        reality = res.scalar_one_or_none()

        if reality is None:
            raise HTTPException(status_code=404, detail="reality_not_found")

        tasks = _parse_json(reality.tasks_json)
        updated = False
        for t in tasks:
            if isinstance(t, dict) and t.get("task_id") == req.task_id:
                # Validate: must be actively paused (paused_at set, resumed_at not set, not ended)
                if t.get("ended_at"):
                    raise HTTPException(
                        status_code=422,
                        detail={"error": "task_already_ended", "detail": "Cannot resume a completed task"},
                    )
                if not t.get("paused_at") or t.get("resumed_at"):
                    raise HTTPException(
                        status_code=409,
                        detail={"error": "task_not_paused", "detail": "Task is not currently paused"},
                    )
                # Set resumed_at — does NOT delete paused_at (preserves history)
                t["resumed_at"] = now_iso
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=404, detail="task_not_found_in_reality")

        reality.tasks_json = json.dumps(tasks)
        await db.commit()

        return {"status": "ok", "action": "resume", "task_id": req.task_id, "timestamp": now_iso}

    elif req.action == "unblock":
        # Unblock: only valid when task is actively blocked
        from models.execution_reality import ExecutionReality
        from sqlalchemy import select as sa_select

        stmt = sa_select(ExecutionReality).where(ExecutionReality.order_id == req.order_id)
        res = await db.execute(stmt)
        reality = res.scalar_one_or_none()

        if reality is None:
            raise HTTPException(status_code=404, detail="reality_not_found")

        tasks = _parse_json(reality.tasks_json)
        updated = False
        for t in tasks:
            if isinstance(t, dict) and t.get("task_id") == req.task_id:
                # Validate: must be actively blocked (blocked_at set, unblocked_at not set, not ended)
                if t.get("ended_at"):
                    raise HTTPException(
                        status_code=422,
                        detail={"error": "task_already_ended", "detail": "Cannot unblock a completed task"},
                    )
                if not t.get("blocked_at") or t.get("unblocked_at"):
                    raise HTTPException(
                        status_code=409,
                        detail={"error": "task_not_blocked", "detail": "Task is not currently blocked"},
                    )
                # Set unblocked_at — does NOT delete blocked_at or block_reason (preserves history)
                t["unblocked_at"] = now_iso
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=404, detail="task_not_found_in_reality")

        reality.tasks_json = json.dumps(tasks)
        await db.commit()

        return {"status": "ok", "action": "unblock", "task_id": req.task_id, "timestamp": now_iso}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")


@router.get(
    "/orders/{order_id}/production-blueprint",
    dependencies=[Depends(require_permission("execution.production_blueprint"))],
)
async def get_order_production_blueprint_endpoint(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only production blueprint for operator/admin — plan + reality merged."""
    return await get_order_production_blueprint(db, order_id)


async def _load_order_product_template(db: AsyncSession, order_id: int) -> Optional[str]:
    order_sql = text(
        "SELECT o.snapshot_line_items FROM orders o WHERE o.id = :oid LIMIT 1"
    )
    row = (await db.execute(order_sql, {"oid": order_id})).mappings().first()
    if not row:
        return None
    snapshot_raw = row.get("snapshot_line_items")
    snapshot: dict = {}
    if isinstance(snapshot_raw, dict):
        snapshot = snapshot_raw
    elif isinstance(snapshot_raw, str):
        try:
            parsed = json.loads(snapshot_raw)
            snapshot = parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            snapshot = {}
    ctx = extract_order_snapshot_context(snapshot)
    product = str(ctx.get("product_template") or "").strip()
    return product or None


@router.patch(
    "/orders/{order_id}/material-procurement/{material_code}",
    dependencies=[Depends(require_permission("execution.production_blueprint"))],
)
async def patch_material_procurement_status(
    order_id: int,
    material_code: str,
    body: MaterialProcurementPatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> Dict[str, Any]:
    """Operator/admin manual procurement status for a planned material item."""
    if body.status not in PROCUREMENT_STATUSES:
        raise HTTPException(status_code=422, detail={"error": "procurement_status_invalid"})
    product_template = await _load_order_product_template(db, order_id)
    return await update_material_procurement_status(
        db,
        order_id=order_id,
        material_code=material_code,
        status=body.status,
        note=body.note,
        affected_task_ids=body.affected_task_ids,
        updated_by_user_id=str(current_user.id or ""),
        product_context=product_template,
    )
