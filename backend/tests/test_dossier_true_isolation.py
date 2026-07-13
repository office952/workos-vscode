"""Tests proving dossier cannot introduce independent runtime structure (v2 pilot)."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import delete, select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from services.template_architecture_scope import VOLUMETRIC_V2_TEMPLATE_CODE


async def _seed_v2_with_dossier_shadow(
    session,
    *,
    dossier_status: str = "approved",
) -> str:
    template_code = VOLUMETRIC_V2_TEMPLATE_CODE
    existing = await session.execute(
        select(Product_templates).where(Product_templates.template_code == template_code)
    )
    existing_row = existing.scalar_one_or_none()
    if existing_row is not None:
        await session.execute(
            delete(ProductBlueprintDossier).where(
                ProductBlueprintDossier.template_id == existing_row.id
            )
        )
        await session.execute(
            delete(Product_templates).where(Product_templates.id == existing_row.id)
        )
        await session.commit()

    parent_components = [
        {
            "component_id": "comp_face_litere",
            "type": "LITERE_3D",
            "name": "Canonical face",
        }
    ]
    template = Product_templates(
        template_code=template_code,
        family_id="signage",
        family_name="Signage",
        description="True isolation test",
        components_json=json.dumps(parent_components),
        operations_json=json.dumps([{"operation_id": "face_cnc_cut", "component_ref": "comp_face_litere"}]),
        required_materials_json=json.dumps(
            [{"code": "MAT-PLEXI", "calculation_type": "formula_based", "formula_id": "F1"}]
        ),
        active=True,
    )
    session.add(template)
    await session.flush()

    dossier = ProductBlueprintDossier(
        template_id=template.id,
        template_code=template_code,
        dossier_version=99,
        status=dossier_status,
        sections_json=json.dumps(
            {
                "components": [
                    {"id": "comp_dossier_only", "label": "Dossier shadow component"},
                ]
            }
        ),
        variants_json=json.dumps(
            [
                {
                    "variant_key": "return_depth_mm",
                    "allowed_values": [999],
                    "default_value": 999,
                }
            ]
        ),
        costengine_mapping_json=json.dumps(
            {"material_keys": ["MAT-DOSSIER"], "operation_keys": ["OP-DOSSIER"]}
        ),
        task_rules_json=json.dumps({"rules": [{"task_code": "DOSSIER-TASK"}]}),
        output_blocks_json=json.dumps({"blocks": [{"block_id": "dossier-only"}]}),
    )
    session.add(dossier)
    await session.commit()
    return template_code


def test_approved_dossier_cannot_introduce_independent_component(auth_client, db_fixture) -> None:
    async def _seed() -> str:
        async with db_fixture.session_maker() as session:
            return await _seed_v2_with_dossier_shadow(session, dossier_status="approved")

    template_code = db_fixture.run(_seed())

    resp = auth_client.get(f"/api/v1/product-system/aggregate/{template_code}")
    assert resp.status_code == 200
    body = resp.json()

    component_ids = {c["component_id"] for c in body["components"]}
    assert "comp_face_litere" in component_ids
    assert "comp_dossier_only" not in component_ids
    assert all(c.get("provenance") == "parent" for c in body["components"])
    assert body["provenance_summary"]["dossier"]["components"] == 0
    warning_codes = {w["code"] for w in body["warnings"]}
    assert "CANONICAL_CONTRACT_AUTHORITY" in warning_codes


def test_approved_dossier_cannot_introduce_independent_operation_mapping(auth_client, db_fixture) -> None:
    async def _seed() -> str:
        async with db_fixture.session_maker() as session:
            return await _seed_v2_with_dossier_shadow(session, dossier_status="approved")

    template_code = db_fixture.run(_seed())

    resp = auth_client.get(f"/api/v1/product-system/aggregate/{template_code}")
    body = resp.json()

    material_codes = {m["material_code"] for m in body["materials"]}
    assert "MAT-DOSSIER" not in material_codes
    operation_codes = {o["operation_code"] for o in body["operations"]}
    assert "OP-DOSSIER" not in operation_codes


@pytest.mark.asyncio
async def test_intake_v6_uses_canonical_variants_not_dossier_override(db_fixture) -> None:
    import uuid

    from services.intake_v6_template_option_contract_service import (
        get_template_form_contract_for_workspace,
    )

    async with db_fixture.session_maker() as session:
        await _seed_v2_with_dossier_shadow(session, dossier_status="approved")
        workspace_id = str(uuid.uuid4())
        session.add(
            IntakeV6WorkspaceRecord(
                id=workspace_id,
                workspace_code=f"WS-{workspace_id[:8]}",
                title="Isolation workspace",
                template_code=VOLUMETRIC_V2_TEMPLATE_CODE,
                payload_json=json.dumps(
                    {
                        "schema_version": "intake_v6_workspace_payload_v1",
                        "product_binding": {"template_code": VOLUMETRIC_V2_TEMPLATE_CODE},
                        "finish_setup": None,
                    }
                ),
                status="draft",
            )
        )
        await session.commit()
        contract = await get_template_form_contract_for_workspace(session, workspace_id)

    assert contract.dossier_source == "canonical_template_contract"
    return_depth_field = next(
        field for field in contract.variant_fields if field.get("field_key") == "return_depth_mm"
    )
    assert 999 not in (return_depth_field.get("allowed_values") or [])
    assert 60 in (return_depth_field.get("allowed_values") or [])
