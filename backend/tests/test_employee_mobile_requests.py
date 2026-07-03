"""Security and behavior tests for employee-mobile self-only requests."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from models.employee_attendance_event import EmployeeAttendanceEvent
from models.employee_payment_record import EmployeePaymentRecord
from models.employee_request import EmployeeRequest
from models.employees import Employees
from schemas.auth import UserResponse
from services.employee_mobile_identity import resolve_employee_for_user
from sqlalchemy import func, select

from core.database import get_db
from dependencies.auth import get_current_user
from main import app


def _user(user_id: str, role: str = "employee_mobile") -> UserResponse:
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
    name: str = "Mobile Employee",
    status: str = "active",
) -> Employees:
    emp = Employees(
        name=name,
        status=status,
        employee_type="productive",
        user_id=user_id,
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _seed_request(
    db_session,
    *,
    employee_id: int,
    request_type: str = "leave",
    status: str = "submitted",
) -> EmployeeRequest:
    row = EmployeeRequest(
        employee_id=employee_id,
        request_type=request_type,
        status=status,
        title="Test request",
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


@pytest.fixture
def mobile_client(db_fixture, db_session):
    user_id = f"mobile-user-{uuid.uuid4().hex[:8]}"

    async def _setup():
        await _seed_employee(db_session, user_id=user_id, name="Linked Mobile")

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    yield client
    _cleanup_overrides()


@pytest.mark.asyncio
async def test_resolve_returns_active_employee(db_session):
    emp = await _seed_employee(db_session, user_id="resolver-user-1")
    resolved = await resolve_employee_for_user(db_session, _user("resolver-user-1"))
    assert resolved.id == emp.id
    assert resolved.status == "active"
    assert resolved.user_id == "resolver-user-1"


@pytest.mark.asyncio
async def test_resolve_no_link_403(db_session):
    with pytest.raises(HTTPException) as exc:
        await resolve_employee_for_user(db_session, _user("missing-link-user"))
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "employee_link_missing"


@pytest.mark.asyncio
async def test_resolve_inactive_employee_403(db_session):
    await _seed_employee(db_session, user_id="inactive-user", status="inactive")
    with pytest.raises(HTTPException) as exc:
        await resolve_employee_for_user(db_session, _user("inactive-user"))
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "employee_not_active"


@pytest.mark.asyncio
async def test_resolve_duplicate_links_409(db_session):
    await _seed_employee(db_session, user_id="dup-user", name="Dup A")
    await _seed_employee(db_session, user_id="dup-user", name="Dup B")
    with pytest.raises(HTTPException) as exc:
        await resolve_employee_for_user(db_session, _user("dup-user"))
    assert exc.value.status_code == 409
    assert exc.value.detail["error"] == "employee_link_ambiguous"


def test_employee_mobile_can_create_own_request(mobile_client):
    response = mobile_client.post(
        "/api/v1/employee-mobile/requests",
        json={
            "request_type": "leave",
            "title": "Concediu",
            "start_date": "2026-07-01",
            "end_date": "2026-07-05",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["request_type"] == "leave"
    assert body["status"] == "submitted"
    assert body["employee_id"] > 0


def test_create_stores_server_resolved_employee_id(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="store-id-user")
        return emp.id

    employee_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("store-id-user", "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/requests",
            json={
                "request_type": "day_off",
                "start_date": "2026-08-01",
            },
        )
        assert response.status_code == 201
        assert response.json()["employee_id"] == employee_id
    finally:
        _cleanup_overrides()


def test_client_sent_employee_id_rejected(mobile_client):
    response = mobile_client.post(
        "/api/v1/employee-mobile/requests",
        json={
            "employee_id": 99999,
            "request_type": "other",
            "title": "Should fail",
        },
    )
    assert response.status_code == 422


def test_unlinked_user_gets_403(db_fixture):
    client = _client_for(db_fixture, _user("unlinked-mobile-user", "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/requests")
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "employee_link_missing"
    finally:
        _cleanup_overrides()


def test_inactive_employee_denied(db_fixture, db_session):
    async def _setup():
        await _seed_employee(db_session, user_id="inactive-mobile", status="inactive")

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("inactive-mobile", "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/requests",
            json={"request_type": "other", "title": "Blocked"},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "employee_not_active"
    finally:
        _cleanup_overrides()


def test_duplicate_employee_links_returns_409_on_endpoint(db_fixture, db_session):
    async def _setup():
        await _seed_employee(db_session, user_id="dup-endpoint-user", name="A")
        await _seed_employee(db_session, user_id="dup-endpoint-user", name="B")

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("dup-endpoint-user", "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/requests")
        assert response.status_code == 409
        assert response.json()["detail"]["error"] == "employee_link_ambiguous"
    finally:
        _cleanup_overrides()


def test_list_returns_only_own_requests(db_fixture, db_session):
    async def _setup():
        emp_a = await _seed_employee(db_session, user_id="list-user-a", name="A")
        emp_b = await _seed_employee(db_session, user_id="list-user-b", name="B")
        await _seed_request(db_session, employee_id=emp_a.id, request_type="leave")
        await _seed_request(db_session, employee_id=emp_b.id, request_type="advance")

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("list-user-a", "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/requests")
        assert response.status_code == 200
        rows = response.json()
        assert len(rows) == 1
        assert rows[0]["request_type"] == "leave"
    finally:
        _cleanup_overrides()


def test_detail_cannot_access_other_employee_request(db_fixture, db_session):
    async def _setup():
        emp_a = await _seed_employee(db_session, user_id="detail-user-a", name="A")
        emp_b = await _seed_employee(db_session, user_id="detail-user-b", name="B")
        other = await _seed_request(db_session, employee_id=emp_b.id)
        return other.id

    other_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("detail-user-a", "employee_mobile"))
    try:
        response = client.get(f"/api/v1/employee-mobile/requests/{other_id}")
        assert response.status_code == 404
    finally:
        _cleanup_overrides()


def test_cancel_own_submitted_request(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="cancel-user")
        req = await _seed_request(db_session, employee_id=emp.id, status="submitted")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("cancel-user", "employee_mobile"))
    try:
        response = client.patch(f"/api/v1/employee-mobile/requests/{request_id}/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    finally:
        _cleanup_overrides()


def test_cancel_other_employee_request_denied(db_fixture, db_session):
    async def _setup():
        emp_a = await _seed_employee(db_session, user_id="cancel-a", name="A")
        emp_b = await _seed_employee(db_session, user_id="cancel-b", name="B")
        req = await _seed_request(db_session, employee_id=emp_b.id, status="submitted")
        return req.id, emp_a.id

    request_id, _ = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("cancel-a", "employee_mobile"))
    try:
        response = client.patch(f"/api/v1/employee-mobile/requests/{request_id}/cancel")
        assert response.status_code == 404
    finally:
        _cleanup_overrides()


def test_admin_without_employee_link_denied(db_fixture, db_session):
    async def _setup():
        await _seed_employee(db_session, user_id="admin-linked-only", name="Linked")

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-no-link", "admin"))
    try:
        response = client.get("/api/v1/employee-mobile/requests")
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "employee_link_missing"
    finally:
        _cleanup_overrides()


def test_manager_linked_can_create_and_list_own_request(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="manager-self-user", name="Manager Self")
        return emp.id

    employee_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-self-user", "manager"))
    try:
        create = client.post(
            "/api/v1/employee-mobile/requests",
            json={
                "request_type": "leave",
                "title": "Concediu manager",
                "start_date": "2026-09-01",
            },
        )
        assert create.status_code == 201
        assert create.json()["employee_id"] == employee_id

        listing = client.get("/api/v1/employee-mobile/requests")
        assert listing.status_code == 200
        rows = listing.json()
        assert len(rows) == 1
        assert rows[0]["title"] == "Concediu manager"
    finally:
        _cleanup_overrides()


def test_admin_linked_can_create_and_list_own_request(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="admin-self-user", name="Admin Self")
        return emp.id

    employee_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-self-user", "admin"))
    try:
        create = client.post(
            "/api/v1/employee-mobile/requests",
            json={"request_type": "other", "title": "Cerere admin"},
        )
        assert create.status_code == 201
        assert create.json()["employee_id"] == employee_id

        listing = client.get("/api/v1/employee-mobile/requests")
        assert listing.status_code == 200
        assert len(listing.json()) == 1
    finally:
        _cleanup_overrides()


def test_manager_unlinked_denied_self_app(db_fixture):
    client = _client_for(db_fixture, _user("manager-unlinked", "manager"))
    try:
        response = client.get("/api/v1/employee-mobile/requests")
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "employee_link_missing"
    finally:
        _cleanup_overrides()


@pytest.mark.parametrize("role", ["viewer", "operator", "sales"])
def test_non_mobile_roles_denied_even_when_linked(db_fixture, db_session, role):
    async def _setup():
        await _seed_employee(db_session, user_id=f"{role}-linked-user", name=role)

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(f"{role}-linked-user", role))
    try:
        response = client.get("/api/v1/employee-mobile/requests")
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "employee_self_role_required"
    finally:
        _cleanup_overrides()


def test_request_create_does_not_create_attendance_event(db_fixture, db_session):
    async def _setup():
        await _seed_employee(db_session, user_id="no-attendance-user")

    async def _events_count():
        async with db_fixture.session_maker() as session:
            result = await session.execute(select(func.count()).select_from(EmployeeAttendanceEvent))
            return result.scalar_one()

    db_fixture.run(_setup())
    before = db_fixture.run(_events_count())
    client = _client_for(db_fixture, _user("no-attendance-user", "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/requests",
            json={
                "request_type": "attendance_correction",
                "start_date": "2026-06-01",
                "title": "Corecție",
            },
        )
        assert response.status_code == 201
        after = db_fixture.run(_events_count())
        assert after == before
    finally:
        _cleanup_overrides()


def test_request_create_does_not_create_payment_record(db_fixture, db_session):
    async def _setup():
        await _seed_employee(db_session, user_id="no-payment-user")

    async def _payments_count():
        async with db_fixture.session_maker() as session:
            result = await session.execute(select(func.count()).select_from(EmployeePaymentRecord))
            return result.scalar_one()

    db_fixture.run(_setup())
    before = db_fixture.run(_payments_count())
    client = _client_for(db_fixture, _user("no-payment-user", "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/requests",
            json={
                "request_type": "advance",
                "amount": 500.0,
                "currency": "RON",
                "title": "Avans",
            },
        )
        assert response.status_code == 201
        after = db_fixture.run(_payments_count())
        assert after == before
    finally:
        _cleanup_overrides()


def test_employee_mobile_can_list_own_attendance(db_fixture, db_session):
    user_id = "mobile-attendance-user"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Self Attendance")
        other = await _seed_employee(db_session, user_id="other-attendance-user", name="Other")
        from services.employee_attendance_service import create_attendance_event

        await create_attendance_event(
            db_session,
            {
                "employee_id": emp.id,
                "start_date": "2026-06-10",
                "end_date": "2026-06-10",
                "event_type": "leave",
                "event_status": "confirmed",
            },
        )
        await create_attendance_event(
            db_session,
            {
                "employee_id": other.id,
                "start_date": "2026-06-11",
                "end_date": "2026-06-11",
                "event_type": "absent",
                "event_status": "confirmed",
            },
        )
        return emp.id

    emp_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.get(
            "/api/v1/employee-mobile/attendance",
            params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        )
        assert response.status_code == 200
        rows = response.json()
        assert len(rows) == 1
        assert rows[0]["employee_id"] == emp_id
        assert rows[0]["event_type"] == "leave"
    finally:
        _cleanup_overrides()


def test_self_attendance_rejects_client_employee_id(db_fixture, db_session):
    user_id = "mobile-attendance-reject-id"

    async def _setup():
        await _seed_employee(db_session, user_id=user_id)

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.get(
            "/api/v1/employee-mobile/attendance",
            params={"employee_id": 999},
        )
        assert response.status_code == 422
    finally:
        _cleanup_overrides()


def test_user_without_employee_link_cannot_self_read_attendance(db_fixture, db_session):
    client = _client_for(db_fixture, _user("no-link-attendance", "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/attendance")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_manager_with_employee_link_can_self_read_attendance(db_fixture, db_session):
    user_id = "manager-self-attendance"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Manager Self")
        from services.employee_attendance_service import create_attendance_event

        await create_attendance_event(
            db_session,
            {
                "employee_id": emp.id,
                "start_date": "2026-06-12",
                "end_date": "2026-06-12",
                "event_type": "partial",
                "event_status": "confirmed",
                "hours_override": 4,
            },
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "manager"))
    try:
        response = client.get(
            "/api/v1/employee-mobile/attendance",
            params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
    finally:
        _cleanup_overrides()
