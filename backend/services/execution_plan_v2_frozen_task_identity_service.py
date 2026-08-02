"""Frozen graph → ExecutionPlan V2 task identity (W5-T02).

Derives deterministic task keys and component ownership from OrderSnapshotV2 only.
No live Product System rebuild, no display-name heuristics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from schemas.execution_plan_v2_frozen_task_identity import (
    FROZEN_TASK_IDENTITY_VERSION,
    FrozenTaskIdentity,
    IdentityClassification,
    OperationScope,
    TaskRuleOrigin,
)
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateCompositionGraph,
    ProductAggregateCompositionNode,
    ProductAggregateOperation,
    ProductAggregateTaskRule,
)
from schemas.quote_snapshot_v2 import QuoteSnapshotComponentInstance
from services.order_execution_snapshot_mapper import resolve_canonical_task_type
from data.product_process.catalogs import is_bom_only_without_activation
from services.product_process_aggregate_bridge import (
    alias_parent_for,
    collapse_operational_alias_rules,
)

LINKED_SEGMENT_PREFIX = "linked_segment:"
SEGMENT_NAMESPACE_SEP = "::"
NODE_ID_PREFIX = "node:"

LINKED_SEGMENT_TRIGGER_RE = re.compile(r"^linked_segment:(?P<segment>[^:\s]+)", re.IGNORECASE)


@dataclass(frozen=True)
class EffectiveTaskRule:
    rule: ProductAggregateTaskRule
    origin: TaskRuleOrigin
    bound_node: ProductAggregateCompositionNode | None
    segment_key: str | None


def _root_node_id(template_code: str) -> str:
    return f"{NODE_ID_PREFIX}root_product:{template_code}"


def _parse_segment_from_trigger(trigger: str | None) -> str | None:
    if not trigger:
        return None
    match = LINKED_SEGMENT_TRIGGER_RE.match(trigger.strip())
    if not match:
        return None
    return match.group("segment").strip() or None


def _parse_node_id_from_component_ref(component_ref: str | None) -> str | None:
    ref = str(component_ref or "").strip()
    if not ref:
        return None
    if ref.lower().startswith(LINKED_SEGMENT_PREFIX):
        return None
    if SEGMENT_NAMESPACE_SEP in ref:
        prefix = ref.split(SEGMENT_NAMESPACE_SEP, 1)[0].strip()
        if prefix.startswith(NODE_ID_PREFIX):
            return prefix
    if ref.startswith(NODE_ID_PREFIX):
        return ref
    return None


def _parse_segment_from_component_ref(component_ref: str | None) -> str | None:
    ref = str(component_ref or "").strip()
    if not ref:
        return None
    if ref.lower().startswith(LINKED_SEGMENT_PREFIX):
        payload = ref[len(LINKED_SEGMENT_PREFIX) :]
        if SEGMENT_NAMESPACE_SEP in payload:
            return payload.split(SEGMENT_NAMESPACE_SEP, 1)[0].strip() or None
        return payload.strip() or None
    if SEGMENT_NAMESPACE_SEP in ref:
        suffix = ref.split(SEGMENT_NAMESPACE_SEP, 1)[1].strip()
        if suffix.startswith("segment:"):
            return suffix.removeprefix("segment:").strip() or None
    return None


def _index_graph_nodes(
    graph: ProductAggregateCompositionGraph | None,
    *,
    root_template_code: str,
) -> dict[str, ProductAggregateCompositionNode]:
    nodes: dict[str, ProductAggregateCompositionNode] = {}
    if graph is None:
        return nodes
    for node in graph.nodes:
        nodes[node.node_id] = node
    if _root_node_id(root_template_code) not in nodes:
        for node in graph.nodes:
            if node.node_role == "root_product":
                nodes[node.node_id] = node
                break
    return nodes


def _match_component_instance(
    instances: list[QuoteSnapshotComponentInstance],
    *,
    template_code: str | None,
    module_code: str | None,
    segment_key: str | None,
    node_role: str | None,
) -> str | None:
    if segment_key:
        for inst in instances:
            if str(inst.segment_key or "").strip() == segment_key:
                return str(inst.instance_id).strip() or None
    for inst in instances:
        inst_template = str(inst.source_template_code or "").strip()
        inst_module = str(inst.runtime_module_code or "").strip()
        if template_code and inst_template == template_code:
            if module_code and inst_module and inst_module != module_code:
                continue
            return str(inst.instance_id).strip() or None
    if node_role == "root_product" and instances:
        for inst in instances:
            if str(inst.classification or "") == "sold":
                return str(inst.instance_id).strip() or None
    return None


def _operation_belongs_to_node(
    operation: ProductAggregateOperation,
    node: ProductAggregateCompositionNode,
) -> bool:
    ref = str(operation.component_ref or "").strip()
    if ref.startswith(f"{node.node_id}{SEGMENT_NAMESPACE_SEP}"):
        return True
    if ref == node.node_id:
        return True
    source_template = str(operation.source_template_code or "").strip()
    if source_template and source_template == node.template_code:
        parsed_node = _parse_node_id_from_component_ref(ref)
        if parsed_node == node.node_id:
            return True
        if node.node_role != "root_product" and operation.provenance == "linked_module":
            return True
    return False


def _infer_task_type_for_operation(operation: ProductAggregateOperation) -> str | None:
    code = str(operation.operation_code or "").strip()
    if not code:
        return None
    return resolve_canonical_task_type(process_id=code, legacy_type=code)


def _synthetic_rule_from_operation(
    operation: ProductAggregateOperation,
    *,
    node: ProductAggregateCompositionNode,
    sequence: int,
) -> ProductAggregateTaskRule | None:
    priced_op = str(operation.operation_code or "").strip()
    if not priced_op:
        return None
    # DEC-002 = A — never synthesize BOM-only ops (premount) into task rules.
    if is_bom_only_without_activation(operation_code=priced_op, priced_operation=priced_op):
        return None
    task_type = _infer_task_type_for_operation(operation)
    if task_type is None:
        return None
    task_name = priced_op.lower()
    return ProductAggregateTaskRule(
        task_name=task_name,
        task_type=task_type,
        priced_operation=priced_op,
        sequence=sequence,
        trigger_condition=None,
        provenance="linked_module",
        mini_module_code=node.module_code,
    )


def collect_effective_task_rules(
    aggregate: ProductAggregate,
    *,
    graph: ProductAggregateCompositionGraph | None,
) -> list[EffectiveTaskRule]:
    """Merge dossier task rules with graph-bound operations missing dossier rules."""
    root_template = aggregate.template_code
    nodes_by_id = _index_graph_nodes(graph, root_template_code=root_template)
    root_node = next(
        (n for n in (graph.nodes if graph else []) if n.node_role == "root_product"),
        None,
    )
    if root_node is None and graph is None:
        root_node = ProductAggregateCompositionNode(
            node_id=_root_node_id(root_template),
            template_code=root_template,
            node_role="root_product",
            module_code=root_template,
            module_role="root_product",
            activation_source="frozen_snapshot",
        )

    effective: list[EffectiveTaskRule] = []
    covered_ops: set[tuple[str, str]] = set()
    covered_rules: set[tuple[str, str, str, str]] = set()

    # DEC-003 / DEC-004 — collapse aliases before EP effective set (frozen or live).
    dossier_rules = collapse_operational_alias_rules(
        list(aggregate.task_contract.task_rules or [])
    )
    dossier_rules.sort(
        key=lambda rule: (rule.sequence if rule.sequence is not None else 9999, rule.task_name)
    )

    op_by_code = {
        str(op.operation_code or "").strip().lower(): op
        for op in aggregate.operations
        if str(op.operation_code or "").strip()
    }

    def _bind_rule_to_node(
        rule: ProductAggregateTaskRule,
        *,
        origin: TaskRuleOrigin,
        segment_key: str | None,
    ) -> ProductAggregateCompositionNode | None:
        priced_op = str(rule.priced_operation or "").strip().lower()
        agg_op = op_by_code.get(priced_op) if priced_op else None
        if agg_op is not None:
            node_id = _parse_node_id_from_component_ref(agg_op.component_ref)
            if node_id and node_id in nodes_by_id:
                return nodes_by_id[node_id]
            if str(agg_op.source_template_code or "").strip():
                for node in nodes_by_id.values():
                    if node.template_code == agg_op.source_template_code:
                        if _operation_belongs_to_node(agg_op, node):
                            return node
        if segment_key:
            for node in nodes_by_id.values():
                if node.node_role not in {"root_product"}:
                    continue
            return root_node
        return root_node

    for rule in dossier_rules:
        if is_bom_only_without_activation(
            priced_operation=rule.priced_operation,
            task_name=rule.task_name,
            process_code=rule.process_code,
            trigger_condition=rule.trigger_condition,
        ):
            continue
        segment_key = _parse_segment_from_trigger(rule.trigger_condition)
        origin: TaskRuleOrigin = (
            "linked_segment_task_rule" if segment_key else "dossier_task_rule"
        )
        bound_node = _bind_rule_to_node(rule, origin=origin, segment_key=segment_key)
        node_id = bound_node.node_id if bound_node else _root_node_id(root_template)
        priced_key = str(rule.priced_operation or rule.task_name or "").strip().lower()
        trigger_key = str(rule.trigger_condition or "").strip().lower()
        dedupe_key = (node_id, priced_key, trigger_key, rule.task_name)
        if dedupe_key in covered_rules:
            continue
        covered_rules.add(dedupe_key)
        covered_ops.add((node_id, priced_key))
        effective.append(
            EffectiveTaskRule(
                rule=rule,
                origin=origin,
                bound_node=bound_node,
                segment_key=segment_key,
            )
        )

    if graph is not None:
        child_nodes = [n for n in graph.nodes if n.node_role != "root_product"]
        next_sequence = (
            max((r.rule.sequence or 0) for r in effective) + 10 if effective else 100
        )
        for node in sorted(child_nodes, key=lambda n: (n.node_role, n.template_code, n.node_id)):
            node_ops = [
                op
                for op in aggregate.operations
                if _operation_belongs_to_node(op, node)
            ]
            node_ops.sort(key=lambda op: str(op.operation_code or ""))
            for op in node_ops:
                priced_key = str(op.operation_code or "").strip().lower()
                if not priced_key or (node.node_id, priced_key) in covered_ops:
                    continue
                # Module alias ops must not synthesize a second planned task.
                parent = alias_parent_for(op.operation_code or "")
                if parent and (node.node_id, parent.lower()) in covered_ops:
                    continue
                if parent and any(
                    str(r.rule.priced_operation or "").strip().lower() == parent.lower()
                    for r in effective
                ):
                    continue
                synthetic = _synthetic_rule_from_operation(
                    op,
                    node=node,
                    sequence=next_sequence,
                )
                if synthetic is None:
                    continue
                covered_ops.add((node.node_id, priced_key))
                effective.append(
                    EffectiveTaskRule(
                        rule=synthetic,
                        origin="composition_graph_operation",
                        bound_node=node,
                        segment_key=None,
                    )
                )
                next_sequence += 1

    effective.sort(
        key=lambda item: (
            item.rule.sequence if item.rule.sequence is not None else 9999,
            item.bound_node.node_id if item.bound_node else "",
            item.rule.task_name,
        )
    )
    return effective


def _classify_identity(
    *,
    bound_node: ProductAggregateCompositionNode | None,
    instance_id: str | None,
    template_code: str | None,
    module_code: str | None,
    operation_code: str | None,
    deterministic_key: str,
    task_rule_code: str,
) -> IdentityClassification:
    if bound_node and instance_id and template_code and operation_code:
        return "FULL_FROZEN_COMPONENT_IDENTITY"
    if bound_node and template_code and operation_code:
        return "FULL_FROZEN_COMPONENT_IDENTITY"
    if bound_node and template_code:
        return "TEMPLATE_LEVEL_IDENTITY_ONLY"
    if module_code and operation_code:
        return "MODULE_LEVEL_IDENTITY_ONLY"
    if operation_code and template_code:
        return "OPERATION_LEVEL_IDENTITY_ONLY"
    if deterministic_key == task_rule_code:
        return "LEGACY_NAME_BASED_IDENTITY"
    if not operation_code and not template_code:
        return "ANONYMOUS_TASK"
    return "OPERATION_LEVEL_IDENTITY_ONLY"


def _resolve_operation_scope(
    *,
    bound_node: ProductAggregateCompositionNode | None,
    segment_key: str | None,
    origin: TaskRuleOrigin,
) -> OperationScope:
    if segment_key:
        return "COMPONENT_LOCAL"
    if bound_node is None:
        return "NOT_PROVEN"
    role = str(bound_node.node_role or "").strip()
    if role == "root_product":
        return "ROOT_PRODUCT"
    if role in {"mounting_panel", "premount_structure", "volum_aluminum"}:
        return "COMPONENT_LOCAL"
    if role == "other":
        return "COMPONENT_LOCAL"
    if origin == "composition_graph_operation":
        return "COMPONENT_LOCAL"
    return "COMPONENT_LOCAL"


def build_frozen_task_identity(
    *,
    snapshot: OrderSnapshotV2,
    effective: EffectiveTaskRule,
    aggregate: ProductAggregate,
    agg_op: ProductAggregateOperation | None,
) -> FrozenTaskIdentity:
    rule = effective.rule
    graph = aggregate.composition_graph
    root_template = aggregate.template_code
    nodes_by_id = _index_graph_nodes(graph, root_template_code=root_template)

    bound_node = effective.bound_node
    if bound_node is None:
        bound_node = nodes_by_id.get(_root_node_id(root_template))
        if bound_node is None and graph:
            bound_node = next(
                (n for n in graph.nodes if n.node_role == "root_product"),
                None,
            )

    segment_key = effective.segment_key
    if not segment_key and agg_op is not None:
        segment_key = _parse_segment_from_component_ref(agg_op.component_ref)

    source_graph_node_id = bound_node.node_id if bound_node else _root_node_id(root_template)
    source_template_code = (
        bound_node.template_code if bound_node else str(agg_op.source_template_code or root_template)
    )
    source_component_role = bound_node.node_role if bound_node else "root_product"
    parent_graph_node_id = bound_node.parent_node_id if bound_node else None

    priced_op = str(rule.priced_operation or "").strip() or None
    task_rule_code = str(rule.task_name or "").strip() or priced_op or "unknown_task"

    if segment_key:
        deterministic_task_key = f"{source_graph_node_id}:seg:{segment_key}:{task_rule_code}"
    else:
        deterministic_task_key = f"{source_graph_node_id}:{task_rule_code}"

    instance_id = _match_component_instance(
        list(snapshot.component_instances or []),
        template_code=source_template_code,
        module_code=rule.mini_module_code or (bound_node.module_code if bound_node else None),
        segment_key=segment_key,
        node_role=source_component_role,
    )

    operation_scope = _resolve_operation_scope(
        bound_node=bound_node,
        segment_key=segment_key,
        origin=effective.origin,
    )

    identity_classification = _classify_identity(
        bound_node=bound_node,
        instance_id=instance_id,
        template_code=source_template_code,
        module_code=rule.mini_module_code,
        operation_code=priced_op,
        deterministic_key=deterministic_task_key,
        task_rule_code=task_rule_code,
    )

    provenance = [
        f"origin={effective.origin}",
        f"graph_node={source_graph_node_id}",
        "execution_plan_v2_frozen_task_identity_service",
    ]
    if snapshot.snapshot_code:
        provenance.append(f"order_snapshot={snapshot.snapshot_code}")
    if snapshot.content_hash:
        provenance.append(f"snapshot_hash={snapshot.content_hash}")

    return FrozenTaskIdentity(
        contract_version=FROZEN_TASK_IDENTITY_VERSION,
        deterministic_task_key=deterministic_task_key,
        source_graph_node_id=source_graph_node_id,
        source_component_role=source_component_role,
        source_template_code=source_template_code,
        source_component_instance_id=instance_id,
        source_segment_key=segment_key,
        parent_graph_node_id=parent_graph_node_id,
        source_module_code=rule.mini_module_code,
        source_operation_code=priced_op,
        source_task_rule_code=task_rule_code,
        operation_scope=operation_scope,
        identity_classification=identity_classification,
        shared_operation=False,
        task_rule_origin=effective.origin,
        provenance=provenance,
    )


def mark_shared_operations(identities: list[FrozenTaskIdentity]) -> list[FrozenTaskIdentity]:
    """Flag operations that appear once across the order at root scope."""
    op_counts: dict[str, list[int]] = {}
    for idx, ident in enumerate(identities):
        op = str(ident.source_operation_code or "").strip().lower()
        if not op:
            continue
        op_counts.setdefault(op, []).append(idx)

    patched = list(identities)
    for op, indices in op_counts.items():
        if len(indices) != 1:
            continue
        idx = indices[0]
        ident = patched[idx]
        if ident.operation_scope == "ROOT_PRODUCT":
            patched[idx] = ident.model_copy(update={"shared_operation": True})
    return patched
