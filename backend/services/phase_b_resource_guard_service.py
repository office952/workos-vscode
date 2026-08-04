"""Phase B resource guards — scheduling / reservation / capacity.

Owner policy: CLEAR = allowed; ACTIVE / UNKNOWN / NOT_CONFIGURED = blocked.

Current WorkOS freeze has scheduling HOLD and capacity NOT_STARTED placeholders.
Without an authoritative CLEAR signal, evaluation returns NOT_CONFIGURED
(fail-closed). Isolated tests may set ``WORKOS_PHASE_B_RESOURCE_GUARDS=CLEAR``
on an isolated backend only — never on QA.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

ResourceState = Literal["CLEAR", "ACTIVE", "UNKNOWN", "NOT_CONFIGURED"]

_ENV_OVERRIDE = "WORKOS_PHASE_B_RESOURCE_GUARDS"


@dataclass(frozen=True)
class ResourceGuardSnapshot:
    scheduling_state: ResourceState
    machine_reservation_state: ResourceState
    capacity_allocation_state: ResourceState

    def blocking_error(self) -> str | None:
        if self.scheduling_state != "CLEAR":
            return "scheduling_state_not_clear"
        if self.machine_reservation_state != "CLEAR":
            return "machine_reservation_state_not_clear"
        if self.capacity_allocation_state != "CLEAR":
            return "capacity_state_not_clear"
        return None


def evaluate_resource_guards(
    *,
    order_id: int,
    plan_id: int,
    task_key: str,
) -> ResourceGuardSnapshot:
    """Fail-closed default for current freeze; optional isolated CLEAR override."""
    del order_id, plan_id, task_key  # reserved for future real subsystem probes
    override = (os.environ.get(_ENV_OVERRIDE) or "").strip().upper()
    if override == "CLEAR":
        return ResourceGuardSnapshot(
            scheduling_state="CLEAR",
            machine_reservation_state="CLEAR",
            capacity_allocation_state="CLEAR",
        )
    # Placeholders in assignment readiness: scheduling HOLD, capacity not_started.
    # No authoritative CLEAR configuration → NOT_CONFIGURED (blocked).
    return ResourceGuardSnapshot(
        scheduling_state="NOT_CONFIGURED",
        machine_reservation_state="NOT_CONFIGURED",
        capacity_allocation_state="NOT_CONFIGURED",
    )
