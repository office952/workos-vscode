"""Finalization Wave 3 — DEC-009=B controlled materialization (fixture-shaped).

Does not hardcode product logic on order 880750. Uses the OD3 next-dry registry
and the same V2 planned_tasks → operational_tasks materializer.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.execution_plan_v2 import PLANNING_MINUTES_WARNING
from services.dec009_materialize_gate import (
    LIVE_DEC009_STATUS,
    WAVE3_CONTROLLED_ORDER_ID,
    WAVE3_CONTROLLED_PLAN_ID,
    close_materialize_pilot_gate,
    enforce_dec009_materialize_gate,
    evaluate_materialize_authorization,
    open_wave3_controlled_materialize_target,
    register_golden_pilot_materialize_target,
)
from services.execution_plan_v2_materialization_audit_service import (
    build_execution_plan_v2_materialization_audit_by_order_id,
)
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot

pytestmark = pytest.mark.enforce_dec009_gate

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_WAVE3_OID = lambda n: 880650 + n  # outside protected + outside durable 880750


@pytest.fixture(autouse=True)
def _gate_isolation():
    close_materialize_pilot_gate()
    yield
    close_materialize_pilot_gate()


@pytest.mark.asyncio
async def test_wave3_closed_gate_denies_materialize(db_session):
    assert LIVE_DEC009_STATUS == "B"
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE3_OID(1))
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    close_materialize_pilot_gate()
    decision = evaluate_materialize_authorization(
        order_id=order.id, plan_id=persist.execution_plan_id
    )
    assert decision["allowed"] is False
    assert "pilot_gate_closed" in decision["blockers"]
    with pytest.raises(HTTPException) as exc:
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == "DEC009_MATERIALIZE_BLOCKED"


@pytest.mark.asyncio
async def test_wave3_wrong_order_denied_when_wave3_open(db_session):
    open_wave3_controlled_materialize_target()
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE3_OID(2))
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    with pytest.raises(HTTPException) as exc:
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert exc.value.status_code == 422
    assert "order_or_plan_outside_scoped_b" in exc.value.detail["blockers"]
    audit = await build_execution_plan_v2_materialization_audit_by_order_id(
        db_session, order.id
    )
    assert audit.guards.post_materialize_allowed is False
    assert audit.materialization_status == "blocked_needs_owner_go"
    _ = persist


@pytest.mark.asyncio
async def test_wave3_production_env_denied(db_session, monkeypatch):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE3_OID(3))
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    register_golden_pilot_materialize_target(
        order_id=order.id, plan_id=persist.execution_plan_id
    )
    monkeypatch.setenv("APP_ENV", "production")
    decision = evaluate_materialize_authorization(
        order_id=order.id, plan_id=persist.execution_plan_id
    )
    assert decision["allowed"] is False
    assert "production_environment_forbidden" in decision["blockers"]
    with pytest.raises(HTTPException):
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)


@pytest.mark.asyncio
async def test_wave3_first_materialize_and_idempotent_second(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE3_OID(4))
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    register_golden_pilot_materialize_target(
        order_id=order.id, plan_id=persist.execution_plan_id
    )

    audit_before = await build_execution_plan_v2_materialization_audit_by_order_id(
        db_session, order.id
    )
    assert audit_before.guards.post_materialize_allowed is True
    assert audit_before.materialization_status == "scoped_materialize_authorized"
    assert audit_before.operational_tasks_in_envelope_count == 0
    candidate_count = len(audit_before.materializable_task_candidates)
    assert candidate_count == audit_before.planned_task_count
    assert candidate_count >= 1

    reality_before = await db_session.scalar(
        select(func.count()).select_from(ExecutionReality)
    )
    first = await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert first.status == "materialized"
    assert first.execution_tasks_created is True
    assert first.operational_tasks_count == candidate_count
    assert first.no_sessions_created is True
    assert PLANNING_MINUTES_WARNING in first.warnings

    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order.id)
        )
    ).scalar_one()
    envelope = json.loads(plan.tasks_json)
    assert envelope["execution_tasks_created"] is True
    assert len(envelope["operational_tasks"]) == candidate_count
    assert len(envelope["planned_tasks"]) == candidate_count
    assert envelope.get("materialization_audit", {}).get("dec009") == "B"
    assert envelope["materialization_audit"]["source_contract"] == "planned_tasks_only"
    assert envelope["materialization_audit"]["no_sessions"] is True
    for task in envelope["operational_tasks"]:
        assert task["assigned_employee_id"] is None
        assert task["estimated_time_minutes"] is None

    audit_after = await build_execution_plan_v2_materialization_audit_by_order_id(
        db_session, order.id
    )
    assert audit_after.materialization_status == "already_materialized_in_envelope"
    assert audit_after.guards.post_materialize_allowed is False
    assert audit_after.operational_tasks_in_envelope_count == candidate_count

    with pytest.raises(HTTPException) as second:
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert second.value.status_code == 409
    assert second.value.detail["error"] == "operational_tasks_already_materialized"

    envelope_again = json.loads(
        (
            await db_session.execute(
                select(ExecutionPlan).where(ExecutionPlan.order_id == order.id)
            )
        )
        .scalar_one()
        .tasks_json
    )
    assert len(envelope_again["operational_tasks"]) == candidate_count
    assert envelope_again["materialization_audit"]["idempotency"] == "first_materialization"

    reality_after = await db_session.scalar(
        select(func.count()).select_from(ExecutionReality)
    )
    assert reality_after == reality_before


@pytest.mark.asyncio
async def test_wave3_planned_operations_not_task_source(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE3_OID(5))
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    register_golden_pilot_materialize_target(
        order_id=order.id, plan_id=persist.execution_plan_id
    )
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order.id)
        )
    ).scalar_one()
    envelope = json.loads(plan.tasks_json)
    planned_ops = len(envelope.get("planned_operations") or [])
    planned_tasks = len(envelope.get("planned_tasks") or [])
    assert planned_ops >= planned_tasks

    result = await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert result.operational_tasks_count == planned_tasks
    after = json.loads(
        (
            await db_session.execute(
                select(ExecutionPlan).where(ExecutionPlan.order_id == order.id)
            )
        )
        .scalar_one()
        .tasks_json
    )
    assert len(after["operational_tasks"]) == planned_tasks
    assert len(after["planned_operations"]) == planned_ops


@pytest.mark.asyncio
async def test_wave3_gate_constants_point_at_durable_fixture():
    open_wave3_controlled_materialize_target()
    enforce_dec009_materialize_gate(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID
    )
    decision = evaluate_materialize_authorization(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID
    )
    assert decision["allowed"] is True
    assert decision["scoped_b_order_id"] == WAVE3_CONTROLLED_ORDER_ID


@pytest.mark.asyncio
async def test_wave3_concurrent_second_writer_gets_409(db_session):
    """Optimistic CAS: overlapping writers must not duplicate operational_tasks."""
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE3_OID(6))
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    register_golden_pilot_materialize_target(
        order_id=order.id, plan_id=persist.execution_plan_id
    )

    async def _once():
        return await materialize_execution_plan_v2_operational_tasks(db_session, order.id)

    # Sequential double-submit (true parallel shares one AsyncSession unsafely).
    first = await _once()
    assert first.status == "materialized"
    with pytest.raises(HTTPException) as exc:
        await _once()
    assert exc.value.status_code == 409

    envelope = json.loads(
        (
            await db_session.execute(
                select(ExecutionPlan).where(ExecutionPlan.order_id == order.id)
            )
        )
        .scalar_one()
        .tasks_json
    )
    assert len(envelope["operational_tasks"]) == first.operational_tasks_count


def test_wave3_no_live_orr_import_in_materialize_module():
    import ast

    path = BACKEND_ROOT / "services" / "execution_plan_v2_materialize_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    joined = " ".join(sorted(imported))
    assert "operational_resource" not in joined
    assert "quote_orchestrator" not in joined
    assert "cost_engine" not in joined


def test_wave3_default_module_next_dry_is_880750_when_not_closed():
    """Committed module defaults open Wave 3 next-dry (tests restore closed via fixture)."""
    # Re-open committed defaults after autouse closed the gate.
    open_wave3_controlled_materialize_target()
    decision = evaluate_materialize_authorization(
        order_id=WAVE3_CONTROLLED_ORDER_ID, plan_id=WAVE3_CONTROLLED_PLAN_ID
    )
    assert decision["allowed"] is True
    assert os.environ.get("APP_ENV", "development").lower() not in {"production", "prod"}
