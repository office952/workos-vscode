"""ACP internal frame domain — OWNER_CONFIRMED formula & crossbar spacing."""

from __future__ import annotations

from services.acp_internal_frame_domain import (
    compute_frame_outer_dimensions,
    max_crossbar_spacing_mm,
    normalize_internal_frame_config,
    suggest_crossbar_count,
    suggest_crossbars_for_orientation,
)
from data.product_system.structural_resource_options_v1 import (
    MAT_STRUCT_ALUMINIUM,
    MAT_STRUCT_STEEL,
    list_materials,
    list_profiles,
)


def test_materials_exist_acp_profiles_gated():
    from data.product_system.structural_resource_options_v1 import (
        ACM_BOXED_TEMPLATE,
        get_accepted_options,
    )

    codes = {m["code"] for m in list_materials()}
    assert MAT_STRUCT_STEEL in codes
    assert MAT_STRUCT_ALUMINIUM in codes
    accepted = get_accepted_options(ACM_BOXED_TEMPLATE) or {}
    assert accepted.get("accepted_profile_codes") == []
    fixing = [p for p in list_profiles() if p["code"] == "PROFILE-SHS-20X20X1_5"]
    assert len(fixing) == 1
    assert "acp_internal_frame" in (fixing[0].get("provenance") or {}).get("not_for", [])


def test_frame_formula_2000x700_acm3():
    dims = compute_frame_outer_dimensions(
        panel_outer_width_mm=2000,
        panel_outer_height_mm=700,
        panel_material_thickness_mm=3,
    )
    assert dims["valid"] is True
    assert dims["frame_outer_width_mm"] == 1992
    assert dims["frame_outer_height_mm"] == 692
    assert dims["total_fit_allowance_mm"] == 2


def test_frame_formula_identical_for_fold_metadata():
    """Fold count must not change frame size — domain ignores fold."""
    a = compute_frame_outer_dimensions(
        panel_outer_width_mm=2000,
        panel_outer_height_mm=700,
        panel_material_thickness_mm=3,
    )
    b = compute_frame_outer_dimensions(
        panel_outer_width_mm=2000,
        panel_outer_height_mm=700,
        panel_material_thickness_mm=3,
    )
    assert a["frame_outer_width_mm"] == b["frame_outer_width_mm"] == 1992
    single = normalize_internal_frame_config(
        {"enabled": True, "material_code": MAT_STRUCT_STEEL},
        panel_width_mm=2000,
        panel_height_mm=700,
        panel_thickness_mm=3,
        fold_count=1,
    )
    double = normalize_internal_frame_config(
        {"enabled": True, "material_code": MAT_STRUCT_STEEL},
        panel_width_mm=2000,
        panel_height_mm=700,
        panel_thickness_mm=3,
        fold_count=2,
    )
    assert single["frame_outer_width_mm"] == double["frame_outer_width_mm"] == 1992
    assert single["frame_outer_height_mm"] == double["frame_outer_height_mm"] == 692


def test_crossbar_spacing_by_material():
    assert max_crossbar_spacing_mm(MAT_STRUCT_STEEL) == 1000
    assert max_crossbar_spacing_mm(MAT_STRUCT_ALUMINIUM) == 750


def test_crossbar_suggestion_steel_width_1992():
    # L=1992, S=1000 → ceil(1.992)=2 spans → 1 internal bar
    assert suggest_crossbar_count(length_mm=1992, max_spacing_mm=1000)["suggested_crossbar_count"] == 1
    vertical = suggest_crossbars_for_orientation(
        material_code=MAT_STRUCT_STEEL,
        frame_outer_width_mm=1992,
        frame_outer_height_mm=692,
        orientation="VERTICAL",
    )
    assert vertical["suggested_crossbar_count"] == 1
    assert vertical["max_crossbar_spacing_mm"] == 1000


def test_crossbar_suggestion_aluminium_width_1992():
    # L=1992, S=750 → ceil(2.656)=3 spans → 2 internal bars
    assert suggest_crossbar_count(length_mm=1992, max_spacing_mm=750)["suggested_crossbar_count"] == 2
    vertical = suggest_crossbars_for_orientation(
        material_code=MAT_STRUCT_ALUMINIUM,
        frame_outer_width_mm=1992,
        frame_outer_height_mm=692,
        orientation="VERTICAL",
    )
    assert vertical["suggested_crossbar_count"] == 2
    assert vertical["max_crossbar_spacing_mm"] == 750


def test_inactive_isolation():
    cfg = normalize_internal_frame_config({"enabled": False, "material_code": MAT_STRUCT_STEEL})
    assert cfg["enabled"] is False
    assert cfg["confirmation_status"] == "NOT_APPLICABLE"
    assert cfg["material_code"] is None


def test_active_incomplete_without_profiles():
    cfg = normalize_internal_frame_config(
        {
            "enabled": True,
            "material_code": MAT_STRUCT_STEEL,
            "crossbar_orientation": "VERTICAL",
            "confirmed_crossbar_count": 1,
        },
        panel_width_mm=2000,
        panel_height_mm=700,
        panel_thickness_mm=3,
    )
    assert cfg["confirmation_status"] == "INCOMPLETE"
    assert "internal_frame_profile_catalog_empty" in cfg["blockers"]


def test_acm_normalize_preserves_nested_frame():
    from services.mounting_solution_service import normalize_acm_mounting_configuration

    cfg = normalize_acm_mounting_configuration(
        {
            "panel_width_mm": 2000,
            "panel_height_mm": 700,
            "acm_thickness_mm": 3,
            "internal_frame_enabled": True,
            "internal_frame": {
                "enabled": True,
                "material_code": MAT_STRUCT_STEEL,
                "crossbar_orientation": "VERTICAL",
                "confirmed_crossbar_count": 1,
            },
        }
    )
    assert cfg["internal_frame"]["enabled"] is True
    assert cfg["internal_frame"]["frame_outer_width_mm"] == 1992
    assert cfg["internal_frame_enabled"] is True
