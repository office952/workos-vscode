"""Direct reports assignment via manager_employee_id — idempotent, no side effects."""

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
from services.employee_direct_reports_assignment_service import (
    DirectReportsAssignmentConfig,
    assign_direct_reports,
    load_direct_reports_config_from_env,
)
from services.owner_employee_bootstrap_service import (
    OwnerBootstrapConfig,
    check_owner_mobile_readiness,
)
from sqlalchemy import func, select

from core.database import get_db
from core.config import resolve_database_url
from dependencies.auth import get_current_user
from main import app


async def _seed_user(db_session, *, user_id: str, email: str, role: str = "manager") -> User:
    user = User(id=user_id, email=email, name=f"User {user_id}", role=role)
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
    department: str | None = None,
    cost_lunar_firma: float | None = None,
) -> Employees:
    emp = Employees(
        name=name,
        status=status,
        employee_type="productive",
        user_id=user_id,
        manager_employee_id=manager_employee_id,
        department=department,
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
        title="Report request",
        start_date=date(2026, 6, 10),
        end_date=date(2026, 6, 12),
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


def _cfg(**kwargs) -> DirectReportsAssignmentConfig:
    defaults = {
        "manager_employee_id": kwargs.pop("manager_employee_id", None),
        "direct_report_employee_ids": kwargs.pop("direct_report_employee_ids", ()),
        "dry_run": False,
        "force_reassign": False,
    }
    defaults.update(kwargs)
    return DirectReportsAssignmentConfig(**defaults)


@pytest.mark.asyncio
async def test_assigns_direct_report_to_manager(db_session):
    mgr = await _seed_employee(db_session, name="Owner Manager", user_id="mgr-1")
    report = await _seed_employee(db_session, name="Direct One", user_id="rep-1")
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(report.id,)),
    )
    assert result.success is True
    assert len(result.assigned) == 1
    await db_session.refresh(report)
    assert report.manager_employee_id == mgr.id


@pytest.mark.asyncio
async def test_dry_run_does_not_persist(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Dry", user_id="mgr-dry")
    report = await _seed_employee(db_session, name="Rep Dry", user_id="rep-dry")
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(report.id,), dry_run=True),
    )
    assert result.success is True
    assert result.dry_run is True
    await db_session.refresh(report)
    assert report.manager_employee_id is None


@pytest.mark.asyncio
async def test_idempotent_when_already_assigned(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Idem", user_id="mgr-idem")
    report = await _seed_employee(
        db_session,
        name="Rep Idem",
        user_id="rep-idem",
        manager_employee_id=mgr.id,
    )
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(report.id,)),
    )
    assert result.success is True
    assert len(result.already_assigned) == 1
    assert len(result.assigned) == 0


@pytest.mark.asyncio
async def test_refuses_self_assignment(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Self", user_id="mgr-self")
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(mgr.id,)),
    )
    assert result.success is False
    assert any(s.get("reason") == "cannot_assign_self" for s in result.skipped)


@pytest.mark.asyncio
async def test_refuses_missing_manager(db_session):
    report = await _seed_employee(db_session, name="Rep Only", user_id="rep-only")
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=99999, direct_report_employee_ids=(report.id,)),
    )
    assert result.success is False
    assert result.error == "manager_employee_not_found"


@pytest.mark.asyncio
async def test_refuses_missing_direct_report(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Missing", user_id="mgr-missing")
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(88888,)),
    )
    assert result.success is False
    assert result.error == "no_direct_reports_resolved"


@pytest.mark.asyncio
async def test_refuses_inactive_manager(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Inactive", user_id="mgr-inact", status="inactive")
    report = await _seed_employee(db_session, name="Rep Inact", user_id="rep-inact")
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(report.id,)),
    )
    assert result.success is False
    assert result.error == "manager_employee_inactive"


@pytest.mark.asyncio
async def test_refuses_inactive_direct_report(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Active", user_id="mgr-act")
    report = await _seed_employee(db_session, name="Rep Inactive", user_id="rep-inactive", status="inactive")
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(report.id,)),
    )
    assert result.success is False
    assert any(s.get("reason") == "direct_report_inactive" for s in result.skipped)


@pytest.mark.asyncio
async def test_refuses_ambiguous_name_match(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Ambig", user_id="mgr-ambig")
    await _seed_employee(db_session, name="Same Name")
    await _seed_employee(db_session, name="Same Name")
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_names=("Same Name",)),
    )
    assert result.success is False
    assert any(s.get("reason") == "ambiguous_employee_name_match" for s in result.skipped)


@pytest.mark.asyncio
async def test_refuses_overwrite_existing_manager_by_default(db_session):
    mgr = await _seed_employee(db_session, name="Mgr A", user_id="mgr-a")
    other = await _seed_employee(db_session, name="Other Mgr", user_id="mgr-other")
    report = await _seed_employee(
        db_session,
        name="Rep Conflict",
        user_id="rep-conflict",
        manager_employee_id=other.id,
    )
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(report.id,)),
    )
    assert len(result.conflicts) == 1
    await db_session.refresh(report)
    assert report.manager_employee_id == other.id


@pytest.mark.asyncio
async def test_allows_overwrite_with_force_flag(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Force", user_id="mgr-force")
    other = await _seed_employee(db_session, name="Other Force", user_id="mgr-other-force")
    report = await _seed_employee(
        db_session,
        name="Rep Force",
        user_id="rep-force",
        manager_employee_id=other.id,
    )
    result = await assign_direct_reports(
        db_session,
        _cfg(
            manager_employee_id=mgr.id,
            direct_report_employee_ids=(report.id,),
            force_reassign=True,
        ),
    )
    assert result.success is True
    assert len(result.assigned) == 1
    await db_session.refresh(report)
    assert report.manager_employee_id == mgr.id


@pytest.mark.asyncio
async def test_does_not_use_department_as_fallback(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Dept", user_id="mgr-dept", department="Management")
    target = await _seed_employee(db_session, name="Target Dept", user_id="target-dept", department="Management")
    peer = await _seed_employee(db_session, name="Peer Dept", user_id="peer-dept", department="Management")
    result = await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(target.id,)),
    )
    assert result.success is True
    await db_session.refresh(target)
    await db_session.refresh(peer)
    assert target.manager_employee_id == mgr.id
    assert peer.manager_employee_id is None


@pytest.mark.asyncio
async def test_does_not_create_attendance_or_requests(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Side", user_id="mgr-side-assign")
    report = await _seed_employee(db_session, name="Rep Side", user_id="rep-side-assign")
    att_before = await db_session.execute(select(func.count()).select_from(EmployeeAttendanceEvent))
    req_before = await db_session.execute(select(func.count()).select_from(EmployeeRequest))
    pay_before = await db_session.execute(select(func.count()).select_from(EmployeePaymentRecord))
    await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(report.id,)),
    )
    att_after = await db_session.execute(select(func.count()).select_from(EmployeeAttendanceEvent))
    req_after = await db_session.execute(select(func.count()).select_from(EmployeeRequest))
    pay_after = await db_session.execute(select(func.count()).select_from(EmployeePaymentRecord))
    assert int(att_after.scalar_one()) == int(att_before.scalar_one())
    assert int(req_after.scalar_one()) == int(req_before.scalar_one())
    assert int(pay_after.scalar_one()) == int(pay_before.scalar_one())


@pytest.mark.asyncio
async def test_does_not_touch_payroll_fields(db_session):
    mgr = await _seed_employee(db_session, name="Mgr Pay", user_id="mgr-pay")
    report = await _seed_employee(
        db_session,
        name="Rep Pay",
        user_id="rep-pay",
        cost_lunar_firma=5000.0,
    )
    before_cost = report.cost_lunar_firma
    await assign_direct_reports(
        db_session,
        _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(report.id,)),
    )
    await db_session.refresh(report)
    assert report.cost_lunar_firma == before_cost


@pytest.mark.asyncio
async def test_assign_by_manager_user_email(db_session):
    await _seed_user(db_session, user_id="mgr-email", email="mgr@test.local")
    mgr = await _seed_employee(db_session, name="Mgr Email", user_id="mgr-email")
    report = await _seed_employee(db_session, name="Rep Email", user_id="rep-email")
    result = await assign_direct_reports(
        db_session,
        _cfg(
            manager_user_email="mgr@test.local",
            direct_report_employee_ids=(report.id,),
        ),
    )
    assert result.success is True
    await db_session.refresh(report)
    assert report.manager_employee_id == mgr.id


@pytest.mark.asyncio
async def test_readiness_reports_direct_reports_count(db_session):
    await _seed_user(db_session, user_id="owner-readiness", email="owner-read@test.local", role="admin")
    mgr = await _seed_employee(db_session, name="Owner Read", user_id="owner-readiness")
    await _seed_employee(db_session, name="Rep Read", user_id="rep-read", manager_employee_id=mgr.id)
    readiness = await check_owner_mobile_readiness(
        db_session,
        OwnerBootstrapConfig(
            owner_user_id="owner-readiness",
            employee_name="Owner Read",
        ),
    )
    assert readiness.direct_reports_count == 1
    assert readiness.team["active_direct_reports_count"] == 1


@pytest.mark.asyncio
async def test_readiness_warns_when_zero_direct_reports(db_session):
    await _seed_user(db_session, user_id="owner-zero", email="owner-zero@test.local", role="admin")
    await _seed_employee(db_session, name="Owner Zero", user_id="owner-zero")
    readiness = await check_owner_mobile_readiness(
        db_session,
        OwnerBootstrapConfig(
            owner_user_id="owner-zero",
            employee_name="Owner Zero",
        ),
    )
    assert readiness.status == "WARN"
    assert "no_direct_reports_assigned" in readiness.team["warnings"]


def _user(user_id: str, role: str) -> UserResponse:
    return UserResponse(
        id=user_id,
        email=f"{user_id}@workos.test",
        name="Manager",
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


def test_manager_sees_assigned_direct_report_in_team_service(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(db_session, name="Mgr Team", user_id="mgr-team-assign")
        report = await _seed_employee(db_session, name="Rep Team", user_id="rep-team-assign")
        await assign_direct_reports(
            db_session,
            _cfg(manager_employee_id=mgr.id, direct_report_employee_ids=(report.id,)),
        )
        outsider = await _seed_employee(db_session, name="Outsider Team", user_id="outsider-team")
        await _seed_request(db_session, employee_id=report.id)
        await _seed_request(db_session, employee_id=outsider.id)
        return report.id, outsider.id

    report_id, outsider_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-team-assign", "manager"))
    try:
        team = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert team.status_code == 200
        ids = {row["employee_id"] for row in team.json()}
        assert report_id in ids
        assert outsider_id not in ids
    finally:
        _cleanup_overrides()


def test_load_config_from_env_parses_csv(monkeypatch):
    monkeypatch.setenv("WORKOS_OWNER_EMPLOYEE_ID", "42")
    monkeypatch.setenv("WORKOS_DIRECT_REPORT_EMPLOYEE_IDS", "1, 2 ,3")
    monkeypatch.setenv("WORKOS_DIRECT_REPORTS_DRY_RUN", "1")
    cfg = load_direct_reports_config_from_env()
    assert cfg.manager_employee_id == 42
    assert cfg.direct_report_employee_ids == [1, 2, 3]
    assert cfg.dry_run is True


def test_assign_script_db_config_accepts_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test-assign-config.db")
    assert resolve_database_url() == "sqlite+aiosqlite:///./test-assign-config.db"


def test_assign_script_db_config_missing_url_clear_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr("core.config.load_backend_env", lambda: None)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        resolve_database_url()
