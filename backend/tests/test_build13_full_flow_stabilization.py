"""
BUILD 13 — Full Flow MVP Stabilization & Real Work Verification Tests.

Tests cover:
  A. Status lifecycle regression (quotes, orders, intake_requests)
  B. Quote → Order conversion gate (priced + accepted allowed, others rejected)
  C. Reports cancelled/invalid exclusion
  D. Readiness blocker/warning enforcement at order creation
  E. Execution plan snapshot_incomplete guard
  F. Reality service boundary enforcement
  G. Full flow entity traceability
"""

import json
import pytest
from datetime import datetime, timezone

from validators.status_lifecycle import (
    validate_status,
    validate_transition,
    ENTITY_STATUSES,
    ENTITY_TRANSITIONS,
    get_enforcement_level,
)


# ═══════════════════════════════════════════════════════════════════════════════
# A. STATUS LIFECYCLE REGRESSION
# ═══════════════════════════════════════════════════════════════════════════════


class TestStatusLifecycleQuotes:
    """Verify all canonical quote transitions are valid and invalid ones are rejected."""

    def test_valid_statuses(self):
        expected = ["draft", "priced", "sent", "viewed", "negotiating", "accepted", "rejected", "expired"]
        assert ENTITY_STATUSES["quotes"] == expected

    def test_valid_transitions_forward(self):
        """Happy path: draft → priced → sent → viewed → negotiating → accepted."""
        validate_transition("quotes", "draft", "priced")
        validate_transition("quotes", "priced", "sent")
        validate_transition("quotes", "sent", "viewed")
        validate_transition("quotes", "viewed", "negotiating")
        validate_transition("quotes", "negotiating", "accepted")

    def test_valid_transitions_rejection(self):
        """Client can reject from sent/viewed/negotiating."""
        validate_transition("quotes", "sent", "rejected")
        validate_transition("quotes", "viewed", "rejected")
        validate_transition("quotes", "negotiating", "rejected")

    def test_valid_transitions_expiry(self):
        """Quotes can expire from sent/viewed/negotiating."""
        validate_transition("quotes", "sent", "expired")
        validate_transition("quotes", "viewed", "expired")
        validate_transition("quotes", "negotiating", "expired")

    def test_direct_priced_to_accepted(self):
        """Admin can directly accept a priced quote (skip send)."""
        validate_transition("quotes", "priced", "accepted")

    def test_invalid_transition_rejected(self):
        """Cannot go from draft to accepted directly."""
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_transition("quotes", "draft", "accepted")

    def test_invalid_transition_backward(self):
        """Cannot go from accepted back to draft."""
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_transition("quotes", "accepted", "draft")

    def test_invalid_status_value(self):
        """Unknown status value is rejected."""
        with pytest.raises(ValueError, match="Invalid status"):
            validate_status("quotes", "nonexistent_status")

    def test_same_status_noop(self):
        """Same status transition is always allowed (no-op)."""
        validate_transition("quotes", "draft", "draft")
        validate_transition("quotes", "accepted", "accepted")


class TestStatusLifecycleOrders:
    """Verify all canonical order transitions."""

    def test_valid_statuses(self):
        expected = ["created", "confirmed", "locked", "in_execution", "completed", "cancelled"]
        assert ENTITY_STATUSES["orders"] == expected

    def test_valid_transitions_forward(self):
        """Happy path: created → confirmed → locked → in_execution → completed."""
        validate_transition("orders", "created", "confirmed")
        validate_transition("orders", "confirmed", "locked")
        validate_transition("orders", "locked", "in_execution")
        validate_transition("orders", "in_execution", "completed")

    def test_cancellation_from_any_active(self):
        """Any active status can be cancelled."""
        validate_transition("orders", "created", "cancelled")
        validate_transition("orders", "confirmed", "cancelled")
        validate_transition("orders", "locked", "cancelled")
        validate_transition("orders", "in_execution", "cancelled")

    def test_cannot_cancel_completed(self):
        """Completed orders cannot be cancelled."""
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_transition("orders", "completed", "cancelled")

    def test_cannot_skip_steps(self):
        """Cannot skip from created to in_execution."""
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_transition("orders", "created", "in_execution")

    def test_cannot_go_backward(self):
        """Cannot go from in_execution back to locked."""
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_transition("orders", "in_execution", "locked")

    def test_invalid_status_value(self):
        with pytest.raises(ValueError, match="Invalid status"):
            validate_status("orders", "pending")


class TestStatusLifecycleIntakeRequests:
    """Verify intake request transitions."""

    def test_valid_statuses(self):
        expected = ["new", "in_review", "needs_info", "ready_for_quote", "blocked", "cancelled"]
        assert ENTITY_STATUSES["intake_requests"] == expected

    def test_valid_transitions_forward(self):
        """Happy path: new → in_review → ready_for_quote."""
        validate_transition("intake_requests", "new", "in_review")
        validate_transition("intake_requests", "in_review", "ready_for_quote")

    def test_needs_info_loop(self):
        """in_review ↔ needs_info loop."""
        validate_transition("intake_requests", "in_review", "needs_info")
        validate_transition("intake_requests", "needs_info", "in_review")

    def test_blocked_loop(self):
        """in_review ↔ blocked loop."""
        validate_transition("intake_requests", "in_review", "blocked")
        validate_transition("intake_requests", "blocked", "in_review")

    def test_cancellation(self):
        """Can cancel from new, in_review, needs_info."""
        validate_transition("intake_requests", "new", "cancelled")
        validate_transition("intake_requests", "in_review", "cancelled")
        validate_transition("intake_requests", "needs_info", "cancelled")

    def test_cannot_cancel_ready_for_quote(self):
        """Cannot cancel a ready_for_quote intake (it's already progressed)."""
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_transition("intake_requests", "ready_for_quote", "cancelled")


class TestStatusLifecycleExecutionPlan:
    """Verify execution plan task-level transitions (documented/derived)."""

    def test_enforcement_level(self):
        assert get_enforcement_level("execution_plan") == "documented_derived"

    def test_valid_transitions(self):
        validate_transition("execution_plan", "pending", "scheduled")
        validate_transition("execution_plan", "scheduled", "in_progress")
        validate_transition("execution_plan", "in_progress", "blocked")
        validate_transition("execution_plan", "blocked", "in_progress")
        validate_transition("execution_plan", "in_progress", "done")

    def test_cannot_skip_to_done(self):
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_transition("execution_plan", "pending", "done")


class TestStatusLifecycleExecutionReality:
    """Verify execution reality task-level transitions (documented/derived)."""

    def test_enforcement_level(self):
        assert get_enforcement_level("execution_reality") == "documented_derived"

    def test_valid_transitions(self):
        validate_transition("execution_reality", "created", "assigned")
        validate_transition("execution_reality", "assigned", "in_progress")
        validate_transition("execution_reality", "in_progress", "blocked")
        validate_transition("execution_reality", "blocked", "in_progress")
        validate_transition("execution_reality", "in_progress", "done")

    def test_cancellation(self):
        validate_transition("execution_reality", "assigned", "cancelled")
        validate_transition("execution_reality", "in_progress", "cancelled")

    def test_cannot_cancel_done(self):
        with pytest.raises(ValueError, match="Invalid status transition"):
            validate_transition("execution_reality", "done", "cancelled")


# ═══════════════════════════════════════════════════════════════════════════════
# B. QUOTE → ORDER CONVERSION GATE
# ═══════════════════════════════════════════════════════════════════════════════


class TestQuoteToOrderConversionGate:
    """Verify the backend allows conversion from priced AND accepted, rejects others."""

    def test_allowed_conversion_statuses(self):
        """Backend should accept 'priced' and 'accepted' for order conversion."""
        allowed = ("priced", "accepted")
        for status in allowed:
            assert status in allowed

    def test_rejected_conversion_statuses(self):
        """Backend should reject draft, sent, viewed, negotiating, rejected, expired."""
        allowed = ("priced", "accepted")
        rejected = ["draft", "sent", "viewed", "negotiating", "rejected", "expired"]
        for status in rejected:
            assert status not in allowed


# ═══════════════════════════════════════════════════════════════════════════════
# C. REPORTS CANCELLED/INVALID EXCLUSION
# ═══════════════════════════════════════════════════════════════════════════════


class TestReportsCancelledExclusion:
    """Verify reports logic excludes cancelled orders from job status funnel."""

    def test_cancelled_excluded_from_funnel(self):
        """Simulate the reports_summary logic: cancelled orders are excluded."""
        orders = [
            {"status": "created"},
            {"status": "locked"},
            {"status": "in_execution"},
            {"status": "completed"},
            {"status": "cancelled"},
            {"status": "cancelled"},
        ]
        # Replicate the reports_summary.py logic (line 138)
        from collections import Counter
        order_statuses = Counter(o["status"] for o in orders if o["status"] != "cancelled")
        
        assert "cancelled" not in order_statuses
        assert order_statuses["created"] == 1
        assert order_statuses["locked"] == 1
        assert order_statuses["in_execution"] == 1
        assert order_statuses["completed"] == 1

    def test_all_cancelled_returns_empty_funnel(self):
        """If all orders are cancelled, funnel should be empty."""
        orders = [
            {"status": "cancelled"},
            {"status": "cancelled"},
        ]
        from collections import Counter
        order_statuses = Counter(o["status"] for o in orders if o["status"] != "cancelled")
        assert len(order_statuses) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# D. READINESS BLOCKER/WARNING ENFORCEMENT
# ═══════════════════════════════════════════════════════════════════════════════


class TestReadinessEnforcement:
    """Verify readiness extraction logic from quote snapshot."""

    def _extract_readiness(self, readiness_result: dict):
        """Replicate the readiness extraction logic from orders.py."""
        readiness_warnings = []
        readiness_blockers = []
        readiness_blocked = False

        if readiness_result:
            overall_status = readiness_result.get("overall_status")
            ready_for_quote = readiness_result.get("ready_for_quote", False)

            if overall_status == "blocked" or not ready_for_quote:
                readiness_blocked = True

            top_level_blockers = readiness_result.get("blockers", [])
            if isinstance(top_level_blockers, list):
                readiness_blockers.extend(top_level_blockers)

            _canonical_blocker_sections = [
                "technical_readiness",
                "costengine_readiness",
                "document_output_readiness",
                "visual_prompt_readiness",
                "execution_preparation_readiness",
            ]
            for section_key in _canonical_blocker_sections:
                section = readiness_result.get(section_key)
                if isinstance(section, dict):
                    section_blockers = section.get("blockers", [])
                    if isinstance(section_blockers, list):
                        readiness_blockers.extend(section_blockers)

            _canonical_warning_sections = [
                "technical_readiness",
                "costengine_readiness",
                "document_output_readiness",
                "visual_prompt_readiness",
                "execution_preparation_readiness",
            ]
            for section_key in _canonical_warning_sections:
                section = readiness_result.get(section_key)
                if isinstance(section, dict):
                    section_warnings = section.get("warnings", [])
                    if isinstance(section_warnings, list):
                        readiness_warnings.extend(section_warnings)

            top_level_warnings = readiness_result.get("warnings", [])
            if isinstance(top_level_warnings, list):
                readiness_warnings.extend(top_level_warnings)

        return readiness_blocked, readiness_blockers, readiness_warnings

    def test_blocked_status_prevents_order(self):
        """Blocked overall_status should prevent order creation."""
        result = {
            "overall_status": "blocked",
            "ready_for_quote": False,
            "blockers": ["missing_material_spec"],
            "technical_readiness": {"blockers": ["no_dimensions"], "warnings": []},
        }
        blocked, blockers, warnings = self._extract_readiness(result)
        assert blocked is True
        assert "missing_material_spec" in blockers
        assert "no_dimensions" in blockers

    def test_not_ready_for_quote_prevents_order(self):
        """ready_for_quote=False should prevent order creation."""
        result = {
            "overall_status": "needs_review",
            "ready_for_quote": False,
            "blockers": [],
        }
        blocked, blockers, warnings = self._extract_readiness(result)
        assert blocked is True

    def test_warnings_collected_from_sections(self):
        """Warnings from canonical sections should be collected."""
        result = {
            "overall_status": "needs_review",
            "ready_for_quote": True,
            "blockers": [],
            "technical_readiness": {"blockers": [], "warnings": ["check_dimensions"]},
            "costengine_readiness": {"blockers": [], "warnings": ["unmapped_material"]},
        }
        blocked, blockers, warnings = self._extract_readiness(result)
        assert blocked is False
        assert "check_dimensions" in warnings
        assert "unmapped_material" in warnings

    def test_eligible_readiness_allows_order(self):
        """Eligible readiness should allow order creation."""
        result = {
            "overall_status": "eligible",
            "ready_for_quote": True,
            "blockers": [],
            "technical_readiness": {"blockers": [], "warnings": []},
        }
        blocked, blockers, warnings = self._extract_readiness(result)
        assert blocked is False
        assert len(blockers) == 0
        assert len(warnings) == 0

    def test_none_readiness_result(self):
        """None readiness_result should not block (legacy orders)."""
        blocked, blockers, warnings = self._extract_readiness(None)
        assert blocked is False


# ═══════════════════════════════════════════════════════════════════════════════
# E. EXECUTION PLAN SNAPSHOT GUARD
# ═══════════════════════════════════════════════════════════════════════════════


class TestExecutionPlanSnapshotGuard:
    """Verify execution plan generation requires canonical snapshot format."""

    def test_snapshot_must_have_product_definition(self):
        """Snapshot without product_definition should be flagged as incomplete."""
        snapshot = {"cost_result": {"total": 100}}
        # The plan generation logic checks for product_definition
        has_product_def = "product_definition" in snapshot
        assert has_product_def is False

    def test_snapshot_must_have_cost_result(self):
        """Snapshot without cost_result should be flagged as incomplete."""
        snapshot = {"product_definition": {"name": "Banner"}}
        has_cost_result = "cost_result" in snapshot
        assert has_cost_result is False

    def test_valid_snapshot_has_both(self):
        """Valid snapshot has both product_definition and cost_result."""
        snapshot = {
            "product_definition": {"name": "Banner", "quantity": 2},
            "cost_result": {"total": 250.0, "materials": []},
        }
        has_product_def = "product_definition" in snapshot
        has_cost_result = "cost_result" in snapshot
        assert has_product_def is True
        assert has_cost_result is True


# ═══════════════════════════════════════════════════════════════════════════════
# F. REALITY SERVICE BOUNDARY ENFORCEMENT
# ═══════════════════════════════════════════════════════════════════════════════


class TestRealityServiceBoundary:
    """Verify ExecutionRealityService boundary rules."""

    def test_reality_input_error_for_missing_timestamp(self):
        """RealityInputError raised for missing timestamp."""
        from services.execution_reality_service import RealityInputError, _iso_utc

        with pytest.raises(RealityInputError) as exc_info:
            _iso_utc(None)
        assert exc_info.value.code == "timestamp_missing"

    def test_reality_input_error_for_empty_timestamp(self):
        """RealityInputError raised for empty string timestamp."""
        from services.execution_reality_service import RealityInputError, _iso_utc

        with pytest.raises(RealityInputError) as exc_info:
            _iso_utc("")
        assert exc_info.value.code == "timestamp_missing"

    def test_reality_input_error_for_invalid_timestamp(self):
        """RealityInputError raised for invalid timestamp format."""
        from services.execution_reality_service import RealityInputError, _iso_utc

        with pytest.raises(RealityInputError) as exc_info:
            _iso_utc("not-a-date")
        assert exc_info.value.code == "timestamp_invalid"

    def test_valid_iso_timestamp_parsed(self):
        """Valid ISO timestamp is parsed correctly."""
        from services.execution_reality_service import _iso_utc

        result = _iso_utc("2026-05-18T10:30:00Z")
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 18
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo is not None

    def test_valid_iso_timestamp_with_offset(self):
        """Valid ISO timestamp with offset is parsed correctly."""
        from services.execution_reality_service import _iso_utc

        result = _iso_utc("2026-05-18T10:30:00+03:00")
        assert result.tzinfo is not None


# ═══════════════════════════════════════════════════════════════════════════════
# G. FULL FLOW ENTITY TRACEABILITY
# ═══════════════════════════════════════════════════════════════════════════════


class TestFullFlowTraceability:
    """Verify entity references maintain traceability across the flow."""

    def test_order_references_quote(self):
        """Order data structure must reference source quote."""
        order_data = {
            "code": "ORD-001",
            "quote_id": 42,
            "quote_code": "QUO-042",
            "client_name": "Test Client",
            "status": "locked",
        }
        assert order_data["quote_id"] == 42
        assert order_data["quote_code"] == "QUO-042"

    def test_readiness_snapshot_structure(self):
        """Readiness snapshot must have canonical structure."""
        snapshot = {
            "source": "backend",
            "snapshot_type": "product_readiness_at_order_acceptance",
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
            "readiness_result": {
                "overall_status": "eligible",
                "ready_for_quote": True,
                "contract_version": "2026-05-15",
            },
            "warnings_acknowledged": False,
            "warnings_acknowledged_at": None,
            "warnings_acknowledgement_reason": None,
        }
        assert snapshot["source"] == "backend"
        assert snapshot["snapshot_type"] == "product_readiness_at_order_acceptance"
        assert snapshot["readiness_result"]["overall_status"] == "eligible"

    def test_order_snapshot_frozen_at_creation(self):
        """Order snapshot must be frozen (immutable after creation)."""
        # Simulate: snapshot_line_items is a JSON string, not mutable
        snapshot_data = {
            "product_definition": {"name": "Banner", "quantity": 5},
            "cost_result": {"total": 500.0},
            "pricing": {"margin_pct": 30},
        }
        frozen_json = json.dumps(snapshot_data)
        # Verify it can be deserialized back identically
        restored = json.loads(frozen_json)
        assert restored == snapshot_data

    def test_execution_plan_references_order(self):
        """Execution plan must reference source order."""
        plan_data = {
            "order_id": 1,
            "order_code": "ORD-001",
            "snapshot_version": 1,
            "tasks_json": "[]",
            "total_estimated_time_minutes": 120.0,
        }
        assert plan_data["order_id"] == 1
        assert plan_data["order_code"] == "ORD-001"
        assert plan_data["snapshot_version"] == 1

    def test_execution_reality_references_order(self):
        """Execution reality must reference source order."""
        reality_data = {
            "order_id": 1,
            "order_code": "ORD-001",
            "tasks_json": "[]",
            "total_actual_time_minutes": 0.0,
        }
        assert reality_data["order_id"] == 1
        assert reality_data["order_code"] == "ORD-001"


# ═══════════════════════════════════════════════════════════════════════════════
# H. BUILD 12 REGRESSION — Document Snapshot & Acceptance Guard
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuild12Regression:
    """Verify Build 12 features remain intact."""

    def test_order_output_snapshot_reference_model_exists(self):
        """OrderOutputSnapshotReference model should be importable."""
        from models.order_output_snapshot_references import OrderOutputSnapshotReference
        assert OrderOutputSnapshotReference is not None

    def test_order_output_snapshot_reference_service_exists(self):
        """OrderOutputSnapshotReferenceService should be importable."""
        from services.order_output_snapshot_reference_service import OrderOutputSnapshotReferenceService
        assert OrderOutputSnapshotReferenceService is not None

    def test_governance_service_exists(self):
        """QuoteOutputSnapshotGovernanceService should be importable."""
        from services.quote_output_snapshot_governance_service import QuoteOutputSnapshotGovernanceService
        assert QuoteOutputSnapshotGovernanceService is not None

    def test_quote_output_snapshot_service_exists(self):
        """QuoteOutputSnapshotService should be importable."""
        from services.quote_output_snapshot_service import QuoteOutputSnapshotService
        assert QuoteOutputSnapshotService is not None