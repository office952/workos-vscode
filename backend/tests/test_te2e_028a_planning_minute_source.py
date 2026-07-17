"""TE2E-028A — Planning-minute source integrity (aggregate → preview → plan → Post-Job)."""

from __future__ import annotations

import json
import uuid
import pytest

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.execution_plan_v2 import (
    PLANNING_MINUTES_SOURCE_AGGREGATE_OPS,
    PLANNING_MINUTES_WARNING,
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
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_plan_v2_preview_service import (
    build_execution_plan_v2_preview,
    resolve_planning_minutes_from_aggregate_op,
)
from services.post_job_truth_service import PostJobTruthService
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
OID_BASE = 972800


def _ops_from_rows(rows):
    """Thin wrapper — product_aggregate_service helper via service instance method path."""
    from services.product_aggregate_service import ProductAggregateService

    svc = ProductAggregateService.__new__(ProductAggregateService)
    return svc._operations_from_rows(
        rows,
        provenance="parent",
        source_template_code=TEMPLATE,
    )


def _sample_aggregate_with_minutes() -> ProductAggregate:
    return ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=[
            ProductAggregateOperation(
                operation_code="face_cnc_cut",
                label="Face CNC Cut",
                workcenter="WC_CNC",
                estimated_minutes=0.0,
                calculation_type="formula_based",
            ),
            ProductAggregateOperation(
                operation_code="qc_letters",
                label="Control calitate",
                workcenter="WC_QC",
                estimated_minutes=15.0,
                calculation_type="static",
            ),
            ProductAggregateOperation(
                operation_code="assembly_letters",
                label="Asamblare litere",
                workcenter="WC_ASSEMBLY",
                estimated_minutes=60.0,
                calculation_type="static",
            ),
        ],
        task_contract=ProductAggregateTaskContract(
            task_rules=[
                ProductAggregateTaskRule(
                    task_name="cnc_face_cut",
                    task_type="cnc_routing",
                    priced_operation="face_cnc_cut",
                    sequence=2,
                ),
                ProductAggregateTaskRule(
                    task_name="qc_internal",
                    task_type="quality_control",
                    priced_operation="qc_letters",
                    sequence=8,
                ),
                ProductAggregateTaskRule(
                    task_name="assembly",
                    task_type="volumetric_letter_assembly",
                    priced_operation="assembly_letters",
                    sequence=7,
                ),
            ]
        ),
    )


def _pd() -> ProductDefinitionPreview:
    return ProductDefinitionPreview(
        template_code=TEMPLATE,
        source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
        operation_roles=[
            ProductDefinitionOperationRole(
                operation_code="face_cnc_cut", label="Face CNC Cut", workcenter="WC_CNC"
            ),
            ProductDefinitionOperationRole(
                operation_code="qc_letters", label="Control calitate", workcenter="WC_QC"
            ),
            ProductDefinitionOperationRole(
                operation_code="assembly_letters",
                label="Asamblare litere",
                workcenter="WC_ASSEMBLY",
            ),
        ],
    )


async def _seed_order(db_session, *, order_id: int | None = None) -> Orders:
    oid = order_id or (OID_BASE + int(uuid.uuid4().hex[:4], 16) % 1000)
    record = QuoteSnapshotV2Record(
        snapshot_code=f"QSN2-TE2E028A-{oid}",
        snapshot_version="1.0.0",
        version=1,
        template_code=TEMPLATE,
        status="frozen",
        readiness="ready_for_owner_review",
        snapshot_json="{}",
        content_hash="te2e028a",
    )
    db_session.add(record)
    await db_session.flush()

    snapshot = OrderSnapshotV2(
        quote_id=oid,
        quote_snapshot_v2_id=int(record.id),
        snapshot_code=f"OSN2-TE2E028A-{oid}",
        content_hash="te2e028a" + ("0" * 24),
        product_definition_snapshot=_pd(),
        product_aggregate_snapshot=_sample_aggregate_with_minutes(),
        commercial_price_proposal_snapshot=_commercial_preview(total=1500.0),
        estimated_internal_cost_snapshot=_internal_preview(total=620.0),
        accepted_commercial_total=1500.0,
        accepted_currency="RON",
        estimated_internal_total=620.0,
    )
    order = Orders(
        id=oid,
        code=f"ORD-TE2E028A-{oid}",
        client_name="TE2E-028A Planning Minutes Fixture",
        status="locked",
        total_amount=1500.0,
        quote_id=oid,
        quote_snapshot_v2_id=int(record.id),
        snapshot_v2_json=snapshot.model_dump_json(),
        readiness_snapshot={
            "execution_plan_created": False,
            "no_execution_plan_created": True,
        },
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


def test_resolve_rejects_formula_zero_placeholder():
    op = ProductAggregateOperation(
        operation_code="x",
        estimated_minutes=0.0,
        calculation_type="formula_based",
    )
    assert resolve_planning_minutes_from_aggregate_op(op) == (None, None)


def test_resolve_accepts_static_nonzero():
    op = ProductAggregateOperation(
        operation_code="qc_letters",
        estimated_minutes=15.0,
        calculation_type="static",
    )
    minutes, source = resolve_planning_minutes_from_aggregate_op(op)
    assert minutes == 15.0
    assert source == PLANNING_MINUTES_SOURCE_AGGREGATE_OPS


def test_aggregate_operations_map_estimated_minutes_from_template_rows():
    ops = _ops_from_rows(
        [
            {
                "code": "qc_letters",
                "label": "Control calitate",
                "estimated_minutes": 15,
                "calculation_type": "static",
            },
            {
                "code": "face_cnc_cut",
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
            },
        ]
    )
    by_code = {o.operation_code: o for o in ops}
    assert by_code["qc_letters"].estimated_minutes == 15.0
    assert by_code["qc_letters"].calculation_type == "static"
    assert by_code["face_cnc_cut"].estimated_minutes == 0.0
    assert by_code["face_cnc_cut"].calculation_type == "formula_based"


@pytest.mark.asyncio
async def test_preview_preserves_static_minutes_and_source(db_session):
    order = await _seed_order(db_session)
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    by_op = {t.source_operation_code: t for t in preview.planned_tasks}

    qc = by_op["qc_letters"]
    assert qc.estimated_minutes == 15.0
    assert qc.planning_minutes_source == PLANNING_MINUTES_SOURCE_AGGREGATE_OPS
    assert PLANNING_MINUTES_WARNING not in qc.warnings

    assembly = by_op["assembly_letters"]
    assert assembly.estimated_minutes == 60.0
    assert assembly.planning_minutes_source == PLANNING_MINUTES_SOURCE_AGGREGATE_OPS

    cnc = by_op["face_cnc_cut"]
    assert cnc.estimated_minutes is None
    assert cnc.planning_minutes_source is None
    assert PLANNING_MINUTES_WARNING in cnc.warnings
    assert preview.status == "partial_missing_planning_minutes"
    assert PLANNING_MINUTES_WARNING in preview.warnings


@pytest.mark.asyncio
async def test_persist_materialize_postjob_preserve_planned_minutes(db_session):
    order = await _seed_order(db_session)
    commercial_before = float(order.total_amount)

    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    assert persist.status == "persisted"
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)

    plan = await db_session.get(ExecutionPlan, persist.execution_plan_id)
    envelope = json.loads(plan.tasks_json)
    planned = {t["source_operation_code"]: t for t in envelope["planned_tasks"]}
    ops = {t["source_operation_code"]: t for t in envelope["operational_tasks"]}

    assert planned["qc_letters"]["estimated_minutes"] == 15.0
    assert planned["qc_letters"]["planning_minutes_source"] == PLANNING_MINUTES_SOURCE_AGGREGATE_OPS
    assert ops["qc_letters"]["estimated_time_minutes"] == 15.0
    assert ops["qc_letters"]["planning_minutes_source"] == PLANNING_MINUTES_SOURCE_AGGREGATE_OPS

    assert planned["face_cnc_cut"]["estimated_minutes"] is None
    assert ops["face_cnc_cut"]["estimated_time_minutes"] is None

    truth = await PostJobTruthService(db_session).build_for_order(order.id)
    body = truth.model_dump(mode="json")
    assert body["write_back_performed"] is False
    qc_rows = [
        o
        for o in body["reconciliation"]["operations"]
        if o.get("planned_minutes", {}).get("value") == 15.0
    ]
    assert len(qc_rows) == 1
    qc_row = qc_rows[0]
    assert qc_row["planned_minutes"]["presence"] == "present"
    assert qc_row["planned_minutes"]["source"] == PLANNING_MINUTES_SOURCE_AGGREGATE_OPS
    assert qc_row["actual_minutes"]["presence"] == "not_captured"
    assert qc_row["reconciliation_state"] == "missing_actual"

    missing_plan = [
        o
        for o in body["reconciliation"]["operations"]
        if o.get("planned_minutes", {}).get("presence") == "missing"
    ]
    assert missing_plan, "formula placeholder must remain missing planned, not zero"

    await db_session.refresh(order)
    assert float(order.total_amount) == commercial_before


@pytest.mark.asyncio
async def test_variance_uses_nonzero_planned_versus_actual(db_session):
    order = await _seed_order(db_session)
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    plan = await db_session.get(ExecutionPlan, persist.execution_plan_id)
    envelope = json.loads(plan.tasks_json)
    qc_task = next(
        t for t in envelope["operational_tasks"] if t.get("source_operation_code") == "qc_letters"
    )
    task_id = qc_task["task_id"]

    reality = ExecutionReality(
        order_id=order.id,
        order_code=order.code,
        tasks_json=json.dumps(
            [
                {
                    "session_id": "te2e028a-qc-1",
                    "task_id": task_id,
                    "employee_id": 11,
                    "role": "primary",
                    "started_at": "2026-07-17T08:00:00+00:00",
                    "ended_at": "2026-07-17T08:25:00+00:00",
                    "duration_minutes": 25.0,
                }
            ]
        ),
        materials_json="[]",
        total_actual_time_minutes=25.0,
    )
    db_session.add(reality)
    await db_session.flush()

    truth = await PostJobTruthService(db_session).build_for_order(order.id)
    body = truth.model_dump(mode="json")
    assert body["write_back_performed"] is False
    qc_row = next(o for o in body["reconciliation"]["operations"] if o["task_id"] == task_id)
    assert qc_row["planned_minutes"]["value"] == 15.0
    assert qc_row["actual_minutes"]["value"] == 25.0
    assert qc_row["variance_minutes"]["value"] == 10.0
    assert qc_row["reconciliation_state"] == "variance"
    assert float(order.total_amount) == 1500.0
