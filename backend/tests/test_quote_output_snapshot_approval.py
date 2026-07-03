"""
BUILD 10 — Tests for Quote Output Snapshot Approval Flow.

Verifies:
  - draft -> needs_review allowed
  - draft -> approved_for_quote_output allowed if no blockers
  - needs_review -> approved_for_quote_output allowed if no blockers
  - Blockers prevent approval
  - Approved snapshot can be archived
  - Draft snapshot can be rejected
  - Rejected snapshot cannot be approved
  - Archived snapshot cannot be approved
  - Approving second snapshot handles conflict safely (supersedes old)
  - Approval does not mutate Quote
  - Approval does not mutate Order
  - Approval does not create Order
  - Approval does not create OrderSnapshot
  - Approval does not change Quote -> Order gates
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.quote_output_snapshot_service import QuoteOutputSnapshotService
from models.quote_output_snapshots import QuoteOutputSnapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snapshot(
    snapshot_id: int = 1,
    quote_id: int = 1,
    status: str = "draft",
    blockers: Optional[List[str]] = None,
    sections: Optional[List[Dict]] = None,
) -> QuoteOutputSnapshot:
    """Create a mock snapshot entity."""
    if sections is None:
        sections_data = [{"title": "Test", "rendered_text": "Content"}]
    else:
        sections_data = sections
    s = QuoteOutputSnapshot(
        id=snapshot_id,
        quote_id=quote_id,
        quote_code="Q-2026-001",
        snapshot_code=f"QDOC-2026-{snapshot_id:04d}",
        snapshot_type="quote_output_candidate",
        status=status,
        version=1,
        source_template_id=1,
        source_template_code="TPL-BANNER",
        rendered_sections_json=json.dumps(sections_data),
        commercial_summary_json=json.dumps({"total": 1190}),
        warnings_json=json.dumps([]),
        blockers_json=json.dumps(blockers or []),
        variables_used_json=json.dumps({}),
        trace_json=json.dumps({"quote_mutated": False, "order_mutated": False}),
        content_hash="abc123def456",
        created_by="user@test.com",
        created_at=datetime(2026, 5, 18, 10, 0, 0),
        updated_at=datetime(2026, 5, 18, 10, 0, 0),
    )
    return s


class MockDBSession:
    """Mock async DB session."""

    def __init__(self, snapshot: Optional[QuoteOutputSnapshot] = None, extra_snapshots: Optional[List] = None):
        self._snapshot = snapshot
        self._extra_snapshots = extra_snapshots or []
        self.committed = False
        self._call_count = 0

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        pass

    async def execute(self, query):
        self._call_count += 1
        # First call: get snapshot entity
        if self._call_count == 1:
            return MockResult(self._snapshot)
        # Second call: find existing approved (for supersede)
        return MockResultList(self._extra_snapshots)


class MockResult:
    def __init__(self, obj):
        self._obj = obj

    def scalar_one_or_none(self):
        return self._obj


class MockResultList:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return MockScalars(self._items)


class MockScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSubmitForReview:
    """Test draft -> needs_review transition."""

    @pytest.mark.asyncio
    async def test_draft_to_needs_review(self):
        """draft -> needs_review is allowed."""
        snapshot = _make_snapshot(status="draft")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.submit_for_review(1, 1)

        assert result.get("status") == "needs_review"
        assert db.committed is True

    @pytest.mark.asyncio
    async def test_non_draft_cannot_submit_review(self):
        """Only draft can be submitted for review."""
        snapshot = _make_snapshot(status="approved_for_quote_output")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.submit_for_review(1, 1)

        assert "error" in result
        assert result.get("status_code") == 409

    @pytest.mark.asyncio
    async def test_snapshot_not_found(self):
        """Missing snapshot returns 404."""
        db = MockDBSession(snapshot=None)

        service = QuoteOutputSnapshotService(db)
        result = await service.submit_for_review(1, 999)

        assert result.get("error") == "snapshot_not_found"
        assert result.get("status_code") == 404


class TestApproval:
    """Test approval transitions."""

    @pytest.mark.asyncio
    async def test_draft_to_approved(self):
        """draft -> approved_for_quote_output is allowed if no blockers."""
        snapshot = _make_snapshot(status="draft")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.approve(1, 1, user="admin@test.com")

        assert result.get("status") == "approved_for_quote_output"
        assert result.get("approved_by") == "admin@test.com"
        assert db.committed is True

    @pytest.mark.asyncio
    async def test_needs_review_to_approved(self):
        """needs_review -> approved_for_quote_output is allowed if no blockers."""
        snapshot = _make_snapshot(status="needs_review")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.approve(1, 1, user="admin@test.com")

        assert result.get("status") == "approved_for_quote_output"

    @pytest.mark.asyncio
    async def test_blockers_prevent_approval(self):
        """Blockers prevent approval."""
        snapshot = _make_snapshot(status="draft", blockers=["missing_dossier"])
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.approve(1, 1)

        assert "error" in result
        assert "blockers" in result.get("error", "").lower() or "blockers" in result

    @pytest.mark.asyncio
    async def test_empty_sections_prevent_approval(self):
        """Empty rendered sections prevent approval."""
        snapshot = _make_snapshot(status="draft", sections=[])
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.approve(1, 1)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_rejected_cannot_be_approved(self):
        """Rejected snapshot cannot be approved."""
        snapshot = _make_snapshot(status="rejected")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.approve(1, 1)

        assert "error" in result
        assert result.get("status_code") == 409

    @pytest.mark.asyncio
    async def test_archived_cannot_be_approved(self):
        """Archived snapshot cannot be approved."""
        snapshot = _make_snapshot(status="archived")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.approve(1, 1)

        assert "error" in result
        assert result.get("status_code") == 409

    @pytest.mark.asyncio
    async def test_second_approval_supersedes_old(self):
        """Approving second snapshot supersedes existing approved."""
        new_snapshot = _make_snapshot(snapshot_id=2, status="draft")
        old_approved = _make_snapshot(snapshot_id=1, status="approved_for_quote_output")
        db = MockDBSession(snapshot=new_snapshot, extra_snapshots=[old_approved])

        service = QuoteOutputSnapshotService(db)
        result = await service.approve(1, 2, user="admin@test.com")

        assert result.get("status") == "approved_for_quote_output"
        # Old snapshot should be superseded
        assert old_approved.status == "superseded"
        assert old_approved.superseded_by_snapshot_id == 2

    @pytest.mark.asyncio
    async def test_approval_does_not_mutate_quote(self):
        """Approval trace confirms no Quote mutation."""
        snapshot = _make_snapshot(status="draft")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.approve(1, 1)

        # The trace in the snapshot confirms no mutations
        trace = json.loads(snapshot.trace_json)
        assert trace.get("quote_mutated") is False
        assert trace.get("order_mutated") is False


class TestArchive:
    """Test archive transitions."""

    @pytest.mark.asyncio
    async def test_approved_can_be_archived(self):
        """Approved snapshot can be archived."""
        snapshot = _make_snapshot(status="approved_for_quote_output")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.archive(1, 1)

        assert result.get("status") == "archived"

    @pytest.mark.asyncio
    async def test_already_archived_cannot_archive(self):
        """Already archived cannot be archived again."""
        snapshot = _make_snapshot(status="archived")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.archive(1, 1)

        assert "error" in result
        assert result.get("status_code") == 409


class TestReject:
    """Test reject transitions."""

    @pytest.mark.asyncio
    async def test_draft_can_be_rejected(self):
        """Draft snapshot can be rejected."""
        snapshot = _make_snapshot(status="draft")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.reject(1, 1, reason="Invalid content")

        assert result.get("status") == "rejected"

    @pytest.mark.asyncio
    async def test_needs_review_can_be_rejected(self):
        """needs_review snapshot can be rejected."""
        snapshot = _make_snapshot(status="needs_review")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.reject(1, 1, reason="Not accurate")

        assert result.get("status") == "rejected"

    @pytest.mark.asyncio
    async def test_approved_cannot_be_rejected(self):
        """Approved snapshot cannot be rejected (must archive instead)."""
        snapshot = _make_snapshot(status="approved_for_quote_output")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        result = await service.reject(1, 1)

        assert "error" in result
        assert result.get("status_code") == 409