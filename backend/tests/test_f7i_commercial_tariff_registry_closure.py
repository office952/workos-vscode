"""F7I — commercial registry / template reference / CPP fail-closed closure."""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.commercial_rules_volumetric_v2 import (  # noqa: E402
    OWNER_CONFIRMED_PROVISIONAL_COMMERCIAL_LINE_CODES,
    OWNER_MISSING_COMMERCIAL_RATE_CODES,
    PILOT_TEMPLATE,
    classify_commercial_rule_publication,
    inventory_commercial_rules_for_template,
)

_F7I1_ACTIVATED = frozenset(
    {"ambalare", "debitare_spate", "sistem_led_module", "sursa_led"}
)
from services.template_pricing_recipe_service import (  # noqa: E402
    ACM_BOXED_TEMPLATE,
    TemplatePricingRecipeService,
    VL_TEMPLATE,
)


class TestF7IPublicationClassification(unittest.TestCase):
    def test_owner_missing_codes_cleared_after_f7i1(self) -> None:
        # F7I left gaps; F7I.1 Owner-confirmed provisional rates emptied the missing set.
        self.assertEqual(OWNER_MISSING_COMMERCIAL_RATE_CODES, frozenset())
        self.assertTrue(_F7I1_ACTIVATED <= OWNER_CONFIRMED_PROVISIONAL_COMMERCIAL_LINE_CODES)

    def test_inventory_marks_former_gaps_as_owner_provisional(self) -> None:
        inv = inventory_commercial_rules_for_template(PILOT_TEMPLATE)
        by_code = {str(row["canonical_rule_code"]): row for row in inv}
        for code in _F7I1_ACTIVATED:
            self.assertIn(code, by_code)
            row = by_code[code]
            self.assertEqual(row["publication_state"], "ACTIVE_PROVISIONAL")
            self.assertIsNotNone(row["current_rate"])
            self.assertNotEqual(row["current_rate"], 0)
            self.assertEqual(row["catalog_owner"], "commercial_rules_volumetric_v2")
            self.assertIsNone(row["owner_question"])
            self.assertEqual(row["provisional_nature"], "owner_confirmed_provisional")

    def test_provisional_face_cnc_not_invented_as_owner_final(self) -> None:
        inv = inventory_commercial_rules_for_template(PILOT_TEMPLATE)
        face = next(r for r in inv if r["canonical_rule_code"] == "debitare_fata")
        self.assertEqual(face["publication_state"], "ACTIVE_PROVISIONAL")
        self.assertEqual(face["current_rate"], 1.5)
        self.assertEqual(face["currency"], "EUR")

    def test_legacy_ron_finish_not_used_on_eur_path(self) -> None:
        inv = inventory_commercial_rules_for_template(PILOT_TEMPLATE)
        finish = next(
            r for r in inv if r["canonical_rule_code"] == "finisaje_colantare_vopsire"
        )
        self.assertEqual(finish["publication_state"], "LEGACY_NOT_USED")
        self.assertEqual(finish["currency"], "RON")


class TestF7ITemplateRecipeReferences(unittest.IsolatedAsyncioTestCase):
    async def _vl_recipe(self, *, site_install_rate: float | None = 200.0):
        db = MagicMock()
        row = MagicMock()
        row.family_name = "Volumetric Letters"
        row.active = True
        row.version = "2"
        row.template_code = VL_TEMPLATE
        result = MagicMock()
        result.scalar_one_or_none.return_value = row
        db.execute = AsyncMock(return_value=result)

        items = []
        if site_install_rate is not None:
            items.append(
                {
                    "pricing_code": "SITE_INSTALLATION_STANDARD",
                    "display_name": "Montaj șantier",
                    "pricing_kind": "service",
                    "typed_catalog": "service",
                    "unit": "locatie",
                    "base_cost": site_install_rate,
                    "currency": "EUR",
                    "status": "active",
                    "confidence": "owner_confirmed",
                    "technical_source": "workcenter_rates",
                    "cost_meaning": "reusable_rate",
                    "cost_label_ro": "Rată comercială",
                    "data_quality_flags": [],
                }
            )
        # Inventory material must never become a commercial sell fill for unpublished gaps.
        items.append(
            {
                "pricing_code": "MAT-ORACAL-651",
                "display_name": "Oracal 651",
                "pricing_kind": "material",
                "typed_catalog": "material",
                "unit": "m2",
                "base_cost": 5.0,
                "currency": "EUR",
                "status": "active",
                "confidence": "owner_confirmed",
                "technical_source": "inventory_materials",
                "cost_meaning": "purchase_cost",
                "cost_label_ro": "Cost achiziție",
                "data_quality_flags": [],
            }
        )

        service = TemplatePricingRecipeService(db)
        service._registry.build_registry = AsyncMock(
            return_value={
                "summary": {
                    "owner_confirmed": 2,
                    "missing_price": 0,
                    "materials_count": 1,
                    "rates_count": 1,
                },
                "items": items,
            }
        )
        return await service.build_recipe(VL_TEMPLATE)

    async def test_former_missing_rates_are_owner_provisional_on_template(self) -> None:
        recipe = await self._vl_recipe()
        assert recipe is not None
        by_code = {r.stable_code: r for r in recipe.recipe if r.recipe_kind == "commercial_line"}
        for code in _F7I1_ACTIVATED:
            self.assertIn(code, by_code)
            item = by_code[code]
            self.assertEqual(item.commercial_reference_status, "ACTIVE_PROVISIONAL")
            self.assertEqual(item.status, "warning")
            self.assertIsNotNone(item.current_value)
            self.assertNotIn("COMMERCIAL_RATE_MISSING", item.blockers)
            self.assertFalse(item.editable)
            self.assertEqual(item.catalog_owner, "commercial_rules_volumetric_v2")

    async def test_montaj_binds_registry_without_using_inventory_unit_cost(self) -> None:
        recipe = await self._vl_recipe(site_install_rate=200.0)
        assert recipe is not None
        montaj = next(r for r in recipe.recipe if r.stable_code == "montaj")
        self.assertEqual(montaj.commercial_reference_status, "ACTIVE_PUBLISHED")
        self.assertEqual(montaj.current_value, 200.0)
        self.assertEqual(montaj.currency, "EUR")
        self.assertEqual(montaj.rate_source, "pricing_registry")

        # Ambalare sell comes from commercial catalog (Owner provisional), not inventory unit_cost.
        ambalare = next(r for r in recipe.recipe if r.stable_code == "ambalare")
        self.assertEqual(ambalare.current_value, 20.0)
        self.assertEqual(ambalare.rate_source, "documented_commercial")
        self.assertNotEqual(ambalare.rate_source, "pricing_registry")

    async def test_acm_treatment_remains_blocked_shell_5_0(self) -> None:
        db = MagicMock()
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
                        "pricing_code": f"ACM-SHELL-{i}",
                        "display_name": f"Shell {i}",
                        "pricing_kind": "material" if i < 2 else "workcenter_rate",
                        "typed_catalog": "material" if i < 2 else "machine_operation",
                        "unit": "m2",
                        "base_cost": 10.0 + i,
                        "currency": "EUR",
                        "status": "active",
                        "confidence": "owner_confirmed",
                        "technical_source": "inventory_materials",
                        "cost_meaning": "purchase_cost",
                        "data_quality_flags": [],
                    }
                    for i in range(5)
                ],
            }
        )
        recipe = await service.build_recipe(ACM_BOXED_TEMPLATE)
        assert recipe is not None
        self.assertTrue(recipe.acm_acceptance.applies)
        self.assertEqual(recipe.acm_acceptance.shell_registry_confirmed, 5)
        self.assertEqual(recipe.acm_acceptance.shell_registry_missing, 0)
        self.assertIs(recipe.acm_acceptance.treatment_commercial_lines_allowed, False)
        self.assertIn(
            "ACM_TREATMENT_COMMERCIAL_BLOCKED",
            recipe.readiness.real_blockers_retained,
        )


@pytest.mark.asyncio
async def test_f7i_classify_matches_inventory_rows():
    inv = inventory_commercial_rules_for_template("TPL-VOLUMETRIC-LETTERS_v2")
    assert inv
    for row in inv:
        # classify is the single honesty source for publication_state
        from data.commercial_rules_volumetric_v2 import RULES_BY_TEMPLATE

        rule = next(
            r
            for r in RULES_BY_TEMPLATE[PILOT_TEMPLATE]
            if r.line_code == row["canonical_rule_code"]
        )
        assert classify_commercial_rule_publication(rule) == row["publication_state"]


if __name__ == "__main__":
    unittest.main()
