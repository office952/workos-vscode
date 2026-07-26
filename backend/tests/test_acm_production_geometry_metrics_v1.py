"""Production geometry metrics — golden DXF, ACI mapping, proxy gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.acm_aci_semantic_mapping import classify_aci_color, known_aci_colors
from services.acm_dxf_path_measurement import (
    LENGTH_COMPARE_TOLERANCE_ML,
    measure_dxf_production_paths,
)
from services.acm_production_geometry_metrics import (
    aggregate_assembly_metrics,
    build_proxy_panel_metrics,
    proxy_rectangular_eligible,
    resolve_production_geometry_metrics,
)
from services.acm_quote_input_helpers import merge_acm_boxed_mounting_derived_fields

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "acm_panel_dxf"
SINGLE = FIXTURES / "un-pliu.dxf"
DOUBLE = FIXTURES / "2-pliuri-100x30.dxf"

TOL = LENGTH_COMPARE_TOLERANCE_ML


def test_aci_mapping_known_colors():
    assert classify_aci_color(256) == "CUT"
    assert classify_aci_color(250) == "CUT"
    assert classify_aci_color(1) == "V_GROOVE_L1"
    assert classify_aci_color(242) == "V_GROOVE_L2"
    assert classify_aci_color(7) == "UNKNOWN"
    assert classify_aci_color(None) == "UNKNOWN"
    assert set(known_aci_colors()) == {256, 250, 1, 242}


def test_golden_single_fold_dxf_exact():
    m = measure_dxf_production_paths(SINGLE)
    assert m["measurement_status"] == "measured"
    assert m["cut_length_ml"] == pytest.approx(5.400000, abs=TOL)
    assert m["v_groove_l1_ml"] == pytest.approx(5.400000, abs=TOL)
    assert m["v_groove_l2_ml"] == pytest.approx(0.0, abs=TOL)
    assert m["v_groove_total_ml"] == pytest.approx(5.400000, abs=TOL)
    assert m["unknown_length_ml"] == 0


def test_golden_double_fold_dxf_exact():
    m = measure_dxf_production_paths(DOUBLE)
    assert m["measurement_status"] == "measured"
    assert m["cut_length_ml"] == pytest.approx(5.499412, abs=TOL)
    assert m["v_groove_l1_ml"] == pytest.approx(5.400000, abs=TOL)
    assert m["v_groove_l2_ml"] == pytest.approx(4.600004, abs=TOL)
    assert m["v_groove_total_ml"] == pytest.approx(10.000004, abs=TOL)


def test_unknown_aci_not_included_in_cut_or_v(tmp_path):
    """Synthetic: unknown color length must warn and stay out of CUT/V."""
    import ezdxf

    doc = ezdxf.new()
    msp = doc.modelspace()
    # minimal line as stand-in (measurement supports LINE)
    msp.add_line((0, 0), (1000, 0), dxfattribs={"color": 1})  # V L1 1ml
    msp.add_line((0, 0), (500, 0), dxfattribs={"color": 99})  # unknown 0.5ml
    path = tmp_path / "mixed.dxf"
    doc.saveas(path)
    m = measure_dxf_production_paths(path)
    assert m["v_groove_l1_ml"] == pytest.approx(1.0, abs=TOL)
    assert m["cut_length_ml"] == 0
    assert m["unknown_length_ml"] == pytest.approx(0.5, abs=TOL)
    assert 99 in m["unknown_aci_colors"]
    assert any("unknown_aci_color:99" in w for w in m["warnings"])


def test_proxy_eligible_single_fold_only():
    assert proxy_rectangular_eligible(
        construction_type="single_fold",
        l2_mm=0,
        fold_sides="all",
        has_cutouts=False,
        has_special_corners=False,
        irregular_contour=False,
    )
    assert not proxy_rectangular_eligible(
        construction_type="double_fold",
        l2_mm=30,
        fold_sides="all",
        has_cutouts=False,
        has_special_corners=False,
        irregular_contour=False,
    )
    assert not proxy_rectangular_eligible(
        construction_type="single_fold",
        l2_mm=30,
        fold_sides="all",
        has_cutouts=False,
        has_special_corners=False,
        irregular_contour=False,
    )


def test_proxy_panel_metrics_parametric_not_hardcoded():
    a = build_proxy_panel_metrics(panel_id="a", width_mm=1200, height_mm=400, l1_mm=80, fold_sides="all")
    b = build_proxy_panel_metrics(panel_id="b", width_mm=800, height_mm=200, l1_mm=50, fold_sides="all")
    # Commercial blank perimeter: 1360×560 → 3.84; 900×300 → 2.4
    assert a["cut_length_ml"] == pytest.approx(3.84)
    assert b["cut_length_ml"] == pytest.approx(2.4)
    assert a["cut_length_ml"] != b["cut_length_ml"]
    assert a["measurement_status"] == "commercial_deduced"


def test_multi_panel_aggregation_sum():
    p1 = build_proxy_panel_metrics(panel_id="p1", width_mm=1000, height_mm=350, l1_mm=60, fold_sides="all")
    p2 = build_proxy_panel_metrics(panel_id="p2", width_mm=1200, height_mm=400, l1_mm=60, fold_sides="all")
    agg = aggregate_assembly_metrics(
        [p1, p2],
        assembly_width_mm=2200,
        assembly_height_mm=400,
        joint_count=1,
    )
    assert agg["panel_count"] == 2
    assert agg["total_cut_length_ml"] == pytest.approx(p1["cut_length_ml"] + p2["cut_length_ml"])
    assert agg["total_active_face_area_m2"] == pytest.approx(0.88)  # assembly 2200x400
    assert agg["measurement_status"] == "commercial_deduced"


def test_resolve_dxf_measured_path():
    metrics = resolve_production_geometry_metrics(
        {
            "acm_production_dxf_path": str(DOUBLE),
            "assembly_width_mm": 2000,
            "assembly_height_mm": 300,
            "finish_setup": {
                "acm_panel_instance": {
                    "schema": "acm_panel_component_instance_v1",
                    "component_instance_id": "acm_dxf",
                    "configuration": {
                        "fold_count": 2,
                        "l1_mm": 100,
                        "l2_mm": 30,
                        "finished_depth_mm": 100,
                    },
                }
            },
        }
    )
    assert metrics["measurement_status"] == "measured"
    assert metrics["total_cut_length_ml"] == pytest.approx(5.499412, abs=TOL)
    assert metrics["total_v_groove_ml"] == pytest.approx(10.000004, abs=TOL)


def test_resolve_double_fold_without_dxf_commercial_deduced():
    metrics = resolve_production_geometry_metrics(
        {
            "finish_setup": {
                "acm_panel_instance": {
                    "schema": "acm_panel_component_instance_v1",
                    "component_instance_id": "acm_df",
                    "configuration": {
                        "fold_count": 2,
                        "l1_mm": 100,
                        "l2_mm": 30,
                        "finished_depth_mm": 100,
                    },
                    "geometry": {
                        "panels": [
                            {
                                "panel_id": "p1",
                                "width_mm": 1000,
                                "height_mm": 350,
                                "position": {"x_mm": 0, "y_mm": 0},
                            },
                            {
                                "panel_id": "p2",
                                "width_mm": 1000,
                                "height_mm": 350,
                                "position": {"x_mm": 1000, "y_mm": 0},
                            },
                        ],
                        "joints": [{"joint_id": "j1"}],
                    },
                },
                "segmented_background": {
                    "status": "PROPOSED",
                    "panels": [
                        {
                            "panel_id": "p1",
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 0, "y_mm": 0},
                        },
                        {
                            "panel_id": "p2",
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 1000, "y_mm": 0},
                        },
                    ],
                    "assembly_dimensions": {"width_mm": 2000, "height_mm": 350},
                },
                "mounting_solution": {
                    "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    "configuration": {
                        "panel_width_mm": 1000,
                        "panel_height_mm": 350,
                        "fold_sides": "all",
                        "return_depth_mm": 60,
                    },
                },
            }
        }
    )
    assert metrics["measurement_status"] == "commercial_deduced"
    assert metrics["total_cut_length_ml"] == pytest.approx(7.48)
    assert metrics["total_v_groove_ml"] == pytest.approx(12.4)
    assert "cut_v_quantity_source=commercial_deduction" in metrics["warnings"]


def test_merge_single_fold_commercial_sets_cpp_aliases():
    payload = {
        "finish_setup": {
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_sf",
                "configuration": {
                    "fold_count": 1,
                    "l1_mm": 100,
                    "l2_mm": 0,
                    "finished_depth_mm": 100,
                },
                "geometry": {
                    "panels": [
                        {
                            "panel_id": "p1",
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 0, "y_mm": 0},
                        },
                        {
                            "panel_id": "p2",
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 1000, "y_mm": 0},
                        },
                    ],
                    "joints": [],
                },
            },
            "segmented_background": {
                "status": "PROPOSED",
                "panels": [
                    {
                        "panel_id": "p1",
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 0, "y_mm": 0},
                    },
                    {
                        "panel_id": "p2",
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 1000, "y_mm": 0},
                    },
                ],
                "assembly_dimensions": {"width_mm": 2000, "height_mm": 350},
            },
            "mounting_solution": {
                "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "configuration": {
                    "panel_width_mm": 1000,
                    "panel_height_mm": 350,
                    "fold_sides": "all",
                    "return_depth_mm": 60,
                },
            },
        }
    }
    merged = merge_acm_boxed_mounting_derived_fields(payload)
    assert merged["panel_area_m2"] == pytest.approx(0.7)
    # blank peri per panel (1200+550)*2/1000 = 3.5 × 2
    assert merged["panel_perimeter_m"] == pytest.approx(7.0)
    assert merged["fold_length_m"] == pytest.approx(7.0)
    assert merged["acm_path_quantity_status"] == "commercial_deduced"


def test_merge_double_fold_sets_commercial_cut_v():
    payload = {
        "finish_setup": {
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_df2",
                "configuration": {
                    "fold_count": 2,
                    "l1_mm": 83,
                    "l2_mm": 28,
                    "finished_depth_mm": 83,
                },
                "geometry": {
                    "panels": [
                        {
                            "panel_id": "p1",
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 0, "y_mm": 0},
                        },
                        {
                            "panel_id": "p2",
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 1000, "y_mm": 0},
                        },
                    ],
                    "joints": [{"joint_id": "j1"}],
                },
            },
            "segmented_background": {
                "status": "PROPOSED",
                "panels": [
                    {
                        "panel_id": "p1",
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 0, "y_mm": 0},
                    },
                    {
                        "panel_id": "p2",
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 1000, "y_mm": 0},
                    },
                ],
                "assembly_dimensions": {"width_mm": 2000, "height_mm": 350},
            },
            "mounting_solution": {
                "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "configuration": {
                    "panel_width_mm": 1000,
                    "panel_height_mm": 350,
                    "fold_sides": "all",
                    "return_depth_mm": 83,
                },
            },
        }
    }
    merged = merge_acm_boxed_mounting_derived_fields(payload)
    assert merged["panel_area_m2"] == pytest.approx(0.7)
    assert merged["panel_perimeter_m"] == pytest.approx(7.176)
    assert merged["fold_length_m"] == pytest.approx(12.128)
    assert merged["acm_path_quantity_status"] == "commercial_deduced"
