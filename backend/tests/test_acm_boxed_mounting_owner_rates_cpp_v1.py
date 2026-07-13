"""Owner rates + CPP/EIC wiring for TPL-ACM-BOXED-MOUNTING-SUPPORT_v1."""

from __future__ import annotations

import pytest
import pytest_asyncio

from seeds.seed_acm_bond_materials import seed_acm_bond_materials
from seeds.seed_acm_boxed_mounting_owner_rates import seed_acm_boxed_mounting_owner_rates
from seeds.seed_acm_owner_confirmed_prices import seed_acm_owner_confirmed_prices
from seeds.seed_tpl_acm_boxed_mounting_support_v1 import (
    TEMPLATE_CODE,
    seed_tpl_acm_boxed_mounting_support_v1,
)
from services.acm_bond_material_rate_resolver import (
    BOXED_MOUNTING_TEMPLATE_CODE,
    resolve_acm_bond_panel_material_rate,
)
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.inventory_materials_admin_service import load_material_cost_dict
from services.mounting_solution_service import ACM_BOXED_MOUNTING_TEMPLATE_CODE
from services.pricing_registry_service import (
    PricingRegistryService,
    TEMPLATE_MATERIAL_VARIANT_EXPANSION,
)
from services.product_aggregate_service import ProductAggregateService
from services.workcenter_rates_service import load_workcenter_rate_pricing_dict

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

LETTERS_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _acm_finish_quote_input(*, thickness_mm: int = 3) -> dict:
    return {
        "analysis_ready": True,
        "client": {"width_mm": 1200, "height_mm": 800},
        "quote_geometry": {
            "letter_count": 3,
            "letter_perimeter_m": 8.0,
            "letter_face_area_m2": 0.8,
        },
        "finish_setup": {
            "mounting_scope": "preparation_only",
            "mounting_solution": {
                "template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
                "configuration": {
                    "panel_width_mm": 1200,
                    "panel_height_mm": 800,
                    "acm_thickness_mm": thickness_mm,
                    "return_depth_mm": 60,
                    "rear_lip_mm": 25,
                    "fold_sides": "all",
                },
            },
            "confirmed": True,
        },
    }


@pytest_asyncio.fixture
async def acm_rates_seeded_db(volumetric_v2_db):
    from seeds.seed_inventory_materials_stubs import seed_inventory_material_stubs

    await seed_inventory_material_stubs()
    await seed_acm_bond_materials()
    await seed_acm_owner_confirmed_prices()
    await seed_acm_boxed_mounting_owner_rates()
    await seed_tpl_acm_boxed_mounting_support_v1()
    return volumetric_v2_db


@pytest.mark.asyncio
async def test_registry_lists_boxed_template_variant_and_owner_rates(acm_rates_seeded_db) -> None:
    expansion = TEMPLATE_MATERIAL_VARIANT_EXPANSION[TEMPLATE_CODE]
    assert expansion["MAT-ACM-BOND-PANEL"] == ["MAT-ACM-BOND-3MM"]

    session = acm_rates_seeded_db
    registry = await PricingRegistryService(session).build_registry(template_filter=TEMPLATE_CODE)
    codes = {item["pricing_code"] for item in registry["items"]}
    assert "MAT-ACM-BOND-3MM" in codes
    assert "MAT-SURUBURI-GEN" in codes
    assert "ACM_PANEL_CUTTING" in codes
    assert "ACM_V_GROOVE" in codes
    assert "ACM_BOXED_ASSEMBLY" in codes

    wc_pricing = await load_workcenter_rate_pricing_dict(session)
    assert wc_pricing["ACM_PANEL_CUTTING"]["rate_per_linear_meter"] == 1.5
    assert wc_pricing["ACM_V_GROOVE"]["rate_per_linear_meter"] == 3.0
    assert wc_pricing["ACM_BOXED_ASSEMBLY"]["rate_basis"] == "per_square_meter"

    material_rates = await load_material_cost_dict(session)
    assert material_rates.get("MAT-SURUBURI-GEN") == 5.0


@pytest.mark.asyncio
async def test_three_mm_material_resolves_for_boxed_template(acm_rates_seeded_db) -> None:
    session = acm_rates_seeded_db
    material_rates = await load_material_cost_dict(session)
    resolution = resolve_acm_bond_panel_material_rate(
        material_rates,
        {"acm_thickness_mm": 3, "panel_width_mm": 1200, "panel_height_mm": 800},
        template_code=BOXED_MOUNTING_TEMPLATE_CODE,
    )
    assert resolution.resolution_status == "resolved"
    assert resolution.unit_cost == 15.0
    assert resolution.source_code == "MAT-ACM-BOND-3MM"


@pytest.mark.asyncio
async def test_four_mm_blocked_for_boxed_template(acm_rates_seeded_db) -> None:
    session = acm_rates_seeded_db
    material_rates = await load_material_cost_dict(session)
    resolution = resolve_acm_bond_panel_material_rate(
        material_rates,
        {"acm_thickness_mm": 4, "panel_width_mm": 1200, "panel_height_mm": 800},
        template_code=BOXED_MOUNTING_TEMPLATE_CODE,
    )
    assert resolution.resolution_status == "unsupported_acm_thickness_mm"


@pytest.mark.asyncio
async def test_owner_workcenters_active_not_missing_price(acm_rates_seeded_db) -> None:
    session = acm_rates_seeded_db
    wc_pricing = await load_workcenter_rate_pricing_dict(session)
    for code in ("ACM_PANEL_CUTTING", "ACM_V_GROOVE", "ACM_BOXED_ASSEMBLY"):
        row = wc_pricing[code]
        assert float(row["rate_per_linear_meter"]) > 0
        assert row["rate_basis"] in {"per_linear_meter", "per_square_meter"}


@pytest.mark.asyncio
async def test_cpp_emits_structura_suport_acm_commercial_lines(acm_rates_seeded_db) -> None:
    session = acm_rates_seeded_db
    preview = await CommercialPriceProposalService(session).build_preview(
        LETTERS_TEMPLATE,
        quote_input=_acm_finish_quote_input(),
    )
    assert preview is not None
    acm_lines = [line for line in preview.commercial_price_lines if line.code.startswith("acm_")]
    assert len(acm_lines) >= 6
    assembly = next(line for line in acm_lines if line.code == "acm_boxed_assembly")
    assert assembly.commercial_unit_price == 15.0
    assert assembly.subtotal is not None
    assert assembly.subtotal >= 20.0
    assert preview.forbidden_hourly_usage_detected == []


@pytest.mark.asyncio
async def test_eic_suruburi_and_acm_capacity_hints(acm_rates_seeded_db) -> None:
    session = acm_rates_seeded_db
    preview = await EstimatedInternalCostService(session).build_preview(
        LETTERS_TEMPLATE,
        quote_input=_acm_finish_quote_input(),
    )
    assert preview is not None
    material_codes = {line.code for line in preview.estimated_material_lines}
    suruburi_blockers = [
        b for b in preview.internal_blockers if b.material_code == "MAT-SURUBURI-GEN"
    ]
    if any(code.startswith("material_MAT-SURUBURI-GEN") for code in material_codes):
        assert suruburi_blockers == []
    acm_capacity = [hint for hint in preview.capacity_hints if hint.code.startswith("acm_")]
    assert len(acm_capacity) >= 3
    assert preview.hourly_contamination_detected == []


@pytest.mark.asyncio
async def test_aggregate_keeps_face_and_return_material_rows(acm_rates_seeded_db) -> None:
    session = acm_rates_seeded_db
    await seed_tpl_acm_boxed_mounting_support_v1()
    aggregate = await ProductAggregateService(session).build(TEMPLATE_CODE)
    assert aggregate is not None
    bond_rows = [
        mat
        for mat in aggregate.materials
        if mat.material_code == "MAT-ACM-BOND-PANEL" and mat.source_template_code == TEMPLATE_CODE
    ]
    component_refs = {mat.component_ref for mat in bond_rows}
    assert "comp_acm_panel_face" in component_refs
    assert "comp_casetted_returns" in component_refs
    assert len(bond_rows) == 2
