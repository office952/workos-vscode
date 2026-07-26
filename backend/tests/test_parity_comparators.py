"""Domain comparator tests."""

from __future__ import annotations

from parity.comparators import (
    compare_authorization_sets,
    compare_competence_sets,
    compare_eligibility_results,
    compare_employee_identity,
    compare_explicit_mapping,
    compare_resource_identity,
    compare_workcenter_codes,
)
from parity.comparators.generic import compare_normalized_values, evaluate_parity_comparison
from parity.enums import (
    ComparisonResult,
    ExplicitMappingClassification,
    ParityDomain,
    ParitySeverity,
)


def test_generic_match():
    assert compare_normalized_values(["A"], ["A"]) == ComparisonResult.MATCH


def test_competence_registry_only():
    result = compare_competence_sets(
        employee_id=4,
        canonical_skills=["SK_PRINT_OPERATOR"],
        transitional_skills=[],
    )
    assert result.comparison_result == ComparisonResult.CANONICAL_ONLY
    assert result.domain == ParityDomain.COMPETENCE


def test_competence_legacy_only():
    result = compare_competence_sets(
        employee_id=4,
        canonical_skills=[],
        transitional_skills=["SK_ASSEMBLY", "SK_ELECTRICIAN"],
    )
    assert result.comparison_result == ComparisonResult.TRANSITIONAL_ONLY


def test_competence_conflict():
    result = compare_competence_sets(
        employee_id=4,
        canonical_skills=["SK_PRINT_OPERATOR"],
        transitional_skills=["SK_ASSEMBLY"],
    )
    assert result.comparison_result == ComparisonResult.VALUE_CONFLICT
    assert result.severity == ParitySeverity.HIGH


def test_competence_duplicate_order_independent():
    left = compare_competence_sets(
        employee_id=1,
        canonical_skills=["SK_A", "SK_B"],
        transitional_skills=["SK_B", "SK_A"],
    )
    right = compare_competence_sets(
        employee_id=1,
        canonical_skills=["SK_B", "SK_A"],
        transitional_skills=["SK_A", "SK_B"],
    )
    assert left.comparison_result == ComparisonResult.MATCH
    assert left.fingerprint == right.fingerprint


def test_authorization_missing_required():
    result = compare_authorization_sets(
        employee_id=4,
        operation_code="cnc_routing",
        canonical_authorizations=[],
        transitional_authorizations=["MCH-CNC-4020"],
        required_authorizations=["MCH-CNC-4020"],
    )
    assert result.comparison_result == ComparisonResult.MISSING_REQUIRED_AUTHORIZATION
    assert result.severity == ParitySeverity.CRITICAL


def test_workcenter_alias_mismatch():
    result = compare_workcenter_codes(
        canonical_code="WC_CNC",
        transitional_code="WC_CNC_ROUTING",
    )
    assert result.comparison_result == ComparisonResult.VALUE_CONFLICT


def test_resource_metadata_mismatch():
    result = compare_resource_identity(
        canonical_code="MCH-CNC-4020",
        transitional_code="MCH-CNC-4020",
        canonical_metadata={"name": "CNC 4020"},
        transitional_metadata={"name": "CNC Router"},
    )
    assert result.comparison_result == ComparisonResult.VALUE_CONFLICT


def test_eligibility_difference_operational_eligible():
    result = compare_eligibility_results(
        employee_id=4,
        operation_code="assembly",
        operational_eligible=True,
        canonical_eligible=False,
    )
    assert result.comparison_result == ComparisonResult.OPERATIONAL_ELIGIBLE_CANONICAL_INELIGIBLE
    assert result.severity == ParitySeverity.HIGH


def test_eligibility_unknown_when_missing():
    result = compare_eligibility_results(
        employee_id=4,
        operation_code="assembly",
        operational_eligible=None,
        canonical_eligible=False,
    )
    assert result.comparison_result == ComparisonResult.UNKNOWN_OR_UNCOMPUTABLE


def test_explicit_mapping_without_competence():
    result = compare_explicit_mapping(
        employee_id=4,
        operation_code="assembly",
        classification=ExplicitMappingClassification.ADAUGARE_FARA_COMPETENTA,
        has_registry_competence=False,
        has_registry_authorization=True,
    )
    assert result.comparison_result == ComparisonResult.MISSING_REQUIRED_COMPETENCE


def test_employee_identity_conflict():
    result = compare_employee_identity(
        employee_id=4,
        canonical_identity={"user_id": 10, "actor_employee_id": 4},
        transitional_identity={"user_id": 11, "actor_employee_id": 4},
    )
    assert result.comparison_result == ComparisonResult.VALUE_CONFLICT
    assert result.severity == ParitySeverity.CRITICAL


def test_evaluate_parity_comparison_builds_contract():
    result = evaluate_parity_comparison(
        domain=ParityDomain.RESOURCE,
        entity_type="resource",
        entity_id="MCH-1",
        canonical_source="machines",
        transitional_source="mock",
        canonical_result="MCH-1",
        transitional_result="MCH-2",
    )
    assert result.fingerprint.startswith("parity_fp_v1:")
    assert result.contract_version == "parity_result/v1"
