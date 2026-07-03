"""Tests for ExecutionPlan V2 source metadata schema and legacy endpoint guard (Step 9.3.1)."""

from __future__ import annotations

import ast
import inspect
import json
import uuid
from pathlib import Path

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from routers.execution import create_plan_from_order
from services.execution_plan_v2_guard_service import (
    order_has_v2_snapshot_fields,
    raise_if_legacy_plan_blocked_for_v2_order,
)
from tests.test_execution_flow import _complete_snapshot_dict

MIGRATION_FILE = "s56_add_execution_plan_source_metadata.py"
BACKEND_ROOT = Path(__file__).resolve().parents[1]
STEP_9_3_1_PATHS = (
    BACKEND_ROOT / "models" / "execution_plan.py",
    BACKEND_ROOT / "alembic" / "versions" / MIGRATION_FILE,
    BACKEND_ROOT / "services" / "execution_plan_v2_guard_service.py",
    BACKEND_ROOT / "routers" / "execution.py",
    Path(__file__).resolve(),
)
STEP_9_3_1_NEW_PATHS = (
    BACKEND_ROOT / "models" / "execution_plan.py",
    BACKEND_ROOT / "alembic" / "versions" / MIGRATION_FILE,
    BACKEND_ROOT / "services" / "execution_plan_v2_guard_service.py",
)


def _forbidden_imports_in_paths(*, extra_forbidden: set[str] | None = None) -> set[str]:
    forbidden = {
        "quote_orchestrator",
        "cost_engine_service",
        "aggregate_cost_bom_price_bridge",
    }
    if extra_forbidden:
        forbidden |= extra_forbidden
    found: set[str] = set()
    for path in STEP_9_3_1_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for part in forbidden:
                    if part in node.module:
                        found.add(node.module)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for part in forbidden:
                        if part in alias.name:
                            found.add(alias.name)
    return found


def _migration_text() -> str:
    return (BACKEND_ROOT / "alembic" / "versions" / MIGRATION_FILE).read_text(encoding="utf-8")


def _seed_legacy_order(db_session, *, order_id: int | None = None) -> Orders:
    oid = order_id or (9000 + int(uuid.uuid4().hex[:4], 16) % 1000)
    order = Orders(
        id=oid,
        code=f"ORD-LEGACY-{oid}",
        client_name="Legacy Client",
        status="locked",
        total_amount=1398.25,
        snapshot_version=1,
        snapshot_line_items=json.dumps(_complete_snapshot_dict()),
        readiness_snapshot={"execution_plan_created": False, "no_execution_plan_created": True},
    )
    db_session.add(order)
    return order


async def _seed_v2_order_by_json(db_session, *, order_id: int | None = None) -> Orders:
    oid = order_id or (9100 + int(uuid.uuid4().hex[:4], 16) % 1000)
    order = Orders(
        id=oid,
        code=f"ORD-V2-JSON-{oid}",
        client_name="V2 JSON Client",
        status="locked",
        total_amount=1500.0,
        snapshot_line_items=None,
        snapshot_v2_json="{}",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


async def _seed_v2_order_by_fk(db_session, *, order_id: int | None = None) -> Orders:
    oid = order_id or (9200 + int(uuid.uuid4().hex[:4], 16) % 1000)
    record = QuoteSnapshotV2Record(
        snapshot_code=f"QSN2-GUARD-{oid}",
        snapshot_version="1.0.0",
        version=1,
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        status="frozen",
        readiness="ready_for_owner_review",
        snapshot_json="{}",
        content_hash="abc123",
    )
    db_session.add(record)
    await db_session.flush()
    order = Orders(
        id=oid,
        code=f"ORD-V2-FK-{oid}",
        client_name="V2 FK Client",
        status="locked",
        total_amount=1500.0,
        snapshot_line_items=None,
        quote_snapshot_v2_id=record.id,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


# ---------------------------------------------------------------------------
# 1-5. Model column exposure
# ---------------------------------------------------------------------------


def test_execution_plan_model_exposes_plan_source():
    assert "plan_source" in ExecutionPlan.__table__.columns
    assert ExecutionPlan.__table__.columns["plan_source"].nullable is True


def test_execution_plan_model_exposes_source_quote_snapshot_v2_id():
    assert "source_quote_snapshot_v2_id" in ExecutionPlan.__table__.columns
    assert ExecutionPlan.__table__.columns["source_quote_snapshot_v2_id"].nullable is True


def test_execution_plan_model_exposes_source_snapshot_code():
    assert "source_snapshot_code" in ExecutionPlan.__table__.columns
    assert ExecutionPlan.__table__.columns["source_snapshot_code"].nullable is True


def test_execution_plan_model_exposes_source_content_hash():
    assert "source_content_hash" in ExecutionPlan.__table__.columns
    assert ExecutionPlan.__table__.columns["source_content_hash"].nullable is True


def test_execution_plan_model_exposes_source_order_snapshot_version():
    assert "source_order_snapshot_version" in ExecutionPlan.__table__.columns
    assert ExecutionPlan.__table__.columns["source_order_snapshot_version"].nullable is True


# ---------------------------------------------------------------------------
# 6. Nullable / legacy compatibility
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_metadata_fields_nullable_and_legacy_compatible(db_session):
    order = _seed_legacy_order(db_session)
    db_session.add(
        ExecutionPlan(
            order_id=order.id,
            order_code=order.code,
            snapshot_version=1,
            tasks_json="[]",
            total_estimated_time_minutes=0.0,
        )
    )
    await db_session.commit()

    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order.id))
    ).scalar_one()
    assert plan.plan_source is None
    assert plan.source_quote_snapshot_v2_id is None
    assert plan.source_snapshot_code is None
    assert plan.source_content_hash is None
    assert plan.source_order_snapshot_version is None


# ---------------------------------------------------------------------------
# 7, 14. Legacy path still works
# ---------------------------------------------------------------------------


def test_legacy_execution_plan_creation_still_works(db_fixture, db_session, auth_client):
    order_id = 9300 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        _seed_legacy_order(db_session, order_id=order_id)
        await db_session.commit()

    db_fixture.run(_setup())
    resp = auth_client.post(f"/api/v1/execution/plan/from-order/{order_id}")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["order_id"] == order_id
    assert isinstance(body.get("tasks"), list)
    assert len(body["tasks"]) > 0


def test_legacy_order_without_v2_fields_follows_existing_path(db_fixture, db_session, auth_client):
    order_id = 9400 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        _seed_legacy_order(db_session, order_id=order_id)
        await db_session.commit()

    db_fixture.run(_setup())
    resp = auth_client.post(f"/api/v1/execution/plan/from-order/{order_id}")
    assert resp.status_code == 201, resp.text

    async def _check():
        plan_count = await db_session.scalar(
            select(func.count()).select_from(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
        assert plan_count == 1

    db_fixture.run(_check())


# ---------------------------------------------------------------------------
# 8-9. V2 orders blocked
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_v2_order_with_snapshot_v2_json_blocked_from_legacy_endpoint(
    db_fixture, db_session, auth_client
):
    order = await _seed_v2_order_by_json(db_session)
    resp = auth_client.post(f"/api/v1/execution/plan/from-order/{order.id}")
    assert resp.status_code == 422, resp.text
    detail = resp.json()["detail"]
    assert detail["error"] == "EXECUTION_PLAN_V2_REQUIRED"
    assert "dedicated execution plan v2 preview/create path" in detail["message"]


@pytest.mark.asyncio
async def test_v2_order_with_quote_snapshot_v2_id_blocked_from_legacy_endpoint(
    db_fixture, db_session, auth_client
):
    order = await _seed_v2_order_by_fk(db_session)
    resp = auth_client.post(f"/api/v1/execution/plan/from-order/{order.id}")
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["error"] == "EXECUTION_PLAN_V2_REQUIRED"


# ---------------------------------------------------------------------------
# 10-11. Guard ordering in router source
# ---------------------------------------------------------------------------


def test_v2_guard_happens_before_from_order():
    source = inspect.getsource(create_plan_from_order)
    guard_pos = source.index("raise_if_legacy_plan_blocked_for_v2_order")
    from_order_pos = source.index("svc.from_order")
    assert guard_pos < from_order_pos


def test_v2_guard_happens_before_gate_service():
    source = inspect.getsource(create_plan_from_order)
    guard_pos = source.index("raise_if_legacy_plan_blocked_for_v2_order")
    gate_pos = source.index("evaluate_gate")
    assert guard_pos < gate_pos


# ---------------------------------------------------------------------------
# 12-13. No side effects on blocked V2
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_v2_guard_creates_no_execution_plan_row(db_fixture, db_session, auth_client):
    order = await _seed_v2_order_by_json(db_session)
    plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    resp = auth_client.post(f"/api/v1/execution/plan/from-order/{order.id}")
    assert resp.status_code == 422
    plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    assert plans_after == plans_before


@pytest.mark.asyncio
async def test_v2_guard_does_not_mutate_readiness_snapshot(db_fixture, db_session, auth_client):
    order_id = 9500 + int(uuid.uuid4().hex[:4], 16) % 1000
    readiness = {"execution_plan_created": False, "no_execution_plan_created": True}
    order = Orders(
        id=order_id,
        code=f"ORD-V2-READY-{order_id}",
        client_name="V2 Ready Client",
        status="locked",
        total_amount=1500.0,
        snapshot_v2_json='{"schema_version":"1.0.0"}',
        readiness_snapshot=dict(readiness),
    )
    db_session.add(order)
    await db_session.commit()

    resp = auth_client.post(f"/api/v1/execution/plan/from-order/{order_id}")
    assert resp.status_code == 422

    refreshed = await db_session.get(Orders, order_id)
    assert refreshed.readiness_snapshot == readiness


# ---------------------------------------------------------------------------
# 15-19. Forbidden scope static checks
# ---------------------------------------------------------------------------


def test_step_9_3_1_code_has_no_price_call():
    for path in STEP_9_3_1_NEW_PATHS:
        text = path.read_text(encoding="utf-8")
        assert '"/price"' not in text
        assert "/api/v1/price" not in text


def test_step_9_3_1_code_has_no_forbidden_quote_orchestrator_import():
    found = _forbidden_imports_in_paths()
    assert "quote_orchestrator" not in "".join(found)


def test_step_9_3_1_code_has_no_forbidden_cost_engine_import():
    assert _forbidden_imports_in_paths() == set()


def test_step_9_3_1_code_has_no_product_system_task_runtime():
    found = _forbidden_imports_in_paths(
        extra_forbidden={"product_system_execution_output_service"}
    )
    new_only = {
        mod
        for mod in found
        if any(
            part in mod
            for part in (
                "execution_plan_v2_guard_service",
                "s56_add_execution_plan_source_metadata",
            )
        )
    }
    assert new_only == set()


def test_v2_guard_does_not_require_cost_result():
    guard_source = inspect.getsource(raise_if_legacy_plan_blocked_for_v2_order)
    helper_source = inspect.getsource(order_has_v2_snapshot_fields)
    assert "cost_result" not in guard_source
    assert "cost_result" not in helper_source
    assert "snapshot_line_items" not in guard_source
    assert "snapshot_line_items" not in helper_source


# ---------------------------------------------------------------------------
# 20-22. Migration safety
# ---------------------------------------------------------------------------


def test_migration_additive_and_rollback_safe():
    text = _migration_text()
    lower = text.lower()
    assert "plan_source" in text
    assert "source_quote_snapshot_v2_id" in text
    assert "source_snapshot_code" in text
    assert "source_content_hash" in text
    assert "source_order_snapshot_version" in text
    assert "quote_snapshots_v2" in text
    assert "ix_execution_plan_plan_source" in text
    assert "ix_execution_plan_source_quote_snapshot_v2_id" in text
    assert "fk_execution_plan_source_quote_snapshot_v2_id" in text
    assert "create_table" not in lower
    assert "backfill" not in lower
    assert "update(" not in lower
    assert "drop_column" in lower
    assert "drop_index" in lower
    assert "drop_constraint" in lower


def test_no_execution_plan_v2_table_in_repo_migrations():
    versions_dir = BACKEND_ROOT / "alembic" / "versions"
    for path in versions_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "execution_plan_v2" not in text


def test_no_execution_tasks_table_in_repo_migrations():
    versions_dir = BACKEND_ROOT / "alembic" / "versions"
    for path in versions_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "execution_tasks" not in text
