"""Build 4C — Execution preview from frozen modular graph only.

Read-only. No live Product System rebuild. No CPP recompute. No ExecutionPlan persist.
No task materialization. Task candidates ⊆ frozen task_contract.task_rules.
"""

from __future__ import annotations

import re
from typing import Any

from schemas.execution_preview_from_frozen import (
    EXECUTION_PREVIEW_FROM_FROZEN_VERSION,
    SOURCE_AUTHORITY_FROZEN_SNAPSHOT_V2,
    ExecutionPreviewCandidate,
    ExecutionPreviewCommercialReference,
    ExecutionPreviewDependencyEdge,
    ExecutionPreviewDependencyGraph,
    ExecutionPreviewFromFrozen,
    ExecutionPreviewMaterialRequirement,
    ExecutionPreviewSafety,
    ExecutionPreviewSource,
    PreviewReadiness,
)
from schemas.frozen_modular_graph import FrozenModularGraphPreview
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from services.frozen_modular_graph_service import (
    build_frozen_modular_graph_from_v2,
    classify_order14_compatibility,
    fingerprint_hash,
)

_ADHESIVE_RE = re.compile(r"(adeziv|adhesive)", re.IGNORECASE)
_BONDING_RE = re.compile(r"(bonding|return_face_bonding)", re.IGNORECASE)


def _as_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return None


def _snapshot_scope_errors(snapshot: Any) -> list[str]:
    data = _as_dict(snapshot) or {}
    active = _as_dict(data.get("active_scope_snapshot")) or {}
    compiled = _as_dict(active.get("compiled")) or {}
    errors = compiled.get("errors") or []
    return [str(e) for e in errors if e]


def _aggregate_materials(
    snapshot: Any,
    *,
    excluded_materials: list[str] | None = None,
    inactive_modules: list[str] | None = None,
) -> list[dict[str, Any]]:
    data = _as_dict(snapshot) or {}
    aggregate = _as_dict(data.get("product_aggregate_snapshot")) or {}
    excluded = {str(x).strip().upper() for x in (excluded_materials or []) if str(x).strip()}
    excluded |= {str(x).strip().lower() for x in (excluded_materials or []) if str(x).strip()}
    inactive = {str(x).strip() for x in (inactive_modules or []) if str(x).strip()}
    rows: list[dict[str, Any]] = []
    for mat in aggregate.get("materials") or []:
        row = _as_dict(mat) or {}
        code = row.get("material_code") or row.get("code")
        if not code:
            continue
        code_s = str(code)
        if code_s.upper() in excluded or code_s.lower() in excluded:
            continue
        owner = row.get("mini_module_code")
        if owner and str(owner) in inactive:
            continue
        rows.append(
            {
                "material_code": code_s,
                "unit": row.get("unit"),
                "owner_module": owner,
                "interface_provenance": bool(_ADHESIVE_RE.search(code_s)),
            }
        )
    return rows


def _project_candidates(graph: FrozenModularGraphPreview) -> list[ExecutionPreviewCandidate]:
    """Project task_rules-only candidates from frozen graph (no all-operations invent)."""
    frozen_hash = graph.hashes.frozen_graph
    out: list[ExecutionPreviewCandidate] = []
    for idx, cand in enumerate(graph.execution.task_candidates):
        seq = cand.sequence if cand.sequence is not None else idx
        key_parts = [
            frozen_hash or "noghash",
            str(cand.task_name),
            str(cand.priced_operation or ""),
            str(cand.owner_module or ""),
            str(seq),
        ]
        preview_key = "pv|" + "|".join(key_parts)
        # Material codes owned by same module (hints only — quantities stay frozen elsewhere).
        mat_reqs = [
            m
            for m in graph.execution.material_codes
            if cand.owner_module
            and (
                (cand.owner_module in m.lower())
                or (
                    cand.interface_owner
                    and _ADHESIVE_RE.search(m)
                    and cand.interface_owner == "interface_face_cant"
                )
            )
        ]
        # Interface bonding gets adhesive materials when present.
        if cand.interface_owner == "interface_face_cant" or (
            cand.priced_operation and _BONDING_RE.search(cand.priced_operation)
        ):
            for m in graph.execution.material_codes:
                if _ADHESIVE_RE.search(m) and m not in mat_reqs:
                    mat_reqs.append(m)

        out.append(
            ExecutionPreviewCandidate(
                preview_candidate_key=preview_key,
                source_operation_code=cand.priced_operation,
                task_rule_code=cand.task_name,
                task_name=cand.task_name,
                owner_module=cand.owner_module,
                interface_owner=cand.interface_owner,
                dependencies=[],  # filled after ordering
                role_hints=[],
                machine_hints=[],
                material_requirements=sorted(set(mat_reqs)),
                readiness="projected",
                provenance=cand.provenance,
                sequence=seq,
            )
        )
    out.sort(key=lambda c: (c.sequence if c.sequence is not None else 10_000, c.task_name))
    return out


def _build_dependency_graph(
    candidates: list[ExecutionPreviewCandidate],
) -> ExecutionPreviewDependencyGraph:
    """Linear sequence dependencies — no invented edges beyond frozen ordinal semantics."""
    edges: list[ExecutionPreviewDependencyEdge] = []
    keys = [c.preview_candidate_key for c in candidates]
    for i in range(1, len(candidates)):
        prev = candidates[i - 1]
        cur = candidates[i]
        edges.append(
            ExecutionPreviewDependencyEdge(
                from_candidate_key=prev.preview_candidate_key,
                to_candidate_key=cur.preview_candidate_key,
                provenance="sequence_order",
            )
        )
        cur.dependencies = [prev.preview_candidate_key]

    # Cycle detection (sequence chain cannot cycle unless duplicate keys).
    seen: set[str] = set()
    cycle = False
    for key in keys:
        if key in seen:
            cycle = True
            break
        seen.add(key)
    if len(keys) != len(set(keys)):
        cycle = True

    return ExecutionPreviewDependencyGraph(
        edges=edges,
        topological_order=[] if cycle else keys,
        cycle_detected=cycle,
        unresolved=[],
    )


def _material_requirements(
    snapshot: Any,
    candidates: list[ExecutionPreviewCandidate],
    *,
    graph: FrozenModularGraphPreview,
) -> list[ExecutionPreviewMaterialRequirement]:
    mats = _aggregate_materials(
        snapshot,
        excluded_materials=list(graph.scope.excluded_materials),
        inactive_modules=list(graph.scope.inactive_modules),
    )
    # Prefer intersection with frozen graph technical material list (already Aggregate-sourced).
    allowed = set(graph.execution.material_codes)
    if allowed:
        mats = [m for m in mats if m["material_code"] in allowed]
    by_code: dict[str, ExecutionPreviewMaterialRequirement] = {}
    for row in mats:
        code = row["material_code"]
        attached = [
            c.preview_candidate_key
            for c in candidates
            if code in c.material_requirements
            or (
                row.get("owner_module")
                and c.owner_module
                and row["owner_module"] == c.owner_module
            )
        ]
        by_code[code] = ExecutionPreviewMaterialRequirement(
            material_code=code,
            unit=row.get("unit"),
            owner_module=row.get("owner_module"),
            interface_provenance=bool(row.get("interface_provenance")),
            attached_candidate_keys=attached,
        )
    return sorted(by_code.values(), key=lambda m: m.material_code)


def _preview_fingerprint(
    graph: FrozenModularGraphPreview,
    candidates: list[ExecutionPreviewCandidate],
    deps: ExecutionPreviewDependencyGraph,
    materials: list[ExecutionPreviewMaterialRequirement],
    blockers: list[str],
) -> str:
    payload = {
        "frozen_graph_hash": graph.hashes.frozen_graph,
        "candidate_keys": [c.preview_candidate_key for c in candidates],
        "dependency_edges": [
            (e.from_candidate_key, e.to_candidate_key) for e in deps.edges
        ],
        "material_codes": [m.material_code for m in materials],
        "blocker_codes": sorted(blockers),
        "compatibility_mode": graph.compatibility.mode,
        "scenario": graph.compatibility.scenario,
    }
    return fingerprint_hash(payload)


def _classify_readiness(
    *,
    graph: FrozenModularGraphPreview,
    scope_errors: list[str],
    cycle: bool,
    has_v1_only: bool,
) -> tuple[PreviewReadiness, list[str], list[str]]:
    blockers: list[str] = list(graph.blockers)
    warnings: list[str] = list(graph.warnings)

    if has_v1_only:
        return "unsupported_v1", ["unsupported_v1_snapshot_line_items"], warnings

    if scope_errors:
        # Build 4A.1 / 4C law: no silent full-product fail-open.
        blockers.extend([f"scope_error:{e}" for e in scope_errors])
        return "scope_invalid", blockers, warnings

    failed = [a for a in graph.assertions if not a.passed]
    if failed:
        blockers.extend([f"assertion_failed:{a.code}" for a in failed])
        # FACE+CANT missing technical adhesive is blocked, not silent ready.
        critical = {
            "adhesive_exactly_once",
            "bonding_exactly_once",
            "interface_active",
            "no_adhesive",
            "no_bonding",
        }
        if any(a.code in critical for a in failed):
            return "blocked", blockers, warnings
        return "degraded", blockers, warnings

    if cycle:
        blockers.append("dependency_cycle")
        return "blocked", blockers, warnings

    if graph.compatibility.mode in ("legacy_full_product",) or graph.compatibility.scenario == "legacy_full_product":
        return "legacy_compatible", blockers, warnings

    if not graph.hashes.frozen_graph:
        return "checksum_invalid", blockers + ["missing_frozen_graph_hash"], warnings

    if graph.execution.candidate_count == 0 and graph.compatibility.scenario not in (
        "unknown",
    ):
        warnings.append("no_task_candidates")
        return "degraded", blockers, warnings

    return "ready", blockers, warnings


def build_execution_preview_from_frozen_snapshot(
    snapshot: QuoteSnapshotV2 | OrderSnapshotV2 | dict[str, Any],
    *,
    order_id: int | None = None,
    source_kind: str | None = None,
) -> ExecutionPreviewFromFrozen:
    """
    Pure in-memory projection. Never touches DB.

    Authority: Quote/Order Snapshot V2 → FrozenModularGraphPreview → candidates.
    Does not call ProductDefinition/Aggregate/CPP builders.
    """
    raw = _as_dict(snapshot) or {}
    # V1-only payload: no Aggregate / no V2 package.
    has_v1_only = (
        raw.get("product_aggregate_snapshot") is None
        and raw.get("snapshot_line_items") is not None
        and raw.get("snapshot_v2_json") is None
        and not raw.get("product_definition_snapshot")
    )

    graph = build_frozen_modular_graph_from_v2(snapshot, source_kind=source_kind)
    scope_errors = _snapshot_scope_errors(snapshot)

    candidates = _project_candidates(graph)
    deps = _build_dependency_graph(candidates)
    materials = _material_requirements(snapshot, candidates, graph=graph)

    readiness, blockers, warnings = _classify_readiness(
        graph=graph,
        scope_errors=scope_errors,
        cycle=deps.cycle_detected,
        has_v1_only=has_v1_only,
    )

    # When scope invalid / unsupported, do not invent candidates from live paths —
    # clear projection surfaces but keep frozen graph for diagnostics.
    if readiness in ("scope_invalid", "unsupported_v1", "checksum_invalid"):
        candidates = []
        deps = ExecutionPreviewDependencyGraph(cycle_detected=False)
        materials = []

    fp = _preview_fingerprint(graph, candidates, deps, materials, blockers)

    oid = order_id
    if oid is None and isinstance(snapshot, OrderSnapshotV2):
        oid = snapshot.order_id
    elif oid is None and isinstance(raw.get("order_id"), int):
        oid = raw["order_id"]

    return ExecutionPreviewFromFrozen(
        readiness=readiness,
        source=ExecutionPreviewSource(
            snapshot_kind=graph.source_kind,
            snapshot_version=graph.identity.snapshot_version,
            frozen_graph_hash=graph.hashes.frozen_graph,
            order_id=oid,
            legacy_mode=graph.scope.use_legacy_full_product
            or graph.compatibility.scenario == "legacy_full_product",
            compatibility_adapter=EXECUTION_PREVIEW_FROM_FROZEN_VERSION,
            source_authority=SOURCE_AUTHORITY_FROZEN_SNAPSHOT_V2,
        ),
        frozen_graph=graph,
        hashes=graph.hashes,
        task_candidates=candidates,
        dependency_graph=deps,
        material_requirements=materials,
        commercial_reference=ExecutionPreviewCommercialReference(
            cpp_fingerprint=list(graph.commercial.line_fingerprint),
            cpp_line_count=graph.commercial.cpp_line_count,
            net_total=graph.commercial.net_total,
            gross_total=graph.commercial.gross_total,
            no_reprice=True,
        ),
        assertions=list(graph.assertions),
        blockers=blockers,
        warnings=warnings,
        preview_fingerprint=fp,
        safety=ExecutionPreviewSafety(),
        message=(
            "Execution preview projected from frozen modular graph only — "
            "no live recompile, no persistence, no materialization."
        ),
    )


def _minimal_shell_graph(template_code: str = "SHELL") -> FrozenModularGraphPreview:
    return build_frozen_modular_graph_from_v2(
        {
            "template_code": template_code,
            "commercial_price_proposal_snapshot": {
                "template_code": template_code,
                "commercial_price_lines": [],
            },
            "estimated_internal_cost_snapshot": {"template_code": template_code},
        },
        source_kind="unknown",
    )


async def build_execution_preview_from_frozen_order(
    db: Any,
    order_id: int,
) -> ExecutionPreviewFromFrozen:
    """Read orders.snapshot_v2_json only (one SELECT). No plan/task writes."""
    from models.orders import Orders

    order = await db.get(Orders, order_id)
    if order is None:
        shell = _minimal_shell_graph("MISSING")
        return ExecutionPreviewFromFrozen(
            readiness="blocked",
            source=ExecutionPreviewSource(order_id=order_id, snapshot_kind="missing"),
            frozen_graph=shell,
            hashes=shell.hashes,
            blockers=["order_not_found"],
            message="Order not found",
            safety=ExecutionPreviewSafety(),
        )

    raw = getattr(order, "snapshot_v2_json", None)
    if not raw:
        compat = (
            classify_order14_compatibility(
                has_order=True, has_execution_plan=False, has_v2_json=False
            )
            if order_id == 14
            else {"mode": "legacy_v1_line_items"}
        )
        shell = _minimal_shell_graph("LEGACY")
        return ExecutionPreviewFromFrozen(
            readiness="unsupported_v1" if order_id != 14 else "legacy_compatible",
            source=ExecutionPreviewSource(
                snapshot_kind="legacy_v1_or_mixed",
                order_id=order_id,
                legacy_mode=True,
                source_authority="compatibility_read_only",
            ),
            frozen_graph=shell,
            hashes=shell.hashes,
            blockers=["order_snapshot_v2_required"],
            warnings=[str(compat)],
            message=(
                "Build 4C requires OrderSnapshotV2. V1 line items are not reinterpreted."
            ),
            safety=ExecutionPreviewSafety(),
        )

    try:
        snapshot = (
            OrderSnapshotV2.model_validate_json(raw)
            if isinstance(raw, str)
            else OrderSnapshotV2.model_validate(raw)
        )
    except Exception as exc:
        shell = _minimal_shell_graph("INVALID")
        return ExecutionPreviewFromFrozen(
            readiness="checksum_invalid",
            source=ExecutionPreviewSource(order_id=order_id, snapshot_kind="corrupt"),
            frozen_graph=shell,
            hashes=shell.hashes,
            blockers=["order_snapshot_v2_invalid", str(exc)],
            message="OrderSnapshotV2 JSON invalid",
            safety=ExecutionPreviewSafety(),
        )

    return build_execution_preview_from_frozen_snapshot(
        snapshot, order_id=order_id, source_kind="order_snapshot_v2"
    )
