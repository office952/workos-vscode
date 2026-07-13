from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import delete, select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from services.intake_v6_template_option_contract_service import get_template_form_contract_for_workspace
from services.template_architecture_scope import VOLUMETRIC_V2_TEMPLATE_CODE


def _workspace_payload() -> dict:
    return {
        "schema_version": "intake_v6_workspace_payload_v1",
        "product_binding": {"template_code": VOLUMETRIC_V2_TEMPLATE_CODE},
        "finish_setup": None,
    }


async def _seed_workspace_with_dossier(session, *, dossier_status: str) -> tuple[str, list[dict]]:
    workspace_id = str(uuid.uuid4())
    template_code = VOLUMETRIC_V2_TEMPLATE_CODE
    custom_variants = [
        {
            "variant_key": "return_depth_mm",
            "allowed_values": [999],
            "description": "Test-only dossier variant",
        }
    ]

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
            delete(IntakeV6WorkspaceRecord).where(
                IntakeV6WorkspaceRecord.template_code == template_code
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
        description="Intake V6 dossier gating test",
        components_json="[]",
        operations_json="[]",
        required_materials_json="[]",
        active=True,
    )
    session.add(template)
    await session.flush()

    session.add(
        ProductBlueprintDossier(
            template_id=template.id,
            template_code=template_code,
            dossier_version=1,
            status=dossier_status,
            variants_json=json.dumps(custom_variants),
        )
    )
    session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-{workspace_id[:8]}",
            title="Dossier gating workspace",
            template_code=template_code,
            payload_json=json.dumps(_workspace_payload()),
            status="draft",
        )
    )
    await session.commit()
    return workspace_id, custom_variants


@pytest.mark.asyncio
async def test_unapproved_dossier_variants_ignored(db_fixture) -> None:
    async with db_fixture.session_maker() as session:
        workspace_id, custom_variants = await _seed_workspace_with_dossier(
            session, dossier_status="needs_review"
        )
        contract = await get_template_form_contract_for_workspace(session, workspace_id)

    assert contract.dossier_source == "canonical_template_contract"
    return_depth_field = next(
        field for field in contract.variant_fields if field.get("field_key") == "return_depth_mm"
    )
    assert 999 not in (return_depth_field.get("allowed_values") or [])


@pytest.mark.asyncio
async def test_approved_dossier_variants_do_not_override_canonical(db_fixture) -> None:
    async with db_fixture.session_maker() as session:
        workspace_id, custom_variants = await _seed_workspace_with_dossier(
            session, dossier_status="approved"
        )
        contract = await get_template_form_contract_for_workspace(session, workspace_id)

    assert contract.dossier_source == "canonical_template_contract"
    return_depth_field = next(
        field for field in contract.variant_fields if field.get("field_key") == "return_depth_mm"
    )
    assert 999 not in (return_depth_field.get("allowed_values") or [])
