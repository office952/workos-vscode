"""TE2E-028B — Formula planning-duration authority (Aggregate resolve → Plan → Post-Job)."""

from __future__ import annotations

import json
import uuid

import pytest

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.execution_plan_v2 import (
    PLANNING_MINUTES_SOURCE_AGGREGATE_FORMULA_PREFIX,
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
from services.formula_handlers import FormulaId
from services.planning_duration_contract import (
    LETTERS_VECTOR_PREP_DURATION,
    get_planning_duration_contract,
)
from services.post_job_truth_service import PostJobTruthService
from services.product_aggregate_planning_duration_service import (
    PLANNING_DURATION_STATUS_MISSING_INPUT,
    PLANNING_DURATION_STATUS_PLACEHOLDER,
    PLANNING_DURATION_STATUS_RESOLVED,
    apply_planning_duration_resolution,
    planning_minutes_source_for_formula,
)
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
OID_BASE = 972850
LETTER_COUNT = 5
EXPECTED_VECTOR_PREP_MINUTES = 10.0  # 5 * 2.0 minutes_per_letter
COMMERCIAL_TOTAL = 1888.0


def _raw_ops() -> list[ProductAggregateOperation]:
    return [
        ProductAggregateOperation(
            operation_code="vector_prep",
            label="Pregătire vector / font",
            workcenter="PREPRESS",
            formula_id="letter_count_material",
            estimated_minutes=0.0,
            calculation_type="formula_based",
        ),
        ProductAggregateOperation(
            operation_code="face_cnc_cut",
            label="Face CNC Cut",
            workcenter="WC_CNC",
            formula_id="perimeter_pass_linear_meter",
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
    ]


def _task_contract() -> ProductAggregateTaskContract:
    return ProductAggregateTaskContract(
        task_rules=[
            ProductAggregateTaskRule(
                task_name="vector_prep",
                task_type="prepress",
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
    )


def _pd(*, letter_count: int | None = LETTER_COUNT) -> ProductDefinitionPreview:
    geometry: dict = {}
    if letter_count is not None:
        geometry["letter_count"] = letter_count
    return ProductDefinitionPreview(
        template_code=TEMPLATE,
        source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
        operation_roles=[
            ProductDefinitionOperationRole(
                operation_code="vector_prep",
                label="Pregătire vector / font",
                workcenter="PREPRESS",
            ),
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
        geometry_inputs=geometry,
        canonical_values=dict(geometry),
    )


def _aggregate_resolved(*, letter_count: int | None = LETTER_COUNT) -> ProductAggregate:
    raw = ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=_raw_ops(),
        task_contract=_task_contract(),
    )
    facts = {"letter_count": letter_count} if letter_count is not None else {}
    return apply_planning_duration_resolution(raw, facts)


async def _seed_order(
    db_session,
    *,
    order_id: int | None = None,
    letter_count: int | None = LETTER_COUNT,
    commercial_total: float = COMMERCIAL_TOTAL,
) -> Orders:
    oid = order_id or (OID_BASE + int(uuid.uuid4().hex[:4], 16) % 1000)
    record = QuoteSnapshotV2Record(
        snapshot_code=f"QSN2-TE2E028B-{oid}",
        snapshot_version="1.0.0",
        version=1,
        template_code=TEMPLATE,
        status="frozen",
        readiness="ready_for_owner_review",
        snapshot_json="{}",
        content_hash="te2e028b",
    )
    db_session.add(record)
    await db_session.flush()

    snapshot = OrderSnapshotV2(
        quote_id=oid,
        quote_snapshot_v2_id=int(record.id),
        snapshot_code=f"OSN2-TE2E028B-{oid}",
        content_hash="te2e028b" + ("0" * 24),
        product_definition_snapshot=_pd(letter_count=letter_count),
        product_aggregate_snapshot=_aggregate_resolved(letter_count=letter_count),
        commercial_price_proposal_snapshot=_commercial_preview(total=commercial_total),
        estimated_internal_cost_snapshot=_internal_preview(total=620.0),
        accepted_commercial_total=commercial_total,
        accepted_currency="RON",
        estimated_internal_total=620.0,
    )
    order = Orders(
        id=oid,
        code=f"ORD-TE2E028B-LOCAL-{oid}",
        client_name="LOCAL_TEST_FIXTURE TE2E-028B Formula Duration",
        status="locked",
        total_amount=commercial_total,
        quote_id=oid,
        quote_snapshot_v2_id=int(record.id),
        snapshot_v2_json=snapshot.model_dump_json(),
        readiness_snapshot={
            "execution_plan_created": False,
            "no_execution_plan_created": True,
            "local_test_fixture": True,
            "te2e_028b": True,
            "retention": "dev_ephemeral",
        },
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


def test_product_system_duration_contract_is_count_based_time():
    contract = get_planning_duration_contract(TEMPLATE, "vector_prep")
    assert contract is not None
    assert contract is LETTERS_VECTOR_PREP_DURATION
    assert contract.duration_mode == "formula"
    assert contract.formula_id == FormulaId.COUNT_BASED_TIME.value
    assert contract.required_inputs == ("letter_count",)
    # Must not reuse the commercial quantity formula id.
    assert contract.formula_id != "letter_count_material"
    assert contract.formula_id != "perimeter_pass_linear_meter"


def test_aggregate_resolves_vector_prep_minutes_and_provenance():
    agg = _aggregate_resolved(letter_count=LETTER_COUNT)
    by_code = {o.operation_code: o for o in agg.operations}

    vp = by_code["vector_prep"]
    assert vp.estimated_minutes == EXPECTED_VECTOR_PREP_MINUTES
    assert vp.planning_duration_mode == "formula"
    assert vp.planning_duration_status == PLANNING_DURATION_STATUS_RESOLVED
    assert vp.planning_duration_formula_id == FormulaId.COUNT_BASED_TIME.value
    assert vp.planning_minutes_source == planning_minutes_source_for_formula(
        FormulaId.COUNT_BASED_TIME.value
    )
    # Commercial formula id preserved on the op.
    assert vp.formula_id == "letter_count_material"


def test_missing_letter_count_stays_null_not_zero():
    agg = _aggregate_resolved(letter_count=None)
    vp = next(o for o in agg.operations if o.operation_code == "vector_prep")
    assert vp.estimated_minutes is None
    assert vp.planning_duration_mode == "formula"
    assert vp.planning_duration_status == PLANNING_DURATION_STATUS_MISSING_INPUT
    assert vp.planning_minutes_source is None


def test_malformed_letter_count_stays_null():
    raw = ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=_raw_ops(),
        task_contract=_task_contract(),
    )
    agg = apply_planning_duration_resolution(raw, {"letter_count": "not-a-number"})
    vp = next(o for o in agg.operations if o.operation_code == "vector_prep")
    assert vp.estimated_minutes is None
    assert vp.planning_minutes_source is None


def test_placeholder_quantity_op_cleared_to_null():
    agg = _aggregate_resolved(letter_count=LETTER_COUNT)
    face = next(o for o in agg.operations if o.operation_code == "face_cnc_cut")
    assert face.estimated_minutes is None
    assert face.planning_duration_mode == "none"
    assert face.planning_duration_status == PLANNING_DURATION_STATUS_PLACEHOLDER


def test_static_ops_not_overwritten_by_formula_resolution():
    agg = _aggregate_resolved(letter_count=LETTER_COUNT)
    by_code = {o.operation_code: o for o in agg.operations}
    assert by_code["qc_letters"].estimated_minutes == 15.0
    assert by_code["qc_letters"].planning_duration_mode == "static"
    assert by_code["assembly_letters"].estimated_minutes == 60.0
    assert by_code["assembly_letters"].planning_duration_mode == "static"


def test_plan_resolver_accepts_formula_resolved_and_rejects_placeholder():
    agg = _aggregate_resolved(letter_count=LETTER_COUNT)
    by_code = {o.operation_code: o for o in agg.operations}

    minutes, source = resolve_planning_minutes_from_aggregate_op(by_code["vector_prep"])
    assert minutes == EXPECTED_VECTOR_PREP_MINUTES
    assert source is not None
    assert source.startswith(PLANNING_MINUTES_SOURCE_AGGREGATE_FORMULA_PREFIX)
    assert FormulaId.COUNT_BASED_TIME.value in source

    minutes_qc, source_qc = resolve_planning_minutes_from_aggregate_op(by_code["qc_letters"])
    assert minutes_qc == 15.0
    assert source_qc == PLANNING_MINUTES_SOURCE_AGGREGATE_OPS

    face = ProductAggregateOperation(
        operation_code="face_cnc_cut",
        estimated_minutes=0.0,
        calculation_type="formula_based",
    )
    assert resolve_planning_minutes_from_aggregate_op(face) == (None, None)


def test_explicit_zero_accepted_only_with_formula_provenance():
    op = ProductAggregateOperation(
        operation_code="vector_prep",
        estimated_minutes=0.0,
        calculation_type="formula_based",
        planning_duration_mode="formula",
        planning_duration_status="resolved",
        planning_duration_formula_id=FormulaId.COUNT_BASED_TIME.value,
        planning_minutes_source=planning_minutes_source_for_formula(
            FormulaId.COUNT_BASED_TIME.value
        ),
    )
    minutes, source = resolve_planning_minutes_from_aggregate_op(op)
    assert minutes == 0.0
    assert source is not None
    assert FormulaId.COUNT_BASED_TIME.value in source


@pytest.mark.asyncio
async def test_preview_persist_materialize_postjob_formula_minutes(db_session):
    order = await _seed_order(db_session)
    commercial_before = float(order.total_amount)

    preview = await build_execution_plan_v2_preview(db_session, order.id)
    by_op = {t.source_operation_code: t for t in preview.planned_tasks}

    vp = by_op["vector_prep"]
    assert vp.estimated_minutes == EXPECTED_VECTOR_PREP_MINUTES
    assert vp.planning_minutes_source is not None
    assert vp.planning_minutes_source.startswith(PLANNING_MINUTES_SOURCE_AGGREGATE_FORMULA_PREFIX)
    assert PLANNING_MINUTES_WARNING not in vp.warnings

    assert by_op["qc_letters"].estimated_minutes == 15.0
    assert by_op["qc_letters"].planning_minutes_source == PLANNING_MINUTES_SOURCE_AGGREGATE_OPS
    assert by_op["face_cnc_cut"].estimated_minutes is None

    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    assert persist.status == "persisted"
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)

    plan = await db_session.get(ExecutionPlan, persist.execution_plan_id)
    envelope = json.loads(plan.tasks_json)
    planned = {t["source_operation_code"]: t for t in envelope["planned_tasks"]}
    ops = {t["source_operation_code"]: t for t in envelope["operational_tasks"]}

    assert planned["vector_prep"]["estimated_minutes"] == EXPECTED_VECTOR_PREP_MINUTES
    assert ops["vector_prep"]["estimated_time_minutes"] == EXPECTED_VECTOR_PREP_MINUTES
    assert FormulaId.COUNT_BASED_TIME.value in (
        planned["vector_prep"].get("planning_minutes_source") or ""
    )

    truth = await PostJobTruthService(db_session).build_for_order(order.id)
    body = truth.model_dump(mode="json")
    assert body["write_back_performed"] is False
    vp_rows = [
        o
        for o in body["reconciliation"]["operations"]
        if o.get("planned_minutes", {}).get("value") == EXPECTED_VECTOR_PREP_MINUTES
    ]
    assert len(vp_rows) == 1
    assert vp_rows[0]["planned_minutes"]["presence"] == "present"
    assert vp_rows[0]["actual_minutes"]["presence"] == "not_captured"
    assert vp_rows[0]["reconciliation_state"] == "missing_actual"

    await db_session.refresh(order)
    assert float(order.total_amount) == commercial_before == COMMERCIAL_TOTAL


@pytest.mark.asyncio
async def test_formula_duration_inputs_do_not_change_commercial_total(db_session):
    order_a = await _seed_order(db_session, letter_count=5, commercial_total=COMMERCIAL_TOTAL)
    order_b = await _seed_order(db_session, letter_count=9, commercial_total=COMMERCIAL_TOTAL)

    preview_a = await build_execution_plan_v2_preview(db_session, order_a.id)
    preview_b = await build_execution_plan_v2_preview(db_session, order_b.id)
    vp_a = next(t for t in preview_a.planned_tasks if t.source_operation_code == "vector_prep")
    vp_b = next(t for t in preview_b.planned_tasks if t.source_operation_code == "vector_prep")
    assert vp_a.estimated_minutes == 10.0
    assert vp_b.estimated_minutes == 18.0
    assert float(order_a.total_amount) == float(order_b.total_amount) == COMMERCIAL_TOTAL
