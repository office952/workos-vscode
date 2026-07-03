"""Operator employee validation for task-action start.

Hard guards:
  - employee_id must reference an active Employee row when provided.

Soft warnings (never block start):
  - authorization mismatch vs operation_resource_requirements
  - missing operation mapping for process_type
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from models.employees import Employees
from services.operational_registry_service import OperationalRegistryService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class OperatorEmployeeGuardResult:
    allowed: bool
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    legacy_operator: bool = False
    authorization_status: str = "unverified"  # authorized | not_authorized | unverified
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class OperatorEmployeeGuard:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.registry = OperationalRegistryService(db)

    async def validate_for_task_start(
        self,
        *,
        employee_id: Optional[int],
        process_type: Optional[str] = None,
        machine_type: Optional[str] = None,
    ) -> OperatorEmployeeGuardResult:
        if employee_id is None:
            return OperatorEmployeeGuardResult(
                allowed=True,
                legacy_operator=True,
                authorization_status="unverified",
                warnings=["operator_legacy_no_employee_id"],
            )

        emp = (
            await self.db.execute(select(Employees).where(Employees.id == employee_id))
        ).scalar_one_or_none()

        if emp is None:
            return OperatorEmployeeGuardResult(
                allowed=False,
                employee_id=employee_id,
                authorization_status="unverified",
                errors=["employee_not_found"],
            )

        if emp.status != "active":
            return OperatorEmployeeGuardResult(
                allowed=False,
                employee_id=employee_id,
                employee_name=emp.name,
                authorization_status="unverified",
                errors=["employee_not_active"],
            )

        result = OperatorEmployeeGuardResult(
            allowed=True,
            employee_id=emp.id,
            employee_name=emp.name,
            legacy_operator=False,
            authorization_status="unverified",
        )

        operation_code = (process_type or "").strip()
        if not operation_code:
            result.warnings.append("authorization_unverified_missing_process_type")
            return result

        resolved = await self.registry.resolve_operation_mapping(operation_code)
        if resolved is None:
            result.warnings.append("authorization_unverified_no_operation_mapping")
            return result

        eligibility = await self.registry.check_employee_operation_eligibility(
            emp.id,
            operation_code,
            machine_type=machine_type,
        )

        if eligibility.get("authorization_status") == "authorized":
            result.authorization_status = "authorized"
        else:
            result.authorization_status = "not_authorized"
            result.warnings.append("employee_authorization_mismatch")

        return result
