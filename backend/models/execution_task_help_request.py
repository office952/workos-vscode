"""Execution task help requests — collaboration need signal (Phase 2).

Broadcast OPEN may be accepted by many helpers; membership stores acceptance.
No singular accepted_by authority. Do not reuse TaskClarificationRequest.
"""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String


class ExecutionTaskHelpRequest(Base):
    """One help-need row; at most one OPEN per (order_id, task_id) via partial unique index."""

    __tablename__ = "execution_task_help_requests"
    __table_args__ = ({"extend_existing": True},)

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    order_id = Column(Integer, nullable=False, index=True)
    task_id = Column(String(256), nullable=False, index=True)
    requested_by_employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    targeted_employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(String(16), nullable=False, default="OPEN", index=True)
    reason = Column(String(512), nullable=True)
    competence_hint = Column(String(128), nullable=True)
    execution_plan_id = Column(Integer, nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )
