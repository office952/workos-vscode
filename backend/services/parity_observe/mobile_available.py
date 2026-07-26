"""Employee Mobile available — observe-only integration."""

from __future__ import annotations

import logging
from typing import Any, List

from parity.comparators.competence import compare_competence_sets
from parity.comparators.eligibility import compare_eligibility_results
from parity.comparators.explicit_mapping import compare_explicit_mapping
from parity.enums import ComparisonResult, ExplicitMappingClassification, ParityEventType
from services.operational_registry_service import OperationalRegistryService
from services.parity_observe.config import parity_domain_enabled, parity_observe_is_enabled
from services.parity_observe.shadow_data import load_employee_parity_snapshot, simulate_canonical_eligibility
from services.parity_observe.structured_log import emit_parity_observation
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_CONSUMER = "employee_mobile_available"


async def observe_mobile_available_tasks(
    db: AsyncSession,
    employee_id: int,
    available_rows: List[dict],
) -> None:
    """Observe parity after operational available list is finalized. Does not mutate rows."""
    if not parity_observe_is_enabled():
        return
    try:
        await _observe_mobile_available_tasks(db, employee_id, available_rows)
    except Exception:
        logger.warning("parity_observe_mobile_available_suppressed", exc_info=True)


async def _observe_mobile_available_tasks(
    db: AsyncSession,
    employee_id: int,
    available_rows: List[dict],
) -> None:
    registry = OperationalRegistryService(db)
    snapshot = await load_employee_parity_snapshot(db, registry, employee_id)
    if snapshot is None:
        return

    if parity_domain_enabled("competence_parity_enabled"):
        result = compare_competence_sets(
            employee_id=employee_id,
            canonical_skills=snapshot["registry_skills"],
            transitional_skills=snapshot["legacy_skills"],
        )
        if parity_domain_enabled("parity_event_emission_enabled"):
            emit_parity_observation(
                event_type=ParityEventType.COMPETENCE_PARITY_DIFFERENCE.value,
                domain=result.domain,
                comparison_result=result.comparison_result,
                severity=result.severity,
                fingerprint=result.fingerprint,
                employee_id=employee_id,
                canonical_source=result.canonical_source,
                transitional_source=result.transitional_source,
                consumer=_CONSUMER,
                projection_scope="employee_snapshot",
            )

    mapping_cache: dict[str, dict[str, Any] | None] = {}
    explicit_cache: dict[str, set[int]] = {}

    if not parity_domain_enabled("eligibility_shadow_enabled"):
        return

    for row in available_rows:
        operation_code = str(row.get("process_type") or "").strip()
        if not operation_code:
            continue
        machine_type = str(row.get("machine_type") or "").strip() or None

        if operation_code not in mapping_cache:
            mapping_cache[operation_code] = await registry.resolve_operation_mapping(operation_code)
            resolved_code = (mapping_cache[operation_code] or {}).get("operation_code") or operation_code
            explicit_cache[operation_code] = set(
                await registry.get_operation_employee_ids(resolved_code)
            )

        mapping = mapping_cache[operation_code]
        canonical_eligible, reason = simulate_canonical_eligibility(
            snapshot=snapshot,
            mapping=mapping,
            machine_type=machine_type,
        )
        operational_eligible = True

        if canonical_eligible is None:
            comparison = ComparisonResult.UNKNOWN_OR_UNCOMPUTABLE
            if reason == "missing_operation_requirement":
                comparison = ComparisonResult.MISSING_OPERATION_REQUIREMENT
            from parity.comparators.generic import evaluate_parity_comparison
            from parity.enums import ParityDomain

            elig_result = evaluate_parity_comparison(
                domain=ParityDomain.ELIGIBILITY,
                entity_type="employee_operation_eligibility",
                entity_id=f"{employee_id}:{operation_code}",
                employee_id=employee_id,
                operation_code=operation_code,
                canonical_source="canonical_eligibility_simulation",
                transitional_source="operational_eligibility",
                canonical_result={"eligible": canonical_eligible},
                transitional_result={"eligible": operational_eligible},
                comparison_result=comparison,
            )
        else:
            elig_result = compare_eligibility_results(
                employee_id=employee_id,
                operation_code=operation_code,
                operational_eligible=operational_eligible,
                canonical_eligible=canonical_eligible,
            )

        if parity_domain_enabled("parity_event_emission_enabled"):
            emit_parity_observation(
                event_type=ParityEventType.ELIGIBILITY_PARITY_DIFFERENCE.value,
                domain=elig_result.domain,
                comparison_result=elig_result.comparison_result,
                severity=elig_result.severity,
                fingerprint=elig_result.fingerprint,
                employee_id=employee_id,
                operation_code=operation_code,
                canonical_source=elig_result.canonical_source,
                transitional_source=elig_result.transitional_source,
                consumer=_CONSUMER,
                projection_scope="available_task",
                metadata={"shadow_reason": reason},
            )

        if parity_domain_enabled("explicit_mapping_tracking_enabled"):
            explicit_ids = explicit_cache.get(operation_code, set())
            if employee_id in explicit_ids:
                required_skills = set((mapping or {}).get("required_skill_codes") or [])
                has_competence = bool(required_skills & set(snapshot["registry_skills"]))
                has_auth = bool(set(snapshot["registry_resources"]) & set((mapping or {}).get("allowed_resource_codes") or []))
                if not has_auth and not (mapping or {}).get("allowed_resource_codes"):
                    has_auth = True
                classification = (
                    ExplicitMappingClassification.ADAUGARE_FARA_COMPETENTA
                    if not has_competence
                    else ExplicitMappingClassification.SELECTIE_DINTRE_ELIGIBILI
                )
                mapping_result = compare_explicit_mapping(
                    employee_id=employee_id,
                    operation_code=operation_code,
                    classification=classification,
                    has_registry_competence=has_competence,
                    has_registry_authorization=has_auth,
                )
                if parity_domain_enabled("parity_event_emission_enabled"):
                    emit_parity_observation(
                        event_type=ParityEventType.EXPLICIT_MAPPING_USED.value,
                        domain=mapping_result.domain,
                        comparison_result=mapping_result.comparison_result,
                        severity=mapping_result.severity,
                        fingerprint=mapping_result.fingerprint,
                        employee_id=employee_id,
                        operation_code=operation_code,
                        canonical_source=mapping_result.canonical_source,
                        transitional_source=mapping_result.transitional_source,
                        consumer=_CONSUMER,
                        projection_scope="explicit_mapping",
                        metadata={"classification": classification.value},
                    )
