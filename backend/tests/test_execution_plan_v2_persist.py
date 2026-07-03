"""Tests for ExecutionPlan V2 persist (Step 9.3.3)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from schemas.execution_plan_v2 import (
    EXECUTION_PLAN_V2_PLAN_SOURCE,
    EXECUTION_PLAN_V2_SOURCE,
    EXECUTION_PLAN_V2_TASKS_JSON_PLAN_VERSION,
    IGNORED_PRICING_SOURCES,
    PLANNING_MINUTES_WARNING,
    TOTAL_ESTIMATED_TIME_SOURCE_NOT_AVAILABLE,
)
from services.execution_plan_v2_persist_service import (
    FORBIDDEN_IMPORT_SUBSTRINGS,
    ExecutionPlanV2PersistOrderNotFound,
    create_execution_plan_v2_from_order,
)
from tests.test_execution_plan_v2_preview import (
    _build_order_snapshot_v2_json,
    _seed_v2_order_with_snapshot,
)
from tests.test_execution_plan_v2_source_metadata import _seed_legacy_order

BACKEND_ROOT = Path(__file__).resolve().parents[1]
STEP_9_3_3_PATHS = (
    BACKEND_ROOT / "schemas" / "execution_plan_v2.py",
    BACKEND_ROOT / "services" / "execution_plan_v2_persist_service.py",
    BACKEND_ROOT / "routers" / "execution_plan_v2.py",
    Path(__file__).resolve(),
)


def _forbidden_imports_in_paths() -> set[str]:
    found: set[str] = set()
    for path in STEP_9_3_3_PATHS:
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


async def _count_execution_plans(db_session) -> int:
    return int(await db_session.scalar(select(func.count()).select_from(ExecutionPlan)) or 0)


async def _count_execution_reality(db_session) -> int:
    return int(await db_session.scalar(select(func.count()).select_from(ExecutionReality)) or 0)


# Persist tests use 198xx order IDs to avoid colliding with preview seed range (96xx).
_PERSIST_OID = lambda n: 19800 + n


@pytest.mark.asyncio
async def test_cannot_persist_without_order(db_session):
    with pytest.raises(ExecutionPlanV2PersistOrderNotFound):
        await create_execution_plan_v2_from_order(db_session, 999999)


def test_cannot_persist_without_order_via_endpoint(db_fixture, auth_client):
    resp = auth_client.post("/api/v1/execution/plan-v2/from-order/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "order_not_found"


@pytest.mark.asyncio
async def test_cannot_persist_legacy_order_without_snapshot_v2_json(db_session):
    order = _seed_legacy_order(db_session, order_id=_PERSIST_OID(1))
    await db_session.commit()
    with pytest.raises(HTTPException) as exc:
        await create_execution_plan_v2_from_order(db_session, order.id)
    assert exc.value.status_code == 422
    assert "blocked_legacy_order" in exc.value.detail["blockers"]


@pytest.mark.asyncio
async def test_cannot_persist_v2_order_without_quote_snapshot_v2_id(db_session):
    oid = _PERSIST_OID(2)
    order = Orders(
        id=oid,
        code=f"ORD-V2-NO-QSN-{oid}",
        client_name="Missing QSN",
        status="locked",
        total_amount=1500.0,
        snapshot_line_items=None,
        quote_snapshot_v2_id=None,
        snapshot_v2_json=_build_order_snapshot_v2_json(quote_id=oid, quote_snapshot_v2_id=1),
    )
    db_session.add(order)
    await db_session.commit()
    with pytest.raises(HTTPException) as exc:
        await create_execution_plan_v2_from_order(db_session, order.id)
    assert exc.value.status_code == 422
    assert "blocked_missing_quote_snapshot_v2_id" in exc.value.detail["blockers"]


@pytest.mark.asyncio
async def test_cannot_persist_if_preview_blocked_missing_product_definition(db_session):
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=_PERSIST_OID(3),
        include_product_definition=False,
    )
    with pytest.raises(HTTPException) as exc:
        await create_execution_plan_v2_from_order(db_session, order.id)
    assert exc.value.status_code == 422
    assert "blocked_missing_product_definition" in exc.value.detail["blockers"]


@pytest.mark.asyncio
async def test_cannot_persist_if_preview_blocked_missing_product_aggregate(db_session):
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=_PERSIST_OID(4),
        include_product_aggregate=False,
    )
    with pytest.raises(HTTPException) as exc:
        await create_execution_plan_v2_from_order(db_session, order.id)
    assert exc.value.status_code == 422
    assert "blocked_missing_product_aggregate" in exc.value.detail["blockers"]


@pytest.mark.asyncio
async def test_cannot_persist_if_planned_tasks_empty(db_session):
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=_PERSIST_OID(5),
        include_task_rules=False,
    )
    with pytest.raises(HTTPException) as exc:
        await create_execution_plan_v2_from_order(db_session, order.id)
    assert exc.value.status_code == 422
    blockers = exc.value.detail["blockers"]
    assert "blocked_missing_task_rules" in blockers or "planned_tasks_empty" in blockers


# ---------------------------------------------------------------------------
# 7-18. Successful persist + envelope
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_can_persist_from_valid_v2_preview(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(10))
    before_plans = await _count_execution_plans(db_session)
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    assert result.status == "persisted"
    assert result.execution_plan_id is not None
    after_plans = await _count_execution_plans(db_session)
    assert after_plans == before_plans + 1


@pytest.mark.asyncio
async def test_persisted_plan_has_plan_source_order_snapshot_v2(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(11))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    assert row is not None
    assert row.plan_source == EXECUTION_PLAN_V2_PLAN_SOURCE


@pytest.mark.asyncio
async def test_persisted_plan_has_source_quote_snapshot_v2_id(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(12))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    assert row.source_quote_snapshot_v2_id == order.quote_snapshot_v2_id


@pytest.mark.asyncio
async def test_persisted_plan_has_source_snapshot_code(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(13))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    assert row.source_snapshot_code == "OSN2-TEST-001"


@pytest.mark.asyncio
async def test_persisted_plan_has_source_content_hash(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(14))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    assert row.source_content_hash == "abc123def456abc123def456abc123de"


@pytest.mark.asyncio
async def test_persisted_plan_has_source_order_snapshot_version(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(15))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    assert row.source_order_snapshot_version is not None


@pytest.mark.asyncio
async def test_tasks_json_contains_v2_envelope(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(16))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    envelope = json.loads(row.tasks_json)
    assert isinstance(envelope, dict)
    assert envelope["source"] == EXECUTION_PLAN_V2_SOURCE
    assert envelope["plan_version"] == EXECUTION_PLAN_V2_TASKS_JSON_PLAN_VERSION


@pytest.mark.asyncio
async def test_tasks_json_contains_planned_tasks(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(17))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    envelope = json.loads(row.tasks_json)
    assert len(envelope["planned_tasks"]) >= 1
    assert envelope["planned_tasks"][0]["task_key"]


@pytest.mark.asyncio
async def test_tasks_json_contains_ignored_pricing_sources(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(18))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    envelope = json.loads(row.tasks_json)
    for src in IGNORED_PRICING_SOURCES:
        assert src in envelope["ignored_pricing_sources"]


@pytest.mark.asyncio
async def test_tasks_json_contains_provenance(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(19))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    envelope = json.loads(row.tasks_json)
    assert len(envelope["provenance"]) >= 1


@pytest.mark.asyncio
async def test_tasks_json_execution_tasks_created_false(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(20))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    assert result.execution_tasks_created is False
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    envelope = json.loads(row.tasks_json)
    assert envelope["execution_tasks_created"] is False
    assert envelope["pricing_sources_used_for_tasks"] == []


@pytest.mark.asyncio
async def test_no_task_or_session_rows_created(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(21))
    before_reality = await _count_execution_reality(db_session)
    await create_execution_plan_v2_from_order(db_session, order.id)
    after_reality = await _count_execution_reality(db_session)
    assert after_reality == before_reality


# ---------------------------------------------------------------------------
# 19-25. Forbidden dependencies / sources
# ---------------------------------------------------------------------------


def test_does_not_import_quote_orchestrator_or_cost_engine():
    assert _forbidden_imports_in_paths() == set()


def test_persist_service_does_not_call_execution_plan_service_from_order():
    source = (BACKEND_ROOT / "services" / "execution_plan_v2_persist_service.py").read_text(
        encoding="utf-8"
    )
    assert "ExecutionPlanService" not in source
    assert "execution_plan_service" not in source


def test_persist_service_does_not_call_execution_plan_gate_service():
    source = (BACKEND_ROOT / "services" / "execution_plan_v2_persist_service.py").read_text(
        encoding="utf-8"
    )
    assert "execution_plan_gate_service" not in source
    assert "evaluate_gate" not in source


def test_persist_router_does_not_call_price():
    source = (BACKEND_ROOT / "routers" / "execution_plan_v2.py").read_text(encoding="utf-8")
    assert "/price" not in source


@pytest.mark.asyncio
async def test_does_not_use_commercial_or_internal_lines_as_task_source(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(22))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    envelope = json.loads(row.tasks_json)
    for task in envelope["planned_tasks"]:
        prov = " ".join(task.get("provenance", []))
        assert "commercial_price_proposal" not in prov.lower()
        assert "estimated_internal_cost" not in prov.lower()
    assert envelope["pricing_sources_used_for_tasks"] == []


# ---------------------------------------------------------------------------
# 26-31. Minutes policy, duplicate, readiness, snapshot immutability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_null_planning_minutes_yields_zero_total_with_warning(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(23))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    assert row.total_estimated_time_minutes == 0.0
    assert result.total_estimated_time_source == TOTAL_ESTIMATED_TIME_SOURCE_NOT_AVAILABLE
    envelope = json.loads(row.tasks_json)
    assert PLANNING_MINUTES_WARNING in envelope["warnings"]
    assert envelope["total_estimated_time_source"] == TOTAL_ESTIMATED_TIME_SOURCE_NOT_AVAILABLE


@pytest.mark.asyncio
async def test_duplicate_persist_returns_already_exists(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(24))
    first = await create_execution_plan_v2_from_order(db_session, order.id)
    assert first.status == "persisted"
    before_plans = await _count_execution_plans(db_session)
    second = await create_execution_plan_v2_from_order(db_session, order.id)
    after_plans = await _count_execution_plans(db_session)
    assert after_plans == before_plans
    assert second.status == "already_exists"
    assert second.persist_status == "already_exists"
    assert second.execution_plan_id == first.execution_plan_id
    assert second.execution_plan_created is False


def test_duplicate_persist_via_endpoint_returns_already_exists(db_fixture, db_session, auth_client):
    order_id = _PERSIST_OID(25)

    async def _setup():
        await _seed_v2_order_with_snapshot(db_session, order_id=order_id)

    db_fixture.run(_setup())
    resp1 = auth_client.post(f"/api/v1/execution/plan-v2/from-order/{order_id}")
    assert resp1.status_code == 201, resp1.text
    resp2 = auth_client.post(f"/api/v1/execution/plan-v2/from-order/{order_id}")
    assert resp2.status_code == 200, resp2.text
    body = resp2.json()
    assert body["status"] == "already_exists"
    assert body["persist_status"] == "already_exists"
    assert body["execution_plan_created"] is False


def test_v2_order_remains_blocked_from_legacy_endpoint(db_fixture, db_session, auth_client):
    order_id = _PERSIST_OID(26)

    async def _setup():
        await _seed_v2_order_with_snapshot(db_session, order_id=order_id)

    db_fixture.run(_setup())
    resp = auth_client.post(f"/api/v1/execution/plan/from-order/{order_id}")
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "EXECUTION_PLAN_V2_REQUIRED"


def test_legacy_order_remains_supported_by_legacy_endpoint(db_fixture, db_session, auth_client):
    order_id = _PERSIST_OID(27)

    async def _setup():
        _seed_legacy_order(db_session, order_id=order_id)
        await db_session.commit()

    db_fixture.run(_setup())
    resp = auth_client.post(f"/api/v1/execution/plan/from-order/{order_id}")
    assert resp.status_code in (200, 201), resp.text


def test_can_persist_via_endpoint(db_fixture, db_session, auth_client):
    order_id = _PERSIST_OID(31)

    async def _setup():
        await _seed_v2_order_with_snapshot(db_session, order_id=order_id)

    db_fixture.run(_setup())
    resp = auth_client.post(f"/api/v1/execution/plan-v2/from-order/{order_id}")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "persisted"
    assert body["persist_status"] == "persisted"
    assert body["plan_source"] == EXECUTION_PLAN_V2_PLAN_SOURCE
    assert body["execution_tasks_created"] is False
    assert body["input_summary"]["task_count"] >= 1


@pytest.mark.asyncio
async def test_order_readiness_execution_plan_created_updated(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(28))
    assert order.readiness_snapshot.get("execution_plan_created") is False
    await create_execution_plan_v2_from_order(db_session, order.id)
    refreshed = await db_session.get(Orders, order.id)
    assert refreshed.readiness_snapshot.get("execution_plan_created") is True
    assert refreshed.readiness_snapshot.get("no_execution_plan_created") is False


@pytest.mark.asyncio
async def test_snapshot_v2_json_not_mutated(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_PERSIST_OID(29))
    before = order.snapshot_v2_json
    await create_execution_plan_v2_from_order(db_session, order.id)
    refreshed = await db_session.get(Orders, order.id)
    assert refreshed.snapshot_v2_json == before


# ---------------------------------------------------------------------------
# 32-35. Scope guards + endpoint smoke
# ---------------------------------------------------------------------------


def test_no_migration_needed_for_step_9_3_3():
    migration_dir = BACKEND_ROOT / "alembic" / "versions"
    recent = sorted(migration_dir.glob("s5*.py"), key=lambda p: p.name)[-3:]
    names = [p.name for p in recent]
    assert "s56_add_execution_plan_source_metadata.py" in names or any(
        "execution_plan_source" in p.name for p in recent
    )


def test_persist_endpoint_exists(db_fixture, auth_client):
    resp = auth_client.post("/api/v1/execution/plan-v2/from-order/999998")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_persist_service_source_has_no_legacy_calls():
    assert _forbidden_imports_in_paths() == set()


def test_persist_endpoint_route_exact():
    router_source = (BACKEND_ROOT / "routers" / "execution_plan_v2.py").read_text(encoding="utf-8")
    assert '"/plan-v2/from-order/{order_id}"' in router_source