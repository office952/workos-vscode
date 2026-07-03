"""Plexiglass face nesting integration in quote/order snapshot handoff."""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.volumetric_face_vinyl_service import build_face_vinyl_handoff_for_quote  # noqa: E402
from services.volumetric_plexiglass_face_nesting_service import (  # noqa: E402
    PROFILE_SOURCE_DEFAULT_INTERNAL,
    build_plexiglass_face_nesting_for_quote,
    resolve_plexiglass_face_profile,
)
from services.work_intake_svg_spec_mapper import build_vector_spec_updates  # noqa: E402
from services.svg_layer_analysis_service import SvgLayerAnalysisService  # noqa: E402
from tests.test_volumetric_finish_mounting_pricing import BASE_QUOTE_INPUT  # noqa: E402

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

_MINIMAL_QI = {
    "face_finish_type": "oracal_651",
    "face_vinyl_roll_width_mm": 1260,
    "face_vinyl_color_code": "651-020",
}

_FACE_VINYL_QI = {**BASE_QUOTE_INPUT, **_MINIMAL_QI}

_FOUR_BOXES = [
    {"piece_id": f"L{i}", "width_mm": 600, "height_mm": 400, "source": "svg_layer_mapped"}
    for i in range(1, 5)
]

_ROLL_FORBIDDEN = (
    "nested_roll_length_m",
    "recommended_roll_length_m",
    "material_width_m",
    "roll_width_mm",
    "quantity_m2",
)


def _serialize_wrapper(**kwargs) -> dict:
    from routers.quotes import _serialize_quote_line_items

    snapshot = {
        "status": "priced",
        "price": {"net": 100.0, "gross": 119.0, "final": 119.0},
        "pricing": {"margin_pct": 0, "discount_pct": 0, "vat_pct": 19},
    }
    return json.loads(_serialize_quote_line_items(snapshot, **kwargs))


def _extract_handoff(wrapper: dict) -> dict:
    handoff: dict = {}
    for key in (
        "quote_input",
        "product_spec_json",
        "delivery_type",
        "face_vinyl_handoff",
        "plexiglass_face_nesting",
    ):
        value = wrapper.get(key)
        if value is not None:
            handoff[key] = value
    return handoff


def _assert_no_roll_fields(obj: dict, path: str = "") -> None:
    for key, value in obj.items():
        full = f"{path}.{key}" if path else key
        self_msg = f"unexpected roll field at {full}"
        assert key not in _ROLL_FORBIDDEN, self_msg
        if isinstance(value, dict):
            _assert_no_roll_fields(value, full)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _assert_no_roll_fields(item, full)


class TestPlexiglassNestingFromLetterBoxes(unittest.TestCase):
    def test_block_enabled_with_sheet_nesting(self) -> None:
        spec = {"letter_bounding_boxes": _FOUR_BOXES}
        block = build_plexiglass_face_nesting_for_quote(_FACE_VINYL_QI, product_spec=spec)
        self.assertTrue(block["enabled"])
        self.assertEqual(block["material"]["material_type"], "sheet")
        nesting = block["nesting"]
        self.assertEqual(nesting["method"], "sheet_rectangular")
        self.assertFalse(nesting["is_fallback"])
        self.assertEqual(nesting["sheets_used"], 1)
        self.assertGreater(len(nesting["placements"]), 0)
        self.assertEqual(block["geometry"]["pieces_source"], "letter_bounding_boxes")
        _assert_no_roll_fields(block)

    def test_numeric_consumption(self) -> None:
        block = build_plexiglass_face_nesting_for_quote(
            _FACE_VINYL_QI,
            product_spec={"letter_bounding_boxes": _FOUR_BOXES},
        )
        nesting = block["nesting"]
        self.assertAlmostEqual(nesting["sheet_width_mm"], 3050, places=0)
        self.assertAlmostEqual(nesting["sheet_height_mm"], 2030, places=0)
        self.assertAlmostEqual(nesting["allocated_sheet_area_m2"], 6.1915, places=3)
        self.assertAlmostEqual(nesting["used_piece_bbox_area_m2"], 0.96, places=3)
        waste = nesting["allocated_sheet_area_m2"] - nesting["used_piece_bbox_area_m2"]
        self.assertAlmostEqual(nesting["remaining_area_m2"], waste, places=3)
        self.assertAlmostEqual(nesting["waste_area_m2"], waste, places=3)


class TestNoMlInPlexiglassBlock(unittest.TestCase):
    def test_no_roll_fields_anywhere(self) -> None:
        block = build_plexiglass_face_nesting_for_quote(
            _FACE_VINYL_QI,
            product_spec={"letter_bounding_boxes": _FOUR_BOXES},
        )
        _assert_no_roll_fields(block)


class TestVinylAndPlexiglassSeparate(unittest.TestCase):
    def test_same_quote_has_both_handoff_blocks(self) -> None:
        spec = {"letter_bounding_boxes": _FOUR_BOXES}
        vinyl = build_face_vinyl_handoff_for_quote(_FACE_VINYL_QI, product_spec=spec)
        plexi = build_plexiglass_face_nesting_for_quote(_FACE_VINYL_QI, product_spec=spec)

        wrapper = _serialize_wrapper(
            quote_input=_FACE_VINYL_QI,
            product_spec_json=spec,
            face_vinyl_handoff=vinyl,
            plexiglass_face_nesting=plexi,
        )
        self.assertIn("face_vinyl_handoff", wrapper)
        self.assertIn("plexiglass_face_nesting", wrapper)
        self.assertNotIn("plexiglass_face_nesting", wrapper["face_vinyl_handoff"])

        v_nest = wrapper["face_vinyl_handoff"]["nesting"]
        p_nest = wrapper["plexiglass_face_nesting"]["nesting"]
        self.assertEqual(v_nest["method"], "piece_based_rectangular")
        self.assertEqual(p_nest["method"], "sheet_rectangular")
        self.assertIsNotNone(v_nest.get("nested_roll_length_m"))
        self.assertIsNotNone(p_nest.get("sheets_used"))


class TestMissingGeometrySafe(unittest.TestCase):
    def test_no_pieces_disabled_with_reason(self) -> None:
        block = build_plexiglass_face_nesting_for_quote(_MINIMAL_QI, product_spec={})
        self.assertFalse(block["enabled"])
        self.assertEqual(block["reason"], "missing_geometry")

    def test_assembly_bbox_fallback_explicit(self) -> None:
        qi = {**_MINIMAL_QI, "width_mm": 2000, "height_mm": 600}
        block = build_plexiglass_face_nesting_for_quote(qi, product_spec={})
        self.assertTrue(block["enabled"])
        self.assertTrue(block["nesting"]["is_fallback"])
        self.assertEqual(block["geometry"]["pieces_source"], "assembly_bbox")
        self.assertEqual(block["nesting"]["method"], "sheet_rectangular_fallback")


class TestMaterialProfileSource(unittest.TestCase):
    def test_default_profile_marked_internal(self) -> None:
        profile, source, display, is_fallback = resolve_plexiglass_face_profile(_FACE_VINYL_QI, {})
        self.assertEqual(source, PROFILE_SOURCE_DEFAULT_INTERNAL)
        self.assertTrue(is_fallback)
        self.assertEqual(profile.sheet_width_mm, 3050)
        self.assertEqual(profile.sheet_height_mm, 2030)

    def test_quote_input_sheet_override(self) -> None:
        qi = {
            **_FACE_VINYL_QI,
            "plexiglass_sheet_width_mm": 3000,
            "plexiglass_sheet_height_mm": 2000,
            "plexiglass_face_thickness_mm": 5,
        }
        profile, source, display, is_fallback = resolve_plexiglass_face_profile(qi, {})
        self.assertEqual(source, "quote_input")
        self.assertFalse(is_fallback)
        self.assertEqual(profile.sheet_width_mm, 3000)
        self.assertEqual(profile.thickness_mm, 5)
        self.assertIn("5 mm", display)


class TestSnapshotPreservation(unittest.TestCase):
    def test_wrapper_and_order_handoff_extract(self) -> None:
        spec = {"letter_bounding_boxes": _FOUR_BOXES}
        plexi = build_plexiglass_face_nesting_for_quote(_FACE_VINYL_QI, product_spec=spec)
        wrapper = _serialize_wrapper(
            quote_input=_FACE_VINYL_QI,
            product_spec_json=spec,
            plexiglass_face_nesting=plexi,
        )
        handoff = _extract_handoff(wrapper)
        self.assertIn("plexiglass_face_nesting", handoff)
        self.assertTrue(handoff["plexiglass_face_nesting"]["enabled"])
        self.assertEqual(
            handoff["plexiglass_face_nesting"]["nesting"]["sheets_used"],
            1,
        )


class TestSvgPipelineFeedsPlexiglass(unittest.TestCase):
    def test_svg_mapped_boxes_in_handoff(self) -> None:
        analysis = SvgLayerAnalysisService.analyze(_FOUR_LETTER_RECTS_SVG)
        product_spec = build_vector_spec_updates(
            filename="four-letters.svg",
            size_bytes=100,
            content_type="image/svg+xml",
            svg_text=_FOUR_LETTER_RECTS_SVG,
            analysis=analysis,
        )
        block = build_plexiglass_face_nesting_for_quote(_FACE_VINYL_QI, product_spec=product_spec)
        self.assertTrue(block["enabled"])
        self.assertEqual(block["geometry"]["pieces_source"], "letter_bounding_boxes")
        self.assertEqual(block["nesting"]["sheets_used"], 1)
        _assert_no_roll_fields(block)


if __name__ == "__main__":
    unittest.main()
