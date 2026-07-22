"""PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1 — contract tests (no parser, no price invent)."""

from __future__ import annotations

from schemas.workflow_adv_analyzer_io_contract_v1 import (
    ANALYZER_IO_CONTRACT_VERSION,
    build_analyzer_io_contract_document,
)
from services.intake_v6_modular_form_contract_service import VOLUMETRIC_FIELD_BINDINGS
from services.product_system_reference_finish_line_service import build_form_field_ownership_map
from data.product_system_reference_finish_line_v1 import (
    FINISH_LINE_NAME,
    MODULARITY_MODEL,
    PRODUCTION_COST_BOUNDARY,
)


def test_form_field_ownership_map_covers_all_vl_bindings():
    m = build_form_field_ownership_map()
    assert m.pilot_template.endswith("VOLUMETRIC-LETTERS_v2") or "VOLUMETRIC" in m.pilot_template
    assert len(m.fields) == len(VOLUMETRIC_FIELD_BINDINGS)
    ids = {f.field_id for f in m.fields}
    assert "letter_perimeter_m" in ids
    assert "return_depth_mm" in ids
    peri = next(f for f in m.fields if f.field_id == "letter_perimeter_m")
    assert peri.source == "ANALYZER_OBSERVED"
    assert "quantity_compiler" in peri.destinations
    assert "TPL-VOLUM-ALUMINIU_v1" in peri.child_template_codes
    assert m.form_system_verdict == "USABLE_WITH_TEMPLATE_GAPS"
    assert "width_mm" in m.reusable_field_ids


def test_analyzer_io_contract_boundary_no_price_authority():
    doc = build_analyzer_io_contract_document()
    assert doc.contract_version == ANALYZER_IO_CONTRACT_VERSION
    assert "parse_svg_in_workos" in doc.do_not
    assert "write_product_truth_from_analyzer" in doc.do_not
    assert "calculate_price_in_analyzer" in doc.do_not
    field_ids = {f.field_id for f in doc.fields}
    for required in (
        "width_mm",
        "height_mm",
        "filled_area_m2",
        "total_perimeter_m",
        "element_count",
        "suggested_groups",
    ):
        assert required in field_ids
    assert doc.example_payload is not None
    assert doc.example_payload.total_perimeter_m == 6.4
    groups = next(f for f in doc.fields if f.field_id == "suggested_groups")
    assert groups.confirmation_required is True
    assert groups.source == "proposed"


def test_finish_line_production_cost_boundary_excludes_offer():
    assert PRODUCTION_COST_BOUNDARY["completion_authority"] == "EIC_production_cost"
    excluded = set(PRODUCTION_COST_BOUNDARY["excluded"])
    for x in ("markup", "offer", "order", "execution_materialization", "supplier_import"):
        assert x in excluded
    assert MODULARITY_MODEL["authoring_decision"] == "OPTION_2_DOCUMENTED_LAB_LIMITATION"
    assert FINISH_LINE_NAME == "PRODUCT_SYSTEM_REFERENCE_COMPLETE"


def test_visibility_and_child_mapping_declared():
    m = build_form_field_ownership_map()
    bevel = next(f for f in m.fields if f.field_id == "back_bevel_enabled")
    assert bevel.visibility_rule
    alum = next(f for f in m.fields if f.field_id == "return_depth_mm")
    assert "child_template_input" in alum.destinations


def test_finish_line_http_contract_authenticated(auth_client):
    r = auth_client.get("/api/v1/product-system/reference-finish-line/contract")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["finish_line_name"] == "PRODUCT_SYSTEM_REFERENCE_COMPLETE"
    assert body["modularity_verdict"] == "MODULAR_WITH_GAPS"
    assert body["form_system_verdict"] == "USABLE_WITH_TEMPLATE_GAPS"
    assert body["scalability_verdict"] == "SCALABLE_WITH_KNOWN_LIMITS"
    assert body["authoring_decision"] == "OPTION_2_DOCUMENTED_LAB_LIMITATION"
    assert "markup" in body["production_cost_boundary"]["excluded"]
    assert body["form_field_map_summary"]["field_count"] >= 20
    assert body["analyzer_contract"]["contract_version"].startswith("workflow_adv_analyzer")

    m = auth_client.get("/api/v1/product-system/reference-finish-line/form-field-ownership-map")
    assert m.status_code == 200
    assert len(m.json()["fields"]) == body["form_field_map_summary"]["field_count"]

    a = auth_client.get("/api/v1/product-system/reference-finish-line/analyzer-io-contract")
    assert a.status_code == 200
    assert "parse_svg_in_workos" in a.json()["do_not"]

    c = auth_client.get("/api/v1/product-system/reference-finish-line/critical-materials")
    assert c.status_code == 200
    crit = c.json()
    assert "ACTIVE_TEMPLATE_CRITICAL" in crit["policy"]
    assert "VARIANT_SELECTOR" in crit["policy"]
    psu = next(i for i in crit["items"] if i["material_code"] == "MAT-LED-PSU-12V")
    assert psu["classification"] == "VARIANT_SELECTOR"
    assert psu["missing_price"] is False
    assert "MAT-LED-PSU-12V" not in crit["active_template_critical_codes"]
