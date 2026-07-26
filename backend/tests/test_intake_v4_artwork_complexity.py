"""Artwork complexity classification preview — material breakdown integration."""

from __future__ import annotations

from services.intake_v4_artwork_complexity_service import (
    effective_artwork_application,
    list_artwork_complexity_assessments,
)
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown


def _payload_with_artwork_complexity(
    assessments: list[dict],
    decisions: list[dict] | None = None,
) -> dict:
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS_v2"},
        "svg_analysis_json": {
            "schemaVersion": "1.11.0",
            "artworkComplexity": {
                "assessments": assessments,
                "has_raster_over_vector": True,
                "default_recommended_application": "print_on_vinyl_laminated",
            },
            "layers": [],
        },
        "quote_geometry": {
            "letter_perimeter_m": 2.0,
            "face_area_m2": 0.5,
            "backing_area_m2": 0.5,
            "return_material_perimeter_ml": 2.0,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_area_m2": 0.5,
            "backing_area_m2": 0.5,
            "return_material_perimeter_ml": 2.0,
        },
        "finish_setup": {
            "face_finish_type": "oracal_651",
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "illuminated": False,
            "letter_group_finishes": [],
            "artwork_complexity_decisions": decisions or [],
            "confirmed": True,
        },
    }


class TestIntakeV4ArtworkComplexity:
    def test_assessment_without_operator_decision_stays_manual_review(self):
        payload = _payload_with_artwork_complexity(
            [
                {
                    "artwork_id": "raster:img1",
                    "recommended_application": "print_on_vinyl_laminated",
                    "artwork_area_estimate_m2": 0.25,
                    "source_layer_name": "maria",
                    "warnings": ["missing_external_image_asset"],
                }
            ]
        )
        result = build_intake_v4_material_breakdown("ws-art", payload)
        print_rows = [
            row
            for row in result.material_rows
            if row.material_key.startswith("artwork_complexity_")
        ]
        assert print_rows == []
        op_keys = {row.key for row in result.operation_rows}
        assert "artwork_complexity_raster_img1_print_vinyl_op" not in op_keys
        assert "artwork_complexity_raster_img1_laminate_op" not in op_keys
        assert any(w.code == "missing_external_image_asset" for w in result.warnings)

    def test_operator_decision_print_laminate_enables_preview_rows(self):
        payload = _payload_with_artwork_complexity(
            [
                {
                    "artwork_id": "raster:img1",
                    "recommended_application": "print_on_vinyl_laminated",
                    "artwork_area_estimate_m2": 0.25,
                    "source_layer_name": "maria",
                }
            ],
            decisions=[
                {
                    "artwork_id": "raster:img1",
                    "operator_application": "print_on_vinyl_laminated",
                }
            ],
        )
        result = build_intake_v4_material_breakdown("ws-art-operator", payload)
        print_rows = [
            row for row in result.material_rows if row.material_key.startswith("artwork_complexity_")
        ]
        assert len(print_rows) == 2
        op_keys = {row.key for row in result.operation_rows}
        assert "artwork_complexity_raster_img1_print_vinyl_op" in op_keys
        assert "artwork_complexity_raster_img1_laminate_op" in op_keys

    def test_operator_override_vinyl_cut_skips_print_rows(self):
        payload = _payload_with_artwork_complexity(
            [
                {
                    "artwork_id": "raster:img1",
                    "recommended_application": "print_on_vinyl_laminated",
                    "artwork_area_estimate_m2": 0.25,
                }
            ],
            decisions=[
                {
                    "artwork_id": "raster:img1",
                    "operator_application": "vinyl_cut",
                    "override_manual_vinyl_cut": True,
                }
            ],
        )
        result = build_intake_v4_material_breakdown("ws-art2", payload)
        assert not any(
            row.material_key.startswith("artwork_complexity_") for row in result.material_rows
        )

    def test_effective_application_prefers_operator_decision(self):
        assessment = {"artwork_id": "raster:img1", "recommended_application": "print_on_vinyl_laminated"}
        operator_map = {"raster:img1": "vinyl_cut"}
        assert effective_artwork_application(assessment, operator_map) == "vinyl_cut"

    def test_effective_application_defaults_to_manual_review_without_operator_choice(self):
        assessment = {"artwork_id": "raster:img1", "recommended_application": "print_on_vinyl_laminated"}
        assert effective_artwork_application(assessment, {}) == "manual_review"

    def test_list_assessments_from_payload(self):
        payload = _payload_with_artwork_complexity(
            [{"artwork_id": "raster:img1", "recommended_application": "manual_review"}]
        )
        rows = list_artwork_complexity_assessments(payload)
        assert len(rows) == 1
        assert rows[0]["artwork_id"] == "raster:img1"
