"""
Owner read-only proof composer for Litere volumetrice.

Assembles existing authorities only:
  Intake workspace payload
  → ProductDefinition preview
  → ProductAggregate (modular process bridge → existing task_rules)
  → live materials / wire_supply
  → in-memory Snapshot V2 → Build 4C execution preview

Zero DB writes. Zero task materialization. Resolver is not a task engine.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.owner_readonly_volumetric_proof import (
    OwnerProofExecutionPreview4C,
    OwnerProofIntakeSelection,
    OwnerProofLiveMaterials,
    OwnerProofProcessGraph,
    OwnerProofProcessNode,
    OwnerProofProductDefinitionSlice,
    OwnerProofTaskRulesProjection,
    OwnerProofVerificationPath,
    OwnerProofWireSupplyLine,
    OwnerReadonlyVolumetricProof,
)
from services.execution_preview_from_frozen_graph_service import (
    build_execution_preview_from_frozen_snapshot,
)
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_process_aggregate_bridge import build_in_memory_snapshot_v2_from_aggregate
from services.product_process_resolve_input_adapter import PROCESS_GRAPH_SOURCE_MODULAR
from services.template_architecture_scope import (
    VOLUMETRIC_V2_TEMPLATE_CODE,
    normalize_template_code,
    resolve_template_identity,
)

logger = logging.getLogger(__name__)

PROOF_CANONICAL_KEYS = (
    "return_finish_type",
    "mounting_system",
    "mounting_solution",
    "mains_cable_length_m",
    "power_supply_service_corner",
    "service_screw_finish",
    "mounting_template_enabled",
    "lighting_system_type",
    "support_type",
)


def _parse_payload(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _finish(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("finish_setup")
    return raw if isinstance(raw, dict) else {}


def _selection_from_finish(finish: dict[str, Any]) -> OwnerProofIntakeSelection:
    sol = finish.get("mounting_solution")
    sol_code = None
    if isinstance(sol, dict):
        sol_code = sol.get("template_code")
    return OwnerProofIntakeSelection(
        mounting_system=finish.get("mounting_system"),
        mounting_solution_template=str(sol_code) if sol_code else None,
        return_finish_type=finish.get("return_finish_type"),
        mains_cable_length_m=(
            float(finish["mains_cable_length_m"])
            if finish.get("mains_cable_length_m") is not None
            else None
        ),
        power_supply_service_corner=finish.get("power_supply_service_corner"),
        service_screw_finish=finish.get("service_screw_finish"),
        mounting_template_enabled=finish.get("mounting_template_enabled"),
        lighting_system_type=finish.get("lighting_system_type"),
        support_source="finish_setup",
    )


def _canonical_slice(values: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in PROOF_CANONICAL_KEYS:
        if key in values and values[key] is not None:
            out[key] = values[key]
    return out


async def build_owner_readonly_volumetric_proof(
    db: AsyncSession,
    *,
    template_code: str,
    workspace_id: str,
) -> OwnerReadonlyVolumetricProof | None:
    identity = resolve_template_identity(template_code)
    canonical = identity.canonical_template_code or template_code
    if normalize_template_code(canonical) != normalize_template_code(VOLUMETRIC_V2_TEMPLATE_CODE):
        return None

    result = await db.execute(
        select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id).limit(1)
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None
    if record.template_code and normalize_template_code(record.template_code) != normalize_template_code(
        canonical
    ):
        # Allow alias TPL-VOLUMETRIC-LETTERS ↔ v2
        if normalize_template_code(resolve_template_identity(record.template_code).canonical_template_code) != normalize_template_code(
            canonical
        ):
            return None

    payload = _parse_payload(record.payload_json)
    finish = _finish(payload)
    guards: list[str] = []
    notes: list[str] = [
        "Resolver compiles process truth into existing task_rules only.",
        "Build 4C preview consumes in-memory Snapshot V2 — no ExecutionPlan write.",
        "Live materials wire_supply uses typed mains_cable_length_m when present.",
    ]

    pd = await ProductDefinitionBuilderService(db).build_preview(
        canonical, workspace_id=workspace_id
    )
    if pd is None:
        return None
    cv = dict(pd.canonical_values or {})
    pd_slice = OwnerProofProductDefinitionSlice(
        template_code=pd.template_code,
        canonical_values=_canonical_slice(cv),
        readiness_status=getattr(pd.validation, "readiness_status", None),
        missing_required_fields=list(getattr(pd.validation, "missing_required_fields", []) or []),
    )

    aggregate = await ProductAggregateService(db).build_for_workspace(canonical, workspace_id)
    if aggregate is None:
        return None

    tc = aggregate.task_contract
    processes = [
        OwnerProofProcessNode(
            process_code=r.task_name,
            depends_on_process_ids=list(r.depends_on_process_ids or []),
            sequence=r.sequence,
            component_ref=r.mini_module_code or r.process_code,
        )
        for r in tc.task_rules
    ]
    edge_count = sum(len(p.depends_on_process_ids) for p in processes)
    process_graph = OwnerProofProcessGraph(
        process_graph_source=tc.process_graph_source,
        process_graph_hash=tc.process_graph_hash,
        process_contract_version=tc.process_contract_version,
        process_count=len(processes),
        edge_count=edge_count,
        processes=processes,
        notes=list(tc.notes or []),
    )
    if tc.process_graph_source != PROCESS_GRAPH_SOURCE_MODULAR:
        guards.append("process_graph_source_not_modular_resolver")

    task_proj = OwnerProofTaskRulesProjection(
        process_graph_source=tc.process_graph_source,
        rule_count=len(processes),
        task_names=[p.process_code for p in processes],
        depends_on_preserved=any(p.depends_on_process_ids for p in processes),
        notes=[
            "task_rules come from ProductAggregate.task_contract (existing contract).",
            "No parallel task graph was created for this proof.",
        ],
    )

    live = OwnerProofLiveMaterials()
    try:
        breakdown = build_intake_v4_material_breakdown(workspace_id, payload)
        live.consumable_keys = [r.material_key for r in breakdown.consumable_rows]
        live.warning_codes = [w.code for w in breakdown.warnings]
        live.cable_channel_commercial_guarded = (
            "CABLE_CHANNEL_COMMERCIAL_FORMULA_GUARDED" in live.warning_codes
        )
        for row in breakdown.consumable_rows:
            if row.material_key == "wire_supply_myyup_2x15":
                live.wire_supply = OwnerProofWireSupplyLine(
                    present=True,
                    material_code=row.material_code,
                    material_key=row.material_key,
                    quantity=row.quantity,
                    unit=row.unit,
                    quantity_source=row.quantity_source,
                    quantity_basis=row.quantity_basis,
                    unit_price=row.unit_price,
                    estimated_cost=row.estimated_cost,
                    price_source=row.price_source,
                )
                break
        if live.cable_channel_commercial_guarded:
            guards.append("cable_channel_commercial_formula_guarded")
    except Exception as exc:  # noqa: BLE001 — proof must surface materials gap, not crash
        guards.append(f"live_materials_unavailable:{type(exc).__name__}")
        notes.append(f"live_materials_error={exc}")

    exec_preview = OwnerProofExecutionPreview4C()
    try:
        snap = build_in_memory_snapshot_v2_from_aggregate(aggregate)
        preview = build_execution_preview_from_frozen_snapshot(snap)
        process_edges = [
            e for e in preview.dependency_graph.edges if e.provenance == "process_depends_on"
        ]
        seq_edges = [
            e for e in preview.dependency_graph.edges if e.provenance == "sequence_order"
        ]
        samples: list[dict[str, Any]] = []
        for cand in preview.task_candidates[:12]:
            samples.append(
                {
                    "task_name": cand.task_name,
                    "preview_candidate_key": cand.preview_candidate_key,
                    "depends_on": list(cand.dependencies or [])[:8],
                    "provenance": cand.provenance,
                }
            )
        exec_preview = OwnerProofExecutionPreview4C(
            present=True,
            no_write=bool(preview.safety.no_write),
            candidate_count=len(preview.task_candidates),
            edge_count=len(preview.dependency_graph.edges),
            process_depends_on_edges=len(process_edges),
            sequence_fallback_edges=len(seq_edges),
            sample_dependencies=samples,
            blockers=list(preview.blockers or []),
        )
        if not preview.safety.no_write:
            guards.append("execution_preview_no_write_false")
    except Exception as exc:  # noqa: BLE001
        guards.append(f"execution_preview_unavailable:{type(exc).__name__}")
        notes.append(f"execution_preview_error={exc}")

    selection = _selection_from_finish(finish)
    # Prefer PD typed cable when present
    if "mains_cable_length_m" in pd_slice.canonical_values:
        try:
            selection.mains_cable_length_m = float(pd_slice.canonical_values["mains_cable_length_m"])
            selection.support_source = "product_definition_canonical_values"
        except (TypeError, ValueError):
            pass

    chain_ok = (
        tc.process_graph_source == PROCESS_GRAPH_SOURCE_MODULAR
        and task_proj.rule_count > 0
        and exec_preview.present
        and exec_preview.no_write
        and "live_materials_unavailable" not in "".join(guards)
    )

    verification = OwnerProofVerificationPath(
        intake_ui=f"http://127.0.0.1:3000/intake-v6/{workspace_id}/operator",
        product_system_ui=(
            f"http://127.0.0.1:3000/product-system/products/{canonical}"
            f"?workspace_id={workspace_id}&owner_proof=1"
        ),
        proof_api=(
            f"/api/v1/product-system/owner-readonly-proof/{canonical}"
            f"?workspace_id={workspace_id}"
        ),
        aggregate_api=f"/api/v1/product-system/aggregate/{canonical}?workspace_id={workspace_id}",
        logical_list_api=f"/api/v1/intake-v6/workspaces/{workspace_id}/logical-list-read-model",
        execution_preview_api="/api/v1/execution/plan-v2/preview-from-frozen-snapshot",
    )

    logger.info(
        "owner_readonly_proof template=%s workspace=%s processes=%s wire_qty=%s chain_ok=%s",
        canonical,
        workspace_id,
        process_graph.process_count,
        live.wire_supply.quantity,
        chain_ok,
    )

    return OwnerReadonlyVolumetricProof(
        template_code=canonical,
        workspace_id=workspace_id,
        intake_selection=selection,
        product_definition=pd_slice,
        process_graph=process_graph,
        task_rules_projection=task_proj,
        live_materials=live,
        execution_preview_4c=exec_preview,
        guards=guards,
        verification_path=verification,
        chain_ok=chain_ok,
        notes=notes,
    )
