"""Dev owner user seed — local readiness only, no employee/payroll side effects."""

from __future__ import annotations

import pytest
from models.auth import User
from models.employee_attendance_event import EmployeeAttendanceEvent
from models.employee_payment_record import EmployeePaymentRecord
from models.employee_request import EmployeeRequest
from models.employees import Employees
from services.dev_owner_user_seed_service import (
    DevOwnerUserSeedConfig,
    load_dev_owner_user_seed_config_from_env,
    seed_dev_owner_user,
    validate_dev_owner_user_seed_config,
)
from sqlalchemy import func, select

from core.config import resolve_database_url


def _cfg(**kwargs) -> DevOwnerUserSeedConfig:
    defaults = {
        "email": "seed-test@workos.test",
        "name": "Seed Test User",
        "role": "admin",
        "user_id": "dev-owner-seed-test",
        "dry_run": False,
    }
    defaults.update(kwargs)
    return DevOwnerUserSeedConfig(**defaults)


async def _count_users(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(User))
    return int(result.scalar_one())


async def _count_employees(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(Employees))
    return int(result.scalar_one())


async def _count_attendance(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(EmployeeAttendanceEvent))
    return int(result.scalar_one())


async def _count_requests(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(EmployeeRequest))
    return int(result.scalar_one())


async def _count_payments(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(EmployeePaymentRecord))
    return int(result.scalar_one())


async def _seed_user(
    db_session,
    *,
    user_id: str,
    email: str,
    name: str = "Existing User",
    role: str = "admin",
) -> User:
    user = User(id=user_id, email=email, name=name, role=role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_dry_run_would_create_user_no_persistence(db_session):
    before = await _count_users(db_session)
    result = await seed_dev_owner_user(
        db_session,
        _cfg(user_id="dev-owner-dry-run", email="dry-run@workos.test", dry_run=True),
    )
    after = await _count_users(db_session)

    assert result.success is True
    assert result.action == "dry_run_would_create"
    assert result.dry_run is True
    assert result.email == "dry-run@workos.test"
    assert before == after


@pytest.mark.asyncio
async def test_real_run_creates_user(db_session):
    result = await seed_dev_owner_user(
        db_session,
        _cfg(user_id="dev-owner-real-create", email="real-create@workos.test", dry_run=False),
    )

    assert result.success is True
    assert result.action == "created"
    assert result.user_id == "dev-owner-real-create"
    assert result.role == "admin"
    user = await db_session.get(User, "dev-owner-real-create")
    assert user is not None
    assert user.email == "real-create@workos.test"


@pytest.mark.asyncio
async def test_idempotent_second_run_returns_already_exists(db_session):
    cfg = _cfg(user_id="dev-owner-idempotent", email="idempotent@workos.test")
    first = await seed_dev_owner_user(db_session, cfg)
    assert first.action == "created"

    second = await seed_dev_owner_user(db_session, cfg)
    assert second.success is True
    assert second.action == "already_exists"
    result = await db_session.execute(
        select(func.count()).select_from(User).where(User.email == "idempotent@workos.test")
    )
    assert int(result.scalar_one()) == 1


@pytest.mark.asyncio
async def test_existing_email_with_same_id_does_not_duplicate(db_session):
    await _seed_user(
        db_session,
        user_id="dev-owner-same-id",
        email="same-id@workos.test",
        name="Same Id User",
    )
    result = await seed_dev_owner_user(
        db_session,
        _cfg(user_id="dev-owner-same-id", email="same-id@workos.test", name="Same Id User"),
    )

    assert result.success is True
    assert result.action == "already_exists"
    result = await db_session.execute(
        select(func.count()).select_from(User).where(User.email == "same-id@workos.test")
    )
    assert int(result.scalar_one()) == 1


@pytest.mark.asyncio
async def test_existing_user_id_with_different_email_returns_conflict(db_session):
    await _seed_user(
        db_session,
        user_id="dev-owner-conflict-id",
        email="conflict-id@workos.test",
    )
    result = await seed_dev_owner_user(
        db_session,
        _cfg(user_id="dev-owner-conflict-id", email="other-conflict@workos.test"),
    )

    assert result.success is False
    assert result.action == "conflict"
    assert result.error == "user_id_exists_with_different_email"


@pytest.mark.asyncio
async def test_existing_email_with_different_user_id_returns_conflict(db_session):
    await _seed_user(
        db_session,
        user_id="other-user-id-conflict",
        email="email-conflict@workos.test",
    )
    result = await seed_dev_owner_user(
        db_session,
        _cfg(user_id="new-user-id-conflict", email="email-conflict@workos.test"),
    )

    assert result.success is False
    assert result.action == "conflict"
    assert result.error == "email_exists_with_different_user_id"


@pytest.mark.asyncio
async def test_default_role_admin_accepted(db_session):
    result = await seed_dev_owner_user(
        db_session,
        _cfg(
            user_id="dev-owner-admin-role",
            email="admin-role@workos.test",
            role="admin",
            dry_run=False,
        ),
    )
    assert result.success is True
    assert result.role == "admin"


@pytest.mark.asyncio
async def test_custom_valid_role_env_accepted(db_session, monkeypatch):
    monkeypatch.setenv("WORKOS_DEV_OWNER_ROLE", "manager")
    cfg = load_dev_owner_user_seed_config_from_env()
    assert cfg.role == "manager"
    assert validate_dev_owner_user_seed_config(cfg) is None

    result = await seed_dev_owner_user(
        db_session,
        _cfg(
            user_id="dev-owner-manager-role",
            email="manager-role@workos.test",
            role="manager",
            dry_run=False,
        ),
    )
    assert result.success is True
    assert result.role == "manager"


@pytest.mark.asyncio
async def test_invalid_role_rejected(db_session):
    before = await _count_users(db_session)
    result = await seed_dev_owner_user(
        db_session,
        _cfg(user_id="dev-owner-invalid-role", email="invalid-role@workos.test", role="owner", dry_run=False),
    )
    assert result.success is False
    assert result.action == "error"
    assert result.error == "invalid_role:owner"
    assert await _count_users(db_session) == before


@pytest.mark.asyncio
async def test_does_not_create_employee(db_session):
    before = await _count_employees(db_session)
    await seed_dev_owner_user(
        db_session,
        _cfg(user_id="dev-owner-no-employee", email="no-employee@workos.test", dry_run=False),
    )
    assert await _count_employees(db_session) == before


@pytest.mark.asyncio
async def test_does_not_create_attendance_events(db_session):
    before = await _count_attendance(db_session)
    await seed_dev_owner_user(
        db_session,
        _cfg(user_id="dev-owner-no-attendance", email="no-attendance@workos.test", dry_run=False),
    )
    assert await _count_attendance(db_session) == before


@pytest.mark.asyncio
async def test_does_not_create_employee_requests(db_session):
    before = await _count_requests(db_session)
    await seed_dev_owner_user(
        db_session,
        _cfg(user_id="dev-owner-no-requests", email="no-requests@workos.test", dry_run=False),
    )
    assert await _count_requests(db_session) == before


@pytest.mark.asyncio
async def test_does_not_create_payment_records(db_session):
    before = await _count_payments(db_session)
    await seed_dev_owner_user(
        db_session,
        _cfg(user_id="dev-owner-no-payments", email="no-payments@workos.test", dry_run=False),
    )
    assert await _count_payments(db_session) == before


def test_resolve_database_url_missing_raises_clear_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr("core.config.load_backend_env", lambda: None)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        resolve_database_url()
