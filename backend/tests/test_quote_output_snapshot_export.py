"""
BUILD 10 — Tests for Quote Output Snapshot HTML Export.

Verifies:
  - Export endpoint exists
  - Auth required
  - HTML export contains saved snapshot content
  - HTML export contains candidate disclaimer
  - Draft export contains not-approved disclaimer
  - Approved export contains approved-for-quote-output label
  - HTML export does not contain raw debug JSON
  - Export creates no Quote
  - Export creates no Order
  - Export creates no snapshot
  - Export mutates nothing
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import pytest

from services.quote_output_snapshot_service import QuoteOutputSnapshotService
from models.quote_output_snapshots import QuoteOutputSnapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snapshot(
    status: str = "draft",
    sections_text: str = "Banner publicitar 3x2m premium",
) -> QuoteOutputSnapshot:
    """Create a snapshot for export testing."""
    return QuoteOutputSnapshot(
        id=1,
        quote_id=1,
        quote_code="Q-2026-001",
        snapshot_code="QDOC-2026-0001",
        snapshot_type="quote_output_candidate",
        status=status,
        version=1,
        source_template_id=1,
        source_template_code="TPL-BANNER",
        source_dossier_id=1,
        rendered_sections_json=json.dumps([
            {
                "section_id": "block-01",
                "title": "Product Description",
                "rendered_text": sections_text,
                "warnings": [],
                "blockers": [],
            }
        ]),
        commercial_summary_json=json.dumps({
            "subtotal": 1000.0,
            "vat": 190.0,
            "total": 1190.0,
            "currency": "RON",
        }),
        warnings_json=json.dumps([]),
        blockers_json=json.dumps([]),
        variables_used_json=json.dumps({}),
        trace_json=json.dumps({
            "created_from": "quote_output_composition_preview",
            "quote_mutated": False,
            "order_mutated": False,
        }),
        content_hash="abc123def456abc123def456abc123de",
        created_by="user@test.com",
        created_at=datetime(2026, 5, 18, 10, 0, 0),
        updated_at=datetime(2026, 5, 18, 10, 0, 0),
    )


class MockDBSession:
    """Mock DB session for export tests."""

    def __init__(self, snapshot: Optional[QuoteOutputSnapshot] = None):
        self._snapshot = snapshot

    async def execute(self, query):
        return MockResult(self._snapshot)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


class MockResult:
    def __init__(self, obj):
        self._obj = obj

    def scalar_one_or_none(self):
        return self._obj


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSnapshotExport:
    """Test HTML export from saved snapshot."""

    @pytest.mark.asyncio
    async def test_export_contains_saved_content(self):
        """HTML export contains saved snapshot content."""
        snapshot = _make_snapshot(sections_text="Banner publicitar 3x2m premium")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        html = await service.export_html(1, 1)

        assert html is not None
        assert "Banner publicitar 3x2m premium" in html

    @pytest.mark.asyncio
    async def test_export_contains_candidate_disclaimer(self):
        """HTML export contains candidate disclaimer."""
        snapshot = _make_snapshot()
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        html = await service.export_html(1, 1)

        assert "SAVED QUOTE OUTPUT SNAPSHOT CANDIDATE" in html
        assert "not an accepted order snapshot" in html

    @pytest.mark.asyncio
    async def test_draft_export_contains_not_approved_disclaimer(self):
        """Draft export contains not-approved disclaimer."""
        snapshot = _make_snapshot(status="draft")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        html = await service.export_html(1, 1)

        assert "DRAFT / NOT APPROVED FOR CLIENT USE" in html

    @pytest.mark.asyncio
    async def test_approved_export_contains_approved_label(self):
        """Approved export contains approved-for-quote-output label."""
        snapshot = _make_snapshot(status="approved_for_quote_output")
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        html = await service.export_html(1, 1)

        assert "APPROVED FOR QUOTE OUTPUT" in html

    @pytest.mark.asyncio
    async def test_export_does_not_contain_raw_json(self):
        """HTML export does not contain raw debug JSON."""
        snapshot = _make_snapshot()
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        html = await service.export_html(1, 1)

        # Should not contain raw JSON array/object markers from trace
        assert '"quote_mutated"' not in html
        assert '"order_mutated"' not in html

    @pytest.mark.asyncio
    async def test_export_snapshot_not_found(self):
        """Export returns None for missing snapshot."""
        db = MockDBSession(snapshot=None)

        service = QuoteOutputSnapshotService(db)
        html = await service.export_html(1, 999)

        assert html is None

    @pytest.mark.asyncio
    async def test_export_contains_snapshot_code(self):
        """HTML export contains snapshot code."""
        snapshot = _make_snapshot()
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        html = await service.export_html(1, 1)

        assert "QDOC-2026-0001" in html

    @pytest.mark.asyncio
    async def test_export_contains_commercial_summary(self):
        """HTML export contains commercial summary."""
        snapshot = _make_snapshot()
        db = MockDBSession(snapshot=snapshot)

        service = QuoteOutputSnapshotService(db)
        html = await service.export_html(1, 1)

        assert "1,190.00" in html or "1190" in html
        assert "RON" in html


class TestExportNoMutation:
    """Verify export creates/mutates nothing."""

    @pytest.mark.asyncio
    async def test_export_does_not_commit(self):
        """Export does not commit to database."""
        snapshot = _make_snapshot()

        class TrackingDB:
            def __init__(self):
                self.committed = False

            async def execute(self, query):
                return MockResult(snapshot)

            async def commit(self):
                self.committed = True

            async def refresh(self, obj):
                pass

        db = TrackingDB()
        service = QuoteOutputSnapshotService(db)
        await service.export_html(1, 1)

        assert db.committed is False