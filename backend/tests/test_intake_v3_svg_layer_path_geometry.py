from __future__ import annotations

import unittest
from pathlib import Path

from services.intake_v3_layer_role_confirmation_service import (
    build_layer_role_confirmation_draft_from_path_geometry,
)
from services.intake_v3_svg_drawable_layer_summary import build_drawable_layer_summary_from_svg_text
from services.intake_v3_svg_layer_path_geometry import build_layer_path_geometry_from_svg_text

REPO_ROOT = Path(__file__).resolve().parents[2]
PBL_COLOR_SVG = REPO_ROOT / "tmp" / "atoms-export" / "uploads" / "pbl-color.svg"

FLAT_PBL_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="205cm" height="35cm" viewBox="0 0 198.61594 33.91004">
  <g id="Publi">
    <path fill="#009846" d="M10 10 L50 10 L50 30 L10 30 Z"/>
  </g>
  <g id="Media">
    <path fill="#66C3D0" d="M60 10 L100 10 L100 30 L60 30 Z"/>
  </g>
</svg>
"""

NESTED_INKSCAPE_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
  width="205cm" height="35cm" viewBox="0 0 198.61594 33.91004">
  <g id="Litere_x0020_Volumetrice_x0020_Luminoase">
    <g inkscape:groupmode="layer" inkscape:label="Publi">
      <path fill="#009846" d="M10 10 L50 10 L50 30 L10 30 Z"/>
    </g>
    <g inkscape:groupmode="layer" inkscape:label="Media">
      <path fill="#66C3D0" d="M60 10 L100 10 L100 30 L60 30 Z"/>
    </g>
  </g>
</svg>
"""

DEFS_ONLY_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <clipPath id="clip">
      <path d="M0 0 L10 0 L10 10 Z"/>
    </clipPath>
  </defs>
  <g id="Letters">
    <path fill="#E31E24" d="M20 20 L40 20 L40 40 L20 40 Z"/>
  </g>
</svg>
"""


def _path_summary(svg_text: str) -> dict:
    geometry = build_layer_path_geometry_from_svg_text(svg_text)
    assert geometry is not None
    return {"parse_status": "parsed", **geometry}


@unittest.skipUnless(PBL_COLOR_SVG.is_file(), "pbl-color.svg fixture missing")
class TestPblColorDrawableLayerSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.svg_text = PBL_COLOR_SVG.read_text(encoding="utf-8", errors="replace")
        cls.summary = _path_summary(cls.svg_text)
        cls.draft = build_layer_role_confirmation_draft_from_path_geometry(
            cls.summary,
            workspace_id="pbl-color-test",
        )

    def test_three_layer_candidates(self) -> None:
        layer_ids = {layer["layer_id"] for layer in self.summary["layers"]}
        self.assertEqual(layer_ids, {"Cadru", "Litere_x0020_volumetrice", "Emblema"})

    def test_defs_clip_path_not_a_layer(self) -> None:
        layer_ids = {layer["layer_id"] for layer in self.summary["layers"]}
        self.assertNotIn("__ungrouped__", layer_ids)
        self.assertNotIn(None, layer_ids)

    def test_cadru_rect_reference_role(self) -> None:
        cadru = next(layer for layer in self.draft.layers if layer.layer_key == "Cadru")
        self.assertEqual(cadru.metrics.rect_count, 10)
        self.assertEqual(cadru.auto_role, "reference")
        self.assertEqual(cadru.color_evidence.fills if cadru.color_evidence else [], [])
        strokes = cadru.color_evidence.strokes if cadru.color_evidence else []
        self.assertIn("#2B2A29", strokes)

    def test_litere_two_paths_and_fill_subgroups(self) -> None:
        litere = next(
            layer for layer in self.draft.layers if layer.layer_key == "Litere_x0020_volumetrice"
        )
        self.assertEqual(litere.metrics.path_count, 2)
        self.assertEqual(litere.auto_role, "face")
        assert litere.color_evidence is not None
        self.assertIn("#E31E24", litere.color_evidence.fills)
        self.assertIn("#393185", litere.color_evidence.fills)
        fill_colors = {group.color for group in litere.color_evidence.fill_groups}
        self.assertEqual(fill_colors, {"#E31E24", "#393185"})
        self.assertFalse(litere.color_evidence.is_multicolor)

    def test_emblema_polygon_multicolor_artwork(self) -> None:
        emblema = next(layer for layer in self.draft.layers if layer.layer_key == "Emblema")
        self.assertEqual(emblema.metrics.polygon_count, 510)
        self.assertEqual(emblema.auto_role, "printed_artwork")
        assert emblema.color_evidence is not None
        self.assertTrue(emblema.color_evidence.is_multicolor)
        self.assertGreater(len(emblema.color_evidence.fill_groups), 10)

    def test_font_evidence_converted_to_paths(self) -> None:
        font = self.summary.get("font_evidence") or {}
        self.assertFalse(font.get("has_text"))
        self.assertTrue(font.get("converted_to_paths"))
        self.assertIn("font not recoverable", (font.get("note") or "").lower())


class TestIntakeV3SvgLayerPathGeometry(unittest.TestCase):
    def test_flat_publi_media_layers_stay_separate(self) -> None:
        summary = build_layer_path_geometry_from_svg_text(FLAT_PBL_SVG)
        assert summary is not None
        layer_ids = {layer["layer_id"] for layer in summary["layers"]}
        self.assertEqual(layer_ids, {"Publi", "Media"})

    def test_nested_inkscape_layers_publi_media_not_aggregated(self) -> None:
        summary = build_layer_path_geometry_from_svg_text(NESTED_INKSCAPE_SVG)
        assert summary is not None
        layer_ids = {layer["layer_id"] for layer in summary["layers"]}
        self.assertEqual(layer_ids, {"Publi", "Media"})
        self.assertNotIn("Litere_x0020_Volumetrice_x0020_Luminoase", layer_ids)

    def test_defs_paths_excluded_from_layers(self) -> None:
        summary = build_layer_path_geometry_from_svg_text(DEFS_ONLY_SVG)
        assert summary is not None
        layer_ids = {layer["layer_id"] for layer in summary["layers"]}
        self.assertEqual(layer_ids, {"Letters"})
        drawable = build_drawable_layer_summary_from_svg_text(DEFS_ONLY_SVG)
        assert drawable is not None
        self.assertEqual(len(drawable["layers"]), 1)


if __name__ == "__main__":
    unittest.main()
