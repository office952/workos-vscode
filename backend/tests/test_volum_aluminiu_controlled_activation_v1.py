"""Controlled activation identity + calculation invariants for TPL-VOLUM-ALUMINIU_v1."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from models.product_templates import Product_templates
from services.product_e2e_readiness_service import ProductE2EReadinessService
from services.product_template_publication_service import ProductTemplatePublicationService
from services.volum_aluminiu_component_contract import (
    ACTIVATION_FORBIDDEN_IN_THIS_BUILD,
    BOM_COMPONENT_ID,
    PARENT_TEMPLATE_CODE,
    PRICING_COMPONENT_CODE,
    PUBLICATION_REMAINS_BLOCKED,
    TEMPLATE_CODE,
    build_identity_convergence_view,
    map_component_ref_to_module,
)
from schemas.volum_aluminiu_separate_calc_preview import VolumAluminiuSeparateCalcPreviewRequest
from services.volum_aluminiu_separate_calc_preview_service import (
    VolumAluminiuSeparateCalcPreviewService,
)
from tests.test_product_aggregate_volumetric_v2 import (
    CHILD_ALUMINUM,
    TEMPLATE_CODE as VL_PARENT,
    _seed_volumetric_v2_fixture,
)
from tests.test_volum_aluminiu_separate_calc_preview import _payload_with_confirmation


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    return db_session


def test_activation_policy_flags_after_owner_go():
    assert ACTIVATION_FORBIDDEN_IN_THIS_BUILD is False
    assert PUBLICATION_REMAINS_BLOCKED is True
    assert TEMPLATE_CODE == "TPL-VOLUM-ALUMINIU_v1"
    assert BOM_COMPONENT_ID == "comp_volum_aluminiu_module"
    assert map_component_ref_to_module(BOM_COMPONENT_ID) == "modelare_cant"
    assert map_component_ref_to_module(PRICING_COMPONENT_CODE) == "modelare_cant"
    view = build_identity_convergence_view()
    assert view["status"] == "PASS"
    assert view["activation_forbidden_in_this_build"] is False
    assert view["publication_remains_blocked"] is True


@pytest.mark.asyncio
async def test_activate_only_mutates_active_not_publication(volumetric_v2_db):
    session = volumetric_v2_db
    child = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM).limit(1)
        )
    ).scalar_one()
    parent = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == VL_PARENT).limit(1)
        )
    ).scalar_one()

    child.active = False
    child.publication_status = None
    parent.publication_status = None
    parent.published_at = None
    await session.commit()

    prior_pub = child.publication_status
    prior_parent_pub = parent.publication_status

    child.active = True
    await session.commit()
    await session.refresh(child)
    await session.refresh(parent)

    assert child.active is True
    assert child.publication_status == prior_pub
    assert parent.publication_status == prior_parent_pub
    assert parent.published_at is None

    count = (
        await session.execute(
            select(func.count())
            .select_from(Product_templates)
            .where(Product_templates.template_code == CHILD_ALUMINUM)
        )
    ).scalar()
    assert int(count or 0) == 1


@pytest.mark.asyncio
async def test_readiness_clears_inactive_blocker_when_active_preserves_not_tested(
    volumetric_v2_db,
):
    session = volumetric_v2_db
    child = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM).limit(1)
        )
    ).scalar_one()
    child.active = True
    await session.commit()

    result = await ProductE2EReadinessService(session).run_static(VL_PARENT)
    assert result.write_performed is False
    assert result.no_write is True

    inactive = [
        f
        for f in result.findings
        if f.evidence.get("conflict_code") == "required_inactive_child"
        and f.component_template_code == CHILD_ALUMINUM
    ]
    assert not inactive, "inactivity-owned blocker must close when child is active"

    active_pass = [
        f
        for f in result.findings
        if f.check_id == f"components.required_active.{CHILD_ALUMINUM}" and f.status == "PASS"
    ]
    assert active_pass

    not_tested = [f for f in result.findings if f.status == "NOT_TESTED"]
    assert not_tested, "NOT_TESTED systems must remain NOT_TESTED (not greenwashed)"

    # Parent must not be treated as published by activation.
    pub = await ProductTemplatePublicationService(session).get_state(VL_PARENT)
    assert pub.publication_status != "PUBLISHED"


@pytest.mark.asyncio
async def test_separate_calc_preview_invariant_after_activation(volumetric_v2_db):
    """Activation must not change separate-calc confirmed-perimeter contract."""
    session = volumetric_v2_db
    child = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM).limit(1)
        )
    ).scalar_one()
    child.active = True
    await session.commit()

    service = VolumAluminiuSeparateCalcPreviewService()
    body = VolumAluminiuSeparateCalcPreviewRequest(payload=_payload_with_confirmation(perimeter=12.5))
    preview = service.build_preview(TEMPLATE_CODE, body)
    assert preview.separate_calculation == "PASS"
    assert preview.quantity["quantity_m"] == 12.5
    assert preview.commercial is not None
    assert preview.commercial["basis_type"] == "ml"
    assert preview.persist is False


@pytest.mark.asyncio
async def test_identity_table_canonical_not_alias(volumetric_v2_db):
    session = volumetric_v2_db
    child = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == TEMPLATE_CODE).limit(1)
        )
    ).scalar_one()
    child.active = True
    await session.commit()

    aspirational = (
        await session.execute(
            select(Product_templates).where(
                Product_templates.template_code == "TPL-COMP-LETTER-RETURN-CANT_v1"
            )
        )
    ).scalars().all()
    assert aspirational == [], "aspirational alias must not become an active DB target"

    assert PARENT_TEMPLATE_CODE == VL_PARENT
    assert map_component_ref_to_module("Cant din aluminiu") is None
