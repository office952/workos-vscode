import json

import pytest
from sqlalchemy import func, select

from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.product_templates import Product_templates
from models.quotes import Quotes


async def _seed_templates_and_materials(db_session):
    db_session.add_all(
        [
            Product_templates(
                template_code="TPL-ACTIVE-1",
                family_id="signage",
                family_name="Signage",
                description="Active template",
                active=True,
                required_materials_json=json.dumps([
                    {"materialCode": "MAT-ACP-3MM", "quantity": 1, "unit": "mp"}
                ]),
            ),
            Product_templates(
                template_code="TPL-INACTIVE-1",
                family_id="signage",
                family_name="Signage",
                description="Inactive template",
                active=False,
            ),
            Inventory_materials(
                code="MAT-ACP-3MM",
                name="ACP / Dibond 3mm",
                category="panou_compozit",
                unit="mp",
                status="missing_price",
                unit_cost=None,
                sheet_format_type="sheet",
                sheet_width=2000,
                sheet_height=1000,
                sheet_unit="mm",
                format_source="manual",
                format_verified=True,
            ),
            Inventory_materials(
                code="MAT-FIT-ROTATED",
                name="Sheet that fits only rotated",
                category="panou_compozit",
                unit="buc",
                status="active",
                unit_cost=1.25,
                sheet_format_type="sheet",
                sheet_width=900,
                sheet_height=1200,
                sheet_unit="mm",
                format_source="supplier",
                format_verified=True,
            ),
            Inventory_materials(
                code="MAT-NO-FIT",
                name="Sheet that does not fit",
                category="panou_compozit",
                unit="sheet",
                status="active",
                unit_cost=2.5,
                sheet_format_type="sheet",
                sheet_width=600,
                sheet_height=400,
                sheet_unit="mm",
                format_source="supplier",
                format_verified=False,
            ),
            Inventory_materials(
                code="MAT-INCOMPLETE-SHEET",
                name="Sheet with incomplete dimensions",
                category="panou_compozit_invalid",
                unit="sheet",
                status="active",
                unit_cost=3.0,
                sheet_format_type="sheet",
                sheet_unit="mm",
                format_source="manual",
                format_verified=False,
            ),
            Quotes(
                code="Q-TEST-1",
                client_name="Client",
                status="draft",
                version=1,
            ),
            Orders(
                code="O-TEST-1",
                client_name="Client",
                status="new",
            ),
        ]
    )
    await db_session.commit()


async def _count_rows(db_session):
    tpl_count = await db_session.scalar(select(func.count(Product_templates.id)))
    mat_count = await db_session.scalar(select(func.count(Inventory_materials.id)))
    quote_count = await db_session.scalar(select(func.count(Quotes.id)))
    order_count = await db_session.scalar(select(func.count(Orders.id)))
    return int(tpl_count or 0), int(mat_count or 0), int(quote_count or 0), int(order_count or 0)


def test_auth_required_for_intake_assist_routes(unauth_client):
    resp = unauth_client.get("/api/v1/intake-assist/product-templates")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_product_templates_list_and_suggestion_contract(auth_client, db_session):
    await _seed_templates_and_materials(db_session)

    list_resp = auth_client.get("/api/v1/intake-assist/product-templates")
    assert list_resp.status_code == 200
    list_body = list_resp.json()

    assert list_body["source"] == "backend"
    assert isinstance(list_body["items"], list)
    assert any(item["name"] == "TPL-ACTIVE-1" for item in list_body["items"])
    assert all(item["name"] != "TPL-INACTIVE-1" for item in list_body["items"])

    suggestion_resp = auth_client.post(
        "/api/v1/intake-assist/product-template-suggestions",
        json={
            "intake_id": "WI-1000",
            "title": "Signage corporate",
            "description": "Need signage panel",
            "requested_product_type": "signage",
            "dimensions": {"width": 1000, "height": 500, "unit": "mm"},
            "quantity": 1,
        },
    )
    assert suggestion_resp.status_code == 200
    body = suggestion_resp.json()
    assert body["source"] == "backend"
    assert isinstance(body["suggestions"], list)
    assert all(s["requires_operator_confirmation"] is True for s in body["suggestions"])
    assert all(s["template_name"] != "TPL-INACTIVE-1" for s in body["suggestions"])


@pytest.mark.asyncio
async def test_material_sheet_assist_contract_and_no_mutation(auth_client, db_session):
    await _seed_templates_and_materials(db_session)
    before_tpl, before_mat, before_quotes, before_orders = await _count_rows(db_session)

    resp = auth_client.post(
        "/api/v1/intake-assist/material-sheet-assist",
        json={
            "product_template_id": None,
            "material_category": "panou_compozit",
            "dimensions": {"width": 1000, "height": 800, "unit": "mm"},
            "quantity": 1,
            "constraints": {"rotation_allowed": True, "indoor_outdoor": "unknown"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["source"] == "backend"
    assert body["assist_available"] is True
    assert body["blockers"] == []
    assert isinstance(body["items"], list)

    by_code = {item["material_id"]: item for item in body["items"]}
    assert by_code["MAT-ACP-3MM"]["fit_status"] == "fits"
    assert by_code["MAT-FIT-ROTATED"]["fit_status"] == "fits_rotated"
    assert by_code["MAT-NO-FIT"]["fit_status"] == "does_not_fit"
    assert "MAT-INCOMPLETE-SHEET" not in by_code

    format_payload = by_code["MAT-ACP-3MM"]["sheet_format"]
    assert format_payload["type"] == "sheet"
    assert format_payload["width"] == 2000
    assert format_payload["height"] == 1000
    assert format_payload["unit"] == "mm"

    expected_top_level_keys = [
        "source",
        "assist_available",
        "items",
        "warnings",
        "blockers",
        "contract_version",
    ]
    assert list(body.keys()) == expected_top_level_keys

    expected_item_keys = [
        "material_id",
        "material_name",
        "category",
        "status",
        "unit",
        "sheet_format",
        "fit_status",
        "fit_reason",
        "warnings",
        "requires_review",
    ]
    assert list(body["items"][0].keys()) == expected_item_keys

    after_tpl, after_mat, after_quotes, after_orders = await _count_rows(db_session)
    assert (before_tpl, before_mat, before_quotes, before_orders) == (
        after_tpl,
        after_mat,
        after_quotes,
        after_orders,
    )


@pytest.mark.asyncio
async def test_material_sheet_assist_rejects_unconfigured_sheet_unit(auth_client, db_session):
    db_session.add(
        Inventory_materials(
            code="MAT-NO-SHEET-TRUTH",
            name="Missing sheet truth",
            category="misc",
            unit="sheet",
            status="active",
            unit_cost=1.0,
            sheet_format_type="sheet",
            sheet_unit="unknown",
        )
    )
    await db_session.commit()

    resp = auth_client.post(
        "/api/v1/intake-assist/material-sheet-assist",
        json={
            "product_template_id": None,
            "material_category": "misc",
            "dimensions": {"width": 1000, "height": 500, "unit": "mm"},
            "quantity": 1,
            "constraints": {"rotation_allowed": True, "indoor_outdoor": "unknown"},
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["detail"]["error"] == "inventory_sheet_contract_error"
    assert body["detail"]["code"] in {"missing_required_field", "invalid_enum"}


@pytest.mark.asyncio
async def test_material_sheet_assist_rejects_partial_dimensions(auth_client, db_session):
    await _seed_templates_and_materials(db_session)

    resp = auth_client.post(
        "/api/v1/intake-assist/material-sheet-assist",
        json={
            "material_category": "panou_compozit",
            "dimensions": {"width": 1000, "unit": "mm"},
            "constraints": {"rotation_allowed": True},
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["detail"]["error"] == "inventory_sheet_contract_error"
    assert body["detail"]["code"] == "partial_dimensions"


@pytest.mark.asyncio
async def test_material_sheet_assist_rejects_invalid_material_shape(auth_client, db_session):
    await _seed_templates_and_materials(db_session)

    resp = auth_client.post(
        "/api/v1/intake-assist/material-sheet-assist",
        json={
            "material_category": "panou_compozit_invalid",
            "dimensions": {"width": 1000, "height": 500, "unit": "mm"},
            "constraints": {"rotation_allowed": True},
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["detail"]["error"] == "inventory_sheet_contract_error"
    assert body["detail"]["code"] == "missing_required_field"


def test_material_sheet_assist_rejects_unexpected_constraints_shape(auth_client):
    resp = auth_client.post(
        "/api/v1/intake-assist/material-sheet-assist",
        json={
            "material_category": "panou_compozit",
            "dimensions": {"width": 1000, "height": 500, "unit": "mm"},
            "constraints": ["rotation_allowed"],
        },
    )
    assert resp.status_code == 422


def test_material_sheet_assist_rejects_wrong_dimensions_type(auth_client):
    resp = auth_client.post(
        "/api/v1/intake-assist/material-sheet-assist",
        json={
            "material_category": "panou_compozit",
            "dimensions": {"width": "wide", "height": 500, "unit": "mm"},
            "constraints": {"rotation_allowed": True},
        },
    )
    assert resp.status_code == 422


def test_fiscal_lookup_returns_not_configured_stub(auth_client):
    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "smartbill", "country": "RO", "tax_id": "12345678"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body["provider"] == "smartbill"
    assert body["status"] == "not_configured"
    assert body["normalized"] is None
