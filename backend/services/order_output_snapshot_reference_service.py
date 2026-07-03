"""
BUILD 12 — Order Output Snapshot Reference Service.

Creates a read-only, historical reference linking an Order to the
approved quote output snapshot candidate that was eligible at acceptance.

Responsibilities:
  - Verifies eligibility via governance service.
  - Resolves approved snapshot candidate.
  - Creates immutable reference for Order.
  - Saves content_hash and trace.

Rules:
  - Does NOT modify the snapshot candidate.
  - Does NOT modify Quote status.
  - Does NOT modify Order status outside existing flow.
  - Does NOT recalculate CostEngine.
  - Does NOT create a new document.
  - Does NOT send email.
  - Does NOT generate final contract.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.order_output_snapshot_references import OrderOutputSnapshotReference
from models.quote_output_snapshots import QuoteOutputSnapshot
from services.quote_output_snapshot_governance_service import (
    ELIGIBILITY_BLOCKED,
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_MISSING,
    ELIGIBILITY_NEEDS_REVIEW,
    QuoteOutputSnapshotGovernanceService,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------

class OrderOutputSnapshotReferenceDTO:
    """DTO for order output snapshot reference responses."""

    def __init__(self, ref: OrderOutputSnapshotReference):
        self.ref = ref

    def to_dict(self) -> Dict[str, Any]:
        r = self.ref
        return {
            "id": r.id,
            "order_id": r.order_id,
            "quote_id": r.quote_id,
            "quote_output_snapshot_id": r.quote_output_snapshot_id,
            "snapshot_code": r.snapshot_code,
            "snapshot_status_at_acceptance": r.snapshot_status_at_acceptance,
            "snapshot_version": r.snapshot_version,
            "snapshot_content_hash": r.snapshot_content_hash,
            "source_template_id": r.source_template_id,
            "source_template_code": r.source_template_code,
            "source_dossier_id": r.source_dossier_id,
            "source_dossier_version": r.source_dossier_version,
            "source_trace_json": _safe_json_load(r.source_trace_json),
            "governance_status_at_acceptance": r.governance_status_at_acceptance,
            "accepted_at": r.accepted_at.isoformat() if r.accepted_at else None,
            "accepted_by": r.accepted_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "notes": r.notes,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class OrderOutputSnapshotReferenceService:
    """
    Manages creation and retrieval of order output snapshot references.

    This service is called during Order creation from Quote to:
      1. Evaluate governance eligibility
      2. Validate explicit snapshot selection (if provided)
      3. Create immutable reference record
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    # ------------------------------------------------------------------
    # Static utility methods (no DB required)
    # ------------------------------------------------------------------

    @staticmethod
    def check_snapshot_eligibility(status: Optional[str]) -> Dict[str, Any]:
        """
        Evaluate eligibility of a snapshot based on its status.

        Returns dict with:
          - status: "eligible" | "warning" | "blocked" | "missing" | "info"
          - detail: human-readable explanation
          - requires_acknowledgement: bool (for warning status)
        """
        if not status:
            return {
                "status": "missing",
                "detail": "No snapshot status provided — snapshot unavailable.",
                "requires_acknowledgement": False,
            }

        if status == "approved_for_quote_output":
            return {
                "status": "eligible",
                "detail": "Snapshot is approved and eligible for order reference.",
                "requires_acknowledgement": False,
            }
        elif status == "rejected":
            return {
                "status": "blocked",
                "detail": "Snapshot was rejected — cannot create order reference.",
                "requires_acknowledgement": False,
            }
        elif status in ("pending_review", "draft"):
            return {
                "status": "warning",
                "detail": f"Snapshot status is '{status}' — requires acknowledgement to proceed.",
                "requires_acknowledgement": True,
            }
        else:
            return {
                "status": "info",
                "detail": f"Unknown snapshot status: '{status}'.",
                "requires_acknowledgement": False,
            }

    @staticmethod
    def select_best_snapshot(snapshots: list) -> Optional[Dict[str, Any]]:
        """
        Select the best snapshot from a list of snapshot dicts.

        Priority:
          1. approved_for_quote_output (latest version)
          2. pending_review (latest version)
          3. draft (latest version)
          4. Never select rejected

        Returns the best snapshot dict or None.
        """
        if not snapshots:
            return None

        # Filter out rejected
        candidates = [s for s in snapshots if s.get("status") != "rejected"]
        if not candidates:
            return None

        # Priority ordering
        priority_map = {
            "approved_for_quote_output": 0,
            "pending_review": 1,
            "draft": 2,
        }

        def sort_key(s):
            status_priority = priority_map.get(s.get("status", ""), 99)
            version = s.get("version", 0) or 0
            return (status_priority, -version)

        candidates.sort(key=sort_key)
        return candidates[0]

    @staticmethod
    def determine_governance_status(snapshot_status: Optional[str]) -> str:
        """
        Determine governance status string based on snapshot status at acceptance.

        Returns: "eligible" | "needs_review" | "blocked" | "missing" | "unknown"
        """
        if not snapshot_status:
            return "missing"
        if snapshot_status == "approved_for_quote_output":
            return "eligible"
        elif snapshot_status in ("pending_review", "draft"):
            return "needs_review"
        elif snapshot_status == "rejected":
            return "blocked"
        else:
            return "unknown"

    async def evaluate_and_create_reference(
        self,
        order_id: int,
        quote_id: int,
        *,
        explicit_snapshot_id: Optional[int] = None,
        acknowledge_missing: bool = False,
        acknowledgement_reason: Optional[str] = None,
        accepted_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate governance eligibility and create reference if eligible.

        Returns dict with:
          - document_snapshot_reference: reference DTO or None
          - document_snapshot_warning: warning dict or None
          - error: error string if blocked

        Trace (all mutation flags = false):
          quote_snapshot_mutated: false
          order_snapshot_rewritten: false
          costengine_called: false
          document_rerendered: false
          email_sent: false
          final_contract_generated: false
        """
        governance = QuoteOutputSnapshotGovernanceService(self.db)
        eligibility = await governance.evaluate_eligibility(quote_id)

        eligibility_status = eligibility.get("eligibility_status", ELIGIBILITY_MISSING)
        approved_snapshot_id = eligibility.get("approved_snapshot_id")

        # --- Handle explicit snapshot_id ---
        if explicit_snapshot_id is not None:
            return await self._handle_explicit_snapshot(
                order_id=order_id,
                quote_id=quote_id,
                explicit_snapshot_id=explicit_snapshot_id,
                eligibility=eligibility,
                accepted_by=accepted_by,
            )

        # --- ELIGIBLE: one approved snapshot, no blockers ---
        if eligibility_status == ELIGIBILITY_ELIGIBLE and approved_snapshot_id:
            snapshot = await self._get_snapshot(quote_id, approved_snapshot_id)
            if not snapshot:
                return self._missing_result(
                    "Approved snapshot not found in database",
                    acknowledged=acknowledge_missing,
                )
            return await self._create_reference(
                order_id=order_id,
                quote_id=quote_id,
                snapshot=snapshot,
                governance_status=eligibility_status,
                accepted_by=accepted_by,
            )

        # --- BLOCKED: approved snapshot has blockers ---
        if eligibility_status == ELIGIBILITY_BLOCKED:
            blockers = eligibility.get("blockers", [])
            return {
                "document_snapshot_reference": None,
                "document_snapshot_warning": None,
                "error": "document_snapshot_blocked",
                "error_detail": {
                    "code": "QUOTE_OUTPUT_SNAPSHOT_BLOCKED",
                    "message": "Approved quote output snapshot has unresolved blockers.",
                    "blockers": blockers,
                    "eligibility_status": eligibility_status,
                },
            }

        # --- NEEDS_REVIEW: conflict or pending review ---
        if eligibility_status == ELIGIBILITY_NEEDS_REVIEW:
            conflict_ids = eligibility.get("conflict_snapshot_ids", [])
            if conflict_ids:
                return {
                    "document_snapshot_reference": None,
                    "document_snapshot_warning": None,
                    "error": "document_snapshot_conflict",
                    "error_detail": {
                        "code": "QUOTE_OUTPUT_SNAPSHOT_CONFLICT",
                        "message": "Multiple approved snapshots detected. Provide explicit quote_output_snapshot_id.",
                        "conflict_snapshot_ids": conflict_ids,
                        "eligibility_status": eligibility_status,
                    },
                }
            # Needs review but no conflict — treat as missing with warning
            if not acknowledge_missing:
                return {
                    "document_snapshot_reference": None,
                    "document_snapshot_warning": None,
                    "error": "document_snapshot_needs_review",
                    "error_detail": {
                        "code": "QUOTE_OUTPUT_SNAPSHOT_NEEDS_REVIEW",
                        "message": "Snapshot requires review before Order integration.",
                        "eligibility_status": eligibility_status,
                    },
                }
            return self._missing_result(
                "Snapshot in needs_review status — acknowledged by user",
                acknowledged=True,
                reason=acknowledgement_reason,
            )

        # --- MISSING: no approved snapshot ---
        if eligibility_status == ELIGIBILITY_MISSING:
            if not acknowledge_missing:
                return self._missing_result(
                    "No approved quote output snapshot exists for this quote",
                    acknowledged=False,
                )
            return self._missing_result(
                "Order created without approved quote output snapshot reference",
                acknowledged=True,
                reason=acknowledgement_reason,
            )

        # Fallback — unknown status
        return self._missing_result(
            f"Unknown eligibility status: {eligibility_status}",
            acknowledged=acknowledge_missing,
            reason=acknowledgement_reason,
        )

    async def get_reference_for_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get the document snapshot reference for an order (if exists)."""
        query = select(OrderOutputSnapshotReference).where(
            OrderOutputSnapshotReference.order_id == order_id
        )
        result = await self.db.execute(query)
        ref = result.scalar_one_or_none()
        if not ref:
            return None
        return OrderOutputSnapshotReferenceDTO(ref).to_dict()

    async def get_by_order_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Alias for get_reference_for_order — used by router."""
        return await self.get_reference_for_order(order_id)

    async def check_quote_document_eligibility(self, quote_id: int) -> Dict[str, Any]:
        """
        Check whether a quote has an eligible document snapshot for order conversion.

        Returns dict with:
          - status: "eligible" | "missing" | "pending_review" | "blocked"
          - snapshot_id: int or None (if eligible)
        """
        governance = QuoteOutputSnapshotGovernanceService(self.db)
        eligibility = await governance.evaluate_eligibility(quote_id)

        eligibility_status = eligibility.get("eligibility_status", ELIGIBILITY_MISSING)
        approved_snapshot_id = eligibility.get("approved_snapshot_id")

        if eligibility_status == ELIGIBILITY_ELIGIBLE and approved_snapshot_id:
            return {"status": "eligible", "snapshot_id": approved_snapshot_id}
        elif eligibility_status == ELIGIBILITY_BLOCKED:
            return {"status": "blocked", "snapshot_id": None}
        elif eligibility_status == ELIGIBILITY_NEEDS_REVIEW:
            return {"status": "pending_review", "snapshot_id": None}
        else:
            return {"status": "missing", "snapshot_id": None}

    # --- Private helpers ---

    async def _handle_explicit_snapshot(
        self,
        order_id: int,
        quote_id: int,
        explicit_snapshot_id: int,
        eligibility: Dict[str, Any],
        accepted_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle explicit snapshot_id selection."""
        # Verify snapshot belongs to quote
        snapshot = await self._get_snapshot(quote_id, explicit_snapshot_id)
        if not snapshot:
            return {
                "document_snapshot_reference": None,
                "document_snapshot_warning": None,
                "error": "document_snapshot_invalid",
                "error_detail": {
                    "code": "QUOTE_OUTPUT_SNAPSHOT_NOT_FOUND",
                    "message": f"Snapshot {explicit_snapshot_id} not found for quote {quote_id}.",
                },
            }

        # Verify status is approved_for_quote_output
        if snapshot.status != "approved_for_quote_output":
            return {
                "document_snapshot_reference": None,
                "document_snapshot_warning": None,
                "error": "document_snapshot_invalid_status",
                "error_detail": {
                    "code": "QUOTE_OUTPUT_SNAPSHOT_INVALID_STATUS",
                    "message": f"Snapshot status is '{snapshot.status}', expected 'approved_for_quote_output'.",
                    "snapshot_status": snapshot.status,
                },
            }

        # Verify no blockers on the snapshot
        blockers = _safe_json_load(snapshot.blockers_json) or []
        if blockers:
            return {
                "document_snapshot_reference": None,
                "document_snapshot_warning": None,
                "error": "document_snapshot_blocked",
                "error_detail": {
                    "code": "QUOTE_OUTPUT_SNAPSHOT_HAS_BLOCKERS",
                    "message": "Selected snapshot has unresolved blockers.",
                    "blockers": blockers,
                },
            }

        # Verify rendered sections exist
        sections = _safe_json_load(snapshot.rendered_sections_json) or []
        if not sections:
            return {
                "document_snapshot_reference": None,
                "document_snapshot_warning": None,
                "error": "document_snapshot_invalid",
                "error_detail": {
                    "code": "QUOTE_OUTPUT_SNAPSHOT_NO_CONTENT",
                    "message": "Selected snapshot has no rendered sections.",
                },
            }

        # All checks passed — create reference
        governance_status = eligibility.get("eligibility_status", "eligible")
        return await self._create_reference(
            order_id=order_id,
            quote_id=quote_id,
            snapshot=snapshot,
            governance_status=governance_status,
            accepted_by=accepted_by,
        )

    async def _create_reference(
        self,
        order_id: int,
        quote_id: int,
        snapshot: QuoteOutputSnapshot,
        governance_status: str,
        accepted_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create the immutable reference record."""
        now = datetime.now(timezone.utc)

        trace = {
            "source": "quote_output_snapshot_candidate",
            "quote_output_snapshot_id": snapshot.id,
            "quote_output_snapshot_status": snapshot.status,
            "governance_status_at_acceptance": governance_status,
            "content_hash": snapshot.content_hash,
            "order_reference_created": True,
            "quote_snapshot_mutated": False,
            "order_snapshot_rewritten": False,
            "costengine_called": False,
            "document_rerendered": False,
            "email_sent": False,
            "final_contract_generated": False,
        }

        ref = OrderOutputSnapshotReference(
            order_id=order_id,
            quote_id=quote_id,
            quote_output_snapshot_id=snapshot.id,
            snapshot_code=snapshot.snapshot_code,
            snapshot_status_at_acceptance=snapshot.status,
            snapshot_version=snapshot.version,
            snapshot_content_hash=snapshot.content_hash,
            source_template_id=snapshot.source_template_id,
            source_template_code=snapshot.source_template_code,
            source_dossier_id=snapshot.source_dossier_id,
            source_dossier_version=snapshot.source_dossier_version,
            source_trace_json=json.dumps(trace),
            governance_status_at_acceptance=governance_status,
            accepted_at=now,
            accepted_by=accepted_by,
            created_at=now,
        )

        self.db.add(ref)
        await self.db.flush()

        return {
            "document_snapshot_reference": OrderOutputSnapshotReferenceDTO(ref).to_dict(),
            "document_snapshot_warning": None,
            "error": None,
        }

    async def _get_snapshot(self, quote_id: int, snapshot_id: int) -> Optional[QuoteOutputSnapshot]:
        """Get snapshot entity by quote_id and snapshot_id."""
        query = select(QuoteOutputSnapshot).where(
            QuoteOutputSnapshot.id == snapshot_id,
            QuoteOutputSnapshot.quote_id == quote_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    def _missing_result(
        message: str,
        acknowledged: bool = False,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a missing/warning result."""
        return {
            "document_snapshot_reference": None,
            "document_snapshot_warning": {
                "code": "QUOTE_OUTPUT_SNAPSHOT_MISSING",
                "message": message,
                "acknowledged": acknowledged,
                "acknowledgement_reason": reason,
            },
            "error": None if acknowledged else "document_snapshot_missing_not_acknowledged",
        }


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