"""Employee self-service requests — not attendance/payment side effects."""

from datetime import date, datetime

from core.database import Base
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text


class EmployeeRequest(Base):
    __tablename__ = "employee_requests"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(32), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="submitted", index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(8), nullable=True, default="RON")
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id = Column(String(255), nullable=True)
    review_note = Column(Text, nullable=True)
