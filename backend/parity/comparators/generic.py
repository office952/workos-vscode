"""Generic pure parity evaluator."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from parity.contracts import ParityResultContract, utc_now
from parity.enums import ComparisonResult, DiscrepancyStatus, ParityDomain, ParitySeverity
from parity.fingerprint import FingerprintInput, compute_fingerprint
from parity.normalization import empty_normalized, normalize_for_comparison, values_equal
from parity.severity import suggest_severity


def compare_normalized_values(canonical: Any, transitional: Any) -> ComparisonResult:
    if empty_normalized(canonical) and empty_normalized(transitional):
        return ComparisonResult.UNKNOWN_OR_UNCOMPUTABLE
    if empty_normalized(canonical) and not empty_normalized(transitional):
        return ComparisonResult.TRANSITIONAL_ONLY
    if not empty_normalized(canonical) and empty_normalized(transitional):
        return ComparisonResult.CANONICAL_ONLY
    if values_equal(canonical, transitional):
        return ComparisonResult.MATCH
    return ComparisonResult.VALUE_CONFLICT


def evaluate_parity_comparison(
    *,
    domain: ParityDomain,
    entity_type: str,
    entity_id: str,
    canonical_source: str,
    transitional_source: str,
    canonical_result: Any,
    transitional_result: Any,
    employee_id: int | None = None,
    operation_code: str | None = None,
    resource_id: str | None = None,
    comparison_result: ComparisonResult | None = None,
    severity: ParitySeverity | None = None,
    status: DiscrepancyStatus = DiscrepancyStatus.OPEN,
    metadata: dict[str, Any] | None = None,
    observed_at: datetime | None = None,
) -> ParityResultContract:
    resolved_comparison = comparison_result or compare_normalized_values(
        canonical_result,
        transitional_result,
    )
    resolved_severity = severity or suggest_severity(
        domain=domain,
        comparison_result=resolved_comparison,
    )
    fingerprint = compute_fingerprint(
        FingerprintInput(
            domain=domain.value,
            entity_type=entity_type,
            entity_id=entity_id,
            employee_id=employee_id,
            operation_code=operation_code,
            resource_id=resource_id,
            canonical_value=canonical_result,
            transitional_value=transitional_result,
        )
    )
    return ParityResultContract(
        domain=domain,
        entity_type=entity_type,
        entity_id=entity_id,
        employee_id=employee_id,
        operation_code=operation_code,
        resource_id=resource_id,
        canonical_source=canonical_source,
        transitional_source=transitional_source,
        canonical_result=normalize_for_comparison(canonical_result),
        transitional_result=normalize_for_comparison(transitional_result),
        comparison_result=resolved_comparison,
        severity=resolved_severity,
        status=status,
        fingerprint=fingerprint,
        observed_at=observed_at or utc_now(),
        metadata=metadata or {},
    )
