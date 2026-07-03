"""Operational Reality Review — read-only gap detection over execution reality.

STRICT BOUNDARIES:
  - SELECT-only. Never writes execution_reality, inventory, quotes, or costs.
  - Does NOT import CostEngine, QuoteOrchestrator, or Pricing services.
  - Reports gaps only — no auto-repair, no auto-assignment, no stock adjustment.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_reality import ExecutionReality
from models.orders import Orders
from models.operational_registry import FieldInstallationTeam, FieldInstallationTeamMember
from services.operational_registry_service import parse_order_id_from_installation_ref

GAP_TYPES = frozenset(
    {
        "TASK_MISSING_EMPLOYEE",
        "TASK_STARTED_NOT_COMPLETED",
        "TASK_COMPLETED_WITHOUT_COMPLETION_NOTES",
        "TASK_COMPLETED_WITHOUT_MATERIALS",
        "MATERIAL_WITHOUT_TASK_ID",
        "MATERIAL_WITHOUT_REPORTER",
        "FIELD_INSTALLATION_PLANNED_NOT_STARTED",
        "FIELD_INSTALLATION_STARTED_NOT_COMPLETED",
        "FIELD_INSTALLATION_COMPLETED_WITHOUT_PHOTOS",
        "FIELD_INSTALLATION_COMPLETED_WITHOUT_CLIENT_OBSERVATIONS",
        "FIELD_INSTALLATION_WITHOUT_TEAM_MEMBERS",
        "TASK_MAPPING_UNCONFIRMED",
        "LEGACY_TASK_WITHOUT_EMPLOYEE_ID",
    }
)

STATION_WORKCENTER_CODES: Dict[str, List[str]] = {
    "print": ["WC_PRINT"],
    "cutter_plotter": ["WC_CUT"],
    "cnc": ["WC_CNC_ROUTING", "WC_LASER_CUTTING"],
    "modelare_litere": ["WC_LETTER_FORMING"],
    "led_electric": ["WC_LED_ASSEMBLY"],
    "lacatuserie_sudura": ["WC_METAL_FAB"],
    "asamblare_lipire": ["WC_ASSEMBLY"],
    "montaj_autocolant": ["WC_VINYL_APPLICATION"],
}

OPERATION_TO_STATION: Dict[str, str] = {
    "print": "print",
    "print_roll": "print",
    "print_uv": "print",
    "cutter_plotter": "cutter_plotter",
    "contour_cut": "cutter_plotter",
    "cnc_cutting": "cnc",
    "routing": "cnc",
    "laser_cutting": "cnc",
    "letter_return_forming": "modelare_litere",
    "led_installation": "led_electric",
    "montaj_led": "led_electric",
    "metal_frame": "lacatuserie_sudura",
    "welding": "lacatuserie_sudura",
    "assembly": "asamblare_lipire",
    "vinyl_application": "montaj_autocolant",
    "colantare": "montaj_autocolant",
}


def _normalize_op(code: Optional[str]) -> str:
    return (code or "").strip().lower().replace("-", "_").replace(" ", "_")


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _has_employee_id(task: Dict[str, Any]) -> bool:
    emp = task.get("employee_id")
    if emp is None:
        return False
    if isinstance(emp, int):
        return emp > 0
    if isinstance(emp, str) and emp.strip().isdigit():
        return int(emp.strip()) > 0
    return False


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


def _resolve_tablet_station(task: Dict[str, Any]) -> Optional[str]:
    op = _normalize_op(task.get("operation_code") or task.get("process_type"))
    if op in OPERATION_TO_STATION:
        return OPERATION_TO_STATION[op]

    wc = (task.get("workcenter_code") or "").strip()
    if wc:
        for station_id, codes in STATION_WORKCENTER_CODES.items():
            if wc in codes:
                return station_id
    return None


def _build_links(
    *,
    order_id: Optional[int],
    order_code: Optional[str],
    task_id: Optional[str] = None,
    station_id: Optional[str] = None,
    team_id: Optional[int] = None,
    category: str,
) -> Dict[str, Optional[str]]:
    links: Dict[str, Optional[str]] = {
        "order": f"/orders/{order_code}" if order_code else None,
        "operator": "/operator" if category == "atelier" else None,
        "tablet": f"/tablet/{station_id}" if station_id else None,
        "field_installation": (
            f"/orders/{order_code}#field-installation"
            if order_code and category == "montaj_teren"
            else None
        ),
        "execution_detail": f"/execution/{order_id}" if order_id else None,
        "team_id": str(team_id) if team_id is not None else None,
        "task_id": task_id,
    }
    return links


def _gap(
    *,
    gap_type: str,
    severity: str,
    category: str,
    message: str,
    order_id: Optional[int] = None,
    order_code: Optional[str] = None,
    task_id: Optional[str] = None,
    team_id: Optional[int] = None,
    station_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "gap_type": gap_type,
        "severity": severity,
        "category": category,
        "message": message,
        "order_id": order_id,
        "order_code": order_code,
        "task_id": task_id,
        "team_id": team_id,
        "links": _build_links(
            order_id=order_id,
            order_code=order_code,
            task_id=task_id,
            station_id=station_id,
            team_id=team_id,
            category=category,
        ),
    }
    if extra:
        payload["context"] = extra
    return payload


class OperationalRealityReviewService:
    """Read-only analyzer — no mutations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_review(self) -> Dict[str, Any]:
        gaps: List[Dict[str, Any]] = []
        summary = self._empty_summary()

        realities = (
            await self.db.execute(
                select(ExecutionReality).where(
                    (ExecutionReality.is_invalid.is_(False))
                    | (ExecutionReality.is_invalid.is_(None))
                )
            )
        ).scalars().all()

        for row in realities:
            tasks = _parse_json_list(row.tasks_json)
            materials = _parse_json_list(row.materials_json)
            material_task_ids: Set[str] = set()
            for m in materials:
                tid = m.get("task_id")
                if tid is not None and str(tid).strip():
                    material_task_ids.add(str(tid))

            for task in tasks:
                if not isinstance(task, dict):
                    continue
                task_id = str(task.get("task_id") or "").strip() or None
                started = _has_text(task.get("started_at"))
                ended = _has_text(task.get("ended_at"))
                has_employee = _has_employee_id(task)
                station_id = _resolve_tablet_station(task)

                summary["total_tasks_analyzed"] += 1
                if has_employee:
                    summary["tasks_with_employee"] += 1
                else:
                    summary["tasks_without_employee"] += 1

                if ended:
                    summary["tasks_completed"] += 1
                    if task_id and task_id not in material_task_ids:
                        summary["tasks_completed_without_materials"] += 1
                        gaps.append(
                            _gap(
                                gap_type="TASK_COMPLETED_WITHOUT_MATERIALS",
                                severity="warning",
                                category="atelier",
                                message=(
                                    f"Task {task_id or '?'} finalizat fără materiale raportate "
                                    f"pentru comanda {row.order_code}."
                                ),
                                order_id=row.order_id,
                                order_code=row.order_code,
                                task_id=task_id,
                                station_id=station_id,
                            )
                        )
                    if not _has_text(task.get("completion_notes")):
                        gaps.append(
                            _gap(
                                gap_type="TASK_COMPLETED_WITHOUT_COMPLETION_NOTES",
                                severity="info",
                                category="atelier",
                                message=(
                                    f"Task {task_id or '?'} finalizat fără note de completare "
                                    f"({row.order_code})."
                                ),
                                order_id=row.order_id,
                                order_code=row.order_code,
                                task_id=task_id,
                                station_id=station_id,
                            )
                        )
                    if not has_employee:
                        gaps.append(
                            _gap(
                                gap_type="LEGACY_TASK_WITHOUT_EMPLOYEE_ID",
                                severity="info",
                                category="atelier",
                                message=(
                                    f"Task {task_id or '?'} finalizat fără employee_id "
                                    f"(captură legacy, {row.order_code})."
                                ),
                                order_id=row.order_id,
                                order_code=row.order_code,
                                task_id=task_id,
                                station_id=station_id,
                            )
                        )

                if started and not ended:
                    summary["tasks_started_not_completed"] += 1
                    gaps.append(
                        _gap(
                            gap_type="TASK_STARTED_NOT_COMPLETED",
                            severity="warning",
                            category="atelier",
                            message=(
                                f"Task {task_id or '?'} pornit dar nefinalizat "
                                f"({row.order_code})."
                            ),
                            order_id=row.order_id,
                            order_code=row.order_code,
                            task_id=task_id,
                            station_id=station_id,
                        )
                    )

                if started and not has_employee:
                    gaps.append(
                        _gap(
                            gap_type="TASK_MISSING_EMPLOYEE",
                            severity="warning",
                            category="atelier",
                            message=(
                                f"Task {task_id or '?'} fără angajat asociat "
                                f"({row.order_code})."
                            ),
                            order_id=row.order_id,
                            order_code=row.order_code,
                            task_id=task_id,
                            station_id=station_id,
                        )
                    )

                op_code = task.get("operation_code") or task.get("process_type")
                if _has_text(str(op_code) if op_code is not None else None):
                    if not _has_text(task.get("workcenter_code")):
                        gaps.append(
                            _gap(
                                gap_type="TASK_MAPPING_UNCONFIRMED",
                                severity="info",
                                category="atelier",
                                message=(
                                    f"Task {task_id or '?'} are operație dar lipsește workcenter_code "
                                    f"({row.order_code})."
                                ),
                                order_id=row.order_id,
                                order_code=row.order_code,
                                task_id=task_id,
                                station_id=station_id,
                                extra={"operation_code": op_code},
                            )
                        )

            for mat in materials:
                if not isinstance(mat, dict):
                    continue
                mat_task = mat.get("task_id")
                if mat_task is None or not str(mat_task).strip():
                    summary["materials_without_task_id"] += 1
                    gaps.append(
                        _gap(
                            gap_type="MATERIAL_WITHOUT_TASK_ID",
                            severity="warning",
                            category="materiale",
                            message=(
                                f"Material '{mat.get('material_name', '?')}' fără task_id "
                                f"({row.order_code})."
                            ),
                            order_id=row.order_id,
                            order_code=row.order_code,
                        )
                    )
                reporter = mat.get("reported_by_employee_id")
                if reporter is None or (
                    isinstance(reporter, str) and not reporter.strip()
                ):
                    summary["materials_without_reporter"] += 1
                    gaps.append(
                        _gap(
                            gap_type="MATERIAL_WITHOUT_REPORTER",
                            severity="warning",
                            category="materiale",
                            message=(
                                f"Material '{mat.get('material_name', '?')}' fără reporter "
                                f"({row.order_code})."
                            ),
                            order_id=row.order_id,
                            order_code=row.order_code,
                            task_id=str(mat_task) if mat_task else None,
                        )
                    )

        order_codes_by_id: Dict[int, str] = {}
        for row in realities:
            order_codes_by_id[row.order_id] = row.order_code
        order_rows = (await self.db.execute(select(Orders))).scalars().all()
        for o in order_rows:
            order_codes_by_id[o.id] = o.code

        teams = (await self.db.execute(select(FieldInstallationTeam))).scalars().all()
        for team in teams:
            members = (
                await self.db.execute(
                    select(FieldInstallationTeamMember).where(
                        FieldInstallationTeamMember.team_id == team.id
                    )
                )
            ).scalars().all()
            member_count = len(members)
            order_id = parse_order_id_from_installation_ref(team.installation_ref)
            order_code = (
                order_codes_by_id.get(order_id) if order_id is not None else None
            ) or team.installation_ref
            reporting = _parse_reporting_json(team.reporting_json)
            photos = reporting.get("completion_photos") or []
            has_photos = isinstance(photos, list) and len(photos) > 0
            status = (team.status or "").lower()
            started = team.started_at is not None
            ended = team.ended_at is not None
            is_completed = status == "completed" or ended

            if member_count == 0:
                gaps.append(
                    _gap(
                        gap_type="FIELD_INSTALLATION_WITHOUT_TEAM_MEMBERS",
                        severity="critical",
                        category="montaj_teren",
                        message=(
                            f"Montaj teren {team.installation_ref} fără membri în echipă."
                        ),
                        order_id=order_id,
                        order_code=order_code if order_id else None,
                        team_id=team.id,
                    )
                )

            if status in {"planned", "draft"} and not started:
                if member_count > 0 or team.scheduled_at is not None:
                    gaps.append(
                        _gap(
                            gap_type="FIELD_INSTALLATION_PLANNED_NOT_STARTED",
                            severity="info",
                            category="montaj_teren",
                            message=(
                                f"Montaj teren planificat dar nepornit ({team.installation_ref})."
                            ),
                            order_id=order_id,
                            order_code=order_code if order_id else None,
                            team_id=team.id,
                        )
                    )

            if started and not ended and status != "cancelled":
                summary["field_installations_started_not_completed"] += 1
                gaps.append(
                    _gap(
                        gap_type="FIELD_INSTALLATION_STARTED_NOT_COMPLETED",
                        severity="warning",
                        category="montaj_teren",
                        message=(
                            f"Montaj teren pornit dar nefinalizat ({team.installation_ref})."
                        ),
                        order_id=order_id,
                        order_code=order_code if order_id else None,
                        team_id=team.id,
                    )
                )

            if is_completed:
                if not has_photos:
                    summary["field_installations_completed_without_photos"] += 1
                    gaps.append(
                        _gap(
                            gap_type="FIELD_INSTALLATION_COMPLETED_WITHOUT_PHOTOS",
                            severity="warning",
                            category="montaj_teren",
                            message=(
                                f"Montaj teren finalizat fără poze ({team.installation_ref})."
                            ),
                            order_id=order_id,
                            order_code=order_code if order_id else None,
                            team_id=team.id,
                        )
                    )
                if not _has_text(team.client_observations):
                    gaps.append(
                        _gap(
                            gap_type="FIELD_INSTALLATION_COMPLETED_WITHOUT_CLIENT_OBSERVATIONS",
                            severity="info",
                            category="montaj_teren",
                            message=(
                                f"Montaj teren finalizat fără observații client "
                                f"({team.installation_ref})."
                            ),
                            order_id=order_id,
                            order_code=order_code if order_id else None,
                            team_id=team.id,
                        )
                    )

        for g in gaps:
            sev = g["severity"]
            if sev in summary["gaps_by_severity"]:
                summary["gaps_by_severity"][sev] += 1
            cat = g["category"]
            if cat in summary["gaps_by_category"]:
                summary["gaps_by_category"][cat] += 1

        summary["total_gaps"] = len(gaps)
        summary["orders_analyzed"] = len(realities)
        summary["field_installation_teams_analyzed"] = len(teams)

        return {
            "read_only": True,
            "summary": summary,
            "gaps": gaps,
            "gap_types_supported": sorted(GAP_TYPES),
        }

    @staticmethod
    def _empty_summary() -> Dict[str, Any]:
        return {
            "orders_analyzed": 0,
            "total_tasks_analyzed": 0,
            "tasks_with_employee": 0,
            "tasks_without_employee": 0,
            "tasks_completed": 0,
            "tasks_started_not_completed": 0,
            "tasks_completed_without_materials": 0,
            "materials_without_task_id": 0,
            "materials_without_reporter": 0,
            "field_installation_teams_analyzed": 0,
            "field_installations_started_not_completed": 0,
            "field_installations_completed_without_photos": 0,
            "total_gaps": 0,
            "gaps_by_severity": {"info": 0, "warning": 0, "critical": 0},
            "gaps_by_category": {"atelier": 0, "materiale": 0, "montaj_teren": 0},
        }
