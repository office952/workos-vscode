"""
BUILD 11 — Tests for Quote Output Snapshot Governance Service.

Tests cover:
  1. Missing eligibility (no snapshots)
  2. Missing eligibility (only drafts)
  3. Needs review (pending review snapshots)
  4. Needs review (conflict — multiple approved)
  5. Blocked (approved with blockers)
  6. Blocked (approved with no rendered content)
  7. Eligible (approved, no blockers, source metadata present)
  8. Needs review (approved but missing source metadata)
  9. Status breakdown accuracy
  10. Governance metadata flags
  11. All archived/superseded/rejected → missing
  12. Warnings propagation
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.quote_output_snapshot_governance_service import (
    ELIGIBILITY_BLOCKED,
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_MISSING,
    ELIGIBILITY_NEEDS_REVIEW,
    QuoteOutputSnapshotGovernanceService,
    SnapshotEligibilityDTO,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snapshot(
    id: int = 1,
    quote_id: int = 100,
    status: str = "draft",
    version: int = 1,
    snapshot_code: str = "SNAP-001",
    source_template_id: int | None = None,
    source_template_code: str | None = None,
    source_dossier_id: int | None = None,
    source_dossier_version: int | None = None,
    source_output_block_versions_json: str | None = None,
    rendered_sections_json: str | None = None,
    blockers_json: str | None = None,
    warnings_json: str | None = None,
    content_hash: str | None = None,
):
    """Create a mock snapshot object."""
    snap = MagicMock()
    snap.id = id
    snap.quote_id = quote_id
    snap.status = status
    snap.version = version
    snap.snapshot_code = snapshot_code
    snap.source_template_id = source_template_id
    snap.source_template_code = source_template_code
    snap.source_dossier_id = source_dossier_id
    snap.source_dossier_version = source_dossier_version
    snap.source_output_block_versions_json = source_output_block_versions_json
    snap.rendered_sections_json = rendered_sections_json
    snap.blockers_json = blockers_json
    snap.warnings_json = warnings_json
    snap.content_hash = content_hash
    return snap


async def _mock_db_with_snapshots(snapshots):
    """Create a mock db session that returns given snapshots."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = snapshots
    mock_result.scalars.return_value = mock_scalars
    db.execute = AsyncMock(return_value=mock_result)
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_eligibility_missing_no_snapshots():
    """No snapshots at all → missing."""
    db = await _mock_db_with_snapshots([])
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_MISSING
    assert result["total_snapshots"] == 0
    assert "No output snapshot candidates exist" in result["reasons"][0]


@pytest.mark.asyncio
async def test_eligibility_missing_only_drafts():
    """Only draft snapshots → missing."""
    snapshots = [
        _make_snapshot(id=1, status="draft", version=1),
        _make_snapshot(id=2, status="draft", version=2),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_MISSING
    assert result["total_snapshots"] == 2
    assert "draft" in result["snapshots_by_status"]


@pytest.mark.asyncio
async def test_eligibility_needs_review_pending():
    """Snapshots in needs_review → needs_review."""
    snapshots = [
        _make_snapshot(id=1, status="needs_review", version=1),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_NEEDS_REVIEW
    assert "pending review" in result["reasons"][1]


@pytest.mark.asyncio
async def test_eligibility_needs_review_conflict():
    """Multiple approved snapshots → needs_review (conflict)."""
    snapshots = [
        _make_snapshot(
            id=1, status="approved_for_quote_output", version=1,
            snapshot_code="SNAP-001",
            source_template_id=10, source_template_code="TPL-BNR",
            rendered_sections_json=json.dumps([{"title": "A"}]),
            content_hash="abc123",
        ),
        _make_snapshot(
            id=2, status="approved_for_quote_output", version=2,
            snapshot_code="SNAP-002",
            source_template_id=10, source_template_code="TPL-BNR",
            rendered_sections_json=json.dumps([{"title": "B"}]),
            content_hash="def456",
        ),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_NEEDS_REVIEW
    assert len(result["conflict_snapshot_ids"]) == 2
    assert "Conflict" in result["reasons"][0]


@pytest.mark.asyncio
async def test_eligibility_blocked_with_blockers():
    """Approved snapshot with blockers → blocked."""
    snapshots = [
        _make_snapshot(
            id=1, status="approved_for_quote_output", version=1,
            snapshot_code="SNAP-001",
            source_template_id=10, source_template_code="TPL-BNR",
            rendered_sections_json=json.dumps([{"title": "Section 1"}]),
            blockers_json=json.dumps(["Material not available", "Price expired"]),
            content_hash="abc123",
        ),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_BLOCKED
    assert len(result["blockers"]) == 2
    assert "Material not available" in result["blockers"]


@pytest.mark.asyncio
async def test_eligibility_blocked_no_rendered_content():
    """Approved snapshot with no rendered sections → blocked."""
    snapshots = [
        _make_snapshot(
            id=1, status="approved_for_quote_output", version=1,
            snapshot_code="SNAP-001",
            source_template_id=10, source_template_code="TPL-BNR",
            rendered_sections_json=None,
            content_hash="abc123",
        ),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_BLOCKED
    assert "No rendered content" in " ".join(result["reasons"])


@pytest.mark.asyncio
async def test_eligibility_eligible_full():
    """Approved snapshot with all metadata → eligible."""
    snapshots = [
        _make_snapshot(
            id=1, status="approved_for_quote_output", version=3,
            snapshot_code="SNAP-003",
            source_template_id=10, source_template_code="TPL-BNR",
            source_dossier_id=5, source_dossier_version=2,
            source_output_block_versions_json=json.dumps([
                {"block_id": 1, "version": 1},
                {"block_id": 2, "version": 1},
            ]),
            rendered_sections_json=json.dumps([
                {"title": "Header", "rendered_text": "Banner 3x2m"},
                {"title": "Specificatii", "rendered_text": "Material: vinyl"},
            ]),
            content_hash="sha256_abc123def456",
        ),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_ELIGIBLE
    assert result["approved_snapshot_id"] == 1
    assert result["approved_snapshot_code"] == "SNAP-003"
    assert result["approved_snapshot_version"] == 3
    assert result["source_metadata_present"] is True
    assert result["source_template_id"] == 10
    assert result["source_template_code"] == "TPL-BNR"
    assert result["source_dossier_id"] == 5
    assert len(result["source_output_block_versions"]) == 2


@pytest.mark.asyncio
async def test_eligibility_needs_review_missing_source_metadata():
    """Approved snapshot without source metadata → needs_review."""
    snapshots = [
        _make_snapshot(
            id=1, status="approved_for_quote_output", version=1,
            snapshot_code="SNAP-001",
            source_template_id=None, source_template_code=None,
            rendered_sections_json=json.dumps([{"title": "A"}]),
            content_hash="abc123",
        ),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_NEEDS_REVIEW
    assert result["source_metadata_present"] is False
    assert "Source metadata incomplete" in result["reasons"]


@pytest.mark.asyncio
async def test_eligibility_status_breakdown():
    """Status breakdown counts are accurate."""
    snapshots = [
        _make_snapshot(id=1, status="draft", version=1),
        _make_snapshot(id=2, status="draft", version=2),
        _make_snapshot(id=3, status="needs_review", version=3),
        _make_snapshot(id=4, status="archived", version=4),
        _make_snapshot(
            id=5, status="approved_for_quote_output", version=5,
            snapshot_code="SNAP-005",
            source_template_id=10, source_template_code="TPL-BNR",
            rendered_sections_json=json.dumps([{"title": "X"}]),
            content_hash="hash",
        ),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["snapshots_by_status"]["draft"] == 2
    assert result["snapshots_by_status"]["needs_review"] == 1
    assert result["snapshots_by_status"]["archived"] == 1
    assert result["snapshots_by_status"]["approved_for_quote_output"] == 1
    assert result["total_snapshots"] == 5


@pytest.mark.asyncio
async def test_eligibility_governance_metadata_flags():
    """Governance metadata flags are always present."""
    db = await _mock_db_with_snapshots([])
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["governance_version"] == "BUILD_11"
    assert result["read_only"] is True
    assert result["no_order_mutation"] is True
    assert result["no_quote_status_change"] is True
    assert result["no_order_creation"] is True
    assert result["no_contract_generation"] is True
    assert result["no_send_to_client"] is True


@pytest.mark.asyncio
async def test_eligibility_all_archived_superseded_rejected():
    """All snapshots archived/superseded/rejected → missing."""
    snapshots = [
        _make_snapshot(id=1, status="archived", version=1),
        _make_snapshot(id=2, status="superseded", version=2),
        _make_snapshot(id=3, status="rejected", version=3),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_MISSING
    assert "archived, superseded, or rejected" in result["reasons"][1]


@pytest.mark.asyncio
async def test_eligibility_warnings_propagation():
    """Warnings from approved snapshot are propagated."""
    snapshots = [
        _make_snapshot(
            id=1, status="approved_for_quote_output", version=1,
            snapshot_code="SNAP-001",
            source_template_id=10, source_template_code="TPL-BNR",
            rendered_sections_json=json.dumps([{"title": "A"}]),
            warnings_json=json.dumps(["Price may be outdated", "Check dimensions"]),
            content_hash="abc123",
        ),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_ELIGIBLE
    assert "Price may be outdated" in result["warnings"]
    assert "Check dimensions" in result["warnings"]


@pytest.mark.asyncio
async def test_dto_to_dict_structure():
    """SnapshotEligibilityDTO.to_dict() produces expected keys."""
    dto = SnapshotEligibilityDTO(
        quote_id=100,
        eligibility_status=ELIGIBILITY_ELIGIBLE,
        reasons=["Test reason"],
        approved_snapshot_id=1,
        approved_snapshot_code="SNAP-001",
        approved_snapshot_version=1,
        source_metadata_present=True,
        total_snapshots=1,
        snapshots_by_status={"approved_for_quote_output": 1},
    )
    d = dto.to_dict()

    assert d["quote_id"] == 100
    assert d["eligibility_status"] == ELIGIBILITY_ELIGIBLE
    assert d["governance_version"] == "BUILD_11"
    assert d["read_only"] is True
    assert "reasons" in d
    assert "blockers" in d
    assert "warnings" in d
    assert "conflict_snapshot_ids" in d
    assert "source_output_block_versions" in d


@pytest.mark.asyncio
async def test_eligibility_content_hash_missing_warning():
    """Missing content hash on approved snapshot generates warning."""
    snapshots = [
        _make_snapshot(
            id=1, status="approved_for_quote_output", version=1,
            snapshot_code="SNAP-001",
            source_template_id=10, source_template_code="TPL-BNR",
            rendered_sections_json=json.dumps([{"title": "A"}]),
            content_hash=None,  # Missing
        ),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert "Content hash missing" in " ".join(result["warnings"])


@pytest.mark.asyncio
async def test_eligibility_empty_rendered_sections_list():
    """Empty rendered sections list (not None) → blocked."""
    snapshots = [
        _make_snapshot(
            id=1, status="approved_for_quote_output", version=1,
            snapshot_code="SNAP-001",
            source_template_id=10, source_template_code="TPL-BNR",
            rendered_sections_json=json.dumps([]),  # Empty list
            content_hash="abc123",
        ),
    ]
    db = await _mock_db_with_snapshots(snapshots)
    service = QuoteOutputSnapshotGovernanceService(db)
    result = await service.evaluate_eligibility(100)

    assert result["eligibility_status"] == ELIGIBILITY_BLOCKED
    assert "No rendered content" in " ".join(result["reasons"])