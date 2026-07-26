"""Employee identity pure comparator."""

from __future__ import annotations

from typing import Any

from parity.comparators.generic import evaluate_parity_comparison
from parity.contracts import ParityResultContract
from parity.enums import ComparisonResult, ParityDomain


def compare_employee_identity(
    *,
    employee_id: int,
    canonical_identity: dict[str, Any],
    transitional_identity: dict[str, Any],
    canonical_source: str = "employees.user_id",
    transitional_source: str = "session.actor",
) -> ParityResultContract:
    comparison_result = ComparisonResult.MATCH
    canonical_user = canonical_identity.get("user_id")
    transitional_user = transitional_identity.get("user_id")
    canonical_actor = canonical_identity.get("actor_employee_id")
    transitional_actor = transitional_identity.get("actor_employee_id")

    if canonical_user is None and transitional_user is not None:
        comparison_result = ComparisonResult.TRANSITIONAL_ONLY
    elif canonical_user is not None and transitional_user is None:
        comparison_result = ComparisonResult.CANONICAL_ONLY
    elif canonical_user != transitional_user:
        comparison_result = ComparisonResult.VALUE_CONFLICT
    elif canonical_actor is not None and transitional_actor is not None and canonical_actor != transitional_actor:
        comparison_result = ComparisonResult.VALUE_CONFLICT

    return evaluate_parity_comparison(
        domain=ParityDomain.EMPLOYEE_IDENTITY,
        entity_type="employee",
        entity_id=str(employee_id),
        employee_id=employee_id,
        canonical_source=canonical_source,
        transitional_source=transitional_source,
        canonical_result=canonical_identity,
        transitional_result=transitional_identity,
        comparison_result=comparison_result,
    )
