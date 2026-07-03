"""ORM model for rendered_output_snapshots table.

BUILD 27.08 — canonical rendered OutputBlock snapshot persistence.

This table stores immutable, backend-owned rendered OutputBlock snapshots.
It does not mutate Quote, Order, Inventory, Execution, or ExecutionReality.
Existing quote_output_snapshots remains candidate-only legacy governance storage.
"""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, Integer, String, Text


class RenderedOutputSnapshot(Base):
    __tablename__ = "rendered_output_snapshots"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    snapshot_uid = Column(String, nullable=False, unique=True, index=True)
    context = Column(String, nullable=False)
    document_type = Column(String, nullable=False)
    audience = Column(String, nullable=False)
    snapshot_purpose = Column(String, nullable=False)
    target_type = Column(String, nullable=True)
    target_id = Column(String, nullable=True)
    source_payload_json = Column(Text, nullable=False)
    source_payload_hash = Column(String, nullable=True)
    rendered_blocks_json = Column(Text, nullable=False)
    warnings_json = Column(Text, nullable=True)
    blockers_json = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="created")
    created_by = Column(String, nullable=True)
    trace_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
