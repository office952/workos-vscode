"""Tests for ExecutionPlan V2 frozen component graph task identity (W5-T02)."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from schemas.execution_plan_v2_frozen_task_identity import FROZEN_TASK_IDENTITY_VERSION
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateCompositionGraph,
    ProductAggregateCompositionNode,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.quote_snapshot_v2 import QuoteSnapshotComponentInstance
from services.execution_owner_decision_production_release_service import (
    assert_production_release_allowed,
)
from services.execution_plan_v2_frozen_task_identity_service import (
    collect_effective_task_rules,
    build_frozen_task_identity,
)
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview
from services.execution_plan_task_parser import materialize_operational_tasks_from_v2_envelope
from services.task_start_gate_service import assert_task_startable
from tests.execution_sold_scope_fixtures import (
    offer_scope,
    sample_product_definition,
    sold_scope_dossier_aggregate,
    snapshot_with_scope,
)
from tests.test_execution_owner_decision_production_release_guard import (
    PRODUCTION_BLOCKERS,
    _build_snapshot_with_owner_decisions,
    _simple_plan_tasks,
)
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

IDENTITY_OID_BASE = 21000
TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
ACM_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
PREMOUNT_TEMPLATE = "TPL-METAL-PREMOUNT-STRUCTURE_v1"
VOLUM_TEMPLATE = "TPL-VOLUM-ALUMINIU_v1"

ROOT_NODE = f"node:root_product:{TEMPLATE}"
MOUNTING_NODE = f"node:mounting_panel:{ACM_TEMPLATE}"
PREMOUNT_NODE = f"node:premount_structure:{PREMOUNT_TEMPLATE}"
VOLUM_NODE = f"node:volum_aluminum:{VOLUM_TEMPLATE}"


def _composition_graph(*, include_mounting: bool = True, include_premount: bool = False, include_volum: bool = False) -> ProductAggregateCompositionGraph:
    nodes = [
        ProductAggregateCompositionNode(
            node_id=ROOT_NODE,
            template_code=TEMPLATE,
            node_role="root_product",
            module_code=TEMPLATE,
            module_role="root_product",
            activation_source="frozen_snapshot",
        ),
    ]
    if include_mounting:
        nodes.append(
            ProductAggregateCompositionNode(
                node_id=MOUNTING_NODE,
                template_code=ACM_TEMPLATE,
                node_role="mounting_panel",
                module_code="structura_suport",
                module_role="mounting_panel",
                parent_node_id=ROOT_NODE,
                activation_source="canonical_mounting_solution",
            )
        )
    if include_premount:
        nodes.append(
            ProductAggregateCompositionNode(
                node_id=PREMOUNT_NODE,
                template_code=PREMOUNT_TEMPLATE,
                node_role="premount_structure",
                module_code="structura_suport",
                module_role="premount_structure",
                parent_node_id=MOUNTING_NODE if include_mounting else ROOT_NODE,
                activation_source="canonical_mounting_solution",
            )
        )
    if include_volum:
        nodes.append(
            ProductAggregateCompositionNode(
                node_id=VOLUM_NODE,
                template_code=VOLUM_TEMPLATE,
                node_role="volum_aluminum",
                module_code="modelare_cant",
                module_role="volum_aluminum",
                parent_node_id=ROOT_NODE,
                activation_source="template_registry",
            )
        )
    return ProductAggregateCompositionGraph(
        composed_graph_version="1.0.0",
        composition_mode="mounting_chain" if include_premount else "single_child",
        root_template_code=TEMPLATE,
        solution_status="confirmed",
        compatibility_status="compatible",
        active_child_template_codes=[
            code
            for code, flag in (
                (ACM_TEMPLATE, include_mounting),
                (PREMOUNT_TEMPLATE, include_premount),
                (VOLUM_TEMPLATE, include_volum),
            )
            if flag
        ],
        nodes=nodes,
        edges=[],
    )


def _root_operation(code: str, *, component_ref: str | None = None) -> ProductAggregateOperation:
    return ProductAggregateOperation(
        operation_code=code,
        label=code.replace("_", " ").title(),
        workcenter="WC_CNC" if "cnc" in code else "WC_ASM",
        component_ref=component_ref,
        source_template_code=TEMPLATE,
        provenance="parent",
    )


def _child_operation(
    code: str,
    *,
    node_id: str,
    template_code: str,
    module_code: str,
) -> ProductAggregateOperation:
    return ProductAggregateOperation(
        operation_code=code,
        label=code.replace("_", " ").title(),
        workcenter="WC_CNC",
        component_ref=f"{node_id}::{code.lower()}",
        source_template_code=template_code,
        mini_module_code=module_code,
        provenance="linked_module",
    )


def _identity_aggregate(
    *,
    include_mounting: bool = False,
    include_premount: bool = False,
    include_volum: bool = False,
    linked_logo: bool = False,
) -> ProductAggregate:
    aggregate = sold_scope_dossier_aggregate()
    aggregate.composition_graph = _composition_graph(
        include_mounting=include_mounting,
        include_premount=include_premount,
        include_volum=include_volum,
    )
    if include_mounting:
        aggregate.operations.extend(
            [
                _child_operation(
                    "CUT_ACM_PANEL",
                    node_id=MOUNTING_NODE,
                    template_code=ACM_TEMPLATE,
                    module_code="structura_suport",
                ),
                _child_operation(
                    "MOUNT_ACM_PANEL",
                    node_id=MOUNTING_NODE,
                    template_code=ACM_TEMPLATE,
                    module_code="structura_suport",
                ),
            ]
        )
    if include_volum:
        aggregate.operations.append(
            _child_operation(
                "side_forming",
                node_id=VOLUM_NODE,
                template_code=VOLUM_TEMPLATE,
                module_code="modelare_cant",
            )
        )
    if linked_logo:
        has_logo = any(
            r.task_name == "linked_logo_apply"
            for r in aggregate.task_contract.task_rules
        )
        if not has_logo:
            aggregate.task_contract.task_rules.append(
                ProductAggregateTaskRule(
                    task_name="linked_logo_apply",
                    task_type="vinyl_cutting",
                    priced_operation="logo_vinyl_apply",
                    sequence=99,
                    trigger_condition="linked_segment:logo_instance_001",
                    mini_module_code="logo_segment",
                )
            )
        if not any(
            op.operation_code == "logo_vinyl_apply" for op in aggregate.operations
        ):
            aggregate.operations.append(
                ProductAggregateOperation(
                    operation_code="logo_vinyl_apply",
                    label="Logo vinyl apply",
                    workcenter="WC_PRINT",
                    component_ref="linked_segment:logo_instance_001::logo_face",
                    source_template_code="TPL-VOLUMETRIC-LOGO_v1",
                    provenance="linked_module",
                )
            )
    return aggregate


def _build_identity_snapshot(
    aggregate: ProductAggregate,
    *,
    component_instances: list[QuoteSnapshotComponentInstance] | None = None,
) -> str:
    snapshot = OrderSnapshotV2(
        quote_id=IDENTITY_OID_BASE,
        quote_snapshot_v2_id=IDENTITY_OID_BASE,
        snapshot_code="OSN2-IDENTITY-001",
        content_hash="identityhashidentityhashidentityha",
        product_definition_snapshot=sample_product_definition(),
        product_aggregate_snapshot=aggregate,
        offer_scope_snapshot=offer_scope(mode="full_product", sold=[], runtime=[], use_legacy=True),
        component_instances=component_instances or [],
        commercial_price_proposal_snapshot=_commercial_preview(total=1500.0),
        estimated_internal_cost_snapshot=_internal_preview(total=620.0),
        owner_decisions_snapshot=[],
        accepted_commercial_total=1500.0,
        accepted_currency="RON",
        estimated_internal_total=620.0,
    )
    return snapshot.model_dump_json()


async def _seed_identity_order(
    db_session,
    *,
    order_id: int,
    aggregate: ProductAggregate,
    component_instances: list[QuoteSnapshotComponentInstance] | None = None,
    with_plan: bool = False,
) -> Orders:
    snapshot_json = _build_identity_snapshot(
        aggregate,
        component_instances=component_instances,
    )
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=order_id,
        snapshot_v2_json=snapshot_json,
    )
    if with_plan:
        preview = await build_execution_plan_v2_preview(db_session, order_id)
        await create_execution_plan_v2_from_order(db_session, order_id)
        await db_session.refresh(order)
    return order


def _task_keys(preview) -> list[str]:
    return [task.task_key for task in preview.planned_tasks]


def _identity_classifications(preview) -> list[str]:
    return [
        task.frozen_identity.identity_classification
        for task in preview.planned_tasks
        if task.frozen_identity is not None
    ]


@pytest.mark.asyncio
async def test_root_task_gets_frozen_root_identity(db_session):
    order_id = IDENTITY_OID_BASE + 1
    aggregate = _identity_aggregate()
    await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
    preview = await build_execution_plan_v2_preview(db_session, order_id)
    root_tasks = [
        t
        for t in preview.planned_tasks
        if t.frozen_identity
        and t.frozen_identity.source_component_role == "root_product"
    ]
    assert root_tasks
    first = root_tasks[0]
    assert first.frozen_identity.source_graph_node_id == ROOT_NODE
    assert first.frozen_identity.identity_classification == "FULL_FROZEN_COMPONENT_IDENTITY"
    assert first.task_key.startswith(f"{ROOT_NODE}:")
    assert first.task_key != first.source_task_rule_code


@pytest.mark.asyncio
async def test_mounting_panel_task_gets_graph_identity(db_session):
    order_id = IDENTITY_OID_BASE + 2
    aggregate = _identity_aggregate(include_mounting=True)
    instances = [
        QuoteSnapshotComponentInstance(
            instance_id="inst-mounting-001",
            source_template_code=ACM_TEMPLATE,
            runtime_module_code="structura_suport",
            classification="sold",
        )
    ]
    await _seed_identity_order(
        db_session,
        order_id=order_id,
        aggregate=aggregate,
        component_instances=instances,
    )
    preview = await build_execution_plan_v2_preview(db_session, order_id)
    mounting_tasks = [
        t
        for t in preview.planned_tasks
        if t.frozen_identity and t.frozen_identity.source_graph_node_id == MOUNTING_NODE
    ]
    assert len(mounting_tasks) >= 2
    assert all(t.frozen_identity.source_component_role == "mounting_panel" for t in mounting_tasks)
    assert all(t.frozen_identity.source_template_code == ACM_TEMPLATE for t in mounting_tasks)
    assert mounting_tasks[0].frozen_identity.source_component_instance_id == "inst-mounting-001"


@pytest.mark.asyncio
async def test_premount_graph_node_identity_when_present(db_session):
    order_id = IDENTITY_OID_BASE + 3
    aggregate = _identity_aggregate(include_mounting=True, include_premount=True)
    aggregate.operations.append(
        _child_operation(
            "fold_cassette",
            node_id=PREMOUNT_NODE,
            template_code=PREMOUNT_TEMPLATE,
            module_code="structura_suport",
        )
    )
    await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
    preview = await build_execution_plan_v2_preview(db_session, order_id)
    premount_tasks = [
        t
        for t in preview.planned_tasks
        if t.frozen_identity and t.frozen_identity.source_graph_node_id == PREMOUNT_NODE
    ]
    assert len(premount_tasks) == 1
    assert premount_tasks[0].frozen_identity.source_component_role == "premount_structure"


@pytest.mark.asyncio
async def test_volum_cant_preserves_component_local_scope(db_session):
    order_id = IDENTITY_OID_BASE + 4
    aggregate = _identity_aggregate(include_volum=True)
    await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
    preview = await build_execution_plan_v2_preview(db_session, order_id)
    volum_tasks = [
        t
        for t in preview.planned_tasks
        if t.frozen_identity and t.frozen_identity.source_graph_node_id == VOLUM_NODE
    ]
    assert len(volum_tasks) == 1
    assert volum_tasks[0].frozen_identity.operation_scope == "COMPONENT_LOCAL"
    assert volum_tasks[0].frozen_identity.source_template_code == VOLUM_TEMPLATE


@pytest.mark.asyncio
async def test_logo_path_partial_identity_nonblocking(db_session):
    order_id = IDENTITY_OID_BASE + 5
    aggregate = _identity_aggregate(linked_logo=True)
    instances = [
        QuoteSnapshotComponentInstance(
            instance_id="inst-logo-001",
            source_template_code="TPL-VOLUMETRIC-LOGO_v1",
            segment_key="logo_instance_001",
            classification="sold",
        )
    ]
    await _seed_identity_order(
        db_session,
        order_id=order_id,
        aggregate=aggregate,
        component_instances=instances,
    )
    preview = await build_execution_plan_v2_preview(db_session, order_id)
    logo_tasks = [
        t
        for t in preview.planned_tasks
        if t.source_task_rule_code == "linked_logo_apply"
        and t.frozen_identity
        and t.frozen_identity.source_segment_key == "logo_instance_001"
    ]
    assert len(logo_tasks) == 1
    assert "seg:logo_instance_001:" in logo_tasks[0].task_key
    assert logo_tasks[0].frozen_identity.source_component_instance_id == "inst-logo-001"


@pytest.mark.asyncio
async def test_repeated_preview_produces_identical_task_keys(db_session):
    order_id = IDENTITY_OID_BASE + 6
    aggregate = _identity_aggregate(include_mounting=True)
    await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
    first = await build_execution_plan_v2_preview(db_session, order_id)
    second = await build_execution_plan_v2_preview(db_session, order_id)
    assert _task_keys(first) == _task_keys(second)


@pytest.mark.asyncio
async def test_reordered_rules_do_not_change_task_keys(db_session):
    aggregate_a = _identity_aggregate(include_mounting=True)
    rules_a = list(aggregate_a.task_contract.task_rules)
    rules_b = list(reversed(rules_a))
    aggregate_b = aggregate_a.model_copy(
        update={
            "task_contract": ProductAggregateTaskContract(task_rules=rules_b),
        }
    )
    snapshot_a = OrderSnapshotV2.model_validate_json(_build_identity_snapshot(aggregate_a))
    snapshot_b = OrderSnapshotV2.model_validate_json(_build_identity_snapshot(aggregate_b))

    effective_a = collect_effective_task_rules(
        aggregate_a,
        graph=aggregate_a.composition_graph,
    )
    effective_b = collect_effective_task_rules(
        aggregate_b,
        graph=aggregate_b.composition_graph,
    )
    keys_a = {
        build_frozen_task_identity(
            snapshot=snapshot_a,
            effective=item,
            aggregate=aggregate_a,
            agg_op=None,
        ).deterministic_task_key
        for item in effective_a
        if item.rule.task_type != "READINESS_GATE"
    }
    keys_b = {
        build_frozen_task_identity(
            snapshot=snapshot_b,
            effective=item,
            aggregate=aggregate_b,
            agg_op=None,
        ).deterministic_task_key
        for item in effective_b
        if item.rule.task_type != "READINESS_GATE"
    }
    assert keys_a == keys_b


@pytest.mark.asyncio
async def test_same_operation_on_different_components_distinct_keys(db_session):
    aggregate = _identity_aggregate(include_mounting=True, include_volum=True)
    snapshot = OrderSnapshotV2.model_validate_json(_build_identity_snapshot(aggregate))
    effective = collect_effective_task_rules(aggregate, graph=aggregate.composition_graph)
    keys = []
    for item in effective:
        if item.bound_node and item.rule.priced_operation:
            ident = build_frozen_task_identity(
                snapshot=snapshot,
                effective=item,
                aggregate=aggregate,
                agg_op=None,
            )
            keys.append((item.bound_node.node_id, ident.deterministic_task_key))
    node_ids = {entry[0] for entry in keys}
    assert MOUNTING_NODE in node_ids
    assert VOLUM_NODE in node_ids
    assert len({entry[1] for entry in keys}) == len(keys)


@pytest.mark.asyncio
async def test_shared_root_operation_not_duplicated_per_child(db_session):
    order_id = IDENTITY_OID_BASE + 7
    aggregate = _identity_aggregate(include_mounting=True)
    await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
    preview = await build_execution_plan_v2_preview(db_session, order_id)
    keys = _task_keys(preview)
    assert len(keys) == len(set(keys))


@pytest.mark.asyncio
async def test_no_anonymous_or_legacy_name_identity_on_canonical_path(db_session):
    order_id = IDENTITY_OID_BASE + 8
    aggregate = _identity_aggregate(include_mounting=True, linked_logo=True)
    await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
    preview = await build_execution_plan_v2_preview(db_session, order_id)
    for task in preview.planned_tasks:
        assert task.frozen_identity is not None
        assert task.frozen_identity.identity_classification not in {
            "ANONYMOUS_TASK",
            "LEGACY_NAME_BASED_IDENTITY",
        }
        assert task.task_key == task.frozen_identity.deterministic_task_key
        assert task.task_key != task.source_task_rule_code or ":" in task.task_key


@pytest.mark.asyncio
async def test_repeated_persist_idempotent(db_session):
    order_id = IDENTITY_OID_BASE + 9
    aggregate = _identity_aggregate(include_mounting=True)
    await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
    first = await create_execution_plan_v2_from_order(db_session, order_id)
    second = await create_execution_plan_v2_from_order(db_session, order_id)
    assert first.execution_plan_id == second.execution_plan_id
    count = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    assert int(count or 0) >= 1


@pytest.mark.asyncio
async def test_materialize_preserves_frozen_identity_fields(db_session):
    order_id = IDENTITY_OID_BASE + 10
    aggregate = _identity_aggregate(include_mounting=True)
    await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
    await create_execution_plan_v2_from_order(db_session, order_id)
    result = await materialize_execution_plan_v2_operational_tasks(db_session, order_id)
    assert result.operational_tasks_count >= 1
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    parsed = json.loads(plan.tasks_json)
    operational = parsed.get("operational_tasks") or []
    mounting = next(
        t
        for t in operational
        if t.get("source_graph_node_id") == MOUNTING_NODE
    )
    assert mounting["task_id"].startswith(f"{MOUNTING_NODE}:")
    assert mounting.get("frozen_identity") is not None


@pytest.mark.asyncio
async def test_w5_t01_production_guard_remains_active(db_session):
    order_id = IDENTITY_OID_BASE + 11
    snapshot_json = _build_snapshot_with_owner_decisions(
        list(PRODUCTION_BLOCKERS),
        quote_id=order_id,
        quote_snapshot_v2_id=order_id,
    )
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=order_id,
        snapshot_v2_json=snapshot_json,
    )
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=order.code,
            snapshot_version=1,
            tasks_json=json.dumps(_simple_plan_tasks()),
            total_estimated_time_minutes=60,
        )
    )
    await db_session.commit()
    with pytest.raises(HTTPException) as exc:
        await assert_production_release_allowed(db_session, order_id)
    assert exc.value.detail["code"] == "production_release_blocked"


@pytest.mark.asyncio
async def test_order_snapshot_unchanged_after_preview_and_persist(db_session):
    order_id = IDENTITY_OID_BASE + 12
    aggregate = _identity_aggregate(include_mounting=True)
    order = await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
    before = order.snapshot_v2_json
    await build_execution_plan_v2_preview(db_session, order_id)
    await create_execution_plan_v2_from_order(db_session, order_id)
    refreshed = await db_session.get(Orders, order_id)
    assert refreshed.snapshot_v2_json == before


def test_materialize_envelope_identity_contract():
    envelope = {
        "source": "order_snapshot_v2",
        "planned_tasks": [
            {
                "task_key": f"{ROOT_NODE}:cnc_face_cut",
                "label": "Face CNC",
                "canonical_task_type": "cnc_routing",
                "source_task_rule_code": "cnc_face_cut",
                "source_operation_code": "face_cnc_cut",
                "frozen_identity": {
                    "contract_version": FROZEN_TASK_IDENTITY_VERSION,
                    "deterministic_task_key": f"{ROOT_NODE}:cnc_face_cut",
                    "source_graph_node_id": ROOT_NODE,
                    "source_component_role": "root_product",
                    "source_template_code": TEMPLATE,
                    "identity_classification": "FULL_FROZEN_COMPONENT_IDENTITY",
                    "operation_scope": "ROOT_PRODUCT",
                },
            }
        ],
    }
    operational, warnings, blockers = materialize_operational_tasks_from_v2_envelope(
        envelope,
        execution_plan_id=1,
        order_id=1,
    )
    assert not blockers
    assert operational[0]["task_id"] == f"{ROOT_NODE}:cnc_face_cut"
    assert operational[0]["source_graph_node_id"] == ROOT_NODE
    assert operational[0]["frozen_identity"]["contract_version"] == FROZEN_TASK_IDENTITY_VERSION
