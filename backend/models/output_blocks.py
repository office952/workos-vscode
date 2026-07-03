"""ORM model for output_blocks table.

BUILD 27.06 — OutputBlock Entity/API Contract foundation.

This table stores source-mapped, versioned, approval-gated OutputBlock
definitions. It does not store rendered snapshots and does not mutate
quotes/orders/inventory/execution entities.
"""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, Integer, String, Text


class OutputBlock(Base):
    __tablename__ = "output_blocks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    block_id = Column(String, nullable=False, unique=True, index=True)
    block_type = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    purpose = Column(Text, nullable=True)
    audience = Column(String, nullable=False)
    document_type = Column(String, nullable=False, index=True)

    # JSON payloads persisted as text for compatibility with current model style.
    source_fields = Column(Text, nullable=False)
    variables = Column(Text, nullable=False)
    template_text = Column(Text, nullable=False)
    conditions = Column(Text, nullable=True)

    approval_status = Column(String, nullable=False, default="draft", index=True)
    version = Column(String, nullable=False, default="v1")
    owner_role = Column(String, nullable=True)
    reviewer_role = Column(String, nullable=True)
    snapshot_policy = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)