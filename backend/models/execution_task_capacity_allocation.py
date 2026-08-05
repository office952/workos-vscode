"""Capacity allocations + append-only allocation transitions (Resource State).

Repo truth: there is no relational ``workcenters`` table. Canonical workcenter
identity in SQLite is the string ``workcenter_code`` (also ``workcenter_rates.code``
for rates). Capacity therefore stores ``workcenter_code`` for WORKCENTER scope
and ``machine_id`` FK for MACHINE scope, plus denormalized ``resource_scope_id``.

XOR CHECK: exactly one of (workcenter_code, machine_id) matches scope type.
Unit CHECK value is ``minutes`` (R2 accepted).
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
)

REASON_NOTE_MAX_LEN = 500

CAPACITY_SCOPE_TYPES = ("WORKCENTER", "MACHINE")
CAPACITY_STATUSES = (
    "HELD",
    "ALLOCATED",
    "RELEASED",
    "CANCELLED",
    "SUPERSEDED",
)
CAPACITY_UNIT = "minutes"


class ExecutionTaskCapacityAllocation(Base):
    __tablename__ = "execution_task_capacity_allocations"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_exec_task_capacity_alloc_idempotency",
        ),
        CheckConstraint(
            "resource_scope_type IN ('WORKCENTER', 'MACHINE')",
            name="ck_exec_task_capacity_alloc_scope_type",
        ),
        CheckConstraint(
            "status IN ('HELD', 'ALLOCATED', 'RELEASED', 'CANCELLED', 'SUPERSEDED')",
            name="ck_exec_task_capacity_alloc_status",
        ),
        CheckConstraint(
            "unit = 'minutes'",
            name="ck_exec_task_capacity_alloc_unit",
        ),
        CheckConstraint("quantity > 0", name="ck_exec_task_capacity_alloc_quantity"),
        CheckConstraint("version >= 1", name="ck_exec_task_capacity_alloc_version"),
        CheckConstraint(
            "length(trim(task_key)) > 0",
            name="ck_exec_task_capacity_alloc_task_key_nonblank",
        ),
        CheckConstraint(
            "length(trim(resource_scope_id)) > 0",
            name="ck_exec_task_capacity_alloc_scope_id_nonblank",
        ),
        CheckConstraint(
            "bucket_end > bucket_start",
            name="ck_exec_task_capacity_alloc_end_after_start",
        ),
        CheckConstraint(
            "superseded_by_id IS NULL OR superseded_by_id != id",
            name="ck_exec_task_capacity_alloc_no_self_supersede",
        ),
        CheckConstraint(
            "("
            "resource_scope_type = 'WORKCENTER' "
            "AND workcenter_code IS NOT NULL "
            "AND machine_id IS NULL"
            ") OR ("
            "resource_scope_type = 'MACHINE' "
            "AND machine_id IS NOT NULL "
            "AND workcenter_code IS NULL"
            ")",
            name="ck_exec_task_capacity_alloc_scope_xor",
        ),
        Index(
            "ix_exec_task_capacity_alloc_plan_task",
            "execution_plan_id",
            "task_key",
        ),
        Index("ix_exec_task_capacity_alloc_status", "status"),
        Index(
            "ix_exec_task_capacity_alloc_wc_bucket",
            "workcenter_code",
            "bucket_start",
            "bucket_end",
        ),
        Index(
            "ix_exec_task_capacity_alloc_machine_bucket",
            "machine_id",
            "bucket_start",
            "bucket_end",
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
    resource_scope_type = Column(String(32), nullable=False)
    resource_scope_id = Column(String(128), nullable=False)
    workcenter_code = Column(String(128), nullable=True)
    machine_id = Column(
        Integer,
        ForeignKey("machines.id", ondelete="RESTRICT"),
        nullable=True,
    )
    bucket_start = Column(DateTime(timezone=True), nullable=False)
    bucket_end = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(64), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(16), nullable=False, default=CAPACITY_UNIT)
    workload_source = Column(String(64), nullable=True)
    workload_source_reference = Column(String(255), nullable=True)
    workload_explanation = Column(String(500), nullable=True)
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
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    superseded_by_id = Column(
        Integer,
        ForeignKey("execution_task_capacity_allocations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    idempotency_key = Column(String(36), nullable=False)


class ExecutionTaskCapacityAllocationTransition(Base):
    """Append-only capacity allocation lifecycle history (insert/read only)."""

    __tablename__ = "execution_task_capacity_allocation_transitions"
    __table_args__ = (
        UniqueConstraint(
            "transition_id",
            name="uq_exec_task_capacity_alloc_tr_transition_id",
        ),
        UniqueConstraint(
            "idempotency_key",
            name="uq_exec_task_capacity_alloc_tr_idempotency",
        ),
        Index("ix_exec_task_capacity_alloc_tr_allocation_id", "allocation_id"),
        Index(
            "ix_exec_task_capacity_alloc_tr_plan_task_created",
            "execution_plan_id",
            "task_key",
            "created_at",
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    transition_id = Column(String(36), nullable=False)
    allocation_id = Column(
        Integer,
        ForeignKey("execution_task_capacity_allocations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    execution_plan_id = Column(
        Integer,
        ForeignKey("execution_plan.id", ondelete="RESTRICT"),
        nullable=False,
    )
    task_key = Column(String(512), nullable=False)
    resource_scope_type = Column(String(32), nullable=False)
    resource_scope_id = Column(String(128), nullable=False)
    operation = Column(String(64), nullable=False)
    previous_status = Column(String(16), nullable=True)
    new_status = Column(String(16), nullable=False)
    previous_quantity = Column(Integer, nullable=True)
    new_quantity = Column(Integer, nullable=True)
    unit = Column(String(16), nullable=False, default=CAPACITY_UNIT)
    workload_source = Column(String(64), nullable=True)
    workload_source_reference = Column(String(255), nullable=True)
    workload_explanation = Column(String(500), nullable=True)
    previous_bucket_start = Column(DateTime(timezone=True), nullable=True)
    previous_bucket_end = Column(DateTime(timezone=True), nullable=True)
    new_bucket_start = Column(DateTime(timezone=True), nullable=True)
    new_bucket_end = Column(DateTime(timezone=True), nullable=True)
    previous_version = Column(Integer, nullable=True)
    new_version = Column(Integer, nullable=False)
    reason_code = Column(String(64), nullable=True)
    reason_note = Column(String(REASON_NOTE_MAX_LEN), nullable=True)
    actor_user_id = Column(String(255), nullable=True)
    idempotency_key = Column(String(36), nullable=False)
    correlation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
