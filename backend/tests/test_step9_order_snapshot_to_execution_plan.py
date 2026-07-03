"""Step 9 audit tests — Order snapshot V2 → ExecutionPlan V2 preview (read-only)."""

from __future__ import annotations

import ast
import uuid
from pathlib import Path

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from schemas.execution_plan_v2 import (
    EXECUTION_PLAN_V2_SOURCE,
    READINESS_GATE_EXCLUDED_WARNING,
)
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.product_definition import (
    ProductDefinitionOperationRole,
    ProductDefinitionPreview,
    ProductDefinitionSourceContext,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_plan_v2_preview_service import (
    FORBIDDEN_IMPORT_SUBSTRINGS,
    build_execution_plan_v2_preview,
)
from tests.test_execution_plan_v2_preview import (
    _build_order_snapshot_v2_json,
    _seed_v2_order_with_snapshot,
)
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

BACKEND_ROOT = Path(__file__).resolve().parents[1]
STEP_9_PATHS = (
    BACKEND_ROOT / "schemas" / "execution_plan_v2.py",
    BACKEND_ROOT / "services" / "execution_plan_v2_preview_service.py",
    BACKEND_ROOT / "routers" / "execution_plan_v2.py",
    Path(__file__).resolve(),
)

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _volumetric_convert_shaped_aggregate() -> ProductAggregate:
    """Task rules aligned with live order 88002 / volumetric dossier."""
    rules = [
        ProductAggregateTaskRule(
            task_name="vector_file_verification",
            task_type="READINESS_GATE",
            sequence=0,
        ),
        ProductAggregateTaskRule(
            task_name="vector_prep",
            task_type="file_preparation",
            priced_operation="vector_prep",
            sequence=1,
        ),
        ProductAggregateTaskRule(
            task_name="cnc_face_cut",
            task_type="cnc_routing",
            priced_operation="face_cnc_cut",
            sequence=2,
        ),
        ProductAggregateTaskRule(
            task_name="electrical_wiring",
            task_type="led_wiring",
            priced_operation="electrical_letters",
            sequence=9,
        ),
    ]
    return ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=[
            ProductAggregateOperation(
                operation_code="vector_prep",
                label="Vector Prep",
                workcenter="WC_PREPRESS",
            ),
            ProductAggregateOperation(
                operation_code="face_cnc_cut",
                label="Face CNC Cut",
                workcenter="WC_CNC",
            ),
            ProductAggregateOperation(
                operation_code="electrical_letters",
                label="Electrical Wiring",
                workcenter="WC_ELECTRICAL",
            ),
        ],
        task_contract=ProductAggregateTaskContract(task_rules=rules),
    )


def _volumetric_product_definition() -> ProductDefinitionPreview:
    return ProductDefinitionPreview(
        template_code=TEMPLATE,
        source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
        operation_roles=[
            ProductDefinitionOperationRole(
                operation_code="vector_prep",
                label="Vector Prep",
                workcenter="WC_PREPRESS",
            ),
            ProductDefinitionOperationRole(
                operation_code="face_cnc_cut",
                label="Face CNC Cut",
                workcenter="WC_CNC",
            ),
            ProductDefinitionOperationRole(
                operation_code="electrical_letters",
                label="Electrical Wiring",
                workcenter="WC_ELECTRICAL",
            ),
        ],
    )


def _build_convert_shaped_snapshot_json(*, order_id: int, quote_snapshot_v2_id: int) -> str:
    snapshot = OrderSnapshotV2(
        quote_id=order_id,
        quote_snapshot_v2_id=quote_snapshot_v2_id,
        snapshot_code="QSN2-STEP9-001",
        content_hash="step9hashstep9hashstep9hashstep9",
        product_definition_snapshot=_volumetric_product_definition(),
        product_aggregate_snapshot=_volumetric_convert_shaped_aggregate(),
        commercial_price_proposal_snapshot=_commercial_preview(total=1500.0),
        estimated_internal_cost_snapshot=_internal_preview(total=620.0),
        accepted_commercial_total=1500.0,
        accepted_currency="RON",
        estimated_internal_total=620.0,
    )
    return snapshot.model_dump_json()


@pytest.mark.asyncio
async def test_step9_preview_skips_readiness_gate_not_blocking(db_session):
    oid = 98000 + int(uuid.uuid4().hex[:4], 16) % 1000
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=oid,
        snapshot_v2_json=_build_convert_shaped_snapshot_json(
            order_id=oid,
            quote_snapshot_v2_id=oid,
        ),
    )
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.status == "partial_missing_planning_minutes"
    assert READINESS_GATE_EXCLUDED_WARNING in preview.warnings
    assert preview.no_write is True
    assert preview.execution_plan_created is False
    assert preview.execution_tasks_created is False
    assert preview.template_code == TEMPLATE
    assert preview.order_code == order.code
    task_keys = {task.task_key for task in preview.planned_tasks}
    assert "vector_file_verification" not in task_keys
    assert "vector_prep" in task_keys


@pytest.mark.asyncio
async def test_step9_preview_endpoint_no_execution_plan_write(db_fixture, db_session, auth_client):
    order = await _seed_v2_order_with_snapshot(db_session)
    plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    resp = auth_client.post(f"/api/v1/execution/plan-v2/preview/{order.id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["no_write"] is True
    assert body["source"] == EXECUTION_PLAN_V2_SOURCE
    assert body["persist_status"] == "not_persisted"
    plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    assert plans_after == plans_before


@pytest.mark.asyncio
async def test_step9_preview_blocks_missing_snapshot_v2_json(db_session):
    oid = 98100 + int(uuid.uuid4().hex[:4], 16) % 1000
    from models.orders import Orders

    order = Orders(
        id=oid,
        code=f"ORD-STEP9-NOSNAP-{oid}",
        client_name="No Snapshot",
        status="locked",
        total_amount=1500.0,
        quote_snapshot_v2_id=1,
        snapshot_v2_json=None,
    )
    db_session.add(order)
    await db_session.commit()
    preview = await build_execution_plan_v2_preview(db_session, oid)
    assert preview.status == "blocked_missing_order_snapshot_v2"
    assert preview.no_write is True


def test_step9_preview_forbidden_imports_static():
    found: set[str] = set()
    for path in STEP_9_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                    if part in node.module:
                        found.add(node.module)
    assert not any("quote_orchestrator" in mod for mod in found)
    assert not any("cost_engine_service" in mod for mod in found)


def test_step9_preview_does_not_call_price_endpoint():
    for path in STEP_9_PATHS[:-1]:
        text = path.read_text(encoding="utf-8")
        assert '"/price"' not in text
        assert "/api/v1/price" not in text


@pytest.mark.asyncio
async def test_step9_persist_draft_from_convert_shaped_snapshot(db_session):
    oid = 98200 + int(uuid.uuid4().hex[:4], 16) % 1000
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=oid,
    )
    aligned_snapshot = _build_convert_shaped_snapshot_json(
        order_id=oid,
        quote_snapshot_v2_id=int(order.quote_snapshot_v2_id),
    )
    order.snapshot_v2_json = aligned_snapshot
    await db_session.commit()
    await db_session.refresh(order)
    before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    assert after == before + 1
    assert result.status == "persisted"
    assert result.persist_status == "persisted"
    assert result.quote_snapshot_v2_id == order.quote_snapshot_v2_id
    assert result.template_code == TEMPLATE
    assert result.execution_tasks_created is False
    row = await db_session.get(ExecutionPlan, result.execution_plan_id)
    assert row.plan_source == EXECUTION_PLAN_V2_SOURCE
    assert row.source_quote_snapshot_v2_id == order.quote_snapshot_v2_id


@pytest.mark.asyncio
async def test_step9_persist_idempotent_second_call_no_extra_row(db_session):
    oid = 98300 + int(uuid.uuid4().hex[:4], 16) % 1000
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=oid,
    )
    order.snapshot_v2_json = _build_convert_shaped_snapshot_json(
        order_id=oid,
        quote_snapshot_v2_id=int(order.quote_snapshot_v2_id),
    )
    await db_session.commit()
    await db_session.refresh(order)
    first = await create_execution_plan_v2_from_order(db_session, order.id)
    before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    second = await create_execution_plan_v2_from_order(db_session, order.id)
    after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    assert after == before
    assert second.status == "already_exists"
    assert second.execution_plan_id == first.execution_plan_id
    assert second.execution_plan_created is False
