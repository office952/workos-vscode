"""Explicit direct-report assignment via employees.manager_employee_id — idempotent, env-driven."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from models.auth import User
from models.employees import Employees
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ACTIVE_EMPLOYEE_STATUS = "active"


@dataclass(frozen=True)
class DirectReportsAssignmentConfig:
    manager_employee_id: Optional[int] = None
    manager_user_email: Optional[str] = None
    manager_user_id: Optional[str] = None
    direct_report_employee_ids: Sequence[int] = ()
    direct_report_user_emails: Sequence[str] = ()
    direct_report_names: Sequence[str] = ()
    dry_run: bool = False
    force_reassign: bool = False


@dataclass
class DirectReportsAssignmentResult:
    success: bool
    manager_employee_id: Optional[int] = None
    manager_name: Optional[str] = None
    dry_run: bool = False
    assigned: List[Dict[str, Any]] = field(default_factory=list)
    already_assigned: List[Dict[str, Any]] = field(default_factory=list)
    skipped: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _truthy_env(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes")


def _parse_csv_ints(raw: Optional[str]) -> List[int]:
    if not raw or not raw.strip():
        return []
    out: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out


def _parse_csv_strings(raw: Optional[str]) -> List[str]:
    if not raw or not raw.strip():
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def load_direct_reports_config_from_env() -> DirectReportsAssignmentConfig:
    owner_emp_id_raw = (os.getenv("WORKOS_OWNER_EMPLOYEE_ID") or "").strip()
    manager_emp_id: Optional[int] = int(owner_emp_id_raw) if owner_emp_id_raw else None
    return DirectReportsAssignmentConfig(
        manager_employee_id=manager_emp_id,
        manager_user_email=(os.getenv("WORKOS_OWNER_EMAIL") or "").strip() or None,
        manager_user_id=(os.getenv("WORKOS_OWNER_USER_ID") or "").strip() or None,
        direct_report_employee_ids=_parse_csv_ints(os.getenv("WORKOS_DIRECT_REPORT_EMPLOYEE_IDS")),
        direct_report_user_emails=_parse_csv_strings(os.getenv("WORKOS_DIRECT_REPORT_USER_EMAILS")),
        direct_report_names=_parse_csv_strings(os.getenv("WORKOS_DIRECT_REPORT_NAMES")),
        dry_run=_truthy_env("WORKOS_DIRECT_REPORTS_DRY_RUN"),
        force_reassign=_truthy_env("WORKOS_DIRECT_REPORTS_FORCE_REASSIGN"),
    )


def validate_direct_reports_config(config: DirectReportsAssignmentConfig) -> Optional[str]:
    if (
        config.manager_employee_id is None
        and not config.manager_user_email
        and not config.manager_user_id
    ):
        return (
            "WORKOS_OWNER_EMPLOYEE_ID, WORKOS_OWNER_EMAIL, or WORKOS_OWNER_USER_ID is required"
        )
    if (
        not config.direct_report_employee_ids
        and not config.direct_report_user_emails
        and not config.direct_report_names
    ):
        return (
            "At least one of WORKOS_DIRECT_REPORT_EMPLOYEE_IDS, "
            "WORKOS_DIRECT_REPORT_USER_EMAILS, or WORKOS_DIRECT_REPORT_NAMES is required"
        )
    return None


async def _resolve_manager_employee(
    db: AsyncSession,
    config: DirectReportsAssignmentConfig,
) -> tuple[Optional[Employees], Optional[str]]:
    if config.manager_employee_id is not None:
        emp = await db.get(Employees, config.manager_employee_id)
        if emp is None:
            return None, "manager_employee_not_found"
        return emp, None

    user: Optional[User] = None
    if config.manager_user_id:
        user = await db.get(User, config.manager_user_id)
    elif config.manager_user_email:
        result = await db.execute(
            select(User).where(func.lower(User.email) == config.manager_user_email.lower())
        )
        rows = list(result.scalars().all())
        if len(rows) > 1:
            return None, "ambiguous_manager_user_email"
        user = rows[0] if rows else None

    if user is None:
        return None, "manager_user_not_found"

    result = await db.execute(
        select(Employees).where(Employees.user_id == user.id).order_by(Employees.id.asc())
    )
    rows = list(result.scalars().all())
    if len(rows) == 0:
        return None, "manager_employee_link_missing"
    if len(rows) > 1:
        return None, "ambiguous_manager_employee_link"
    return rows[0], None


async def _employee_by_id(db: AsyncSession, employee_id: int) -> Optional[Employees]:
    return await db.get(Employees, employee_id)


async def _employee_by_user_email(db: AsyncSession, email: str) -> tuple[Optional[Employees], Optional[str]]:
    result = await db.execute(
        select(User).where(func.lower(User.email) == email.strip().lower())
    )
    users = list(result.scalars().all())
    if len(users) > 1:
        return None, "ambiguous_user_email"
    if not users:
        return None, "direct_report_user_not_found"
    user = users[0]
    emp_result = await db.execute(
        select(Employees).where(Employees.user_id == user.id).order_by(Employees.id.asc())
    )
    emps = list(emp_result.scalars().all())
    if len(emps) > 1:
        return None, "ambiguous_employee_link"
    if not emps:
        return None, "direct_report_employee_link_missing"
    return emps[0], None


async def _employee_by_unique_name(
    db: AsyncSession,
    name: str,
) -> tuple[Optional[Employees], Optional[str]]:
    normalized = name.strip().lower()
    result = await db.execute(
        select(Employees).where(func.lower(Employees.name) == normalized)
    )
    rows = list(result.scalars().all())
    if len(rows) > 1:
        return None, "ambiguous_employee_name_match"
    if not rows:
        return None, "direct_report_employee_not_found"
    return rows[0], None


def _employee_summary(emp: Employees) -> Dict[str, Any]:
    return {
        "employee_id": emp.id,
        "employee_name": emp.name,
        "status": emp.status,
        "manager_employee_id": emp.manager_employee_id,
    }


async def _resolve_direct_report_targets(
    db: AsyncSession,
    config: DirectReportsAssignmentConfig,
) -> tuple[List[Employees], List[Dict[str, Any]]]:
    targets: Dict[int, Employees] = {}
    skipped: List[Dict[str, Any]] = []

    for emp_id in config.direct_report_employee_ids:
        emp = await _employee_by_id(db, emp_id)
        if emp is None:
            skipped.append({"employee_id": emp_id, "reason": "direct_report_employee_not_found"})
            continue
        targets[emp.id] = emp

    for email in config.direct_report_user_emails:
        emp, err = await _employee_by_user_email(db, email)
        if err:
            skipped.append({"user_email": email, "reason": err})
            continue
        targets[emp.id] = emp

    for name in config.direct_report_names:
        emp, err = await _employee_by_unique_name(db, name)
        if err:
            skipped.append({"employee_name": name, "reason": err})
            continue
        targets[emp.id] = emp

    return list(targets.values()), skipped


async def assign_direct_reports(
    db: AsyncSession,
    config: DirectReportsAssignmentConfig,
) -> DirectReportsAssignmentResult:
    config_error = validate_direct_reports_config(config)
    if config_error:
        return DirectReportsAssignmentResult(success=False, error=config_error, dry_run=config.dry_run)

    manager, mgr_error = await _resolve_manager_employee(db, config)
    if mgr_error or manager is None:
        hint = " Run bootstrap_owner_employee.py first." if mgr_error == "manager_employee_link_missing" else ""
        return DirectReportsAssignmentResult(
            success=False,
            error=f"{mgr_error}{hint}" if mgr_error else "manager_not_found",
            dry_run=config.dry_run,
        )

    if manager.status != ACTIVE_EMPLOYEE_STATUS:
        return DirectReportsAssignmentResult(
            success=False,
            error="manager_employee_inactive",
            manager_employee_id=manager.id,
            manager_name=manager.name,
            dry_run=config.dry_run,
        )

    targets, resolve_skipped = await _resolve_direct_report_targets(db, config)
    if not targets and resolve_skipped:
        return DirectReportsAssignmentResult(
            success=False,
            error="no_direct_reports_resolved",
            manager_employee_id=manager.id,
            manager_name=manager.name,
            skipped=resolve_skipped,
            dry_run=config.dry_run,
        )

    assigned: List[Dict[str, Any]] = []
    already_assigned: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = list(resolve_skipped)
    conflicts: List[Dict[str, Any]] = []
    pending_changes = False

    for report in targets:
        if report.id == manager.id:
            skipped.append({**_employee_summary(report), "reason": "cannot_assign_self"})
            continue
        if report.status != ACTIVE_EMPLOYEE_STATUS:
            skipped.append({**_employee_summary(report), "reason": "direct_report_inactive"})
            continue
        if report.manager_employee_id == manager.id:
            already_assigned.append(_employee_summary(report))
            continue
        if report.manager_employee_id is not None and report.manager_employee_id != manager.id:
            if not config.force_reassign:
                conflicts.append(
                    {
                        **_employee_summary(report),
                        "reason": "existing_manager_conflict",
                        "existing_manager_employee_id": report.manager_employee_id,
                    }
                )
                continue
        if config.dry_run:
            assigned.append({**_employee_summary(report), "would_set_manager_employee_id": manager.id})
            pending_changes = True
            continue
        report.manager_employee_id = manager.id
        assigned.append(_employee_summary(report))
        pending_changes = True

    if config.dry_run:
        return DirectReportsAssignmentResult(
            success=True,
            manager_employee_id=manager.id,
            manager_name=manager.name,
            dry_run=True,
            assigned=assigned,
            already_assigned=already_assigned,
            skipped=skipped,
            conflicts=conflicts,
        )

    if pending_changes:
        await db.commit()
        for report in targets:
            await db.refresh(report)

    success = not conflicts or config.force_reassign
    if conflicts and not config.force_reassign:
        success = len(assigned) > 0 or len(already_assigned) > 0

    return DirectReportsAssignmentResult(
        success=success and (len(assigned) > 0 or len(already_assigned) > 0 or not targets),
        manager_employee_id=manager.id,
        manager_name=manager.name,
        dry_run=False,
        assigned=assigned,
        already_assigned=already_assigned,
        skipped=skipped,
        conflicts=conflicts,
        error="conflicts_without_force" if conflicts and not config.force_reassign and not assigned else None,
    )
