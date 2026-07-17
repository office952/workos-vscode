"""Commercial pricing ↔ operational time isolation (audit differential proof).

Uncommitted pending owner review. Does not mutate Wave 7 refs or order 972901.
"""

from __future__ import annotations

import ast
import json
import uuid
from pathlib import Path

import pytest

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
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
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.post_job_truth_service import PostJobTruthService
from tests.test_commercial_price_proposal_preview import _full_quote_input
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
OID_BASE = 973500

_BANNED_PRICING_MODULES = (
    "commercial_price_proposal",
    "quote_orchestrator",
    "cost_engine_service",
    "intake_v6_priced_quote",
)


def _ast_import_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.append(node.module)
    return out


def _assert_no_pricing_imports(rel_path: str) -> None:
    modules = _ast_import_modules(Path(__file__).resolve().parents[1] / rel_path)
    bad = [m for m in modules if any(b in m for b in _BANNED_PRICING_MODULES)]
    assert bad == [], f"{rel_path} imports pricing modules: {bad}"


def _aggregate(qc_minutes: float) -> ProductAggregate:
    return ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=[
            ProductAggregateOperation(
                operation_code="qc_letters",
                label="Control calitate",
                workcenter="WC_QC",
                estimated_minutes=qc_minutes,
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
                operation_code="qc_letters", label="Control calitate", workcenter="WC_QC"
            ),
            ProductDefinitionOperationRole(
                operation_code="assembly_letters",
                label="Asamblare",
                workcenter="WC_ASSEMBLY",
            ),
        ],
    )


async def _seed_order(db_session, *, qc_minutes: float, commercial_total: float = 1500.0) -> Orders:
    oid = OID_BASE + int(uuid.uuid4().hex[:4], 16) % 900
    record = QuoteSnapshotV2Record(
        snapshot_code=f"QSN2-CTIME-{oid}",
        snapshot_version="1.0.0",
        version=1,
        template_code=TEMPLATE,
        status="frozen",
        readiness="ready_for_owner_review",
        snapshot_json="{}",
        content_hash=f"ctime{oid}",
    )
    db_session.add(record)
    await db_session.flush()

    snapshot = OrderSnapshotV2(
        quote_id=oid,
        quote_snapshot_v2_id=int(record.id),
        snapshot_code=f"OSN2-CTIME-{oid}",
        content_hash=("ctime" + "0" * 28)[:32],
        product_definition_snapshot=_pd(),
        product_aggregate_snapshot=_aggregate(qc_minutes),
        commercial_price_proposal_snapshot=_commercial_preview(total=commercial_total),
        estimated_internal_cost_snapshot=_internal_preview(total=620.0),
        accepted_commercial_total=commercial_total,
        accepted_currency="RON",
        estimated_internal_total=620.0,
        no_reprice_policy=True,
    )
    order = Orders(
        id=oid,
        code=f"ORD-CTIME-{oid}",
        client_name="COMMERCIAL TIME ISOLATION FIXTURE",
        status="locked",
        total_amount=commercial_total,
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


def _accepted_and_hash(order: Orders) -> tuple[float, str, str]:
    snap = OrderSnapshotV2.model_validate_json(order.snapshot_v2_json)
    return (
        float(order.total_amount),
        str(snap.accepted_commercial_total),
        str(snap.content_hash),
    )


@pytest.mark.asyncio
async def test_cpp_commercial_total_ignores_quote_input_minutes(volumetric_v2_db):
    """Active 7G engine: injecting minutes into quote_input must not change total."""
    svc = CommercialPriceProposalService(volumetric_v2_db)
    base_input = _full_quote_input()
    polluted = {
        **base_input,
        "estimated_minutes": 999,
        "duration_minutes": 888,
        "hours": 12,
        "rate_per_hour": 100,
        "labor_minutes": 777,
        "operations": [{"code": "qc_letters", "estimated_minutes": 150}],
    }
    a = await svc.build_preview(TEMPLATE, quote_input=base_input)
    b = await svc.build_preview(TEMPLATE, quote_input=polluted)
    assert a is not None and b is not None
    assert a.commercial_total == b.commercial_total
    assert a.subtotal_commercial == b.subtotal_commercial
    assert a.commercial_total is not None and a.commercial_total > 0


@pytest.mark.asyncio
async def test_planned_minutes_15_vs_150_same_commercial_different_plan(db_session):
    order_a = await _seed_order(db_session, qc_minutes=15.0, commercial_total=1500.0)
    order_b = await _seed_order(db_session, qc_minutes=150.0, commercial_total=1500.0)

    before_a = _accepted_and_hash(order_a)
    before_b = _accepted_and_hash(order_b)
    assert before_a[0] == before_b[0] == 1500.0

    persist_a = await create_execution_plan_v2_from_order(db_session, order_a.id)
    persist_b = await create_execution_plan_v2_from_order(db_session, order_b.id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order_a.id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order_b.id)

    plan_a = await db_session.get(ExecutionPlan, persist_a.execution_plan_id)
    plan_b = await db_session.get(ExecutionPlan, persist_b.execution_plan_id)
    env_a = json.loads(plan_a.tasks_json)
    env_b = json.loads(plan_b.tasks_json)
    qc_a = next(t for t in env_a["planned_tasks"] if t.get("source_operation_code") == "qc_letters")
    qc_b = next(t for t in env_b["planned_tasks"] if t.get("source_operation_code") == "qc_letters")
    assert qc_a["estimated_minutes"] == 15.0
    assert qc_b["estimated_minutes"] == 150.0

    await db_session.refresh(order_a)
    await db_session.refresh(order_b)
    after_a = _accepted_and_hash(order_a)
    after_b = _accepted_and_hash(order_b)
    assert after_a == before_a
    assert after_b == before_b
    assert after_a[0] == after_b[0] == 1500.0

    truth_a = (await PostJobTruthService(db_session).build_for_order(order_a.id)).model_dump(
        mode="json"
    )
    truth_b = (await PostJobTruthService(db_session).build_for_order(order_b.id)).model_dump(
        mode="json"
    )
    assert truth_a["write_back_performed"] is False
    assert truth_b["write_back_performed"] is False
    assert truth_a["baseline"]["revenue_net"]["value"] == 1500.0
    assert truth_b["baseline"]["revenue_net"]["value"] == 1500.0
    assert truth_a["baseline"]["revenue_net"]["value"] == truth_b["baseline"]["revenue_net"]["value"]
    pa = next(
        o
        for o in truth_a["reconciliation"]["operations"]
        if o.get("planned_minutes", {}).get("value") == 15.0
    )
    pb = next(
        o
        for o in truth_b["reconciliation"]["operations"]
        if o.get("planned_minutes", {}).get("value") == 150.0
    )
    assert pa["planned_minutes"]["value"] != pb["planned_minutes"]["value"]


@pytest.mark.asyncio
async def test_actual_minutes_states_do_not_mutate_frozen_commercial(db_session):
    order = await _seed_order(db_session, qc_minutes=15.0, commercial_total=1500.0)
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    plan = await db_session.get(ExecutionPlan, persist.execution_plan_id)
    envelope = json.loads(plan.tasks_json)
    qc_task = next(
        t for t in envelope["operational_tasks"] if t.get("source_operation_code") == "qc_letters"
    )
    task_id = qc_task["task_id"]
    frozen_before = _accepted_and_hash(order)
    snap_json_before = order.snapshot_v2_json

    # State 1 — no actual
    t1 = (await PostJobTruthService(db_session).build_for_order(order.id)).model_dump(mode="json")
    assert t1["write_back_performed"] is False
    qc1 = next(o for o in t1["reconciliation"]["operations"] if o["task_id"] == task_id)
    assert qc1["actual_minutes"]["presence"] == "not_captured"

    # State 2 — small actual
    reality = ExecutionReality(
        order_id=order.id,
        order_code=order.code,
        tasks_json=json.dumps(
            [
                {
                    "session_id": "ctime-s2",
                    "task_id": task_id,
                    "employee_id": 11,
                    "role": "primary",
                    "started_at": "2026-07-17T08:00:00+00:00",
                    "ended_at": "2026-07-17T08:10:00+00:00",
                    "duration_minutes": 10.0,
                }
            ]
        ),
        materials_json="[]",
        total_actual_time_minutes=10.0,
    )
    db_session.add(reality)
    await db_session.flush()
    t2 = (await PostJobTruthService(db_session).build_for_order(order.id)).model_dump(mode="json")
    qc2 = next(o for o in t2["reconciliation"]["operations"] if o["task_id"] == task_id)
    assert qc2["actual_minutes"]["value"] == 10.0
    assert t2["write_back_performed"] is False

    # State 3 — large actual (mutate reality only)
    reality.tasks_json = json.dumps(
        [
            {
                "session_id": "ctime-s3",
                "task_id": task_id,
                "employee_id": 11,
                "role": "primary",
                "started_at": "2026-07-17T08:00:00+00:00",
                "ended_at": "2026-07-17T11:00:00+00:00",
                "duration_minutes": 180.0,
            }
        ]
    )
    reality.total_actual_time_minutes = 180.0
    await db_session.flush()
    t3 = (await PostJobTruthService(db_session).build_for_order(order.id)).model_dump(mode="json")
    qc3 = next(o for o in t3["reconciliation"]["operations"] if o["task_id"] == task_id)
    assert qc3["actual_minutes"]["value"] == 180.0
    assert qc3["variance_minutes"]["value"] == 165.0
    assert t3["write_back_performed"] is False

    await db_session.refresh(order)
    assert order.snapshot_v2_json == snap_json_before
    assert _accepted_and_hash(order) == frozen_before
    assert float(order.total_amount) == 1500.0
    assert t1["baseline"]["revenue_net"]["value"] == t2["baseline"]["revenue_net"]["value"] == 1500.0
    assert t3["baseline"]["revenue_net"]["value"] == 1500.0


def test_post_job_service_module_has_no_pricing_imports():
    _assert_no_pricing_imports("services/post_job_truth_service.py")


def test_plan_persist_module_has_no_pricing_imports():
    _assert_no_pricing_imports("services/execution_plan_v2_persist_service.py")


def test_plan_materialize_module_has_no_pricing_imports():
    _assert_no_pricing_imports("services/execution_plan_v2_materialize_service.py")


def test_reality_service_module_has_no_pricing_imports():
    _assert_no_pricing_imports("services/execution_reality_service.py")
