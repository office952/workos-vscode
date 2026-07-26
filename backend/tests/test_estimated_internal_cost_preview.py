"""Tests for read-only EstimatedInternalCost preview (Step 7H)."""

from __future__ import annotations

import ast
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.estimated_internal_cost import EstimatedInternalCostLine
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.estimated_internal_cost_service import (
    EstimatedInternalCostService,
    scan_hourly_contamination,
)
from tests.eic_patched_bom_builder import PatchedAggregateCostBomBuilder
from tests.test_aggregate_cost_bom_adapter import INVENTORY_CATALOG, SAMPLE_RATES

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


@pytest_asyncio.fixture
async def cpp_service(volumetric_v2_db):
    yield CommercialPriceProposalService(volumetric_v2_db)


@pytest_asyncio.fixture
async def eic_service(volumetric_v2_db):
    service = EstimatedInternalCostService(
        volumetric_v2_db,
        bom_builder=PatchedAggregateCostBomBuilder(
            volumetric_v2_db,
            material_rates=SAMPLE_RATES,
            inventory_catalog=INVENTORY_CATALOG,
        ),
    )

    async def _patched_load():
        return SAMPLE_RATES, {"RON": "RON"}, {"WC_CNC_ROUTING": 120.0}, INVENTORY_CATALOG

    service._load_pricing_context = _patched_load  # type: ignore[method-assign]
    yield service


@pytest.fixture
def eic_auth_client(volumetric_auth_client):
    return volumetric_auth_client


def _full_quote_input(*, mounting_system: str = "direct_wall") -> dict:
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "test.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "closed_back",
            "mounting_system": mounting_system,
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "led_module_count": 24,
            "selected_psu_watts": 100,
            "required_psu_watts": 140.4,
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 2.5,
            "mounting_template_material_type": "forex",
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
        },
    }


@pytest.mark.asyncio
async def test_rate_per_hour_not_in_internal_total(eic_service: EstimatedInternalCostService):
    preview = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    blob = preview.model_dump_json().lower()
    assert "rate_per_hour" not in blob or preview.estimated_total_internal_cost is not None
    if preview.estimated_total_internal_cost is not None:
        assert "rate_per_hour" not in str(preview.estimated_total_internal_cost)
    for line in preview.estimated_operation_lines:
        assert line.basis_type not in ("hours",)


@pytest.mark.asyncio
async def test_estimated_minutes_only_in_capacity_hints(eic_service: EstimatedInternalCostService):
    preview = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    assert preview.capacity_hints
    for hint in preview.capacity_hints:
        assert hint.excluded_from_total is True
        assert hint.estimated_minutes is not None
    op_blob = preview.model_dump_json()
    assert "estimated_minutes" not in op_blob or all(
        h.code in op_blob for h in preview.capacity_hints
    )
    for line in preview.estimated_operation_lines + preview.estimated_material_lines:
        assert "estimated_minutes" not in line.source


@pytest.mark.asyncio
async def test_missing_workcenter_hourly_not_in_total_or_commercial_block(
    eic_service: EstimatedInternalCostService,
    cpp_service: CommercialPriceProposalService,
):
    async def _empty_wc():
        return SAMPLE_RATES, {}, {}, INVENTORY_CATALOG

    eic_service._load_pricing_context = _empty_wc  # type: ignore[method-assign]
    internal = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    commercial = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert internal is not None and commercial is not None
    assert "rate_per_hour" not in str(internal.estimated_total_internal_cost or "")
    assert not any("WORKCENTER" in b.code for b in commercial.commercial_blockers)


@pytest.mark.asyncio
async def test_missing_inventory_produces_internal_material_cost_missing(volumetric_v2_db):
    service = EstimatedInternalCostService(
        volumetric_v2_db,
        bom_builder=PatchedAggregateCostBomBuilder(
            volumetric_v2_db,
            material_rates={},
            inventory_catalog={},
        ),
    )

    async def _empty():
        return {}, {}, {}, {}

    service._load_pricing_context = _empty  # type: ignore[method-assign]
    preview = await service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    assert any(b.code == "INTERNAL_MATERIAL_COST_MISSING" for b in preview.internal_blockers)


@pytest.mark.asyncio
async def test_material_costs_separate_from_commercial(
    eic_service: EstimatedInternalCostService,
    cpp_service: CommercialPriceProposalService,
):
    internal = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    commercial = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert internal is not None and commercial is not None
    assert any(l.source == "inventory_materials.unit_cost" for l in internal.estimated_material_lines)
    assert all("inventory_materials" not in l.source for l in commercial.commercial_price_lines)
    if internal.estimated_material_cost and commercial.commercial_total:
        assert internal.estimated_material_cost != commercial.commercial_total


@pytest.mark.asyncio
async def test_debitare_spate_dev_bridge_documents_m2_basis(
    eic_service: EstimatedInternalCostService,
):
    preview = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    back = next(line for line in preview.estimated_operation_lines if line.code == "debitare_spate")
    assert back.basis_type == "m2"
    assert back.internal_unit_cost == 12.0
    assert back.subtotal == pytest.approx(14.4)
    assert not any(b.code == "INTERNAL_OPERATION_BASIS_UNKNOWN" for b in preview.internal_blockers)


@pytest.mark.asyncio
async def test_no_db_writes(eic_service: EstimatedInternalCostService, volumetric_v2_db):
    session = volumetric_v2_db
    add_mock = MagicMock(wraps=session.add)
    commit_mock = AsyncMock(wraps=session.commit)
    session.add = add_mock
    session.commit = commit_mock
    preview = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    add_mock.assert_not_called()
    commit_mock.assert_not_called()


def _forbidden_imports(service_file: str) -> set[str]:
    path = Path(__file__).resolve().parents[1] / "services" / service_file
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
    return modules


def test_service_does_not_import_quote_orchestrator():
    modules = _forbidden_imports("estimated_internal_cost_service.py")
    assert not any("quote_orchestrator" in mod for mod in modules)


def test_service_does_not_import_price_bridge():
    modules = _forbidden_imports("estimated_internal_cost_service.py")
    assert not any("aggregate_cost_bom_price_bridge" in mod for mod in modules)


@pytest.mark.asyncio
async def test_same_payload_produces_independent_7g_and_7h(
    eic_service: EstimatedInternalCostService,
    cpp_service: CommercialPriceProposalService,
):
    payload = _full_quote_input()
    internal = await eic_service.build_preview(TEMPLATE, quote_input=payload)
    commercial = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert internal is not None and commercial is not None
    assert internal.source == "estimated_internal_cost"
    assert commercial.source == "commercial_price_proposal"
    assert internal.template_code == commercial.template_code


@pytest.mark.asyncio
async def test_internal_only_qc_excluded_from_operation_cost(eic_service: EstimatedInternalCostService):
    preview = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    codes = {line.code for line in preview.estimated_operation_lines}
    assert "qc_letters" not in codes
    assert not any("qc_" in code for code in codes)


@pytest.mark.asyncio
async def test_provenance_present(eic_service: EstimatedInternalCostService):
    preview = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    keys = {p.key for p in preview.provenance}
    assert "aggregate_cost_bom" in keys
    assert "internal_rules" in keys
    assert "inventory" in keys


def test_hourly_contamination_blocks():
    lines = [
        EstimatedInternalCostLine(
            code="bad",
            label="Bad",
            line_type="operation",
            basis_type="fixed",
            quantity=1,
            unit="set",
            rule_code="BAD",
            source="rate_per_hour_fallback",
        )
    ]
    assert scan_hourly_contamination(*lines)


@pytest.mark.asyncio
async def test_hourly_contamination_blocks_preview(eic_service: EstimatedInternalCostService, monkeypatch):
    from services import estimated_internal_cost_service as mod

    original = mod.scan_hourly_contamination

    def _force(*lines):
        return original(*lines) + ["debitare_fata:rate_per_hour"]

    monkeypatch.setattr(mod, "scan_hourly_contamination", _force)
    preview = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    assert preview.status == "blocked"
    assert preview.ready_for_quote_snapshot is False
    assert preview.hourly_contamination_detected


@pytest.mark.asyncio
async def test_inventory_unit_cost_is_internal_not_commercial(eic_service: EstimatedInternalCostService):
    preview = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    assert preview.estimated_material_lines
    for line in preview.estimated_material_lines:
        assert line.basis_type == "inventory_unit_cost"
        assert "inventory_materials.unit_cost" in line.source


@pytest.mark.asyncio
async def test_capacity_hints_excluded_from_total(eic_service: EstimatedInternalCostService):
    preview = await eic_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    assert preview.capacity_hints
    minutes_sum = sum(h.estimated_minutes or 0 for h in preview.capacity_hints)
    assert minutes_sum > 0
    for hint in preview.capacity_hints:
        assert hint.excluded_from_total is True
    total_without_time = (preview.estimated_material_cost or 0) + (preview.estimated_operation_cost or 0)
    assert preview.estimated_total_internal_cost == pytest.approx(total_without_time)


def test_post_endpoint_returns_preview(eic_auth_client):
    response = eic_auth_client.post(
        f"/api/v1/product-system/estimated-internal-cost-preview/{TEMPLATE}",
        json={"quote_input": _full_quote_input(), "currency": "RON"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "estimated_internal_cost"
    assert isinstance(body["estimated_material_lines"], list)


@pytest.mark.asyncio
async def test_workspace_id_payload(volumetric_v2_db):
    import json

    service = EstimatedInternalCostService(
        volumetric_v2_db,
        bom_builder=PatchedAggregateCostBomBuilder(
            volumetric_v2_db,
            material_rates=SAMPLE_RATES,
            inventory_catalog=INVENTORY_CATALOG,
        ),
    )

    async def _patched():
        return SAMPLE_RATES, {}, {}, INVENTORY_CATALOG

    service._load_pricing_context = _patched  # type: ignore[method-assign]
    workspace_id = str(uuid.uuid4())
    record = IntakeV6WorkspaceRecord(
        id=workspace_id,
        workspace_code=f"WS-EIC-{workspace_id[:8]}",
        title="EIC test workspace",
        template_code=TEMPLATE,
        payload_json=json.dumps(_full_quote_input()),
        status="draft",
    )
    volumetric_v2_db.add(record)
    await volumetric_v2_db.commit()
    preview = await service.build_preview(TEMPLATE, workspace_id=workspace_id)
    assert preview is not None
    assert preview.input_summary.get("workspace_id") == workspace_id
