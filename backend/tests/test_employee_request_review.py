"""Manager/admin employee request review — no side effects."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from models.employee_attendance_event import EmployeeAttendanceEvent
from models.employee_payment_record import EmployeePaymentRecord
from models.employee_request import EmployeeRequest
from models.employees import Employees
from schemas.auth import UserResponse
from sqlalchemy import func, select

from core.database import get_db
from dependencies.auth import get_current_user
from main import app


def _user(user_id: str, role: str) -> UserResponse:
    return UserResponse(
        id=user_id,
        email=f"{user_id}@workos.test",
        name=f"User {user_id}",
        role=role,
        last_login=None,
    )


async def _seed_employee(
    db_session,
    *,
    user_id: str | None,
    name: str = "Employee",
    status: str = "active",
    department: str | None = None,
    manager_employee_id: int | None = None,
) -> Employees:
    emp = Employees(
        name=name,
        status=status,
        employee_type="productive",
        user_id=user_id,
        department=department,
        manager_employee_id=manager_employee_id,
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _seed_manager_with_direct_report(
    db_session,
    *,
    manager_user_id: str,
    worker_user_id: str,
    manager_name: str = "Manager",
    worker_name: str = "Worker",
) -> tuple[Employees, Employees]:
    mgr = await _seed_employee(
        db_session,
        user_id=manager_user_id,
        name=manager_name,
    )
    worker = await _seed_employee(
        db_session,
        user_id=worker_user_id,
        name=worker_name,
        manager_employee_id=mgr.id,
    )
    return mgr, worker


async def _seed_request(
    db_session,
    *,
    employee_id: int,
    request_type: str = "leave",
    status: str = "submitted",
    title: str = "Review request",
) -> EmployeeRequest:
    row = EmployeeRequest(
        employee_id=employee_id,
        request_type=request_type,
        status=status,
        title=title,
        start_date=date(2026, 6, 10),
        end_date=date(2026, 6, 12),
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


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


def test_manager_can_list_submitted_requests(db_fixture, db_session):
    async def _setup():
        mgr, emp = await _seed_manager_with_direct_report(
            db_session,
            manager_user_id="manager-reviewer",
            worker_user_id="worker-1",
            worker_name="Worker One",
        )
        await _seed_request(db_session, employee_id=emp.id, status="submitted")
        await _seed_request(db_session, employee_id=emp.id, status="approved", title="Old")

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-reviewer", "manager"))
    try:
        response = client.get("/api/v1/employee-requests/review")
        assert response.status_code == 200
        rows = response.json()
        worker_rows = [r for r in rows if r["employee_name"] == "Worker One" and r["status"] == "submitted"]
        assert len(worker_rows) == 1
        assert worker_rows[0]["status"] == "submitted"
        assert worker_rows[0]["employee_name"] == "Worker One"
        assert "cost_lunar_firma" not in rows[0]
        assert "monthly_internal_pay_amount" not in rows[0]
    finally:
        _cleanup_overrides()


def test_admin_can_list_submitted_requests(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="worker-2", name="Worker Two")
        await _seed_request(db_session, employee_id=emp.id)

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-reviewer", "admin"))
    try:
        response = client.get("/api/v1/employee-requests/review")
        assert response.status_code == 200
        rows = response.json()
        worker_rows = [r for r in rows if r["employee_name"] == "Worker Two" and r["status"] == "submitted"]
        assert len(worker_rows) == 1
    finally:
        _cleanup_overrides()


@pytest.mark.parametrize("role", ["employee_mobile", "viewer", "operator", "sales"])
def test_non_reviewers_denied_review_list(db_fixture, db_session, role):
    async def _setup():
        emp = await _seed_employee(db_session, user_id=f"{role}-worker", name=role)
        await _seed_request(db_session, employee_id=emp.id)

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(f"{role}-reviewer", role))
    try:
        response = client.get("/api/v1/employee-requests/review")
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "employee_request_reviewer_required"
    finally:
        _cleanup_overrides()


def test_manager_can_approve_submitted_request(db_fixture, db_session):
    async def _setup():
        mgr, emp = await _seed_manager_with_direct_report(
            db_session,
            manager_user_id="manager-approve",
            worker_user_id="approve-worker",
            worker_name="Approve Me",
        )
        req = await _seed_request(db_session, employee_id=emp.id)
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-approve", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/approve",
            json={"review_note": "OK"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "approved"
        assert body["review_note"] == "OK"
        assert body["reviewed_by_user_id"] == "manager-approve"
        assert body["reviewed_at"] is not None
    finally:
        _cleanup_overrides()


def test_manager_can_reject_submitted_request(db_fixture, db_session):
    async def _setup():
        mgr, emp = await _seed_manager_with_direct_report(
            db_session,
            manager_user_id="manager-reject",
            worker_user_id="reject-worker",
            worker_name="Reject Me",
        )
        req = await _seed_request(db_session, employee_id=emp.id)
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-reject", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/reject",
            json={"review_note": "Not now"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "rejected"
        assert body["review_note"] == "Not now"
    finally:
        _cleanup_overrides()


def test_approving_already_approved_returns_409(db_fixture, db_session):
    async def _setup():
        mgr, emp = await _seed_manager_with_direct_report(
            db_session,
            manager_user_id="manager-conflict",
            worker_user_id="already-approved-worker",
        )
        req = await _seed_request(db_session, employee_id=emp.id, status="approved")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-conflict", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/approve",
            json={},
        )
        assert response.status_code == 409
        assert response.json()["detail"]["error"] == "request_not_reviewable"
    finally:
        _cleanup_overrides()


def test_rejecting_cancelled_returns_409(db_fixture, db_session):
    async def _setup():
        mgr, emp = await _seed_manager_with_direct_report(
            db_session,
            manager_user_id="manager-cancelled",
            worker_user_id="cancelled-worker",
        )
        req = await _seed_request(db_session, employee_id=emp.id, status="cancelled")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-cancelled", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/reject",
            json={},
        )
        assert response.status_code == 409
    finally:
        _cleanup_overrides()


def test_approving_draft_returns_422(db_fixture, db_session):
    async def _setup():
        mgr, emp = await _seed_manager_with_direct_report(
            db_session,
            manager_user_id="manager-draft",
            worker_user_id="draft-worker",
        )
        req = await _seed_request(db_session, employee_id=emp.id, status="draft")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-draft", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/approve",
            json={},
        )
        assert response.status_code == 422
    finally:
        _cleanup_overrides()


def test_manager_cannot_approve_own_request(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="manager-own", name="Manager Own")
        req = await _seed_request(db_session, employee_id=emp.id, title="My leave")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-own", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/approve",
            json={},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "self_review_forbidden"
    finally:
        _cleanup_overrides()


def test_admin_cannot_approve_own_request_when_linked(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="admin-own", name="Admin Own")
        req = await _seed_request(db_session, employee_id=emp.id)
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-own", "admin"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/approve",
            json={},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "self_review_forbidden"
    finally:
        _cleanup_overrides()


def test_manager_cannot_approve_own_request_when_inactive_link(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(
            db_session,
            user_id="manager-inactive",
            name="Manager Inactive Link",
            status="inactive",
        )
        req = await _seed_request(db_session, employee_id=emp.id, title="Inactive link leave")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-inactive", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/approve",
            json={},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "self_review_forbidden"
    finally:
        _cleanup_overrides()


def test_manager_can_use_self_app_and_review_others(db_fixture, db_session):
    async def _setup():
        manager_emp = await _seed_employee(db_session, user_id="dual-manager", name="Dual Manager")
        other_emp = await _seed_employee(
            db_session,
            user_id="dual-worker",
            name="Dual Worker",
            manager_employee_id=manager_emp.id,
        )
        other_req = await _seed_request(db_session, employee_id=other_emp.id, title="Other leave")
        return other_req.id, manager_emp.id

    other_id, manager_emp_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("dual-manager", "manager"))
    try:
        own = client.post(
            "/api/v1/employee-mobile/requests",
            json={"request_type": "day_off", "title": "My day off", "start_date": "2026-10-01"},
        )
        assert own.status_code == 201
        assert own.json()["employee_id"] == manager_emp_id

        approve = client.patch(
            f"/api/v1/employee-requests/review/{other_id}/approve",
            json={"review_note": "Approved other"},
        )
        assert approve.status_code == 200
        assert approve.json()["employee_name"] == "Dual Worker"
    finally:
        _cleanup_overrides()


def test_approve_does_not_create_attendance_event(db_fixture, db_session):
    async def _setup():
        mgr, emp = await _seed_manager_with_direct_report(
            db_session,
            manager_user_id="manager-no-attendance",
            worker_user_id="attendance-worker",
        )
        req = await _seed_request(
            db_session,
            employee_id=emp.id,
            request_type="attendance_correction",
        )
        return req.id

    async def _events_count():
        async with db_fixture.session_maker() as session:
            result = await session.execute(select(func.count()).select_from(EmployeeAttendanceEvent))
            return result.scalar_one()

    request_id = db_fixture.run(_setup())
    before = db_fixture.run(_events_count())
    client = _client_for(db_fixture, _user("manager-no-attendance", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/approve",
            json={},
        )
        assert response.status_code == 200
        after = db_fixture.run(_events_count())
        assert after == before
    finally:
        _cleanup_overrides()


def test_approve_does_not_create_payment_record(db_fixture, db_session):
    async def _setup():
        mgr, emp = await _seed_manager_with_direct_report(
            db_session,
            manager_user_id="manager-no-payment",
            worker_user_id="payment-worker",
        )
        req = await _seed_request(db_session, employee_id=emp.id, request_type="advance")
        return req.id

    async def _payments_count():
        async with db_fixture.session_maker() as session:
            result = await session.execute(select(func.count()).select_from(EmployeePaymentRecord))
            return result.scalar_one()

    request_id = db_fixture.run(_setup())
    before = db_fixture.run(_payments_count())
    client = _client_for(db_fixture, _user("manager-no-payment", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/approve",
            json={},
        )
        assert response.status_code == 200
        after = db_fixture.run(_payments_count())
        assert after == before
    finally:
        _cleanup_overrides()


def test_reject_does_not_create_side_effects(db_fixture, db_session):
    async def _setup():
        mgr, emp = await _seed_manager_with_direct_report(
            db_session,
            manager_user_id="manager-reject-side",
            worker_user_id="reject-side-effect-worker",
        )
        req = await _seed_request(db_session, employee_id=emp.id, request_type="advance")
        return req.id

    async def _events_count():
        async with db_fixture.session_maker() as session:
            result = await session.execute(select(func.count()).select_from(EmployeeAttendanceEvent))
            return result.scalar_one()

    async def _payments_count():
        async with db_fixture.session_maker() as session:
            result = await session.execute(select(func.count()).select_from(EmployeePaymentRecord))
            return result.scalar_one()

    request_id = db_fixture.run(_setup())
    events_before = db_fixture.run(_events_count())
    payments_before = db_fixture.run(_payments_count())
    client = _client_for(db_fixture, _user("manager-reject-side", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/reject",
            json={"review_note": "No"},
        )
        assert response.status_code == 200
        assert db_fixture.run(_events_count()) == events_before
        assert db_fixture.run(_payments_count()) == payments_before
    finally:
        _cleanup_overrides()


def test_review_detail_returns_safe_fields(db_fixture, db_session):
    async def _setup():
        mgr, emp = await _seed_manager_with_direct_report(
            db_session,
            manager_user_id="manager-detail",
            worker_user_id="detail-worker",
            worker_name="Detail Worker",
        )
        emp.cost_lunar_firma = 99999.0
        emp.monthly_internal_pay_amount = 5000.0
        await db_session.commit()
        req = await _seed_request(db_session, employee_id=emp.id)
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-detail", "manager"))
    try:
        response = client.get(f"/api/v1/employee-requests/review/{request_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["employee_name"] == "Detail Worker"
        assert "cost_lunar_firma" not in body
        assert "monthly_internal_pay_amount" not in body
        assert "salary" not in body
    finally:
        _cleanup_overrides()


def test_manager_review_list_excludes_same_department_non_report(db_fixture, db_session):
    dept = "Review-Dept-Iso"

    async def _setup():
        mgr = await _seed_employee(
            db_session,
            user_id="mgr-review-scope",
            name="Mgr Review",
            department=dept,
        )
        direct = await _seed_employee(
            db_session,
            user_id="direct-review",
            name="Direct Review",
            department=dept,
            manager_employee_id=mgr.id,
        )
        peer = await _seed_employee(
            db_session,
            user_id="peer-review",
            name="Peer Review",
            department=dept,
        )
        await _seed_request(db_session, employee_id=direct.id, title="Direct in scope")
        await _seed_request(db_session, employee_id=peer.id, title="Peer out scope")
        return direct.id

    direct_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-review-scope", "manager"))
    try:
        response = client.get("/api/v1/employee-requests/review")
        assert response.status_code == 200
        scoped = [r for r in response.json() if r["title"] in ("Direct in scope", "Peer out scope")]
        assert len(scoped) == 1
        assert scoped[0]["employee_id"] == direct_id
    finally:
        _cleanup_overrides()


def test_manager_cannot_detail_outside_scope_request(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(db_session, user_id="mgr-detail-scope", name="Mgr Detail")
        outsider = await _seed_employee(db_session, user_id="outsider-detail", name="Outsider")
        req = await _seed_request(db_session, employee_id=outsider.id, title="Outside")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-detail-scope", "manager"))
    try:
        response = client.get(f"/api/v1/employee-requests/review/{request_id}")
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "team_scope_violation"
    finally:
        _cleanup_overrides()


def test_manager_cannot_approve_outside_scope_request(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(db_session, user_id="mgr-approve-scope", name="Mgr Approve")
        outsider = await _seed_employee(db_session, user_id="outsider-approve", name="Outsider Approve")
        req = await _seed_request(db_session, employee_id=outsider.id, title="Outside approve")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-approve-scope", "manager"))
    try:
        response = client.patch(
            f"/api/v1/employee-requests/review/{request_id}/approve",
            json={},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "team_scope_violation"
    finally:
        _cleanup_overrides()


def test_manager_without_direct_reports_gets_empty_review_list(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(db_session, user_id="mgr-empty-review", name="Mgr Empty")
        outsider = await _seed_employee(db_session, user_id="outsider-empty-review", name="Outsider Empty")
        await _seed_request(db_session, employee_id=outsider.id, title="Not mine")

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-empty-review", "manager"))
    try:
        response = client.get("/api/v1/employee-requests/review")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        _cleanup_overrides()
