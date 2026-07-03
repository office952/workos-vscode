"""Step 9.3.4.b — shared execution plan parser adoption by backend operational consumers."""

from __future__ import annotations

import ast
import json
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.employees import Employees
from services.divergence_service import DivergenceService
from services.execution_plan_task_parser import (
    load_operational_tasks_from_plan_json,
    operational_tasks_only,
    parse_tasks_json_raw,
)
from services.execution_task_assignment_service import (
    ExecutionTaskAssignmentError,
    assign_plan_task,
)
from services.order_production_blueprint_service import get_order_production_blueprint
from services.task_start_gate_service import evaluate_task_start_readiness

BACKEND_ROOT = Path(__file__).resolve().parents[1]

CONSUMER_SERVICE_PATHS = (
    BACKEND_ROOT / "services" / "execution_task_assignment_service.py",
    BACKEND_ROOT / "services" / "execution_task_instructions_service.py",
    BACKEND_ROOT / "services" / "task_start_gate_service.py",
    BACKEND_ROOT / "services" / "order_production_blueprint_service.py",
    BACKEND_ROOT / "services" / "divergence_service.py",
    BACKEND_ROOT / "services" / "material_procurement_status_service.py",
    BACKEND_ROOT / "routers" / "execution.py",
    BACKEND_ROOT / "routers" / "operator_tasks.py",
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


def _legacy_tasks(task_id: str = "T-LEGACY") -> str:
    return json.dumps(
        [
            {
                "task_id": task_id,
                "name": "Legacy task",
                "process_type": "print",
                "machine_type": "PRINTER",
                "estimated_time_minutes": 15,
            }
        ]
    )


def _v2_envelope(*, operational: list | None = None, execution_tasks_created: bool = False) -> str:
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


async def _seed_plan(db_session, *, order_id: int, tasks_json: str) -> ExecutionPlan:
    row = ExecutionPlan(
        order_id=order_id,
        order_code=f"ORD-{order_id}",
        snapshot_version=1,
        tasks_json=tasks_json,
        total_estimated_time_minutes=15,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _seed_employee(db_session) -> Employees:
    emp = Employees(name="Parser Worker", status="active", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _count_execution_reality(db_session) -> int:
    return int(await db_session.scalar(select(func.count()).select_from(ExecutionReality)) or 0)


# ---------------------------------------------------------------------------
# Parser behavior (consumer contract)
# ---------------------------------------------------------------------------


def test_legacy_v1_list_works_through_shared_parser():
    tasks, parsed = load_operational_tasks_from_plan_json(_legacy_tasks())
    assert parsed.format == "legacy_list"
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "T-LEGACY"


def test_v2_envelope_with_operational_tasks_works_through_shared_parser():
    operational = [
        {
            "task_id": "cnc_face_cut",
            "process_type": "cnc_routing",
            "estimated_time_minutes": 20,
        }
    ]
    tasks, parsed = load_operational_tasks_from_plan_json(
        _v2_envelope(operational=operational, execution_tasks_created=True)
    )
    assert parsed.format == "v2_envelope"
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "cnc_face_cut"


def test_v2_envelope_without_operational_tasks_returns_empty():
    parsed = parse_tasks_json_raw(_v2_envelope())
    assert parsed.format == "v2_envelope"
    assert parsed.operational_tasks == []
    assert len(parsed.planned_tasks) == 1


def test_parser_does_not_fallback_to_planned_tasks_as_operational():
    parsed = parse_tasks_json_raw(_v2_envelope())
    assert parsed.operational_tasks == []
    assert operational_tasks_only(_v2_envelope()) == []
    assert len(parsed.planned_tasks) == 1


def test_invalid_json_handled_safely_by_parser():
    parsed = parse_tasks_json_raw("{not-json")
    assert parsed.format == "invalid"
    assert parsed.operational_tasks == []
    assert parsed.parse_errors


# ---------------------------------------------------------------------------
# Consumer integration (assignment / gates / blueprint / divergence)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assignment_legacy_v1_preserves_list_shape(db_session):
    order_id = 39701
    emp = await _seed_employee(db_session)
    await _seed_plan(db_session, order_id=order_id, tasks_json=_legacy_tasks("T-ASSIGN-V1"))

    before = await _count_execution_reality(db_session)
    result = await assign_plan_task(
        db_session,
        order_id=order_id,
        task_id="T-ASSIGN-V1",
        assigned_employee_id=emp.id,
    )
    after = await _count_execution_reality(db_session)

    assert result["assigned_employee_id"] == emp.id
    assert after == before

    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one()
    loaded = json.loads(plan.tasks_json)
    assert isinstance(loaded, list)
    assert loaded[0]["assigned_employee_id"] == emp.id


@pytest.mark.asyncio
async def test_assignment_v2_materialized_preserves_envelope_shape(db_session):
    order_id = 39702
    emp = await _seed_employee(db_session)
    operational = [
        {
            "task_id": "cnc_face_cut",
            "process_type": "cnc_routing",
            "estimated_time_minutes": 20,
        }
    ]
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(operational=operational, execution_tasks_created=True),
    )

    await assign_plan_task(
        db_session,
        order_id=order_id,
        task_id="cnc_face_cut",
        assigned_employee_id=emp.id,
    )

    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one()
    envelope = json.loads(plan.tasks_json)
    assert envelope.get("source") == "order_snapshot_v2"
    assert isinstance(envelope.get("operational_tasks"), list)
    assert envelope["operational_tasks"][0]["assigned_employee_id"] == emp.id
    assert "planned_tasks" in envelope


@pytest.mark.asyncio
async def test_assignment_v2_not_materialized_has_no_operational_tasks(db_session):
    order_id = 39703
    emp = await _seed_employee(db_session)
    await _seed_plan(db_session, order_id=order_id, tasks_json=_v2_envelope())

    with pytest.raises(HTTPException) as exc:
        await assign_plan_task(
            db_session,
            order_id=order_id,
            task_id="cnc_face_cut",
            assigned_employee_id=emp.id,
        )
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == "operational_readiness_blocked"
    assert exc.value.detail["operational_readiness_status"] == "v2_not_materialized"


@pytest.mark.asyncio
async def test_start_gate_uses_operational_tasks_not_planned(db_session):
    order_id = 39704
    await _seed_plan(db_session, order_id=order_id, tasks_json=_v2_envelope())

    with pytest.raises(HTTPException) as exc:
        await evaluate_task_start_readiness(
            db_session,
            order_id=order_id,
            task_id="cnc_face_cut",
        )
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == "operational_readiness_blocked"
    assert exc.value.detail["operational_readiness_status"] == "v2_not_materialized"


@pytest.mark.asyncio
async def test_blueprint_v2_not_materialized_returns_empty_task_list(db_session):
    order_id = 39705
    await _seed_plan(db_session, order_id=order_id, tasks_json=_v2_envelope())

    blueprint = await get_order_production_blueprint(db_session, order_id)
    assert blueprint["tasks"] == []
    assert blueprint["summary"]["total_tasks"] == 0


def test_divergence_parse_plan_tasks_uses_operational_only():
    plan = ExecutionPlan(
        order_id=1,
        order_code="ORD-1",
        snapshot_version=1,
        tasks_json=_v2_envelope(),
        total_estimated_time_minutes=0,
    )
    assert DivergenceService._parse_plan_tasks(plan) == []


# ---------------------------------------------------------------------------
# Guardrails — scope, forbidden imports, no mobile edits
# ---------------------------------------------------------------------------


def test_touched_consumers_import_shared_parser_helpers():
    for path in CONSUMER_SERVICE_PATHS:
        source = path.read_text(encoding="utf-8")
        assert "execution_plan_task_parser" in source, f"{path.name} must use shared parser"


def test_touched_consumers_have_no_forbidden_imports():
    found: set[str] = set()
    for path in CONSUMER_SERVICE_PATHS:
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
    assert not found, f"Forbidden imports in consumer files: {found}"


def test_step_does_not_modify_employee_mobile_files():
    """Step 9.3.4.b consumer paths must not include Employee Mobile task service modules."""
    consumer_paths = {p.resolve() for p in CONSUMER_SERVICE_PATHS}
    forbidden_mobile = [
        BACKEND_ROOT / "services" / "employee_mobile_tasks_service.py",
        BACKEND_ROOT / "services" / "dev_employee_mobile_sandu_fixture_service.py",
    ]
    for mobile_path in forbidden_mobile:
        assert mobile_path.resolve() not in consumer_paths
        assert mobile_path.exists(), f"Expected mobile guard path: {mobile_path}"


def test_assignment_invalid_json_raises_clear_error():
    from services.execution_task_assignment_service import _load_plan_operational_tasks

    with pytest.raises(ExecutionTaskAssignmentError) as exc:
        _load_plan_operational_tasks("{bad-json")
    assert exc.value.code == "tasks_json_invalid"
