"""Safe SVG sanitization for CorelDRAW DOCTYPE exports."""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.svg_layer_analysis_service import SvgLayerAnalysisService  # noqa: E402
from services.svg_metrics_service import SvgMetricsService  # noqa: E402
from services.svg_sanitization_service import (  # noqa: E402
    WARN_SVG_SANITIZED_DOCTYPE_REMOVED,
    has_unsafe_svg_declarations,
    sanitize_svg_for_analysis,
)

VALIDATION_INPUT = Path(__file__).resolve().parents[1] / "validation_input"
LETTERS_FILE = VALIDATION_INPUT / "TPL-VOLUMETRIC-LETTERS_vetro_litere.svg"
BARS_FILE = VALIDATION_INPUT / "TPL-VOLUMETRIC-LETTERS_vetro_litere_bari.svg"

COREL_DOCTYPE_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="50mm" viewBox="0 0 100 50">
  <g id="Layer_x0020_1">
    <path d="M10 10 L90 10 L90 40 L10 40 Z"/>
  </g>
</svg>
""".strip()


def _path_d_values(svg_text: str) -> list[str]:
    return re.findall(r'\bd="([^"]*)"', svg_text)


class TestSvgSanitizationService(unittest.TestCase):
    def test_raw_parser_rejects_doctype(self) -> None:
        raw = SvgMetricsService.parse_svg_metrics(COREL_DOCTYPE_SVG)
        self.assertEqual(raw.parse_status, "failed")
        self.assertEqual(raw.error_code, "xml_unsafe_construct")

    def test_sanitizer_removes_doctype_without_changing_path_data(self) -> None:
        before_paths = _path_d_values(COREL_DOCTYPE_SVG)
        sanitized, meta = sanitize_svg_for_analysis(COREL_DOCTYPE_SVG)
        self.assertIsNotNone(sanitized)
        self.assertIsNotNone(meta)
        self.assertFalse(has_unsafe_svg_declarations(sanitized or ""))
        self.assertEqual(_path_d_values(sanitized or ""), before_paths)
        self.assertTrue(meta.analysis_sanitized)
        self.assertTrue(meta.original_file_has_doctype)
        self.assertEqual(meta.sanitization_reason, "svg_doctype_removed")

    def test_sanitized_content_passes_safe_parser(self) -> None:
        sanitized, _ = sanitize_svg_for_analysis(COREL_DOCTYPE_SVG)
        parsed = SvgMetricsService.parse_svg_metrics(sanitized or "")
        self.assertEqual(parsed.parse_status, "parsed")

    def test_analyze_returns_parsed_sanitized_with_warning(self) -> None:
        result = SvgLayerAnalysisService.analyze(COREL_DOCTYPE_SVG)
        self.assertEqual(result.parse_status, "parsed_sanitized")
        self.assertIn(WARN_SVG_SANITIZED_DOCTYPE_REMOVED, result.warnings)
        self.assertIsNotNone(result.sanitization)
        self.assertTrue(result.sanitization["analysis_sanitized"])

    def test_generic_corel_layer_stays_unmapped(self) -> None:
        result = SvgLayerAnalysisService.analyze(COREL_DOCTYPE_SVG)
        self.assertEqual(result.summary["layers_found"], 1)
        layer = result.layers[0]
        self.assertEqual(layer.svg_layer_name, "Layer_x0020_1")
        self.assertEqual(layer.mapping_status, "unmapped")
        self.assertIsNone(layer.mapped_template_code)

    def test_no_letter_geometry_invented_from_sanitized_corel(self) -> None:
        result = SvgLayerAnalysisService.analyze(COREL_DOCTYPE_SVG)
        layer = result.layers[0]
        self.assertIsNone(layer.quote_input_suggestions.get("letter_count"))
        self.assertEqual(layer.quote_input_suggestions, {})

    def test_entity_declaration_blocks_sanitization(self) -> None:
        entity_svg = """<?xml version="1.0"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd" [
  <!ENTITY foo "bar">
]>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <path d="M0 0 L10 10"/>
</svg>
"""
        sanitized, meta = sanitize_svg_for_analysis(entity_svg)
        self.assertIsNone(sanitized)
        self.assertIsNone(meta)

    def test_xxe_entity_blocks_geometry_prepare(self) -> None:
        xxe_svg = """<?xml version="1.0"?>
<!DOCTYPE svg [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <path d="M0 0 L10 10"/>
</svg>
"""
        from services.svg_sanitization_service import prepare_svg_text_for_safe_geometry_parsing

        prep = prepare_svg_text_for_safe_geometry_parsing(xxe_svg)
        self.assertFalse(prep.ok)
        self.assertIsNotNone(prep.error_code)


@unittest.skipUnless(LETTERS_FILE.is_file(), "validation_input letters SVG missing")
class TestCorelDrawValidationInputLetters(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.svg_text = LETTERS_FILE.read_text(encoding="utf-8")

    def test_letters_file_parsed_sanitized(self) -> None:
        result = SvgLayerAnalysisService.analyze(
            self.svg_text,
            source_file_name=LETTERS_FILE.name,
        )
        self.assertEqual(result.parse_status, "parsed_sanitized")
        self.assertNotEqual(result.error_code, "xml_unsafe_construct")
        self.assertIn(WARN_SVG_SANITIZED_DOCTYPE_REMOVED, result.warnings)
        self.assertEqual(result.sanitization["source_file_name"], LETTERS_FILE.name)

    def test_letters_layer_unmapped_no_count(self) -> None:
        result = SvgLayerAnalysisService.analyze(self.svg_text)
        layer = result.layers[0]
        self.assertEqual(layer.svg_layer_name, "Layer_x0020_1")
        self.assertEqual(layer.mapping_status, "unmapped")
        self.assertIsNone(layer.quote_input_suggestions.get("letter_count"))


@unittest.skipUnless(BARS_FILE.is_file(), "validation_input bars SVG missing")
class TestCorelDrawValidationInputBars(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.svg_text = BARS_FILE.read_text(encoding="utf-8")

    def test_bars_file_parsed_sanitized_without_letter_geometry(self) -> None:
        result = SvgLayerAnalysisService.analyze(
            self.svg_text,
            source_file_name=BARS_FILE.name,
        )
        self.assertEqual(result.parse_status, "parsed_sanitized")
        self.assertNotEqual(result.error_code, "xml_unsafe_construct")
        layer = result.layers[0]
        self.assertEqual(layer.mapping_status, "unmapped")
        self.assertEqual(layer.quote_input_suggestions, {})
        self.assertIsNone(layer.quote_input_suggestions.get("letter_face_area_m2"))


if __name__ == "__main__":
    unittest.main()
