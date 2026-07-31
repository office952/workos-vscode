"""OD3 DEC-009 server gate + scoped B stamp (Capacity Batch 14B / 20D).

No successful materialize. No operational_tasks / sessions / ExecutionActuals.
"""

from __future__ import annotations

import json

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from models.execution_plan import ExecutionPlan
from services.dec009_materialize_gate import (
    BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
    ERROR_DEC009_MATERIALIZE_BLOCKED,
    LIVE_DEC009_STATUS,
    OD3_GATE_MODULE,
    OD3_MIN_MERGE_COMMIT,
    OD3_RUNTIME_IDENTITY_VERSION,
    SCOPED_B_FIXTURE_ID,
    SCOPED_B_FIXTURES,
    SCOPED_B_ORDER_ID,
    SCOPED_B_PLAN_ID,
    SCOPED_B_STAMP_STATUS,
    build_od3_runtime_identity,
    enforce_dec009_materialize_gate,
    evaluate_materialize_authorization,
    scoped_b_matches,
)
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot

pytestmark = pytest.mark.enforce_dec009_gate

_GATE_OID = 29890


def test_live_dec009_remains_a_blocked():
    assert LIVE_DEC009_STATUS == "A"
    assert BATCH_EXECUTE_MATERIALIZE_AUTHORIZED is False


def test_od3_runtime_identity_stamp_for_preflight():
    """20D: process identity proves OD3 + multi-fixture scoped-B (not execute)."""
    identity = build_od3_runtime_identity()
    assert identity["gate_landed"] is True
    assert identity["gate_module"] == OD3_GATE_MODULE
    assert identity["identity_version"] == OD3_RUNTIME_IDENTITY_VERSION
    assert identity["min_merge_commit"] == OD3_MIN_MERGE_COMMIT
    assert identity["live_dec009"] == "A"
    assert identity["scoped_b_stamp"] == "SCOPED_B_STAMPED"
    assert identity["scoped_b_order_id"] == 92401
    assert identity["scoped_b_plan_id"] == 13
    assert identity["scoped_b_fixture_id"] == "FIX-DEC009-MAT-02"
    assert identity["batch_execute_materialize_authorized"] is False
    roles = {f["role"]: f for f in identity["scoped_b_fixtures"]}
    assert roles["historical_stamped"]["order_id"] == 973010
    assert roles["historical_stamped"]["allow_materialize"] is False
    assert roles["next_dry_target"]["order_id"] == 92401
    assert roles["next_dry_target"]["allow_materialize"] is True


def test_scoped_b_stamp_exact_scope():
    assert SCOPED_B_STAMP_STATUS == "SCOPED_B_STAMPED"
    assert SCOPED_B_ORDER_ID == 92401
    assert SCOPED_B_PLAN_ID == 13
    assert SCOPED_B_FIXTURE_ID == "FIX-DEC009-MAT-02"
    assert len(SCOPED_B_FIXTURES) == 2
    # Next dry target matches; historical MAT-01 does not (no rematerialize).
    assert scoped_b_matches(order_id=92401, plan_id=13) is True
    assert scoped_b_matches(order_id=92401, plan_id=99) is False
    assert scoped_b_matches(order_id=973010, plan_id=12) is False
    assert scoped_b_matches(order_id=1, plan_id=13) is False


def test_evaluate_rejects_while_live_a_and_execute_unauthorized():
    for order_id, plan_id in ((92401, 13), (973010, 12)):
        decision = evaluate_materialize_authorization(
            order_id=order_id,
            plan_id=plan_id,
        )
        assert decision["allowed"] is False
        assert "live_dec009_A_blocked" in decision["blockers"]
        assert "batch_execute_materialize_not_authorized" in decision["blockers"]


def test_evaluate_rejects_out_of_scope_even_if_execute_patched(monkeypatch):
    monkeypatch.setattr(
        "services.dec009_materialize_gate.BATCH_EXECUTE_MATERIALIZE_AUTHORIZED",
        True,
    )
    decision = evaluate_materialize_authorization(order_id=1, plan_id=13)
    assert decision["allowed"] is False
    assert "order_or_plan_outside_scoped_b" in decision["blockers"]


def test_evaluate_rejects_historical_mat01_even_if_execute_patched(monkeypatch):
    """MAT-01 remains in registry but rematerialize is forbidden."""
    monkeypatch.setattr(
        "services.dec009_materialize_gate.BATCH_EXECUTE_MATERIALIZE_AUTHORIZED",
        True,
    )
    decision = evaluate_materialize_authorization(order_id=973010, plan_id=12)
    assert decision["allowed"] is False
    assert "order_or_plan_outside_scoped_b" in decision["blockers"]


def test_evaluate_allows_only_when_execute_and_scoped(monkeypatch):
    monkeypatch.setattr(
        "services.dec009_materialize_gate.BATCH_EXECUTE_MATERIALIZE_AUTHORIZED",
        True,
    )
    decision = evaluate_materialize_authorization(
        order_id=SCOPED_B_ORDER_ID,
        plan_id=SCOPED_B_PLAN_ID,
    )
    assert decision["allowed"] is True
    assert decision["blockers"] == []


def test_enforce_hard_rejects_without_side_effects():
    with pytest.raises(HTTPException) as exc:
        enforce_dec009_materialize_gate(
            order_id=SCOPED_B_ORDER_ID,
            plan_id=SCOPED_B_PLAN_ID,
        )
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED
    assert exc.value.detail["live_dec009"] == "A"
    assert exc.value.detail["scoped_b_stamp"] == "SCOPED_B_STAMPED"
    assert exc.value.detail["batch_execute_materialize_authorized"] is False
    assert exc.value.detail["scoped_b_scope"]["order_id"] == 92401


def test_enforce_hard_rejects_92401_and_973010_without_authorize():
    """Unauthorized POST identity must stay 422 for both fixture orders."""
    for order_id, plan_id in ((92401, 13), (973010, 12)):
        with pytest.raises(HTTPException) as exc:
            enforce_dec009_materialize_gate(order_id=order_id, plan_id=plan_id)
        assert exc.value.status_code == 422
        assert exc.value.detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED
        assert exc.value.detail["batch_execute_materialize_authorized"] is False
        blockers = exc.value.detail["blockers"]
        assert "batch_execute_materialize_not_authorized" in blockers
        assert "live_dec009_A_blocked" in blockers


@pytest.mark.asyncio
async def test_materialize_service_hard_rejects_and_writes_no_ops(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_GATE_OID)
    await create_execution_plan_v2_from_order(db_session, order.id)
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order.id)
        )
    ).scalar_one()
    before = json.loads(plan.tasks_json)

    with pytest.raises(HTTPException) as exc:
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)

    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED

    await db_session.refresh(plan)
    after = json.loads(plan.tasks_json)
    assert after.get("execution_tasks_created") is not True
    assert after.get("operational_tasks") in (None, [])
    assert after.get("planned_tasks") == before.get("planned_tasks")


def test_endpoint_hard_rejects_post_without_creating_ops(
    db_fixture, db_session, auth_client
):
    order_id = _GATE_OID + 1

    async def _setup():
        order = await _seed_v2_order_with_snapshot(db_session, order_id=order_id)
        await create_execution_plan_v2_from_order(db_session, order.id)

    db_fixture.run(_setup())
    resp = auth_client.post(f"/api/v1/execution/plan-v2/materialize-tasks/{order_id}")
    assert resp.status_code == 422, resp.text
    body = resp.json()
    detail = body.get("detail") or body
    assert detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED
    assert detail["live_dec009"] == "A"

    async def _assert_no_ops():
        plan = (
            await db_session.execute(
                select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
            )
        ).scalar_one()
        envelope = json.loads(plan.tasks_json)
        assert envelope.get("execution_tasks_created") is not True
        assert envelope.get("operational_tasks") in (None, [])

    db_fixture.run(_assert_no_ops())
