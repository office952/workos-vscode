"""Eligibility endpoint — observe-only integration."""

from __future__ import annotations

import logging
from typing import Any

from parity.comparators.competence import compare_competence_sets
from parity.comparators.eligibility import compare_eligibility_results
from parity.enums import ComparisonResult, ParityEventType
from services.operational_registry_service import OperationalRegistryService
from services.parity_observe.config import parity_domain_enabled, parity_observe_is_enabled
from services.parity_observe.shadow_data import load_employee_parity_snapshot, simulate_canonical_eligibility
from services.parity_observe.structured_log import emit_parity_observation
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_CONSUMER = "operational_registry_eligible_employees"


async def observe_eligible_employees_endpoint(
    db: AsyncSession,
    operation_code: str,
    operational_result: dict[str, Any],
    *,
    machine_type: str | None = None,
) -> None:
    if not parity_observe_is_enabled():
        return
    try:
        await _observe_eligible_employees_endpoint(
            db, operation_code, operational_result, machine_type=machine_type
        )
    except Exception:
        logger.warning("parity_observe_eligibility_endpoint_suppressed", exc_info=True)


async def _observe_eligible_employees_endpoint(
    db: AsyncSession,
    operation_code: str,
    operational_result: dict[str, Any],
    *,
    machine_type: str | None = None,
) -> None:
    registry = OperationalRegistryService(db)
    resolved_code = operational_result.get("resolved_operation_code") or operation_code
    mapping = await registry.resolve_operation_mapping(operation_code)
    explicit_ids = set(operational_result.get("authorized_employee_ids") or [])

    for item in operational_result.get("items") or []:
        employee_id = int(item.get("id"))
        snapshot = await load_employee_parity_snapshot(db, registry, employee_id)
        if snapshot is None:
            continue

        if parity_domain_enabled("competence_parity_enabled"):
            comp = compare_competence_sets(
                employee_id=employee_id,
                canonical_skills=snapshot["registry_skills"],
                transitional_skills=snapshot["legacy_skills"],
            )
            if parity_domain_enabled("parity_event_emission_enabled"):
                emit_parity_observation(
                    event_type=ParityEventType.COMPETENCE_PARITY_DIFFERENCE.value,
                    domain=comp.domain,
                    comparison_result=comp.comparison_result,
                    severity=comp.severity,
                    fingerprint=comp.fingerprint,
                    employee_id=employee_id,
                    operation_code=resolved_code,
                    canonical_source=comp.canonical_source,
                    transitional_source=comp.transitional_source,
                    consumer=_CONSUMER,
                    projection_scope="eligible_employee_item",
                )

        if not parity_domain_enabled("eligibility_shadow_enabled"):
            continue

        operational_eligible = item.get("eligibility") == "authorized"
        canonical_eligible, reason = simulate_canonical_eligibility(
            snapshot=snapshot,
            mapping=mapping,
            machine_type=machine_type,
        )
        if canonical_eligible is None and reason == "missing_operation_requirement":
            from parity.comparators.generic import evaluate_parity_comparison
            from parity.enums import ParityDomain

            elig = evaluate_parity_comparison(
                domain=ParityDomain.ELIGIBILITY,
                entity_type="employee_operation_eligibility",
                entity_id=f"{employee_id}:{resolved_code}",
                employee_id=employee_id,
                operation_code=resolved_code,
                canonical_source="canonical_eligibility_simulation",
                transitional_source="operational_eligibility",
                canonical_result={"eligible": canonical_eligible},
                transitional_result={"eligible": operational_eligible},
                comparison_result=ComparisonResult.MISSING_OPERATION_REQUIREMENT,
            )
        else:
            elig = compare_eligibility_results(
                employee_id=employee_id,
                operation_code=resolved_code,
                operational_eligible=operational_eligible,
                canonical_eligible=canonical_eligible,
            )

        if (
            employee_id in explicit_ids
            and parity_domain_enabled("explicit_mapping_tracking_enabled")
            and operational_eligible
            and not bool(set(snapshot["registry_skills"]) & set((mapping or {}).get("required_skill_codes") or []))
        ):
            from parity.comparators.generic import evaluate_parity_comparison
            from parity.enums import ParityDomain

            elig = evaluate_parity_comparison(
                domain=ParityDomain.ELIGIBILITY,
                entity_type="employee_operation_eligibility",
                entity_id=f"{employee_id}:{resolved_code}",
                employee_id=employee_id,
                operation_code=resolved_code,
                canonical_source="canonical_eligibility_simulation",
                transitional_source="operational_eligibility",
                canonical_result={"eligible": False},
                transitional_result={"eligible": operational_eligible},
                comparison_result=ComparisonResult.OPERATIONAL_ELIGIBLE_CANONICAL_INELIGIBLE,
            )

        if parity_domain_enabled("parity_event_emission_enabled"):
            emit_parity_observation(
                event_type=ParityEventType.ELIGIBILITY_PARITY_DIFFERENCE.value,
                domain=elig.domain,
                comparison_result=elig.comparison_result,
                severity=elig.severity,
                fingerprint=elig.fingerprint,
                employee_id=employee_id,
                operation_code=resolved_code,
                canonical_source=elig.canonical_source,
                transitional_source=elig.transitional_source,
                consumer=_CONSUMER,
                projection_scope="eligible_employee_item",
                metadata={"shadow_reason": reason, "explicit_override": employee_id in explicit_ids},
            )
