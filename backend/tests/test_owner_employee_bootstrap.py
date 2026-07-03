"""Owner employee bootstrap — idempotent, no payroll/attendance side effects."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from models.auth import User
from models.employee_attendance_event import EmployeeAttendanceEvent
from models.employee_payment_record import EmployeePaymentRecord
from models.employee_request import EmployeeRequest
from models.employees import Employees
from schemas.auth import UserResponse
from services.owner_employee_bootstrap_service import (
    OwnerBootstrapConfig,
    bootstrap_owner_employee,
    check_owner_mobile_readiness,
    validate_bootstrap_config,
)
from sqlalchemy import func, select

from core.database import get_db
from core.config import resolve_database_url, settings
from dependencies.auth import get_current_user
from main import app


def _config(**kwargs) -> OwnerBootstrapConfig:
    defaults = {
        "owner_user_id": kwargs.pop("owner_user_id", "owner-user-default"),
        "employee_name": "Axinte Remus",
        "employee_department": "Management",
        "employee_title": "Owner",
        "dry_run": False,
    }
    defaults.update(kwargs)
    return OwnerBootstrapConfig(**defaults)


async def _seed_user(db_session, *, user_id: str, email: str, role: str = "admin") -> User:
    user = User(id=user_id, email=email, name="Owner User", role=role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _seed_employee(
    db_session,
    *,
    name: str,
    user_id: str | None = None,
    status: str = "active",
    manager_employee_id: int | None = None,
    employee_type: str = "productive",
    cost_lunar_firma: float | None = None,
) -> Employees:
    emp = Employees(
        name=name,
        status=status,
        employee_type=employee_type,
        user_id=user_id,
        manager_employee_id=manager_employee_id,
        cost_lunar_firma=cost_lunar_firma,
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _seed_request(db_session, *, employee_id: int, status: str = "submitted") -> EmployeeRequest:
    row = EmployeeRequest(
        employee_id=employee_id,
        request_type="leave",
        status=status,
        title="Team request",
        start_date=date(2026, 6, 10),
        end_date=date(2026, 6, 12),
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


def test_validate_config_requires_lookup_and_name():
    assert validate_bootstrap_config(OwnerBootstrapConfig(employee_name="X")) is not None
    assert validate_bootstrap_config(_config()) is None


@pytest.mark.asyncio
async def test_creates_employee_for_user_without_employee(db_session):
    uid = "owner-create-1"
    await _seed_user(db_session, user_id=uid, email="owner-create@test.local")
    result = await bootstrap_owner_employee(db_session, _config(owner_user_id=uid))
    assert result.success is True
    assert result.action == "created"
    assert result.employee_id is not None

    emp = await db_session.get(Employees, result.employee_id)
    assert emp.user_id == uid
    assert emp.status == "active"
    assert emp.manager_employee_id is None
    assert emp.employee_type == "management"
    assert emp.cost_lunar_firma is None
    assert emp.monthly_internal_pay_amount is None


@pytest.mark.asyncio
async def test_does_not_create_duplicate_when_already_linked(db_session):
    uid = "owner-dup-1"
    await _seed_user(db_session, user_id=uid, email="owner-dup@test.local")
    cfg = _config(owner_user_id=uid)
    first = await bootstrap_owner_employee(db_session, cfg)
    second = await bootstrap_owner_employee(db_session, cfg)
    assert first.action == "created"
    assert second.action in ("already_linked", "updated")
    assert first.employee_id == second.employee_id

    count = await db_session.execute(
        select(func.count()).select_from(Employees).where(Employees.user_id == uid)
    )
    assert int(count.scalar_one()) == 1


@pytest.mark.asyncio
async def test_links_existing_employee_without_user_id(db_session):
    uid = "owner-link-1"
    await _seed_user(db_session, user_id=uid, email="owner-link@test.local")
    existing = await _seed_employee(db_session, name="Axinte Remus", user_id=None)
    result = await bootstrap_owner_employee(db_session, _config(owner_user_id=uid))
    assert result.success is True
    assert result.action == "linked_existing_employee"
    assert result.employee_id == existing.id
    await db_session.refresh(existing)
    assert existing.user_id == uid


@pytest.mark.asyncio
async def test_dry_run_does_not_persist(db_session):
    uid = "owner-dry-1"
    await _seed_user(db_session, user_id=uid, email="owner-dry@test.local")
    before = await db_session.execute(select(func.count()).select_from(Employees))
    before_count = int(before.scalar_one())
    result = await bootstrap_owner_employee(db_session, _config(owner_user_id=uid, dry_run=True))
    assert result.success is True
    assert result.action == "dry_run_would_create"
    after = await db_session.execute(select(func.count()).select_from(Employees))
    assert int(after.scalar_one()) == before_count


@pytest.mark.asyncio
async def test_owner_employee_has_null_manager_employee_id(db_session):
    uid = "owner-mgr-null-1"
    await _seed_user(db_session, user_id=uid, email="owner-mgr-null@test.local")
    result = await bootstrap_owner_employee(db_session, _config(owner_user_id=uid))
    emp = await db_session.get(Employees, result.employee_id)
    assert emp.manager_employee_id is None


@pytest.mark.asyncio
async def test_does_not_set_payroll_fields(db_session):
    uid = "owner-payroll-1"
    await _seed_user(db_session, user_id=uid, email="owner-payroll@test.local")
    result = await bootstrap_owner_employee(db_session, _config(owner_user_id=uid))
    emp = await db_session.get(Employees, result.employee_id)
    assert emp.cost_lunar_firma is None
    assert emp.monthly_internal_pay_amount is None
    assert emp.ore_lucru_luna is None
    assert emp.ore_productive_luna is None


@pytest.mark.asyncio
async def test_does_not_create_attendance_or_requests(db_session):
    uid = "owner-sidefx-1"
    await _seed_user(db_session, user_id=uid, email="owner-sidefx@test.local")
    att_before = await db_session.execute(select(func.count()).select_from(EmployeeAttendanceEvent))
    req_before = await db_session.execute(select(func.count()).select_from(EmployeeRequest))
    pay_before = await db_session.execute(select(func.count()).select_from(EmployeePaymentRecord))
    await bootstrap_owner_employee(db_session, _config(owner_user_id=uid))
    att_after = await db_session.execute(select(func.count()).select_from(EmployeeAttendanceEvent))
    req_after = await db_session.execute(select(func.count()).select_from(EmployeeRequest))
    pay_after = await db_session.execute(select(func.count()).select_from(EmployeePaymentRecord))
    assert int(att_after.scalar_one()) == int(att_before.scalar_one())
    assert int(req_after.scalar_one()) == int(req_before.scalar_one())
    assert int(pay_after.scalar_one()) == int(pay_before.scalar_one())


@pytest.mark.asyncio
async def test_checker_pass_for_linked_active_owner(db_session):
    uid = "owner-check-pass-1"
    await _seed_user(db_session, user_id=uid, email="owner-check-pass@test.local", role="admin")
    mgr = await _seed_employee(db_session, name="Owner Read", user_id=uid)
    await _seed_employee(
        db_session,
        name="Direct For Owner",
        user_id="direct-owner-check",
        manager_employee_id=mgr.id,
    )
    cfg = OwnerBootstrapConfig(
        owner_user_id=uid,
        employee_name="Owner Read",
    )
    readiness = await check_owner_mobile_readiness(db_session, cfg)
    assert readiness.status == "PASS"
    assert readiness.employee_linked is True
    assert readiness.manager_employee_id_null is True
    assert readiness.direct_reports_count == 1


@pytest.mark.asyncio
async def test_checker_fail_without_employee_link(db_session):
    uid = "owner-check-fail-1"
    await _seed_user(db_session, user_id=uid, email="owner-check-fail@test.local", role="admin")
    readiness = await check_owner_mobile_readiness(db_session, _config(owner_user_id=uid))
    assert readiness.status == "FAIL"
    assert "missing_employee_link" in readiness.issues


@pytest.mark.asyncio
async def test_checker_warns_inactive_employee(db_session):
    uid = "owner-check-inactive-1"
    await _seed_user(db_session, user_id=uid, email="owner-check-inactive@test.local", role="admin")
    await _seed_employee(
        db_session,
        name="Axinte Remus",
        user_id=uid,
        status="inactive",
        employee_type="management",
    )
    readiness = await check_owner_mobile_readiness(db_session, _config(owner_user_id=uid))
    assert readiness.status == "FAIL"
    assert "inactive_employee" in readiness.issues


@pytest.mark.asyncio
async def test_user_not_found_returns_clear_error(db_session):
    result = await bootstrap_owner_employee(db_session, _config(owner_user_id="missing-user"))
    assert result.success is False
    assert result.error == "owner_user_not_found"


@pytest.mark.asyncio
async def test_ambiguous_name_match_blocks_auto_link(db_session):
    uid = "owner-ambig-1"
    await _seed_user(db_session, user_id=uid, email="owner-ambig@test.local")
    await _seed_employee(db_session, name="Axinte Remus", user_id=None)
    await _seed_employee(db_session, name="Axinte Remus", user_id=None)
    result = await bootstrap_owner_employee(db_session, _config(owner_user_id=uid))
    assert result.success is False
    assert result.error == "ambiguous_employee_name_match"


@pytest.mark.asyncio
async def test_idempotency_same_employee_id(db_session):
    uid = "owner-idem-1"
    await _seed_user(db_session, user_id=uid, email="owner-idem@test.local")
    cfg = _config(owner_user_id=uid)
    ids = []
    for _ in range(2):
        result = await bootstrap_owner_employee(db_session, cfg)
        ids.append(result.employee_id)
    assert ids[0] == ids[1]


def _user(user_id: str, role: str) -> UserResponse:
    return UserResponse(
        id=user_id,
        email=f"{user_id}@workos.test",
        name="Owner",
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


def _cleanup_overrides():
    app.dependency_overrides.clear()


def test_owner_as_formal_manager_sees_direct_report_team_requests(db_fixture, db_session):
    async def _setup():
        await _seed_user(db_session, user_id="owner-mgr", email="owner-mgr@test.local", role="manager")
        owner_result = await bootstrap_owner_employee(
            db_session,
            _config(
                owner_user_id="owner-mgr",
                employee_name="Owner Formal Manager Test",
            ),
        )
        assert owner_result.success is True
        assert owner_result.employee_id is not None
        report = await _seed_employee(
            db_session,
            name="Direct Report",
            user_id="report-1",
            manager_employee_id=owner_result.employee_id,
            employee_type="productive",
        )
        peer = await _seed_employee(db_session, name="Same Dept Peer", user_id="peer-1")
        await _seed_request(db_session, employee_id=report.id, status="submitted")
        await _seed_request(db_session, employee_id=peer.id, status="submitted")
        return owner_result.employee_id, report.id, peer.id

    owner_emp_id, report_id, peer_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("owner-mgr", "manager"))
    try:
        team = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert team.status_code == 200, team.text
        ids = {row["employee_id"] for row in team.json()}
        assert report_id in ids, f"owner_emp={owner_emp_id} team={team.json()}"
        assert peer_id not in ids

        review = client.get("/api/v1/employee-requests/review")
        assert review.status_code == 200
        review_ids = {row["employee_id"] for row in review.json()}
        assert report_id in review_ids
        assert peer_id not in review_ids
    finally:
        _cleanup_overrides()


def test_resolve_database_url_missing_raises_clear_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr("core.config.load_backend_env", lambda: None)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        resolve_database_url()


def test_resolve_database_url_reads_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test-resolve-owner.db")
    assert resolve_database_url() == "sqlite+aiosqlite:///./test-resolve-owner.db"


def test_settings_database_url_attribute_error_when_env_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr("core.config.load_backend_env", lambda: None)
    with pytest.raises(AttributeError):
        _ = settings.database_url


@pytest.mark.asyncio
async def test_init_db_missing_database_url_raises_value_error_not_attribute_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr("core.config.load_backend_env", lambda: None)
    from core.database import DatabaseManager

    mgr = DatabaseManager()
    with pytest.raises(ValueError, match="DATABASE_URL"):
        await mgr.init_db()
