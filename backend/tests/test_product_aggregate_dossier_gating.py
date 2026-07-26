from __future__ import annotations

import json

import pytest
from sqlalchemy import delete, select

from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from services.template_architecture_scope import VOLUMETRIC_V2_TEMPLATE_CODE


async def _seed_template_with_dossier(
    session,
    *,
    dossier_status: str,
    sections: dict | None = None,
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

    template = Product_templates(
        template_code=template_code,
        family_id="signage",
        family_name="Signage",
        description="Aggregate dossier gating test",
        components_json=json.dumps(
            [
                {
                    "component_id": "comp_face_litere",
                    "type": "LITERE_3D",
                    "name": "Face",
                }
            ]
        ),
        operations_json="[]",
        required_materials_json="[]",
        active=True,
    )
    session.add(template)
    await session.flush()

    dossier = ProductBlueprintDossier(
        template_id=template.id,
        template_code=template_code,
        dossier_version=1,
        status=dossier_status,
        sections_json=json.dumps(
            sections
            or {
                "components": [
                    {
                        "id": "comp_face_litere",
                        "label": "Face",
                    }
                ]
            }
        ),
        costengine_mapping_json=json.dumps(
            {"material_keys": ["MAT-TEST"], "operation_keys": ["OP-TEST"]}
        ),
        task_rules_json=json.dumps({"rules": [{"task_code": "TASK-1"}]}),
    )
    session.add(dossier)
    await session.commit()
    return template_code


def test_unapproved_dossier_ignored_for_behavior_bearing_fields(auth_client, db_fixture) -> None:
    async def _seed() -> str:
        async with db_fixture.session_maker() as session:
            return await _seed_template_with_dossier(session, dossier_status="draft")

    template_code = db_fixture.run(_seed())
    resp = auth_client.get(f"/api/v1/product-system/aggregate/{template_code}")
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["components"]) == 1
    assert body["components"][0]["component_id"] == "comp_face_litere"
    assert body["provenance_summary"]["dossier"]["components"] == 0
    warning_codes = {w["code"] for w in body["warnings"]}
    assert "DOSSIER_METADATA_ONLY" in warning_codes


def test_approved_dossier_cannot_shadow_parent_components(auth_client, db_fixture) -> None:
    async def _seed() -> str:
        async with db_fixture.session_maker() as session:
            return await _seed_template_with_dossier(
                session,
                dossier_status="approved",
                sections={
                    "components": [
                        {"id": "comp_dossier_shadow", "label": "Shadow"},
                    ]
                },
            )

    template_code = db_fixture.run(_seed())
    resp = auth_client.get(f"/api/v1/product-system/aggregate/{template_code}")
    assert resp.status_code == 200
    body = resp.json()

    component_ids = {c["component_id"] for c in body["components"]}
    assert "comp_face_litere" in component_ids
    assert "comp_dossier_shadow" not in component_ids
    assert body["provenance_summary"]["dossier"]["components"] == 0
    warning_codes = {w["code"] for w in body["warnings"]}
    assert "CANONICAL_CONTRACT_AUTHORITY" in warning_codes
