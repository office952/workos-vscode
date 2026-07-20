"""Shared AcmPanel assembly extent — FE/BE parity contract."""

from services.acm_assembly_extent import (
    ASSEMBLY_DIMENSION_TOLERANCE_MM,
    compute_acm_assembly_extent,
    inject_assembly_extent_keys,
)
from services.product_definition_builder_service import _build_canonical_values


def test_tolerance_is_one_mm():
    assert ASSEMBLY_DIMENSION_TOLERANCE_MM == 1.0


def test_multi_panel_positioned_matches_assembly_dimensions():
    result = compute_acm_assembly_extent(
        panels=[
            {"width_mm": 1000, "height_mm": 350, "position": {"x_mm": 0, "y_mm": 0}},
            {"width_mm": 1000, "height_mm": 350, "position": {"x_mm": 1000, "y_mm": 0}},
        ],
        assembly_dimensions={"width_mm": 2000, "height_mm": 350},
        envelope_width_mm=1000,
        envelope_height_mm=350,
    )
    assert result["assembly_width_mm"] == 2000
    assert result["assembly_height_mm"] == 350
    assert result["source"] == "assembly_dimensions"
    assert result["envelope_ignored_for_multi_panel"] is True
    assert any("Envelope contour" in w for w in result["warnings"])


def test_multi_panel_missing_positions_uses_assembly_dimensions():
    result = compute_acm_assembly_extent(
        panels=[
            {"panel_id": "p1", "width_mm": 1000, "height_mm": 350},
            {"panel_id": "p2", "width_mm": 1000, "height_mm": 350},
        ],
        assembly_dimensions={"width_mm": 2000, "height_mm": 350},
        envelope_width_mm=1000,
        envelope_height_mm=350,
    )
    assert result["assembly_width_mm"] == 2000
    assert result["assembly_height_mm"] == 350
    assert result["source"] == "assembly_dimensions"


def test_never_overloads_panel_keys_in_canonical_values():
    payload = {
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
                            "panel_id": "panel_1",
                            "order": 1,
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 0, "y_mm": 0},
                        },
                        {
                            "panel_id": "panel_2",
                            "order": 2,
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 1000, "y_mm": 0},
                        },
                    ],
                },
            },
            "segmented_background": {
                "schema": "acm_segmented_background_v1",
                "status": "PROPOSED",
                "operator_confirmed": False,
                "panels": [
                    {
                        "panel_id": "panel_1",
                        "order": 1,
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 0, "y_mm": 0},
                    },
                    {
                        "panel_id": "panel_2",
                        "order": 2,
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 1000, "y_mm": 0},
                    },
                ],
                "assembly_dimensions": {"width_mm": 2000, "height_mm": 350},
            },
        }
    }
    values = _build_canonical_values([], payload)
    assert values["assembly_width_mm"] == 2000
    assert values["assembly_height_mm"] == 350
    assert "panel_width_mm" not in values or values.get("panel_width_mm") != 2000


def test_inject_assembly_extent_keys_on_values():
    values: dict = {}
    warnings = inject_assembly_extent_keys(
        values,
        finish={
            "segmented_background": {
                "panels": [
                    {"width_mm": 1000, "height_mm": 350, "x_mm": 0, "y_mm": 0},
                    {"width_mm": 1000, "height_mm": 350, "x_mm": 1000, "y_mm": 0},
                ],
                "assembly_dimensions": {"width_mm": 2000, "height_mm": 350},
            }
        },
    )
    assert values["assembly_width_mm"] == 2000
    assert values["assembly_height_mm"] == 350
    assert isinstance(warnings, list)
