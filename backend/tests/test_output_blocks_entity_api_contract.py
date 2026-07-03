import uuid

import pytest
from sqlalchemy import func, select

from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.quotes import Quotes


def _block_id(prefix: str = "ob") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _valid_payload(block_id: str | None = None) -> dict:
    return {
        "block_id": block_id or _block_id(),
        "block_type": "offer_short_description",
        "title": "Offer short description",
        "purpose": "Client-facing concise summary",
        "audience": "client",
        "document_type": "offer",
        "source_fields": ["identity.product_name", "quote.quantity"],
        "variables": [
            {
                "key": "product_name",
                "source_field": "identity.product_name",
                "required": True,
                "format": "plain_text",
                "missing_behavior": "block_rendering",
            },
            {
                "key": "qty",
                "source_field": "quote.quantity",
                "required": False,
                "format": "quantity",
                "missing_behavior": "render_with_warning",
            },
        ],
        "template_text": "{{product_name}} x {{qty}}",
        "conditions": {
            "show_if": {
                "field": "options.mounting_type",
                "operator": "equals",
                "value": "spacers",
            }
        },
        "approval_status": "draft",
        "version": "v1",
        "owner_role": "manager",
        "reviewer_role": None,
        "snapshot_policy": {"freeze_on_approval": True},
    }


def test_auth_required_for_output_blocks_api(unauth_client):
    resp = unauth_client.get("/api/v1/product-system/output-blocks")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_list_read_contract(auth_client, db_session):
    payload = _valid_payload()

    create_resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["block_id"] == payload["block_id"]
    assert created["approval_status"] == "draft"

    list_resp = auth_client.get("/api/v1/product-system/output-blocks")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] >= 1
    assert any(item["block_id"] == payload["block_id"] for item in body["items"])

    read_resp = auth_client.get(f"/api/v1/product-system/output-blocks/{payload['block_id']}")
    assert read_resp.status_code == 200
    read_body = read_resp.json()
    assert read_body["block_type"] == "offer_short_description"
    assert isinstance(read_body["variables"], list)


def test_invalid_block_type_rejected(auth_client):
    payload = _valid_payload()
    payload["block_type"] = "visual_prompt_block"

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_invalid_audience_rejected(auth_client):
    payload = _valid_payload()
    payload["audience"] = "sales"

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_invalid_document_type_rejected(auth_client):
    payload = _valid_payload()
    payload["document_type"] = "installation_sheet"

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_invalid_approval_status_rejected(auth_client):
    payload = _valid_payload()
    payload["approval_status"] = "approved_for_client"

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_allowed_source_prefix_accepted(auth_client):
    payload = _valid_payload()
    payload["source_fields"] = ["materials.main_material", "operations.cnc_cut.required"]
    payload["variables"][0]["source_field"] = "materials.main_material"
    payload["variables"][0]["missing_behavior"] = "block_rendering"

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 201


@pytest.mark.parametrize(
    "field",
    [
        "frontend.title",
        "ai.generated_scope",
        "inventory.stock_current",
        "execution_reality.duration_minutes",
    ],
)
def test_forbidden_source_rejected(auth_client, field):
    payload = _valid_payload()
    payload["source_fields"] = [field]
    payload["variables"][0]["source_field"] = field

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_missing_variable_key_rejected(auth_client):
    payload = _valid_payload()
    payload["variables"][0].pop("key")

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_missing_variable_source_field_rejected(auth_client):
    payload = _valid_payload()
    payload["variables"][0].pop("source_field")

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_duplicate_variable_key_rejected(auth_client):
    payload = _valid_payload()
    payload["variables"].append(
        {
            "key": "product_name",
            "source_field": "identity.product_name",
            "required": False,
            "format": "plain_text",
            "missing_behavior": "render_with_warning",
        }
    )

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_invalid_variable_format_rejected(auth_client):
    payload = _valid_payload()
    payload["variables"][0]["format"] = "markdown"

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_invalid_missing_behavior_rejected(auth_client):
    payload = _valid_payload()
    payload["variables"][0]["missing_behavior"] = "silent"

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_valid_condition_accepted(auth_client):
    payload = _valid_payload()
    payload["conditions"] = {
        "show_if": {
            "field": "options.mounting_type",
            "operator": "in",
            "value": ["spacers", "flush"],
        }
    }

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 201


def test_regex_operator_rejected(auth_client):
    payload = _valid_payload()
    payload["conditions"] = {
        "show_if": {
            "field": "options.mounting_type",
            "operator": "regex",
            "value": "spa.*",
        }
    }

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_frontend_condition_source_rejected(auth_client):
    payload = _valid_payload()
    payload["conditions"] = {
        "show_if": {
            "field": "frontend.mounting_label",
            "operator": "equals",
            "value": "spacers",
        }
    }

    resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert resp.status_code == 422


def test_approve_draft_block(auth_client):
    payload = _valid_payload()
    create_resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert create_resp.status_code == 201

    approve_resp = auth_client.post(
        f"/api/v1/product-system/output-blocks/{payload['block_id']}/approve",
        json={"reviewer_role": "manager"},
    )
    assert approve_resp.status_code == 200
    body = approve_resp.json()
    assert body["approval_status"] == "approved"
    assert body["reviewer_role"] == "manager"


def test_approved_block_cannot_be_unsafely_modified(auth_client):
    payload = _valid_payload()
    create_resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert create_resp.status_code == 201

    approve_resp = auth_client.post(
        f"/api/v1/product-system/output-blocks/{payload['block_id']}/approve",
        json={},
    )
    assert approve_resp.status_code == 200

    patch_resp = auth_client.patch(
        f"/api/v1/product-system/output-blocks/{payload['block_id']}",
        json={"title": "unsafe update"},
    )
    assert patch_resp.status_code == 409


def test_deprecated_block_cannot_be_approved_directly(auth_client):
    payload = _valid_payload()
    payload["approval_status"] = "deprecated"

    create_resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert create_resp.status_code == 201

    approve_resp = auth_client.post(
        f"/api/v1/product-system/output-blocks/{payload['block_id']}/approve",
        json={},
    )
    assert approve_resp.status_code == 409


@pytest.mark.asyncio
async def test_create_update_do_not_mutate_quotes_orders_inventory(auth_client, db_session):
    before_quotes = await db_session.scalar(select(func.count(Quotes.id)))
    before_orders = await db_session.scalar(select(func.count(Orders.id)))
    before_inventory = await db_session.scalar(select(func.count(Inventory_materials.id)))

    payload = _valid_payload(block_id=_block_id("boundary"))
    create_resp = auth_client.post("/api/v1/product-system/output-blocks", json=payload)
    assert create_resp.status_code == 201

    patch_resp = auth_client.patch(
        f"/api/v1/product-system/output-blocks/{payload['block_id']}",
        json={"title": "updated title", "approval_status": "needs_review"},
    )
    assert patch_resp.status_code == 200

    after_quotes = await db_session.scalar(select(func.count(Quotes.id)))
    after_orders = await db_session.scalar(select(func.count(Orders.id)))
    after_inventory = await db_session.scalar(select(func.count(Inventory_materials.id)))

    assert int(before_quotes or 0) == int(after_quotes or 0)
    assert int(before_orders or 0) == int(after_orders or 0)
    assert int(before_inventory or 0) == int(after_inventory or 0)


def test_no_renderer_endpoint_added_for_entity_contract(auth_client):
    resp = auth_client.post("/api/v1/product-system/output-blocks/render", json={})
    assert resp.status_code in (404, 405)