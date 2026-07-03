"""Operational Reports — read-only aggregation over execution reality.

STRICT BOUNDARIES:
  - SELECT-only. Never writes execution_reality, inventory, quotes, or costs.
  - Does NOT import CostEngine, QuoteOrchestrator, or Pricing services.
  - Observational reports only — no stock adjustment, no auto-repair.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from models.operational_registry import FieldInstallationTeam, FieldInstallationTeamMember
from services.execution_plan_operational_readiness_service import (
    STATUS_V2_NOT_MATERIALIZED,
    evaluate_execution_plan_operational_readiness,
)
from services.execution_plan_task_parser import operational_tasks_only
from services.operational_registry_service import parse_order_id_from_installation_ref


def _parse_json_list(raw: Optional[str]) -> List[Dict[str, Any]]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def _parse_reporting_json(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not _has_text(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _normalize_employee_id(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.strip().isdigit():
        v = int(value.strip())
        return v if v > 0 else None
    return None


def _minutes_between(started_at: Optional[str], ended_at: Optional[str]) -> Optional[float]:
    start = _parse_iso(started_at)
    end = _parse_iso(ended_at)
    if start is None or end is None or end < start:
        return None
    return round((end - start).total_seconds() / 60.0, 2)


def _task_status(task: Dict[str, Any]) -> str:
    if _has_text(task.get("ended_at")):
        return "completed"
    if _has_text(task.get("blocked_at")):
        return "blocked"
    if _has_text(task.get("paused_at")):
        return "paused"
    if _has_text(task.get("started_at")):
        return "in_progress"
    return "not_started"


def _timestamp_in_range(
    value: Optional[str],
    from_dt: Optional[datetime],
    to_dt: Optional[datetime],
) -> bool:
    if from_dt is None and to_dt is None:
        return True
    parsed = _parse_iso(value)
    if parsed is None:
        return from_dt is None and to_dt is None
    if from_dt and parsed < from_dt:
        return False
    if to_dt and parsed > to_dt:
        return False
    return True


_OPERATION_TO_STATION: Dict[str, str] = {
    "print": "print",
    "cutter_plotter": "cutter_plotter",
    "cnc_cutting": "cnc",
    "vinyl_application": "montaj_autocolant",
    "assembly": "asamblare_lipire",
}


def _resolve_station_id(task: Dict[str, Any]) -> Optional[str]:
    op = (task.get("operation_code") or task.get("process_type") or "").strip().lower()
    op = op.replace("-", "_").replace(" ", "_")
    if op in _OPERATION_TO_STATION:
        return _OPERATION_TO_STATION[op]
    wc = (task.get("workcenter_code") or "").strip()
    _wc_map = {
        "WC_PRINT": "print",
        "WC_CUT": "cutter_plotter",
        "WC_VINYL_APPLICATION": "montaj_autocolant",
    }
    return _wc_map.get(wc)


def _task_in_date_range(
    task: Dict[str, Any],
    from_dt: Optional[datetime],
    to_dt: Optional[datetime],
) -> bool:
    if from_dt is None and to_dt is None:
        return True
    for key in ("started_at", "ended_at", "blocked_at"):
        if _timestamp_in_range(task.get(key), from_dt, to_dt):
            return True
    return False


class OperationalReportsService:
    """Read-only operational reports aggregator."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_summary(
        self,
        *,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        employee_id: Optional[int] = None,
        order_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        from_dt = _parse_iso(from_date) if from_date else None
        to_dt = _parse_iso(to_date) if to_date else None
        if to_dt:
            to_dt = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        cat = (category or "all").lower()
        include_employee = cat in {"all", "employee", "employees", "employee_activity"}
        include_tasks = cat in {"all", "tasks", "task", "task_reality"}
        include_materials = cat in {"all", "materials", "material", "materials_reality"}
        include_field = cat in {"all", "field", "field_installation", "montaj", "montaj_teren"}
        include_completeness = cat in {"all", "completeness", "summary"}

        realities_q = select(ExecutionReality).where(
            (ExecutionReality.is_invalid.is_(False)) | (ExecutionReality.is_invalid.is_(None))
        )
        if order_id is not None:
            realities_q = realities_q.where(ExecutionReality.order_id == order_id)
        realities = list((await self.db.execute(realities_q)).scalars().all())

        order_codes: Dict[int, str] = {r.order_id: r.order_code for r in realities}
        for o in (await self.db.execute(select(Orders))).scalars().all():
            order_codes[o.id] = o.code

        employee_names: Dict[int, str] = {}
        for emp in (await self.db.execute(select(Employees))).scalars().all():
            employee_names[emp.id] = emp.name

        task_rows: List[Dict[str, Any]] = []
        material_rows: List[Dict[str, Any]] = []
        material_task_ids_by_order: Dict[int, Set[str]] = {}
        employee_stats: Dict[int, Dict[str, Any]] = {}

        def _ensure_employee_stat(emp_id: int, emp_name: Optional[str]) -> Dict[str, Any]:
            if emp_id not in employee_stats:
                employee_stats[emp_id] = {
                    "employee_id": emp_id,
                    "employee_name": emp_name or employee_names.get(emp_id) or f"Employee #{emp_id}",
                    "tasks_started": 0,
                    "tasks_completed": 0,
                    "tasks_blocked": 0,
                    "observed_minutes_total": 0.0,
                    "observed_minutes_computable": 0,
                }
            return employee_stats[emp_id]

        completeness = {
            "total_tasks": 0,
            "tasks_with_employee": 0,
            "tasks_without_employee": 0,
            "tasks_with_materials": 0,
            "tasks_without_materials": 0,
            "total_materials_reported": 0,
            "materials_with_reporter": 0,
            "materials_without_reporter": 0,
            "materials_with_task_id": 0,
            "materials_without_task_id": 0,
            "field_installations_complete": 0,
            "field_installations_incomplete": 0,
            "plan_operational_tasks_total": 0,
            "plan_orders_v2_not_materialized": 0,
        }

        plans_q = select(ExecutionPlan)
        if order_id is not None:
            plans_q = plans_q.where(ExecutionPlan.order_id == order_id)
        execution_plans = list((await self.db.execute(plans_q)).scalars().all())
        for plan in execution_plans:
            operational = operational_tasks_only(plan.tasks_json)
            completeness["plan_operational_tasks_total"] += len(operational)
            readiness = evaluate_execution_plan_operational_readiness(plan)
            if readiness.status == STATUS_V2_NOT_MATERIALIZED:
                completeness["plan_orders_v2_not_materialized"] += 1

        for row in realities:
            tasks = _parse_json_list(row.tasks_json)
            materials = _parse_json_list(row.materials_json)
            order_material_task_ids: Set[str] = set()
            for m in materials:
                tid = m.get("task_id")
                if tid is not None and str(tid).strip():
                    order_material_task_ids.add(str(tid))
            material_task_ids_by_order[row.order_id] = order_material_task_ids

            for task in tasks:
                if not isinstance(task, dict):
                    continue
                if not _task_in_date_range(task, from_dt, to_dt):
                    continue

                task_id = str(task.get("task_id") or "").strip() or None
                emp_id = _normalize_employee_id(task.get("employee_id"))
                completed_by = _normalize_employee_id(task.get("completed_by_employee_id"))
                emp_name = task.get("employee_name") or task.get("completed_by_employee_name")

                if employee_id is not None:
                    if emp_id != employee_id and completed_by != employee_id:
                        continue

                status = _task_status(task)
                has_materials = bool(task_id and task_id in order_material_task_ids)
                has_employee = emp_id is not None

                completeness["total_tasks"] += 1
                if has_employee:
                    completeness["tasks_with_employee"] += 1
                else:
                    completeness["tasks_without_employee"] += 1
                if has_materials:
                    completeness["tasks_with_materials"] += 1
                else:
                    completeness["tasks_without_materials"] += 1

                if include_tasks:
                    op = task.get("operation_code") or task.get("process_type")
                    station_id = _resolve_station_id(task)
                    task_rows.append(
                        {
                            "order_id": row.order_id,
                            "order_code": row.order_code,
                            "task_id": task_id,
                            "process_type": task.get("process_type"),
                            "operation_code": task.get("operation_code"),
                            "employee_id": emp_id,
                            "employee_name": emp_name,
                            "started_at": task.get("started_at"),
                            "ended_at": task.get("ended_at"),
                            "status": status,
                            "completion_notes_present": _has_text(task.get("completion_notes")),
                            "materials_reported": has_materials,
                            "observed_minutes": _minutes_between(
                                task.get("started_at"), task.get("ended_at")
                            ),
                            "links": {
                                "order": f"/orders/{row.order_code}",
                                "execution_detail": f"/execution/{row.order_id}",
                                "operator": "/operator",
                                "tablet": f"/tablet/{station_id}" if station_id else None,
                            },
                        }
                    )

                if include_employee:
                    if emp_id is not None and _has_text(task.get("started_at")):
                        stat = _ensure_employee_stat(emp_id, emp_name)
                        stat["tasks_started"] += 1
                        if status == "blocked":
                            stat["tasks_blocked"] += 1
                        minutes = _minutes_between(task.get("started_at"), task.get("ended_at"))
                        if minutes is not None:
                            stat["observed_minutes_total"] += minutes
                            stat["observed_minutes_computable"] += 1
                    finisher = completed_by or emp_id
                    if finisher is not None and _has_text(task.get("ended_at")):
                        fin_name = task.get("completed_by_employee_name") or emp_name
                        stat = _ensure_employee_stat(finisher, fin_name)
                        stat["tasks_completed"] += 1

            for mat in materials:
                if not isinstance(mat, dict):
                    continue
                reported_at = mat.get("reported_at") or mat.get("added_at")
                if not _timestamp_in_range(reported_at, from_dt, to_dt):
                    continue
                reporter_id = _normalize_employee_id(mat.get("reported_by_employee_id"))
                mat_task = mat.get("task_id")
                has_task_id = mat_task is not None and str(mat_task).strip() != ""
                has_reporter = reporter_id is not None

                if include_completeness:
                    completeness["total_materials_reported"] += 1
                    if has_reporter:
                        completeness["materials_with_reporter"] += 1
                    else:
                        completeness["materials_without_reporter"] += 1
                    if has_task_id:
                        completeness["materials_with_task_id"] += 1
                    else:
                        completeness["materials_without_task_id"] += 1

                if employee_id is not None and reporter_id != employee_id:
                    continue

                if include_materials:
                    reporter_name = mat.get("reported_by_employee_name")
                    if not reporter_name and reporter_id:
                        reporter_name = employee_names.get(reporter_id)
                    material_rows.append(
                        {
                            "order_id": row.order_id,
                            "order_code": row.order_code,
                            "task_id": mat.get("task_id"),
                            "material_id": mat.get("material_id"),
                            "material_code": mat.get("material_code"),
                            "material_name": mat.get("material_name"),
                            "quantity": mat.get("quantity"),
                            "unit": mat.get("unit"),
                            "reported_by_employee_id": reporter_id,
                            "reported_by_employee_name": reporter_name,
                            "reported_at": reported_at,
                            "consumption_notes": mat.get("consumption_notes"),
                        }
                    )

        field_rows: List[Dict[str, Any]] = []
        teams_q = select(FieldInstallationTeam)
        teams = list((await self.db.execute(teams_q)).scalars().all())
        for team in teams:
            team_order_id = parse_order_id_from_installation_ref(team.installation_ref)
            if order_id is not None and team_order_id != order_id:
                continue
            started_iso = team.started_at.isoformat() if team.started_at else None
            ended_iso = team.ended_at.isoformat() if team.ended_at else None
            if not (
                _timestamp_in_range(started_iso, from_dt, to_dt)
                or _timestamp_in_range(ended_iso, from_dt, to_dt)
            ):
                if from_dt or to_dt:
                    continue

            members = list(
                (
                    await self.db.execute(
                        select(FieldInstallationTeamMember).where(
                            FieldInstallationTeamMember.team_id == team.id
                        )
                    )
                ).scalars().all()
            )
            if employee_id is not None:
                if not any(m.employee_id == employee_id for m in members):
                    continue

            reporting = _parse_reporting_json(team.reporting_json)
            photos = reporting.get("completion_photos") or []
            photo_count = len(photos) if isinstance(photos, list) else 0
            status = (team.status or "").lower()
            is_complete = status == "completed" or team.ended_at is not None
            if is_complete:
                completeness["field_installations_complete"] += 1
            else:
                completeness["field_installations_incomplete"] += 1

            order_code = (
                order_codes.get(team_order_id) if team_order_id is not None else None
            ) or team.installation_ref

            if include_field:
                field_rows.append(
                    {
                        "team_id": team.id,
                        "installation_ref": team.installation_ref,
                        "order_id": team_order_id,
                        "order_code": order_code,
                        "status": team.status,
                        "team_members_count": len(members),
                        "started_at": started_iso,
                        "ended_at": ended_iso,
                        "completion_photos_count": photo_count,
                        "client_observations_present": _has_text(team.client_observations),
                    }
                )

        employee_activity = sorted(
            employee_stats.values(),
            key=lambda r: (r.get("employee_name") or "", r.get("employee_id") or 0),
        )
        for stat in employee_activity:
            stat["observed_minutes_total"] = round(stat["observed_minutes_total"], 2)

        payload: Dict[str, Any] = {
            "read_only": True,
            "filters_applied": {
                "from_date": from_date,
                "to_date": to_date,
                "employee_id": employee_id,
                "order_id": order_id,
                "category": cat,
            },
        }
        if include_employee:
            payload["employee_activity"] = employee_activity
        if include_tasks:
            payload["task_reality"] = task_rows
        if include_materials:
            payload["materials_reality"] = material_rows
        if include_field:
            payload["field_installation"] = field_rows
        if include_completeness:
            payload["completeness_summary"] = completeness

        payload["counts"] = {
            "employee_activity_rows": len(employee_activity) if include_employee else 0,
            "task_reality_rows": len(task_rows) if include_tasks else 0,
            "materials_reality_rows": len(material_rows) if include_materials else 0,
            "field_installation_rows": len(field_rows) if include_field else 0,
        }
        return payload
