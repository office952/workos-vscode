"""G6 — Dashboard KPI metric honesty (machine util + throughput today)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from routers.dashboard_stats import (
    _aggregate_workcenter_minutes,
    _clamp_pct,
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
