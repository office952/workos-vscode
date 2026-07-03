"""
BUILD 11 — Quote Output Snapshot Governance / Readiness Layer.

Evaluates whether a quote's output snapshot candidates are eligible
for future Order integration. This is a READ-ONLY governance layer.

Produces eligibility status:
  eligible — one approved snapshot, no blockers, source metadata present
  blocked — approved snapshot has blockers or missing source metadata
  needs_review — multiple approved snapshots (conflict) or snapshot in needs_review
  missing — no approved snapshot exists

Rules:
  - No Order snapshot modification
  - No Quote → Order gate modification
  - No Order creation
  - No Quote status change
  - No saving snapshot candidate in Order
  - No transforming approved_for_quote_output into accepted order truth
  - No sending document to client
  - No final contract generation
  - Pure read-only evaluation
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.quote_output_snapshots import QuoteOutputSnapshot

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Eligibility statuses
# ---------------------------------------------------------------------------

ELIGIBILITY_ELIGIBLE = "eligible"
ELIGIBILITY_BLOCKED = "blocked"
ELIGIBILITY_NEEDS_REVIEW = "needs_review"
ELIGIBILITY_MISSING = "missing"

ALLOWED_ELIGIBILITY_STATUSES = [
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_BLOCKED,
    ELIGIBILITY_NEEDS_REVIEW,
    ELIGIBILITY_MISSING,
]


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------

class SnapshotEligibilityDTO:
    """DTO for snapshot governance eligibility response."""

    def __init__(
        self,
        quote_id: int,
        eligibility_status: str,
        reasons: List[str],
        approved_snapshot_id: Optional[int] = None,
        approved_snapshot_code: Optional[str] = None,
        approved_snapshot_version: Optional[int] = None,
        conflict_snapshot_ids: Optional[List[int]] = None,
        blockers: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        source_metadata_present: bool = False,
        source_template_id: Optional[int] = None,
        source_template_code: Optional[str] = None,
        source_dossier_id: Optional[int] = None,
        source_dossier_version: Optional[int] = None,
        source_output_block_versions: Optional[List[Dict[str, Any]]] = None,
        total_snapshots: int = 0,
        snapshots_by_status: Optional[Dict[str, int]] = None,
    ):
        self.quote_id = quote_id
        self.eligibility_status = eligibility_status
        self.reasons = reasons
        self.approved_snapshot_id = approved_snapshot_id
        self.approved_snapshot_code = approved_snapshot_code
        self.approved_snapshot_version = approved_snapshot_version
        self.conflict_snapshot_ids = conflict_snapshot_ids or []
        self.blockers = blockers or []
        self.warnings = warnings or []
        self.source_metadata_present = source_metadata_present
        self.source_template_id = source_template_id
        self.source_template_code = source_template_code
        self.source_dossier_id = source_dossier_id
        self.source_dossier_version = source_dossier_version
        self.source_output_block_versions = source_output_block_versions or []
        self.total_snapshots = total_snapshots
        self.snapshots_by_status = snapshots_by_status or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quote_id": self.quote_id,
            "eligibility_status": self.eligibility_status,
            "reasons": self.reasons,
            "approved_snapshot_id": self.approved_snapshot_id,
            "approved_snapshot_code": self.approved_snapshot_code,
            "approved_snapshot_version": self.approved_snapshot_version,
            "conflict_snapshot_ids": self.conflict_snapshot_ids,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "source_metadata_present": self.source_metadata_present,
            "source_template_id": self.source_template_id,
            "source_template_code": self.source_template_code,
            "source_dossier_id": self.source_dossier_id,
            "source_dossier_version": self.source_dossier_version,
            "source_output_block_versions": self.source_output_block_versions,
            "total_snapshots": self.total_snapshots,
            "snapshots_by_status": self.snapshots_by_status,
            # Governance metadata
            "governance_version": "BUILD_11",
            "read_only": True,
            "no_order_mutation": True,
            "no_quote_status_change": True,
            "no_order_creation": True,
            "no_contract_generation": True,
            "no_send_to_client": True,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class QuoteOutputSnapshotGovernanceService:
    """
    Read-only governance layer for quote output snapshot eligibility.

    Evaluates:
      1. Whether a quote has an approved snapshot candidate
      2. Conflict detection (multiple approved snapshots)
      3. Blocker check on approved snapshot
      4. Status validation (superseded/archived/rejected detection)
      5. Source metadata presence (template/dossier/output block versions)
      6. Produces eligibility status for future Order integration
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_eligibility(self, quote_id: int) -> Dict[str, Any]:
        """
        Evaluate snapshot eligibility for a quote.

        Returns eligibility DTO with status and reasons.
        This is purely read-only — no mutations occur.
        """
        # Fetch all snapshots for this quote
        query = (
            select(QuoteOutputSnapshot)
            .where(QuoteOutputSnapshot.quote_id == quote_id)
            .order_by(QuoteOutputSnapshot.version.desc())
        )
        result = await self.db.execute(query)
        all_snapshots = list(result.scalars().all())

        # If no snapshots exist at all
        if not all_snapshots:
            return SnapshotEligibilityDTO(
                quote_id=quote_id,
                eligibility_status=ELIGIBILITY_MISSING,
                reasons=["No output snapshot candidates exist for this quote"],
                total_snapshots=0,
                snapshots_by_status={},
            ).to_dict()

        # Count by status
        snapshots_by_status: Dict[str, int] = {}
        for s in all_snapshots:
            snapshots_by_status[s.status] = snapshots_by_status.get(s.status, 0) + 1

        total_snapshots = len(all_snapshots)

        # Find approved snapshots
        approved_snapshots = [
            s for s in all_snapshots
            if s.status == "approved_for_quote_output"
        ]

        # --- CASE: No approved snapshot ---
        if not approved_snapshots:
            # Check if any are in needs_review
            needs_review_count = snapshots_by_status.get("needs_review", 0)
            draft_count = snapshots_by_status.get("draft", 0)

            if needs_review_count > 0:
                return SnapshotEligibilityDTO(
                    quote_id=quote_id,
                    eligibility_status=ELIGIBILITY_NEEDS_REVIEW,
                    reasons=[
                        "No approved snapshot exists",
                        f"{needs_review_count} snapshot(s) pending review",
                    ],
                    total_snapshots=total_snapshots,
                    snapshots_by_status=snapshots_by_status,
                ).to_dict()

            if draft_count > 0:
                return SnapshotEligibilityDTO(
                    quote_id=quote_id,
                    eligibility_status=ELIGIBILITY_MISSING,
                    reasons=[
                        "No approved snapshot exists",
                        f"{draft_count} draft snapshot(s) available but not approved",
                    ],
                    total_snapshots=total_snapshots,
                    snapshots_by_status=snapshots_by_status,
                ).to_dict()

            # All snapshots are archived/superseded/rejected
            return SnapshotEligibilityDTO(
                quote_id=quote_id,
                eligibility_status=ELIGIBILITY_MISSING,
                reasons=[
                    "No approved snapshot exists",
                    "All existing snapshots are archived, superseded, or rejected",
                ],
                total_snapshots=total_snapshots,
                snapshots_by_status=snapshots_by_status,
            ).to_dict()

        # --- CASE: Multiple approved snapshots (CONFLICT) ---
        if len(approved_snapshots) > 1:
            conflict_ids = [s.id for s in approved_snapshots]
            return SnapshotEligibilityDTO(
                quote_id=quote_id,
                eligibility_status=ELIGIBILITY_NEEDS_REVIEW,
                reasons=[
                    f"Conflict: {len(approved_snapshots)} approved snapshots detected",
                    "Only one approved snapshot should exist per quote",
                    "Resolve conflict by archiving or superseding extra snapshots",
                ],
                conflict_snapshot_ids=conflict_ids,
                warnings=["Multiple approved snapshots — governance conflict"],
                total_snapshots=total_snapshots,
                snapshots_by_status=snapshots_by_status,
            ).to_dict()

        # --- CASE: Exactly one approved snapshot ---
        approved = approved_snapshots[0]
        reasons: List[str] = []
        warnings: List[str] = []
        blockers: List[str] = []

        # Check blockers on approved snapshot
        snapshot_blockers = _safe_json_load(approved.blockers_json) or []
        if snapshot_blockers:
            blockers.extend(snapshot_blockers)
            reasons.append(f"Approved snapshot has {len(snapshot_blockers)} blocker(s)")

        # Check warnings on approved snapshot
        snapshot_warnings = _safe_json_load(approved.warnings_json) or []
        if snapshot_warnings:
            warnings.extend(snapshot_warnings)

        # Check source metadata presence
        source_metadata_present = self._check_source_metadata(approved)
        if not source_metadata_present:
            missing_sources = self._get_missing_source_details(approved)
            warnings.extend(missing_sources)
            reasons.append("Source metadata incomplete")

        # Check if snapshot has rendered content
        sections = _safe_json_load(approved.rendered_sections_json) or []
        if not sections:
            blockers.append("Approved snapshot has no rendered sections")
            reasons.append("No rendered content in approved snapshot")

        # Check content hash
        if not approved.content_hash:
            warnings.append("Content hash missing — integrity unverifiable")

        # Parse source output block versions
        source_output_block_versions = _safe_json_load(
            approved.source_output_block_versions_json
        ) or []

        # --- Determine final eligibility ---
        if blockers:
            eligibility_status = ELIGIBILITY_BLOCKED
            if not reasons:
                reasons.append("Approved snapshot has unresolved blockers")
        elif not source_metadata_present:
            eligibility_status = ELIGIBILITY_NEEDS_REVIEW
            if not reasons:
                reasons.append("Source metadata needs verification")
        else:
            eligibility_status = ELIGIBILITY_ELIGIBLE
            reasons.append("Approved snapshot is eligible for future Order integration")

        return SnapshotEligibilityDTO(
            quote_id=quote_id,
            eligibility_status=eligibility_status,
            reasons=reasons,
            approved_snapshot_id=approved.id,
            approved_snapshot_code=approved.snapshot_code,
            approved_snapshot_version=approved.version,
            blockers=blockers,
            warnings=warnings,
            source_metadata_present=source_metadata_present,
            source_template_id=approved.source_template_id,
            source_template_code=approved.source_template_code,
            source_dossier_id=approved.source_dossier_id,
            source_dossier_version=approved.source_dossier_version,
            source_output_block_versions=source_output_block_versions,
            total_snapshots=total_snapshots,
            snapshots_by_status=snapshots_by_status,
        ).to_dict()

    # --- Private helpers ---

    def _check_source_metadata(self, snapshot: QuoteOutputSnapshot) -> bool:
        """Check if source template/dossier/output block versions are present."""
        has_template = (
            snapshot.source_template_id is not None
            and snapshot.source_template_code is not None
        )
        # Dossier is optional but if template exists, we consider metadata present
        # Output block versions are optional enhancement
        return has_template

    def _get_missing_source_details(self, snapshot: QuoteOutputSnapshot) -> List[str]:
        """Get details about missing source metadata."""
        missing: List[str] = []
        if snapshot.source_template_id is None:
            missing.append("Source template ID missing")
        if snapshot.source_template_code is None:
            missing.append("Source template code missing")
        if snapshot.source_dossier_id is None:
            missing.append("Source dossier ID not linked")
        if snapshot.source_output_block_versions_json is None:
            missing.append("Output block versions not recorded")
        return missing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_json_load(value: Optional[str]) -> Any:
    """Safely parse JSON string, return None on failure."""
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None