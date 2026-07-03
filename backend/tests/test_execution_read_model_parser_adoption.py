"""Step 9.3.5 — shared parser adoption in admin/reporting read models."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from routers.dashboard_stats import (
    _plan_operational_tasks as dashboard_plan_tasks,
    _task_estimated_minutes,
)
from routers.reports_summary import _plan_operational_tasks as reports_plan_tasks
from services.execution_plan_task_parser import operational_tasks_only
from services.operational_reports_service import OperationalReportsService

BACKEND_ROOT = Path(__file__).resolve().parents[1]
STEP_PATHS = (
    BACKEND_ROOT / "routers" / "dashboard_stats.py",
    BACKEND_ROOT / "routers" / "reports_summary.py",
    BACKEND_ROOT / "services" / "operational_reports_service.py",
    Path(__file__).resolve(),
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
    "/price",
)


def _legacy_tasks() -> str:
    return json.dumps(
        [
            {
                "task_id": "T-V1",
                "workcenter": "Print",
                "estimated_minutes": 10,
            }
        ]
    )


def _v2_envelope(*, operational: list | None = None) -> str:
    envelope: dict = {
        "source": "order_snapshot_v2",
        "planned_tasks": [
            {
                "task_key": "cnc_face_cut",
                "label": "CNC Face Cut",
                "canonical_task_type": "cnc_routing",
            }
        ],
        "execution_tasks_created": bool(operational),
    }
    if operational is not None:
        envelope["operational_tasks"] = operational
    return json.dumps(envelope)


# ---------------------------------------------------------------------------
# Dashboard / reports parser counts
# ---------------------------------------------------------------------------


def test_dashboard_counts_v1_flat_tasks():
    tasks = dashboard_plan_tasks(_legacy_tasks())
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "T-V1"


def test_dashboard_counts_v2_materialized_operational_tasks():
    operational = [
        {
            "task_id": "cnc_face_cut",
            "machine_type": "CNC",
            "estimated_time_minutes": 20,
        }
    ]
    tasks = dashboard_plan_tasks(_v2_envelope(operational=operational))
    assert len(tasks) == 1
    assert _task_estimated_minutes(tasks[0]) == 20.0


def test_dashboard_does_not_count_planned_tasks_when_not_materialized():
    raw = _v2_envelope()
    assert len(dashboard_plan_tasks(raw)) == 0
    parsed = operational_tasks_only(raw)
    assert len(parsed) == 0


def test_reports_summary_counts_v1_flat_tasks():
    assert len(reports_plan_tasks(_legacy_tasks())) == 1


def test_reports_summary_counts_v2_materialized_operational_tasks():
    operational = [{"task_id": "cnc_face_cut", "estimated_time_minutes": 15}]
    assert len(reports_plan_tasks(_v2_envelope(operational=operational))) == 1


def test_reports_summary_does_not_use_planned_tasks_fallback():
    assert len(reports_plan_tasks(_v2_envelope())) == 0


def test_invalid_tasks_json_does_not_crash_read_model_helpers():
    assert dashboard_plan_tasks("{bad-json") == []
    assert reports_plan_tasks("{bad-json") == []
    assert dashboard_plan_tasks(None) == []


# ---------------------------------------------------------------------------
# Operational reports plan metrics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_operational_reports_counts_v2_materialized_plan_tasks(db_session):
    order_id = 40001
    operational = [{"task_id": "cnc_face_cut", "process_type": "cnc_routing"}]
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-{order_id}",
            snapshot_version=1,
            tasks_json=_v2_envelope(operational=operational),
            total_estimated_time_minutes=15,
        )
    )
    await db_session.commit()

    summary = await OperationalReportsService(db_session).build_summary(order_id=order_id)
    completeness = summary["completeness_summary"]
    assert completeness["plan_operational_tasks_total"] == 1
    assert completeness["plan_orders_v2_not_materialized"] == 0


@pytest.mark.asyncio
async def test_operational_reports_zero_operational_tasks_for_v2_not_materialized(db_session):
    order_id = 40002
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-{order_id}",
            snapshot_version=1,
            tasks_json=_v2_envelope(),
            total_estimated_time_minutes=10,
        )
    )
    await db_session.commit()

    summary = await OperationalReportsService(db_session).build_summary(order_id=order_id)
    completeness = summary["completeness_summary"]
    assert completeness["plan_operational_tasks_total"] == 0
    assert completeness["plan_orders_v2_not_materialized"] == 1


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_model_parser_adoption_does_not_create_execution_reality(db_session):
    before = int(await db_session.scalar(select(func.count()).select_from(ExecutionReality)) or 0)
    dashboard_plan_tasks(_v2_envelope())
    reports_plan_tasks(_legacy_tasks())
    await OperationalReportsService(db_session).build_summary()
    after = int(await db_session.scalar(select(func.count()).select_from(ExecutionReality)) or 0)
    assert after == before


def test_procurement_already_uses_operational_tasks_only():
    source = (BACKEND_ROOT / "services" / "material_procurement_status_service.py").read_text(
        encoding="utf-8"
    )
    assert "operational_tasks_only" in source


def test_no_forbidden_pricing_imports():
    found: set[str] = set()
    for path in STEP_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                    if part in node.module:
                        found.add(f"{path.name}:{node.module}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                        if part in alias.name:
                            found.add(f"{path.name}:{alias.name}")
    assert not found, f"Forbidden imports: {found}"


def test_employee_mobile_and_frontend_not_in_step_scope():
    for path in STEP_PATHS:
        assert "employee_mobile" not in str(path).lower()
        assert "frontend" not in str(path).lower()
