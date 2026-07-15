"""Authorization set pure comparator."""

from __future__ import annotations

from typing import Any

from parity.comparators.generic import evaluate_parity_comparison
from parity.contracts import ParityResultContract
from parity.enums import ComparisonResult, ParityDomain
from parity.normalization import normalize_string_set


def compare_authorization_sets(
    *,
    employee_id: int,
    operation_code: str,
    canonical_authorizations: Any,
    transitional_authorizations: Any,
    required_authorizations: Any | None = None,
    canonical_source: str = "employee_resource_authorizations",
    transitional_source: str = "legacy_authorization_proxy",
) -> ParityResultContract:
    canonical_set = normalize_string_set(canonical_authorizations)
    transitional_set = normalize_string_set(transitional_authorizations)
    required_set = normalize_string_set(required_authorizations) if required_authorizations is not None else frozenset()

    if required_set and not canonical_set.intersection(required_set):
        comparison_result = ComparisonResult.MISSING_REQUIRED_AUTHORIZATION
    elif canonical_set == transitional_set:
        comparison_result = ComparisonResult.MATCH
    elif canonical_set and not transitional_set:
        comparison_result = ComparisonResult.CANONICAL_ONLY
    elif transitional_set and not canonical_set:
        comparison_result = ComparisonResult.TRANSITIONAL_ONLY
    else:
        comparison_result = ComparisonResult.VALUE_CONFLICT

    return evaluate_parity_comparison(
        domain=ParityDomain.AUTHORIZATION,
        entity_type="employee_operation",
        entity_id=f"{employee_id}:{operation_code}",
        employee_id=employee_id,
        operation_code=operation_code,
        canonical_source=canonical_source,
        transitional_source=transitional_source,
        canonical_result=sorted(canonical_set),
        transitional_result=sorted(transitional_set),
        comparison_result=comparison_result,
    )
