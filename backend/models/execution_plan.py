"""
ExecutionPlan model — WorkOS Execution Layer v1.

Canonical invariants (DO NOT VIOLATE):
  - ExecutionPlan is generated EXCLUSIVELY from an OrderSnapshot that was
    already persisted on the `orders` table (column `snapshot_line_items`).
  - ExecutionPlan NEVER reads ProductTemplate, MaterialRates, CostEngine,
    QuoteOrchestrator, ProductSystemService at runtime.
  - ExecutionPlan is the "planned" truth. It is write-once from the order
    snapshot. Further revisions (if any) must be separate rows; mutation of
    an existing row is NOT a design goal of v1.

Fields:
  - order_id:           FK-like integer pointing to orders.id
  - order_code:         human-readable code copied from the order at creation
  - snapshot_version:   integer copied verbatim from orders.snapshot_version
  - tasks_json:         JSON array of task dicts (see ExecutionPlanService)
  - total_estimated_time_minutes: sum of task estimates, computed at generation
  - created_at / updated_at: managed by SQLAlchemy
"""

from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String


class ExecutionPlan(Base):
    __tablename__ = "execution_plan"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    order_id = Column(Integer, nullable=False, index=True)
    order_code = Column(String, nullable=False)
    snapshot_version = Column(Integer, nullable=False)
    tasks_json = Column(String, nullable=False)
    total_estimated_time_minutes = Column(Float, nullable=False)
    prepared_by_user_id = Column(String(255), nullable=True, index=True)
    plan_source = Column(String, nullable=True, index=True)
    source_quote_snapshot_v2_id = Column(
        Integer,
        ForeignKey("quote_snapshots_v2.id"),
        nullable=True,
        index=True,
    )
    source_snapshot_code = Column(String, nullable=True)
    source_content_hash = Column(String, nullable=True)
    source_order_snapshot_version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)