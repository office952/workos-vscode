"""LABOR_RECIPE_CONTRACT_V1_CLOSURE — formula status classification."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.template_labor_formula_truth import (  # noqa: E402
    classify_labor_formula_truth,
    enrich_labor_recipes_formula_truth,
)


class TestLaborFormulaTruth(unittest.TestCase):
    def test_vl_led_quantity_key_not_throughput_formula(self) -> None:
        r = classify_labor_formula_truth(
            {
                "catalog_code": "LED_ASSEMBLY",
                "operation_code": "LED_ASSEMBLY",
                "quantity_keys": [],
                "formula_id": None,
                "formula_owner": "pricing_registry_template_filter",
                "warnings": [],
                "technical_ready": False,
            },
            registered_formula_ids={"led_assembly_time", "face_vinyl_used_sqm"},
        )
        self.assertEqual(r["formula_status"], "QUANTITY_KEY_CONFIRMED")
        self.assertEqual(r["quantity_keys"], ["letter_led_module_count"])
        self.assertTrue(r["technical_ready"])

    def test_packaging_missing_owner(self) -> None:
        r = classify_labor_formula_truth(
            {
                "catalog_code": "PACKAGING",
                "operation_code": "PACKAGING",
                "quantity_keys": [],
                "formula_id": None,
                "formula_owner": "pricing_registry_template_filter",
                "warnings": [],
            },
            registered_formula_ids=set(),
        )
        self.assertEqual(r["formula_status"], "MISSING_OWNER_FORMULA")
        self.assertTrue(r["owner_confirmation_required"])

    def test_montaj_commercial_confirmed(self) -> None:
        r = classify_labor_formula_truth(
            {
                "catalog_code": "SITE_INSTALLATION_STANDARD",
                "operation_code": "montaj",
                "quantity_keys": [],
                "formula_id": None,
                "formula_owner": "commercial_rule_catalog_ref",
                "warnings": [],
            },
            registered_formula_ids=set(),
        )
        self.assertEqual(r["formula_status"], "FORMULA_CONFIRMED")

    def test_legacy_unregistered_formula_with_qty(self) -> None:
        r = classify_labor_formula_truth(
            {
                "catalog_code": "RETURN_PROFILE_FACE_BONDING",
                "operation_code": "RETURN_PROFILE_FACE_BONDING",
                "quantity_keys": [],
                "formula_id": "return_profile_face_bonding",
                "formula_owner": "operations_json",
                "warnings": [],
            },
            registered_formula_ids=set(),
        )
        self.assertEqual(r["formula_status"], "QUANTITY_KEY_CONFIRMED")
        self.assertIn("LEGACY_FORMULA_NAME_UNREGISTERED", r["warnings"])
        self.assertEqual(r["quantity_keys"], ["letter_perimeter_m"])

    def test_enrich_preserves_count(self) -> None:
        recipes = [
            {
                "catalog_code": "PREPRESS",
                "operation_code": "PREPRESS",
                "quantity_keys": [],
                "formula_id": None,
                "formula_owner": "pricing_registry_template_filter",
                "warnings": [],
            }
        ]
        out = enrich_labor_recipes_formula_truth(recipes)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["formula_status"], "OPERATION_ONLY")


if __name__ == "__main__":
    unittest.main()
