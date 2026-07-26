"""Batch canonical and transitional data for shadow comparisons."""

from __future__ import annotations

import json
from typing import Any

from models.employees import Employees
from services.operational_registry_service import OperationalRegistryService, _parse_json_list
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def load_employee_parity_snapshot(
    db: AsyncSession,
    registry: OperationalRegistryService,
    employee_id: int,
) -> dict[str, Any] | None:
    row = (
        await db.execute(select(Employees).where(Employees.id == employee_id))
    ).scalar_one_or_none()
    if row is None:
        return None
    auth = await registry.get_employee_authorizations(employee_id)
    return {
        "employee_id": employee_id,
        "registry_skills": auth.get("skill_codes") or [],
        "registry_resources": auth.get("resource_codes") or [],
        "registry_workcenters": auth.get("workcenter_codes") or [],
        "legacy_skills": _parse_json_list(row.skills),
        "legacy_machines": _parse_json_list(row.machines),
    }


def simulate_canonical_eligibility(
    *,
    snapshot: dict[str, Any],
    mapping: dict[str, Any] | None,
    machine_type: str | None = None,
) -> tuple[bool | None, str]:
    """Strict canonical eligibility — explicit mapping does not bypass competence/authorization."""
    if mapping is None:
        return None, "no_operation_mapping"

    required_skills = set(mapping.get("required_skill_codes") or [])
    allowed_workcenters = set(mapping.get("allowed_workcenter_codes") or [])
    allowed_resources = set(mapping.get("allowed_resource_codes") or [])

    if not required_skills and not allowed_workcenters and not allowed_resources:
        return None, "missing_operation_requirement"

    employee_skills = set(snapshot.get("registry_skills") or [])
    employee_workcenters = set(snapshot.get("registry_workcenters") or [])
    employee_resources = set(snapshot.get("registry_resources") or [])

    if required_skills and not (required_skills & employee_skills):
        return False, "missing_required_competence"

    if allowed_workcenters and not (allowed_workcenters & employee_workcenters):
        return False, "missing_workcenter_authorization"

    if allowed_resources:
        if machine_type:
            mt = machine_type.lower().replace(" ", "_")
            resource_ok = any(
                r.lower() in mt or mt in r.lower() for r in allowed_resources
            ) or bool(allowed_resources & employee_resources)
        else:
            resource_ok = bool(allowed_resources & employee_resources)
        if not resource_ok:
            return False, "missing_required_authorization"

    return True, "canonical_authorized"
