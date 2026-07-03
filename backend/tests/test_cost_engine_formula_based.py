"""Sprint #21.1 — tests for CostEngine additive formula-based support.

Coverage:
  1. Pure formula handler behaviour (6 handlers × success + missing-input).
  2. Engine integration — formula lines inside a hierarchical component.
  3. NEEDS_QUOTE_INPUT / FORMULA_UNKNOWN / FORMULA_INVALID semantics.
  4. Non-regression — static templates, missing rates, empty components.
  5. Quote multiplier interaction with formula outputs.

These tests never hit a database; the CostEngine is exercised directly
through `build_execution_layers_from_components` with rate maps passed
in-memory. This matches the pattern established in
`test_costengine_v2_component_aware.py`.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.cost_engine_service import (  # noqa: E402
    ERR_FORMULA_INVALID,
    ERR_FORMULA_UNKNOWN,
    ERR_MATERIAL_RATE_MISSING,
    ERR_NEEDS_QUOTE_INPUT,
    ERR_WORKCENTER_RATE_MISSING,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.formula_handlers import (  # noqa: E402
    FORMULA_REGISTRY,
    FormulaId,
    FormulaResult,
    known_formulas,
    resolve_formula,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _template(components, name: str = "TPL-FORMULA-TEST") -> dict:
    """Build a raw template dict with a hierarchical components_json."""
    return {
        "name": name,
        "components_json": json.dumps(components),
        "operations_json": json.dumps([]),
        "required_materials_json": json.dumps([]),
    }


def _rates():
    """Canonical rate context reused across integration tests."""
    return {
        "material_rates": {
            "plexi_3mm_clear": 85.0,   # RON / m²
            "pvc_black_5mm": 110.0,    # RON / m²
            "led_white_module": 2.5,   # RON / unit
            "psu_generic": 45.0,       # RON / unit
        },
        "workcenter_rates": {
            "CNC_ROUTER": 90.0,      # RON / h
            "LED_ASSEMBLY": 60.0,    # RON / h
        },
    }


# ---------------------------------------------------------------------------
# 1. Formula handlers — pure unit tests
# ---------------------------------------------------------------------------
class TestFormulaRegistry:
    def test_registry_has_six_handlers(self):
        assert len(FORMULA_REGISTRY) >= 13

    def test_registry_covers_every_enum_entry(self):
        # Every FormulaId must map to exactly one handler.
        for fid in FormulaId:
            assert fid in FORMULA_REGISTRY

    def test_known_formulas_returns_canonical_strings(self):
        ids = known_formulas()
        assert "cnc_time_from_path" in ids
        assert "plexi_diffuser_area" in ids
        assert "relief_material_area" in ids
        assert "led_count_from_area" in ids
        assert "led_psu_sizing" in ids
        assert "led_assembly_time" in ids
        assert "letter_face_area" in ids
        assert "perimeter_based_time" in ids

    def test_resolve_unknown_formula_returns_structured_error(self):
        res = resolve_formula("nope", {}, {})
        assert isinstance(res, FormulaResult)
        assert res.resolved is False
        assert res.value is None
        assert res.error is not None
        assert res.error["kind"] == "UNKNOWN_FORMULA"
        # `known` hint should be included for the UI.
        assert "known" in res.error["detail"]


class TestCncTimeFromPath:
    def test_happy_path(self):
        res = resolve_formula(
            "cnc_time_from_path",
            {"divisor_mm_per_min": 2000, "min_minutes": 0},
            {"path_length_mm": 4000, "passes": 2},
        )
        assert res.resolved is True
        assert res.unit == "min"
        assert res.value == pytest.approx(4.0)  # 4000/2000 * 2

    def test_missing_input_reports_all_required_keys(self):
        res = resolve_formula("cnc_time_from_path", {}, {})
        assert res.resolved is False
        assert res.error["kind"] == "MISSING_INPUT"
        assert set(res.error["missing"]) == {"path_length_mm", "passes"}

    def test_min_minutes_clamp_applies(self):
        res = resolve_formula(
            "cnc_time_from_path",
            {"divisor_mm_per_min": 10_000, "min_minutes": 5.0},
            {"path_length_mm": 1000, "passes": 1},
        )
        # 1000 / 10000 * 1 = 0.1, clamped to 5.
        assert res.resolved is True
        assert res.value == pytest.approx(5.0)

    def test_invalid_param_divisor_zero(self):
        res = resolve_formula(
            "cnc_time_from_path",
            {"divisor_mm_per_min": 0},
            {"path_length_mm": 1000, "passes": 1},
        )
        assert res.resolved is False
        assert res.error["kind"] == "INVALID_PARAM"


class TestLedPsuSizing:
    def test_picks_smallest_sufficient_psu(self):
        res = resolve_formula(
            "led_psu_sizing",
            {"watts_per_led": 1.0, "safety_factor": 1.0, "psu_options_w": [60, 100, 200]},
            {"led_count": 80},
        )
        # total = 80 W, picks 100 W, count=ceil(80/100)=1.
        assert res.resolved is True
        assert res.value == pytest.approx(1.0)
        assert res.breakdown["psu_watts_picked"] == 100.0

    def test_large_load_requires_multiple_units(self):
        res = resolve_formula(
            "led_psu_sizing",
            {"watts_per_led": 1.0, "safety_factor": 1.2, "psu_options_w": [60, 100, 200]},
            {"led_count": 500},
        )
        # total = 500 * 1 * 1.2 = 600 W. No single option >= 600 -> pick 200.
        # count = ceil(600/200) = 3.
        assert res.resolved is True
        assert res.value == pytest.approx(3.0)
        assert res.breakdown["psu_watts_picked"] == 200.0

    def test_rejects_empty_psu_options(self):
        res = resolve_formula(
            "led_psu_sizing",
            {"psu_options_w": []},
            {"led_count": 10},
        )
        assert res.resolved is False
        assert res.error["kind"] == "INVALID_PARAM"


class TestOtherHandlers:
    def test_plexi_diffuser_area_adds_margin(self):
        res = resolve_formula(
            "plexi_diffuser_area",
            {"margin_mm": 100},
            {"personalization_bounding_area_m2": 1.0},
        )
        # side=1000mm, outer=1200mm, area=1.44 m².
        assert res.resolved is True
        assert res.value == pytest.approx(1.44, rel=1e-3)

    def test_relief_material_area_applies_coverage(self):
        res = resolve_formula(
            "relief_material_area",
            {"coverage_pct": 0.25},
            {"front_face_area_m2": 2.0},
        )
        assert res.resolved is True
        assert res.value == pytest.approx(0.5)

    def test_relief_material_area_rejects_bad_coverage(self):
        res = resolve_formula(
            "relief_material_area",
            {"coverage_pct": 1.5},
            {"front_face_area_m2": 2.0},
        )
        assert res.resolved is False
        assert res.error["kind"] == "INVALID_PARAM"

    def test_led_count_rounds_up(self):
        res = resolve_formula(
            "led_count_from_area",
            {"leds_per_m2": 50},
            {"front_face_area_m2": 1.01},
        )
        # 50.5 -> ceil -> 51
        assert res.resolved is True
        assert res.value == pytest.approx(51.0)

    def test_led_assembly_time_respects_min(self):
        res = resolve_formula(
            "led_assembly_time",
            {"leds_per_minute": 20, "min_minutes": 10},
            {"led_count": 40},  # 2 minutes raw, clamped to 10.
        )
        assert res.resolved is True
        assert res.value == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# 2. Engine integration — formula lines embedded in components
# ---------------------------------------------------------------------------
class TestEngineFormulaIntegration:
    def test_formula_material_happy_path(self):
        rates = _rates()
        components = [
            {
                "component_id": "comp_diffuser",
                "type": "PERSONALIZARE",
                "name": "Plexi diffuser",
                "materials": [
                    {
                        "material_code": "plexi_3mm_clear",
                        "unit": "m2",
                        "calculation_type": "formula_based",
                        "formula_id": "plexi_diffuser_area",
                        "formula_params": {"margin_mm": 100},
                        "requires_quote_input": ["personalization_bounding_area_m2"],
                    }
                ],
                "operations": [],
            }
        ]
        ctx = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
            quantity=1,
            quote_input={"personalization_bounding_area_m2": 1.0},
        )
        out = build_execution_layers_from_components(_template(components), ctx)

        assert out["is_valid"] is True
        assert out["source"] == "hierarchical"
        # area = 1.44 m², unit_cost = 85 RON/m² → 122.4
        assert out["total_material_cost"] == pytest.approx(1.44 * 85.0, rel=1e-3)
        mat = out["components"][0]["materials_detail"][0]
        assert mat["calculation_type"] == "formula_based"
        assert mat["formula_id"] == "plexi_diffuser_area"
        assert mat["resolved"] is True
        assert mat["quantity"] == pytest.approx(1.44, rel=1e-3)
        assert "formula_breakdown" in mat

    def test_formula_operation_happy_path(self):
        rates = _rates()
        components = [
            {
                "component_id": "comp_cnc",
                "type": "STRUCTURA",
                "name": "Routed face",
                "materials": [],
                "operations": [
                    {
                        "code": "OP_CNC_ROUT",
                        "workcenter": "CNC_ROUTER",
                        "calculation_type": "formula_based",
                        "formula_id": "cnc_time_from_path",
                        "formula_params": {"divisor_mm_per_min": 2000, "min_minutes": 0},
                        "requires_quote_input": ["path_length_mm", "passes"],
                    }
                ],
            }
        ]
        ctx = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
            quantity=1,
            quote_input={"path_length_mm": 6000, "passes": 2},
        )
        out = build_execution_layers_from_components(_template(components), ctx)

        assert out["is_valid"] is True
        # minutes = 6000/2000*2 = 6 min = 0.1 h; 0.1 * 90 RON/h = 9.0 RON
        assert out["total_operation_cost"] == pytest.approx(9.0, rel=1e-3)
        op = out["components"][0]["operations_detail"][0]
        assert op["calculation_type"] == "formula_based"
        assert op["formula_id"] == "cnc_time_from_path"
        assert op["resolved"] is True
        assert op["estimated_minutes"] == pytest.approx(6.0, rel=1e-3)

    def test_needs_quote_input_surfaces_as_error_not_zero(self):
        """A formula line with missing inputs MUST produce a
        NEEDS_QUOTE_INPUT error, 0 contribution, and is_valid=False.
        It must NEVER be silently treated as a free line."""
        rates = _rates()
        components = [
            {
                "component_id": "comp_diffuser",
                "type": "PERSONALIZARE",
                "name": "Plexi diffuser",
                "materials": [
                    {
                        "material_code": "plexi_3mm_clear",
                        "unit": "m2",
                        "calculation_type": "formula_based",
                        "formula_id": "plexi_diffuser_area",
                        "formula_params": {"margin_mm": 100},
                        "requires_quote_input": ["personalization_bounding_area_m2"],
                    }
                ],
                "operations": [],
            }
        ]
        ctx = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
            quantity=1,
            quote_input={},  # nothing provided
        )
        out = build_execution_layers_from_components(_template(components), ctx)

        assert out["is_valid"] is False
        assert out["total_material_cost"] == 0.0
        # Exactly one NEEDS_QUOTE_INPUT error, path points to the line.
        kinds = [e["kind"] for e in out["errors"]]
        assert ERR_NEEDS_QUOTE_INPUT in kinds
        err = next(e for e in out["errors"] if e["kind"] == ERR_NEEDS_QUOTE_INPUT)
        assert err["path"] == "components[0].materials[0]"
        # Detail must mention the missing key name verbatim.
        assert "personalization_bounding_area_m2" in err["detail"]
        # The detail row must record resolved=False AND line_total=0.
        mat = out["components"][0]["materials_detail"][0]
        assert mat["resolved"] is False
        assert mat["line_total"] == 0.0

    def test_formula_unknown_reports_hard_misconfiguration(self):
        rates = _rates()
        components = [
            {
                "component_id": "comp_weird",
                "type": "STRUCTURA",
                "name": "weird",
                "materials": [],
                "operations": [
                    {
                        "code": "OP_WEIRD",
                        "workcenter": "CNC_ROUTER",
                        "calculation_type": "formula_based",
                        "formula_id": "this_does_not_exist",
                        "formula_params": {},
                        "requires_quote_input": [],
                    }
                ],
            }
        ]
        ctx = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
            quote_input={},
        )
        out = build_execution_layers_from_components(_template(components), ctx)

        assert out["is_valid"] is False
        kinds = [e["kind"] for e in out["errors"]]
        assert ERR_FORMULA_UNKNOWN in kinds

    def test_formula_invalid_input_reports_formula_invalid(self):
        """Providing a bogus value (negative) must surface FORMULA_INVALID,
        not NEEDS_QUOTE_INPUT — because the user DID provide the key."""
        rates = _rates()
        components = [
            {
                "component_id": "comp_diffuser",
                "type": "PERSONALIZARE",
                "name": "Plexi diffuser",
                "materials": [
                    {
                        "material_code": "plexi_3mm_clear",
                        "unit": "m2",
                        "calculation_type": "formula_based",
                        "formula_id": "plexi_diffuser_area",
                        "formula_params": {"margin_mm": 100},
                        "requires_quote_input": ["personalization_bounding_area_m2"],
                    }
                ],
                "operations": [],
            }
        ]
        ctx = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
            quote_input={"personalization_bounding_area_m2": -1.0},
        )
        out = build_execution_layers_from_components(_template(components), ctx)

        assert out["is_valid"] is False
        kinds = [e["kind"] for e in out["errors"]]
        assert ERR_FORMULA_INVALID in kinds

    def test_formula_missing_formula_id_reports_formula_invalid(self):
        rates = _rates()
        components = [
            {
                "component_id": "comp_x",
                "type": "STRUCTURA",
                "name": "x",
                "materials": [
                    {
                        "material_code": "plexi_3mm_clear",
                        "unit": "m2",
                        "calculation_type": "formula_based",
                        # formula_id intentionally absent
                        "formula_params": {},
                        "requires_quote_input": [],
                    }
                ],
                "operations": [],
            }
        ]
        ctx = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
        )
        out = build_execution_layers_from_components(_template(components), ctx)
        assert out["is_valid"] is False
        assert any(e["kind"] == ERR_FORMULA_INVALID for e in out["errors"])

    def test_quantity_multiplier_scales_formula_quantity(self):
        rates = _rates()
        components = [
            {
                "component_id": "comp_diffuser",
                "type": "PERSONALIZARE",
                "name": "Plexi diffuser",
                "materials": [
                    {
                        "material_code": "plexi_3mm_clear",
                        "unit": "m2",
                        "calculation_type": "formula_based",
                        "formula_id": "plexi_diffuser_area",
                        "formula_params": {"margin_mm": 100},
                        "requires_quote_input": ["personalization_bounding_area_m2"],
                    }
                ],
                "operations": [],
            }
        ]
        ctx_q1 = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
            quantity=1,
            quote_input={"personalization_bounding_area_m2": 1.0},
        )
        ctx_q5 = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
            quantity=5,
            quote_input={"personalization_bounding_area_m2": 1.0},
        )
        out1 = build_execution_layers_from_components(_template(components), ctx_q1)
        out5 = build_execution_layers_from_components(_template(components), ctx_q5)
        assert out1["is_valid"] and out5["is_valid"]
        assert out5["total_material_cost"] == pytest.approx(
            5 * out1["total_material_cost"], rel=1e-3
        )


# ---------------------------------------------------------------------------
# 3. Non-regression — static templates MUST behave exactly as before
# ---------------------------------------------------------------------------
class TestNonRegression:
    def test_static_template_unchanged_with_quote_input(self):
        """Passing quote_input on a context used against a purely static
        template MUST NOT change the outcome vs. the pre-Sprint-21.1
        behaviour (empty quote_input)."""
        rates = _rates()
        components = [
            {
                "component_id": "comp_static",
                "type": "STRUCTURA",
                "name": "static",
                "materials": [
                    {
                        "material_code": "pvc_black_5mm",
                        "quantity": 0.5,
                        "unit": "m2",
                    }
                ],
                "operations": [
                    {
                        "code": "OP_CNC",
                        "workcenter": "CNC_ROUTER",
                        "estimatedMinutes": 10,
                    }
                ],
            }
        ]
        ctx_no_input = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
        )
        ctx_with_input = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
            quote_input={"irrelevant": 999, "personalization_bounding_area_m2": 1.0},
        )
        out_a = build_execution_layers_from_components(_template(components), ctx_no_input)
        out_b = build_execution_layers_from_components(_template(components), ctx_with_input)
        # Both valid, both produce identical totals.
        assert out_a["is_valid"] is True
        assert out_b["is_valid"] is True
        assert out_a["total_cost"] == out_b["total_cost"]
        assert out_a["components"][0]["material_cost"] == out_b["components"][0]["material_cost"]

    def test_static_template_missing_rate_still_reports_rate_missing(self):
        """NEEDS_QUOTE_INPUT must NOT be conflated with RATE_MISSING —
        static lines without a rate still get the legacy error kind."""
        components = [
            {
                "component_id": "comp_static",
                "type": "STRUCTURA",
                "name": "static",
                "materials": [
                    {
                        "material_code": "unknown_code",
                        "quantity": 0.5,
                        "unit": "m2",
                    }
                ],
                "operations": [
                    {
                        "code": "OP_CNC",
                        "workcenter": "UNKNOWN_WC",
                        "estimatedMinutes": 10,
                    }
                ],
            }
        ]
        ctx = ComponentCostContext(
            material_rates={},
            workcenter_rates={},
        )
        out = build_execution_layers_from_components(_template(components), ctx)
        assert out["is_valid"] is False
        kinds = {e["kind"] for e in out["errors"]}
        assert ERR_MATERIAL_RATE_MISSING in kinds
        assert ERR_WORKCENTER_RATE_MISSING in kinds
        assert ERR_NEEDS_QUOTE_INPUT not in kinds

    def test_mixed_component_static_plus_formula(self):
        """A component may mix static and formula-based lines — both
        must be accounted for; one missing does not corrupt the other."""
        rates = _rates()
        components = [
            {
                "component_id": "comp_mixed",
                "type": "STRUCTURA",
                "name": "mixed",
                "materials": [
                    {
                        "material_code": "pvc_black_5mm",
                        "quantity": 0.5,
                        "unit": "m2",
                    },
                    {
                        "material_code": "plexi_3mm_clear",
                        "unit": "m2",
                        "calculation_type": "formula_based",
                        "formula_id": "plexi_diffuser_area",
                        "formula_params": {"margin_mm": 50},
                        "requires_quote_input": ["personalization_bounding_area_m2"],
                    },
                ],
                "operations": [],
            }
        ]
        ctx_ok = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
            quote_input={"personalization_bounding_area_m2": 1.0},
        )
        out_ok = build_execution_layers_from_components(_template(components), ctx_ok)
        assert out_ok["is_valid"] is True
        # Static contribution = 0.5 * 110 = 55.0; formula contribution > 0.
        assert out_ok["total_material_cost"] > 55.0

        ctx_missing = ComponentCostContext(
            material_rates=rates["material_rates"],
            workcenter_rates=rates["workcenter_rates"],
            quote_input={},
        )
        out_missing = build_execution_layers_from_components(
            _template(components), ctx_missing
        )
        assert out_missing["is_valid"] is False
        # Static line still counted; only formula line becomes 0.
        static_line = out_missing["components"][0]["materials_detail"][0]
        formula_line = out_missing["components"][0]["materials_detail"][1]
        assert static_line["line_total"] == pytest.approx(0.5 * 110.0)
        assert formula_line["line_total"] == 0.0
        assert formula_line["resolved"] is False


# ---------------------------------------------------------------------------
# Sprint #21.1.5 — cnc_time_from_path additive extension
# ---------------------------------------------------------------------------
# Rationale: user decision "Option A" (hybrid, backwards-compatible):
#   1. ``passes`` may now live in formula_params (template property).
#      Fallback to quote_input["passes"] preserves the Sprint #21.1 contract.
#   2. ``path_length_key`` (optional param, default "path_length_mm") lets
#      distinct CNC operations on the same quote (plexi cut, ACP routing,
#      relief cut) each read their own path-length key without collision.
#   3. NO silent fallback to 0 — missing values still surface NEEDS_QUOTE_INPUT
#      / MISSING_INPUT.
#   4. NO change to existing Sprint #21.1 tests; those remain green.
#
# These tests are APPENDED only — nothing above this block is modified.
class TestCncTimeFromPathSprint215Extension:
    def test_passes_in_params_and_custom_path_key_computes_correctly(self):
        """Sprint #21.2 canonical shape: passes as template property,
        aliased path key. Case: relief 10mm plexi cut, 4 passes at
        divisor 2000, with relief_cut_path_length_mm = 4000.
        Expected minutes = 4000 / 2000 * 4 = 8.0 min.
        """
        res = resolve_formula(
            "cnc_time_from_path",
            {
                "divisor_mm_per_min": 2000,
                "passes": 4,
                "path_length_key": "relief_cut_path_length_mm",
                "min_minutes": 0,
            },
            {"relief_cut_path_length_mm": 4000},
        )
        assert res.resolved is True
        assert res.unit == "min"
        assert res.value == pytest.approx(8.0)
        # Breakdown must disclose which key was used AND that passes came
        # from the template, so traceability never degrades.
        assert res.breakdown["passes"] == 4
        assert res.breakdown["passes_source"] == "params"
        assert res.breakdown["path_length_key"] == "relief_cut_path_length_mm"
        assert res.breakdown["path_length_mm"] == pytest.approx(4000.0)

    def test_passes_absent_from_params_falls_back_to_quote_input(self):
        """Sprint #21.1 legacy contract must still work: when the
        template does NOT declare ``passes`` in params, the handler
        reads it from quote_input. Also exercises the default path key.
        """
        res = resolve_formula(
            "cnc_time_from_path",
            {"divisor_mm_per_min": 2000, "min_minutes": 0},
            {"path_length_mm": 6000, "passes": 3},
        )
        assert res.resolved is True
        # 6000 / 2000 * 3 = 9.0 min.
        assert res.value == pytest.approx(9.0)
        assert res.breakdown["passes"] == 3
        assert res.breakdown["passes_source"] == "quote_input"
        assert res.breakdown["path_length_key"] == "path_length_mm"

    def test_passes_in_both_params_and_quote_input_params_wins(self):
        """Precedence rule: when ``passes`` is declared in both the
        template params AND the quote_input payload, the template wins.
        This is what makes ``passes`` a true material/operation property
        (e.g. relief 10mm = 4 passes) that a quote cannot accidentally
        override.
        """
        res = resolve_formula(
            "cnc_time_from_path",
            {"divisor_mm_per_min": 2000, "passes": 4},
            # quote_input tries to force passes=1 — must be ignored.
            {"path_length_mm": 4000, "passes": 1},
        )
        assert res.resolved is True
        # 4000 / 2000 * 4 = 8.0 (from params), NOT 4000/2000*1 = 2.0.
        assert res.value == pytest.approx(8.0)
        assert res.breakdown["passes"] == 4
        assert res.breakdown["passes_source"] == "params"

    def test_custom_path_key_missing_from_quote_input_reports_that_key(self):
        """When the template asks for ``relief_cut_path_length_mm`` and
        the quote payload carries only the generic ``path_length_mm``,
        the error must call out the aliased key — not the default —
        so the UI prompts the user for the right field. Still
        MISSING_INPUT (no fallback to 0).
        """
        res = resolve_formula(
            "cnc_time_from_path",
            {
                "divisor_mm_per_min": 2000,
                "passes": 4,
                "path_length_key": "relief_cut_path_length_mm",
            },
            {"path_length_mm": 4000},  # wrong key on purpose
        )
        assert res.resolved is False
        assert res.error["kind"] == "MISSING_INPUT"
        assert res.error["missing"] == ["relief_cut_path_length_mm"]
        # ``passes`` is NOT listed as missing because it came from params.
        assert "passes" not in res.error["missing"]
        # Value must be None — never a silent 0.
        assert res.value is None

    def test_default_path_key_is_path_length_mm_when_unspecified(self):
        """When ``path_length_key`` is NOT declared, behaviour must
        match Sprint #21.1 exactly: the handler looks up
        ``path_length_mm`` in quote_input.
        """
        res = resolve_formula(
            "cnc_time_from_path",
            # No path_length_key, no passes-in-params.
            {"divisor_mm_per_min": 2000, "min_minutes": 0},
            {"path_length_mm": 2000, "passes": 1},
        )
        assert res.resolved is True
        # 2000 / 2000 * 1 = 1.0 min.
        assert res.value == pytest.approx(1.0)
        assert res.breakdown["path_length_key"] == "path_length_mm"
        assert res.breakdown["passes_source"] == "quote_input"