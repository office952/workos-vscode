"""
StockMovement model — BUILD 16: Inventory Operational Loop.

Records every stock mutation as an auditable, immutable event.
Each row represents a single atomic stock change tied to a specific
ExecutionReality material consumption row.

Invariants:
  - A stock movement is NEVER created without updating inventory_materials.stock_current.
  - A stock movement is NEVER created from quote estimates or plan data.
  - A stock movement is NEVER created for free-text material rows (no material_id).
  - Duplicate deductions are prevented via the idempotency_key (unique constraint).
  - movement_type is always 'consumption' in BUILD 16 (extensible later).
"""

from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, UniqueConstraint


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_stock_movements_idempotency"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    material_id = Column(Integer, nullable=False, index=True)
    source_type = Column(String, nullable=False)  # "execution_reality"
    source_id = Column(Integer, nullable=False)  # execution_reality.id
    order_id = Column(Integer, nullable=True)
    task_id = Column(String, nullable=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    movement_type = Column(String, nullable=False)  # "consumption"
    old_stock = Column(Float, nullable=False)
    new_stock = Column(Float, nullable=False)
    performed_by = Column(String, nullable=False)
    performed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    reason = Column(String, nullable=True)
    idempotency_key = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    # Frozen at the actual stock movement. A reservation or planned BOM is not actual cost.
    unit_cost_snapshot = Column(Float, nullable=True)
    currency_snapshot = Column(String, nullable=True)
    valuation_method = Column(String, nullable=True)
    valuation_provenance = Column(String, nullable=True)
    extended_cost_snapshot = Column(Float, nullable=True)
    price_history_id_snapshot = Column(Integer, nullable=True)