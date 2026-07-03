"""Sprint #17 — Quote Orchestrator v2 component-aware integration tests.

Proves:
  1. Hierarchical template + full rates  -> priced + v2 breakdown (2 comps).
  2. Flat legacy template                 -> IDENTICAL behaviour to pre-sprint
                                              (v1 engine, breakdown is None).
  3. Hierarchical + missing material rate -> blocked + MATERIAL_RATE_MISSING
                                              with path preserved.
  4. Hierarchical + missing workcenter    -> blocked + WORKCENTER_RATE_MISSING
                                              with path preserved.
  5. Pre-sprint snapshot (no v2 extras)   -> readable via getattr, no crash.
  6. Hierarchical + empty component       -> priced + COMPONENT_EMPTY warning
                                              persisted on the snapshot.
"""
from __future__ import annotations

import json
import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from data_models.product_contracts import QuotePricing  # noqa: E402
from services.cost_engine_service import (  # noqa: E402
    CostEngineService,
    CostEngineWithMaterialRates,
)
from services.quote_orchestrator import QuoteOrchestrator  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def _hierarchical_template() -> dict:
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
                {"code": "CUT", "name": "Debitare", "workcenter": "CNC",
                 "estimatedMinutes": 30, "sequence": 1, "component_ref": "comp_1"},
                {"code": "WELD", "name": "Sudură", "workcenter": "welding",
                 "estimatedMinutes": 60, "sequence": 2, "component_ref": "comp_1"},
            ],
        },
        {
            "component_id": "comp_2",
            "type": "FATA",
            "name": "Fațadă ACP",
            "materials": [
                {"materialCode": "MAT-ACP", "name": "ACP 3mm", "quantity": 4, "unit": "sqm"},
            ],
            "operations": [
                {"code": "PRINT", "name": "Printare", "workcenter": "printing",
                 "estimatedMinutes": 45, "sequence": 1, "component_ref": "comp_2"},
            ],
        },
    ]
    flat_ops, flat_mats = [], []
    for c in components:
        for op in c["operations"]:
            flat_ops.append({**op, "component_ref": c["component_id"]})
        for m in c["materials"]:
            flat_mats.append({**m, "component_ref": c["component_id"]})
    return {
        "id": 10,
        "template_code": "HIER-01",
        "family_id": "totemuri_pyloni",
        "family_name": "Totemuri / Pyloni",
        "components_json": json.dumps(components),
        "operations_json": json.dumps(flat_ops),
        "required_materials_json": json.dumps(flat_mats),
        "estimated_hours": 2.5,
        "base_labor_rate": 80,
        "base_margin_pct": 25,
        "active": True,
    }


def _flat_legacy_template() -> dict:
    """Legacy flat shape — identical to the fixture used by
    test_productsystem_costengine_foundation.py / test_quote_orders_integration.py.
    """
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


def _sample_user_config() -> dict:
    return {
        "quantity": 2,
        "dimensions": {"width_mm": 1000, "height_mm": 3000, "depth_mm": 300},
    }


def _full_v2_rates() -> dict:
    return dict(
        material_rates={
            "MAT-STEEL": 10.0,
            "MAT-WELD": 25.0,
            "MAT-ACP": 120.0,
        },
        workcenter_rates={
            "CNC": 120.0,
            "welding": 90.0,
            "printing": 80.0,
            "assembly": 60.0,
            "finishing": 70.0,
        },
    )


# ---------------------------------------------------------------------------
# 1. Hierarchical + full rates -> priced + v2 breakdown
# ---------------------------------------------------------------------------
class TestHierarchicalPricedWithBreakdown(unittest.TestCase):
    def test_priced_with_component_breakdown(self):
        orch = QuoteOrchestrator(**_full_v2_rates())
        snap = orch.build_snapshot(
            product_template=_hierarchical_template(),
            user_config=_sample_user_config(),
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        self.assertEqual(snap.status, "priced", msg=f"blocked={snap.blocked_reasons}")
        self.assertTrue(snap.cost_result.is_valid)
        self.assertGreater(snap.cost_result.total_cost, 0)
        self.assertGreater(snap.price.gross, snap.price.net)

        # v2 extras must be attached
        self.assertEqual(getattr(snap, "cost_engine_version", None), "v2")
        breakdown = getattr(snap, "component_breakdown", None)
        self.assertIsNotNone(breakdown)
        self.assertEqual(len(breakdown), 2)
        self.assertEqual(breakdown[0]["component_id"], "comp_1")
        self.assertEqual(breakdown[1]["component_id"], "comp_2")
        self.assertGreater(breakdown[0]["total_component_cost"], 0)
        self.assertGreater(breakdown[1]["total_component_cost"], 0)

        # JSON variant must be serializable and match the dict
        breakdown_json = getattr(snap, "component_breakdown_json", None)
        self.assertIsInstance(breakdown_json, str)
        self.assertEqual(json.loads(breakdown_json), breakdown)

        # Cost aggregates from v2 are reflected in CostResult
        # Expected (quantity=2):
        #   comp_1 materials = (2*10 + 1*25) * 2 = 90 ; ops = ((30/60)*120 + (60/60)*90) * 2 = 300
        #   comp_2 materials = (4*120) * 2         = 960 ; ops = ((45/60)*80) * 2            = 120
        #   total_material = 1050 ; total_ops = 420 ; total = 1470
        self.assertAlmostEqual(snap.cost_result.materials_cost, 1050.0)
        self.assertAlmostEqual(snap.cost_result.labour_cost, 420.0)
        self.assertAlmostEqual(snap.cost_result.total_cost, 1470.0)


# ---------------------------------------------------------------------------
# 2. Flat legacy -> IDENTICAL behaviour to pre-sprint
# ---------------------------------------------------------------------------
class TestFlatLegacyBackwardCompat(unittest.TestCase):
    def test_flat_legacy_priced_goes_through_v1_engine(self):
        # v1 engine + v2 rates both provided — v2 rates MUST be ignored for
        # legacy templates because components_json is not hierarchical.
        orch = QuoteOrchestrator(
            cost_engine=CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
            **_full_v2_rates(),
        )
        snap = orch.build_snapshot(
            product_template=_flat_legacy_template(),
            user_config=_sample_user_config(),
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        self.assertEqual(snap.status, "priced", msg=f"blocked={snap.blocked_reasons}")
        self.assertTrue(snap.cost_result.is_valid)
        self.assertGreater(snap.cost_result.total_cost, 0)

        # v2 was NOT used — version tag must be v1, breakdown must be None
        self.assertEqual(getattr(snap, "cost_engine_version", None), "v1")
        self.assertIsNone(getattr(snap, "component_breakdown", None))
        self.assertIsNone(getattr(snap, "component_breakdown_json", None))

    def test_flat_legacy_blocked_without_rates_preserves_v1_reasons(self):
        # This mirrors the pre-existing foundation test
        # `TestQuoteBlockedWithoutValidCost` — the router assertion
        # `r.startswith("cost_invalid:")` and presence of "unit_cost" in
        # the reason MUST still hold.
        orch = QuoteOrchestrator(cost_engine=CostEngineService())
        snap = orch.build_snapshot(
            product_template=_flat_legacy_template(),
            user_config=_sample_user_config(),
            pricing=QuotePricing(margin_pct=20, vat_pct=19),
        )
        self.assertEqual(snap.status, "blocked")
        self.assertTrue(any(r.startswith("cost_invalid:") for r in snap.blocked_reasons))
        self.assertTrue(
            any("unit_cost" in r for r in snap.blocked_reasons),
            msg=f"expected unit_cost mention, got {snap.blocked_reasons}",
        )
        self.assertEqual(getattr(snap, "cost_engine_version", None), "v1")


# ---------------------------------------------------------------------------
# 3. Hierarchical + missing material rate -> blocked with path
# ---------------------------------------------------------------------------
class TestHierarchicalBlockedMaterialRateMissing(unittest.TestCase):
    def test_missing_material_rate_produces_blocked_with_path(self):
        rates = _full_v2_rates()
        # Drop MAT-WELD (used by comp_1, materials[1])
        rates["material_rates"].pop("MAT-WELD")
        orch = QuoteOrchestrator(**rates)
        snap = orch.build_snapshot(
            product_template=_hierarchical_template(),
            user_config=_sample_user_config(),
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        self.assertEqual(snap.status, "blocked")
        self.assertFalse(snap.cost_result.is_valid)
        reasons = snap.blocked_reasons
        self.assertTrue(any("MATERIAL_RATE_MISSING" in r for r in reasons),
                        msg=f"expected MATERIAL_RATE_MISSING, got {reasons}")
        self.assertTrue(any("components[0].materials[1]" in r for r in reasons),
                        msg=f"expected path components[0].materials[1], got {reasons}")
        # Router contract: reasons must still start with cost_invalid:
        self.assertTrue(all(r.startswith("cost_invalid:") for r in reasons))


# ---------------------------------------------------------------------------
# 4. Hierarchical + missing workcenter -> blocked with path
# ---------------------------------------------------------------------------
class TestHierarchicalBlockedWorkcenterRateMissing(unittest.TestCase):
    def test_missing_workcenter_rate_produces_blocked_with_path(self):
        rates = _full_v2_rates()
        # Drop 'welding' (used by comp_1, operations[1])
        rates["workcenter_rates"].pop("welding")
        orch = QuoteOrchestrator(**rates)
        snap = orch.build_snapshot(
            product_template=_hierarchical_template(),
            user_config=_sample_user_config(),
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        self.assertEqual(snap.status, "blocked")
        reasons = snap.blocked_reasons
        self.assertTrue(any("WORKCENTER_RATE_MISSING" in r for r in reasons),
                        msg=f"expected WORKCENTER_RATE_MISSING, got {reasons}")
        self.assertTrue(any("components[0].operations[1]" in r for r in reasons),
                        msg=f"expected path components[0].operations[1], got {reasons}")
        self.assertTrue(all(r.startswith("cost_invalid:") for r in reasons))


# ---------------------------------------------------------------------------
# 5. Pre-sprint snapshot (no v2 extras) is readable via getattr
# ---------------------------------------------------------------------------
class TestPreSprintSnapshotRoundtrip(unittest.TestCase):
    def test_pre_sprint_style_construction_is_readable(self):
        # Simulate a caller that constructs QuoteOrchestrator with ONLY
        # the pre-sprint two-argument form (no v2 rates). Behaviour must
        # be identical to v1 AND all getattr() accesses must return
        # sensible defaults instead of crashing.
        orch = QuoteOrchestrator(
            cost_engine=CostEngineWithMaterialRates({"MAT-ACP-3": 120.0})
        )
        snap = orch.build_snapshot(
            product_template=_flat_legacy_template(),
            user_config=_sample_user_config(),
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        self.assertEqual(snap.status, "priced")

        # Every v2 extras access must be safe (no AttributeError).
        self.assertIsNone(getattr(snap, "component_breakdown", None))
        self.assertIsNone(getattr(snap, "component_breakdown_json", None))
        self.assertIsNone(getattr(snap, "cost_warnings", None))
        self.assertEqual(getattr(snap, "cost_engine_version", "v1"), "v1")

        # snapshot.to_dict() must NOT leak any v2 key (frozen contract).
        d = snap.to_dict()
        for forbidden_key in (
            "component_breakdown",
            "component_breakdown_json",
            "cost_warnings",
            "cost_engine_version",
        ):
            self.assertNotIn(forbidden_key, d,
                             msg=f"{forbidden_key} must not leak into QuoteCalculationSnapshot.to_dict()")


# ---------------------------------------------------------------------------
# 6. Hierarchical + empty component -> priced + warning persisted
# ---------------------------------------------------------------------------
class TestHierarchicalEmptyComponentWarning(unittest.TestCase):
    def test_empty_component_warning_is_persisted_on_snapshot(self):
        # One real component + one intentionally-empty component.
        tpl = _hierarchical_template()
        parsed = json.loads(tpl["components_json"])
        parsed.append(
            {
                "component_id": "comp_empty",
                "type": "SUPORT",
                "name": "Suport gol",
                "materials": [],
                "operations": [],
            }
        )
        tpl["components_json"] = json.dumps(parsed)

        orch = QuoteOrchestrator(**_full_v2_rates())
        snap = orch.build_snapshot(
            product_template=tpl,
            user_config=_sample_user_config(),
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        self.assertEqual(snap.status, "priced", msg=f"blocked={snap.blocked_reasons}")
        breakdown = getattr(snap, "component_breakdown", None)
        self.assertIsNotNone(breakdown)
        self.assertEqual(len(breakdown), 3)
        self.assertEqual(breakdown[2]["component_id"], "comp_empty")
        self.assertEqual(breakdown[2]["total_component_cost"], 0.0)

        warnings = getattr(snap, "cost_warnings", None)
        self.assertIsNotNone(warnings)
        self.assertTrue(
            any(w.get("kind") == "COMPONENT_EMPTY"
                and w.get("path") == "components[2]"
                for w in warnings),
            msg=f"expected COMPONENT_EMPTY on components[2], got {warnings}",
        )

        # Priced totals must equal the sum of the TWO non-empty components.
        self.assertAlmostEqual(
            snap.cost_result.total_cost,
            sum(b["total_component_cost"] for b in breakdown),
        )


if __name__ == "__main__":
    unittest.main()