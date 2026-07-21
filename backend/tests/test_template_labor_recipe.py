"""LABOR_RECIPE_CONTRACT_V1 — central rate + template recipe ownership."""

from __future__ import annotations

import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.template_labor_recipe import (  # noqa: E402
    basis_from_rate_basis,
    build_labor_recipes,
    labor_class_for,
    merge_labor_from_pricing_recipe_items,
    recipe_role_for_code,
    resolve_catalog_code,
)
from services.template_pricing_recipe_service import (  # noqa: E402
    ACM_BOXED_TEMPLATE,
    TemplatePricingRecipeService,
)


class TestLaborHelpers(unittest.TestCase):
    def test_resolve_alias(self) -> None:
        self.assertEqual(resolve_catalog_code("WC_ASSEMBLY"), "ASSEMBLY")
        self.assertEqual(resolve_catalog_code("ACM_BOXED_ASSEMBLY"), "ACM_BOXED_ASSEMBLY")

    def test_role_and_basis(self) -> None:
        self.assertEqual(recipe_role_for_code("LED_ASSEMBLY"), "wiring")
        self.assertEqual(basis_from_rate_basis("per_square_meter", "m2"), "mp")
        self.assertEqual(basis_from_rate_basis("per_piece", "buc"), "buc")

    def test_labor_class(self) -> None:
        self.assertEqual(
            labor_class_for(
                typed_catalog="labor",
                catalog_code="ACM_BOXED_ASSEMBLY",
                status="active",
                has_commercial_map=True,
            ),
            "LABOR_COMMERCIAL",
        )
        self.assertEqual(
            labor_class_for(
                typed_catalog="labor",
                catalog_code="ASSEMBLY",
                status="missing",
                has_commercial_map=False,
            ),
            "MISSING_RATE",
        )


class TestBuildLaborRecipes(unittest.TestCase):
    def test_template_op_joins_central_rate(self) -> None:
        row = SimpleNamespace(
            operations_json=None,
            components_json=[
                {
                    "component_id": "comp_acm",
                    "operations": [
                        {
                            "code": "acm_boxed_assembly_op",
                            "workcenter": "ACM_BOXED_ASSEMBLY",
                            "formula_id": "area_from_quote_input",
                            "requires_quote_input": ["panel_area_m2"],
                            "quote_priced": True,
                            "label": "Asamblare ACM",
                        }
                    ],
                }
            ],
        )
        registry = {
            "ACM_BOXED_ASSEMBLY": {
                "pricing_code": "ACM_BOXED_ASSEMBLY",
                "display_name": "Asamblare",
                "typed_catalog": "labor",
                "base_cost": 15.0,
                "currency": "EUR",
                "unit": "m2",
                "rate_basis": "per_square_meter",
                "confidence": "owner_confirmed",
                "status": "active",
                "data_quality_flags": ["rate_basis_column_mismatch"],
                "data_quality_message_ro": "Valoarea ratei necesită verificare",
            }
        }
        recipes = build_labor_recipes(
            template_code=ACM_BOXED_TEMPLATE,
            row=row,
            registry_by_code=registry,
            commercial_line_by_catalog={"ACM_BOXED_ASSEMBLY": "acm_boxed_assembly"},
        )
        self.assertEqual(len(recipes), 1)
        r = recipes[0]
        self.assertEqual(r["catalog_code"], "ACM_BOXED_ASSEMBLY")
        self.assertEqual(r["quantity_keys"], ["panel_area_m2"])
        self.assertEqual(r["formula_id"], "area_from_quote_input")
        self.assertTrue(r["technical_ready"])
        self.assertEqual(r["status"], "warning")
        self.assertIn("rate_basis_column_mismatch", r["data_quality_flags"])
        self.assertFalse(r["editable"])

    def test_dedupes_ops_json_and_component_ops(self) -> None:
        op = {
            "code": "acm_boxed_assembly_op",
            "workcenter": "ACM_BOXED_ASSEMBLY",
            "formula_id": "area_from_quote_input",
            "requires_quote_input": ["panel_area_m2"],
            "quote_priced": True,
        }
        row = SimpleNamespace(
            operations_json=[op],
            components_json=[{"component_id": "c1", "operations": [op]}],
        )
        recipes = build_labor_recipes(
            template_code=ACM_BOXED_TEMPLATE,
            row=row,
            registry_by_code={
                "ACM_BOXED_ASSEMBLY": {
                    "pricing_code": "ACM_BOXED_ASSEMBLY",
                    "typed_catalog": "labor",
                    "base_cost": 15.0,
                    "unit": "m2",
                    "rate_basis": "per_square_meter",
                    "confidence": "owner_confirmed",
                    "status": "active",
                    "data_quality_flags": [],
                }
            },
        )
        self.assertEqual(len(recipes), 1)
        self.assertTrue(recipes[0]["labor_recipe_id"].startswith(ACM_BOXED_TEMPLATE))

    def test_missing_rate_blocks_commercial_not_technical(self) -> None:
        row = SimpleNamespace(
            operations_json=[
                {
                    "code": "assembly_letters",
                    "workcenter": "ASSEMBLY",
                    "formula_id": "static",
                    "quote_priced": True,
                }
            ],
            components_json=None,
        )
        recipes = build_labor_recipes(
            template_code="TPL-VOLUMETRIC-LETTERS_v2",
            row=row,
            registry_by_code={},
        )
        self.assertEqual(len(recipes), 1)
        self.assertTrue(recipes[0]["technical_ready"])
        self.assertFalse(recipes[0]["commercial_ready"])
        self.assertEqual(recipes[0]["labor_class"], "MISSING_RATE")


class TestMergeRegistryLabor(unittest.TestCase):
    def test_merges_vl_registry_labor_when_ops_empty(self) -> None:
        item = SimpleNamespace(
            recipe_kind="labor",
            catalog_code="LED_ASSEMBLY",
            stable_code="LED_ASSEMBLY",
            operator_name="Montaj LED",
            status="warning",
            current_value=12.0,
            unit="buc",
            currency="EUR",
            quantity_keys=[],
            data_quality_flags=["rate_basis_column_mismatch"],
            data_quality_message_ro="Verificare",
            blockers=[],
            warnings=["RATE_BASIS_COLUMN_MISMATCH"],
            cpp_line_code=None,
        )
        merged = merge_labor_from_pricing_recipe_items(
            template_code="TPL-VOLUMETRIC-LETTERS_v2",
            pricing_items=[item],
            existing=[],
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["catalog_code"], "LED_ASSEMBLY")
        self.assertIn("REGISTRY_LINKED_LABOR_NO_OPS_FORMULA", merged[0]["warnings"])
        self.assertFalse(merged[0]["technical_ready"])


class TestServiceLaborRecipes(unittest.IsolatedAsyncioTestCase):
    async def test_acm_response_includes_labor_recipes(self) -> None:
        db = MagicMock()
        row = MagicMock()
        row.family_name = "ACM"
        row.active = True
        row.version = "1"
        row.template_code = ACM_BOXED_TEMPLATE
        row.operations_json = None
        row.components_json = (
            '[{"operations":[{"code":"asm","workcenter":"ACM_BOXED_ASSEMBLY",'
            '"formula_id":"area_from_quote_input","requires_quote_input":["panel_area_m2"],'
            '"quote_priced":true}]}]'
        )
        result = MagicMock()
        result.scalar_one_or_none.return_value = row
        db.execute = AsyncMock(return_value=result)
        service = TemplatePricingRecipeService(db)
        service._registry.build_registry = AsyncMock(
            return_value={
                "summary": {"owner_confirmed": 5, "missing_price": 0},
                "items": [
                    {
                        "pricing_code": "ACM_BOXED_ASSEMBLY",
                        "display_name": "Asamblare",
                        "pricing_kind": "workcenter_rate",
                        "typed_catalog": "labor",
                        "unit": "m2",
                        "base_cost": 15.0,
                        "currency": "EUR",
                        "status": "active",
                        "confidence": "owner_confirmed",
                        "technical_source": "workcenter_rates",
                        "cost_meaning": "reusable_rate",
                        "cost_label_ro": "Rată calcul",
                        "data_quality_flags": [],
                    }
                ],
            }
        )
        recipe = await service.build_recipe(ACM_BOXED_TEMPLATE)
        assert recipe is not None
        self.assertEqual(recipe.schema_version, "1.1.0")
        self.assertGreaterEqual(recipe.labor_summary.total, 1)
        self.assertTrue(any(r.catalog_code == "ACM_BOXED_ASSEMBLY" for r in recipe.labor_recipes))
        self.assertTrue(all(r.editable is False for r in recipe.labor_recipes))


if __name__ == "__main__":
    unittest.main()
