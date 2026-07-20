"""Publication lifecycle — readiness hard gate; active≠published; VL aluminiu blocks publish."""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select

from models.product_templates import Product_templates
from schemas.product_template_publication import ProductTemplatePublicationTransitionRequest
from services.product_template_availability_service import ProductTemplateAvailabilityService
from services.product_template_publication_service import (
    ProductTemplatePublicationService,
    apply_publication_offerability_gate,
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


def test_active_is_never_published_gate_helper():
    ok, reason = apply_publication_offerability_gate(
        legacy_quote_offerable=True,
        publication_status=None,
    )
    assert ok is True
    assert "legacy" in reason

    blocked, reason2 = apply_publication_offerability_gate(
        legacy_quote_offerable=True,
        publication_status="DRAFT",
    )
    assert blocked is False
    assert "draft" in reason2.lower()


@pytest.mark.asyncio
async def test_get_state_legacy_unspecified(volumetric_v2_db):
    state = await ProductTemplatePublicationService(volumetric_v2_db).get_state(TEMPLATE_CODE)
    assert state.legacy_unspecified is True
    assert state.publication_status is None
    assert state.active_is_not_published is True
    assert state.effective_status == "LEGACY_UNSPECIFIED"


@pytest.mark.asyncio
async def test_publish_vl_blocked_by_inactive_aluminiu(volumetric_v2_db):
    session = volumetric_v2_db
    child = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM).limit(1)
        )
    ).scalar_one()
    child.active = False
    await session.commit()

    service = ProductTemplatePublicationService(session)
    with pytest.raises(HTTPException) as exc:
        await service.transition(
            TEMPLATE_CODE,
            ProductTemplatePublicationTransitionRequest(action="publish", actor="test"),
        )
    assert exc.value.status_code == 409
    detail = exc.value.detail
    assert detail["error"] == "publication_blocked_by_e2e_readiness"
    assert any("required_inactive_child" in str(b) or "BLOCKED" in str(b) for b in detail["blockers"])

    row = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == TEMPLATE_CODE).limit(1)
        )
    ).scalar_one()
    assert row.publication_status is None or row.publication_status != "PUBLISHED"


@pytest.mark.asyncio
async def test_enter_draft_then_offerability_blocked(volumetric_v2_db):
    session = volumetric_v2_db
    service = ProductTemplatePublicationService(session)
    result = await service.transition(
        TEMPLATE_CODE,
        ProductTemplatePublicationTransitionRequest(action="enter_draft", actor="test"),
    )
    assert result.ok is True
    assert result.state.publication_status == "DRAFT"

    availability = await ProductTemplateAvailabilityService(session).list_availability()
    item = next(i for i in availability.items if i.template_code == TEMPLATE_CODE)
    assert item.publication_status == "DRAFT"
    assert item.quote_offerable is False
    assert item.active_is_not_published is True
    assert item.db_active is True


@pytest.mark.asyncio
async def test_mark_validated_without_readiness(volumetric_v2_db):
    session = volumetric_v2_db
    service = ProductTemplatePublicationService(session)
    state = await service.get_state(TEMPLATE_CODE)
    if state.publication_status != "DRAFT":
        if state.publication_status is None:
            await service.transition(
                TEMPLATE_CODE,
                ProductTemplatePublicationTransitionRequest(action="enter_draft"),
            )
        elif state.publication_status == "VALIDATED":
            pass
        else:
            await service.transition(
                TEMPLATE_CODE,
                ProductTemplatePublicationTransitionRequest(action="reopen_draft"),
            )
    if (await service.get_state(TEMPLATE_CODE)).publication_status != "VALIDATED":
        result = await service.transition(
            TEMPLATE_CODE,
            ProductTemplatePublicationTransitionRequest(action="mark_validated"),
        )
        assert result.state.publication_status == "VALIDATED"
    else:
        assert (await service.get_state(TEMPLATE_CODE)).publication_status == "VALIDATED"
