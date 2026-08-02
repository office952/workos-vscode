"""OD3 DEC-009 server gate — True_CONDITIONAL + F7B closed/open pilot.

Default committed state is fail-closed. Open only via register / F7B helper.
Protected orders (including 973019) never materialize.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

import services.dec009_materialize_gate as gate
from services.dec009_materialize_gate import (
    BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
    BATCH_EXECUTE_MATERIALIZE_MODE,
    ERROR_DEC009_MATERIALIZE_BLOCKED,
    F7B_CONTROLLED_ORDER_ID,
    F7B_CONTROLLED_PLAN_ID,
    LIVE_DEC009_STATUS,
    OD3_GATE_MODULE,
    OD3_RUNTIME_IDENTITY_VERSION,
    PROTECTED_ORDER_IDS,
    SCOPED_B_STAMP_STATUS,
    build_od3_runtime_identity,
    close_materialize_pilot_gate,
    enforce_dec009_materialize_gate,
    evaluate_materialize_authorization,
    open_f7b_controlled_materialize_pilot,
    register_golden_pilot_materialize_target,
    scoped_b_matches,
)

pytestmark = pytest.mark.enforce_dec009_gate


@pytest.fixture(autouse=True)
def _fail_closed_default():
    """Each test starts from the committed closed posture."""
    close_materialize_pilot_gate()
    yield
    close_materialize_pilot_gate()


def test_live_dec009_remains_a_with_true_conditional():
    assert LIVE_DEC009_STATUS == "A"
    assert BATCH_EXECUTE_MATERIALIZE_AUTHORIZED is True
    assert BATCH_EXECUTE_MATERIALIZE_MODE == "True_CONDITIONAL"


def test_protected_orders_never_match():
    open_f7b_controlled_materialize_pilot()
    for oid in PROTECTED_ORDER_IDS:
        assert scoped_b_matches(order_id=oid, plan_id=13) is False
        decision = evaluate_materialize_authorization(order_id=oid, plan_id=13)
        assert decision["allowed"] is False
        assert "protected_order_forbidden" in decision["blockers"]


def test_973019_forbidden_even_when_f7b_open():
    open_f7b_controlled_materialize_pilot()
    assert 973019 in PROTECTED_ORDER_IDS
    decision = evaluate_materialize_authorization(order_id=973019, plan_id=21)
    assert decision["allowed"] is False
    assert "protected_order_forbidden" in decision["blockers"]
    with pytest.raises(HTTPException) as exc:
        enforce_dec009_materialize_gate(order_id=973019, plan_id=21)
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED


def test_f7b_880811_22_allowed_when_open():
    open_f7b_controlled_materialize_pilot()
    decision = evaluate_materialize_authorization(
        order_id=F7B_CONTROLLED_ORDER_ID, plan_id=F7B_CONTROLLED_PLAN_ID
    )
    assert decision["allowed"] is True
    assert decision["blockers"] == []
    assert decision["pilot_gate_open"] is True
    enforce_dec009_materialize_gate(
        order_id=F7B_CONTROLLED_ORDER_ID, plan_id=F7B_CONTROLLED_PLAN_ID
    )


def test_f7b_wrong_plan_for_880811_forbidden():
    open_f7b_controlled_materialize_pilot()
    decision = evaluate_materialize_authorization(
        order_id=F7B_CONTROLLED_ORDER_ID, plan_id=21
    )
    assert decision["allowed"] is False
    assert "order_or_plan_outside_scoped_b" in decision["blockers"]


def test_another_order_forbidden_when_f7b_open():
    open_f7b_controlled_materialize_pilot()
    decision = evaluate_materialize_authorization(order_id=999001, plan_id=1)
    assert decision["allowed"] is False
    assert "order_or_plan_outside_scoped_b" in decision["blockers"]


def test_second_identical_call_remains_eligible_for_idempotency():
    """Gate does not auto-close after allow — second POST may prove idempotency."""
    open_f7b_controlled_materialize_pilot()
    first = evaluate_materialize_authorization(
        order_id=F7B_CONTROLLED_ORDER_ID, plan_id=F7B_CONTROLLED_PLAN_ID
    )
    second = evaluate_materialize_authorization(
        order_id=F7B_CONTROLLED_ORDER_ID, plan_id=F7B_CONTROLLED_PLAN_ID
    )
    assert first["allowed"] is True
    assert second["allowed"] is True
    enforce_dec009_materialize_gate(
        order_id=F7B_CONTROLLED_ORDER_ID, plan_id=F7B_CONTROLLED_PLAN_ID
    )
    enforce_dec009_materialize_gate(
        order_id=F7B_CONTROLLED_ORDER_ID, plan_id=F7B_CONTROLLED_PLAN_ID
    )


def test_closed_final_state_allows_no_order():
    close_materialize_pilot_gate()
    identity = build_od3_runtime_identity()
    assert identity["pilot_gate_open"] is False
    assert identity["scoped_b_order_id"] == 0
    for oid, pid in (
        (F7B_CONTROLLED_ORDER_ID, F7B_CONTROLLED_PLAN_ID),
        (973019, 21),
        (999001, 1),
        (92401, 13),
    ):
        decision = evaluate_materialize_authorization(order_id=oid, plan_id=pid)
        assert decision["allowed"] is False
        assert "pilot_gate_closed" in decision["blockers"] or (
            "protected_order_forbidden" in decision["blockers"]
        )


def test_out_of_scope_rejected_when_target_registered():
    register_golden_pilot_materialize_target(order_id=973099, plan_id=99)
    decision = evaluate_materialize_authorization(order_id=999001, plan_id=1)
    assert decision["allowed"] is False
    assert "order_or_plan_outside_scoped_b" in decision["blockers"]


def test_register_and_allow_only_golden_pilot():
    register_golden_pilot_materialize_target(order_id=973099, plan_id=99)
    assert scoped_b_matches(order_id=973099, plan_id=99) is True
    assert scoped_b_matches(order_id=973099, plan_id=17) is False
    assert scoped_b_matches(order_id=92401, plan_id=13) is False
    assert scoped_b_matches(order_id=973015, plan_id=17) is False
    assert scoped_b_matches(order_id=973018, plan_id=20) is False
    assert scoped_b_matches(order_id=973019, plan_id=21) is False

    decision = evaluate_materialize_authorization(order_id=973099, plan_id=99)
    assert decision["allowed"] is True
    assert decision["blockers"] == []

    blocked = evaluate_materialize_authorization(order_id=92401, plan_id=13)
    assert blocked["allowed"] is False
    blocked_old = evaluate_materialize_authorization(order_id=973015, plan_id=17)
    assert blocked_old["allowed"] is False
    blocked_pt = evaluate_materialize_authorization(order_id=973018, plan_id=20)
    assert blocked_pt["allowed"] is False


def test_register_rejects_protected():
    with pytest.raises(ValueError):
        register_golden_pilot_materialize_target(order_id=92401, plan_id=13)
    with pytest.raises(ValueError):
        register_golden_pilot_materialize_target(order_id=973015, plan_id=17)
    with pytest.raises(ValueError):
        register_golden_pilot_materialize_target(order_id=973018, plan_id=20)
    with pytest.raises(ValueError):
        register_golden_pilot_materialize_target(order_id=973019, plan_id=21)


def test_od3_runtime_identity_stamp_for_preflight():
    register_golden_pilot_materialize_target(order_id=973099, plan_id=99)
    identity = build_od3_runtime_identity()
    assert identity["gate_landed"] is True
    assert identity["gate_module"] == OD3_GATE_MODULE
    assert identity["identity_version"] == OD3_RUNTIME_IDENTITY_VERSION
    assert identity["live_dec009"] == "A"
    assert identity["scoped_b_stamp"] == SCOPED_B_STAMP_STATUS
    assert identity["scoped_b_fixture_id"] == gate.SCOPED_B_FIXTURE_ID
    assert identity["scoped_b_fixture_id"] == "FIX-PILOT-MATERIALIZE-973099-99"
    assert identity["batch_execute_materialize_authorized"] is True
    assert identity["batch_execute_materialize_mode"] == "True_CONDITIONAL"
    assert 92401 in identity["protected_order_ids"]
    assert 973015 in identity["protected_order_ids"]
    assert 973018 in identity["protected_order_ids"]
    assert 973019 in identity["protected_order_ids"]
    assert identity["scoped_b_order_id"] == 973099
    assert identity["pilot_gate_open"] is True


def test_enforce_rejects_protected():
    with pytest.raises(HTTPException) as exc:
        enforce_dec009_materialize_gate(order_id=92401, plan_id=13)
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED


def test_enforce_allows_registered_pilot():
    register_golden_pilot_materialize_target(order_id=973099, plan_id=99)
    enforce_dec009_materialize_gate(order_id=973099, plan_id=99)
