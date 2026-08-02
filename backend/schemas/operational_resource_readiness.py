"""Operational Resource Readiness (F7C) — read-only ORR allow-list ∩ machines registry.

Canonical read model over materialized ``operational_tasks[]``:
  OperationalTask -> WorkcenterRequirement -> ResourceRequirementMode
    -> CompatibleMachineCandidates -> ResourceReadinessResult

Source of truth (never invented, never a parallel system):
  - ``operation_resource_requirements`` (ORR) — ``allowed_resource_codes`` /
    ``allowed_workcenter_codes`` / ``default_resource_code``
  - ``machines`` registry — ``resource_kind`` (machine | tool | work_area) / ``is_active``
  - ``data.operational_workcenters`` — canonical workcenter code identity

Honesty constraints (Lead GO, F7C):
  - A formal ``machine_required|optional|workcenter_only`` enum does **not** exist in the
    registry. ``resource_requirement_mode`` is *derived* from ORR truth only.
  - Never silently assign ``machine_code`` onto ``operational_tasks``.
  - ``WC_CNC`` must never be silently treated as ``WC_CNC_ROUTING``.
  - ``estimated_minutes`` stays null with a warning — never invented.
  - Read-only: zero DB writes, zero sessions, zero assignments.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

REQUIREMENT_SOURCE = "operation_resource_requirements+machines_registry"
REQUIREMENT_VERSION = "resource-readiness/v1"

WorkcenterRegistryStatus = Literal["resolved", "non_canonical", "missing", "empty"]

ResourceRequirementMode = Literal[
    "orr_allowlist",
    "workcenter_only",
    "unknown_resource_policy",
]

# Enum kept complete per Owner spec even though some members are not yet
# reachable by current registry truth (e.g. no maintenance-window data
# source exists today). Statuses are only ever emitted when justified.
ResourceReadinessStatus = Literal[
    "ready",
    "ready_with_warnings",
    "missing_workcenter",
    "unknown_resource_policy",
    "machine_required_but_none_compatible",
    "machine_optional_no_candidate",
    "workcenter_only",
    "machine_unavailable",
    "maintenance_conflict",
    "ambiguous_mapping",
]

BLOCKED_STATUSES: frozenset[str] = frozenset(
    {
        "missing_workcenter",
        "unknown_resource_policy",
        "machine_required_but_none_compatible",
        "machine_optional_no_candidate",
        "machine_unavailable",
        "maintenance_conflict",
        "ambiguous_mapping",
    }
)


class CompatibleMachineCandidate(BaseModel):
    """One active registry row compatible with an ORR allow-list entry."""

    resource_code: str
    name: str | None = None
    resource_kind: str
    workcenter_code: str | None = None
    is_active: bool
    is_available: bool
    operational_status: str | None = None
    is_default: bool = False


class OperationalTaskResourceReadiness(BaseModel):
    """Resource readiness for exactly one materialized operational task."""

    task_key: str | None = None
    display_name: str | None = None
    source_operation_code: str | None = None
    canonical_task_type: str | None = None
    workcenter_code: str | None = None
    workcenter_registry_status: WorkcenterRegistryStatus
    resource_requirement_mode: ResourceRequirementMode
    authorization_mode: str | None = None
    registry_operation_code: str | None = None
    allowed_resource_codes: list[str] = Field(default_factory=list)
    default_resource_code: str | None = None
    compatible_machine_candidates: list[CompatibleMachineCandidate] = Field(
        default_factory=list
    )
    work_area_candidates: list[CompatibleMachineCandidate] = Field(default_factory=list)
    estimated_minutes: float | None = None
    status: ResourceReadinessStatus
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    requirement_source: str = REQUIREMENT_SOURCE
    requirement_version: str = REQUIREMENT_VERSION


OperationalResourceReadinessTopStatus = Literal[
    "ok",
    "plan_not_found",
    "blocked_not_materialized",
]


class OperationalResourceReadinessResult(BaseModel):
    """Read-only resource readiness for an order's materialized plan."""

    mode: Literal["operational_resource_readiness"] = "operational_resource_readiness"
    order_id: int
    execution_plan_id: int | None = None
    status: OperationalResourceReadinessTopStatus
    requirement_source: str = REQUIREMENT_SOURCE
    requirement_version: str = REQUIREMENT_VERSION
    operational_task_count: int = 0
    ready_count: int = 0
    warning_count: int = 0
    blocked_count: int = 0
    tasks: list[OperationalTaskResourceReadiness] = Field(default_factory=list)
    side_effects: Literal["none"] = "none"
    notes: list[str] = Field(default_factory=list)
