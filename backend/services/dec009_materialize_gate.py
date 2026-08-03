"""OD3 server-side DEC-009 gate for POST materialize.

Owner decision 2026-08-03 (Finalization Wave 3):
```text
DEC-009 = B
FINALIZATION_WAVE_3_GO = GRANTED_WITH_STRICT_SCOPE
```

DEC-009=B authorizes controlled operational task materialization only for the
registered next-dry non-production fixture. It does **not** authorize
assignment, sessions, scheduling, capacity, Employee Mobile, or production
rollout.

Protected baselines never materialize. Fail-closed when next-dry is closed or
the process runs under a production APP_ENV/ENVIRONMENT label.
"""

from __future__ import annotations

import os
from typing import Any, TypedDict

from fastapi import HTTPException


class ScopedBFixture(TypedDict):
    order_id: int
    plan_id: int
    fixture_id: str
    role: str
    allow_materialize: bool


# ---------------------------------------------------------------------------
# Live DEC-009 (Owner-recorded Wave 3)
# ---------------------------------------------------------------------------
LIVE_DEC009_STATUS = "B"
LIVE_DEC009_LABEL = "CONTROLLED_SCOPED_MATERIALIZE"

# ---------------------------------------------------------------------------
# Scoped B stamp — multi-fixture registry
# ---------------------------------------------------------------------------
SCOPED_B_STAMP_STATUS = "SCOPED_B_STAMPED"

# Protected baselines — never materialize / rematerialize.
PROTECTED_ORDER_IDS: frozenset[int] = frozenset(
    {
        88002,  # historical Step 9 fixture — read-only
        880811,  # F7B / Wave 2 protected commercial baseline
        92401,
        973010,
        973012,
        973013,
        973015,  # Golden Pilot task-graph baseline — never rematerialize
        973018,  # Golden Pilot planning-truth baseline — LED ambiguous frozen
        973019,  # Golden Pilot eligibility RM / protected commercial — never materialize
    }
)

# Wave 3 controlled durable QA fixture (Owner GO — Finalization Wave 3).
WAVE3_CONTROLLED_ORDER_ID = 880750
WAVE3_CONTROLLED_PLAN_ID = 23
WAVE3_CONTROLLED_FIXTURE_ID = "WAVE2-DURABLE-QA-880750"

# Explicit registry. allow_materialize=True ONLY for the open next-dry target.
# Wave 3 committed posture: next-dry open for durable fixture 880750 / plan 23.
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
    {
        "order_id": 880811,
        "plan_id": 22,
        "fixture_id": "FIX-F7B-CONTROLLED-MATERIALIZE-880811",
        "role": "protected_baseline",
        "allow_materialize": False,
    },
    {
        "order_id": WAVE3_CONTROLLED_ORDER_ID,
        "plan_id": WAVE3_CONTROLLED_PLAN_ID,
        "fixture_id": WAVE3_CONTROLLED_FIXTURE_ID,
        "role": "next_dry_target",
        "allow_materialize": True,
    },
]

# Scalar aliases = next dry target only (preflight / identity honesty).
SCOPED_B_ORDER_ID = WAVE3_CONTROLLED_ORDER_ID
SCOPED_B_PLAN_ID = WAVE3_CONTROLLED_PLAN_ID
SCOPED_B_FIXTURE_ID = WAVE3_CONTROLLED_FIXTURE_ID
SCOPED_B_ACTION = "exactly_one_post_materialize_tasks"
SCOPED_B_ALLOW = ("write_operational_tasks_into_v2_envelope",)
SCOPED_B_FORBID = (
    "sessions",
    "employee_mobile",
    "execution_actuals",
    "invent_minutes_wc_assign_downtime",
    "other_order_id_or_plan",
    "rematerialize_protected_orders",
    "assignment",
    "machine_assignment",
    "scheduling",
    "capacity_allocation",
    "production_rollout",
)

# True_CONDITIONAL — authorize path open only for registered next-dry target.
BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = True
BATCH_EXECUTE_MATERIALIZE_MODE = "True_CONDITIONAL"

# Monkeypatched True only for legacy materialize *mechanic* unit tests.
_UNIT_TEST_BYPASS = False

ERROR_DEC009_MATERIALIZE_BLOCKED = "DEC009_MATERIALIZE_BLOCKED"

OD3_GATE_MODULE = "services.dec009_materialize_gate"
OD3_RUNTIME_IDENTITY_VERSION = "wave3-controlled-materialize-880750/v1"
OD3_MIN_MERGE_COMMIT = "a1b759c81355124f285b83425b93a9422f0e891e"

# Historical F7B constants retained for docs/tests that reference the closed pilot.
F7B_CONTROLLED_ORDER_ID = 880811
F7B_CONTROLLED_PLAN_ID = 22
F7B_CONTROLLED_FIXTURE_ID = "FIX-F7B-CONTROLLED-MATERIALIZE-880811"


def _is_production_environment() -> bool:
    for key in ("APP_ENV", "ENVIRONMENT"):
        value = (os.environ.get(key) or "").strip().lower()
        if value in {"production", "prod"}:
            return True
    return False


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

    Rejects protected order IDs. Process-local only unless also written into
    SCOPED_B_FIXTURES next_dry_target for a restarted server.
    """
    global SCOPED_B_ORDER_ID, SCOPED_B_PLAN_ID, SCOPED_B_FIXTURE_ID
    oid = int(order_id)
    pid = int(plan_id)
    if oid in PROTECTED_ORDER_IDS or oid <= 0 or pid <= 0:
        raise ValueError(
            f"refuse materialize register for protected/invalid order={oid} plan={pid}"
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
    """Fail-closed: clear next-dry so no order may materialize."""
    global SCOPED_B_ORDER_ID, SCOPED_B_PLAN_ID, SCOPED_B_FIXTURE_ID
    for fixture in SCOPED_B_FIXTURES:
        if fixture["role"] == "next_dry_target":
            fixture["order_id"] = 0
            fixture["plan_id"] = 0
            fixture["fixture_id"] = "FIX-MATERIALIZE-GATE-CLOSED"
            fixture["allow_materialize"] = False
            SCOPED_B_ORDER_ID = 0
            SCOPED_B_PLAN_ID = 0
            SCOPED_B_FIXTURE_ID = "FIX-MATERIALIZE-GATE-CLOSED"
            return
    raise RuntimeError("scoped-B registry missing next_dry_target")


def open_wave3_controlled_materialize_target() -> None:
    """Open exactly order 880750 / plan 23 for Finalization Wave 3."""
    register_golden_pilot_materialize_target(
        order_id=WAVE3_CONTROLLED_ORDER_ID,
        plan_id=WAVE3_CONTROLLED_PLAN_ID,
        fixture_id=WAVE3_CONTROLLED_FIXTURE_ID,
    )


def open_f7b_controlled_materialize_pilot() -> None:
    """Historical F7B helper — 880811 is now protected; cannot reopen.

    Use ``open_wave3_controlled_materialize_target`` or
    ``register_golden_pilot_materialize_target`` for authorized fixtures.
    """
    raise ValueError(
        "F7B order 880811 is a protected baseline; cannot open materialize pilot. "
        "Use open_wave3_controlled_materialize_target() for Wave 3 fixture 880750."
    )


def build_od3_runtime_identity() -> dict[str, Any]:
    """Read-only OD3 gate identity for preflight / stale-runtime detection."""
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
        "production_environment": _is_production_environment(),
    }


def scoped_b_matches(*, order_id: int, plan_id: int | None = None) -> bool:
    """True only for the next-dry fixture that may receive an authorized POST."""
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

    if _is_production_environment():
        blockers.append("production_environment_forbidden")
    if oid in PROTECTED_ORDER_IDS:
        blockers.append("protected_order_forbidden")
    if LIVE_DEC009_STATUS == "A" and not BATCH_EXECUTE_MATERIALIZE_AUTHORIZED:
        blockers.append("live_dec009_A_blocked")
    if LIVE_DEC009_STATUS not in {"A", "B"}:
        blockers.append("live_dec009_unknown_status")
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
        "production_environment": _is_production_environment(),
    }


def enforce_dec009_materialize_gate(
    *,
    order_id: int,
    plan_id: int | None = None,
) -> None:
    """Hard-reject materialize when unauthorized. Never writes."""
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
                "DEC-009=B True_CONDITIONAL: only the registered next-dry fixture "
                "may materialize (Wave 3: 880750/plan 23). Close via "
                "close_materialize_pilot_gate; never materialize protected orders "
                "including 880811 and 973019. Production APP_ENV is always denied."
            ),
        },
    )
