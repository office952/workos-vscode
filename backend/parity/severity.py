"""Pure severity suggestion rules for parity comparison results."""

from __future__ import annotations

from parity.enums import ComparisonResult, ParityDomain, ParitySeverity


def suggest_severity(
    *,
    domain: ParityDomain,
    comparison_result: ComparisonResult,
) -> ParitySeverity:
    if comparison_result == ComparisonResult.MATCH:
        return ParitySeverity.INFORMATIONAL

    if comparison_result in {
        ComparisonResult.MISSING_REQUIRED_AUTHORIZATION,
    }:
        return ParitySeverity.CRITICAL

    if domain == ParityDomain.EMPLOYEE_IDENTITY and comparison_result == ComparisonResult.VALUE_CONFLICT:
        return ParitySeverity.CRITICAL

    if comparison_result in {
        ComparisonResult.OPERATIONAL_ELIGIBLE_CANONICAL_INELIGIBLE,
        ComparisonResult.OPERATIONAL_INELIGIBLE_CANONICAL_ELIGIBLE,
    }:
        return ParitySeverity.HIGH

    if comparison_result == ComparisonResult.MISSING_REQUIRED_COMPETENCE:
        return ParitySeverity.HIGH

    if comparison_result == ComparisonResult.LEGACY_FALLBACK_USED:
        return ParitySeverity.MEDIUM

    if comparison_result in {
        ComparisonResult.CANONICAL_ONLY,
        ComparisonResult.TRANSITIONAL_ONLY,
        ComparisonResult.VALUE_CONFLICT,
    }:
        if domain in {ParityDomain.COMPETENCE, ParityDomain.AUTHORIZATION, ParityDomain.ELIGIBILITY}:
            return ParitySeverity.HIGH
        if domain in {ParityDomain.RESOURCE, ParityDomain.WORKCENTER}:
            return ParitySeverity.MEDIUM
        return ParitySeverity.LOW

    if comparison_result == ComparisonResult.TRANSITIONAL_EXCEPTION_ACTIVE:
        return ParitySeverity.MEDIUM

    if comparison_result == ComparisonResult.MISSING_OPERATION_REQUIREMENT:
        return ParitySeverity.MEDIUM

    if comparison_result == ComparisonResult.UNKNOWN_OR_UNCOMPUTABLE:
        return ParitySeverity.INFORMATIONAL

    return ParitySeverity.INFORMATIONAL
