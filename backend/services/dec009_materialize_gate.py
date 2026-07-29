"""OD3 server-side DEC-009 gate for POST materialize (Capacity Batch 14B).

Live DEC-009 remains Owner-LOCKED **A / BLOCKED**. Scoped B is stamped as a
distinct ready-for-future-GO scope (`973010` / `12` / `FIX-DEC009-MAT-01` only).
This module hard-rejects materialize writes until Owner authorizes Batch 14C
execute for that stamped scope. It is a **block** gate — not an execute path.

No sessions, Employee Mobile, ExecutionActuals, or CostEngine involvement.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Live DEC-009 (global policy label — do not invent open execute)
# ---------------------------------------------------------------------------
LIVE_DEC009_STATUS = "A"
LIVE_DEC009_LABEL = "BLOCKED"

# ---------------------------------------------------------------------------
# Scoped B stamp (Batch 14B) — distinct from live DEC-009=A
# ---------------------------------------------------------------------------
SCOPED_B_STAMP_STATUS = "SCOPED_B_STAMPED"
SCOPED_B_ORDER_ID = 973010
SCOPED_B_PLAN_ID = 12
SCOPED_B_FIXTURE_ID = "FIX-DEC009-MAT-01"
SCOPED_B_ACTION = "exactly_one_post_materialize_tasks"
SCOPED_B_ALLOW = ("write_operational_tasks_into_v2_envelope",)
SCOPED_B_FORBID = (
    "sessions",
    "employee_mobile",
    "execution_actuals",
    "invent_minutes_wc_assign_downtime",
    "other_order_id_or_plan",
)

# Execute unlock for Batch 14C — remains false until Owner GO.
BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = False

# Monkeypatched True only for legacy materialize *mechanic* unit tests.
# Production / default test path keeps the OD3 gate enforced.
_UNIT_TEST_BYPASS = False

ERROR_DEC009_MATERIALIZE_BLOCKED = "DEC009_MATERIALIZE_BLOCKED"

# Runtime identity stamp (Capacity Batch 14D) — proves this process loaded OD3.
# Agents must observe this via GET /api/v1/system/local-compatibility before
# any controlled materialize execute; absence ⇒ stale/pre-OD3 runtime.
OD3_GATE_MODULE = "services.dec009_materialize_gate"
OD3_RUNTIME_IDENTITY_VERSION = "capacity-batch-14d/v1"
# First main merge that landed OD3 DEC-009 hard reject (PR #29).
OD3_MIN_MERGE_COMMIT = "a1b759c81355124f285b83425b93a9422f0e891e"


def build_od3_runtime_identity() -> dict[str, Any]:
    """Read-only OD3 gate identity for preflight / stale-runtime detection.

    No DB I/O. No authorization side effects. Not an execute path.
    """
    return {
        "identity_version": OD3_RUNTIME_IDENTITY_VERSION,
        "gate_module": OD3_GATE_MODULE,
        "gate_landed": True,
        "min_merge_commit": OD3_MIN_MERGE_COMMIT,
        "live_dec009": LIVE_DEC009_STATUS,
        "live_dec009_label": LIVE_DEC009_LABEL,
        "scoped_b_stamp": SCOPED_B_STAMP_STATUS,
        "scoped_b_order_id": SCOPED_B_ORDER_ID,
        "scoped_b_plan_id": SCOPED_B_PLAN_ID,
        "scoped_b_fixture_id": SCOPED_B_FIXTURE_ID,
        "batch_execute_materialize_authorized": BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
    }


def scoped_b_matches(*, order_id: int, plan_id: int | None = None) -> bool:
    if int(order_id) != SCOPED_B_ORDER_ID:
        return False
    if plan_id is not None and int(plan_id) != SCOPED_B_PLAN_ID:
        return False
    return True


def evaluate_materialize_authorization(
    *,
    order_id: int,
    plan_id: int | None = None,
) -> dict[str, Any]:
    """Pure authorization evaluation — no DB I/O, no writes."""
    blockers: list[str] = []

    if LIVE_DEC009_STATUS == "A" and not BATCH_EXECUTE_MATERIALIZE_AUTHORIZED:
        blockers.append("live_dec009_A_blocked")
    if not BATCH_EXECUTE_MATERIALIZE_AUTHORIZED:
        blockers.append("batch_execute_materialize_not_authorized")
    if SCOPED_B_STAMP_STATUS != "SCOPED_B_STAMPED":
        blockers.append("scoped_b_not_stamped")
    if not scoped_b_matches(order_id=order_id, plan_id=plan_id):
        blockers.append("order_or_plan_outside_scoped_b")

    allowed = len(blockers) == 0
    return {
        "allowed": allowed,
        "live_dec009": LIVE_DEC009_STATUS,
        "live_dec009_label": LIVE_DEC009_LABEL,
        "scoped_b_stamp": SCOPED_B_STAMP_STATUS,
        "scoped_b_order_id": SCOPED_B_ORDER_ID,
        "scoped_b_plan_id": SCOPED_B_PLAN_ID,
        "scoped_b_fixture_id": SCOPED_B_FIXTURE_ID,
        "batch_execute_materialize_authorized": BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
        "order_id": order_id,
        "plan_id": plan_id,
        "blockers": blockers,
    }


def enforce_dec009_materialize_gate(
    *,
    order_id: int,
    plan_id: int | None = None,
) -> None:
    """Hard-reject materialize when live A / execute unauthorized / out of scope.

    Raises HTTP 422 with stable DEC009_MATERIALIZE_BLOCKED — never writes.
    """
    if _UNIT_TEST_BYPASS:
        return

    decision = evaluate_materialize_authorization(order_id=order_id, plan_id=plan_id)
    if decision["allowed"]:
        return

    raise HTTPException(
        status_code=422,
        detail={
            "error": ERROR_DEC009_MATERIALIZE_BLOCKED,
            "message": (
                "POST materialize hard-rejected by OD3 DEC-009 server gate. "
                f"Live DEC-009={LIVE_DEC009_STATUS}/{LIVE_DEC009_LABEL}; "
                f"scoped_b={SCOPED_B_STAMP_STATUS}; "
                f"execute_authorized={BATCH_EXECUTE_MATERIALIZE_AUTHORIZED}."
            ),
            "blockers": list(decision["blockers"]),
            "live_dec009": LIVE_DEC009_STATUS,
            "scoped_b_stamp": SCOPED_B_STAMP_STATUS,
            "scoped_b_scope": {
                "order_id": SCOPED_B_ORDER_ID,
                "plan_id": SCOPED_B_PLAN_ID,
                "fixture_id": SCOPED_B_FIXTURE_ID,
            },
            "batch_execute_materialize_authorized": BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
            "recovery": (
                "Owner Batch 14C execute GO required for stamped scope only; "
                "do not invent live global DEC-009=B."
            ),
        },
    )
