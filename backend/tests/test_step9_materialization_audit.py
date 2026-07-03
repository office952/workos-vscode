"""Step 9 materialization audit-only tests — no DB writes, no execution_tasks."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.execution_plan_v2_materialization_audit_service import (
    FORBIDDEN_IMPORT_SUBSTRINGS,
    ExecutionPlanV2MaterializationAuditOrderNotFound,
    ExecutionPlanV2MaterializationAuditPlanNotFound,
    build_execution_plan_v2_materialization_audit_by_order_id,
    build_execution_plan_v2_materialization_audit_by_plan_id,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot
from tests.test_step9_order_snapshot_to_execution_plan import (
    _build_convert_shaped_snapshot_json,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATHS = (
    BACKEND_ROOT / "schemas" / "execution_plan_v2_materialization_audit.py",
    BACKEND_ROOT / "services" / "execution_plan_v2_materialization_audit_service.py",
    BACKEND_ROOT / "routers" / "execution_plan_v2.py",
    Path(__file__).resolve(),
)

_AUDIT_OID = lambda n: 29900 + n


def _forbidden_imports() -> set[str]:
    found: set[str] = set()
    for path in AUDIT_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                    if part in node.module:
                        found.add(node.module)
    return found


@pytest.mark.asyncio
async def test_audit_returns_audit_only_mode(db_session):
    oid = _AUDIT_OID(1)
    order = await _seed_v2_order_with_snapshot(db_session, order_id=oid)
    order.snapshot_v2_json = _build_convert_shaped_snapshot_json(
        order_id=oid,
        quote_snapshot_v2_id=int(order.quote_snapshot_v2_id),
    )
    await db_session.commit()
    await create_execution_plan_v2_from_order(db_session, order.id)
    audit = await build_execution_plan_v2_materialization_audit_by_order_id(db_session, order.id)
    assert audit.mode == "audit_only"
    assert audit.materialization_status == "blocked_needs_owner_go"
    assert audit.guards.creates_execution_tasks is False
    assert audit.guards.creates_sessions is False
    assert audit.guards.writes_database is False
    assert audit.planned_task_count >= 1
    assert len(audit.materializable_task_candidates) >= 1


@pytest.mark.asyncio
async def test_audit_no_db_side_effects(db_fixture, db_session, auth_client):
    oid = _AUDIT_OID(2)
    order = await _seed_v2_order_with_snapshot(db_session, order_id=oid)
    order.snapshot_v2_json = _build_convert_shaped_snapshot_json(
        order_id=oid,
        quote_snapshot_v2_id=int(order.quote_snapshot_v2_id),
    )
    await db_session.commit()
    await create_execution_plan_v2_from_order(db_session, order.id)
    plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    reality_before = await db_session.scalar(select(func.count()).select_from(ExecutionReality))
    resp = auth_client.get(f"/api/v1/execution/plan-v2/from-order/{order.id}/materialization-audit")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mode"] == "audit_only"
    assert body["guards"]["writes_database"] is False
    plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    reality_after = await db_session.scalar(select(func.count()).select_from(ExecutionReality))
    assert plans_after == plans_before
    assert reality_after == reality_before


@pytest.mark.asyncio
async def test_audit_by_plan_id_route(db_fixture, db_session, auth_client):
    oid = _AUDIT_OID(3)
    order = await _seed_v2_order_with_snapshot(db_session, order_id=oid)
    await create_execution_plan_v2_from_order(db_session, order.id)
    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order.id))
    ).scalar_one()
    resp = auth_client.get(f"/api/v1/execution/plan-v2/{plan.id}/materialization-audit")
    assert resp.status_code == 200, resp.text
    assert resp.json()["execution_plan_id"] == plan.id


@pytest.mark.asyncio
async def test_audit_missing_plan_404(db_session):
    with pytest.raises(ExecutionPlanV2MaterializationAuditOrderNotFound):
        await build_execution_plan_v2_materialization_audit_by_order_id(db_session, 999999)
    with pytest.raises(ExecutionPlanV2MaterializationAuditPlanNotFound):
        await build_execution_plan_v2_materialization_audit_by_plan_id(db_session, 999999)


def test_audit_forbidden_imports():
    assert _forbidden_imports() == set()


def test_audit_service_forbidden_imports_static():
    assert _forbidden_imports() == set()
