"""ORM model for quote_snapshots_v2 table.

Step 8.2 — Dual Quote Snapshot V2 persistence (CommercialPriceProposal + EstimatedInternalCost).
Does NOT modify quotes, orders, or legacy quote_output_snapshots.
"""

from __future__ import annotations

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, Index, Integer, String, Text, func

ALLOWED_SNAPSHOT_V2_STATUSES = [
    "draft",
    "frozen",
    "superseded",
    "archived",
    "rejected",
]


class QuoteSnapshotV2Record(Base):
    __tablename__ = "quote_snapshots_v2"
    __table_args__ = (
        Index("ix_quote_snapshots_v2_quote_id_version", "quote_id", "version"),
        Index("ix_quote_snapshots_v2_workspace_id_version", "workspace_id", "version"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    snapshot_code = Column(String, nullable=False, unique=True, index=True)
    snapshot_version = Column(String, nullable=False, default="1.0.0")
    version = Column(Integer, nullable=False, default=1)
    quote_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    template_code = Column(String, nullable=False)
    status = Column(String, nullable=False, default="draft", index=True)
    readiness = Column(String, nullable=False)
    frozen_at = Column(DateTime(timezone=True), nullable=True)
    frozen_by = Column(String, nullable=True)
    snapshot_json = Column(Text, nullable=False)
    content_hash = Column(String, nullable=True)
    superseded_by_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
