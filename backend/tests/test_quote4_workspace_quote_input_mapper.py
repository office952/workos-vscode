"""Tests for Step 7E.1 workspace → quote_input mapping (no live DB)."""

from __future__ import annotations

import os
import sys

import pytest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.quote4_workspace_quote_input_mapper import (  # noqa: E402
    audit_wc_assembly_rate,
    build_product_spec_proposal,
    map_workspace_to_quote_input,
)


SAMPLE_WORKSPACE = {
    "client": {"client_name": "Test Client", "width_mm": None, "height_mm": None},
    "quote_geometry": {
        "width_mm": 1200.0,
        "height_mm": 400.0,
        "letter_count": 19,
        "letter_perimeter_m": 20.97,
        "face_area_m2": 1.2638,
    },
    "finish_setup": {
        "illuminated": True,
        "lighting_system_type": "led_modules",
        "led_module_count": 144,
        "selected_psu_watts": 100,
        "required_psu_watts": 140.4,
        "psu_allocation_status": "ok",
        "mounting_system": "direct_wall",
        "mounting_template_enabled": True,
        "return_depth_mm": 60.0,
        "face_finish_type": "oracal_651",
        "volum_aluminum_module_template_code": None,
        "letter_group_finishes": [
            {
                "group_key": "pseudo:a",
                "face_area_m2": 0.5,
                "confirmed": False,
                "face_finish_type": "oracal_651",
                "return_finish_type": "white_aluminum",
                "return_depth_mm": 60.0,
            },
            {
                "group_key": "pseudo:b",
                "face_area_m2": 0.7638,
                "confirmed": True,
                "face_finish_type": "oracal_651",
                "return_finish_type": "white_aluminum",
                "return_depth_mm": 60.0,
            },
        ],
    },
    "svg_source": {"file_name": "test.svg", "upload_status": "analyzed"},
}


def test_face_area_m2_alias_to_letter_face_area_m2():
    result = map_workspace_to_quote_input(SAMPLE_WORKSPACE, quantity=19)
    assert result.quote_input["letter_face_area_m2"] == pytest.approx(1.2638)
    assert any(a["field"] == "letter_face_area_m2" for a in result.aliases_applied)


def test_width_height_from_quote_geometry_not_client():
    result = map_workspace_to_quote_input(SAMPLE_WORKSPACE)
    assert result.quote_input["width_mm"] == 1200.0
    assert result.quote_input["height_mm"] == 400.0
    sources = {p.key: p.source_path for p in result.field_provenance}
    assert sources["width_mm"].startswith("quote_geometry")


def test_psu_watts_required_fields_present():
    result = map_workspace_to_quote_input(SAMPLE_WORKSPACE)
    assert result.quote_input["selected_psu_watts"] == 100
    assert result.quote_input["required_psu_watts"] == pytest.approx(140.4)
    assert result.quote_input["psu_allocation_status"] == "ok"


def test_direct_wall_structura_suport_note():
    result = map_workspace_to_quote_input(SAMPLE_WORKSPACE)
    assert result.quote_input["mounting_system"] == "direct_wall"
    notes = [p for p in result.field_provenance if p.key == "structura_suport"]
    assert notes and "inactive" in str(notes[0].value)


def test_volum_aluminum_derived_from_module_link_not_invented():
    result = map_workspace_to_quote_input(
        SAMPLE_WORKSPACE,
        module_link_codes=["TPL-VOLUM-ALUMINIU_v1", "TPL-METAL-PREMOUNT-STRUCTURE_v1"],
    )
    assert result.quote_input["volum_aluminum_module_template_code"] == "TPL-VOLUM-ALUMINIU_v1"
    assert any(p.key == "volum_aluminum_module_template_code" and p.status == "derived" for p in result.field_provenance)


def test_missing_finish_confirmations_remains_blocker():
    result = map_workspace_to_quote_input(
        SAMPLE_WORKSPACE,
        module_link_codes=["TPL-VOLUM-ALUMINIU_v1"],
    )
    assert "finish_groups_partially_unconfirmed" in result.blockers
    assert result.finish_groups_summary["confirmed"] == 1
    assert result.finish_groups_summary["unconfirmed"] == 1


def test_all_unconfirmed_finish_groups_blocker():
    ws = dict(SAMPLE_WORKSPACE)
    ws = {**ws, "finish_setup": {**ws["finish_setup"], "letter_group_finishes": [
        {**g, "confirmed": False} for g in ws["finish_setup"]["letter_group_finishes"]
    ]}}
    result = map_workspace_to_quote_input(ws, module_link_codes=["TPL-VOLUM-ALUMINIU_v1"])
    assert "finish_groups_unconfirmed" in result.blockers


def test_no_invented_fields_when_geometry_missing():
    empty = {"finish_setup": {}, "quote_geometry": {}, "svg_source": {}}
    result = map_workspace_to_quote_input(empty)
    assert "width_mm" in result.missing_fields
    assert "letter_face_area_m2" in result.missing_fields
    assert result.quote_input.get("width_mm") is None


def test_product_spec_only_includes_confirmed_groups_by_default():
    spec = build_product_spec_proposal(SAMPLE_WORKSPACE, include_unconfirmed_groups=False)
    assert len(spec["letterGroupFinishAssignments"]) == 1
    assert spec["letterGroupFinishAssignments"][0]["groupId"] == "pseudo:b"
    assert spec["letterGroupFinishAssignments"][0]["confirmedByOperator"] is True


def test_wc_assembly_audit_missing_row():
    audit = audit_wc_assembly_rate([{"code": "CNC_ROUTER", "rate_per_hour": None, "status": "active"}])
    assert audit["wc_assembly_exists"] is False
    assert audit["proposed_fix"]["action"] == "add_workcenter_rate_row"
    assert audit["do_not_apply"] is True
