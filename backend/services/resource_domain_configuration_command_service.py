"""Resource State R7/R10 — domain configuration command (CAS + idempotency).

Activation is **domain-specific** via ``DOMAIN_WRITER_READY``:
  SCHEDULING / MACHINE_RESERVATION → writers implemented (R9)
  CAPACITY_ALLOCATION → blocked until writer + capacity source exist

R10 disable safety:
  DISABLE rejected while blocking source rows exist for that domain.
  Terminal/history-only rows do not block disable. Rows are never deleted.

QA activation remains NOT_AUTHORIZED without a separate Owner GO.

DISABLED semantics (R1/R2/R6): only ACTIVE configurations are loaded by the
read path → DISABLED evaluates as NOT_CONFIGURED (configured=False).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from core.schema_ownership import CAPACITY_SOURCE_TABLES, RESOURCE_STATE_TABLES
from models.execution_task_capacity_allocation import CAPACITY_STATUSES
from models.execution_task_machine_reservation import RESERVATION_STATUSES
from models.execution_task_schedule import SCHEDULE_STATUSES
from models.resource_domain_configuration import (
    CONFIGURATION_STATUSES,
    RESOURCE_DOMAINS,
    ResourceDomainConfiguration,
    ResourceDomainConfigurationTransition,
)
from schemas.resource_state_configuration import (
    ResourceDomainConfigurationCommand,
    ResourceDomainConfigurationResult,
)
from services.resource_domain_configuration_repository import (
    ResourceDomainConfigurationRepository,
)
from services.resource_state_read_evaluator import (
    CAPACITY_BLOCKING_STATUSES,
    RESERVATION_BLOCKING_STATUSES,
    SCHEDULE_BLOCKING_STATUSES,
    evaluate_domain_from_rows,
)
from services.resource_state_read_service import evaluate_task_resource_state
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Domain-specific writer readiness (not a global unlock).
DOMAIN_WRITER_READY: dict[str, bool] = {
    "SCHEDULING": True,
    "MACHINE_RESERVATION": True,
    # Stage 1 writer + workcenter source exist in code (s65).
    # QA stays on s64 → activation still blocked until schema rollout GO.
    "CAPACITY_ALLOCATION": True,
}

DOMAIN_SOURCE_TABLE: dict[str, str] = {
    "SCHEDULING": "execution_task_schedules",
    "MACHINE_RESERVATION": "execution_task_machine_reservations",
    "CAPACITY_ALLOCATION": "execution_task_capacity_allocations",
}

DOMAIN_KNOWN_STATUSES: dict[str, frozenset[str]] = {
    "SCHEDULING": frozenset(SCHEDULE_STATUSES),
    "MACHINE_RESERVATION": frozenset(RESERVATION_STATUSES),
    "CAPACITY_ALLOCATION": frozenset(CAPACITY_STATUSES),
}

DOMAIN_BLOCKING_STATUSES: dict[str, frozenset[str]] = {
    "SCHEDULING": SCHEDULE_BLOCKING_STATUSES,
    "MACHINE_RESERVATION": RESERVATION_BLOCKING_STATUSES,
    "CAPACITY_ALLOCATION": CAPACITY_BLOCKING_STATUSES,
}

# Retained for test imports / docs; no longer unlocks activation globally.
ACTIVATION_ALLOW_ENV = "WORKOS_RESOURCE_STATE_ALLOW_DOMAIN_ACTIVATION"


class ResourceDomainConfigurationError(Exception):
    """Base command error with machine-readable code."""

    def __init__(self, code: str, message: str = ""):
        self.code = code
        self.message = message or code
        super().__init__(self.message)


class ResourceDomainConfigurationConflictError(ResourceDomainConfigurationError):
    pass


class ResourceDomainConfigurationCasConflictError(ResourceDomainConfigurationError):
    pass


class ResourceDomainConfigurationValidationError(ResourceDomainConfigurationError):
    pass


class ResourceDomainConfigurationActivationBlockedError(ResourceDomainConfigurationError):
    pass


class ResourceDomainConfigurationDisableBlockedError(ResourceDomainConfigurationError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_operation(
    *, previous_status: str | None, target_status: str
) -> str:
    if previous_status is None and target_status == "DISABLED":
        return "CONFIGURE_DOMAIN"
    if target_status == "ACTIVE":
        return "ACTIVATE_DOMAIN"
    return "DISABLE_DOMAIN"


def _evaluated_hint(*, status: str) -> str:
    if status == "ACTIVE":
        return "ACTIVE_CONFIG_READS_AS_CLEAR_WHEN_NO_BLOCKING_RECORDS"
    return "DISABLED_READS_AS_NOT_CONFIGURED"


async def _schema_tables_present(db: AsyncSession) -> bool:
    result = await db.execute(
        text(
            "SELECT name FROM sqlite_master WHERE type='table' AND ("
            "name LIKE 'resource_%' "
            "OR name LIKE 'execution_task_schedule%' "
            "OR name LIKE 'execution_task_machine_reservation%' "
            "OR name LIKE 'execution_task_capacity_allocation%' "
            "OR name LIKE 'workcenter_capacity%'"
            ")"
        )
    )
    names = {row[0] for row in result.fetchall()}
    return RESOURCE_STATE_TABLES.issubset(names)


async def _capacity_source_schema_present(db: AsyncSession) -> bool:
    result = await db.execute(
        text(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name LIKE 'workcenter_capacity%'"
        )
    )
    names = {row[0] for row in result.fetchall()}
    return CAPACITY_SOURCE_TABLES.issubset(names)


def _read_evaluator_present() -> bool:
    return callable(evaluate_domain_from_rows) and callable(
        evaluate_task_resource_state
    )


async def _inconsistent_source_count(db: AsyncSession, domain: str) -> int:
    table = DOMAIN_SOURCE_TABLE[domain]
    known = DOMAIN_KNOWN_STATUSES[domain]
    # Count rows whose status is outside the frozen vocabulary.
    placeholders = ", ".join(f"'{s}'" for s in sorted(known))
    result = await db.execute(
        text(
            f"SELECT COUNT(*) FROM {table} "
            f"WHERE status IS NULL OR status NOT IN ({placeholders})"
        )
    )
    return int(result.scalar_one())


async def count_blocking_source_rows(db: AsyncSession, domain: str) -> int:
    table = DOMAIN_SOURCE_TABLE[domain]
    blocking = DOMAIN_BLOCKING_STATUSES[domain]
    placeholders = ", ".join(f"'{s}'" for s in sorted(blocking))
    result = await db.execute(
        text(f"SELECT COUNT(*) FROM {table} WHERE status IN ({placeholders})")
    )
    return int(result.scalar_one())


async def assess_activation_readiness(
    db: AsyncSession, *, domain: str
) -> tuple[bool, str]:
    """Return (ok, reason_code). Used before any transition to ACTIVE.

    Writer readiness is **per domain** — CAPACITY cannot be unlocked by a
    global env flag when its writer is not ready.
    """
    if domain not in RESOURCE_DOMAINS:
        return False, "domain_not_supported"
    if not await _schema_tables_present(db):
        return False, "schema_missing"
    if not _read_evaluator_present():
        return False, "read_evaluator_missing"
    inconsistent = await _inconsistent_source_count(db, domain)
    if inconsistent > 0:
        return False, "inconsistent_source_records"
    if not DOMAIN_WRITER_READY.get(domain, False):
        if domain == "CAPACITY_ALLOCATION":
            return False, "ACTIVATION_BLOCKED_MISSING_WRITER_AND_SOURCE"
        return False, "ACTIVATION_BLOCKED_UNTIL_DOMAIN_WRITER_EXISTS"
    if domain == "CAPACITY_ALLOCATION":
        if not await _capacity_source_schema_present(db):
            return False, "ACTIVATION_BLOCKED_MISSING_WRITER_AND_SOURCE"
    return True, "ready"


async def assess_disable_readiness(
    db: AsyncSession, *, domain: str
) -> tuple[bool, str]:
    """DISABLE allowed only when no blocking source rows exist."""
    if domain not in RESOURCE_DOMAINS:
        return False, "domain_not_supported"
    blocking = await count_blocking_source_rows(db, domain)
    if blocking > 0:
        return False, "disable_blocked_active_source_rows"
    return True, "ready"


async def domain_activation_readiness_report(
    db: AsyncSession,
) -> dict[str, dict[str, Any]]:
    """R10 readiness matrix for all Resource State domains."""
    report: dict[str, dict[str, Any]] = {}
    for domain in RESOURCE_DOMAINS:
        ok, reason = await assess_activation_readiness(db, domain=domain)
        report[domain] = {
            "ready": ok,
            "reason_code": reason,
            "writer_ready": bool(DOMAIN_WRITER_READY.get(domain, False)),
            "blocking_source_rows": await count_blocking_source_rows(db, domain),
            "inconsistent_source_rows": await _inconsistent_source_count(
                db, domain
            ),
        }
    return report


def _payload_fingerprint(
    *,
    domain: str,
    command: ResourceDomainConfigurationCommand,
    actor_user_id: str,
) -> dict[str, Any]:
    return {
        "domain": domain,
        "target_status": command.target_status,
        "expected_version": command.expected_version,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "application_scope_key": command.application_scope_key,
        "actor_user_id": actor_user_id,
    }


def _transition_matches_payload(
    transition: ResourceDomainConfigurationTransition,
    fingerprint: dict[str, Any],
) -> bool:
    expected = fingerprint["expected_version"]
    prev_ver = transition.previous_version
    version_ok = (prev_ver is None and expected == 0) or prev_ver == expected
    return (
        transition.domain == fingerprint["domain"]
        and transition.new_status == fingerprint["target_status"]
        and version_ok
        and (transition.reason_code or "") == fingerprint["reason_code"]
        and (transition.reason_note or None) == fingerprint["reason_note"]
        and (transition.actor_user_id or "") == fingerprint["actor_user_id"]
    )


async def configure_resource_domain(
    db: AsyncSession,
    *,
    domain: str,
    command: ResourceDomainConfigurationCommand,
    actor_user_id: str,
) -> ResourceDomainConfigurationResult:
    """Apply CONFIGURE / ACTIVATE / DISABLE with CAS + idempotency.

    Current-state update and transition insert commit in the same session
    transaction (caller commits; this function flushes within the open txn).
    """
    domain_norm = (domain or "").strip().upper()
    if domain_norm not in RESOURCE_DOMAINS:
        raise ResourceDomainConfigurationValidationError(
            "invalid_domain", f"unsupported domain: {domain}"
        )
    if command.target_status not in CONFIGURATION_STATUSES:
        raise ResourceDomainConfigurationValidationError(
            "invalid_status", f"unsupported status: {command.target_status}"
        )

    repo = ResourceDomainConfigurationRepository(db)
    fingerprint = _payload_fingerprint(
        domain=domain_norm, command=command, actor_user_id=actor_user_id
    )

    existing_transition = await repo.get_transition_by_idempotency_key(
        command.idempotency_key
    )
    if existing_transition is not None:
        if not _transition_matches_payload(existing_transition, fingerprint):
            raise ResourceDomainConfigurationConflictError(
                "idempotency_payload_conflict",
                "idempotency_key already used with a different payload",
            )
        cfg = await repo.get_by_domain_scope(
            domain=domain_norm,
            application_scope_key=command.application_scope_key,
        )
        if cfg is None:
            raise ResourceDomainConfigurationConflictError(
                "idempotency_orphaned_transition",
                "transition exists without configuration row",
            )
        return ResourceDomainConfigurationResult(
            domain=domain_norm,  # type: ignore[arg-type]
            configuration_id=cfg.id,
            status=cfg.status,  # type: ignore[arg-type]
            version=cfg.version,
            operation=existing_transition.operation,  # type: ignore[arg-type]
            transition_id=existing_transition.transition_id,
            previous_status=existing_transition.previous_status,  # type: ignore[arg-type]
            previous_version=existing_transition.previous_version,
            already_applied=True,
            configured_at=cfg.configured_at,
            disabled_at=cfg.disabled_at,
            evaluated_hint=_evaluated_hint(status=cfg.status),
        )

    if command.target_status == "ACTIVE":
        ready, reason = await assess_activation_readiness(db, domain=domain_norm)
        if not ready:
            raise ResourceDomainConfigurationActivationBlockedError(
                reason,
                f"activation blocked for {domain_norm}: {reason}",
            )

    cfg = await repo.get_by_domain_scope(
        domain=domain_norm,
        application_scope_key=command.application_scope_key,
    )

    if command.target_status == "DISABLED" and (
        cfg is None or cfg.status == "ACTIVE"
    ):
        # Create-as-DISABLED is fine (no active rows expected).
        # ACTIVE→DISABLED requires no blocking source rows.
        if cfg is not None and cfg.status == "ACTIVE":
            d_ok, d_reason = await assess_disable_readiness(
                db, domain=domain_norm
            )
            if not d_ok:
                raise ResourceDomainConfigurationDisableBlockedError(
                    d_reason,
                    f"disable blocked for {domain_norm}: {d_reason}",
                )

    now = _utcnow()

    if cfg is None:
        if command.expected_version != 0:
            raise ResourceDomainConfigurationCasConflictError(
                "cas_stale_or_missing",
                "configuration missing; expected_version must be 0 for create",
            )
        previous_status = None
        previous_version = None
        new_version = 1
        operation = _resolve_operation(
            previous_status=None, target_status=command.target_status
        )
        cfg = ResourceDomainConfiguration(
            domain=domain_norm,
            application_scope_key=command.application_scope_key,
            status=command.target_status,
            version=new_version,
            configured_at=now if command.target_status == "ACTIVE" else None,
            configured_by=actor_user_id if command.target_status == "ACTIVE" else None,
            disabled_at=now if command.target_status == "DISABLED" else None,
            disabled_by=actor_user_id if command.target_status == "DISABLED" else None,
            created_at=now,
            updated_at=now,
        )
        await repo.add_configuration(cfg)
    else:
        if cfg.version != command.expected_version:
            raise ResourceDomainConfigurationCasConflictError(
                "cas_stale",
                f"expected_version={command.expected_version} "
                f"current_version={cfg.version}",
            )
        previous_status = cfg.status
        previous_version = cfg.version
        new_version = cfg.version + 1
        operation = _resolve_operation(
            previous_status=previous_status, target_status=command.target_status
        )
        cfg.status = command.target_status
        cfg.version = new_version
        cfg.updated_at = now
        if command.target_status == "ACTIVE":
            cfg.configured_at = now
            cfg.configured_by = actor_user_id
            # Keep disabled_* for audit trail of last disable; CHECK requires
            # disabled_at when DISABLED only — clear for ACTIVE.
            cfg.disabled_at = None
            cfg.disabled_by = None
        else:
            cfg.disabled_at = now
            cfg.disabled_by = actor_user_id

    transition = ResourceDomainConfigurationTransition(
        transition_id=str(uuid.uuid4()),
        configuration_id=cfg.id,
        domain=domain_norm,
        operation=operation,
        previous_status=previous_status,
        new_status=command.target_status,
        previous_version=previous_version,
        new_version=new_version,
        reason_code=command.reason_code,
        reason_note=command.reason_note,
        actor_user_id=actor_user_id,
        idempotency_key=command.idempotency_key,
        correlation_id=command.correlation_id,
        created_at=now,
    )
    await repo.add_transition(transition)
    # Same open transaction: caller commits both rows together.
    await db.flush()

    return ResourceDomainConfigurationResult(
        domain=domain_norm,  # type: ignore[arg-type]
        configuration_id=cfg.id,
        status=cfg.status,  # type: ignore[arg-type]
        version=cfg.version,
        operation=operation,  # type: ignore[arg-type]
        transition_id=transition.transition_id,
        previous_status=previous_status,  # type: ignore[arg-type]
        previous_version=previous_version,
        already_applied=False,
        configured_at=cfg.configured_at,
        disabled_at=cfg.disabled_at,
        evaluated_hint=_evaluated_hint(status=cfg.status),
    )


async def count_configuration_transitions(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(ResourceDomainConfigurationTransition)
    )
    return int(result.scalar_one())
