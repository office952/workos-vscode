from __future__ import annotations

import pytest

from schemas.product_system_template_readiness import (
    CommercialReadinessStatus,
    ExecutionReadinessStatus,
    PricingReadinessStatus,
    ReadinessRollup,
    TechnicalReadinessStatus,
)
from services.product_system_template_readiness_service import (
    ProductSystemTemplateReadinessService,
    TemplateAvailabilityReadinessContext,
)
from services.product_template_availability_service import ProductTemplateAvailabilityService
from tests.test_product_template_availability import (
    LETTERS,
    LOGO,
    PREMOUNT,
    VOLUM_ALUMINUM,
    _by_code,
    _seed_availability_fixture,
)

ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"


def test_readiness_schema_enums_stable() -> None:
    assert TechnicalReadinessStatus.TECHNICALLY_READY.value == "TECHNICALLY_READY"
    assert PricingReadinessStatus.PRICING_READY.value == "PRICING_READY"
    assert ExecutionReadinessStatus.EXECUTION_READY.value == "EXECUTION_READY"
    assert CommercialReadinessStatus.OFFERABLE.value == "OFFERABLE"
    assert ReadinessRollup.BLOCKED.value == "BLOCKED"


@pytest.mark.asyncio
async def test_availability_items_include_readiness_and_capabilities(db_session) -> None:
    await _seed_availability_fixture(db_session)
    response = await ProductTemplateAvailabilityService(db_session).list_availability()
    for item in response.items:
        assert item.readiness is not None
        assert item.capabilities is not None
        assert item.readiness.rollup in ReadinessRollup
        assert item.readiness.technical.status in TechnicalReadinessStatus
        assert isinstance(item.readiness.technical.blockers, list)


@pytest.mark.asyncio
async def test_letters_readiness_derived_honestly(db_session) -> None:
    await _seed_availability_fixture(db_session)
    item = _by_code(
        (await ProductTemplateAvailabilityService(db_session).list_availability()).items
    )[LETTERS]
    assert item.capabilities.root_offerable is True
    assert item.capabilities.linked_child_offerable is False
    assert item.readiness.commercial.status == CommercialReadinessStatus.OFFERABLE.value
    assert item.readiness.technical.status == TechnicalReadinessStatus.TECHNICALLY_READY.value
    assert item.readiness.execution.status == ExecutionReadinessStatus.EXECUTION_INCOMPLETE.value
    assert item.readiness.rollup == ReadinessRollup.BLOCKED
    assert any(
        blocker.code in {"MISSING_CANONICAL_OPERATION", "MISSING_TASK_RULE"}
        for blocker in item.readiness.execution.blockers
    )


@pytest.mark.asyncio
async def test_logo_not_falsely_offerable(db_session) -> None:
    await _seed_availability_fixture(db_session)
    item = _by_code(
        (await ProductTemplateAvailabilityService(db_session).list_availability()).items
    )[LOGO]
    assert item.quote_offerable is False
    assert item.capabilities.root_offerable is False
    assert item.readiness.commercial.status == CommercialReadinessStatus.INTERNAL_ONLY.value
    assert item.readiness.rollup in {ReadinessRollup.INTERNAL, ReadinessRollup.BLOCKED}


@pytest.mark.asyncio
async def test_internal_module_capabilities_separate_from_root(db_session) -> None:
    await _seed_availability_fixture(db_session)
    item = _by_code(
        (await ProductTemplateAvailabilityService(db_session).list_availability()).items
    )[PREMOUNT]
    assert item.capabilities.root_offerable is False
    assert item.capabilities.internal_only is True
    assert item.readiness.commercial.status == CommercialReadinessStatus.INTERNAL_ONLY.value


@pytest.mark.asyncio
async def test_component_first_experimental_not_operator_offerable(db_session) -> None:
    await _seed_availability_fixture(db_session)
    item = _by_code(
        (await ProductTemplateAvailabilityService(db_session).list_availability()).items
    )[VOLUM_ALUMINUM]
    assert item.quote_offerable is False
    assert item.capabilities.root_offerable is False
    assert item.readiness.commercial.status == CommercialReadinessStatus.INTERNAL_ONLY.value


@pytest.mark.asyncio
async def test_missing_links_emit_technical_blockers(db_session) -> None:
    await _seed_availability_fixture(db_session, include_letter_links=False)
    item = _by_code(
        (await ProductTemplateAvailabilityService(db_session).list_availability()).items
    )[LETTERS]
    assert item.readiness.technical.status == TechnicalReadinessStatus.TECHNICALLY_READY.value
    assert item.readiness.execution.status == ExecutionReadinessStatus.EXECUTION_INCOMPLETE.value
    assert item.readiness.rollup == ReadinessRollup.BLOCKED


@pytest.mark.asyncio
async def test_readiness_blockers_are_structured(db_session) -> None:
    await _seed_availability_fixture(db_session)
    item = _by_code(
        (await ProductTemplateAvailabilityService(db_session).list_availability()).items
    )[LETTERS]
    blocker = item.readiness.execution.blockers[0]
    assert blocker.code
    assert blocker.dimension == "execution"
    assert blocker.severity in {"blocking", "warning", "diagnostic"}
    assert blocker.owner
    assert blocker.message


def test_rollup_deprecated_and_internal_rules() -> None:
    service = ProductSystemTemplateReadinessService(db=None)  # type: ignore[arg-type]
    commercial_deprecated = service._derive_commercial(  # noqa: SLF001
        template=type("T", (), {"template_code": LOGO, "active": False})(),
        context=TemplateAvailabilityReadinessContext(
            template_code=LOGO,
            db_active=False,
            quote_offerable=False,
            runtime_module=False,
            is_parent=True,
            has_modules=True,
            display_group="archived_experimental",
        ),
        capabilities=service._derive_capabilities(  # noqa: SLF001
            type("T", (), {"template_code": LOGO, "active": False})(),
            TemplateAvailabilityReadinessContext(
                template_code=LOGO,
                db_active=False,
                quote_offerable=False,
                runtime_module=False,
                is_parent=True,
                has_modules=True,
                display_group="archived_experimental",
            ),
        ),
    )
    assert commercial_deprecated.status == CommercialReadinessStatus.DEPRECATED.value


def test_root_offerable_policy_includes_acm_excludes_logo() -> None:
    from services.template_usage_mode_policy import ROOT_OFFERABLE_TEMPLATE_CODES

    normalized = {code.strip().upper() for code in ROOT_OFFERABLE_TEMPLATE_CODES}
    assert "TPL-ACM-BOXED-MOUNTING-SUPPORT_V1" in normalized
    assert "TPL-VOLUMETRIC-LOGO_V1" not in normalized
