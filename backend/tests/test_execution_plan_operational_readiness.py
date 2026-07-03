"""Step 9.3.4.c — execution plan operational readiness evaluation."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.execution_plan_operational_readiness_service import (
    BLOCKER_EXECUTION_PLAN_MISSING,
    BLOCKER_EXECUTION_PLAN_TASKS_JSON_INVALID,
    BLOCKER_OPERATIONAL_TASK_DEPENDENCY_MISSING,
    BLOCKER_OPERATIONAL_TASKS_EMPTY_AFTER_MATERIALIZATION,
    BLOCKER_OPERATIONAL_TASKS_NOT_MATERIALIZED,
    NEXT_ACTION_GENERATE_EXECUTION_PLAN,
    NEXT_ACTION_MATERIALIZE_V2_OPERATIONAL_TASKS,
    STATUS_BLOCKED_TASK_GRAPH,
    STATUS_INVALID_TASKS_JSON,
    STATUS_LEGACY_OPERATIONAL_READY,
    STATUS_NO_EXECUTION_PLAN,
    STATUS_UNKNOWN_FORMAT,
    STATUS_V2_NOT_MATERIALIZED,
    STATUS_V2_OPERATIONAL_EMPTY,
    STATUS_V2_OPERATIONAL_READY,
    evaluate_execution_plan_operational_readiness,
)
from services.execution_plan_task_parser import parse_tasks_json_raw

BACKEND_ROOT = Path(__file__).resolve().parents[1]
STEP_PATHS = (
    BACKEND_ROOT / "services" / "execution_plan_operational_readiness_service.py",
    BACKEND_ROOT / "routers" / "execution.py",
    Path(__file__).resolve(),
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
    "/price",
)

EMPLOYEE_MOBILE_PATH_FRAGMENTS = (
    "employee_mobile_tasks_service",
    "dev_employee_mobile_sandu_fixture_service",
    "routers/employee_mobile",
)


def _plan(*, order_id: int = 501, tasks_json: str) -> ExecutionPlan:
    return ExecutionPlan(
        id=9001,
        order_id=order_id,
        order_code=f"ORD-{order_id}",
        snapshot_version=1,
        tasks_json=tasks_json,
        total_estimated_time_minutes=10.0,
    )


def _legacy_tasks(task_id: str = "T-LEGACY") -> str:
    return json.dumps(
        [
            {
                "task_id": task_id,
                "name": "Legacy task",
                "process_type": "print",
            }
        ]
    )


def _v2_envelope(
    *,
    operational: list | None = None,
    execution_tasks_created: bool = False,
) -> str:
    envelope: dict = {
        "source": "order_snapshot_v2",
        "planned_tasks": [
            {
                "task_key": "cnc_face_cut",
                "label": "CNC Face Cut",
                "canonical_task_type": "cnc_routing",
            }
        ],
        "execution_tasks_created": execution_tasks_created,
    }
    if operational is not None:
        envelope["operational_tasks"] = operational
    return json.dumps(envelope)


async def _count_execution_reality(db_session) -> int:
    return int(await db_session.scalar(select(func.count()).select_from(ExecutionReality)) or 0)


# ---------------------------------------------------------------------------
# Mandatory readiness contract tests (1–9)
# ---------------------------------------------------------------------------


def test_no_execution_plan_returns_no_execution_plan_status():
    result = evaluate_execution_plan_operational_readiness(None)
    assert result.status == STATUS_NO_EXECUTION_PLAN
    assert BLOCKER_EXECUTION_PLAN_MISSING in result.blockers
    assert result.next_action == NEXT_ACTION_GENERATE_EXECUTION_PLAN


def test_invalid_tasks_json_returns_invalid_tasks_json():
    result = evaluate_execution_plan_operational_readiness(_plan(tasks_json="{not-json"))
    assert result.status == STATUS_INVALID_TASKS_JSON
    assert BLOCKER_EXECUTION_PLAN_TASKS_JSON_INVALID in result.blockers


def test_legacy_v1_list_returns_legacy_operational_ready():
    result = evaluate_execution_plan_operational_readiness(_plan(tasks_json=_legacy_tasks()))
    assert result.status == STATUS_LEGACY_OPERATIONAL_READY
    assert result.operational_tasks_materialized is True
    assert result.operational_tasks_count == 1


def test_v2_envelope_without_operational_tasks_returns_v2_not_materialized():
    result = evaluate_execution_plan_operational_readiness(_plan(tasks_json=_v2_envelope()))
    assert result.status == STATUS_V2_NOT_MATERIALIZED
    assert BLOCKER_OPERATIONAL_TASKS_NOT_MATERIALIZED in result.blockers
    assert result.operational_tasks_count == 0


def test_v2_envelope_with_operational_tasks_returns_v2_operational_ready():
    operational = [
        {
            "task_id": "cnc_face_cut",
            "process_type": "cnc_routing",
            "depends_on_task_ids": [],
        }
    ]
    result = evaluate_execution_plan_operational_readiness(
        _plan(tasks_json=_v2_envelope(operational=operational, execution_tasks_created=True))
    )
    assert result.status == STATUS_V2_OPERATIONAL_READY
    assert result.operational_tasks_materialized is True
    assert result.operational_tasks_count == 1


def test_v2_execution_tasks_created_true_but_empty_operational_tasks():
    result = evaluate_execution_plan_operational_readiness(
        _plan(tasks_json=_v2_envelope(operational=[], execution_tasks_created=True))
    )
    assert result.status == STATUS_V2_OPERATIONAL_EMPTY
    assert BLOCKER_OPERATIONAL_TASKS_EMPTY_AFTER_MATERIALIZATION in result.blockers


def test_missing_dependency_returns_blocked_task_graph():
    operational = [
        {
            "task_id": "child",
            "process_type": "cnc_routing",
            "depends_on_task_ids": ["missing_parent"],
        }
    ]
    result = evaluate_execution_plan_operational_readiness(
        _plan(tasks_json=_v2_envelope(operational=operational, execution_tasks_created=True))
    )
    assert result.status == STATUS_BLOCKED_TASK_GRAPH
    assert BLOCKER_OPERATIONAL_TASK_DEPENDENCY_MISSING in result.blockers


def test_not_materialized_includes_next_action_materialize():
    result = evaluate_execution_plan_operational_readiness(_plan(tasks_json=_v2_envelope()))
    assert result.next_action == NEXT_ACTION_MATERIALIZE_V2_OPERATIONAL_TASKS


def test_readiness_does_not_use_planned_tasks_as_operational():
    raw = _v2_envelope()
    parsed = parse_tasks_json_raw(raw)
    assert parsed.operational_tasks == []
    assert len(parsed.planned_tasks) == 1

    result = evaluate_execution_plan_operational_readiness(_plan(tasks_json=raw))
    assert result.operational_tasks_count == 0
    assert result.status == STATUS_V2_NOT_MATERIALIZED


# ---------------------------------------------------------------------------
# Guardrails (10–13)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_readiness_evaluation_does_not_write_db(db_session):
    order_id = 39801
    plan = ExecutionPlan(
        order_id=order_id,
        order_code=f"ORD-{order_id}",
        snapshot_version=1,
        tasks_json=_v2_envelope(),
        total_estimated_time_minutes=10.0,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    before_json = plan.tasks_json
    evaluate_execution_plan_operational_readiness(plan)
    await db_session.refresh(plan)
    assert plan.tasks_json == before_json


@pytest.mark.asyncio
async def test_no_execution_reality_rows_created(db_session):
    before = await _count_execution_reality(db_session)
    evaluate_execution_plan_operational_readiness(_plan(tasks_json=_legacy_tasks()))
    after = await _count_execution_reality(db_session)
    assert after == before


def test_step_does_not_modify_employee_mobile_files():
    for fragment in EMPLOYEE_MOBILE_PATH_FRAGMENTS:
        for path in STEP_PATHS:
            assert fragment not in str(path).lower()


def test_no_forbidden_pricing_imports():
    found: set[str] = set()
    for path in STEP_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                    if part in node.module:
                        found.add(f"{path.name}:{node.module}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                        if part in alias.name:
                            found.add(f"{path.name}:{alias.name}")
    assert not found, f"Forbidden imports: {found}"


# ---------------------------------------------------------------------------
# Additional contract coverage
# ---------------------------------------------------------------------------


def test_unrecognized_shape_returns_unknown_format():
    result = evaluate_execution_plan_operational_readiness(
        _plan(tasks_json=json.dumps({"source": "other", "tasks": []}))
    )
    assert result.status == STATUS_UNKNOWN_FORMAT


def test_router_plan_dict_exposes_readiness_fields(db_fixture, db_session, auth_client):
    order_id = 39802

    async def _setup():
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-{order_id}",
                snapshot_version=1,
                tasks_json=_v2_envelope(),
                total_estimated_time_minutes=10.0,
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())
    resp = auth_client.get(f"/api/v1/execution/plan/{order_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["operational_readiness_status"] == STATUS_V2_NOT_MATERIALIZED
    assert body["operational_tasks_count"] == 0
    assert BLOCKER_OPERATIONAL_TASKS_NOT_MATERIALIZED in body["operational_readiness_blockers"]
    assert body["operational_readiness_next_action"] == NEXT_ACTION_MATERIALIZE_V2_OPERATIONAL_TASKS
    assert body["operational_tasks_materialized"] is False
