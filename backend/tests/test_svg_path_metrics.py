from __future__ import annotations

import unittest
from pathlib import Path

from services.svg_layer_analysis_service import SvgLayerAnalysisService
from services.svg_metrics_service import SvgMetricsService
from services.svg_path_metrics import estimate_letter_count_from_subpaths, parse_path_metrics


class TestSvgPathMetrics(unittest.TestCase):
    def test_simple_closed_rectangle(self) -> None:
        r = parse_path_metrics("M 0 0 L 100 0 L 100 50 L 0 50 Z")
        self.assertEqual(r.subpath_count, 1)
        self.assertAlmostEqual(r.total_length, 300.0, delta=1.0)
        self.assertAlmostEqual(r.total_closed_area, 5000.0, delta=10.0)

    def test_relative_commands(self) -> None:
        r = parse_path_metrics("m 0 0 l 100 0 l 0 50 l -100 0 z")
        self.assertAlmostEqual(r.total_length, 300.0, delta=1.0)
        self.assertAlmostEqual(r.total_closed_area, 5000.0, delta=10.0)

    def test_horizontal_vertical_commands(self) -> None:
        r = parse_path_metrics("M 0 0 H 100 V 50 H 0 Z")
        self.assertAlmostEqual(r.total_length, 300.0, delta=1.0)
        self.assertAlmostEqual(r.total_closed_area, 5000.0, delta=10.0)

    def test_cubic_curve_produces_nonzero_metrics(self) -> None:
        r = parse_path_metrics("M0 0 C 25 0, 75 50, 100 50 L 100 0 Z")
        self.assertGreater(r.total_length, 0)
        self.assertGreater(r.total_closed_area, 0)
        self.assertIn("path_curve_metrics_approximate", r.warnings)

    def test_quadratic_curve_produces_nonzero_metrics(self) -> None:
        r = parse_path_metrics("M0 50 Q 50 0, 100 50 L 100 50 L 0 50 Z")
        self.assertGreater(r.total_length, 0)
        self.assertIn("path_curve_metrics_approximate", r.warnings)

    def test_letter_count_from_subpaths(self) -> None:
        r = parse_path_metrics("M0 0 L10 0 L10 10 Z m20 0 L30 0 L30 10 Z")
        count = estimate_letter_count_from_subpaths(r.subpaths)
        self.assertEqual(count, 2)


LAYERED_PATH_SVG = """
<svg width="400.023cm" height="50.0176cm" viewBox="0 0 403.44383 50.44538"
  xmlns="http://www.w3.org/2000/svg">
  <g id="Litere_x0020_Volumetrice">
    <metadata id="CorelCorpID_0Corel-Layer"/>
    <path d="M0.0089 48.89823l0 -47.35108 11.19494 0 0 17.38884 18.30077 0 0 -17.38884 11.12791 0 0 47.35108 -11.12791 0 0 -19.86336 -18.30077 0 0 19.86336 -11.19494 0zm60.26506 -23.67554c0,4.11311 1.20668,7.56858 3.61994,10.34411 2.41331,2.77554 5.38523,4.16886 8.91576,4.16886 3.55288,0 6.53599,-1.38219 8.9381,-4.14657 2.40212,-2.77549 3.59755,-6.231 3.59755,-10.3664 0,-4.15773 -1.19544,-7.63548 -3.59755,-10.41098 -2.40211,-2.77554 -5.38522,-4.16885 -8.9381,-4.16885 -3.53053,0 -6.50245,1.3933 -8.91576,4.16885 -2.41326,2.77549 -3.61994,6.25324 -3.61994,10.41098zm-11.66417 0c0,-3.51121 0.60329,-6.78832 1.82111,-9.8425 1.20663,-3.06534 2.99426,-5.79631 5.3517,-8.21514 2.22334,-2.30733 4.81538,-4.07964 7.76496,-5.30581 2.93838,-1.23729 6.0332,-1.85035 9.26211,-1.85035 3.22886,0 6.32368,0.62422 9.28446,1.86151 2.96072,1.23729 5.5863,3.03189 7.87666,5.36156 2.31275,2.32962 4.06684,5.01601 5.25114,8.0813 1.19549,3.05423 1.78763,6.36479 1.78763,9.90942 0,2.96502 -0.41337,5.75168 -1.24017,8.35999 -0.83794,2.60836 -2.06691,4.99372 -3.7093,7.15616 -2.31275,3.06534 -5.15058,5.45077 -8.52472,7.14505 -3.3741,1.70544 -6.94936,2.5526 -10.72569,2.5526 -3.20657,0 -6.27899,-0.62422 -9.21743,-1.86151 -2.93839,-1.23729 -5.54162,-3.03189 -7.80964,-5.36156 -2.35744,-2.40766 -4.14507,-5.13862 -5.3517,-8.18162 -1.21783,-3.03194 -1.82111,-6.30905 -1.82111,-9.80909z"/>
  </g>
  <g id="Structura_x0020_metalca">
    <rect x="0.00891" y="44.50192" width="399.38653" height="3.02566"/>
    <rect x="0.0089" y="2.66047" width="380.71812" height="3.02566"/>
  </g>
</svg>
""".strip()


class TestSvgMetricsPathIntegration(unittest.TestCase):
    def test_path_layer_in_metrics_service(self) -> None:
        svg = (
            '<svg width="100mm" height="50mm" viewBox="0 0 100 50" '
            'xmlns="http://www.w3.org/2000/svg">'
            '<path d="M 0 0 L 100 0 L 100 50 L 0 50 Z"/></svg>'
        )
        result = SvgMetricsService.parse_svg_metrics(svg)
        self.assertEqual(result.parse_status, "parsed")
        self.assertNotIn("unsupported_path", result.warnings)
        self.assertAlmostEqual(float(result.metrics.bbox_w_mm or 0), 100.0, places=1)
        self.assertGreater(float(result.metrics.perimeter_mm_approx or 0), 0)
        self.assertGreater(float(result.metrics.area_mm2_approx or 0), 0)

    def test_metadata_does_not_block_path_geometry(self) -> None:
        result = SvgMetricsService.parse_svg_metrics(LAYERED_PATH_SVG)
        self.assertEqual(result.parse_status, "parsed")
        self.assertNotIn("unsupported_path", result.warnings)
        self.assertNotIn("unsupported_element:metadata", result.warnings)
        self.assertGreater(float(result.metrics.bbox_w_mm or 0), 3000.0)

    def test_viewbox_fallback_without_invented_perimeter(self) -> None:
        svg = (
            '<svg viewBox="0 0 100 50" xmlns="http://www.w3.org/2000/svg">'
            '<path d=""/></svg>'
        )
        result = SvgMetricsService.parse_svg_metrics(svg)
        self.assertEqual(result.parse_status, "parsed")
        self.assertIn("viewbox_bbox_fallback", result.warnings)
        self.assertIsNone(result.metrics.perimeter_mm_approx)
        self.assertIsNone(result.metrics.area_mm2_approx)

    def test_layer_analysis_letters_separate_from_structure(self) -> None:
        fixture_path = (
            Path(__file__).resolve().parents[2]
            / "frontend"
            / "e2e"
            / "fixtures"
            / "lleexxaa.svg"
        )
        if fixture_path.is_file():
            svg_text = fixture_path.read_text(encoding="utf-8")
        else:
            svg_text = LAYERED_PATH_SVG

        result = SvgLayerAnalysisService.analyze(svg_text)
        self.assertIn(result.parse_status, {"parsed", "parsed_sanitized"})
        by_id = {row.svg_layer_id: row for row in result.layers}
        letters = by_id.get("Litere_x0020_Volumetrice")
        structure = by_id.get("Structura_x0020_metalca")
        self.assertIsNotNone(letters)
        self.assertIsNotNone(structure)
        self.assertNotIn("unsupported_path", letters.warnings)
        self.assertGreater(float(letters.metrics.bbox_width_mm or 0), 3000.0)
        self.assertGreater(float(letters.metrics.path_perimeter_m or 0), 1.0)
        self.assertGreater(float(letters.metrics.path_area_m2 or 0), 0.1)
        struct_w = float(structure.metrics.bbox_width_mm or 0)
        letter_w = float(letters.metrics.bbox_width_mm or 0)
        self.assertGreater(struct_w, 0)
        self.assertNotEqual(struct_w, letter_w)


if __name__ == "__main__":
    unittest.main()
