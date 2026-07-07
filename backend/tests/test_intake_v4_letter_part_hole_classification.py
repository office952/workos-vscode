"""Intake V4 letter vs inner-hole part classification."""

from __future__ import annotations

import pytest

from services.intake_v4_finish_adapter import build_v3_workspace_from_v4_payload
from services.intake_v4_letter_part_classification_service import classify_letter_parts_from_analysis
from services.intake_v4_pricing_input_service import build_v4_pricing_input_preview
from services.intake_v4_quote_geometry_service import build_quote_geometry_from_analysis
from schemas.intake_v4 import (
    IntakeV4ClientRequest,
    IntakeV4FinishSetup,
    IntakeV4LayerRoleSetup,
    IntakeV4ProductBinding,
    IntakeV4WorkspacePayload,
)


def _layer_setup(*roles: tuple[str, str]) -> dict:
    return {
        "confirmation_status": "complete",
        "layers": [
            {
                "layer_key": layer_key,
                "layer_name": layer_key,
                "confirmed_role": role,
                "confirmation_state": "confirmed",
            }
            for layer_key, role in roles
        ],
    }


def _part(
    part_id: str,
    *,
    layer: str,
    x: float,
    y: float,
    width: float,
    height: float,
    outer_mm: float,
    inner_mm: float = 0.0,
    inner_count: int = 0,
    contour_count: int = 1,
    can_nest: bool = True,
) -> dict:
    total = outer_mm + inner_mm
    return {
        "id": part_id,
        "contourCount": contour_count,
        "outerContourCount": 1,
        "innerContourCount": inner_count,
        "canNest": can_nest,
        "source": {"layerId": layer, "layerName": layer},
        "bounds": {
            "xMm": x,
            "yMm": y,
            "widthMm": width,
            "heightMm": height,
        },
        "geometry": {
            "outerPerimeterMm": outer_mm,
            "innerPerimeterMm": inner_mm,
            "totalContourPerimeterMm": total,
        },
    }


class TestIntakeV4LetterPartHoleClassification:
    def test_inner_contour_inside_outer_is_classified_as_hole(self):
        analysis = {
            "parts": {
                "count": 2,
                "nestableCount": 2,
                "items": [
                    _part("outer-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=800, inner_mm=120, inner_count=1, contour_count=2),
                    _part("hole-orphan", layer="face-layer", x=50, y=50, width=40, height=40, outer_mm=160, contour_count=1),
                ],
            }
        }
        result = classify_letter_parts_from_analysis(analysis, _layer_setup(("face-layer", "face")))
        hole_rows = [row for row in result["parts"] if row["is_inner_hole"]]
        assert len(hole_rows) == 1
        assert hole_rows[0]["part_id"] == "hole-orphan"
        assert hole_rows[0]["parent_part_id"] == "outer-a"

    def test_hole_does_not_count_as_real_letter(self):
        analysis = {
            "parts": {
                "count": 2,
                "nestableCount": 2,
                "items": [
                    _part("outer-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=800),
                    _part("hole-orphan", layer="face-layer", x=50, y=50, width=40, height=40, outer_mm=160),
                ],
            }
        }
        result = classify_letter_parts_from_analysis(analysis, _layer_setup(("face-layer", "face")))
        assert result["real_letters_count"] == 1
        assert result["inner_holes_count"] == 1

    def test_hole_not_nestable_independent_part(self):
        analysis = {
            "parts": {
                "items": [
                    _part("outer-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=800),
                    _part("hole-orphan", layer="face-layer", x=50, y=50, width=40, height=40, outer_mm=160),
                ]
            }
        }
        result = classify_letter_parts_from_analysis(analysis, _layer_setup(("face-layer", "face")))
        hole = next(row for row in result["parts"] if row["part_id"] == "hole-orphan")
        assert hole["nestable"] is False
        assert hole["counts_as_material_piece"] is False

    def test_letter_O_with_inner_hole_should_nest_as_one_piece_with_negative_cutout_not_two_material_parts(self):
        analysis = {
            "parts": {
                "items": [
                    _part("outer-o", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=800, inner_mm=120, inner_count=1, contour_count=2),
                    _part("inner-o-hole", layer="face-layer", x=60, y=60, width=50, height=50, outer_mm=180),
                ]
            }
        }
        result = classify_letter_parts_from_analysis(analysis, _layer_setup(("face-layer", "face")))

        assert result["real_letters_count"] == 1
        assert result["material_piece_count"] == 1
        assert result["inner_holes_count"] == 2
        hole = next(row for row in result["parts"] if row["part_id"] == "inner-o-hole")
        assert hole["is_inner_hole"] is True
        assert hole["nestable"] is False
        assert hole["counts_as_material_piece"] is False

    def test_letter_A_inner_counter_should_not_be_nested_as_positive_material_piece(self):
        analysis = {
            "parts": {
                "items": [
                    _part("outer-a", layer="face-layer", x=0, y=0, width=220, height=220, outer_mm=900, inner_mm=90, inner_count=1, contour_count=2),
                    _part("inner-a-hole", layer="face-layer", x=85, y=90, width=35, height=35, outer_mm=120),
                ]
            }
        }
        result = classify_letter_parts_from_analysis(analysis, _layer_setup(("face-layer", "face")))

        assert result["real_letters_count"] == 1
        assert result["material_piece_count"] == 1
        hole = next(row for row in result["parts"] if row["part_id"] == "inner-a-hole")
        assert hole["is_inner_hole"] is True
        assert hole["nestable"] is False
        assert hole["counts_as_material_piece"] is False

    def test_hole_perimeter_contributes_to_cutting_perimeter(self):
        analysis = {
            "parts": {
                "items": [
                    _part("outer-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=800, inner_mm=100, inner_count=1, contour_count=2),
                ]
            }
        }
        result = classify_letter_parts_from_analysis(analysis, _layer_setup(("face-layer", "face")))
        assert result["outer_perimeter_mm"] == 800
        assert result["hole_perimeter_mm"] == 100
        assert result["cutting_perimeter_mm"] == 900

    def test_holes_increase_return_and_cnc_not_letter_count(self):
        analysis = {
            "layers": [{"id": "face-layer", "name": "face-layer", "perimeterMl": 9.0, "boundingAreaSqm": 1.0}],
            "parts": {
                "items": [
                    _part(
                        "outer-a",
                        layer="face-layer",
                        x=0,
                        y=0,
                        width=200,
                        height=200,
                        outer_mm=800,
                        inner_mm=100,
                        inner_count=1,
                        contour_count=2,
                    ),
                ]
            },
        }
        layer_setup = _layer_setup(("face-layer", "face"))
        finish_setup = {
            "return_finish_type": "standard_aluminum",
            "return_depth_mm": 60,
            "letter_group_finishes": [
                {
                    "group_key": "face-layer",
                    "layer_name": "face-layer",
                    "return_finish_type": "standard_aluminum",
                    "return_depth_mm": 60,
                }
            ],
        }
        from services.intake_v4_volumetric_return_metrics_service import enrich_quote_geometry_with_volumetric_return

        base = build_quote_geometry_from_analysis(analysis, layer_setup)
        quote = enrich_quote_geometry_with_volumetric_return(
            base,
            finish_setup=finish_setup,
            svg_analysis_json=analysis,
            layer_role_setup=layer_setup,
        )
        assert quote["letter_count"] == 1
        assert quote["inner_holes_count"] == 1
        assert quote["outer_letter_perimeter_ml"] == 0.8
        assert quote["inner_hole_letter_perimeter_ml"] == 0.1
        assert quote["letter_return_perimeter_ml"] == 0.9
        assert quote["cnc_cutting_perimeter_ml"] == 0.9
        assert quote["led_perimeter_ml"] == 0.8
        assert quote.get("volumetric_piece_count") == 1

    def test_cant_return_excludes_holes_when_return_inactive(self):
        analysis = {
            "layers": [
                {"id": "face-layer", "name": "face-layer", "perimeterMl": 9.9, "boundingAreaSqm": 1.0},
            ],
            "parts": {
                "items": [
                    _part("outer-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=800, inner_mm=100, inner_count=1),
                    _part("outer-b", layer="face-layer", x=300, y=0, width=200, height=200, outer_mm=600, inner_mm=0),
                ]
            },
        }
        quote = build_quote_geometry_from_analysis(analysis, _layer_setup(("face-layer", "face")))
        assert quote["letter_count"] == 2
        assert quote["letter_perimeter_m"] == 1.4
        assert quote["cutting_perimeter_ml"] == 1.5
        assert quote.get("letter_return_perimeter_ml") is None

    def test_artwork_return_included_when_cant_active(self):
        analysis = {
            "layers": [
                {"id": "face-layer", "name": "face-layer", "perimeterMl": 6.0, "boundingAreaSqm": 1.0},
                {"id": "logo", "name": "logo", "perimeterMl": 2.0, "boundingAreaSqm": 0.4},
            ],
            "parts": {
                "items": [
                    _part("face-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=600),
                    _part("logo-a", layer="logo", x=0, y=300, width=100, height=100, outer_mm=200),
                ],
            },
        }
        layer_setup = _layer_setup(("face-layer", "face"), ("logo", "printed_artwork"))
        finish_setup = {
            "artwork_finishes": [
                {
                    "layer_key": "logo",
                    "layer_name": "logo",
                    "execution_type": "needs_decision",
                    "return_finish_type": "standard_aluminum",
                    "return_depth_mm": 60,
                    "element_count": 1,
                }
            ],
            "letter_group_finishes": [
                {
                    "group_key": "face-layer",
                    "layer_name": "face-layer",
                    "return_finish_type": "standard_aluminum",
                    "return_depth_mm": 60,
                }
            ],
        }
        from services.intake_v4_volumetric_return_metrics_service import enrich_quote_geometry_with_volumetric_return

        base = build_quote_geometry_from_analysis(analysis, layer_setup)
        quote = enrich_quote_geometry_with_volumetric_return(
            base,
            finish_setup=finish_setup,
            svg_analysis_json=analysis,
            layer_role_setup=layer_setup,
        )
        assert quote["letter_count"] == 1
        assert quote["artwork_piece_count"] == 1
        assert quote["volumetric_piece_count"] == 2
        assert quote["letter_return_perimeter_ml"] == 0.6
        assert quote["artwork_return_perimeter_ml"] == 0.2
        assert quote["return_material_perimeter_ml"] == 0.8
        assert quote["led_perimeter_ml"] == 0.6

    def test_artwork_return_none_excluded(self):
        analysis = {
            "layers": [{"id": "logo", "name": "logo", "perimeterMl": 2.0, "boundingAreaSqm": 0.4}],
            "parts": {"items": [_part("logo-a", layer="logo", x=0, y=0, width=100, height=100, outer_mm=200)]},
        }
        layer_setup = _layer_setup(("logo", "printed_artwork"))
        finish_setup = {
            "artwork_finishes": [
                {
                    "layer_key": "logo",
                    "layer_name": "logo",
                    "execution_type": "needs_decision",
                    "return_finish_type": "none",
                }
            ]
        }
        from services.intake_v4_volumetric_return_metrics_service import enrich_quote_geometry_with_volumetric_return

        base = build_quote_geometry_from_analysis(analysis, layer_setup)
        quote = enrich_quote_geometry_with_volumetric_return(
            base,
            finish_setup=finish_setup,
            svg_analysis_json=analysis,
            layer_role_setup=layer_setup,
        )
        assert quote.get("artwork_return_perimeter_ml") is None
        assert quote.get("artwork_piece_count") == 0

    def test_artwork_not_in_led_perimeter(self):
        analysis = {
            "layers": [
                {"id": "face-layer", "name": "face-layer", "perimeterMl": 6.0, "boundingAreaSqm": 1.0},
                {"id": "logo", "name": "logo", "perimeterMl": 2.0, "boundingAreaSqm": 0.4},
            ],
            "parts": {
                "items": [
                    _part("face-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=600),
                    _part("logo-a", layer="logo", x=0, y=300, width=100, height=100, outer_mm=200),
                ],
            },
        }
        layer_setup = _layer_setup(("face-layer", "face"), ("logo", "printed_artwork"))
        finish_setup = {
            "illuminated": True,
            "artwork_finishes": [
                {
                    "layer_key": "logo",
                    "layer_name": "logo",
                    "execution_type": "needs_decision",
                    "return_finish_type": "standard_aluminum",
                    "return_depth_mm": 60,
                }
            ],
        }
        from services.intake_v4_volumetric_return_metrics_service import enrich_quote_geometry_with_volumetric_return

        quote = enrich_quote_geometry_with_volumetric_return(
            build_quote_geometry_from_analysis(analysis, layer_setup),
            finish_setup=finish_setup,
            svg_analysis_json=analysis,
            layer_role_setup=layer_setup,
        )
        assert quote["led_perimeter_ml"] == 0.6
        assert quote["return_material_perimeter_ml"] == 0.8

    def test_material_breakdown_includes_artwork_return_when_active(self):
        from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown

        payload = {
            "schema_version": "1.0.0",
            "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
            "svg_analysis_json": {
                "layers": [
                    {"id": "face-layer", "name": "face-layer", "perimeterMl": 6.0, "filledAreaSqm": 1.0},
                    {"id": "logo", "name": "logo", "perimeterMl": 2.0, "filledAreaSqm": 0.4},
                ],
                "parts": {
                    "items": [
                        _part("face-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=600),
                        _part("logo-a", layer="logo", x=0, y=300, width=100, height=100, outer_mm=200),
                    ]
                },
            },
            "layer_role_setup": {
                "confirmation_status": "complete",
                "layers": [
                    {"layer_key": "face-layer", "confirmed_role": "face", "confirmation_state": "confirmed"},
                    {"layer_key": "logo", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
                ],
            },
            "finish_setup": {
                "confirmed": True,
                "illuminated": False,
                "return_finish_type": "standard_aluminum",
                "return_depth_mm": 60,
                "letter_group_finishes": [
                    {
                        "group_key": "face-layer",
                        "layer_name": "face-layer",
                        "face_finish_type": "none",
                        "return_finish_type": "standard_aluminum",
                        "return_depth_mm": 60,
                        "face_area_m2": 1.0,
                        "perimeter_m": 6.0,
                    }
                ],
                "artwork_finishes": [
                    {
                        "layer_key": "logo",
                        "layer_name": "logo",
                        "execution_type": "needs_decision",
                        "return_finish_type": "standard_aluminum",
                        "return_depth_mm": 60,
                        "estimated_area_m2": 0.4,
                    }
                ],
            },
            "quote_geometry": {},
        }
        result = build_intake_v4_material_breakdown("ws-art-return", payload)
        ret = next(row for row in result.material_rows if row.material_key == "return_material")
        assert ret.quantity == pytest.approx(0.8, rel=1e-3)
        assert "artwork" in ret.display_name.lower()

    def test_material_breakdown_splits_return_when_depth_differs(self):
        from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown

        payload = {
            "schema_version": "1.0.0",
            "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
            "svg_analysis_json": {
                "layers": [
                    {"id": "face-layer", "name": "face-layer", "perimeterMl": 6.0, "filledAreaSqm": 1.0},
                    {"id": "logo", "name": "logo", "perimeterMl": 2.0, "filledAreaSqm": 0.4},
                ],
                "parts": {
                    "items": [
                        _part("face-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=600),
                        _part("logo-a", layer="logo", x=0, y=300, width=100, height=100, outer_mm=200),
                    ]
                },
            },
            "layer_role_setup": {
                "confirmation_status": "complete",
                "layers": [
                    {"layer_key": "face-layer", "confirmed_role": "face", "confirmation_state": "confirmed"},
                    {"layer_key": "logo", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
                ],
            },
            "finish_setup": {
                "confirmed": True,
                "return_finish_type": "standard_aluminum",
                "return_depth_mm": 60,
                "letter_group_finishes": [
                    {
                        "group_key": "face-layer",
                        "layer_name": "face-layer",
                        "return_finish_type": "standard_aluminum",
                        "return_depth_mm": 60,
                        "face_area_m2": 1.0,
                        "perimeter_m": 6.0,
                    }
                ],
                "artwork_finishes": [
                    {
                        "layer_key": "logo",
                        "layer_name": "logo",
                        "execution_type": "needs_decision",
                        "return_finish_type": "standard_aluminum",
                        "return_depth_mm": 80,
                        "estimated_area_m2": 0.4,
                    }
                ],
            },
            "quote_geometry": {},
        }
        result = build_intake_v4_material_breakdown("ws-art-split", payload)
        keys = {row.material_key for row in result.material_rows}
        assert "return_material" in keys
        assert "artwork_return_logo" in keys

    def test_led_and_letter_count_use_real_letters_only(self):
        analysis = {
            "parts": {
                "count": 3,
                "nestableCount": 3,
                "items": [
                    _part("face-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=500),
                    _part("face-b", layer="face-layer", x=300, y=0, width=200, height=200, outer_mm=500),
                    _part("hole-orphan", layer="face-layer", x=50, y=50, width=30, height=30, outer_mm=120),
                ],
            }
        }
        quote = build_quote_geometry_from_analysis(analysis, _layer_setup(("face-layer", "face")))
        assert quote["real_letters_count"] == 2
        assert quote["inner_holes_count"] == 1

    def test_material_piece_count_excludes_holes(self):
        analysis = {
            "parts": {
                "items": [
                    _part("face-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=500, inner_mm=80, inner_count=1),
                    _part("hole-orphan", layer="face-layer", x=50, y=50, width=30, height=30, outer_mm=120),
                ]
            }
        }
        result = classify_letter_parts_from_analysis(analysis, _layer_setup(("face-layer", "face")))
        assert result["material_piece_count"] == 1
        assert result["inner_holes_count"] == 2

    def test_metrics_expose_real_letters_inner_holes_cutting_contours(self):
        analysis = {
            "parts": {
                "items": [
                    _part("face-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=500, inner_mm=80, inner_count=1, contour_count=2),
                ]
            }
        }
        quote = build_quote_geometry_from_analysis(analysis, _layer_setup(("face-layer", "face")))
        assert quote["real_letters_count"] == 1
        assert quote["inner_holes_count"] == 1
        assert quote["cutting_contours_count"] == 2
        assert quote["material_piece_count"] == 1

    def test_pbl_like_multi_layer_excludes_artwork_from_pieces(self):
        analysis = {
            "layers": [
                {"id": "art", "name": "art-layer", "perimeterMl": 1.0, "boundingAreaSqm": 0.2},
                {"id": "face-a", "name": "face-a", "perimeterMl": 6.0, "boundingAreaSqm": 1.0},
                {"id": "face-b", "name": "face-b", "perimeterMl": 7.0, "boundingAreaSqm": 1.1},
            ],
            "parts": {
                "count": 11,
                "nestableCount": 11,
                "items": [
                    _part("art-1", layer="art-layer", x=0, y=0, width=100, height=100, outer_mm=400, can_nest=True),
                    *[
                        _part(f"face-a-{index}", layer="face-a", x=index * 120, y=0, width=100, height=100, outer_mm=500)
                        for index in range(5)
                    ],
                    *[
                        _part(f"face-b-{index}", layer="face-b", x=index * 120, y=200, width=100, height=100, outer_mm=500)
                        for index in range(5)
                    ],
                ],
            },
        }
        layer_setup = _layer_setup(
            ("art-layer", "printed_artwork"),
            ("face-a", "face"),
            ("face-b", "face"),
        )
        quote = build_quote_geometry_from_analysis(analysis, layer_setup)
        assert quote["letter_count"] == 10
        assert quote["real_letters_count"] == 10
        assert quote["inner_holes_count"] == 0

    def test_no_execution_plan_or_tasks_json_side_effects(self):
        payload = IntakeV4WorkspacePayload(
            client=IntakeV4ClientRequest(),
            product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
            finish_setup=IntakeV4FinishSetup(confirmed=True, illuminated=False),
            svg_analysis_json={
                "parts": {
                    "items": [
                        _part("face-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=500),
                    ]
                }
            },
            layer_role_setup=IntakeV4LayerRoleSetup(
                confirmation_status="complete",
                layers=[{"layer_key": "face-layer", "confirmed_role": "face", "confirmation_state": "confirmed"}],
            ),
        )
        workspace = build_v3_workspace_from_v4_payload(payload)
        dumped = workspace.model_dump(mode="json")
        assert "execution_plan" not in dumped
        assert "tasks_json" not in dumped

    def test_pricing_preview_uses_classified_counts(self):
        payload = IntakeV4WorkspacePayload(
            client=IntakeV4ClientRequest(),
            product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
            finish_setup=IntakeV4FinishSetup(
                confirmed=True,
                illuminated=False,
                face_finish_type="oracal_651",
                return_finish_type="standard_aluminum",
                return_depth_mm=60,
            ),
            svg_analysis_json={
                "layers": [{"id": "face-layer", "name": "face-layer", "perimeterMl": 2.0, "boundingAreaSqm": 1.0}],
                "parts": {
                    "count": 2,
                    "nestableCount": 2,
                    "items": [
                        _part("face-a", layer="face-layer", x=0, y=0, width=200, height=200, outer_mm=800, inner_mm=100, inner_count=1, contour_count=2),
                        _part("hole-orphan", layer="face-layer", x=50, y=50, width=30, height=30, outer_mm=120),
                    ],
                },
            },
            layer_role_setup=IntakeV4LayerRoleSetup(
                confirmation_status="complete",
                layers=[{"layer_key": "face-layer", "confirmed_role": "face", "confirmation_state": "confirmed"}],
            ),
            quote_geometry={},
        )
        preview = build_v4_pricing_input_preview(workspace_id="ws-classify", payload=payload)
        assert preview.production_counts["letter_count"] == 1
        assert preview.production_counts["inner_hole_count"] == 2
        assert preview.production_counts["cut_contour_count"] == 3
        assert preview.quote_input_payload["letter_count"] == 1
