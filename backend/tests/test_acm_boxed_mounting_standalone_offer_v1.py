"""Standalone Product System offer flow for TPL-ACM-BOXED-MOUNTING-SUPPORT_v1."""

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
from services.acm_quote_input_helpers import (
    is_acm_boxed_mounting_payload,
    is_acm_boxed_mounting_standalone_root_template,
    merge_acm_boxed_mounting_derived_fields,
)
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.inventory_materials_admin_service import load_material_cost_dict
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_template_availability_service import ProductTemplateAvailabilityService
from services.quote_snapshot_v2_service import QuoteSnapshotV2Service

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def _standalone_quote_input(*, thickness_mm: int = 3) -> dict:
    return {
        "template_code": TEMPLATE_CODE,
        "panel_width_mm": 1200,
        "panel_height_mm": 800,
        "acm_thickness_mm": thickness_mm,
        "return_depth_mm": 60,
        "rear_lip_mm": 25,
        "fold_sides": "all",
        "quantity": 1,
    }


@pytest_asyncio.fixture
async def acm_standalone_seeded_db(volumetric_v2_db):
    from seeds.seed_inventory_materials_stubs import seed_inventory_material_stubs

    await seed_inventory_material_stubs()
    await seed_acm_bond_materials()
    await seed_acm_owner_confirmed_prices()
    await seed_acm_boxed_mounting_owner_rates()
    await seed_tpl_acm_boxed_mounting_support_v1()
    return volumetric_v2_db


@pytest.mark.asyncio
async def test_standalone_root_template_policy(acm_standalone_seeded_db) -> None:
    assert is_acm_boxed_mounting_standalone_root_template(TEMPLATE_CODE) is True


@pytest.mark.asyncio
async def test_availability_marks_acm_root_offerable(acm_standalone_seeded_db) -> None:
    session = acm_standalone_seeded_db
    response = await ProductTemplateAvailabilityService(session).list_availability(
        offerable_only=True,
        include_runtime_modules=True,
    )
    codes = {item.template_code for item in response.items}
    assert TEMPLATE_CODE in codes
    acm_item = next(item for item in response.items if item.template_code == TEMPLATE_CODE)
    assert acm_item.quote_offerable is True
    assert acm_item.product_system_role == "offerable_product"


@pytest.mark.asyncio
async def test_product_definition_standalone_root_builds(acm_standalone_seeded_db) -> None:
    session = acm_standalone_seeded_db
    pd = await ProductDefinitionBuilderService(session).build_preview(TEMPLATE_CODE)
    assert pd is not None
    assert pd.template_code == TEMPLATE_CODE
    assert {m.module_code for m in pd.selected_modules} == {"structura_suport"}


@pytest.mark.asyncio
async def test_standalone_payload_derivation_and_detection(acm_standalone_seeded_db) -> None:
    payload = merge_acm_boxed_mounting_derived_fields(_standalone_quote_input())
    assert is_acm_boxed_mounting_payload(payload) is True
    assert payload["panel_area_m2"] == pytest.approx(0.96, rel=1e-3)
    assert payload["panel_perimeter_m"] == pytest.approx(4.0, rel=1e-3)
    assert payload["fold_length_m"] == pytest.approx(4.0, rel=1e-3)


@pytest.mark.asyncio
async def test_four_mm_blocked_standalone_material_resolution(acm_standalone_seeded_db) -> None:
    session = acm_standalone_seeded_db
    material_rates = await load_material_cost_dict(session)
    resolution = resolve_acm_bond_panel_material_rate(
        material_rates,
        _standalone_quote_input(thickness_mm=4),
        template_code=BOXED_MOUNTING_TEMPLATE_CODE,
    )
    assert resolution.resolution_status == "unsupported_acm_thickness_mm"


@pytest.mark.asyncio
async def test_standalone_cpp_emits_six_acm_lines_with_assembly_min(acm_standalone_seeded_db) -> None:
    session = acm_standalone_seeded_db
    quote_input = _standalone_quote_input()
    preview = await CommercialPriceProposalService(session).build_preview(
        TEMPLATE_CODE,
        quote_input=quote_input,
    )
    assert preview is not None
    acm_lines = [line for line in preview.commercial_price_lines if line.code.startswith("acm_")]
    assert len(acm_lines) == 6
    assembly = next(line for line in acm_lines if line.code == "acm_boxed_assembly")
    assert assembly.subtotal is not None
    assert assembly.subtotal >= 20.0


@pytest.mark.asyncio
async def test_standalone_cpp_not_letter_blocked_by_acm_geometry(acm_standalone_seeded_db) -> None:
    """AGENT-B-F003: TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 has ACM-shaped geometry
    (panel_width_mm/panel_height_mm/acm_thickness_mm/return_depth_mm/fold_sides), never
    letter-shaped (letter_count/letter_face_area_m2/vector_file). A valid standalone ACM
    payload must not trip CRITICAL_GEOMETRY_MISSING for the letter-only keys, and must not
    invent any ACM shell finish price to get there."""
    session = acm_standalone_seeded_db
    preview = await CommercialPriceProposalService(session).build_preview(
        TEMPLATE_CODE,
        quote_input=_standalone_quote_input(),
    )
    assert preview is not None
    assert not any(b.code == "CRITICAL_GEOMETRY_MISSING" for b in preview.commercial_blockers)
    codes = {line.code for line in preview.commercial_price_lines}
    finish_shell_codes = {c for c in codes if "shell" in c or "mass_color" in c or "mirror" in c}
    assert finish_shell_codes == set()


@pytest.mark.asyncio
async def test_standalone_cpp_geometry_check_uses_acm_keys_not_letter_keys(
    acm_standalone_seeded_db,
) -> None:
    """AGENT-B-F003 branch dispatch: the standalone ACM root must be validated against
    ACM_BOXED_MOUNTING_STANDALONE_REQUIRED_KEYS, never the letter-shaped CRITICAL_GEOMETRY_KEYS
    (letter_count/letter_face_area_m2/letter_perimeter_m/width_mm/height_mm/vector_file) —
    none of those letter-only fields exist in this payload, yet the preview is not blocked."""
    from services.acm_quote_input_helpers import ACM_BOXED_MOUNTING_STANDALONE_REQUIRED_KEYS

    letter_only_keys = {"letter_count", "letter_face_area_m2", "letter_perimeter_m", "width_mm", "height_mm"}
    quote_input = _standalone_quote_input()
    assert not (letter_only_keys & set(quote_input.keys()))
    assert set(ACM_BOXED_MOUNTING_STANDALONE_REQUIRED_KEYS) <= set(quote_input.keys())

    session = acm_standalone_seeded_db
    preview = await CommercialPriceProposalService(session).build_preview(
        TEMPLATE_CODE,
        quote_input=quote_input,
    )
    assert preview is not None
    assert not any(b.code == "CRITICAL_GEOMETRY_MISSING" for b in preview.commercial_blockers)


@pytest.mark.asyncio
async def test_standalone_eic_capacity_hints(acm_standalone_seeded_db) -> None:
    session = acm_standalone_seeded_db
    preview = await EstimatedInternalCostService(session).build_preview(
        TEMPLATE_CODE,
        quote_input=_standalone_quote_input(),
    )
    assert preview is not None
    acm_capacity = [hint for hint in preview.capacity_hints if hint.code.startswith("acm_")]
    assert len(acm_capacity) >= 3


@pytest.mark.asyncio
async def test_standalone_aggregate_face_and_return_materials(acm_standalone_seeded_db) -> None:
    session = acm_standalone_seeded_db
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


@pytest.mark.asyncio
async def test_standalone_quote_snapshot_v2_preview(acm_standalone_seeded_db) -> None:
    session = acm_standalone_seeded_db
    snapshot = await QuoteSnapshotV2Service(session).build_preview(
        TEMPLATE_CODE,
        quote_input=_standalone_quote_input(),
    )
    assert snapshot is not None
    assert snapshot.template_code == TEMPLATE_CODE
    assert snapshot.commercial_price_proposal_snapshot is not None
    assert snapshot.estimated_internal_cost_snapshot is not None
    acm_lines = [
        line
        for line in snapshot.commercial_price_proposal_snapshot.commercial_price_lines
        if line.code.startswith("acm_")
    ]
    assert len(acm_lines) == 6
