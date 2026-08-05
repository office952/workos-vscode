"""Resource State R7 — domain configuration command contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ResourceDomain = Literal[
    "SCHEDULING", "MACHINE_RESERVATION", "CAPACITY_ALLOCATION"
]
ConfigurationStatus = Literal["ACTIVE", "DISABLED"]
ConfigurationOperation = Literal[
    "CONFIGURE_DOMAIN", "ACTIVATE_DOMAIN", "DISABLE_DOMAIN"
]


class ResourceDomainConfigurationCommand(BaseModel):
    target_status: ConfigurationStatus
    expected_version: int = Field(
        ...,
        ge=0,
        description="0 when creating; otherwise must match current version (CAS).",
    )
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)
    application_scope_key: str = Field(default="application", max_length=64)


class ResourceDomainConfigurationResult(BaseModel):
    domain: ResourceDomain
    configuration_id: int
    status: ConfigurationStatus
    version: int
    operation: ConfigurationOperation
    transition_id: str
    previous_status: ConfigurationStatus | None = None
    previous_version: int | None = None
    already_applied: bool = False
    configured_at: datetime | None = None
    disabled_at: datetime | None = None
    evaluated_hint: str = Field(
        default="",
        description="Read-evaluator hint after command (not a persisted state).",
    )
