"""Internal employee payment records — actual paid amounts per tranșă (not fiscal payroll)."""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text


class EmployeePaymentRecord(Base):
    __tablename__ = "employee_payment_records"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    slot = Column(String(2), nullable=False)  # 15 | 30
    amount_paid = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    status = Column(String(32), nullable=False, default="confirmed")
    notes = Column(Text, nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_reason = Column(Text, nullable=True)
    source = Column(String(32), nullable=False, default="manual")
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
