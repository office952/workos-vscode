"""Step 9.3.4.d — operational readiness gate enforcement on backend mutations."""

from __future__ import annotations

import ast
import json
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.auth import UserResponse
from services.execution_plan_operational_readiness_service import (
    BLOCKER_OPERATIONAL_TASK_DEPENDENCY_MISSING,
    BLOCKER_OPERATIONAL_TASKS_NOT_MATERIALIZED,
    STATUS_V2_NOT_MATERIALIZED,
)
from services.execution_task_assignment_service import assign_plan_task
from services.execution_task_instructions_service import update_plan_task_instructions
from services.order_production_blueprint_service import get_order_production_blueprint
from services.task_start_gate_service import evaluate_task_start_readiness

BACKEND_ROOT = Path(__file__).resolve().parents[1]
STEP_PATHS = (
    BACKEND_ROOT / "services" / "execution_plan_operational_readiness_service.py",
    BACKEND_ROOT / "services" / "execution_task_assignment_service.py",
    BACKEND_ROOT / "services" / "execution_task_instructions_service.py",
    BACKEND_ROOT / "services" / "task_start_gate_service.py",
    BACKEND_ROOT / "services" / "order_production_blueprint_service.py",
    BACKEND_ROOT / "routers" / "operator_tasks.py",
    Path(__file__).resolve(),
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
    "/price",
)


def _user(role: str = "admin") -> UserResponse:
    uid = f"gate-{uuid.uuid4().hex[:8]}"
    return UserResponse(
        id=uid,
        email=f"{uid}@workos.test",
        name=f"User {uid}",
        role=role,
        last_login=None,
    )


def _client_for(db_fixture, user: UserResponse) -> TestClient:
    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    return TestClient(app, raise_server_exceptions=False)


def _cleanup():
    app.dependency_overrides.clear()


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


async def _seed_employee(db_session) -> Employees:
    emp = Employees(name="Gate Worker", status="active", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


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


async def _count_execution_reality(db_session) -> int:
    return int(await db_session.scalar(select(func.count()).select_from(ExecutionReality)) or 0)


def _assert_readiness_blocked(exc: HTTPException, *, status: str, blocker: str):
    assert exc.value.status_code == 422
    detail = exc.value.detail
    assert detail["error"] == "operational_readiness_blocked"
    assert detail["operational_readiness_status"] == status
    assert blocker in detail["blockers"]


# ---------------------------------------------------------------------------
# Mutating path gates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assignment_v2_not_materialized_returns_422(db_session):
    order_id = 39901
    emp = await _seed_employee(db_session)
    await _seed_plan(db_session, order_id=order_id, tasks_json=_v2_envelope())

    with pytest.raises(HTTPException) as exc:
        await assign_plan_task(
            db_session,
            order_id=order_id,
            task_id="cnc_face_cut",
            assigned_employee_id=emp.id,
        )
    _assert_readiness_blocked(
        exc,
        status=STATUS_V2_NOT_MATERIALIZED,
        blocker=BLOCKER_OPERATIONAL_TASKS_NOT_MATERIALIZED,
    )


@pytest.mark.asyncio
async def test_instructions_v2_not_materialized_returns_422(db_session):
    order_id = 39902
    await _seed_plan(db_session, order_id=order_id, tasks_json=_v2_envelope())

    with pytest.raises(HTTPException) as exc:
        await update_plan_task_instructions(
            db_session,
            order_id=order_id,
            task_id="cnc_face_cut",
            instructions="Prep CNC",
        )
    _assert_readiness_blocked(
        exc,
        status=STATUS_V2_NOT_MATERIALIZED,
        blocker=BLOCKER_OPERATIONAL_TASKS_NOT_MATERIALIZED,
    )


@pytest.mark.asyncio
async def test_start_gate_v2_not_materialized_returns_422(db_session):
    order_id = 39903
    await _seed_plan(db_session, order_id=order_id, tasks_json=_v2_envelope())

    with pytest.raises(HTTPException) as exc:
        await evaluate_task_start_readiness(
            db_session,
            order_id=order_id,
            task_id="cnc_face_cut",
        )
    _assert_readiness_blocked(
        exc,
        status=STATUS_V2_NOT_MATERIALIZED,
        blocker=BLOCKER_OPERATIONAL_TASKS_NOT_MATERIALIZED,
    )


@pytest.mark.asyncio
async def test_assignment_blocked_task_graph_returns_422(db_session):
    order_id = 39904
    emp = await _seed_employee(db_session)
    operational = [
        {
            "task_id": "child",
            "process_type": "cnc_routing",
            "depends_on_task_ids": ["missing_parent"],
        }
    ]
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(operational=operational, execution_tasks_created=True),
    )

    with pytest.raises(HTTPException) as exc:
        await assign_plan_task(
            db_session,
            order_id=order_id,
            task_id="child",
            assigned_employee_id=emp.id,
        )
    _assert_readiness_blocked(
        exc,
        status="blocked_task_graph",
        blocker=BLOCKER_OPERATIONAL_TASK_DEPENDENCY_MISSING,
    )


@pytest.mark.asyncio
async def test_start_gate_blocked_task_graph_returns_422(db_session):
    order_id = 39905
    operational = [
        {
            "task_id": "child",
            "process_type": "cnc_routing",
            "depends_on_task_ids": ["missing_parent"],
        }
    ]
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(operational=operational, execution_tasks_created=True),
    )

    with pytest.raises(HTTPException) as exc:
        await evaluate_task_start_readiness(
            db_session,
            order_id=order_id,
            task_id="child",
        )
    _assert_readiness_blocked(
        exc,
        status="blocked_task_graph",
        blocker=BLOCKER_OPERATIONAL_TASK_DEPENDENCY_MISSING,
    )


@pytest.mark.asyncio
async def test_legacy_v1_assignment_unchanged(db_session):
    order_id = 39906
    emp = await _seed_employee(db_session)
    await _seed_plan(db_session, order_id=order_id, tasks_json=_legacy_tasks("T-V1"))

    result = await assign_plan_task(
        db_session,
        order_id=order_id,
        task_id="T-V1",
        assigned_employee_id=emp.id,
    )
    assert result["assigned_employee_id"] == emp.id


@pytest.mark.asyncio
async def test_legacy_v1_instructions_unchanged(db_session):
    order_id = 39907
    await _seed_plan(db_session, order_id=order_id, tasks_json=_legacy_tasks("T-V1-INS"))

    result = await update_plan_task_instructions(
        db_session,
        order_id=order_id,
        task_id="T-V1-INS",
        instructions="Follow sketch",
    )
    assert result["instructions"] == "Follow sketch"


@pytest.mark.asyncio
async def test_legacy_v1_start_gate_wrong_task_still_404(db_session):
    order_id = 39908
    await _seed_plan(db_session, order_id=order_id, tasks_json=_legacy_tasks("T-V1-START"))

    with pytest.raises(HTTPException) as exc:
        await evaluate_task_start_readiness(
            db_session,
            order_id=order_id,
            task_id="WRONG-TASK",
        )
    assert exc.value.status_code == 404
    assert exc.value.detail == {"error": "task_not_in_plan"}


@pytest.mark.asyncio
async def test_v2_materialized_assignment_happy_path(db_session):
    order_id = 39909
    emp = await _seed_employee(db_session)
    operational = [
        {
            "task_id": "cnc_face_cut",
            "process_type": "cnc_routing",
            "depends_on_task_ids": [],
        }
    ]
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(operational=operational, execution_tasks_created=True),
    )

    result = await assign_plan_task(
        db_session,
        order_id=order_id,
        task_id="cnc_face_cut",
        assigned_employee_id=emp.id,
    )
    assert result["assigned_employee_id"] == emp.id


@pytest.mark.asyncio
async def test_v2_materialized_instructions_happy_path(db_session):
    order_id = 39910
    operational = [
        {
            "task_id": "cnc_face_cut",
            "process_type": "cnc_routing",
            "depends_on_task_ids": [],
        }
    ]
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(operational=operational, execution_tasks_created=True),
    )

    result = await update_plan_task_instructions(
        db_session,
        order_id=order_id,
        task_id="cnc_face_cut",
        instructions="Use fixture A",
    )
    assert result["instructions"] == "Use fixture A"


@pytest.mark.asyncio
async def test_v2_materialized_start_gate_reaches_task_lookup(db_session):
    order_id = 39911
    operational = [
        {
            "task_id": "cnc_face_cut",
            "process_type": "cnc_routing",
            "depends_on_task_ids": [],
        }
    ]
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(operational=operational, execution_tasks_created=True),
    )

    plan_task, readiness, _quote_input = await evaluate_task_start_readiness(
        db_session,
        order_id=order_id,
        task_id="cnc_face_cut",
    )
    assert plan_task["task_id"] == "cnc_face_cut"
    assert "readiness_status" in readiness


@pytest.mark.asyncio
async def test_wrong_task_id_after_readiness_ready_returns_404(db_session):
    order_id = 39912
    emp = await _seed_employee(db_session)
    await _seed_plan(db_session, order_id=order_id, tasks_json=_legacy_tasks("T-OK"))

    with pytest.raises(HTTPException) as exc:
        await assign_plan_task(
            db_session,
            order_id=order_id,
            task_id="T-MISSING",
            assigned_employee_id=emp.id,
        )
    assert exc.value.status_code == 404
    assert exc.value.detail == {"error": "task_not_found_in_plan"}


# ---------------------------------------------------------------------------
# Read-only paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_blueprint_includes_readiness_fields_for_not_materialized(db_session):
    order_id = 39913
    await _seed_plan(db_session, order_id=order_id, tasks_json=_v2_envelope())

    blueprint = await get_order_production_blueprint(db_session, order_id)
    assert blueprint["operational_readiness_status"] == STATUS_V2_NOT_MATERIALIZED
    assert blueprint["operational_tasks_count"] == 0
    assert BLOCKER_OPERATIONAL_TASKS_NOT_MATERIALIZED in blueprint["operational_readiness_blockers"]
    assert blueprint["tasks"] == []


def test_operator_task_list_includes_order_readiness_metadata(db_fixture, db_session):
    order_id = 39914

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
    client = _client_for(db_fixture, _user("operator"))
    try:
        resp = client.get("/api/v1/operator/tasks")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        readiness = body["order_operational_readiness"][str(order_id)]
        assert readiness["operational_readiness_status"] == STATUS_V2_NOT_MATERIALIZED
        assert readiness["operational_tasks_count"] == 0
    finally:
        _cleanup()


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_guard_checks_do_not_create_execution_reality_rows(db_session):
    before = await _count_execution_reality(db_session)
    await _seed_plan(db_session, order_id=39915, tasks_json=_v2_envelope())
    with pytest.raises(HTTPException):
        await evaluate_task_start_readiness(
            db_session,
            order_id=39915,
            task_id="cnc_face_cut",
        )
    after = await _count_execution_reality(db_session)
    assert after == before


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


def test_employee_mobile_files_not_in_step_scope():
    mobile_fragments = (
        "employee_mobile_tasks_service.py",
        "dev_employee_mobile_sandu_fixture_service.py",
    )
    for path in STEP_PATHS:
        for fragment in mobile_fragments:
            assert fragment not in path.name
