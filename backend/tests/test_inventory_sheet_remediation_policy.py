import copy
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from core.database import get_db
from dependencies.auth import get_current_user
from models.inventory_materials import Inventory_materials
from schemas.auth import UserResponse
from services.inventory_sheet_quality_audit import (
    InventorySheetQualityAuditItem,
    audit_inventory_sheet_quality,
)
from services.inventory_sheet_remediation_policy import (
    build_remediation_plan_for_audit_item,
    build_remediation_plan_for_report,
    get_remediation_policy_for_issue,
)


def _make_invalid_item(issue_code: str) -> InventorySheetQualityAuditItem:
    return InventorySheetQualityAuditItem(
        material_id=f"MAT-{issue_code}",
        material_name=f"Material {issue_code}",
        category="panou",
        status="invalid",
        issue_code=issue_code,
        message=f"Issue: {issue_code}",
        recommended_action="Review and fix",
        would_block_intake_assist=True,
    )


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


async def _seed_plan_rows(db_session):
    suffix = uuid.uuid4().hex[:8]
    seed_rows = [
        Inventory_materials(
            code=f"MAT-PLAN-MISSING-{suffix}",
            name="Plan missing dims",
            category="panou",
            unit="sheet",
            status="active",
            sheet_format_type="sheet",
            sheet_unit="mm",
        ),
        Inventory_materials(
            code=f"MAT-PLAN-PARTIAL-{suffix}",
            name="Plan partial",
            category="panou",
            unit="mp",
            status="active",
            sheet_format_type="sheet",
            sheet_width=2000,
            sheet_height=1000,
            sheet_unit="mm",
            usable_width=2400,
        ),
        Inventory_materials(
            code=f"MAT-PLAN-INVALID-UNIT-{suffix}",
            name="Plan invalid unit",
            category="panou",
            unit="invalid_unit",
            status="active",
            sheet_format_type="sheet",
            sheet_width=2000,
            sheet_height=1000,
            sheet_unit="mm",
        ),
        Inventory_materials(
            code=f"MAT-PLAN-INVALID-DIMS-{suffix}",
            name="Plan invalid dims",
            category="panou",
            unit="mp",
            status="active",
            sheet_format_type="sheet",
            sheet_width=0,
            sheet_height=1000,
            sheet_unit="mm",
        ),
    ]
    db_session.add_all(seed_rows)
    await db_session.commit()
    return seed_rows


def test_each_issue_code_has_policy():
    issue_codes = [
        "missing_required_field",
        "missing_configuration",
        "invalid_unit",
        "invalid_dimensions",
        "partial_payload",
        "unexpected_shape",
    ]

    for code in issue_codes:
        policy = get_remediation_policy_for_issue(code)
        assert policy.issue_code == code


def test_missing_required_field_maps_to_manual_only():
    policy = get_remediation_policy_for_issue("missing_required_field")
    assert policy.remediation_category == "manual_only"


def test_missing_configuration_maps_to_assisted_manual():
    policy = get_remediation_policy_for_issue("missing_configuration")
    assert policy.remediation_category == "assisted_manual"


def test_invalid_dimensions_maps_to_manual_only():
    policy = get_remediation_policy_for_issue("invalid_dimensions")
    assert policy.remediation_category == "manual_only"


def test_partial_payload_maps_to_assisted_manual():
    policy = get_remediation_policy_for_issue("partial_payload")
    assert policy.remediation_category == "assisted_manual"


def test_unexpected_shape_maps_to_not_repairable_without_domain_decision():
    policy = get_remediation_policy_for_issue("unexpected_shape")
    assert policy.remediation_category == "not_repairable_without_domain_decision"


def test_invalid_unit_maps_to_assisted_or_future_bulk_safe():
    policy = get_remediation_policy_for_issue("invalid_unit")
    assert policy.remediation_category in {"assisted_manual", "future_bulk_safe"}


def test_policy_includes_allowed_and_forbidden_actions():
    policy = get_remediation_policy_for_issue("partial_payload")
    assert policy.allowed_actions
    assert policy.forbidden_actions


def test_build_plan_does_not_mutate_audit_item():
    item = _make_invalid_item("missing_configuration")
    before = copy.deepcopy(item)

    _ = build_remediation_plan_for_audit_item(item)

    assert item == before


@pytest.mark.asyncio
async def test_plan_report_does_not_modify_inventory_row_count(db_session):
    await _seed_plan_rows(db_session)

    before_count = await db_session.scalar(select(func.count(Inventory_materials.id)))
    audit_report = await audit_inventory_sheet_quality(db_session)
    _ = build_remediation_plan_for_report(audit_report)
    after_count = await db_session.scalar(select(func.count(Inventory_materials.id)))

    assert before_count == after_count


@pytest.mark.asyncio
async def test_plan_report_does_not_modify_inventory_values(db_session):
    rows = await _seed_plan_rows(db_session)
    tracked_code = rows[0].code

    before_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == tracked_code)
    )
    before_material = before_result.scalar_one()
    before_sheet_width = before_material.sheet_width
    before_sheet_unit = before_material.sheet_unit

    audit_report = await audit_inventory_sheet_quality(db_session)
    _ = build_remediation_plan_for_report(audit_report)

    after_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == tracked_code)
    )
    after_material = after_result.scalar_one()

    assert before_sheet_width == after_material.sheet_width
    assert before_sheet_unit == after_material.sheet_unit


def test_remediation_plan_endpoint_requires_auth(unauth_client):
    response = unauth_client.get("/api/v1/admin/inventory/sheet-quality-remediation-plan")
    assert response.status_code in (401, 403)


def test_remediation_plan_endpoint_requires_admin(non_admin_auth_client):
    response = non_admin_auth_client.get("/api/v1/admin/inventory/sheet-quality-remediation-plan")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_remediation_plan_endpoint_returns_summary_and_items(auth_client, db_session):
    await _seed_plan_rows(db_session)

    response = auth_client.get("/api/v1/admin/inventory/sheet-quality-remediation-plan")
    assert response.status_code == 200
    body = response.json()

    assert body["source"] == "backend"
    assert body["report_type"] == "inventory_sheet_remediation_plan"
    assert "generated_at" in body
    assert "summary" in body
    assert "items" in body
    assert body["warnings"] == [
        "This plan is read-only and does not modify inventory data."
    ]

    summary = body["summary"]
    assert summary["total_items"] >= 4
    assert summary["manual_only_count"] >= 1
    assert summary["assisted_manual_count"] >= 1

    first = body["items"][0]
    assert "material_id" in first
    assert "issue_code" in first
    assert "remediation_category" in first
    assert "allowed_actions" in first
    assert "forbidden_actions" in first
    assert "recommended_next_step" in first


@pytest.mark.asyncio
async def test_remediation_plan_endpoint_no_mutation(auth_client, db_session):
    rows = await _seed_plan_rows(db_session)
    tracked_code = rows[0].code

    before_count = await db_session.scalar(select(func.count(Inventory_materials.id)))
    before_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == tracked_code)
    )
    before_material = before_result.scalar_one()
    before_sheet_unit = before_material.sheet_unit

    response = auth_client.get("/api/v1/admin/inventory/sheet-quality-remediation-plan")
    assert response.status_code == 200

    after_count = await db_session.scalar(select(func.count(Inventory_materials.id)))
    after_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == tracked_code)
    )
    after_material = after_result.scalar_one()

    assert before_count == after_count
    assert before_sheet_unit == after_material.sheet_unit
