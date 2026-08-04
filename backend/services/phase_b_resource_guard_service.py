"""Phase B resource guards — scheduling / reservation / capacity.

Owner policy: CLEAR = allowed; ACTIVE / UNKNOWN / NOT_CONFIGURED = blocked.

Current WorkOS freeze has scheduling HOLD and capacity NOT_STARTED placeholders.
Without an authoritative CLEAR signal, evaluation returns NOT_CONFIGURED
(fail-closed).

``WORKOS_PHASE_B_RESOURCE_GUARDS=CLEAR`` is **TEST_ONLY**:
accepted solely when ``APP_ENV``/``ENVIRONMENT`` is exactly ``test``.
In development/QA/staging/production-like runtimes the override is ignored
(and startup safety reports it as unsafe).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

ResourceState = Literal["CLEAR", "ACTIVE", "UNKNOWN", "NOT_CONFIGURED"]

ENV_RESOURCE_GUARDS = "WORKOS_PHASE_B_RESOURCE_GUARDS"
ENV_DEC015_FIXTURE = "WORKOS_PHASE_B_DEC015_FIXTURE"


@dataclass(frozen=True)
class ResourceGuardSnapshot:
    scheduling_state: ResourceState
    machine_reservation_state: ResourceState
    capacity_allocation_state: ResourceState
    override_applied: bool = False
    override_rejected: bool = False

    def blocking_error(self) -> str | None:
        if self.scheduling_state != "CLEAR":
            return "scheduling_state_not_clear"
        if self.machine_reservation_state != "CLEAR":
            return "machine_reservation_state_not_clear"
        if self.capacity_allocation_state != "CLEAR":
            return "capacity_state_not_clear"
        return None


def _runtime_env_name() -> str:
    return (
        os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development"
    ).strip().lower()


def is_phase_b_test_runtime() -> bool:
    """True only for explicit APP_ENV/ENVIRONMENT=test."""
    return _runtime_env_name() == "test"


def resource_clear_override_requested() -> bool:
    return (os.environ.get(ENV_RESOURCE_GUARDS) or "").strip().upper() == "CLEAR"


def dec015_fixture_requested() -> bool:
    return (os.environ.get(ENV_DEC015_FIXTURE) or "").strip().upper() == "READY"


def dec015_test_fixture_allowed() -> bool:
    """DEC-015 READY fixture is TEST_ONLY (same boundary as CLEAR)."""
    return is_phase_b_test_runtime() and dec015_fixture_requested()


def evaluate_resource_guards(
    *,
    order_id: int,
    plan_id: int,
    task_key: str,
) -> ResourceGuardSnapshot:
    """Fail-closed default; CLEAR override only in APP_ENV=test."""
    del order_id, plan_id, task_key  # reserved for future real subsystem probes
    not_configured = ResourceGuardSnapshot(
        scheduling_state="NOT_CONFIGURED",
        machine_reservation_state="NOT_CONFIGURED",
        capacity_allocation_state="NOT_CONFIGURED",
    )
    if resource_clear_override_requested():
        if not is_phase_b_test_runtime():
            logger.warning(
                "Ignoring %s=CLEAR outside APP_ENV=test (runtime=%s)",
                ENV_RESOURCE_GUARDS,
                _runtime_env_name(),
            )
            return ResourceGuardSnapshot(
                scheduling_state="NOT_CONFIGURED",
                machine_reservation_state="NOT_CONFIGURED",
                capacity_allocation_state="NOT_CONFIGURED",
                override_rejected=True,
            )
        return ResourceGuardSnapshot(
            scheduling_state="CLEAR",
            machine_reservation_state="CLEAR",
            capacity_allocation_state="CLEAR",
            override_applied=True,
        )
    return not_configured


def validate_phase_b_test_overrides_at_startup() -> tuple[str, str]:
    """Return (status, message) for startup_safety integration.

    status: PASS | WARNING | BLOCKED
    """
    env = _runtime_env_name()
    clear_req = resource_clear_override_requested()
    dec_req = dec015_fixture_requested()
    if not clear_req and not dec_req:
        return (
            "PASS",
            "Phase B test overrides unset (resource CLEAR / DEC015 READY)",
        )
    if env == "test":
        parts = []
        if clear_req:
            parts.append(f"{ENV_RESOURCE_GUARDS}=CLEAR")
        if dec_req:
            parts.append(f"{ENV_DEC015_FIXTURE}=READY")
        return (
            "PASS",
            "Phase B test-only overrides accepted under APP_ENV=test: "
            + ", ".join(parts),
        )
    # Non-test: overrides are never operational truth.
    msg = (
        f"Phase B test overrides set outside APP_ENV=test (runtime={env}). "
        "CLEAR/READY are ignored by evaluate_* and must not be used as QA truth."
    )
    if env in {"staging", "production", "live"}:
        return ("BLOCKED", msg)
    # development/local — do not kill Owner stack, but do not honor override.
    return ("WARNING", msg)
