"""VECTOR_PREP_DURATION_E2E — controlled fixture Aggregate → EP → projection.

Owner GO: AUTHORIZE_VECTOR_PREP_DURATION_E2E_COMPLETENESS
Protected QA plans 21/22/23 are not mutated by these tests.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
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
from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview
from services.planning_duration_contract import (
    LETTERS_VECTOR_PREP_DURATION,
    PLANNING_MINUTES_SOURCE_LETTERS_VECTOR_PREP,
)
from services.product_aggregate_planning_duration_service import (
    PLANNING_DURATION_STATUS_INVALID_INPUT,
    PLANNING_DURATION_STATUS_MISSING_INPUT,
    PLANNING_DURATION_STATUS_RESOLVED,
    apply_planning_duration_resolution,
    collect_planning_duration_facts,
)
from services.task_resource_requirement_projection_service import (
    project_plan_resource_requirements,
    project_task_resource_requirements,
)
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
OID_BASE = 974200
LETTER_COUNT = 5
EXPECTED_MINUTES = 10.0
WC_PREPRESS = "WC_PREPRESS"
QA_DB = Path(__file__).resolve().parents[1] / "dev.db"
PLAN23_SHA = (
    "00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2"
)
PLAN21_SHA = (
    "75933211c1c180d421648bd3c54a96493716ba4c92262f42032c522486b9ff59"
)
PLAN22_SHA = (
    "0ec2dce6f1daea4509808b876f58c9ee7326fb7059e64d057cd81fbbd35ecb97"
)


def _raw_ops(*, workcenter: str = WC_PREPRESS) -> list[ProductAggregateOperation]:
    return [
        ProductAggregateOperation(
            operation_code="vector_prep",
            label="Pregătire vector / font",
            workcenter=workcenter,
            formula_id="letter_count_material",
            estimated_minutes=0.0,
            calculation_type="formula_based",
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
        ]
    )


def _pd(*, letter_count: int | None) -> ProductDefinitionPreview:
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
                workcenter=WC_PREPRESS,
            ),
        ],
        geometry_inputs=geometry,
        canonical_values=dict(geometry),
    )


def _aggregate(*, letter_count: int | None) -> ProductAggregate:
    raw = ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=_raw_ops(),
        task_contract=_task_contract(),
    )
    # Factual geometry only — never invent letter_count.
    facts = collect_planning_duration_facts(
        {"quote_geometry": {"letter_count": letter_count}}
        if letter_count is not None
        else {}
    )
    if letter_count is not None:
        assert facts.get("letter_count") == letter_count
    return apply_planning_duration_resolution(raw, facts)


# ---------------------------------------------------------------------------
# Contract / resolver
# ---------------------------------------------------------------------------


def test_formula_authority_is_single_contract():
    assert LETTERS_VECTOR_PREP_DURATION.formula_params is not None
    assert LETTERS_VECTOR_PREP_DURATION.formula_params["minutes_per_letter"] == 2.0
    assert (
        LETTERS_VECTOR_PREP_DURATION.planning_minutes_source
        == PLANNING_MINUTES_SOURCE_LETTERS_VECTOR_PREP
    )


@pytest.mark.parametrize(
    "letter_count,expected",
    [(1, 2.0), (5, 10.0), (9, 18.0)],
)
def test_letter_count_resolves_duration_and_source(letter_count: int, expected: float):
    agg = _aggregate(letter_count=letter_count)
    vp = agg.operations[0]
    assert vp.estimated_minutes == expected
    assert vp.planning_minutes_source == PLANNING_MINUTES_SOURCE_LETTERS_VECTOR_PREP
    assert vp.planning_duration_status == PLANNING_DURATION_STATUS_RESOLVED


def test_missing_letter_count_preserves_null():
    agg = _aggregate(letter_count=None)
    vp = agg.operations[0]
    assert vp.estimated_minutes is None
    assert vp.estimated_minutes != 0
    assert vp.planning_minutes_source is None
    assert vp.planning_duration_status == PLANNING_DURATION_STATUS_MISSING_INPUT


def test_zero_letter_count_invalid_preserves_null():
    """Canonical COUNT_BASED_TIME: letter_count must be int > 0."""
    raw = ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=_raw_ops(),
        task_contract=_task_contract(),
    )
    agg = apply_planning_duration_resolution(raw, {"letter_count": 0})
    vp = agg.operations[0]
    assert vp.estimated_minutes is None
    assert vp.planning_minutes_source is None
    assert vp.planning_duration_status == PLANNING_DURATION_STATUS_INVALID_INPUT


def test_no_dispatch_fallback_when_missing():
    agg = _aggregate(letter_count=None)
    vp = agg.operations[0]
    # volumetric_execution_dispatch defaults must not appear
    assert vp.estimated_minutes not in {15.0, 15}


# ---------------------------------------------------------------------------
# Aggregate → EP → projection (isolated fixture DB via pytest db_session)
# ---------------------------------------------------------------------------


async def _seed_controlled_order(
    db_session,
    *,
    letter_count: int | None = LETTER_COUNT,
) -> Orders:
    oid = OID_BASE + int(uuid.uuid4().hex[:4], 16) % 500
    record = QuoteSnapshotV2Record(
        snapshot_code=f"QSN2-VP-E2E-{oid}",
        snapshot_version="1.0.0",
        version=1,
        template_code=TEMPLATE,
        status="frozen",
        readiness="ready_for_owner_review",
        snapshot_json="{}",
        content_hash="vp-e2e",
    )
    db_session.add(record)
    await db_session.flush()

    snapshot = OrderSnapshotV2(
        quote_id=oid,
        quote_snapshot_v2_id=int(record.id),
        snapshot_code=f"OSN2-VP-E2E-{oid}",
        content_hash="vp-e2e" + ("0" * 26),
        product_definition_snapshot=_pd(letter_count=letter_count),
        product_aggregate_snapshot=_aggregate(letter_count=letter_count),
        commercial_price_proposal_snapshot=_commercial_preview(total=1000.0),
        estimated_internal_cost_snapshot=_internal_preview(total=400.0),
        accepted_commercial_total=1000.0,
        accepted_currency="RON",
        estimated_internal_total=400.0,
    )
    order = Orders(
        id=oid,
        code=f"ORD-VP-E2E-{oid}",
        client_name="LOCAL_TEST_FIXTURE vector_prep duration E2E",
        status="locked",
        total_amount=1000.0,
        quote_id=oid,
        quote_snapshot_v2_id=int(record.id),
        snapshot_v2_json=snapshot.model_dump_json(),
        readiness_snapshot={
            "execution_plan_created": False,
            "local_test_fixture": True,
            "vector_prep_duration_e2e": True,
            "retention": "dev_ephemeral",
        },
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


@pytest.mark.asyncio
async def test_positive_fixture_ep_and_projection(db_session):
    order = await _seed_controlled_order(db_session, letter_count=LETTER_COUNT)

    preview = await build_execution_plan_v2_preview(db_session, order.id)
    vp_preview = next(
        t for t in preview.planned_tasks if t.source_operation_code == "vector_prep"
    )
    assert vp_preview.estimated_minutes == EXPECTED_MINUTES
    assert vp_preview.planning_minutes_source == PLANNING_MINUTES_SOURCE_LETTERS_VECTOR_PREP
    assert (
        vp_preview.machine_requirement is not None
        and vp_preview.machine_requirement.workcenter == WC_PREPRESS
    )

    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    assert persist.status == "persisted"
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)

    plan = await db_session.get(ExecutionPlan, persist.execution_plan_id)
    assert plan is not None
    envelope = json.loads(plan.tasks_json)
    ops = {
        t["source_operation_code"]: t for t in envelope["operational_tasks"]
    }
    vp_op = ops["vector_prep"]
    assert vp_op["estimated_time_minutes"] == EXPECTED_MINUTES
    assert vp_op["planning_minutes_source"] == PLANNING_MINUTES_SOURCE_LETTERS_VECTOR_PREP
    assert vp_op["workcenter"] == WC_PREPRESS

    # No secondary recalculation: snapshot equals Aggregate emission
    assert vp_op["estimated_time_minutes"] == EXPECTED_MINUTES

    proj = await project_plan_resource_requirements(
        db_session, plan_id=int(plan.id), task_key=str(vp_op["task_id"])
    )
    assert proj.summary.total_tasks == 1
    task = proj.tasks[0]
    assert task.operation_code == "vector_prep"
    assert task.workcenter_code == WC_PREPRESS
    assert task.estimated_time_minutes == EXPECTED_MINUTES
    assert task.planning_minutes_source == PLANNING_MINUTES_SOURCE_LETTERS_VECTOR_PREP
    assert "estimated_time_minutes" in task.known_fields
    assert "planning_minutes_source" in task.known_fields
    # PREPRESS soft hint + duration → KNOWN_MINIMAL
    assert task.resource_mode_hint == "PERSON_DRIVEN"
    assert task.resource_requirements_status == "KNOWN_MINIMAL"


@pytest.mark.asyncio
async def test_missing_letter_count_fixture_null_projection(db_session):
    order = await _seed_controlled_order(db_session, letter_count=None)
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    plan = await db_session.get(ExecutionPlan, persist.execution_plan_id)
    assert plan is not None
    envelope = json.loads(plan.tasks_json)
    vp_op = next(
        t
        for t in envelope["operational_tasks"]
        if t.get("source_operation_code") == "vector_prep"
    )
    assert vp_op["estimated_time_minutes"] is None
    assert vp_op.get("planning_minutes_source") is None

    task = project_task_resource_requirements(
        vp_op, execution_plan_id=int(plan.id)
    )
    assert task.estimated_time_minutes is None
    assert "estimated_time_minutes" in task.unknown_fields
    assert task.resource_requirements_status == "PARTIAL"


# ---------------------------------------------------------------------------
# Protected QA plans — read-only SHA guard (skips if QA DB absent)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not QA_DB.is_file(), reason="QA dev.db not present")
def test_protected_plans_sha_unchanged_read_only():
    import sqlite3

    conn = sqlite3.connect(QA_DB)
    try:
        for pid, expected in (
            (21, PLAN21_SHA),
            (22, PLAN22_SHA),
            (23, PLAN23_SHA),
        ):
            tj = conn.execute(
                "select tasks_json from execution_plan where id=?", (pid,)
            ).fetchone()[0]
            assert hashlib.sha256(tj.encode()).hexdigest() == expected
        env = json.loads(
            conn.execute(
                "select tasks_json from execution_plan where id=23"
            ).fetchone()[0]
        )
        vp = next(
            t
            for t in (env.get("operational_tasks") or [])
            if "vector_prep" in str(t.get("task_id") or "")
        )
        assert vp.get("estimated_time_minutes") is None
        assert vp.get("planning_minutes_source") is None
        assert len(env.get("operational_tasks") or []) == 13
    finally:
        conn.close()
