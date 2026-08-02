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
from services.order_execution_snapshot_mapper import resolve_canonical_task_type
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


# Module ops are aggregate aliases of parent priced ops (DEC-003 / DEC-004).
# Keys normalized uppercase for lookup.
_MODULE_ALIAS_TO_PARENT: dict[str, str] = {
    "RETURN_PROFILE_FACE_BONDING": "return_face_bonding",
    "RETURN_PROFILE_MACHINE_FORMING": "side_forming",
    "PAINTING": "painting",
}


def _alias_parent_for(name_or_priced: str) -> str | None:
    """Return parent priced op when *name_or_priced* is a module alias token.

    Canonical parents (e.g. ``painting``) must not resolve as aliases of themselves
    just because ``painting``.upper() == ``PAINTING``.
    """
    raw = str(name_or_priced or "").strip()
    if not raw:
        return None
    # Alias tokens are the uppercase module forms (or exact map keys).
    if raw in _MODULE_ALIAS_TO_PARENT:
        return _MODULE_ALIAS_TO_PARENT[raw]
    if raw.upper() == raw and raw in _MODULE_ALIAS_TO_PARENT:
        return _MODULE_ALIAS_TO_PARENT[raw]
    # Lower/mixed-case module names like return_profile_face_bonding.
    upper = raw.upper()
    parent = _MODULE_ALIAS_TO_PARENT.get(upper)
    if parent is None:
        return None
    if raw.lower() == parent.lower():
        return None
    return parent


def _collapse_operational_alias_rules(
    rules: list[ProductAggregateTaskRule],
) -> list[ProductAggregateTaskRule]:
    """Drop module RETURN/PAINTING aliases when the parent priced op already exists.

    Distinct process codes that share a priced_operation mapping (e.g. multiple
    electrical_letters steps) are NOT collapsed — they are different work.
    """
    parent_ops = {
        str(r.priced_operation or "").strip().lower()
        for r in rules
        if (r.priced_operation or "").strip()
        and str(r.priced_operation).strip() not in _MODULE_ALIAS_TO_PARENT
        and str(r.task_name or "").strip() not in _MODULE_ALIAS_TO_PARENT
    }
    collapsed: list[ProductAggregateTaskRule] = []
    for rule in rules:
        name = str(rule.task_name or "").strip()
        priced = str(rule.priced_operation or "").strip()
        alias_parent = _alias_parent_for(name) or _alias_parent_for(priced)
        if alias_parent and alias_parent.lower() in parent_ops:
            # Alias only — do not emit a second operational task for the same work.
            continue
        if alias_parent and alias_parent.lower() not in parent_ops:
            # Promote alias to parent identity when parent rule absent.
            rule = rule.model_copy(
                update={
                    "task_name": alias_parent,
                    "priced_operation": alias_parent,
                    "trigger_condition": (
                        f"{rule.trigger_condition}|alias_promoted_from={name or priced}"
                        if rule.trigger_condition
                        else f"alias_promoted_from={name or priced}"
                    ),
                }
            )
        collapsed.append(rule)
    return collapsed


def _rules_from_resolved(graph: ResolvedProductProcessGraph) -> list[ProductAggregateTaskRule]:
    raw = resolved_graph_to_aggregate_task_rules(graph)
    rules: list[ProductAggregateTaskRule] = []
    for row in raw:
        priced = row.get("priced_operation")
        priced_s = str(priced).strip() if priced else ""
        canonical = (
            resolve_canonical_task_type(process_id=priced_s, legacy_type="")
            if priced_s
            else None
        )
        rules.append(
            ProductAggregateTaskRule(
                task_name=str(row.get("task_name") or ""),
                # Prefer EP-canonical type from priced op; avoid bare "process".
                task_type=canonical or row.get("task_type"),
                priced_operation=priced_s or None,
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
    product_definition_canonical_values: dict[str, Any] | None = None,
) -> ProductAggregate:
    """
    Live Aggregate bridge: replace letters task_rules with resolver DAG when template
    has modular process contract. Preserves linked_segment logo rules. Never concatenates
    dossier + resolver. Zero DB writes.

    Typed ProductDefinition canonical_values win over finish_setup (adapter precedence).
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

    inp, map_warnings, map_blockers, config_meta = build_resolve_input_from_active_config(
        template_code=aggregate.template_code,
        workspace_payload=workspace_payload,
        geometry_inputs=geometry_inputs,
        product_definition_canonical_values=product_definition_canonical_values,
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
        # Keep dossier letters rules (pre-bridge) instead of clearing to [].
        # Empty task_rules caused blocked_missing_task_rules on EP V2 preview.
        dossier_letters = [
            r
            for r in aggregate.task_contract.task_rules
            if not str(r.trigger_condition or "").startswith("linked_segment:")
        ]
        dossier_letters = _collapse_operational_alias_rules(dossier_letters)
        fallback = list(dossier_letters) + list(logo_rules)
        logger.info(
            "process_bridge_blocked template=%s blockers=%s dossier_fallback_rules=%s",
            aggregate.template_code,
            [b.code for b in graph.blockers] + map_blockers,
            len(dossier_letters),
        )
        notes = [
            "process_graph_source=modular_resolver",
            "process_graph_status=blocked",
            f"contract_version={graph.contract_version}",
            f"graph_hash={graph.graph_hash}",
            "letters_task_rules_dossier_fallback_on_block",
            f"dossier_fallback_rule_count={len(dossier_letters)}",
            "logo linked_segment rules preserved",
        ]
        return aggregate.model_copy(
            update={
                "task_contract": ProductAggregateTaskContract(
                    task_rules=fallback,
                    notes=notes,
                    process_graph_source=PROCESS_GRAPH_SOURCE_MODULAR,
                    process_graph_hash=graph.graph_hash,
                    process_contract_version=graph.contract_version,
                ),
                "warnings": warnings,
                "conflicts": conflicts,
            }
        )

    modular_rules = _collapse_operational_alias_rules(_rules_from_resolved(graph))
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
        f"config_source={config_meta.get('config_source')}",
        f"support_source={config_meta.get('support_source')}",
        f"cable_source={config_meta.get('cable_source')}",
        f"mains_cable_length_m={graph.config_echo.get('mains_cable_length_m')}",
        f"power_supply_service_corner={graph.config_echo.get('power_supply_service_corner')}",
        f"service_screw_finish={graph.config_echo.get('screw_finish')}",
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

    # Replace prior bridge info on re-apply (workspace compose / explicit PD overlay).
    warnings = [w for w in warnings if w.code != "PROCESS_GRAPH_MODULAR_RESOLVER"]
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
                **config_meta,
                "mains_cable_length_m": graph.config_echo.get("mains_cable_length_m"),
                "power_supply_service_corner": graph.config_echo.get("power_supply_service_corner"),
                "service_screw_finish": graph.config_echo.get("screw_finish"),
                "support_type": graph.config_echo.get("support_type"),
                "cant_finish": graph.config_echo.get("cant_finish"),
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
