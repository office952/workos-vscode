"""Capacity Batch 04 — maintenance / assignment / machine-util gates + pre-materialize checklist.

Owner CAP lock (Batch 03 pack):
  CAP-011 A: maintenance_windows in capacity_metadata (calendarized)
  CAP-012 A: machine assignment truth = machine_code on operational task
  CAP-013: machine util% only when full gate; else GAP / NEEDS ASSIGNMENT TRUTH
  CAP-014: deduct available only for calendarized active/scheduled windows
  CAP-015: pre-materialize checklist; DEC-009 remains BLOCKED

Never invents downtime, minutes, or machine util%. Never calls materialize.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from services.capacity_batch_02_readiness import (
    extract_maintenance_windows,
    parse_estimated_minutes,
    workcenter_label,
)
from services.execution_plan_task_parser import parse_tasks_json_raw

OWNER_CAP_LOCK_BATCH_04: Dict[str, str] = {
    "CAP-011": "A",
    "CAP-012": "A",
    "CAP-013": "gated",
    "CAP-014": "calendarized_only",
    "CAP-015": "checklist_dec009_blocked",
}

STATUS_DEDUCTIBLE = frozenset({"scheduled", "active", ""})
LABEL_NEEDS_ASSIGNMENT = "NEEDS ASSIGNMENT TRUTH"
LABEL_GAP = "GAP"
LABEL_READY = "READY"
MATERIALIZE_BLOCKED = "BLOCKED"


def _window_is_deductible(raw: Mapping[str, Any]) -> bool:
    """CAP-014: only active/scheduled (+ active!=false) windows deduct."""
    if raw.get("active") is False:
        return False
    status = str(raw.get("status") or "").strip().lower()
    if status in ("done", "cancelled", "canceled", "inactive"):
        return False
    if status and status not in ("scheduled", "active"):
        # Unknown status with dates: warn path — do not deduct (no invent)
        return False
    return True


def validate_maintenance_windows(
    capacity_metadata: Any,
    *,
    year: int,
    month: int,
    machine_code: str = "",
    workcenter_code: str = "",
    operational_status: str = "",
) -> Dict[str, Any]:
    """Classify maintenance for one machine — calendarized deduct vs gap/status-only."""
    from calendar import monthrange

    from services.capacity_batch_02_readiness import overlap_minutes

    month_start = date(year, month, 1)
    month_end = date(year, month, monthrange(year, month)[1])
    windows = extract_maintenance_windows(capacity_metadata)
    deductible: List[Dict[str, Any]] = []
    ignored: List[str] = []
    downtime = 0.0

    for w in windows:
        raw = w.get("raw") or {}
        if not isinstance(raw, dict):
            continue
        if not _window_is_deductible(raw):
            ignored.append(
                f"maintenance_window_ignored:{machine_code}:status={raw.get('status')}"
            )
            continue
        mins = overlap_minutes(w["start"], w["end"], month_start, month_end)
        if mins <= 0:
            ignored.append(f"maintenance_window_no_overlap:{machine_code}")
            continue
        downtime += mins
        deductible.append(
            {
                "machineCode": machine_code,
                "workcenterCode": workcenter_code or None,
                "start": w["start"].isoformat(),
                "end": w["end"].isoformat(),
                "reason": raw.get("reason"),
                "status": raw.get("status") or "scheduled",
                "overlapMinutes": round(mins, 1),
            }
        )

    status_only = (
        str(operational_status or "").lower() == "maintenance" and not deductible
    )
    if deductible:
        availability = "calendarized"
        notice = "Calendarized maintenance_windows — deducted from available."
    elif status_only:
        availability = "gap"
        notice = (
            "maintenance availability: gap — operational_status=maintenance "
            "fără maintenance_windows calendarizate (nu inventăm downtime)."
        )
    elif windows and not deductible:
        availability = "gap"
        notice = (
            "maintenance availability: gap — windows prezente dar inactive/cancelled "
            "sau fără overlap (nu scădem)."
        )
    else:
        availability = "gap"
        notice = (
            "maintenance availability: gap — fără maintenance_windows în capacity_metadata."
        )

    return {
        "availability": availability,
        "notice": notice,
        "statusOnlyMaintenance": status_only,
        "deductibleWindows": deductible,
        "downtimeMinutesMonth": round(downtime, 1),
        "ignored": ignored[:20],
        "contract": "CAP-011A/CAP-014",
    }


def extract_machine_code_from_task(task: Mapping[str, Any]) -> Optional[str]:
    for key in (
        "machine_code",
        "assigned_machine_code",
        "assignedMachineCode",
        "machineCode",
    ):
        raw = task.get(key)
        if raw is None:
            continue
        text = str(raw).strip()
        if text:
            return text
    return None


def evaluate_machine_assignment_truth(
    task: Mapping[str, Any],
    *,
    machines_by_code: Mapping[str, Mapping[str, Any]],
    layer: str,
) -> Dict[str, Any]:
    """CAP-012: truth only on operational layer with machine_code mapped to same WC."""
    machine_code = extract_machine_code_from_task(task)
    task_wc = workcenter_label(task)
    minutes = parse_estimated_minutes(task)

    if layer != "operational_tasks":
        return {
            "hasTruth": False,
            "status": LABEL_NEEDS_ASSIGNMENT,
            "reason": "not_operational_layer",
            "machineCode": machine_code,
            "workcenter": task_wc,
            "estimatedMinutes": minutes,
            "layer": layer,
        }
    if not machine_code:
        return {
            "hasTruth": False,
            "status": LABEL_NEEDS_ASSIGNMENT,
            "reason": "missing_machine_code",
            "machineCode": None,
            "workcenter": task_wc,
            "estimatedMinutes": minutes,
            "layer": layer,
        }
    machine = machines_by_code.get(machine_code)
    if machine is None:
        return {
            "hasTruth": False,
            "status": LABEL_NEEDS_ASSIGNMENT,
            "reason": "machine_not_in_registry",
            "machineCode": machine_code,
            "workcenter": task_wc,
            "estimatedMinutes": minutes,
            "layer": layer,
        }
    m_wc = str(machine.get("workcenter_code") or "").strip()
    if not m_wc:
        return {
            "hasTruth": False,
            "status": LABEL_NEEDS_ASSIGNMENT,
            "reason": "machine_unmapped_wc",
            "machineCode": machine_code,
            "workcenter": task_wc,
            "estimatedMinutes": minutes,
            "layer": layer,
        }
    # Soft WC consistency: if task WC unknown, still allow mapped machine
    if task_wc not in ("Unknown", "—", "") and m_wc != task_wc:
        # Allow if one contains the other (CNC vs WC_CNC) — else fail truth
        a, b = m_wc.upper(), task_wc.upper()
        if a not in b and b not in a and a.replace("WC_", "") != b.replace("WC_", ""):
            return {
                "hasTruth": False,
                "status": LABEL_NEEDS_ASSIGNMENT,
                "reason": "wc_mismatch",
                "machineCode": machine_code,
                "workcenter": task_wc,
                "machineWorkcenter": m_wc,
                "estimatedMinutes": minutes,
                "layer": layer,
            }
    if str(machine.get("operational_status") or "").lower() == "decommissioned":
        return {
            "hasTruth": False,
            "status": LABEL_NEEDS_ASSIGNMENT,
            "reason": "machine_decommissioned",
            "machineCode": machine_code,
            "workcenter": task_wc,
            "estimatedMinutes": minutes,
            "layer": layer,
        }
    if machine.get("is_active") is False:
        return {
            "hasTruth": False,
            "status": LABEL_NEEDS_ASSIGNMENT,
            "reason": "machine_inactive",
            "machineCode": machine_code,
            "workcenter": task_wc,
            "estimatedMinutes": minutes,
            "layer": layer,
        }
    return {
        "hasTruth": True,
        "status": LABEL_READY,
        "reason": "assignment_truth_ok",
        "machineCode": machine_code,
        "workcenter": task_wc,
        "machineWorkcenter": m_wc,
        "estimatedMinutes": minutes,
        "layer": layer,
    }


def evaluate_machine_util_gate(
    *,
    calendar_shift_ok: bool,
    assignment: Mapping[str, Any],
    maintenance_availability: str,
    materialize_status: str = MATERIALIZE_BLOCKED,
) -> Dict[str, Any]:
    """CAP-013: all conditions required before machine util% may be shown."""
    checks = {
        "wcCalendarShiftModel": bool(calendar_shift_ok),
        "estimatedMinutesPresent": assignment.get("estimatedMinutes") is not None,
        "assignmentTruth": bool(assignment.get("hasTruth")),
        "machineMappedWc": assignment.get("reason")
        not in ("machine_unmapped_wc", "machine_not_in_registry", "missing_machine_code"),
        "maintenancePolicyKnown": maintenance_availability in ("calendarized", "gap"),
        "materializeOpen": materialize_status == "OPEN",
    }
    # maintenancePolicyKnown is always true with our classifier; materialize must be OPEN
    allowed = all(
        [
            checks["wcCalendarShiftModel"],
            checks["estimatedMinutesPresent"],
            checks["assignmentTruth"],
            checks["materializeOpen"],
        ]
    )
    if allowed:
        return {
            "allowed": True,
            "status": LABEL_READY,
            "machineUtilPct": None,  # Batch 04 does not compute % — only opens gate
            "note": "Gate OPEN — machine util% may be computed in a later GO; not invented here.",
            "checks": checks,
        }
    missing = [k for k, v in checks.items() if not v and k != "maintenancePolicyKnown"]
    status = LABEL_NEEDS_ASSIGNMENT if not checks["assignmentTruth"] or not checks["materializeOpen"] else LABEL_GAP
    return {
        "allowed": False,
        "status": status,
        "machineUtilPct": None,
        "note": (
            f"{status} — machine util% gated (CAP-013). "
            f"Missing: {', '.join(missing) or 'n/a'}."
        ),
        "checks": checks,
    }


def scan_assignment_and_util_gates(
    plans: Sequence[Any],
    machines: Sequence[Mapping[str, Any]],
    *,
    calendar_shift_ok: bool = True,
    year: int,
    month: int,
) -> Dict[str, Any]:
    machines_by_code = {
        str(m.get("machine_code") or "").strip(): m
        for m in machines
        if str(m.get("machine_code") or "").strip()
    }
    # Per-machine maintenance classification
    maint_by_machine: Dict[str, Dict[str, Any]] = {}
    deduction_by_wc: Dict[str, float] = {}
    any_calendarized = False
    status_only_count = 0
    for m in machines:
        code = str(m.get("machine_code") or "").strip()
        wc = str(m.get("workcenter_code") or "").strip()
        classified = validate_maintenance_windows(
            m.get("capacity_metadata"),
            year=year,
            month=month,
            machine_code=code,
            workcenter_code=wc,
            operational_status=str(m.get("operational_status") or ""),
        )
        maint_by_machine[code] = classified
        if classified["availability"] == "calendarized":
            any_calendarized = True
            if wc and classified["downtimeMinutesMonth"] > 0:
                deduction_by_wc[wc] = (
                    deduction_by_wc.get(wc, 0.0) + float(classified["downtimeMinutesMonth"])
                )
        if classified.get("statusOnlyMaintenance"):
            status_only_count += 1

    global_maint_availability = "calendarized" if any_calendarized else "gap"

    task_evals: List[Dict[str, Any]] = []
    truth_count = 0
    needs_count = 0
    for plan in plans:
        order_id = getattr(plan, "order_id", None)
        parsed = parse_tasks_json_raw(getattr(plan, "tasks_json", None))
        # Evaluate operational tasks for truth; planned only as draft (never truth)
        for layer_name, tasks in (
            ("operational_tasks", parsed.operational_tasks),
            ("planned_tasks", parsed.planned_tasks),
        ):
            for task in tasks:
                if not isinstance(task, dict):
                    continue
                assignment = evaluate_machine_assignment_truth(
                    task,
                    machines_by_code=machines_by_code,
                    layer=layer_name,
                )
                m_code = assignment.get("machineCode") or ""
                m_maint = maint_by_machine.get(str(m_code), {})
                gate = evaluate_machine_util_gate(
                    calendar_shift_ok=calendar_shift_ok,
                    assignment=assignment,
                    maintenance_availability=str(
                        m_maint.get("availability") or global_maint_availability
                    ),
                    materialize_status=MATERIALIZE_BLOCKED,
                )
                if assignment.get("hasTruth"):
                    truth_count += 1
                else:
                    needs_count += 1
                task_evals.append(
                    {
                        "orderId": order_id,
                        "taskId": task.get("task_id") or task.get("id"),
                        "assignment": assignment,
                        "utilGate": gate,
                    }
                )

    # Per-machine util status (no % without gate)
    machine_util_rows: List[Dict[str, Any]] = []
    for code, m in machines_by_code.items():
        # Any operational truth for this machine?
        related = [
            e
            for e in task_evals
            if e.get("assignment", {}).get("machineCode") == code
            and e.get("assignment", {}).get("hasTruth")
        ]
        if related and any(e["utilGate"].get("allowed") for e in related):
            util_status = LABEL_READY
            util_note = "Gate OPEN (util% computation deferred — not invented)."
            util_pct = None
        elif related:
            util_status = LABEL_NEEDS_ASSIGNMENT
            util_note = related[0]["utilGate"].get("note") or LABEL_NEEDS_ASSIGNMENT
            util_pct = None
        else:
            util_status = LABEL_GAP
            util_note = (
                f"{LABEL_GAP} / {LABEL_NEEDS_ASSIGNMENT} — no operational "
                f"machine_code assignment (CAP-012/013). Materialize {MATERIALIZE_BLOCKED}."
            )
            util_pct = None
        m_maint = maint_by_machine.get(code, {})
        machine_util_rows.append(
            {
                "machineCode": code,
                "name": m.get("name"),
                "workcenterCode": m.get("workcenter_code"),
                "machineUtilPct": util_pct,
                "machineUtilStatus": util_status,
                "machineUtilNote": util_note,
                "maintenanceAvailability": m_maint.get("availability") or "gap",
                "maintenanceNotice": m_maint.get("notice"),
                "statusOnlyMaintenance": bool(m_maint.get("statusOnlyMaintenance")),
            }
        )

    return {
        "batch": "capacity_batch_04",
        "ownerCapLock": dict(OWNER_CAP_LOCK_BATCH_04),
        "materialize": MATERIALIZE_BLOCKED,
        "maintenance": {
            "availability": global_maint_availability,
            "statusOnlyCount": status_only_count,
            "deductionMinutesByWc": {
                k: round(v, 1) for k, v in sorted(deduction_by_wc.items())
            },
            "notice": (
                "Calendarized maintenance_windows deducted from WC available."
                if any_calendarized
                else "maintenance availability: gap — no deductible calendarized windows."
            ),
            "byMachine": maint_by_machine,
        },
        "assignment": {
            "truthCount": truth_count,
            "needsAssignmentCount": needs_count,
            "policy": "machine_code on operational_tasks only (CAP-012A)",
            "sample": task_evals[:30],
        },
        "machineUtil": {
            "rows": machine_util_rows,
            "policy": "CAP-013 gated — pct never invented when gate closed",
        },
    }


def build_pre_materialize_checklist(
    *,
    minutes_readiness: Mapping[str, Any],
    mapping_summary: Mapping[str, Any],
    gates: Mapping[str, Any],
    dec009: str = "A",
) -> Dict[str, Any]:
    """CAP-015 visible checklist — why DEC-009 stays blocked."""
    missing_minutes = int(minutes_readiness.get("tasksMissingMinutes") or 0)
    with_minutes = int(minutes_readiness.get("tasksWithMinutes") or 0)
    mapped = int(mapping_summary.get("mappedToWc") or 0)
    unmapped = int(mapping_summary.get("unmappedWc") or 0)
    maint = (gates.get("maintenance") or {}).get("availability") or "gap"
    truth = int((gates.get("assignment") or {}).get("truthCount") or 0)

    items = [
        {
            "id": "DEC-003_004_005_007",
            "label": "Semantic DEC-003/004/005/007 answered (route 21)",
            "status": "OWNER_PENDING",
            "blocking": True,
            "detail": "Not auto-verified in Capacity Batch 04 — Owner/route gate.",
        },
        {
            "id": "CAP-011",
            "label": "Maintenance windows contract (CAP-011A)",
            "status": LABEL_READY if maint == "calendarized" else "GAP",
            "blocking": False,
            "detail": (
                "Calendarized windows present."
                if maint == "calendarized"
                else "No deductible maintenance_windows — gap (OK to proceed with warn)."
            ),
        },
        {
            "id": "DEC-006",
            "label": "estimated_minutes coverage (DEC-006)",
            "status": "WARN" if missing_minutes > 0 else LABEL_READY,
            "blocking": False,
            "detail": f"{with_minutes} with minutes · {missing_minutes} NULL+WARN",
        },
        {
            "id": "WC_MAPPING",
            "label": "WC → machine registry mapping",
            "status": "WARN" if unmapped > 0 else (LABEL_READY if mapped > 0 else "GAP"),
            "blocking": False,
            "detail": f"{mapped} mapped · {unmapped} unmapped",
        },
        {
            "id": "CAP-012",
            "label": "Machine assignment truth on operational tasks",
            "status": LABEL_READY if truth > 0 else LABEL_NEEDS_ASSIGNMENT,
            "blocking": True,
            "detail": (
                f"{truth} operational assignments with machine_code"
                if truth > 0
                else "No operational machine_code — requires materialize + assignment (blocked)."
            ),
        },
        {
            "id": "DEC-007",
            "label": "Dependency model (DEC-007)",
            "status": "OWNER_PENDING",
            "blocking": True,
            "detail": "Shop graph dependency — Owner/route gate.",
        },
        {
            "id": "DEC-009",
            "label": "POST materialize GO (DEC-009)",
            "status": "BLOCKED" if dec009 == "A" else "OPEN",
            "blocking": True,
            "detail": (
                "DEC-009=A — materialize remains BLOCKED until Owner sets B "
                "and blockers above clear."
            ),
        },
        {
            "id": "COMMERCIAL",
            "label": "Capacity warnings non-blocking for commercial offer",
            "status": LABEL_READY,
            "blocking": False,
            "detail": "Policy locked — overload/minutes warns do not block offers.",
        },
    ]
    blockers = [i for i in items if i["blocking"] and i["status"] not in (LABEL_READY, "OPEN")]
    return {
        "materialize": MATERIALIZE_BLOCKED,
        "dec009": dec009,
        "readyForMaterializeGo": False,
        "blockerCount": len(blockers),
        "items": items,
        "summary": (
            f"DEC-009 blocked — {len(blockers)} capacity/route blockers still open. "
            "No POST materialize from Capacity Batch 04."
        ),
    }
