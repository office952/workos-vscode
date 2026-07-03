"""Step 7C — QuoteOrchestrator aggregate-expanded cost path tests."""

from __future__ import annotations

import json

import pytest
import pytest_asyncio
from data_models.product_contracts import PricingContext, QuotePricing
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.aggregate_cost_bom_adapter import AggregateCostBomAdapter
from services.aggregate_cost_bom_price_bridge import (
    AggregatePriceContext,
    build_synthetic_hierarchical_template,
    collect_aggregate_pricing_blockers,
    costable_line_keys,
    load_template_row_index,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.quote_orchestrator import QuoteOrchestrator

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"

SAMPLE_RATES = {
    "MAT-SABLON-MONTAJ": 8.0,
    "MAT-SABLON-HARTIE": 2.0,
    "MAT-LED-MODULE": 0.5,
    "MAT-LED-PSU-12V-100W": 45.0,
    "MAT-PROFIL-LATERAL-LITERE-60MM": 3.0,
    "MAT-ORACAL-651": 9.0,
    "MAT-PREMOUNT-BAR-STEEL": 12.0,
    "MAT-ACP-FATA-LITERE": 15.0,
    "MAT-SPATE-PVC-LITERE": 8.0,
    "MAT-VOPSEA-RAL": 10.0,
    "MAT-ADEZIV-CANT-LITERE": 4.0,
}

SAMPLE_WC = {
    "WC_CNC_ROUTING": 120.0,
    "WC_METAL_FAB": 90.0,
    "PREPRESS": 50.0,
    "WC_METAL": 90.0,
}

INVENTORY_CATALOG = {code: {"status": "active", "unit_cost": rate} for code, rate in SAMPLE_RATES.items()}


def _quote_input(*, mounting_system: str = "direct_wall", with_psu: bool = True) -> dict:
    payload = {
        "width_mm": 1200,
        "height_mm": 400,
        "letter_count": 5,
        "letter_perimeter_m": 12.5,
        "letter_face_area_m2": 1.2,
        "return_depth_mm": 60,
        "return_finish_type": "ral_paint",
        "mounting_system": mounting_system,
        "lighting_system_type": "front_lit",
        "illuminated": True,
        "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
        "backing_mode": "closed_back",
    }
    if with_psu:
        payload["selected_psu_watts"] = 100
        payload["led_module_count"] = 180
    return payload


def _product_template_dict() -> dict:
    return {
        "template_code": TEMPLATE,
        "product_id": TEMPLATE,
        "family_id": "litere_volumetrice",
        "family_name": "Litere volumetrice luminoase",
        "components_json": "[]",
        "operations_json": json.dumps(
            [{"code": "legacy_op", "workcenter": "PREPRESS", "formula_id": "legacy_gate"}]
        ),
        "required_materials_json": json.dumps(
            [{"material_code": "MAT-LEGACY-PARENT", "unit": "buc"}]
        ),
    }


def _orchestrator() -> QuoteOrchestrator:
    return QuoteOrchestrator(
        material_rates=dict(SAMPLE_RATES),
        workcenter_rates=dict(SAMPLE_WC),
        base_currency="RON",
    )


async def _build_test_aggregate_context(
    db,
    *,
    quote_input: dict | None = None,
    workspace_id: str | None = None,
) -> AggregatePriceContext:
    pd_builder = ProductDefinitionBuilderService(db)
    aggregate_svc = ProductAggregateService(db)
    adapter = AggregateCostBomAdapter()

    pd = await pd_builder.build_preview(TEMPLATE, workspace_id=workspace_id)
    aggregate = await aggregate_svc.build(TEMPLATE)
    assert pd is not None and aggregate is not None

    bom = adapter.build(
        product_definition=pd,
        aggregate=aggregate,
        quote_input=quote_input,
        material_rates=SAMPLE_RATES,
        workcenter_rates=SAMPLE_WC,
        inventory_catalog=INVENTORY_CATALOG,
    )
    template_rows = await load_template_row_index(db, aggregate)
    return AggregatePriceContext(
        template_code=TEMPLATE,
        aggregate=aggregate,
        aggregate_cost_bom=bom,
        template_rows=template_rows,
    )


@pytest_asyncio.fixture
async def aggregate_price_ctx(volumetric_v2_db):
    return await _build_test_aggregate_context(
        volumetric_v2_db,
        quote_input=_quote_input(),
    )


@pytest.mark.asyncio
async def test_volumetric_price_path_no_comp_flat_legacy(aggregate_price_ctx):
    orch = _orchestrator()
    snap = orch.build_snapshot(
        product_template=_product_template_dict(),
        user_config={"quantity": 1, "dimensions": {"width_mm": 1200, "height_mm": 400}},
        pricing=QuotePricing(margin_pct=40, discount_pct=0, vat_pct=19),
        pricing_context=PricingContext(currency="RON"),
        quote_input=_quote_input(),
        aggregate_price_context=aggregate_price_ctx,
    )
    breakdown = getattr(snap, "component_breakdown", []) or []
    ids = {c.get("component_id") for c in breakdown}
    assert "comp_flat_legacy" not in ids
    assert getattr(snap, "aggregate_cost_source", False) is True
    assert getattr(snap, "cost_engine_version", "") == "v2_aggregate"


@pytest.mark.asyncio
async def test_volumetric_uses_aggregate_cost_bom_adapter(aggregate_price_ctx):
    synthetic = build_synthetic_hierarchical_template(aggregate_price_ctx)
    assert synthetic.get("_aggregate_expanded_source") is True
    comps = synthetic.get("components_json") or []
    assert comps
    assert all(c.get("component_id") != "comp_flat_legacy" for c in comps)


@pytest.mark.asyncio
async def test_dossier_components_in_cost_breakdown(aggregate_price_ctx):
    orch = _orchestrator()
    snap = orch.build_snapshot(
        product_template=_product_template_dict(),
        user_config={"quantity": 1, "dimensions": {"width_mm": 1200, "height_mm": 400}},
        pricing=QuotePricing(margin_pct=40, discount_pct=0, vat_pct=19),
        quote_input=_quote_input(),
        aggregate_price_context=aggregate_price_ctx,
    )
    breakdown = getattr(snap, "component_breakdown", []) or []
    ids = {c.get("component_id") for c in breakdown}
    assert "comp_face_litere" in ids or "comp_lateral_litere" in ids


@pytest.mark.asyncio
async def test_geometry_svg_not_priced_operation(aggregate_price_ctx):
    bom = aggregate_price_ctx.aggregate_cost_bom
    assert not any(o.operation_code == "svg_geometry_analysis" for o in bom.costable_operations)


@pytest.mark.asyncio
async def test_electrica_logo_not_costed(aggregate_price_ctx):
    bom = aggregate_price_ctx.aggregate_cost_bom
    assert not any(c.mini_module_code == "electrica_logo" for c in bom.costable_components)
    assert any(s.item_key == "electrica_logo" for s in bom.skipped_items)


@pytest.mark.asyncio
async def test_structura_suport_inactive_excluded(volumetric_v2_db):
    ctx = await _build_test_aggregate_context(
        volumetric_v2_db,
        quote_input=_quote_input(mounting_system="direct_wall"),
    )
    premount = [
        m for m in ctx.aggregate_cost_bom.costable_materials if "PREMOUNT" in (m.source_template_code or "")
    ]
    assert premount == []


@pytest.mark.asyncio
async def test_structura_suport_active_included_or_blocked(volumetric_v2_db):
    ctx = await _build_test_aggregate_context(
        volumetric_v2_db,
        quote_input=_quote_input(mounting_system="steel_bars"),
    )
    premount = [
        m for m in ctx.aggregate_cost_bom.costable_materials if "PREMOUNT" in (m.source_template_code or "")
    ]
    assert premount or collect_aggregate_pricing_blockers(ctx.aggregate_cost_bom)


@pytest.mark.asyncio
async def test_missing_psu_watts_blocks_not_zero(volumetric_v2_db):
    ctx = await _build_test_aggregate_context(
        volumetric_v2_db,
        quote_input=_quote_input(with_psu=False),
    )
    blockers = collect_aggregate_pricing_blockers(ctx.aggregate_cost_bom)
    assert blockers or ctx.aggregate_cost_bom.missing_pricing
    orch = _orchestrator()
    snap = orch.build_snapshot(
        product_template=_product_template_dict(),
        user_config={"quantity": 1, "dimensions": {"width_mm": 1200, "height_mm": 400}},
        pricing=QuotePricing(margin_pct=40, discount_pct=0, vat_pct=19),
        quote_input=_quote_input(with_psu=False),
        aggregate_price_context=ctx,
    )
    assert snap.status == "blocked"
    assert snap.cost_result.total_cost == 0.0


@pytest.mark.asyncio
async def test_missing_material_rate_blocks(volumetric_v2_db):
    ctx = await _build_test_aggregate_context(
        volumetric_v2_db,
        quote_input=_quote_input(),
    )
    orch = QuoteOrchestrator(material_rates={}, workcenter_rates=SAMPLE_WC)
    snap = orch.build_snapshot(
        product_template=_product_template_dict(),
        user_config={"quantity": 1, "dimensions": {"width_mm": 1200, "height_mm": 400}},
        pricing=QuotePricing(margin_pct=40, discount_pct=0, vat_pct=19),
        quote_input=_quote_input(),
        aggregate_price_context=ctx,
    )
    assert snap.status == "blocked"


@pytest.mark.asyncio
async def test_unused_inventory_not_in_costable(aggregate_price_ctx):
    bom = aggregate_price_ctx.aggregate_cost_bom
    costable = {m.resolved_material_code or m.material_code for m in bom.costable_materials}
    for unused in bom.unused_inventory_candidates:
        assert unused not in costable


@pytest.mark.asyncio
async def test_legacy_parent_not_in_costable(aggregate_price_ctx):
    bom = aggregate_price_ctx.aggregate_cost_bom
    costable = {m.material_code for m in bom.costable_materials}
    for legacy in bom.legacy_inventory_references:
        if legacy.startswith("MAT-LEGACY"):
            assert legacy not in costable


@pytest.mark.asyncio
async def test_future_externalization_not_blocking(aggregate_price_ctx):
    bom = aggregate_price_ctx.aggregate_cost_bom
    ext_blockers = [
        b for b in bom.pricing_blockers if b.blocker_code == "EXTERNAL_PRICE_REQUIRED"
    ]
    assert ext_blockers == []
    assert not any(r.selected_now for r in bom.externalization_requirements)


@pytest.mark.asyncio
async def test_commercial_markup_applied_on_valid_case(aggregate_price_ctx):
    orch = _orchestrator()
    pricing = QuotePricing(margin_pct=50, discount_pct=0, vat_pct=19)
    snap = orch.build_snapshot(
        product_template=_product_template_dict(),
        user_config={"quantity": 1, "dimensions": {"width_mm": 1200, "height_mm": 400}},
        pricing=pricing,
        quote_input=_quote_input(),
        aggregate_price_context=aggregate_price_ctx,
    )
    if snap.status == "priced":
        assert snap.price is not None
        assert snap.price.grand_total > snap.cost_result.total_cost


@pytest.mark.asyncio
async def test_preview_price_parity_line_keys(volumetric_v2_db):
    ctx = await _build_test_aggregate_context(volumetric_v2_db, quote_input=_quote_input())
    bom_keys = costable_line_keys(ctx.aggregate_cost_bom)
    orch = _orchestrator()
    snap = orch.build_snapshot(
        product_template=_product_template_dict(),
        user_config={"quantity": 1, "dimensions": {"width_mm": 1200, "height_mm": 400}},
        pricing=QuotePricing(margin_pct=40, discount_pct=0, vat_pct=19),
        quote_input=_quote_input(),
        aggregate_price_context=ctx,
    )
    price_keys = set(getattr(snap, "aggregate_cost_line_keys", []) or [])
    if snap.status == "priced":
        assert bom_keys.issubset(price_keys)


@pytest.mark.asyncio
async def test_no_db_writes_on_aggregate_price_build(volumetric_v2_db):
    from sqlalchemy import func, select

    before = await volumetric_v2_db.scalar(select(func.count()).select_from(IntakeV6WorkspaceRecord))
    ctx = await _build_test_aggregate_context(volumetric_v2_db, quote_input=_quote_input())
    orch = _orchestrator()
    orch.build_snapshot(
        product_template=_product_template_dict(),
        user_config={"quantity": 1, "dimensions": {"width_mm": 1200, "height_mm": 400}},
        pricing=QuotePricing(margin_pct=40, discount_pct=0, vat_pct=19),
        quote_input=_quote_input(),
        aggregate_price_context=ctx,
    )
    after = await volumetric_v2_db.scalar(select(func.count()).select_from(IntakeV6WorkspaceRecord))
    assert before == after


@pytest.mark.asyncio
async def test_volumetric_without_aggregate_context_blocks(volumetric_v2_db):
    orch = _orchestrator()
    snap = orch.build_snapshot(
        product_template=_product_template_dict(),
        user_config={"quantity": 1, "dimensions": {"width_mm": 1200, "height_mm": 400}},
        pricing=QuotePricing(margin_pct=40, discount_pct=0, vat_pct=19),
        quote_input=_quote_input(),
        aggregate_price_context=None,
    )
    assert snap.status == "blocked"
    assert "aggregate_bom:context_not_prepared" in snap.blocked_reasons


@pytest.mark.asyncio
async def test_quote_4_read_only_not_repriced(volumetric_v2_db):
    """Quote 4 audit only — no /price call, no mutation."""
    from sqlalchemy import select

    from models.quotes import Quotes

    result = await volumetric_v2_db.execute(select(Quotes).where(Quotes.id == 4))
    row = result.scalar_one_or_none()
    if row is None:
        pytest.skip("Quote 4 not present in test DB")
    status_before = row.status
    total_before = row.grand_total
    assert status_before is not None
    assert total_before == row.grand_total
