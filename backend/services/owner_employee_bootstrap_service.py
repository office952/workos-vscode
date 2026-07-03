"""Configurable, idempotent owner user → employee link for Employee Mobile readiness.

No runtime hardcoding. No payroll/attendance/request side effects.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from dependencies.permissions import resolve_effective_role
from models.auth import User
from models.employee_request import EmployeeRequest
from models.employees import Employees
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

OWNER_EMPLOYEE_TYPE = "management"
ACTIVE_EMPLOYEE_STATUS = "active"
MOBILE_SELF_ROLES = frozenset({"employee_mobile", "manager", "admin"})
REVIEW_ROLES = frozenset({"admin", "manager"})
TEAM_ROLES = frozenset({"admin", "manager"})
EFFECTS_ROLES = frozenset({"admin", "operator"})


@dataclass(frozen=True)
class OwnerBootstrapConfig:
    owner_email: Optional[str] = None
    owner_user_id: Optional[str] = None
    employee_name: str = ""
    employee_department: Optional[str] = None
    employee_title: Optional[str] = None
    dry_run: bool = False


@dataclass
class OwnerBootstrapResult:
    success: bool
    action: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    employee_id: Optional[int] = None
    dry_run: bool = False
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OwnerReadinessResult:
    status: str
    user_found: bool = False
    employee_found: bool = False
    employee_linked: bool = False
    employee_active: bool = False
    manager_employee_id_null: bool = False
    user_role: Optional[str] = None
    effective_role: Optional[str] = None
    has_mobile_self_role: bool = False
    has_review_role: bool = False
    has_team_role: bool = False
    direct_reports_count: int = 0
    pending_review_count: int = 0
    issues: List[str] = field(default_factory=list)
    owner: Dict[str, Any] = field(default_factory=dict)
    capabilities: Dict[str, str] = field(default_factory=dict)
    team: Dict[str, Any] = field(default_factory=dict)
    schema: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _capability_status(ok: bool) -> str:
    return "PASS" if ok else "WARN"


async def _employees_has_manager_column(db: AsyncSession) -> bool:
    def _check(connection) -> bool:
        from sqlalchemy import inspect

        cols = {c["name"] for c in inspect(connection).get_columns("employees")}
        return "manager_employee_id" in cols

    connection = await db.connection()
    return await connection.run_sync(_check)


def _truthy_env(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes")


def load_bootstrap_config_from_env() -> OwnerBootstrapConfig:
    return OwnerBootstrapConfig(
        owner_email=(os.getenv("WORKOS_OWNER_EMAIL") or "").strip() or None,
        owner_user_id=(os.getenv("WORKOS_OWNER_USER_ID") or "").strip() or None,
        employee_name=(os.getenv("WORKOS_OWNER_EMPLOYEE_NAME") or "").strip(),
        employee_department=(os.getenv("WORKOS_OWNER_EMPLOYEE_DEPARTMENT") or "").strip() or None,
        employee_title=(os.getenv("WORKOS_OWNER_EMPLOYEE_TITLE") or "").strip() or None,
        dry_run=_truthy_env("WORKOS_OWNER_BOOTSTRAP_DRY_RUN"),
    )


def validate_bootstrap_config(config: OwnerBootstrapConfig) -> Optional[str]:
    if not config.owner_email and not config.owner_user_id:
        return "WORKOS_OWNER_EMAIL or WORKOS_OWNER_USER_ID is required"
    if not config.employee_name:
        return "WORKOS_OWNER_EMPLOYEE_NAME is required"
    return None


async def _find_owner_user(db: AsyncSession, config: OwnerBootstrapConfig) -> Optional[User]:
    if config.owner_user_id:
        return await db.get(User, config.owner_user_id)
    if config.owner_email:
        result = await db.execute(
            select(User).where(func.lower(User.email) == config.owner_email.lower())
        )
        rows = list(result.scalars().all())
        if len(rows) > 1:
            return None  # caller treats as ambiguous via separate check
        return rows[0] if rows else None
    return None


async def _find_employee_by_user_id(db: AsyncSession, user_id: str) -> Optional[Employees]:
    result = await db.execute(
        select(Employees).where(Employees.user_id == user_id).order_by(Employees.id.asc())
    )
    rows = list(result.scalars().all())
    if len(rows) > 1:
        raise ValueError("multiple employees linked to user_id")
    return rows[0] if rows else None


async def _find_linkable_employee_by_name(
    db: AsyncSession,
    name: str,
) -> tuple[Optional[Employees], Optional[str]]:
    """Return (employee, error). Error set when match is ambiguous."""
    normalized = name.strip().lower()
    result = await db.execute(
        select(Employees).where(
            func.lower(Employees.name) == normalized,
            Employees.user_id.is_(None),
        )
    )
    rows = list(result.scalars().all())
    if len(rows) > 1:
        return None, "ambiguous_employee_name_match"
    return (rows[0] if rows else None), None


def _apply_safe_owner_fields(
    employee: Employees,
    config: OwnerBootstrapConfig,
    *,
    force_name: bool = False,
) -> List[str]:
    warnings: List[str] = []
    if force_name or config.employee_name:
        employee.name = config.employee_name
    if config.employee_department and not employee.department:
        employee.department = config.employee_department
    elif config.employee_department and employee.department != config.employee_department:
        warnings.append("department_not_overwritten")
    if config.employee_title and not employee.role:
        employee.role = config.employee_title
    elif config.employee_title and employee.role != config.employee_title:
        warnings.append("role_not_overwritten")
    if employee.status != ACTIVE_EMPLOYEE_STATUS:
        employee.status = ACTIVE_EMPLOYEE_STATUS
        warnings.append("status_set_active")
    if employee.manager_employee_id is not None:
        employee.manager_employee_id = None
        warnings.append("manager_employee_id_cleared")
    if employee.employee_type != OWNER_EMPLOYEE_TYPE:
        if employee.employee_type == "productive" and employee.cost_lunar_firma:
            warnings.append("employee_type_left_productive_with_cost")
        else:
            employee.employee_type = OWNER_EMPLOYEE_TYPE
    return warnings


def _new_owner_employee(user_id: str, config: OwnerBootstrapConfig) -> Employees:
    return Employees(
        name=config.employee_name,
        role=config.employee_title,
        department=config.employee_department,
        status=ACTIVE_EMPLOYEE_STATUS,
        employee_type=OWNER_EMPLOYEE_TYPE,
        user_id=user_id,
        manager_employee_id=None,
    )


async def bootstrap_owner_employee(
    db: AsyncSession,
    config: OwnerBootstrapConfig,
) -> OwnerBootstrapResult:
    config_error = validate_bootstrap_config(config)
    if config_error:
        return OwnerBootstrapResult(success=False, action="error", error=config_error, dry_run=config.dry_run)

    if config.owner_email and not config.owner_user_id:
        dup_check = await db.execute(
            select(User).where(func.lower(User.email) == config.owner_email.lower())
        )
        if len(list(dup_check.scalars().all())) > 1:
            return OwnerBootstrapResult(
                success=False,
                action="error",
                error="ambiguous_user_email_match",
                dry_run=config.dry_run,
            )

    user = await _find_owner_user(db, config)
    if user is None:
        return OwnerBootstrapResult(
            success=False,
            action="error",
            error="owner_user_not_found",
            dry_run=config.dry_run,
        )

    warnings: List[str] = []
    try:
        linked = await _find_employee_by_user_id(db, user.id)
    except ValueError:
        return OwnerBootstrapResult(
            success=False,
            action="error",
            error="multiple_employees_for_user",
            user_id=user.id,
            user_email=user.email,
            dry_run=config.dry_run,
        )

    if linked is not None:
        if config.dry_run:
            return OwnerBootstrapResult(
                success=True,
                action="dry_run_already_linked",
                user_id=user.id,
                user_email=user.email,
                employee_id=linked.id,
                dry_run=True,
            )
        warnings.extend(_apply_safe_owner_fields(linked, config))
        await db.commit()
        await db.refresh(linked)
        action = "updated" if warnings else "already_linked"
        return OwnerBootstrapResult(
            success=True,
            action=action,
            user_id=user.id,
            user_email=user.email,
            employee_id=linked.id,
            dry_run=False,
            warnings=warnings,
        )

    candidate, link_error = await _find_linkable_employee_by_name(db, config.employee_name)
    if link_error:
        return OwnerBootstrapResult(
            success=False,
            action="error",
            error=link_error,
            user_id=user.id,
            user_email=user.email,
            dry_run=config.dry_run,
        )

    if candidate is not None:
        if config.dry_run:
            return OwnerBootstrapResult(
                success=True,
                action="dry_run_would_link_existing",
                user_id=user.id,
                user_email=user.email,
                employee_id=candidate.id,
                dry_run=True,
            )
        candidate.user_id = user.id
        warnings.extend(_apply_safe_owner_fields(candidate, config))
        await db.commit()
        await db.refresh(candidate)
        return OwnerBootstrapResult(
            success=True,
            action="linked_existing_employee",
            user_id=user.id,
            user_email=user.email,
            employee_id=candidate.id,
            dry_run=False,
            warnings=warnings,
        )

    if config.dry_run:
        return OwnerBootstrapResult(
            success=True,
            action="dry_run_would_create",
            user_id=user.id,
            user_email=user.email,
            dry_run=True,
        )

    employee = _new_owner_employee(user.id, config)
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return OwnerBootstrapResult(
        success=True,
        action="created",
        user_id=user.id,
        user_email=user.email,
        employee_id=employee.id,
        dry_run=False,
    )


async def check_owner_mobile_readiness(
    db: AsyncSession,
    config: OwnerBootstrapConfig,
) -> OwnerReadinessResult:
    issues: List[str] = []
    warnings: List[str] = []
    config_error = validate_bootstrap_config(config)
    if config_error:
        return OwnerReadinessResult(status="FAIL", issues=[config_error])

    has_manager_column = await _employees_has_manager_column(db)
    schema_info = {
        "manager_employee_id_column_exists": has_manager_column,
        "migration_hint": None if has_manager_column else "Run alembic upgrade head through s51_employee_manager_employee_id",
    }
    if not has_manager_column:
        issues.append("manager_employee_id_column_missing")

    user = await _find_owner_user(db, config)
    if user is None:
        return OwnerReadinessResult(
            status="FAIL",
            user_found=False,
            issues=["owner_user_not_found"],
            schema=schema_info,
        )

    effective_role = resolve_effective_role(user.role or "viewer")
    has_mobile = effective_role in MOBILE_SELF_ROLES
    has_review = effective_role in REVIEW_ROLES
    has_team = effective_role in TEAM_ROLES
    has_effects = effective_role in EFFECTS_ROLES

    if not has_mobile:
        issues.append("missing_mobile_self_role")
    if not has_review:
        warnings.append("missing_manager_role_for_review")
    if not has_team:
        warnings.append("missing_manager_role_for_team")

    capabilities = {
        "employee_mobile_self": _capability_status(has_mobile),
        "review": _capability_status(has_review),
        "team": _capability_status(has_team),
        "effects_console": _capability_status(has_effects),
    }

    try:
        employee = await _find_employee_by_user_id(db, user.id)
    except ValueError:
        return OwnerReadinessResult(
            status="FAIL",
            user_found=True,
            user_role=user.role,
            effective_role=effective_role,
            has_mobile_self_role=has_mobile,
            has_review_role=has_review,
            has_team_role=has_team,
            issues=["multiple_employees_for_user"],
            capabilities=capabilities,
            schema=schema_info,
        )

    owner_info: Dict[str, Any] = {
        "user_found": True,
        "user_id": user.id,
        "user_email": user.email,
        "employee_found": employee is not None,
        "employee_id": employee.id if employee else None,
        "employee_name": employee.name if employee else None,
        "employee_active": False,
        "employee_linked": False,
        "manager_employee_id": employee.manager_employee_id if employee else None,
    }

    if employee is None:
        issues.append("missing_employee_link")
        status = "FAIL"
        team_info = {
            "direct_reports_count": 0,
            "active_direct_reports_count": 0,
            "direct_reports": [],
            "submitted_requests_count": 0,
            "warnings": ["no_direct_reports_assigned"],
        }
        return OwnerReadinessResult(
            status=status,
            user_found=True,
            user_role=user.role,
            effective_role=effective_role,
            has_mobile_self_role=has_mobile,
            has_review_role=has_review,
            has_team_role=has_team,
            issues=issues,
            owner=owner_info,
            capabilities=capabilities,
            team=team_info,
            schema=schema_info,
        )

    employee_found = True
    employee_linked = employee.user_id == user.id
    employee_active = employee.status == ACTIVE_EMPLOYEE_STATUS
    manager_null = employee.manager_employee_id is None

    owner_info.update(
        {
            "employee_active": employee_active,
            "employee_linked": employee_linked,
            "manager_employee_id": employee.manager_employee_id,
        }
    )

    if not employee_linked:
        issues.append("employee_user_id_mismatch")
    if not employee_active:
        issues.append("inactive_employee")
    if not manager_null:
        warnings.append("manager_employee_id_not_null_for_owner_root")

    reports_rows = await db.execute(
        select(Employees).where(Employees.manager_employee_id == employee.id)
    )
    all_reports = list(reports_rows.scalars().all())
    active_reports = [r for r in all_reports if r.status == ACTIVE_EMPLOYEE_STATUS]
    direct_reports_count = len(active_reports)

    if direct_reports_count == 0:
        warnings.append("no_direct_reports_assigned")

    if direct_reports_count > 0:
        team_ids = select(Employees.id).where(
            Employees.manager_employee_id == employee.id,
            Employees.status == ACTIVE_EMPLOYEE_STATUS,
        )
        pending_result = await db.execute(
            select(func.count())
            .select_from(EmployeeRequest)
            .where(
                EmployeeRequest.status == "submitted",
                EmployeeRequest.employee_id.in_(team_ids),
            )
        )
        pending_review_count = int(pending_result.scalar_one())
    else:
        pending_review_count = 0

    team_info = {
        "direct_reports_count": len(all_reports),
        "active_direct_reports_count": direct_reports_count,
        "direct_reports": [
            {"employee_id": r.id, "employee_name": r.name, "status": r.status}
            for r in active_reports[:20]
        ],
        "submitted_requests_count": pending_review_count,
        "warnings": list(warnings),
    }

    if issues:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    return OwnerReadinessResult(
        status=status,
        user_found=True,
        employee_found=employee_found,
        employee_linked=employee_linked,
        employee_active=employee_active,
        manager_employee_id_null=manager_null,
        user_role=user.role,
        effective_role=effective_role,
        has_mobile_self_role=has_mobile,
        has_review_role=has_review,
        has_team_role=has_team,
        direct_reports_count=direct_reports_count,
        pending_review_count=pending_review_count,
        issues=issues,
        owner=owner_info,
        capabilities=capabilities,
        team=team_info,
        schema=schema_info,
    )
