"""AI_OPERATIONAL_DEFAULTS_V1 — contract, precedence, packaging/electrical/LED."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.ai_operational_defaults_v1 import (  # noqa: E402
    SOURCE_PRECEDENCE,
    resolve_packaging_band,
)
from services.ai_operational_defaults import (  # noqa: E402
    apply_ai_defaults_to_labor_recipes,
    build_ai_decisions_for_template,
    compute_activation_status,
    save_override,
)


class TestPackagingBands(unittest.TestCase):
    def test_size_bands_no_time(self) -> None:
        small = resolve_packaging_band(face_area_m2=0.2, illuminated=False, overrides={})
        med = resolve_packaging_band(face_area_m2=1.0, illuminated=False, overrides={})
        large = resolve_packaging_band(face_area_m2=3.0, illuminated=True, overrides={})
        self.assertEqual(small.band, "SMALL")
        self.assertEqual(med.band, "MEDIUM")
        self.assertEqual(large.band, "LARGE")
        self.assertGreater(large.value, med.value)
        self.assertGreater(large.fragile_addon, 0)


class TestAiLaborApply(unittest.TestCase):
    def test_packaging_and_electrical_receive_ai(self) -> None:
        decisions = build_ai_decisions_for_template(
            "TPL-VOLUMETRIC-LETTERS_v2",
            illuminated=True,
            psu_count=2,
        )
        self.assertTrue(any(d["domain"] == "packaging" for d in decisions))
        self.assertTrue(any(d["domain"] == "electrical" for d in decisions))
        self.assertTrue(any(d["domain"] == "led" for d in decisions))
        labor = [
            {
                "catalog_code": "PACKAGING",
                "operation_code": "PACKAGING",
                "status": "missing",
                "internal_cost_rate": None,
                "formula_status": "MISSING_OWNER_FORMULA",
                "quantity_keys": [],
                "blockers": ["MISSING_CATALOG_RATE"],
                "warnings": [],
                "technical_ready": False,
                "commercial_ready": False,
                "base_rate_source": "missing",
            },
            {
                "catalog_code": "ELECTRICAL_WIRING",
                "operation_code": "ELECTRICAL_WIRING",
                "status": "warning",
                "internal_cost_rate": 10.0,
                "formula_status": "OPERATION_ONLY",
                "quantity_keys": [],
                "blockers": [],
                "warnings": [],
                "technical_ready": False,
                "commercial_ready": False,
                "base_rate_source": "pricing_registry",
            },
            {
                "catalog_code": "LED_ASSEMBLY",
                "operation_code": "LED_ASSEMBLY",
                "status": "warning",
                "internal_cost_rate": 2.0,
                "formula_status": "QUANTITY_KEY_CONFIRMED",
                "quantity_keys": ["letter_led_module_count"],
                "blockers": [],
                "warnings": ["LED_ASSEMBLY_TIME_NOT_BOUND"],
                "technical_ready": True,
                "commercial_ready": False,
                "base_rate_source": "pricing_registry",
            },
        ]
        out, demoted = apply_ai_defaults_to_labor_recipes(
            template_code="TPL-VOLUMETRIC-LETTERS_v2",
            labor_recipes=labor,
            ai_decisions=decisions,
        )
        pack = next(r for r in out if r["catalog_code"] == "PACKAGING")
        self.assertEqual(pack["decision_source"], "AI_DECISION")
        self.assertEqual(pack["status"], "warning")
        self.assertTrue(pack["commercial_ready"])
        elec = next(r for r in out if r["catalog_code"] == "ELECTRICAL_WIRING")
        self.assertEqual(elec["decision_source"], "CATALOG")  # catalog beats AI
        self.assertEqual(elec["ai_decision_id"], "AI_ELEC_MIN_PRODUCT")
        led = next(r for r in out if r["catalog_code"] == "LED_ASSEMBLY")
        self.assertEqual(led["decision_source"], "CATALOG")  # catalog beats AI
        self.assertTrue(pack["is_configurable"])
        self.assertIn("MISSING_OWNER_FORMULA", demoted)

    def test_activation_status(self) -> None:
        self.assertEqual(
            compute_activation_status(
                technical_ready=True,
                commercial_ready=True,
                has_ai_decisions=True,
                ai_covers_gaps=True,
                has_real_blockers=False,
                has_warnings=True,
            ),
            "ACTIVE_WITH_AI_DEFAULTS",
        )
        self.assertEqual(
            compute_activation_status(
                technical_ready=True,
                commercial_ready=True,
                has_ai_decisions=False,
                ai_covers_gaps=False,
                has_real_blockers=False,
                has_warnings=False,
            ),
            "ACTIVE_WITH_CONFIRMED_TRUTH",
        )
        self.assertEqual(
            compute_activation_status(
                technical_ready=True,
                commercial_ready=True,
                has_ai_decisions=True,
                ai_covers_gaps=True,
                has_real_blockers=True,
                has_warnings=True,
            ),
            "ACTIVE_WITH_WARNINGS",
        )

    def test_precedence_tuple(self) -> None:
        self.assertEqual(SOURCE_PRECEDENCE[0], "MEASURED_REALITY")
        self.assertEqual(SOURCE_PRECEDENCE[3], "AI_DECISION")

    def test_override_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "overrides.json"
            with patch("services.ai_operational_defaults._OVERRIDES_PATH", path):
                save_override("AI_LED_PER_MODULE", 0.5)
                from services.ai_operational_defaults import load_overrides

                self.assertEqual(load_overrides().get("AI_LED_PER_MODULE"), 0.5)


if __name__ == "__main__":
    unittest.main()
