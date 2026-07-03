import json
import uuid

import pytest
from sqlalchemy import func, select

from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.output_blocks import OutputBlock
from models.quotes import Quotes


def _block_id(prefix: str = "ob-prev") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _source_payload_complete() -> dict:
    return {
        "identity": {"product_name": "Placa plexiglass test"},
        "materials": {"main_material": "plexiglass transparent"},
        "options": {"mounting_type": "spacers"},
    }


async def _create_output_block_row(
    db_session,
    *,
    block_id: str,
    approval_status: str = "approved",
    template_text: str = "{{product_name}} realizat din {{main_material}}.",
    variables: list | None = None,
    conditions: dict | list | None = None,
    source_fields: list[str] | None = None,
):
    row = OutputBlock(
        block_id=block_id,
        block_type="offer_short_description",
        title="Preview block",
        purpose="Preview validation",
        audience="client",
        document_type="offer",
        source_fields=json.dumps(source_fields or ["identity.product_name", "materials.main_material"]),
        variables=json.dumps(
            variables
            or [
                {
                    "key": "product_name",
                    "source_field": "identity.product_name",
                    "required": True,
                    "format": "plain_text",
                    "missing_behavior": "block_rendering",
                },
                {
                    "key": "main_material",
                    "source_field": "materials.main_material",
                    "required": True,
                    "format": "plain_text",
                    "missing_behavior": "block_rendering",
                },
            ]
        ),
        template_text=template_text,
        conditions=json.dumps(conditions if conditions is not None else {}),
        approval_status=approval_status,
        version="1.0.0",
        owner_role="manager",
        reviewer_role="manager",
        snapshot_policy=json.dumps({"preserve_rendered_text": True}),
    )
    db_session.add(row)
    await db_session.commit()


def test_preview_endpoint_exists(auth_client):
    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": ["missing-id"],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["preview_only"] is True


def test_preview_invalid_context_rejected(auth_client):
    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": ["missing-id"],
            "context": "order_final",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 422


def test_preview_requires_block_ids_or_block_types(auth_client):
    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_approved_and_draft_blocks_render_preview(auth_client, db_session):
    approved_id = _block_id("approved")
    draft_id = _block_id("draft")
    await _create_output_block_row(db_session, block_id=approved_id, approval_status="approved")
    await _create_output_block_row(db_session, block_id=draft_id, approval_status="draft")

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [approved_id, draft_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["preview_only"] is True
    assert len(body["rendered_blocks"]) == 2

    approved = body["rendered_blocks"][0]
    draft = body["rendered_blocks"][1]
    assert approved["approval_status"] == "approved"
    assert approved["rendered_text"]
    assert draft["approval_status"] == "draft"
    assert draft["rendered_text"]
    assert any(item["code"] == "non_canonical_preview_draft_block" for item in draft["warnings"])


@pytest.mark.asyncio
async def test_deprecated_and_blocked_statuses_are_skipped(auth_client, db_session):
    deprecated_id = _block_id("deprecated")
    blocked_id = _block_id("blocked")
    await _create_output_block_row(db_session, block_id=deprecated_id, approval_status="deprecated")
    await _create_output_block_row(db_session, block_id=blocked_id, approval_status="blocked")

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [deprecated_id, blocked_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    for block in body["rendered_blocks"]:
        assert block["skipped"] is True
        assert block["rendered_text"] is None
        assert any(item["code"] == "approval_status_blocked_for_preview" for item in block["blockers"])


@pytest.mark.asyncio
async def test_missing_required_variable_blocks_render(auth_client, db_session):
    block_id = _block_id("missing-required")
    await _create_output_block_row(db_session, block_id=block_id)

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [block_id],
            "context": "quote_preview",
            "source_payload": {"identity": {"product_name": "Placa plexiglass test"}, "materials": {}},
        },
    )

    assert resp.status_code == 200
    block = resp.json()["rendered_blocks"][0]
    assert block["rendered_text"] is None
    assert any(item["code"] == "required_variable_missing" for item in block["blockers"])


@pytest.mark.asyncio
async def test_optional_missing_render_with_warning(auth_client, db_session):
    block_id = _block_id("optional-warning")
    await _create_output_block_row(
        db_session,
        block_id=block_id,
        template_text="{{product_name}} {{subtitle}}",
        variables=[
            {
                "key": "product_name",
                "source_field": "identity.product_name",
                "required": True,
                "format": "plain_text",
                "missing_behavior": "block_rendering",
            },
            {
                "key": "subtitle",
                "source_field": "identity.subtitle",
                "required": False,
                "format": "plain_text",
                "missing_behavior": "render_with_warning",
            },
        ],
    )

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [block_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200
    block = resp.json()["rendered_blocks"][0]
    assert block["rendered_text"] is not None
    assert any(item["code"] == "optional_variable_missing_render_with_warning" for item in block["warnings"])


@pytest.mark.asyncio
async def test_optional_missing_hide_block_skips_block(auth_client, db_session):
    block_id = _block_id("optional-hide")
    await _create_output_block_row(
        db_session,
        block_id=block_id,
        template_text="{{product_name}} {{subtitle}}",
        variables=[
            {
                "key": "product_name",
                "source_field": "identity.product_name",
                "required": True,
                "format": "plain_text",
                "missing_behavior": "block_rendering",
            },
            {
                "key": "subtitle",
                "source_field": "identity.subtitle",
                "required": False,
                "format": "plain_text",
                "missing_behavior": "hide_block",
            },
        ],
    )

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [block_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200
    block = resp.json()["rendered_blocks"][0]
    assert block["skipped"] is True
    assert block["skip_reason"] == "optional_variable_missing_hide_block"
    assert block["rendered_text"] is None


@pytest.mark.asyncio
async def test_unknown_placeholder_is_blocked(auth_client, db_session):
    block_id = _block_id("unknown-placeholder")
    await _create_output_block_row(db_session, block_id=block_id, template_text="{{product_name}} {{unknown_key}}")

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [block_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200
    block = resp.json()["rendered_blocks"][0]
    assert block["rendered_text"] is None
    assert any(item["code"] == "unknown_placeholder" for item in block["blockers"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source_field",
    [
        "frontend.display_name",
        "ai.generated_text",
        "execution_reality.actual_materials",
        "inventory.stock_current",
        "inventory.live_stock",
    ],
)
async def test_forbidden_source_prefixes_are_blocked(auth_client, db_session, source_field):
    block_id = _block_id("forbidden")
    await _create_output_block_row(
        db_session,
        block_id=block_id,
        variables=[
            {
                "key": "forbidden_value",
                "source_field": source_field,
                "required": True,
                "format": "plain_text",
                "missing_behavior": "block_rendering",
            }
        ],
        template_text="{{forbidden_value}}",
        source_fields=[source_field],
    )

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [block_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200
    block = resp.json()["rendered_blocks"][0]
    assert block["rendered_text"] is None
    assert any(item["code"] == "forbidden_source_path" for item in block["blockers"])


@pytest.mark.asyncio
async def test_conditions_equals_match_and_mismatch(auth_client, db_session):
    match_id = _block_id("cond-match")
    mismatch_id = _block_id("cond-mismatch")

    condition = {"show_if": {"field": "options.mounting_type", "operator": "equals", "value": "spacers"}}
    await _create_output_block_row(db_session, block_id=match_id, conditions=condition)
    await _create_output_block_row(
        db_session,
        block_id=mismatch_id,
        conditions={"show_if": {"field": "options.mounting_type", "operator": "equals", "value": "flush"}},
    )

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [match_id, mismatch_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200
    blocks = resp.json()["rendered_blocks"]
    assert blocks[0]["skipped"] is False
    assert blocks[0]["rendered_text"] is not None
    assert blocks[1]["skipped"] is True
    assert blocks[1]["skip_reason"] == "conditions_not_matched"


@pytest.mark.asyncio
async def test_regex_condition_operator_is_blocked(auth_client, db_session):
    block_id = _block_id("cond-regex")
    await _create_output_block_row(
        db_session,
        block_id=block_id,
        conditions={"show_if": {"field": "options.mounting_type", "operator": "regex", "value": "sp.*"}},
    )

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [block_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200
    block = resp.json()["rendered_blocks"][0]
    assert block["skipped"] is True
    assert any(item["code"] == "unsupported_condition_operator" for item in block["blockers"])


@pytest.mark.asyncio
async def test_not_equals_condition_operator_is_blocked(auth_client, db_session):
    block_id = _block_id("cond-not-equals")
    await _create_output_block_row(
        db_session,
        block_id=block_id,
        conditions={"show_if": {"field": "options.mounting_type", "operator": "not_equals", "value": "flush"}},
    )

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [block_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200
    block = resp.json()["rendered_blocks"][0]
    assert block["skipped"] is True
    assert any(item["code"] == "unsupported_condition_operator" for item in block["blockers"])


@pytest.mark.asyncio
async def test_preview_does_not_mutate_quote_order_inventory(auth_client, db_session):
    block_id = _block_id("no-mutate")
    await _create_output_block_row(db_session, block_id=block_id)

    before_quotes = await db_session.scalar(select(func.count(Quotes.id)))
    before_orders = await db_session.scalar(select(func.count(Orders.id)))
    before_inventory = await db_session.scalar(select(func.count(Inventory_materials.id)))
    before_blocks = await db_session.scalar(select(func.count(OutputBlock.id)))

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [block_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200

    after_quotes = await db_session.scalar(select(func.count(Quotes.id)))
    after_orders = await db_session.scalar(select(func.count(Orders.id)))
    after_inventory = await db_session.scalar(select(func.count(Inventory_materials.id)))
    after_blocks = await db_session.scalar(select(func.count(OutputBlock.id)))

    assert int(before_quotes or 0) == int(after_quotes or 0)
    assert int(before_orders or 0) == int(after_orders or 0)
    assert int(before_inventory or 0) == int(after_inventory or 0)
    assert int(before_blocks or 0) == int(after_blocks or 0)


@pytest.mark.asyncio
async def test_preview_response_shape_includes_usage_and_top_level_arrays(auth_client, db_session):
    block_id = _block_id("response-shape")
    await _create_output_block_row(db_session, block_id=block_id)

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [block_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["preview_only"] is True
    assert isinstance(body["warnings"], list)
    assert isinstance(body["blockers"], list)

    block = body["rendered_blocks"][0]
    assert isinstance(block["warnings"], list)
    assert isinstance(block["blockers"], list)
    assert "product_name" in block["variables_used"]
    assert "identity.product_name" in block["source_fields_used"]
