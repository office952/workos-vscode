"""Attendance request effects foundation — idempotent pending/conflict, no auto-apply."""

from __future__ import annotations

from datetime import date

import pytest
from models.attendance_request_effect import AttendanceRequestEffect
from models.employee_attendance_event import EmployeeAttendanceEvent
from models.employee_payment_record import EmployeePaymentRecord
from models.employee_request import EmployeeRequest
from models.employees import Employees
from services.attendance_request_effect_service import (
    ATTENDANCE_CAPABLE_REQUEST_TYPES,
    ATTENDANCE_EFFECT_SOURCE_PREFIX,
    CONFLICT_CORRECTION_PAYLOAD,
    CONFLICT_TIME_OFF_HOURS,
    EFFECT_STATUSES,
    apply_attendance_request_effect,
    cancel_attendance_effect_for_request,
    generate_attendance_effect_for_request,
    get_attendance_effect_for_request,
)
from services.employee_attendance_service import create_attendance_event
from sqlalchemy import func, select

from core.database import get_db
from dependencies.auth import get_current_user
from fastapi.testclient import TestClient
from main import app
from schemas.auth import UserResponse


async def _seed_employee(db_session, name: str = "Effect Worker", user_id: str = "effect-worker") -> Employees:
    emp = Employees(name=name, status="active", employee_type="productive", user_id=user_id)
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _seed_request(
    db_session,
    *,
    employee_id: int,
    request_type: str = "leave",
    status: str = "approved",
    start_date: date | None = date(2026, 7, 1),
    end_date: date | None = date(2026, 7, 3),
    title: str | None = None,
) -> EmployeeRequest:
    row = EmployeeRequest(
        employee_id=employee_id,
        request_type=request_type,
        status=status,
        title=title or f"{request_type} request",
        start_date=start_date,
        end_date=end_date,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _effects_count(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(AttendanceRequestEffect))
    return int(result.scalar_one())


async def _attendance_events_count(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(EmployeeAttendanceEvent))
    return int(result.scalar_one())


async def _payments_count(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(EmployeePaymentRecord))
    return int(result.scalar_one())


def _user(user_id: str, role: str) -> UserResponse:
    return UserResponse(
        id=user_id,
        email=f"{user_id}@workos.test",
        name=f"User {user_id}",
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


async def _events_for_effect_source(db_session, effect_id: int) -> list[EmployeeAttendanceEvent]:
    source = f"{ATTENDANCE_EFFECT_SOURCE_PREFIX}{effect_id}"
    result = await db_session.execute(
        select(EmployeeAttendanceEvent).where(EmployeeAttendanceEvent.source == source)
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_approved_leave_creates_pending_effect(db_session):
    emp = await _seed_employee(db_session)
    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    before = await _effects_count(db_session)

    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")

    assert effect is not None
    assert await _effects_count(db_session) == before + 1
    assert effect.status == "pending"
    assert effect.effect_type == "leave_range"
    assert effect.employee_request_id == req.id
    assert effect.employee_id == emp.id
    assert effect.date_start == date(2026, 7, 1)
    assert effect.date_end == date(2026, 7, 3)


@pytest.mark.asyncio
async def test_repeated_generation_returns_same_effect(db_session):
    emp = await _seed_employee(db_session, name="Repeat Worker")
    req = await _seed_request(db_session, employee_id=emp.id, title="repeat-leave")
    first = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    second = await generate_attendance_effect_for_request(db_session, req, "other-user")

    assert second is not None
    assert second.id == first.id
    stored = await get_attendance_effect_for_request(db_session, req.id)
    assert stored is not None
    assert stored.id == first.id


@pytest.mark.asyncio
async def test_approved_day_off_creates_pending_effect(db_session):
    emp = await _seed_employee(db_session)
    req = await _seed_request(
        db_session,
        employee_id=emp.id,
        request_type="day_off",
        start_date=date(2026, 7, 10),
        end_date=date(2026, 7, 10),
    )
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")

    assert effect is not None
    assert effect.status == "pending"
    assert effect.effect_type == "day_off"


@pytest.mark.asyncio
@pytest.mark.parametrize("request_type", ["advance", "equipment", "issue_report", "other"])
async def test_non_attendance_types_create_no_effect(db_session, request_type: str):
    emp = await _seed_employee(db_session)
    req = await _seed_request(db_session, employee_id=emp.id, request_type=request_type)
    before = await _effects_count(db_session)

    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")

    assert effect is None
    assert await _effects_count(db_session) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["rejected", "submitted"])
async def test_non_approved_request_raises(db_session, status: str):
    emp = await _seed_employee(db_session, name=f"NoGen {status}")
    req = await _seed_request(db_session, employee_id=emp.id, status=status)

    with pytest.raises(ValueError, match="Only approved"):
        await generate_attendance_effect_for_request(db_session, req, "generator-user")

    assert await get_attendance_effect_for_request(db_session, req.id) is None


@pytest.mark.asyncio
async def test_existing_attendance_event_creates_conflict_effect(db_session):
    emp = await _seed_employee(db_session)
    attendance_before = await _attendance_events_count(db_session)
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-07-02",
            "end_date": "2026-07-02",
            "event_type": "leave",
            "event_status": "confirmed",
        },
    )
    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")

    assert effect is not None
    assert effect.status == "conflict"
    assert effect.conflict_reason is not None
    assert "attendance_event_overlap" in effect.conflict_reason
    assert await _attendance_events_count(db_session) == attendance_before + 1


@pytest.mark.asyncio
async def test_conflict_does_not_modify_existing_attendance_event(db_session):
    emp = await _seed_employee(db_session)
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-07-02",
            "end_date": "2026-07-02",
            "event_type": "sick",
            "event_status": "confirmed",
            "notes": "Original sick note",
        },
    )
    before = await _attendance_events_count(db_session)
    result = await db_session.execute(select(EmployeeAttendanceEvent))
    original = result.scalars().first()
    assert original is not None
    original_notes = original.notes

    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    await generate_attendance_effect_for_request(db_session, req, "generator-user")

    after_row = await db_session.get(EmployeeAttendanceEvent, original.id)
    assert after_row is not None
    assert after_row.notes == original_notes
    assert await _attendance_events_count(db_session) == before


@pytest.mark.asyncio
async def test_time_off_without_hours_creates_conflict_effect(db_session):
    emp = await _seed_employee(db_session)
    req = await _seed_request(
        db_session,
        employee_id=emp.id,
        request_type="time_off",
        start_date=date(2026, 7, 5),
        end_date=date(2026, 7, 5),
    )
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")

    assert effect is not None
    assert effect.status == "conflict"
    assert effect.conflict_reason == CONFLICT_TIME_OFF_HOURS
    assert effect.effect_type == "partial_time_off"


@pytest.mark.asyncio
async def test_attendance_correction_without_payload_creates_conflict_effect(db_session):
    emp = await _seed_employee(db_session)
    req = await _seed_request(
        db_session,
        employee_id=emp.id,
        request_type="attendance_correction",
        start_date=date(2026, 7, 6),
        end_date=date(2026, 7, 6),
    )
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")

    assert effect is not None
    assert effect.status == "conflict"
    assert effect.conflict_reason == CONFLICT_CORRECTION_PAYLOAD


@pytest.mark.asyncio
async def test_effect_stores_audit_fields(db_session):
    emp = await _seed_employee(db_session)
    req = await _seed_request(db_session, employee_id=emp.id)
    effect = await generate_attendance_effect_for_request(db_session, req, "audit-generator")

    assert effect is not None
    assert effect.employee_request_id == req.id
    assert effect.employee_id == emp.id
    assert effect.generated_by_user_id == "audit-generator"
    assert effect.generated_at is not None
    assert effect.status in EFFECT_STATUSES
    assert effect.request_type in ATTENDANCE_CAPABLE_REQUEST_TYPES


@pytest.mark.asyncio
async def test_generation_creates_no_payment_records(db_session):
    emp = await _seed_employee(db_session)
    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    payments_before = await _payments_count(db_session)
    attendance_before = await _attendance_events_count(db_session)

    await generate_attendance_effect_for_request(db_session, req, "generator-user")

    assert await _payments_count(db_session) == payments_before
    assert await _attendance_events_count(db_session) == attendance_before


@pytest.mark.asyncio
async def test_cancel_marks_pending_effect_cancelled(db_session):
    emp = await _seed_employee(db_session)
    req = await _seed_request(db_session, employee_id=emp.id)
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None
    assert effect.status == "pending"

    cancelled = await cancel_attendance_effect_for_request(
        db_session,
        req.id,
        reason="Request cancelled after approval",
    )

    assert cancelled is not None
    assert cancelled.status == "cancelled"
    assert cancelled.notes == "Request cancelled after approval"
    stored = await get_attendance_effect_for_request(db_session, req.id)
    assert stored is not None
    assert stored.status == "cancelled"


@pytest.mark.asyncio
async def test_service_has_no_costengine_import():
    import services.attendance_request_effect_service as module

    source = module.__file__
    assert source is not None
    with open(source, encoding="utf-8") as handle:
        text = handle.read()
    assert "CostEngine" not in text
    assert "cost_engine" not in text


@pytest.mark.asyncio
async def test_apply_leave_creates_attendance_event(db_session):
    emp = await _seed_employee(db_session, name="Apply Leave Worker")
    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None
    before = await _attendance_events_count(db_session)

    result = await apply_attendance_request_effect(db_session, effect.id, "admin-applier")

    assert result["already_applied"] is False
    assert result["effect"]["status"] == "applied"
    assert result["effect"]["applied_by_user_id"] == "admin-applier"
    assert result["effect"]["applied_at"] is not None
    assert await _attendance_events_count(db_session) == before + 1
    events = await _events_for_effect_source(db_session, effect.id)
    assert len(events) == 1
    assert events[0].event_type == "leave"
    assert events[0].start_date == date(2026, 7, 1)
    assert events[0].end_date == date(2026, 7, 3)


@pytest.mark.asyncio
async def test_apply_day_off_creates_attendance_event(db_session):
    emp = await _seed_employee(db_session, name="Apply Day Off Worker")
    req = await _seed_request(
        db_session,
        employee_id=emp.id,
        request_type="day_off",
        start_date=date(2026, 8, 4),
        end_date=date(2026, 8, 4),
    )
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None

    result = await apply_attendance_request_effect(db_session, effect.id, "admin-applier")

    events = await _events_for_effect_source(db_session, effect.id)
    assert len(events) == 1
    assert events[0].event_type == "leave"
    assert events[0].start_date == date(2026, 8, 4)


@pytest.mark.asyncio
async def test_apply_rejects_when_request_not_approved(db_session):
    emp = await _seed_employee(db_session, name="Not Approved Apply")
    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None
    req.status = "submitted"
    await db_session.commit()

    with pytest.raises(ValueError, match="apply_conflict: request must be approved"):
        await apply_attendance_request_effect(db_session, effect.id, "admin-applier")


@pytest.mark.asyncio
async def test_apply_rejects_rejected_request(db_session):
    emp = await _seed_employee(db_session, name="Rejected Apply")
    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None
    req.status = "rejected"
    await db_session.commit()

    with pytest.raises(ValueError, match="apply_conflict"):
        await apply_attendance_request_effect(db_session, effect.id, "admin-applier")


@pytest.mark.asyncio
async def test_apply_rejects_cancelled_effect(db_session):
    emp = await _seed_employee(db_session, name="Cancelled Effect Apply")
    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None
    await cancel_attendance_effect_for_request(db_session, req.id, reason="cancelled")

    with pytest.raises(ValueError, match="cancelled effect cannot be applied"):
        await apply_attendance_request_effect(db_session, effect.id, "admin-applier")


@pytest.mark.asyncio
async def test_apply_conflict_blocks_without_creating_event(db_session):
    emp = await _seed_employee(db_session, name="Apply Conflict Worker")
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-07-02",
            "end_date": "2026-07-02",
            "event_type": "sick",
            "event_status": "confirmed",
        },
    )
    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None
    effect.status = "pending"
    effect.conflict_reason = None
    await db_session.commit()
    before = await _attendance_events_count(db_session)

    with pytest.raises(ValueError, match="apply_conflict"):
        await apply_attendance_request_effect(db_session, effect.id, "admin-applier")

    assert await _attendance_events_count(db_session) == before
    refreshed = await get_attendance_effect_for_request(db_session, req.id)
    assert refreshed is not None
    assert refreshed.status == "conflict"


@pytest.mark.asyncio
async def test_apply_is_idempotent(db_session):
    emp = await _seed_employee(db_session, name="Idempotent Apply Worker")
    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None

    first = await apply_attendance_request_effect(db_session, effect.id, "admin-applier")
    second = await apply_attendance_request_effect(db_session, effect.id, "admin-applier")

    assert first["attendance_event_id"] == second["attendance_event_id"]
    assert second["already_applied"] is True
    events = await _events_for_effect_source(db_session, effect.id)
    assert len(events) == 1


@pytest.mark.asyncio
async def test_apply_unsupported_time_off_returns_422(db_session):
    emp = await _seed_employee(db_session, name="Time Off Apply")
    req = await _seed_request(
        db_session,
        employee_id=emp.id,
        request_type="time_off",
        start_date=date(2026, 7, 8),
        end_date=date(2026, 7, 8),
    )
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None
    before = await _attendance_events_count(db_session)

    with pytest.raises(ValueError, match="apply_unsupported: time_off"):
        await apply_attendance_request_effect(db_session, effect.id, "admin-applier")

    assert await _attendance_events_count(db_session) == before


@pytest.mark.asyncio
async def test_apply_unsupported_attendance_correction_returns_422(db_session):
    emp = await _seed_employee(db_session, name="Correction Apply")
    req = await _seed_request(
        db_session,
        employee_id=emp.id,
        request_type="attendance_correction",
        start_date=date(2026, 7, 9),
        end_date=date(2026, 7, 9),
    )
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None
    before = await _attendance_events_count(db_session)

    with pytest.raises(ValueError, match="apply_unsupported: attendance_correction"):
        await apply_attendance_request_effect(db_session, effect.id, "admin-applier")

    assert await _attendance_events_count(db_session) == before


@pytest.mark.asyncio
async def test_apply_does_not_create_payment_records(db_session):
    emp = await _seed_employee(db_session, name="Apply No Payment")
    req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
    effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
    assert effect is not None
    payments_before = await _payments_count(db_session)

    await apply_attendance_request_effect(db_session, effect.id, "admin-applier")

    assert await _payments_count(db_session) == payments_before


def test_employee_mobile_cannot_apply_effect_endpoint(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="mobile-worker", name="Mobile Worker")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
        assert effect is not None
        return effect.id

    effect_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mobile-worker", "employee_mobile"))
    try:
        response = client.post(f"/api/v1/employee-attendance/effects/{effect_id}/apply")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_manager_cannot_apply_effect_endpoint(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="worker-for-manager", name="Worker")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
        assert effect is not None
        return effect.id

    effect_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-applier", "manager"))
    try:
        response = client.post(f"/api/v1/employee-attendance/effects/{effect_id}/apply")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_admin_can_apply_effect_endpoint(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="worker-for-admin", name="Worker Admin Apply")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
        assert effect is not None
        return effect.id, emp.id

    effect_id, employee_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-applier", "admin"))
    try:
        response = client.post(f"/api/v1/employee-attendance/effects/{effect_id}/apply")
        assert response.status_code == 200
        body = response.json()
        assert body["effect_id"] == effect_id
        assert body["employee_id"] == employee_id
        assert body["effect_status"] == "applied"
        assert body["already_applied"] is False
        assert isinstance(body["attendance_event_id"], int)
    finally:
        _cleanup_overrides()


def test_operator_can_apply_effect_endpoint(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="worker-for-operator", name="Worker Operator Apply")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
        assert effect is not None
        return effect.id, emp.id

    effect_id, employee_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("operator-applier", "operator"))
    try:
        response = client.post(f"/api/v1/employee-attendance/effects/{effect_id}/apply")
        assert response.status_code == 200
        body = response.json()
        assert body["effect_id"] == effect_id
        assert body["employee_id"] == employee_id
        assert body["effect_status"] == "applied"
        assert body["already_applied"] is False
        assert isinstance(body["attendance_event_id"], int)
    finally:
        _cleanup_overrides()


def test_admin_apply_endpoint_is_idempotent(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="worker-idempotent", name="Worker Idempotent")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
        assert effect is not None
        return effect.id

    effect_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-idempotent", "admin"))
    try:
        first = client.post(f"/api/v1/employee-attendance/effects/{effect_id}/apply")
        assert first.status_code == 200
        assert first.json()["already_applied"] is False
        event_id = first.json()["attendance_event_id"]

        second = client.post(f"/api/v1/employee-attendance/effects/{effect_id}/apply")
        assert second.status_code == 200
        body = second.json()
        assert body["already_applied"] is True
        assert body["attendance_event_id"] == event_id
        assert body["effect_status"] == "applied"
    finally:
        _cleanup_overrides()


def test_admin_apply_endpoint_conflict_returns_409(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="worker-conflict", name="Conflict Worker")
        await create_attendance_event(
            db_session,
            {
                "employee_id": emp.id,
                "start_date": "2026-07-02",
                "end_date": "2026-07-02",
                "event_type": "sick",
                "event_status": "confirmed",
            },
        )
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
        assert effect is not None
        effect.status = "pending"
        effect.conflict_reason = None
        await db_session.commit()
        return effect.id

    effect_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-conflict", "admin"))
    try:
        response = client.post(f"/api/v1/employee-attendance/effects/{effect_id}/apply")
        assert response.status_code == 409
    finally:
        _cleanup_overrides()


def test_admin_can_list_attendance_effects(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="effects-list-worker")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
        assert effect is not None
        return effect.id

    effect_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-effects-list", "admin"))
    try:
        response = client.get("/api/v1/employee-attendance/effects")
        assert response.status_code == 200
        rows = response.json()
        assert any(row["id"] == effect_id for row in rows)
    finally:
        _cleanup_overrides()


def test_operator_can_list_attendance_effects(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="effects-operator-worker")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        await generate_attendance_effect_for_request(db_session, req, "generator-user")

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("operator-effects-list", "operator"))
    try:
        response = client.get("/api/v1/employee-attendance/effects", params={"status": "pending"})
        assert response.status_code == 200
        assert all(row["status"] == "pending" for row in response.json())
    finally:
        _cleanup_overrides()


def test_manager_cannot_list_attendance_effects(db_fixture, db_session):
    client = _client_for(db_fixture, _user("manager-effects-list", "manager"))
    try:
        response = client.get("/api/v1/employee-attendance/effects")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_employee_mobile_cannot_list_attendance_effects(db_fixture, db_session):
    client = _client_for(db_fixture, _user("mobile-effects-list", "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-attendance/effects")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_viewer_cannot_list_attendance_effects(db_fixture, db_session):
    client = _client_for(db_fixture, _user("viewer-effects-list", "viewer"))
    try:
        response = client.get("/api/v1/employee-attendance/effects")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_admin_can_get_attendance_effect_detail(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="effects-detail-worker")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        effect = await generate_attendance_effect_for_request(db_session, req, "generator-user")
        assert effect is not None
        return effect.id

    effect_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-effects-detail", "admin"))
    try:
        response = client.get(f"/api/v1/employee-attendance/effects/{effect_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == effect_id
        assert body["status"] == "pending"
    finally:
        _cleanup_overrides()


def test_admin_get_missing_effect_returns_404(db_fixture, db_session):
    client = _client_for(db_fixture, _user("admin-effects-missing", "admin"))
    try:
        response = client.get("/api/v1/employee-attendance/effects/999999")
        assert response.status_code == 404
    finally:
        _cleanup_overrides()


# --- HTTP generation endpoints ---


def test_admin_can_generate_effect_endpoint(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="gen-endpoint-worker")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-gen", "admin"))
    try:
        async def _event_count():
            return await _attendance_events_count(db_session)

        before_events = db_fixture.run(_event_count())
        response = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["employee_request_id"] == request_id
        assert body["status"] in ("pending", "conflict")
        assert body["already_exists"] is False
        after_events = db_fixture.run(_event_count())
        assert after_events == before_events
    finally:
        _cleanup_overrides()


def test_operator_can_generate_effect_endpoint(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="gen-operator-worker")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="day_off")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("operator-gen", "operator"))
    try:
        response = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert response.status_code == 201
        assert response.json()["already_exists"] is False
    finally:
        _cleanup_overrides()


def test_manager_cannot_generate_effect_endpoint(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="gen-manager-worker")
        req = await _seed_request(db_session, employee_id=emp.id)
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("manager-gen", "manager"))
    try:
        response = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_employee_mobile_cannot_generate_effect_endpoint(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="gen-mobile-worker")
        req = await _seed_request(db_session, employee_id=emp.id)
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("mobile-gen", "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_generate_endpoint_is_idempotent(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="gen-idempotent-worker")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-gen-idem", "admin"))
    try:
        first = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert first.status_code == 201
        effect_id = first.json()["id"]

        second = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert second.status_code == 200
        assert second.json()["id"] == effect_id
        assert second.json()["already_exists"] is True

        async def _count_for_request():
            result = await db_session.execute(
                select(func.count())
                .select_from(AttendanceRequestEffect)
                .where(AttendanceRequestEffect.employee_request_id == request_id)
            )
            return int(result.scalar_one())

        count = db_fixture.run(_count_for_request())
        assert count == 1
    finally:
        _cleanup_overrides()


def test_generate_not_approved_returns_422(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="gen-submitted-worker")
        req = await _seed_request(
            db_session,
            employee_id=emp.id,
            status="submitted",
        )
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-gen-submitted", "admin"))
    try:
        response = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert response.status_code == 422
    finally:
        _cleanup_overrides()


def test_generate_skipped_type_returns_422(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="gen-advance-worker")
        req = await _seed_request(
            db_session,
            employee_id=emp.id,
            request_type="advance",
        )
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-gen-advance", "admin"))
    try:
        response = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert response.status_code == 422
    finally:
        _cleanup_overrides()


def test_generate_missing_request_returns_404(db_fixture, db_session):
    client = _client_for(db_fixture, _user("admin-gen-missing", "admin"))
    try:
        response = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": 999999},
        )
        assert response.status_code == 404
    finally:
        _cleanup_overrides()


def test_generate_does_not_change_request_status(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="gen-status-worker")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-gen-status", "admin"))
    try:
        response = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert response.status_code == 201

        async def _check_status():
            result = await db_session.execute(
                select(EmployeeRequest.status).where(EmployeeRequest.id == request_id)
            )
            return result.scalar_one()

        assert db_fixture.run(_check_status()) == "approved"
    finally:
        _cleanup_overrides()


def test_generate_time_off_creates_conflict_effect(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="gen-timeoff-worker")
        req = await _seed_request(
            db_session,
            employee_id=emp.id,
            request_type="time_off",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 1),
        )
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-gen-timeoff", "admin"))
    try:
        response = client.post(
            "/api/v1/employee-attendance/effects/generate",
            json={"employee_request_id": request_id},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "conflict"
        assert CONFLICT_TIME_OFF_HOURS in (response.json().get("conflict_reason") or "")
    finally:
        _cleanup_overrides()


def test_admin_can_list_generation_candidates(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="cand-worker", name="Candidate Worker")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-cand", "admin"))
    try:
        response = client.get("/api/v1/employee-attendance/effects/generation-candidates")
        assert response.status_code == 200
        rows = response.json()
        assert any(row["employee_request_id"] == request_id for row in rows)
        match = next(row for row in rows if row["employee_request_id"] == request_id)
        assert match["has_effect"] is False
        assert match["employee_name"] == "Candidate Worker"
    finally:
        _cleanup_overrides()


def test_manager_cannot_list_generation_candidates(db_fixture, db_session):
    client = _client_for(db_fixture, _user("manager-cand", "manager"))
    try:
        response = client.get("/api/v1/employee-attendance/effects/generation-candidates")
        assert response.status_code == 403
    finally:
        _cleanup_overrides()


def test_candidate_with_existing_effect_excluded_by_default(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="cand-has-effect")
        req = await _seed_request(db_session, employee_id=emp.id, request_type="leave")
        await generate_attendance_effect_for_request(db_session, req, "seed-user")
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-cand-exclude", "admin"))
    try:
        response = client.get("/api/v1/employee-attendance/effects/generation-candidates")
        assert response.status_code == 200
        assert all(row["employee_request_id"] != request_id for row in response.json())

        with_existing = client.get(
            "/api/v1/employee-attendance/effects/generation-candidates",
            params={"include_existing": "true"},
        )
        assert with_existing.status_code == 200
        match = next(
            row for row in with_existing.json() if row["employee_request_id"] == request_id
        )
        assert match["has_effect"] is True
        assert match["effect_status"] == "pending"
    finally:
        _cleanup_overrides()


def test_submitted_request_not_in_generation_candidates(db_fixture, db_session):
    async def _setup():
        emp = await _seed_employee(db_session, user_id="cand-submitted")
        req = await _seed_request(
            db_session,
            employee_id=emp.id,
            status="submitted",
        )
        return req.id

    request_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-cand-submitted", "admin"))
    try:
        response = client.get("/api/v1/employee-attendance/effects/generation-candidates")
        assert response.status_code == 200
        assert all(row["employee_request_id"] != request_id for row in response.json())
    finally:
        _cleanup_overrides()
