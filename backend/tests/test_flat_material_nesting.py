"""Tests for generic flat-material nesting foundation (roll + sheet adapters)."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.face_vinyl_piece_nesting import (  # noqa: E402
    FaceVinylPiece,
    estimate_piece_based_rectangular_nesting,
)
from services.flat_material_nesting import (  # noqa: E402
    FlatPiece,
    RollMaterialProfile,
    SheetMaterialProfile,
    estimate_roll_rectangular_nesting,
    estimate_sheet_rectangular_nesting,
    expand_flat_pieces,
    flat_pieces_from_bounding_boxes,
)
from services.volumetric_plexiglass_face_nesting_service import (  # noqa: E402
    build_plexiglass_face_nesting_block,
    estimate_plexiglass_face_sheet_nesting,
)
from services.work_intake_svg_spec_mapper import build_vector_spec_updates  # noqa: E402
from services.svg_layer_analysis_service import SvgLayerAnalysisService  # noqa: E402

_FOUR_LETTER_RECTS_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="1220mm" height="810mm" viewBox="0 0 1220 810">
  <g id="Litere" inkscape:label="TPL-VOLUMETRIC-LETTERS"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     inkscape:groupmode="layer">
    <rect x="0" y="0" width="600" height="400"/>
    <rect x="610" y="0" width="600" height="400"/>
    <rect x="0" y="410" width="600" height="400"/>
    <rect x="610" y="410" width="600" height="400"/>
  </g>
</svg>
""".strip()


def _four_pieces() -> list[FlatPiece]:
    return [
        FlatPiece(piece_id=f"L{i}", width_mm=600, height_mm=400, label=chr(64 + i))
        for i in range(1, 5)
    ]


class TestGenericFlatPieceModel(unittest.TestCase):
    def test_flat_piece_has_geometry_only(self) -> None:
        piece = FlatPiece(piece_id="a", width_mm=520, height_mm=400, label="M")
        self.assertEqual(piece.width_mm, 520)
        self.assertEqual(piece.height_mm, 400)
        self.assertFalse(hasattr(piece, "recommended_roll_length_m"))
        d = piece.__dict__ if hasattr(piece, "__dict__") else {}
        for forbidden in (
            "recommended_roll_length_m",
            "quantity_m2",
            "sheets_used",
            "nested_roll_length_m",
        ):
            self.assertNotIn(forbidden, d)

    def test_quantity_expands_to_individual_pieces(self) -> None:
        expanded = expand_flat_pieces(
            [FlatPiece(piece_id="x", width_mm=100, height_mm=50, quantity=3)]
        )
        self.assertEqual(len(expanded), 3)
        self.assertEqual(expanded[0].piece_id, "x_1")
        self.assertEqual(expanded[2].piece_id, "x_3")

    def test_bounding_boxes_to_flat_pieces(self) -> None:
        boxes = [
            {"piece_id": "a", "width_mm": 600, "height_mm": 400, "source": "svg_layer_mapped"},
            {"piece_id": "b", "width_mm": 600, "height_mm": 400, "quantity": 2},
        ]
        pieces = flat_pieces_from_bounding_boxes(boxes)
        self.assertEqual(len(pieces), 2)
        self.assertEqual(pieces[1].quantity, 2)


class TestRollAdapterKeepsVinylBehavior(unittest.TestCase):
    def test_roll_result_has_ml_not_sheets(self) -> None:
        vinyl_pieces = [
            FaceVinylPiece(piece_id=f"L{i}", width_mm=600, height_mm=400) for i in range(4)
        ]
        res = estimate_piece_based_rectangular_nesting(
            vinyl_pieces,
            roll_width_mm=1260,
            nesting_source="letter_bounding_boxes",
        )
        self.assertIsNotNone(res.nested_roll_length_m)
        self.assertIsNotNone(res.recommended_roll_length_m)
        self.assertIsNotNone(res.quantity_m2)
        self.assertAlmostEqual(res.material_width_m or 0, 1.26, places=2)
        self.assertFalse(hasattr(res, "sheets_used"))
        d = res.__dict__
        self.assertNotIn("sheets_used", d)
        self.assertNotIn("sheet_width_mm", d)

    def test_numeric_vinyl_example(self) -> None:
        res = estimate_piece_based_rectangular_nesting(
            [FaceVinylPiece(piece_id=f"L{i}", width_mm=600, height_mm=400) for i in range(4)],
            roll_width_mm=1260,
            nesting_source="letter_bounding_boxes",
        )
        self.assertAlmostEqual(res.nested_roll_length_m or 0, 0.80, places=1)
        self.assertAlmostEqual(res.recommended_roll_length_m or 0, 0.88, places=1)
        qty = res.quantity_m2 or 0
        self.assertAlmostEqual(qty, 1.1088, places=3)
        labor_eur = qty * 5.0
        self.assertAlmostEqual(labor_eur, 5.544, places=2)


class TestSheetAdapterPlexiglas(unittest.TestCase):
    def test_four_pieces_one_sheet(self) -> None:
        res = estimate_sheet_rectangular_nesting(
            _four_pieces(),
            sheet_width_mm=3050,
            sheet_height_mm=2030,
            spacing_mm=10,
        )
        self.assertEqual(res.material_type, "sheet")
        self.assertEqual(res.nesting_method, "sheet_rectangular")
        self.assertEqual(res.sheets_used, 1)
        self.assertGreater(len(res.placements), 0)
        self.assertIsNone(getattr(res, "nested_roll_length_m", None))
        self.assertIsNone(getattr(res, "recommended_roll_length_m", None))
        self.assertAlmostEqual(res.allocated_sheet_area_m2 or 0, 3050 * 2030 / 1_000_000, places=4)
        self.assertAlmostEqual(res.used_piece_bbox_area_m2 or 0, 4 * 600 * 400 / 1_000_000, places=4)
        waste = (res.allocated_sheet_area_m2 or 0) - (res.used_piece_bbox_area_m2 or 0)
        self.assertAlmostEqual(res.waste_area_m2 or 0, waste, places=4)
        if res.allocated_sheet_area_m2:
            self.assertAlmostEqual(
                res.waste_percent or 0,
                round(100.0 * waste / res.allocated_sheet_area_m2, 2),
                places=1,
            )
        for p in res.placements:
            self.assertEqual(p.sheet_index, 0)

    def test_multiple_sheets(self) -> None:
        many = [
            FlatPiece(piece_id=f"p{i}", width_mm=600, height_mm=400)
            for i in range(12)
        ]
        res = estimate_sheet_rectangular_nesting(
            many,
            sheet_width_mm=1000,
            sheet_height_mm=1000,
            spacing_mm=10,
        )
        self.assertGreater(res.sheets_used, 1)
        indices = {p.sheet_index for p in res.placements}
        self.assertGreater(len(indices), 1)
        self.assertAlmostEqual(
            res.allocated_sheet_area_m2 or 0,
            res.sheets_used * 1000 * 1000 / 1_000_000,
            places=4,
        )

    def test_rotation_90_places_piece(self) -> None:
        res = estimate_sheet_rectangular_nesting(
            [FlatPiece(piece_id="wide", width_mm=2800, height_mm=1900)],
            sheet_width_mm=2000,
            sheet_height_mm=3050,
            rotation_allowed=True,
        )
        self.assertEqual(res.sheets_used, 1)
        self.assertEqual(len(res.unplaceable_pieces), 0)
        self.assertEqual(res.placements[0].rotation_deg, 90)
        self.assertAlmostEqual(res.placements[0].width_mm, 1900, places=0)
        self.assertAlmostEqual(res.placements[0].height_mm, 2800, places=0)

    def test_unplaceable_piece_reported(self) -> None:
        res = estimate_sheet_rectangular_nesting(
            [FlatPiece(piece_id="huge", width_mm=4000, height_mm=3000)],
            sheet_width_mm=3050,
            sheet_height_mm=2030,
        )
        self.assertIn("huge", res.unplaceable_pieces)
        self.assertEqual(res.sheets_used, 0)
        self.assertEqual(len(res.placements), 0)


class TestRollVsSheetFieldSeparation(unittest.TestCase):
    def test_roll_has_no_sheet_fields(self) -> None:
        res = estimate_roll_rectangular_nesting(
            _four_pieces(),
            roll_width_mm=1260,
        )
        d = res.__dict__
        for key in (
            "sheets_used",
            "sheet_width_mm",
            "sheet_height_mm",
            "allocated_sheet_area_m2",
        ):
            self.assertNotIn(key, d)

    def test_sheet_has_no_roll_fields(self) -> None:
        res = estimate_sheet_rectangular_nesting(
            _four_pieces(),
            sheet_width_mm=3050,
            sheet_height_mm=2030,
        )
        d = res.__dict__
        for key in (
            "nested_roll_length_m",
            "recommended_roll_length_m",
            "material_width_m",
            "roll_width_mm",
            "quantity_m2",
        ):
            self.assertNotIn(key, d)


class TestSamePiecesFeedRollAndSheet(unittest.TestCase):
    def test_svg_boxes_feed_both_adapters(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_FOUR_LETTER_RECTS_SVG)
        product_spec = build_vector_spec_updates(
            filename="four-letters.svg",
            size_bytes=100,
            content_type="image/svg+xml",
            svg_text=_FOUR_LETTER_RECTS_SVG,
            analysis=analysis,
        )
        boxes = product_spec["letter_bounding_boxes"]
        flat = flat_pieces_from_bounding_boxes(boxes)

        roll = estimate_roll_rectangular_nesting(flat, roll_width_mm=1260)
        sheet = estimate_sheet_rectangular_nesting(
            flat, sheet_width_mm=3050, sheet_height_mm=2030
        )

        self.assertEqual(roll.pieces_count, 4)
        self.assertEqual(sheet.pieces_count, 4)
        self.assertIsNotNone(roll.nested_roll_length_m)
        self.assertIsNotNone(sheet.sheets_used)
        self.assertGreater(len(roll.placements), 0)
        self.assertGreater(len(sheet.placements), 0)
        self.assertNotIn("nested_roll_length_m", sheet.__dict__)

    def test_plexiglass_block_from_product_spec(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_FOUR_LETTER_RECTS_SVG)
        product_spec = build_vector_spec_updates(
            filename="four-letters.svg",
            size_bytes=100,
            content_type="image/svg+xml",
            svg_text=_FOUR_LETTER_RECTS_SVG,
            analysis=analysis,
        )
        block = build_plexiglass_face_nesting_block(product_spec)
        self.assertTrue(block["enabled"])
        nesting = block["nesting"]
        self.assertEqual(nesting["method"], "sheet_rectangular")
        self.assertEqual(nesting["material_type"], "sheet")
        self.assertEqual(nesting["sheets_used"], 1)
        self.assertNotIn("nested_roll_length_m", nesting)
        self.assertNotIn("recommended_roll_length_m", nesting)

    def test_plexiglass_service_numeric_example(self) -> None:
        spec = {
            "letter_bounding_boxes": [
                {"piece_id": f"L{i}", "width_mm": 600, "height_mm": 400}
                for i in range(4)
            ]
        }
        res = estimate_plexiglass_face_sheet_nesting(spec)
        self.assertEqual(res.sheets_used, 1)
        self.assertAlmostEqual(res.sheet_width_mm or 0, 3050, places=0)
        self.assertAlmostEqual(res.sheet_height_mm or 0, 2030, places=0)
        self.assertAlmostEqual(res.allocated_sheet_area_m2 or 0, 6.1915, places=3)
        self.assertAlmostEqual(res.used_piece_bbox_area_m2 or 0, 0.96, places=3)


if __name__ == "__main__":
    unittest.main()
