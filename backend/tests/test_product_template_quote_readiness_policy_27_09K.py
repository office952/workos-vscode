from __future__ import annotations

import json

from models.product_templates import Product_templates


async def _create_template(
    db_session,
    *,
    code: str,
    active: bool,
    materials: list | None = None,
    operations: list | None = None,
    components: list | None = None,
):
    row = Product_templates(
        template_code=code,
        family_id="signage",
        family_name="Signage",
        description="BUILD_27_09K readiness policy test",
        components_json=json.dumps(components if components is not None else []),
        operations_json=json.dumps(operations if operations is not None else []),
        required_materials_json=json.dumps(
            materials
            if materials is not None
            else [
                {
                    "materialCode": "MAT-ACP-3",
                    "quantity": 0.0,
                    "unit": "sqm",
                    "calculation_type": "formula_based",
                    "formula_id": "area_with_waste",
                    "formula_params": {"waste_pct": 0.05},
                }
            ]
        ),
        active=active,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


def test_inactive_template_remains_blocked_and_not_quote_ready(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(
                session,
                code="TPL-READINESS-27-09K-INACTIVE",
                active=False,
            )
            return tpl.id

    template_id = db_fixture.run(_seed())

    response = auth_client.get(f"/api/v1/product-readiness/blueprints/{template_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["overall_status"] == "blocked"
    assert body["ready_for_quote"] is False
    assert "template_inactive" in body["technical_readiness"]["blockers"]


def test_active_missing_critical_sections_is_not_quote_ready(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(
                session,
                code="TPL-READINESS-27-09K-CRITICAL-MISSING",
                active=True,
            )
            return tpl.id

    template_id = db_fixture.run(_seed())

    response = auth_client.get(f"/api/v1/product-readiness/blueprints/{template_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["overall_status"] in {"needs_review", "blocked"}
    assert body["ready_for_quote"] is False
    assert "blueprint_dossier_missing" in body["technical_readiness"]["warnings"]
    assert "costengine_mapping_missing_no_dossier" in body["costengine_readiness"]["warnings"]
    assert "output_blocks_missing" in body["document_output_readiness"]["warnings"]
    assert "task_rules_missing" in body["execution_preparation_readiness"]["warnings"]


def test_no_needs_review_true_ready_state(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(
                session,
                code="TPL-READINESS-27-09K-NO-FALSE-READY",
                active=True,
            )
            return tpl.id

    template_id = db_fixture.run(_seed())

    response = auth_client.get(f"/api/v1/product-readiness/blueprints/{template_id}")
    assert response.status_code == 200
    body = response.json()

    assert not (body["overall_status"] == "needs_review" and body["ready_for_quote"] is True)


def test_quote_pricing_blocks_when_readiness_not_ready(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(
                session,
                code="TPL-READINESS-27-09K-PRICE-GATE",
                active=True,
            )
            return tpl.id, tpl.template_code, tpl.required_materials_json, tpl.components_json, tpl.operations_json

    template_id, template_code, required_materials_json, components_json, operations_json = db_fixture.run(_seed())

    payload = {
        "product_template": {
            "id": template_id,
            "template_code": template_code,
            "family_id": "signage",
            "family_name": "Signage",
            "required_materials_json": required_materials_json,
            "components_json": components_json,
            "operations_json": operations_json,
            "active": True,
        },
        "user_config": {
            "quantity": 1,
            "dimensions": {"width_mm": 500, "height_mm": 300},
        },
        "pricing": {"margin_pct": 20, "vat_pct": 19},
        "client_name": "Readiness Policy Client",
    }

    response = auth_client.post("/api/v1/entities/quotes/price", json=payload)
    assert response.status_code == 422

    detail = response.json().get("detail", {})
    assert detail.get("status") == "blocked"
    blocked_reasons = detail.get("blocked_reasons", [])

    assert any(str(reason).startswith("readiness_blocked:") for reason in blocked_reasons)
    assert any(
        token in "|".join(str(reason) for reason in blocked_reasons)
        for token in [
            "blueprint_dossier_missing",
            "document_output_readiness:needs_review",
            "execution_preparation_readiness:needs_review",
        ]
    )

    readiness_result = detail.get("readiness_result", {})
    assert readiness_result.get("ready_for_quote") is False
