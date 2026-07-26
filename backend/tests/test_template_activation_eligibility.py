"""TEMPLATE_ACTIVATION_V1 — eligibility map and structural vs optional blockers."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.template_activation_eligibility import (  # noqa: E402
    build_activation_eligibility,
    classify_finding_scope,
    is_structural_known_conflict,
)


class TestActivationEligibility(unittest.TestCase):
    def test_known_conflicts_mostly_warnings(self) -> None:
        self.assertTrue(is_structural_known_conflict("required_inactive_child"))
        self.assertFalse(is_structural_known_conflict("TEMPLATE_IDENTITY"))

    def test_optional_logo_honesty(self) -> None:
        scope = classify_finding_scope(
            {
                "check_id": "components.acm_logo_branch_honesty",
                "status": "PASS_WITH_WARNINGS",
                "blocking": False,
                "evidence": {"optional_capability": True, "optional_absent_ok": True},
            }
        )
        self.assertEqual(scope, "optional_capability")

    def test_vl_publishable_with_ai(self) -> None:
        elig = build_activation_eligibility(
            template_code="TPL-VOLUMETRIC-LETTERS_v2",
            publication_status=None,
            effective_status="LEGACY_UNSPECIFIED",
            db_active=True,
            e2e_verdict="STATIC_READY_WITH_WARNINGS",
            e2e_ready=False,
            known_conflicts=["TEMPLATE_IDENTITY", "DOSSIER_METADATA_ONLY"],
            findings=[],
            pricing_activation="ACTIVE_WITH_AI_DEFAULTS",
            ai_decisions=[{"decision_id": "AI_PACK_PRODUCT_BAND"}],
        )
        self.assertTrue(elig["publication_eligible"])
        self.assertTrue(elig["ai_defaults"]["uses_ai_defaults"])
        self.assertEqual(elig["target_state"], "PUBLISHED")
        self.assertEqual(elig["structural_blockers"], [])

    def test_inactive_child_blocks(self) -> None:
        elig = build_activation_eligibility(
            template_code="TPL-VOLUMETRIC-LETTERS_v2",
            publication_status=None,
            effective_status="LEGACY_UNSPECIFIED",
            db_active=True,
            e2e_verdict="BLOCKED",
            e2e_ready=False,
            known_conflicts=["required_inactive_child"],
            findings=[
                {
                    "check_id": "components.required_child",
                    "status": "BLOCKED",
                    "blocking": True,
                    "evidence": {"conflict_code": "required_inactive_child"},
                }
            ],
            pricing_activation="ACTIVE_WITH_AI_DEFAULTS",
            ai_decisions=[],
        )
        self.assertFalse(elig["publication_eligible"])
        self.assertTrue(any("required_inactive_child" in b for b in elig["structural_blockers"]))


if __name__ == "__main__":
    unittest.main()
