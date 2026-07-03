from __future__ import annotations

import importlib.util
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from core.database import get_db
from dependencies.auth import get_current_user
from models.inventory_materials import Inventory_materials
from models.inventory_sheet_remediation_audit_events import (
    Inventory_sheet_remediation_audit_events,
)
from schemas.auth import UserResponse


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@pytest.fixture
def non_admin_auth_client(db_fixture):
    from main import app

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="test-user-id",
            email="user@example.com",
            name="Test User",
            role="user",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


async def _seed_audit_trail_rows(db_session):
    suffix = uuid.uuid4().hex[:8]
    now = datetime.now(timezone.utc)

    mat_a = f"MAT-AUDIT-TRAIL-A-{suffix}"
    mat_b = f"MAT-AUDIT-TRAIL-B-{suffix}"

    db_session.add_all(
        [
            Inventory_materials(
                code=mat_a,
                name="Audit trail material A",
                category="panou",
                unit="mp",
                status="active",
                sheet_format_type="sheet",
                sheet_width=1000,
                sheet_height=500,
                sheet_unit="mm",
            ),
            Inventory_materials(
                code=mat_b,
                name="Audit trail material B",
                category="panou",
                unit="mp",
                status="active",
                sheet_format_type="sheet",
                sheet_width=1200,
                sheet_height=800,
                sheet_unit="mm",
            ),
        ]
    )

    events = [
        Inventory_sheet_remediation_audit_events(
            event_type="inventory_sheet_remediation_applied",
            entity_type="InventoryMaterial",
            entity_id=mat_a,
            issue_code="missing_configuration",
            old_values={"sheet_width": None},
            new_values={"sheet_width": 3050},
            changed_by="admin-a",
            changed_at=now - timedelta(days=2),
            reason="Verified supplier label A",
            validation_result_before={"audit_status": "invalid", "issue_code": "missing_configuration"},
            validation_result_after={"audit_status": "valid", "issue_code": None},
            source="admin_manual_remediation",
        ),
        Inventory_sheet_remediation_audit_events(
            event_type="inventory_sheet_remediation_applied",
            entity_type="InventoryMaterial",
            entity_id=mat_b,
            issue_code="partial_payload",
            old_values={"usable_width": 4000},
            new_values={"usable_width": 3000},
            changed_by="admin-b",
            changed_at=now - timedelta(days=1),
            reason="Corrected usable width",
            validation_result_before={"audit_status": "invalid", "issue_code": "partial_payload"},
            validation_result_after={"audit_status": "valid", "issue_code": None},
            source="admin_manual_remediation",
        ),
        Inventory_sheet_remediation_audit_events(
            event_type="inventory_sheet_remediation_applied",
            entity_type="InventoryMaterial",
            entity_id=mat_a,
            issue_code="invalid_dimensions",
            old_values={"sheet_height": 0},
            new_values={"sheet_height": 2050},
            changed_by="admin-a",
            changed_at=now,
            reason="Corrected physical dimensions",
            validation_result_before={"audit_status": "invalid", "issue_code": "invalid_dimensions"},
            validation_result_after={"audit_status": "valid", "issue_code": None},
            source="admin_manual_remediation",
        ),
    ]

    db_session.add_all(events)
    await db_session.commit()
    return {
        "mat_a": mat_a,
        "mat_b": mat_b,
        "now": now,
    }


def test_audit_trail_requires_auth(unauth_client):
    response = unauth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail")
    assert response.status_code in (401, 403)


def test_audit_trail_requires_admin(non_admin_auth_client):
    response = non_admin_auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_audit_trail_admin_shape(auth_client, db_session):
    await _seed_audit_trail_rows(db_session)

    response = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail")
    assert response.status_code == 200

    body = response.json()
    assert body["source"] == "backend"
    assert body["report_type"] == "inventory_sheet_remediation_audit_trail"
    assert "generated_at" in body
    assert "summary" in body
    assert "filters" in body
    assert "events" in body

    first = body["events"][0]
    assert "audit_event_id" in first
    assert "material_id" in first
    assert "issue_code" in first
    assert "reason" in first
    assert "changed_at" in first
    assert "old_values" in first
    assert "new_values" in first
    assert "validation_result_before" in first
    assert "validation_result_after" in first


@pytest.mark.asyncio
async def test_audit_trail_filter_material_id(auth_client, db_session):
    seeded = await _seed_audit_trail_rows(db_session)

    response = auth_client.get(
        f"/api/v1/admin/inventory/sheet-remediation-audit-trail?material_id={seeded['mat_b']}"
    )
    assert response.status_code == 200
    body = response.json()

    assert body["filters"]["material_id"] == seeded["mat_b"]
    assert all(event["material_id"] == seeded["mat_b"] for event in body["events"])


@pytest.mark.asyncio
async def test_audit_trail_filter_issue_code(auth_client, db_session):
    await _seed_audit_trail_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail?issue_code=partial_payload"
    )
    assert response.status_code == 200
    body = response.json()

    assert body["filters"]["issue_code"] == "partial_payload"
    assert all(event["issue_code"] == "partial_payload" for event in body["events"])


@pytest.mark.asyncio
async def test_audit_trail_filter_changed_by(auth_client, db_session):
    await _seed_audit_trail_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail?changed_by=admin-a"
    )
    assert response.status_code == 200
    body = response.json()

    assert body["filters"]["changed_by"] == "admin-a"
    assert all(event["changed_by"] == "admin-a" for event in body["events"])


@pytest.mark.asyncio
async def test_audit_trail_filter_date_from(auth_client, db_session):
    seeded = await _seed_audit_trail_rows(db_session)
    date_from = seeded["now"] - timedelta(hours=12)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail",
        params={"date_from": date_from.isoformat()},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["filters"]["date_from"] is not None
    assert all(
        _as_utc(datetime.fromisoformat(event["changed_at"])) >= _as_utc(date_from)
        for event in body["events"]
    )


@pytest.mark.asyncio
async def test_audit_trail_filter_date_to(auth_client, db_session):
    seeded = await _seed_audit_trail_rows(db_session)
    date_to = seeded["now"] - timedelta(hours=36)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail",
        params={"date_to": date_to.isoformat()},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["filters"]["date_to"] is not None
    assert all(
        _as_utc(datetime.fromisoformat(event["changed_at"])) <= _as_utc(date_to)
        for event in body["events"]
    )


@pytest.mark.asyncio
async def test_audit_trail_invalid_date_range_returns_422(auth_client, db_session):
    seeded = await _seed_audit_trail_rows(db_session)
    date_from = seeded["now"].isoformat()
    date_to = (seeded["now"] - timedelta(days=2)).isoformat()

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail",
        params={"date_from": date_from, "date_to": date_to},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_date_range"


@pytest.mark.asyncio
async def test_audit_trail_pagination(auth_client, db_session):
    await _seed_audit_trail_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail?limit=2&offset=1"
    )
    assert response.status_code == 200
    body = response.json()

    assert body["filters"]["limit"] == 2
    assert body["filters"]["offset"] == 1
    assert len(body["events"]) == 2
    assert body["summary"]["returned_events"] == 2


@pytest.mark.asyncio
async def test_audit_trail_max_limit_enforced(auth_client, db_session):
    await _seed_audit_trail_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail?limit=999"
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_audit_trail_invalid_offset_rejected(auth_client, db_session):
    await _seed_audit_trail_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail?offset=-1"
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_audit_trail_summary_semantics(auth_client, db_session):
    await _seed_audit_trail_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail?limit=1&offset=0"
    )
    assert response.status_code == 200
    body = response.json()

    summary = body["summary"]
    assert summary["total_events"] >= 3
    assert summary["returned_events"] == 1
    assert "by_issue_code" in summary
    assert "by_status" in summary


@pytest.mark.asyncio
async def test_audit_trail_no_mutation_inventory_count(auth_client, db_session):
    await _seed_audit_trail_rows(db_session)

    before_count = await db_session.scalar(select(func.count(Inventory_materials.id)))

    response = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail")
    assert response.status_code == 200

    after_count = await db_session.scalar(select(func.count(Inventory_materials.id)))
    assert before_count == after_count


@pytest.mark.asyncio
async def test_audit_trail_no_mutation_inventory_values(auth_client, db_session):
    seeded = await _seed_audit_trail_rows(db_session)

    before_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == seeded["mat_a"])
    )
    before_material = before_result.scalar_one()
    before_sheet_width = before_material.sheet_width

    response = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail")
    assert response.status_code == 200

    after_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == seeded["mat_a"])
    )
    after_material = after_result.scalar_one()
    assert before_sheet_width == after_material.sheet_width


@pytest.mark.asyncio
async def test_audit_trail_no_mutation_event_count(auth_client, db_session):
    await _seed_audit_trail_rows(db_session)

    before_count = await db_session.scalar(
        select(func.count(Inventory_sheet_remediation_audit_events.id))
    )

    response = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail")
    assert response.status_code == 200

    after_count = await db_session.scalar(
        select(func.count(Inventory_sheet_remediation_audit_events.id))
    )
    assert before_count == after_count


@pytest.mark.asyncio
async def test_audit_trail_no_mutation_event_values(auth_client, db_session):
    seeded = await _seed_audit_trail_rows(db_session)

    before_result = await db_session.execute(
        select(Inventory_sheet_remediation_audit_events).where(
            Inventory_sheet_remediation_audit_events.entity_id == seeded["mat_a"]
        )
    )
    before_event = before_result.scalars().first()
    assert before_event is not None
    before_reason = before_event.reason

    response = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail")
    assert response.status_code == 200

    after_result = await db_session.execute(
        select(Inventory_sheet_remediation_audit_events).where(
            Inventory_sheet_remediation_audit_events.id == before_event.id
        )
    )
    after_event = after_result.scalar_one()
    assert before_reason == after_event.reason


def test_audit_trail_stock_movement_not_present():
    stock_movements_spec = importlib.util.find_spec("models.stock_movements")
    # BUILD 16 introduced stock_movements model — it should now exist
    assert stock_movements_spec is not None
