"""Workforce context helpers for execution_reality task observations.

Extends tasks_json entries without breaking legacy rows missing employee_id.
Does NOT touch CostEngine, Pricing, or Quote.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from models.execution_reality import ExecutionReality
from services.operational_registry_service import OperationalRegistryService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def normalize_operation_code(code: str) -> str:
    return (code or "").lower().replace("-", "_").replace(" ", "_")


async def resolve_task_workforce_context(
    db: AsyncSession,
    *,
    process_type: str = "",
    machine_type: str = "",
) -> Dict[str, Any]:
    """Resolve operation/workcenter/resource hints for a shop-floor task."""
    op = normalize_operation_code(process_type)
    workcenter_code: Optional[str] = None
    resource_code: Optional[str] = None

    resolved_operation_code: Optional[str] = None
    resolution: Optional[str] = None

    if op:
        registry = OperationalRegistryService(db)
        mapping = await registry.resolve_operation_mapping(op)
        if mapping:
            resolved_operation_code = mapping.get("resolved_operation_code") or mapping.get(
                "operation_code"
            )
            resolution = mapping.get("resolution")
            wcs = mapping.get("allowed_workcenter_codes") or []
            resources = mapping.get("allowed_resource_codes") or []
            if wcs:
                workcenter_code = wcs[0]
            if resources:
                resource_code = resources[0]

    if machine_type and machine_type not in ("—", "-", ""):
        resource_code = resource_code or machine_type

    return {
        "operation_code": op or None,
        "resolved_operation_code": resolved_operation_code,
        "resolution": resolution,
        "process_type": process_type or None,
        "machine_type": machine_type or None,
        "workcenter_code": workcenter_code,
        "resource_code": resource_code,
    }


def _parse_tasks(raw: Optional[str]) -> list:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


async def annotate_reality_task(
    db: AsyncSession,
    order_id: int,
    task_id: str,
    fields: Dict[str, Any],
) -> bool:
    """Merge workforce fields into an existing reality task observation."""
    if not fields:
        return False

    stmt = select(ExecutionReality).where(ExecutionReality.order_id == order_id)
    reality = (await db.execute(stmt)).scalar_one_or_none()
    if reality is None:
        return False

    tasks = _parse_tasks(reality.tasks_json)
    updated = False
    for t in tasks:
        if isinstance(t, dict) and t.get("task_id") == task_id:
            for key, value in fields.items():
                if value is not None:
                    t[key] = value
            updated = True
            break

    if updated:
        reality.tasks_json = json.dumps(tasks)
        await db.commit()
    return updated
