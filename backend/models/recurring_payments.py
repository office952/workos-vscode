"""Recurring payments model — canonical source for overhead & fixed costs.

Canonical rules:
- Only `status='active'` payments enter any calculation.
- `include_in_overhead=True` ⇒ contributes to `monthly_overhead_cost`.
- `include_in_machine_cost=True` + `linked_machine_id` ⇒ may feed a
  per-machine hour cost in a later iteration (NOT mixed with general
  overhead to avoid double counting).
"""
from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text


class RecurringPayments(Base):
    __tablename__ = "recurring_payments"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False, default="alte_costuri")
    # category in: chirie | utilitati | leasing | asigurare | abonament |
    #              servicii | salarii_indirecte | alte_costuri
    amount = Column(Float, nullable=True)                # numeric, see validation
    currency = Column(String, nullable=False, default="RON")
    periodicity = Column(String, nullable=False, default="lunar")  # lunar | anual
    supplier = Column(String, nullable=True)
    due_day = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="active")  # active | inactive

    include_in_overhead = Column(Boolean, nullable=False, default=False)
    include_in_machine_cost = Column(Boolean, nullable=False, default=False)
    linked_machine_id = Column(String, nullable=True)

    observatii = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)