"""F7H — native EUR commercial pricing functional closure (volumetric letters + ACM).

Architecture / currency integrity tests. Final commercial tariff levels remain deferred —
fixtures inject explicit rates; unpublished rates fail closed without invention.
"""

from __future__ import annotations

import copy
import json
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.workcenter_rates import Workcenter_rates
from schemas.commercial_price_proposal import CommercialBlocker, CommercialPriceLine
from seeds.seed_acm_bond_materials import seed_acm_bond_materials
from seeds.seed_acm_boxed_mounting_owner_rates import seed_acm_boxed_mounting_owner_rates
from seeds.seed_acm_owner_confirmed_prices import seed_acm_owner_confirmed_prices
from seeds.seed_tpl_acm_boxed_mounting_support_v1 import seed_tpl_acm_boxed_mounting_support_v1
from services.commercial_price_proposal_service import (
    CommercialPriceProposalService,
    _apply_cant_ral_paint_minimum_eur,
    _build_commercial_product_breakdown,
)
from services.company_commercial_settings_service import CompanyCommercialSettingsService
from services.quote_snapshot_v2_service import QuoteSnapshotV2Service

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _eur_letters_payload(*, illuminated: bool = False, ral: bool = False) -> dict:
    finish: dict = {
        "face_finish_type": "oracal_651",
        "return_depth_mm": 60,
        "return_finish_type": "ral_paint" if ral else "white_aluminum",
        "backing_mode": "closed_back",
        "mounting_system": "direct_wall",
        "lighting_system_type": "front_lit" if illuminated else "none",
        "illuminated": illuminated,
        "mounting_template_enabled": False,
        "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
    }
    if illuminated:
        finish["led_module_count"] = 10
        finish["selected_psu_watts"] = 60
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "f7h.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 4,
            "letter_perimeter_m": 10.0,
            "letter_face_area_m2": 1.0,
        },
        "finish_setup": finish,
    }


def _letters_acm_payload() -> dict:
    from tests.test_f7f_owner_commercial_law_step3_total import _letters_with_acm_panel

    return _letters_with_acm_panel({"variant": "standard", "environment": "interior"})


async def _upsert_rate(db, *, code: str, amount: float, currency: str = "EUR") -> None:
    await CompanyCommercialSettingsService(db).update_settings(eur_to_ron_rate=5.0)
    existing = (
        await db.execute(select(Workcenter_rates).where(Workcenter_rates.code == code).limit(1))
    ).scalar_one_or_none()
    # Commercial ops historically store unit rates in rate_per_linear_meter (including fixed).
    if existing is None:
        db.add(
            Workcenter_rates(
                code=code,
                label=code,
                rate_basis="per_piece" if code == "SITE_INSTALLATION_STANDARD" else "per_linear_meter",
                rate_per_linear_meter=amount,
                currency=currency,
                status="active",
                is_active=True,
                notes="F7H test fixture — documented EUR registry rate.",
            )
        )
    else:
        existing.rate_per_linear_meter = amount
        existing.rate_basis = (
            "per_piece" if code == "SITE_INSTALLATION_STANDARD" else "per_linear_meter"
        )
        existing.currency = currency
        existing.status = "active"
        existing.is_active = True
    await db.commit()


@pytest_asyncio.fixture
async def f7h_db(volumetric_v2_db):
    from seeds.seed_inventory_materials_stubs import seed_inventory_material_stubs

    await seed_inventory_material_stubs()
    await seed_acm_bond_materials()
    await seed_acm_owner_confirmed_prices()
    await seed_acm_boxed_mounting_owner_rates()
    await seed_tpl_acm_boxed_mounting_support_v1()
    for code, amount in (
        ("CNC_ROUTER", 1.5),
        ("RETURN_PROFILE_MACHINE_FORMING", 5.0),
        ("RETURN_CANT_RAL_PAINT_LABOR", 1.0),
        ("SITE_INSTALLATION_STANDARD", 200.0),
    ):
        await _upsert_rate(volumetric_v2_db, code=code, amount=amount)
    return volumetric_v2_db


@pytest_asyncio.fixture
async def cpp(f7h_db):
    yield CommercialPriceProposalService(f7h_db)


@pytest.mark.asyncio
async def test_f7h_presentation_currency_eur_scoped(cpp):
    preview = await cpp.build_preview(TEMPLATE, quote_input=_eur_letters_payload())
    assert preview is not None
    assert preview.currency == "EUR"
    assert preview.commercial_product_breakdown is not None
    assert preview.commercial_product_breakdown.presentation_currency == "EUR"


@pytest.mark.asyncio
async def test_f7h_five_former_dev_bridge_routes_eur_or_unpublished(cpp):
    preview = await cpp.build_preview(TEMPLATE, quote_input=_eur_letters_payload(illuminated=True))
    assert preview is not None
    by_code = {line.code: line for line in preview.commercial_price_lines}

    face = by_code["debitare_fata"]
    assert face.cpp_currency == "EUR"
    assert face.commercial_unit_price == pytest.approx(1.5)
    assert face.unit == "ml"

    forming = by_code["modelare_cant_aluminiu"]
    assert forming.cpp_currency == "EUR"
    assert forming.commercial_unit_price == pytest.approx(5.0)
    assert forming.unit == "ml"

    back = by_code["debitare_spate"]
    assert back.basis_type == "m2"
    assert back.unit == "m2"
    assert back.commercial_unit_price is None
    assert back.owner_decision_required is True
    assert back.rate_publication_status == "unpublished"

    led = by_code["sistem_led_module"]
    assert led.commercial_unit_price is None
    assert led.owner_decision_required is True
    assert led.rate_publication_status == "unpublished"

    psu = by_code["sursa_led"]
    assert psu.commercial_unit_price is None
    assert psu.owner_decision_required is True


@pytest.mark.asyncio
async def test_f7h_ral_labor_and_montaj_native_eur(cpp, f7h_db):
    payload = _eur_letters_payload(ral=True)
    payload["finish_setup"]["mounting_scope"] = "preparation_and_site_installation"
    payload["finish_setup"]["site_installation_included"] = True
    payload["finish_setup"]["mounting_solution"] = {
        "kind": "installation_template",
        "template_code": None,
        "configuration": {},
    }
    preview = await cpp.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    labor = next(line for line in preview.commercial_price_lines if line.code == "finisaje_cant_ral_labor")
    assert labor.cpp_currency == "EUR"
    assert labor.commercial_unit_price == pytest.approx(1.0)
    assert labor.currency_conversion_rate is None
    montaj = next(line for line in preview.commercial_price_lines if line.code == "montaj")
    assert montaj.cpp_currency == "EUR"
    assert montaj.commercial_unit_price == pytest.approx(200.0)
    assert montaj.unit == "locatie"


@pytest.mark.asyncio
async def test_f7h_ral_top_up_explicit_eur_line(cpp, monkeypatch):
    import data.commercial_rules_volumetric_v2 as rules_mod
    import services.commercial_price_proposal_service as cpp_mod

    monkeypatch.setattr(rules_mod, "CANT_RAL_PAINT_MINIMUM_EUR_PER_COLOR", 50.0)
    monkeypatch.setattr(cpp_mod, "CANT_RAL_PAINT_MINIMUM_EUR_PER_COLOR", 50.0)
    # 10 ml × 2.5 EUR material + 10 ml × 1 EUR labor = 35 < 50 → top-up 15
    payload = _eur_letters_payload(ral=True)
    preview = await cpp.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    material = next(
        line for line in preview.commercial_price_lines if line.code == "finisaje_cant_ral_material"
    )
    assert material.subtotal == pytest.approx(25.0)
    top_up = next(
        line for line in preview.commercial_price_lines if line.code == "finisaje_cant_ral_minimum_top_up"
    )
    assert top_up.cpp_currency == "EUR"
    assert top_up.subtotal == pytest.approx(15.0)
    assert top_up.basis_type == "minimum"


@pytest.mark.asyncio
async def test_f7h_ral_exactly_at_minimum_no_top_up(monkeypatch):
    lines = [
        CommercialPriceLine(
            code="finisaje_cant_ral_material",
            label="m",
            module_code="finisaje",
            basis_type="ml",
            source="t",
            pricing_rule_code="VOL_V2_CANT_RAL_MATERIAL_ML",
            subtotal=30.0,
            source_currency="EUR",
            cpp_currency="EUR",
            commercial_product_key="letters",
        ),
        CommercialPriceLine(
            code="finisaje_cant_ral_labor",
            label="l",
            module_code="finisaje",
            basis_type="ml",
            source="t",
            pricing_rule_code="VOL_V2_CANT_RAL_LABOR_ML",
            subtotal=20.0,
            source_currency="EUR",
            cpp_currency="EUR",
            commercial_product_key="letters",
        ),
    ]
    blockers: list[CommercialBlocker] = []
    _apply_cant_ral_paint_minimum_eur(lines, blockers=blockers, minimum_eur_per_color=50.0)
    assert blockers == []
    assert not any(line.code == "finisaje_cant_ral_minimum_top_up" for line in lines)


@pytest.mark.asyncio
async def test_f7h_ral_currency_mismatch_blocked():
    lines = [
        CommercialPriceLine(
            code="finisaje_cant_ral_material",
            label="m",
            module_code="finisaje",
            basis_type="ml",
            source="t",
            pricing_rule_code="VOL_V2_CANT_RAL_MATERIAL_ML",
            subtotal=17.6185,
            source_currency="EUR",
            cpp_currency="EUR",
            commercial_product_key="letters",
        ),
        CommercialPriceLine(
            code="finisaje_cant_ral_labor",
            label="l",
            module_code="finisaje",
            basis_type="ml",
            source="t",
            pricing_rule_code="VOL_V2_CANT_RAL_LABOR_ML",
            subtotal=35.237,
            source_currency="EUR",
            cpp_currency="RON",  # dishonest cross-currency — must refuse
            commercial_product_key="letters",
        ),
    ]
    blockers: list[CommercialBlocker] = []
    _apply_cant_ral_paint_minimum_eur(lines, blockers=blockers, minimum_eur_per_color=100.0)
    assert any(b.code == "COMMERCIAL_MINIMUM_CURRENCY_MISMATCH" for b in blockers)
    assert not any(line.code == "finisaje_cant_ral_minimum_top_up" for line in lines)
    # Material subtotal must not be mutated into a fake EUR figure.
    assert lines[0].subtotal == pytest.approx(17.6185)


@pytest.mark.asyncio
async def test_f7h_mixed_eur_ron_fail_closed():
    breakdown = _build_commercial_product_breakdown(
        lines=[
            CommercialPriceLine(
                code="a",
                label="a",
                module_code="x",
                basis_type="ml",
                source="t",
                pricing_rule_code="a",
                subtotal=10.0,
                source_currency="EUR",
                cpp_currency="EUR",
                commercial_product_key="letters",
            ),
            CommercialPriceLine(
                code="b",
                label="b",
                module_code="x",
                basis_type="m2",
                source="t",
                pricing_rule_code="b",
                subtotal=20.0,
                source_currency="RON",
                cpp_currency="RON",
                commercial_product_key="letters",
            ),
        ],
        blockers=[],
        vat_rate_percent=None,
        vat_policy_source=None,
        presentation_currency="EUR",
    )
    assert breakdown.complete_offer_total is None
    assert breakdown.currency_mix_detected is True
    assert breakdown.complete_offer_total_unavailable_reason in {
        "COMMERCIAL_CURRENCY_MIX_UNRESOLVED",
        "COMMERCIAL_PRESENTATION_CURRENCY_UNAVAILABLE",
    }


@pytest.mark.asyncio
async def test_f7h_ron_only_legacy_total_still_works():
    breakdown = _build_commercial_product_breakdown(
        lines=[
            CommercialPriceLine(
                code="legacy",
                label="legacy",
                module_code="x",
                basis_type="m2",
                source="t",
                pricing_rule_code="legacy",
                subtotal=100.0,
                source_currency="RON",
                cpp_currency="RON",
                commercial_product_key="letters",
            ),
        ],
        blockers=[],
        vat_rate_percent=19.0,
        vat_policy_source="test",
        presentation_currency=None,
    )
    assert breakdown.complete_offer_total == pytest.approx(100.0)
    assert breakdown.complete_offer_total_currency == "RON"
    assert breakdown.vat_rate_percent == 19.0


@pytest.mark.asyncio
async def test_f7h_letters_acm_eur_total(cpp):
    preview = await cpp.build_preview(TEMPLATE, quote_input=_letters_acm_payload())
    assert preview is not None
    breakdown = preview.commercial_product_breakdown
    assert breakdown is not None
    assert breakdown.presentation_currency == "EUR"
    assert breakdown.currency_mix_detected is False
    keys = {p.product_key for p in breakdown.products}
    assert keys == {"letters", "acm_panel"}
    if breakdown.complete_offer_total is not None:
        assert breakdown.complete_offer_total_currency == "EUR"
        assert breakdown.complete_offer_total > 0


@pytest.mark.asyncio
async def test_f7h_cpp_does_not_read_eic_total(cpp):
    path = __import__("pathlib").Path(__file__).resolve().parents[1] / "services" / "commercial_price_proposal_service.py"
    text = path.read_text(encoding="utf-8")
    assert "from services.estimated_internal_cost" not in text
    assert "EstimatedInternalCostService" not in text
    assert "estimated_internal_cost_trace" not in text
    preview = await cpp.build_preview(TEMPLATE, quote_input=_eur_letters_payload())
    assert preview is not None
    dumped = preview.model_dump_json().lower()
    assert "estimated_internal_cost" not in dumped
    assert "eic_total" not in dumped


@pytest.mark.asyncio
async def test_f7h_snapshot_freezes_commercial_and_ignores_registry_change(f7h_db):
    payload = _eur_letters_payload()
    snap_svc = QuoteSnapshotV2Service(f7h_db)
    snap_a = await snap_svc.build_preview(TEMPLATE, quote_input=payload)
    assert snap_a is not None
    commercial_a = snap_a.commercial_price_proposal_snapshot
    face_a = next(line for line in commercial_a.commercial_price_lines if line.code == "debitare_fata")
    assert face_a.commercial_unit_price == pytest.approx(1.5)

    try:
        await _upsert_rate(f7h_db, code="CNC_ROUTER", amount=9.9)
        preview_b = await CommercialPriceProposalService(f7h_db).build_preview(
            TEMPLATE, quote_input=payload
        )
        assert preview_b is not None
        face_b = next(line for line in preview_b.commercial_price_lines if line.code == "debitare_fata")
        assert face_b.commercial_unit_price == pytest.approx(9.9)

        # Frozen snapshot A must keep the original rate — no reprice.
        face_frozen = next(
            line
            for line in commercial_a.commercial_price_lines
            if line.code == "debitare_fata"
        )
        assert face_frozen.commercial_unit_price == pytest.approx(1.5)
        assert face_frozen.cpp_currency == "EUR"
        assert commercial_a.commercial_product_breakdown is not None
        assert commercial_a.commercial_product_breakdown.presentation_currency == "EUR"
    finally:
        # Restore — do not poison later suites sharing the process DB fixture.
        await _upsert_rate(f7h_db, code="CNC_ROUTER", amount=1.5)


@pytest.mark.asyncio
async def test_f7h_no_eur_plus_ron_numeric_replacement():
    """Regression guard for the F7G-R1 defect: never emit RON remainder labelled as EUR."""
    lines = [
        CommercialPriceLine(
            code="finisaje_cant_ral_material",
            label="m",
            module_code="finisaje",
            basis_type="ml",
            source="t",
            pricing_rule_code="VOL_V2_CANT_RAL_MATERIAL_ML",
            subtotal=17.6185,
            source_currency="EUR",
            cpp_currency="EUR",
            commercial_product_key="letters",
        ),
        CommercialPriceLine(
            code="finisaje_cant_ral_labor",
            label="l",
            module_code="finisaje",
            basis_type="ml",
            source="t",
            pricing_rule_code="VOL_V2_CANT_RAL_LABOR_ML",
            subtotal=35.237,
            source_currency="EUR",
            cpp_currency="EUR",
            commercial_product_key="letters",
        ),
    ]
    blockers: list[CommercialBlocker] = []
    # Unpublished EUR floor — must not fall back to 100 RON math.
    _apply_cant_ral_paint_minimum_eur(lines, blockers=blockers, minimum_eur_per_color=None)
    assert blockers == []
    assert lines[0].subtotal == pytest.approx(17.6185)
    assert not any(abs((line.subtotal or 0) - 64.763) < 1e-6 for line in lines)
