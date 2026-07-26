"""Vertical steel fixing bracket — independent of commercial mounting_scope."""

from __future__ import annotations

from data.product_system.mounting_fixing_system_v1 import (
    PROFILE_SHS_20X20X1_5,
    VERTICAL_STEEL_BRACKET,
)
from data.product_system.structural_resource_options_v1 import (
    ACM_BOXED_TEMPLATE,
    get_accepted_options,
)
from services.mounting_fixing_system_service import (
    build_fixing_aggregate_projection,
    normalize_mounting_fixing_system,
    select_vertical_steel_bracket,
)
from services.mounting_solution_service import (
    ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    is_acp_product_component_active,
    is_mounting_solution_composition_active,
)


def test_vertical_bracket_normalizes_manual_dimensions():
    fixing = select_vertical_steel_bracket()
    assert fixing["type_code"] == VERTICAL_STEEL_BRACKET
    assert fixing["main_profile_code"] == PROFILE_SHS_20X20X1_5
    assert fixing["material_code"] == "MAT-STRUCT-STEEL"
    assert fixing["top_angle"]["length_mm"] is None
    assert fixing["top_angle"]["dimension_status"] == "MANUAL_CONFIRMATION_REQUIRED"
    assert fixing["bottom_horizontal_bar"]["length_mm"] is None
    assert fixing["lower_fastener"]["diameter_mm"] == 4.5
    assert fixing["lower_fastener"]["length_mm"] == 60
    assert fixing["confirmation_status"] == "CONFIRMED_WITH_MANUAL_DIMENSIONS"
    assert fixing["top_angle"]["length_mm"] is None
    assert fixing["bottom_horizontal_bar"]["length_mm"] is None


def test_fixing_aggregate_has_no_fake_bom():
    projection = build_fixing_aggregate_projection(select_vertical_steel_bracket())
    assert projection is not None
    assert projection["quantity_status"] == "CONFIGURED_WITH_MANUAL_DIMENSIONS"
    assert projection.get("cut_length_mm") is None
    assert projection.get("bom_lines") is None
    assert projection["top_angle"]["length_mm"] is None


def test_acp_active_when_commercial_mounting_none():
    setup = {
        "mounting_scope": "none",
        "mounting_solution": {
            "template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
            "configuration": {"panel_width_mm": 1000, "panel_height_mm": 600},
        },
    }
    assert is_acp_product_component_active(setup) is True
    assert is_mounting_solution_composition_active(setup) is True


def test_fixing_profile_not_accepted_for_acp_internal_frame():
    accepted = get_accepted_options(ACM_BOXED_TEMPLATE) or {}
    assert PROFILE_SHS_20X20X1_5 not in (accepted.get("accepted_profile_codes") or [])


def test_normalize_ignores_invented_default_length():
    fixing = normalize_mounting_fixing_system(
        {
            "type_code": VERTICAL_STEEL_BRACKET,
            "top_angle": {"length_mm": None},
            "bottom_horizontal_bar": {"length_mm": ""},
        }
    )
    assert fixing["top_angle"]["length_mm"] is None
    assert fixing["bottom_horizontal_bar"]["length_mm"] is None
