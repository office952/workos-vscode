"""AcmPanel live DXF attachment + fingerprint + binding tests."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from services.acm_aci_semantic_mapping import ACM_ACI_SEMANTIC_MAPPING_VERSION
from services.acm_production_geometry_attachment import (
    ELIGIBLE_GEOMETRY_ROLES,
    compute_config_fingerprint,
    measure_and_guard_dxf,
    resolve_metrics_from_attachments,
    sanitize_dxf_filename,
    validate_dxf_bytes,
)
from services.acm_production_geometry_metrics import (
    apply_production_metrics_to_commercial_payload,
    resolve_production_geometry_metrics,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "acm_panel_dxf"
SINGLE = FIXTURES / "un-pliu.dxf"
DOUBLE = FIXTURES / "2-pliuri-100x30.dxf"


def _instance(*, fold_count=1, l1=100.0, l2=0.0, panels=None, production_geometry=None):
    panels = panels or [
        {"panel_id": "p1", "width_mm": 2000, "height_mm": 300, "position": {"x_mm": 0, "y_mm": 0}}
    ]
    inst = {
        "schema": "acm_panel_component_instance_v1",
        "component_instance_id": "acm_test_1",
        "configuration": {
            "fold_count": fold_count,
            "l1_mm": l1,
            "l2_mm": l2,
            "finished_depth_mm": l1,
            "service_corner": None,
        },
        "geometry": {
            "geometry_hash": "gh1",
            "width_mm": panels[0]["width_mm"],
            "height_mm": panels[0]["height_mm"],
            "panels": panels,
            "joints": [],
        },
    }
    if production_geometry is not None:
        inst["production_geometry"] = production_geometry
    return inst


def _payload(inst, *, assembly_w=2000, assembly_h=300):
    return {
        "finish_setup": {
            "acm_panel_instance": inst,
            "segmented_background": {
                "assembly_dimensions": {"width_mm": assembly_w, "height_mm": assembly_h},
                "panels": inst["geometry"]["panels"],
            },
            "mounting_solution": {
                "configuration": {"fold_sides": "all", "return_depth_mm": 60},
            },
        },
        "fold_sides": "all",
    }


def test_sanitize_rejects_non_dxf_and_traversal():
    with pytest.raises(ValueError):
        sanitize_dxf_filename("evil.svg")
    with pytest.raises(ValueError):
        sanitize_dxf_filename("../x.dxf")
    assert sanitize_dxf_filename("ok-file.dxf") == "ok-file.dxf"


def test_validate_rejects_empty_zip_oversized():
    assert validate_dxf_bytes(b"", filename="a.dxf")["outcome"] == "rejected"
    assert validate_dxf_bytes(b"PK\x03\x04", filename="a.dxf")["code"] == "archive_not_allowed"
    assert validate_dxf_bytes(b"not-dxf", filename="a.dxf")["outcome"] == "rejected"
    raw = SINGLE.read_bytes()
    assert validate_dxf_bytes(raw, filename="un-pliu.dxf")["outcome"] == "accepted"


def test_golden_single_and_double_via_guard():
    s = measure_and_guard_dxf(SINGLE)
    assert s["measurement_status"] in {"measured", "measured_with_warnings"}
    assert abs(s["cut_length_ml"] - 5.4) < 1e-4
    assert abs(s["v_groove_total_ml"] - 5.4) < 1e-4
    d = measure_and_guard_dxf(DOUBLE)
    assert abs(d["cut_length_ml"] - 5.499412) < 1e-4
    assert abs(d["v_groove_l2_ml"] - 4.600004) < 1e-4
    assert abs(d["v_groove_total_ml"] - 10.000004) < 1e-4


def test_fingerprint_changes_with_l1_and_dims():
    inst = _instance(l1=100)
    p = _payload(inst)
    fp1 = compute_config_fingerprint(payload=p, acm_instance=inst)
    inst2 = _instance(l1=80)
    fp2 = compute_config_fingerprint(payload=_payload(inst2), acm_instance=inst2)
    assert fp1 != fp2
    inst3 = _instance(
        panels=[{"panel_id": "p1", "width_mm": 2100, "height_mm": 300, "position": {"x_mm": 0, "y_mm": 0}}]
    )
    fp3 = compute_config_fingerprint(payload=_payload(inst3, assembly_w=2100), acm_instance=inst3)
    assert fp1 != fp3


def test_resolve_consumes_bound_attachment_snapshot():
    measured = measure_and_guard_dxf(DOUBLE)
    snap = {
        "schema": "acm_panel_production_geometry_metrics_v1",
        "panel_id": "p1",
        "construction_type": "double_fold",
        "active_width_mm": 2000,
        "active_height_mm": 300,
        "l1_mm": 100,
        "l2_mm": 30,
        "active_face_area_m2": 0.6,
        "blank_area_m2": None,
        "cut_length_ml": measured["cut_length_ml"],
        "v_groove_l1_ml": measured["v_groove_l1_ml"],
        "v_groove_l2_ml": measured["v_groove_l2_ml"],
        "v_groove_total_ml": measured["v_groove_total_ml"],
        "measurement_source": "imported_dxf",
        "measurement_status": "measured",
        "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
        "warnings": [],
    }
    inst = _instance(fold_count=2, l1=100, l2=30)
    fp = compute_config_fingerprint(payload=_payload(inst), acm_instance=inst)
    inst["production_geometry"] = {
        "schema": "acm_panel_production_geometry_bundle_v1",
        "attachments": [
            {
                "schema": "acm_panel_production_geometry_attachment_v1",
                "attachment_id": "att1",
                "workspace_id": "ws1",
                "component_instance_id": "acm_test_1",
                "panel_id": "p1",
                "geometry_role": "production_geometry",
                "measurement_status": "measured",
                "config_fingerprint": fp,
                "checksum": "abc",
                "storage_reference": "x.dxf",
                "metrics_snapshot": snap,
                "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
                "warnings": [],
            }
        ],
    }
    metrics = resolve_production_geometry_metrics(_payload(inst))
    assert metrics["measurement_status"] == "measured"
    assert abs(metrics["total_v_groove_ml"] - 10.000004) < 1e-4


def test_stale_fingerprint_rejects_measured_quantities_double_fold():
    snap = {
        "schema": "acm_panel_production_geometry_metrics_v1",
        "panel_id": "p1",
        "cut_length_ml": 5.4,
        "v_groove_l1_ml": 5.4,
        "v_groove_l2_ml": 4.6,
        "v_groove_total_ml": 10.0,
        "measurement_status": "measured",
        "measurement_source": "imported_dxf",
        "warnings": [],
    }
    inst = _instance(fold_count=2, l1=100, l2=30)
    inst["production_geometry"] = {
        "schema": "acm_panel_production_geometry_bundle_v1",
        "attachments": [
            {
                "attachment_id": "att1",
                "workspace_id": "ws1",
                "component_instance_id": "acm_test_1",
                "panel_id": "p1",
                "geometry_role": "production_geometry",
                "measurement_status": "measured",
                "config_fingerprint": "outdated",
                "metrics_snapshot": snap,
                "warnings": [],
            }
        ],
    }
    payload = _payload(inst)
    metrics = resolve_production_geometry_metrics(payload)
    # Stale measured rejected; commercial deduction fills offer-time CUT/V.
    assert metrics["measurement_status"] in {
        "commercial_deduced",
        "commercial_deduced_with_assumptions",
    }
    assert metrics["total_cut_length_ml"] == pytest.approx(5.64)
    assert metrics["total_v_groove_ml"] == pytest.approx(10.0)
    assert "production_geometry_stale" in (metrics.get("warnings") or [])
    m = dict(payload)
    apply_production_metrics_to_commercial_payload(m, commercial_face_area_m2=0.6, return_depth_mm=60)
    assert m.get("panel_perimeter_m") == pytest.approx(5.64)
    assert m.get("fold_length_m") == pytest.approx(10.0)
    assert m.get("acm_path_quantity_status") in {
        "commercial_deduced",
        "commercial_deduced_with_assumptions",
    }


def test_reference_role_not_eligible():
    assert "reference_only" not in ELIGIBLE_GEOMETRY_ROLES
    assert "production_geometry" in ELIGIBLE_GEOMETRY_ROLES


def test_multi_panel_missing_attachment_marks_unavailable():
    panels = [
        {"panel_id": "p1", "width_mm": 1000, "height_mm": 350, "position": {"x_mm": 0, "y_mm": 0}},
        {"panel_id": "p2", "width_mm": 1000, "height_mm": 350, "position": {"x_mm": 1000, "y_mm": 0}},
    ]
    inst = _instance(fold_count=1, l1=60, l2=0, panels=panels)
    fp = compute_config_fingerprint(
        payload=_payload(inst, assembly_w=2000, assembly_h=350), acm_instance=inst
    )
    inst["production_geometry"] = {
        "schema": "acm_panel_production_geometry_bundle_v1",
        "attachments": [
            {
                "attachment_id": "att1",
                "workspace_id": "ws1",
                "component_instance_id": "acm_test_1",
                "panel_id": "p1",
                "geometry_role": "production_geometry",
                "measurement_status": "measured",
                "config_fingerprint": fp,
                "metrics_snapshot": {
                    "schema": "acm_panel_production_geometry_metrics_v1",
                    "panel_id": "p1",
                    "cut_length_ml": 2.7,
                    "v_groove_l1_ml": 2.7,
                    "v_groove_l2_ml": 0,
                    "v_groove_total_ml": 2.7,
                    "measurement_status": "measured",
                    "measurement_source": "imported_dxf",
                    "active_face_area_m2": 0.35,
                    "warnings": [],
                },
                "warnings": [],
            }
        ],
    }
    metrics = resolve_production_geometry_metrics(_payload(inst, assembly_w=2000, assembly_h=350))
    assert metrics["measurement_status"] in {"unavailable", "partial"}
    panel_ids = {p["panel_id"] for p in metrics["panels"]}
    assert "p2" in panel_ids
    p2 = next(p for p in metrics["panels"] if p["panel_id"] == "p2")
    assert p2["measurement_status"] == "unavailable"
    assert "missing_panel_attachment" in (p2.get("warnings") or [])
