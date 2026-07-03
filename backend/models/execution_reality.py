"""
ExecutionReality model — WorkOS Execution Layer v1.

Canonical invariants (DO NOT VIOLATE):
  - ExecutionReality is an INDEPENDENT write-layer. It never modifies Order
    rows and never modifies ExecutionPlan rows.
  - ExecutionReality stores actual execution facts: a list of task
    observations, each with its own start/end timestamps.
  - Totals are derived from this table alone. No upstream lookups.
  - Materials captured here are observational only — they do NOT update
    inventory or cost engine.

Fields:
  - order_id:    FK-like integer pointing to orders.id
  - order_code:  human-readable code copied from the order at first write
  - tasks_json:  JSON array of observations: [{"task_id", "started_at", "ended_at"}]
  - materials_json: JSON array of consumed materials:
      [{"material_id": str|null, "material_name": str, "quantity": float,
        "unit": str, "task_id": str|null, "added_at": str}]
  - total_actual_time_minutes: sum of (ended_at - started_at) across completed tasks
  - created_at / updated_at: managed by SQLAlchemy
"""

from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String


class ExecutionReality(Base):
    __tablename__ = "execution_reality"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    order_id = Column(Integer, nullable=False, index=True, unique=True)
    order_code = Column(String, nullable=False)
    tasks_json = Column(String, nullable=False, default="[]")
    materials_json = Column(String, nullable=False, default="[]")
    total_actual_time_minutes = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    # BUILD 18 — Invalid Reality Marker fields (all nullable for backward compat)
    is_invalid = Column(Boolean, nullable=True, default=False)
    invalidated_at = Column(DateTime(timezone=True), nullable=True)
    invalidated_by = Column(String, nullable=True)
    invalid_reason = Column(String, nullable=True)
    # Flag set when invalidation happens after stock was already deducted
    stock_reconciliation_required = Column(Boolean, nullable=True, default=False)
    # Restoration fields (simple permission-protected restore)
    restored_at = Column(DateTime(timezone=True), nullable=True)
    restored_by = Column(String, nullable=True)
    restored_reason = Column(String, nullable=True)