"""Production task clarification requests — employee-initiated, not HR employee_requests."""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text


class TaskClarificationRequest(Base):
    __tablename__ = "task_clarification_requests"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    order_id = Column(Integer, nullable=False, index=True)
    task_id = Column(String(64), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="open", index=True)
    target_user_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id = Column(String(255), nullable=True)
