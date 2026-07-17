"""Build 1 — golden Intake V6 parity harness (SVG / formula / PD / Aggregate / CPP).

Boundary:
- no formula/price/schema changes
- no subset UI
- historical workspace never mutated
- disposable workspace clone only
"""

from __future__ import annotations

import json
import os
import uuid
from copy import deepcopy
from pathlib import Path

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.intake_v4_quote_geometry_service import build_quote_geometry_from_analysis
from services.intake_v6_golden_parity_harness import (
    CONTRACT_VERSION,
    FIXTURE_DIR,
    HISTORICAL_GOLDEN_WORKSPACE_ID,
    INTERFACE_FACE_CANT,
    TEMPLATE_CODE,
    assert_face_cant_interface_present,
    compare_commercial_fingerprints,
    compare_quote_geometry,
    compare_svg_facts,
    extract_svg_facts,
    fingerprint_commercial_lines,
    geometry_inputs_from_pd,
    load_golden_workspace_payload,
    load_json_fixture,
    material_codes,
    operation_codes,
    review_contract_snapshot,
    selected_module_codes,
)
from services.intake_v6_priced_quote_dry_run_service import build_intake_v6_priced_quote_dry_run
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def _write_expect(name: str, data: object) -> None:
    path = FIXTURE_DIR / name
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@pytest_asyncio.fixture
async def golden_workspace_id(volumetric_v2_db):
    workspace_id = str(uuid.uuid4())
    payload = load_golden_workspace_payload(include_analysis=True)
    # Never collide with historical golden id.
    assert workspace_id != HISTORICAL_GOLDEN_WORKSPACE_ID
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"IV6-GOLD-{workspace_id[:8]}",
            title="Build1 golden parity disposable",
            template_code=TEMPLATE_CODE,
            payload_json=json.dumps(payload),
            status="draft",
        )
    )
    await volumetric_v2_db.commit()
    return workspace_id


def test_golden_fixtures_present():
    required = [
        "golden_contract_v1.json",
        "svg_facts.expect.json",
        "svg_analysis_json.json",
        "layer_role_setup.json",
        "quote_geometry.expect.json",
        "workspace_payload.golden.json",
        "ownership_map.json",
        "pd_fingerprint.expect.json",
        "aggregate_fingerprint.expect.json",
        "review_contract.expect.json",
        "gradi-curat.svg",
    ]
    missing = [name for name in required if not (FIXTURE_DIR / name).exists()]
    assert not missing, f"missing fixtures: {missing}"
    contract = load_json_fixture("golden_contract_v1.json")
    assert contract["identity"]["contract_version"] == CONTRACT_VERSION
    assert contract["identity"]["historical_workspace_id"] == HISTORICAL_GOLDEN_WORKSPACE_ID


def test_svg_file_identity_hash():
    import hashlib

    svg_bytes = (FIXTURE_DIR / "gradi-curat.svg").read_bytes()
    digest = hashlib.sha256(svg_bytes).hexdigest()
    facts = load_json_fixture("svg_facts.expect.json")
    assert len(svg_bytes) == facts["source"]["file_size_bytes"]
    assert digest == facts["source"]["file_hash"]
    assert facts["report"]["acm_declared"] is False


def test_svg_facts_parity_from_analysis_fixture():
    analysis = load_json_fixture("svg_analysis_json.json")
    roles = load_json_fixture("layer_role_setup.json")
    expected = load_json_fixture("svg_facts.expect.json")
    actual = extract_svg_facts(analysis, roles)
    mismatches = compare_svg_facts(actual, expected)
    assert not mismatches, mismatches


def test_formula_quote_geometry_parity():
    analysis = load_json_fixture("svg_analysis_json.json")
    roles = load_json_fixture("layer_role_setup.json")
    expected = load_json_fixture("quote_geometry.expect.json")
    built = build_quote_geometry_from_analysis(analysis, roles)
    mismatches = compare_quote_geometry(built, expected)
    assert not mismatches, mismatches


def test_review_contract_capture():
    payload = load_golden_workspace_payload(include_analysis=False)
    snap = review_contract_snapshot(payload)
    expected = load_json_fixture("review_contract.expect.json")
    assert snap["file_identity"]["file_name"] == expected["file_identity"]["file_name"]
    assert snap["layers_confirmed"] == expected["layers_confirmed"]
    assert snap["layer_count"] == expected["layer_count"]
    assert snap["geometry"] == expected["geometry"]
    assert snap["operator_intent"]["illuminated"] == expected["operator_intent"]["illuminated"]
    assert snap["cpp_boundary"]["intake_is_money_authority"] is False


def test_ownership_map_covers_minimum_elements():
    ownership = load_json_fixture("ownership_map.json")
    names = {row["element"] for row in ownership["elements"]}
    required = {
        "svg_file_identity",
        "layer_ids",
        "colors",
        "width_height_mm",
        "face_area_m2",
        "perimeter_m",
        "letter_count",
        "face_material",
        "cant_material",
        "cant_height",
        "back_material",
        "illumination",
        "led_count",
        "psu",
        "installation_template",
        "mounting",
        "packaging",
        "adhesive",
        "bonding_operation",
        "cpp_line_inputs",
        "readiness_blockers",
        "candidate_ACM",
    }
    missing = sorted(required - names)
    assert not missing
    adhesive = next(row for row in ownership["elements"] if row["element"] == "adhesive")
    assert adhesive["target_owner"] == INTERFACE_FACE_CANT["target_owner"]


def test_interface_face_cant_candidate_documented():
    contract = load_json_fixture("golden_contract_v1.json")
    iface = contract["interface_candidates"][0]
    assert iface["material_code"] == "MAT-ADEZIV-CANT-LITERE"
    assert iface["target_owner"] == "interface:FACE+CANT"
    assert iface["build3"] == "cant_only_isolation"


def test_no_schema_migration_artifacts_in_build1():
    # Guard: Build 1 must not introduce alembic revisions as part of this harness.
    # Presence of pre-existing alembic/ is fine; this test only asserts harness boundary docs.
    contract = load_json_fixture("golden_contract_v1.json")
    assert "schema_change" in contract["forbidden_in_build1"]
    assert "migration" in contract["forbidden_in_build1"]


@pytest.mark.asyncio
async def test_product_definition_geometry_and_modules_parity(volumetric_v2_db, golden_workspace_id):
    expected = load_json_fixture("pd_fingerprint.expect.json")
    pd = await ProductDefinitionBuilderService(volumetric_v2_db).build_preview(
        TEMPLATE_CODE, workspace_id=golden_workspace_id
    )
    assert pd is not None
    codes = selected_module_codes(pd)
    assert codes == expected["selected_module_codes"], codes
    geom = geometry_inputs_from_pd(pd)
    for key, value in expected["geometry_inputs"].items():
        assert geom.get(key) == value, f"{key}: {geom.get(key)!r} != {value!r}"


@pytest.mark.asyncio
async def test_product_aggregate_fixture_db_baseline_parity(volumetric_v2_db, golden_workspace_id):
    """CI seed Aggregate is thinner than live dossier — freeze seed-visible anchors only."""
    expected = load_json_fixture("aggregate_fingerprint.expect.json")["fixture_db_baseline"]
    aggregate = await ProductAggregateService(volumetric_v2_db).build_for_workspace(
        TEMPLATE_CODE, golden_workspace_id
    )
    assert aggregate is not None
    mats = material_codes(aggregate)
    ops = operation_codes(aggregate)
    for code in expected["required_material_codes"]:
        assert code in mats, f"missing material {code}; have={sorted(mats)}"
    for group in expected["required_operation_codes_any_of"]:
        assert any(code in ops for code in group), f"missing ops any_of={group}; have={sorted(ops)}"
    iface = load_json_fixture("aggregate_fingerprint.expect.json")["interface_face_cant"]
    assert iface["fixture_db_emits_adhesive"] is False
    assert "MAT-ADEZIV-CANT-LITERE" not in mats


@pytest.mark.asyncio
async def test_product_aggregate_live_runtime_interface_parity():
    """Read-only live Aggregate against historical golden WS (adhesive + bonding)."""
    import urllib.error
    import urllib.request

    expected = load_json_fixture("aggregate_fingerprint.expect.json")["live_runtime_baseline"]
    live = load_json_fixture("aggregate_live.fingerprint.json")
    url = (
        "http://127.0.0.1:8001/api/v1/product-system/aggregate/"
        f"{TEMPLATE_CODE}?workspace_id={HISTORICAL_GOLDEN_WORKSPACE_ID}"
    )
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            agg = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        pytest.skip(f"live backend unavailable for Aggregate parity: {exc}")

    mats = material_codes(agg)
    ops = operation_codes(agg)
    for code in expected["required_material_codes"]:
        assert code in mats, f"missing live material {code}; have={sorted(mats)}"
    for group in expected["required_operation_codes_any_of"]:
        assert any(code in ops for code in group), f"missing live ops any_of={group}; have={sorted(ops)}"
    issues = assert_face_cant_interface_present(agg)
    assert not issues, issues
    # Frozen fingerprint file must stay aligned with live (detect silent drift).
    assert live["has_adhesive"] is True
    assert live["has_bonding"] is True
    assert set(live["material_codes"]) == mats
    assert set(live["operation_codes"]) == ops


@pytest.mark.asyncio
async def test_cpp_exact_parity_and_dry_run_boundary(volumetric_v2_db, golden_workspace_id):
    """Exact commercial fingerprint for disposable fixture payload; capture via GOLDEN_CAPTURE=1."""
    preview = await CommercialPriceProposalService(volumetric_v2_db).build_preview(
        TEMPLATE_CODE, workspace_id=golden_workspace_id, currency="RON"
    )
    assert preview is not None
    fingerprint = fingerprint_commercial_lines(preview.commercial_price_lines)
    expect_path = FIXTURE_DIR / "cpp_fingerprint.expect.json"
    if os.environ.get("GOLDEN_CAPTURE") == "1" or not expect_path.exists():
        payload = {
            "contract_version": "intake_v6_golden_cpp_v1",
            "template_code": TEMPLATE_CODE,
            "currency": "RON",
            "lines": fingerprint,
            "totals": {"subtotal_net": None},
            "notes": [
                "Disposable fixture payload against volumetric_v2_db + commercial_rules_volumetric_v2.",
                "Seed DB may omit some live commercial lines (LED/PSU); live historical fingerprint is authoritative for full line set.",
                "Intake is not money authority; dry-run must remain no-write.",
            ],
        }
        dumped = preview.model_dump() if hasattr(preview, "model_dump") else {}
        totals = dumped.get("totals") or dumped.get("commercial_totals") or {}
        if totals:
            payload["totals"] = {
                "subtotal_net": totals.get("subtotal_net"),
                "vat_rate": totals.get("vat_rate"),
                "vat_amount": totals.get("vat_amount"),
                "total_gross": totals.get("total_gross"),
                "currency": totals.get("currency") or "RON",
            }
        _write_expect("cpp_fingerprint.expect.json", payload)

    expected = load_json_fixture("cpp_fingerprint.expect.json")
    mismatches = compare_commercial_fingerprints(fingerprint, expected["lines"])
    assert not mismatches, mismatches

    qg = load_json_fixture("quote_geometry.expect.json")
    face_line = next(row for row in fingerprint if row["code"] == "debitare_fata")
    assert abs(float(face_line["quantity"]) - float(qg["letter_perimeter_m"])) < 1e-4

    dry = await build_intake_v6_priced_quote_dry_run(volumetric_v2_db, golden_workspace_id)
    assert dry.get("dry_run_only") is True
    assert dry.get("can_write_quote_totals") is False


@pytest.mark.asyncio
async def test_cpp_live_historical_exact_parity_readonly():
    """Read-only exact CPP dry-run against historical golden workspace."""
    import urllib.error
    import urllib.request

    expected = load_json_fixture("cpp_live_historical.fingerprint.json")
    url = (
        "http://127.0.0.1:8001/api/v1/intake-v6/workspaces/"
        f"{HISTORICAL_GOLDEN_WORKSPACE_ID}/priced-quote-dry-run"
    )
    try:
        with urllib.request.urlopen(url, timeout=90) as resp:
            dry = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        pytest.skip(f"live backend unavailable for CPP parity: {exc}")

    assert dry.get("dry_run_only") is True
    assert dry.get("can_write_quote_totals") is False
    fingerprint = fingerprint_commercial_lines(dry.get("commercial_line_items") or [])
    mismatches = compare_commercial_fingerprints(fingerprint, expected["lines"])
    assert not mismatches, mismatches
    # Geometry chain on historical WS (drift vs fixture rebuild is intentional guard).
    face = next(row for row in fingerprint if row["code"] == "debitare_fata")
    assert abs(float(face["quantity"]) - 20.9727) < 1e-4


@pytest.mark.asyncio
async def test_persistence_reload_parity_roundtrip(volumetric_v2_db, golden_workspace_id):
    row = await volumetric_v2_db.get(IntakeV6WorkspaceRecord, golden_workspace_id)
    assert row is not None
    payload = json.loads(row.payload_json)
    assert payload["svg_source"]["file_name"] == "gradi-curat.svg"
    assert payload["layer_role_setup"]["confirmation_status"] == "complete"
    assert abs(float(payload["quote_geometry"]["letter_perimeter_m"]) - 21.1675) < 1e-4

    # Simulate reload: re-read and re-derive geometry; must match.
    rebuilt = build_quote_geometry_from_analysis(
        payload["svg_analysis_json"], payload["layer_role_setup"]
    )
    mismatches = compare_quote_geometry(rebuilt, payload["quote_geometry"])
    assert not mismatches, mismatches


@pytest.mark.asyncio
async def test_historical_workspace_id_not_used_for_writes(golden_workspace_id):
    assert golden_workspace_id != HISTORICAL_GOLDEN_WORKSPACE_ID


@pytest.mark.asyncio
async def test_legacy_active_scope_empty_keeps_fixture_db_anchors(volumetric_v2_db, golden_workspace_id):
    """active=[] + legacy must not strip fixture-visible full-product anchors."""
    row = await volumetric_v2_db.get(IntakeV6WorkspaceRecord, golden_workspace_id)
    payload = json.loads(row.payload_json)
    mutated = deepcopy(payload)
    offer = mutated.get("offer_scope") if isinstance(mutated.get("offer_scope"), dict) else {}
    offer = dict(offer)
    offer["component_subset"] = []
    offer["legacy"] = True
    mutated["offer_scope"] = offer
    row.payload_json = json.dumps(mutated)
    await volumetric_v2_db.commit()

    aggregate = await ProductAggregateService(volumetric_v2_db).build_for_workspace(
        TEMPLATE_CODE, golden_workspace_id
    )
    mats = material_codes(aggregate)
    ops = operation_codes(aggregate)
    assert "MAT-PROFIL-LATERAL-LITERE-60MM" in mats
    assert "RETURN_PROFILE_MACHINE_FORMING" in ops or "svg_geometry_analysis" in ops


def test_historical_vs_fixture_geometry_drift_guard():
    """Document live historical perimeter drift vs analysis-fixture rebuild (no mutation)."""
    qg = load_json_fixture("quote_geometry.expect.json")
    live_cpp = load_json_fixture("cpp_live_historical.fingerprint.json")
    face = next(row for row in live_cpp["lines"] if row.get("code") == "debitare_fata")
    fixture_perimeter = float(qg["letter_perimeter_m"])
    live_perimeter = float(face["quantity"])
    assert fixture_perimeter == 21.1675
    assert live_perimeter == 20.9727
    assert abs(fixture_perimeter - live_perimeter) > 1e-4


# Spec-only marker for Build 3 — must not fail Build 1.
@pytest.mark.skip(reason="Build 3 cant-only isolation — not in Build 1 scope")
def test_spec_build3_cant_only_silences_adhesive():
    assert False, "implement in Build 3"


def test_build3_cant_only_spec_documented():
    """Pending Build 3 requirement captured without failing the suite."""
    iface = INTERFACE_FACE_CANT
    assert iface["build3_isolation"]
    assert Path(FIXTURE_DIR / "golden_contract_v1.json").exists()
