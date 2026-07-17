"""Typed SVG Alucobond panel selection → ProductDefinition canonical_values."""

from __future__ import annotations

from services.mounting_solution_service import normalize_acm_mounting_configuration
from services.product_definition_builder_service import _build_canonical_values


def test_normalize_acm_preserves_svg_panel_fields():
    cfg = normalize_acm_mounting_configuration(
        {
            "panel_width_mm": 2098,
            "panel_height_mm": 734,
            "return_depth_mm": 60,
            "rear_lip_mm": 25,
            "fold_count": 2,
            "finished_depth_mm": 60,
            "svg_support_element_id": "el-3",
            "geometry_hash": "abc",
            "contour_id": "cc_abc",
            "internal_frame_enabled": True,
        }
    )
    assert cfg["fold_count"] == 2
    assert cfg["svg_support_element_id"] == "el-3"
    assert cfg["geometry_hash"] == "abc"
    assert cfg["internal_frame_enabled"] is True
    assert cfg["return_depth_mm"] == 60.0


def test_pd_canonical_projects_confirmed_alucobond_selection():
    payload = {
        "finish_setup": {
            "svg_support_selection": {
                "schema": "svg_support_selection_v1",
                "status": "confirmed",
                "role": "ALUCOBOND_CASED_PANEL",
                "contour_id": "cc_1",
                "svg_support_element_id": "el-3",
                "geometry_hash": "deadbeef",
                "panel_geometry": {
                    "width_mm": 2098.0,
                    "height_mm": 734.0,
                    "area_mm2": 1.5e6,
                    "perimeter_mm": 5600.0,
                    "geometry_hash": "deadbeef",
                },
                "casing_profile": {
                    "fold_count": 2,
                    "l1_mm": 60,
                    "l2_mm": 25,
                    "finished_depth_mm": 60,
                },
                "service_corner": "TOP_RIGHT",
                "internal_frame_enabled": True,
            },
        }
    }
    values = _build_canonical_values([], payload)
    assert values["support_type"] == "alucobond_cased"
    assert values["svg_support_element_id"] == "el-3"
    assert values["casing_profile"]["l1_mm"] == 60
    assert values["panel_geometry"]["width_mm"] == 2098.0
    assert values["service_corner"] == "TOP_RIGHT"
    assert values["internal_frame_enabled"] is True


def test_pd_inactive_selection_no_casing_leakage():
    payload = {
        "finish_setup": {
            "svg_support_selection": {
                "schema": "svg_support_selection_v1",
                "status": "confirmed",
                "role": "DECORATIVE_CONTOUR",
                "contour_id": "cc_x",
            }
        }
    }
    values = _build_canonical_values([], payload)
    assert "casing_profile" not in values
    assert "panel_geometry" not in values
    assert values.get("support_type") != "alucobond_cased"
