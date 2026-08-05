"""Resource State R6 — domain + aggregate read evaluators.

Rules (Owner GO R6):
  no ACTIVE configuration → NOT_CONFIGURED
  ACTIVE config + query failure / inconsistency → UNKNOWN
  ACTIVE config + blocking source rows → ACTIVE
  ACTIVE config + successful query + no blockers → CLEAR

absence of records != CLEAR without ACTIVE configuration.

Aggregate (Owner R6 order):
  UNKNOWN → BLOCKED_UNKNOWN
  else NOT_CONFIGURED → BLOCKED_NOT_CONFIGURED
  else ACTIVE → BLOCKED_ACTIVE
  else all CLEAR → CLEAR
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Iterable, Sequence

from models.execution_task_capacity_allocation import CAPACITY_STATUSES
from models.execution_task_machine_reservation import RESERVATION_STATUSES
from models.execution_task_schedule import SCHEDULE_STATUSES
from models.resource_domain_configuration import ResourceDomainConfiguration
from schemas.resource_state_read import (
    AggregateEvaluationState,
    DomainResourceStateResult,
)

# Guard-blocking statuses when domain is configured (R2 frozen vocabulary).
SCHEDULE_BLOCKING_STATUSES = frozenset({"PLANNED", "CONFIRMED"})
RESERVATION_BLOCKING_STATUSES = frozenset({"HELD", "RESERVED"})
CAPACITY_BLOCKING_STATUSES = frozenset({"HELD", "ALLOCATED"})

# DRAFT is open for authoring uniqueness but not guard-blocking.
SCHEDULE_KNOWN_STATUSES = frozenset(SCHEDULE_STATUSES)
RESERVATION_KNOWN_STATUSES = frozenset(RESERVATION_STATUSES)
CAPACITY_KNOWN_STATUSES = frozenset(CAPACITY_STATUSES)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def evaluate_domain_from_rows(
    *,
    domain: str,
    configuration: ResourceDomainConfiguration | None,
    rows: Sequence[object],
    blocking_statuses: frozenset[str],
    known_statuses: frozenset[str],
    status_getter: Callable[[object], str | None],
    id_getter: Callable[[object], int],
    evaluated_at: datetime | None = None,
    force_unknown: bool = False,
    unknown_reason: str = "query_or_inconsistency",
) -> DomainResourceStateResult:
    """Pure evaluation helper (also used by isolated tests)."""
    now = evaluated_at or _utcnow()

    if force_unknown:
        return DomainResourceStateResult(
            domain=domain,  # type: ignore[arg-type]
            state="UNKNOWN",
            configured=configuration is not None
            and getattr(configuration, "status", None) == "ACTIVE",
            configuration_id=getattr(configuration, "id", None),
            configuration_version=getattr(configuration, "version", None),
            source_record_ids=[],
            reason_code=unknown_reason,
            evaluated_at=now,
        )

    if configuration is None or configuration.status != "ACTIVE":
        return DomainResourceStateResult(
            domain=domain,  # type: ignore[arg-type]
            state="NOT_CONFIGURED",
            configured=False,
            configuration_id=None,
            configuration_version=None,
            source_record_ids=[],
            reason_code="no_active_configuration",
            evaluated_at=now,
        )

    # Inconsistency: unknown/invalid status values on source rows.
    for row in rows:
        status = status_getter(row)
        if status is None or status not in known_statuses:
            return DomainResourceStateResult(
                domain=domain,  # type: ignore[arg-type]
                state="UNKNOWN",
                configured=True,
                configuration_id=configuration.id,
                configuration_version=configuration.version,
                source_record_ids=[id_getter(r) for r in rows],
                reason_code="inconsistent_source_status",
                evaluated_at=now,
            )

    blockers = [
        row for row in rows if status_getter(row) in blocking_statuses
    ]
    if blockers:
        return DomainResourceStateResult(
            domain=domain,  # type: ignore[arg-type]
            state="ACTIVE",
            configured=True,
            configuration_id=configuration.id,
            configuration_version=configuration.version,
            source_record_ids=[id_getter(r) for r in blockers],
            reason_code="blocking_source_records",
            evaluated_at=now,
        )

    return DomainResourceStateResult(
        domain=domain,  # type: ignore[arg-type]
        state="CLEAR",
        configured=True,
        configuration_id=configuration.id,
        configuration_version=configuration.version,
        source_record_ids=[],
        reason_code="configured_no_blocking_records",
        evaluated_at=now,
    )


def aggregate_domain_states(
    domains: Iterable[DomainResourceStateResult],
) -> tuple[AggregateEvaluationState, str]:
    """Fail-closed aggregate — Owner R6 precedence."""
    states = [d.state for d in domains]
    if any(s == "UNKNOWN" for s in states):
        return "BLOCKED_UNKNOWN", "domain_unknown"
    if any(s == "NOT_CONFIGURED" for s in states):
        return "BLOCKED_NOT_CONFIGURED", "domain_not_configured"
    if any(s == "ACTIVE" for s in states):
        return "BLOCKED_ACTIVE", "domain_active"
    if states and all(s == "CLEAR" for s in states):
        return "CLEAR", "all_domains_clear"
    return "BLOCKED_UNKNOWN", "aggregate_incomplete"
