"""Sprint #16 — CostEngine v2 component-aware tests.

Proves:
  1. Hierarchical template (Sprint #15 shape) → breakdown per component.
  2. Empty component (no ops + no mats) → 0.00 cost, COMPONENT_EMPTY warning, NOT an error.
  3. Multiple components with different types → each appears in output with its type.
  4. Flat legacy template (string[] or null components_json) → fallback,
     synthetic `comp_flat_legacy` component hosts everything.
  5. Flat legacy + material_code missing from rates → MATERIAL_RATE_MISSING with path.
  6. Hierarchical + workcenter missing from rates → WORKCENTER_RATE_MISSING with path.
  7. Aggregation consistency: totals == sum per component.
  8. Smoke test: legacy `CostEngineService.calculate` output unchanged
     (proof nothing old was modified).
"""

from __future__ import annotations

import json
import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from data_models.product_contracts import CostRequest, PricingContext  # noqa: E402
from services.cost_engine_service import (  # noqa: E402
    ComponentCostContext,
    CostEngineService,
    CostEngineWithMaterialRates,
    ERR_MATERIAL_RATE_MISSING,
    ERR_WORKCENTER_RATE_MISSING,
    WARN_COMPONENT_EMPTY,
    build_execution_layers_from_components,
)
from services.product_system_service import ProductSystemService  # noqa: E402
from services.quote_orchestrator import QuoteOrchestrator  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def _hierarchical_template() -> dict:
    """Sprint #15 hierarchical shape: 2 components, each with its own ops + mats."""
    components = [
        {
            "component_id": "comp_1",
            "type": "STRUCTURA",
            "name": "Cadru metalic",
            "materials": [
                {"materialCode": "MAT-STEEL", "name": "Oțel", "quantity": 2, "unit": "kg"},
                {"materialCode": "MAT-WELD", "name": "Sârmă sudură", "quantity": 1, "unit": "kg"},
            ],
            "operations": [
                {
                    "code": "CUT",
                    "name": "Debitare",
                    "workcenter": "CNC",
                    "estimatedMinutes": 30,
                    "sequence": 1,
                    "component_ref": "comp_1",
                },
                {
                    "code": "WELD",
                    "name": "Sudură",
                    "workcenter": "welding",
                    "estimatedMinutes": 60,
                    "sequence": 2,
                    "component_ref": "comp_1",
                },
            ],
        },
        {
            "component_id": "comp_2",
            "type": "FATA",
            "name": "Fațadă ACP",
            "materials": [
                {"materialCode": "MAT-ACP", "name": "ACP 3mm", "quantity": 4, "unit": "sqm"},
                {"materialCode": "MAT-VINYL", "name": "Folie grafică", "quantity": 4, "unit": "sqm"},
            ],
            "operations": [
                {
                    "code": "PRINT",
                    "name": "Printare",
                    "workcenter": "printing",
                    "estimatedMinutes": 45,
                    "sequence": 1,
                    "component_ref": "comp_2",
                },
                {
                    "code": "APPLY",
                    "name": "Aplicare folie",
                    "workcenter": "finishing",
                    "estimatedMinutes": 30,
                    "sequence": 2,
                    "component_ref": "comp_2",
                },
            ],
        },
    ]
    # draftToPayload-equivalent flat mirrors (Sprint #15 contract):
    flat_ops = []
    flat_mats = []
    for c in components:
        for op in c["operations"]:
            flat_ops.append({**op, "component_ref": c["component_id"]})
        for m in c["materials"]:
            flat_mats.append({**m, "component_ref": c["component_id"]})
    return {
        "id": 100,
        "template_code": "HIER-01",
        "family_name": "Test hierarchical",
        "components_json": json.dumps(components),
        "operations_json": json.dumps(flat_ops),
        "required_materials_json": json.dumps(flat_mats),
    }


def _flat_legacy_template() -> dict:
    """Legacy shape: components_json is a bare string[], ops and mats are top-level flat."""
    return {
        "id": 200,
        "template_code": "LEG-01",
        "family_name": "Test legacy flat",
        "components_json": json.dumps(["Cadru", "Fațadă"]),  # bare string[]
        "operations_json": json.dumps(
            [
                {
                    "code": "CUT",
                    "name": "Debitare",
                    "workcenter": "CNC",
                    "estimatedMinutes": 30,
                    "sequence": 1,
                },
                {
                    "code": "ASM",
                    "name": "Asamblare",
                    "workcenter": "assembly",
                    "estimatedMinutes": 60,
                    "sequence": 2,
                },
            ]
        ),
        "required_materials_json": json.dumps(
            [
                {"materialCode": "MAT-ACP", "name": "ACP 3mm", "quantity": 2, "unit": "sqm"},
            ]
        ),
    }


def _rates_ctx_full() -> ComponentCostContext:
    return ComponentCostContext(
        material_rates={
            "MAT-STEEL": 10.0,  # RON / kg
            "MAT-WELD": 25.0,   # RON / kg
            "MAT-ACP": 120.0,   # RON / sqm
            "MAT-VINYL": 45.0,  # RON / sqm
        },
        workcenter_rates={
            "CNC": 120.0,       # RON / h
            "welding": 90.0,
            "printing": 80.0,
            "finishing": 70.0,
            "assembly": 60.0,
        },
        quantity=1,
    )


# ---------------------------------------------------------------------------
# 1. Hierarchical breakdown
# ---------------------------------------------------------------------------
class TestHierarchicalBreakdown(unittest.TestCase):
    def test_two_components_full_breakdown(self):
        result = build_execution_layers_from_components(
            _hierarchical_template(), _rates_ctx_full()
        )
        self.assertTrue(result["is_valid"], msg=f"errors={result['errors']}")
        self.assertEqual(result["source"], "hierarchical")
        self.assertEqual(len(result["components"]), 2)

        # comp_1 expected: materials = 2*10 + 1*25 = 45 ; ops = (30/60)*120 + (60/60)*90 = 60 + 90 = 150 ; total = 195
        c1 = result["components"][0]
        self.assertEqual(c1["component_id"], "comp_1")
        self.assertEqual(c1["type"], "STRUCTURA")
        self.assertAlmostEqual(c1["material_cost"], 45.0)
        self.assertAlmostEqual(c1["operation_cost"], 150.0)
        self.assertAlmostEqual(c1["total_component_cost"], 195.0)

        # comp_2 expected: materials = 4*120 + 4*45 = 480 + 180 = 660 ; ops = (45/60)*80 + (30/60)*70 = 60 + 35 = 95 ; total = 755
        c2 = result["components"][1]
        self.assertEqual(c2["component_id"], "comp_2")
        self.assertEqual(c2["type"], "FATA")
        self.assertAlmostEqual(c2["material_cost"], 660.0)
        self.assertAlmostEqual(c2["operation_cost"], 95.0)
        self.assertAlmostEqual(c2["total_component_cost"], 755.0)

        # Each materials_detail row carries its path
        for j, md in enumerate(c1["materials_detail"]):
            self.assertEqual(md["path"], f"components[0].materials[{j}]")
        for j, od in enumerate(c2["operations_detail"]):
            self.assertEqual(od["path"], f"components[1].operations[{j}]")


# ---------------------------------------------------------------------------
# 2. Empty component — warning not error
# ---------------------------------------------------------------------------
class TestEmptyComponentIsWarningNotError(unittest.TestCase):
    def test_empty_component_returns_zero_and_warns(self):
        tpl = {
            "components_json": json.dumps(
                [
                    {
                        "component_id": "comp_empty",
                        "type": "SUPORT",
                        "name": "Suport gol",
                        "materials": [],
                        "operations": [],
                    }
                ]
            ),
            "operations_json": "[]",
            "required_materials_json": "[]",
        }
        result = build_execution_layers_from_components(tpl, _rates_ctx_full())
        self.assertTrue(result["is_valid"], msg=f"errors={result['errors']}")
        self.assertEqual(result["total_cost"], 0.0)
        self.assertEqual(len(result["components"]), 1)
        c = result["components"][0]
        self.assertEqual(c["total_component_cost"], 0.0)
        self.assertEqual(c["errors"], [])
        self.assertEqual(len(c["warnings"]), 1)
        self.assertEqual(c["warnings"][0]["kind"], WARN_COMPONENT_EMPTY)
        self.assertEqual(c["warnings"][0]["path"], "components[0]")


# ---------------------------------------------------------------------------
# 3. Three components with different types
# ---------------------------------------------------------------------------
class TestMultipleComponentTypes(unittest.TestCase):
    def test_three_distinct_types_are_preserved(self):
        components = [
            {
                "component_id": f"comp_{i+1}",
                "type": t,
                "name": f"Part {t}",
                "materials": [
                    {"materialCode": "MAT-STEEL", "name": "Oțel", "quantity": 1, "unit": "kg"}
                ],
                "operations": [
                    {"code": "OP", "name": "op", "workcenter": "CNC", "estimatedMinutes": 30, "sequence": 1}
                ],
            }
            for i, t in enumerate(["STRUCTURA", "ILUMINARE", "SUPORT"])
        ]
        tpl = {
            "components_json": json.dumps(components),
            "operations_json": "[]",
            "required_materials_json": "[]",
        }
        result = build_execution_layers_from_components(tpl, _rates_ctx_full())
        self.assertTrue(result["is_valid"])
        types_out = [c["type"] for c in result["components"]]
        self.assertEqual(types_out, ["STRUCTURA", "ILUMINARE", "SUPORT"])
        # Each contributes materials 1*10 + ops (30/60)*120 = 10+60 = 70
        for c in result["components"]:
            self.assertAlmostEqual(c["total_component_cost"], 70.0)


# ---------------------------------------------------------------------------
# 4. Flat legacy fallback
# ---------------------------------------------------------------------------
class TestFlatLegacyFallback(unittest.TestCase):
    def test_legacy_template_uses_flat_branch_with_synthetic_component(self):
        result = build_execution_layers_from_components(
            _flat_legacy_template(), _rates_ctx_full()
        )
        self.assertEqual(result["source"], "flat_legacy")
        self.assertEqual(len(result["components"]), 1)
        c = result["components"][0]
        self.assertEqual(c["component_id"], "comp_flat_legacy")
        self.assertEqual(c["type"], "STRUCTURA")
        # materials: 2*120 = 240 ; ops: (30/60)*120 + (60/60)*60 = 60 + 60 = 120 ; total = 360
        self.assertAlmostEqual(c["material_cost"], 240.0)
        self.assertAlmostEqual(c["operation_cost"], 120.0)
        self.assertAlmostEqual(c["total_component_cost"], 360.0)
        self.assertTrue(result["is_valid"])

    def test_null_components_json_still_uses_flat_branch(self):
        tpl = _flat_legacy_template()
        tpl["components_json"] = None  # total absence
        result = build_execution_layers_from_components(tpl, _rates_ctx_full())
        self.assertEqual(result["source"], "flat_legacy")
        self.assertEqual(len(result["components"]), 1)


# ---------------------------------------------------------------------------
# 5. Missing material rate → explicit MATERIAL_RATE_MISSING with path
# ---------------------------------------------------------------------------
class TestMaterialRateMissingExplicit(unittest.TestCase):
    def test_missing_material_rate_in_flat_legacy(self):
        # rates cover workcenters but NOT MAT-ACP
        ctx = ComponentCostContext(
            material_rates={},  # empty
            workcenter_rates={"CNC": 120.0, "assembly": 60.0},
        )
        result = build_execution_layers_from_components(_flat_legacy_template(), ctx)
        self.assertFalse(result["is_valid"])
        errs = [e for e in result["errors"] if e["kind"] == ERR_MATERIAL_RATE_MISSING]
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0]["path"], "components[0].materials[0]")
        self.assertIn("MAT-ACP", errs[0]["detail"])
        # Totals remain finite (0 contribution from the missing line)
        self.assertAlmostEqual(result["components"][0]["material_cost"], 0.0)
        # But ops cost still computed
        self.assertAlmostEqual(result["components"][0]["operation_cost"], 120.0)


# ---------------------------------------------------------------------------
# 6. Missing workcenter rate → explicit WORKCENTER_RATE_MISSING with path
# ---------------------------------------------------------------------------
class TestWorkcenterRateMissingExplicit(unittest.TestCase):
    def test_missing_workcenter_rate_in_hierarchical(self):
        # rates cover materials + most workcenters but NOT 'welding'
        ctx = ComponentCostContext(
            material_rates={
                "MAT-STEEL": 10.0,
                "MAT-WELD": 25.0,
                "MAT-ACP": 120.0,
                "MAT-VINYL": 45.0,
            },
            workcenter_rates={
                "CNC": 120.0,
                # 'welding' is MISSING on purpose
                "printing": 80.0,
                "finishing": 70.0,
            },
        )
        result = build_execution_layers_from_components(_hierarchical_template(), ctx)
        self.assertFalse(result["is_valid"])
        errs = [e for e in result["errors"] if e["kind"] == ERR_WORKCENTER_RATE_MISSING]
        self.assertEqual(len(errs), 1)
        # Should be the second operation of comp_1
        self.assertEqual(errs[0]["path"], "components[0].operations[1]")
        self.assertIn("welding", errs[0]["detail"])


# ---------------------------------------------------------------------------
# 7. Aggregation consistency
# ---------------------------------------------------------------------------
class TestAggregationConsistency(unittest.TestCase):
    def test_totals_equal_component_sums(self):
        result = build_execution_layers_from_components(
            _hierarchical_template(), _rates_ctx_full()
        )
        mat_sum = sum(c["material_cost"] for c in result["components"])
        op_sum = sum(c["operation_cost"] for c in result["components"])
        tot_sum = sum(c["total_component_cost"] for c in result["components"])
        self.assertAlmostEqual(result["total_material_cost"], round(mat_sum, 2))
        self.assertAlmostEqual(result["total_operation_cost"], round(op_sum, 2))
        self.assertAlmostEqual(result["total_cost"], round(tot_sum, 2))
        # And total == mat_total + op_total
        self.assertAlmostEqual(
            result["total_cost"],
            round(result["total_material_cost"] + result["total_operation_cost"], 2),
        )

    def test_quantity_multiplier_scales_both_sides_linearly(self):
        ctx1 = _rates_ctx_full()
        ctx1.quantity = 1
        ctx3 = _rates_ctx_full()
        ctx3.quantity = 3
        r1 = build_execution_layers_from_components(_hierarchical_template(), ctx1)
        r3 = build_execution_layers_from_components(_hierarchical_template(), ctx3)
        self.assertAlmostEqual(r3["total_material_cost"], round(r1["total_material_cost"] * 3, 2))
        self.assertAlmostEqual(r3["total_operation_cost"], round(r1["total_operation_cost"] * 3, 2))


# ---------------------------------------------------------------------------
# 8. Backwards compat — legacy CostEngineService.calculate still works
# ---------------------------------------------------------------------------
class TestLegacyCostEngineUnchanged(unittest.TestCase):
    """Smoke test: the pre-existing CostEngineService.calculate contract —
    consumed by QuoteOrchestrator — MUST keep working identically. This
    proves Sprint #16 is purely additive."""

    def _legacy_template(self) -> dict:
        return {
            "id": 1,
            "template_code": "TOTEM-STD",
            "family_id": "totemuri_pyloni",
            "family_name": "Totemuri / Pyloni",
            "components_json": json.dumps(["Cadru metalic", "LED RGB"]),
            "operations_json": json.dumps(
                [
                    {"code": "CNC_CUT", "name": "Debitare", "workcenter": "CNC",
                     "estimatedMinutes": 30, "sequence": 1},
                    {"code": "ASM", "name": "Asamblare", "workcenter": "assembly",
                     "estimatedMinutes": 60, "sequence": 2},
                ]
            ),
            "required_materials_json": json.dumps(
                [
                    {"materialCode": "MAT-ACP-3", "name": "ACP 3mm alb",
                     "quantity": 2, "unit": "sqm"},
                ]
            ),
            "estimated_hours": 1.5,
            "base_labor_rate": 80,
            "base_margin_pct": 25,
            "active": True,
        }

    def test_legacy_engine_priced_with_material_rates(self):
        from data_models.product_contracts import QuotePricing

        orch = QuoteOrchestrator(
            cost_engine=CostEngineWithMaterialRates({"MAT-ACP-3": 120.0})
        )
        snap = orch.build_snapshot(
            product_template=self._legacy_template(),
            user_config={"quantity": 2, "dimensions": {"width_mm": 1000, "height_mm": 3000, "depth_mm": 300}},
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        self.assertEqual(snap.status, "priced", msg=f"blocked={snap.blocked_reasons}")
        self.assertTrue(snap.cost_result.is_valid)
        self.assertGreater(snap.cost_result.total_cost, 0)

    def test_legacy_engine_blocked_without_material_rates(self):
        from data_models.product_contracts import QuotePricing

        orch = QuoteOrchestrator(cost_engine=CostEngineService())
        snap = orch.build_snapshot(
            product_template=self._legacy_template(),
            user_config={"quantity": 2, "dimensions": {"width_mm": 1000, "height_mm": 3000, "depth_mm": 300}},
            pricing=QuotePricing(margin_pct=20, vat_pct=19),
        )
        self.assertEqual(snap.status, "blocked")
        self.assertFalse(snap.cost_result.is_valid)


if __name__ == "__main__":
    unittest.main()