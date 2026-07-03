"""Tests for intake persistence fields (template confirm, site audit, status)."""

from __future__ import annotations

import json
import unittest

from validators.intake_site_audit import validate_intake_site_audit
from validators.status_lifecycle import validate_transition


class IntakeSiteAuditValidatorTests(unittest.TestCase):
    def test_normalizes_site_audit_shape(self) -> None:
        result = validate_intake_site_audit(
            {
                "mounting_address": "Str. Test",
                "location_photos_status": "received",
                "power_available": "yes",
                "checks": {
                    "address_confirmed": True,
                    "photos_verified": True,
                    "power_confirmed": True,
                },
            }
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["mounting_address"], "Str. Test")
        self.assertTrue(result["checks"]["photos_verified"])

    def test_empty_audit_returns_none(self) -> None:
        self.assertIsNone(validate_intake_site_audit({}))


class IntakeStatusTransitionTests(unittest.TestCase):
    def test_in_review_to_ready_for_quote_allowed(self) -> None:
        validate_transition("intake_requests", "in_review", "ready_for_quote")

    def test_new_to_ready_for_quote_not_allowed(self) -> None:
        with self.assertRaises(ValueError):
            validate_transition("intake_requests", "new", "ready_for_quote")


if __name__ == "__main__":
    unittest.main()
