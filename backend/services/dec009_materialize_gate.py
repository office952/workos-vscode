"""OD3 server-side DEC-009 gate for POST materialize (Golden Pilot Task Graph V1).

Live DEC-009 remains Owner-LOCKED **A / BLOCKED** for historical / protected
orders. Golden Pilot authorizes materialize **conditionally**:

```text
BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = True_CONDITIONAL
```

Meaning:
- protected orders (92401, 973012, 973013, 973010, …) are always rejected;
- only the registered golden-pilot next-dry fixture may materialize;
- no sessions / Employee Mobile / ExecutionActuals / CostEngine involvement.
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
# Scoped B stamp — multi-fixture registry (Batch 20D + Golden Pilot)
# ---------------------------------------------------------------------------
SCOPED_B_STAMP_STATUS = "SCOPED_B_STAMPED"

# Protected baselines — never materialize / rematerialize.
PROTECTED_ORDER_IDS: frozenset[int] = frozenset(
    {
        92401,
        973010,
        973012,
        973013,
    }
)

# Explicit registry. allow_materialize=True ONLY for golden pilot next-dry.
# order_id/plan_id for golden pilot are filled after canonical fixture create
# via register_golden_pilot_materialize_target (or static patch in this module).
SCOPED_B_FIXTURES: list[ScopedBFixture] = [
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
        "role": "protected_baseline",
        "allow_materialize": False,
    },
    {
        "order_id": 973012,
        "plan_id": 15,
        "fixture_id": "FIX-MATERIALS-RO-WRAP",
        "role": "protected_baseline",
        "allow_materialize": False,
    },
    {
        "order_id": 973013,
        "plan_id": 16,
        "fixture_id": "FIX-MATERIALS-RO-PAINT",
        "role": "protected_baseline",
        "allow_materialize": False,
    },
    # Golden Pilot V1 live fixture (973015 / plan 17).
    {
        "order_id": 973015,
        "plan_id": 17,
        "fixture_id": "FIX-GOLDEN-PILOT-TASK-GRAPH-V1",
        "role": "next_dry_target",
        "allow_materialize": True,
    },
]

# Scalar aliases = next dry target only (preflight / identity honesty).
SCOPED_B_ORDER_ID = 973015
SCOPED_B_PLAN_ID = 17
SCOPED_B_FIXTURE_ID = "FIX-GOLDEN-PILOT-TASK-GRAPH-V1"
SCOPED_B_ACTION = "exactly_one_post_materialize_tasks"
SCOPED_B_ALLOW = ("write_operational_tasks_into_v2_envelope",)
SCOPED_B_FORBID = (
    "sessions",
    "employee_mobile",
    "execution_actuals",
    "invent_minutes_wc_assign_downtime",
    "other_order_id_or_plan",
    "rematerialize_protected_orders",
    "rematerialize_973010_mat01",
    "rematerialize_92401_mat02",
    "rematerialize_973012",
    "rematerialize_973013",
)

# True_CONDITIONAL — authorize path open only for registered next-dry target.
BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = True
BATCH_EXECUTE_MATERIALIZE_MODE = "True_CONDITIONAL"

# Monkeypatched True only for legacy materialize *mechanic* unit tests.
# Production / default test path keeps the OD3 gate enforced.
_UNIT_TEST_BYPASS = False

ERROR_DEC009_MATERIALIZE_BLOCKED = "DEC009_MATERIALIZE_BLOCKED"

# Runtime identity stamp — proves this process loaded OD3 + current scoped-B.
OD3_GATE_MODULE = "services.dec009_materialize_gate"
OD3_RUNTIME_IDENTITY_VERSION = "golden-pilot-task-graph-v1/v1"
# First main merge that landed OD3 DEC-009 hard reject (PR #29).
OD3_MIN_MERGE_COMMIT = "a1b759c81355124f285b83425b93a9422f0e891e"


def register_golden_pilot_materialize_target(*, order_id: int, plan_id: int) -> None:
    """Register the sole materialize-allowed golden pilot fixture (in-process).

    Call after canonical Quote→Order→persist creates the new fixture.
    Rejects protected order IDs. Does not persist to DB — process-local only
    (dev runtime / tests). For a restarted server, set the same IDs in
    SCOPED_B_FIXTURES next_dry_target statically before start.
    """
    global SCOPED_B_ORDER_ID, SCOPED_B_PLAN_ID
    oid = int(order_id)
    pid = int(plan_id)
    if oid in PROTECTED_ORDER_IDS or oid <= 0 or pid <= 0:
        raise ValueError(
            f"refuse golden-pilot register for protected/invalid order={oid} plan={pid}"
        )
    for fixture in SCOPED_B_FIXTURES:
        if fixture["role"] == "next_dry_target":
            fixture["order_id"] = oid
            fixture["plan_id"] = pid
            fixture["allow_materialize"] = True
            SCOPED_B_ORDER_ID = oid
            SCOPED_B_PLAN_ID = pid
            return
    raise RuntimeError("scoped-B registry missing next_dry_target")


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
        "batch_execute_materialize_mode": BATCH_EXECUTE_MATERIALIZE_MODE,
        "protected_order_ids": sorted(PROTECTED_ORDER_IDS),
    }


def scoped_b_matches(*, order_id: int, plan_id: int | None = None) -> bool:
    """True only for the next-dry fixture that may receive an authorized POST.

    Protected / historical fixtures never match.
    """
    oid = int(order_id)
    if oid in PROTECTED_ORDER_IDS:
        return False
    for fixture in SCOPED_B_FIXTURES:
        if not fixture["allow_materialize"]:
            continue
        if fixture["role"] != "next_dry_target":
            continue
        if int(fixture["order_id"]) <= 0:
            return False
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
    oid = int(order_id)

    if oid in PROTECTED_ORDER_IDS:
        blockers.append("protected_order_forbidden")
    if LIVE_DEC009_STATUS == "A" and not BATCH_EXECUTE_MATERIALIZE_AUTHORIZED:
        blockers.append("live_dec009_A_blocked")
    if not BATCH_EXECUTE_MATERIALIZE_AUTHORIZED:
        blockers.append("batch_execute_materialize_not_authorized")
    if SCOPED_B_STAMP_STATUS != "SCOPED_B_STAMPED":
        blockers.append("scoped_b_not_stamped")
    if int(next_dry["order_id"]) <= 0:
        blockers.append("golden_pilot_target_unregistered")
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
        "batch_execute_materialize_mode": BATCH_EXECUTE_MATERIALIZE_MODE,
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
                f"execute_authorized={BATCH_EXECUTE_MATERIALIZE_AUTHORIZED} "
                f"({BATCH_EXECUTE_MATERIALIZE_MODE})."
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
            "batch_execute_materialize_mode": BATCH_EXECUTE_MATERIALIZE_MODE,
            "recovery": (
                "Golden Pilot True_CONDITIONAL: register next-dry via "
                "register_golden_pilot_materialize_target; never materialize "
                "protected orders 92401/973012/973013/973010."
            ),
        },
    )
