"""ExecutionPlan V2 operational task materialization schema (Step 9.3.4.a)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

OPERATIONAL_TASKS_VERSION = "v2.materialize.1"
OPERATIONAL_TASK_SOURCE = "execution_plan_v2"
OPERATIONAL_STATUS_PENDING = "pending"
V2_LAYER_ID = "v2"

ExecutionPlanV2MaterializeStatus = Literal[
    "materialized",
    "already_materialized",
    "blocked",
    "wrong_plan_source",
    "not_found",
]


class ExecutionPlanV2MaterializeResult(BaseModel):
    """Result of materializing operational_tasks[] from V2 plan envelope — no sessions."""

    status: ExecutionPlanV2MaterializeStatus
    order_id: int
    execution_plan_id: int | None = None
    execution_tasks_created: bool = False
    operational_tasks_count: int = 0
    operational_tasks_version: str | None = None
    activation_hash: str | None = None
    activation_status: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    operational_tasks_preview: list[dict[str, Any]] = Field(default_factory=list)
    no_sessions_created: bool = True
    message: str | None = None
