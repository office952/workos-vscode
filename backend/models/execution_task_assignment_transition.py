"""Append-only assignment transition history (Phase A).

Current operational assignee remains on ExecutionPlan.tasks_json
operational_tasks[].assigned_employee_id. This table is historical truth only.
No update/delete repository paths are provided.
"""

from __future__ import annotations

from datetime import datetime

from core.database import Base
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)


REASON_NOTE_MAX_LEN = 500

TRANSITION_TYPES = ("ASSIGN", "REASSIGN", "UNASSIGN")

REASON_CODES = (
    "EMPLOYEE_UNAVAILABLE",
    "EMPLOYEE_INACTIVE",
    "ELIGIBILITY_CHANGED",
    "INCORRECT_INITIAL_ASSIGNMENT",
    "MANAGER_CORRECTION",
    "PLANNING_CHANGE",
    "OPERATIONAL_REBALANCE_PRE_START",
    "OTHER",
    "INITIAL_ASSIGNMENT_BACKFILL",
)

SOURCE_LEGACY_EMBEDDED_BACKFILL = "LEGACY_EMBEDDED_BACKFILL"


class ExecutionTaskAssignmentTransition(Base):
    """One immutable row per assignment transition (ASSIGN / REASSIGN / UNASSIGN)."""

    __tablename__ = "execution_task_assignment_transitions"
    __table_args__ = (
        UniqueConstraint(
            "transition_id",
            name="uq_exec_task_assign_transition_id",
        ),
        CheckConstraint(
            "transition_type IN ('ASSIGN', 'REASSIGN', 'UNASSIGN')",
            name="ck_exec_task_assign_transition_type",
        ),
        CheckConstraint(
            "("
            "transition_type = 'UNASSIGN' AND new_employee_id IS NULL"
            ") OR ("
            "transition_type IN ('ASSIGN', 'REASSIGN') AND new_employee_id IS NOT NULL"
            ")",
            name="ck_exec_task_assign_transition_employee_shape",
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    transition_id = Column(String(36), nullable=False, index=True)
    execution_plan_id = Column(
        Integer,
        ForeignKey("execution_plan.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_id = Column(Integer, nullable=False, index=True)
    task_key = Column(String(512), nullable=False, index=True)
    transition_type = Column(String(16), nullable=False)
    previous_employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=True,
    )
    new_employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=True,
    )
    actor_user_id = Column(String(255), nullable=True)
    actor_role = Column(String(50), nullable=True)
    reason_code = Column(String(64), nullable=True)
    reason_note = Column(String(REASON_NOTE_MAX_LEN), nullable=True)
    task_state_at_transition = Column(String(64), nullable=True)
    eligibility_decision_code = Column(String(64), nullable=True)
    eligibility_provenance = Column(String(128), nullable=True)
    request_id = Column(String(64), nullable=True)
    correlation_id = Column(String(64), nullable=True)
    expected_current_employee_id = Column(Integer, nullable=True)
    source = Column(String(64), nullable=True, index=True)
    command_version = Column(String(32), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
