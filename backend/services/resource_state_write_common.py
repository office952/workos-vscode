"""Shared helpers for Resource State domain writers (R9).

Plan process-lock + FOR UPDATE, task_key validation inside the transaction,
ACTIVE domain-configuration guard, and shared error types.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from weakref import WeakValueDictionary

from models.execution_plan import ExecutionPlan
from models.resource_domain_configuration import ResourceDomainConfiguration
from services.execution_plan_task_parser import load_operational_tasks_from_plan_json
from services.resource_domain_configuration_repository import (
    ResourceDomainConfigurationRepository,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_plan_locks: "WeakValueDictionary[int, asyncio.Lock]" = WeakValueDictionary()
_machine_locks: "WeakValueDictionary[int, asyncio.Lock]" = WeakValueDictionary()


def plan_order_lock(order_id: int) -> asyncio.Lock:
    lock = _plan_locks.get(order_id)
    if lock is None:
        lock = asyncio.Lock()
        _plan_locks[order_id] = lock
    return lock


def machine_lock(machine_id: int) -> asyncio.Lock:
    """Process-local serialization for machine-centric writers (e.g. MACHINE_RUN)."""
    lock = _machine_locks.get(machine_id)
    if lock is None:
        lock = asyncio.Lock()
        _machine_locks[machine_id] = lock
    return lock


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResourceStateWriteError(Exception):
    def __init__(self, code: str, message: str = "", *, http_status: int = 409):
        self.code = code
        self.message = message or code
        self.http_status = http_status
        super().__init__(self.message)


class ResourceStateNotFoundError(ResourceStateWriteError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(code, message, http_status=404)


class ResourceStateValidationError(ResourceStateWriteError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(code, message, http_status=422)


async def load_plan_for_update(
    db: AsyncSession, *, plan_id: int
) -> ExecutionPlan:
    result = await db.execute(
        select(ExecutionPlan)
        .where(ExecutionPlan.id == plan_id)
        .with_for_update()
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise ResourceStateNotFoundError(
            "execution_plan_not_found", f"plan {plan_id} not found"
        )
    return plan


def require_task_in_plan(plan: ExecutionPlan, task_key: str) -> None:
    get_operational_task_from_plan(plan, task_key)


def get_operational_task_from_plan(
    plan: ExecutionPlan, task_key: str
) -> dict[str, Any]:
    """Return the operational_tasks[] entry for task_key (canonical EP V2 truth)."""
    tid = (task_key or "").strip()
    if not tid:
        raise ResourceStateValidationError(
            "invalid_task_identity", "task_key is blank"
        )
    tasks, parsed = load_operational_tasks_from_plan_json(plan.tasks_json or "")
    if parsed.format == "invalid":
        raise ResourceStateValidationError(
            "tasks_json_invalid", ";".join(parsed.parse_errors)
        )
    for entry in tasks:
        if isinstance(entry, dict) and str(entry.get("task_id")) == tid:
            return entry
    raise ResourceStateNotFoundError(
        "task_key_not_found", f"task_key {tid!r} not in plan {plan.id}"
    )


async def require_active_domain_config(
    db: AsyncSession, *, domain: str
) -> ResourceDomainConfiguration:
    repo = ResourceDomainConfigurationRepository(db)
    cfg = await repo.get_by_domain_scope(domain=domain)
    if cfg is None:
        raise ResourceStateWriteError(
            "domain_not_active",
            f"no configuration for {domain}",
            http_status=409,
        )
    if cfg.status != "ACTIVE":
        raise ResourceStateWriteError(
            "domain_disabled",
            f"configuration for {domain} is {cfg.status}",
            http_status=409,
        )
    return cfg


def as_naive_utc(value: datetime) -> datetime:
    """Normalize aware/naive instants for SQLite round-trip comparisons."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def windows_overlap(
    start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime
) -> bool:
    """Half-open style adjacency: end == start is NOT overlap."""
    sa, ea = as_naive_utc(start_a), as_naive_utc(end_a)
    sb, eb = as_naive_utc(start_b), as_naive_utc(end_b)
    return sa < eb and ea > sb


def dt_key(value: datetime | None) -> str | None:
    """Canonical instant key for idempotency (SQLite may drop tzinfo)."""
    if value is None:
        return None
    value = as_naive_utc(value)
    return value.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")


def fingerprint_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return a == b
