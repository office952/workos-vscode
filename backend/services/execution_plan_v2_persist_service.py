"""Persist ExecutionPlan V2 from validated preview (Step 9.3.3).

Writes one execution_plan row only — no tasks, sessions, or ExecutionActuals.
Uses Step 9.3.2 preview as the sole task source.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from schemas.execution_plan_v2 import (
    EXECUTION_PLAN_V2_PLAN_SOURCE,
    EXECUTION_PLAN_V2_SOURCE,
    EXECUTION_PLAN_V2_TASKS_JSON_PLAN_VERSION,
    PLANNING_MINUTES_WARNING,
    TOTAL_ESTIMATED_TIME_SOURCE_NOT_AVAILABLE,
    ExecutionPlanV2PersistResult,
    ExecutionPlanV2Preview,
)
from services.execution_plan_v2_preview_service import (
    build_execution_plan_v2_preview,
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
    "product_system_execution_output",
)

PERSIST_ALLOWED_PREVIEW_STATUSES = frozenset(
    {
        "ready_for_owner_review",
        "partial_missing_planning_minutes",
        # Draft shell allowed so Order Snapshot materials RO can attach to a plan
        # without inventing task rules / materializing ops.
        "blocked_missing_task_rules",
    }
)


class ExecutionPlanV2PersistOrderNotFound(Exception):
    """Raised when the target order row does not exist."""


def _raise_blocked(error: str, message: str, blockers: list[str] | None = None) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error": error,
            "message": message,
            "blockers": blockers or [error],
        },
    )


def _validate_preview_for_persist(preview: ExecutionPlanV2Preview) -> None:
    if preview.source != EXECUTION_PLAN_V2_SOURCE:
        _raise_blocked(
            "PREVIEW_SOURCE_INVALID",
            f"Preview source {preview.source!r} is not order_snapshot_v2.",
            ["blocked_forbidden_source"],
        )
    if preview.persist_status != "not_persisted":
        _raise_blocked(
            "PREVIEW_ALREADY_PERSISTED",
            "Preview persist_status is not not_persisted.",
            ["preview_already_persisted"],
        )
    if preview.execution_plan_created:
        _raise_blocked(
            "PREVIEW_PLAN_ALREADY_CREATED",
            "Preview indicates execution_plan_created=true.",
            ["execution_plan_already_created"],
        )
    if preview.execution_tasks_created:
        _raise_blocked(
            "PREVIEW_TASKS_ALREADY_CREATED",
            "Preview indicates execution_tasks_created=true.",
            ["execution_tasks_already_created"],
        )
    if preview.status not in PERSIST_ALLOWED_PREVIEW_STATUSES:
        _raise_blocked(
            "PREVIEW_STATUS_BLOCKED",
            f"Preview status {preview.status!r} is not persistable.",
            preview.blockers or [preview.status],
        )
    # Materials-RO draft shell: allow empty planned_tasks when task rules absent.
    if not preview.planned_tasks and preview.status != "blocked_missing_task_rules":
        _raise_blocked(
            "PREVIEW_EMPTY_TASKS",
            "Preview has no planned_tasks — cannot persist.",
            ["planned_tasks_empty"],
        )


def _compute_total_estimated_time_minutes(
    preview: ExecutionPlanV2Preview,
) -> tuple[float, str | None, list[str]]:
    warnings = list(preview.warnings)
    minutes_values = [task.estimated_minutes for task in preview.planned_tasks]
    if all(m is not None for m in minutes_values):
        return float(sum(float(m) for m in minutes_values)), None, warnings

    if PLANNING_MINUTES_WARNING not in warnings:
        warnings.append(PLANNING_MINUTES_WARNING)
    return 0.0, TOTAL_ESTIMATED_TIME_SOURCE_NOT_AVAILABLE, warnings


def build_tasks_json_envelope(
    preview: ExecutionPlanV2Preview,
    *,
    order_id: int,
    order_code: str,
    total_estimated_time_minutes: float,
    total_estimated_time_source: str | None,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "source": EXECUTION_PLAN_V2_PLAN_SOURCE,
        "plan_version": EXECUTION_PLAN_V2_TASKS_JSON_PLAN_VERSION,
        "order_id": order_id,
        "order_code": order_code,
        "quote_id": preview.quote_id,
        "quote_snapshot_v2_id": preview.quote_snapshot_v2_id,
        "template_code": preview.template_code,
        "source_snapshot_code": preview.source_snapshot_code,
        "source_content_hash": preview.source_content_hash,
        "source_order_snapshot_version": preview.source_order_snapshot_version,
        "order_snapshot_hash": preview.order_snapshot_hash,
        "planned_operations": [op.model_dump(mode="json") for op in preview.planned_operations],
        "planned_tasks": [task.model_dump(mode="json") for task in preview.planned_tasks],
        "dependencies": [dep.model_dump(mode="json") for dep in preview.dependencies],
        "ignored_pricing_sources": list(preview.ignored_pricing_sources),
        "warnings": warnings,
        "blockers": [],
        "provenance": [entry.model_dump(mode="json") for entry in preview.provenance],
        "execution_tasks_created": False,
        "pricing_sources_used_for_tasks": [],
        "total_estimated_time_minutes": total_estimated_time_minutes,
        "total_estimated_time_source": total_estimated_time_source,
        "preview_status": preview.status,
    }


def _persist_input_summary(preview: ExecutionPlanV2Preview) -> dict[str, Any]:
    summary = dict(preview.input_summary or {})
    summary.setdefault("task_count", len(preview.planned_tasks))
    summary.setdefault("operation_count", len(preview.planned_operations))
    summary.setdefault("material_count", len(preview.material_readiness_inputs))
    if preview.template_code and "template_code" not in summary:
        summary["template_code"] = preview.template_code
    return summary


def _result_from_existing_plan(
    order: Orders,
    existing_plan: ExecutionPlan,
    *,
    preview: ExecutionPlanV2Preview | None = None,
) -> ExecutionPlanV2PersistResult:
    envelope: dict[str, Any] = {}
    warnings: list[str] = []
    if existing_plan.tasks_json:
        try:
            envelope = json.loads(existing_plan.tasks_json)
            warnings = list(envelope.get("warnings") or [])
        except json.JSONDecodeError:
            envelope = {}

    input_summary = {
        "task_count": len(envelope.get("planned_tasks") or []),
        "operation_count": len(envelope.get("planned_operations") or []),
        "material_count": len(envelope.get("material_readiness_inputs") or []),
    }
    template_code = envelope.get("template_code") or (
        preview.template_code if preview is not None else None
    )
    if template_code:
        input_summary["template_code"] = template_code

    return ExecutionPlanV2PersistResult(
        status="already_exists",
        persist_status="already_exists",
        execution_plan_id=existing_plan.id,
        order_id=order.id,
        order_code=order.code,
        quote_id=preview.quote_id if preview is not None else None,
        quote_snapshot_v2_id=existing_plan.source_quote_snapshot_v2_id,
        template_code=template_code,
        source_snapshot_code=existing_plan.source_snapshot_code,
        source_content_hash=existing_plan.source_content_hash,
        source_order_snapshot_version=existing_plan.source_order_snapshot_version,
        order_snapshot_hash=preview.order_snapshot_hash if preview is not None else envelope.get(
            "order_snapshot_hash"
        ),
        preview_status=preview.status if preview is not None else envelope.get("preview_status"),
        total_estimated_time_minutes=existing_plan.total_estimated_time_minutes,
        total_estimated_time_source=envelope.get("total_estimated_time_source"),
        execution_plan_created=False,
        execution_tasks_created=False,
        warnings=warnings,
        provenance=preview.provenance if preview is not None else [],
        input_summary=input_summary,
        message="ExecutionPlan V2 already exists for this order — no duplicate row created.",
    )


async def create_execution_plan_v2_from_order(
    db: AsyncSession,
    order_id: int,
    *,
    prepared_by_user_id: str | None = None,
) -> ExecutionPlanV2PersistResult:
    """Persist one ExecutionPlan row from validated V2 preview."""
    order = await db.get(Orders, order_id)
    if order is None:
        raise ExecutionPlanV2PersistOrderNotFound()

    existing_stmt = select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
    existing_result = await db.execute(existing_stmt)
    existing_plan = existing_result.scalar_one_or_none()
    preview = await build_execution_plan_v2_preview(db, order_id)
    if existing_plan is not None:
        if (
            preview.quote_snapshot_v2_id is not None
            and existing_plan.source_quote_snapshot_v2_id is not None
            and existing_plan.source_quote_snapshot_v2_id != preview.quote_snapshot_v2_id
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "plan_source_snapshot_mismatch",
                    "plan_id": existing_plan.id,
                    "existing_source_quote_snapshot_v2_id": existing_plan.source_quote_snapshot_v2_id,
                    "requested_source_quote_snapshot_v2_id": preview.quote_snapshot_v2_id,
                },
            )
        return _result_from_existing_plan(order, existing_plan, preview=preview)

    _validate_preview_for_persist(preview)

    total_minutes, time_source, warnings = _compute_total_estimated_time_minutes(preview)
    envelope = build_tasks_json_envelope(
        preview,
        order_id=order.id,
        order_code=str(order.code),
        total_estimated_time_minutes=total_minutes,
        total_estimated_time_source=time_source,
        warnings=warnings,
    )

    snapshot_version = getattr(order, "snapshot_version", None)
    if snapshot_version is None:
        snapshot_version = 1

    row = ExecutionPlan(
        order_id=order.id,
        order_code=str(order.code),
        snapshot_version=int(snapshot_version),
        tasks_json=json.dumps(envelope, ensure_ascii=False),
        total_estimated_time_minutes=total_minutes,
        prepared_by_user_id=prepared_by_user_id,
        plan_source=EXECUTION_PLAN_V2_PLAN_SOURCE,
        source_quote_snapshot_v2_id=preview.quote_snapshot_v2_id,
        source_snapshot_code=preview.source_snapshot_code,
        source_content_hash=preview.source_content_hash,
        source_order_snapshot_version=preview.source_order_snapshot_version,
    )

    readiness_snapshot = getattr(order, "readiness_snapshot", None)
    if isinstance(readiness_snapshot, dict):
        patched_readiness = dict(readiness_snapshot)
        patched_readiness["execution_plan_created"] = True
        patched_readiness["no_execution_plan_created"] = False
        order.readiness_snapshot = patched_readiness

    db.add(row)
    await db.commit()
    await db.refresh(row)
    await db.refresh(order)

    return ExecutionPlanV2PersistResult(
        status="persisted",
        persist_status="persisted",
        execution_plan_id=row.id,
        order_id=order.id,
        order_code=order.code,
        quote_id=preview.quote_id,
        quote_snapshot_v2_id=preview.quote_snapshot_v2_id,
        template_code=preview.template_code,
        source_snapshot_code=preview.source_snapshot_code,
        source_content_hash=preview.source_content_hash,
        source_order_snapshot_version=preview.source_order_snapshot_version,
        order_snapshot_hash=preview.order_snapshot_hash,
        preview_status=preview.status,
        total_estimated_time_minutes=total_minutes,
        total_estimated_time_source=time_source,
        warnings=warnings,
        provenance=preview.provenance,
        input_summary=_persist_input_summary(preview),
        message="ExecutionPlan V2 persisted from validated preview.",
    )
