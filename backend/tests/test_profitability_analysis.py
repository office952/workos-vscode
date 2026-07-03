"""Contract tests for Slice 10.2 + 10.3 — read-only ProfitabilityAnalysis."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from sqlalchemy import select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from schemas.order_snapshot_v2 import OrderSnapshotV2
from tests.test_execution_plan_v2_preview import (
    _build_order_snapshot_v2_json,
    _seed_v2_order_with_snapshot,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SLICE_10_23_PATHS = (
    BACKEND_ROOT / "services" / "profitability_analysis_service.py",
    BACKEND_ROOT / "routers" / "profitability_analysis.py",
    BACKEND_ROOT / "schemas" / "profitability_analysis.py",
    Path(__file__).resolve(),
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
)

_PROFIT_OID_BASE = 19800


def _forbidden_imports_in_paths() -> set[str]:
    found: set[str] = set()
    for path in SLICE_10_23_PATHS:
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


def _get(auth_client, order_id: int):
    return auth_client.get(f"/api/v1/profitability-analysis/order/{order_id}")


async def _seed_v2_order_no_reality(db_session, *, order_id: int) -> Orders:
    return await _seed_v2_order_with_snapshot(db_session, order_id=order_id)


async def _seed_v2_order_with_reality(
    db_session,
    *,
    order_id: int,
    actual_minutes: float = 42.5,
) -> Orders:
    order = await _seed_v2_order_with_snapshot(db_session, order_id=order_id)
    reality = ExecutionReality(
        order_id=order.id,
        order_code=order.code,
        tasks_json=json.dumps(
            [
                {
                    "task_id": "cnc_face_cut",
                    "started_at": "2026-06-30T10:00:00+00:00",
                    "ended_at": "2026-06-30T10:42:30+00:00",
                }
            ]
        ),
        materials_json=json.dumps(
            [{"material_name": "ACM Panel", "quantity": 1.0, "unit": "sheet"}]
        ),
        total_actual_time_minutes=actual_minutes,
    )
    db_session.add(reality)
    plan = ExecutionPlan(
        order_id=order.id,
        order_code=order.code,
        snapshot_version=1,
        tasks_json='{"planned_tasks":[],"operational_tasks":[]}',
        total_estimated_time_minutes=30.0,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(order)
    return order


async def _seed_legacy_order(db_session, *, order_id: int) -> Orders:
    order = Orders(
        id=order_id,
        code=f"ORD-PROFIT-LEG-{order_id}",
        client_name="Legacy Profit Client",
        status="confirmed",
        total_amount=888.0,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


@pytest.mark.asyncio
async def test_v2_order_without_reality_estimated_only(db_session, auth_client):
    order = await _seed_v2_order_no_reality(
        db_session, order_id=_PROFIT_OID_BASE + 1
    )
    before_snapshot = order.snapshot_v2_json

    resp = _get(auth_client, order.id)
    assert resp.status_code == 200
    body = resp.json()

    assert body["order_id"] == order.id
    assert body["profitability_status"] == "estimated_only"
    assert body["has_snapshot_v2"] is True
    assert body["revenue_source"] == "order_snapshot_v2"
    assert body["accepted_commercial_total"] == 1500.0
    assert body["estimated_internal_total"] == 620.0
    assert body["has_execution_reality"] is False
    assert body["actual_total_cost"] is None
    assert body["actual_labor_minutes"] is None
    assert body["retroactive_change_allowed"] is False
    assert body["write_back_performed"] is False
    assert "execution_reality_missing" in body["warnings"]
    assert "actual_costing_not_available" in body["warnings"]

    refreshed = await db_session.get(Orders, order.id)
    assert refreshed.snapshot_v2_json == before_snapshot
    reality_count = await db_session.execute(
        select(ExecutionReality).where(ExecutionReality.order_id == order.id)
    )
    assert reality_count.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_v2_order_with_partial_reality(db_session, auth_client):
    order = await _seed_v2_order_with_reality(
        db_session, order_id=_PROFIT_OID_BASE + 2
    )

    resp = _get(auth_client, order.id)
    assert resp.status_code == 200
    body = resp.json()

    assert body["profitability_status"] == "actuals_partial"
    assert body["has_execution_reality"] is True
    assert body["actual_labor_minutes"] == 42.5
    assert body["actual_total_cost"] is None
    assert body["actual_margin_amount"] is None
    assert body["variance_estimated_vs_actual"]["minutes_delta"] == 12.5
    assert body["variance_estimated_vs_actual"]["cost_delta"] is None
    assert "actual_costing_not_available" in body["warnings"]
    assert "hr_labor_cost_missing" in body["warnings"]
    assert "actual_material_cost_missing" in body["warnings"]


@pytest.mark.asyncio
async def test_missing_order_returns_404(auth_client):
    resp = _get(auth_client, _PROFIT_OID_BASE + 9999)
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "order_not_found"


@pytest.mark.asyncio
async def test_legacy_order_without_v2_supported_with_warning(db_session, auth_client):
    order = await _seed_legacy_order(db_session, order_id=_PROFIT_OID_BASE + 3)

    resp = _get(auth_client, order.id)
    assert resp.status_code == 200
    body = resp.json()

    assert body["profitability_status"] == "unsupported_legacy_order"
    assert body["has_snapshot_v2"] is False
    assert body["revenue_source"] == "order.total_amount"
    assert body["accepted_commercial_total"] == 888.0
    assert body["estimated_internal_total"] is None
    assert "legacy_order_without_snapshot_v2" in body["warnings"]


@pytest.mark.asyncio
async def test_v2_missing_estimated_internal_warning(db_session, auth_client):
    snapshot_json = _build_order_snapshot_v2_json(
        quote_id=_PROFIT_OID_BASE + 4,
        quote_snapshot_v2_id=1,
    )
    payload = OrderSnapshotV2.model_validate_json(snapshot_json)
    payload = payload.model_copy(update={"estimated_internal_total": None})
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=_PROFIT_OID_BASE + 4,
        snapshot_v2_json=payload.model_dump_json(),
    )

    resp = _get(auth_client, order.id)
    assert resp.status_code == 200
    body = resp.json()

    assert body["estimated_internal_total"] is None
    assert body["estimated_margin_amount"] is None
    assert "estimated_internal_total_missing" in body["warnings"]


@pytest.mark.asyncio
async def test_invalid_order_id_returns_422(auth_client):
    resp = _get(auth_client, 0)
    assert resp.status_code == 422


def test_no_forbidden_imports_in_slice_paths():
    assert _forbidden_imports_in_paths() == set()
