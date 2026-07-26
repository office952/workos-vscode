"""Resource identity pure comparator."""

from __future__ import annotations

from parity.comparators.generic import evaluate_parity_comparison
from parity.contracts import ParityResultContract
from parity.enums import ComparisonResult, ParityDomain
from parity.normalization import normalize_code


def compare_resource_identity(
    *,
    canonical_code: str | None,
    transitional_code: str | None,
    canonical_metadata: dict | None = None,
    transitional_metadata: dict | None = None,
    canonical_source: str = "machines",
    transitional_source: str = "registry.resources",
) -> ParityResultContract:
    left = normalize_code(canonical_code)
    right = normalize_code(transitional_code)
    if left is None and right is None:
        comparison_result = ComparisonResult.UNKNOWN_OR_UNCOMPUTABLE
    elif left == right:
        if canonical_metadata and transitional_metadata and canonical_metadata != transitional_metadata:
            comparison_result = ComparisonResult.VALUE_CONFLICT
        else:
            comparison_result = ComparisonResult.MATCH
    elif left is None:
        comparison_result = ComparisonResult.TRANSITIONAL_ONLY
    elif right is None:
        comparison_result = ComparisonResult.CANONICAL_ONLY
    else:
        comparison_result = ComparisonResult.VALUE_CONFLICT

    entity_id = left or right or "unknown"
    return evaluate_parity_comparison(
        domain=ParityDomain.RESOURCE,
        entity_type="resource",
        entity_id=entity_id,
        resource_id=entity_id,
        canonical_source=canonical_source,
        transitional_source=transitional_source,
        canonical_result={"code": left, "metadata": canonical_metadata or {}},
        transitional_result={"code": right, "metadata": transitional_metadata or {}},
        comparison_result=comparison_result,
    )
