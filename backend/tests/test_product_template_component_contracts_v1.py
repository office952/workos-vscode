"""Component contracts — used-by map + link usage_mode; no CT table."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from models.product_template_module_links import ProductTemplateModuleLink
from schemas.product_template_component_contract import ComponentContractLinkPatchRequest
from services.product_template_component_contract_service import (
    ProductTemplateComponentContractService,
)
from tests.test_product_aggregate_volumetric_v2 import (
    CHILD_ALUMINUM,
    TEMPLATE_CODE,
    _seed_volumetric_v2_fixture,
)


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    return db_session


@pytest.mark.asyncio
async def test_component_contract_used_by_and_children(volumetric_v2_db):
    service = ProductTemplateComponentContractService(volumetric_v2_db)
    root = await service.get_contract(TEMPLATE_CODE)
    assert root.no_component_templates_table is True
    assert root.template_code == TEMPLATE_CODE
    assert any(c.module_template_code == CHILD_ALUMINUM for c in root.children)

    child = await service.get_contract(CHILD_ALUMINUM)
    assert child.role in {"child_component", "component_only"}
    assert any(e.parent_template_code == TEMPLATE_CODE for e in child.used_by)


@pytest.mark.asyncio
async def test_patch_link_usage_mode(volumetric_v2_db):
    session = volumetric_v2_db
    link = (
        await session.execute(
            select(ProductTemplateModuleLink)
            .where(
                ProductTemplateModuleLink.parent_template_code == TEMPLATE_CODE,
                ProductTemplateModuleLink.module_template_code == CHILD_ALUMINUM,
            )
            .limit(1)
        )
    ).scalar_one()

    service = ProductTemplateComponentContractService(session)
    patched = await service.patch_link(
        int(link.id),
        ComponentContractLinkPatchRequest(
            usage_mode="linked_child",
            instance_schema_id="letter_group_instances.sidewall",
        ),
    )
    assert patched.usage_mode == "linked_child"
    assert patched.instance_schema_id == "letter_group_instances.sidewall"

    view = await service.get_contract(TEMPLATE_CODE)
    edge = next(c for c in view.children if c.module_template_code == CHILD_ALUMINUM)
    assert edge.usage_mode == "linked_child"
