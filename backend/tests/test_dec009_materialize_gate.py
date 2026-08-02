"""OD3 DEC-009 server gate — Golden Pilot True_CONDITIONAL.

Protected orders never materialize. Only registered next-dry golden pilot may.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from services.dec009_materialize_gate import (
    BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
    BATCH_EXECUTE_MATERIALIZE_MODE,
    ERROR_DEC009_MATERIALIZE_BLOCKED,
    LIVE_DEC009_STATUS,
    OD3_GATE_MODULE,
    OD3_RUNTIME_IDENTITY_VERSION,
    PROTECTED_ORDER_IDS,
    SCOPED_B_FIXTURE_ID,
    SCOPED_B_STAMP_STATUS,
    build_od3_runtime_identity,
    enforce_dec009_materialize_gate,
    evaluate_materialize_authorization,
    register_golden_pilot_materialize_target,
    scoped_b_matches,
)

pytestmark = pytest.mark.enforce_dec009_gate


def test_live_dec009_remains_a_with_true_conditional():
    assert LIVE_DEC009_STATUS == "A"
    assert BATCH_EXECUTE_MATERIALIZE_AUTHORIZED is True
    assert BATCH_EXECUTE_MATERIALIZE_MODE == "True_CONDITIONAL"


def test_protected_orders_never_match():
    for oid in PROTECTED_ORDER_IDS:
        assert scoped_b_matches(order_id=oid, plan_id=13) is False
        decision = evaluate_materialize_authorization(order_id=oid, plan_id=13)
        assert decision["allowed"] is False
        assert "protected_order_forbidden" in decision["blockers"]


def test_out_of_scope_rejected_when_target_registered():
    register_golden_pilot_materialize_target(order_id=973015, plan_id=17)
    decision = evaluate_materialize_authorization(order_id=999001, plan_id=1)
    assert decision["allowed"] is False
    assert "order_or_plan_outside_scoped_b" in decision["blockers"]


def test_register_and_allow_only_golden_pilot():
    register_golden_pilot_materialize_target(order_id=973015, plan_id=17)
    assert scoped_b_matches(order_id=973015, plan_id=17) is True
    assert scoped_b_matches(order_id=973015, plan_id=99) is False
    assert scoped_b_matches(order_id=92401, plan_id=13) is False

    decision = evaluate_materialize_authorization(order_id=973015, plan_id=17)
    assert decision["allowed"] is True
    assert decision["blockers"] == []

    blocked = evaluate_materialize_authorization(order_id=92401, plan_id=13)
    assert blocked["allowed"] is False


def test_register_rejects_protected():
    with pytest.raises(ValueError):
        register_golden_pilot_materialize_target(order_id=92401, plan_id=13)


def test_od3_runtime_identity_stamp_for_preflight():
    register_golden_pilot_materialize_target(order_id=973015, plan_id=17)
    identity = build_od3_runtime_identity()
    assert identity["gate_landed"] is True
    assert identity["gate_module"] == OD3_GATE_MODULE
    assert identity["identity_version"] == OD3_RUNTIME_IDENTITY_VERSION
    assert identity["live_dec009"] == "A"
    assert identity["scoped_b_stamp"] == SCOPED_B_STAMP_STATUS
    assert identity["scoped_b_fixture_id"] == SCOPED_B_FIXTURE_ID
    assert identity["batch_execute_materialize_authorized"] is True
    assert identity["batch_execute_materialize_mode"] == "True_CONDITIONAL"
    assert 92401 in identity["protected_order_ids"]
    assert identity["scoped_b_order_id"] == 973015


def test_enforce_rejects_protected():
    with pytest.raises(HTTPException) as exc:
        enforce_dec009_materialize_gate(order_id=92401, plan_id=13)
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED


def test_enforce_allows_registered_pilot():
    register_golden_pilot_materialize_target(order_id=973015, plan_id=17)
    enforce_dec009_materialize_gate(order_id=973015, plan_id=17)
