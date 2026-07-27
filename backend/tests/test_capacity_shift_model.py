"""Capacity Batch 01 — calendar/shift planned load model (Owner CAP lock)."""

from __future__ import annotations

from services.capacity_shift_model import (
    OWNER_CAP_LOCK,
    build_calendar_shift_capacity,
    planned_over_shift_pct,
    shift_available_minutes_for_month,
)
from services.company_calendar import count_company_workdays_in_month


def test_owner_cap_lock_matches_batch_01():
    assert OWNER_CAP_LOCK["CAP-001"] == "A"
    assert OWNER_CAP_LOCK["CAP-002"] == "A"
    assert OWNER_CAP_LOCK["CAP-007"] == "A"
    assert OWNER_CAP_LOCK["CAP-008"] == "A"
    assert OWNER_CAP_LOCK["CAP-010"] == "A"


def test_shift_available_minutes_july_2026():
    # 23 company workdays × 8h × 60 = 11040
    assert count_company_workdays_in_month(2026, 7) == 23
    assert shift_available_minutes_for_month(2026, 7) == 11040.0


def test_util_pct_is_planned_over_shift_not_hr_hours():
    available = shift_available_minutes_for_month(2026, 7)
    # Half month planned on one WC → ~50%
    planned = available * 0.5
    assert planned_over_shift_pct(planned, available) == 50
    assert planned_over_shift_pct(0, available) == 0
    assert planned_over_shift_pct(available * 2, available) == 100  # clamped


def test_build_model_marks_calendar_available_and_warns_overload():
    available = shift_available_minutes_for_month(2026, 7)
    model = build_calendar_shift_capacity(
        {"CNC": available * 1.5, "Print": 0.0},
        year=2026,
        month=7,
        default_workcenters=("CNC", "Print"),
    )
    assert model["calendarShiftUtilAvailable"] is True
    assert model["availableMinutesMonth"] == 11040.0
    by_name = {r["workcenterName"]: r for r in model["capacityLoad"]}
    assert by_name["CNC"]["loadToday"] == 100
    assert by_name["CNC"]["rawLoadRatio"] == 1.5
    assert by_name["CNC"]["warningNonBlocking"] is True
    assert any("capacity_overload_warning:CNC" in w for w in model["warnings"])
    assert by_name["Print"]["loadToday"] == 0
    assert model["meanUtilPctActiveWc"] == 100  # only CNC has planned>0
    assert "CostEngine" in model["boundary"] or "commercial" in model["boundary"]
