"""Finalization Wave 4 — read-only capability + eligibility (compose F7C + DEC-015).

Zero mutation. Operational tasks source only. No assignment/sessions/scheduling.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.employee_eligibility_read_model_service import (
    build_employee_eligibility_read_model,
)
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.operational_resource_readiness_service import (
    build_operational_resource_readiness,
)
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_WAVE4_OID = lambda n: 880640 + n


def test_wave4_services_have_no_forbidden_imports():
    paths = (
        BACKEND_ROOT / "services" / "operational_resource_readiness_service.py",
        BACKEND_ROOT / "services" / "employee_eligibility_read_model_service.py",
    )
    forbidden = (
        "quote_orchestrator",
        "cost_engine_service",
        "controlled_employee_assignment",
        "controlled_task_session",
    )
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
        joined = " ".join(sorted(imported))
        for part in forbidden:
            assert part not in joined, f"{path.name} imports {part}"


@pytest.mark.asyncio
async def test_wave4_resource_and_eligibility_read_only_zero_mutation(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE4_OID(1))
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)

    plan_before = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order.id)
        )
    ).scalar_one()
    tasks_json_before = plan_before.tasks_json
    updated_before = getattr(plan_before, "updated_at", None)
    reality_before = await db_session.scalar(
        select(func.count()).select_from(ExecutionReality)
    )

    resources = await build_operational_resource_readiness(db_session, order.id)
    eligibility = await build_employee_eligibility_read_model(db_session, order.id)

    assert resources.status == "ok"
    assert resources.side_effects == "none"
    assert resources.wave4_boundary.assignable is False
    assert resources.wave4_boundary.schedulable is False
    assert resources.operational_task_count >= 1
    for task in resources.tasks:
        for cand in task.compatible_machine_candidates:
            assert cand.assignment_status == "unassigned"
            assert cand.reservation_status == "not_reserved"
            assert cand.match_provenance

    assert eligibility["status"] == "ok"
    assert eligibility["side_effects"] == "none"
    assert eligibility["wave4_boundary"]["assignable"] is False
    assert eligibility["wave4_boundary"]["schedulable"] is False
    assert eligibility["operational_task_count"] == resources.operational_task_count
    for task in eligibility["tasks"]:
        for emp in task.get("eligible_employees") or []:
            assert emp.get("availability_status") == "not_evaluated"
            assert "match_provenance" in emp

    await db_session.refresh(plan_before)
    assert plan_before.tasks_json == tasks_json_before
    if updated_before is not None:
        assert getattr(plan_before, "updated_at", None) == updated_before
    reality_after = await db_session.scalar(
        select(func.count()).select_from(ExecutionReality)
    )
    assert reality_after == reality_before
    envelope = json.loads(plan_before.tasks_json)
    assert envelope.get("execution_tasks_created") is True
    assert len(envelope.get("operational_tasks") or []) == resources.operational_task_count
    _ = persist


@pytest.mark.asyncio
async def test_wave4_no_planned_tasks_fallback(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE4_OID(2))
    await create_execution_plan_v2_from_order(db_session, order.id)
    # Intentionally do NOT materialize.
    resources = await build_operational_resource_readiness(db_session, order.id)
    eligibility = await build_employee_eligibility_read_model(db_session, order.id)
    assert resources.status == "blocked_not_materialized"
    assert resources.operational_task_count == 0
    assert eligibility["status"] == "blocked_not_materialized"
    assert eligibility["operational_task_count"] == 0


@pytest.mark.asyncio
async def test_wave4_repeated_get_stable(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE4_OID(3))
    await create_execution_plan_v2_from_order(db_session, order.id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)

    first = await build_operational_resource_readiness(db_session, order.id)
    second = await build_operational_resource_readiness(db_session, order.id)
    assert first.model_dump() == second.model_dump()

    e1 = await build_employee_eligibility_read_model(db_session, order.id)
    e2 = await build_employee_eligibility_read_model(db_session, order.id)
    assert e1 == e2
