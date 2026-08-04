"""Finalization Wave 5 — assignment readiness audit (read-only, zero mutation)."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.assignment_readiness_audit_service import (
    OWNER_GO_BLOCKER,
    build_assignment_readiness_audit,
    evaluate_candidate_for_future_assignment,
)
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_WAVE5_OID = lambda n: 880620 + n


def test_wave5_audit_service_has_no_forbidden_imports():
    path = BACKEND_ROOT / "services" / "assignment_readiness_audit_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    joined = " ".join(sorted(imported))
    for part in (
        "controlled_employee_assignment",
        "execution_task_assignment_service",
        "quote_orchestrator",
        "cost_engine_service",
    ):
        assert part not in joined, f"audit service must not import {part}"


def test_wave5_pure_candidate_eval_not_eligible():
    result = evaluate_candidate_for_future_assignment(
        eligibility_task={
            "eligibility_status": "ready_with_warnings",
            "eligible_employees": [{"employee_id": 7}],
            "blockers": [],
        },
        plan_task={"task_id": "t1", "assigned_employee_id": None},
        candidate_employee_id=999,
        employee=SimpleNamespace(id=999, status="active", end_date=None),
        active_session=False,
    )
    assert result["evaluation_status"] == "NOT_ELIGIBLE"
    assert result["assignment_authorized"] is False
    assert result["authorization_blocker"] == OWNER_GO_BLOCKER


def test_wave5_pure_candidate_eval_valid_still_not_authorized():
    emp = SimpleNamespace(id=7, status="active", end_date=None)
    result = evaluate_candidate_for_future_assignment(
        eligibility_task={
            "eligibility_status": "ready",
            "eligible_employees": [{"employee_id": 7}],
            "blockers": [],
        },
        plan_task={"task_id": "t1"},
        candidate_employee_id=7,
        employee=emp,
        active_session=False,
    )
    assert result["evaluation_status"] == "VALID_CANDIDATE_FOR_FUTURE_ASSIGNMENT"
    assert result["assignment_authorized"] is False
    assert result["semantics"]["PERSISTED_ASSIGNMENT"] is False
    assert result["semantics"]["AUTHORIZED_TO_START"] is False


def test_wave5_pure_candidate_eval_already_assigned():
    emp = SimpleNamespace(id=7, status="active", end_date=None)
    result = evaluate_candidate_for_future_assignment(
        eligibility_task={
            "eligibility_status": "ready",
            "eligible_employees": [{"employee_id": 7}],
            "blockers": [],
        },
        plan_task={"task_id": "t1", "assigned_employee_id": 3},
        candidate_employee_id=7,
        employee=emp,
        active_session=False,
    )
    assert result["evaluation_status"] == "TASK_ALREADY_ASSIGNED"
    assert result["assignment_authorized"] is False


def test_wave5_frontend_eligible_override_cannot_exist_in_pure_eval():
    """Pure eval ignores any forged eligible flag — only eligibility list + status."""
    emp = SimpleNamespace(id=9, status="active", end_date=None)
    result = evaluate_candidate_for_future_assignment(
        eligibility_task={
            "eligibility_status": "ready",
            "eligible_employees": [{"employee_id": 7}],
            "eligible": True,  # forged / ignored
            "blockers": [],
        },
        plan_task={"task_id": "t1"},
        candidate_employee_id=9,
        employee=emp,
        active_session=False,
    )
    assert result["evaluation_status"] == "NOT_ELIGIBLE"


@pytest.mark.asyncio
async def test_wave5_audit_read_only_zero_mutation(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE5_OID(1))
    await create_execution_plan_v2_from_order(db_session, order.id)
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

    audit = await build_assignment_readiness_audit(db_session, order.id)
    assert audit["status"] == "ok"
    assert audit["side_effects"] == "none"
    assert audit["wave5_boundary"]["assignment_authorized"] is False
    assert audit["wave5_boundary"]["authorization_blocker"] == OWNER_GO_BLOCKER
    assert audit["employee_assignment_count"] == 0
    assert audit["machine_assignment_count"] == 0
    assert audit["scheduling"] == "HOLD"
    assert audit["operational_task_count"] >= 1
    assert "assign_operational_task_controlled" in audit["command_contract"]["persist_service"] or (
        "BLOCKED_LEGACY" in audit["command_contract"]["persist_service"]
    )
    assert (
        audit["command_contract"]["idempotency"]["status"]
        == "IDEMPOTENCY_VERIFIED_FOR_EMBEDDED_MODEL"
    )
    assert (
        audit["command_contract"]["transactionality"]["status"]
        == "TRANSACTIONALITY_VERIFIED_WITHIN_DOCUMENTED_BOUNDARY"
    )
    for task in audit["tasks"]:
        assert task["current_assignment"]["status"] == "unassigned"
        assert task["future_assign_preconditions"]["assignment_authorized"] is False
        assert task["machine_capability_ref"]["semantics"]["ASSIGNED_MACHINE"] is False
        assert task["estimated_minutes"] is None

    # Hypothetical without mutating even when candidate missing.
    hyp = await build_assignment_readiness_audit(
        db_session,
        order.id,
        candidate_employee_id=999999,
        task_key=audit["tasks"][0]["task_key"],
    )
    assert hyp["hypothetical_candidate_evaluation"]["assignment_authorized"] is False
    assert hyp["hypothetical_candidate_evaluation"]["evaluation_status"] in {
        "CANDIDATE_NOT_FOUND",
        "NOT_ELIGIBLE",
        "CANDIDATE_INACTIVE",
        "ELIGIBILITY_UNKNOWN",
        "ELIGIBILITY_REQUIREMENTS_NOT_CONFIGURED",
        "VALID_CANDIDATE_FOR_FUTURE_ASSIGNMENT",
        "TASK_ALREADY_ASSIGNED",
        "COMMAND_NOT_AUTHORIZED",
    }

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
    for task in envelope.get("operational_tasks") or []:
        if isinstance(task, dict):
            assert task.get("assigned_employee_id") in (None, "")


@pytest.mark.asyncio
async def test_wave5_no_planned_tasks_fallback(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE5_OID(2))
    await create_execution_plan_v2_from_order(db_session, order.id)
    audit = await build_assignment_readiness_audit(db_session, order.id)
    assert audit["status"] == "blocked_not_materialized"
    assert audit["operational_task_count"] == 0
    assert audit["wave5_boundary"]["assignment_authorized"] is False


@pytest.mark.asyncio
async def test_wave5_repeated_get_stable(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_WAVE5_OID(3))
    await create_execution_plan_v2_from_order(db_session, order.id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    a = await build_assignment_readiness_audit(db_session, order.id)
    b = await build_assignment_readiness_audit(db_session, order.id)
    assert a == b
