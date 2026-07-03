"""
Phase 6 — Execution Output Model data contracts (S27).

Canonical data shapes for the ProductSystemExecutionPreview envelope
returned by ProductSystemExecutionPreviewService.preview_for_execution().

These are pure data containers (Pydantic models for serialization).
No business logic lives here.

Forbidden imports (spec §24 FP-02):
  - cost_engine_service
  - quote_orchestrator
  - ExecutionPlanService
  - MaterialRate
  - execution_plan_service
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class GeneratedOperation(BaseModel):
    """A single production operation mapped from production_operations table."""

    model_config = ConfigDict(extra="forbid")

    operation_id: str
    task_type: str
    sequence_index: int
    depends_on_operation_ids: List[str]
    component_id: Optional[str]
    description: Optional[str]


class GeneratedTaskRequirement(BaseModel):
    """A single task requirement mapped from task_templates table."""

    model_config = ConfigDict(extra="forbid")

    task_template_id: str
    source_operation_id: str
    task_type: str
    required_skill_ids: List[str]
    required_workcenter_id: Optional[str]
    required_machine_type: Optional[str]
    required_machine_id: Optional[str]
    material_requirements: List[Dict[str, Any]]
    estimated_duration: Dict[str, Any]


class MissingLink(BaseModel):
    """A single missing linkage field on a task_template."""

    model_config = ConfigDict(extra="forbid")

    field: str
    task_template_id: str
    reason: str
    available_today: bool


class TraceSource(BaseModel):
    """Diagnostic trace of which registries were consulted."""

    model_config = ConfigDict(extra="forbid")

    registries_consulted: List[str]
    registries_unavailable: List[str]
    template_resolved_at: str
    linkage_validation_run: bool
    linkage_blockers_count: int
    linkage_warnings_count: int


class ProductSystemExecutionPreview(BaseModel):
    """
    Full execution preview envelope for a given order.

    This is the canonical output of Phase 6 — consumed read-only by:
      - S30 Execution Plan Generation Gate (conditional on REGISTRY_PRODUCTSYSTEM_LIVE)
      - Frontend /execution/{order_id} page (read-only display)
    """

    model_config = ConfigDict(extra="forbid")

    order_id: int
    order_code: str
    template_code: str
    template_version: Optional[str]
    generated_operations: List[GeneratedOperation]
    generated_task_requirements: List[GeneratedTaskRequirement]
    missing_links: List[MissingLink]
    blockers: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    trace_source: TraceSource