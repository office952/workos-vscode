from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class TechnicalReadinessStatus(str, Enum):
    DRAFT = "DRAFT"
    TECHNICALLY_READY = "TECHNICALLY_READY"


class PricingReadinessStatus(str, Enum):
    PRICING_INCOMPLETE = "PRICING_INCOMPLETE"
    PRICING_READY = "PRICING_READY"


class ExecutionReadinessStatus(str, Enum):
    EXECUTION_INCOMPLETE = "EXECUTION_INCOMPLETE"
    EXECUTION_READY = "EXECUTION_READY"


class CommercialReadinessStatus(str, Enum):
    INTERNAL_ONLY = "INTERNAL_ONLY"
    OFFERABLE = "OFFERABLE"
    DEPRECATED = "DEPRECATED"


class ReadinessRollup(str, Enum):
    READY = "READY"
    PARTIALLY_READY = "PARTIALLY_READY"
    BLOCKED = "BLOCKED"
    INTERNAL = "INTERNAL"
    DEPRECATED = "DEPRECATED"


ReadinessDimensionName = Literal["technical", "pricing", "execution", "commercial"]
ReadinessSeverity = Literal["blocking", "warning", "diagnostic"]


class ProductSystemReadinessBlocker(BaseModel):
    code: str
    dimension: ReadinessDimensionName
    severity: ReadinessSeverity = "blocking"
    owner: str
    message: str
    source_code: str | None = None
    target_route: str | None = None


class ProductSystemReadinessDimension(BaseModel):
    status: str
    blockers: list[ProductSystemReadinessBlocker] = Field(default_factory=list)


class ProductSystemTemplateCapabilities(BaseModel):
    root_offerable: bool
    linked_child_offerable: bool
    internal_only: bool


class ProductSystemTemplateReadiness(BaseModel):
    technical: ProductSystemReadinessDimension
    pricing: ProductSystemReadinessDimension
    execution: ProductSystemReadinessDimension
    commercial: ProductSystemReadinessDimension
    rollup: ReadinessRollup
