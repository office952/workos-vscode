"""Resource State R7 — configuration command CAS / idempotency / activation boundary."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import get_db
from core.schema_ownership import RESOURCE_STATE_TABLES
from core.sqlite_pragma import register_sqlite_foreign_keys
from dependencies.auth import get_current_user
from main import app
from schemas.auth import UserResponse
from schemas.resource_state_configuration import ResourceDomainConfigurationCommand
from services.resource_domain_configuration_command_service import (
    ACTIVATION_ALLOW_ENV,
    DOMAIN_WRITER_READY,
    ResourceDomainConfigurationActivationBlockedError,
    ResourceDomainConfigurationCasConflictError,
    ResourceDomainConfigurationConflictError,
    ResourceDomainConfigurationValidationError,
    assess_activation_readiness,
    configure_resource_domain,
)
from services.resource_domain_configuration_repository import (
    FORBIDDEN_TRANSITION_MUTATORS,
    ResourceDomainConfigurationRepository,
)
from services.resource_state_read_service import evaluate_task_resource_state

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LED_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters"


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


def _cmd(
    *,
    target_status: str,
    expected_version: int,
    idempotency_key: str | None = None,
    reason_code: str = "r7_test",
    reason_note: str | None = None,
) -> ResourceDomainConfigurationCommand:
    return ResourceDomainConfigurationCommand(
        target_status=target_status,  # type: ignore[arg-type]
        expected_version=expected_version,
        idempotency_key=idempotency_key or str(uuid.uuid4()),
        reason_code=reason_code,
        reason_note=reason_note,
        correlation_id="corr-r7-test",
    )


def _user(user_id: str, role: str) -> UserResponse:
    return UserResponse(
        id=user_id,
        email=f"{user_id}@workos.test",
        name=f"User {user_id}",
        role=role,
        last_login=None,
    )


@pytest_asyncio.fixture
async def r7_session(tmp_path: Path):
    db = tmp_path / "r7.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    tasks = {
        "source": "order_snapshot_v2",
        "operational_tasks": [
            {"task_id": LED_TASK, "assigned_employee_id": 7},
        ],
    }
    with sync.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO employees "
                "(id, name, status, employee_type, salary_currency, salary_period) "
                "VALUES (7, 'Andrei', 'active', 'internal', 'RON', 'monthly')"
            )
        )
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


def test_repository_forbids_transition_mutators():
    names = {
        n.lower()
        for n in dir(ResourceDomainConfigurationRepository)
        if not n.startswith("_")
    }
    for forbidden in FORBIDDEN_TRANSITION_MUTATORS:
        assert forbidden not in names


@pytest.mark.asyncio
async def test_create_disabled_configuration(r7_session: AsyncSession):
    result = await configure_resource_domain(
        r7_session,
        domain="SCHEDULING",
        command=_cmd(target_status="DISABLED", expected_version=0),
        actor_user_id="admin-1",
    )
    await r7_session.commit()
    assert result.version == 1
    assert result.status == "DISABLED"
    assert result.operation == "CONFIGURE_DOMAIN"
    assert result.already_applied is False
    count = (
        await r7_session.execute(
            text("SELECT COUNT(*) FROM resource_domain_configuration_transitions")
        )
    ).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_activate_and_disable(r7_session: AsyncSession):
    created = await configure_resource_domain(
        r7_session,
        domain="MACHINE_RESERVATION",
        command=_cmd(target_status="DISABLED", expected_version=0),
        actor_user_id="admin-1",
    )
    await r7_session.commit()
    activated = await configure_resource_domain(
        r7_session,
        domain="MACHINE_RESERVATION",
        command=_cmd(target_status="ACTIVE", expected_version=created.version),
        actor_user_id="admin-1",
    )
    await r7_session.commit()
    assert activated.status == "ACTIVE"
    assert activated.version == 2
    assert activated.operation == "ACTIVATE_DOMAIN"

    disabled = await configure_resource_domain(
        r7_session,
        domain="MACHINE_RESERVATION",
        command=_cmd(target_status="DISABLED", expected_version=activated.version),
        actor_user_id="manager-1",
    )
    await r7_session.commit()
    assert disabled.status == "DISABLED"
    assert disabled.version == 3
    assert disabled.operation == "DISABLE_DOMAIN"


@pytest.mark.asyncio
async def test_cas_success_and_stale(
    r7_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
):
    # Capacity has no product writer; temporarily mark ready for CAS path only.
    monkeypatch.setitem(DOMAIN_WRITER_READY, "CAPACITY_ALLOCATION", True)
    first = await configure_resource_domain(
        r7_session,
        domain="CAPACITY_ALLOCATION",
        command=_cmd(target_status="DISABLED", expected_version=0),
        actor_user_id="admin-1",
    )
    await r7_session.commit()
    with pytest.raises(ResourceDomainConfigurationCasConflictError) as stale:
        await configure_resource_domain(
            r7_session,
            domain="CAPACITY_ALLOCATION",
            command=_cmd(target_status="ACTIVE", expected_version=0),
            actor_user_id="admin-1",
        )
    assert stale.value.code == "cas_stale"
    await r7_session.rollback()

    ok = await configure_resource_domain(
        r7_session,
        domain="CAPACITY_ALLOCATION",
        command=_cmd(target_status="ACTIVE", expected_version=first.version),
        actor_user_id="admin-1",
    )
    await r7_session.commit()
    assert ok.version == first.version + 1


@pytest.mark.asyncio
async def test_idempotent_retry_same_payload(r7_session: AsyncSession):
    key = str(uuid.uuid4())
    cmd = _cmd(
        target_status="DISABLED",
        expected_version=0,
        idempotency_key=key,
        reason_note="same",
    )
    first = await configure_resource_domain(
        r7_session, domain="SCHEDULING", command=cmd, actor_user_id="admin-1"
    )
    await r7_session.commit()
    second = await configure_resource_domain(
        r7_session, domain="SCHEDULING", command=cmd, actor_user_id="admin-1"
    )
    await r7_session.commit()
    assert second.already_applied is True
    assert second.transition_id == first.transition_id
    assert second.version == first.version
    count = (
        await r7_session.execute(
            text("SELECT COUNT(*) FROM resource_domain_configuration_transitions")
        )
    ).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_idempotency_payload_conflict(r7_session: AsyncSession):
    key = str(uuid.uuid4())
    await configure_resource_domain(
        r7_session,
        domain="SCHEDULING",
        command=_cmd(
            target_status="DISABLED",
            expected_version=0,
            idempotency_key=key,
            reason_code="first",
        ),
        actor_user_id="admin-1",
    )
    await r7_session.commit()
    with pytest.raises(ResourceDomainConfigurationConflictError) as conflict:
        await configure_resource_domain(
            r7_session,
            domain="SCHEDULING",
            command=_cmd(
                target_status="DISABLED",
                expected_version=0,
                idempotency_key=key,
                reason_code="different",
            ),
            actor_user_id="admin-1",
        )
    assert conflict.value.code == "idempotency_payload_conflict"


@pytest.mark.asyncio
async def test_transition_exactly_once_and_atomic(r7_session: AsyncSession):
    result = await configure_resource_domain(
        r7_session,
        domain="SCHEDULING",
        command=_cmd(target_status="DISABLED", expected_version=0),
        actor_user_id="admin-1",
    )
    await r7_session.commit()
    row = (
        await r7_session.execute(
            text(
                "SELECT c.version, c.status, t.new_version, t.new_status "
                "FROM resource_domain_configurations c "
                "JOIN resource_domain_configuration_transitions t "
                "ON t.configuration_id = c.id "
                "WHERE c.domain = 'SCHEDULING'"
            )
        )
    ).one()
    assert row == (1, "DISABLED", 1, "DISABLED")
    assert result.transition_id

    # Failure before commit leaves nothing durable when rolled back.
    with pytest.raises(ResourceDomainConfigurationCasConflictError):
        await configure_resource_domain(
            r7_session,
            domain="SCHEDULING",
            command=_cmd(target_status="ACTIVE", expected_version=99),
            actor_user_id="admin-1",
        )
    await r7_session.rollback()
    count = (
        await r7_session.execute(
            text("SELECT COUNT(*) FROM resource_domain_configuration_transitions")
        )
    ).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_invalid_domain_and_status(r7_session: AsyncSession):
    with pytest.raises(ResourceDomainConfigurationValidationError) as bad_domain:
        await configure_resource_domain(
            r7_session,
            domain="NOT_A_DOMAIN",
            command=_cmd(target_status="DISABLED", expected_version=0),
            actor_user_id="admin-1",
        )
    assert bad_domain.value.code == "invalid_domain"

    with pytest.raises(Exception):
        # Pydantic rejects invalid status before service.
        ResourceDomainConfigurationCommand(
            target_status="CLEAR",  # type: ignore[arg-type]
            expected_version=0,
            idempotency_key=str(uuid.uuid4()),
            reason_code="x",
        )


@pytest.mark.asyncio
async def test_capacity_activation_ready_when_source_schema_present(
    r7_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
):
    """Stage 1: capacity activates on isolated head (s65); env bypass still unused."""
    monkeypatch.setenv(ACTIVATION_ALLOW_ENV, "1")
    ready, reason = await assess_activation_readiness(
        r7_session, domain="CAPACITY_ALLOCATION"
    )
    assert ready is True
    assert reason == "ready"
    act = await configure_resource_domain(
        r7_session,
        domain="CAPACITY_ALLOCATION",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await r7_session.commit()
    assert act.status == "ACTIVE"


@pytest.mark.asyncio
async def test_evaluator_disabled_is_not_configured(r7_session: AsyncSession):
    await configure_resource_domain(
        r7_session,
        domain="SCHEDULING",
        command=_cmd(target_status="DISABLED", expected_version=0),
        actor_user_id="admin-1",
    )
    await r7_session.commit()
    result = await evaluate_task_resource_state(
        r7_session, plan_id=23, task_key=LED_TASK
    )
    assert result.scheduling.state == "NOT_CONFIGURED"
    assert result.scheduling.configured is False


@pytest.mark.asyncio
async def test_evaluator_active_no_records_clear(
    r7_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setitem(DOMAIN_WRITER_READY, "CAPACITY_ALLOCATION", True)
    await configure_resource_domain(
        r7_session,
        domain="SCHEDULING",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await configure_resource_domain(
        r7_session,
        domain="MACHINE_RESERVATION",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await configure_resource_domain(
        r7_session,
        domain="CAPACITY_ALLOCATION",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await r7_session.commit()
    result = await evaluate_task_resource_state(
        r7_session, plan_id=23, task_key=LED_TASK
    )
    assert result.scheduling.state == "CLEAR"
    assert result.machine_reservation.state == "CLEAR"
    assert result.capacity_allocation.state == "CLEAR"
    assert result.aggregate == "CLEAR"


@pytest.mark.asyncio
async def test_api_roles_admin_manager_ok_operator_viewer_denied(
    r7_session: AsyncSession,
):
    async def _override_get_db():
        yield r7_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        for role in ("admin", "manager"):
            user = _user(f"{role}-1", role)

            async def _ok_user(u=user):
                return u

            app.dependency_overrides[get_current_user] = _ok_user
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post(
                "/api/v1/execution/resource-state/configurations/SCHEDULING",
                json={
                    "target_status": "DISABLED",
                    "expected_version": 0 if role == "admin" else 1,
                    "idempotency_key": str(uuid.uuid4()),
                    "reason_code": "api_role_test",
                },
            )
            assert resp.status_code == 200, (role, resp.status_code, resp.text)

        for role in ("operator", "viewer"):
            user = _user(f"{role}-1", role)

            async def _denied_user(u=user):
                return u

            app.dependency_overrides[get_current_user] = _denied_user
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post(
                "/api/v1/execution/resource-state/configurations/"
                "CAPACITY_ALLOCATION",
                json={
                    "target_status": "DISABLED",
                    "expected_version": 0,
                    "idempotency_key": str(uuid.uuid4()),
                    "reason_code": "api_role_denied",
                },
            )
            assert resp.status_code == 403, (role, resp.status_code, resp.text)
    finally:
        app.dependency_overrides.clear()


def test_rs_tables_still_eight():
    assert len(RESOURCE_STATE_TABLES) == 8


def test_no_config_hint_constants():
    # Sanity: activation allow env name is stable for docs/tests.
    assert ACTIVATION_ALLOW_ENV == "WORKOS_RESOURCE_STATE_ALLOW_DOMAIN_ACTIVATION"
