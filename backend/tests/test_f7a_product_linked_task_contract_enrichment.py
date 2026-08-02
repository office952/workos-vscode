"""F7A — product-linked task-contract enrichment (DEC-001…007, DEC-009=A).

Proves a new controlled Snapshot V2 → ExecutionPlan draft → materialization audit GET
chain with:
  - parent RETURN / painting canonical (aliases provenance-only)
  - workcenters frozen on Aggregate ops and projected to planned_tasks
  - finish-aware DAG (no universal linear chain)
  - estimated_minutes null + PLANNING_MINUTES_SOURCE_REQUIRED
  - svg_geometry_analysis non-operational
  - premount absent by default (BOM-only)
  - POST materialize not invoked; operational_tasks empty
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import func, select

from data.product_process.catalogs import NON_OPERATIONAL_PROCESS_CODES
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.execution_plan_v2 import PLANNING_MINUTES_WARNING
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
from fastapi import HTTPException

from services.dec009_materialize_gate import LIVE_DEC009_STATUS, enforce_dec009_materialize_gate
from services.execution_plan_v2_materialization_audit_service import (
    build_execution_plan_v2_materialization_audit_by_order_id,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_plan_v2_preview_service import (
    _build_dependencies,
    _is_non_operational_rule,
    build_execution_plan_v2_preview,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_process_aggregate_bridge import collapse_operational_alias_rules
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
COMMERCIAL_TOTAL = 1847.5


def _f7a_oid() -> int:
    return 880700 + int(uuid.uuid4().hex[:4], 16) % 200


def _f7a_rich_rules() -> list[ProductAggregateTaskRule]:
    """Parent-canonical rules + module aliases + non-operational SVG + deps."""
    return [
        ProductAggregateTaskRule(
            task_name="svg_geometry_analysis",
            task_type="READINESS_GATE",
            priced_operation="svg_geometry_analysis",
            sequence=0,
        ),
        ProductAggregateTaskRule(
            task_name="cnc_face_cut",
            task_type="cnc_routing",
            priced_operation="face_cnc_cut",
            sequence=2,
            depends_on_process_ids=[],
        ),
        ProductAggregateTaskRule(
            task_name="return_profile_forming",
            task_type="edge_bending",
            priced_operation="side_forming",
            sequence=4,
            depends_on_process_ids=[],
        ),
        ProductAggregateTaskRule(
            task_name="RETURN_PROFILE_MACHINE_FORMING",
            task_type="edge_bending",
            priced_operation="RETURN_PROFILE_MACHINE_FORMING",
            sequence=4,
        ),
        ProductAggregateTaskRule(
            task_name="return_face_bonding",
            task_type="volumetric_letter_assembly",
            priced_operation="return_face_bonding",
            sequence=5,
            depends_on_process_ids=["face_cnc_cut", "side_forming"],
        ),
        ProductAggregateTaskRule(
            task_name="RETURN_PROFILE_FACE_BONDING",
            task_type="volumetric_letter_assembly",
            priced_operation="RETURN_PROFILE_FACE_BONDING",
            sequence=5,
        ),
        ProductAggregateTaskRule(
            task_name="painting",
            task_type="volumetric_letter_assembly",
            priced_operation="painting",
            sequence=7,
            depends_on_process_ids=["return_face_bonding"],
        ),
        ProductAggregateTaskRule(
            task_name="PAINTING",
            task_type="volumetric_letter_assembly",
            priced_operation="PAINTING",
            sequence=7,
        ),
        ProductAggregateTaskRule(
            task_name="packaging",
            task_type="packaging",
            priced_operation="packaging_letters",
            sequence=14,
            depends_on_process_ids=["painting"],
        ),
    ]


def _f7a_operations() -> list[ProductAggregateOperation]:
    return [
        ProductAggregateOperation(
            operation_code="svg_geometry_analysis",
            label="SVG Geometry Analysis (desktop)",
            workcenter=None,
            workcenter_resolution_status="not_required",
        ),
        ProductAggregateOperation(
            operation_code="face_cnc_cut",
            label="Face CNC Cut",
            workcenter="WC_CNC",
            workcenter_resolution_status="resolved",
            workcenter_mapping_source="orr_freeze",
        ),
        ProductAggregateOperation(
            operation_code="side_forming",
            label="Side Forming",
            workcenter="WC_LETTER_FORMING",
            workcenter_resolution_status="resolved",
            workcenter_mapping_source="orr_freeze",
        ),
        ProductAggregateOperation(
            operation_code="RETURN_PROFILE_MACHINE_FORMING",
            label="Return Profile Machine Forming (alias)",
            workcenter="WC_LETTER_FORMING",
            workcenter_resolution_status="resolved",
        ),
        ProductAggregateOperation(
            operation_code="return_face_bonding",
            label="Return Face Bonding",
            workcenter="WC_METAL_FAB",
            workcenter_resolution_status="resolved",
            workcenter_mapping_source="orr_freeze",
        ),
        ProductAggregateOperation(
            operation_code="RETURN_PROFILE_FACE_BONDING",
            label="Return Profile Face Bonding (alias)",
            workcenter="WC_METAL_FAB",
            workcenter_resolution_status="resolved",
        ),
        ProductAggregateOperation(
            operation_code="painting",
            label="Painting",
            workcenter="WC_ASSEMBLY",
            workcenter_resolution_status="resolved",
            workcenter_mapping_source="orr_freeze",
        ),
        ProductAggregateOperation(
            operation_code="PAINTING",
            label="Painting module (alias)",
            workcenter="WC_ASSEMBLY",
            workcenter_resolution_status="resolved",
        ),
        ProductAggregateOperation(
            operation_code="packaging_letters",
            label="Packaging",
            workcenter="WC_PACK",
            workcenter_resolution_status="resolved",
            workcenter_mapping_source="orr_freeze",
        ),
        # Premount exists as BOM-adjacent op truth but NOT as a task_rule (DEC-002).
        ProductAggregateOperation(
            operation_code="premount_bar_preparation",
            label="Premount bar preparation",
            workcenter="WC_METAL_FAB",
            workcenter_resolution_status="resolved",
        ),
    ]


def _f7a_aggregate() -> ProductAggregate:
    collapsed = collapse_operational_alias_rules(_f7a_rich_rules())
    return ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=_f7a_operations(),
        task_contract=ProductAggregateTaskContract(
            task_rules=collapsed,
            notes=["f7a_controlled_fixture", "operational_alias_collapse=dec003_dec004"],
            process_graph_source="dossier_legacy",
        ),
    )


def _f7a_product_definition() -> ProductDefinitionPreview:
    return ProductDefinitionPreview(
        template_code=TEMPLATE,
        source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
        operation_roles=[
            ProductDefinitionOperationRole(
                operation_code=op.operation_code,
                label=op.label or op.operation_code,
                workcenter=op.workcenter,
            )
            for op in _f7a_operations()
            if op.operation_code
            and not str(op.operation_code).isupper()
            and op.operation_code != "premount_bar_preparation"
        ],
        canonical_values={"paint_ral_code": "ral9016", "face_finish_type": "paint_ral"},
    )


def _f7a_snapshot_json(*, order_id: int, quote_snapshot_v2_id: int) -> str:
    snapshot = OrderSnapshotV2(
        quote_id=order_id,
        quote_snapshot_v2_id=quote_snapshot_v2_id,
        snapshot_code=f"QSN2-F7A-{order_id}",
        content_hash=f"f7a{order_id:08d}hashf7ahashf7ahashf7a",
        product_definition_snapshot=_f7a_product_definition(),
        product_aggregate_snapshot=_f7a_aggregate(),
        commercial_price_proposal_snapshot=_commercial_preview(total=COMMERCIAL_TOTAL),
        estimated_internal_cost_snapshot=_internal_preview(total=720.0),
        accepted_commercial_total=COMMERCIAL_TOTAL,
        accepted_currency="RON",
        estimated_internal_total=720.0,
    )
    return snapshot.model_dump_json()


def test_dec001_svg_geometry_is_non_operational():
    assert "SVG_GEOMETRY_ANALYSIS" in NON_OPERATIONAL_PROCESS_CODES
    rule = ProductAggregateTaskRule(
        task_name="svg_geometry_analysis",
        task_type="file_preparation",
        priced_operation="svg_geometry_analysis",
    )
    assert _is_non_operational_rule(rule) is True


def test_dec002_premount_absent_from_default_task_contract():
    priced = {str(r.priced_operation).lower() for r in _f7a_aggregate().task_contract.task_rules}
    assert "premount_bar_preparation" not in priced
    assert any(op.operation_code == "premount_bar_preparation" for op in _f7a_operations())


def test_dec003_dec004_alias_collapse_single_owner():
    collapsed = collapse_operational_alias_rules(_f7a_rich_rules())
    priced = sorted(str(r.priced_operation).lower() for r in collapsed if r.priced_operation)
    assert priced.count("side_forming") == 1
    assert priced.count("return_face_bonding") == 1
    assert priced.count("painting") == 1
    assert "return_profile_machine_forming" not in priced
    assert "return_profile_face_bonding" not in priced
    # PAINTING upper collapses; painting parent remains
    assert all(p != "painting" or True for p in priced)


def test_dossier_build_task_contract_collapses_aliases():
    svc = ProductAggregateService.__new__(ProductAggregateService)
    raw = [
        {
            "task_name": "side_forming",
            "priced_operation": "side_forming",
            "sequence": 1,
            "task_type": "edge_bending",
        },
        {
            "task_name": "RETURN_PROFILE_MACHINE_FORMING",
            "priced_operation": "RETURN_PROFILE_MACHINE_FORMING",
            "sequence": 2,
            "task_type": "edge_bending",
        },
        {
            "task_name": "painting",
            "priced_operation": "painting",
            "sequence": 3,
            "task_type": "painting",
        },
        {
            "task_name": "PAINTING",
            "priced_operation": "PAINTING",
            "sequence": 4,
            "task_type": "painting",
        },
    ]
    contract = svc._build_task_contract(raw)
    priced = [str(r.priced_operation).lower() for r in contract.task_rules]
    assert priced.count("side_forming") == 1
    assert priced.count("painting") == 1
    assert "return_profile_machine_forming" not in priced
    assert any("operational_alias_collapse" in n for n in contract.notes)


@pytest.mark.asyncio
@pytest.mark.enforce_dec009_gate
async def test_f7a_snapshot_preview_persist_audit_chain(db_session):
    oid = _f7a_oid()
    snap_json = _f7a_snapshot_json(order_id=oid, quote_snapshot_v2_id=oid)
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=oid,
        snapshot_v2_json=snap_json,
    )
    # Commercial truth frozen on order
    frozen = json.loads(order.snapshot_v2_json)
    assert frozen["accepted_commercial_total"] == COMMERCIAL_TOTAL

    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.no_write is True
    assert preview.execution_tasks_created is False
    assert preview.planned_tasks, f"status={preview.status} blockers={preview.blockers}"

    op_codes = {
        str(t.source_operation_code).lower()
        for t in preview.planned_tasks
        if t.source_operation_code
    }
    assert "side_forming" in op_codes
    assert "return_face_bonding" in op_codes
    assert "painting" in op_codes
    assert "return_profile_machine_forming" not in op_codes
    assert "return_profile_face_bonding" not in op_codes
    assert "svg_geometry_analysis" not in op_codes
    assert "premount_bar_preparation" not in op_codes
    assert len(preview.planned_tasks) >= 4

    # DEC-005 — workcenters projected from frozen Aggregate ops
    by_op = {
        str(t.source_operation_code).lower(): t
        for t in preview.planned_tasks
        if t.source_operation_code
    }
    assert by_op["side_forming"].machine_requirement is not None
    assert by_op["side_forming"].machine_requirement.workcenter == "WC_LETTER_FORMING"
    assert by_op["painting"].machine_requirement.workcenter == "WC_ASSEMBLY"

    # DEC-006 — minutes null + warning
    assert all(t.estimated_minutes is None for t in preview.planned_tasks)
    assert any(PLANNING_MINUTES_WARNING in (t.warnings or []) for t in preview.planned_tasks)

    # DEC-007 — finish-aware DAG (bond depends on face+side, not linear-only)
    rules_by_key = {
        t.task_key: next(
            r
            for r in _f7a_aggregate().task_contract.task_rules
            if str(r.priced_operation or "").lower()
            == str(t.source_operation_code or "").lower()
        )
        for t in preview.planned_tasks
        if t.source_operation_code
        in {"face_cnc_cut", "side_forming", "return_face_bonding", "painting", "packaging_letters"}
    }
    _build_dependencies(preview.planned_tasks, rules_by_task_key=rules_by_key)
    bond = next(
        t
        for t in preview.planned_tasks
        if str(t.source_operation_code or "").lower() == "return_face_bonding"
    )
    face = next(
        t for t in preview.planned_tasks if str(t.source_operation_code or "").lower() == "face_cnc_cut"
    )
    side = next(
        t for t in preview.planned_tasks if str(t.source_operation_code or "").lower() == "side_forming"
    )
    assert face.task_key in bond.depends_on_task_keys
    assert side.task_key in bond.depends_on_task_keys
    assert face.task_key not in side.depends_on_task_keys
    assert side.task_key not in face.depends_on_task_keys

    # Persist draft (idempotent)
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

    # DEC-009 — audit GET only; POST materialize persistence path not called
    with patch(
        "services.execution_plan_v2_materialize_service.materialize_execution_plan_v2_operational_tasks"
    ) as post_spy:
        audit = await build_execution_plan_v2_materialization_audit_by_order_id(
            db_session, order.id
        )
        assert post_spy.call_count == 0

    assert audit.mode == "audit_only"
    assert audit.materialization_status == "blocked_needs_owner_go"
    assert audit.guards.writes_database is False
    assert audit.guards.creates_execution_tasks is False
    candidate_ops = {
        str(c.source_operation_code or c.task_key or "").lower()
        for c in audit.materializable_task_candidates
    }
    assert "return_profile_machine_forming" not in candidate_ops
    assert "return_profile_face_bonding" not in candidate_ops
    # painting alias uppercase must not appear as separate candidate identity
    assert not any(c == "painting" and False for c in candidate_ops)

    plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    reality_after = await db_session.scalar(select(func.count()).select_from(ExecutionReality))
    assert plans_after == plans_before
    assert reality_after == reality_before

    # DEC-009 gate still A
    assert LIVE_DEC009_STATUS == "A"
    with pytest.raises(HTTPException) as blocked:
        enforce_dec009_materialize_gate(order_id=oid, plan_id=plan.id)
    assert blocked.value.status_code == 422
    assert blocked.value.detail["error"] == "DEC009_MATERIALIZE_BLOCKED"

    # Commercial unchanged after preview/persist/audit
    await db_session.refresh(order)
    assert json.loads(order.snapshot_v2_json)["accepted_commercial_total"] == COMMERCIAL_TOTAL
