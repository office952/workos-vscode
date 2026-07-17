"""Letters commercial-measurement contract — non-monetary quantities for CPP 7G.

TE2E / LETTERS_CANONICAL_PRODUCT_SLICE_V1.
ProductAggregate emits measurements; CPP alone turns them into money.
Forbidden: unit_price, totals, minutes, internal_cost.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

COMMERCIAL_MEASUREMENT_CONTRACT_VERSION = "letters_commercial_measurement_v1"
CommercialMeasurementStatus = Literal[
    "resolved",
    "missing_input",
    "not_applicable",
    "pending_owner",
]


class CommercialMeasurement(BaseModel):
    """One non-monetary commercial measurement for a pricing line."""

    measurement_key: str
    line_code: str
    quantity: float | None = None
    unit: str
    module_code: str | None = None
    component_code: str | None = None
    source_fact_keys: list[str] = Field(default_factory=list)
    resolution_status: CommercialMeasurementStatus = "missing_input"
    pricing_rule_code: str | None = None
    selector: dict[str, Any] = Field(default_factory=dict)
    provenance: str = "product_aggregate.commercial_measurements"
    notes: list[str] = Field(default_factory=list)


class CommercialMeasurementBundle(BaseModel):
    """Versioned bundle attached to ProductAggregate (Letters only)."""

    contract_version: str = COMMERCIAL_MEASUREMENT_CONTRACT_VERSION
    template_code: str
    measurements: list[CommercialMeasurement] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
