"""Capacity Batch 04 — maintenance / assignment / machine-util gates + checklist."""

from __future__ import annotations

import json
from types import SimpleNamespace

from services.capacity_batch_02_readiness import overlap_minutes
from services.capacity_batch_04_gates import (
    LABEL_GAP,
    LABEL_NEEDS_ASSIGNMENT,
    MATERIALIZE_BLOCKED,
    build_pre_materialize_checklist,
    evaluate_machine_assignment_truth,
    evaluate_machine_util_gate,
    scan_assignment_and_util_gates,
    validate_maintenance_windows,
)
from datetime import date


def test_overlap_minutes_public_rename():
    assert (
        overlap_minutes(date(2026, 7, 10), date(2026, 7, 11), date(2026, 7, 1), date(2026, 7, 31))
        == 2 * 24 * 60
    )


def test_calendarized_maintenance_deducts_status_only_does_not():
    cal = validate_maintenance_windows(
        {
            "maintenance_windows": [
                {
                    "start": "2026-07-10",
                    "end": "2026-07-11",
                    "status": "scheduled",
                    "reason": "preventive",
                }
            ]
        },
        year=2026,
        month=7,
        machine_code="M1",
        workcenter_code="WC_CNC",
    )
    assert cal["availability"] == "calendarized"
    assert cal["downtimeMinutesMonth"] == 2 * 24 * 60
    assert len(cal["deductibleWindows"]) == 1

    status_only = validate_maintenance_windows(
        {},
        year=2026,
        month=7,
        machine_code="M2",
        operational_status="maintenance",
    )
    assert status_only["availability"] == "gap"
    assert status_only["statusOnlyMaintenance"] is True
    assert status_only["downtimeMinutesMonth"] == 0

    cancelled = validate_maintenance_windows(
        {
            "maintenance_windows": [
                {"start": "2026-07-10", "end": "2026-07-11", "status": "cancelled"}
            ]
        },
        year=2026,
        month=7,
        machine_code="M3",
    )
    assert cancelled["availability"] == "gap"
    assert cancelled["downtimeMinutesMonth"] == 0


def test_assignment_truth_requires_operational_machine_code():
    machines = {
        "MCH-CNC-01": {
            "machine_code": "MCH-CNC-01",
            "workcenter_code": "WC_CNC",
            "operational_status": "active",
            "is_active": True,
        }
    }
    planned = evaluate_machine_assignment_truth(
        {
            "task_id": "T1",
            "workcenter": "WC_CNC",
            "machine_code": "MCH-CNC-01",
            "estimated_minutes": 30,
        },
        machines_by_code=machines,
        layer="planned_tasks",
    )
    assert planned["hasTruth"] is False
    assert planned["status"] == LABEL_NEEDS_ASSIGNMENT
    assert planned["reason"] == "not_operational_layer"

    missing = evaluate_machine_assignment_truth(
        {"task_id": "T2", "workcenter": "WC_CNC", "estimated_minutes": 30},
        machines_by_code=machines,
        layer="operational_tasks",
    )
    assert missing["hasTruth"] is False
    assert missing["reason"] == "missing_machine_code"

    ok = evaluate_machine_assignment_truth(
        {
            "task_id": "T3",
            "workcenter": "WC_CNC",
            "machine_code": "MCH-CNC-01",
            "estimated_minutes": 45,
        },
        machines_by_code=machines,
        layer="operational_tasks",
    )
    assert ok["hasTruth"] is True
    assert ok["status"] == "READY"


def test_machine_util_gate_blocked_without_materialize_and_truth():
    assignment_ok = {
        "hasTruth": True,
        "estimatedMinutes": 40,
        "reason": "assignment_truth_ok",
    }
    closed = evaluate_machine_util_gate(
        calendar_shift_ok=True,
        assignment=assignment_ok,
        maintenance_availability="gap",
        materialize_status=MATERIALIZE_BLOCKED,
    )
    assert closed["allowed"] is False
    assert closed["machineUtilPct"] is None
    assert closed["status"] in (LABEL_NEEDS_ASSIGNMENT, LABEL_GAP)

    no_truth = evaluate_machine_util_gate(
        calendar_shift_ok=True,
        assignment={"hasTruth": False, "estimatedMinutes": 40, "reason": "missing_machine_code"},
        maintenance_availability="calendarized",
        materialize_status="OPEN",
    )
    assert no_truth["allowed"] is False
    assert no_truth["machineUtilPct"] is None

    open_gate = evaluate_machine_util_gate(
        calendar_shift_ok=True,
        assignment=assignment_ok,
        maintenance_availability="calendarized",
        materialize_status="OPEN",
    )
    assert open_gate["allowed"] is True
    assert open_gate["machineUtilPct"] is None  # Batch 04 does not invent %


def test_scan_and_checklist_keep_materialize_blocked():
    machines = [
        {
            "machine_code": "MCH-CNC-01",
            "name": "CNC 1",
            "workcenter_code": "WC_CNC",
            "operational_status": "active",
            "is_active": True,
            "capacity_metadata": {
                "maintenance_windows": [
                    {"start": "2026-07-15", "end": "2026-07-15", "status": "active"}
                ]
            },
        },
        {
            "machine_code": "MCH-PRINT-01",
            "name": "Print 1",
            "workcenter_code": "WC_PRINT",
            "operational_status": "maintenance",
            "is_active": True,
            "capacity_metadata": {},
        },
    ]
    plans = [
        SimpleNamespace(
            order_id=9,
            tasks_json=json.dumps(
                {
                    "source": "order_snapshot_v2",
                    "planned_tasks": [
                        {
                            "task_id": "P1",
                            "workcenter": "WC_CNC",
                            "machine_code": "MCH-CNC-01",
                            "estimated_minutes": 20,
                        }
                    ],
                    "operational_tasks": [],
                }
            ),
        )
    ]
    gates = scan_assignment_and_util_gates(
        plans, machines, calendar_shift_ok=True, year=2026, month=7
    )
    assert gates["materialize"] == MATERIALIZE_BLOCKED
    assert gates["maintenance"]["availability"] == "calendarized"
    assert gates["maintenance"]["statusOnlyCount"] == 1
    assert gates["maintenance"]["deductionMinutesByWc"]["WC_CNC"] == 24 * 60
    assert gates["assignment"]["truthCount"] == 0
    assert gates["assignment"]["needsAssignmentCount"] >= 1
    for row in gates["machineUtil"]["rows"]:
        assert row["machineUtilPct"] is None
        assert row["machineUtilStatus"] in (LABEL_GAP, LABEL_NEEDS_ASSIGNMENT, "READY")

    checklist = build_pre_materialize_checklist(
        minutes_readiness={"tasksMissingMinutes": 2, "tasksWithMinutes": 1},
        mapping_summary={"mappedToWc": 2, "unmappedWc": 0},
        gates=gates,
        dec009="A",
    )
    assert checklist["materialize"] == MATERIALIZE_BLOCKED
    assert checklist["readyForMaterializeGo"] is False
    assert checklist["blockerCount"] >= 1
    dec009 = next(i for i in checklist["items"] if i["id"] == "DEC-009")
    assert dec009["status"] == "BLOCKED"
    assert dec009["blocking"] is True
