"""Execution task collaboration membership — HELPER authorization rows.

Phase 1: membership intent distinct from sessions (work proof) and
assigned_employee_id (optional principal hint). No PRINCIPAL rows.
"""

from datetime import datetime

from core.database import Base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)


class ExecutionTaskParticipant(Base):
    """One HELPER membership row per (order_id, task_id, employee_id)."""

    __tablename__ = "execution_task_participants"
    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "task_id",
            "employee_id",
            name="uq_execution_task_participant",
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    order_id = Column(Integer, nullable=False, index=True)
    task_id = Column(String(256), nullable=False, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(16), nullable=False, default="helper")
    status = Column(String(16), nullable=False, default="active", index=True)
    joined_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    left_at = Column(DateTime(timezone=True), nullable=True)
    joined_by_employee_id = Column(Integer, nullable=True)
    join_source = Column(String(32), nullable=True)
    source_help_request_id = Column(Integer, nullable=True, index=True)
    execution_plan_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )
