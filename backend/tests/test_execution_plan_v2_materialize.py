"""Tests for ExecutionPlan V2 operational task materialization (Step 9.3.4.a)."""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.execution_plan_v2 import PLANNING_MINUTES_WARNING
from schemas.execution_plan_v2_materialize import (
    OPERATIONAL_TASKS_VERSION,
    OPERATIONAL_STATUS_PENDING,
    V2_LAYER_ID,
)
from services.execution_plan_task_parser import (
    compute_activation_hash,
    materialize_operational_tasks_from_v2_envelope,
    parse_tasks_json_raw,
)
from services.execution_plan_v2_materialize_service import (
    FORBIDDEN_IMPORT_SUBSTRINGS,
    ExecutionPlanV2MaterializeOrderNotFound,
    ExecutionPlanV2MaterializePlanNotFound,
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot
from tests.test_execution_plan_v2_source_metadata import _seed_legacy_order

BACKEND_ROOT = Path(__file__).resolve().parents[1]
STEP_9_3_4_PATHS = (
    BACKEND_ROOT / "schemas" / "execution_plan_v2_materialize.py",
    BACKEND_ROOT / "services" / "execution_plan_task_parser.py",
    BACKEND_ROOT / "services" / "execution_plan_v2_materialize_service.py",
    BACKEND_ROOT / "routers" / "execution_plan_v2.py",
    Path(__file__).resolve(),
)

# Avoid order-id collisions with 9.3.3 persist tests (198xx) and preview seeds (96xx).
_MATERIALIZE_OID = lambda n: 29800 + n


def _forbidden_imports_in_paths() -> set[str]:
    found: set[str] = set()
    for path in STEP_9_3_4_PATHS:
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


async def _count_execution_reality(db_session) -> int:
    return int(await db_session.scalar(select(func.count()).select_from(ExecutionReality)) or 0)


async def _seed_persisted_v2_plan(db_session, *, order_id: int | None = None):
    oid = order_id or _MATERIALIZE_OID(10)
    order = await _seed_v2_order_with_snapshot(db_session, order_id=oid)
    await create_execution_plan_v2_from_order(db_session, order.id)
    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order.id))
    ).scalar_one()
    return order, plan


async def _load_envelope(db_session, order_id: int) -> dict:
    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one()
    return json.loads(plan.tasks_json)


# ---------------------------------------------------------------------------
# Parser unit tests
# ---------------------------------------------------------------------------


def test_legacy_flat_list_parses_via_shared_parser():
    raw = json.dumps([{"task_id": "T-001", "process_type": "cnc_routing"}])
    parsed = parse_tasks_json_raw(raw)
    assert parsed.format == "legacy_list"
    assert len(parsed.operational_tasks) == 1
    assert parsed.envelope is None


def test_v2_envelope_without_operational_tasks_parses_empty_operational():
    envelope = {
        "source": "order_snapshot_v2",
        "planned_tasks": [{"task_key": "cnc_face_cut", "label": "Cut"}],
        "execution_tasks_created": False,
    }
    parsed = parse_tasks_json_raw(json.dumps(envelope))
    assert parsed.format == "v2_envelope"
    assert parsed.operational_tasks == []
    assert len(parsed.planned_tasks) == 1


def test_invalid_json_returns_parse_errors():
    parsed = parse_tasks_json_raw("{not-json")
    assert parsed.format == "invalid"
    assert parsed.parse_errors


def test_activation_hash_stable_for_same_input():
    envelope = {
        "planned_tasks": [{"task_key": "a"}],
        "dependencies": [],
        "source_content_hash": "abc123",
    }
    assert compute_activation_hash(envelope) == compute_activation_hash(envelope)


def test_missing_task_key_blocks_materialization():
    envelope = {
        "planned_tasks": [{"label": "No Key", "canonical_task_type": "cnc_routing"}],
        "dependencies": [],
    }
    tasks, _warnings, blockers = materialize_operational_tasks_from_v2_envelope(
        envelope,
        execution_plan_id=1,
        order_id=1,
    )
    assert tasks == []
    assert any("missing_task_key" in b for b in blockers)


def test_duplicate_task_key_blocks_materialization():
    envelope = {
        "planned_tasks": [
            {"task_key": "dup", "label": "One", "canonical_task_type": "cnc_routing"},
            {"task_key": "dup", "label": "Two", "canonical_task_type": "led_wiring"},
        ],
    }
    _tasks, _warnings, blockers = materialize_operational_tasks_from_v2_envelope(
        envelope,
        execution_plan_id=1,
        order_id=1,
    )
    assert any("duplicate_task_key:dup" in b for b in blockers)


def test_unresolved_dependency_blocks_materialization():
    envelope = {
        "planned_tasks": [
            {
                "task_key": "child",
                "label": "Child",
                "canonical_task_type": "cnc_routing",
                "depends_on_task_keys": ["missing_parent"],
            },
        ],
    }
    _tasks, _warnings, blockers = materialize_operational_tasks_from_v2_envelope(
        envelope,
        execution_plan_id=1,
        order_id=1,
    )
    assert any("unresolved_dependency:child->missing_parent" in b for b in blockers)


def test_depends_on_task_keys_maps_to_depends_on_task_ids():
    envelope = {
        "planned_tasks": [
            {
                "task_key": "first",
                "label": "First",
                "canonical_task_type": "cnc_routing",
                "sequence_index": 1,
            },
            {
                "task_key": "second",
                "label": "Second",
                "canonical_task_type": "led_wiring",
                "depends_on_task_keys": ["first"],
                "sequence_index": 2,
            },
        ],
    }
    tasks, _warnings, blockers = materialize_operational_tasks_from_v2_envelope(
        envelope,
        execution_plan_id=99,
        order_id=100,
    )
    assert not blockers
    by_id = {t["task_id"]: t for t in tasks}
    assert by_id["second"]["depends_on_task_ids"] == ["first"]


# ---------------------------------------------------------------------------
# Service + integration tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_v2_envelope_materializes_operational_tasks(db_session):
    order, plan = await _seed_persisted_v2_plan(db_session, order_id=_MATERIALIZE_OID(11))
    before_reality = await _count_execution_reality(db_session)
    result = await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    after_reality = await _count_execution_reality(db_session)

    assert result.status == "materialized"
    assert result.execution_tasks_created is True
    assert result.operational_tasks_count >= 1
    assert result.no_sessions_created is True
    assert after_reality == before_reality

    envelope = await _load_envelope(db_session, order.id)
    assert envelope["execution_tasks_created"] is True
    assert envelope["operational_tasks_version"] == OPERATIONAL_TASKS_VERSION
    assert envelope["activation_status"] == "materialized"
    assert len(envelope["operational_tasks"]) >= 1


@pytest.mark.asyncio
async def test_task_key_maps_to_task_id_same_value(db_session):
    order, _plan = await _seed_persisted_v2_plan(db_session, order_id=_MATERIALIZE_OID(12))
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    for planned, operational in zip(envelope["planned_tasks"], envelope["operational_tasks"], strict=False):
        assert operational["task_id"] == planned["task_key"]
        assert operational["source_task_key"] == planned["task_key"]


@pytest.mark.asyncio
async def test_rerun_materialization_returns_409(db_session):
    order, _plan = await _seed_persisted_v2_plan(db_session, order_id=_MATERIALIZE_OID(13))
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    with pytest.raises(HTTPException) as exc:
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert exc.value.status_code == 409
    assert exc.value.detail["error"] == "operational_tasks_already_materialized"


@pytest.mark.asyncio
async def test_execution_reality_unchanged_after_materialize(db_session):
    order, _plan = await _seed_persisted_v2_plan(db_session, order_id=_MATERIALIZE_OID(14))
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    reality = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order.id)
        )
    ).scalar_one_or_none()
    assert reality is None


@pytest.mark.asyncio
async def test_assigned_employee_id_null_and_operational_status_pending(db_session):
    order, _plan = await _seed_persisted_v2_plan(db_session, order_id=_MATERIALIZE_OID(15))
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    for task in envelope["operational_tasks"]:
        assert task["assigned_employee_id"] is None
        assert task["operational_status"] == OPERATIONAL_STATUS_PENDING
        assert task["layer_id"] == V2_LAYER_ID
        assert task["quantity"] == 1.0


@pytest.mark.asyncio
async def test_mobile_required_legacy_fields_present(db_session):
    order, _plan = await _seed_persisted_v2_plan(db_session, order_id=_MATERIALIZE_OID(16))
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    task = envelope["operational_tasks"][0]
    for field in (
        "task_id",
        "name",
        "display_name",
        "process_type",
        "machine_type",
        "process_id",
        "estimated_time_minutes",
        "depends_on_task_ids",
    ):
        assert field in task


@pytest.mark.asyncio
async def test_null_estimated_minutes_yields_zero_with_warning(db_session):
    order, _plan = await _seed_persisted_v2_plan(db_session, order_id=_MATERIALIZE_OID(17))
    result = await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert PLANNING_MINUTES_WARNING in result.warnings
    envelope = await _load_envelope(db_session, order.id)
    assert envelope["operational_tasks"][0]["estimated_time_minutes"] == 0.0


@pytest.mark.asyncio
async def test_planned_tasks_unchanged_after_materialization(db_session):
    order, _plan = await _seed_persisted_v2_plan(db_session, order_id=_MATERIALIZE_OID(18))
    before = copy.deepcopy(json.loads(_plan.tasks_json)["planned_tasks"])
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    after = (await _load_envelope(db_session, order.id))["planned_tasks"]
    assert after == before


@pytest.mark.asyncio
async def test_snapshot_v2_json_not_mutated(db_session):
    order, _plan = await _seed_persisted_v2_plan(db_session, order_id=_MATERIALIZE_OID(19))
    before = order.snapshot_v2_json
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    await db_session.refresh(order)
    assert order.snapshot_v2_json == before


@pytest.mark.asyncio
async def test_non_v2_plan_returns_wrong_plan_source(db_session):
    order_id = _MATERIALIZE_OID(20)
    _seed_legacy_order(db_session, order_id=order_id)
    await db_session.flush()
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-LEG-{order_id}",
            snapshot_version=1,
            tasks_json=json.dumps([{"task_id": "T-001"}]),
            total_estimated_time_minutes=10.0,
            plan_source=None,
        )
    )
    await db_session.commit()
    with pytest.raises(HTTPException) as exc:
        await materialize_execution_plan_v2_operational_tasks(db_session, order_id)
    assert exc.value.status_code == 422
    assert "wrong_plan_source" in exc.value.detail["blockers"]


@pytest.mark.asyncio
async def test_missing_plan_returns_404(db_session):
    order = await _seed_v2_order_with_snapshot(db_session, order_id=_MATERIALIZE_OID(21))
    with pytest.raises(ExecutionPlanV2MaterializePlanNotFound):
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)


@pytest.mark.asyncio
async def test_missing_order_returns_404(db_session):
    with pytest.raises(ExecutionPlanV2MaterializeOrderNotFound):
        await materialize_execution_plan_v2_operational_tasks(db_session, 999999)


def test_endpoint_materialize_returns_201(db_fixture, db_session, auth_client):
    order_id = _MATERIALIZE_OID(22)

    async def _setup():
        order = await _seed_v2_order_with_snapshot(db_session, order_id=order_id)
        await create_execution_plan_v2_from_order(db_session, order.id)

    db_fixture.run(_setup())
    resp = auth_client.post(f"/api/v1/execution/plan-v2/materialize-tasks/{order_id}")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "materialized"
    assert body["execution_tasks_created"] is True
    assert body["no_sessions_created"] is True


def test_endpoint_plan_not_found_returns_404(db_fixture, db_session, auth_client):
    order_id = _MATERIALIZE_OID(23)

    async def _setup():
        await _seed_v2_order_with_snapshot(db_session, order_id=order_id)

    db_fixture.run(_setup())
    resp = auth_client.post(f"/api/v1/execution/plan-v2/materialize-tasks/{order_id}")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "plan_not_found"


def test_no_forbidden_imports():
    assert _forbidden_imports_in_paths() == set()


@pytest.mark.asyncio
async def test_operational_tasks_do_not_use_pricing_fields(db_session):
    order, _plan = await _seed_persisted_v2_plan(db_session, order_id=_MATERIALIZE_OID(24))
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    blob = json.dumps(envelope["operational_tasks"]).lower()
    assert "commercial_price" not in blob
    assert "estimated_internal_cost" not in blob
    assert "cost_result" not in blob


def test_scope_files_exclude_employee_mobile_paths():
    for path in STEP_9_3_4_PATHS:
        assert "employee_mobile" not in str(path).lower()
