"""Tests for event-based internal employee attendance (ranges + status)."""

from __future__ import annotations

from datetime import date

import pytest
from models.employees import Employees
from services.employee_attendance_service import (
    DEFAULT_WORK_HOURS_PER_DAY,
    count_standard_work_days,
    create_attendance_event,
    delete_attendance_event,
    get_attendance_month_summary,
    update_attendance_event,
    working_days_in_range,
)


async def _seed_active(db_session, name: str = "Andrei Goghi") -> Employees:
    emp = Employees(name=name, status="active", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


def _summary_row(summary: dict, employee_id: int) -> dict:
    return next(r for r in summary["employees"] if r["employee_id"] == employee_id)


@pytest.mark.asyncio
async def test_default_present_without_events(db_session):
    emp = await _seed_active(db_session)
    summary = await get_attendance_month_summary(db_session, 2026, 6)
    expected_days = count_standard_work_days(date(2026, 6, 1), date(2026, 6, 30))
    row = _summary_row(summary, emp.id)
    assert row["standard_work_days"] == expected_days
    assert row["total_hours"] == expected_days * DEFAULT_WORK_HOURS_PER_DAY
    assert row["present_days"] == expected_days
    assert row["event_count"] == 0


@pytest.mark.asyncio
async def test_leave_planned_range_five_workdays(db_session):
    emp = await _seed_active(db_session)
    # Mon 2026-06-15 .. Fri 2026-06-19
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-06-15",
            "end_date": "2026-06-19",
            "event_type": "leave",
            "event_status": "planned",
        },
    )
    row = _summary_row(await get_attendance_month_summary(db_session, 2026, 6), emp.id)
    assert row["leave_days"] == 5
    assert row["total_hours"] == row["standard_hours"] - 40
    assert row["planned_event_count"] == 1


@pytest.mark.asyncio
async def test_sick_confirmed_range_two_days(db_session):
    emp = await _seed_active(db_session)
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-06-02",
            "end_date": "2026-06-03",
            "event_type": "sick",
            "event_status": "confirmed",
            "notes": "Certificat medical",
        },
    )
    row = _summary_row(await get_attendance_month_summary(db_session, 2026, 6), emp.id)
    assert row["sick_days"] == 2
    assert row["total_hours"] == row["standard_hours"] - 16


@pytest.mark.asyncio
async def test_cancelled_leave_does_not_affect_summary(db_session):
    emp = await _seed_active(db_session)
    created = await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-06-08",
            "end_date": "2026-06-10",
            "event_type": "leave",
            "event_status": "planned",
        },
    )
    await update_attendance_event(
        db_session,
        created["id"],
        {"event_status": "cancelled"},
    )
    row = _summary_row(await get_attendance_month_summary(db_session, 2026, 6), emp.id)
    assert row["leave_days"] == 0
    assert row["total_hours"] == row["standard_hours"]
    assert row["cancelled_event_count"] == 1
    assert row["event_count"] == 0


@pytest.mark.asyncio
async def test_leave_range_skips_weekends(db_session):
    emp = await _seed_active(db_session)
    # Sat 2026-06-06 .. Mon 2026-06-08 — only Mon counts
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-06-06",
            "end_date": "2026-06-08",
            "event_type": "leave",
            "event_status": "approved",
        },
    )
    row = _summary_row(await get_attendance_month_summary(db_session, 2026, 6), emp.id)
    assert row["leave_days"] == 1
    assert row["total_hours"] == row["standard_hours"] - 8


@pytest.mark.asyncio
async def test_partial_single_day_hours_override(db_session):
    emp = await _seed_active(db_session)
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-06-02",
            "end_date": "2026-06-02",
            "event_type": "partial",
            "hours_override": 4,
        },
    )
    row = _summary_row(await get_attendance_month_summary(db_session, 2026, 6), emp.id)
    assert row["partial_days"] == 1
    assert row["total_hours"] == row["standard_hours"] - 4


@pytest.mark.asyncio
async def test_overtime_weekend_allowed(db_session):
    emp = await _seed_active(db_session)
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-06-06",
            "end_date": "2026-06-06",
            "event_type": "overtime",
            "hours_delta": 2,
        },
    )
    row = _summary_row(await get_attendance_month_summary(db_session, 2026, 6), emp.id)
    assert row["overtime_hours"] == 2
    assert row["total_hours"] == row["standard_hours"] + 2


@pytest.mark.asyncio
async def test_absent_and_leave_same_day_rejected(db_session):
    emp = await _seed_active(db_session)
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-06-11",
            "end_date": "2026-06-11",
            "event_type": "leave",
        },
    )
    with pytest.raises(ValueError, match="conflict"):
        await create_attendance_event(
            db_session,
            {
                "employee_id": emp.id,
                "start_date": "2026-06-11",
                "end_date": "2026-06-11",
                "event_type": "absent",
            },
        )


@pytest.mark.asyncio
async def test_partial_on_leave_day_rejected(db_session):
    emp = await _seed_active(db_session)
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-06-12",
            "end_date": "2026-06-12",
            "event_type": "leave",
        },
    )
    with pytest.raises(ValueError, match="partial"):
        await create_attendance_event(
            db_session,
            {
                "employee_id": emp.id,
                "start_date": "2026-06-12",
                "end_date": "2026-06-12",
                "event_type": "partial",
                "hours_override": 4,
            },
        )


@pytest.mark.asyncio
async def test_correction_without_notes_rejected(db_session):
    emp = await _seed_active(db_session)
    with pytest.raises(ValueError, match="notes"):
        await create_attendance_event(
            db_session,
            {
                "employee_id": emp.id,
                "start_date": "2026-06-14",
                "end_date": "2026-06-14",
                "event_type": "correction",
                "hours_delta": 1,
            },
        )


@pytest.mark.asyncio
async def test_start_date_after_end_date_rejected(db_session):
    emp = await _seed_active(db_session)
    with pytest.raises(ValueError, match="end_date"):
        await create_attendance_event(
            db_session,
            {
                "employee_id": emp.id,
                "start_date": "2026-06-20",
                "end_date": "2026-06-10",
                "event_type": "leave",
            },
        )


@pytest.mark.asyncio
async def test_delete_event_restores_standard_summary(db_session):
    emp = await _seed_active(db_session)
    created = await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-06-16",
            "end_date": "2026-06-16",
            "event_type": "absent",
        },
    )
    await delete_attendance_event(db_session, created["id"])
    row = _summary_row(await get_attendance_month_summary(db_session, 2026, 6), emp.id)
    assert row["absent_days"] == 0
    assert row["total_hours"] == row["standard_hours"]


@pytest.mark.asyncio
async def test_future_leave_in_month_affects_summary(db_session):
    emp = await _seed_active(db_session)
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-06-25",
            "end_date": "2026-06-26",
            "event_type": "leave",
            "event_status": "planned",
        },
    )
    row = _summary_row(await get_attendance_month_summary(db_session, 2026, 6), emp.id)
    assert row["leave_days"] == 2


@pytest.mark.asyncio
async def test_summary_api_returns_200(auth_client, db_session):
    emp = Employees(name="API Summary", status="active", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()

    resp = auth_client.get(
        "/api/v1/employee-attendance/summary",
        params={"year": 2026, "month": 6},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["standard_work_hours_per_day"] == 8
    assert any(row["employee_id"] == emp.id for row in body["employees"])


# --- Access control (admin/operator only) ---

from core.database import get_db
from dependencies.auth import get_current_user
from fastapi.testclient import TestClient
from main import app
from schemas.auth import UserResponse
from services.employee_attendance_service import create_attendance_event as svc_create_event


def _user(user_id: str, role: str) -> UserResponse:
    return UserResponse(
        id=user_id,
        email=f"{user_id}@workos.test",
        name=f"User {user_id}",
        role=role,
        last_login=None,
    )


def _client_for(db_fixture, user: UserResponse | None) -> TestClient:
    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    if user is not None:
        async def _override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = _override_get_current_user
    elif get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

    return TestClient(app, raise_server_exceptions=False)


def _cleanup_overrides():
    app.dependency_overrides.clear()


def _list_params():
    return {"start_date": "2026-06-01", "end_date": "2026-06-30"}


def _create_payload(employee_id: int) -> dict:
    return {
        "employee_id": employee_id,
        "start_date": "2026-06-10",
        "end_date": "2026-06-10",
        "event_type": "leave",
        "event_status": "confirmed",
    }


async def _seed_event(db_session, employee_id: int) -> dict:
    return await svc_create_event(
        db_session,
        {
            "employee_id": employee_id,
            "start_date": "2026-06-11",
            "end_date": "2026-06-11",
            "event_type": "absent",
            "event_status": "confirmed",
        },
    )


@pytest.mark.parametrize("role", ["viewer", "sales"])
def test_authenticated_non_operator_cannot_list_attendance(db_fixture, db_session, role):
    db_fixture.run(_seed_active(db_session))
    client = _client_for(db_fixture, _user(f"{role}-list", role))
    try:
        response = client.get("/api/v1/employee-attendance/events", params=_list_params())
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_unauthenticated_cannot_list_attendance(db_fixture, db_session):
    from fastapi import HTTPException

    db_fixture.run(_seed_active(db_session))

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _deny_current_user():
        raise HTTPException(status_code=401, detail="Authentication credentials were not provided")

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _deny_current_user
    client = TestClient(app, raise_server_exceptions=False)
    try:
        response = client.get("/api/v1/employee-attendance/events", params=_list_params())
        assert response.status_code == 401
    finally:
        _cleanup_overrides()


def test_employee_mobile_cannot_list_general_attendance(db_fixture, db_session):
    db_fixture.run(_seed_active(db_session))
    client = _client_for(db_fixture, _user("mobile-list", "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-attendance/events", params=_list_params())
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_manager_cannot_create_attendance_event(db_fixture, db_session):
    emp = db_fixture.run(_seed_active(db_session))
    client = _client_for(db_fixture, _user("manager-create", "manager"))
    try:
        response = client.post("/api/v1/employee-attendance/events", json=_create_payload(emp.id))
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_employee_mobile_cannot_create_attendance_event(db_fixture, db_session):
    emp = db_fixture.run(_seed_active(db_session))
    client = _client_for(db_fixture, _user("mobile-create", "employee_mobile"))
    try:
        response = client.post("/api/v1/employee-attendance/events", json=_create_payload(emp.id))
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_viewer_cannot_create_attendance_event(db_fixture, db_session):
    emp = db_fixture.run(_seed_active(db_session))
    client = _client_for(db_fixture, _user("viewer-create", "viewer"))
    try:
        response = client.post("/api/v1/employee-attendance/events", json=_create_payload(emp.id))
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_admin_can_list_attendance(db_fixture, db_session):
    db_fixture.run(_seed_active(db_session))
    client = _client_for(db_fixture, _user("admin-list", "admin"))
    try:
        response = client.get("/api/v1/employee-attendance/events", params=_list_params())
        assert response.status_code == 200
    finally:
        _cleanup_overrides()


def test_admin_can_create_attendance_event(db_fixture, db_session):
    emp = db_fixture.run(_seed_active(db_session))
    client = _client_for(db_fixture, _user("admin-create", "admin"))
    try:
        response = client.post("/api/v1/employee-attendance/events", json=_create_payload(emp.id))
        assert response.status_code == 200
    finally:
        _cleanup_overrides()


def test_operator_can_list_attendance(db_fixture, db_session):
    db_fixture.run(_seed_active(db_session))
    client = _client_for(db_fixture, _user("operator-list", "operator"))
    try:
        response = client.get("/api/v1/employee-attendance/events", params=_list_params())
        assert response.status_code == 200
    finally:
        _cleanup_overrides()


def test_operator_can_create_attendance_event(db_fixture, db_session):
    emp = db_fixture.run(_seed_active(db_session))
    client = _client_for(db_fixture, _user("operator-create", "operator"))
    try:
        response = client.post("/api/v1/employee-attendance/events", json=_create_payload(emp.id))
        assert response.status_code == 200
    finally:
        _cleanup_overrides()


def test_manager_cannot_update_attendance_event(db_fixture, db_session):
    async def _setup():
        emp = await _seed_active(db_session)
        created = await _seed_event(db_session, emp.id)
        return created["id"]

    event_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-update", "manager"))
    try:
        response = client.put(
            f"/api/v1/employee-attendance/events/{event_id}",
            json={"notes": "blocked"},
        )
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_employee_mobile_cannot_update_attendance_event(db_fixture, db_session):
    async def _setup():
        emp = await _seed_active(db_session)
        created = await _seed_event(db_session, emp.id)
        return created["id"]

    event_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mobile-update", "employee_mobile"))
    try:
        response = client.put(
            f"/api/v1/employee-attendance/events/{event_id}",
            json={"notes": "blocked"},
        )
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_admin_can_update_attendance_event(db_fixture, db_session):
    async def _setup():
        emp = await _seed_active(db_session)
        created = await _seed_event(db_session, emp.id)
        return created["id"]

    event_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-update", "admin"))
    try:
        response = client.put(
            f"/api/v1/employee-attendance/events/{event_id}",
            json={"notes": "admin edit"},
        )
        assert response.status_code == 200
        assert response.json()["notes"] == "admin edit"
    finally:
        _cleanup_overrides()


def test_operator_can_update_attendance_event(db_fixture, db_session):
    async def _setup():
        emp = await _seed_active(db_session)
        created = await _seed_event(db_session, emp.id)
        return created["id"]

    event_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("operator-update", "operator"))
    try:
        response = client.put(
            f"/api/v1/employee-attendance/events/{event_id}",
            json={"notes": "operator edit"},
        )
        assert response.status_code == 200
    finally:
        _cleanup_overrides()


def test_manager_cannot_delete_attendance_event(db_fixture, db_session):
    async def _setup():
        emp = await _seed_active(db_session)
        created = await _seed_event(db_session, emp.id)
        return created["id"]

    event_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-delete", "manager"))
    try:
        response = client.delete(f"/api/v1/employee-attendance/events/{event_id}")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_employee_mobile_cannot_delete_attendance_event(db_fixture, db_session):
    async def _setup():
        emp = await _seed_active(db_session)
        created = await _seed_event(db_session, emp.id)
        return created["id"]

    event_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mobile-delete", "employee_mobile"))
    try:
        response = client.delete(f"/api/v1/employee-attendance/events/{event_id}")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_admin_can_delete_attendance_event(db_fixture, db_session):
    async def _setup():
        emp = await _seed_active(db_session)
        created = await _seed_event(db_session, emp.id)
        return created["id"]

    event_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-delete", "admin"))
    try:
        response = client.delete(f"/api/v1/employee-attendance/events/{event_id}")
        assert response.status_code == 204
    finally:
        _cleanup_overrides()


def test_operator_can_delete_attendance_event(db_fixture, db_session):
    async def _setup():
        emp = await _seed_active(db_session)
        created = await _seed_event(db_session, emp.id)
        return created["id"]

    event_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("operator-delete", "operator"))
    try:
        response = client.delete(f"/api/v1/employee-attendance/events/{event_id}")
        assert response.status_code == 204
    finally:
        _cleanup_overrides()
