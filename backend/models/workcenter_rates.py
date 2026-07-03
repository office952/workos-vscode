"""Workcenter Rates registry — canonical source of truth for per-workcenter hourly rates.

Sprint #20 — Product Registry Foundation.

This table persists the hourly rate (RON/h) for each canonical production
workcenter referenced by hierarchical product templates (Sprint #15 shape).
Today the v2 CostEngine still receives `workcenter_rates` as a runtime dict
injected at the orchestrator boundary; this table is the first step toward
having that dict sourced from the database instead of caller-supplied.

Status contract (enum-in-code, validated at service level):
  - "active"              -> rate_per_hour IS NOT NULL AND > 0
  - "missing_price"       -> rate_per_hour IS NULL, waiting for owner price
  - "needs_owner_input"   -> rate_per_hour IS NULL, owner review required
  - "archived"            -> soft-deleted, hidden from registry consumers

No commercial value is ever invented: unknown rates are persisted as NULL
with a non-active status. This is a Sprint #20 invariant.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from core.database import Base


class Workcenter_rates(Base):
    __tablename__ = "workcenter_rates"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    code = Column(String, nullable=False, unique=True, index=True)
    label = Column(String, nullable=False)
    rate_per_hour = Column(Float, nullable=True)
    rate_per_linear_meter = Column(Float, nullable=True)
    rate_basis = Column(String, nullable=False, default="per_hour")
    currency = Column(String, nullable=False, default="RON")
    status = Column(String, nullable=False, default="missing_price")
    is_active = Column(Boolean, nullable=False, default=False)
    approval_reference = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now, nullable=False
    )