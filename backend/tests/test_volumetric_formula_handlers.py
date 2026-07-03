"""CostEngine — TPL-VOLUMETRIC-LETTERS formula handler registration (Sprint Product 001)."""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_build4_templates import _volumetric_letters_components  # noqa: E402
from services.cost_engine_service import (  # noqa: E402
    ERR_FORMULA_UNKNOWN,
    ERR_MATERIAL_RATE_MISSING,
    ERR_NEEDS_QUOTE_INPUT,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.formula_handlers import (  # noqa: E402
    FORMULA_REGISTRY,
    FormulaId,
    known_formulas,
    resolve_formula,
)


VOLUMETRIC_FORMULA_IDS = [
    "svg_geometry_readiness_gate",
    "perimeter_pass_linear_meter",
    "led_module_count",
    "ceil_quote_input_quantity",
    "mounting_bar_total_length",
    "letter_face_area",
    "letter_perimeter",
    "perimeter_based_time",
    "count_based_time",
    "led_per_letter",
    "psu_count",
    "letter_count_material",
]

FULL_QUOTE_INPUT = {
    "vector_file": "letters.svg",
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "letter_count": 9,
    "led_module_count": 180,
    "return_depth_mm": 60,
    "selected_psu_watts": 100,
    "mounting_template_area_m2": 2.88,
    "face_finish_type": "none",
    "mounting_system": "direct_wall",
    "mounting_template_enabled": True,
    "back_bevel_enabled": False,
}

HAPPY_PATH_CASES = [
    ("svg_geometry_readiness_gate", {}, {"vector_file": "letters.svg"}, 0.0),
    ("letter_face_area", {"waste_pct": 15}, {"letter_face_area_m2": 2.0}, 2.3),
    ("letter_perimeter", {"extra_pct": 10}, {"letter_perimeter_m": 18.0}, 19.8),
    (
        "perimeter_based_time",
        {"speed_m_per_min": 0.3, "passes": 2},
        {"letter_perimeter_m": 9.0},
        60.0,
    ),
    ("count_based_time", {"minutes_per_letter": 8}, {"letter_count": 9}, 72.0),
    (
        "led_per_letter",
        {"module_length_mm": 75, "module_gap_mm": 25},
        {"letter_perimeter_m": 18.0},
        180.0,
    ),
    (
        "psu_count",
        {"watts_per_module": 1.5, "psu_watts": 150},
        {"led_module_count": 27},
        1.0,
    ),
    ("letter_count_material", {}, {"letter_count": 9}, 9.0),
]


def _approx_equal(a: float, b: float, rel: float = 1e-3) -> bool:
    if a == b:
        return True
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) <= rel * scale


class TestVolumetricFormulaRegistry(unittest.TestCase):
    def test_all_volumetric_ids_registered(self):
        known = set(known_formulas())
        for fid in VOLUMETRIC_FORMULA_IDS:
            self.assertIn(fid, known)
        for fid in VOLUMETRIC_FORMULA_IDS:
            self.assertIn(FormulaId(fid), FORMULA_REGISTRY)

    def test_unknown_id_still_fails_for_nonsense(self):
        res = resolve_formula("not_a_formula", {}, {})
        self.assertFalse(res.resolved)
        self.assertEqual(res.error["kind"], "UNKNOWN_FORMULA")


class TestVolumetricHandlersHappyPath(unittest.TestCase):
    def test_resolves_with_quote_input(self):
        for formula_id, params, quote_input, expected_value in HAPPY_PATH_CASES:
            with self.subTest(formula_id=formula_id):
                res = resolve_formula(formula_id, params, quote_input)
                self.assertTrue(res.resolved, res.error)
                self.assertTrue(
                    _approx_equal(float(res.value), expected_value),
                    f"{formula_id}: got {res.value}, want {expected_value}",
                )


MISSING_INPUT_FORMULA_PARAMS = {
    "perimeter_pass_linear_meter": {"pass_count": 2},
    "ceil_quote_input_quantity": {},
}


class TestVolumetricHandlersMissingInput(unittest.TestCase):
    def test_missing_quote_input_fails_clearly(self):
        for formula_id in VOLUMETRIC_FORMULA_IDS:
            with self.subTest(formula_id=formula_id):
                params = MISSING_INPUT_FORMULA_PARAMS.get(formula_id, {})
                res = resolve_formula(formula_id, params, {})
                self.assertFalse(res.resolved)
                self.assertIsNone(res.value)
                self.assertEqual(res.error["kind"], "MISSING_INPUT")
                self.assertGreaterEqual(len(res.error["missing"]), 1)


def _template_from_components(components: list) -> dict:
    return {
        "template_code": "TPL-VOLUMETRIC-LETTERS",
        "components_json": json.dumps(components),
        "operations_json": json.dumps([]),
        "required_materials_json": json.dumps([]),
    }


class TestVolumetricEngineIntegration(unittest.TestCase):
    def test_seed_template_no_formula_unknown_with_full_quote_input(self):
        components = _volumetric_letters_components()
        ctx = ComponentCostContext(
            material_rates={},
            workcenter_rates={"CNC_ROUTER": 90.0, "LED_ASSEMBLY": 60.0},
            quantity=1,
            quote_input=dict(FULL_QUOTE_INPUT),
        )
        out = build_execution_layers_from_components(
            _template_from_components(components), ctx
        )
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertNotIn(ERR_FORMULA_UNKNOWN, kinds)
        self.assertFalse(
            any(
                "WORKCENTER_PIECE_QUANTITY_MISSING" in str(e.get("kind", ""))
                or "WORKCENTER_PIECE_QUANTITY_MISSING" in str(e.get("detail", ""))
                for e in out.get("errors") or []
            )
        )

    def test_missing_quote_input_surfaces_needs_quote_input(self):
        components = _volumetric_letters_components()
        ctx = ComponentCostContext(
            material_rates={},
            workcenter_rates={},
            quantity=1,
            quote_input={},
        )
        out = build_execution_layers_from_components(
            _template_from_components(components), ctx
        )
        self.assertFalse(out["is_valid"])
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_NEEDS_QUOTE_INPUT, kinds)
        self.assertNotIn(ERR_FORMULA_UNKNOWN, kinds)

    def test_missing_material_prices_still_blocks(self):
        components = _volumetric_letters_components()
        ctx = ComponentCostContext(
            material_rates={},
            workcenter_rates={
                "CNC_ROUTER": 90.0,
                "LASER_CUTTING": 90.0,
                "ASSEMBLY": 80.0,
                "LED_ASSEMBLY": 60.0,
                "ELECTRICAL_WIRING": 60.0,
                "PAINTING": 70.0,
                "QC_INSPECTION": 50.0,
                "PACKAGING": 40.0,
                "PREPRESS": 50.0,
            },
            quantity=1,
            quote_input=dict(FULL_QUOTE_INPUT),
        )
        out = build_execution_layers_from_components(
            _template_from_components(components), ctx
        )
        self.assertFalse(out["is_valid"])
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertTrue(
            ERR_MATERIAL_RATE_MISSING in kinds
            or any(
                "unit_cost" in str(e.get("detail", "")).lower()
                for e in out.get("errors") or []
            )
        )
        self.assertNotIn(ERR_FORMULA_UNKNOWN, kinds)

    def test_explicit_requires_quote_input_on_seed_lines(self):
        components = _volumetric_letters_components()
        for comp in components:
            for bucket in ("operations", "materials"):
                for line in comp.get(bucket) or []:
                    if line.get("calculation_type") != "formula_based":
                        continue
                    req = line.get("requires_quote_input")
                    self.assertIsInstance(
                        req,
                        list,
                        f"{comp['component_id']}.{bucket} "
                        f"{line.get('formula_id')} requires_quote_input must be a list",
                    )
                    if line.get("formula_id") in (
                        "ceil_quote_input_quantity",
                        "mounting_bar_total_length",
                    ):
                        continue
                    self.assertGreaterEqual(len(req), 1)


if __name__ == "__main__":
    unittest.main()
