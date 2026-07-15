"""Explicit mapping pure comparator."""

from __future__ import annotations

from parity.comparators.generic import evaluate_parity_comparison
from parity.contracts import ParityResultContract
from parity.enums import ComparisonResult, ExplicitMappingClassification, ParityDomain


def compare_explicit_mapping(
    *,
    employee_id: int,
    operation_code: str,
    classification: ExplicitMappingClassification,
    has_registry_competence: bool,
    has_registry_authorization: bool,
) -> ParityResultContract:
    if classification == ExplicitMappingClassification.ADAUGARE_FARA_COMPETENTA:
        comparison_result = ComparisonResult.MISSING_REQUIRED_COMPETENCE
    elif classification == ExplicitMappingClassification.ADAUGARE_FARA_AUTORIZARE:
        comparison_result = ComparisonResult.MISSING_REQUIRED_AUTHORIZATION
    elif has_registry_competence and has_registry_authorization:
        comparison_result = ComparisonResult.MATCH
    else:
        comparison_result = ComparisonResult.TRANSITIONAL_EXCEPTION_ACTIVE

    return evaluate_parity_comparison(
        domain=ParityDomain.EXPLICIT_MAPPING,
        entity_type="operation_employee_mapping",
        entity_id=f"{operation_code}:{employee_id}",
        employee_id=employee_id,
        operation_code=operation_code,
        canonical_source="operation_employee_authorizations",
        transitional_source="hybrid_eligibility_path",
        canonical_result={
            "classification": classification.value,
            "has_registry_competence": has_registry_competence,
            "has_registry_authorization": has_registry_authorization,
        },
        transitional_result={"explicit_mapping_active": True},
        comparison_result=comparison_result,
        metadata={"classification": classification.value},
    )
