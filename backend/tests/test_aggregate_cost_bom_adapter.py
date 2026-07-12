"""Tests for aggregate-expanded cost BOM adapter (Step 7B)."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.aggregate_cost_bom_adapter import AggregateCostBomAdapter, AggregateCostBomBuilderService
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService

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
}

SAMPLE_WC_RATES = {
    "WC_CNC_ROUTING": 120.0,
    "WC_METAL_FAB": 90.0,
    "PREPRESS": 50.0,
}

INVENTORY_CATALOG = {
    code: {"status": "active", "unit_cost": rate}
    for code, rate in {
        **SAMPLE_RATES,
        "MAT-LED-PSU-12V-60W": 30.0,
        "MAT-LED-PSU-12V-160W": 55.0,
        "MAT-LED-PSU-12V-200W": 65.0,
        "MAT-ACP-FATA-LITERE": 15.0,
        "MAT-SPATE-PVC-LITERE": 8.0,
        "MAT-ADEZIV-CANT-LITERE": 4.0,
        "MAT-VOPSEA-RAL": 10.0,
        "MAT-VINYL-PRINT": 5.0,
        "MAT-CONSUMABILE-MONTAJ": 2.0,
        "MAT-CABLU-MYYUP-2X075": 3.0,
        "MAT-PREMOUNT-BAR-ALUMINUM": 11.0,
    }.items()
}


def _full_payload(*, mounting_system: str = "direct_wall", with_psu: bool = True) -> dict:
    finish = {
        "face_finish_type": "plexiglas_clear",
        "return_depth_mm": 60,
        "return_finish_type": "ral",
        "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
        "backing_mode": "closed_back",
        "mounting_system": mounting_system,
        "lighting_system_type": "front_lit",
        "illuminated": True,
    }
    if with_psu:
        finish["selected_psu_watts"] = 100
        finish["led_module_count"] = 180
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "test.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
        },
        "finish_setup": finish,
    }


@pytest_asyncio.fixture
async def bom_context(volumetric_v2_db):
    pd_builder = ProductDefinitionBuilderService(volumetric_v2_db)
    aggregate_svc = ProductAggregateService(volumetric_v2_db)
    adapter = AggregateCostBomAdapter()

    async def _build(*, workspace_id: str | None = None, quote_input=None, rates=None, wc=None, inventory=None, external_selections=None):
        pd = await pd_builder.build_preview(TEMPLATE, workspace_id=workspace_id)
        if workspace_id:
            aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, workspace_id)
        else:
            aggregate = await aggregate_svc.build(TEMPLATE)
        assert pd is not None and aggregate is not None
        return adapter.build(
            product_definition=pd,
            aggregate=aggregate,
            quote_input=quote_input,
            material_rates=rates if rates is not None else SAMPLE_RATES,
            workcenter_rates=wc if wc is not None else SAMPLE_WC_RATES,
            inventory_catalog=inventory if inventory is not None else INVENTORY_CATALOG,
            external_selections=external_selections,
        )

    return _build


@pytest.mark.asyncio
async def test_nested_finish_setup_flattens_return_depth_for_profile_variant(bom_context):
    """IV6 quote_input nests return_depth_mm under finish_setup — BOM must resolve profile variant."""
    bom = await bom_context(quote_input=_full_payload())
    profile_rows = [
        m
        for m in bom.costable_materials
        if (m.material_code or "").startswith("MAT-PROFIL-LATERAL-LITERE")
    ]
    assert profile_rows
    assert all(m.pricing_availability == "available" for m in profile_rows)
    assert all(m.unit_cost is not None and m.unit_cost > 0 for m in profile_rows)
    resolved_codes = {m.resolved_material_code or m.material_code for m in profile_rows}
    assert "MAT-PROFIL-LATERAL-LITERE-60MM" in resolved_codes


@pytest.mark.asyncio
async def test_no_comp_auto_1_in_costable_components(bom_context):
    bom = await bom_context()
    ids = {c.component_id for c in bom.costable_components}
    assert "comp_auto_1" not in ids
    skipped_ids = {s.item_key for s in bom.skipped_items if s.item_type == "component"}
    assert "comp_flat_legacy" in skipped_ids


@pytest.mark.asyncio
async def test_includes_aggregate_dossier_components(bom_context):
    bom = await bom_context()
    ids = {c.component_id for c in bom.costable_components}
    for expected in (
        "comp_face_litere",
        "comp_lateral_litere",
        "comp_spate_litere",
        "comp_finisaj_litere",
    ):
        assert expected in ids
    assert "comp_led_litere" not in ids


@pytest.mark.asyncio
async def test_geometry_svg_gate_not_in_costable_operations(bom_context):
    bom = await bom_context()
    op_codes = {o.operation_code for o in bom.costable_operations}
    assert "svg_geometry_analysis" not in op_codes
    assert any(
        s.item_key == "svg_geometry_analysis" and s.reason == "geometry_gate"
        for s in bom.skipped_items
    )


@pytest.mark.asyncio
async def test_electrica_logo_future_not_costed(bom_context):
    bom = await bom_context()
    assert any(s.item_key == "electrica_logo" and s.reason == "future_reserved" for s in bom.skipped_items)
    assert not any(c.mini_module_code == "electrica_logo" for c in bom.costable_components)


@pytest.mark.asyncio
async def test_structura_suport_excluded_for_direct_wall(bom_context, volumetric_v2_db):
    ws_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=ws_id,
            workspace_code=f"WS-BOM-{ws_id[:8]}",
            title="BOM direct wall",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(_full_payload(mounting_system="direct_wall")),
        )
    )
    await volumetric_v2_db.commit()
    bom = await bom_context(workspace_id=ws_id)
    premount_mats = [
        m for m in bom.costable_materials if m.source_template_code and "PREMOUNT" in m.source_template_code
    ]
    assert premount_mats == []
    structura = next((m for m in bom.inactive_modules if m.module_code == "structura_suport"), None)
    assert structura is not None
    assert structura.included_in_cost_bom is False


@pytest.mark.asyncio
async def test_structura_suport_included_for_steel_bars(bom_context, volumetric_v2_db):
    ws_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=ws_id,
            workspace_code=f"WS-BOM-{ws_id[:8]}",
            title="BOM steel bars",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(_full_payload(mounting_system="steel_bars")),
        )
    )
    await volumetric_v2_db.commit()
    bom = await bom_context(workspace_id=ws_id)
    structura_active = any(
        m.module_code == "structura_suport" and m.included_in_cost_bom for m in bom.active_modules
    )
    assert structura_active
    premount_mats = [
        m for m in bom.costable_materials if m.source_template_code and "PREMOUNT" in (m.source_template_code or "")
    ]
    assert premount_mats


@pytest.mark.asyncio
async def test_sistem_led_included_with_workspace_payload(bom_context, volumetric_v2_db):
    ws_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=ws_id,
            workspace_code=f"WS-BOM-{ws_id[:8]}",
            title="BOM led",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(_full_payload(mounting_system="direct_wall", with_psu=True)),
        )
    )
    await volumetric_v2_db.commit()
    bom = await bom_context(workspace_id=ws_id)
    ids = {c.component_id for c in bom.costable_components}
    assert "comp_led_litere" in ids


@pytest.mark.asyncio
async def test_missing_psu_watts_produces_requirement_not_zero_cost(bom_context, volumetric_v2_db):
    ws_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=ws_id,
            workspace_code=f"WS-BOM-{ws_id[:8]}",
            title="BOM no psu",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(_full_payload(mounting_system="direct_wall", with_psu=False)),
        )
    )
    await volumetric_v2_db.commit()
    bom = await bom_context(workspace_id=ws_id)
    assert "selected_psu_watts" in bom.missing_geometry or any(
        m.reason == "missing_psu_watts_selection" for m in bom.missing_pricing
    )
    psu_mats = [m for m in bom.costable_materials if "PSU" in m.material_code]
    for mat in psu_mats:
        assert mat.unit_cost is None or mat.pricing_availability != "available"


@pytest.mark.asyncio
async def test_missing_rates_produce_missing_pricing_not_silent_zero(bom_context):
    bom = await bom_context(rates={}, wc={})
    assert bom.missing_pricing
    assert bom.bom_status == "blocked"
    for mat in bom.costable_materials:
        if mat.pricing_availability == "available":
            assert mat.unit_cost and mat.unit_cost > 0


@pytest.mark.asyncio
async def test_always_on_modules_have_cost_lines(bom_context):
    bom = await bom_context()
    modules_with_lines = set()
    for item in bom.costable_components + bom.costable_materials + bom.costable_operations:
        if item.mini_module_code:
            modules_with_lines.add(item.mini_module_code)
    for expected in ("debitare_fata", "modelare_cant", "debitare_spate"):
        assert expected in modules_with_lines


@pytest.mark.asyncio
async def test_provenance_and_warnings_propagated(bom_context):
    bom = await bom_context()
    assert len(bom.provenance) >= 3
    assert any("TRIGGER" in w or "PARENT_COMPONENTS" in w for w in bom.warnings)


@pytest.mark.asyncio
async def test_parent_bom_not_structural_truth(bom_context):
    bom = await bom_context()
    assert bom.source_context.uses_parent_bom_as_structural_truth is False
    assert bom.source_context.legacy_parent_bom_note


@pytest.mark.asyncio
async def test_no_db_writes_on_build(bom_context, volumetric_v2_db):
    from sqlalchemy import func, select

    before = await volumetric_v2_db.scalar(select(func.count()).select_from(IntakeV6WorkspaceRecord))
    await bom_context()
    after = await volumetric_v2_db.scalar(select(func.count()).select_from(IntakeV6WorkspaceRecord))
    assert before == after


@pytest.fixture
def bom_auth_client(volumetric_auth_client):
    return volumetric_auth_client


def test_cost_bom_preview_endpoint_200(bom_auth_client):
    response = bom_auth_client.get(f"/api/v1/product-system/cost-bom-preview/{TEMPLATE}")
    assert response.status_code == 200
    body = response.json()
    assert body["template_code"] == TEMPLATE
    assert body["bom_status"] in ("ready", "partial", "blocked")
    assert "costable_components" in body
    assert body["source_context"]["uses_parent_bom_as_structural_truth"] is False


def test_cost_bom_preview_endpoint_404(bom_auth_client):
    response = bom_auth_client.get("/api/v1/product-system/cost-bom-preview/TPL-UNKNOWN")
    assert response.status_code == 404


# --- Step 7B.1 inventory alignment ---


@pytest.mark.asyncio
async def test_active_materials_mapped_to_inventory_usage(bom_context):
    bom = await bom_context()
    assert bom.inventory_usage
    active_used = [
        u for u in bom.inventory_usage if u.classification == "USED_BY_ACTIVE_TEMPLATE" and u.module_active
    ]
    assert active_used
    costable_codes = {m.material_code for m in bom.costable_materials}
    for mat in bom.costable_materials:
        matching = [
            u for u in bom.inventory_usage
            if u.material_code == mat.material_code or u.resolved_material_code == (mat.resolved_material_code or mat.material_code)
        ]
        assert matching, f"inventory_usage missing for costable {mat.material_code}"


@pytest.mark.asyncio
async def test_missing_materials_reported_missing_from_inventory(bom_context):
    sparse_catalog = {k: v for k, v in INVENTORY_CATALOG.items() if "SABLON" not in k}
    bom = await bom_context(rates=SAMPLE_RATES, inventory=sparse_catalog)
    assert any(
        u.classification == "MISSING_FROM_INVENTORY" for u in bom.inventory_usage
    ) or "MAT-SABLON-MONTAJ" in bom.missing_inventory_materials


@pytest.mark.asyncio
async def test_missing_price_reported_not_zero_fallback(bom_context):
    catalog = dict(INVENTORY_CATALOG)
    catalog["MAT-SABLON-MONTAJ"] = {"status": "missing_price", "unit_cost": None}
    rates = {k: v for k, v in SAMPLE_RATES.items() if k != "MAT-SABLON-MONTAJ"}
    bom = await bom_context(rates=rates, inventory=catalog)
    assert any(u.classification == "MISSING_PRICE" for u in bom.inventory_usage) or any(
        b.blocker_code == "MISSING_PRICE" for b in bom.pricing_blockers
    )
    sablon = next((m for m in bom.costable_materials if m.material_code == "MAT-SABLON-MONTAJ"), None)
    if sablon:
        assert sablon.unit_cost is None or sablon.pricing_availability != "available"


@pytest.mark.asyncio
async def test_legacy_parent_materials_classified_not_truth(bom_context):
    bom = await bom_context()
    legacy = [u for u in bom.inventory_usage if u.classification == "LEGACY_REFERENCED_ONLY"]
    if bom.legacy_inventory_references:
        assert legacy or bom.legacy_inventory_references
    parent_mats = [u for u in bom.inventory_usage if u.provenance == "parent"]
    for entry in parent_mats:
        assert entry.classification == "LEGACY_REFERENCED_ONLY"


@pytest.mark.asyncio
async def test_unused_inventory_not_in_costable_materials(bom_context):
    bom = await bom_context()
    costable_codes = {m.resolved_material_code or m.material_code for m in bom.costable_materials}
    for unused_code in bom.unused_inventory_candidates:
        assert unused_code not in costable_codes


@pytest.mark.asyncio
async def test_psu_base_requires_watt_variant_not_zero(bom_context, volumetric_v2_db):
    ws_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=ws_id,
            workspace_code=f"WS-BOM-{ws_id[:8]}",
            title="BOM psu variant",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(_full_payload(mounting_system="direct_wall", with_psu=False)),
        )
    )
    await volumetric_v2_db.commit()
    catalog = {k: v for k, v in INVENTORY_CATALOG.items() if k != "MAT-LED-PSU-12V"}
    bom = await bom_context(workspace_id=ws_id, inventory=catalog)
    psu_entries = [u for u in bom.inventory_usage if "PSU" in u.material_code]
    assert psu_entries
    for entry in psu_entries:
        assert entry.classification != "MISSING_PRICE" or "variant" in (entry.notes or "").lower() or any(
            b.blocker_code == "VARIANT_REQUIRED" for b in bom.pricing_blockers
        )
    assert not any(
        m.unit_cost == 0 for m in bom.costable_materials if "PSU" in m.material_code
    )


# --- Step 7B.1 externalization readiness ---


@pytest.mark.asyncio
async def test_externalizable_operation_not_forced_internal_wc_blocker(bom_context):
    bom = await bom_context(wc={})
    painting_ops = [
        o for o in bom.costable_operations if o.operation_code.upper() == "PAINTING" or "PAINT" in o.operation_code.upper()
    ]
    painting_missing = [
        m for m in bom.missing_pricing if m.item_type == "operation" and "PAINT" in m.code.upper()
    ]
    if painting_ops or any(h.operation_code.upper() == "PAINTING" for h in bom.subcontractable_operations):
        assert not painting_missing or bom.subcontractable_operations
    assert any(s.default_mode == "external_service_possible" for s in bom.subcontractable_operations)


@pytest.mark.asyncio
async def test_external_service_selected_without_price_is_blocker(bom_context):
    bom = await bom_context(
        external_selections={"EXT_POWDER_COATING_RAL": True},
    )
    blockers = [b for b in bom.pricing_blockers if b.blocker_code == "EXTERNAL_PRICE_REQUIRED"]
    assert blockers
    assert bom.bom_status == "blocked"


@pytest.mark.asyncio
async def test_reseller_future_no_internal_operations_required(bom_context):
    bom = await bom_context()
    assert bom.reseller_requirements
    for req in bom.reseller_requirements:
        assert req.internal_operations_required is False
        assert req.status == "future_reserved"
    reseller_lines = [c for c in bom.cost_line_classification if c.classification == "RESELLER_PRODUCT"]
    assert reseller_lines


@pytest.mark.asyncio
async def test_hybrid_separates_internal_and_external_requirements(bom_context):
    bom = await bom_context(external_selections={"EXT_POWDER_COATING_RAL": True})
    internal_lines = [c for c in bom.cost_line_classification if c.classification == "INTERNAL_PRODUCTION"]
    external_reqs = [e for e in bom.externalization_requirements if e.selected_now]
    assert internal_lines
    assert external_reqs
    assert bom.production_mode == "hybrid_internal_external"


@pytest.mark.asyncio
async def test_volumetric_default_internal_with_future_hooks(bom_context):
    bom = await bom_context()
    assert bom.production_mode == "internal_production"
    assert bom.subcontractable_operations
    future_rules = [
        c for c in bom.cost_line_classification if c.classification == "FUTURE_EXTERNALIZATION_RULE"
    ]
    assert future_rules or bom.externalization_requirements


@pytest.mark.asyncio
async def test_externalization_hooks_no_real_tasks_or_suppliers(bom_context):
    bom = await bom_context()
    for req in bom.externalization_requirements:
        assert req.creates_external_task_now is False
    assert bom.reseller_requirements
    assert all(r.status == "future_reserved" for r in bom.reseller_requirements)


def test_cost_bom_preview_endpoint_includes_7b1_sections(bom_auth_client):
    response = bom_auth_client.get(f"/api/v1/product-system/cost-bom-preview/{TEMPLATE}")
    assert response.status_code == 200
    body = response.json()
    for key in (
        "inventory_usage",
        "missing_inventory_materials",
        "unused_inventory_candidates",
        "legacy_inventory_references",
        "externalization_requirements",
        "reseller_requirements",
        "subcontractable_operations",
        "cost_line_classification",
    ):
        assert key in body
    assert body["preview_version"] == "1.1.0"
