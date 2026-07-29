"""Capacity Batch 15 — read-model / regression guards.

Scope:
- Unauthorized POST materialize remains OD3-blocked (422) — no new ops.
- Already-materialized envelopes stay coherent on GET plan + audit.
- Duplicate materialize under OD3 does not inflate ops count.
- Sessions / ExecutionActuals remain untouched by read paths.

No invent of FIX-DEC009 live DB fixtures in unit tests — synthetic seeds only.
Live fixture ops=12 is proven separately via GET probes (see Track A / guard report).
"""

from __future__ import annotations

import json

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.dec009_materialize_gate import (
    BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
    ERROR_DEC009_MATERIALIZE_BLOCKED,
    LIVE_DEC009_STATUS,
    SCOPED_B_FIXTURE_ID,
    SCOPED_B_ORDER_ID,
    SCOPED_B_PLAN_ID,
    enforce_dec009_materialize_gate,
)
from services.execution_plan_task_parser import parse_tasks_json_raw
from services.execution_plan_v2_materialization_audit_service import (
    build_execution_plan_v2_materialization_audit_by_order_id,
)
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot

_REGRESSION_OID = 29750


def _assert_graph_coherent(envelope: dict) -> None:
    planned = [t for t in (envelope.get("planned_tasks") or []) if isinstance(t, dict)]
    ops = [t for t in (envelope.get("operational_tasks") or []) if isinstance(t, dict)]
    assert len(ops) >= 1
    planned_keys = {str(t.get("task_key")) for t in planned if t.get("task_key")}
    ops_keys = {
        str(t.get("source_task_key") or t.get("task_id"))
        for t in ops
        if (t.get("source_task_key") or t.get("task_id"))
    }
    assert planned_keys == ops_keys
    assert len(ops_keys) == len(ops)

    for task in ops:
        assert task.get("order_id") is not None or task.get("execution_plan_id") is not None
        deps = task.get("depends_on_task_ids") or []
        for dep in deps:
            assert str(dep) in ops_keys

    for task in planned:
        deps = task.get("depends_on_task_keys") or []
        for dep in deps:
            assert str(dep) in planned_keys


async def _count_reality(db_session) -> int:
    return int(await db_session.scalar(select(func.count()).select_from(ExecutionReality)) or 0)


async def _load_plan(db_session, order_id: int) -> ExecutionPlan:
    return (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one()


def test_batch_15_scoped_b_and_authorize_defaults_unchanged():
    """Regression: Batch 15 must not unlock execute or widen scoped B."""
    assert LIVE_DEC009_STATUS == "A"
    assert BATCH_EXECUTE_MATERIALIZE_AUTHORIZED is False
    assert SCOPED_B_ORDER_ID == 973010
    assert SCOPED_B_PLAN_ID == 12
    assert SCOPED_B_FIXTURE_ID == "FIX-DEC009-MAT-01"


@pytest.mark.enforce_dec009_gate
def test_batch_15_unauthorized_materialize_still_hard_rejects():
    with pytest.raises(HTTPException) as exc:
        enforce_dec009_materialize_gate(
            order_id=SCOPED_B_ORDER_ID,
            plan_id=SCOPED_B_PLAN_ID,
        )
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED
    assert exc.value.detail["batch_execute_materialize_authorized"] is False


@pytest.mark.asyncio
async def test_batch_15_read_model_coherent_after_materialize(db_session):
    """Materialize under unit-test bypass → GET audit/plan read model coherent."""
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_REGRESSION_OID)
    await create_execution_plan_v2_from_order(db_session, order.id)
    reality_before = await _count_reality(db_session)

    result = await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert result.status == "materialized"
    assert result.no_sessions_created is True
    assert result.operational_tasks_count >= 1

    plan = await _load_plan(db_session, order.id)
    envelope = json.loads(plan.tasks_json)
    _assert_graph_coherent(envelope)
    ops_count = len(envelope["operational_tasks"])
    assert ops_count == result.operational_tasks_count

    audit = await build_execution_plan_v2_materialization_audit_by_order_id(db_session, order.id)
    assert audit.mode == "audit_only"
    assert audit.materialization_status == "already_materialized_in_envelope"
    assert audit.dry_run_status == "already_materialized"
    assert audit.operational_tasks_in_envelope_count == ops_count
    assert audit.guards.writes_database is False
    assert audit.guards.creates_sessions is False
    assert audit.guards.post_materialize_allowed is False
    assert audit.guards.employee_mobile_scope is False

    parsed = parse_tasks_json_raw(plan.tasks_json)
    assert len(parsed.operational_tasks) == ops_count
    assert await _count_reality(db_session) == reality_before


@pytest.mark.enforce_dec009_gate
def test_batch_15_unauthorized_post_does_not_duplicate_ops(
    db_fixture, db_session, auth_client, monkeypatch
):
    """Ops already present: OD3 still 422; envelope cardinality unchanged."""
    order_id = _REGRESSION_OID + 1
    state: dict = {}

    async def _setup():
        # Temporarily bypass OD3 only to seed an already-materialized envelope.
        monkeypatch.setattr("services.dec009_materialize_gate._UNIT_TEST_BYPASS", True)
        order = await _seed_v2_order_with_snapshot(db_session, order_id=order_id)
        await create_execution_plan_v2_from_order(db_session, order.id)
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
        monkeypatch.setattr("services.dec009_materialize_gate._UNIT_TEST_BYPASS", False)
        plan = await _load_plan(db_session, order_id)
        env = json.loads(plan.tasks_json)
        state["ops_before"] = len(env.get("operational_tasks") or [])
        state["hash_before"] = env.get("activation_hash")
        assert state["ops_before"] >= 1

    db_fixture.run(_setup())

    resp = auth_client.post(f"/api/v1/execution/plan-v2/materialize-tasks/{order_id}")
    assert resp.status_code == 422, resp.text
    detail = resp.json().get("detail") or resp.json()
    assert detail["error"] == ERROR_DEC009_MATERIALIZE_BLOCKED
    assert "batch_execute_materialize_not_authorized" in detail["blockers"]

    async def _assert_stable():
        plan = await _load_plan(db_session, order_id)
        env = json.loads(plan.tasks_json)
        assert len(env.get("operational_tasks") or []) == state["ops_before"]
        assert env.get("activation_hash") == state["hash_before"]
        _assert_graph_coherent(env)

    db_fixture.run(_assert_stable())
