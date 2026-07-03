from __future__ import annotations

import json

from sqlalchemy import func, select

from models.orders import Orders
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from models.quotes import Quotes
from services.cost_engine_service import CostEngineWithMaterialRates
import services.quote_orchestrator as quote_orchestrator_module


async def _create_template(
    db_session,
    *,
    family_id: str | None = "signage",
    family_name: str | None = "Signage",
    active: bool = True,
    materials: list | None = None,
):
    row = Product_templates(
        template_code="TPL-READINESS-Q",
        family_id=family_id,
        family_name=family_name or "",
        components_json="[]",
        operations_json="[]",
        required_materials_json=json.dumps(materials if materials is not None else [{"materialCode": "MAT-ACP-3", "quantity": 1, "unit": "sqm"}]),
        active=active,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _create_dossier(
    db_session,
    *,
    template_id: int,
    template_code: str,
    status: str = "needs_review",
    cost_map: dict | None = None,
    output_blocks: dict | None = None,
    visual_blocks: dict | None = None,
    task_rules: dict | None = None,
):
    row = ProductBlueprintDossier(
        template_id=template_id,
        template_code=template_code,
        dossier_version=1,
        status=status,
        costengine_mapping_json=json.dumps(cost_map) if cost_map is not None else None,
        output_blocks_json=json.dumps(output_blocks) if output_blocks is not None else None,
        visual_prompt_blocks_json=json.dumps(visual_blocks) if visual_blocks is not None else None,
        task_rules_json=json.dumps(task_rules) if task_rules is not None else None,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


def _price_payload(template_id: int, template_code: str, *, family_id: str | None = "signage", family_name: str = "Signage") -> dict:
    return {
        "product_template": {
            "id": template_id,
            "template_code": template_code,
            "family_id": family_id,
            "family_name": family_name,
            "required_materials_json": json.dumps([{"materialCode": "MAT-ACP-3", "quantity": 1, "unit": "sqm"}]),
            "components_json": "[]",
            "operations_json": "[]",
            "active": True,
        },
        "user_config": {
            "quantity": 1,
            "dimensions": {"width_mm": 500, "height_mm": 300},
        },
        "pricing": {"margin_pct": 20, "vat_pct": 19},
        "client_name": "Readiness Quote Client",
    }


def test_quote_price_blocked_when_readiness_blockers_exist(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, family_id=None, family_name=None)
            return tpl.id, tpl.template_code

    template_id, template_code = db_fixture.run(_seed())

    response = auth_client.post(
        "/api/v1/entities/quotes/price",
        json=_price_payload(template_id, template_code, family_id=None, family_name=""),
    )

    assert response.status_code == 422
    detail = response.json().get("detail", {})
    assert detail.get("status") == "blocked"
    assert any(str(reason).startswith("readiness_blocked:") for reason in detail.get("blocked_reasons", []))
    assert detail.get("readiness_result", {}).get("ready_for_quote") is False


def test_quote_price_blocks_when_critical_sections_are_needs_review(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session)
            await _create_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="needs_review",
                cost_map={"labor": "mapped"},
                # Keep optional sections empty to force warnings-only readiness.
                output_blocks=None,
                visual_blocks=None,
                task_rules=None,
            )
            return tpl.id, tpl.template_code

    template_id, template_code = db_fixture.run(_seed())

    original_init = quote_orchestrator_module.QuoteOrchestrator.__init__

    def patched_init(self, product_service=None, cost_engine=None, **kwargs):
        original_init(
            self,
            product_service=product_service,
            cost_engine=cost_engine or CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
            **kwargs,
        )

    quote_orchestrator_module.QuoteOrchestrator.__init__ = patched_init
    try:
        response = auth_client.post(
            "/api/v1/entities/quotes/price",
            json=_price_payload(template_id, template_code),
        )
    finally:
        quote_orchestrator_module.QuoteOrchestrator.__init__ = original_init

    assert response.status_code == 422, response.text
    detail = response.json().get("detail", {})
    assert detail.get("status") == "blocked"
    assert any(str(reason).startswith("readiness_blocked:") for reason in detail.get("blocked_reasons", []))
    readiness = detail.get("readiness_result")
    assert isinstance(readiness, dict)
    assert readiness.get("ready_for_quote") is False
    assert readiness.get("overall_status") in {"needs_review", "draft", "blocked"}


def test_blocked_readiness_does_not_create_quote_or_order(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, family_id=None, family_name=None)
            return tpl.id, tpl.template_code

    template_id, template_code = db_fixture.run(_seed())

    async def _counts():
        async with db_fixture.session_maker() as session:
            quotes_count = await session.scalar(select(func.count(Quotes.id)))
            orders_count = await session.scalar(select(func.count(Orders.id)))
            return int(quotes_count or 0), int(orders_count or 0)

    before_quotes, before_orders = db_fixture.run(_counts())

    response = auth_client.post(
        "/api/v1/entities/quotes/price",
        json=_price_payload(template_id, template_code, family_id=None, family_name=""),
    )

    assert response.status_code == 422

    after_quotes, after_orders = db_fixture.run(_counts())
    assert before_quotes == after_quotes
    assert before_orders == after_orders
