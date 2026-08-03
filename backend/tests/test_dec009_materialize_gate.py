"""OD3 DEC-009 server gate — True_CONDITIONAL + Wave 3 scoped B.

Default committed module state opens next-dry for durable fixture 880750/23.
Unit tests start from fail-closed via close_materialize_pilot_gate(), then
open the Wave 3 helper or register_golden_pilot_materialize_target.
Protected orders (880811, 973019, …) never materialize.
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
    WAVE3_CONTROLLED_FIXTURE_ID,
    WAVE3_CONTROLLED_ORDER_ID,
    WAVE3_CONTROLLED_PLAN_ID,
    build_od3_runtime_identity,
    close_materialize_pilot_gate,
    enforce_dec009_materialize_gate,
    evaluate_materialize_authorization,
    open_f7b_controlled_materialize_pilot,
    open_wave3_controlled_materialize_target,
    register_golden_pilot_materialize_target,
    scoped_b_matches,
)

pytestmark = pytest.mark.enforce_dec009_gate


@pytest.fixture(autouse=True)
def _fail_closed_default():
    """Each test starts from the fail-closed posture."""
    close_materialize_pilot_gate()
    yield
    close_materialize_pilot_gate()


def test_live_dec009_is_b_with_true_conditional():
    assert LIVE_DEC009_STATUS == "B"
    assert BATCH_EXECUTE_MATERIALIZE_AUTHORIZED is True
    assert BATCH_EXECUTE_MATERIALIZE_MODE == "True_CONDITIONAL"


def test_protected_orders_never_match():
    open_wave3_controlled_materialize_target()
    for oid in PROTECTED_ORDER_IDS:
        assert scoped_b_matches(order_id=oid, plan_id=13) is False
        decision = evaluate_materialize_authorization(order_id=oid, plan_id=13)
        assert decision["allowed"] is False
        assert "protected_order_forbidden" in decision["blockers"]


def test_973019_and_880811_forbidden_even_when_wave3_open():
    open_wave3_controlled_materialize_target()
    assert 973019 in PROTECTED_ORDER_IDS
    assert 880811 in PROTECTED_ORDER_IDS
    for oid, pid in ((973019, 21), (880811, 22), (F7B_CONTROLLED_ORDER_ID, F7B_CONTROLLED_PLAN_ID)):
        decision = evaluate_materialize_authorization(order_id=oid, plan_id=pid)
        assert decision["allowed"] is False
        assert "protected_order_forbidden" in decision["blockers"]
        with pytest.raises(HTTPException) as exc:
            enforce_dec009_materialize_gate(order_id=oid, plan_id=pid)
        assert exc.value.status_code == 422
        assert exc.value.detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED


def test_f7b_helper_refuses_protected_880811():
    with pytest.raises(ValueError, match="880811"):
        open_f7b_controlled_materialize_pilot()


def test_wave3_880750_23_allowed_when_open():
    open_wave3_controlled_materialize_target()
    decision = evaluate_materialize_authorization(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID
    )
    assert decision["allowed"] is True
    assert decision["blockers"] == []
    assert decision["pilot_gate_open"] is True
    assert decision["live_dec009"] == "B"
    enforce_dec009_materialize_gate(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID
    )


def test_wave3_wrong_plan_for_880750_forbidden():
    open_wave3_controlled_materialize_target()
    decision = evaluate_materialize_authorization(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=21
    )
    assert decision["allowed"] is False
    assert "order_or_plan_outside_scoped_b" in decision["blockers"]


def test_another_order_forbidden_when_wave3_open():
    open_wave3_controlled_materialize_target()
    decision = evaluate_materialize_authorization(order_id=999001, plan_id=1)
    assert decision["allowed"] is False
    assert "order_or_plan_outside_scoped_b" in decision["blockers"]


def test_second_identical_call_remains_eligible_for_idempotency():
    """Gate does not auto-close after allow — second POST may prove idempotency."""
    open_wave3_controlled_materialize_target()
    first = evaluate_materialize_authorization(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID
    )
    second = evaluate_materialize_authorization(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID
    )
    assert first["allowed"] is True
    assert second["allowed"] is True
    enforce_dec009_materialize_gate(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID
    )
    enforce_dec009_materialize_gate(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID
    )


def test_closed_final_state_allows_no_order():
    close_materialize_pilot_gate()
    identity = build_od3_runtime_identity()
    assert identity["pilot_gate_open"] is False
    assert identity["scoped_b_order_id"] == 0
    for oid, pid in (
        (WAVE3_CONTROLLED_ORDER_ID, WAVE3_CONTROLLED_PLAN_ID),
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


def test_production_environment_forbidden(monkeypatch):
    open_wave3_controlled_materialize_target()
    monkeypatch.setenv("APP_ENV", "production")
    decision = evaluate_materialize_authorization(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID
    )
    assert decision["allowed"] is False
    assert "production_environment_forbidden" in decision["blockers"]


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
    assert scoped_b_matches(order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID) is False

    decision = evaluate_materialize_authorization(order_id=973099, plan_id=99)
    assert decision["allowed"] is True
    assert decision["blockers"] == []

    blocked = evaluate_materialize_authorization(order_id=92401, plan_id=13)
    assert blocked["allowed"] is False


def test_register_rejects_protected():
    with pytest.raises(ValueError):
        register_golden_pilot_materialize_target(order_id=92401, plan_id=13)
    with pytest.raises(ValueError):
        register_golden_pilot_materialize_target(order_id=880811, plan_id=22)
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
    assert identity["live_dec009"] == "B"
    assert identity["scoped_b_stamp"] == SCOPED_B_STAMP_STATUS
    assert identity["scoped_b_fixture_id"] == gate.SCOPED_B_FIXTURE_ID
    assert identity["scoped_b_fixture_id"] == "FIX-PILOT-MATERIALIZE-973099-99"
    assert identity["batch_execute_materialize_authorized"] is True
    assert identity["batch_execute_materialize_mode"] == "True_CONDITIONAL"
    assert 92401 in identity["protected_order_ids"]
    assert 880811 in identity["protected_order_ids"]
    assert 973019 in identity["protected_order_ids"]
    assert identity["scoped_b_order_id"] == 973099
    assert identity["pilot_gate_open"] is True


def test_committed_wave3_defaults_after_open_helper():
    open_wave3_controlled_materialize_target()
    identity = build_od3_runtime_identity()
    assert identity["scoped_b_order_id"] == WAVE3_CONTROLLED_ORDER_ID
    assert identity["scoped_b_plan_id"] == WAVE3_CONTROLLED_PLAN_ID
    assert identity["scoped_b_fixture_id"] == WAVE3_CONTROLLED_FIXTURE_ID


def test_enforce_rejects_protected():
    with pytest.raises(HTTPException) as exc:
        enforce_dec009_materialize_gate(order_id=92401, plan_id=13)
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED


def test_enforce_allows_registered_pilot():
    register_golden_pilot_materialize_target(order_id=973099, plan_id=99)
    enforce_dec009_materialize_gate(order_id=973099, plan_id=99)
