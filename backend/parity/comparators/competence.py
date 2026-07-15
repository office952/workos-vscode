"""Competence set pure comparator."""

from __future__ import annotations

from typing import Any

from parity.comparators.generic import compare_normalized_values, evaluate_parity_comparison
from parity.contracts import ParityResultContract
from parity.enums import ComparisonResult, ParityDomain
from parity.normalization import normalize_string_set


def compare_competence_sets(
    *,
    employee_id: int,
    canonical_skills: Any,
    transitional_skills: Any,
    canonical_source: str = "employee_skill_authorizations",
    transitional_source: str = "employees.skills",
) -> ParityResultContract:
    canonical_set = normalize_string_set(canonical_skills)
    transitional_set = normalize_string_set(transitional_skills)
    base = compare_normalized_values(sorted(canonical_set), sorted(transitional_set))

    if base == ComparisonResult.MATCH:
        comparison_result = ComparisonResult.MATCH
    elif canonical_set and not transitional_set:
        comparison_result = ComparisonResult.CANONICAL_ONLY
    elif transitional_set and not canonical_set:
        comparison_result = ComparisonResult.TRANSITIONAL_ONLY
    elif canonical_set - transitional_set and not transitional_set - canonical_set:
        comparison_result = ComparisonResult.CANONICAL_ONLY
    elif transitional_set - canonical_set and not canonical_set - transitional_set:
        comparison_result = ComparisonResult.TRANSITIONAL_ONLY
    else:
        comparison_result = ComparisonResult.VALUE_CONFLICT

    return evaluate_parity_comparison(
        domain=ParityDomain.COMPETENCE,
        entity_type="employee",
        entity_id=str(employee_id),
        employee_id=employee_id,
        canonical_source=canonical_source,
        transitional_source=transitional_source,
        canonical_result=sorted(canonical_set),
        transitional_result=sorted(transitional_set),
        comparison_result=comparison_result,
    )
