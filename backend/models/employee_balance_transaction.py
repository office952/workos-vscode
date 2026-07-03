"""Internal employee balance ledger — advances, loans, retentions (not fiscal payroll)."""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text


class EmployeeBalanceTransaction(Base):
    __tablename__ = "employee_balance_transactions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_type = Column(String(32), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="RON")
    status = Column(String(32), nullable=False, default="active")
    notes = Column(Text, nullable=True)
    source = Column(String(32), nullable=False, default="manual")
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
