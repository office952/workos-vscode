"""Manual SVG layer mapping for volumetric vector readiness."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.svg_layer_analysis_service import SvgLayerAnalysisService  # noqa: E402
from services.svg_manual_layer_mapping import (  # noqa: E402
    normalize_svg_layer_mappings,
    letters_template_manually_mapped,
)
from services.volumetric_vector_readiness_policy import (  # noqa: E402
    WARN_VECTOR_LAYER_MAPPING_PENDING,
    WARN_VECTOR_MANUAL_REVIEW_REQUIRED,
    evaluate_volumetric_vector_readiness,
)
from validators.intake_product_spec import validate_intake_product_spec  # noqa: E402

VALIDATION_INPUT = Path(__file__).resolve().parents[1] / "validation_input"
LETTERS_FILE = VALIDATION_INPUT / "TPL-VOLUMETRIC-LETTERS_vetro_litere.svg"
BARS_FILE = VALIDATION_INPUT / "TPL-VOLUMETRIC-LETTERS_vetro_litere_bari.svg"

MULTI_LAYER_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <g id="Layer_Litere"><path d="M10 10 H40 V40 H10 Z"/></g>
  <g id="Layer_Bare"><rect x="0" y="50" width="100" height="10"/></g>
  <g id="Layer_Ghidaj"><line x1="0" y1="0" x2="100" y2="100"/></g>
</svg>"""


class TestSvgManualLayerMappingValidation(unittest.TestCase):
    def test_rejects_invalid_mapping_target(self) -> None:
        with self.assertRaises(ValueError):
            normalize_svg_layer_mappings({"Layer_x0020_1": "AUTO_LETTERS"})

    def test_accepts_valid_mappings_in_intake_spec(self) -> None:
        out = validate_intake_product_spec(
            {
                "vector_file_name": "litere.svg",
                "vector_file_type": "svg",
                "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
            }
        )
        self.assertEqual(
            out["svg_layer_mappings"]["Layer_x0020_1"],
            "TPL-VOLUMETRIC-LETTERS",
        )


class TestSvgManualLayerAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not LETTERS_FILE.is_file():
            raise unittest.SkipTest("letters validation SVG missing")
        cls.letters_svg = LETTERS_FILE.read_text(encoding="utf-8")

    def test_generic_layer_unmapped_without_manual_mapping(self) -> None:
        result = SvgLayerAnalysisService.analyze(self.letters_svg)
        self.assertEqual(result.parse_status, "parsed_sanitized")
        layer = result.layers[0]
        self.assertEqual(layer.svg_layer_name, "Layer_x0020_1")
        self.assertEqual(layer.mapping_status, "unmapped")
        self.assertIsNone(layer.mapped_by)

    def test_manual_mapping_maps_letters_layer(self) -> None:
        result = SvgLayerAnalysisService.analyze(
            self.letters_svg,
            manual_layer_mappings={"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
        )
        layer = result.layers[0]
        self.assertEqual(layer.mapping_status, "mapped_manual")
        self.assertEqual(layer.mapped_template_code, "TPL-VOLUMETRIC-LETTERS")
        self.assertEqual(layer.mapped_by, "manual")
        self.assertNotIn("svg_layer_unmapped", layer.blockers)

    def test_manual_mapping_does_not_invent_geometry(self) -> None:
        """Parseable SVG metrics are suggestions from real paths, not invented counts."""
        result = SvgLayerAnalysisService.analyze(
            self.letters_svg,
            manual_layer_mappings={"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
        )
        layer = result.layers[0]
        # Single compound path — letter_count is never inferred automatically.
        self.assertIsNone(layer.quote_input_suggestions.get("letter_count"))
        self.assertEqual(layer.mapped_by, "manual")
        if layer.metrics.metrics_confidence == "unavailable":
            self.assertIn("manual_geometry_required", layer.blockers)
            self.assertIsNone(layer.quote_input_suggestions.get("letter_perimeter_m"))
        else:
            perimeter = layer.quote_input_suggestions.get("letter_perimeter_m")
            self.assertIsNotNone(perimeter)
            self.assertGreater(float(perimeter), 0)
            # Real perimeter from SVG paths — not a blocker for missing geometry.
            self.assertNotIn("manual_geometry_required", layer.blockers)

    def test_manual_mapping_without_parseable_metrics_keeps_blocker(self) -> None:
        empty_path_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <g id="Layer_x0020_1"><path d=""/></g>
</svg>"""
        result = SvgLayerAnalysisService.analyze(
            empty_path_svg,
            manual_layer_mappings={"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
        )
        layer = result.layers[0]
        self.assertIn("manual_geometry_required", layer.blockers)
        self.assertIsNone(layer.quote_input_suggestions.get("letter_perimeter_m"))


@unittest.skipUnless(BARS_FILE.is_file(), "bars validation SVG missing")
class TestSvgManualLayerBarsFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bars_svg = BARS_FILE.read_text(encoding="utf-8")

    def test_support_bars_mapping_no_letter_geometry(self) -> None:
        result = SvgLayerAnalysisService.analyze(
            self.bars_svg,
            manual_layer_mappings={"Layer_x0020_1": "support_bars"},
        )
        layer = result.layers[0]
        self.assertEqual(layer.mapping_status, "mapped_manual")
        self.assertEqual(layer.detected_kind, "support_bars")
        self.assertIsNone(layer.mapped_template_code)
        self.assertEqual(layer.quote_input_suggestions, {})


class TestSvgMultiLayerAnalysis(unittest.TestCase):
    def test_multi_layer_mappings_in_one_request(self) -> None:
        result = SvgLayerAnalysisService.analyze(
            MULTI_LAYER_SVG,
            manual_layer_mappings={
                "Layer_Litere": "TPL-VOLUMETRIC-LETTERS",
                "Layer_Bare": "support_bars",
                "Layer_Ghidaj": "ignore",
            },
        )
        self.assertEqual(result.parse_status, "parsed")
        self.assertEqual(len(result.layers), 3)
        by_name = {layer.svg_layer_name: layer for layer in result.layers}
        self.assertEqual(by_name["Layer_Litere"].mapping_status, "mapped_manual")
        self.assertEqual(by_name["Layer_Litere"].mapped_template_code, "TPL-VOLUMETRIC-LETTERS")
        self.assertEqual(by_name["Layer_Bare"].mapping_status, "mapped_manual")
        self.assertEqual(by_name["Layer_Bare"].detected_kind, "support_bars")
        self.assertEqual(by_name["Layer_Ghidaj"].mapping_status, "ignored")
        self.assertIsNotNone(result.preview_svg)
        self.assertIn("<svg", result.preview_svg or "")

    def test_support_bars_only_does_not_create_letter_geometry(self) -> None:
        result = SvgLayerAnalysisService.analyze(
            MULTI_LAYER_SVG,
            manual_layer_mappings={"Layer_Bare": "support_bars"},
        )
        bars = next(layer for layer in result.layers if layer.svg_layer_name == "Layer_Bare")
        self.assertEqual(bars.quote_input_suggestions, {})
        letters = next(layer for layer in result.layers if layer.svg_layer_name == "Layer_Litere")
        self.assertEqual(letters.mapping_status, "unmapped")


class TestManualMappingReadinessPolicy(unittest.TestCase):
    def test_analyzed_with_manual_mapping_still_requires_review_without_geometry(self) -> None:
        spec = {
            "vector_file_name": "litere.svg",
            "vector_file_type": "svg",
            "vector_analysis_status": "analyzed",
            "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
            "vector_layer_mapping_status": "mapped",
        }
        result = evaluate_volumetric_vector_readiness(spec)
        self.assertFalse(result.vector_gate_satisfied)
        self.assertIn(WARN_VECTOR_MANUAL_REVIEW_REQUIRED, result.warnings)
        self.assertNotIn(WARN_VECTOR_LAYER_MAPPING_PENDING, result.warnings)

    def test_manual_review_with_mapping_satisfies_gate(self) -> None:
        spec = {
            "vector_file_name": "litere.svg",
            "vector_file_type": "svg",
            "vector_analysis_status": "analyzed",
            "vector_manual_review_approved": True,
            "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
        }
        result = evaluate_volumetric_vector_readiness(spec)
        self.assertTrue(result.vector_gate_satisfied)
        self.assertTrue(letters_template_manually_mapped(spec["svg_layer_mappings"]))

    def test_pending_mapping_warns_when_no_manual_map(self) -> None:
        spec = {
            "vector_file_name": "litere.svg",
            "vector_file_type": "svg",
            "vector_analysis_status": "analyzed",
        }
        result = evaluate_volumetric_vector_readiness(spec)
        self.assertIn(WARN_VECTOR_LAYER_MAPPING_PENDING, result.warnings)

    def test_support_bars_only_still_pending_letters_mapping(self) -> None:
        spec = {
            "vector_file_name": "litere.svg",
            "vector_file_type": "svg",
            "vector_analysis_status": "analyzed",
            "svg_layer_mappings": {"Layer_Bare": "support_bars"},
            "vector_layer_mapping_status": "pending",
        }
        result = evaluate_volumetric_vector_readiness(spec)
        self.assertIn(WARN_VECTOR_LAYER_MAPPING_PENDING, result.warnings)
        self.assertFalse(result.vector_gate_satisfied)


if __name__ == "__main__":
    unittest.main()
