"""Capacity Batch 02 — minutes readiness + WC→machine mapping + maintenance honesty.

Owner order (CAPACITY_BATCH_02_OWNER_DIRECTION.md):
  1. DEC-006 estimated_minutes: valid → planned load; missing → null + warn (no invent)
  2. WC → utilaj mapping / assignment readiness (not operational assignment)
  3. Maintenance deducts available only with calendarized truth; else GAP
  4. Materialize remains blocked (this module never calls POST materialize)

Boundaries: no CostEngine, no HR hours denominator, no client pricing, no invent util%.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from schemas.execution_plan_v2 import PLANNING_MINUTES_WARNING
from services.execution_plan_task_parser import parse_tasks_json_raw

LABEL_MINUTES_REQUIRED = "PLANNING MINUTES REQUIRED"
LABEL_NULL_WARN = "NULL + WARN"
MINUTES_SOURCE_DEC006 = "task.estimated_minutes|estimated_time_minutes"


def parse_estimated_minutes(task: Mapping[str, Any]) -> Optional[float]:
    """Return valid planning minutes or None (never invent)."""
    raw = task.get("estimated_minutes")
    if raw is None:
        raw = task.get("estimated_time_minutes")
    if raw is None:
        return None
    if isinstance(raw, str) and not raw.strip():
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value < 0:
        return None
    return value


def task_identity(task: Mapping[str, Any], *, order_id: Any = None) -> str:
    tid = (
        task.get("task_id")
        or task.get("id")
        or task.get("operation_code")
        or task.get("task_name")
        or "unknown"
    )
    if order_id is not None:
        return f"order:{order_id}:task:{tid}"
    return str(tid)


def workcenter_label(task: Mapping[str, Any]) -> str:
    return str(
        task.get("workcenter")
        or task.get("workcenter_code")
        or task.get("machine_type")
        or "Unknown"
    )


def planning_tasks_from_plan(tasks_json: Optional[str]) -> Tuple[List[dict], str]:
    """Tasks used for capacity planning without materialize.

    Prefer operational_tasks when present; else planned_tasks (V2 envelope).
    """
    parsed = parse_tasks_json_raw(tasks_json)
    if parsed.operational_tasks:
        return list(parsed.operational_tasks), "operational_tasks"
    if parsed.planned_tasks:
        return list(parsed.planned_tasks), "planned_tasks"
    return [], parsed.format or "empty"


def scan_minutes_readiness(
    plans: Sequence[Any],
) -> Dict[str, Any]:
    """DEC-006 scan: sum valid minutes by WC; warn on null/missing."""
    planned_by_wc: Dict[str, float] = {}
    warnings: List[str] = []
    null_tasks: List[Dict[str, Any]] = []
    present_count = 0
    null_count = 0
    layer_counts: Dict[str, int] = {}

    for plan in plans:
        order_id = getattr(plan, "order_id", None)
        tasks_json = getattr(plan, "tasks_json", None)
        tasks, layer = planning_tasks_from_plan(tasks_json)
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
        for task in tasks:
            minutes = parse_estimated_minutes(task)
            wc = workcenter_label(task)
            identity = task_identity(task, order_id=order_id)
            if minutes is None:
                null_count += 1
                warn = (
                    f"estimated_minutes_null:{identity}:wc={wc}:"
                    f"{LABEL_NULL_WARN}:{PLANNING_MINUTES_WARNING}"
                )
                warnings.append(warn)
                null_tasks.append(
                    {
                        "taskRef": identity,
                        "workcenter": wc,
                        "estimatedMinutes": None,
                        "label": LABEL_MINUTES_REQUIRED,
                        "status": LABEL_NULL_WARN,
                        "warningCode": PLANNING_MINUTES_WARNING,
                        "layer": layer,
                    }
                )
                continue
            present_count += 1
            planned_by_wc[wc] = planned_by_wc.get(wc, 0.0) + float(minutes)

    return {
        "dec006": {
            "policy": "valid_minutes_sum_else_null_warn",
            "source": MINUTES_SOURCE_DEC006,
            "noInvent": True,
            "noCostEngine": True,
            "noCommercialPricing": True,
        },
        "plannedMinutesByWc": {
            k: round(v, 1) for k, v in sorted(planned_by_wc.items())
        },
        "tasksWithMinutes": present_count,
        "tasksMissingMinutes": null_count,
        "nullMinuteTasks": null_tasks[:40],
        "warnings": warnings[:80],
        "planningLayerCounts": layer_counts,
        "labels": {
            "required": LABEL_MINUTES_REQUIRED,
            "nullWarn": LABEL_NULL_WARN,
        },
        "materialize": "BLOCKED",
    }


def _parse_iso_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            return dt.date()
        return dt.astimezone(timezone.utc).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def overlap_minutes(start: date, end: date, month_start: date, month_end: date) -> float:
    """Whole-day overlap minutes within month (8h company day not applied — calendar downtime)."""
    if end < start:
        return 0.0
    lo = max(start, month_start)
    hi = min(end, month_end)
    if hi < lo:
        return 0.0
    days = (hi - lo).days + 1
    # Calendarized maintenance: count full days as 24h wall downtime on that machine.
    # WC pool available still uses shift minutes; we subtract machine downtime minutes
    # only when windows are explicit — Owner: no invent.
    return float(days) * 24.0 * 60.0


def extract_maintenance_windows(capacity_metadata: Any) -> List[Dict[str, Any]]:
    if capacity_metadata is None:
        return []
    meta = capacity_metadata
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except (TypeError, ValueError):
            return []
    if not isinstance(meta, dict):
        return []
    windows = meta.get("maintenance_windows") or meta.get("maintenanceWindows")
    if not isinstance(windows, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in windows:
        if not isinstance(item, dict):
            continue
        start = _parse_iso_date(item.get("start") or item.get("start_date") or item.get("from"))
        end = _parse_iso_date(item.get("end") or item.get("end_date") or item.get("to"))
        if start is None or end is None:
            continue
        out.append({"start": start, "end": end, "raw": item})
    return out


def build_machine_mapping_readiness(
    machines: Sequence[Mapping[str, Any]],
    *,
    year: int,
    month: int,
) -> Dict[str, Any]:
    """WC → utilaj mapping readiness. Never invent machine util%."""
    from calendar import monthrange

    month_start = date(year, month, 1)
    month_end = date(year, month, monthrange(year, month)[1])

    by_wc: Dict[str, List[Dict[str, Any]]] = {}
    machine_rows: List[Dict[str, Any]] = []
    maintenance_deduction_by_wc: Dict[str, float] = {}
    has_any_calendarized = False

    for m in machines:
        code = str(m.get("machine_code") or m.get("id") or "").strip()
        name = str(m.get("name") or code or "—")
        wc = str(m.get("workcenter_code") or m.get("workcenterId") or "").strip()
        mapped = bool(wc)
        status = str(m.get("operational_status") or "")
        meta = m.get("capacity_metadata")
        windows = extract_maintenance_windows(meta)
        downtime = 0.0
        for w in windows:
            downtime += overlap_minutes(w["start"], w["end"], month_start, month_end)
        if windows:
            has_any_calendarized = True
            if mapped and downtime > 0:
                maintenance_deduction_by_wc[wc] = (
                    maintenance_deduction_by_wc.get(wc, 0.0) + downtime
                )

        assignment_status = "mapped_wc" if mapped else "unmapped_wc"
        util_status = "GAP"
        util_note = (
            "Utilaj individual: GAP — fără assignment truth operațional "
            "(CAP-006; Batch 02 readiness only)."
        )
        row = {
            "machineCode": code,
            "name": name,
            "workcenterCode": wc or None,
            "mappingStatus": assignment_status,
            "assignmentReadiness": "ready_for_mapping" if mapped else "needs_wc_mapping",
            "operationalAssignment": False,
            "machineUtilPct": None,
            "machineUtilStatus": util_status,
            "machineUtilNote": util_note,
            "operationalStatus": status,
            "maintenanceWindowsCount": len(windows),
            "maintenanceDowntimeMinutesMonth": round(downtime, 1),
            "maintenanceAvailability": (
                "calendarized" if windows else "gap"
            ),
        }
        machine_rows.append(row)
        if mapped:
            by_wc.setdefault(wc, []).append(
                {
                    "machineCode": code,
                    "name": name,
                    "assignmentReadiness": row["assignmentReadiness"],
                    "machineUtilStatus": util_status,
                }
            )

    mapped_count = sum(1 for r in machine_rows if r["mappingStatus"] == "mapped_wc")
    unmapped_count = len(machine_rows) - mapped_count

    return {
        "policy": {
            "wcLevelPrimary": True,
            "machineUtilInventForbidden": True,
            "operationalAssignment": False,
            "materialize": "BLOCKED",
        },
        "workcenters": [
            {
                "workcenterCode": wc,
                "machineCount": len(items),
                "machines": items,
                "assignmentReadiness": "machines_mapped",
            }
            for wc, items in sorted(by_wc.items())
        ],
        "machines": machine_rows,
        "summary": {
            "machineCount": len(machine_rows),
            "mappedToWc": mapped_count,
            "unmappedWc": unmapped_count,
            "calendarizedMaintenancePresent": has_any_calendarized,
        },
        "maintenance": {
            "availability": "calendarized" if has_any_calendarized else "gap",
            "notice": (
                "Maintenance windows calendarizate găsite — scăzute din available pe WC."
                if has_any_calendarized
                else "maintenance availability: gap — fără maintenance_windows calendarizate în registry."
            ),
            "deductionMinutesByWc": {
                k: round(v, 1) for k, v in sorted(maintenance_deduction_by_wc.items())
            },
        },
    }


def apply_maintenance_to_available(
    base_available: float,
    deduction: float,
    *,
    maintenance_availability: str,
) -> Tuple[float, Optional[float]]:
    """Subtract maintenance only when calendarized truth exists."""
    if maintenance_availability != "calendarized":
        return float(base_available), None
    deducted = max(0.0, float(base_available) - max(0.0, float(deduction)))
    return deducted, max(0.0, float(deduction))
