from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ReadinessStatus = Literal["ready", "needs_review", "blocked", "draft", "deprecated"]


class ReadinessSectionDTO(BaseModel):
    status: ReadinessStatus
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReadinessPolicyDTO(BaseModel):
    authority: Literal["backend"] = "backend"
    compute_mode: Literal["read_only"] = "read_only"
    quote_gate: Literal["enforced"] = "enforced"
    order_snapshot: Literal["quote_snapshot_frozen"] = "quote_snapshot_frozen"


class ProductReadinessDTO(BaseModel):
    entity_type: Literal["blueprint"]
    entity_id: str
    blueprint_id: str
    overall_status: ReadinessStatus
    ready_for_quote: bool
    technical_readiness: ReadinessSectionDTO
    costengine_readiness: ReadinessSectionDTO
    document_output_readiness: ReadinessSectionDTO
    visual_prompt_readiness: ReadinessSectionDTO
    execution_preparation_readiness: ReadinessSectionDTO
    policy: ReadinessPolicyDTO = Field(default_factory=ReadinessPolicyDTO)
    source: Literal["backend"] = "backend"
    contract_version: str = "2026-05-15"
