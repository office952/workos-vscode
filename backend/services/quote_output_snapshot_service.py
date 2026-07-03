"""
BUILD 10 — Quote Output Snapshot Candidate Service.

Creates, lists, retrieves, and manages lifecycle transitions for
quote output snapshot candidates.

A snapshot candidate is a saved, auditable version of a rendered quote output
composition. It is NOT an Order snapshot, NOT a final contract, and does NOT
change the Quote or Order status.

Rules:
  - Creates snapshot from quote_output_composition_preview (Build 9)
  - Lifecycle: draft -> needs_review -> approved_for_quote_output -> archived/superseded/rejected
  - No CostEngine recalculation
  - No Quote/Order mutation
  - No email/send
  - No final contract generation
  - content_hash for integrity verification
  - trace JSON for audit (all mutation flags = false)
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.quote_output_snapshots import QuoteOutputSnapshot, ALLOWED_SNAPSHOT_STATUSES
from services.html_safety import escape_html_text
from services.quote_output_composition_service import QuoteOutputCompositionService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DTO / Contract types
# ---------------------------------------------------------------------------

class QuoteOutputSnapshotCandidateDTO:
    """DTO for quote output snapshot candidate responses."""

    def __init__(self, snapshot: QuoteOutputSnapshot):
        self.snapshot = snapshot

    def to_dict(self) -> Dict[str, Any]:
        s = self.snapshot
        return {
            "snapshot_id": s.id,
            "quote_id": s.quote_id,
            "quote_code": s.quote_code,
            "snapshot_code": s.snapshot_code,
            "snapshot_type": s.snapshot_type,
            "status": s.status,
            "version": s.version,
            "source_template_id": s.source_template_id,
            "source_template_code": s.source_template_code,
            "source_dossier_id": s.source_dossier_id,
            "source_dossier_version": s.source_dossier_version,
            "rendered_sections_json": _safe_json_load(s.rendered_sections_json),
            "commercial_summary_json": _safe_json_load(s.commercial_summary_json),
            "warnings": _safe_json_load(s.warnings_json) or [],
            "blockers": _safe_json_load(s.blockers_json) or [],
            "variables_used": _safe_json_load(s.variables_used_json) or {},
            "trace": _safe_json_load(s.trace_json) or {},
            "content_hash": s.content_hash,
            "created_by": s.created_by,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "approved_by": s.approved_by,
            "approved_at": s.approved_at.isoformat() if s.approved_at else None,
            "archived_at": s.archived_at.isoformat() if s.archived_at else None,
            "superseded_by_snapshot_id": s.superseded_by_snapshot_id,
            "notes": s.notes,
            "persisted": True,
            "not_order_snapshot": True,
            "not_final_contract": True,
            "not_sent_to_client": True,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class QuoteOutputSnapshotService:
    """Manages quote output snapshot candidates — CRUD + lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # --- CREATE ---

    async def create_snapshot(
        self,
        quote_id: int,
        *,
        notes: Optional[str] = None,
        initial_status: str = "draft",
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a snapshot candidate from the quote's composition preview.

        Does NOT mutate Quote, Order, ProductTemplate, BlueprintDossier, Inventory.
        Does NOT call CostEngine formulas.
        Does NOT create ExecutionTask.
        """
        # Validate initial_status
        if initial_status not in ("draft", "needs_review"):
            initial_status = "draft"

        # Get composition preview (read-only)
        composition_service = QuoteOutputCompositionService(self.db)
        composition_result = await composition_service.compose_preview(quote_id)
        composition = composition_result.to_dict()

        # Check if quote exists
        if "quote_not_found" in composition.get("blockers", []):
            return {"error": "quote_not_found", "status_code": 404}

        # If blockers exist, force draft or needs_review (never direct approval)
        blockers = composition.get("blockers", [])
        if blockers and initial_status not in ("draft", "needs_review"):
            initial_status = "needs_review"

        # Extract source metadata
        template_link = composition.get("template_link", {})
        source_template_id = template_link.get("template_id")
        source_template_code = template_link.get("template_code")
        source_dossier_id = template_link.get("dossier_id")

        # Generate snapshot code
        snapshot_code = await self._generate_snapshot_code(quote_id)

        # Get version (next version for this quote)
        version = await self._get_next_version(quote_id)

        # Build content for hash
        sections = composition.get("sections", [])
        commercial_summary = composition.get("commercial_summary", {})
        warnings = composition.get("warnings", [])

        content_for_hash = json.dumps({
            "sections": sections,
            "commercial_summary": commercial_summary,
            "warnings": warnings,
            "blockers": blockers,
        }, sort_keys=True)
        content_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()[:32]

        # Build trace (all mutation flags = false)
        trace = {
            "created_from": "quote_output_composition_preview",
            "quote_mutated": False,
            "order_mutated": False,
            "order_snapshot_created": False,
            "costengine_formula_changed": False,
            "costengine_called": False,
            "product_template_mutated": False,
            "blueprint_dossier_mutated": False,
            "inventory_mutated": False,
            "execution_task_created": False,
            "not_final_contract": True,
            "not_sent_to_client": True,
        }

        # Create snapshot entity
        snapshot = QuoteOutputSnapshot(
            quote_id=quote_id,
            quote_code=composition.get("quote_code", ""),
            snapshot_code=snapshot_code,
            snapshot_type="quote_output_candidate",
            status=initial_status,
            version=version,
            source_template_id=source_template_id,
            source_template_code=source_template_code,
            source_dossier_id=source_dossier_id,
            source_dossier_version=None,
            source_output_block_versions_json=None,
            rendered_sections_json=json.dumps(sections),
            commercial_summary_json=json.dumps(commercial_summary),
            warnings_json=json.dumps(warnings),
            blockers_json=json.dumps(blockers),
            variables_used_json=json.dumps({}),
            trace_json=json.dumps(trace),
            content_hash=content_hash,
            created_by=created_by,
            notes=notes,
        )

        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)

        return QuoteOutputSnapshotCandidateDTO(snapshot).to_dict()

    # --- LIST ---

    async def list_snapshots(self, quote_id: int) -> List[Dict[str, Any]]:
        """List all snapshot candidates for a quote."""
        query = (
            select(QuoteOutputSnapshot)
            .where(QuoteOutputSnapshot.quote_id == quote_id)
            .order_by(QuoteOutputSnapshot.version.desc())
        )
        result = await self.db.execute(query)
        snapshots = result.scalars().all()
        return [QuoteOutputSnapshotCandidateDTO(s).to_dict() for s in snapshots]

    # --- GET ---

    async def get_snapshot(self, quote_id: int, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """Get a single snapshot candidate."""
        query = select(QuoteOutputSnapshot).where(
            QuoteOutputSnapshot.id == snapshot_id,
            QuoteOutputSnapshot.quote_id == quote_id,
        )
        result = await self.db.execute(query)
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            return None
        return QuoteOutputSnapshotCandidateDTO(snapshot).to_dict()

    # --- LIFECYCLE TRANSITIONS ---

    async def submit_for_review(
        self, quote_id: int, snapshot_id: int, *, user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transition: draft -> needs_review."""
        snapshot = await self._get_snapshot_entity(quote_id, snapshot_id)
        if not snapshot:
            return {"error": "snapshot_not_found", "status_code": 404}

        if snapshot.status != "draft":
            return {"error": f"Cannot submit for review: current status is '{snapshot.status}', expected 'draft'", "status_code": 409}

        snapshot.status = "needs_review"
        snapshot.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(snapshot)
        return QuoteOutputSnapshotCandidateDTO(snapshot).to_dict()

    async def approve(
        self, quote_id: int, snapshot_id: int, *, user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transition: draft/needs_review -> approved_for_quote_output.

        Approval does NOT:
          - Send anything to client
          - Change Quote status
          - Create Order
          - Modify Order snapshot
          - Call CostEngine

        If blockers exist, approval is rejected.
        If another approved snapshot exists, it is superseded.
        """
        snapshot = await self._get_snapshot_entity(quote_id, snapshot_id)
        if not snapshot:
            return {"error": "snapshot_not_found", "status_code": 404}

        if snapshot.status not in ("draft", "needs_review"):
            return {"error": f"Cannot approve: current status is '{snapshot.status}'", "status_code": 409}

        # Check blockers
        blockers = _safe_json_load(snapshot.blockers_json) or []
        if blockers:
            return {"error": "Cannot approve snapshot with blockers", "blockers": blockers, "status_code": 409}

        # Check rendered sections exist
        sections = _safe_json_load(snapshot.rendered_sections_json) or []
        if not sections:
            return {"error": "Cannot approve snapshot without rendered sections", "status_code": 409}

        # Supersede any existing approved snapshot for this quote
        await self._supersede_existing_approved(quote_id, snapshot_id)

        snapshot.status = "approved_for_quote_output"
        snapshot.approved_by = user
        snapshot.approved_at = datetime.now()
        snapshot.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(snapshot)
        return QuoteOutputSnapshotCandidateDTO(snapshot).to_dict()

    async def archive(
        self, quote_id: int, snapshot_id: int, *, user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transition: draft/needs_review/approved_for_quote_output -> archived."""
        snapshot = await self._get_snapshot_entity(quote_id, snapshot_id)
        if not snapshot:
            return {"error": "snapshot_not_found", "status_code": 404}

        if snapshot.status in ("archived", "superseded"):
            return {"error": f"Cannot archive: current status is '{snapshot.status}'", "status_code": 409}

        snapshot.status = "archived"
        snapshot.archived_at = datetime.now()
        snapshot.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(snapshot)
        return QuoteOutputSnapshotCandidateDTO(snapshot).to_dict()

    async def reject(
        self, quote_id: int, snapshot_id: int, *, user: Optional[str] = None, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transition: draft/needs_review -> rejected."""
        snapshot = await self._get_snapshot_entity(quote_id, snapshot_id)
        if not snapshot:
            return {"error": "snapshot_not_found", "status_code": 404}

        if snapshot.status not in ("draft", "needs_review"):
            return {"error": f"Cannot reject: current status is '{snapshot.status}'", "status_code": 409}

        snapshot.status = "rejected"
        if reason:
            existing_notes = snapshot.notes or ""
            snapshot.notes = f"{existing_notes}\nRejected: {reason}".strip()
        snapshot.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(snapshot)
        return QuoteOutputSnapshotCandidateDTO(snapshot).to_dict()

    async def supersede(
        self, quote_id: int, snapshot_id: int, *, new_snapshot_id: int, user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Explicitly supersede a snapshot with a newer one."""
        snapshot = await self._get_snapshot_entity(quote_id, snapshot_id)
        if not snapshot:
            return {"error": "snapshot_not_found", "status_code": 404}

        if snapshot.status == "superseded":
            return {"error": "Snapshot already superseded", "status_code": 409}

        snapshot.status = "superseded"
        snapshot.superseded_by_snapshot_id = new_snapshot_id
        snapshot.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(snapshot)
        return QuoteOutputSnapshotCandidateDTO(snapshot).to_dict()

    # --- EXPORT ---

    async def export_html(self, quote_id: int, snapshot_id: int) -> Optional[str]:
        """Export snapshot as HTML with appropriate disclaimers.

        Exports from SAVED snapshot content, not from live preview.
        Does NOT create Quote, Order, or any entity.
        """
        snapshot = await self._get_snapshot_entity(quote_id, snapshot_id)
        if not snapshot:
            return None

        e = escape_html_text

        sections = _safe_json_load(snapshot.rendered_sections_json) or []
        commercial_summary = _safe_json_load(snapshot.commercial_summary_json) or {}
        warnings = _safe_json_load(snapshot.warnings_json) or []
        blockers = _safe_json_load(snapshot.blockers_json) or []
        trace = _safe_json_load(snapshot.trace_json) or {}

        # Determine disclaimer based on status
        if snapshot.status == "approved_for_quote_output":
            status_label = "APPROVED FOR QUOTE OUTPUT"
            disclaimer_color = "#059669"
        else:
            status_label = "DRAFT / NOT APPROVED FOR CLIENT USE"
            disclaimer_color = "#d97706"

        # Build sections HTML
        sections_html = ""
        for section in sections:
            section_warnings = section.get("warnings", [])
            section_blockers = section.get("blockers", [])
            warn_html = ""
            if section_warnings:
                warn_items = "".join(f"<li style='color:#d97706;'>{e(w)}</li>" for w in section_warnings)
                warn_html = f"<ul style='margin:4px 0 0 16px;font-size:12px;'>{warn_items}</ul>"
            if section_blockers:
                block_items = "".join(f"<li style='color:#dc2626;'>{e(b)}</li>" for b in section_blockers)
                warn_html += f"<ul style='margin:4px 0 0 16px;font-size:12px;'>{block_items}</ul>"

            sections_html += f"""
            <div style="margin-bottom:16px;padding:12px 16px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;">
                <h3 style="margin:0 0 8px 0;font-size:14px;color:#1e40af;">{e(section.get('title', 'Section'))}</h3>
                <p style="margin:0;font-size:13px;color:#374151;white-space:pre-wrap;">{e(section.get('rendered_text', ''))}</p>
                {warn_html}
            </div>"""

        # Issues section
        issues_html = ""
        if warnings or blockers:
            items = ""
            for w in warnings:
                items += f"<li style='color:#d97706;'>⚠️ {e(w)}</li>"
            for b in blockers:
                items += f"<li style='color:#dc2626;'>🚫 {e(b)}</li>"
            issues_html = f"""
            <div style="margin-top:16px;padding:12px 16px;background:#fef2f2;border:1px solid #fca5a5;border-radius:6px;">
                <strong>Warnings / Blockers:</strong>
                <ul style="margin:8px 0 0 16px;">{items}</ul>
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quote Output Snapshot — {e(snapshot.snapshot_code)}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 32px;
            color: #1f2937;
            line-height: 1.5;
        }}
        .disclaimer {{
            background: #fef3c7;
            border: 2px solid {disclaimer_color};
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 24px;
            text-align: center;
            font-weight: 700;
            color: #92400e;
        }}
        .candidate-label {{
            background: #dbeafe;
            border: 1px solid #93c5fd;
            border-radius: 6px;
            padding: 10px 16px;
            margin-bottom: 16px;
            text-align: center;
            font-size: 13px;
            color: #1e40af;
        }}
        .header {{
            border-bottom: 3px solid #2563eb;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .header h1 {{
            font-size: 20px;
            color: #1e40af;
            margin: 0;
        }}
        .meta {{
            font-size: 13px;
            color: #6b7280;
            margin-top: 8px;
        }}
        .commercial {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 6px;
            padding: 12px 16px;
            margin-top: 16px;
        }}
        .commercial h3 {{
            margin: 0 0 8px 0;
            font-size: 14px;
            color: #1e40af;
        }}
    </style>
</head>
<body>
    <div class="disclaimer">
        SAVED QUOTE OUTPUT SNAPSHOT CANDIDATE — not an accepted order snapshot
    </div>

    <div class="candidate-label">
        Status: {status_label} | Snapshot: {e(snapshot.snapshot_code)} | Version: {e(snapshot.version)}
    </div>

    <div class="header">
        <h1>Quote Output Snapshot</h1>
        <div class="meta">
            <p><strong>Quote:</strong> {e(snapshot.quote_code or 'N/A')}</p>
            <p><strong>Template:</strong> {e(snapshot.source_template_code or 'N/A')}</p>
            <p><strong>Content Hash:</strong> {e(snapshot.content_hash or 'N/A')}</p>
            <p><strong>Created:</strong> {e(snapshot.created_at.isoformat() if snapshot.created_at else 'N/A')}</p>
            {f"<p><strong>Approved:</strong> {e(snapshot.approved_at.isoformat())}</p>" if snapshot.approved_at else ""}
        </div>
    </div>

    <h2 style="font-size:16px;color:#1e40af;border-bottom:1px solid #dbeafe;padding-bottom:6px;">Rendered Sections</h2>
    {sections_html if sections_html else '<p style="color:#6b7280;font-style:italic;">No rendered sections.</p>'}

    <div class="commercial">
        <h3>Commercial Summary</h3>
        <p style="margin:4px 0;font-size:13px;">Subtotal: {e(f"{commercial_summary.get('subtotal', 0):,.2f}")} {e(commercial_summary.get('currency', 'RON'))}</p>
        <p style="margin:4px 0;font-size:13px;">TVA: {e(f"{commercial_summary.get('vat', 0):,.2f}")} {e(commercial_summary.get('currency', 'RON'))}</p>
        <p style="margin:4px 0;font-size:13px;font-weight:700;">Total: {e(f"{commercial_summary.get('total', 0):,.2f}")} {e(commercial_summary.get('currency', 'RON'))}</p>
    </div>

    {issues_html}

    <div style="margin-top:32px;padding-top:12px;border-top:1px solid #e5e7eb;font-size:11px;color:#9ca3af;text-align:center;">
        SAVED QUOTE OUTPUT SNAPSHOT CANDIDATE — Not a final document. Not sent to client. Not an order snapshot.
    </div>
</body>
</html>"""
        return html

    # --- PRIVATE HELPERS ---

    async def _get_snapshot_entity(self, quote_id: int, snapshot_id: int) -> Optional[QuoteOutputSnapshot]:
        """Get raw snapshot entity."""
        query = select(QuoteOutputSnapshot).where(
            QuoteOutputSnapshot.id == snapshot_id,
            QuoteOutputSnapshot.quote_id == quote_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _generate_snapshot_code(self, quote_id: int) -> str:
        """Generate unique snapshot code: QDOC-YYYY-NNNN."""
        year = datetime.now().year
        query = select(func.count(QuoteOutputSnapshot.id))
        result = await self.db.execute(query)
        count = result.scalar() or 0
        return f"QDOC-{year}-{count + 1:04d}"

    async def _get_next_version(self, quote_id: int) -> int:
        """Get next version number for snapshots of this quote."""
        query = select(func.max(QuoteOutputSnapshot.version)).where(
            QuoteOutputSnapshot.quote_id == quote_id
        )
        result = await self.db.execute(query)
        max_version = result.scalar() or 0
        return max_version + 1

    async def _supersede_existing_approved(self, quote_id: int, new_snapshot_id: int) -> None:
        """Supersede any existing approved snapshot for this quote."""
        query = select(QuoteOutputSnapshot).where(
            QuoteOutputSnapshot.quote_id == quote_id,
            QuoteOutputSnapshot.status == "approved_for_quote_output",
            QuoteOutputSnapshot.id != new_snapshot_id,
        )
        result = await self.db.execute(query)
        existing_approved = result.scalars().all()

        for old_snapshot in existing_approved:
            old_snapshot.status = "superseded"
            old_snapshot.superseded_by_snapshot_id = new_snapshot_id
            old_snapshot.updated_at = datetime.now()


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