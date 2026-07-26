"""Eligibility result pure comparator."""

from __future__ import annotations

from parity.comparators.generic import evaluate_parity_comparison
from parity.contracts import ParityResultContract
from parity.enums import ComparisonResult, ParityDomain


def compare_eligibility_results(
    *,
    employee_id: int,
    operation_code: str,
    operational_eligible: bool | None,
    canonical_eligible: bool | None,
    canonical_source: str = "canonical_eligibility_simulation",
    transitional_source: str = "operational_eligibility",
) -> ParityResultContract:
    if operational_eligible is None or canonical_eligible is None:
        comparison_result = ComparisonResult.UNKNOWN_OR_UNCOMPUTABLE
    elif operational_eligible == canonical_eligible:
        comparison_result = ComparisonResult.MATCH
    elif operational_eligible and not canonical_eligible:
        comparison_result = ComparisonResult.OPERATIONAL_ELIGIBLE_CANONICAL_INELIGIBLE
    else:
        comparison_result = ComparisonResult.OPERATIONAL_INELIGIBLE_CANONICAL_ELIGIBLE

    return evaluate_parity_comparison(
        domain=ParityDomain.ELIGIBILITY,
        entity_type="employee_operation_eligibility",
        entity_id=f"{employee_id}:{operation_code}",
        employee_id=employee_id,
        operation_code=operation_code,
        canonical_source=canonical_source,
        transitional_source=transitional_source,
        canonical_result={"eligible": canonical_eligible},
        transitional_result={"eligible": operational_eligible},
        comparison_result=comparison_result,
    )
