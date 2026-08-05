"""Machine reservations + append-only reservation transitions (Resource State).

Open-authoring uniqueness (partial unique index): at most one row per
(execution_plan_id, task_key, machine_id) with status IN ('HELD','RESERVED').
Distinct from machine assignment on tasks_json.
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

RESERVATION_STATUSES = (
    "HELD",
    "RESERVED",
    "CANCELLED",
    "RELEASED",
    "SUPERSEDED",
)
RESERVATION_OPEN_STATUSES = ("HELD", "RESERVED")


class ExecutionTaskMachineReservation(Base):
    __tablename__ = "execution_task_machine_reservations"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_exec_task_machine_res_idempotency",
        ),
        CheckConstraint(
            "status IN ('HELD', 'RESERVED', 'CANCELLED', 'RELEASED', 'SUPERSEDED')",
            name="ck_exec_task_machine_res_status",
        ),
        CheckConstraint("version >= 1", name="ck_exec_task_machine_res_version"),
        CheckConstraint(
            "length(trim(task_key)) > 0",
            name="ck_exec_task_machine_res_task_key_nonblank",
        ),
        CheckConstraint(
            "reservation_end > reservation_start",
            name="ck_exec_task_machine_res_end_after_start",
        ),
        CheckConstraint(
            "superseded_by_id IS NULL OR superseded_by_id != id",
            name="ck_exec_task_machine_res_no_self_supersede",
        ),
        Index(
            "ix_exec_task_machine_res_plan_task",
            "execution_plan_id",
            "task_key",
        ),
        Index("ix_exec_task_machine_res_status", "status"),
        Index(
            "ix_exec_task_machine_res_machine_window",
            "machine_id",
            "reservation_start",
            "reservation_end",
        ),
        Index(
            "uq_exec_task_machine_res_open_per_task_machine",
            "execution_plan_id",
            "task_key",
            "machine_id",
            unique=True,
            sqlite_where=text("status IN ('HELD', 'RESERVED')"),
            postgresql_where=text("status IN ('HELD', 'RESERVED')"),
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
    machine_id = Column(
        Integer,
        ForeignKey("machines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reservation_start = Column(DateTime(timezone=True), nullable=False)
    reservation_end = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False)
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
    released_at = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(String(255), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by = Column(String(255), nullable=True)
    superseded_by_id = Column(
        Integer,
        ForeignKey("execution_task_machine_reservations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    idempotency_key = Column(String(36), nullable=False)


class ExecutionTaskMachineReservationTransition(Base):
    """Append-only reservation lifecycle history (insert/read only)."""

    __tablename__ = "execution_task_machine_reservation_transitions"
    __table_args__ = (
        UniqueConstraint(
            "transition_id",
            name="uq_exec_task_machine_res_tr_transition_id",
        ),
        UniqueConstraint(
            "idempotency_key",
            name="uq_exec_task_machine_res_tr_idempotency",
        ),
        Index("ix_exec_task_machine_res_tr_reservation_id", "reservation_id"),
        Index(
            "ix_exec_task_machine_res_tr_plan_task_created",
            "execution_plan_id",
            "task_key",
            "created_at",
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    transition_id = Column(String(36), nullable=False)
    reservation_id = Column(
        Integer,
        ForeignKey("execution_task_machine_reservations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    execution_plan_id = Column(
        Integer,
        ForeignKey("execution_plan.id", ondelete="RESTRICT"),
        nullable=False,
    )
    task_key = Column(String(512), nullable=False)
    machine_id = Column(Integer, nullable=False)
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
