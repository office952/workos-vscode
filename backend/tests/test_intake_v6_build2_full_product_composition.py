"""Build 2 — full-product composition from modular form contracts (no subset activation)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.intake_v6_golden_parity_harness import (
    HISTORICAL_GOLDEN_WORKSPACE_ID,
    TEMPLATE_CODE,
    assert_face_cant_interface_present,
    compare_commercial_fingerprints,
    compare_quote_geometry,
    fingerprint_commercial_lines,
    geometry_inputs_from_pd,
    load_golden_workspace_payload,
    load_json_fixture,
    material_codes,
    selected_module_codes,
)
from services.intake_v6_modular_form_contract_service import IntakeV6ModularFormContractService
from services.intake_v4_quote_geometry_service import build_quote_geometry_from_analysis
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


@pytest.fixture
def form_service() -> IntakeV6ModularFormContractService:
    return IntakeV6ModularFormContractService()


def test_build2_full_product_composition_authority(form_service: IntakeV6ModularFormContractService):
    contract = form_service.get_for_template(TEMPLATE_CODE)
    assert contract is not None
    assert contract.summary.composition_authority is True
    assert contract.full_product_composition is not None
    assert contract.full_product_composition.mode == "full_product_only"
    assert contract.full_product_composition.subset_activation_enabled is False
    assert contract.full_product_composition.ui_tab_ids == ["finisaje", "iluminare", "montaj"]
    assert "FACE" in contract.full_product_composition.component_owners
    assert "CANT" in contract.full_product_composition.component_owners
    iface = contract.full_product_composition.interface_candidates[0]
    assert iface["material_code"] == "MAT-ADEZIV-CANT-LITERE"
    assert iface["target_owner"] == "interface:FACE+CANT"
    assert iface["build2_behavior"] == "full_product_output_unchanged"


def test_build2_tab_driving_sections_preserve_golden_order(
    form_service: IntakeV6ModularFormContractService,
):
    contract = form_service.get_for_template(TEMPLATE_CODE)
    assert contract is not None
    driving = sorted(
        [s for s in contract.render_sections if s.drives_review_tab],
        key=lambda s: s.order,
    )
    assert [s.ui_tab_id for s in driving] == ["finisaje", "iluminare", "montaj"]
    assert driving[0].renderer == "specialized_letter_groups"
    assert driving[1].renderer == "specialized_lighting"
    assert "INSTALLATION_TEMPLATE" in (driving[2].component_owners or [])


def test_build2_writable_paths_unchanged_vs_build1(form_service: IntakeV6ModularFormContractService):
    """Generic write allowlist must not expand into sold FINISH/MOUNTING or subset paths."""
    contract = form_service.get_for_template(TEMPLATE_CODE)
    assert contract is not None
    paths = set(contract.writable_workspace_paths)
    assert "finish_setup.face_finish_type" in paths
    assert "finish_setup.mounting_template_enabled" in paths
    assert "finish_setup.mounting_system" not in paths
    assert not any("offer_scope" in p for p in paths)


def test_build2_formula_geometry_still_matches_build1_fixture():
    analysis = load_json_fixture("svg_analysis_json.json")
    roles = load_json_fixture("layer_role_setup.json")
    expected = load_json_fixture("quote_geometry.expect.json")
    built = build_quote_geometry_from_analysis(analysis, roles)
    mismatches = compare_quote_geometry(built, expected)
    assert not mismatches, mismatches
    assert float(built["letter_perimeter_m"]) == 21.1675


def test_build2_historical_perimeter_drift_guard_preserved():
    qg = load_json_fixture("quote_geometry.expect.json")
    live_cpp = load_json_fixture("cpp_live_historical.fingerprint.json")
    face = next(row for row in live_cpp["lines"] if row.get("code") == "debitare_fata")
    assert float(qg["letter_perimeter_m"]) == 21.1675
    assert float(face["quantity"]) == 20.9727


@pytest_asyncio.fixture
async def golden_workspace_id(volumetric_v2_db):
    workspace_id = str(uuid.uuid4())
    payload = load_golden_workspace_payload(include_analysis=True)
    assert workspace_id != HISTORICAL_GOLDEN_WORKSPACE_ID
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"IV6-B2-{workspace_id[:8]}",
            title="Build2 full-product composition disposable",
            template_code=TEMPLATE_CODE,
            payload_json=json.dumps(payload),
            status="draft",
        )
    )
    await volumetric_v2_db.commit()
    return workspace_id


@pytest.mark.asyncio
async def test_build2_pd_parity_matches_build1_fingerprint(volumetric_v2_db, golden_workspace_id):
    expected = load_json_fixture("pd_fingerprint.expect.json")
    pd = await ProductDefinitionBuilderService(volumetric_v2_db).build_preview(
        TEMPLATE_CODE, workspace_id=golden_workspace_id
    )
    assert selected_module_codes(pd) == expected["selected_module_codes"]
    geom = geometry_inputs_from_pd(pd)
    for key, value in expected["geometry_inputs"].items():
        assert geom.get(key) == value


@pytest.mark.asyncio
async def test_build2_cpp_disposable_parity_unchanged(volumetric_v2_db, golden_workspace_id):
    preview = await CommercialPriceProposalService(volumetric_v2_db).build_preview(
        TEMPLATE_CODE, workspace_id=golden_workspace_id, currency="RON"
    )
    fingerprint = fingerprint_commercial_lines(preview.commercial_price_lines)
    expected = load_json_fixture("cpp_fingerprint.expect.json")
    mismatches = compare_commercial_fingerprints(fingerprint, expected["lines"])
    assert not mismatches, mismatches


@pytest.mark.asyncio
async def test_build2_aggregate_live_adhesive_still_present():
    url = (
        "http://127.0.0.1:8001/api/v1/product-system/aggregate/"
        f"{TEMPLATE_CODE}?workspace_id={HISTORICAL_GOLDEN_WORKSPACE_ID}"
    )
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            agg = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        pytest.skip(f"live backend unavailable: {exc}")
    issues = assert_face_cant_interface_present(agg)
    assert not issues, issues
    assert "MAT-ADEZIV-CANT-LITERE" in material_codes(agg)


@pytest.mark.asyncio
async def test_build2_cpp_live_historical_fingerprint_authority():
    expected = load_json_fixture("cpp_live_historical.fingerprint.json")
    url = (
        "http://127.0.0.1:8001/api/v1/intake-v6/workspaces/"
        f"{HISTORICAL_GOLDEN_WORKSPACE_ID}/priced-quote-dry-run"
    )
    try:
        with urllib.request.urlopen(url, timeout=90) as resp:
            dry = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        pytest.skip(f"live backend unavailable: {exc}")
    fingerprint = fingerprint_commercial_lines(dry.get("commercial_line_items") or [])
    mismatches = compare_commercial_fingerprints(fingerprint, expected["lines"])
    assert not mismatches, mismatches
    assert dry.get("dry_run_only") is True
    assert dry.get("can_write_quote_totals") is False
