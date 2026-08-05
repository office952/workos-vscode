"""Task Resource Requirement — read-only projection service + API proofs."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import get_db
from core.sqlite_pragma import register_sqlite_foreign_keys
from dependencies.auth import get_current_user
from main import app
from schemas.auth import UserResponse
from services.task_resource_requirement_projection_service import (
    TaskResourceRequirementPlanNotFoundError,
    TaskResourceRequirementTaskNotFoundError,
    project_plan_resource_requirements,
    project_task_resource_requirements,
    soft_resource_mode_hint,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LED_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters"
CNC_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:cnc_face_cut"
METAL_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:return_face_bonding"
VINYL_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vinyl_application"


def _alembic_cmd(db_async_url: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["ENVIRONMENT"] = "test"
    env["DATABASE_URL"] = db_async_url
    env["JWT_SECRET_KEY"] = "local-dev-secret-not-for-production"
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _async_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.resolve().as_posix()}"


def _user(uid: str, role: str) -> UserResponse:
    return UserResponse(
        id=uid, email=f"{uid}@t.test", name=uid, role=role, last_login=None
    )


def _op(
    *,
    task_id: str,
    workcenter: str | None = None,
    operation: str | None = None,
    minutes: float | None = None,
    minutes_source: str | None = None,
    sequence: int = 1,
    assigned_employee_id: int | None = None,
) -> dict:
    task: dict = {
        "task_id": task_id,
        "sequence_index": sequence,
    }
    if operation is not None:
        task["source_operation_code"] = operation
    if workcenter is not None:
        task["workcenter"] = workcenter
        task["machine_requirement"] = {
            "workcenter": workcenter,
            "mapping_source": "test",
            "resolution_status": "resolved",
        }
    if minutes is not None:
        task["estimated_time_minutes"] = minutes
    if minutes_source is not None:
        task["planning_minutes_source"] = minutes_source
    if assigned_employee_id is not None:
        task["assigned_employee_id"] = assigned_employee_id
    return task


# ---------------------------------------------------------------------------
# Pure unit — soft hint + classification
# ---------------------------------------------------------------------------


def test_soft_hint_hybrid_is_unknown():
    assert soft_resource_mode_hint("WC_METAL_FAB") == "UNKNOWN"
    assert soft_resource_mode_hint("WC_VINYL_APPLICATION") == "UNKNOWN"


def test_soft_hint_non_hybrid_safe():
    assert soft_resource_mode_hint("WC_CNC_ROUTING") == "MACHINE_BOUND"
    assert soft_resource_mode_hint("WC_LED_ASSEMBLY") == "MANUAL_WORKSPACE"
    assert soft_resource_mode_hint("WC_PREPRESS") == "PERSON_DRIVEN"
    assert soft_resource_mode_hint("WC_FIELD_INSTALLATION") == "FIELD"
    assert soft_resource_mode_hint(None) == "UNKNOWN"
    assert soft_resource_mode_hint("WC_UNKNOWN_ZONE") == "UNKNOWN"


def test_known_minimal_task():
    p = project_task_resource_requirements(
        _op(
            task_id=CNC_TASK,
            workcenter="WC_CNC_ROUTING",
            operation="cnc_face_cut",
            minutes=45.0,
            minutes_source="PRODUCT_AGGREGATE_DERIVED",
        ),
        execution_plan_id=23,
    )
    assert p.resource_requirements_status == "KNOWN_MINIMAL"
    assert p.resource_mode_hint == "MACHINE_BOUND"
    assert "estimated_time_minutes" in p.known_fields
    assert "resource_mode_hint" in p.derived_fields
    assert "required_people_min" in p.unknown_fields
    assert "workspace_class" in p.unknown_fields
    assert p.estimated_time_minutes == 45.0


def test_partial_null_duration_led():
    p = project_task_resource_requirements(
        _op(
            task_id=LED_TASK,
            workcenter="WC_LED_ASSEMBLY",
            operation="led_install_letters",
            minutes=None,
            assigned_employee_id=7,
        ),
        execution_plan_id=23,
    )
    assert p.resource_requirements_status == "PARTIAL"
    assert p.resource_mode_hint == "MANUAL_WORKSPACE"
    assert p.estimated_time_minutes is None
    assert "estimated_time_minutes" in p.unknown_fields
    assert "required_people_min" in p.unknown_fields
    # Assignment must not invent people demand
    assert "assigned_employee_id" not in p.known_fields


def test_hybrid_unknown_mode_partial_when_wc_known():
    p = project_task_resource_requirements(
        _op(
            task_id=METAL_TASK,
            workcenter="WC_METAL_FAB",
            operation="return_face_bonding",
        ),
        execution_plan_id=23,
    )
    assert p.resource_mode_hint == "UNKNOWN"
    assert p.resource_requirements_status == "PARTIAL"
    assert "resource_mode_hint" not in p.derived_fields


def test_vinyl_hybrid_unknown():
    p = project_task_resource_requirements(
        _op(task_id=VINYL_TASK, workcenter="WC_VINYL_APPLICATION"),
        execution_plan_id=23,
    )
    assert p.resource_mode_hint == "UNKNOWN"


def test_unknown_missing_identity_and_wc():
    p = project_task_resource_requirements(
        {"sequence_index": 1},
        execution_plan_id=1,
    )
    assert p.task_key == ""
    assert p.resource_requirements_status == "UNKNOWN"


def test_missing_operation_code_listed_unknown():
    p = project_task_resource_requirements(
        _op(task_id=CNC_TASK, workcenter="WC_CNC_ROUTING"),
        execution_plan_id=1,
    )
    assert "operation_code" in p.unknown_fields
    assert p.operation_code is None


def test_missing_workcenter_unknown_or_partial():
    p = project_task_resource_requirements(
        _op(task_id=CNC_TASK, operation="cnc_face_cut", minutes=10.0),
        execution_plan_id=1,
    )
    assert "workcenter_code" in p.unknown_fields
    assert p.resource_requirements_status in {"PARTIAL", "UNKNOWN"}


def test_known_duration_preserved_null_not_zero():
    p = project_task_resource_requirements(
        _op(task_id=LED_TASK, workcenter="WC_LED_ASSEMBLY"),
        execution_plan_id=23,
    )
    assert p.estimated_time_minutes is None
    assert p.estimated_time_minutes != 0


def test_provenance_entries_present():
    p = project_task_resource_requirements(
        _op(
            task_id=CNC_TASK,
            workcenter="WC_CNC_ROUTING",
            operation="cnc_face_cut",
            minutes=12,
            minutes_source="MANAGER_ESTIMATE",
        ),
        execution_plan_id=1,
    )
    fields = {x.field: x for x in p.source_provenance}
    assert fields["task_key"].source == "EXECUTION_PLAN_SNAPSHOT"
    assert fields["workcenter_label"].source == "WORKCENTER_REGISTRY"
    assert fields["workcenter_label"].derived is True
    assert fields["resource_mode_hint"].confidence == "SAFE_DERIVATION"


# ---------------------------------------------------------------------------
# Isolated DB — plan load / filter / ordering / immutability
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def trr_session(tmp_path: Path):
    db = tmp_path / "trr.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    tasks = {
        "source": "order_snapshot_v2",
        "operational_tasks": [
            _op(
                task_id=CNC_TASK,
                workcenter="WC_CNC_ROUTING",
                operation="cnc_face_cut",
                minutes=30,
                minutes_source="PRODUCT_AGGREGATE_DERIVED",
                sequence=2,
            ),
            _op(
                task_id=LED_TASK,
                workcenter="WC_LED_ASSEMBLY",
                operation="led_install_letters",
                sequence=1,
                assigned_employee_id=7,
            ),
            _op(
                task_id=METAL_TASK,
                workcenter="WC_METAL_FAB",
                operation="return_face_bonding",
                sequence=3,
            ),
        ],
    }
    with sync.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (23, 880750, '880750', 1, :tj, 0.0, "
                "'2026-08-04 16:00:00', '2026-08-04 16:00:00')"
            ),
            {"tj": json.dumps(tasks)},
        )
    sync.dispose()

    engine = create_async_engine(url)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_plan_summary_and_stable_ordering(trr_session: AsyncSession):
    before = (
        await trr_session.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id = 23")
        )
    ).scalar_one()
    sha_before = hashlib.sha256(before.encode("utf-8")).hexdigest()

    result = await project_plan_resource_requirements(trr_session, plan_id=23)
    assert result.summary.total_tasks == 3
    assert result.summary.known_minimal == 1
    assert result.summary.partial == 2
    assert result.summary.hybrid_unknown_mode == 1
    assert result.summary.duration_known == 1
    assert result.summary.duration_unknown == 2
    # sequence_index order: LED(1), CNC(2), METAL(3)
    assert [t.task_key for t in result.tasks] == [LED_TASK, CNC_TASK, METAL_TASK]

    after = (
        await trr_session.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id = 23")
        )
    ).scalar_one()
    assert hashlib.sha256(after.encode("utf-8")).hexdigest() == sha_before


@pytest.mark.asyncio
async def test_task_filter(trr_session: AsyncSession):
    result = await project_plan_resource_requirements(
        trr_session, plan_id=23, task_key=LED_TASK
    )
    assert result.summary.total_tasks == 1
    assert result.tasks[0].task_key == LED_TASK
    assert result.tasks[0].resource_mode_hint == "MANUAL_WORKSPACE"


@pytest.mark.asyncio
async def test_plan_and_task_missing(trr_session: AsyncSession):
    with pytest.raises(TaskResourceRequirementPlanNotFoundError):
        await project_plan_resource_requirements(trr_session, plan_id=99999)
    with pytest.raises(TaskResourceRequirementTaskNotFoundError):
        await project_plan_resource_requirements(
            trr_session, plan_id=23, task_key="missing-task"
        )


@pytest.mark.asyncio
async def test_api_plan_summary_filter_permissions(trr_session: AsyncSession):
    async def _override_get_db():
        yield trr_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        for role, expect in (("admin", 200), ("manager", 200), ("operator", 403)):
            user = _user(f"{role}-trr", role)

            async def _u(u=user):
                return u

            app.dependency_overrides[get_current_user] = _u
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/v1/execution/plans/23/resource-requirements")
            assert resp.status_code == expect, (role, resp.status_code, resp.text)
            if expect == 200:
                body = resp.json()
                assert body["summary"]["total_tasks"] == 3
                assert len(body["tasks"]) == 3

        # task filter
        app.dependency_overrides[get_current_user] = lambda: _user("admin-f", "admin")
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(
            "/api/v1/execution/plans/23/resource-requirements",
            params={"task_key": LED_TASK},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["total_tasks"] == 1
        assert body["tasks"][0]["workcenter_code"] == "WC_LED_ASSEMBLY"

        # missing plan / task
        assert (
            client.get("/api/v1/execution/plans/99999/resource-requirements").status_code
            == 404
        )
        assert (
            client.get(
                "/api/v1/execution/plans/23/resource-requirements",
                params={"task_key": "nope"},
            ).status_code
            == 404
        )
    finally:
        app.dependency_overrides.clear()


def test_no_frontend_touched():
    # Guardrail marker — GO forbids frontend changes; file exists only in backend.
    assert (BACKEND_ROOT / "services" / "task_resource_requirement_projection_service.py").is_file()
    assert not (
        BACKEND_ROOT.parent / "frontend" / "src" / "lib" / "taskResourceRequirement.ts"
    ).exists()
