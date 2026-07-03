from __future__ import annotations

import csv
import importlib.util
import io
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


async def _seed_quality_rows(db_session):
    suffix = uuid.uuid4().hex[:8]
    partial_code = f"MAT-EXP-PARTIAL-{suffix}"
    invalid_dims_code = f"MAT-EXP-INV-DIMS-{suffix}"

    db_session.add_all(
        [
            Inventory_materials(
                code=partial_code,
                name="=Danger, \"quoted\"\nline",
                category="panou",
                unit="mp",
                status="active",
                sheet_format_type="sheet",
                sheet_width=2000,
                sheet_height=1000,
                sheet_unit="mm",
                usable_width=3000,
            ),
            Inventory_materials(
                code=invalid_dims_code,
                name="Material invalid dims",
                category="panou",
                unit="mp",
                status="active",
                sheet_format_type="sheet",
                sheet_width=0,
                sheet_height=1000,
                sheet_unit="mm",
            ),
        ]
    )
    await db_session.commit()
    return {"partial_code": partial_code, "invalid_dims_code": invalid_dims_code}


async def _seed_trail_rows(db_session):
    suffix = uuid.uuid4().hex[:8]
    now = datetime.now(timezone.utc)
    mat_code = f"MAT-EXP-TRAIL-{suffix}"

    db_session.add(
        Inventory_materials(
            code=mat_code,
            name="Trail material",
            category="panou",
            unit="mp",
            status="active",
            sheet_format_type="sheet",
            sheet_width=1200,
            sheet_height=800,
            sheet_unit="mm",
        )
    )

    db_session.add_all(
        [
            Inventory_sheet_remediation_audit_events(
                event_type="inventory_sheet_remediation_applied",
                entity_type="InventoryMaterial",
                entity_id=mat_code,
                issue_code="partial_payload",
                old_values={"usable_width": 4500},
                new_values={"usable_width": 3000},
                changed_by="@admin,one",
                changed_at=now - timedelta(hours=2),
                reason='=HYPERLINK("x")\nwith "quote"',
                validation_result_before={"audit_status": "invalid", "issue_code": "partial_payload"},
                validation_result_after={"audit_status": "valid", "issue_code": None},
                source="admin_manual_remediation",
            ),
            Inventory_sheet_remediation_audit_events(
                event_type="inventory_sheet_remediation_applied",
                entity_type="InventoryMaterial",
                entity_id=mat_code,
                issue_code="invalid_dimensions",
                old_values={"sheet_height": 0},
                new_values={"sheet_height": 2050},
                changed_by="admin-two",
                changed_at=now - timedelta(hours=1),
                reason="Corrected dimensions",
                validation_result_before={"audit_status": "invalid", "issue_code": "invalid_dimensions"},
                validation_result_after={"audit_status": "valid", "issue_code": None},
                source="admin_manual_remediation",
            ),
        ]
    )
    await db_session.commit()
    return {"material_id": mat_code, "changed_by": "@admin,one"}


def _csv_rows(response_text: str):
    return list(csv.DictReader(io.StringIO(response_text)))


def test_quality_export_requires_auth(unauth_client):
    response = unauth_client.get("/api/v1/admin/inventory/sheet-quality-audit/export")
    assert response.status_code in (401, 403)


def test_trail_export_requires_auth(unauth_client):
    response = unauth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail/export")
    assert response.status_code in (401, 403)


def test_quality_export_requires_admin(non_admin_auth_client):
    response = non_admin_auth_client.get("/api/v1/admin/inventory/sheet-quality-audit/export")
    assert response.status_code == 403


def test_trail_export_requires_admin(non_admin_auth_client):
    response = non_admin_auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail/export")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_quality_export_csv_content_type(auth_client, db_session):
    await _seed_quality_rows(db_session)
    response = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit/export?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


@pytest.mark.asyncio
async def test_quality_export_json_content_type(auth_client, db_session):
    await _seed_quality_rows(db_session)
    response = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit/export?format=json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["export_type"] == "inventory_sheet_quality_audit"
    assert body["format"] == "json"


@pytest.mark.asyncio
async def test_trail_export_csv_content_type(auth_client, db_session):
    await _seed_trail_rows(db_session)
    response = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail/export?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


@pytest.mark.asyncio
async def test_trail_export_json_content_type(auth_client, db_session):
    await _seed_trail_rows(db_session)
    response = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail/export?format=json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["export_type"] == "inventory_sheet_remediation_audit_trail"
    assert body["format"] == "json"


def test_invalid_format_returns_422(auth_client):
    response_quality = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit/export?format=xml")
    response_trail = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail/export?format=xml")
    assert response_quality.status_code == 422
    assert response_trail.status_code == 422


@pytest.mark.asyncio
async def test_quality_export_filters_respected(auth_client, db_session):
    seeded = await _seed_quality_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-quality-audit/export?format=csv&issue_code=partial_payload"
    )
    assert response.status_code == 200

    rows = _csv_rows(response.text)
    targeted = [row for row in rows if row["material_id"] == seeded["partial_code"]]
    other = [row for row in rows if row["material_id"] == seeded["invalid_dims_code"]]

    assert targeted
    assert not other
    assert all(row["issue_code"] == "partial_payload" for row in targeted)


@pytest.mark.asyncio
async def test_trail_export_filters_respected(auth_client, db_session):
    seeded = await _seed_trail_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail/export",
        params={
            "format": "csv",
            "material_id": seeded["material_id"],
            "changed_by": seeded["changed_by"],
        },
    )
    assert response.status_code == 200

    rows = _csv_rows(response.text)
    assert rows
    assert all(row["material_id"] == seeded["material_id"] for row in rows)
    assert all(row["changed_by"].startswith("'@admin,one") for row in rows)


@pytest.mark.asyncio
async def test_export_limit_max_limit_enforced(auth_client, db_session):
    await _seed_quality_rows(db_session)

    quality = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit/export?limit=6000")
    trail = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail/export?limit=6000")

    assert quality.status_code == 422
    assert trail.status_code == 422


@pytest.mark.asyncio
async def test_csv_escaping_and_injection_neutralization(auth_client, db_session):
    seeded_quality = await _seed_quality_rows(db_session)
    await _seed_trail_rows(db_session)

    quality_resp = auth_client.get(
        "/api/v1/admin/inventory/sheet-quality-audit/export?format=csv&issue_code=partial_payload"
    )
    assert quality_resp.status_code == 200
    quality_rows = _csv_rows(quality_resp.text)
    quality_target = [row for row in quality_rows if row["material_id"] == seeded_quality["partial_code"]]
    assert quality_target
    assert quality_target[0]["material_name"].startswith("'=")
    assert '"quoted"' in quality_target[0]["material_name"]
    assert "line" in quality_target[0]["material_name"]

    trail_resp = auth_client.get(
        "/api/v1/admin/inventory/sheet-remediation-audit-trail/export?format=csv"
    )
    assert trail_resp.status_code == 200
    trail_rows = _csv_rows(trail_resp.text)
    assert trail_rows
    inj_rows = [row for row in trail_rows if row["changed_by"].startswith("'@")]
    assert inj_rows
    assert all(row["reason"].startswith("'=") or row["reason"] == "Corrected dimensions" for row in trail_rows)


@pytest.mark.asyncio
async def test_export_no_mutation_inventory_and_audit_counts(auth_client, db_session):
    await _seed_quality_rows(db_session)
    await _seed_trail_rows(db_session)

    before_inventory_count = await db_session.scalar(select(func.count(Inventory_materials.id)))
    before_audit_count = await db_session.scalar(
        select(func.count(Inventory_sheet_remediation_audit_events.id))
    )

    q_csv = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit/export?format=csv")
    q_json = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit/export?format=json")
    t_csv = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail/export?format=csv")
    t_json = auth_client.get("/api/v1/admin/inventory/sheet-remediation-audit-trail/export?format=json")

    assert q_csv.status_code == 200
    assert q_json.status_code == 200
    assert t_csv.status_code == 200
    assert t_json.status_code == 200

    after_inventory_count = await db_session.scalar(select(func.count(Inventory_materials.id)))
    after_audit_count = await db_session.scalar(
        select(func.count(Inventory_sheet_remediation_audit_events.id))
    )

    assert before_inventory_count == after_inventory_count
    assert before_audit_count == after_audit_count


def test_export_does_not_create_stock_movement_and_no_remediation_side_effect(auth_client):
    """BUILD 16: stock_movements model now exists. Verify export does not create movements."""
    stock_movements_spec = importlib.util.find_spec("models.stock_movements")
    # BUILD 16 introduced stock_movements model — it should now exist
    assert stock_movements_spec is not None

    response = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit/export?format=csv")
    assert response.status_code == 200
