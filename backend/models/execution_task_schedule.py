"""Execution task schedules + append-only schedule transitions (Resource State).

Open-authoring uniqueness (partial unique index): at most one row per
(execution_plan_id, task_key) with status IN ('DRAFT','PLANNED','CONFIRMED').
This is authoring uniqueness — distinct from resource-guard blocking, where
only PLANNED/CONFIRMED are blocking when the domain is configured.
"""

from __future__ import annotations

from datetime import datetime

from core.database import Base
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)

REASON_NOTE_MAX_LEN = 500

SCHEDULE_STATUSES = ("DRAFT", "PLANNED", "CONFIRMED", "CANCELLED", "SUPERSEDED")
SCHEDULE_OPEN_STATUSES = ("DRAFT", "PLANNED", "CONFIRMED")


class ExecutionTaskSchedule(Base):
    __tablename__ = "execution_task_schedules"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_exec_task_schedule_idempotency",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'PLANNED', 'CONFIRMED', 'CANCELLED', 'SUPERSEDED')",
            name="ck_exec_task_schedule_status",
        ),
        CheckConstraint("version >= 1", name="ck_exec_task_schedule_version"),
        CheckConstraint(
            "length(trim(task_key)) > 0",
            name="ck_exec_task_schedule_task_key_nonblank",
        ),
        CheckConstraint(
            "scheduled_end > scheduled_start",
            name="ck_exec_task_schedule_end_after_start",
        ),
        CheckConstraint(
            "superseded_by_id IS NULL OR superseded_by_id != id",
            name="ck_exec_task_schedule_no_self_supersede",
        ),
        CheckConstraint(
            "("
            "status != 'CANCELLED'"
            ") OR ("
            "status = 'CANCELLED' AND cancelled_at IS NOT NULL"
            ")",
            name="ck_exec_task_schedule_cancel_timestamp",
        ),
        Index("ix_exec_task_schedule_plan_task", "execution_plan_id", "task_key"),
        Index("ix_exec_task_schedule_status", "status"),
        Index(
            "ix_exec_task_schedule_window",
            "scheduled_start",
            "scheduled_end",
        ),
        Index(
            "uq_exec_task_schedule_open_per_task",
            "execution_plan_id",
            "task_key",
            unique=True,
            sqlite_where=text(
                "status IN ('DRAFT', 'PLANNED', 'CONFIRMED')"
            ),
            postgresql_where=text(
                "status IN ('DRAFT', 'PLANNED', 'CONFIRMED')"
            ),
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    execution_plan_id = Column(
        Integer,
        ForeignKey("execution_plan.id", ondelete="RESTRICT"),
        nullable=False,
    )
    order_id = Column(Integer, nullable=False)
    task_key = Column(String(512), nullable=False)
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False)
    workcenter_code = Column(String(128), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by = Column(String(255), nullable=True)
    superseded_by_id = Column(
        Integer,
        ForeignKey("execution_task_schedules.id", ondelete="RESTRICT"),
        nullable=True,
    )
    idempotency_key = Column(String(36), nullable=False)


class ExecutionTaskScheduleTransition(Base):
    """Append-only schedule lifecycle history (insert/read only)."""

    __tablename__ = "execution_task_schedule_transitions"
    __table_args__ = (
        UniqueConstraint(
            "transition_id",
            name="uq_exec_task_schedule_tr_transition_id",
        ),
        UniqueConstraint(
            "idempotency_key",
            name="uq_exec_task_schedule_tr_idempotency",
        ),
        Index("ix_exec_task_schedule_tr_schedule_id", "schedule_id"),
        Index(
            "ix_exec_task_schedule_tr_plan_task_created",
            "execution_plan_id",
            "task_key",
            "created_at",
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    transition_id = Column(String(36), nullable=False)
    schedule_id = Column(
        Integer,
        ForeignKey("execution_task_schedules.id", ondelete="RESTRICT"),
        nullable=False,
    )
    execution_plan_id = Column(
        Integer,
        ForeignKey("execution_plan.id", ondelete="RESTRICT"),
        nullable=False,
    )
    task_key = Column(String(512), nullable=False)
    operation = Column(String(64), nullable=False)
    previous_status = Column(String(16), nullable=True)
    new_status = Column(String(16), nullable=False)
    previous_start = Column(DateTime(timezone=True), nullable=True)
    previous_end = Column(DateTime(timezone=True), nullable=True)
    new_start = Column(DateTime(timezone=True), nullable=True)
    new_end = Column(DateTime(timezone=True), nullable=True)
    previous_version = Column(Integer, nullable=True)
    new_version = Column(Integer, nullable=False)
    reason_code = Column(String(64), nullable=True)
    reason_note = Column(String(REASON_NOTE_MAX_LEN), nullable=True)
    actor_user_id = Column(String(255), nullable=True)
    idempotency_key = Column(String(36), nullable=False)
    correlation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
