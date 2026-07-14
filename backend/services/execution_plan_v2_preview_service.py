"""Read-only ExecutionPlan V2 preview from OrderSnapshotV2 (Step 9.3.2).

No DB writes, no persisted ExecutionPlan, no tasks/sessions.
Does NOT read commercial/internal pricing snapshots for task generation.
"""

from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.orders import Orders
from schemas.execution_plan_v2 import (
    EXECUTION_PLAN_V2_SOURCE,
    IGNORED_PRICING_SOURCES,
    READINESS_GATE_EXCLUDED_WARNING,
    READINESS_GATE_TASK_TYPE,
    EmployeeRoleRequirementSummary,
    ExecutionPlanV2Preview,
    ExecutionPlanV2PreviewStatus,
    MachineRequirementSummary,
    MaterialReadinessInput,
    PlannedOperationPreview,
    PlannedTaskDependency,
    PlannedTaskMachineRequirement,
    PlannedTaskPreview,
)
from schemas.order_snapshot_v2 import ORDER_SNAPSHOT_V2_VERSION, OrderSnapshotV2
from schemas.product_aggregate import ProductAggregate, ProductAggregateTaskRule
from schemas.product_definition import ProductDefinitionPreview, ProductDefinitionOperationRole
from schemas.quote_snapshot_v2 import QuoteSnapshotProvenanceEntry
from services.execution_plan_gate_service import CANONICAL_TASK_TYPES
from services.execution_sold_scope_reader_service import (
    BLOCKED_MISSING_SOLD_SCOPE,
    ExecutionSoldScopeContext,
    include_operation_for_sold_scope,
    include_task_rule_for_sold_scope,
    read_execution_sold_scope,
)
from services.execution_plan_v2_frozen_task_identity_service import (
    build_frozen_task_identity,
    collect_effective_task_rules,
    mark_shared_operations,
)
from services.order_execution_snapshot_mapper import resolve_canonical_task_type

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
    "product_system_execution_output",
)

PLANNING_MINUTES_WARNING = "PLANNING_MINUTES_SOURCE_REQUIRED"


class ExecutionPlanV2PreviewOrderNotFound(Exception):
    """Raised when the target order row does not exist."""


def _order_has_v2_fields(order: Orders) -> bool:
    quote_snapshot_v2_id = getattr(order, "quote_snapshot_v2_id", None)
    if quote_snapshot_v2_id is not None:
        return True
    snapshot_v2_json = getattr(order, "snapshot_v2_json", None)
    if snapshot_v2_json is None:
        return False
    if isinstance(snapshot_v2_json, str):
        return bool(snapshot_v2_json.strip())
    return bool(snapshot_v2_json)


def _compute_order_snapshot_hash(snapshot_v2_json: str) -> str:
    return hashlib.sha256(snapshot_v2_json.encode()).hexdigest()[:32]


def _base_provenance() -> list[QuoteSnapshotProvenanceEntry]:
    return [
        QuoteSnapshotProvenanceEntry(
            key="order_snapshot_v2",
            source=EXECUTION_PLAN_V2_SOURCE,
            detail="OrderSnapshotV2 frozen payload",
        ),
        QuoteSnapshotProvenanceEntry(
            key="execution_plan_v2_preview_service",
            source="execution_plan_v2_preview_service",
            detail="Read-only preview — not persisted",
        ),
    ]


def _is_readiness_gate_rule(rule: ProductAggregateTaskRule) -> bool:
    task_type = (rule.task_type or "").strip().upper()
    return task_type == READINESS_GATE_TASK_TYPE


def _blocked_preview(
    *,
    status: ExecutionPlanV2PreviewStatus,
    order: Orders | None,
    message: str,
    blockers: list[str] | None = None,
    warnings: list[str] | None = None,
    order_snapshot_hash: str | None = None,
) -> ExecutionPlanV2Preview:
    return ExecutionPlanV2Preview(
        status=status,
        order_id=order.id if order is not None else None,
        order_code=getattr(order, "code", None) if order is not None else None,
        quote_id=getattr(order, "quote_id", None) if order is not None else None,
        quote_snapshot_v2_id=getattr(order, "quote_snapshot_v2_id", None) if order is not None else None,
        order_snapshot_hash=order_snapshot_hash,
        blockers=blockers or [status],
        warnings=warnings or [],
        provenance=_base_provenance(),
        ignored_pricing_sources=list(IGNORED_PRICING_SOURCES),
        message=message,
    )


def _operation_role_index(
    product_definition: ProductDefinitionPreview,
) -> dict[str, ProductDefinitionOperationRole]:
    return {role.operation_code: role for role in product_definition.operation_roles}


def _should_include_task_rule(
    rule: ProductAggregateTaskRule,
    *,
    owner_decision_codes: set[str],
) -> bool:
    trigger = (rule.trigger_condition or "").strip()
    if not trigger:
        return True
    trigger_lower = trigger.lower()
    for code in owner_decision_codes:
        if code.lower() in trigger_lower:
            return True
    if trigger_lower.startswith("exclude:"):
        excluded = trigger_lower.removeprefix("exclude:").strip()
        return excluded not in owner_decision_codes
    return True


def _resolve_canonical_type(
    rule: ProductAggregateTaskRule,
) -> str | None:
    raw_type = (rule.task_type or "").strip()
    if raw_type in CANONICAL_TASK_TYPES:
        return raw_type
    priced_op = (rule.priced_operation or "").strip()
    if priced_op:
        mapped = resolve_canonical_task_type(process_id=priced_op, legacy_type=raw_type)
        if mapped is not None:
            return mapped
    if raw_type:
        mapped = resolve_canonical_task_type(process_id=raw_type, legacy_type=raw_type)
        if mapped is not None:
            return mapped
    return None


def _build_planned_operations(
    aggregate: ProductAggregate,
    op_roles: dict[str, ProductDefinitionOperationRole],
    *,
    sold_scope: ExecutionSoldScopeContext,
) -> list[PlannedOperationPreview]:
    operations: list[PlannedOperationPreview] = []
    for idx, op in enumerate(aggregate.operations):
        if not include_operation_for_sold_scope(op, ctx=sold_scope):
            continue
        role = op_roles.get(op.operation_code)
        operations.append(
            PlannedOperationPreview(
                operation_code=op.operation_code,
                label=op.label or (role.label if role else None),
                workcenter=op.workcenter or (role.workcenter if role else None),
                component_ref=op.component_ref or (role.component_ref if role else None),
                sequence_index=idx,
                source_template_code=op.source_template_code,
                priced=op.priced,
                provenance=["product_aggregate_snapshot.operations"],
            )
        )
    operations.sort(key=lambda item: (item.sequence_index or 0, item.operation_code))
    return operations


def _build_planned_tasks(
    snapshot: OrderSnapshotV2,
    aggregate: ProductAggregate,
    product_definition: ProductDefinitionPreview,
    *,
    owner_decision_codes: set[str],
    sold_scope: ExecutionSoldScopeContext,
) -> tuple[list[PlannedTaskPreview], list[str], str | None]:
    op_roles = _operation_role_index(product_definition)
    op_by_code = {
        str(op.operation_code or "").strip().lower(): op for op in aggregate.operations
    }
    tasks: list[PlannedTaskPreview] = []
    blockers: list[str] = []
    readiness_gate_excluded = False

    effective_rules = collect_effective_task_rules(
        aggregate,
        graph=aggregate.composition_graph,
    )
    frozen_identities: list = []

    for effective in effective_rules:
        rule = effective.rule
        if _is_readiness_gate_rule(rule):
            readiness_gate_excluded = True
            continue
        if not _should_include_task_rule(rule, owner_decision_codes=owner_decision_codes):
            continue
        if not include_task_rule_for_sold_scope(rule, ctx=sold_scope):
            continue

        canonical = _resolve_canonical_type(rule)
        if canonical is None or canonical not in CANONICAL_TASK_TYPES:
            blockers.append(f"unknown_task_type:{rule.task_name}")
            continue

        priced_op = (rule.priced_operation or "").strip()
        agg_op = op_by_code.get(priced_op.lower()) if priced_op else None
        role = op_roles.get(priced_op) if priced_op else None

        label = rule.task_name.replace("_", " ").strip().title()
        if agg_op and agg_op.label:
            label = agg_op.label
        elif role and role.label:
            label = role.label

        machine_req = None
        workcenter = None
        if agg_op and agg_op.workcenter:
            workcenter = agg_op.workcenter
        elif role and role.workcenter:
            workcenter = role.workcenter
        if workcenter:
            machine_req = PlannedTaskMachineRequirement(workcenter=workcenter)

        frozen_identity = build_frozen_task_identity(
            snapshot=snapshot,
            effective=effective,
            aggregate=aggregate,
            agg_op=agg_op,
        )
        frozen_identities.append(frozen_identity)

        task_provenance = ["product_aggregate_snapshot.task_contract.task_rules"]
        if effective.origin == "composition_graph_operation":
            task_provenance.append("product_aggregate_snapshot.composition_graph.operations")
        elif effective.origin == "linked_segment_task_rule":
            task_provenance.append("product_aggregate_snapshot.linked_segment_task_rules")

        tasks.append(
            PlannedTaskPreview(
                task_key=frozen_identity.deterministic_task_key,
                label=label,
                canonical_task_type=canonical,
                source_module_code=rule.mini_module_code,
                source_component_code=agg_op.component_ref if agg_op else None,
                source_operation_code=priced_op or None,
                source_task_rule_code=rule.task_name,
                sequence_index=rule.sequence,
                estimated_minutes=None,
                planning_minutes_source=None,
                machine_requirement=machine_req,
                warnings=[PLANNING_MINUTES_WARNING],
                provenance=task_provenance,
                frozen_identity=frozen_identity,
            )
        )

    frozen_identities = mark_shared_operations(frozen_identities)
    identity_by_key = {ident.deterministic_task_key: ident for ident in frozen_identities}
    for task in tasks:
        ident = identity_by_key.get(task.task_key)
        if ident is not None:
            task.frozen_identity = ident

    tasks.sort(key=lambda item: (item.sequence_index if item.sequence_index is not None else 9999, item.task_key))

    unknown_blocker = next((b for b in blockers if b.startswith("unknown_task_type:")), None)
    return tasks, blockers, unknown_blocker, readiness_gate_excluded


def _build_dependencies(tasks: list[PlannedTaskPreview]) -> list[PlannedTaskDependency]:
    deps: list[PlannedTaskDependency] = []
    sorted_tasks = sorted(
        tasks,
        key=lambda item: (item.sequence_index if item.sequence_index is not None else 9999, item.task_key),
    )
    prior_keys: list[str] = []
    for task in sorted_tasks:
        if prior_keys:
            immediate_prior = prior_keys[-1]
            task.depends_on_task_keys = [immediate_prior]
            deps.append(
                PlannedTaskDependency(task_key=task.task_key, depends_on_task_key=immediate_prior)
            )
        prior_keys.append(task.task_key)
    return deps


def _build_material_readiness(aggregate: ProductAggregate) -> list[MaterialReadinessInput]:
    return [
        MaterialReadinessInput(
            material_code=mat.material_code,
            label=mat.label,
            unit=mat.unit,
            status=mat.status,
        )
        for mat in aggregate.materials
    ]


def _build_machine_requirements(tasks: list[PlannedTaskPreview]) -> list[MachineRequirementSummary]:
    by_workcenter: dict[str, list[str]] = {}
    for task in tasks:
        wc = task.machine_requirement.workcenter if task.machine_requirement else None
        if not wc:
            continue
        by_workcenter.setdefault(wc, [])
        if task.source_operation_code:
            by_workcenter[wc].append(task.source_operation_code)
    return [
        MachineRequirementSummary(workcenter=wc, operation_codes=sorted(set(codes)))
        for wc, codes in sorted(by_workcenter.items())
    ]


def _build_preview_from_snapshot(
    order: Orders,
    snapshot: OrderSnapshotV2,
    *,
    order_snapshot_hash: str,
) -> ExecutionPlanV2Preview:
    product_definition = snapshot.product_definition_snapshot
    aggregate = snapshot.product_aggregate_snapshot
    assert product_definition is not None
    assert aggregate is not None

    owner_codes = {
        str(item.code).strip()
        for item in snapshot.owner_decisions_snapshot
        if getattr(item, "code", None)
    }

    provenance = _base_provenance()
    provenance.extend(
        [
            QuoteSnapshotProvenanceEntry(
                key="product_definition_snapshot",
                source="product_definition_snapshot",
                detail=f"template={product_definition.template_code}",
            ),
            QuoteSnapshotProvenanceEntry(
                key="product_aggregate_snapshot",
                source="product_aggregate_snapshot",
                detail=f"template={aggregate.template_code}",
            ),
        ]
    )

    sold_scope = read_execution_sold_scope(snapshot)
    if sold_scope.block_preview:
        return ExecutionPlanV2Preview(
            status="blocked_missing_sold_scope",
            order_id=order.id,
            order_code=getattr(order, "code", None),
            quote_id=snapshot.quote_id,
            quote_snapshot_v2_id=snapshot.quote_snapshot_v2_id,
            source_snapshot_code=snapshot.snapshot_code,
            source_content_hash=snapshot.content_hash,
            source_order_snapshot_version=snapshot.snapshot_version,
            order_snapshot_hash=order_snapshot_hash,
            blockers=[sold_scope.block_reason or BLOCKED_MISSING_SOLD_SCOPE],
            provenance=provenance,
            ignored_pricing_sources=list(IGNORED_PRICING_SOURCES),
            message="Component subset order snapshot is missing frozen sold runtime modules.",
        )

    if sold_scope.filter_enabled:
        provenance.append(
            QuoteSnapshotProvenanceEntry(
                key="execution_sold_scope_frozen",
                source="execution_sold_scope_reader_service",
                detail=f"mode={sold_scope.mode} sold_modules={sorted(sold_scope.sold_runtime_modules)}",
            )
        )

    if not aggregate.task_contract.task_rules:
        return ExecutionPlanV2Preview(
            status="blocked_missing_task_rules",
            order_id=order.id,
            quote_id=snapshot.quote_id,
            quote_snapshot_v2_id=snapshot.quote_snapshot_v2_id,
            source_snapshot_code=snapshot.snapshot_code,
            source_content_hash=snapshot.content_hash,
            source_order_snapshot_version=snapshot.snapshot_version,
            order_snapshot_hash=order_snapshot_hash,
            blockers=["blocked_missing_task_rules"],
            provenance=provenance,
            ignored_pricing_sources=list(IGNORED_PRICING_SOURCES),
            message="ProductAggregate task_contract.task_rules are required for V2 preview.",
        )

    tasks, task_blockers, unknown_blocker, readiness_gate_excluded = _build_planned_tasks(
        snapshot,
        aggregate,
        product_definition,
        owner_decision_codes=owner_codes,
        sold_scope=sold_scope,
    )
    if unknown_blocker is not None:
        return ExecutionPlanV2Preview(
            status="blocked_unknown_task_type",
            order_id=order.id,
            order_code=getattr(order, "code", None),
            quote_id=snapshot.quote_id,
            template_code=aggregate.template_code,
            quote_snapshot_v2_id=snapshot.quote_snapshot_v2_id,
            source_snapshot_code=snapshot.snapshot_code,
            source_content_hash=snapshot.content_hash,
            source_order_snapshot_version=snapshot.snapshot_version,
            order_snapshot_hash=order_snapshot_hash,
            blockers=task_blockers or ["blocked_unknown_task_type"],
            provenance=provenance,
            ignored_pricing_sources=list(IGNORED_PRICING_SOURCES),
            message="One or more task rules could not be mapped to canonical task types.",
        )

    operations = _build_planned_operations(
        aggregate,
        _operation_role_index(product_definition),
        sold_scope=sold_scope,
    )
    dependencies = _build_dependencies(tasks)
    warnings = [PLANNING_MINUTES_WARNING]
    if readiness_gate_excluded and READINESS_GATE_EXCLUDED_WARNING not in warnings:
        warnings.append(READINESS_GATE_EXCLUDED_WARNING)

    status: ExecutionPlanV2PreviewStatus = "partial_missing_planning_minutes"
    if tasks and all(task.estimated_minutes is not None for task in tasks):
        status = "ready_for_owner_review"

    return ExecutionPlanV2Preview(
        status=status,
        order_id=order.id,
        order_code=getattr(order, "code", None),
        quote_id=snapshot.quote_id,
        quote_snapshot_v2_id=snapshot.quote_snapshot_v2_id,
        template_code=aggregate.template_code,
        source_snapshot_code=snapshot.snapshot_code,
        source_content_hash=snapshot.content_hash,
        source_order_snapshot_version=snapshot.snapshot_version,
        order_snapshot_hash=order_snapshot_hash,
        planned_operations=operations,
        planned_tasks=tasks,
        dependencies=dependencies,
        material_readiness_inputs=_build_material_readiness(aggregate),
        machine_requirements=_build_machine_requirements(tasks),
        warnings=warnings,
        provenance=provenance,
        ignored_pricing_sources=list(IGNORED_PRICING_SOURCES),
        message="ExecutionPlan V2 preview built from OrderSnapshotV2 technical snapshots only.",
        input_summary={
            "task_count": len(tasks),
            "operation_count": len(operations),
            "template_code": aggregate.template_code,
            "owner_decision_count": len(owner_codes),
            "sold_scope_mode": sold_scope.mode,
            "sold_scope_filter_enabled": sold_scope.filter_enabled,
            "sold_runtime_modules_count": len(sold_scope.sold_runtime_modules),
        },
    )


async def build_execution_plan_v2_preview(
    db: AsyncSession,
    order_id: int,
) -> ExecutionPlanV2Preview:
    """Build a deterministic read-only ExecutionPlan V2 preview for an order."""
    order = await db.get(Orders, order_id)
    if order is None:
        raise ExecutionPlanV2PreviewOrderNotFound()

    if not _order_has_v2_fields(order):
        return _blocked_preview(
            status="blocked_legacy_order",
            order=order,
            message="ExecutionPlan V2 preview requires OrderSnapshotV2.",
            blockers=["blocked_legacy_order"],
        )

    if not getattr(order, "quote_snapshot_v2_id", None):
        return _blocked_preview(
            status="blocked_missing_quote_snapshot_v2_id",
            order=order,
            message="Order is missing quote_snapshot_v2_id.",
            blockers=["blocked_missing_quote_snapshot_v2_id"],
        )

    raw_json = getattr(order, "snapshot_v2_json", None)
    if raw_json is None or not str(raw_json).strip():
        return _blocked_preview(
            status="blocked_missing_order_snapshot_v2",
            order=order,
            message="Order is missing snapshot_v2_json.",
            blockers=["blocked_missing_order_snapshot_v2"],
        )

    snapshot_json = str(raw_json)
    order_snapshot_hash = _compute_order_snapshot_hash(snapshot_json)

    try:
        snapshot = OrderSnapshotV2.model_validate_json(snapshot_json)
    except Exception as exc:
        return _blocked_preview(
            status="blocked_missing_order_snapshot_v2",
            order=order,
            message=f"snapshot_v2_json invalid: {exc}",
            blockers=["SNAPSHOT_JSON_INVALID"],
            order_snapshot_hash=order_snapshot_hash,
        )

    if snapshot.product_definition_snapshot is None:
        return _blocked_preview(
            status="blocked_missing_product_definition",
            order=order,
            message="OrderSnapshotV2 product_definition_snapshot is required.",
            blockers=["blocked_missing_product_definition"],
            order_snapshot_hash=order_snapshot_hash,
        )

    if snapshot.product_aggregate_snapshot is None:
        return _blocked_preview(
            status="blocked_missing_product_aggregate",
            order=order,
            message="OrderSnapshotV2 product_aggregate_snapshot is required.",
            blockers=["blocked_missing_product_aggregate"],
            order_snapshot_hash=order_snapshot_hash,
        )

    preview = _build_preview_from_snapshot(
        order,
        snapshot,
        order_snapshot_hash=order_snapshot_hash,
    )
    if snapshot.snapshot_version and snapshot.snapshot_version != ORDER_SNAPSHOT_V2_VERSION:
        if "ORDER_SNAPSHOT_HASH_VERIFICATION_PENDING" not in preview.warnings:
            preview.warnings.append("ORDER_SNAPSHOT_HASH_VERIFICATION_PENDING")
    return preview
