"""OrderSnapshotV2 planning/readiness adapter contract (W5-T03)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PLANNING_READINESS_CONTRACT_VERSION = "order_snapshot_v2_planning_readiness/v1"

ReadinessAuthoritySource = Literal[
    "FROZEN_ORDER_SNAPSHOT_V2",
    "LEGACY_ORDER_INPUT",
    "BLOCKED_MISSING_ORDER_SNAPSHOT_V2",
]

PREPARATION_READINESS_KEYS: frozenset[str] = frozenset(
    {
        "mounting_template_enabled",
        "mounting_template_material_type",
        "mounting_template_area_m2",
        "face_finish_type",
        "face_vinyl_color_code",
        "face_vinyl_roll_width_mm",
        "face_vinyl_enabled",
        "mounting_system",
        "metal_support_required",
    }
)


class OrderSnapshotV2PlanningReadinessInput(BaseModel):
    """Smallest frozen planning/readiness projection for task-start gates."""

    contract_version: str = PLANNING_READINESS_CONTRACT_VERSION
    authority_source: ReadinessAuthoritySource
    order_id: int
    snapshot_code: str | None = None
    content_hash: str | None = None
    quote_snapshot_v2_id: int | None = None
    frozen_task_identity_version: str | None = None
    preparation_input: dict = Field(default_factory=dict)

    def as_quote_input_compat(self) -> dict:
        """Flat dict consumed by task_preparation_readiness_service gates."""
        payload = dict(self.preparation_input)
        payload["_planning_readiness_authority"] = self.authority_source
        payload["_planning_readiness_contract"] = self.contract_version
        if self.snapshot_code:
            payload["_order_snapshot_code"] = self.snapshot_code
        return payload
