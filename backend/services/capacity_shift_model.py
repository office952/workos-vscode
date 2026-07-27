"""Capacity Model Batch 01 — calendar/shift planned load (WC-level).

Owner CAP lock (do not renegotiate here):
  CAP-001 A: util% = planned_load_min / shift_available_min per workcenter
  CAP-002 A: Company Calendar (Mon–Fri 8h, RO holidays) as denominator
  CAP-003: Batch 02 may subtract calendarized maintenance only (else GAP)
  CAP-004 A: missing estimated_minutes → null + warn (no invent)
  CAP-005 A: numerator = sum valid estimated_minutes on planning tasks by WC
  CAP-006 D: WC-level util%; machine util stays GAP without assignment truth
  CAP-007 A: overload = warning only (never blocks commercial)
  CAP-008 A: no CostEngine coupling
  CAP-010 A: no materialize/sessions

HR productive hours are a separate domain — never mixed into util%.
Client pricing is never derived from this model.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List, Mapping, Optional

from services.company_calendar import (
    WORK_HOURS_PER_DAY,
    count_company_workdays_in_month,
)

MINUTES_PER_HOUR = 60.0

DEFAULT_WORKCENTERS: tuple[str, ...] = (
    "Print",
    "Laminare",
    "Cut / Plotter",
    "CNC",
    "Metal / Sudură",
    "Asamblare",
    "Electric",
    "Ambalare",
)

OWNER_CAP_LOCK: Dict[str, str] = {
    "CAP-001": "A",
    "CAP-002": "A",
    "CAP-003": "C",
    "CAP-004": "A",
    "CAP-005": "A",
    "CAP-006": "D",
    "CAP-007": "A",
    "CAP-008": "A",
    "CAP-009": "D",
    "CAP-010": "A",
}


def clamp_pct(value: float) -> int:
    if value < 0:
        return 0
    if value > 100:
        return 100
    return int(round(value))


def shift_available_minutes_for_month(year: int, month: int) -> float:
    """Firm shift pool minutes for one WC slot in the month (CAP-002=A, CAP-006=D)."""
    workdays = count_company_workdays_in_month(year, month)
    return float(workdays) * WORK_HOURS_PER_DAY * MINUTES_PER_HOUR


def planned_over_shift_pct(planned_minutes: float, available_minutes: float) -> int:
    """CAP-001: planned load / shift available. Display clamped 0–100."""
    if available_minutes <= 0:
        return 0
    return clamp_pct((float(planned_minutes) / float(available_minutes)) * 100.0)


def raw_load_ratio(planned_minutes: float, available_minutes: float) -> Optional[float]:
    if available_minutes <= 0:
        return None
    return float(planned_minutes) / float(available_minutes)


def build_calendar_shift_capacity(
    planned_minutes_by_wc: Mapping[str, float],
    *,
    year: Optional[int] = None,
    month: Optional[int] = None,
    default_workcenters: Optional[Iterable[str]] = None,
    actual_minutes_by_wc: Optional[Mapping[str, float]] = None,
    maintenance_deduction_by_wc: Optional[Mapping[str, float]] = None,
    maintenance_availability: str = "gap",
) -> Dict[str, Any]:
    """Build WC capacity rows. calendarShiftUtilAvailable is True when denominator exists."""
    today = date.today()
    y = int(year if year is not None else today.year)
    m = int(month if month is not None else today.month)
    base_available = shift_available_minutes_for_month(y, m)
    actuals = actual_minutes_by_wc or {}
    maint = maintenance_deduction_by_wc or {}

    names: List[str] = []
    seen: set[str] = set()
    for source in (planned_minutes_by_wc.keys(), default_workcenters or DEFAULT_WORKCENTERS):
        for name in source:
            label = str(name or "").strip() or "—"
            if label not in seen:
                seen.add(label)
                names.append(label)

    rows: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for wc_name in names:
        planned = float(planned_minutes_by_wc.get(wc_name) or 0.0)
        actual = float(actuals.get(wc_name) or 0.0)
        deduction = float(maint.get(wc_name) or 0.0)
        if maintenance_availability == "calendarized" and deduction > 0:
            available = max(0.0, base_available - deduction)
            maint_applied = deduction
        else:
            available = base_available
            maint_applied = None
        ratio = raw_load_ratio(planned, available)
        load_pct = planned_over_shift_pct(planned, available)
        overrun = max(0.0, actual - planned)
        row_warnings: List[str] = []
        if ratio is not None and ratio > 1.0:
            msg = (
                f"capacity_overload_warning:{wc_name}:"
                f"planned={round(planned, 1)}>available={round(available, 1)}"
            )
            row_warnings.append(msg)
            warnings.append(msg)

        rows.append(
            {
                "workcenterId": (
                    f"wc_{wc_name.lower().replace(' ', '_').replace('/', '_')}"
                ),
                "workcenterName": wc_name,
                "loadToday": load_pct,
                "load7d": load_pct,
                "load30d": load_pct,
                "availableToday": max(100 - load_pct, 0),
                "plannedMinutes": round(planned, 1),
                "actualMinutes": round(actual, 1),
                "overrunMinutes": round(overrun, 1),
                "availableMinutes": round(available, 1),
                "baseAvailableMinutes": round(base_available, 1),
                "maintenanceDeductionMinutes": (
                    None if maint_applied is None else round(maint_applied, 1)
                ),
                "maintenanceAvailability": maintenance_availability,
                "rawLoadRatio": None if ratio is None else round(ratio, 4),
                "loadKind": "calendar_shift_planned_load",
                "loadLabel": "Planned load / ore shift (WC)",
                "window": f"month_{y:04d}_{m:02d}",
                "explanation": (
                    "planned_minutes / company_shift_available_minutes pe workcenter, "
                    "clamp 0–100 pentru bară. Nu este HR ore productive, nu tarif client."
                ),
                "warnings": row_warnings,
                "warningNonBlocking": True,
            }
        )

    mean_util = 0
    active = [r["loadToday"] for r in rows if float(r.get("plannedMinutes") or 0) > 0]
    if active:
        mean_util = int(round(sum(active) / len(active)))

    return {
        "calendarShiftUtilAvailable": True,
        "year": y,
        "month": m,
        "availableMinutesMonth": round(available, 1),
        "workdaysInMonth": count_company_workdays_in_month(y, m),
        "hoursPerDay": WORK_HOURS_PER_DAY,
        "meanUtilPctActiveWc": mean_util,
        "capacityLoad": rows,
        "warnings": warnings,
        "ownerCapLock": dict(OWNER_CAP_LOCK),
        "boundary": (
            "Capacity / planned-load / WC shift util ≠ commercial tariff; "
            "≠ HR productive hours; ≠ CostEngine."
        ),
    }
