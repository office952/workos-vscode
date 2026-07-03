import json
import uuid

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.output_blocks import OutputBlock
from models.quotes import Quotes
from models.rendered_output_snapshots import RenderedOutputSnapshot


def _block_id(prefix: str = "ob-snap") -> str:
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
        title="Snapshot block",
        purpose="Snapshot validation",
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
    await db_session.refresh(row)
    return row


async def _create_quote_row(db_session, quote_id: int = 1001) -> Quotes:
    row = Quotes(
        id=quote_id,
        code=f"Q-{quote_id}",
        intake_id=None,
        intake_code=None,
        client_id=501,
        client_name="Client Test",
        contact_person="Operator",
        status="draft",
        version=1,
        valid_until="2026-12-31",
        line_items=json.dumps({"product_definition": {"name": "Placa plexiglass"}}),
        subtotal=100.0,
        discount=0.0,
        discount_pct=0.0,
        total_before_vat=100.0,
        vat=19.0,
        grand_total=119.0,
        margin_pct=10.0,
        notes="unchanged",
        assigned_to="tester",
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _create_order_row(db_session, order_id: int = 2001, quote_id: int = 1001) -> Orders:
    row = Orders(
        id=order_id,
        code=f"ORD-{order_id}",
        quote_id=quote_id,
        quote_code=f"Q-{quote_id}",
        client_id=501,
        client_name="Client Test",
        contact_person="Operator",
        status="accepted",
        product_summary="Frozen order",
        total_amount=119.0,
        locked_at="2026-05-28T10:00:00",
        promised_delivery="2026-06-15",
        job_id=None,
        payment_status="pending",
        snapshot_version=1,
        snapshot_line_items=json.dumps({"is_locked": True, "quote_snapshot": {"status": "priced"}}),
        notes="do not rewrite",
        readiness_snapshot={"overall_status": "ready"},
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _snapshot_count(db_session) -> int:
    return (await db_session.execute(select(func.count(RenderedOutputSnapshot.id)))).scalar() or 0


@pytest.mark.asyncio
async def test_preview_route_remains_non_persistent(auth_client, db_session):
    block_id = _block_id("preview-nonpersistent")
    await _create_output_block_row(db_session, block_id=block_id)
    before = await _snapshot_count(db_session)

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": [block_id],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
        },
    )

    after = await _snapshot_count(db_session)
    assert resp.status_code == 200
    assert resp.json()["preview_only"] is True
    assert before == after


@pytest.mark.asyncio
async def test_snapshot_creation_happy_path_persists_rendered_output(auth_client, db_session):
    block_id = _block_id("snapshot-ok")
    await _create_output_block_row(db_session, block_id=block_id)
    quote = await _create_quote_row(db_session, quote_id=1002)
    order = await _create_order_row(db_session, order_id=2002, quote_id=quote.id)

    quote_before = {
        "status": quote.status,
        "subtotal": quote.subtotal,
        "grand_total": quote.grand_total,
        "notes": quote.notes,
    }
    order_before = {
        "status": order.status,
        "snapshot_line_items": order.snapshot_line_items,
        "notes": order.notes,
    }
    inventory_before = (await db_session.execute(select(func.count(Inventory_materials.id)))).scalar() or 0
    execution_plan_before = (await db_session.execute(select(func.count(ExecutionPlan.id)))).scalar() or 0
    execution_reality_before = (await db_session.execute(select(func.count(ExecutionReality.id)))).scalar() or 0

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/snapshots",
        json={
            "block_ids": [block_id],
            "context": "quote_snapshot",
            "source_payload": _source_payload_complete(),
            "document_type": "offer",
            "audience": "client",
            "snapshot_purpose": "quote_document_candidate",
            "target_type": "quote",
            "target_id": quote.id,
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["preview_only"] is False
    assert body["snapshot_status"] == "created"
    assert body["target_type"] == "quote"
    assert body["target_id"] == quote.id
    assert body["rendered_blocks"][0]["rendered_text"] == "Placa plexiglass test realizat din plexiglass transparent."
    assert body["rendered_blocks"][0]["variables_used"] == {
        "product_name": "Placa plexiglass test",
        "main_material": "plexiglass transparent",
    }
    assert body["rendered_blocks"][0]["source_fields_used"] == ["identity.product_name", "materials.main_material"]

    snapshot = await db_session.get(RenderedOutputSnapshot, body["snapshot_id"])
    assert snapshot is not None
    assert snapshot.context == "quote_snapshot"
    assert snapshot.document_type == "offer"
    assert snapshot.audience == "client"
    assert snapshot.target_type == "quote"
    assert snapshot.target_id == str(quote.id)
    persisted_blocks = json.loads(snapshot.rendered_blocks_json)
    assert persisted_blocks[0]["approval_status"] == "approved"
    assert persisted_blocks[0]["block_version"] == "1.0.0"
    assert persisted_blocks[0]["rendered_text"] == "Placa plexiglass test realizat din plexiglass transparent."

    await db_session.refresh(quote)
    await db_session.refresh(order)
    inventory_after = (await db_session.execute(select(func.count(Inventory_materials.id)))).scalar() or 0
    execution_plan_after = (await db_session.execute(select(func.count(ExecutionPlan.id)))).scalar() or 0
    execution_reality_after = (await db_session.execute(select(func.count(ExecutionReality.id)))).scalar() or 0

    assert {"status": quote.status, "subtotal": quote.subtotal, "grand_total": quote.grand_total, "notes": quote.notes} == quote_before
    assert {"status": order.status, "snapshot_line_items": order.snapshot_line_items, "notes": order.notes} == order_before
    assert inventory_before == inventory_after
    assert execution_plan_before == execution_plan_after
    assert execution_reality_before == execution_reality_after


@pytest.mark.asyncio
async def test_snapshot_creation_rejects_draft_block(auth_client, db_session):
    block_id = _block_id("snapshot-draft")
    await _create_output_block_row(db_session, block_id=block_id, approval_status="draft")
    await _create_quote_row(db_session, quote_id=1003)
    before = await _snapshot_count(db_session)

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/snapshots",
        json={
            "block_ids": [block_id],
            "context": "quote_snapshot",
            "source_payload": _source_payload_complete(),
            "document_type": "offer",
            "audience": "client",
            "snapshot_purpose": "quote_document_candidate",
            "target_type": "quote",
            "target_id": 1003,
        },
    )

    after = await _snapshot_count(db_session)
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["error"] == "rendered_output_snapshot_blocked"
    assert detail["snapshot"]["blockers"][0]["code"] == "approval_status_not_allowed_for_snapshot"
    assert before == after


@pytest.mark.asyncio
async def test_snapshot_creation_rejects_missing_required_variable(auth_client, db_session):
    block_id = _block_id("snapshot-missing")
    await _create_output_block_row(db_session, block_id=block_id)
    await _create_quote_row(db_session, quote_id=1004)
    before = await _snapshot_count(db_session)

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/snapshots",
        json={
            "block_ids": [block_id],
            "context": "quote_snapshot",
            "source_payload": {"identity": {"product_name": "Placa plexiglass test"}, "materials": {}},
            "document_type": "offer",
            "audience": "client",
            "snapshot_purpose": "quote_document_candidate",
            "target_type": "quote",
            "target_id": 1004,
        },
    )

    after = await _snapshot_count(db_session)
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["error"] == "rendered_output_snapshot_blocked"
    blocker_codes = [item["code"] for item in detail["snapshot"]["blockers"]]
    assert "required_variable_missing" in blocker_codes
    assert before == after


@pytest.mark.asyncio
async def test_snapshot_creation_invalid_context_rejected(auth_client):
    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/snapshots",
        json={
            "block_ids": ["missing-id"],
            "context": "quote_preview",
            "source_payload": _source_payload_complete(),
            "document_type": "offer",
            "audience": "client",
            "snapshot_purpose": "quote_document_candidate",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "rendered_output_snapshot_validation_error"


@pytest.mark.asyncio
async def test_snapshot_creation_missing_selector_rejected(auth_client):
    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/snapshots",
        json={
            "context": "quote_snapshot",
            "source_payload": _source_payload_complete(),
            "document_type": "offer",
            "audience": "client",
            "snapshot_purpose": "quote_document_candidate",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "rendered_output_snapshot_validation_error"


@pytest.mark.asyncio
async def test_snapshot_creation_missing_target_returns_404(auth_client, db_session):
    block_id = _block_id("snapshot-missing-target")
    await _create_output_block_row(db_session, block_id=block_id)

    resp = auth_client.post(
        "/api/v1/product-system/output-blocks/snapshots",
        json={
            "block_ids": [block_id],
            "context": "quote_snapshot",
            "source_payload": _source_payload_complete(),
            "document_type": "offer",
            "audience": "client",
            "snapshot_purpose": "quote_document_candidate",
            "target_type": "quote",
            "target_id": 999999,
        },
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "quote_not_found"


@pytest.mark.asyncio
async def test_snapshot_is_immutable_after_output_block_changes(auth_client, db_session):
    block_id = _block_id("snapshot-immutable")
    block = await _create_output_block_row(db_session, block_id=block_id)
    await _create_quote_row(db_session, quote_id=1005)

    create_resp = auth_client.post(
        "/api/v1/product-system/output-blocks/snapshots",
        json={
            "block_ids": [block_id],
            "context": "quote_snapshot",
            "source_payload": _source_payload_complete(),
            "document_type": "offer",
            "audience": "client",
            "snapshot_purpose": "quote_document_candidate",
            "target_type": "quote",
            "target_id": 1005,
        },
    )
    assert create_resp.status_code == 201
    snapshot_id = create_resp.json()["snapshot_id"]

    block.template_text = "CHANGED {{product_name}}"
    block.approval_status = "deprecated"
    await db_session.commit()

    snapshot = await db_session.get(RenderedOutputSnapshot, snapshot_id)
    persisted_blocks = json.loads(snapshot.rendered_blocks_json)
    assert persisted_blocks[0]["rendered_text"] == "Placa plexiglass test realizat din plexiglass transparent."
    assert persisted_blocks[0]["approval_status"] == "approved"
