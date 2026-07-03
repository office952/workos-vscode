from __future__ import annotations

import json

from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates


def _canonical_costengine_mapping() -> dict:
    return {
        "version": "27.09N",
        "template_code": "TPL-PLEXI-PLATE",
        "family_id": "plexi_cnc",
        "status": "draft_structural_mapping",
        "quote_ready": False,
        "pricing_ready": False,
        "inputs": {
            "required": ["width_mm", "height_mm", "thickness_mm", "quantity"],
            "optional": ["material_type", "print_option"],
        },
        "derived_primitives": {
            "area_m2": "width_mm * height_mm / 1000000 * quantity",
            "cut_length_m": "2 * (width_mm + height_mm) / 1000 * quantity",
        },
        "material_keys": ["plexiglass_sheet", "printed_vinyl"],
        "operation_keys": ["prepress", "cnc_laser_cut", "qc"],
        "cost_basis_refs": {
            "material_unit_cost_ref": "configured_material_catalog",
            "operation_rate_ref": "configured_operation_rates",
            "machine_rate_ref": "configured_machine_rates",
            "labor_rate_ref": "configured_labor_rates",
        },
        "readiness_notes": ["Structural mapping only."],
    }


async def _create_template(db_session, *, code: str, active: bool):
    row = Product_templates(
        template_code=code,
        family_id="plexi_cnc",
        family_name="Plexi CNC",
        description="BUILD 27.09T readiness policy test",
        active=active,
        components_json=json.dumps([
            {
                "component_id": "comp_plexi",
                "type": "PLEXI_PANEL",
                "name": "Plexi panel",
            }
        ]),
        operations_json=json.dumps([
            {
                "code": "cnc_laser_cut",
                "name": "Laser cut",
                "workcenter": "LASER_CUTTING",
                "estimatedMinutes": 10,
                "sequence": 1,
                "component_ref": "comp_plexi",
                "calculation_type": "static",
            }
        ]),
        required_materials_json=json.dumps([
            {
                "materialCode": "MAT-PLEXI-TRANSP-3MM",
                "quantity": 0.0,
                "unit": "sqm",
                "component_ref": "comp_plexi",
                "calculation_type": "formula_based",
                "formula_id": "area_with_waste",
                "formula_params": {
                    "waste_pct": 0.05,
                    "thickness_options_mm": [3, 5, 10],
                },
            }
        ]),
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
    status: str,
    cost_map: dict | None = None,
):
    row = ProductBlueprintDossier(
        template_id=template_id,
        template_code=template_code,
        dossier_version=1,
        status=status,
        costengine_mapping_json=json.dumps(cost_map) if cost_map is not None else None,
        output_blocks_json=json.dumps({"short_description": "Ready output"}),
        visual_prompt_blocks_json=json.dumps({"prompt": "Ready visual"}),
        task_rules_json=json.dumps({"rules": [{"task_name": "Cut", "trigger_condition": "always"}]}),
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


def test_draft_active_all_sections_ready_stays_draft(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, code="TPL-27-09T-DRAFT", active=True)
            await _create_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="draft",
                cost_map=_canonical_costengine_mapping(),
            )
            return tpl.id

    template_id = db_fixture.run(_seed())

    response = auth_client.get(f"/api/v1/product-readiness/blueprints/{template_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["overall_status"] == "draft"
    assert body["ready_for_quote"] is False


def test_needs_review_active_all_sections_ready_stays_not_quote_ready(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, code="TPL-27-09T-REVIEW", active=True)
            await _create_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="needs_review",
                cost_map=_canonical_costengine_mapping(),
            )
            return tpl.id

    template_id = db_fixture.run(_seed())

    response = auth_client.get(f"/api/v1/product-readiness/blueprints/{template_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["overall_status"] == "needs_review"
    assert body["ready_for_quote"] is False


def test_approved_active_all_sections_ready_can_quote_ready(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, code="TPL-27-09T-APPROVED", active=True)
            await _create_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="approved",
                cost_map=_canonical_costengine_mapping(),
            )
            return tpl.id

    template_id = db_fixture.run(_seed())

    response = auth_client.get(f"/api/v1/product-readiness/blueprints/{template_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["overall_status"] == "ready"
    assert body["ready_for_quote"] is True


def test_inactive_approved_template_stays_blocked(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, code="TPL-27-09T-INACTIVE", active=False)
            await _create_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="approved",
                cost_map=_canonical_costengine_mapping(),
            )
            return tpl.id

    template_id = db_fixture.run(_seed())

    response = auth_client.get(f"/api/v1/product-readiness/blueprints/{template_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["overall_status"] == "blocked"
    assert body["ready_for_quote"] is False
    assert "template_inactive" in body["technical_readiness"]["blockers"]


def test_approved_transition_accepts_canonical_costengine_mapping(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, code="TPL-27-09T-APPROVAL-OK", active=False)
            return tpl.id, tpl.template_code

    template_id, template_code = db_fixture.run(_seed())

    dossier_response = auth_client.post(
        "/api/v1/entities/product-blueprint-dossiers",
        json={
            "template_id": template_id,
            "template_code": template_code,
            "status": "draft",
            "costengine_mapping_json": json.dumps(_canonical_costengine_mapping()),
        },
    )
    assert dossier_response.status_code == 201, dossier_response.text
    dossier = dossier_response.json()

    review_response = auth_client.put(
        f"/api/v1/entities/product-blueprint-dossiers/{dossier['id']}",
        json={"status": "needs_review"},
    )
    assert review_response.status_code == 200, review_response.text

    approve_response = auth_client.put(
        f"/api/v1/entities/product-blueprint-dossiers/{dossier['id']}",
        json={"status": "approved"},
    )
    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json()["status"] == "approved"


def test_approved_transition_rejects_invalid_costengine_mapping(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, code="TPL-27-09T-APPROVAL-BAD", active=False)
            return tpl.id, tpl.template_code

    template_id, template_code = db_fixture.run(_seed())

    dossier_response = auth_client.post(
        "/api/v1/entities/product-blueprint-dossiers",
        json={
            "template_id": template_id,
            "template_code": template_code,
            "status": "draft",
            "costengine_mapping_json": json.dumps({"version": "27.09N"}),
        },
    )
    assert dossier_response.status_code == 201, dossier_response.text
    dossier = dossier_response.json()

    review_response = auth_client.put(
        f"/api/v1/entities/product-blueprint-dossiers/{dossier['id']}",
        json={"status": "needs_review"},
    )
    assert review_response.status_code == 200, review_response.text

    approve_response = auth_client.put(
        f"/api/v1/entities/product-blueprint-dossiers/{dossier['id']}",
        json={"status": "approved"},
    )
    assert approve_response.status_code == 422
    assert "costengine_mapping_json" in approve_response.text


def test_pricing_gate_blocks_needs_review_even_when_sections_ready(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, code="TPL-27-09T-PRICE-GATE", active=True)
            await _create_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="needs_review",
                cost_map=_canonical_costengine_mapping(),
            )
            return tpl.id, tpl.template_code, tpl.required_materials_json, tpl.components_json, tpl.operations_json

    template_id, template_code, required_materials_json, components_json, operations_json = db_fixture.run(_seed())

    response = auth_client.post(
        "/api/v1/entities/quotes/price",
        json={
            "product_template": {
                "id": template_id,
                "template_code": template_code,
                "family_id": "plexi_cnc",
                "family_name": "Plexi CNC",
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
            "client_name": "27.09T Pricing Gate",
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    readiness_result = detail["readiness_result"]
    assert readiness_result["overall_status"] == "needs_review"
    assert readiness_result["ready_for_quote"] is False
    assert any(reason.startswith("readiness_blocked:") for reason in detail["blocked_reasons"])


def test_no_false_ready_regression_for_needs_review(auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            tpl = await _create_template(session, code="TPL-27-09T-NO-FALSE-READY", active=True)
            await _create_dossier(
                session,
                template_id=tpl.id,
                template_code=tpl.template_code,
                status="needs_review",
                cost_map=_canonical_costengine_mapping(),
            )
            return tpl.id

    template_id = db_fixture.run(_seed())

    response = auth_client.get(f"/api/v1/product-readiness/blueprints/{template_id}")
    assert response.status_code == 200
    body = response.json()
    assert not (body["overall_status"] == "needs_review" and body["ready_for_quote"] is True)