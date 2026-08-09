"""Shared MachineRun eligibility predicates — CREATE/ADD writers + candidate reads.

Writers keep raising validation errors. Candidate discovery soft-evaluates the
same predicates so GET and POST cannot drift for the same factual state.
"""

from __future__ import annotations

import json
from typing import Any

from models.machine_run import MachineRunParticipant
from models.operational_registry import MachineRegistry
from services.resource_state_write_common import (
    ResourceStateNotFoundError,
    ResourceStateValidationError,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def parse_machine_capabilities(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(v) for v in raw]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(v) for v in parsed]
        except (TypeError, ValueError):
            return []
    return []


def demand_stamps(task: dict[str, Any]) -> tuple[str, str, bool]:
    """Strict CREATE/ADD demand stamps (raises on failure)."""
    mode = task.get("resource_mode")
    if mode is None or (isinstance(mode, str) and not mode.strip()):
        raise ResourceStateValidationError(
            "task_not_machine_bound",
            "resource_mode missing (hint-only fields are not accepted)",
        )
    mode_s = str(mode).strip()
    if mode_s != "MACHINE_BOUND":
        raise ResourceStateValidationError(
            "task_not_machine_bound",
            f"resource_mode={mode_s!r} (required MACHINE_BOUND)",
        )
    cap = task.get("machine_capability_code")
    if cap is None or (isinstance(cap, str) and not str(cap).strip()):
        raise ResourceStateValidationError(
            "task_capability_unknown",
            "machine_capability_code missing",
        )
    cap_s = str(cap).strip()
    eligible = task.get("batch_eligible")
    if eligible is not True:
        raise ResourceStateValidationError(
            "task_not_batch_eligible",
            f"batch_eligible={eligible!r} (required true)",
        )
    return mode_s, cap_s, True


def evaluate_demand_stamps(task: dict[str, Any]) -> tuple[bool, str | None, str | None]:
    """Soft demand evaluation — same rules as demand_stamps, no raise.

    Returns (ok, capability_or_none, reason_code_or_none).
    """
    try:
        _mode, cap, _eligible = demand_stamps(task)
        return True, cap, None
    except ResourceStateValidationError as exc:
        return False, None, exc.code


def validate_machine_capability_join(
    machine: MachineRegistry, required_capability: str
) -> None:
    """Hard-join only when inventory capabilities are non-empty (readiness MVP)."""
    caps = parse_machine_capabilities(machine.capabilities)
    if not caps:
        return
    if required_capability not in caps:
        raise ResourceStateValidationError(
            "machine_capability_mismatch",
            f"machine {machine.id} capabilities={caps!r} "
            f"missing {required_capability!r}",
        )


def machine_capability_compatible(
    machine: MachineRegistry, required_capability: str
) -> bool:
    """Soft mirror of validate_machine_capability_join."""
    try:
        validate_machine_capability_join(machine, required_capability)
        return True
    except ResourceStateValidationError:
        return False


async def require_reservable_machine(
    db: AsyncSession, machine_id: int
) -> MachineRegistry:
    machine = await db.get(MachineRegistry, machine_id)
    if machine is None:
        raise ResourceStateNotFoundError(
            "machine_not_found", f"machine_id {machine_id} not found"
        )
    if not bool(machine.is_active):
        raise ResourceStateValidationError(
            "machine_not_reservable", "machine is_active=false"
        )
    if not bool(machine.is_available):
        raise ResourceStateValidationError(
            "machine_not_reservable", "machine is_available=false"
        )
    if machine.operational_status != "active":
        raise ResourceStateValidationError(
            "machine_not_reservable",
            f"operational_status={machine.operational_status!r}",
        )
    return machine


async def find_active_membership(
    db: AsyncSession, *, execution_plan_id: int, task_key: str
) -> MachineRunParticipant | None:
    result = await db.execute(
        select(MachineRunParticipant).where(
            MachineRunParticipant.execution_plan_id == execution_plan_id,
            MachineRunParticipant.task_key == task_key,
            MachineRunParticipant.status == "ACTIVE",
        )
    )
    return result.scalar_one_or_none()


async def find_all_active_memberships(
    db: AsyncSession, *, execution_plan_id: int, task_key: str
) -> list[MachineRunParticipant]:
    """All ACTIVE memberships for integrity checks (should be 0 or 1)."""
    result = await db.execute(
        select(MachineRunParticipant).where(
            MachineRunParticipant.execution_plan_id == execution_plan_id,
            MachineRunParticipant.task_key == task_key,
            MachineRunParticipant.status == "ACTIVE",
        )
    )
    return list(result.scalars().all())
