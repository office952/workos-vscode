from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.clients import Clients
from models.intake_requests import Intake_requests
from models.orders import Orders
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from models.quotes import Quotes


async def _count_mutation_tables(db_session):
    clients_count = await db_session.scalar(select(func.count(Clients.id)))
    intake_count = await db_session.scalar(select(func.count(Intake_requests.id)))
    quotes_count = await db_session.scalar(select(func.count(Quotes.id)))
    orders_count = await db_session.scalar(select(func.count(Orders.id)))
    return (
        int(clients_count or 0),
        int(intake_count or 0),
        int(quotes_count or 0),
        int(orders_count or 0),
    )


async def _create_template(db_session, *, family_id: str | None = "signage", active: bool = True, materials: list | None = None):
    row = Product_templates(
        template_code="T-READINESS",
        family_id=family_id,
        family_name="Signage" if family_id else "",
        description="Readiness template",
        components_json="[]",
        operations_json="[]",
        required_materials_json=json.dumps(materials if materials is not None else [{"materialCode": "MAT-01", "quantity": 1, "unit": "pcs"}]),
        active=active,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _upsert_dossier(
    db_session,
    *,
    template_id: int,
    template_code: str,
    status: str = "draft",
    cost_map: dict | None = None,
    output_blocks: dict | None = None,
    visual_blocks: dict | None = None,
    task_rules: dict | None = None,
):
    dossier = ProductBlueprintDossier(
        template_id=template_id,
        template_code=template_code,
        dossier_version=1,
        status=status,
        costengine_mapping_json=json.dumps(cost_map) if cost_map is not None else None,
        output_blocks_json=json.dumps(output_blocks) if output_blocks is not None else None,
        visual_prompt_blocks_json=json.dumps(visual_blocks) if visual_blocks is not None else None,
        task_rules_json=json.dumps(task_rules) if task_rules is not None else None,
    )
    db_session.add(dossier)
    await db_session.commit()
    await db_session.refresh(dossier)
    return dossier


def test_missing_identity_or_family_blocked(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            row = await _create_template(session, family_id=None)
            return row.id

    template_id = db_fixture.run(_seed())

    resp = auth_client.get(f"/api/v1/product_system/readiness/{template_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall_status"] == "blocked"
    assert "family_missing" in body["technical_readiness"]["blockers"]
    assert body["entity_type"] == "blueprint"
    assert body["source"] == "backend"
    assert body["contract_version"] == "2026-05-15"
    assert body["policy"]["authority"] == "backend"
    assert body["policy"]["quote_gate"] == "enforced"
    assert body["policy"]["order_snapshot"] == "quote_snapshot_frozen"


def test_blueprint_alias_route_returns_same_contract(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session)
            await _upsert_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="needs_review",
                cost_map={"labor": "mapped"},
                output_blocks={"short_description": "Short output"},
                visual_blocks={"prompt": "Visual prompt block"},
                task_rules={"sequence": ["cut", "assembly"]},
            )
            return tpl.id

    template_id = db_fixture.run(_seed())

    legacy = auth_client.get(f"/api/v1/product_system/readiness/{template_id}")
    alias = auth_client.get(f"/api/v1/product-readiness/blueprints/{template_id}")

    assert legacy.status_code == 200
    assert alias.status_code == 200

    legacy_body = legacy.json()
    alias_body = alias.json()

    assert legacy_body["entity_id"] == alias_body["entity_id"]
    assert legacy_body["overall_status"] == alias_body["overall_status"]
    assert legacy_body["ready_for_quote"] == alias_body["ready_for_quote"]
    assert alias_body["contract_version"] == "2026-05-15"


def test_readiness_endpoint_requires_auth(unauth_client):
    response = unauth_client.get("/api/v1/product-readiness/blueprints/1")
    assert response.status_code in {401, 403}


def test_deprecated_blueprint_blocked(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session)
            await _upsert_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="deprecated",
                cost_map={"labor": "mapped"},
            )
            return tpl.id

    template_id = db_fixture.run(_seed())

    resp = auth_client.get(f"/api/v1/product_system/readiness/{template_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall_status"] == "blocked"
    assert "blueprint_deprecated" in body["technical_readiness"]["blockers"]


def test_missing_costengine_mapping_blocked(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session)
            await _upsert_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="needs_review",
                cost_map=None,
            )
            return tpl.id

    template_id = db_fixture.run(_seed())
    resp = auth_client.get(f"/api/v1/product_system/readiness/{template_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["costengine_readiness"]["status"] == "blocked"
    assert "costengine_mapping_missing" in body["costengine_readiness"]["blockers"]


def test_complete_minimal_blueprint_needs_review_not_quote_ready(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session)
            await _upsert_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="needs_review",
                cost_map={"labor": "mapped"},
                output_blocks={"short_description": "Short output"},
                visual_blocks={"prompt": "Visual prompt block"},
                task_rules={"sequence": ["cut", "assembly"]},
            )
            return tpl.id

    template_id = db_fixture.run(_seed())
    resp = auth_client.get(f"/api/v1/product_system/readiness/{template_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall_status"] in {"needs_review", "draft", "blocked"}
    assert body["ready_for_quote"] is False


@pytest.mark.asyncio
async def test_readiness_service_read_only_no_mutation(auth_client, db_session):
    before = await _count_mutation_tables(db_session)
    resp = auth_client.get("/api/v1/product_system/readiness/999999")
    assert resp.status_code == 200
    after = await _count_mutation_tables(db_session)
    assert before == after


def test_quotes_respects_readiness_blockers(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, family_id=None)
            return tpl.id, tpl.template_code

    template_id, template_code = db_fixture.run(_seed())

    payload = {
        "product_template": {
            "id": template_id,
            "template_code": template_code,
            "family_id": None,
            "family_name": "",
            "required_materials_json": "[]",
            "components_json": "[]",
            "operations_json": "[]",
        },
        "user_config": {
            "quantity": 1,
            "dimensions": {"width_mm": 100, "height_mm": 50},
        },
        "client_name": "Readiness Test Client",
    }

    resp = auth_client.post("/api/v1/entities/quotes/price", json=payload)
    assert resp.status_code == 422
    body = resp.json().get("detail", {})
    assert body.get("status") == "blocked"
    reasons = body.get("blocked_reasons", [])
    assert any(str(r).startswith("readiness_blocked:") for r in reasons)
