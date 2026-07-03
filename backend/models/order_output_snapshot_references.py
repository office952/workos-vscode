"""
BUILD 12 — Order Output Snapshot Reference model.

Stores a read-only, historical reference linking an Order to the
approved quote output snapshot candidate that was eligible at acceptance time.

Rules:
  - Read-only after creation (immutable).
  - Does NOT copy live ProductSystem data.
  - Does NOT copy live Output Blocks.
  - Does NOT re-render document text.
  - Points to the saved snapshot from Build 10.
  - Content hash preserved for integrity verification.
  - If the source snapshot is later archived/superseded, this reference remains unchanged.
  - This is NOT the quote_output_snapshot itself — it is a separate historical link.
"""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, Integer, String, Text


class OrderOutputSnapshotReference(Base):
    __tablename__ = "order_output_snapshot_references"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    order_id = Column(Integer, nullable=False, index=True)
    quote_id = Column(Integer, nullable=False, index=True)
    quote_output_snapshot_id = Column(Integer, nullable=False, index=True)
    snapshot_code = Column(String, nullable=False)
    snapshot_status_at_acceptance = Column(String, nullable=False)
    snapshot_version = Column(Integer, nullable=True)
    snapshot_content_hash = Column(String, nullable=True)
    source_template_id = Column(Integer, nullable=True)
    source_template_code = Column(String, nullable=True)
    source_dossier_id = Column(Integer, nullable=True)
    source_dossier_version = Column(Integer, nullable=True)
    source_trace_json = Column(Text, nullable=True)
    governance_status_at_acceptance = Column(String, nullable=False, default="eligible")
    accepted_at = Column(DateTime(timezone=True), default=datetime.now)
    accepted_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    notes = Column(Text, nullable=True)