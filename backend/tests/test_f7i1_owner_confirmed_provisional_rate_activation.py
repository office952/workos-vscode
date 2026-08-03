"""F7I.1 — Owner-confirmed provisional commercial rates (2026-08-03)."""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.commercial_rules_volumetric_v2 import (  # noqa: E402
    AMBALARE_COMMERCIAL_EUR_SET,
    BACK_CNC_COMMERCIAL_EUR_M2,
    LED_MODULE_COMMERCIAL_EUR_BUC,
    OWNER_CONFIRMED_PROVISIONAL_COMMERCIAL_LINE_CODES,
    OWNER_CONFIRMED_PROVISIONAL_CONFIRMATION_DATE,
    OWNER_MISSING_COMMERCIAL_RATE_CODES,
    PILOT_TEMPLATE,
    PSU_COMMERCIAL_EUR_BUC,
    classify_commercial_rule_publication,
    inventory_commercial_rules_for_template,
)
from services.template_pricing_recipe_service import (  # noqa: E402
    ACM_BOXED_TEMPLATE,
    TemplatePricingRecipeService,
    VL_TEMPLATE,
)
from tests.test_commercial_price_proposal_preview import (  # noqa: E402
    TEMPLATE,
    _full_quote_input,
)

pytest_plugins = [
    "tests.test_product_aggregate_volumetric_v2",
    "tests.test_commercial_price_proposal_preview",
]


EXPECTED_RATES = {
    "debitare_spate": (BACK_CNC_COMMERCIAL_EUR_M2, "m2", 15.0),
    "sistem_led_module": (LED_MODULE_COMMERCIAL_EUR_BUC, "buc", 1.5),
    "sursa_led": (PSU_COMMERCIAL_EUR_BUC, "buc", 35.0),
    "ambalare": (AMBALARE_COMMERCIAL_EUR_SET, "set", 20.0),
}


class TestF7I1CatalogConstants(unittest.TestCase):
    def test_owner_confirmed_exact_values(self) -> None:
        self.assertEqual(BACK_CNC_COMMERCIAL_EUR_M2, 15.0)
        self.assertEqual(LED_MODULE_COMMERCIAL_EUR_BUC, 1.5)
        self.assertEqual(PSU_COMMERCIAL_EUR_BUC, 35.0)
        self.assertEqual(AMBALARE_COMMERCIAL_EUR_SET, 20.0)
        self.assertEqual(OWNER_CONFIRMED_PROVISIONAL_CONFIRMATION_DATE, "2026-08-03")
        self.assertEqual(OWNER_MISSING_COMMERCIAL_RATE_CODES, frozenset())

    def test_inventory_marks_four_as_provisional_not_missing(self) -> None:
        inv = inventory_commercial_rules_for_template(PILOT_TEMPLATE)
        by_code = {str(row["canonical_rule_code"]): row for row in inv}
        for code, (rate, unit, exact) in EXPECTED_RATES.items():
            self.assertIn(code, by_code)
            row = by_code[code]
            self.assertEqual(row["publication_state"], "ACTIVE_PROVISIONAL")
            self.assertEqual(row["current_rate"], exact)
            self.assertEqual(row["pricing_unit"], unit)
            self.assertEqual(row["currency"], "EUR")
            self.assertEqual(row["provisional_nature"], "owner_confirmed_provisional")
            self.assertEqual(row["confirmation_date"], "2026-08-03")
            self.assertTrue(row["final_pricing_review_required"])
            self.assertIsNone(row["owner_question"])
            self.assertEqual(rate, exact)


class TestF7I1TemplateRecipe(unittest.IsolatedAsyncioTestCase):
    async def test_template_resolves_provisional_rates_read_only(self) -> None:
        db = MagicMock()
        row = MagicMock()
        row.family_name = "Volumetric Letters"
        row.active = True
        row.version = "2"
        row.template_code = VL_TEMPLATE
        result = MagicMock()
        result.scalar_one_or_none.return_value = row
        db.execute = AsyncMock(return_value=result)

        service = TemplatePricingRecipeService(db)
        service._registry.build_registry = AsyncMock(
            return_value={"summary": {"owner_confirmed": 0, "missing_price": 0}, "items": []}
        )
        recipe = await service.build_recipe(VL_TEMPLATE)
        assert recipe is not None
        by_code = {r.stable_code: r for r in recipe.recipe if r.recipe_kind == "commercial_line"}
        for code, (_rate, unit, exact) in EXPECTED_RATES.items():
            item = by_code[code]
            self.assertEqual(item.commercial_reference_status, "ACTIVE_PROVISIONAL")
            self.assertEqual(item.current_value, exact)
            self.assertEqual(item.currency, "EUR")
            self.assertEqual(item.unit, unit)
            self.assertFalse(item.editable)
            self.assertNotIn("COMMERCIAL_RATE_MISSING", item.blockers)
            self.assertIn(
                "OWNER_CONFIRMED_PROVISIONAL_COMMERCIAL_RATE_FINAL_REVIEW_REQUIRED",
                item.warnings,
            )
            self.assertIn("provizoriu", (item.cost_label_ro or "").lower())
            self.assertEqual(item.catalog_owner, "commercial_rules_volumetric_v2")
            self.assertEqual(item.rate_publication_status, "provisional")

    async def test_acm_treatment_still_blocked(self) -> None:
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
                "summary": {"owner_confirmed": 5, "missing_price": 0},
                "items": [],
            }
        )
        recipe = await service.build_recipe(ACM_BOXED_TEMPLATE)
        assert recipe is not None
        self.assertEqual(recipe.acm_acceptance.shell_registry_confirmed, 5)
        self.assertEqual(recipe.acm_acceptance.shell_registry_missing, 0)
        self.assertIs(recipe.acm_acceptance.treatment_commercial_lines_allowed, False)
        self.assertIn(
            "ACM_TREATMENT_COMMERCIAL_BLOCKED",
            recipe.readiness.real_blockers_retained,
        )


@pytest.mark.asyncio
async def test_f7i1_cpp_lines_use_owner_provisional_rates(cpp_service):
    payload = _full_quote_input()
    # Ensure packaging module is selected so ambalare is applicable.
    finish = payload.setdefault("finish_setup", {})
    finish["ambalare_livrare_montaj"] = True
    finish["packaging_included"] = True
    modules = payload.setdefault("modules", {})
    if isinstance(modules, dict):
        modules["ambalare_livrare_montaj"] = {"enabled": True, "selected": True}

    preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    by_code = {line.code: line for line in preview.commercial_price_lines}

    back = by_code["debitare_spate"]
    assert back.commercial_unit_price == pytest.approx(15.0)
    assert back.unit == "m2"
    assert back.cpp_currency == "EUR"
    assert back.owner_decision_required is False
    assert back.rate_publication_status == "provisional"
    assert "owner_confirmed_provisional" in (back.source or "")

    led = by_code["sistem_led_module"]
    assert led.commercial_unit_price == pytest.approx(1.5)
    assert led.unit == "buc"
    assert led.owner_decision_required is False
    assert led.rate_publication_status == "provisional"

    psu = by_code["sursa_led"]
    assert psu.commercial_unit_price == pytest.approx(35.0)
    assert psu.unit == "buc"
    assert psu.owner_decision_required is False

    ambalare = by_code.get("ambalare")
    if ambalare is not None:
        assert ambalare.commercial_unit_price == pytest.approx(20.0)
        assert ambalare.unit == "set"
        assert ambalare.owner_decision_required is False
        assert ambalare.rate_publication_status == "provisional"

    assert not any(
        d.code
        in {
            "DEBITARE_SPATE_COMMERCIAL_EUR_M2",
            "LED_MODULE_COMMERCIAL_EUR_BUC",
            "PSU_COMMERCIAL_EUR_BUC",
            "AMBALARE_COMMERCIAL_RULE",
        }
        for d in preview.unknown_owner_decisions
    )


@pytest.mark.asyncio
async def test_f7i1_classify_owner_confirmed_codes():
    inv = inventory_commercial_rules_for_template(PILOT_TEMPLATE)
    for row in inv:
        code = str(row["canonical_rule_code"])
        if code in OWNER_CONFIRMED_PROVISIONAL_COMMERCIAL_LINE_CODES & {
            "ambalare",
            "debitare_spate",
            "sistem_led_module",
            "sursa_led",
        }:
            assert row["publication_state"] == "ACTIVE_PROVISIONAL"


@pytest.mark.asyncio
async def test_f7i1_snapshot_embeds_owner_provisional_rates(cpp_service):
    """Snapshot V2 freezes Owner provisional rates + provenance (no live reprice of the object)."""
    from services.quote_snapshot_v2_service import QuoteSnapshotV2Service

    payload = _full_quote_input()
    snap_svc = QuoteSnapshotV2Service(cpp_service._db)
    snap = await snap_svc.build_preview(TEMPLATE, quote_input=payload)
    assert snap is not None
    commercial = snap.commercial_price_proposal_snapshot
    by_code = {line.code: line for line in commercial.commercial_price_lines}

    back = by_code["debitare_spate"]
    assert back.commercial_unit_price == pytest.approx(15.0)
    assert back.unit == "m2"
    assert back.cpp_currency == "EUR"
    assert back.rate_publication_status == "provisional"
    assert "owner_confirmed_provisional" in (back.source or "")

    led = by_code["sistem_led_module"]
    assert led.commercial_unit_price == pytest.approx(1.5)
    assert led.rate_publication_status == "provisional"

    psu = by_code["sursa_led"]
    assert psu.commercial_unit_price == pytest.approx(35.0)
    assert psu.rate_publication_status == "provisional"

    # Object identity freeze: mutating the in-memory snapshot line must not alter a fresh rebuild.
    back.commercial_unit_price = 99.0
    snap_b = await snap_svc.build_preview(TEMPLATE, quote_input=payload)
    assert snap_b is not None
    back_b = next(
        line
        for line in snap_b.commercial_price_proposal_snapshot.commercial_price_lines
        if line.code == "debitare_spate"
    )
    assert back_b.commercial_unit_price == pytest.approx(15.0)


if __name__ == "__main__":
    unittest.main()
