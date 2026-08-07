"""MACHINE_RUN schema foundation (s66) — no command runtime yet.

Ownership semantic (D4): a MACHINE_RUN owns exactly one Machine Reservation.
DB link is one-direction to avoid circular FK:
  execution_task_machine_reservations.machine_run_id → machine_runs.id (UNIQUE when set)

Lookup: reservation WHERE machine_run_id = run.id
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

MACHINE_RUN_STATUSES = (
    "HELD",
    "RESERVED",
    "CANCELLED",
    "RELEASED",
    "SUPERSEDED",
)
MACHINE_RUN_OPEN_STATUSES = ("HELD", "RESERVED")

PARTICIPANT_STATUSES = ("ACTIVE", "REMOVED")


class MachineRun(Base):
    __tablename__ = "machine_runs"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_machine_run_idempotency"),
        CheckConstraint(
            "status IN ('HELD', 'RESERVED', 'CANCELLED', 'RELEASED', 'SUPERSEDED')",
            name="ck_machine_run_status",
        ),
        CheckConstraint("version >= 1", name="ck_machine_run_version"),
        CheckConstraint(
            "superseded_by_id IS NULL OR superseded_by_id != id",
            name="ck_machine_run_no_self_supersede",
        ),
        Index("ix_machine_run_status", "status"),
        Index("ix_machine_run_machine_id", "machine_id"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    machine_id = Column(
        Integer,
        ForeignKey("machines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status = Column(String(16), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    timezone = Column(String(64), nullable=False)
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
    released_at = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(String(255), nullable=True)
    superseded_by_id = Column(
        Integer,
        ForeignKey("machine_runs.id", ondelete="RESTRICT"),
        nullable=True,
    )
    idempotency_key = Column(String(36), nullable=False)


class MachineRunParticipant(Base):
    """Participant reference — not a task snapshot clone."""

    __tablename__ = "machine_run_participants"
    __table_args__ = (
        UniqueConstraint(
            "machine_run_id",
            "execution_plan_id",
            "task_key",
            name="uq_machine_run_participant_membership",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'REMOVED')",
            name="ck_machine_run_participant_status",
        ),
        CheckConstraint(
            "length(trim(task_key)) > 0",
            name="ck_machine_run_participant_task_key_nonblank",
        ),
        Index(
            "ix_machine_run_participant_plan_task",
            "execution_plan_id",
            "task_key",
        ),
        Index(
            "uq_machine_run_participant_active_plan_task",
            "execution_plan_id",
            "task_key",
            unique=True,
            sqlite_where=text("status = 'ACTIVE'"),
            postgresql_where=text("status = 'ACTIVE'"),
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    machine_run_id = Column(
        Integer,
        ForeignKey("machine_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    execution_plan_id = Column(
        Integer,
        ForeignKey("execution_plan.id", ondelete="RESTRICT"),
        nullable=False,
    )
    order_id = Column(Integer, nullable=False)
    task_key = Column(String(512), nullable=False)
    status = Column(String(16), nullable=False, default="ACTIVE")
    added_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    added_by = Column(String(255), nullable=True)
    removed_at = Column(DateTime(timezone=True), nullable=True)
    removed_by = Column(String(255), nullable=True)
    idempotency_key = Column(String(36), nullable=True)


class MachineRunTransition(Base):
    """Append-only MACHINE_RUN lifecycle history (insert/read only)."""

    __tablename__ = "machine_run_transitions"
    __table_args__ = (
        UniqueConstraint(
            "transition_id",
            name="uq_machine_run_tr_transition_id",
        ),
        UniqueConstraint(
            "idempotency_key",
            name="uq_machine_run_tr_idempotency",
        ),
        Index("ix_machine_run_tr_run_id", "machine_run_id"),
        Index(
            "ix_machine_run_tr_run_created",
            "machine_run_id",
            "created_at",
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    transition_id = Column(String(36), nullable=False)
    machine_run_id = Column(
        Integer,
        ForeignKey("machine_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    machine_id = Column(Integer, nullable=False)
    operation = Column(String(64), nullable=False)
    previous_status = Column(String(16), nullable=True)
    new_status = Column(String(16), nullable=False)
    previous_version = Column(Integer, nullable=True)
    new_version = Column(Integer, nullable=False)
    reason_code = Column(String(64), nullable=True)
    reason_note = Column(String(REASON_NOTE_MAX_LEN), nullable=True)
    actor_user_id = Column(String(255), nullable=True)
    idempotency_key = Column(String(36), nullable=False)
    correlation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
