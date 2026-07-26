"""G6/G7 — Dashboard KPI metric honesty (machine util + throughput + truth metadata)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from routers.dashboard_stats import (
    NOTICE_CALENDAR_SHIFT_GAP,
    _aggregate_workcenter_minutes,
    _build_capacity_load,
    _clamp_pct,
    _kpi,
    _machine_util_pct,
    _throughput_today_count,
)


def _plan(*, order_id: int, tasks: list[dict], total_est: float = 0) -> SimpleNamespace:
    return SimpleNamespace(
        order_id=order_id,
        tasks_json=json.dumps(tasks),
        total_estimated_time_minutes=total_est,
    )


def _reality(*, order_id: int, sessions: list[dict], total_actual: float = 0) -> SimpleNamespace:
    return SimpleNamespace(
        order_id=order_id,
        tasks_json=json.dumps(sessions),
        total_actual_time_minutes=total_actual,
    )


def test_clamp_pct_bounds():
    assert _clamp_pct(-5) == 0
    assert _clamp_pct(50.4) == 50
    assert _clamp_pct(100) == 100
    assert _clamp_pct(56596) == 100


def test_machine_util_never_explodes_like_global_overrun_ratio():
    """
    Former bug: Σactual/Σplanned×100 with tiny plans + huge actuals → 56596%.
    New semantics: mean per-WC planned-load completion, each WC clamped to 0–100.
    """
    plans = [
        _plan(
            order_id=1,
            total_est=100,
            tasks=[
                {"task_id": "T1", "workcenter": "CNC", "estimated_minutes": 100},
            ],
        )
    ]
    realities = [
        _reality(
            order_id=1,
            total_actual=56596,
            sessions=[
                {
                    "task_id": "T1",
                    "started_at": "2026-07-01T08:00:00Z",
                    "ended_at": "2026-07-26T18:00:00Z",
                    "actual_minutes": 56596,
                }
            ],
        )
    ]
    plans_by_order = {1: plans[0]}
    workcenters = _aggregate_workcenter_minutes(plans, realities, plans_by_order)
    util = _machine_util_pct(workcenters)

    # Global overrun would be ~56596%; mean clamped WC load must stay in [0, 100].
    assert 0 <= util <= 100
    assert util == 100


def test_machine_util_is_mean_of_workcenter_loads():
    plans = [
        _plan(
            order_id=1,
            tasks=[
                {"task_id": "A", "workcenter": "Print", "estimated_minutes": 100},
                {"task_id": "B", "workcenter": "CNC", "estimated_minutes": 100},
            ],
        )
    ]
    realities = [
        _reality(
            order_id=1,
            sessions=[
                {
                    "task_id": "A",
                    "started_at": "2026-07-26T08:00:00Z",
                    "ended_at": "2026-07-26T09:00:00Z",
                    "actual_minutes": 50,  # Print load 50%
                },
                {
                    "task_id": "B",
                    "started_at": "2026-07-26T09:00:00Z",
                    "ended_at": "2026-07-26T10:00:00Z",
                    "actual_minutes": 100,  # CNC load 100%
                },
            ],
        )
    ]
    workcenters = _aggregate_workcenter_minutes(plans, realities, {1: plans[0]})
    assert _machine_util_pct(workcenters) == 75


def test_machine_util_zero_when_no_planned_minutes():
    assert _machine_util_pct({}) == 0
    assert _machine_util_pct({"X": {"total_min": 0, "completed_min": 10}}) == 0


def test_throughput_today_counts_only_utc_calendar_day():
    now = datetime(2026, 7, 26, 15, 0, tzinfo=timezone.utc)
    orders = [
        SimpleNamespace(
            status="completed",
            updated_at=now - timedelta(hours=2),
        ),
        SimpleNamespace(
            status="completed",
            updated_at=now - timedelta(days=1),
        ),
        SimpleNamespace(
            status="in_execution",
            updated_at=now,
        ),
        SimpleNamespace(
            status="completed",
            updated_at=None,
        ),
    ]
    assert _throughput_today_count(orders, now=now) == 1


def test_throughput_today_naive_updated_at_treated_as_utc():
    now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    orders = [
        SimpleNamespace(
            status="completed",
            updated_at=datetime(2026, 7, 26, 8, 0),  # naive
        )
    ]
    assert _throughput_today_count(orders, now=now) == 1


def test_kpi_payload_includes_operational_truth_fields():
    payload = _kpi(
        code="KPI_MACHINE_UTIL",
        label="Load planificat WC",
        value=68,
        unit="%",
        status="good",
        kind="derived",
        window="lifetime_plan_vs_finished_sessions",
        explanation="mean planned-load",
        gap_note=NOTICE_CALENDAR_SHIFT_GAP,
    )
    assert payload["kind"] == "derived"
    assert payload["window"] == "lifetime_plan_vs_finished_sessions"
    assert "calendar/shift" in payload["gapNote"]
    assert "Load planificat" in payload["label"]


def test_capacity_load_exposes_planned_actual_overrun_and_clamped_pct():
    workcenters = {
        "CNC": {"total_min": 100.0, "completed_min": 250.0},
        "Print": {"total_min": 100.0, "completed_min": 40.0},
    }
    slots = _build_capacity_load(workcenters)
    by_name = {s["workcenterName"]: s for s in slots}
    assert by_name["CNC"]["loadToday"] == 100  # clamped
    assert by_name["CNC"]["plannedMinutes"] == 100.0
    assert by_name["CNC"]["actualMinutes"] == 250.0
    assert by_name["CNC"]["overrunMinutes"] == 150.0
    assert by_name["CNC"]["loadKind"] == "planned_load"
    assert by_name["Print"]["loadToday"] == 40
    assert by_name["Print"]["overrunMinutes"] == 0.0
