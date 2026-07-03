"""Sprint #27 — Quote Orchestrator strict product-level validation.

Proves:

  1. v2 branch (hierarchical template + rates) STILL blocks on missing
     `quantity` with `product_invalid:quantity` — no silent clamp to 1.
  2. v2 branch blocks on missing `dimensions` (neither width nor height
     provided) with `product_invalid:dimensions`.
  3. v2 branch blocks on missing `product_type` (empty family on template)
     with `product_invalid:product_type`.
  4. v2 branch PRICES successfully when all product-level fields + rates
     are provided — regression guard that strict validation did not break
     the happy path.
  5. v1 branch unchanged — missing quantity still blocks exactly as before.

Uses the same fixture style as `test_quote_orchestrator_v2.py` but isolates
the new product-level gate on the v2 path.
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


def _hierarchical_template(family_name: str = "Totemuri / Pyloni") -> dict:
    components = [
        {
            "component_id": "comp_1",
            "type": "STRUCTURA",
            "name": "Cadru",
            "materials": [
                {
                    "materialCode": "MAT-STEEL",
                    "name": "Oțel",
                    "quantity": 2,
                    "unit": "kg",
                    "component_ref": "comp_1",
                },
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
        "id": 101,
        "template_code": "HIER-S27",
        "family_id": "totemuri_pyloni",
        "family_name": family_name,
        "components_json": json.dumps(components),
        "operations_json": json.dumps(flat_ops),
        "required_materials_json": json.dumps(flat_mats),
    }


def _flat_legacy_template() -> dict:
    return {
        "id": 202,
        "template_code": "FLAT-S27",
        "family_id": "totemuri_pyloni",
        "family_name": "Totemuri / Pyloni",
        "components_json": json.dumps(["Cadru metalic"]),
        "operations_json": json.dumps(
            [
                {
                    "code": "CUT",
                    "name": "Debitare",
                    "workcenter": "CNC",
                    "estimatedMinutes": 30,
                    "sequence": 1,
                }
            ]
        ),
        "required_materials_json": json.dumps(
            [
                {
                    "materialCode": "MAT-STEEL",
                    "name": "Oțel",
                    "quantity": 2,
                    "unit": "kg",
                }
            ]
        ),
    }


class QuoteOrchestratorStrictProductLevelSuite(unittest.TestCase):
    def _orch_v2(self) -> QuoteOrchestrator:
        return QuoteOrchestrator(
            cost_engine=CostEngineService(),
            material_rates={"MAT-STEEL": 10.0},
            workcenter_rates={"CNC": 90.0},
        )

    # ------------------------------------------------------------------
    # 1. v2 + missing quantity → product_invalid:quantity
    # ------------------------------------------------------------------
    def test_v2_blocks_on_missing_quantity(self):
        orch = self._orch_v2()
        snap = orch.build_snapshot(
            product_template=_hierarchical_template(),
            user_config={"dimensions": {"width_mm": 500, "height_mm": 1000}},
            pricing=QuotePricing(margin_pct=20, vat_pct=19),
        )
        self.assertEqual(snap.status, "blocked")
        self.assertIn("product_invalid:quantity", snap.blocked_reasons)

    # ------------------------------------------------------------------
    # 2. v2 + missing dimensions → product_invalid:dimensions
    # ------------------------------------------------------------------
    def test_v2_blocks_on_missing_dimensions(self):
        orch = self._orch_v2()
        snap = orch.build_snapshot(
            product_template=_hierarchical_template(),
            user_config={"quantity": 3},
            pricing=QuotePricing(margin_pct=20, vat_pct=19),
        )
        self.assertEqual(snap.status, "blocked")
        self.assertIn("product_invalid:dimensions", snap.blocked_reasons)

    # ------------------------------------------------------------------
    # 3. v2 + missing product_type → product_invalid:product_type
    # ------------------------------------------------------------------
    def test_v2_blocks_on_missing_product_type(self):
        orch = self._orch_v2()
        tpl = _hierarchical_template(family_name="")
        tpl["family_id"] = ""  # both empty → product_type missing
        snap = orch.build_snapshot(
            product_template=tpl,
            user_config={
                "quantity": 3,
                "dimensions": {"width_mm": 500, "height_mm": 1000},
            },
            pricing=QuotePricing(margin_pct=20, vat_pct=19),
        )
        self.assertEqual(snap.status, "blocked")
        self.assertIn("product_invalid:product_type", snap.blocked_reasons)

    # ------------------------------------------------------------------
    # 4. Happy path — regression guard
    # ------------------------------------------------------------------
    def test_v2_prices_when_all_product_level_fields_present(self):
        orch = self._orch_v2()
        snap = orch.build_snapshot(
            product_template=_hierarchical_template(),
            user_config={
                "quantity": 2,
                "dimensions": {"width_mm": 500, "height_mm": 1000},
            },
            pricing=QuotePricing(margin_pct=20, vat_pct=19),
        )
        self.assertEqual(
            snap.status,
            "priced",
            f"expected priced, got {snap.status} reasons={snap.blocked_reasons}",
        )
        self.assertIsNotNone(snap.price)
        self.assertGreater(snap.price.net, 0)

    # ------------------------------------------------------------------
    # 5. v1 unchanged — missing quantity blocks with quantity reason
    # ------------------------------------------------------------------
    def test_v1_still_blocks_on_missing_quantity(self):
        # No rates context → v2 branch is NOT activated, so v1 path runs.
        orch = QuoteOrchestrator(
            cost_engine=CostEngineWithMaterialRates({"MAT-STEEL": 10.0}),
        )
        snap = orch.build_snapshot(
            product_template=_flat_legacy_template(),
            user_config={"dimensions": {"width_mm": 500, "height_mm": 1000}},
            pricing=QuotePricing(margin_pct=20, vat_pct=19),
        )
        self.assertEqual(snap.status, "blocked")
        self.assertIn("product_invalid:quantity", snap.blocked_reasons)


if __name__ == "__main__":
    unittest.main()