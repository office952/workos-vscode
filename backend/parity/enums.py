"""Canonical enums for runtime parity instrumentation foundation."""

from __future__ import annotations

from core.enums import AutoStrEnum


class ParityDomain(AutoStrEnum):
    EMPLOYEE_IDENTITY = "employee_identity"
    COMPETENCE = "competence"
    AUTHORIZATION = "authorization"
    WORKCENTER = "workcenter"
    RESOURCE = "resource"
    EXPLICIT_MAPPING = "explicit_mapping"
    ELIGIBILITY = "eligibility"
    EXECUTION_SURFACE = "execution_surface"
    ASSIGNMENT_WRITER = "assignment_writer"
    EXECUTION_SESSION = "execution_session"
    ATTENDANCE_COMPARISON = "attendance_comparison"
    EMPLOYEE_RECONCILIATION = "employee_reconciliation"


class ComparisonResult(AutoStrEnum):
    MATCH = "match"
    CANONICAL_ONLY = "canonical_only"
    TRANSITIONAL_ONLY = "transitional_only"
    VALUE_CONFLICT = "value_conflict"
    OPERATIONAL_ELIGIBLE_CANONICAL_INELIGIBLE = "operational_eligible_canonical_ineligible"
    OPERATIONAL_INELIGIBLE_CANONICAL_ELIGIBLE = "operational_ineligible_canonical_eligible"
    MISSING_REQUIRED_COMPETENCE = "missing_required_competence"
    MISSING_REQUIRED_AUTHORIZATION = "missing_required_authorization"
    MISSING_OPERATION_REQUIREMENT = "missing_operation_requirement"
    TRANSITIONAL_EXCEPTION_ACTIVE = "transitional_exception_active"
    LEGACY_FALLBACK_USED = "legacy_fallback_used"
    UNKNOWN_OR_UNCOMPUTABLE = "unknown_or_uncomputable"


class ParitySeverity(AutoStrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class DiscrepancyStatus(AutoStrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    CONFIRMATION_REQUIRED = "confirmation_required"
    TECHNICAL_VALIDATION_REQUIRED = "technical_validation_required"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    REOPENED = "reopened"


class ParityEventType(AutoStrEnum):
    EMPLOYEE_IDENTITY_PARITY_DIFFERENCE = "employee_identity_parity_difference"
    COMPETENCE_PARITY_DIFFERENCE = "competence_parity_difference"
    AUTHORIZATION_PARITY_DIFFERENCE = "authorization_parity_difference"
    WORKCENTER_PARITY_DIFFERENCE = "workcenter_parity_difference"
    RESOURCE_PARITY_DIFFERENCE = "resource_parity_difference"
    ELIGIBILITY_PARITY_DIFFERENCE = "eligibility_parity_difference"
    LEGACY_FALLBACK_USED = "legacy_fallback_used"
    EXPLICIT_MAPPING_USED = "explicit_mapping_used"
    EXECUTION_SURFACE_PARITY_DIFFERENCE = "execution_surface_parity_difference"
    ASSIGNMENT_WRITER_OUTSIDE_AUTHORITY = "assignment_writer_outside_authority"
    SESSION_AUTHORITY_DIFFERENCE = "session_authority_difference"
    ATTENDANCE_EXECUTION_DIFFERENCE = "attendance_execution_difference"


class ParityMetricName(AutoStrEnum):
    EMPLOYEES_COMPARED_TOTAL = "employees_compared_total"
    EMPLOYEES_WITH_DRIFT_TOTAL = "employees_with_drift_total"
    COMPETENCE_REGISTRY_ONLY_TOTAL = "competence_registry_only_total"
    COMPETENCE_LEGACY_ONLY_TOTAL = "competence_legacy_only_total"
    MISSING_AUTHORIZATIONS_TOTAL = "missing_authorizations_total"
    EXPLICIT_MAPPINGS_USED_TOTAL = "explicit_mappings_used_total"
    MAPPINGS_WITHOUT_COMPETENCE_TOTAL = "mappings_without_competence_total"
    MAPPINGS_WITHOUT_AUTHORIZATION_TOTAL = "mappings_without_authorization_total"
    OPERATIONS_MISSING_REQUIREMENTS_TOTAL = "operations_missing_requirements_total"
    ELIGIBILITY_DIFFERENCES_TOTAL = "eligibility_differences_total"
    LEGACY_FALLBACK_USAGE_TOTAL = "legacy_fallback_usage_total"
    LEGACY_READS_BY_CONSUMER_TOTAL = "legacy_reads_by_consumer_total"
    LEGACY_WRITES_BY_WRITER_TOTAL = "legacy_writes_by_writer_total"
    EXECUTION_SURFACE_DIFFERENCES_TOTAL = "execution_surface_differences_total"
    INCOMPATIBLE_SESSIONS_TOTAL = "incompatible_sessions_total"
    EMPLOYEE_RECONCILIATION_DIFFERENCES_TOTAL = "employee_reconciliation_differences_total"
    UNRESOLVED_DISCREPANCIES_TOTAL = "unresolved_discrepancies_total"
    RESOLVED_DISCREPANCIES_TOTAL = "resolved_discrepancies_total"
    DISCREPANCY_AGE_SECONDS = "discrepancy_age_seconds"
    MAXIMUM_ACTIVE_SEVERITY = "maximum_active_severity"


class ExplicitMappingClassification(AutoStrEnum):
    SELECTIE_DINTRE_ELIGIBILI = "selectie_dintre_eligibili"
    RESTRANGERE_ELIGIBILITATE = "restrangere_eligibilitate"
    COMPATIBILITATE_TRANZITORIE = "compatibilitate_tranzitorie"
    ADAUGARE_FARA_COMPETENTA = "adaugare_fara_competenta"
    ADAUGARE_FARA_AUTORIZARE = "adaugare_fara_autorizare"
    SCOP_NECUNOSCUT = "scop_necunoscut"


class CapabilityClassification(AutoStrEnum):
    AUTONOM = "autonom"
    ASISTAT = "asistat"
    NU_EXECUTA = "nu_executa"
    NECONFIRMAT = "neconfirmat"


class AuthorizationConfirmationStatus(AutoStrEnum):
    CONFIRMATA = "confirmata"
    LIPSA = "lipsa"
    EXPIRATA = "expirata"
    NECONFIRMATA = "neconfirmata"
    NU_ESTE_NECESARA = "nu_este_necesara"
