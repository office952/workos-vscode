"""Machine reservations + append-only reservation transitions (Resource State).

Owner forms (s66):
  TASK: execution_plan_id + task_key set, machine_run_id NULL
  RUN:  machine_run_id set, plan/task/order NULL

Open-authoring uniqueness (task-owned): at most one open row per
(execution_plan_id, task_key, machine_id) WHERE machine_run_id IS NULL.
Run-owned: at most one open row per machine_run_id.
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

RESERVATION_OWNER_FORMS = ("TASK", "MACHINE_RUN")

OWNER_XOR_SQL = (
    "("
    "execution_plan_id IS NOT NULL AND task_key IS NOT NULL "
    "AND machine_run_id IS NULL"
    ") OR ("
    "execution_plan_id IS NULL AND task_key IS NULL "
    "AND machine_run_id IS NOT NULL"
    ")"
)


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
            "task_key IS NULL OR length(trim(task_key)) > 0",
            name="ck_exec_task_machine_res_task_key_nonblank",
        ),
        CheckConstraint(
            OWNER_XOR_SQL,
            name="ck_exec_task_machine_res_owner_xor",
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
        Index("ix_exec_task_machine_res_machine_run_id", "machine_run_id"),
        UniqueConstraint(
            "machine_run_id",
            name="uq_exec_task_machine_res_machine_run_id",
        ),
        Index(
            "uq_exec_task_machine_res_open_per_task_machine",
            "execution_plan_id",
            "task_key",
            "machine_id",
            unique=True,
            sqlite_where=text(
                "status IN ('HELD', 'RESERVED') AND machine_run_id IS NULL"
            ),
            postgresql_where=text(
                "status IN ('HELD', 'RESERVED') AND machine_run_id IS NULL"
            ),
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    execution_plan_id = Column(
        Integer,
        ForeignKey("execution_plan.id", ondelete="RESTRICT"),
        nullable=True,
    )
    order_id = Column(Integer, nullable=True)
    task_key = Column(String(512), nullable=True)
    machine_run_id = Column(
        Integer,
        ForeignKey("machine_runs.id", ondelete="RESTRICT"),
        nullable=True,
    )
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
    """Append-only reservation lifecycle history (insert/read only).

    Ownership snapshot columns preserve TASK vs MACHINE_RUN owner at transition time.
    """

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
        CheckConstraint(
            "owner_form IN ('TASK', 'MACHINE_RUN')",
            name="ck_exec_task_machine_res_tr_owner_form",
        ),
        CheckConstraint(
            "("
            "owner_form = 'TASK' AND execution_plan_id IS NOT NULL "
            "AND task_key IS NOT NULL AND machine_run_id IS NULL"
            ") OR ("
            "owner_form = 'MACHINE_RUN' AND machine_run_id IS NOT NULL "
            "AND execution_plan_id IS NULL AND task_key IS NULL"
            ")",
            name="ck_exec_task_machine_res_tr_owner_snapshot",
        ),
        Index("ix_exec_task_machine_res_tr_reservation_id", "reservation_id"),
        Index(
            "ix_exec_task_machine_res_tr_plan_task_created",
            "execution_plan_id",
            "task_key",
            "created_at",
        ),
        Index("ix_exec_task_machine_res_tr_machine_run_id", "machine_run_id"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    transition_id = Column(String(36), nullable=False)
    reservation_id = Column(
        Integer,
        ForeignKey("execution_task_machine_reservations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    owner_form = Column(String(16), nullable=False, default="TASK")
    execution_plan_id = Column(
        Integer,
        ForeignKey("execution_plan.id", ondelete="RESTRICT"),
        nullable=True,
    )
    task_key = Column(String(512), nullable=True)
    machine_run_id = Column(
        Integer,
        ForeignKey("machine_runs.id", ondelete="RESTRICT"),
        nullable=True,
    )
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
