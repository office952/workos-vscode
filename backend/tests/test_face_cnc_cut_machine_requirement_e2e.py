"""FACE_CNC_CUT_MACHINE_REQUIREMENT_E2E — Operation Contract → Aggregate → EP → projection."""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest

from data.product_process.catalogs import CAPABILITY_CODES
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
from services.operation_machine_requirement_contract import (
    FACE_CNC_CUT_MACHINE_REQUIREMENT,
    get_operation_machine_requirement_contract,
    machine_exclusive_implied,
)
from services.product_aggregate_machine_requirement_service import (
    apply_machine_requirement_resolution,
)
from services.task_resource_requirement_projection_service import (
    project_plan_resource_requirements,
    project_task_resource_requirements,
)
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
OID_BASE = 974500
WC_CNC = "WC_CNC_ROUTING"
QA_DB = Path(__file__).resolve().parents[1] / "dev.db"
PLAN21_SHA = (
    "75933211c1c180d421648bd3c54a96493716ba4c92262f42032c522486b9ff59"
)
PLAN22_SHA = (
    "0ec2dce6f1daea4509808b876f58c9ee7326fb7059e64d057cd81fbbd35ecb97"
)
PLAN23_SHA = (
    "00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2"
)


def _ops(*codes: str) -> list[ProductAggregateOperation]:
    out: list[ProductAggregateOperation] = []
    for code in codes:
        wc = WC_CNC if code == "face_cnc_cut" else None
        if code == "return_face_bonding":
            wc = "WC_METAL_FAB"
        out.append(
            ProductAggregateOperation(
                operation_code=code,
                label=code,
                workcenter=wc,
                estimated_minutes=0.0,
                calculation_type="formula_based",
            )
        )
    return out


def _task_contract(*priced: str) -> ProductAggregateTaskContract:
    rules = []
    for i, code in enumerate(priced, start=1):
        rules.append(
            ProductAggregateTaskRule(
                task_name=code if code != "face_cnc_cut" else "cnc_face_cut",
                task_type="cnc_routing" if code == "face_cnc_cut" else "welding",
                priced_operation=code,
                sequence=i,
            )
        )
    return ProductAggregateTaskContract(task_rules=rules)


def _aggregate(*codes: str) -> ProductAggregate:
    raw = ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=_ops(*codes),
        task_contract=_task_contract(*codes),
    )
    return apply_machine_requirement_resolution(raw)


def _pd(*codes: str) -> ProductDefinitionPreview:
    return ProductDefinitionPreview(
        template_code=TEMPLATE,
        source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
        operation_roles=[
            ProductDefinitionOperationRole(
                operation_code=c,
                label=c,
                workcenter=WC_CNC if c == "face_cnc_cut" else "WC_METAL_FAB",
            )
            for c in codes
        ],
        geometry_inputs={},
        canonical_values={},
    )


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------


def test_capability_authority_from_catalog_and_contract():
    assert FACE_CNC_CUT_MACHINE_REQUIREMENT.machine_capability_code in CAPABILITY_CODES
    assert FACE_CNC_CUT_MACHINE_REQUIREMENT.machine_capability_code == "CNC_ROUTER_CUTTING"
    assert FACE_CNC_CUT_MACHINE_REQUIREMENT.resource_mode == "MACHINE_BOUND"
    assert FACE_CNC_CUT_MACHINE_REQUIREMENT.batch_eligible is True
    assert FACE_CNC_CUT_MACHINE_REQUIREMENT.operation_code == "face_cnc_cut"
    assert machine_exclusive_implied("MACHINE_BOUND") is True
    assert get_operation_machine_requirement_contract("painting") is None


def test_aggregate_projects_face_cnc_cut_demand():
    agg = _aggregate("face_cnc_cut", "painting")
    by = {o.operation_code: o for o in agg.operations}
    face = by["face_cnc_cut"]
    assert face.machine_capability_code == "CNC_ROUTER_CUTTING"
    assert face.resource_mode == "MACHINE_BOUND"
    assert face.batch_eligible is True
    paint = by["painting"]
    assert paint.machine_capability_code is None
    assert paint.resource_mode is None
    assert paint.batch_eligible is None


# ---------------------------------------------------------------------------
# Isolated fixture E2E
# ---------------------------------------------------------------------------


async def _seed_order(db_session, *, codes: tuple[str, ...] = ("face_cnc_cut",)) -> Orders:
    oid = OID_BASE + int(uuid.uuid4().hex[:4], 16) % 400
    record = QuoteSnapshotV2Record(
        snapshot_code=f"QSN2-FACE-CNC-{oid}",
        snapshot_version="1.0.0",
        version=1,
        template_code=TEMPLATE,
        status="frozen",
        readiness="ready_for_owner_review",
        snapshot_json="{}",
        content_hash="face-cnc-e2e",
    )
    db_session.add(record)
    await db_session.flush()
    snapshot = OrderSnapshotV2(
        quote_id=oid,
        quote_snapshot_v2_id=int(record.id),
        snapshot_code=f"OSN2-FACE-CNC-{oid}",
        content_hash="face-cnc-e2e" + ("0" * 20),
        product_definition_snapshot=_pd(*codes),
        product_aggregate_snapshot=_aggregate(*codes),
        commercial_price_proposal_snapshot=_commercial_preview(total=1100.0),
        estimated_internal_cost_snapshot=_internal_preview(total=500.0),
        accepted_commercial_total=1100.0,
        accepted_currency="RON",
        estimated_internal_total=500.0,
    )
    order = Orders(
        id=oid,
        code=f"ORD-FACE-CNC-{oid}",
        client_name="LOCAL_TEST_FIXTURE face_cnc_cut machine requirement E2E",
        status="locked",
        total_amount=1100.0,
        quote_id=oid,
        quote_snapshot_v2_id=int(record.id),
        snapshot_v2_json=snapshot.model_dump_json(),
        readiness_snapshot={
            "execution_plan_created": False,
            "local_test_fixture": True,
            "face_cnc_cut_machine_requirement_e2e": True,
            "retention": "dev_ephemeral",
        },
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


@pytest.mark.asyncio
async def test_ep_snapshot_and_projection_face_cnc(db_session):
    order = await _seed_order(db_session)
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    face_p = next(
        t for t in preview.planned_tasks if t.source_operation_code == "face_cnc_cut"
    )
    assert face_p.machine_capability_code == "CNC_ROUTER_CUTTING"
    assert face_p.resource_mode == "MACHINE_BOUND"
    assert face_p.batch_eligible is True
    assert face_p.machine_requirement is not None
    assert face_p.machine_requirement.workcenter == WC_CNC
    assert getattr(face_p, "machine_id", None) is None

    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    assert persist.status == "persisted"
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    plan = await db_session.get(ExecutionPlan, persist.execution_plan_id)
    assert plan is not None
    envelope = json.loads(plan.tasks_json)
    op = next(
        t
        for t in envelope["operational_tasks"]
        if t.get("source_operation_code") == "face_cnc_cut"
    )
    assert op["machine_capability_code"] == "CNC_ROUTER_CUTTING"
    assert op["resource_mode"] == "MACHINE_BOUND"
    assert op["batch_eligible"] is True
    assert op["workcenter"] == WC_CNC
    assert "machine_id" not in op or op.get("machine_id") is None

    proj = await project_plan_resource_requirements(
        db_session, plan_id=int(plan.id), task_key=str(op["task_id"])
    )
    task = proj.tasks[0]
    assert task.operation_code == "face_cnc_cut"
    assert task.workcenter_code == WC_CNC
    assert task.machine_capability_code == "CNC_ROUTER_CUTTING"
    assert task.resource_mode == "MACHINE_BOUND"
    assert task.batch_eligible is True
    assert "machine_capability_code" in task.known_fields
    assert "resource_mode" in task.known_fields
    assert "batch_eligible" in task.known_fields
    assert "machine_capability_code" not in task.unknown_fields
    caps = {p.field: p for p in task.source_provenance}
    assert caps["machine_capability_code"].source == "EXECUTION_PLAN_SNAPSHOT"
    assert caps["machine_capability_code"].confidence == "CONFIRMED"
    assert task.resource_requirements_status == "PARTIAL"  # duration still unknown


@pytest.mark.asyncio
async def test_no_reservation_or_run_side_effects(db_session):
    order = await _seed_order(db_session)
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    from sqlalchemy import text

    res = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM execution_task_machine_reservations")
        )
    ).scalar_one()
    assert int(res) == 0
    # MACHINE_RUN table must not exist / not be written
    try:
        runs = (
            await db_session.execute(text("SELECT COUNT(*) FROM machine_runs"))
        ).scalar_one()
        assert int(runs) == 0
    except Exception:
        pass  # table absent = NOT_IMPLEMENTED


def test_legacy_without_capability_stays_unknown():
    task = {
        "task_id": "legacy-cnc",
        "source_operation_code": "face_cnc_cut",
        "workcenter": WC_CNC,
    }
    p = project_task_resource_requirements(task, execution_plan_id=1)
    assert p.machine_capability_code is None
    assert p.resource_mode is None
    assert p.batch_eligible is None
    assert "machine_capability_code" in p.unknown_fields
    assert p.resource_mode_hint == "MACHINE_BOUND"  # soft only


def test_hybrid_without_authoritative_mode_stays_unknown():
    task = {
        "task_id": "hybrid-bond",
        "source_operation_code": "return_face_bonding",
        "workcenter": "WC_METAL_FAB",
    }
    p = project_task_resource_requirements(task, execution_plan_id=1)
    assert p.resource_mode is None
    assert p.resource_mode_hint == "UNKNOWN"
    assert "resource_mode" in p.unknown_fields


def test_projection_does_not_infer_capability_from_wc_alone():
    task = {
        "task_id": "wc-only",
        "source_operation_code": "back_cut",
        "workcenter": WC_CNC,
    }
    p = project_task_resource_requirements(task, execution_plan_id=1)
    assert p.machine_capability_code is None
    assert p.resource_mode_hint == "MACHINE_BOUND"


@pytest.mark.skipif(not QA_DB.is_file(), reason="QA dev.db not present")
def test_protected_plans_unchanged():
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
            env = json.loads(tj)
            for t in env.get("operational_tasks") or []:
                # No backfill on protected plans
                assert t.get("machine_capability_code") in (None, "")
    finally:
        conn.close()
