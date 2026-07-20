"""Commercial geometry deduction — offer-time CUT/V without DXF."""

from __future__ import annotations

import pytest

from services.acm_production_geometry_metrics import (
    aggregate_assembly_metrics,
    build_commercial_deduction_panel_metrics,
    resolve_production_geometry_metrics,
)
from services.acm_quote_input_helpers import merge_acm_boxed_mounting_derived_fields


def test_golden_single_fold_commercial_deduction():
    m = build_commercial_deduction_panel_metrics(
        panel_id="g1",
        width_mm=2000,
        height_mm=300,
        l1_mm=100,
        l2_mm=0,
        fold_sides="all",
        construction_type="single_fold",
    )
    assert m["measurement_status"] == "commercial_deduced"
    assert m["measurement_source"] == "commercial_deduced"
    assert m["cut_length_ml"] == pytest.approx(5.400000)
    assert m["v_groove_l1_ml"] == pytest.approx(5.400000)
    assert m["v_groove_l2_ml"] == pytest.approx(0.0)
    assert m["v_groove_total_ml"] == pytest.approx(5.400000)
    assert "cut_uses_blank_outer_perimeter_no_cnc_relief" in m["assumptions"]
    assert m["return_material_area_m2"] == pytest.approx(m["blank_area_m2"] - m["active_face_area_m2"])


def test_golden_double_fold_commercial_deduction():
    m = build_commercial_deduction_panel_metrics(
        panel_id="g2",
        width_mm=2000,
        height_mm=300,
        l1_mm=100,
        l2_mm=30,
        fold_sides="all",
        construction_type="double_fold",
    )
    assert m["measurement_status"] == "commercial_deduced"
    assert m["cut_length_ml"] == pytest.approx(5.640000)
    assert m["v_groove_l1_ml"] == pytest.approx(5.400000)
    assert m["v_groove_l2_ml"] == pytest.approx(4.600000)
    assert m["v_groove_total_ml"] == pytest.approx(10.000000)


def test_unequal_panels_sum_not_first_times_n():
    p1 = build_commercial_deduction_panel_metrics(
        panel_id="a",
        width_mm=1000,
        height_mm=350,
        l1_mm=60,
        l2_mm=0,
        fold_sides="all",
    )
    p2 = build_commercial_deduction_panel_metrics(
        panel_id="b",
        width_mm=2000,
        height_mm=350,
        l1_mm=60,
        l2_mm=0,
        fold_sides="all",
    )
    agg = aggregate_assembly_metrics(
        [p1, p2],
        assembly_width_mm=3000,
        assembly_height_mm=350,
        joint_count=1,
    )
    assert agg["total_cut_length_ml"] == pytest.approx(p1["cut_length_ml"] + p2["cut_length_ml"])
    assert agg["total_cut_length_ml"] != pytest.approx(p1["cut_length_ml"] * 2)
    assert agg["measurement_status"] == "commercial_deduced"


def test_three_unequal_panels_sum():
    dims = [(800, 300), (1200, 400), (1500, 350)]
    panels = [
        build_commercial_deduction_panel_metrics(
            panel_id=f"p{i}",
            width_mm=w,
            height_mm=h,
            l1_mm=50,
            l2_mm=0,
            fold_sides="all",
        )
        for i, (w, h) in enumerate(dims)
    ]
    agg = aggregate_assembly_metrics(
        panels,
        assembly_width_mm=3500,
        assembly_height_mm=400,
        joint_count=2,
    )
    assert agg["total_cut_length_ml"] == pytest.approx(
        sum(p["cut_length_ml"] for p in panels)
    )
    assert agg["total_cut_length_ml"] != pytest.approx(panels[0]["cut_length_ml"] * 3)


def test_ten_panels_sum():
    panels = [
        build_commercial_deduction_panel_metrics(
            panel_id=f"p{i}",
            width_mm=1000,
            height_mm=350,
            l1_mm=60,
            l2_mm=0,
            fold_sides="all",
        )
        for i in range(10)
    ]
    agg = aggregate_assembly_metrics(
        panels,
        assembly_width_mm=10000,
        assembly_height_mm=350,
        joint_count=9,
    )
    assert agg["panel_count"] == 10
    assert agg["total_cut_length_ml"] == pytest.approx(panels[0]["cut_length_ml"] * 10)
    assert agg["total_v_groove_ml"] == pytest.approx(panels[0]["v_groove_total_ml"] * 10)


def test_resolve_double_fold_without_dxf_commercial():
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
    # per panel: blank 1260×610 → cut 3.74; V_L1 3.5; V_L2 2.7; V_tot 6.2
    assert metrics["total_cut_length_ml"] == pytest.approx(7.48)
    assert metrics["total_v_groove_l1_ml"] == pytest.approx(7.0)
    assert metrics["total_v_groove_l2_ml"] == pytest.approx(5.4)
    assert metrics["total_v_groove_ml"] == pytest.approx(12.4)


def test_fold_sides_not_all_unavailable():
    m = build_commercial_deduction_panel_metrics(
        panel_id="x",
        width_mm=1000,
        height_mm=350,
        l1_mm=60,
        l2_mm=0,
        fold_sides="long_only",
    )
    assert m["measurement_status"] == "unavailable"
    assert m["cut_length_ml"] is None


def test_merge_single_fold_commercial_cpp_aliases():
    payload = {
        "finish_setup": {
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_sf",
                "configuration": {
                    "fold_count": 1,
                    "l1_mm": 60,
                    "l2_mm": 0,
                    "finished_depth_mm": 60,
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
    # blank peri per panel 3.18 × 2
    assert merged["panel_perimeter_m"] == pytest.approx(6.36)
    assert merged["fold_length_m"] == pytest.approx(6.36)
    assert merged["acm_path_quantity_status"] == "commercial_deduced"


def test_stale_attachment_falls_to_commercial_deduction():
    payload = {
        "finish_setup": {
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_stale",
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
                            "width_mm": 2000,
                            "height_mm": 300,
                            "position": {"x_mm": 0, "y_mm": 0},
                        }
                    ],
                    "joints": [],
                },
                "production_geometry": {
                    "schema": "acm_panel_production_geometry_bundle_v1",
                    "attachments": [
                        {
                            "attachment_id": "att1",
                            "workspace_id": "ws1",
                            "component_instance_id": "acm_stale",
                            "panel_id": "p1",
                            "geometry_role": "production_geometry",
                            "measurement_status": "measured",
                            "config_fingerprint": "outdated",
                            "metrics_snapshot": {
                                "schema": "acm_panel_production_geometry_metrics_v1",
                                "panel_id": "p1",
                                "cut_length_ml": 99.0,
                                "v_groove_l1_ml": 99.0,
                                "v_groove_l2_ml": 0.0,
                                "v_groove_total_ml": 99.0,
                                "measurement_status": "measured",
                                "measurement_source": "imported_dxf",
                                "warnings": [],
                            },
                            "warnings": [],
                        }
                    ],
                },
            },
            "mounting_solution": {
                "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "configuration": {
                    "panel_width_mm": 2000,
                    "panel_height_mm": 300,
                    "fold_sides": "all",
                    "return_depth_mm": 100,
                },
            },
        }
    }
    metrics = resolve_production_geometry_metrics(payload)
    assert metrics["measurement_status"] in {
        "commercial_deduced",
        "commercial_deduced_with_assumptions",
    }
    assert metrics["total_cut_length_ml"] == pytest.approx(5.4)
    assert metrics["total_cut_length_ml"] != pytest.approx(99.0)
    assert "production_geometry_stale" in metrics["warnings"]
    assert metrics.get("measurement_source") == "commercial_deduced_after_stale"
