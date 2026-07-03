"""
Canonical foundation tests.

Prove that:
  1. ProductSystemService does not return cost.
  2. CostEngineService does not modify ProductDefinition.
  3. Quote cannot become priced without a valid ProductDefinition.
  4. Quote cannot become priced without a valid CostResult.
  5. Quote becomes blocked when cost data is missing.
  6. Order is created only from an accepted/priced Quote.
  7. OrderSnapshot is locked after creation.
  8. Order is not recalculated after creation.
"""

from __future__ import annotations

import copy
import json
import os
import sys
import unittest

# Ensure backend root on sys.path so `data_models`, `services` resolve
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from data_models.product_contracts import (  # noqa: E402
    CostRequest,
    CostResult,
    OrderSnapshot,
    PricingContext,
    ProductDefinition,
    QuoteCalculationSnapshot,
    QuotePricing,
)
from services.cost_engine_service import (  # noqa: E402
    CostEngineService,
    CostEngineWithMaterialRates,
)
from services.order_snapshot_service import OrderSnapshotService  # noqa: E402
from services.product_system_service import ProductSystemService  # noqa: E402
from services.quote_orchestrator import QuoteOrchestrator  # noqa: E402


def sample_template_complete() -> dict:
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


def sample_user_config() -> dict:
    return {
        "quantity": 2,
        "dimensions": {"width_mm": 1000, "height_mm": 3000, "depth_mm": 300},
    }


class TestProductSystemDoesNotReturnCost(unittest.TestCase):
    def test_product_definition_has_no_cost_fields(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(sample_template_complete(), sample_user_config())

        d = pd.to_dict()

        cost_like_keys = {
            "total_cost", "materials_cost", "labour_cost",
            "unit_cost", "price", "vat", "margin_pct", "discount_pct",
        }
        found = cost_like_keys.intersection(set(d.keys()))
        self.assertEqual(found, set(), f"ProductDefinition leaked cost keys: {found}")

        # Also check no component/layer carries unit_cost
        for layer in pd.layers:
            for comp in layer.components:
                self.assertFalse(hasattr(comp, "unit_cost") and getattr(comp, "unit_cost", None))


class TestCostEngineDoesNotMutateProduct(unittest.TestCase):
    def test_product_definition_is_not_mutated(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(sample_template_complete(), sample_user_config())
        snapshot_before = copy.deepcopy(pd.to_dict())

        CostEngineService().calculate(CostRequest(product_definition=pd))

        self.assertEqual(pd.to_dict(), snapshot_before,
                         "CostEngine must not mutate ProductDefinition")


class TestQuoteBlockedWithoutValidProduct(unittest.TestCase):
    def test_blocked_when_template_missing(self):
        orch = QuoteOrchestrator()
        snap = orch.build_snapshot(product_template=None, user_config={"quantity": 1})
        self.assertEqual(snap.status, "blocked")
        self.assertFalse(snap.product_definition.validation.is_valid)
        self.assertTrue(any(r.startswith("product_invalid:") for r in snap.blocked_reasons))


class TestQuoteBlockedWithoutValidCost(unittest.TestCase):
    def test_blocked_when_material_unit_cost_missing(self):
        # No material rates provided — cost must be invalid.
        orch = QuoteOrchestrator(cost_engine=CostEngineService())
        snap = orch.build_snapshot(
            product_template=sample_template_complete(),
            user_config=sample_user_config(),
            pricing=QuotePricing(margin_pct=20, vat_pct=19),
        )
        self.assertEqual(snap.status, "blocked")
        self.assertTrue(snap.product_definition.validation.is_valid,
                        "Product should be valid in this scenario")
        self.assertFalse(snap.cost_result.is_valid)
        self.assertTrue(any("unit_cost" in m for m in snap.cost_result.validation.missing_cost_data))


class TestQuoteBecomesPricedWithFullData(unittest.TestCase):
    def test_priced_when_material_rates_provided(self):
        orch = QuoteOrchestrator(
            cost_engine=CostEngineWithMaterialRates({"MAT-ACP-3": 120.0})
        )
        snap = orch.build_snapshot(
            product_template=sample_template_complete(),
            user_config=sample_user_config(),
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        self.assertEqual(snap.status, "priced", msg=f"blocked_reasons={snap.blocked_reasons}")
        self.assertTrue(snap.cost_result.is_valid)
        self.assertGreater(snap.cost_result.total_cost, 0)
        self.assertGreater(snap.price.net, snap.cost_result.total_cost * 1.0)
        self.assertGreater(snap.price.gross, snap.price.net)


class TestOrderOnlyFromPricedQuote(unittest.TestCase):
    def test_raises_when_quote_blocked(self):
        orch = QuoteOrchestrator()
        snap = orch.build_snapshot(product_template=None)
        self.assertEqual(snap.status, "blocked")
        with self.assertRaises(ValueError):
            OrderSnapshotService().create_from_quote(snap)

    def test_ok_when_quote_priced(self):
        orch = QuoteOrchestrator(
            cost_engine=CostEngineWithMaterialRates({"MAT-ACP-3": 120.0})
        )
        snap = orch.build_snapshot(
            product_template=sample_template_complete(),
            user_config=sample_user_config(),
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        order = OrderSnapshotService().create_from_quote(snap)
        self.assertIsInstance(order, OrderSnapshot)
        self.assertTrue(order.order_id)
        self.assertTrue(order.is_locked)


class TestOrderSnapshotIsLocked(unittest.TestCase):
    def test_is_locked_true(self):
        orch = QuoteOrchestrator(
            cost_engine=CostEngineWithMaterialRates({"MAT-ACP-3": 120.0})
        )
        snap = orch.build_snapshot(
            product_template=sample_template_complete(),
            user_config=sample_user_config(),
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        order = OrderSnapshotService().create_from_quote(snap)
        self.assertTrue(order.is_locked)


class TestOrderIsNotRecalculatedAfterCreation(unittest.TestCase):
    def test_upstream_mutation_does_not_affect_order(self):
        orch = QuoteOrchestrator(
            cost_engine=CostEngineWithMaterialRates({"MAT-ACP-3": 120.0})
        )
        snap = orch.build_snapshot(
            product_template=sample_template_complete(),
            user_config=sample_user_config(),
            pricing=QuotePricing(margin_pct=25, vat_pct=19),
        )
        order = OrderSnapshotService().create_from_quote(snap)
        original_total = order.cost_result.total_cost
        original_net = order.final_price.net

        # Mutate upstream snapshot aggressively
        snap.cost_result.total_cost = 999999.99
        snap.price.net = 123456.78
        snap.product_definition.quantity = 9999
        for layer in snap.product_definition.layers:
            layer.material.name = "MUTATED"

        # Order snapshot must remain unchanged (deep copy protection)
        self.assertEqual(order.cost_result.total_cost, original_total)
        self.assertEqual(order.final_price.net, original_net)
        self.assertNotEqual(order.product_definition.quantity, 9999)
        for layer in order.product_definition.layers:
            self.assertNotEqual(layer.material.name, "MUTATED")


if __name__ == "__main__":
    unittest.main(verbosity=2)