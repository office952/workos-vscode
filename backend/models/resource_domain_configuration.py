"""Persisted Resource State domain configuration + append-only transitions.

Configuration status is ACTIVE/DISABLED only — never CLEAR/ACTIVE/UNKNOWN/
NOT_CONFIGURED evaluation results (those are derived at read time).
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

RESOURCE_DOMAINS = ("SCHEDULING", "MACHINE_RESERVATION", "CAPACITY_ALLOCATION")
CONFIGURATION_STATUSES = ("ACTIVE", "DISABLED")


class ResourceDomainConfiguration(Base):
    __tablename__ = "resource_domain_configurations"
    __table_args__ = (
        UniqueConstraint(
            "domain",
            "application_scope_key",
            name="uq_resource_domain_config_domain_scope",
        ),
        CheckConstraint(
            "domain IN ('SCHEDULING', 'MACHINE_RESERVATION', 'CAPACITY_ALLOCATION')",
            name="ck_resource_domain_config_domain",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'DISABLED')",
            name="ck_resource_domain_config_status",
        ),
        CheckConstraint("version >= 1", name="ck_resource_domain_config_version"),
        CheckConstraint(
            "("
            "status = 'ACTIVE' AND configured_at IS NOT NULL"
            ") OR ("
            "status = 'DISABLED' AND disabled_at IS NOT NULL"
            ")",
            name="ck_resource_domain_config_status_timestamps",
        ),
        Index("ix_resource_domain_config_domain_scope", "domain", "application_scope_key"),
        Index("ix_resource_domain_config_status", "status"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    domain = Column(String(32), nullable=False)
    application_scope_key = Column(String(64), nullable=False, default="application")
    status = Column(String(16), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    configured_at = Column(DateTime(timezone=True), nullable=True)
    configured_by = Column(String(255), nullable=True)
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    disabled_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )


class ResourceDomainConfigurationTransition(Base):
    """Append-only configuration lifecycle history (insert/read only)."""

    __tablename__ = "resource_domain_configuration_transitions"
    __table_args__ = (
        UniqueConstraint(
            "transition_id",
            name="uq_resource_domain_config_tr_transition_id",
        ),
        UniqueConstraint(
            "idempotency_key",
            name="uq_resource_domain_config_tr_idempotency",
        ),
        CheckConstraint(
            "domain IN ('SCHEDULING', 'MACHINE_RESERVATION', 'CAPACITY_ALLOCATION')",
            name="ck_resource_domain_config_tr_domain",
        ),
        CheckConstraint(
            "previous_status IN ('ACTIVE', 'DISABLED') OR previous_status IS NULL",
            name="ck_resource_domain_config_tr_prev_status",
        ),
        CheckConstraint(
            "new_status IN ('ACTIVE', 'DISABLED')",
            name="ck_resource_domain_config_tr_new_status",
        ),
        Index("ix_resource_domain_config_tr_configuration_id", "configuration_id"),
        Index("ix_resource_domain_config_tr_created_at", "created_at"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    transition_id = Column(String(36), nullable=False)
    configuration_id = Column(
        Integer,
        ForeignKey("resource_domain_configurations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    domain = Column(String(32), nullable=False)
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
