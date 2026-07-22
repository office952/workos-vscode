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
async def test_known_conflicts_do_not_block_when_verdict_publishable(volumetric_v2_db):
    """TEMPLATE_ACTIVATION_V1: TEMPLATE_IDENTITY etc. are warnings, not publish blockers."""
    from unittest.mock import AsyncMock, MagicMock, patch

    session = volumetric_v2_db
    row = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == TEMPLATE_CODE).limit(1)
        )
    ).scalar_one()
    # LEGACY_UNSPECIFIED may publish directly when readiness is publishable.
    row.publication_status = None
    row.publication_version = None
    await session.commit()

    service = ProductTemplatePublicationService(session)
    fake_readiness = MagicMock()
    fake_readiness.verdict = "STATIC_READY_WITH_WARNINGS"
    fake_readiness.e2e_ready = False
    fake_readiness.known_conflicts = ["TEMPLATE_IDENTITY", "DOSSIER_METADATA_ONLY"]
    fake_readiness.findings = []

    with patch(
        "services.product_template_publication_service.ProductE2EReadinessService"
    ) as readiness_cls:
        readiness_cls.return_value.run_static = AsyncMock(return_value=fake_readiness)
        with patch.object(
            service,
            "_pricing_context",
            AsyncMock(
                return_value={
                    "operational_readiness": "ACTIVE_WITH_AI_DEFAULTS",
                    "ai_decisions": [{"decision_id": "AI_PACK_PRODUCT_BAND"}],
                    "acm_treatment_allowed": None,
                }
            ),
        ):
            result = await service.transition(
                TEMPLATE_CODE,
                ProductTemplatePublicationTransitionRequest(
                    action="publish", actor="activation_v1_test"
                ),
            )
    assert result.ok is True
    assert result.state.publication_status == "PUBLISHED"
    assert result.evidence.get("uses_ai_defaults") is True
    assert "AI_PACK_PRODUCT_BAND" in (result.evidence.get("ai_decision_ids") or [])
    # Isolate session for subsequent tests in this module.
    row.publication_status = None
    row.publication_version = None
    row.published_at = None
    row.published_by = None
    await session.commit()


@pytest.mark.asyncio
async def test_mark_validated_without_readiness(volumetric_v2_db):
    session = volumetric_v2_db
    row = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == TEMPLATE_CODE).limit(1)
        )
    ).scalar_one()
    row.publication_status = None
    await session.commit()

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
