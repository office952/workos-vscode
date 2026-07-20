"""Real product configuration proofs for TPL-VOLUMETRIC-LETTERS_v2.

Composition / contracts / readiness / publication blocker / no Aluminiu activation.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select

from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from schemas.product_template_publication import ProductTemplatePublicationTransitionRequest
from services.product_aggregate_service import ProductAggregateService
from services.product_e2e_readiness_service import ProductE2EReadinessService
from services.product_template_component_contract_service import (
    ProductTemplateComponentContractService,
)
from services.product_template_publication_service import ProductTemplatePublicationService
from tests.test_product_aggregate_volumetric_v2 import (
    CHILD_ALUMINUM,
    CHILD_BACK,
    CHILD_FACE,
    CHILD_FINISH,
    CHILD_LED,
    CHILD_PREMOUNT,
    TEMPLATE_CODE,
    _seed_volumetric_v2_fixture,
)

REQUIRED_CHILDREN = {
    CHILD_FACE,
    CHILD_BACK,
    CHILD_ALUMINUM,
    CHILD_LED,
    CHILD_FINISH,
}


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    return db_session


@pytest.mark.asyncio
async def test_vl_composition_has_required_component_children(volumetric_v2_db):
    links = (
        await volumetric_v2_db.execute(
            select(ProductTemplateModuleLink).where(
                ProductTemplateModuleLink.parent_template_code == TEMPLATE_CODE,
                ProductTemplateModuleLink.active.is_(True),
            )
        )
    ).scalars().all()
    by_child = {str(link.module_template_code): link for link in links}
    assert REQUIRED_CHILDREN.issubset(set(by_child))
    assert CHILD_PREMOUNT in by_child
    assert by_child[CHILD_PREMOUNT].relation_type == "optional_addon"
    for code in REQUIRED_CHILDREN:
        assert by_child[code].relation_type == "required_module"
        assert by_child[code].usage_mode == "linked_child"
        assert by_child[code].instance_schema_id


@pytest.mark.asyncio
async def test_vl_component_contract_exposes_geometry_inputs_consume_only(volumetric_v2_db):
    view = await ProductTemplateComponentContractService(volumetric_v2_db).get_contract(
        TEMPLATE_CODE
    )
    assert view.geometry_inputs_consume_only is True
    assert "letter_face_area_m2" in view.geometry_input_hints
    assert "external_artwork_analysis_ref" in view.geometry_input_hints
    child_codes = {c.module_template_code for c in view.children}
    assert REQUIRED_CHILDREN.issubset(child_codes)


@pytest.mark.asyncio
async def test_vl_aggregate_pulls_linked_face_ops(volumetric_v2_db):
    aggregate = await ProductAggregateService(volumetric_v2_db).build(TEMPLATE_CODE)
    assert aggregate is not None
    op_codes = {op.operation_code for op in aggregate.operations}
    assert "face_cnc_cut" in op_codes
    face_ops = [op for op in aggregate.operations if op.source_template_code == CHILD_FACE]
    assert face_ops
    assert all(op.provenance == "linked_module" for op in face_ops)


@pytest.mark.asyncio
async def test_vl_readiness_blocks_publication_on_inactive_aluminiu(volumetric_v2_db):
    child = (
        await volumetric_v2_db.execute(
            select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM).limit(1)
        )
    ).scalar_one()
    child.active = False
    await volumetric_v2_db.commit()

    result = await ProductE2EReadinessService(volumetric_v2_db).run_static(TEMPLATE_CODE)
    assert result.write_performed is False
    assert result.template_publication_status == "BLOCKED"
    assert result.verdict == "BLOCKED"
    assert any(
        f.component_template_code == CHILD_ALUMINUM
        and f.evidence.get("conflict_code") == "required_inactive_child"
        for f in result.findings
    )
    # System Link Check spine present
    systems = {node.system: node.status for node in result.systems}
    assert "catalog" in systems
    assert "components" in systems
    assert "execution_preview" in systems


@pytest.mark.asyncio
async def test_vl_publish_blocked_without_activating_aluminiu(volumetric_v2_db):
    child = (
        await volumetric_v2_db.execute(
            select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM).limit(1)
        )
    ).scalar_one()
    child.active = False
    await volumetric_v2_db.commit()

    pub = ProductTemplatePublicationService(volumetric_v2_db)
    with pytest.raises(HTTPException) as exc:
        await pub.transition(
            TEMPLATE_CODE,
            ProductTemplatePublicationTransitionRequest(action="publish", actor="test"),
        )
    assert exc.value.status_code == 409
    # Aluminiu must remain inactive — no auto-activate side effect
    after = (
        await volumetric_v2_db.execute(
            select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM).limit(1)
        )
    ).scalar_one()
    assert after.active is False
