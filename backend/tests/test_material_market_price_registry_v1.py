"""MATERIAL_MARKET_PRICE_REGISTRY_V1 — purchase truth, normalization, no invented prices."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from models.inventory_materials import Inventory_materials
from services.material_market_price_registry_service import (
    MaterialMarketPriceRegistryService,
    build_normalization,
    classify_source_type,
    compute_freshness,
)
from services.product_price_breakdown_service import ProductPriceBreakdownService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def test_classify_source_precedence_helpers():
    row = Inventory_materials(
        code="X",
        name="X",
        unit="mp",
        unit_cost=10.0,
        source_review_status="owner_confirmed",
        source_name="Owner seed",
    )
    assert classify_source_type(row) == "OWNER_CONFIRMED"

    missing = Inventory_materials(code="Y", name="Y", unit="mp", unit_cost=None)
    assert classify_source_type(missing) == "MISSING"

    invoice = Inventory_materials(
        code="Z",
        name="Z",
        unit="mp",
        unit_cost=1.0,
        source_notes="factura furnizor 2026",
    )
    assert classify_source_type(invoice) == "PURCHASE_INVOICE"


def test_freshness_unknown_without_date():
    status, policy = compute_freshness(source_type="OWNER_CONFIRMED", source_date=None)
    assert status == "UNKNOWN_DATE"
    assert policy


def test_freshness_current_recent_date():
    status, _ = compute_freshness(
        source_type="SUPPLIER_OFFER",
        source_date=datetime.now(timezone.utc) - timedelta(days=5),
    )
    assert status == "CURRENT"


def test_sheet_to_mp_normalization_formula():
    row = Inventory_materials(
        code="MAT-SHEET",
        name="Sheet",
        unit="sheet",
        unit_cost=89.3,
        currency="EUR",
        sheet_width=2440,
        sheet_height=1220,
        sheet_unit="mm",
    )
    norm = build_normalization(row)
    assert norm.conversion_applied is True
    assert norm.normalized_unit == "mp"
    assert norm.sheet_area_m2 == pytest.approx(2.9768, abs=1e-4)
    assert norm.normalized_price == pytest.approx(30.0, abs=0.05)
    assert norm.formula_display
    assert "mp" in norm.formula_display


def test_mp_unit_identity_no_false_conversion():
    row = Inventory_materials(
        code="MAT-ACM-BOND-3MM",
        name="ACM 3mm",
        unit="mp",
        unit_cost=15.0,
        currency="EUR",
    )
    norm = build_normalization(row)
    assert norm.conversion_applied is False
    assert norm.normalized_price == 15.0
    assert norm.normalized_unit == "mp"


@pytest.mark.asyncio
async def test_registry_lists_missing_and_priced(volumetric_v2_db):
    from seeds.seed_acm_bond_materials import seed_acm_bond_materials
    from seeds.seed_acm_owner_confirmed_prices import seed_acm_owner_confirmed_prices
    from seeds.seed_inventory_materials_stubs import seed_inventory_material_stubs

    await seed_inventory_material_stubs()
    await seed_acm_bond_materials()
    await seed_acm_owner_confirmed_prices()

    svc = MaterialMarketPriceRegistryService(volumetric_v2_db)
    out = await svc.build_registry(include_history=False)
    assert out.summary.total >= 1
    assert out.summary.temporary_ai_fallback == 0
    assert "TEMPORARY_AI_FALLBACK" in out.source_precedence

    missing = [i for i in out.items if i.raw_price is None]
    for m in missing:
        assert m.source_type == "MISSING"
        if m.material_role == "variant_selector":
            # Selectors intentionally lack direct purchase price.
            assert m.requires_direct_price is False
            assert m.blocker is None
            assert m.canonical is True
            continue
        assert m.canonical is False
        assert m.blocker

    acm = next((i for i in out.items if i.material_code == "MAT-ACM-BOND-3MM"), None)
    assert acm is not None
    assert acm.raw_price is not None
    assert acm.normalization.normalized_price is not None
    assert acm.canonical is True


@pytest.mark.asyncio
async def test_breakdown_material_provenance_enriched(volumetric_v2_db):
    out = await ProductPriceBreakdownService(volumetric_v2_db).build(
        "TPL-VOLUMETRIC-LETTERS_v2",
        fixture_id="vl_letters_demo_v1",
    )
    material_lines = [l for l in out.lines if l.line_group == "material"]
    assert len(material_lines) >= 1
    # At least gap lines or inventory-backed lines carry market provenance hooks
    assert any(
        l.material_source_type is not None
        or (l.warning and "lipsă" in l.warning.lower())
        for l in material_lines
    )
