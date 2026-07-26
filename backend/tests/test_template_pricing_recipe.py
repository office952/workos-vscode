"""TEMPLATE_PRICING_STUDIO_V1 — recipe composition read model."""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.commercial_rules_volumetric_v2 import ACM_STRUCTURA_COMMERCIAL_RULES  # noqa: E402
from services.template_pricing_recipe_service import (  # noqa: E402
    ACM_BOXED_TEMPLATE,
    TemplatePricingRecipeService,
    _kind_from_typed,
    _recipe_id,
)


class TestRecipeHelpers(unittest.TestCase):
    def test_recipe_id_stable(self) -> None:
        self.assertEqual(
            _recipe_id("TPL-A", "material", "MAT-X"),
            "TPL-A::material::MAT-X",
        )

    def test_kind_from_typed(self) -> None:
        self.assertEqual(_kind_from_typed("material", None), "material")
        self.assertEqual(_kind_from_typed("machine_operation", None), "machine_operation")
        self.assertEqual(_kind_from_typed("labor", None), "labor")
        self.assertEqual(_kind_from_typed("service", None), "service")
        self.assertEqual(_kind_from_typed("markup_rule", None), "adjustment")


class TestRegistryToRecipe(unittest.IsolatedAsyncioTestCase):
    async def test_acm_shell_composes_registry_and_commercial_lines(self) -> None:
        db = MagicMock()
        # Product_templates row
        row = MagicMock()
        row.family_name = "ACM Boxed"
        row.active = True
        row.version = "1"
        row.template_code = ACM_BOXED_TEMPLATE
        result = MagicMock()
        result.scalar_one_or_none.return_value = row
        db.execute = AsyncMock(return_value=result)

        service = TemplatePricingRecipeService(db)
        service._registry.build_registry = AsyncMock(
            return_value={
                "summary": {
                    "owner_confirmed": 5,
                    "missing_price": 0,
                    "materials_count": 2,
                    "rates_count": 3,
                },
                "items": [
                    {
                        "pricing_code": "MAT-ACM-BOND-3MM",
                        "display_name": "ACM 3mm",
                        "pricing_kind": "material",
                        "typed_catalog": "material",
                        "unit": "m2",
                        "base_cost": 15.0,
                        "currency": "EUR",
                        "status": "active",
                        "confidence": "owner_confirmed",
                        "technical_source": "inventory_materials",
                        "cost_meaning": "purchase_cost",
                        "cost_label_ro": "Cost achiziție",
                        "data_quality_flags": [],
                    },
                    {
                        "pricing_code": "ACM_PANEL_CUTTING",
                        "display_name": "Debitare ACM",
                        "pricing_kind": "workcenter_rate",
                        "typed_catalog": "machine_operation",
                        "machine_family": "cnc_mechanical",
                        "unit": "ml",
                        "base_cost": 1.5,
                        "currency": "EUR",
                        "status": "active",
                        "confidence": "owner_confirmed",
                        "technical_source": "workcenter_rates",
                        "cost_meaning": "reusable_rate",
                        "cost_label_ro": "Rată calcul",
                        "data_quality_flags": [],
                    },
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
                        "data_quality_flags": ["rate_basis_column_mismatch"],
                        "data_quality_message_ro": "Valoarea ratei necesita verificare",
                    },
                ],
            }
        )

        recipe = await service.build_recipe(ACM_BOXED_TEMPLATE)
        assert recipe is not None
        self.assertEqual(recipe.template_code, ACM_BOXED_TEMPLATE)
        self.assertEqual(recipe.editability_policy, "read_only_v1")
        self.assertTrue(recipe.acm_acceptance.applies)
        self.assertEqual(recipe.acm_acceptance.shell_registry_confirmed, 5)
        self.assertEqual(recipe.acm_acceptance.shell_registry_missing, 0)
        self.assertIs(recipe.acm_acceptance.treatment_commercial_lines_allowed, False)
        self.assertGreaterEqual(recipe.summary.materials, 1)
        self.assertGreaterEqual(recipe.summary.machine_operations, 1)
        self.assertGreaterEqual(recipe.summary.commercial_lines, len(ACM_STRUCTURA_COMMERCIAL_RULES))
        # mismatch warning surfaces
        flagged = [r for r in recipe.recipe if "rate_basis_column_mismatch" in r.data_quality_flags]
        self.assertTrue(flagged)
        # no invented editable writes
        self.assertTrue(all(r.editable is False for r in recipe.recipe))
        # CPP structural lines present
        self.assertIn("acm_panel_cut", recipe.cpp_preview.line_codes)

    async def test_missing_template_returns_none(self) -> None:
        db = MagicMock()
        miss = MagicMock()
        miss.scalar_one_or_none.return_value = None
        empty = MagicMock()
        empty.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(side_effect=[miss, empty])
        service = TemplatePricingRecipeService(db)
        self.assertIsNone(await service.build_recipe("TPL-DOES-NOT-EXIST"))

    async def test_case_insensitive_template_lookup(self) -> None:
        db = MagicMock()
        row = MagicMock()
        row.family_name = "ACM Boxed"
        row.active = True
        row.version = "1"
        row.template_code = ACM_BOXED_TEMPLATE
        miss = MagicMock()
        miss.scalar_one_or_none.return_value = None
        scan = MagicMock()
        scan.scalars.return_value.all.return_value = [row]
        db.execute = AsyncMock(side_effect=[miss, scan])
        service = TemplatePricingRecipeService(db)
        service._registry.build_registry = AsyncMock(
            return_value={
                "summary": {"owner_confirmed": 5, "missing_price": 0},
                "items": [],
            }
        )
        recipe = await service.build_recipe("TPL-ACM-BOXED-MOUNTING-SUPPORT_V1")
        assert recipe is not None
        self.assertEqual(recipe.template_code, ACM_BOXED_TEMPLATE)
        self.assertTrue(recipe.acm_acceptance.applies)


if __name__ == "__main__":
    unittest.main()
