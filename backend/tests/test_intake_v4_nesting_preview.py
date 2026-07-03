"""Intake V4 nesting preview diagnostic — read-only, does not alter material totals."""

from __future__ import annotations

from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown
from services.intake_v4_nesting_preview_service import build_intake_v4_nesting_preview


def _payload_with_nesting_placements() -> dict:
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
        "svg_analysis_json": {
            "nesting": {
                "sheets": [
                    {
                        "configId": "sheet_3000x2000",
                        "sheetsUsed": 1,
                        "usedSheetAreaSqm": 6.0,
                        "efficiencyPercent": 13.0,
                        "placedItemsCount": 2,
                        "placements": [
                            {
                                "partId": "face-a",
                                "sourceLayerName": "L2",
                                "xMm": 10,
                                "yMm": 20,
                                "placedWidthMm": 500,
                                "placedHeightMm": 400,
                            },
                            {
                                "partId": "art-a",
                                "sourceLayerName": "L1",
                                "xMm": 600,
                                "yMm": 20,
                                "placedWidthMm": 300,
                                "placedHeightMm": 200,
                            },
                        ],
                    },
                    {
                        "configId": "sheet_1300x900",
                        "sheetsUsed": 1,
                        "usedSheetAreaSqm": 1.17,
                        "efficiencyPercent": 0,
                        "placedItemsCount": 0,
                    },
                ],
                "rolls": [
                    {
                        "rollWidthMm": 1000,
                        "jobs": [
                            {
                                "sourceLayerName": "L2",
                                "colorKey": "#009846",
                                "usedRollAreaSqm": 0.54,
                                "placedItemsCount": 1,
                            }
                        ],
                    },
                    {
                        "rollWidthMm": 1260,
                        "jobs": [
                            {
                                "sourceLayerName": "L2",
                                "colorKey": "#009846",
                                "usedRollAreaSqm": 0.50,
                                "placedItemsCount": 1,
                            }
                        ],
                    },
                ],
            },
            "parts": {
                "items": [
                    {"id": "face-a", "source": {"layerId": "L2", "layerName": "L2"}},
                    {"id": "art-a", "source": {"layerId": "L1", "layerName": "L1"}},
                ]
            },
            "layers": [],
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {"layer_key": "L1", "layer_name": "L1", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
                {"layer_key": "L2", "layer_name": "L2", "confirmed_role": "face", "confirmation_state": "confirmed"},
            ],
        },
        "quote_geometry": {"face_area_m2": 0.2, "return_material_perimeter_ml": 1.0},
        "path_geometry_summary": {"face_area_m2": 0.2, "return_material_perimeter_ml": 1.0},
        "finish_setup": {
            "face_finish_type": "oracal_651",
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 60,
            "confirmed": True,
            "illuminated": False,
        },
    }


class TestIntakeV4NestingPreview:
    def test_preview_includes_part_role_and_material_trace(self):
        payload = _payload_with_nesting_placements()
        breakdown = build_intake_v4_material_breakdown("ws-preview", payload)
        preview = breakdown.nesting_preview
        assert preview is not None
        assert preview.breakdown_uses_single_active_layout is True
        assert preview.active_sheet_config_id == "sheet_3000x2000"

        active_sheets = [s for s in preview.sheets if s.is_active_for_breakdown]
        alt_sheets = [s for s in preview.sheets if not s.is_active_for_breakdown]
        assert len(active_sheets) == 1
        assert len(alt_sheets) >= 1
        assert alt_sheets[0].layout_kind == "alternative_variant"

        face_part = next(p for p in preview.parts if p.part_id == "face-a")
        art_part = next(p for p in preview.parts if p.part_id == "art-a")
        assert face_part.layer_role == "face"
        assert "plexiglas_face" in face_part.counted_in_material_lines
        assert art_part.layer_role == "printed_artwork"
        assert "plexiglas_face" not in art_part.counted_in_material_lines

        plexi_trace = next(t for t in preview.material_traces if t.material_key == "plexiglas_face")
        assert "face-a" in plexi_trace.source_part_ids
        assert "art-a" not in plexi_trace.source_part_ids
        assert plexi_trace.uses_placement_footprint is True
        assert plexi_trace.uses_full_sheet_stock_proration is False

    def test_preview_boundary_flags_read_only(self):
        payload = _payload_with_nesting_placements()
        breakdown = build_intake_v4_material_breakdown("ws-boundary", payload)
        preview = breakdown.nesting_preview
        assert preview is not None
        assert preview.preview_only is True
        assert preview.mutates_inventory is False
        assert preview.uses_stock is False
        assert preview.boundary.creates_execution_plan is False
        assert preview.boundary.consumes_stock is False
        assert preview.summary.sheet_layouts >= 1
        assert preview.summary.alternative_layouts >= 1

    def test_preview_does_not_change_material_totals(self):
        payload = _payload_with_nesting_placements()
        breakdown = build_intake_v4_material_breakdown("ws-preview-totals", payload)
        plexi = next(r for r in breakdown.material_rows if r.material_key == "plexiglas_face")
        standalone = build_intake_v4_nesting_preview(
            payload,
            workspace_id="ws-preview-totals",
            material_rows=breakdown.material_rows,
            face_area=0.2,
            backing_area=None,
        )
        assert breakdown.nesting_preview is not None
        assert standalone.material_traces[0].reported_quantity == plexi.quantity

    def test_artwork_on_sheet_not_counted_in_plexiglas_face_quantity(self):
        payload = _payload_with_nesting_placements()
        breakdown = build_intake_v4_material_breakdown("ws-art-sheet", payload)
        plexi = next(r for r in breakdown.material_rows if r.material_key == "plexiglas_face")
        # Only face-a footprint (500×400mm = 0.2 m²), not artwork 300×200mm.
        assert plexi.quantity == 0.2
        preview = breakdown.nesting_preview
        assert preview is not None
        art_parts = [p for p in preview.parts if p.part_id == "art-a"]
        if art_parts:
            assert art_parts[0].part_kind == "artwork_part"

    def test_roll_jobs_mark_active_vs_alternative_width(self):
        payload = _payload_with_nesting_placements()
        breakdown = build_intake_v4_material_breakdown("ws-preview", payload)
        preview = breakdown.nesting_preview
        assert preview is not None
        l2_jobs = [j for j in preview.rolls if j.source_layer_name == "L2"]
        assert len(l2_jobs) == 2
        active = [j for j in l2_jobs if j.is_active_for_breakdown]
        assert len(active) == 1
        assert active[0].used_roll_area_sqm == 0.5
