"""OD3 server-side DEC-009 gate for POST materialize (Golden Pilot / F7B).

Live DEC-009 remains Owner-LOCKED **A / BLOCKED** for historical / protected
orders. Materialize is authorized **conditionally** only when a next-dry
target is explicitly registered with ``allow_materialize=True``.

F7B controlled pilot (Owner resume 2026-08-02):
- temporary open target was order ``880811`` / plan ``22`` only;
- protected commercial baseline ``973019`` / plan ``21`` is forbidden;
- after pilot evidence, the gate must be **closed** (no open next-dry).

```text
BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = True_CONDITIONAL
```

Meaning:
- protected orders never materialize;
- only the registered next-dry fixture may materialize when open;
- when the pilot gate is closed, every order is rejected;
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
# Scoped B stamp — multi-fixture registry (Batch 20D + Golden Pilot + F7B)
# ---------------------------------------------------------------------------
SCOPED_B_STAMP_STATUS = "SCOPED_B_STAMPED"

# Protected baselines — never materialize / rematerialize.
# 973019 = Golden Pilot eligibility / commercial protected baseline (F7B).
PROTECTED_ORDER_IDS: frozenset[int] = frozenset(
    {
        92401,
        973010,
        973012,
        973013,
        973015,  # Golden Pilot task-graph baseline — never rematerialize
        973018,  # Golden Pilot planning-truth baseline — LED ambiguous frozen
        973019,  # Golden Pilot eligibility RM / protected commercial — never materialize
    }
)

# Explicit registry. allow_materialize=True ONLY for an open next-dry pilot.
# FINAL COMMITTED STATE (post-F7B): next_dry closed — no order authorized.
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
    {
        "order_id": 973015,
        "plan_id": 17,
        "fixture_id": "FIX-GOLDEN-PILOT-TASK-GRAPH-V1",
        "role": "protected_baseline",
        "allow_materialize": False,
    },
    {
        "order_id": 973018,
        "plan_id": 20,
        "fixture_id": "FIX-GOLDEN-PILOT-PLANNING-TRUTH-V1",
        "role": "protected_baseline",
        "allow_materialize": False,
    },
    {
        "order_id": 973019,
        "plan_id": 21,
        "fixture_id": "FIX-GOLDEN-PILOT-ELIGIBILITY-RM-V1",
        "role": "protected_baseline",
        "allow_materialize": False,
    },
    # Closed next-dry stub — F7B pilot complete; no open materialize target.
    {
        "order_id": 0,
        "plan_id": 0,
        "fixture_id": "FIX-F7B-CONTROLLED-MATERIALIZE-CLOSED",
        "role": "next_dry_target",
        "allow_materialize": False,
    },
]

# Scalar aliases = next dry target only (preflight / identity honesty).
# Closed: zeros + closed fixture id. Open only via register_* during pilot/tests.
SCOPED_B_ORDER_ID = 0
SCOPED_B_PLAN_ID = 0
SCOPED_B_FIXTURE_ID = "FIX-F7B-CONTROLLED-MATERIALIZE-CLOSED"
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
    "rematerialize_973015",
    "rematerialize_973018",
    "rematerialize_973019",
    "rematerialize_after_f7b_gate_closed",
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
OD3_RUNTIME_IDENTITY_VERSION = "f7b-controlled-materialize-closed/v1"
# First main merge that landed OD3 DEC-009 hard reject (PR #29).
OD3_MIN_MERGE_COMMIT = "a1b759c81355124f285b83425b93a9422f0e891e"

# F7B controlled fixture identity (Owner-authorized pair; not an open grant).
F7B_CONTROLLED_ORDER_ID = 880811
F7B_CONTROLLED_PLAN_ID = 22
F7B_CONTROLLED_FIXTURE_ID = "FIX-F7B-CONTROLLED-MATERIALIZE-880811"


def _next_dry_entry() -> ScopedBFixture:
    for fixture in SCOPED_B_FIXTURES:
        if fixture["role"] == "next_dry_target":
            return fixture
    raise RuntimeError("scoped-B registry missing next_dry_target")


def _open_next_dry_fixture() -> ScopedBFixture | None:
    fixture = _next_dry_entry()
    if fixture["allow_materialize"] and int(fixture["order_id"]) > 0:
        return fixture
    return None


def register_golden_pilot_materialize_target(
    *,
    order_id: int,
    plan_id: int,
    fixture_id: str | None = None,
) -> None:
    """Register the sole materialize-allowed next-dry fixture (in-process).

    Call after canonical Quote→Order→persist creates the new fixture, or for
    controlled F7B open. Rejects protected order IDs. Does not persist to DB —
    process-local only (dev runtime / tests). For a restarted server, set the
    same IDs in SCOPED_B_FIXTURES next_dry_target statically before start.
    """
    global SCOPED_B_ORDER_ID, SCOPED_B_PLAN_ID, SCOPED_B_FIXTURE_ID
    oid = int(order_id)
    pid = int(plan_id)
    if oid in PROTECTED_ORDER_IDS or oid <= 0 or pid <= 0:
        raise ValueError(
            f"refuse golden-pilot register for protected/invalid order={oid} plan={pid}"
        )
    fid = fixture_id or f"FIX-PILOT-MATERIALIZE-{oid}-{pid}"
    for fixture in SCOPED_B_FIXTURES:
        if fixture["role"] == "next_dry_target":
            fixture["order_id"] = oid
            fixture["plan_id"] = pid
            fixture["fixture_id"] = fid
            fixture["allow_materialize"] = True
            SCOPED_B_ORDER_ID = oid
            SCOPED_B_PLAN_ID = pid
            SCOPED_B_FIXTURE_ID = fid
            return
    raise RuntimeError("scoped-B registry missing next_dry_target")


def close_materialize_pilot_gate() -> None:
    """Fail-closed: clear next-dry so no order may materialize.

    Final F7B committed posture. Does not reopen 973019 as next_dry.
    """
    global SCOPED_B_ORDER_ID, SCOPED_B_PLAN_ID, SCOPED_B_FIXTURE_ID
    for fixture in SCOPED_B_FIXTURES:
        if fixture["role"] == "next_dry_target":
            fixture["order_id"] = 0
            fixture["plan_id"] = 0
            fixture["fixture_id"] = "FIX-F7B-CONTROLLED-MATERIALIZE-CLOSED"
            fixture["allow_materialize"] = False
            SCOPED_B_ORDER_ID = 0
            SCOPED_B_PLAN_ID = 0
            SCOPED_B_FIXTURE_ID = "FIX-F7B-CONTROLLED-MATERIALIZE-CLOSED"
            return
    raise RuntimeError("scoped-B registry missing next_dry_target")


def open_f7b_controlled_materialize_pilot() -> None:
    """Open exactly order 880811 / plan 22 for the controlled F7B POST window.

    Must be closed via ``close_materialize_pilot_gate`` after evidence.
    """
    register_golden_pilot_materialize_target(
        order_id=F7B_CONTROLLED_ORDER_ID,
        plan_id=F7B_CONTROLLED_PLAN_ID,
        fixture_id=F7B_CONTROLLED_FIXTURE_ID,
    )


def build_od3_runtime_identity() -> dict[str, Any]:
    """Read-only OD3 gate identity for preflight / stale-runtime detection.

    No DB I/O. No authorization side effects. Not an execute path.
    """
    next_dry = _next_dry_entry()
    open_target = _open_next_dry_fixture()
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
        "pilot_gate_open": open_target is not None,
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

    Protected / historical fixtures never match. Closed gate never matches.
    """
    oid = int(order_id)
    if oid in PROTECTED_ORDER_IDS:
        return False
    open_target = _open_next_dry_fixture()
    if open_target is None:
        return False
    if oid != int(open_target["order_id"]):
        return False
    if plan_id is not None and int(plan_id) != int(open_target["plan_id"]):
        return False
    return True


def evaluate_materialize_authorization(
    *,
    order_id: int,
    plan_id: int | None = None,
) -> dict[str, Any]:
    """Pure authorization evaluation — no DB I/O, no writes."""
    blockers: list[str] = []
    next_dry = _next_dry_entry()
    open_target = _open_next_dry_fixture()
    oid = int(order_id)

    if oid in PROTECTED_ORDER_IDS:
        blockers.append("protected_order_forbidden")
    if LIVE_DEC009_STATUS == "A" and not BATCH_EXECUTE_MATERIALIZE_AUTHORIZED:
        blockers.append("live_dec009_A_blocked")
    if not BATCH_EXECUTE_MATERIALIZE_AUTHORIZED:
        blockers.append("batch_execute_materialize_not_authorized")
    if SCOPED_B_STAMP_STATUS != "SCOPED_B_STAMPED":
        blockers.append("scoped_b_not_stamped")
    if open_target is None:
        blockers.append("pilot_gate_closed")
    elif not scoped_b_matches(order_id=order_id, plan_id=plan_id):
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
        "pilot_gate_open": open_target is not None,
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

    next_dry = _next_dry_entry()
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
                "allow_materialize": next_dry["allow_materialize"],
            },
            "scoped_b_fixtures": list(decision["scoped_b_fixtures"]),
            "batch_execute_materialize_authorized": BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
            "batch_execute_materialize_mode": BATCH_EXECUTE_MATERIALIZE_MODE,
            "recovery": (
                "True_CONDITIONAL: open a next-dry via "
                "register_golden_pilot_materialize_target / "
                "open_f7b_controlled_materialize_pilot only under Owner GO; "
                "close via close_materialize_pilot_gate after evidence; "
                "never materialize protected orders including 973019."
            ),
        },
    )
