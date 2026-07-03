"""Pending/conflict attendance effects from approved employee requests — no auto-apply."""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint


class AttendanceRequestEffect(Base):
    __tablename__ = "attendance_request_effects"
    __table_args__ = (
        UniqueConstraint("employee_request_id", name="uq_attendance_request_effects_request_id"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    employee_request_id = Column(
        Integer,
        ForeignKey("employee_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(32), nullable=False, index=True)
    effect_type = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="pending", index=True)
    date_start = Column(Date, nullable=True)
    date_end = Column(Date, nullable=True)
    hours = Column(Float, nullable=True)
    generated_by_user_id = Column(String(255), nullable=False)
    generated_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    applied_by_user_id = Column(String(255), nullable=True)
    source = Column(String(32), nullable=False, default="employee_request")
    notes = Column(Text, nullable=True)
    conflict_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
