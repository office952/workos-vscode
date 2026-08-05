"""Stage 1 — Owner-configured workcenter capacity source (available minutes / day).

No relational workcenters table: identity is string ``workcenter_code``
(APPLICATION_GUARDED referential integrity).
"""

from __future__ import annotations

from datetime import datetime

from core.database import Base
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

REASON_NOTE_MAX_LEN = 500

CAPACITY_SOURCE_STATUSES = ("ACTIVE", "DISABLED", "SUPERSEDED")
OVER_ALLOCATION_POLICIES = ("WARN_ONLY", "HARD_BLOCK", "ALLOW_WITH_REASON")
CAPACITY_SOURCE_LABELS = ("OWNER_CONFIGURED", "SYSTEM_DERIVED", "AI_DECISION")
DEFAULT_OVER_ALLOCATION_POLICY = "WARN_ONLY"


class WorkcenterCapacitySource(Base):
    __tablename__ = "workcenter_capacity_sources"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_wc_capacity_source_idempotency",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'DISABLED', 'SUPERSEDED')",
            name="ck_wc_capacity_source_status",
        ),
        CheckConstraint(
            "over_allocation_policy IN "
            "('WARN_ONLY', 'HARD_BLOCK', 'ALLOW_WITH_REASON')",
            name="ck_wc_capacity_source_policy",
        ),
        CheckConstraint(
            "source_label IN "
            "('OWNER_CONFIGURED', 'SYSTEM_DERIVED', 'AI_DECISION')",
            name="ck_wc_capacity_source_label",
        ),
        CheckConstraint(
            "available_minutes >= 0",
            name="ck_wc_capacity_source_minutes_nonneg",
        ),
        CheckConstraint("version >= 1", name="ck_wc_capacity_source_version"),
        CheckConstraint(
            "length(trim(workcenter_code)) > 0",
            name="ck_wc_capacity_source_wc_nonblank",
        ),
        CheckConstraint(
            "bucket_end > bucket_start",
            name="ck_wc_capacity_source_end_after_start",
        ),
        CheckConstraint(
            "superseded_by_id IS NULL OR superseded_by_id != id",
            name="ck_wc_capacity_source_no_self_supersede",
        ),
        Index("ix_wc_capacity_source_status", "status"),
        Index(
            "ix_wc_capacity_source_wc_day",
            "workcenter_code",
            "bucket_date",
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    workcenter_code = Column(String(128), nullable=False)
    bucket_date = Column(Date, nullable=False)
    bucket_start = Column(DateTime(timezone=True), nullable=False)
    bucket_end = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(64), nullable=False)
    available_minutes = Column(Integer, nullable=False)
    over_allocation_policy = Column(
        String(32), nullable=False, default=DEFAULT_OVER_ALLOCATION_POLICY
    )
    source_label = Column(String(32), nullable=False, default="OWNER_CONFIGURED")
    source_explanation = Column(String(500), nullable=True)
    source_execution_truth = Column(Integer, nullable=False, default=1)
    status = Column(String(16), nullable=False, default="ACTIVE")
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
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    disabled_by = Column(String(255), nullable=True)
    superseded_by_id = Column(
        Integer,
        ForeignKey("workcenter_capacity_sources.id", ondelete="RESTRICT"),
        nullable=True,
    )
    idempotency_key = Column(String(36), nullable=False)


class WorkcenterCapacitySourceTransition(Base):
    """Append-only history for workcenter capacity source commands."""

    __tablename__ = "workcenter_capacity_source_transitions"
    __table_args__ = (
        UniqueConstraint(
            "transition_id",
            name="uq_wc_capacity_source_tr_transition_id",
        ),
        UniqueConstraint(
            "idempotency_key",
            name="uq_wc_capacity_source_tr_idempotency",
        ),
        Index("ix_wc_capacity_source_tr_source_id", "source_id"),
        Index(
            "ix_wc_capacity_source_tr_wc_day_created",
            "workcenter_code",
            "bucket_date",
            "created_at",
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    transition_id = Column(String(36), nullable=False)
    source_id = Column(
        Integer,
        ForeignKey("workcenter_capacity_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    workcenter_code = Column(String(128), nullable=False)
    bucket_date = Column(Date, nullable=False)
    operation = Column(String(64), nullable=False)
    previous_status = Column(String(16), nullable=True)
    new_status = Column(String(16), nullable=False)
    previous_available_minutes = Column(Integer, nullable=True)
    new_available_minutes = Column(Integer, nullable=True)
    previous_policy = Column(String(32), nullable=True)
    new_policy = Column(String(32), nullable=True)
    previous_version = Column(Integer, nullable=True)
    new_version = Column(Integer, nullable=False)
    reason_code = Column(String(64), nullable=True)
    reason_note = Column(String(REASON_NOTE_MAX_LEN), nullable=True)
    actor_user_id = Column(String(255), nullable=True)
    idempotency_key = Column(String(36), nullable=False)
    correlation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
