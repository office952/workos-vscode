"""
BUILD 10 — Tests for Quote Output Snapshot Schema.

Verifies:
  - Table model exists
  - Required columns exist
  - Status defaults are valid
  - quote_id index exists (via model definition)
  - content_hash column exists
  - Model does not reference quotes FK directly (soft ref pattern)
"""

from __future__ import annotations

import pytest

from models.quote_output_snapshots import QuoteOutputSnapshot, ALLOWED_SNAPSHOT_STATUSES


class TestSnapshotSchema:
    """Test schema definition."""

    def test_table_name(self):
        """Table name is quote_output_snapshots."""
        assert QuoteOutputSnapshot.__tablename__ == "quote_output_snapshots"

    def test_required_columns_exist(self):
        """All required columns are defined."""
        columns = {c.name for c in QuoteOutputSnapshot.__table__.columns}
        required = {
            "id", "quote_id", "quote_code", "snapshot_code", "snapshot_type",
            "status", "version", "source_template_id", "source_template_code",
            "source_dossier_id", "source_dossier_version",
            "source_output_block_versions_json",
            "rendered_sections_json", "commercial_summary_json",
            "warnings_json", "blockers_json", "variables_used_json",
            "trace_json", "content_hash",
            "created_by", "approved_by", "approved_at", "archived_at",
            "superseded_by_snapshot_id", "notes",
            "created_at", "updated_at",
        }
        for col in required:
            assert col in columns, f"Missing column: {col}"

    def test_status_default(self):
        """Status default is 'draft'."""
        col = QuoteOutputSnapshot.__table__.c.status
        assert col.default.arg == "draft"

    def test_snapshot_type_default(self):
        """snapshot_type default is 'quote_output_candidate'."""
        col = QuoteOutputSnapshot.__table__.c.snapshot_type
        assert col.default.arg == "quote_output_candidate"

    def test_version_default(self):
        """version default is 1."""
        col = QuoteOutputSnapshot.__table__.c.version
        assert col.default.arg == 1

    def test_quote_id_indexed(self):
        """quote_id column is indexed."""
        col = QuoteOutputSnapshot.__table__.c.quote_id
        assert col.index is True

    def test_snapshot_code_unique(self):
        """snapshot_code is unique."""
        col = QuoteOutputSnapshot.__table__.c.snapshot_code
        assert col.unique is True

    def test_content_hash_exists(self):
        """content_hash column exists."""
        columns = {c.name for c in QuoteOutputSnapshot.__table__.columns}
        assert "content_hash" in columns

    def test_allowed_statuses_complete(self):
        """All 6 statuses are defined."""
        expected = {"draft", "needs_review", "approved_for_quote_output", "archived", "superseded", "rejected"}
        assert set(ALLOWED_SNAPSHOT_STATUSES) == expected

    def test_no_fk_to_quotes(self):
        """No FK constraint to quotes table (soft ref pattern)."""
        col = QuoteOutputSnapshot.__table__.c.quote_id
        assert len(col.foreign_keys) == 0