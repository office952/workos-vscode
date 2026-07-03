"""ORM model for quote_output_snapshots table.

BUILD 10 — Quote Output Snapshot Candidate + Approval Foundation.

This table stores saved, auditable versions of rendered quote output compositions.
Each snapshot is linked to a quote via quote_id.

This is NOT an Order snapshot.
This is NOT a final contract.
This does NOT change Quote status.
This does NOT create Order.
This does NOT send anything to the client.

Statuses:
  draft — saved internally, not final
  needs_review — requires verification
  approved_for_quote_output — approved for quote preview/export (NOT Order snapshot)
  archived — kept historically, not actively used
  superseded — replaced by newer snapshot
  rejected — invalid / rejected
"""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, Integer, String, Text


ALLOWED_SNAPSHOT_STATUSES = [
    "draft",
    "needs_review",
    "approved_for_quote_output",
    "archived",
    "superseded",
    "rejected",
]


class QuoteOutputSnapshot(Base):
    __tablename__ = "quote_output_snapshots"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    quote_id = Column(Integer, nullable=False, index=True)
    quote_code = Column(String, nullable=True)
    snapshot_code = Column(String, nullable=False, unique=True, index=True)
    snapshot_type = Column(String, nullable=False, default="quote_output_candidate")
    status = Column(String, nullable=False, default="draft")
    version = Column(Integer, nullable=False, default=1)

    # --- Source metadata ---
    source_template_id = Column(Integer, nullable=True)
    source_template_code = Column(String, nullable=True)
    source_dossier_id = Column(Integer, nullable=True)
    source_dossier_version = Column(Integer, nullable=True)
    source_output_block_versions_json = Column(Text, nullable=True)

    # --- Content ---
    rendered_sections_json = Column(Text, nullable=True)
    commercial_summary_json = Column(Text, nullable=True)
    warnings_json = Column(Text, nullable=True)
    blockers_json = Column(Text, nullable=True)
    variables_used_json = Column(Text, nullable=True)
    trace_json = Column(Text, nullable=True)
    content_hash = Column(String, nullable=True)

    # --- Ownership / review ---
    created_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    superseded_by_snapshot_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    # --- Timestamps ---
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)