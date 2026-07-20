"""AcmPanel commercial geometry — face/assembly + production metrics wiring."""

import pytest

from services.acm_commercial_geometry import (
    apply_acm_commercial_geometry,
    build_acm_panel_authority_summary,
    compute_acm_commercial_geometry,
)
from services.acm_quote_input_helpers import merge_acm_boxed_mounting_derived_fields


def _fixture_payload(*, fold_count: int = 1, l2_mm: float = 0.0) -> dict:
    return {
        "finish_setup": {
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_1",
                "association_status": "proposed",
                "technical_configuration_status": "proposed",
                "composition_status": "unconfirmed",
                "geometry": {
                    "width_mm": 1000,
                    "height_mm": 350,
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
                    "joints": [
                        {
                            "joint_id": "j1",
                            "left_panel_id": "p1",
                            "right_panel_id": "p2",
                            "orientation": "VERTICAL",
                        }
                    ],
                },
                "configuration": {
                    "finished_depth_mm": 60,
                    "fold_count": fold_count,
                    "l1_mm": 60,
                    "l2_mm": l2_mm,
                    "field_authority": {
                        "fold_count": "catalog_default",
                        "l1_mm": "catalog_default",
                        "acm_thickness_mm": "catalog_default",
                    },
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
                "joints": [{"joint_id": "j1"}],
            },
            "mounting_solution": {
                "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "configuration": {
                    "panel_width_mm": 1000,
                    "panel_height_mm": 350,
                    "acm_thickness_mm": 3,
                    "return_depth_mm": 60,
                    "fold_sides": "all",
                },
            },
        }
    }


def test_multi_panel_face_area_from_assembly_not_envelope():
    geom = compute_acm_commercial_geometry(_fixture_payload())
    assert geom["assembly_width_mm"] == 2000
    assert geom["assembly_height_mm"] == 350
    assert geom["commercial_face_area_m2"] == 0.7
    assert geom["assembly_exterior_perimeter_m"] == 4.7
    assert geom["panel_count"] == 2
    assert geom["mode"] == "multi_panel"


def test_merge_single_fold_commercial_aliases_cpp_keys():
    merged = merge_acm_boxed_mounting_derived_fields(_fixture_payload(fold_count=1, l2_mm=0))
    assert merged["panel_width_mm"] == 1000
    assert merged["panel_height_mm"] == 350
    assert merged["assembly_width_mm"] == 2000
    assert merged["panel_area_m2"] == 0.7
    # blank peri L1=60: 3.18 × 2 panels
    assert merged["panel_perimeter_m"] == 6.36
    assert merged["fold_length_m"] == 6.36
    assert merged["acm_path_quantity_status"] == "commercial_deduced"


def test_merge_double_fold_sets_commercial_cut_v():
    merged = merge_acm_boxed_mounting_derived_fields(_fixture_payload(fold_count=2, l2_mm=28))
    assert merged["panel_area_m2"] == 0.7
    # per panel L1=60 L2=28: blank 1176×526 → cut 3.404; V_L1 3.18; V_L2 2.7; V_tot 5.88
    assert merged["panel_perimeter_m"] == pytest.approx(6.808)
    assert merged["fold_length_m"] == pytest.approx(11.76)
    assert merged["acm_path_quantity_status"] == "commercial_deduced"


def test_apply_does_not_overwrite_panel_dims_with_assembly():
    payload = _fixture_payload()
    payload["panel_width_mm"] = 1000
    payload["panel_height_mm"] = 350
    apply_acm_commercial_geometry(payload)
    assert payload["panel_width_mm"] == 1000
    assert payload["panel_height_mm"] == 350
    assert payload["assembly_width_mm"] == 2000


def test_single_panel_parity():
    payload = {
        "finish_setup": {
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_s",
                "association_status": "proposed",
                "technical_configuration_status": "proposed",
                "composition_status": "unconfirmed",
                "geometry": {
                    "width_mm": 1200,
                    "height_mm": 800,
                    "panels": [
                        {
                            "panel_id": "p1",
                            "width_mm": 1200,
                            "height_mm": 800,
                            "position": {"x_mm": 0, "y_mm": 0},
                        }
                    ],
                    "joints": [],
                },
                "configuration": {
                    "finished_depth_mm": 60,
                    "fold_count": 1,
                    "l1_mm": 60,
                    "l2_mm": 0,
                },
            },
            "mounting_solution": {
                "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "configuration": {
                    "panel_width_mm": 1200,
                    "panel_height_mm": 800,
                    "return_depth_mm": 60,
                    "fold_sides": "all",
                },
            },
        }
    }
    merged = merge_acm_boxed_mounting_derived_fields(payload)
    assert merged["panel_area_m2"] == 0.96
    # blank 1320×920 → 4.48
    assert merged["panel_perimeter_m"] == pytest.approx(4.48)
    assert merged["fold_length_m"] == pytest.approx(4.48)
    assert merged["acm_path_quantity_status"] == "commercial_deduced"


def test_authority_summary_fixture_provisional_with_warnings():
    summary = build_acm_panel_authority_summary(_fixture_payload())
    assert summary["status"] == "provisional_with_warnings"
    assert summary["final_eligibility"] is False
    assert summary["offer_eligibility"] is False
    assert summary["execution_eligibility"] is False
    assert "technical_configuration_unconfirmed" in summary["warnings"]
    assert "segmentation_proposed" in summary["warnings"]
    assert "construction_catalog_defaults" in summary["warnings"]
    assert "composition_inconsistent_or_unconfirmed" in summary["warnings"]


def test_assembly_fallback_warns_when_panel_list_missing():
    payload = {
        "assembly_width_mm": 2000,
        "assembly_height_mm": 350,
        "finish_setup": {
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_fb",
                "association_status": "proposed",
                "technical_configuration_status": "proposed",
                "composition_status": "unconfirmed",
                "geometry": {"width_mm": 1000, "height_mm": 350, "panels": [], "joints": []},
                "configuration": {
                    "finished_depth_mm": 60,
                    "fold_count": 1,
                    "l2_mm": 0,
                },
            },
            "mounting_solution": {
                "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "configuration": {
                    "panel_width_mm": 1000,
                    "panel_height_mm": 350,
                    "return_depth_mm": 60,
                    "fold_sides": "all",
                },
            },
        },
    }
    geom = compute_acm_commercial_geometry(payload)
    assert geom["commercial_face_area_m2"] == 0.7
    assert geom["mode"] == "assembly_fallback"
    assert "missing_panel_list_assembly_face_only" in geom["warnings"]
