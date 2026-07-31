"""OD3 server-side DEC-009 gate for POST materialize (Capacity Batch 14B / 20D).

Live DEC-009 remains Owner-LOCKED **A / BLOCKED**. Scoped B is stamped as a
multi-fixture registry:

- `FIX-DEC009-MAT-01` / `973010` / `12` — historical (ops already written; rematerialize forbidden)
- `FIX-DEC009-MAT-02` / `92401` / `13` — **next dry target** (Batch 20D live stamp)

Authorize-path matching allows **only** the next dry target. This module
hard-rejects materialize writes until Owner authorizes a separate execute GO
for that stamped next-dry scope. It is a **block** gate — not an execute path.

No sessions, Employee Mobile, ExecutionActuals, or CostEngine involvement.
"""

from __future__ import annotations

from typing import Any, TypedDict

from fastapi import HTTPException


class ScopedBFixture(TypedDict):
    order_id: int
    plan_id: int
    fixture_id: str
    role: str
    allow_materialize: bool


# ---------------------------------------------------------------------------
# Live DEC-009 (global policy label — do not invent open execute)
# ---------------------------------------------------------------------------
LIVE_DEC009_STATUS = "A"
LIVE_DEC009_LABEL = "BLOCKED"

# ---------------------------------------------------------------------------
# Scoped B stamp — multi-fixture registry (Batch 20D)
# ---------------------------------------------------------------------------
SCOPED_B_STAMP_STATUS = "SCOPED_B_STAMPED"

# Explicit registry: MAT-01 historical + MAT-02 next dry. MAT-01 stamp does NOT
# cover 92401; matching for authorize/execute uses allow_materialize=True only.
SCOPED_B_FIXTURES: tuple[ScopedBFixture, ...] = (
    {
        "order_id": 973010,
        "plan_id": 12,
        "fixture_id": "FIX-DEC009-MAT-01",
        "role": "historical_stamped",
        "allow_materialize": False,
    },
    {
        "order_id": 92401,
        "plan_id": 13,
        "fixture_id": "FIX-DEC009-MAT-02",
        "role": "next_dry_target",
        "allow_materialize": True,
    },
)

# Scalar aliases = next dry target only (preflight / identity honesty).
SCOPED_B_ORDER_ID = 92401
SCOPED_B_PLAN_ID = 13
SCOPED_B_FIXTURE_ID = "FIX-DEC009-MAT-02"
SCOPED_B_ACTION = "exactly_one_post_materialize_tasks"
SCOPED_B_ALLOW = ("write_operational_tasks_into_v2_envelope",)
SCOPED_B_FORBID = (
    "sessions",
    "employee_mobile",
    "execution_actuals",
    "invent_minutes_wc_assign_downtime",
    "other_order_id_or_plan",
    "rematerialize_973010_mat01",
)

# Execute unlock — remains false until separate Owner execute GO.
BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = False

# Monkeypatched True only for legacy materialize *mechanic* unit tests.
# Production / default test path keeps the OD3 gate enforced.
_UNIT_TEST_BYPASS = False

ERROR_DEC009_MATERIALIZE_BLOCKED = "DEC009_MATERIALIZE_BLOCKED"

# Runtime identity stamp — proves this process loaded OD3 + current scoped-B.
# Agents must observe this via GET /api/v1/system/local-compatibility before
# any controlled materialize execute; absence ⇒ stale/pre-OD3 runtime.
OD3_GATE_MODULE = "services.dec009_materialize_gate"
OD3_RUNTIME_IDENTITY_VERSION = "capacity-batch-20d/v1"
# First main merge that landed OD3 DEC-009 hard reject (PR #29).
OD3_MIN_MERGE_COMMIT = "a1b759c81355124f285b83425b93a9422f0e891e"


def _next_dry_fixture() -> ScopedBFixture:
    for fixture in SCOPED_B_FIXTURES:
        if fixture["role"] == "next_dry_target" and fixture["allow_materialize"]:
            return fixture
    raise RuntimeError("scoped-B registry missing next_dry_target")


def build_od3_runtime_identity() -> dict[str, Any]:
    """Read-only OD3 gate identity for preflight / stale-runtime detection.

    No DB I/O. No authorization side effects. Not an execute path.
    """
    next_dry = _next_dry_fixture()
    return {
        "identity_version": OD3_RUNTIME_IDENTITY_VERSION,
        "gate_module": OD3_GATE_MODULE,
        "gate_landed": True,
        "min_merge_commit": OD3_MIN_MERGE_COMMIT,
        "live_dec009": LIVE_DEC009_STATUS,
        "live_dec009_label": LIVE_DEC009_LABEL,
        "scoped_b_stamp": SCOPED_B_STAMP_STATUS,
        # Next dry target scalars (Batch 20D) — do not imply execute unlock.
        "scoped_b_order_id": next_dry["order_id"],
        "scoped_b_plan_id": next_dry["plan_id"],
        "scoped_b_fixture_id": next_dry["fixture_id"],
        "scoped_b_fixtures": [
            {
                "order_id": f["order_id"],
                "plan_id": f["plan_id"],
                "fixture_id": f["fixture_id"],
                "role": f["role"],
                "allow_materialize": f["allow_materialize"],
            }
            for f in SCOPED_B_FIXTURES
        ],
        "batch_execute_materialize_authorized": BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
    }


def scoped_b_matches(*, order_id: int, plan_id: int | None = None) -> bool:
    """True only for the next-dry fixture that may receive a future authorized POST.

    Historical MAT-01 remains in the registry for honesty but never matches —
    rematerialize of 973010 is forbidden.
    """
    oid = int(order_id)
    for fixture in SCOPED_B_FIXTURES:
        if not fixture["allow_materialize"]:
            continue
        if oid != int(fixture["order_id"]):
            continue
        if plan_id is not None and int(plan_id) != int(fixture["plan_id"]):
            return False
        return True
    return False


def evaluate_materialize_authorization(
    *,
    order_id: int,
    plan_id: int | None = None,
) -> dict[str, Any]:
    """Pure authorization evaluation — no DB I/O, no writes."""
    blockers: list[str] = []
    next_dry = _next_dry_fixture()

    if LIVE_DEC009_STATUS == "A" and not BATCH_EXECUTE_MATERIALIZE_AUTHORIZED:
        blockers.append("live_dec009_A_blocked")
    if not BATCH_EXECUTE_MATERIALIZE_AUTHORIZED:
        blockers.append("batch_execute_materialize_not_authorized")
    if SCOPED_B_STAMP_STATUS != "SCOPED_B_STAMPED":
        blockers.append("scoped_b_not_stamped")
    if not scoped_b_matches(order_id=order_id, plan_id=plan_id):
        blockers.append("order_or_plan_outside_scoped_b")

    allowed = len(blockers) == 0
    fixtures_view = [
        {
            "order_id": f["order_id"],
            "plan_id": f["plan_id"],
            "fixture_id": f["fixture_id"],
            "role": f["role"],
            "allow_materialize": f["allow_materialize"],
        }
        for f in SCOPED_B_FIXTURES
    ]
    return {
        "allowed": allowed,
        "live_dec009": LIVE_DEC009_STATUS,
        "live_dec009_label": LIVE_DEC009_LABEL,
        "scoped_b_stamp": SCOPED_B_STAMP_STATUS,
        "scoped_b_order_id": next_dry["order_id"],
        "scoped_b_plan_id": next_dry["plan_id"],
        "scoped_b_fixture_id": next_dry["fixture_id"],
        "scoped_b_fixtures": fixtures_view,
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

    next_dry = _next_dry_fixture()
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
                "order_id": next_dry["order_id"],
                "plan_id": next_dry["plan_id"],
                "fixture_id": next_dry["fixture_id"],
                "role": next_dry["role"],
            },
            "scoped_b_fixtures": list(decision["scoped_b_fixtures"]),
            "batch_execute_materialize_authorized": BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
            "recovery": (
                "Owner execute GO required for stamped next-dry scope only "
                f"({next_dry['fixture_id']} / {next_dry['order_id']} / "
                f"{next_dry['plan_id']}); do not invent live global DEC-009=B; "
                "do not rematerialize historical MAT-01 / 973010."
            ),
        },
    )
