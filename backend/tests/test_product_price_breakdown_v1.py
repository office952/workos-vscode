"""PRODUCT_PRICE_BREAKDOWN_V1 — adapter over CPP/EIC; no second calculator."""

from __future__ import annotations

import pytest
import pytest_asyncio

from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.product_price_breakdown_fixtures import FIXTURES
from services.product_price_breakdown_service import ProductPriceBreakdownService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

VL = "TPL-VOLUMETRIC-LETTERS_v2"
ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
LOGO = "TPL-VOLUMETRIC-LOGO_v1"
VOLUM_AL = "TPL-VOLUM-ALUMINIU_v1"


@pytest_asyncio.fixture
async def breakdown(volumetric_v2_db):
    yield ProductPriceBreakdownService(volumetric_v2_db)


@pytest.mark.asyncio
async def test_vl_breakdown_reconciles_with_cpp_and_eic(volumetric_v2_db, breakdown):
    fixture = FIXTURES["vl_letters_demo_v1"]
    qi = fixture["quote_input"]

    out = await breakdown.build(VL, quote_input=qi, fixture_id="vl_letters_demo_v1")
    assert out.template_code == VL
    assert out.fixture_id == "vl_letters_demo_v1"
    assert out.totals.cpp_total_matches is True
    assert out.totals.eic_total_matches is True
    assert out.totals.no_duplicate_commercial_codes is True
    assert out.totals.no_duplicate_internal_codes is True

    cpp = await CommercialPriceProposalService(volumetric_v2_db).build_preview(
        VL, quote_input=qi
    )
    eic = await EstimatedInternalCostService(volumetric_v2_db).build_preview(
        VL, quote_input=qi
    )
    assert cpp is not None
    assert eic is not None
    assert out.totals.commercial_total == cpp.commercial_total
    assert out.totals.internal_total == eic.estimated_total_internal_cost

    commercial_lines = [l for l in out.lines if l.commercial_value is not None]
    assert len(commercial_lines) >= 1
    assert any(l.line_group == "ai_decision" for l in out.lines) or out.uses_ai_defaults
    # Time hooks secondary / excluded
    for hook in out.calibration_hooks:
        assert hook.excluded_from_total is True


@pytest_asyncio.fixture
async def acm_seeded_db(volumetric_v2_db):
    from seeds.seed_acm_bond_materials import seed_acm_bond_materials
    from seeds.seed_acm_boxed_mounting_owner_rates import seed_acm_boxed_mounting_owner_rates
    from seeds.seed_acm_owner_confirmed_prices import seed_acm_owner_confirmed_prices
    from seeds.seed_inventory_materials_stubs import seed_inventory_material_stubs
    from seeds.seed_tpl_acm_boxed_mounting_support_v1 import seed_tpl_acm_boxed_mounting_support_v1

    await seed_inventory_material_stubs()
    await seed_acm_bond_materials()
    await seed_acm_owner_confirmed_prices()
    await seed_acm_boxed_mounting_owner_rates()
    await seed_tpl_acm_boxed_mounting_support_v1()
    return volumetric_v2_db


@pytest.mark.asyncio
async def test_acm_shell_breakdown_marks_treatments_blocked(acm_seeded_db):
    breakdown = ProductPriceBreakdownService(acm_seeded_db)
    out = await breakdown.build(ACM, fixture_id="acm_shell_demo_v1")
    assert out.template_code == ACM
    assert out.acm_treatments_blocked is True
    assert out.totals.cpp_total_matches is True
    assert out.totals.eic_total_matches is True
    # Optional treatments must not silently inflate base shell commercial total
    treatish = [
        l
        for l in out.lines
        if "treatment" in (l.resource_code or "").lower()
        or "tratament" in (l.display_name or "").lower()
        or "face_print" in (l.resource_code or "").lower()
    ]
    for l in treatish:
        assert l.commercial_value in (None, 0) or (
            l.warning is not None and len(l.warning) > 0
        )


@pytest.mark.asyncio
async def test_logo_breakdown_honest_without_pretending_publication(breakdown):
    out = await breakdown.build(LOGO, fixture_id="logo_demo_v1")
    assert out.template_code == LOGO
    # May be partial — must not invent a fake commercial total when CPP missing
    joined = " ".join(out.warnings).lower()
    if out.totals.commercial_total is None:
        assert "cpp" in joined or "product definition" in joined or out.cpp_status is None


@pytest.mark.asyncio
async def test_volum_aluminiu_child_breakdown_not_root(breakdown):
    out = await breakdown.build(VOLUM_AL, fixture_id="volum_aluminiu_demo_v1")
    assert out.template_code == VOLUM_AL
    assert any("copil" in w.lower() or "publication" in w.lower() for w in out.warnings)
    commercial = [l for l in out.lines if l.commercial_value is not None]
    # Component slice: at most the return/cant perimeter line(s)
    assert len(commercial) <= 3
    if commercial:
        assert out.totals.cpp_total_matches is True
        assert commercial[0].quantity_key == "confirmed_perimeter_m"


@pytest.mark.asyncio
async def test_default_fixture_resolves_per_template(breakdown):
    out = await breakdown.build(VL)
    assert out.fixture_id == "vl_letters_demo_v1"
    assert out.configuration_summary.get("has_quote_input") is True


@pytest.mark.asyncio
async def test_missing_material_price_visible_not_hidden(breakdown):
    out = await breakdown.build(VL, fixture_id="vl_letters_demo_v1")
    gaps = [l for l in out.lines if l.warning and "lipsă" in l.warning.lower()]
    # May be zero if registry complete — if present, must keep line visible
    for g in gaps:
        assert g.display_name
        assert g.line_group in {"material", "labor", "machine", "service", "ai_decision"}
