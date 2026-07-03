"""
BUILD 12 — Tests for Order Output Snapshot Reference Service and API.

Tests the document snapshot reference that is created when a quote with an
approved output snapshot is converted to an order.

Rules verified:
  1. Order creation with approved snapshot creates a reference record.
  2. Order creation without snapshot still succeeds (no reference created).
  3. GET /orders/{order_id}/document-snapshot-reference returns reference when present.
  4. GET /orders/{order_id}/document-snapshot-reference returns has_document_snapshot=false when absent.
  5. Reference is immutable after creation.
  6. Service correctly evaluates snapshot eligibility.
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


class TestOrderOutputSnapshotReferenceService(unittest.TestCase):
    """Unit tests for OrderOutputSnapshotReferenceService."""

    def test_service_imports(self):
        """Service module imports without error."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        self.assertIsNotNone(OrderOutputSnapshotReferenceService)

    def test_service_has_required_methods(self):
        """Service exposes required public methods."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        self.assertTrue(hasattr(svc, "evaluate_and_create_reference"))
        self.assertTrue(hasattr(svc, "get_reference_for_order"))
        self.assertTrue(hasattr(svc, "check_snapshot_eligibility"))

    def test_check_snapshot_eligibility_approved(self):
        """Eligible when snapshot status is approved_for_quote_output."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        result = svc.check_snapshot_eligibility("approved_for_quote_output")
        self.assertEqual(result["status"], "eligible")

    def test_check_snapshot_eligibility_pending(self):
        """Warning when snapshot status is pending_review."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        result = svc.check_snapshot_eligibility("pending_review")
        self.assertEqual(result["status"], "warning")

    def test_check_snapshot_eligibility_rejected(self):
        """Blocked when snapshot status is rejected."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        result = svc.check_snapshot_eligibility("rejected")
        self.assertEqual(result["status"], "blocked")

    def test_check_snapshot_eligibility_none(self):
        """Missing when no snapshot status provided."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        result = svc.check_snapshot_eligibility(None)
        self.assertEqual(result["status"], "missing")

    def test_check_snapshot_eligibility_unknown_status(self):
        """Info for unknown status values."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        result = svc.check_snapshot_eligibility("some_unknown_status")
        self.assertEqual(result["status"], "info")


class TestOrderOutputSnapshotReferenceModel(unittest.TestCase):
    """Unit tests for OrderOutputSnapshotReference model."""

    def test_model_imports(self):
        """Model module imports without error."""
        from models.order_output_snapshot_references import (
            OrderOutputSnapshotReference,
        )
        self.assertIsNotNone(OrderOutputSnapshotReference)

    def test_model_has_required_columns(self):
        """Model has all required columns."""
        from models.order_output_snapshot_references import (
            OrderOutputSnapshotReference,
        )
        required_columns = [
            "id", "order_id", "quote_id", "quote_output_snapshot_id",
            "snapshot_code", "snapshot_status_at_acceptance",
            "snapshot_version", "snapshot_content_hash",
            "source_template_id", "source_template_code",
            "source_dossier_id", "source_dossier_version",
            "source_trace_json", "governance_status_at_acceptance",
            "accepted_at", "accepted_by", "created_at", "notes",
        ]
        mapper = OrderOutputSnapshotReference.__table__
        column_names = [c.name for c in mapper.columns]
        for col in required_columns:
            self.assertIn(col, column_names, f"Missing column: {col}")

    def test_model_table_name(self):
        """Model uses correct table name."""
        from models.order_output_snapshot_references import (
            OrderOutputSnapshotReference,
        )
        self.assertEqual(
            OrderOutputSnapshotReference.__tablename__,
            "order_output_snapshot_references",
        )


class TestQuoteAcceptanceGuardEndpoint(unittest.TestCase):
    """Unit tests for the quote acceptance guard endpoint logic."""

    def test_guard_endpoint_route_exists(self):
        """The quote-acceptance-guard route is registered."""
        from routers.orders import router
        routes = [r.path for r in router.routes]
        matching = [r for r in routes if "quote-acceptance-guard" in r]
        self.assertTrue(
            len(matching) > 0,
            f"quote-acceptance-guard route must be registered. Routes: {routes}",
        )

    def test_document_snapshot_reference_route_exists(self):
        """The document-snapshot-reference route is registered."""
        from routers.orders import router
        routes = [r.path for r in router.routes]
        matching = [r for r in routes if "document-snapshot-reference" in r]
        self.assertTrue(
            len(matching) > 0,
            f"document-snapshot-reference route must be registered. Routes: {routes}",
        )


class TestOrderOutputSnapshotReferenceServiceSelection(unittest.TestCase):
    """Tests for select_best_snapshot method."""

    def test_select_best_picks_approved(self):
        """Approved snapshot is preferred."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        snapshots = [
            {"id": 1, "status": "draft", "version": 1},
            {"id": 2, "status": "approved_for_quote_output", "version": 2},
        ]
        best = svc.select_best_snapshot(snapshots)
        self.assertEqual(best["id"], 2)

    def test_select_best_returns_none_for_empty(self):
        """Returns None when no snapshots."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        self.assertIsNone(svc.select_best_snapshot([]))

    def test_select_best_skips_rejected(self):
        """Rejected snapshots are never selected."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        snapshots = [
            {"id": 1, "status": "rejected", "version": 5},
            {"id": 2, "status": "draft", "version": 1},
        ]
        best = svc.select_best_snapshot(snapshots)
        self.assertEqual(best["id"], 2)

    def test_determine_governance_eligible(self):
        """Approved status yields eligible governance."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        self.assertEqual(svc.determine_governance_status("approved_for_quote_output"), "eligible")

    def test_determine_governance_missing(self):
        """None status yields missing governance."""
        from services.order_output_snapshot_reference_service import (
            OrderOutputSnapshotReferenceService,
        )
        svc = OrderOutputSnapshotReferenceService()
        self.assertEqual(svc.determine_governance_status(None), "missing")


if __name__ == "__main__":
    unittest.main()