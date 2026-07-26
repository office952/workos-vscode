"""Post-job truth V1 — actuals, reconciliation, profitability coverage."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.stock_movements import StockMovement
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SLICE_PATHS = (
    BACKEND_ROOT / "services" / "post_job_truth_service.py",
    BACKEND_ROOT / "routers" / "post_job_truth.py",
    BACKEND_ROOT / "schemas" / "post_job_truth.py",
    BACKEND_ROOT / "services" / "profitability_analysis_service.py",
    Path(__file__).resolve(),
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
)

_OID_BASE = 19700


def _forbidden_imports_in_paths() -> set[str]:
    found: set[str] = set()
    for path in SLICE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                    if part in node.module:
                        found.add(node.module)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                        if part in alias.name:
                            found.add(alias.name)
    return found


def _get_truth(auth_client, order_id: int):
    return auth_client.get(f"/api/v1/execution/{order_id}/post-job-truth")


def _get_profit(auth_client, order_id: int):
    return auth_client.get(f"/api/v1/profitability-analysis/order/{order_id}")


async def _seed_order_with_sessions(
    db_session,
    *,
    order_id: int,
    with_open_session: bool = False,
) -> Orders:
    order = await _seed_v2_order_with_snapshot(db_session, order_id=order_id)
    sessions = [
        {
            "session_id": "ws-primary-1",
            "task_id": "cnc_face_cut",
            "employee_id": 11,
            "employee_name": "Primary",
            "role": "primary",
            "session_type": "work",
            "started_at": "2026-07-16T08:00:00+00:00",
            "ended_at": "2026-07-16T09:00:00+00:00",
            "duration_minutes": 60,
        },
        {
            "session_id": "ws-helper-1",
            "task_id": "cnc_face_cut",
            "employee_id": 22,
            "employee_name": "Helper",
            "role": "helper",
            "session_type": "assist",
            "started_at": "2026-07-16T08:15:00+00:00",
            "ended_at": "2026-07-16T08:45:00+00:00",
            "duration_minutes": 30,
        },
    ]
    if with_open_session:
        sessions.append(
            {
                "session_id": "ws-open-1",
                "task_id": "cnc_face_cut",
                "employee_id": 33,
                "role": "helper",
                "started_at": "2026-07-16T10:00:00+00:00",
            }
        )
    reality = ExecutionReality(
        order_id=order.id,
        order_code=order.code,
        tasks_json=json.dumps(sessions),
        materials_json=json.dumps(
            [
                {
                    "material_id": None,
                    "material_name": "Observed free text",
                    "quantity": 2.0,
                    "unit": "pcs",
                    "task_id": "cnc_face_cut",
                }
            ]
        ),
        total_actual_time_minutes=90.0,
    )
    db_session.add(reality)
    plan = ExecutionPlan(
        order_id=order.id,
        order_code=order.code,
        snapshot_version=1,
        tasks_json=json.dumps(
            [
                {
                    "task_id": "cnc_face_cut",
                    "name": "CNC Face",
                    "estimated_time_minutes": 40,
                    "required_machine_type": "cnc",
                }
            ]
        ),
        total_estimated_time_minutes=40.0,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(order)
    return order


async def _seed_material_and_deduction(
    db_session,
    *,
    order: Orders,
    quantity: float = 1.5,
    unit_cost: float | None = 10.0,
) -> Inventory_materials:
    mat = Inventory_materials(
        code=f"MAT-PJT-{order.id}",
        name=f"PostJob Mat {order.id}",
        unit="sheet",
        stock_current=100.0,
        unit_cost=unit_cost,
    )
    db_session.add(mat)
    await db_session.flush()

    reality = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order.id)
        )
    ).scalar_one()
    materials = json.loads(reality.materials_json or "[]")
    materials.append(
        {
            "material_id": mat.id,
            "material_name": mat.name,
            "quantity": quantity,
            "unit": "sheet",
            "task_id": "cnc_face_cut",
        }
    )
    reality.materials_json = json.dumps(materials)

    movement = StockMovement(
        material_id=mat.id,
        source_type="execution_reality",
        source_id=reality.id,
        order_id=order.id,
        task_id="cnc_face_cut",
        quantity=quantity,
        unit="sheet",
        movement_type="consumption",
        old_stock=100.0,
        new_stock=100.0 - quantity,
        performed_by="test",
        performed_at=datetime.now(timezone.utc),
        reason="post_job_truth_test",
        idempotency_key=f"reality:{reality.id}:mat_idx:test",
    )
    db_session.add(movement)
    await db_session.commit()
    return mat


@pytest.mark.asyncio
async def test_post_job_truth_labor_minutes_include_helper(db_session, auth_client):
    order = await _seed_order_with_sessions(db_session, order_id=_OID_BASE + 1)
    before = order.snapshot_v2_json

    resp = _get_truth(auth_client, order.id)
    assert resp.status_code == 200
    body = resp.json()

    assert body["contract_version"] == "post_job_truth_v1"
    assert body["labor"]["closed_minutes_total"]["value"] == 90.0
    assert body["labor"]["closed_minutes_total"]["presence"] == "present"
    assert body["labor"]["session_count"] == 2
    assert body["labor"]["monetary_cost"]["presence"] == "excluded"
    assert body["labor"]["variance_minutes"]["value"] == 50.0
    roles = {s["role"] for s in body["labor"]["sessions"]}
    assert "primary" in roles and "helper" in roles

    refreshed = await db_session.get(Orders, order.id)
    assert refreshed.snapshot_v2_json == before


@pytest.mark.asyncio
async def test_open_session_not_silently_final(db_session, auth_client):
    order = await _seed_order_with_sessions(
        db_session, order_id=_OID_BASE + 2, with_open_session=True
    )
    resp = _get_truth(auth_client, order.id)
    body = resp.json()
    assert body["labor"]["open_session_count"] == 1
    assert body["labor"]["completeness"] == "still_active"
    assert body["labor"]["closed_minutes_total"]["value"] == 90.0
    assert any(m["code"] == "open_work_sessions" for m in body["missing_data"])


@pytest.mark.asyncio
async def test_planned_material_not_treated_as_actual(db_session, auth_client):
    order = await _seed_order_with_sessions(db_session, order_id=_OID_BASE + 3)
    resp = _get_truth(auth_client, order.id)
    body = resp.json()
    assert body["materials"]["deducted_movement_count"] == 0
    assert body["materials"]["known_actual_cost_total"]["presence"] == "not_captured"
    # Observed free-text row stays not_captured, not zero
    assert any(
        line["actual_deducted_quantity"]["presence"] == "not_captured"
        for line in body["materials"]["lines"]
    )


@pytest.mark.asyncio
async def test_real_deduction_appears_as_material_actual(db_session, auth_client):
    order = await _seed_order_with_sessions(db_session, order_id=_OID_BASE + 4)
    mat = await _seed_material_and_deduction(db_session, order=order, quantity=2.0, unit_cost=12.5)

    resp = _get_truth(auth_client, order.id)
    body = resp.json()
    assert body["materials"]["deducted_movement_count"] == 1
    assert body["materials"]["known_actual_cost_total"]["value"] == 25.0
    assert body["materials"]["valuation_method"] == "inventory_materials.unit_cost_at_read"
    deducted = [
        line
        for line in body["materials"]["lines"]
        if line["actual_deducted_quantity"]["presence"] == "present"
    ]
    assert len(deducted) == 1
    assert deducted[0]["material_id"] == mat.id
    assert deducted[0]["actual_deducted_quantity"]["value"] == 2.0

    profit = _get_profit(auth_client, order.id).json()
    assert profit["actual_materials_total"] == 25.0
    assert profit["known_actual_cost"] == 25.0
    assert profit["actual_total_cost"] is None
    assert profit["cost_coverage_status"] == "PARTIAL"
    assert profit["actual_margin_amount"] is None
    assert "labor_money" in profit["excluded_cost_components"]
    assert profit["known_actual_margin"] == 1475.0  # 1500 - 25


@pytest.mark.asyncio
async def test_missing_unit_cost_stays_missing(db_session, auth_client):
    order = await _seed_order_with_sessions(db_session, order_id=_OID_BASE + 5)
    await _seed_material_and_deduction(db_session, order=order, unit_cost=None)
    body = _get_truth(auth_client, order.id).json()
    assert body["materials"]["deducted_movement_count"] == 1
    assert body["materials"]["known_actual_cost_total"]["presence"] == "missing"
    assert body["profitability"]["cost_coverage_status"] in ("INCOMPLETE", "PARTIAL")


@pytest.mark.asyncio
async def test_machine_planned_only_not_actual(db_session, auth_client):
    order = await _seed_order_with_sessions(db_session, order_id=_OID_BASE + 6)
    body = _get_truth(auth_client, order.id).json()
    assert body["machines"]["completeness"] == "not_captured"
    assert body["machines"]["items"]
    assert body["machines"]["items"][0]["status"] == "not_captured"
    assert body["quantity"]["completed_quantity"]["presence"] == "not_captured"


@pytest.mark.asyncio
async def test_reconciliation_zero_denominator_no_percent(db_session, auth_client):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_OID_BASE + 7)
    plan = ExecutionPlan(
        order_id=order.id,
        order_code=order.code,
        snapshot_version=1,
        tasks_json='{"planned_tasks":[],"operational_tasks":[]}',
        total_estimated_time_minutes=0.0,
    )
    db_session.add(plan)
    reality = ExecutionReality(
        order_id=order.id,
        order_code=order.code,
        tasks_json=json.dumps(
            [
                {
                    "session_id": "ws-z",
                    "task_id": "t1",
                    "started_at": "2026-07-16T08:00:00+00:00",
                    "ended_at": "2026-07-16T08:10:00+00:00",
                    "duration_minutes": 10,
                }
            ]
        ),
        materials_json="[]",
        total_actual_time_minutes=10.0,
    )
    db_session.add(reality)
    await db_session.commit()

    body = _get_truth(auth_client, order.id).json()
    labor_var = next(
        v for v in body["reconciliation"]["variances"] if v["dimension"] == "labor_minutes"
    )
    assert labor_var["absolute_variance"] == 10.0
    assert labor_var["percentage_variance"] is None


@pytest.mark.asyncio
async def test_profitability_never_complete_without_labor_money(db_session, auth_client):
    order = await _seed_order_with_sessions(db_session, order_id=_OID_BASE + 8)
    await _seed_material_and_deduction(db_session, order=order)
    body = _get_truth(auth_client, order.id).json()
    assert body["profitability"]["profitability_status"] == "PARTIAL"
    assert body["profitability"]["cost_coverage_status"] == "PARTIAL"
    assert body["profitability"]["false_final_profit_forbidden"] is True
    assert "labor_money" in body["profitability"]["excluded_cost_components"]


@pytest.mark.asyncio
async def test_reversed_deduction_excluded_from_actual_cost(db_session, auth_client):
    order = await _seed_order_with_sessions(db_session, order_id=_OID_BASE + 9)
    mat = await _seed_material_and_deduction(db_session, order=order, quantity=1.0, unit_cost=10.0)
    movement = (
        await db_session.execute(
            select(StockMovement).where(StockMovement.order_id == order.id)
        )
    ).scalar_one()
    reversal = StockMovement(
        material_id=mat.id,
        source_type="stock_movement_reversal",
        source_id=movement.id,
        order_id=order.id,
        task_id="cnc_face_cut",
        quantity=1.0,
        unit="sheet",
        movement_type="reversal",
        old_stock=99.0,
        new_stock=100.0,
        performed_by="test",
        performed_at=datetime.now(timezone.utc),
        reason="cleanup",
        idempotency_key=f"reversal:{movement.id}",
    )
    db_session.add(reversal)
    await db_session.commit()

    body = _get_truth(auth_client, order.id).json()
    assert body["materials"]["deducted_movement_count"] == 0
    assert body["materials"]["known_actual_cost_total"]["presence"] == "not_captured"
    profit = _get_profit(auth_client, order.id).json()
    assert profit["actual_materials_total"] is None
    assert profit["known_actual_cost"] is None


async def _seed_multi_task_breadth(
    db_session,
    *,
    order_id: int,
    mode: str,
) -> Orders:
    """mode: partial | variance | matched"""
    order = await _seed_v2_order_with_snapshot(db_session, order_id=order_id)
    plan = ExecutionPlan(
        order_id=order.id,
        order_code=order.code,
        snapshot_version=1,
        tasks_json=json.dumps(
            [
                {
                    "task_id": "task_alpha",
                    "name": "Alpha",
                    "estimated_time_minutes": 30,
                },
                {
                    "task_id": "task_beta",
                    "name": "Beta",
                    "estimated_time_minutes": 20,
                },
                {
                    "task_id": "task_gamma",
                    "name": "Gamma",
                    "estimated_time_minutes": 15,
                },
            ]
        ),
        total_estimated_time_minutes=65.0,
    )
    db_session.add(plan)

    if mode == "partial":
        sessions = [
            {
                "session_id": "ws-alpha-1",
                "task_id": "task_alpha",
                "employee_id": 11,
                "employee_name": "Primary",
                "role": "primary",
                "started_at": "2026-07-17T08:00:00+00:00",
                "ended_at": "2026-07-17T08:30:00+00:00",
                "duration_minutes": 30,
            }
        ]
        total_actual = 30.0
    elif mode == "variance":
        sessions = [
            {
                "session_id": "ws-alpha-var",
                "task_id": "task_alpha",
                "employee_id": 11,
                "employee_name": "Primary",
                "role": "primary",
                "started_at": "2026-07-17T08:00:00+00:00",
                "ended_at": "2026-07-17T09:15:00+00:00",
                "duration_minutes": 75,
            }
        ]
        total_actual = 75.0
    else:  # matched
        sessions = [
            {
                "session_id": "ws-alpha-m",
                "task_id": "task_alpha",
                "employee_id": 11,
                "role": "primary",
                "started_at": "2026-07-17T08:00:00+00:00",
                "ended_at": "2026-07-17T08:30:00+00:00",
                "duration_minutes": 30,
            },
            {
                "session_id": "ws-beta-m",
                "task_id": "task_beta",
                "employee_id": 11,
                "role": "primary",
                "started_at": "2026-07-17T09:00:00+00:00",
                "ended_at": "2026-07-17T09:20:00+00:00",
                "duration_minutes": 20,
            },
            {
                "session_id": "ws-gamma-m",
                "task_id": "task_gamma",
                "employee_id": 11,
                "role": "primary",
                "started_at": "2026-07-17T10:00:00+00:00",
                "ended_at": "2026-07-17T10:15:00+00:00",
                "duration_minutes": 15,
            },
        ]
        total_actual = 65.0

    reality = ExecutionReality(
        order_id=order.id,
        order_code=order.code,
        tasks_json=json.dumps(sessions),
        materials_json="[]",
        total_actual_time_minutes=total_actual,
    )
    db_session.add(reality)
    await db_session.commit()
    await db_session.refresh(order)
    return order


@pytest.mark.asyncio
async def test_w7_t02_partial_missing_actuals_not_zero(db_session, auth_client):
    order = await _seed_multi_task_breadth(
        db_session, order_id=_OID_BASE + 20, mode="partial"
    )
    before_snap = order.snapshot_v2_json
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order.id)
        )
    ).scalar_one()
    before_plan_tasks = plan.tasks_json

    body = _get_truth(auth_client, order.id).json()
    ops = {o["task_id"]: o for o in body["reconciliation"]["operations"]}
    assert ops["task_alpha"]["reconciliation_state"] in ("matched", "variance")
    assert ops["task_beta"]["reconciliation_state"] == "missing_actual"
    assert ops["task_beta"]["actual_minutes"]["presence"] == "not_captured"
    assert ops["task_beta"]["actual_minutes"]["value"] is None
    assert ops["task_gamma"]["reconciliation_state"] == "missing_actual"
    summary = body["reconciliation"]["summary"]
    assert summary["operations_total"] == 3
    assert summary["missing_actual_count"] == 2
    assert summary["matched_count"] + summary["variance_count"] == 1

    refreshed = await db_session.get(Orders, order.id)
    assert refreshed.snapshot_v2_json == before_snap
    plan2 = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order.id)
        )
    ).scalar_one()
    assert plan2.tasks_json == before_plan_tasks


@pytest.mark.asyncio
async def test_w7_t02_measurable_minute_variance(db_session, auth_client):
    order = await _seed_multi_task_breadth(
        db_session, order_id=_OID_BASE + 21, mode="variance"
    )
    body = _get_truth(auth_client, order.id).json()
    alpha = next(
        o for o in body["reconciliation"]["operations"] if o["task_id"] == "task_alpha"
    )
    assert alpha["planned_minutes"]["value"] == 30
    assert alpha["actual_minutes"]["value"] == 75
    assert alpha["variance_minutes"]["value"] == 45
    assert alpha["variance_minutes"]["presence"] == "present"
    assert alpha["reconciliation_state"] == "variance"
    assert body["reconciliation"]["summary"]["variance_count"] >= 1


@pytest.mark.asyncio
async def test_w7_t02_matched_operations_summary(db_session, auth_client):
    order = await _seed_multi_task_breadth(
        db_session, order_id=_OID_BASE + 22, mode="matched"
    )
    body = _get_truth(auth_client, order.id).json()
    summary = body["reconciliation"]["summary"]
    assert summary["operations_total"] == 3
    assert summary["matched_count"] == 3
    assert summary["missing_actual_count"] == 0
    assert summary["variance_count"] == 0
    for op in body["reconciliation"]["operations"]:
        assert op["reconciliation_state"] == "matched"
        assert op["planned_quantity"]["presence"] == "not_captured"
        assert op["actual_quantity"]["presence"] == "not_captured"
