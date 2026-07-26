"""Versioned parity contracts (Pydantic)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from parity.confidentiality import sanitize_safe_metadata, validate_safe_metadata
from parity.enums import (
    AuthorizationConfirmationStatus,
    CapabilityClassification,
    ComparisonResult,
    DiscrepancyStatus,
    ExplicitMappingClassification,
    ParityDomain,
    ParityEventType,
    ParityMetricName,
    ParitySeverity,
)

PARITY_RESULT_CONTRACT_VERSION = "parity_result/v1"
PARITY_EVENT_CONTRACT_VERSION = "parity_event/v1"
RECONCILIATION_SHEET_CONTRACT_VERSION = "reconciliation_sheet/v1"


class ParityResultContract(BaseModel):
    """Rezultat comparat versionat pentru o discrepanță de paritate."""

    model_config = ConfigDict(extra="forbid")

    contract_version: str = Field(default=PARITY_RESULT_CONTRACT_VERSION)
    domain: ParityDomain
    entity_type: str
    entity_id: str
    employee_id: int | None = None
    operation_code: str | None = None
    resource_id: str | None = None
    canonical_source: str
    transitional_source: str
    canonical_result: Any = None
    transitional_result: Any = None
    comparison_result: ComparisonResult
    severity: ParitySeverity
    status: DiscrepancyStatus = DiscrepancyStatus.OPEN
    fingerprint: str
    observed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("contract_version")
    @classmethod
    def _require_contract_version(cls, value: str) -> str:
        if value != PARITY_RESULT_CONTRACT_VERSION:
            raise ValueError(f"unsupported contract_version: {value}")
        return value

    @field_validator("metadata")
    @classmethod
    def _validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_safe_metadata(value)


class ParityEntityReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: str
    entity_id: str
    employee_id: int | None = None
    operation_code: str | None = None
    resource_id: str | None = None


class ParitySourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_source: str
    transitional_source: str


class ParityActorReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: int | None = None
    user_id: int | None = None
    surface_id: str | None = None


class ParityEventV1(BaseModel):
    """Contract generic parity_event/v1 — nepublicat runtime în APP-AUTH-04."""

    model_config = ConfigDict(extra="forbid")

    event_type: ParityEventType
    event_version: str = Field(default=PARITY_EVENT_CONTRACT_VERSION)
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    fingerprint: str
    domain: ParityDomain
    severity: ParitySeverity
    status: DiscrepancyStatus = DiscrepancyStatus.OPEN
    entity: ParityEntityReference
    sources: ParitySourceReference
    comparison_result: ComparisonResult
    occurred_at: datetime
    actor: ParityActorReference | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_version")
    @classmethod
    def _require_event_version(cls, value: str) -> str:
        if value != PARITY_EVENT_CONTRACT_VERSION:
            raise ValueError(f"unsupported event_version: {value}")
        return value

    @field_validator("metadata")
    @classmethod
    def _validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_safe_metadata(value)

    @classmethod
    def from_parity_result(
        cls,
        *,
        event_type: ParityEventType,
        result: ParityResultContract,
        actor: ParityActorReference | None = None,
    ) -> ParityEventV1:
        return cls(
            event_type=event_type,
            fingerprint=result.fingerprint,
            domain=result.domain,
            severity=result.severity,
            status=result.status,
            entity=ParityEntityReference(
                entity_type=result.entity_type,
                entity_id=result.entity_id,
                employee_id=result.employee_id,
                operation_code=result.operation_code,
                resource_id=result.resource_id,
            ),
            sources=ParitySourceReference(
                canonical_source=result.canonical_source,
                transitional_source=result.transitional_source,
            ),
            comparison_result=result.comparison_result,
            occurred_at=result.observed_at,
            actor=actor,
            metadata=sanitize_safe_metadata(result.metadata),
        )


class ParityMetricDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ParityMetricName
    description: str
    unit: str
    cardinality: str


PARITY_METRIC_CATALOG: dict[ParityMetricName, ParityMetricDefinition] = {
    ParityMetricName.EMPLOYEES_COMPARED_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.EMPLOYEES_COMPARED_TOTAL,
        description="Angajați pentru care s-a rulat cel puțin o comparație de paritate",
        unit="count",
        cardinality="low",
    ),
    ParityMetricName.EMPLOYEES_WITH_DRIFT_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.EMPLOYEES_WITH_DRIFT_TOTAL,
        description="Angajați cu cel puțin o discrepanță deschisă",
        unit="count",
        cardinality="low",
    ),
    ParityMetricName.COMPETENCE_REGISTRY_ONLY_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.COMPETENCE_REGISTRY_ONLY_TOTAL,
        description="Competențe prezente doar în registry",
        unit="count",
        cardinality="medium",
    ),
    ParityMetricName.COMPETENCE_LEGACY_ONLY_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.COMPETENCE_LEGACY_ONLY_TOTAL,
        description="Competențe prezente doar în sursa tranzitorie",
        unit="count",
        cardinality="medium",
    ),
    ParityMetricName.MISSING_AUTHORIZATIONS_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.MISSING_AUTHORIZATIONS_TOTAL,
        description="Autorizări obligatorii lipsă în sursa canonică",
        unit="count",
        cardinality="medium",
    ),
    ParityMetricName.EXPLICIT_MAPPINGS_USED_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.EXPLICIT_MAPPINGS_USED_TOTAL,
        description="Utilizări ale mapărilor explicite",
        unit="count",
        cardinality="medium",
    ),
    ParityMetricName.MAPPINGS_WITHOUT_COMPETENCE_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.MAPPINGS_WITHOUT_COMPETENCE_TOTAL,
        description="Mapări explicite fără competență",
        unit="count",
        cardinality="low",
    ),
    ParityMetricName.MAPPINGS_WITHOUT_AUTHORIZATION_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.MAPPINGS_WITHOUT_AUTHORIZATION_TOTAL,
        description="Mapări explicite fără autorizare",
        unit="count",
        cardinality="low",
    ),
    ParityMetricName.OPERATIONS_MISSING_REQUIREMENTS_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.OPERATIONS_MISSING_REQUIREMENTS_TOTAL,
        description="Operații cu cerințe incomplete",
        unit="count",
        cardinality="low",
    ),
    ParityMetricName.ELIGIBILITY_DIFFERENCES_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.ELIGIBILITY_DIFFERENCES_TOTAL,
        description="Diferențe eligibilitate operațională vs canonică simulată",
        unit="count",
        cardinality="medium",
    ),
    ParityMetricName.LEGACY_FALLBACK_USAGE_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.LEGACY_FALLBACK_USAGE_TOTAL,
        description="Total fallback-uri legacy folosite",
        unit="count",
        cardinality="medium",
    ),
    ParityMetricName.LEGACY_READS_BY_CONSUMER_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.LEGACY_READS_BY_CONSUMER_TOTAL,
        description="Citiri legacy grupate pe consumator",
        unit="count",
        cardinality="low",
    ),
    ParityMetricName.LEGACY_WRITES_BY_WRITER_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.LEGACY_WRITES_BY_WRITER_TOTAL,
        description="Scrieri legacy grupate pe writer",
        unit="count",
        cardinality="low",
    ),
    ParityMetricName.EXECUTION_SURFACE_DIFFERENCES_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.EXECUTION_SURFACE_DIFFERENCES_TOTAL,
        description="Diferențe între suprafețe de execuție",
        unit="count",
        cardinality="medium",
    ),
    ParityMetricName.INCOMPATIBLE_SESSIONS_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.INCOMPATIBLE_SESSIONS_TOTAL,
        description="Sesiuni incompatibile cu alocare/eligibilitate",
        unit="count",
        cardinality="medium",
    ),
    ParityMetricName.EMPLOYEE_RECONCILIATION_DIFFERENCES_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.EMPLOYEE_RECONCILIATION_DIFFERENCES_TOTAL,
        description="Discrepanțe deschise în fișa de reconciliere angajat",
        unit="count",
        cardinality="low",
    ),
    ParityMetricName.UNRESOLVED_DISCREPANCIES_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.UNRESOLVED_DISCREPANCIES_TOTAL,
        description="Discrepanțe nerezolvate",
        unit="count",
        cardinality="bounded",
    ),
    ParityMetricName.RESOLVED_DISCREPANCIES_TOTAL: ParityMetricDefinition(
        name=ParityMetricName.RESOLVED_DISCREPANCIES_TOTAL,
        description="Discrepanțe rezolvate",
        unit="count",
        cardinality="bounded",
    ),
    ParityMetricName.DISCREPANCY_AGE_SECONDS: ParityMetricDefinition(
        name=ParityMetricName.DISCREPANCY_AGE_SECONDS,
        description="Vârsta medie a discrepanțelor deschise",
        unit="seconds",
        cardinality="single_gauge",
    ),
    ParityMetricName.MAXIMUM_ACTIVE_SEVERITY: ParityMetricDefinition(
        name=ParityMetricName.MAXIMUM_ACTIVE_SEVERITY,
        description="Severitate maximă activă pe discrepanțe deschise",
        unit="severity_score",
        cardinality="single_gauge",
    ),
}


class ReconciliationCapabilityEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_code: str
    classification: CapabilityClassification = CapabilityClassification.NECONFIRMAT


class ReconciliationAuthorizationEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_code: str | None = None
    workcenter_code: str | None = None
    status: AuthorizationConfirmationStatus = AuthorizationConfirmationStatus.NECONFIRMATA


class ReconciliationExplicitMappingEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_code: str
    classification: ExplicitMappingClassification
    competence_match: bool | None = None
    authorization_match: bool | None = None


class ReconciliationSheetContract(BaseModel):
    """Fișă generică de reconciliere angajat — fără date populate runtime."""

    model_config = ConfigDict(extra="forbid")

    contract_version: str = Field(default=RECONCILIATION_SHEET_CONTRACT_VERSION)
    employee_id: int
    display_name: str
    capabilities: list[ReconciliationCapabilityEntry] = Field(default_factory=list)
    canonical_entries: dict[str, Any] = Field(default_factory=dict)
    transitional_entries: dict[str, Any] = Field(default_factory=dict)
    explicit_mappings: list[ReconciliationExplicitMappingEntry] = Field(default_factory=list)
    authorizations: list[ReconciliationAuthorizationEntry] = Field(default_factory=list)
    affected_operations: list[str] = Field(default_factory=list)
    required_confirmations: list[str] = Field(default_factory=list)
    reconciliation_status: DiscrepancyStatus = DiscrepancyStatus.CONFIRMATION_REQUIRED

    @field_validator("canonical_entries", "transitional_entries")
    @classmethod
    def _validate_entry_maps(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_safe_metadata(value)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
