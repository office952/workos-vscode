"""Workcenter code pure comparator."""

from __future__ import annotations

from parity.comparators.generic import evaluate_parity_comparison
from parity.contracts import ParityResultContract
from parity.enums import ComparisonResult, ParityDomain
from parity.normalization import normalize_code


def compare_workcenter_codes(
    *,
    canonical_code: str | None,
    transitional_code: str | None,
    canonical_source: str = "operational_registry.workcenters",
    transitional_source: str = "frontend.constants",
) -> ParityResultContract:
    left = normalize_code(canonical_code)
    right = normalize_code(transitional_code)
    if left is None or right is None:
        comparison_result = ComparisonResult.UNKNOWN_OR_UNCOMPUTABLE
    elif left == right:
        comparison_result = ComparisonResult.MATCH
    else:
        comparison_result = ComparisonResult.VALUE_CONFLICT

    entity_id = left or right or "unknown"
    return evaluate_parity_comparison(
        domain=ParityDomain.WORKCENTER,
        entity_type="workcenter",
        entity_id=entity_id,
        canonical_source=canonical_source,
        transitional_source=transitional_source,
        canonical_result=left,
        transitional_result=right,
        comparison_result=comparison_result,
    )
