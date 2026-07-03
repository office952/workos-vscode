"""
BUILD 12 — Tests for Quote-to-Order Document Snapshot Policy.

Verifies the policy rules governing when a document snapshot reference
is required, optional, or blocked during quote → order conversion.

Policy rules:
  1. Approved snapshot → reference is created automatically (eligible).
  2. Pending snapshot → warning, requires acknowledgement.
  3. Rejected snapshot → blocked, cannot create reference.
  4. No snapshot → missing, order proceeds without reference.
  5. Multiple snapshots → latest approved is selected.
  6. Governance status is captured at acceptance time.
"""

from __future__ import annotations

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.order_output_snapshot_reference_service import (
    OrderOutputSnapshotReferenceService,
)


class TestDocumentSnapshotPolicyEligibility(unittest.TestCase):
    """Tests for snapshot eligibility evaluation policy."""

    def setUp(self):
        self.svc = OrderOutputSnapshotReferenceService()

    def test_approved_status_is_eligible(self):
        """approved_for_quote_output status is eligible."""
        result = self.svc.check_snapshot_eligibility("approved_for_quote_output")
        self.assertEqual(result["status"], "eligible")
        self.assertIn("detail", result)

    def test_pending_review_is_warning(self):
        """pending_review status triggers warning."""
        result = self.svc.check_snapshot_eligibility("pending_review")
        self.assertEqual(result["status"], "warning")
        self.assertTrue(result.get("requires_acknowledgement", False))

    def test_rejected_is_blocked(self):
        """rejected status blocks reference creation."""
        result = self.svc.check_snapshot_eligibility("rejected")
        self.assertEqual(result["status"], "blocked")

    def test_draft_is_warning(self):
        """draft status triggers warning."""
        result = self.svc.check_snapshot_eligibility("draft")
        self.assertEqual(result["status"], "warning")

    def test_none_is_missing(self):
        """None status means no snapshot available."""
        result = self.svc.check_snapshot_eligibility(None)
        self.assertEqual(result["status"], "missing")

    def test_empty_string_is_missing(self):
        """Empty string status means no snapshot available."""
        result = self.svc.check_snapshot_eligibility("")
        self.assertEqual(result["status"], "missing")

    def test_unknown_status_is_info(self):
        """Unknown status returns info level."""
        result = self.svc.check_snapshot_eligibility("some_future_status")
        self.assertEqual(result["status"], "info")


class TestDocumentSnapshotPolicySelection(unittest.TestCase):
    """Tests for snapshot selection logic when multiple snapshots exist."""

    def setUp(self):
        self.svc = OrderOutputSnapshotReferenceService()

    def test_select_best_snapshot_picks_approved(self):
        """When multiple snapshots exist, approved one is selected."""
        snapshots = [
            {"id": 1, "status": "draft", "version": 1},
            {"id": 2, "status": "approved_for_quote_output", "version": 2},
            {"id": 3, "status": "pending_review", "version": 3},
        ]
        best = self.svc.select_best_snapshot(snapshots)
        self.assertIsNotNone(best)
        self.assertEqual(best["id"], 2)

    def test_select_best_snapshot_picks_latest_approved(self):
        """When multiple approved snapshots exist, latest version is selected."""
        snapshots = [
            {"id": 1, "status": "approved_for_quote_output", "version": 1},
            {"id": 2, "status": "approved_for_quote_output", "version": 3},
            {"id": 3, "status": "approved_for_quote_output", "version": 2},
        ]
        best = self.svc.select_best_snapshot(snapshots)
        self.assertIsNotNone(best)
        self.assertEqual(best["id"], 2)

    def test_select_best_snapshot_returns_none_when_empty(self):
        """When no snapshots exist, returns None."""
        best = self.svc.select_best_snapshot([])
        self.assertIsNone(best)

    def test_select_best_snapshot_falls_back_to_pending(self):
        """When no approved snapshot exists, falls back to pending_review."""
        snapshots = [
            {"id": 1, "status": "draft", "version": 1},
            {"id": 2, "status": "pending_review", "version": 2},
        ]
        best = self.svc.select_best_snapshot(snapshots)
        self.assertIsNotNone(best)
        self.assertEqual(best["id"], 2)

    def test_select_best_snapshot_skips_rejected(self):
        """Rejected snapshots are never selected."""
        snapshots = [
            {"id": 1, "status": "rejected", "version": 5},
            {"id": 2, "status": "draft", "version": 1},
        ]
        best = self.svc.select_best_snapshot(snapshots)
        self.assertIsNotNone(best)
        self.assertEqual(best["id"], 2)


class TestDocumentSnapshotPolicyGovernance(unittest.TestCase):
    """Tests for governance status capture at acceptance."""

    def setUp(self):
        self.svc = OrderOutputSnapshotReferenceService()

    def test_governance_status_eligible_for_approved(self):
        """Approved snapshot yields eligible governance status."""
        gov = self.svc.determine_governance_status("approved_for_quote_output")
        self.assertEqual(gov, "eligible")

    def test_governance_status_needs_review_for_pending(self):
        """Pending snapshot yields needs_review governance status."""
        gov = self.svc.determine_governance_status("pending_review")
        self.assertEqual(gov, "needs_review")

    def test_governance_status_blocked_for_rejected(self):
        """Rejected snapshot yields blocked governance status."""
        gov = self.svc.determine_governance_status("rejected")
        self.assertEqual(gov, "blocked")

    def test_governance_status_missing_for_none(self):
        """None status yields missing governance status."""
        gov = self.svc.determine_governance_status(None)
        self.assertEqual(gov, "missing")

    def test_governance_status_unknown_for_other(self):
        """Unknown status yields unknown governance status."""
        gov = self.svc.determine_governance_status("future_status")
        self.assertEqual(gov, "unknown")


if __name__ == "__main__":
    unittest.main()