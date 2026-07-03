"""CostEngine company-level config — SINGLETON (id=1).

Stores static knobs the CostEngine consumes. Derived aggregates
(e.g. total productive hours, overhead per hour) are NEVER persisted
here — they are computed on read from the live Employees /
RecurringPayments tables to prevent drift.
"""
from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String


class CostEngineConfig(Base):
    __tablename__ = "cost_engine_config"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    moneda_implicita = Column(String, nullable=False, default="RON")
    ore_productive_luna_firma = Column(Float, nullable=True)
    overhead_profile_name = Column(String, nullable=False, default="default")
    metoda_overhead = Column(String, nullable=False, default="pe_ora_productiva")
    cost_ora_manopera_default = Column(Float, nullable=True)
    allow_manual_override = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)