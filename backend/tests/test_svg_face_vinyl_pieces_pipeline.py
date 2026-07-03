"""SVG → letter_bounding_boxes → piece-based face vinyl nesting pipeline."""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.svg_face_vinyl_pieces_service import (  # noqa: E402
    extract_flat_material_pieces_from_svg,
    extract_letter_bounding_boxes_from_svg,
)
from services.volumetric_face_vinyl_service import (  # noqa: E402
    build_face_vinyl_handoff_for_quote,
    build_face_vinyl_task_instructions,
    collect_nesting_pieces,
    estimate_face_vinyl_nesting,
    resolve_face_vinyl_used_sqm,
)
from services.work_intake_svg_spec_mapper import build_vector_spec_updates  # noqa: E402
from services.svg_layer_analysis_service import SvgLayerAnalysisService  # noqa: E402
from validators.intake_product_spec import validate_intake_product_spec  # noqa: E402

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

_PATH_LETTERS_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="100mm" viewBox="0 0 200 100">
  <g id="layer-letters" inkscape:label="TPL-VOLUMETRIC-LETTERS"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     inkscape:groupmode="layer">
    <path d="M10,10 L60,10 L60,40 L10,40 Z"/>
    <path d="M70,10 L120,10 L120,40 L70,40 Z"/>
    <path d="M130,10 L180,10 L180,40 L130,40 Z"/>
  </g>
</svg>
""".strip()

_NO_MAPPING_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="400mm" height="50mm" viewBox="0 0 400 50">
  <g id="Layer_x0020_1">
    <rect x="0" y="0" width="100" height="50"/>
    <rect x="110" y="0" width="100" height="50"/>
  </g>
</svg>
""".strip()


def _face_vinyl_quote_input(**overrides):
    base = {
        "face_finish_type": "oracal_651",
        "face_vinyl_roll_width_mm": 1260,
        "face_vinyl_color_code": "651-020",
        "face_vinyl_color_name": "Golden Yellow",
        "letter_face_area_m2": 1.466571,
        "width_mm": 4800,
        "height_mm": 600,
        "mounting_system": "direct_wall",
    }
    base.update(overrides)
    return base


class TestSvgPiecesExtracted(unittest.TestCase):
    def test_four_rect_pieces_not_single_assembly(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_FOUR_LETTER_RECTS_SVG)
        updates = build_vector_spec_updates(
            filename="four-letters.svg",
            size_bytes=len(_FOUR_LETTER_RECTS_SVG),
            content_type="image/svg+xml",
            svg_text=_FOUR_LETTER_RECTS_SVG,
            analysis=analysis,
        )
        boxes = updates.get("letter_bounding_boxes") or []
        self.assertEqual(len(boxes), 4)
        for box in boxes:
            self.assertIn("width_mm", box)
            self.assertIn("height_mm", box)
            self.assertAlmostEqual(box["width_mm"], 600.0, places=1)
            self.assertAlmostEqual(box["height_mm"], 400.0, places=1)
            self.assertEqual(box.get("source"), "svg_layer_mapped")

    def test_path_subpaths_extracted_as_separate_pieces(self) -> None:
        boxes = extract_letter_bounding_boxes_from_svg(
            _PATH_LETTERS_SVG,
            svg_layer_mappings={"TPL-VOLUMETRIC-LETTERS": "TPL-VOLUMETRIC-LETTERS"},
        )
        self.assertGreaterEqual(len(boxes), 3)
        for box in boxes:
            self.assertGreater(box["width_mm"], 0)
            self.assertGreater(box["height_mm"], 0)
            self.assertEqual(box.get("source"), "svg_layer_mapped")

    def test_unmapped_generic_layer_returns_empty(self) -> None:
        boxes = extract_flat_material_pieces_from_svg(_NO_MAPPING_SVG)
        self.assertEqual(boxes, [])

    def test_upload_without_letters_mapping_skips_letter_bounding_boxes(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_NO_MAPPING_SVG)
        updates = build_vector_spec_updates(
            filename="generic-layer.svg",
            size_bytes=100,
            content_type="image/svg+xml",
            svg_text=_NO_MAPPING_SVG,
            analysis=analysis,
        )
        self.assertNotIn("letter_bounding_boxes", updates)

    def test_flat_geometry_is_material_agnostic(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_FOUR_LETTER_RECTS_SVG)
        product_spec = build_vector_spec_updates(
            filename="four-letters.svg",
            size_bytes=100,
            content_type="image/svg+xml",
            svg_text=_FOUR_LETTER_RECTS_SVG,
            analysis=analysis,
        )
        boxes = product_spec["letter_bounding_boxes"]
        pieces, source = collect_nesting_pieces({}, product_spec=product_spec)
        self.assertEqual(source, "letter_bounding_boxes")
        nesting = estimate_face_vinyl_nesting(
            pieces, roll_width_mm=1260, nesting_source=source
        )
        # Generic pieces feed roll adapter — sheet adapter would use same pieces differently.
        self.assertEqual(nesting.nesting_method, "piece_based_rectangular")
        self.assertIsNotNone(nesting.nested_roll_length_m)
        for box in boxes:
            self.assertNotIn("nested_roll_length_m", box)
            self.assertNotIn("quantity_m2", box)


class TestPiecesPersistIntoProductSpec(unittest.TestCase):
    def test_validator_accepts_letter_bounding_boxes(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_FOUR_LETTER_RECTS_SVG)
        updates = build_vector_spec_updates(
            filename="four-letters.svg",
            size_bytes=100,
            content_type="image/svg+xml",
            svg_text=_FOUR_LETTER_RECTS_SVG,
            analysis=analysis,
        )
        validated = validate_intake_product_spec(
            {
                "text": "TEST",
                "face_finish_type": "oracal_651",
                **updates,
            }
        )
        self.assertIn("letter_bounding_boxes", validated)
        self.assertEqual(len(validated["letter_bounding_boxes"]), 4)

    def test_handoff_sees_persisted_pieces(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_FOUR_LETTER_RECTS_SVG)
        product_spec = validate_intake_product_spec(
            build_vector_spec_updates(
                filename="four-letters.svg",
                size_bytes=100,
                content_type="image/svg+xml",
                svg_text=_FOUR_LETTER_RECTS_SVG,
                analysis=analysis,
            )
        )
        qi = _face_vinyl_quote_input()
        pieces, source = collect_nesting_pieces(qi, product_spec=product_spec)
        self.assertEqual(source, "letter_bounding_boxes")
        self.assertEqual(len(pieces), 4)

        handoff = build_face_vinyl_handoff_for_quote(qi, product_spec=product_spec)
        nesting = handoff.get("nesting") or {}
        self.assertEqual(nesting.get("method"), "piece_based_rectangular")
        self.assertFalse(nesting.get("is_fallback"))
        self.assertGreater(nesting.get("pieces_count") or 0, 1)


class TestPieceBasedNestingFromSvgPieces(unittest.TestCase):
    def test_piece_based_triggered_from_svg_pieces(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_FOUR_LETTER_RECTS_SVG)
        product_spec = build_vector_spec_updates(
            filename="four-letters.svg",
            size_bytes=100,
            content_type="image/svg+xml",
            svg_text=_FOUR_LETTER_RECTS_SVG,
            analysis=analysis,
        )
        qi = _face_vinyl_quote_input()
        pieces, source = collect_nesting_pieces(qi, product_spec=product_spec)
        nesting = estimate_face_vinyl_nesting(
            pieces,
            roll_width_mm=1260,
            nesting_source=source,
        )
        self.assertEqual(nesting.nesting_method, "piece_based_rectangular")
        self.assertFalse(nesting.is_fallback)
        self.assertGreater(nesting.pieces_count, 1)
        self.assertGreater(len(nesting.placements), 1)
        self.assertNotEqual(nesting.nesting_source, "assembly_bbox")


class TestFallbackStillWorks(unittest.TestCase):
    def test_no_svg_pieces_uses_assembly_bbox_fallback(self) -> None:
        qi = _face_vinyl_quote_input()
        product_spec = {"vector_suggested_assembly_width_mm": 4800, "vector_suggested_assembly_height_mm": 600}
        pieces, source = collect_nesting_pieces(qi, product_spec=product_spec)
        nesting = estimate_face_vinyl_nesting(pieces, roll_width_mm=1260, nesting_source=source)
        self.assertEqual(source, "assembly_bbox")
        self.assertEqual(nesting.nesting_method, "fallback_weak_estimate")
        self.assertTrue(nesting.is_fallback)

        handoff = build_face_vinyl_handoff_for_quote(qi, product_spec=product_spec)
        self.assertTrue(handoff.get("fallback_weak_estimate"))


class TestMlMpSeparationFromSvgPipeline(unittest.TestCase):
    def test_numeric_ml_mp_labor_from_svg_pieces(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_FOUR_LETTER_RECTS_SVG)
        product_spec = build_vector_spec_updates(
            filename="four-letters.svg",
            size_bytes=100,
            content_type="image/svg+xml",
            svg_text=_FOUR_LETTER_RECTS_SVG,
            analysis=analysis,
        )
        qi = _face_vinyl_quote_input()
        resolution = resolve_face_vinyl_used_sqm(qi, product_spec=product_spec)
        handoff = build_face_vinyl_handoff_for_quote(qi, product_spec=product_spec)
        nesting = handoff.get("nesting") or {}

        nested_ml = nesting.get("nested_roll_length_m")
        recommended_ml = nesting.get("recommended_roll_length_m") or resolution.recommended_roll_length_m
        material_width_m = nesting.get("material_width_m") or resolution.material_width_m
        quantity_m2 = nesting.get("quantity_m2") or resolution.face_vinyl_used_sqm

        self.assertIsNotNone(nested_ml)
        self.assertIsNotNone(recommended_ml)
        self.assertAlmostEqual(material_width_m or 0, 1.26, places=2)
        self.assertAlmostEqual(
            quantity_m2 or 0,
            round((recommended_ml or 0) * (material_width_m or 0), 4),
            places=3,
        )
        # 4×600×400 on 1260 roll → ~0.8 ml nested, ~0.88 ml recommended (10% reserve)
        self.assertAlmostEqual(nested_ml or 0, 0.80, places=1)
        self.assertAlmostEqual(recommended_ml or 0, 0.88, places=1)
        self.assertAlmostEqual(quantity_m2 or 0, 1.1088, places=3)

        labor_eur = (quantity_m2 or 0) * 5.0
        self.assertAlmostEqual(labor_eur, 5.544, places=2)
        self.assertNotAlmostEqual(labor_eur, (recommended_ml or 0) * 5.0, places=1)


class TestEmployeeMobileInstructionsClean(unittest.TestCase):
    _FORBIDDEN = (
        "nu pe cant",
        "10% rezervă",
        "assembly_bbox",
        "fallback_weak_estimate",
        "suprafață minim teoretic",
        "ml ×",
        "EUR/mp",
        "quantity_m2",
        "labor_cost",
    )

    def test_piece_based_instructions_clean(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_FOUR_LETTER_RECTS_SVG)
        product_spec = build_vector_spec_updates(
            filename="four-letters.svg",
            size_bytes=100,
            content_type="image/svg+xml",
            svg_text=_FOUR_LETTER_RECTS_SVG,
            analysis=analysis,
        )
        text = build_face_vinyl_task_instructions(
            _face_vinyl_quote_input(),
            product_spec=product_spec,
        )
        self.assertIn("Colantezi fețele din plexiglas ale literelor cu autocolantul selectat.", text)
        self.assertIn("Material autocolant:", text)
        self.assertIn("Lățime rolă:", text)
        self.assertIn("Lungime pregătire:", text)
        lowered = text.lower()
        for forbidden in self._FORBIDDEN:
            self.assertNotIn(forbidden.lower(), lowered, msg=forbidden)

    def test_fallback_instructions_clean(self) -> None:
        text = build_face_vinyl_task_instructions(_face_vinyl_quote_input())
        self.assertIn("Material estimat pentru pregătire:", text)
        lowered = text.lower()
        for forbidden in self._FORBIDDEN:
            self.assertNotIn(forbidden.lower(), lowered, msg=forbidden)


if __name__ == "__main__":
    unittest.main()
