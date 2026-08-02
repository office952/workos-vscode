"""F7A.1 — workcenter registry fidelity + premount hard BOM-only policy."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from data.operational_workcenters import (
    CANONICAL_CNC_WORKCENTER,
    CANONICAL_WORKCENTER_CODES,
    NON_CANONICAL_WORKCENTER_CODES,
    is_canonical_workcenter_code,
    workcenter_registry_status,
)
from data.product_process.catalogs import (
    is_bom_only_operation_code,
    is_bom_only_without_activation,
    premount_activation_signal_present,
)
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.execution_plan_v2 import DAG_PROCESS_DEPENDENCIES_UNRESOLVED, PLANNING_MINUTES_WARNING
from schemas.product_aggregate import (
    ProductAggregateOperation,
    ProductAggregateTaskRule,
)
from services.dec009_materialize_gate import LIVE_DEC009_STATUS
from services.execution_plan_v2_frozen_task_identity_service import (
    _synthetic_rule_from_operation,
    collect_effective_task_rules,
)
from services.execution_plan_v2_materialization_audit_service import (
    build_execution_plan_v2_materialization_audit_by_order_id,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_plan_v2_preview_service import (
    _is_non_operational_rule,
    build_execution_plan_v2_preview,
)
from services.product_aggregate_service import ProductAggregateService
from schemas.product_aggregate import ProductAggregateCompositionNode
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot
from tests.test_f7a_product_linked_task_contract_enrichment import (
    COMMERCIAL_TOTAL,
    _f7a_oid,
    _f7a_snapshot_json,
)


def test_canonical_cnc_is_routing_not_wc_cnc():
    assert CANONICAL_CNC_WORKCENTER == "WC_CNC_ROUTING"
    assert "WC_CNC_ROUTING" in CANONICAL_WORKCENTER_CODES
    assert "WC_CNC" in NON_CANONICAL_WORKCENTER_CODES
    assert is_canonical_workcenter_code("WC_CNC") is False
    assert is_canonical_workcenter_code("WC_CNC_ROUTING") is True
    assert workcenter_registry_status("WC_CNC") == "non_canonical"
    assert workcenter_registry_status("WC_CNC_ROUTING") == "resolved"


def test_fixture_workcenters_are_registry_canonical():
    from tests.test_f7a_product_linked_task_contract_enrichment import _f7a_operations

    for op in _f7a_operations():
        if op.operation_code in {
            "svg_geometry_analysis",
            "premount_bar_preparation",
            "RETURN_PROFILE_MACHINE_FORMING",
            "RETURN_PROFILE_FACE_BONDING",
            "PAINTING",
        }:
            continue
        if not op.workcenter:
            continue
        assert is_canonical_workcenter_code(op.workcenter), (
            f"{op.operation_code} stamped non-canonical WC {op.workcenter}"
        )
        assert op.workcenter != "WC_CNC"


def test_dec002_no_activation_signal_in_repo():
    assert premount_activation_signal_present() is False
    assert is_bom_only_operation_code("premount_bar_preparation") is True
    assert is_bom_only_without_activation(
        priced_operation="premount_bar_preparation"
    ) is True


def test_premount_rule_is_non_operational_for_preview():
    rule = ProductAggregateTaskRule(
        task_name="premount_bar_preparation",
        task_type="metal_fabrication",
        priced_operation="premount_bar_preparation",
    )
    assert _is_non_operational_rule(rule) is True


def test_build_task_contract_drops_premount_without_activation():
    svc = ProductAggregateService.__new__(ProductAggregateService)
    raw = [
        {
            "task_name": "side_forming",
            "priced_operation": "side_forming",
            "sequence": 1,
            "task_type": "edge_bending",
        },
        {
            "task_name": "premount_bar_preparation",
            "priced_operation": "premount_bar_preparation",
            "sequence": 2,
            "task_type": "metal_fabrication",
        },
    ]
    contract = svc._build_task_contract(raw)
    priced = [str(r.priced_operation).lower() for r in contract.task_rules]
    assert "premount_bar_preparation" not in priced
    assert "side_forming" in priced
    assert any("bom_only_exclusion" in n for n in contract.notes)


def test_composition_graph_cannot_synthesize_premount():
    node = ProductAggregateCompositionNode(
        node_id="node:root_product:TPL-X",
        template_code="TPL-X",
        node_role="root_product",
        module_code="root",
        module_role="root_product",
        activation_source="frozen_snapshot",
    )
    op = ProductAggregateOperation(
        operation_code="premount_bar_preparation",
        label="Premount bar",
        workcenter="WC_METAL_FAB",
    )
    assert _synthetic_rule_from_operation(op, node=node, sequence=10) is None


@pytest.mark.asyncio
@pytest.mark.enforce_dec009_gate
async def test_f7a1_fixture_preview_wc_premount_dag_audit(db_session):
    oid = _f7a_oid()
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=oid,
        snapshot_v2_json=_f7a_snapshot_json(order_id=oid, quote_snapshot_v2_id=oid),
    )
    frozen = json.loads(order.snapshot_v2_json)
    assert frozen["accepted_commercial_total"] == COMMERCIAL_TOTAL

    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.planned_tasks
    ops = {
        str(t.source_operation_code).lower(): t
        for t in preview.planned_tasks
        if t.source_operation_code
    }
    assert "premount_bar_preparation" not in ops
    assert "svg_geometry_analysis" not in ops
    assert "return_profile_machine_forming" not in ops
    assert "face_cnc_cut" in ops
    assert ops["face_cnc_cut"].machine_requirement is not None
    assert ops["face_cnc_cut"].machine_requirement.workcenter == "WC_CNC_ROUTING"
    assert "WORKCENTER_CODE_NON_CANONICAL" not in (ops["face_cnc_cut"].warnings or [])

    for t in preview.planned_tasks:
        wc = t.machine_requirement.workcenter if t.machine_requirement else None
        if wc:
            assert is_canonical_workcenter_code(wc)
            assert wc != "WC_CNC"

    assert all(t.estimated_minutes is None for t in preview.planned_tasks)
    assert any(PLANNING_MINUTES_WARNING in (t.warnings or []) for t in preview.planned_tasks)
    assert not any(
        DAG_PROCESS_DEPENDENCIES_UNRESOLVED in (t.warnings or []) for t in preview.planned_tasks
    )

    bond = ops["return_face_bonding"]
    face = ops["face_cnc_cut"]
    side = ops["side_forming"]
    assert face.task_key in bond.depends_on_task_keys
    assert side.task_key in bond.depends_on_task_keys

    first = await create_execution_plan_v2_from_order(db_session, order.id)
    second = await create_execution_plan_v2_from_order(db_session, order.id)
    assert first.execution_plan_id == second.execution_plan_id
    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order.id))
    ).scalar_one()
    envelope = json.loads(plan.tasks_json) if isinstance(plan.tasks_json, str) else plan.tasks_json
    assert envelope.get("execution_tasks_created") in (False, None)
    assert not envelope.get("operational_tasks")

    plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    reality_before = await db_session.scalar(select(func.count()).select_from(ExecutionReality))
    audit = await build_execution_plan_v2_materialization_audit_by_order_id(db_session, order.id)
    assert audit.mode == "audit_only"
    assert audit.materialization_status == "blocked_needs_owner_go"
    assert audit.guards.writes_database is False
    cand = {
        str(c.source_operation_code or "").lower() for c in audit.materializable_task_candidates
    }
    assert "premount_bar_preparation" not in cand
    plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    reality_after = await db_session.scalar(select(func.count()).select_from(ExecutionReality))
    assert plans_after == plans_before
    assert reality_after == reality_before
    assert LIVE_DEC009_STATUS == "A"

    await db_session.refresh(order)
    assert json.loads(order.snapshot_v2_json)["accepted_commercial_total"] == COMMERCIAL_TOTAL
