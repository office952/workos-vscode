"""Piece-based face vinyl nesting — ml/mp separation and fallback marking.

Pricing contract: rate = 5 EUR/mp; quantity_m2 = recommended_roll_length_m × material_width_m;
labor line (EUR) = quantity_m2 × rate — never multiply ml by rate directly.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.face_vinyl_piece_nesting import (  # noqa: E402
    FaceVinylPiece,
    estimate_piece_based_rectangular_nesting,
)
from services.volumetric_face_vinyl_service import (  # noqa: E402
    build_face_vinyl_task_instructions,
    collect_nesting_pieces,
    estimate_face_vinyl_nesting,
    resolve_face_vinyl_used_sqm,
    NestingPiece,
)


def _face_vinyl_qi(**overrides):
    base = {
        "face_finish_type": "oracal_651",
        "face_vinyl_color_code": "651-020",
        "face_vinyl_color_name": "Golden yellow",
        "face_vinyl_roll_width_mm": 1260,
        "letter_face_area_m2": 1.466571,
        "width_mm": 4800,
        "height_mm": 600,
        "mounting_system": "direct_wall",
    }
    base.update(overrides)
    return base


def _four_letter_pieces():
    return [
        {"piece_id": "L1", "label": "A", "width_mm": 600, "height_mm": 400},
        {"piece_id": "L2", "label": "B", "width_mm": 600, "height_mm": 400},
        {"piece_id": "L3", "label": "C", "width_mm": 600, "height_mm": 400},
        {"piece_id": "L4", "label": "D", "width_mm": 600, "height_mm": 400},
    ]


class TestMlMpSeparation(unittest.TestCase):
    def test_recommended_roll_length_is_ml_not_m2(self) -> None:
        res = resolve_face_vinyl_used_sqm(
            _face_vinyl_qi(letter_bounding_boxes=_four_letter_pieces())
        )
        self.assertEqual(res.source, "nesting")
        self.assertFalse(res.fallback_weak_estimate)
        self.assertIsNotNone(res.recommended_roll_length_m)
        self.assertIsNotNone(res.material_width_m)
        self.assertAlmostEqual(res.material_width_m or 0, 1.26, places=2)
        # 4×600×400 on 1260 roll → ~0.8 m nested × 1.10 waste ≈ 0.88 ml
        self.assertLess(res.recommended_roll_length_m or 999, 2.0)
        expected_m2 = round((res.recommended_roll_length_m or 0) * (res.material_width_m or 0), 4)
        self.assertAlmostEqual(res.value or 0, expected_m2, places=4)
        quantity_m2 = res.value or 0
        labor_eur = quantity_m2 * 5.0  # rate 5 EUR/mp → labor line in EUR
        self.assertNotAlmostEqual(labor_eur, (res.recommended_roll_length_m or 0) * 5.0, places=1)

    def test_explicit_numeric_example(self) -> None:
        pieces = [FaceVinylPiece(piece_id="x", width_mm=500, height_mm=400, source="test")]
        raw = estimate_piece_based_rectangular_nesting(
            pieces,
            roll_width_mm=1260,
            nesting_source="letter_bounding_boxes",
            apply_internal_waste=False,
        )
        self.assertAlmostEqual(raw.nested_roll_length_m or 0, 0.4, places=2)
        raw_waste = estimate_piece_based_rectangular_nesting(
            pieces,
            roll_width_mm=1260,
            nesting_source="letter_bounding_boxes",
            apply_internal_waste=True,
        )
        self.assertAlmostEqual(raw_waste.recommended_roll_length_m or 0, 0.44, places=2)
        self.assertAlmostEqual(raw_waste.material_width_m or 0, 1.26, places=2)
        self.assertAlmostEqual(raw_waste.quantity_m2 or 0, round(0.44 * 1.26, 4), places=3)
        labor_eur = (raw_waste.quantity_m2 or 0) * 5  # rate 5 EUR/mp → labor line EUR
        self.assertAlmostEqual(labor_eur, round(0.44 * 1.26 * 5, 2), places=2)


class TestPieceBasedBeatsAssemblyBbox(unittest.TestCase):
    def test_piece_nesting_shorter_than_single_assembly_bbox(self) -> None:
        piece_qi = _face_vinyl_qi(letter_bounding_boxes=_four_letter_pieces())
        assembly_qi = _face_vinyl_qi(width_mm=2400, height_mm=400)

        piece_pieces, piece_src = collect_nesting_pieces(piece_qi)
        asm_pieces, asm_src = collect_nesting_pieces(assembly_qi)

        self.assertEqual(piece_src, "letter_bounding_boxes")
        self.assertEqual(asm_src, "assembly_bbox")

        piece_nest = estimate_face_vinyl_nesting(
            piece_pieces, roll_width_mm=1260, nesting_source=piece_src
        )
        asm_nest = estimate_face_vinyl_nesting(
            asm_pieces, roll_width_mm=1260, nesting_source=asm_src
        )

        self.assertEqual(piece_nest.nesting_method, "piece_based_rectangular")
        self.assertFalse(piece_nest.is_fallback)
        self.assertEqual(asm_nest.nesting_method, "fallback_weak_estimate")
        self.assertTrue(asm_nest.is_fallback)
        self.assertGreater(len(piece_nest.placements), 1)
        self.assertLess(
            piece_nest.nested_roll_length_m or 0,
            asm_nest.nested_roll_length_m or 0,
        )

    def test_rotation_90_helps_narrow_roll(self) -> None:
        pieces = [NestingPiece(width_mm=1300, height_mm=400, piece_id="p1")]
        with_rot = estimate_face_vinyl_nesting(
            pieces, roll_width_mm=1260, rotation_allowed=True, nesting_source="letter_bounding_boxes"
        )
        without_rot = estimate_face_vinyl_nesting(
            pieces,
            roll_width_mm=1260,
            rotation_allowed=False,
            nesting_source="letter_bounding_boxes",
        )
        self.assertFalse(with_rot.oversized_piece)
        self.assertTrue(without_rot.oversized_piece)


class TestFallbackExplicit(unittest.TestCase):
    def test_assembly_bbox_marked_fallback(self) -> None:
        res = resolve_face_vinyl_used_sqm(_face_vinyl_qi())
        self.assertEqual(res.source, "nesting")
        self.assertTrue(res.fallback_weak_estimate)

    def test_no_geometry_uses_face_area_fallback(self) -> None:
        qi = _face_vinyl_qi()
        qi.pop("width_mm")
        qi.pop("height_mm")
        res = resolve_face_vinyl_used_sqm(qi)
        self.assertEqual(res.source, "fallback_face_area")
        self.assertTrue(res.fallback_weak_estimate)


class TestEmployeeMobileInstructionsClean(unittest.TestCase):
    _FORBIDDEN = (
        "nu pe cant",
        "10% rezervă",
        "10% rezerva",
        "assembly_bbox",
        "fallback_weak_estimate",
        "suprafață minim teoretic",
        "minim teoretic",
        "metodă estimare",
        "metoda estimare",
        "ml ×",
        "Nesting estimativ",
    )

    def test_piece_based_instructions_operator_friendly(self) -> None:
        text = build_face_vinyl_task_instructions(
            _face_vinyl_qi(letter_bounding_boxes=_four_letter_pieces())
        )
        lowered = text.lower()
        for forbidden in self._FORBIDDEN:
            self.assertNotIn(forbidden.lower(), lowered, msg=forbidden)
        self.assertIn("Colantezi fețele din plexiglas", text)
        self.assertIn("Material autocolant:", text)
        self.assertIn("651-020", text)
        self.assertIn("Lățime rolă: 1260 mm", text)
        self.assertIn("Lungime pregătire:", text)
        self.assertIn("Nesting: calculat pe piesele literelor", text)
        self.assertIn("PAȘI DE LUCRU", text)

    def test_fallback_instructions_neutral_length_label(self) -> None:
        text = build_face_vinyl_task_instructions(_face_vinyl_qi())
        lowered = text.lower()
        for forbidden in self._FORBIDDEN:
            self.assertNotIn(forbidden.lower(), lowered, msg=forbidden)
        self.assertIn("Material estimat pentru pregătire:", text)
        self.assertNotIn("Nesting: calculat pe piesele literelor", text)


if __name__ == "__main__":
    unittest.main()
