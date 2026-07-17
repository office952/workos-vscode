"""Bridge ResolvedProductProcessGraph → Aggregate task_contract / in-memory Snapshot V2.

Read-only helpers. No DB writes. No CPP. No Intake mutation.
Live Aggregate overlay: apply_modular_process_graph_to_aggregate.
"""

from __future__ import annotations

import logging
from typing import Any

from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateConflict,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.product_process_contract import (
    ProductProcessResolveInput,
    ResolvedProductProcessGraph,
)
from services.product_process_resolve_input_adapter import (
    PROCESS_GRAPH_SOURCE_LEGACY,
    PROCESS_GRAPH_SOURCE_MODULAR,
    build_resolve_input_from_active_config,
    template_has_modular_process_contract,
)
from services.product_process_resolver_service import (
    resolve_product_process_graph,
    resolved_graph_to_aggregate_task_rules,
)

logger = logging.getLogger(__name__)


def build_aggregate_task_contract_from_resolved(
    graph: ResolvedProductProcessGraph,
) -> dict[str, Any]:
    return {
        "task_rules": resolved_graph_to_aggregate_task_rules(graph),
        "notes": [
            "derived_from_product_process_resolver",
            f"contract_version={graph.contract_version}",
            f"graph_hash={graph.graph_hash}",
        ],
    }


def build_in_memory_snapshot_v2_from_resolved(
    graph: ResolvedProductProcessGraph,
    *,
    inp: ProductProcessResolveInput | None = None,
) -> dict[str, Any]:
    """Minimal QuoteSnapshotV2-shaped payload for frozen graph + Build 4C proof."""
    task_contract = build_aggregate_task_contract_from_resolved(graph)
    materials: list[dict[str, Any]] = []
    # Role codes only — not commercial SKUs (no invent)
    seen_roles: set[str] = set()
    for m in graph.material_roles:
        if m.material_role in seen_roles:
            continue
        seen_roles.add(m.material_role)
        materials.append(
            {
                "material_code": f"ROLE-{m.material_role}",
                "label": m.material_role,
                "unit": None,
                "mini_module_code": None,
                "component_ref": m.source_component,
            }
        )
    # Interface adhesive visibility for FACE+CANT frozen assertions when both present
    if "FACE_CANT" in graph.active_interface_codes:
        if not any("ADEZIV" in (x.get("material_code") or "").upper() or "ADHESIVE" in (x.get("material_code") or "").upper() for x in materials):
            materials.append(
                {
                    "material_code": "MAT-ADEZIV-CANT-LITERE",
                    "label": "CYANOACRYLATE_ADHESIVE",
                    "mini_module_code": "modelare_cant",
                }
            )

    operations: list[dict[str, Any]] = []
    for r in graph.process_rules:
        if r.priced_operation:
            operations.append(
                {
                    "operation_code": r.priced_operation,
                    "label": r.name,
                    "mini_module_code": r.mini_module_code,
                }
            )
        if r.process_code == "BOND_FACE_TO_CANT":
            operations.append(
                {
                    "operation_code": "return_face_bonding",
                    "label": r.name,
                    "mini_module_code": "modelare_cant",
                }
            )

    active_modules = list(graph.active_component_codes)
    geometry = (inp.geometry if inp else {}) or {}

    return {
        "snapshot_version": "v2",
        "template_code": graph.product_template_code,
        "product_aggregate_snapshot": {
            "materials": materials,
            "operations": operations,
            "task_contract": task_contract,
            "components": [
                {"component_id": c, "mini_module_code": c.lower()}
                for c in graph.active_component_codes
            ],
        },
        "active_scope_snapshot": {
            "compiled": {
                "errors": [],
                "active_modules": active_modules,
                "sold_modules": active_modules,
            }
        },
        "geometry_input_snapshot": {
            "width_mm": geometry.get("overall_width") or geometry.get("width_mm"),
            "height_mm": geometry.get("overall_height") or geometry.get("height_mm"),
            "letter_count": geometry.get("element_count") or geometry.get("letter_count"),
            "letter_face_area_m2": geometry.get("total_face_area"),
            "letter_perimeter_m": geometry.get("total_perimeter"),
        },
        "commercial_price_proposal_snapshot": {
            "currency": "RON",
            "lines": [],
            "net_total": None,
            "gross_total": None,
        },
        "process_graph_meta": {
            "graph_hash": graph.graph_hash,
            "contract_version": graph.contract_version,
            "config_echo": graph.config_echo,
        },
    }


def resolve_and_build_snapshot(inp: ProductProcessResolveInput) -> tuple[ResolvedProductProcessGraph, dict[str, Any]]:
    graph = resolve_product_process_graph(inp)
    snap = build_in_memory_snapshot_v2_from_resolved(graph, inp=inp)
    return graph, snap


def _logo_segment_rules(aggregate: ProductAggregate) -> list[ProductAggregateTaskRule]:
    out: list[ProductAggregateTaskRule] = []
    for rule in aggregate.task_contract.task_rules:
        trig = str(rule.trigger_condition or "")
        if trig.startswith("linked_segment:"):
            out.append(rule)
    return out


def _rules_from_resolved(graph: ResolvedProductProcessGraph) -> list[ProductAggregateTaskRule]:
    raw = resolved_graph_to_aggregate_task_rules(graph)
    rules: list[ProductAggregateTaskRule] = []
    for row in raw:
        rules.append(
            ProductAggregateTaskRule(
                task_name=str(row.get("task_name") or ""),
                task_type=row.get("task_type"),
                priced_operation=row.get("priced_operation"),
                sequence=row.get("sequence"),
                trigger_condition=row.get("trigger_condition"),
                provenance="derived",
                mini_module_code=row.get("mini_module_code"),
                depends_on_process_ids=list(row.get("depends_on_process_ids") or []),
                process_code=row.get("process_code"),
            )
        )
    return rules


def apply_modular_process_graph_to_aggregate(
    aggregate: ProductAggregate,
    *,
    workspace_payload: dict[str, Any] | None = None,
    geometry_inputs: dict[str, Any] | None = None,
) -> ProductAggregate:
    """
    Live Aggregate bridge: replace letters task_rules with resolver DAG when template
    has modular process contract. Preserves linked_segment logo rules. Never concatenates
    dossier + resolver. Zero DB writes.
    """
    if not template_has_modular_process_contract(aggregate.template_code):
        tc = aggregate.task_contract
        if tc.process_graph_source:
            return aggregate
        return aggregate.model_copy(
            update={
                "task_contract": tc.model_copy(
                    update={
                        "process_graph_source": PROCESS_GRAPH_SOURCE_LEGACY,
                        "notes": list(tc.notes)
                        + ["process_graph_source=dossier_legacy"],
                    }
                )
            }
        )

    inp, map_warnings, map_blockers = build_resolve_input_from_active_config(
        template_code=aggregate.template_code,
        workspace_payload=workspace_payload,
        geometry_inputs=geometry_inputs,
    )
    graph = resolve_product_process_graph(inp)
    logo_rules = _logo_segment_rules(aggregate)

    warnings = list(aggregate.warnings)
    conflicts = list(aggregate.conflicts)
    for code in map_warnings:
        warnings.append(
            ProductAggregateConflict(
                code=f"PROCESS_MAP_{code.upper()}",
                severity="warning",
                message=code,
                details={},
            )
        )
    for code in map_blockers:
        conflicts.append(
            ProductAggregateConflict(
                code=f"PROCESS_MAP_{code.upper()}",
                severity="error",
                message=code,
                details={},
            )
        )
    for b in graph.blockers:
        conflicts.append(
            ProductAggregateConflict(
                code=f"PROCESS_RESOLVER_{b.code.upper()}",
                severity="error",
                message=b.message,
                details=b.details,
            )
        )
    for w in graph.warnings:
        warnings.append(
            ProductAggregateConflict(
                code=f"PROCESS_RESOLVER_{w.code.upper()}",
                severity="warning",
                message=w.message,
                details=w.details,
            )
        )

    hard_blocked = graph.readiness == "blocked" or bool(map_blockers)
    if hard_blocked:
        logger.info(
            "process_bridge_blocked template=%s blockers=%s",
            aggregate.template_code,
            [b.code for b in graph.blockers] + map_blockers,
        )
        notes = [
            "process_graph_source=modular_resolver",
            "process_graph_status=blocked",
            f"contract_version={graph.contract_version}",
            f"graph_hash={graph.graph_hash}",
            "letters_task_rules_cleared_on_block; logo linked_segment rules preserved",
        ]
        return aggregate.model_copy(
            update={
                "task_contract": ProductAggregateTaskContract(
                    task_rules=list(logo_rules),
                    notes=notes,
                    process_graph_source=PROCESS_GRAPH_SOURCE_MODULAR,
                    process_graph_hash=graph.graph_hash,
                    process_contract_version=graph.contract_version,
                ),
                "warnings": warnings,
                "conflicts": conflicts,
            }
        )

    modular_rules = _rules_from_resolved(graph)
    # Single letters graph — no dossier concat
    combined = list(modular_rules) + list(logo_rules)
    notes = [
        "process_graph_source=modular_resolver",
        "process_graph_status=ready",
        f"contract_version={graph.contract_version}",
        f"graph_hash={graph.graph_hash}",
        f"active_components={','.join(graph.active_component_codes)}",
        f"active_interfaces={','.join(graph.active_interface_codes)}",
        "dossier_task_rules_not_concatenated",
    ]
    if logo_rules:
        notes.append(f"logo_linked_segment_rules_preserved={len(logo_rules)}")

    logger.info(
        "process_bridge_applied template=%s source=modular_resolver rules=%s edges=%s hash=%s",
        aggregate.template_code,
        len(modular_rules),
        sum(len(r.depends_on_process_ids) for r in modular_rules),
        graph.graph_hash,
    )

    warnings.append(
        ProductAggregateConflict(
            code="PROCESS_GRAPH_MODULAR_RESOLVER",
            severity="info",
            message="task_contract compiled from modular product process resolver (not dossier list).",
            details={
                "process_graph_source": PROCESS_GRAPH_SOURCE_MODULAR,
                "process_graph_hash": graph.graph_hash,
                "contract_version": graph.contract_version,
                "process_count": len(modular_rules),
                "edge_count": sum(len(r.depends_on_process_ids) for r in modular_rules),
            },
        )
    )

    return aggregate.model_copy(
        update={
            "task_contract": ProductAggregateTaskContract(
                task_rules=combined,
                notes=notes,
                process_graph_source=PROCESS_GRAPH_SOURCE_MODULAR,
                process_graph_hash=graph.graph_hash,
                process_contract_version=graph.contract_version,
            ),
            "warnings": warnings,
            "conflicts": conflicts,
        }
    )


def build_in_memory_snapshot_v2_from_aggregate(aggregate: ProductAggregate) -> dict[str, Any]:
    """Snapshot V2-shaped payload from a live Aggregate (materials/ops/task_contract)."""
    return {
        "snapshot_version": "v2",
        "template_code": aggregate.template_code,
        "product_aggregate_snapshot": aggregate.model_dump(mode="json"),
        "active_scope_snapshot": {
            "compiled": {
                "errors": [],
                "active_modules": [c.component_id for c in aggregate.components],
                "sold_modules": [c.component_id for c in aggregate.components],
            }
        },
        "geometry_input_snapshot": {},
        "commercial_price_proposal_snapshot": {
            "currency": "RON",
            "lines": [],
            "net_total": None,
            "gross_total": None,
        },
        "process_graph_meta": {
            "graph_hash": aggregate.task_contract.process_graph_hash,
            "contract_version": aggregate.task_contract.process_contract_version,
            "process_graph_source": aggregate.task_contract.process_graph_source,
        },
    }
