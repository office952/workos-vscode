"""Quote geometry derivation for Intake V4."""

from __future__ import annotations

from services.intake_v4_quote_geometry_service import (
    build_quote_geometry_from_analysis,
    merge_quote_geometry_into_path_summary,
)


class TestIntakeV4QuoteGeometry:
    def test_build_quote_geometry_sums_face_layers(self):
        analysis = {
            "document": {"widthMm": 3000, "heightMm": 1000},
            "geometry": {"perimeterMl": 50},
            "layers": [
                {"id": "l1", "name": "litere-volumetrice-1", "perimeterMl": 12.5, "boundingAreaSqm": 1.2},
                {"id": "l2", "name": "litere-volumetrice-2", "perimeterMl": 8.0, "boundingAreaSqm": 0.8},
                {"id": "logo", "name": "logo", "perimeterMl": 99, "boundingAreaSqm": 9},
            ],
            "parts": {"count": 12, "nestableCount": 10},
        }
        layer_setup = {
            "confirmation_status": "complete",
            "layers": [
                {"layer_key": "l1", "confirmed_role": "face", "confirmation_state": "confirmed"},
                {"layer_key": "l2", "confirmed_role": "face", "confirmation_state": "confirmed"},
                {"layer_key": "logo", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
            ],
        }
        quote = build_quote_geometry_from_analysis(analysis, layer_setup)
        assert quote["letter_perimeter_m"] == 20.5
        assert quote["face_area_m2"] == 2.0
        assert quote["artwork_area_m2"] == 9.0
        assert quote["geometry_source"] == "nest2_face_layers"
        assert quote["letter_count"] == 10

    def test_merge_into_path_summary(self):
        merged = merge_quote_geometry_into_path_summary(
            {"parse_status": "parsed"},
            {"letter_perimeter_m": 20.5, "face_area_m2": 2.0, "letter_count": 10},
        )
        assert merged["letter_perimeter_m"] == 20.5
        assert merged["face_area_m2"] == 2.0
        assert merged["letter_count"] == 10
