"""Bridge ResolvedProductProcessGraph → Aggregate task_contract / in-memory Snapshot V2.

Read-only helpers. No DB writes. No CPP. No Intake mutation.
"""

from __future__ import annotations

from typing import Any

from schemas.product_process_contract import (
    ProductProcessResolveInput,
    ResolvedProductProcessGraph,
)
from services.product_process_resolver_service import (
    resolve_product_process_graph,
    resolved_graph_to_aggregate_task_rules,
)


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
