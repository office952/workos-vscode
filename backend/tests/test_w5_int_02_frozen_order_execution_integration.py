"""W5-INT-02 integrated Wave 5 seam tests — frozen order → execution runtime chain."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from schemas.execution_plan_v2_frozen_task_identity import FROZEN_TASK_IDENTITY_VERSION
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.order_snapshot_v2_planning_readiness import PLANNING_READINESS_CONTRACT_VERSION
from schemas.quote_snapshot_v2 import QuoteSnapshotOwnerDecision
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview
from services.execution_plan_v2_materialize_service import materialize_execution_plan_v2_operational_tasks
from services.order_snapshot_v2_planning_readiness_adapter_service import (
    load_order_planning_readiness_input,
)
from services.task_start_gate_service import assert_task_startable, load_order_quote_input
from tests.test_execution_owner_decision_production_release_guard import (
    NONBLOCKING,
    PRODUCTION_BLOCKERS,
)
from tests.test_execution_plan_v2_frozen_task_identity import (
    IDENTITY_OID_BASE,
    MOUNTING_NODE,
    ROOT_NODE,
    _build_identity_snapshot,
    _identity_aggregate,
)
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot
from tests.test_order_snapshot_v2_planning_readiness_adapter import (
    _snapshot_with_preparation_canonical,
)

INT02_OID_BASE = 23000
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _snapshot_with_production_blockers(order_id: int) -> str:
    aggregate = _identity_aggregate(include_mounting=True)
    payload = json.loads(_build_identity_snapshot(aggregate))
    payload["owner_decisions_snapshot"] = [
        QuoteSnapshotOwnerDecision(
            code=code,
            label=code.replace("_", " ").title(),
            source="estimated_internal_cost",
            module_code="test_module",
            detail="int02 gate",
        ).model_dump()
        for code in PRODUCTION_BLOCKERS
    ] + [
        QuoteSnapshotOwnerDecision(
            code=NONBLOCKING[0],
            label="Nonblocking",
            source="estimated_internal_cost",
            module_code="test_module",
            detail="int02 gate",
        ).model_dump()
    ]
    payload["quote_id"] = order_id
    payload["quote_snapshot_v2_id"] = order_id
    payload["snapshot_code"] = "OSN2-INT02-GATE"
    return json.dumps(payload)


@pytest.mark.asyncio
async def test_int02_preview_persist_materialize_identity_chain(db_session):
    order_id = INT02_OID_BASE + 1
    snapshot_json = _snapshot_with_production_blockers(order_id)
    before_hash = hash(snapshot_json)
    await _seed_v2_order_with_snapshot(
        db_session,
        order_id=order_id,
        snapshot_v2_json=snapshot_json,
    )

    preview_one = await build_execution_plan_v2_preview(db_session, order_id)
    preview_two = await build_execution_plan_v2_preview(db_session, order_id)
    keys_one = [t.task_key for t in preview_one.planned_tasks]
    keys_two = [t.task_key for t in preview_two.planned_tasks]
    assert keys_one == keys_two
    assert all(":" in k for k in keys_one)
    assert all(t.frozen_identity for t in preview_one.planned_tasks)

    persist_one = await create_execution_plan_v2_from_order(db_session, order_id)
    persist_two = await create_execution_plan_v2_from_order(db_session, order_id)
    assert persist_one.status in {"created", "already_exists", "persisted"}
    assert persist_two.status == "already_exists"

    materialized = await materialize_execution_plan_v2_operational_tasks(db_session, order_id)
    assert materialized.operational_tasks_count >= 1

    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one()
    envelope = json.loads(plan.tasks_json)
    op_tasks = envelope.get("operational_tasks") or []
    op_keys = [t.get("task_id") or t.get("task_key") for t in op_tasks if isinstance(t, dict)]
    assert set(op_keys) == set(keys_one)

    refreshed = await db_session.get(Orders, order_id)
    assert hash(refreshed.snapshot_v2_json or "") == before_hash


@pytest.mark.asyncio
async def test_int02_readiness_adapter_on_persisted_plan_path(db_session):
    order_id = INT02_OID_BASE + 2
    await _seed_v2_order_with_snapshot(
        db_session,
        order_id=order_id,
        snapshot_v2_json=_snapshot_with_preparation_canonical(
            quote_id=order_id,
            quote_snapshot_v2_id=order_id,
            preparation={"mounting_template_material_type": "forex", "mounting_template_area_m2": 1.5},
        ),
    )
    await create_execution_plan_v2_from_order(db_session, order_id)
    payload = await load_order_quote_input(db_session, order_id)
    assert payload["_planning_readiness_authority"] == "FROZEN_ORDER_SNAPSHOT_V2"
    assert payload["_planning_readiness_contract"] == PLANNING_READINESS_CONTRACT_VERSION
    assert payload["mounting_template_material_type"] == "forex"


@pytest.mark.asyncio
async def test_int02_production_guard_blocks_after_v2_persist(db_session):
    order_id = INT02_OID_BASE + 3
    await _seed_v2_order_with_snapshot(
        db_session,
        order_id=order_id,
        snapshot_v2_json=_snapshot_with_production_blockers(order_id),
    )
    preview = await build_execution_plan_v2_preview(db_session, order_id)
    await create_execution_plan_v2_from_order(db_session, order_id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order_id)
    task_id = preview.planned_tasks[0].task_key

    with pytest.raises(HTTPException) as exc:
        await assert_task_startable(db_session, order_id=order_id, task_id=task_id)
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "production_release_blocked"


@pytest.mark.asyncio
async def test_int02_corrupt_snapshot_fail_closed_no_legacy_fallback(db_session):
    order_id = INT02_OID_BASE + 4
    order = Orders(
        id=order_id,
        code=f"ORD-INT02-{order_id}",
        client_name="INT02",
        status="locked",
        total_amount=1500.0,
        quote_snapshot_v2_id=order_id,
        snapshot_v2_json="{bad-json",
        snapshot_line_items=json.dumps({"quote_input": {"mounting_template_material_type": "paper"}}),
    )
    db_session.add(order)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await load_order_planning_readiness_input(db_session, order_id)
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_int02_mounting_task_preserves_graph_identity_through_chain(db_session):
    order_id = INT02_OID_BASE + 5
    await _seed_v2_order_with_snapshot(
        db_session,
        order_id=order_id,
        snapshot_v2_json=_snapshot_with_production_blockers(order_id),
    )
    preview = await build_execution_plan_v2_preview(db_session, order_id)
    mounting = next(
        t for t in preview.planned_tasks if t.frozen_identity and t.frozen_identity.source_graph_node_id == MOUNTING_NODE
    )
    assert mounting.frozen_identity.contract_version == FROZEN_TASK_IDENTITY_VERSION
    assert mounting.frozen_identity.source_component_role == "mounting_panel"


def test_int02_preview_service_does_not_use_snapshot_line_items_authority():
    path = BACKEND_ROOT / "services" / "execution_plan_v2_preview_service.py"
    source = path.read_text(encoding="utf-8")
    assert "snapshot_line_items" not in source


def test_int02_v2_adapter_does_not_use_live_product_system():
    path = BACKEND_ROOT / "services" / "order_snapshot_v2_planning_readiness_adapter_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {"product_system", "product_definition_builder", "quote_orchestrator"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(part in node.module for part in forbidden)


def test_int02_task_start_gate_delegates_readiness_to_adapter():
    source = inspect.getsource(load_order_quote_input)
    assert "load_order_planning_readiness_input" in source
