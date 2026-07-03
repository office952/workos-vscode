"""Manager team read-only workspace — permissions, isolation, no writes."""

from __future__ import annotations

from datetime import date

import pytest
from models.employee_attendance_event import EmployeeAttendanceEvent
from models.employee_request import EmployeeRequest
from models.employees import Employees
from schemas.auth import UserResponse
from services.employee_attendance_service import create_attendance_event
from sqlalchemy import func, select

from core.database import get_db
from dependencies.auth import get_current_user
from fastapi.testclient import TestClient
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
    department: str | None = None,
    status: str = "active",
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


async def _seed_request(
    db_session,
    *,
    employee_id: int,
    request_type: str = "leave",
    status: str = "submitted",
    title: str = "Team request",
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


TEAM_DEPT = "Productie-A"


# --- Permissions ---


def test_manager_can_read_team_attendance(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(
            db_session,
            user_id="mgr-team-att",
            name="Manager Att",
            department=TEAM_DEPT,
        )
        worker = await _seed_employee(
            db_session,
            user_id="worker-team-att",
            name="Worker Att",
            department=TEAM_DEPT,
            manager_employee_id=mgr.id,
        )
        await create_attendance_event(
            db_session,
            {
                "employee_id": worker.id,
                "start_date": "2026-06-10",
                "end_date": "2026-06-10",
                "event_type": "leave",
                "event_status": "approved",
            },
        )
        return worker.id

    worker_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-team-att", "manager"))
    try:
        response = client.get(
            "/api/v1/employee-mobile/manager/team-attendance",
            params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        )
        assert response.status_code == 200
        rows = response.json()
        assert len(rows) == 1
        assert rows[0]["employee_id"] == worker_id
        assert rows[0]["employee_name"] == "Worker Att"
    finally:
        _cleanup_overrides()


def test_manager_can_read_team_requests(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(
            db_session,
            user_id="mgr-team-req",
            name="Manager Req",
            department=TEAM_DEPT,
        )
        worker = await _seed_employee(
            db_session,
            user_id="worker-team-req",
            name="Worker Req",
            department=TEAM_DEPT,
            manager_employee_id=mgr.id,
        )
        await _seed_request(db_session, employee_id=worker.id, title="Leave team")
        return worker.id

    worker_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-team-req", "manager"))
    try:
        response = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert response.status_code == 200
        rows = response.json()
        assert len(rows) == 1
        assert rows[0]["employee_id"] == worker_id
        assert rows[0]["title"] == "Leave team"
    finally:
        _cleanup_overrides()


def test_employee_mobile_cannot_read_team_attendance(db_fixture):
    client = _client_for(db_fixture, _user("emp-mobile-team-att", "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/manager/team-attendance")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_employee_mobile_cannot_read_team_requests(db_fixture):
    client = _client_for(db_fixture, _user("emp-mobile-team-req", "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_basic_user_cannot_read_team_endpoints(db_fixture):
    client = _client_for(db_fixture, _user("viewer-team", "viewer"))
    try:
        att = client.get("/api/v1/employee-mobile/manager/team-attendance")
        req = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert att.status_code == 403
        assert req.status_code == 403
    finally:
        _cleanup_overrides()


def test_admin_can_read_all_team_attendance(db_fixture, db_session):
    async def _setup():
        worker = await _seed_employee(
            db_session,
            user_id="worker-admin-att",
            name="Worker Admin",
            department="Other",
        )
        await create_attendance_event(
            db_session,
            {
                "employee_id": worker.id,
                "start_date": "2026-06-05",
                "end_date": "2026-06-05",
                "event_type": "sick",
                "event_status": "confirmed",
            },
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-team-att", "admin"))
    try:
        response = client.get(
            "/api/v1/employee-mobile/manager/team-attendance",
            params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1
    finally:
        _cleanup_overrides()


def test_operator_cannot_read_team_requests(db_fixture):
    client = _client_for(db_fixture, _user("operator-team", "operator"))
    try:
        response = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


# --- Data isolation ---


def test_manager_sees_only_direct_report_team_attendance(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(
            db_session,
            user_id="mgr-iso-att",
            name="Manager Iso",
            department=TEAM_DEPT,
        )
        direct = await _seed_employee(
            db_session,
            user_id="direct-att",
            name="Direct Report",
            department=TEAM_DEPT,
            manager_employee_id=mgr.id,
        )
        same_dept_peer = await _seed_employee(
            db_session,
            user_id="peer-att",
            name="Same Dept Peer",
            department=TEAM_DEPT,
        )
        other_mgr = await _seed_employee(
            db_session,
            user_id="other-mgr-att",
            name="Other Manager",
            department="Magazie",
        )
        other_report = await _seed_employee(
            db_session,
            user_id="other-report-att",
            name="Other Report",
            department=TEAM_DEPT,
            manager_employee_id=other_mgr.id,
        )
        for emp in (direct, same_dept_peer, other_report):
            await create_attendance_event(
                db_session,
                {
                    "employee_id": emp.id,
                    "start_date": "2026-06-11",
                    "end_date": "2026-06-11",
                    "event_type": "leave",
                    "event_status": "approved",
                },
            )
        return direct.id, same_dept_peer.id, other_report.id

    direct_id, peer_id, other_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-iso-att", "manager"))
    try:
        response = client.get(
            "/api/v1/employee-mobile/manager/team-attendance",
            params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        )
        assert response.status_code == 200
        ids = {row["employee_id"] for row in response.json()}
        assert direct_id in ids
        assert peer_id not in ids
        assert other_id not in ids
    finally:
        _cleanup_overrides()


def test_manager_cannot_filter_attendance_outside_team(db_fixture, db_session):
    async def _setup():
        await _seed_employee(
            db_session,
            user_id="mgr-filter-att",
            name="Manager Filter",
            department=TEAM_DEPT,
        )
        outsider = await _seed_employee(
            db_session,
            user_id="outsider-att",
            name="Outsider",
            department="Magazie",
        )
        return outsider.id

    outsider_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-filter-att", "manager"))
    try:
        response = client.get(
            "/api/v1/employee-mobile/manager/team-attendance",
            params={"employee_id": outsider_id},
        )
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_manager_sees_only_direct_report_team_requests(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(
            db_session,
            user_id="mgr-iso-req",
            name="Manager Iso Req",
            department=TEAM_DEPT,
        )
        direct = await _seed_employee(
            db_session,
            user_id="direct-req",
            name="Direct Req",
            department=TEAM_DEPT,
            manager_employee_id=mgr.id,
        )
        same_dept_peer = await _seed_employee(
            db_session,
            user_id="peer-req",
            name="Peer Req",
            department=TEAM_DEPT,
        )
        await _seed_request(db_session, employee_id=direct.id, title="Direct scope")
        await _seed_request(db_session, employee_id=same_dept_peer.id, title="Peer out scope")
        return direct.id

    direct_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-iso-req", "manager"))
    try:
        response = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert response.status_code == 200
        rows = [r for r in response.json() if r["title"] in ("Direct scope", "Peer out scope")]
        assert len(rows) == 1
        assert rows[0]["employee_id"] == direct_id
    finally:
        _cleanup_overrides()


def test_manager_cannot_filter_requests_outside_team(db_fixture, db_session):
    async def _setup():
        await _seed_employee(
            db_session,
            user_id="mgr-filter-req",
            name="Manager Filter Req",
            department=TEAM_DEPT,
        )
        outsider = await _seed_employee(
            db_session,
            user_id="outsider-req",
            name="Outsider Req",
            department="Magazie",
        )
        await _seed_request(db_session, employee_id=outsider.id)
        return outsider.id

    outsider_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-filter-req", "manager"))
    try:
        response = client.get(
            "/api/v1/employee-mobile/manager/team-requests",
            params={"employee_id": outsider_id},
        )
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_admin_employee_id_filter_works(db_fixture, db_session):
    async def _setup():
        worker = await _seed_employee(
            db_session,
            user_id="admin-filter-worker",
            name="Admin Filter Worker",
            department="X",
        )
        await _seed_request(db_session, employee_id=worker.id, title="Admin scoped")
        return worker.id

    worker_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-filter", "admin"))
    try:
        response = client.get(
            "/api/v1/employee-mobile/manager/team-requests",
            params={"employee_id": worker_id},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["employee_id"] == worker_id
    finally:
        _cleanup_overrides()


def test_manager_without_direct_reports_gets_empty_team(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(
            db_session,
            user_id="mgr-no-reports",
            name="Manager No Reports",
            department=TEAM_DEPT,
        )
        worker = await _seed_employee(
            db_session,
            user_id="worker-no-reports",
            name="Worker",
            department=TEAM_DEPT,
        )
        await _seed_request(db_session, employee_id=worker.id)

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-no-reports", "manager"))
    try:
        att = client.get("/api/v1/employee-mobile/manager/team-attendance")
        req = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert att.status_code == 200
        assert req.status_code == 200
        assert att.json() == []
        assert req.json() == []
    finally:
        _cleanup_overrides()


# --- Read-only ---


def test_team_attendance_endpoint_creates_no_events(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(
            db_session,
            user_id="mgr-ro-att",
            name="Manager RO",
            department=TEAM_DEPT,
        )
        worker = await _seed_employee(
            db_session,
            user_id="worker-ro-att",
            name="Worker RO",
            department=TEAM_DEPT,
            manager_employee_id=mgr.id,
        )
        await create_attendance_event(
            db_session,
            {
                "employee_id": worker.id,
                "start_date": "2026-06-12",
                "end_date": "2026-06-12",
                "event_type": "leave",
                "event_status": "approved",
            },
        )

        async def _count():
            result = await db_session.execute(
                select(func.count()).select_from(EmployeeAttendanceEvent)
            )
            return int(result.scalar_one())

        return _count

    count_fn = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-ro-att", "manager"))
    try:
        before = db_fixture.run(count_fn())
        response = client.get("/api/v1/employee-mobile/manager/team-attendance")
        assert response.status_code == 200
        after = db_fixture.run(count_fn())
        assert after == before
    finally:
        _cleanup_overrides()


def test_team_requests_endpoint_is_read_only_list(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(
            db_session,
            user_id="mgr-ro-req",
            name="Manager RO Req",
            department=TEAM_DEPT,
        )
        worker = await _seed_employee(
            db_session,
            user_id="worker-ro-req",
            name="Worker RO Req",
            department=TEAM_DEPT,
            manager_employee_id=mgr.id,
        )
        req = await _seed_request(db_session, employee_id=worker.id, status="submitted")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-ro-req", "manager"))
    try:
        list_resp = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert list_resp.status_code == 200
        assert list_resp.json()[0]["status"] == "submitted"

        async def _status():
            row = await db_session.get(EmployeeRequest, request_id)
            return row.status

        status_before = db_fixture.run(_status())
        second = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert second.status_code == 200
        status_after = db_fixture.run(_status())
        assert status_after == status_before == "submitted"
    finally:
        _cleanup_overrides()


def test_manager_still_cannot_crud_attendance(db_fixture):
    client = _client_for(db_fixture, _user("mgr-crud", "manager"))
    try:
        response = client.post(
            "/api/v1/employee-attendance/events",
            json={
                "employee_id": 1,
                "start_date": "2026-06-01",
                "end_date": "2026-06-01",
                "event_type": "leave",
            },
        )
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_manager_still_cannot_generate_effects(db_fixture, db_session):
    async def _setup():
        worker = await _seed_employee(db_session, user_id="worker-gen-block")
        req = await _seed_request(db_session, employee_id=worker.id, status="approved")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-gen-block", "manager"))
    try:
        response = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


# --- Formal manager reporting link ---


def test_employee_can_have_manager_employee_id(db_fixture, db_session):
    async def _setup():
        mgr = await _seed_employee(db_session, user_id="mgr-model", name="Mgr Model")
        worker = await _seed_employee(
            db_session,
            user_id="worker-model",
            name="Worker Model",
            manager_employee_id=mgr.id,
        )
        return mgr.id, worker.manager_employee_id

    mgr_id, link = db_fixture.run(_setup())
    assert link == mgr_id


def test_employee_can_have_null_manager_employee_id(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="solo-model", name="Solo")
        return emp.manager_employee_id

    assert db_fixture.run(_setup()) is None


def test_validate_blocks_self_manager_assignment():
    from services.employee_manager_team_service import validate_manager_employee_id_assignment

    with pytest.raises(ValueError, match="cannot be their own manager"):
        validate_manager_employee_id_assignment(5, 5)


def test_department_does_not_determine_team_scope(db_fixture, db_session):
    dept = "Shared-Dept-Only"

    async def _setup():
        mgr = await _seed_employee(
            db_session,
            user_id="mgr-dept-scope",
            name="Mgr Dept",
            department=dept,
        )
        peer = await _seed_employee(
            db_session,
            user_id="peer-dept-scope",
            name="Peer Dept",
            department=dept,
        )
        await _seed_request(db_session, employee_id=peer.id, title="Dept peer only")
        return peer.id

    peer_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mgr-dept-scope", "manager"))
    try:
        response = client.get("/api/v1/employee-mobile/manager/team-requests")
        assert response.status_code == 200
        ids = {row["employee_id"] for row in response.json()}
        assert peer_id not in ids
    finally:
        _cleanup_overrides()
