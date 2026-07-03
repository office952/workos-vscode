"""Internal employee attendance events — exceptions to default present schedule."""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text


class EmployeeAttendanceEvent(Base):
    __tablename__ = "employee_attendance_events"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    event_type = Column(String(32), nullable=False)  # absent|leave|sick|partial|overtime|correction
    event_status = Column(String(32), nullable=False, default="confirmed")
    hours_override = Column(Float, nullable=True)
    hours_delta = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    source = Column(String(32), nullable=False, default="manual")
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
