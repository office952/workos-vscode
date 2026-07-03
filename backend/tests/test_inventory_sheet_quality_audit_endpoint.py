import importlib.util
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from models.inventory_materials import Inventory_materials
from schemas.auth import UserResponse


async def _seed_audit_rows(db_session):
    suffix = uuid.uuid4().hex[:8]
    codes = {
        "valid": f"MAT-AUDIT-VALID-{suffix}",
        "not_applicable": f"MAT-AUDIT-NA-{suffix}",
        "missing": f"MAT-AUDIT-MISSING-{suffix}",
        "partial": f"MAT-AUDIT-PARTIAL-{suffix}",
        "bad_unit": f"MAT-AUDIT-BAD-UNIT-{suffix}",
        "bad_dims": f"MAT-AUDIT-BAD-DIMS-{suffix}",
    }

    db_session.add_all(
        [
            Inventory_materials(
                code=codes["valid"],
                name="Audit valid",
                category="panou",
                unit="mp",
                status="active",
                sheet_format_type="sheet",
                sheet_width=2000,
                sheet_height=1000,
                sheet_unit="mm",
            ),
            Inventory_materials(
                code=codes["not_applicable"],
                name="Audit roll",
                category="material",
                unit="ml",
                status="active",
                sheet_format_type="roll",
                sheet_unit="mm",
            ),
            Inventory_materials(
                code=codes["missing"],
                name="Audit missing dims",
                category="panou",
                unit="sheet",
                status="active",
                sheet_format_type="sheet",
                sheet_unit="mm",
            ),
            Inventory_materials(
                code=codes["partial"],
                name="Audit partial payload",
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
                code=codes["bad_unit"],
                name="Audit bad unit",
                category="panou",
                unit="invalid_unit",
                status="active",
                sheet_format_type="sheet",
                sheet_width=2000,
                sheet_height=1000,
                sheet_unit="mm",
            ),
            Inventory_materials(
                code=codes["bad_dims"],
                name="Audit bad dims",
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
    return codes


def _seeded_items(body: dict, codes: dict[str, str]) -> list[dict]:
    code_set = set(codes.values())
    return [item for item in body["items"] if item.get("material_code") in code_set]


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


def test_inventory_sheet_quality_audit_requires_auth(unauth_client):
    response = unauth_client.get("/api/v1/admin/inventory/sheet-quality-audit")
    assert response.status_code in (401, 403)


def test_inventory_sheet_quality_audit_requires_admin_role(non_admin_auth_client):
    response = non_admin_auth_client.get("/api/v1/admin/inventory/sheet-quality-audit")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_inventory_sheet_quality_audit_response_shape(auth_client, db_session):
    await _seed_audit_rows(db_session)

    response = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit")
    assert response.status_code == 200
    body = response.json()

    assert body["source"] == "backend"
    assert body["report_type"] == "inventory_sheet_quality_audit"
    assert "generated_at" in body
    assert "summary" in body
    assert "filters" in body
    assert "items" in body
    assert "warnings" in body


@pytest.mark.asyncio
async def test_inventory_sheet_quality_audit_summary_and_issue_categories(auth_client, db_session):
    codes = await _seed_audit_rows(db_session)

    response = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit")
    assert response.status_code == 200
    body = response.json()

    summary = body["summary"]
    assert summary["total_records_checked"] >= 6
    assert summary["valid_count"] >= 1
    assert summary["not_applicable_count"] >= 1
    assert summary["invalid_count"] >= 4
    assert summary["would_block_intake_assist_count"] >= 4

    by_issue_code = summary["by_issue_code"]
    expected_codes = {
        "missing_required_field",
        "missing_configuration",
        "invalid_unit",
        "invalid_dimensions",
        "partial_payload",
        "unexpected_shape",
    }
    assert set(by_issue_code.keys()) == expected_codes
    assert by_issue_code["missing_configuration"] >= 1
    assert by_issue_code["partial_payload"] >= 1
    assert by_issue_code["invalid_unit"] >= 1
    assert by_issue_code["invalid_dimensions"] >= 1

    seeded = _seeded_items(body, codes)
    assert len(seeded) == 6


@pytest.mark.asyncio
async def test_inventory_sheet_quality_audit_filter_status_invalid(auth_client, db_session):
    codes = await _seed_audit_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-quality-audit?status=invalid"
    )
    assert response.status_code == 200
    body = response.json()

    assert body["filters"]["status"] == "invalid"
    assert all(item["status"] == "invalid" for item in body["items"])
    seeded_invalid = [
        item
        for item in _seeded_items(body, codes)
        if item["material_code"]
        in {codes["missing"], codes["partial"], codes["bad_unit"], codes["bad_dims"]}
    ]
    assert len(seeded_invalid) == 4


@pytest.mark.asyncio
async def test_inventory_sheet_quality_audit_filter_issue_code(auth_client, db_session):
    codes = await _seed_audit_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-quality-audit?issue_code=partial_payload"
    )
    assert response.status_code == 200
    body = response.json()

    assert body["filters"]["issue_code"] == "partial_payload"
    assert all(item["issue_code"] == "partial_payload" for item in body["items"])
    seeded = _seeded_items(body, codes)
    assert len(seeded) == 1
    assert seeded[0]["material_code"] == codes["partial"]


@pytest.mark.asyncio
async def test_inventory_sheet_quality_audit_filter_would_block(auth_client, db_session):
    codes = await _seed_audit_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-quality-audit?would_block_intake_assist=true"
    )
    assert response.status_code == 200
    body = response.json()

    assert body["filters"]["would_block_intake_assist"] is True
    assert all(item["would_block_intake_assist"] is True for item in body["items"])
    seeded = _seeded_items(body, codes)
    assert len(seeded) == 4


@pytest.mark.asyncio
async def test_inventory_sheet_quality_audit_pagination(auth_client, db_session):
    await _seed_audit_rows(db_session)

    response = auth_client.get(
        "/api/v1/admin/inventory/sheet-quality-audit?limit=2&offset=1"
    )
    assert response.status_code == 200
    body = response.json()

    assert body["filters"]["limit"] == 2
    assert body["filters"]["offset"] == 1
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_inventory_sheet_quality_audit_endpoint_no_mutation_row_count(auth_client, db_session):
    await _seed_audit_rows(db_session)

    before_count = await db_session.scalar(select(func.count(Inventory_materials.id)))

    response = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit")
    assert response.status_code == 200

    after_count = await db_session.scalar(select(func.count(Inventory_materials.id)))
    assert before_count == after_count


@pytest.mark.asyncio
async def test_inventory_sheet_quality_audit_endpoint_no_mutation_values(auth_client, db_session):
    codes = await _seed_audit_rows(db_session)

    before_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == codes["valid"])
    )
    before_material = before_result.scalar_one()
    before_width = before_material.sheet_width
    before_height = before_material.sheet_height

    response = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit")
    assert response.status_code == 200

    after_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == codes["valid"])
    )
    after_material = after_result.scalar_one()
    after_width = after_material.sheet_width
    after_height = after_material.sheet_height

    assert before_width == after_width
    assert before_height == after_height


@pytest.mark.asyncio
async def test_inventory_sheet_quality_audit_endpoint_no_commit_or_flush(auth_client, db_session, monkeypatch):
    await _seed_audit_rows(db_session)

    async def _raise_on_commit(self):
        raise AssertionError("commit should not be called by read-only audit endpoint")

    async def _raise_on_flush(self, *args, **kwargs):
        raise AssertionError("flush should not be called by read-only audit endpoint")

    monkeypatch.setattr(AsyncSession, "commit", _raise_on_commit)
    monkeypatch.setattr(AsyncSession, "flush", _raise_on_flush)

    response = auth_client.get("/api/v1/admin/inventory/sheet-quality-audit")
    assert response.status_code == 200


def test_inventory_sheet_quality_audit_stock_movements_not_applicable():
    stock_movements_spec = importlib.util.find_spec("models.stock_movements")
    # BUILD 16 introduced stock_movements model — it should now exist
    assert stock_movements_spec is not None
