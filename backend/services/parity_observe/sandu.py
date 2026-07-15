"""Sandu observe-only reconciliation report (in-memory)."""

from __future__ import annotations

import logging
from typing import Any

from parity.contracts import ReconciliationSheetContract
from parity.enums import DiscrepancyStatus
from parity.comparators.competence import compare_competence_sets
from services.operational_registry_service import OperationalRegistryService
from services.parity_observe.config import parity_observe_is_enabled
from services.parity_observe.shadow_data import load_employee_parity_snapshot
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

SANDU_EMPLOYEE_ID = 4


async def build_sandu_observe_report(db: AsyncSession) -> dict[str, Any] | None:
    """Generate in-memory Sandu reconciliation sheet — no persistence, no mutations."""
    if not parity_observe_is_enabled():
        return None
    try:
        return await _build_sandu_observe_report(db)
    except Exception:
        logger.warning("parity_observe_sandu_suppressed", exc_info=True)
        return None


async def _build_sandu_observe_report(db: AsyncSession) -> dict[str, Any] | None:
    registry = OperationalRegistryService(db)
    snapshot = await load_employee_parity_snapshot(db, registry, SANDU_EMPLOYEE_ID)
    if snapshot is None:
        return None

    from models.employees import Employees
    from sqlalchemy import select

    emp = (
        await db.execute(select(Employees).where(Employees.id == SANDU_EMPLOYEE_ID))
    ).scalar_one_or_none()
    if emp is None:
        return None

    competence = compare_competence_sets(
        employee_id=SANDU_EMPLOYEE_ID,
        canonical_skills=snapshot["registry_skills"],
        transitional_skills=snapshot["legacy_skills"],
    )

    explicit_mappings = []
    mappings = await registry.list_operation_mappings()
    for mapping in mappings:
        code = mapping.get("operation_code")
        if not code:
            continue
        explicit_ids = await registry.get_operation_employee_ids(code)
        if SANDU_EMPLOYEE_ID in explicit_ids:
            explicit_mappings.append(
                {
                    "operation_code": code,
                    "explicit_override": True,
                }
            )

    sheet = ReconciliationSheetContract(
        employee_id=SANDU_EMPLOYEE_ID,
        display_name=str(emp.name),
        canonical_entries={"skills": snapshot["registry_skills"], "resources": snapshot["registry_resources"]},
        transitional_entries={"skills": snapshot["legacy_skills"], "machines": snapshot["legacy_machines"]},
        explicit_mappings=[],
        affected_operations=[m["operation_code"] for m in explicit_mappings],
        required_confirmations=["manager_ack", "technical_validation", "practical_confirmation"],
        reconciliation_status=DiscrepancyStatus.CONFIRMATION_REQUIRED,
    )

    return {
        "sheet": sheet.model_dump(mode="json"),
        "competence_comparison": competence.model_dump(mode="json"),
        "explicit_mapping_operations": explicit_mappings,
        "mutations_performed": False,
    }
