"""F7F — Owner commercial law activation + Step 3 complete offer total.

Covers the ACM sheet commercial law (standard/colorat 15, mirror 40 as a REPLACEMENT rate),
fail-closed behaviour for unknown shells and unproven mirror-exterior combinations, and the
per-product commercial breakdown that Step 3 renders as `Subtotal Litere` / `Subtotal Panou ACM`
plus one complete `Total ofertă` sourced from CPP.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from seeds.seed_acm_bond_materials import seed_acm_bond_materials
from seeds.seed_acm_boxed_mounting_owner_rates import seed_acm_boxed_mounting_owner_rates
from seeds.seed_acm_owner_confirmed_prices import seed_acm_owner_confirmed_prices
from seeds.seed_tpl_acm_boxed_mounting_support_v1 import seed_tpl_acm_boxed_mounting_support_v1
from services.commercial_price_proposal_service import CommercialPriceProposalService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

LETTERS = "TPL-VOLUMETRIC-LETTERS_v2"
ACM_FACE_AREA_M2 = 0.7


def _letters_with_acm_panel(sheet_material: dict | None = None) -> dict:
    finish: dict = {
        "face_finish_type": "oracal_651",
        "return_depth_mm": 60,
        "return_finish_type": "white_aluminum",
        "acm_panel_instance": {
            "schema": "acm_panel_component_instance_v1",
            "component_instance_id": "acm_f7f",
            "association_status": "proposed",
            "technical_configuration_status": "proposed",
            "composition_status": "unconfirmed",
            "geometry": {
                "width_mm": 1000,
                "height_mm": 350,
                "panels": [
                    {
                        "panel_id": "p1",
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 0, "y_mm": 0},
                    },
                    {
                        "panel_id": "p2",
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 1000, "y_mm": 0},
                    },
                ],
                "joints": [{"joint_id": "j1"}],
            },
            "configuration": {
                "finished_depth_mm": 60,
                "fold_count": 1,
                "l1_mm": 60,
                "l2_mm": 0,
                "field_authority": {"fold_count": "catalog_default"},
            },
        },
        "segmented_background": {
            "status": "PROPOSED",
            "panels": [
                {
                    "panel_id": "p1",
                    "width_mm": 1000,
                    "height_mm": 350,
                    "position": {"x_mm": 0, "y_mm": 0},
                },
                {
                    "panel_id": "p2",
                    "width_mm": 1000,
                    "height_mm": 350,
                    "position": {"x_mm": 1000, "y_mm": 0},
                },
            ],
            "assembly_dimensions": {"width_mm": 2000, "height_mm": 350},
        },
        "mounting_solution": {
            "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
            "configuration": {
                "panel_width_mm": 1000,
                "panel_height_mm": 350,
                "acm_thickness_mm": 3,
                "return_depth_mm": 60,
                "fold_sides": "all",
            },
        },
        "confirmed": True,
    }
    if sheet_material is not None:
        finish["acm_panel_instance"]["sheet_material"] = sheet_material
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "test-bond-litere.svg"},
        "client": {"width_mm": 2000, "height_mm": 350},
        "quote_geometry": {
            "letter_count": 3,
            "letter_perimeter_m": 8.0,
            "letter_face_area_m2": 0.8,
        },
        "finish_setup": finish,
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


async def _preview(db, sheet_material: dict | None):
    preview = await CommercialPriceProposalService(db).build_preview(
        LETTERS, quote_input=_letters_with_acm_panel(sheet_material)
    )
    assert preview is not None
    return preview


@pytest.mark.parametrize("variant", ["standard", "colorat"])
@pytest.mark.asyncio
async def test_acm_standard_and_colorat_priced_at_owner_15_eur_m2(acm_rates_seeded_db, variant):
    preview = await _preview(acm_rates_seeded_db, {"variant": variant, "environment": "interior"})
    face = next(
        line for line in preview.commercial_price_lines if line.code == "acm_panel_face_material"
    )
    assert face.commercial_unit_price == pytest.approx(15.0)
    assert face.source_currency == "EUR"
    assert face.subtotal == pytest.approx(15.0 * ACM_FACE_AREA_M2)
    assert face.owner_decision_required is False


@pytest.mark.asyncio
async def test_acm_mirror_is_a_replacement_rate_never_a_surcharge(acm_rates_seeded_db):
    """40 EUR/m2 REPLACES the 15 EUR/m2 rate. There must be exactly one ACM face material line
    and no second mirror surcharge line stacked on top of it."""
    preview = await _preview(
        acm_rates_seeded_db, {"variant": "oglinda_gold", "environment": "interior"}
    )
    face_lines = [
        line for line in preview.commercial_price_lines if line.code == "acm_panel_face_material"
    ]
    assert len(face_lines) == 1
    face = face_lines[0]
    assert face.commercial_unit_price == pytest.approx(40.0)
    assert face.subtotal == pytest.approx(40.0 * ACM_FACE_AREA_M2)
    assert not any(
        "surcharge" in line.code or "supliment" in line.code
        for line in preview.commercial_price_lines
    )
    acm_material_total = sum(
        line.subtotal or 0.0
        for line in preview.commercial_price_lines
        if line.code == "acm_panel_face_material"
    )
    assert acm_material_total == pytest.approx(40.0 * ACM_FACE_AREA_M2)


@pytest.mark.asyncio
async def test_acm_absent_variant_keeps_owner_confirmed_standard_sheet(acm_rates_seeded_db):
    preview = await _preview(acm_rates_seeded_db, None)
    face = next(
        line for line in preview.commercial_price_lines if line.code == "acm_panel_face_material"
    )
    assert face.commercial_unit_price == pytest.approx(15.0)
    assert not any(
        b.code == "COMMERCIAL_RULE_MISSING" and "acm_sheet_variant" in b.message
        for b in preview.commercial_blockers
    )


@pytest.mark.asyncio
async def test_acm_unknown_shell_fails_closed(acm_rates_seeded_db):
    preview = await _preview(
        acm_rates_seeded_db, {"variant": "titan_brushed", "environment": "interior"}
    )
    face = next(
        line for line in preview.commercial_price_lines if line.code == "acm_panel_face_material"
    )
    assert face.commercial_unit_price is None
    assert face.subtotal is None
    assert face.owner_decision_required is True
    assert any(
        b.code == "COMMERCIAL_RULE_MISSING" and "titan_brushed" in b.message
        for b in preview.commercial_blockers
    )
    assert preview.status == "blocked"


@pytest.mark.asyncio
async def test_acm_mirror_exterior_without_proven_sku_requires_technical_compatibility(
    acm_rates_seeded_db,
):
    preview = await _preview(
        acm_rates_seeded_db, {"variant": "oglinda_antracit", "environment": "exterior"}
    )
    assert any(
        b.code == "TECHNICAL_MATERIAL_COMPATIBILITY_REQUIRED" for b in preview.commercial_blockers
    )
    assert preview.status == "blocked"

    proven = await _preview(
        acm_rates_seeded_db,
        {
            "variant": "oglinda_antracit",
            "environment": "exterior",
            "exterior_sku": "MAT-ACM-MIRROR-ANTRACIT-EXT",
        },
    )
    assert not any(
        b.code == "TECHNICAL_MATERIAL_COMPATIBILITY_REQUIRED" for b in proven.commercial_blockers
    )


@pytest.mark.asyncio
async def test_commercial_product_breakdown_separates_letters_and_acm(acm_rates_seeded_db):
    """Step 3 truth: Litere and Panou ACM are distinct commercial products, and the complete
    offer total is the CPP sum of both — never a partial labelled as the full offer."""
    preview = await _preview(
        acm_rates_seeded_db, {"variant": "standard", "environment": "interior"}
    )
    breakdown = preview.commercial_product_breakdown
    assert breakdown is not None
    by_key = {product.product_key: product for product in breakdown.products}
    assert set(by_key) == {"letters", "acm_panel"}
    assert by_key["letters"].label == "Litere volumetrice"
    assert by_key["acm_panel"].label == "Panou ACM"

    # Every priced line lands in exactly one product bucket.
    assigned = [code for product in breakdown.products for code in product.line_codes]
    assert sorted(assigned) == sorted(line.code for line in preview.commercial_price_lines)
    assert "acm_panel_face_material" in by_key["acm_panel"].line_codes
    assert "acm_panel_face_material" not in by_key["letters"].line_codes
    assert any(code.startswith("finisaje_") for code in by_key["letters"].line_codes)

    # The complete total equals the sum of the product subtotals, per currency.
    for product in breakdown.products:
        assert product.subtotals_by_currency
    per_currency: dict[str, float] = {}
    for product in breakdown.products:
        for bucket in product.subtotals_by_currency:
            per_currency[bucket.currency] = round(
                per_currency.get(bucket.currency, 0.0) + bucket.subtotal, 4
            )
    assert {bucket.currency: bucket.subtotal for bucket in breakdown.subtotals_by_currency} == {
        currency: pytest.approx(total) for currency, total in per_currency.items()
    }
    assert breakdown.tax_status == "tax_exclusive"
    assert breakdown.vat_rate_percent is None

    # F7H: volumetric+ACM presentation is EUR-native. Priced lines share EUR; unpublished
    # rates stay pending (partial total) — never fused with legacy RON via FX rename.
    assert breakdown.presentation_currency == "EUR"
    assert breakdown.currency_mix_detected is False
    assert {bucket.currency for bucket in breakdown.subtotals_by_currency} == {"EUR"}
    assert breakdown.complete_offer_total is not None
    assert breakdown.complete_offer_total_currency == "EUR"
    assert breakdown.complete_offer_total_unavailable_reason is None
    # Unpublished critical rates (e.g. back CNC EUR/m²) keep the total honestly partial.
    assert breakdown.complete_offer_total_is_partial is True or bool(breakdown.pending_line_codes)

    # Owner-pending lines are reported, never silently dropped from the offer story.
    assert set(breakdown.pending_line_codes) == set(by_key["letters"].pending_line_codes) | set(
        by_key["acm_panel"].pending_line_codes
    )
    assert all(
        next(line for line in preview.commercial_price_lines if line.code == code).subtotal is None
        for code in breakdown.pending_line_codes
    )


@pytest.mark.asyncio
async def test_single_currency_offer_exposes_one_complete_total(acm_rates_seeded_db):
    """When every priced line shares one currency, CPP publishes exactly one complete total and
    marks it partial if Owner decisions are still outstanding."""
    from schemas.commercial_price_proposal import CommercialPriceLine
    from services.commercial_price_proposal_service import _build_commercial_product_breakdown

    def _line(code: str, product: str, currency: str | None, subtotal: float | None) -> CommercialPriceLine:
        return CommercialPriceLine(
            code=code,
            label=code,
            module_code="finisaje",
            basis_type="m2",
            source="test",
            pricing_rule_code=code,
            subtotal=subtotal,
            source_currency=currency,
            owner_decision_required=subtotal is None,
            commercial_product_key=product,
        )

    breakdown = _build_commercial_product_breakdown(
        lines=[
            _line("finisaje_oracal_651_material", "letters", "EUR", 4.0),
            _line("finisaje_aplicare_autocolant_fata", "letters", "EUR", 2.4),
            _line("acm_panel_face_material", "acm_panel", "EUR", 10.5),
            _line("montaj", "letters", None, None),
        ],
        blockers=[],
        vat_rate_percent=None,
        vat_policy_source=None,
        presentation_currency="EUR",
    )
    assert breakdown.presentation_currency == "EUR"
    assert breakdown.currency_mix_detected is False
    assert breakdown.complete_offer_total == pytest.approx(16.9)
    assert breakdown.complete_offer_total_currency == "EUR"
    assert breakdown.complete_offer_total_unavailable_reason is None
    assert breakdown.complete_offer_total_is_partial is True
    assert breakdown.pending_line_codes == ["montaj"]

    by_key = {product.product_key: product for product in breakdown.products}
    assert by_key["letters"].subtotals_by_currency[0].subtotal == pytest.approx(6.4)
    assert by_key["acm_panel"].subtotals_by_currency[0].subtotal == pytest.approx(10.5)
    # The complete total is the CPP sum of the products, never a single product's subtotal.
    assert breakdown.complete_offer_total == pytest.approx(
        by_key["letters"].subtotals_by_currency[0].subtotal
        + by_key["acm_panel"].subtotals_by_currency[0].subtotal
    )


@pytest.mark.asyncio
async def test_blocked_product_suppresses_the_complete_offer_total(acm_rates_seeded_db):
    """A blocked product must never yield a confident complete total — Step 3 has to show
    'Total ofertă indisponibil' with an actionable blocker instead."""
    preview = await _preview(
        acm_rates_seeded_db, {"variant": "titan_brushed", "environment": "interior"}
    )
    breakdown = preview.commercial_product_breakdown
    assert breakdown is not None
    assert breakdown.complete_offer_total is None
    assert breakdown.complete_offer_total_currency is None
    assert breakdown.complete_offer_total_unavailable_reason == "COMMERCIAL_PRODUCT_BLOCKED"
    acm = next(p for p in breakdown.products if p.product_key == "acm_panel")
    assert acm.blocked is True
    assert "COMMERCIAL_RULE_MISSING" in acm.blocker_codes
