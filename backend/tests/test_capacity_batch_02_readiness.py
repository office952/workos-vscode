"""Capacity Batch 02 — DEC-006 minutes + machine mapping + maintenance honesty."""

from __future__ import annotations

import json
from datetime import date
from types import SimpleNamespace

from schemas.execution_plan_v2 import PLANNING_MINUTES_WARNING
from services.capacity_batch_02_readiness import (
    LABEL_NULL_WARN,
    apply_maintenance_to_available,
    build_machine_mapping_readiness,
    extract_maintenance_windows,
    parse_estimated_minutes,
    scan_minutes_readiness,
)
from services.capacity_shift_model import build_calendar_shift_capacity


def test_parse_estimated_minutes_null_not_invented():
    assert parse_estimated_minutes({}) is None
    assert parse_estimated_minutes({"estimated_minutes": None}) is None
    assert parse_estimated_minutes({"estimated_minutes": ""}) is None
    assert parse_estimated_minutes({"estimated_minutes": "x"}) is None
    assert parse_estimated_minutes({"estimated_minutes": -1}) is None
    assert parse_estimated_minutes({"estimated_minutes": 15}) == 15.0
    assert parse_estimated_minutes({"estimated_time_minutes": 8}) == 8.0


def test_scan_minutes_null_warn_and_valid_sum():
    plans = [
        SimpleNamespace(
            order_id=1,
            tasks_json=json.dumps(
                {
                    "source": "order_snapshot_v2",
                    "planned_tasks": [
                        {
                            "task_id": "T1",
                            "workcenter": "CNC",
                            "estimated_minutes": 100,
                        },
                        {
                            "task_id": "T2",
                            "workcenter": "CNC",
                            "estimated_minutes": None,
                        },
                        {
                            "task_id": "T3",
                            "workcenter": "Print",
                        },
                    ],
                    "operational_tasks": [],
                }
            ),
        )
    ]
    result = scan_minutes_readiness(plans)
    assert result["plannedMinutesByWc"]["CNC"] == 100.0
    assert "Print" not in result["plannedMinutesByWc"]
    assert result["tasksWithMinutes"] == 1
    assert result["tasksMissingMinutes"] == 2
    assert result["materialize"] == "BLOCKED"
    assert any(PLANNING_MINUTES_WARNING in w for w in result["warnings"])
    assert any(LABEL_NULL_WARN in w for w in result["warnings"])
    assert result["dec006"]["noInvent"] is True


def test_machine_mapping_gap_util_and_maintenance_gap():
    machines = [
        {
            "machine_code": "M1",
            "name": "CNC 1",
            "workcenter_code": "WC_CNC",
            "operational_status": "active",
            "capacity_metadata": {"table_width_mm": 4000},
        },
        {
            "machine_code": "M2",
            "name": "Orphan",
            "workcenter_code": None,
            "operational_status": "maintenance",
            "capacity_metadata": {},
        },
    ]
    readiness = build_machine_mapping_readiness(machines, year=2026, month=7)
    assert readiness["summary"]["mappedToWc"] == 1
    assert readiness["summary"]["unmappedWc"] == 1
    assert readiness["maintenance"]["availability"] == "gap"
    assert readiness["policy"]["operationalAssignment"] is False
    assert readiness["policy"]["materialize"] == "BLOCKED"
    m1 = next(r for r in readiness["machines"] if r["machineCode"] == "M1")
    assert m1["machineUtilPct"] is None
    assert m1["machineUtilStatus"] == "GAP"
    assert m1["assignmentReadiness"] == "ready_for_mapping"


def test_calendarized_maintenance_deducts_available():
    machines = [
        {
            "machine_code": "M1",
            "name": "CNC 1",
            "workcenter_code": "CNC",
            "capacity_metadata": {
                "maintenance_windows": [
                    {"start": "2026-07-10", "end": "2026-07-11"},
                ]
            },
        }
    ]
    readiness = build_machine_mapping_readiness(machines, year=2026, month=7)
    assert readiness["maintenance"]["availability"] == "calendarized"
    assert readiness["maintenance"]["deductionMinutesByWc"]["CNC"] == 2 * 24 * 60
    windows = extract_maintenance_windows(machines[0]["capacity_metadata"])
    assert len(windows) == 1
    assert windows[0]["start"] == date(2026, 7, 10)

    base = 11040.0
    deducted, applied = apply_maintenance_to_available(
        base, 2880.0, maintenance_availability="calendarized"
    )
    assert applied == 2880.0
    assert deducted == 11040.0 - 2880.0
    gap_avail, gap_applied = apply_maintenance_to_available(
        base, 2880.0, maintenance_availability="gap"
    )
    assert gap_avail == base
    assert gap_applied is None

    model = build_calendar_shift_capacity(
        {"CNC": 1000.0},
        year=2026,
        month=7,
        maintenance_deduction_by_wc={"CNC": 2880.0},
        maintenance_availability="calendarized",
    )
    row = model["capacityLoad"][0]
    assert row["baseAvailableMinutes"] == 11040.0
    assert row["maintenanceDeductionMinutes"] == 2880.0
    assert row["availableMinutes"] == 8160.0
