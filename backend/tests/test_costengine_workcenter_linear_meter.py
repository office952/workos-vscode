from __future__ import annotations

import json
import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.cost_engine_service import (  # noqa: E402
    ComponentCostContext,
    ERR_WORKCENTER_LINEAR_METER_QUANTITY_MISSING,
    ERR_WORKCENTER_RATE_MISSING,
    build_execution_layers_from_components,
)


def _template_with_cut_operation(op_patch: dict | None = None) -> dict:
    op = {
        "code": "LASER_CUT",
        "name": "Laser cut",
        "workcenter": "LASER_CUTTING",
        "estimatedMinutes": 12,
    }
    if op_patch:
        op.update(op_patch)

    return {
        "components_json": json.dumps(
            [
                {
                    "component_id": "comp_1",
                    "type": "STRUCTURA",
                    "name": "Panel",
                    "materials": [],
                    "operations": [op],
                }
            ]
        ),
        "operations_json": "[]",
        "required_materials_json": "[]",
    }


class TestWorkcenterLinearMeterPricing(unittest.TestCase):
    def test_linear_meter_basis_prices_from_perimeter(self):
        ctx = ComponentCostContext(
            workcenter_rates={
                "LASER_CUTTING": {
                    "rate_basis": "per_linear_meter",
                    "rate_per_linear_meter": 10.0,
                }
            },
            quantity=1,
        )
        tpl = _template_with_cut_operation({"total_cut_perimeter_m": 2.5})

        result = build_execution_layers_from_components(tpl, ctx)
        self.assertTrue(result["is_valid"], msg=result["errors"])
        self.assertAlmostEqual(result["total_operation_cost"], 25.0)
        op = result["components"][0]["operations_detail"][0]
        self.assertEqual(op["rate_basis"], "per_linear_meter")
        self.assertAlmostEqual(op["linear_meters"], 2.5)
        self.assertAlmostEqual(op["line_total"], 25.0)

    def test_linear_meter_basis_requires_linear_quantity(self):
        ctx = ComponentCostContext(
            workcenter_rates={
                "LASER_CUTTING": {
                    "rate_basis": "per_linear_meter",
                    "rate_per_linear_meter": 10.0,
                }
            },
            quantity=1,
        )
        tpl = _template_with_cut_operation()

        result = build_execution_layers_from_components(tpl, ctx)
        self.assertFalse(result["is_valid"])
        kinds = [e["kind"] for e in result["errors"]]
        self.assertIn(ERR_WORKCENTER_LINEAR_METER_QUANTITY_MISSING, kinds)

    def test_linear_meter_basis_no_silent_fallback_to_hourly(self):
        ctx = ComponentCostContext(
            workcenter_rates={
                "LASER_CUTTING": {
                    "rate_basis": "per_linear_meter",
                    "rate_per_hour": 120.0,
                }
            },
            quantity=1,
        )
        tpl = _template_with_cut_operation({"total_cut_perimeter_m": 1.0})

        result = build_execution_layers_from_components(tpl, ctx)
        self.assertFalse(result["is_valid"])
        kinds = [e["kind"] for e in result["errors"]]
        self.assertIn(ERR_WORKCENTER_RATE_MISSING, kinds)

    def test_linear_meter_from_letter_perimeter_formula_breakdown(self):
        ctx = ComponentCostContext(
            workcenter_rates={
                "RETURN_PROFILE_MACHINE_FORMING": {
                    "rate_basis": "per_linear_meter",
                    "rate_per_linear_meter": 5.0,
                }
            },
            quantity=1,
            quote_input={"letter_perimeter_m": 18.0},
        )
        op = {
            "code": "side_forming",
            "workcenter": "RETURN_PROFILE_MACHINE_FORMING",
            "calculation_type": "formula_based",
            "formula_id": "letter_perimeter",
            "formula_params": {"extra_pct": 0},
            "requires_quote_input": ["letter_perimeter_m"],
        }
        tpl = _template_with_cut_operation(op)
        result = build_execution_layers_from_components(tpl, ctx)
        self.assertTrue(result["is_valid"], msg=result["errors"])
        op_row = result["components"][0]["operations_detail"][0]
        self.assertAlmostEqual(op_row["linear_meters"], 18.0)
        self.assertAlmostEqual(op_row["line_total"], 90.0)

    def test_legacy_hourly_rate_still_supported(self):
        ctx = ComponentCostContext(
            workcenter_rates={"LASER_CUTTING": 60.0},
            quantity=1,
        )
        tpl = _template_with_cut_operation()

        result = build_execution_layers_from_components(tpl, ctx)
        self.assertTrue(result["is_valid"], msg=result["errors"])
        self.assertAlmostEqual(result["total_operation_cost"], 12.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
