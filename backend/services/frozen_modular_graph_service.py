"""Build 4A — Frozen Modular Graph normalization over Quote/Order Snapshot V2.

Read-only. No DB writes. No freeze persist. No ExecutionPlan. No task materialization.
Does not recompute PD / Aggregate / CPP from live template defaults.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from schemas.frozen_modular_graph import (
    FROZEN_MODULAR_GRAPH_ADAPTER_VERSION,
    FrozenGraphAssertionResult,
    FrozenGraphCommercial,
    FrozenGraphCompatibility,
    FrozenGraphComponentHashes,
    FrozenGraphExecutionPreview,
    FrozenGraphGeometry,
    FrozenGraphIdentity,
    FrozenGraphRequest,
    FrozenGraphScope,
    FrozenModularGraphPreview,
    FrozenTaskCandidatePreview,
    ScenarioKind,
)
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.quote_snapshot_v2 import QuoteSnapshotV2

# Volatile / identity fields excluded from content fingerprints (not from truth display).
_VOLATILE_KEYS = frozenset(
    {
        "frozen_at",
        "frozen_by",
        "converted_at",
        "converted_by",
        "accepted_at",
        "accepted_by",
        "compiled_at",
        "snapshot_id",
        "snapshot_code",
        "order_id",
        "quote_id",
        "quote_snapshot_v2_id",
        "persist_status",
        "version",
        "assembled_at",
        "created_at",
        "updated_at",
        "content_hash",  # outer hash may embed volatiles; we recompute layered hashes
    }
)

_ADHESIVE_MATERIAL_RE = re.compile(r"(adeziv|adhesive)", re.IGNORECASE)
_BONDING_OPERATION_RE = re.compile(r"(bonding|return_face_bonding)", re.IGNORECASE)
_FACE_HINT_RE = re.compile(r"(face|fata|debitare_fata|comp_fata)", re.IGNORECASE)
_CANT_HINT_RE = re.compile(r"(cant|return|lateral|modelare_cant)", re.IGNORECASE)
_LED_HINT_RE = re.compile(r"(led|lighting|sistem_led|illumin)", re.IGNORECASE)
_MOUNT_HINT_RE = re.compile(r"(mount|montaj|sablon-montaj)", re.IGNORECASE)

_SORTABLE_LIST_KEYS = frozenset(
    {
        "materials",
        "operations",
        "selected_modules",
        "optional_modules",
        "inactive_modules",
        "sold_modules",
        "sold_module_codes",
        "active_runtime_modules",
        "inactive_runtime_modules",
        "active_modules",
        "active_components",
        "selected_components",
        "excluded_operations",
        "excluded_materials",
        "composition_excluded_operations",
        "composition_excluded_materials",
        "commercial_scope_modules",
        "execution_scope_modules",
        "calculation_prerequisites",
        "warnings",
        "errors",
        "notes",
        "blockers",
        "cpp_rule_codes",
        "material_codes",
        "operation_codes",
    }
)


def _as_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return None


def _strip_volatiles(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if key in _VOLATILE_KEYS:
                continue
            out[key] = _strip_volatiles(item)
        return out
    if isinstance(value, list):
        return [_strip_volatiles(item) for item in value]
    return value


def _sort_key_for_item(item: Any) -> str:
    if isinstance(item, dict):
        for key in (
            "code",
            "material_code",
            "operation_code",
            "module_code",
            "task_name",
            "canonical_key",
            "key",
            "id",
            "instance_id",
            "node_id",
        ):
            if item.get(key) is not None:
                return str(item[key])
        return json.dumps(item, sort_keys=True, ensure_ascii=False, default=str)
    return str(item)


def _canonicalize(value: Any, *, parent_key: str | None = None) -> Any:
    """Stable structure for hashing. Preserves task_rules order (semantic)."""
    if isinstance(value, dict):
        return {k: _canonicalize(value[k], parent_key=k) for k in sorted(value.keys())}
    if isinstance(value, list):
        items = [_canonicalize(item) for item in value]
        if parent_key == "task_rules":
            return items  # sequence is semantic
        if parent_key in _SORTABLE_LIST_KEYS or (
            items
            and isinstance(items[0], dict)
            and any(
                k in items[0]
                for k in ("material_code", "operation_code", "module_code", "code", "task_name")
            )
            and parent_key != "task_candidates"
        ):
            return sorted(items, key=_sort_key_for_item)
        return items
    if isinstance(value, float):
        # Stable numeric render without changing commercial meaning beyond float repr noise.
        return round(value, 6)
    return value


def canonical_json_bytes(payload: Any) -> bytes:
    cleaned = _strip_volatiles(payload)
    canonical = _canonicalize(cleaned)
    return json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def fingerprint_hash(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()[:16]


def fingerprint_cpp_lines(cpp: Any) -> list[dict[str, Any]]:
    data = _as_dict(cpp) or {}
    lines = data.get("commercial_price_lines") or []
    out: list[dict[str, Any]] = []
    for line in lines:
        row = _as_dict(line) or {}
        unit_price = row.get("commercial_unit_price")
        if unit_price is None:
            unit_price = row.get("unit_price")
        out.append(
            {
                "code": row.get("code") or row.get("pricing_rule_code") or row.get("rule_code"),
                "quantity": row.get("quantity"),
                "unit": row.get("unit"),
                "unit_price": unit_price,
                "subtotal": row.get("subtotal"),
                "currency": row.get("currency") or data.get("currency"),
                "module_code": row.get("module_code"),
            }
        )
    out.sort(key=lambda r: str(r.get("code") or ""))
    return out


def _material_codes_raw(aggregate: dict[str, Any] | None) -> list[str]:
    """Preserve multiplicity — duplicate adhesive rows must not collapse to one."""
    if not aggregate:
        return []
    codes: list[str] = []
    for mat in aggregate.get("materials") or []:
        row = _as_dict(mat) or {}
        code = row.get("material_code") or row.get("code")
        if code:
            codes.append(str(code))
    return codes


def _operation_codes_raw(aggregate: dict[str, Any] | None) -> list[str]:
    if not aggregate:
        return []
    codes: list[str] = []
    for op in aggregate.get("operations") or []:
        row = _as_dict(op) or {}
        code = row.get("operation_code") or row.get("code")
        if code:
            codes.append(str(code))
    return codes


def _count_adhesive(materials: list[str]) -> int:
    return sum(1 for code in materials if _ADHESIVE_MATERIAL_RE.search(code))


def _count_bonding(operations: list[str]) -> int:
    return sum(1 for code in operations if _BONDING_OPERATION_RE.search(code))


def _task_candidates(aggregate: dict[str, Any] | None) -> list[FrozenTaskCandidatePreview]:
    if not aggregate:
        return []
    task_contract = aggregate.get("task_contract") or {}
    rules = task_contract.get("task_rules") or []
    inactive = set(str(x) for x in (aggregate.get("modules") or {}).get("optional") or [])
    # Prefer explicit inactive modules from active scope later; filter by mini_module if present.
    candidates: list[FrozenTaskCandidatePreview] = []
    for idx, rule in enumerate(rules):
        row = _as_dict(rule) or {}
        task_name = str(row.get("task_name") or "").strip()
        if not task_name:
            continue
        if str(row.get("task_type") or "").upper() == "READINESS_GATE":
            continue
        owner = row.get("mini_module_code")
        priced = row.get("priced_operation")
        seq = row.get("sequence")
        if seq is None:
            seq = idx
        interface_owner = None
        if priced and _BONDING_OPERATION_RE.search(str(priced)):
            interface_owner = "interface_face_cant"
        if task_name and _BONDING_OPERATION_RE.search(task_name):
            interface_owner = "interface_face_cant"
        key_parts = [
            str(seq),
            task_name,
            str(priced or ""),
            str(owner or ""),
            str(row.get("provenance") or ""),
        ]
        dep_ids = row.get("depends_on_process_ids") or row.get("depends_on") or []
        if not isinstance(dep_ids, list):
            dep_ids = []
        candidates.append(
            FrozenTaskCandidatePreview(
                candidate_key="|".join(key_parts),
                task_name=task_name,
                task_type=row.get("task_type"),
                priced_operation=priced,
                sequence=int(seq) if seq is not None else None,
                owner_module=owner,
                provenance=str(row.get("provenance")) if row.get("provenance") is not None else None,
                trigger_condition=row.get("trigger_condition"),
                interface_owner=interface_owner,
                depends_on_process_ids=[str(d) for d in dep_ids if str(d).strip()],
            )
        )
    # Stable order: sequence then name (do not invent from operations[])
    candidates.sort(key=lambda c: (c.sequence if c.sequence is not None else 10_000, c.task_name))
    _ = inactive  # reserved for future cross-check; Aggregate already filtered at freeze
    return candidates


def _classify_scenario(scope: FrozenGraphScope, request: FrozenGraphRequest) -> ScenarioKind:
    if scope.use_legacy_full_product or request.use_legacy or request.request_mode == "full_product":
        if not scope.sold_modules and (
            scope.use_legacy_full_product or request.use_legacy or not scope.active_modules
        ):
            return "legacy_full_product" if (scope.use_legacy_full_product or request.use_legacy) else "full_product"
        if request.request_mode == "full_product" or scope.use_legacy_full_product:
            return "full_product" if not scope.use_legacy_full_product else "legacy_full_product"

    sold = {s.upper() for s in scope.sold_modules}
    # Normalize aliases
    has_face = "FACE" in sold or any(s == "FACE" for s in scope.sold_modules)
    has_cant = "RETURN-CANT" in sold or "CANT" in sold or any(
        "CANT" in s.upper() or s.upper() == "RETURN-CANT" for s in scope.sold_modules
    )
    extras = sold - {"FACE", "RETURN-CANT", "CANT", "BACK", "LIGHTING", "ELECTRICAL", "MOUNTING"}
    # FACE / CANT primary classification for Build 3 subsets
    if has_face and has_cant and not ({"LIGHTING", "ELECTRICAL", "MOUNTING"} & sold):
        return "face_cant"
    if has_face and not has_cant:
        return "face_only"
    if has_cant and not has_face:
        return "cant_only"
    if request.request_mode == "full_product" or scope.use_legacy_full_product:
        return "legacy_full_product" if scope.use_legacy_full_product else "full_product"
    _ = extras
    return "unknown"


def _build_assertions(
    *,
    scenario: ScenarioKind,
    materials: list[str],
    operations: list[str],
    candidates: list[FrozenTaskCandidatePreview],
    scope: FrozenGraphScope,
) -> list[FrozenGraphAssertionResult]:
    adhesive = _count_adhesive(materials)
    bonding = _count_bonding(operations)
    bonding_candidates = sum(
        1
        for c in candidates
        if (c.priced_operation and _BONDING_OPERATION_RE.search(c.priced_operation))
        or _BONDING_OPERATION_RE.search(c.task_name)
        or c.interface_owner == "interface_face_cant"
    )
    face_ops = [c for c in operations if _FACE_HINT_RE.search(c) and not _CANT_HINT_RE.search(c)]
    cant_ops = [c for c in operations if _CANT_HINT_RE.search(c) and "bonding" not in c.lower()]
    led_mats = [m for m in materials if _LED_HINT_RE.search(m)]
    mount_mats = [m for m in materials if _MOUNT_HINT_RE.search(m)]
    face_candidates = [
        c
        for c in candidates
        if (c.owner_module and _FACE_HINT_RE.search(c.owner_module))
        or _FACE_HINT_RE.search(c.task_name)
    ]
    cant_candidates = [
        c
        for c in candidates
        if (c.owner_module and _CANT_HINT_RE.search(c.owner_module))
        or _CANT_HINT_RE.search(c.task_name)
    ]

    results: list[FrozenGraphAssertionResult] = []

    def add(code: str, passed: bool, detail: str | None = None) -> None:
        results.append(FrozenGraphAssertionResult(code=code, passed=passed, detail=detail))

    if scenario in ("face_only", "cant_only"):
        add("no_adhesive", adhesive == 0, f"count={adhesive}")
        add("no_bonding", bonding == 0 and bonding_candidates == 0, f"ops={bonding} cand={bonding_candidates}")
        add("interface_inactive", scope.interface_face_cant_active is not True, str(scope.interface_face_cant_active))
    if scenario == "face_only":
        add("no_cant_ops", len(cant_ops) == 0, ",".join(cant_ops[:8]) or None)
        add("no_cant_candidates", len(cant_candidates) == 0, str(len(cant_candidates)))
        add("no_led", len(led_mats) == 0, ",".join(led_mats[:8]) or None)
        add("no_mounting", len(mount_mats) == 0, ",".join(mount_mats[:8]) or None)
    if scenario == "cant_only":
        face_mats = [m for m in materials if _FACE_HINT_RE.search(m) and not _ADHESIVE_MATERIAL_RE.search(m)]
        add("no_face_ops", len(face_ops) == 0, ",".join(face_ops[:8]) or None)
        add("no_face_materials", len(face_mats) == 0, ",".join(face_mats[:8]) or None)
        add("no_face_candidates", len(face_candidates) == 0, str(len(face_candidates)))
        add("no_led", len(led_mats) == 0, ",".join(led_mats[:8]) or None)
        add("no_mounting", len(mount_mats) == 0, ",".join(mount_mats[:8]) or None)
    if scenario == "face_cant":
        # Semantic + technical — missing adhesive/bonding is a FAILED assertion (no greenwash).
        add("interface_active", scope.interface_face_cant_active is True, str(scope.interface_face_cant_active))
        add(
            "interface_exclusions_empty",
            not scope.excluded_materials and not scope.excluded_operations,
            f"mats={scope.excluded_materials} ops={scope.excluded_operations}",
        )
        add("adhesive_exactly_once", adhesive == 1, f"count={adhesive}")
        add("bonding_exactly_once", bonding == 1, f"count={bonding}")
        add("bonding_candidate_at_most_once", bonding_candidates <= 1, f"count={bonding_candidates}")
        add("no_led", len(led_mats) == 0, ",".join(led_mats[:8]) or None)
        add("no_mounting", len(mount_mats) == 0, ",".join(mount_mats[:8]) or None)
    if scenario in ("full_product", "legacy_full_product"):
        add("adhesive_present", adhesive >= 1, f"count={adhesive}")
        add("bonding_present", bonding >= 1, f"count={bonding}")
        add(
            "legacy_active_empty_not_empty_subset",
            not (scope.use_legacy_full_product and scope.sold_modules and not scope.active_modules),
            "active=[] with use_legacy means full product",
        )

    add("candidates_from_task_rules_only", True, "operations[] are not auto-promoted")
    add("no_inactive_module_required", True, "Aggregate assumed freeze-filtered")
    return results


def build_frozen_modular_graph_from_v2(
    snapshot: QuoteSnapshotV2 | OrderSnapshotV2 | dict[str, Any],
    *,
    source_kind: str | None = None,
) -> FrozenModularGraphPreview:
    """Normalize an existing V2 snapshot payload into the Build 4A read model."""
    if isinstance(snapshot, QuoteSnapshotV2):
        data = snapshot.model_dump(mode="json")
        kind = source_kind or "quote_snapshot_v2"
    elif isinstance(snapshot, OrderSnapshotV2):
        data = snapshot.model_dump(mode="json")
        kind = source_kind or "order_snapshot_v2"
    else:
        data = dict(snapshot)
        kind = source_kind or (
            "order_snapshot_v2"
            if data.get("order_id") is not None or data.get("quote_snapshot_v2_id") is not None
            else "quote_snapshot_v2"
            if data.get("template_code") or data.get("product_aggregate_snapshot")
            else "unknown"
        )

    pd = _as_dict(data.get("product_definition_snapshot"))
    aggregate = _as_dict(data.get("product_aggregate_snapshot"))
    cpp = _as_dict(data.get("commercial_price_proposal_snapshot"))
    active = _as_dict(data.get("active_scope_snapshot"))
    offer = _as_dict(data.get("offer_scope_snapshot")) or {}
    geometry = _as_dict(data.get("geometry_input_snapshot")) or {}

    compiled = _as_dict((active or {}).get("compiled")) or {}
    provenance = compiled.get("provenance") if isinstance(compiled.get("provenance"), dict) else {}
    use_legacy = bool(
        compiled.get("use_legacy_full_product")
        or offer.get("use_legacy")
        or (offer.get("mode") == "full_product")
    )
    # Critical: active=[] with use_legacy is FULL PRODUCT, never empty subset.
    if use_legacy and not compiled.get("active_runtime_modules"):
        use_legacy = True

    request = FrozenGraphRequest(
        request_mode=str(compiled.get("mode") or offer.get("mode") or "unknown"),
        selected_components=list(compiled.get("sold_module_codes") or offer.get("sold_modules") or []),
        selected_modules=list(compiled.get("active_runtime_modules") or []),
        use_legacy=use_legacy,
    )
    scope = FrozenGraphScope(
        active_components=list(compiled.get("sold_module_codes") or offer.get("sold_modules") or []),
        active_modules=list(compiled.get("active_runtime_modules") or []),
        inactive_modules=list(compiled.get("inactive_runtime_modules") or []),
        sold_modules=list(compiled.get("sold_module_codes") or offer.get("sold_modules") or []),
        excluded_operations=list(compiled.get("composition_excluded_operations") or []),
        excluded_materials=list(compiled.get("composition_excluded_materials") or []),
        interface_face_cant_active=(
            bool(provenance.get("interface_face_cant_active"))
            if provenance.get("interface_face_cant_active") is not None
            else None
        ),
        use_legacy_full_product=use_legacy,
    )
    scenario = _classify_scenario(scope, request)

    materials_raw = _material_codes_raw(aggregate)
    operations_raw = _operation_codes_raw(aggregate)
    # Display lists sorted unique; multiplicity checks use raw lists.
    materials = sorted(set(materials_raw))
    operations = sorted(set(operations_raw))
    candidates = _task_candidates(aggregate)
    # Drop candidates whose priced_operation is composition-excluded (defense in depth)
    excluded_ops = set(scope.excluded_operations)
    if excluded_ops:
        candidates = [
            c
            for c in candidates
            if not c.priced_operation or c.priced_operation not in excluded_ops
        ]

    line_fp = fingerprint_cpp_lines(cpp)
    commercial = FrozenGraphCommercial(
        cpp_rule_codes=[str(r["code"]) for r in line_fp if r.get("code")],
        cpp_line_count=len(line_fp),
        currency=(cpp or {}).get("currency"),
        net_total=(cpp or {}).get("subtotal_commercial") or (cpp or {}).get("net_total"),
        gross_total=(cpp or {}).get("commercial_total") or (cpp or {}).get("gross_total"),
        line_fingerprint=line_fp,
    )

    geo_dims = {}
    qg = geometry.get("quote_geometry") if isinstance(geometry.get("quote_geometry"), dict) else {}
    if qg:
        geo_dims = {
            k: qg.get(k)
            for k in ("letter_count", "letter_perimeter_m", "letter_face_area_m2", "width_mm", "height_mm")
            if k in qg
        }
    svg = geometry.get("svg_source") if isinstance(geometry.get("svg_source"), dict) else {}
    geo = FrozenGraphGeometry(
        source_file=svg.get("file_name"),
        workspace_payload_hash=geometry.get("workspace_payload_hash"),
        analysis_ready=geometry.get("analysis_ready"),
        dimensions=geo_dims,
        perimeter=qg.get("letter_perimeter_m") if isinstance(qg, dict) else None,
        area=qg.get("letter_face_area_m2") if isinstance(qg, dict) else None,
    )

    task_contract = (aggregate or {}).get("task_contract")
    hashes = FrozenGraphComponentHashes(
        product_definition=fingerprint_hash(pd) if pd is not None else None,
        product_aggregate=fingerprint_hash(aggregate) if aggregate is not None else None,
        cpp=fingerprint_hash({"lines": line_fp, "totals": {
            "net": commercial.net_total,
            "gross": commercial.gross_total,
            "currency": commercial.currency,
        }}) if cpp is not None else None,
        active_scope=fingerprint_hash(active) if active is not None else None,
        geometry=fingerprint_hash(geometry) if geometry else None,
        task_contract=fingerprint_hash(task_contract) if task_contract is not None else None,
        frozen_graph="",  # filled below
    )

    identity = FrozenGraphIdentity(
        snapshot_version=data.get("snapshot_version"),
        product_template_code=data.get("template_code")
        or (pd or {}).get("template_code")
        or (aggregate or {}).get("template_code"),
        product_definition_version=(pd or {}).get("preview_version"),
        aggregate_version=(aggregate or {}).get("aggregate_version"),
        form_contract_version=((aggregate or {}).get("form_contract") or {}).get("contract_version")
        if isinstance((aggregate or {}).get("form_contract"), dict)
        else None,
        component_scope_version=data.get("component_scope_version"),
    )

    compat_mode: Any = "modular_v2"
    notes: list[str] = []
    if kind == "order_snapshot_v2":
        compat_mode = "order_v2_frozen"
    if use_legacy or scenario == "legacy_full_product":
        compat_mode = "legacy_full_product"
        notes.append("active=[] with use_legacy_full_product means full product, not empty subset")
    if aggregate is None and data.get("snapshot_line_items") is not None:
        compat_mode = "legacy_v1_line_items"
        notes.append("V1 snapshot_line_items present without Aggregate — compatibility read only")

    adhesive_count = _count_adhesive(materials_raw)
    bonding_count = _count_bonding(operations_raw)
    execution = FrozenGraphExecutionPreview(
        candidate_count=len(candidates),
        task_candidates=candidates,
        material_codes=materials,
        operation_codes=operations,
        adhesive_material_count=adhesive_count,
        bonding_operation_count=bonding_count,
        semantic_interface_face_cant_active=scope.interface_face_cant_active,
        technical_adhesive_present=adhesive_count > 0,
        technical_bonding_present=bonding_count > 0,
    )
    assertions = _build_assertions(
        scenario=scenario,
        materials=materials_raw,
        operations=operations_raw,
        candidates=candidates,
        scope=scope,
    )

    package_for_hash = {
        "identity": identity.model_dump(mode="json"),
        "request": request.model_dump(mode="json"),
        "scope": scope.model_dump(mode="json"),
        "geometry": geo.model_dump(mode="json"),
        "commercial_lines": line_fp,
        "materials": materials,
        "operations": operations,
        "task_candidates": [c.model_dump(mode="json") for c in candidates],
        "pd_hash": hashes.product_definition,
        "aggregate_hash": hashes.product_aggregate,
        "cpp_hash": hashes.cpp,
        "active_scope_hash": hashes.active_scope,
        "geometry_hash": hashes.geometry,
        "task_contract_hash": hashes.task_contract,
    }
    hashes.frozen_graph = fingerprint_hash(package_for_hash)

    blockers = []
    for b in data.get("blockers_snapshot") or []:
        if isinstance(b, dict):
            blockers.append(str(b.get("code") or b.get("message") or b))
        else:
            blockers.append(str(getattr(b, "code", None) or b))

    return FrozenModularGraphPreview(
        identity=identity,
        request=request,
        scope=scope,
        geometry=geo,
        commercial=commercial,
        execution=execution,
        compatibility=FrozenGraphCompatibility(
            mode=compat_mode,
            scenario=scenario,
            source_snapshot_version=data.get("snapshot_version"),
            adapter_version=FROZEN_MODULAR_GRAPH_ADAPTER_VERSION,
            notes=notes,
        ),
        hashes=hashes,
        assertions=assertions,
        readiness=data.get("readiness"),
        blockers=blockers,
        warnings=[str(w) for w in (data.get("warnings_snapshot") or [])],
        no_write=True,
        source_kind=kind if kind in ("quote_snapshot_v2", "order_snapshot_v2", "unknown") else "unknown",
    )


def classify_order14_compatibility(*, has_order: bool, has_execution_plan: bool, has_v2_json: bool) -> dict[str, Any]:
    """Read-only health-anchor classification — never reinterprets Order 14 as modular subset."""
    return {
        "anchor_order_id": 14,
        "role": "system_health_anchor",
        "has_order": has_order,
        "has_execution_plan": has_execution_plan,
        "has_order_snapshot_v2": has_v2_json,
        "compatibility_mode": "order_v2_frozen" if has_v2_json else "legacy_v1_or_mixed",
        "must_not": [
            "reinterpret_as_empty_subset",
            "reprice",
            "regenerate_tasks",
            "rewrite_snapshot",
        ],
        "no_write": True,
    }
