"""Composition link contract fields — usage_mode / instance_schema_id on module links."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from models.product_template_module_links import ProductTemplateModuleLink
from services.product_template_module_links_service import ProductTemplateModuleLinksService
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
async def test_module_link_exposes_contract_fields_on_update(volumetric_v2_db):
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
    original_relation = link.relation_type
    link_id = int(link.id)

    service = ProductTemplateModuleLinksService(session)
    updated = await service.update(
        link_id,
        {
            "usage_mode": "linked_child",
            "instance_schema_id": "letter_group_instances.sidewall",
            "relation_type": "required_child",
            "active": True,
        },
    )
    assert updated is not None
    assert updated.usage_mode == "linked_child"
    assert updated.instance_schema_id == "letter_group_instances.sidewall"
    assert updated.relation_type == "required_child"
    # Restore seed fields — shared fixture DB is upserted across tests.
    await service.update(
        link_id,
        {
            "usage_mode": None,
            "instance_schema_id": None,
            "relation_type": original_relation,
            "active": True,
        },
    )


@pytest.mark.asyncio
async def test_module_link_soft_deactivate_does_not_delete(volumetric_v2_db):
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
    link_id = int(link.id)

    service = ProductTemplateModuleLinksService(session)
    updated = await service.update(link_id, {"active": False})
    assert updated is not None
    assert updated.active is False

    still = await service.get_by_id(link_id)
    assert still is not None
    assert still.active is False
    # Soft-remove must not delete; restore active so aluminiu blocker stays real for other tests.
    restored = await service.update(link_id, {"active": True})
    assert restored is not None
    assert restored.active is True
