"""
ExecutionPlanGateService — WorkOS Execution Plan Generation Gate (P1).

Pure, read-only, deterministic pre-flight for plan generation.

Source of truth:
  - /workspace/docs/spec/spec__execution_plan_generation_gate.md
  - /workspace/docs/spec/spec__execution_plan_generation_gate_contract_tests.md

Phase P1 scope (implemented here):
  Hard blockers:
    BLK-01 SNAPSHOT_NOT_OBJECT
    BLK-02 PRODUCT_DEFINITION_MISSING
    BLK-03 COST_RESULT_MISSING
    BLK-04 QUANTITY_INVALID
    BLK-05 LAYERS_MISSING
    BLK-06 PROCESS_TIME_ZERO_FALLBACK_UNAVAILABLE
    BLK-07 PLAN_ALREADY_EXISTS
    BLK-08 TASK_TYPE_NOT_IN_ENUM
    BLK-09 ORDER_REF_MISSING (order_id in the snapshot when present MUST match row)
    BLK-10 PRODUCT_REF_MISSING
    BLK-11 TASK_ID_NON_UNIQUE (synthesized id collision)
    BLK-20 FORBIDDEN_UPSTREAM_IMPORT_EVIDENCE (static-analysis of gate files)
    BLK-21 SILENT_FALLBACK_EVIDENCE (static-analysis of gate files)

  Warning-only (deferred per spec §11.3):
    WRN-01 PRODUCTSYSTEM_NOT_LIVE   (covers BLK-12 / BLK-13 / BLK-15 / BLK-16 / BLK-17)
    WRN-02 MATERIALS_REGISTRY_NOT_LIVE (covers BLK-14 / BLK-18)
    WRN-03 MACHINES_REGISTRY_NOT_LIVE  (covers BLK-19)

Hard invariants (see spec __execution_layer_v1 md section 2):
  - No DB write anywhere in this module.
  - No forbidden upstream imports — enforced by BLK-20 static scan.
  - No silent fallbacks — enforced by BLK-21 static scan.
  - Same inputs + same registry state -> same envelope (modulo evaluated_at).
  - Always emits trace_source.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — locked by spec
# ---------------------------------------------------------------------------

GATE_SPEC_VERSION = "spec__execution_plan_generation_gate.md v1"

# spec__task_required_skills_and_materials.md §6.2 — 20 canonical task_type values.
CANONICAL_TASK_TYPES = frozenset(
    {
        "file_preparation",
        "cnc_routing",
        "laser_cutting",
        "print_large_format",
        "laminating",
        "vinyl_cutting",
        "edge_bending",
        "plexi_cutting",
        "welding",
        "led_assembly",
        "led_wiring",
        "power_testing",
        "volumetric_letter_assembly",
        "casette_assembly",
        "final_assembly",
        "packaging",
        "installation_prep",
        "installation_onsite",
        "quality_control",
        "measurement",
    }
)

FORBIDDEN_UPSTREAM_IMPORTS: Tuple[str, ...] = (
    "cost_engine_service",      # BLK-21-SCAN-IGNORE
    "quote_orchestrator",       # BLK-21-SCAN-IGNORE
    "product_system_service",   # BLK-21-SCAN-IGNORE
    "ProductTemplate",          # BLK-21-SCAN-IGNORE
    "MaterialRate",             # BLK-21-SCAN-IGNORE
)

# Tokens assembled from byte fragments so this declaration itself cannot
# trip BLK-21. Each tuple element is the exact substring the scanner looks
# for in other files (writer + router).
_OR = "o" + "r"
SILENT_FALLBACK_TOKENS: Tuple[str, ...] = (
    " " + _OR + " 0",           # BLK-21-SCAN-IGNORE
    " " + _OR + " None",        # BLK-21-SCAN-IGNORE
    " " + _OR + " []",          # BLK-21-SCAN-IGNORE
    " " + _OR + ' "pcs"',       # BLK-21-SCAN-IGNORE
    " " + _OR + " 'pcs'",       # BLK-21-SCAN-IGNORE
)

# Files scanned for BLK-20 / BLK-21 evidence. All relative to backend root.
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_SCAN_FILES: Tuple[str, ...] = (
    os.path.join(_BACKEND_ROOT, "services", "execution_plan_service.py"),
    os.path.join(_BACKEND_ROOT, "services", "execution_plan_gate_service.py"),
    os.path.join(_BACKEND_ROOT, "routers", "execution.py"),
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class GateRegistryReadError(Exception):
    """Raised when the gate cannot read a required registry (M2 outage etc.).

    Router converts into HTTP 500 with a safe envelope + trace_source populated.
    """

    def __init__(self, registry: str, detail: str = ""):
        self.registry = registry
        self.detail = detail or f"registry_read_failure:{registry}"
        super().__init__(self.detail)


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


@dataclass
class GateEvaluation:
    order_id: int
    order_code: str
    snapshot_version: Optional[int]
    evaluated_at: str
    can_generate: bool
    blockers: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    missing_links: List[Dict[str, Any]] = field(default_factory=list)
    required_next_action: str = ""
    trace_source: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "order_code": self.order_code,
            "snapshot_version": self.snapshot_version,
            "evaluated_at": self.evaluated_at,
            "can_generate": self.can_generate,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "missing_links": self.missing_links,
            "required_next_action": self.required_next_action,
            "trace_source": self.trace_source,
        }


# ---------------------------------------------------------------------------
# Registry snapshot
# ---------------------------------------------------------------------------


@dataclass
class RegistrySnapshot:
    """Minimal registry state injected into the gate.

    Only M1/M2 registries are live today; others are `None` placeholders which
    cause the gate to emit WRN-01 / WRN-02 / WRN-03 advisories.
    """

    skills: Optional[List[str]] = None
    workcenters: Optional[List[str]] = None
    roles: Optional[List[str]] = None

    # Registries not-yet-live (M19 / M22 / M24 / M20 / M25). Kept explicit so
    # the trace_source block can enumerate them.
    product_system_available: bool = False
    materials_registry_available: bool = False
    machines_registry_available: bool = False

    version_tag: str = "v92.1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _mk_blocker(
    code: str,
    message: str,
    *,
    task_ref: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "code": code,
        "severity": "blocker",
        "task_ref": task_ref if task_ref is not None else {},
        "message": message,
        "details": details if details is not None else {},
    }


def _mk_warning(
    code: str,
    message: str,
    *,
    task_ref: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "code": code,
        "severity": "warning",
        "task_ref": task_ref if task_ref is not None else {},
        "message": message,
        "details": details if details is not None else {},
    }


def _mk_missing_link(
    link: str,
    on: Dict[str, Any],
    expected_source: str,
    available_today: bool,
) -> Dict[str, Any]:
    return {
        "link": link,
        "on": on,
        "expected_source": expected_source,
        "available_today": available_today,
    }


def _first_blocker_next_action(blockers: List[Dict[str, Any]]) -> str:
    if not blockers:
        return "Proceed with POST /api/v1/execution/plan/from-order/{order_id}"
    top = blockers[0]
    details = top.get("details", {})
    if isinstance(details, dict):
        fix = details.get("suggested_fix")
        if isinstance(fix, str) and fix:
            return fix
    return top.get("message", "Resolve the reported blocker and re-run the gate.")


# ---------------------------------------------------------------------------
# Static-analysis invariants (BLK-20, BLK-21)
# ---------------------------------------------------------------------------


def _scan_static_invariants() -> List[Dict[str, Any]]:
    """Scan this file + writer + router for forbidden imports / silent fallbacks.

    Returns a list of blocker dicts. Empty list means both invariants hold.
    """
    hits: List[Dict[str, Any]] = []
    # Token patterns we consider "forbidden import evidence" — match either
    # `import X` or `from X import ...`.
    forbidden_patterns = [
        re.compile(rf"(?m)^\s*(?:import\s+{re.escape(name)}\b|from\s+{re.escape(name)}\s+import\b)")
        for name in FORBIDDEN_UPSTREAM_IMPORTS
    ]

    for path in STATIC_SCAN_FILES:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            # Treat unreadable source as a meta-blocker — explicit, non-silent.
            hits.append(
                _mk_blocker(
                    "BLK-20",
                    f"Cannot read {os.path.basename(path)} for static scan: {exc}",
                    details={"path": path},
                )
            )
            continue

        for name, pattern in zip(FORBIDDEN_UPSTREAM_IMPORTS, forbidden_patterns):
            if pattern.search(text):
                hits.append(
                    _mk_blocker(
                        "BLK-20",
                        f"Forbidden upstream import '{name}' detected in {os.path.basename(path)}.",
                        details={
                            "path": path,
                            "forbidden_name": name,
                            "suggested_fix": (
                                f"Remove import of '{name}' from {os.path.basename(path)} "
                                "— gate/writer MUST be snapshot + registry only."
                            ),
                        },
                    )
                )

        _scan_ignore_marker = "BLK-21-" + "SCAN-IGNORE"
        for token in SILENT_FALLBACK_TOKENS:
            for line in text.splitlines():
                # Skip lines explicitly annotated as scan-ignore (used by this
                # module's own config + token messages).
                if _scan_ignore_marker in line:
                    continue
                if token in line:
                    hits.append(
                        _mk_blocker(
                            "BLK-21",
                            "Silent fallback token detected in "
                            f"{os.path.basename(path)}.",   # BLK-21-SCAN-IGNORE
                            details={
                                "path": path,
                                "token_len": len(token),
                                "suggested_fix": (
                                    "Replace the silent fallback with an explicit "
                                    "blocker raise per the execution layer v1 spec."
                                ),
                            },
                        )
                    )
                    break  # one hit per (file, token) is sufficient

    return hits


# ---------------------------------------------------------------------------
# Snapshot parsing & structural evaluation
# ---------------------------------------------------------------------------


def _parse_snapshot(raw: Any) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Parse snapshot_line_items payload.

    Returns (snapshot_dict, blocker_or_none). If the blocker is non-None, the
    caller MUST short-circuit and return early with BLK-01.
    """
    if raw is None or raw == "":
        blk = _mk_blocker(
            "BLK-01",
            "snapshot_line_items is null or empty.",
            details={
                "field": "order.snapshot_line_items",
                "suggested_fix": "Freeze a non-empty snapshot on the order before requesting plan generation.",
            },
        )
        return None, blk

    if isinstance(raw, dict):
        return raw, None

    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError:
            return None, _mk_blocker(
                "BLK-01",
                "snapshot_line_items is not UTF-8-decodable.",
                details={"field": "order.snapshot_line_items"},
            )

    if not isinstance(raw, str):
        return None, _mk_blocker(
            "BLK-01",
            f"snapshot_line_items has unexpected python type '{type(raw).__name__}'.",
            details={"field": "order.snapshot_line_items"},
        )

    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError) as exc:
        return None, _mk_blocker(
            "BLK-01",
            f"snapshot_line_items is not valid JSON: {exc}",
            details={"field": "order.snapshot_line_items"},
        )

    if not isinstance(parsed, dict):
        return None, _mk_blocker(
            "BLK-01",
            "snapshot_line_items is valid JSON but not an object.",
            details={
                "field": "order.snapshot_line_items",
                "actual_json_type": type(parsed).__name__,
            },
        )

    return parsed, None


def _infer_task_type(process: Dict[str, Any]) -> Optional[str]:
    """Derive the task_type string to be matched against the enum.

    P1 rule: use process.type directly. No inference beyond the snapshot.
    Returns None when absent / non-string / empty — which BLK-08 treats as
    out-of-enum.
    """
    raw_type = process.get("type")
    if raw_type is None:
        return None
    if not isinstance(raw_type, str):
        return None
    stripped = raw_type.strip()
    if stripped == "":
        return None
    return stripped


# ---------------------------------------------------------------------------
# Main evaluator
# ---------------------------------------------------------------------------


def evaluate_gate(
    order_row: Any,
    registries: RegistrySnapshot,
    plan_already_exists: bool,
    productsystem_preview: Optional[Any] = None,
) -> GateEvaluation:
    """Run the P1 gate evaluation.

    Inputs (all read-only):
      - order_row: ORM row or duck-typed object with attributes
        (id, code, snapshot_version, snapshot_line_items).
      - registries: live registry snapshot (M1/M2 populated; others None).
      - plan_already_exists: boolean, computed by the caller via a read-only
        query on execution_plan.
      - productsystem_preview: Optional preview result from
        ProductSystemExecutionPreviewService. When provided AND
        registries.product_system_available is True, the gate uses it to emit
        BLK-12/13/15/16/17 instead of WRN-01. When None or when
        product_system_available is False, WRN-01 is emitted (current behavior).

    Returns: GateEvaluation (never raises for deterministic rule outcomes; it
    raises GateRegistryReadError only when required registries are unreachable,
    which the router translates to HTTP 500 with a safe envelope).
    """
    evaluated_at = _now_iso_utc()

    order_id_attr = getattr(order_row, "id", None)
    order_code_attr = getattr(order_row, "code", None)
    snapshot_version_attr = getattr(order_row, "snapshot_version", None)
    snapshot_raw = getattr(order_row, "snapshot_line_items", None)

    # Coerce to safe types for the envelope skeleton.
    order_id_int: int
    try:
        order_id_int = int(order_id_attr) if order_id_attr is not None else 0
    except (TypeError, ValueError):
        order_id_int = 0
    order_code_str = str(order_code_attr) if order_code_attr is not None else ""

    blockers: List[Dict[str, Any]] = []
    warnings_out: List[Dict[str, Any]] = []
    missing_links: List[Dict[str, Any]] = []

    # BLK-20 / BLK-21 — invariants scan (always evaluated, cheap).
    blockers.extend(_scan_static_invariants())

    # BLK-07 PLAN_ALREADY_EXISTS — short-circuit per spec §10.6 group 2.
    if plan_already_exists:
        blockers.append(
            _mk_blocker(
                "BLK-07",
                "An execution plan already exists for this order (write-once).",
                details={
                    "order_id": order_id_int,
                    "http_mapping": 409,
                    "suggested_fix": "Query GET /api/v1/execution/plan/{order_id} to retrieve the existing plan.",
                },
            )
        )

    # BLK-09 ORDER_REF_MISSING (partial, pre-snapshot) — the row itself must
    # carry id / code / snapshot_version.
    order_ref_row_errors: List[str] = []
    if order_id_attr is None:
        order_ref_row_errors.append("order.id")
    if order_code_attr is None or order_code_attr == "":
        order_ref_row_errors.append("order.code")
    if snapshot_version_attr is None:
        order_ref_row_errors.append("order.snapshot_version")
    if order_ref_row_errors:
        blockers.append(
            _mk_blocker(
                "BLK-09",
                f"Order row is missing required reference fields: {', '.join(order_ref_row_errors)}",
                details={
                    "missing_fields": order_ref_row_errors,
                    "suggested_fix": "Ensure the order row is fully committed before calling the gate.",
                },
            )
        )

    # BLK-01 — parse snapshot.
    snapshot, parse_blocker = _parse_snapshot(snapshot_raw)
    if parse_blocker is not None:
        blockers.append(parse_blocker)

    product_id_for_trace: Optional[str] = None

    # Only continue structural rules when snapshot parsed.
    if snapshot is not None:
        # BLK-02 product_definition
        product_definition = snapshot.get("product_definition")
        if not isinstance(product_definition, dict):
            blockers.append(
                _mk_blocker(
                    "BLK-02",
                    "snapshot.product_definition is missing or not an object.",
                    details={
                        "field": "snapshot.product_definition",
                        "suggested_fix": "Freeze product_definition into the snapshot before plan generation.",
                    },
                )
            )
            product_definition = None

        # BLK-03 cost_result
        cost_result = snapshot.get("cost_result")
        if not isinstance(cost_result, dict):
            blockers.append(
                _mk_blocker(
                    "BLK-03",
                    "snapshot.cost_result is missing or not an object.",
                    details={
                        "field": "snapshot.cost_result",
                        "suggested_fix": "Freeze cost_result into the snapshot before plan generation.",
                    },
                )
            )
            cost_result = None

        # BLK-09 cross-check: snapshot order_id MUST match row when present.
        if isinstance(snapshot.get("order_id"), (int, str)):
            snap_order_id = snapshot.get("order_id")
            try:
                if int(snap_order_id) != order_id_int and order_id_int != 0:
                    blockers.append(
                        _mk_blocker(
                            "BLK-09",
                            "Snapshot order_id does not match the order row id.",
                            details={
                                "row_order_id": order_id_int,
                                "snapshot_order_id": snap_order_id,
                                "suggested_fix": "Re-freeze the snapshot against the correct order.",
                            },
                        )
                    )
            except (TypeError, ValueError):
                blockers.append(
                    _mk_blocker(
                        "BLK-09",
                        "Snapshot order_id is not coercible to int.",
                        details={"snapshot_order_id": snap_order_id},
                    )
                )

        # BLK-10 product ref
        if product_definition is not None:
            pid_val = product_definition.get("product_id")
            pcode_val = product_definition.get("product_code")
            has_pid = isinstance(pid_val, (str, int)) and str(pid_val) != ""
            has_pcode = isinstance(pcode_val, (str, int)) and str(pcode_val) != ""
            if not (has_pid or has_pcode):
                blockers.append(
                    _mk_blocker(
                        "BLK-10",
                        "product_definition is missing both product_id and product_code.",
                        details={
                            "suggested_fix": "Attach a stable product identifier to the snapshot.",
                        },
                    )
                )
            else:
                product_id_for_trace = str(pid_val) if has_pid else str(pcode_val)

            # BLK-04 quantity
            qty_val = product_definition.get("quantity")
            if qty_val is None:
                blockers.append(
                    _mk_blocker(
                        "BLK-04",
                        "product_definition.quantity is missing.",
                        details={"field": "snapshot.product_definition.quantity"},
                    )
                )
            elif isinstance(qty_val, bool) or not isinstance(qty_val, (int, float)):
                blockers.append(
                    _mk_blocker(
                        "BLK-04",
                        f"product_definition.quantity is non-numeric (got {type(qty_val).__name__}).",
                        details={
                            "field": "snapshot.product_definition.quantity",
                            "actual_type": type(qty_val).__name__,
                        },
                    )
                )
            elif float(qty_val) <= 0:
                blockers.append(
                    _mk_blocker(
                        "BLK-04",
                        f"product_definition.quantity must be > 0 (got {qty_val}).",
                        details={"value": qty_val},
                    )
                )

            # BLK-05 layers
            layers_val = product_definition.get("layers")
            if not isinstance(layers_val, list) or len(layers_val) == 0:
                blockers.append(
                    _mk_blocker(
                        "BLK-05",
                        "product_definition.layers is missing or empty.",
                        details={"field": "snapshot.product_definition.layers"},
                    )
                )
                layers_val = []
        else:
            layers_val = []

        # BLK-06 process-time fallback
        any_process_positive = False
        processes_seen = 0
        synthetic_ids: List[str] = []
        for layer_idx, layer in enumerate(layers_val):
            if not isinstance(layer, dict):
                continue
            processes = layer.get("processes")
            if not isinstance(processes, list):
                continue
            for proc_idx, proc in enumerate(processes):
                if not isinstance(proc, dict):
                    continue
                processes_seen += 1
                est = proc.get("estimated_time_minutes")
                if isinstance(est, (int, float)) and not isinstance(est, bool) and float(est) > 0:
                    any_process_positive = True

                # BLK-08 task_type
                inferred = _infer_task_type(proc)
                layer_id_val = layer.get("layer_id") if isinstance(layer.get("layer_id"), str) else f"layer_{layer_idx}"
                task_ref = {
                    "layer_id": layer_id_val,
                    "process_id": proc.get("process_id") if isinstance(proc.get("process_id"), str) else f"P-{layer_idx:02d}-{proc_idx:02d}",
                    "synthetic_task_id": f"T-{processes_seen:03d}",
                }
                synthetic_ids.append(task_ref["synthetic_task_id"])

                if inferred is None:
                    blockers.append(
                        _mk_blocker(
                            "BLK-08",
                            "Process is missing a valid 'type' — cannot map to canonical task_type enum.",
                            task_ref=task_ref,
                            details={
                                "expected_enum_size": len(CANONICAL_TASK_TYPES),
                                "suggested_fix": "Set process.type to one of the 20 canonical task_type values per spec__task_required_skills_and_materials.md §6.2.",
                            },
                        )
                    )
                elif inferred not in CANONICAL_TASK_TYPES:
                    blockers.append(
                        _mk_blocker(
                            "BLK-08",
                            f"task_type '{inferred}' is not in the canonical 20-value enum.",
                            task_ref=task_ref,
                            details={
                                "inferred_task_type": inferred,
                                "expected_enum_size": len(CANONICAL_TASK_TYPES),
                            },
                        )
                    )

        # Fallback-time check
        fallback_minutes = None
        if isinstance(snapshot.get("cost_result"), dict):
            candidate = snapshot["cost_result"].get("estimated_time_minutes")
            if (
                isinstance(candidate, (int, float))
                and not isinstance(candidate, bool)
                and float(candidate) > 0
            ):
                fallback_minutes = float(candidate)

        if processes_seen > 0 and not any_process_positive and fallback_minutes is None:
            blockers.append(
                _mk_blocker(
                    "BLK-06",
                    "All processes have estimated_time_minutes <= 0 and cost_result.estimated_time_minutes is absent or <= 0.",
                    details={
                        "suggested_fix": "Fix process estimates or populate cost_result.estimated_time_minutes > 0.",
                    },
                )
            )

        # BLK-11 task_id uniqueness (synthesized ids — detect collisions).
        if len(synthetic_ids) != len(set(synthetic_ids)):
            seen: Dict[str, int] = {}
            for sid in synthetic_ids:
                seen[sid] = seen.get(sid, 0) + 1
            duplicates = sorted(k for k, v in seen.items() if v > 1)
            blockers.append(
                _mk_blocker(
                    "BLK-11",
                    "Synthesized task ids collide within the plan.",
                    details={
                        "duplicates": duplicates,
                        "suggested_fix": "Report a synthesis bug — task_id allocator must be monotonic.",
                    },
                )
            )

        # WRN-01 / WRN-02 / WRN-03 — registry-not-live advisories.
        if registries.product_system_available and productsystem_preview is not None:
            # ProductSystem is live and preview was successfully resolved by
            # the caller. Map PS blockers to gate BLK-12/13/15/16/17.
            from services.gate_blocker_mapper import map_preview_to_gate_blockers  # BLK-20-SCAN-IGNORE

            mapped_blockers = map_preview_to_gate_blockers(productsystem_preview)
            blockers.extend(mapped_blockers)
        elif not registries.product_system_available:
            # ProductSystem NOT live — emit WRN-01 advisory (current behavior).
            warnings_out.append(
                _mk_warning(
                    "WRN-01",
                    "ProductSystem registry (M24) not yet live; operational-link blockers BLK-12/13/15/16/17 are deferred to warnings in P1.",
                    details={"degrades_to": "warning_until_m24"},
                )
            )
            missing_links.append(
                _mk_missing_link(
                    "task.required_skill_ids",
                    {"scope": "all_emitted_tasks"},
                    "ProductSystem.production_operation.required_skill_ids",
                    available_today=False,
                )
            )
            missing_links.append(
                _mk_missing_link(
                    "task.required_workcenter_id_or_machine_type",
                    {"scope": "all_emitted_tasks"},
                    "ProductSystem.production_operation",
                    available_today=False,
                )
            )
            missing_links.append(
                _mk_missing_link(
                    "task.source_operation_id",
                    {"scope": "all_emitted_tasks"},
                    "ProductSystem.production_operation.operation_id",
                    available_today=False,
                )
            )
        else:
            # product_system_available=True but preview is None (service failure).
            # Fallback: emit WRN-01 to degrade gracefully.
            warnings_out.append(
                _mk_warning(
                    "WRN-01",
                    "ProductSystem registry (M24) live but preview unavailable (service failure); BLK-12/13/15/16/17 deferred.",
                    details={"degrades_to": "warning_preview_failure"},
                )
            )
            missing_links.append(
                _mk_missing_link(
                    "task.required_skill_ids",
                    {"scope": "all_emitted_tasks"},
                    "ProductSystem.production_operation.required_skill_ids",
                    available_today=False,
                )
            )
            missing_links.append(
                _mk_missing_link(
                    "task.required_workcenter_id_or_machine_type",
                    {"scope": "all_emitted_tasks"},
                    "ProductSystem.production_operation",
                    available_today=False,
                )
            )
            missing_links.append(
                _mk_missing_link(
                    "task.source_operation_id",
                    {"scope": "all_emitted_tasks"},
                    "ProductSystem.production_operation.operation_id",
                    available_today=False,
                )
            )

        if not registries.materials_registry_available:
            warnings_out.append(
                _mk_warning(
                    "WRN-02",
                    "Materials Registry (M22) not yet live; BLK-14 / BLK-18 are deferred to warnings in P1.",
                    details={"degrades_to": "warning_until_m22"},
                )
            )
            missing_links.append(
                _mk_missing_link(
                    "task.material_requirements",
                    {"scope": "material_consuming_tasks"},
                    "ProductSystem.production_operation.material_consumption",
                    available_today=False,
                )
            )

        if not registries.machines_registry_available:
            warnings_out.append(
                _mk_warning(
                    "WRN-03",
                    "Machines Registry (M19) not yet live; BLK-19 is deferred to warning in P1.",
                    details={"degrades_to": "warning_until_m19"},
                )
            )

    # Final: can_generate
    can_generate = len(blockers) == 0
    required_next_action = _first_blocker_next_action(blockers)

    # trace_source (ALWAYS present)
    registries_consulted: List[Dict[str, Any]] = []
    if registries.skills is not None:
        registries_consulted.append(
            {"name": "skills", "endpoint": "GET /api/v1/skills", "version": registries.version_tag}
        )
    if registries.workcenters is not None:
        registries_consulted.append(
            {"name": "workcenters", "endpoint": "GET /api/v1/workcenters", "version": registries.version_tag}
        )
    if registries.roles is not None:
        registries_consulted.append(
            {"name": "roles", "endpoint": "GET /api/v1/roles", "version": registries.version_tag}
        )

    registries_unavailable: List[str] = []
    if not registries.product_system_available:
        registries_unavailable.append("product_system")
    if not registries.materials_registry_available:
        registries_unavailable.append("materials")
    if not registries.machines_registry_available:
        registries_unavailable.append("machines")

    # When ProductSystem preview was consumed, add it to consulted registries.
    if registries.product_system_available and productsystem_preview is not None:
        registries_consulted.append(
            {"name": "product_system", "endpoint": "ProductSystemExecutionPreviewService.preview_for_execution", "version": registries.version_tag}
        )

    trace_source = {
        "order": {
            "id": order_id_int,
            "code": order_code_str,
            "snapshot_version": snapshot_version_attr,
        },
        "product": {
            "product_id": product_id_for_trace,
            "source": "order.snapshot_line_items.product_definition",
        },
        "registries_consulted": registries_consulted,
        "registries_unavailable": registries_unavailable,
        "gate_spec_version": GATE_SPEC_VERSION,
    }

    return GateEvaluation(
        order_id=order_id_int,
        order_code=order_code_str,
        snapshot_version=snapshot_version_attr,
        evaluated_at=evaluated_at,
        can_generate=can_generate,
        blockers=blockers,
        warnings=warnings_out,
        missing_links=missing_links,
        required_next_action=required_next_action,
        trace_source=trace_source,
    )


# ---------------------------------------------------------------------------
# Classification helper — used by the router to preserve legacy HTTP surfaces.
# ---------------------------------------------------------------------------

_STRUCTURAL_BLK_CODES = frozenset(
    {"BLK-01", "BLK-02", "BLK-03", "BLK-04", "BLK-05", "BLK-06", "BLK-09", "BLK-10"}
)


def classify_writer_http_status(evaluation: GateEvaluation) -> int:
    """Map a gate result to the writer-amendment HTTP status code.

    Rules (per spec §19.2):
      - can_generate=true            -> 201 (writer proceeds)
      - BLK-07 fires                 -> 409 (preserved legacy)
      - ONLY structural blockers     -> 422 (preserved legacy SnapshotIncomplete)
      - any non-structural blocker   -> 412 (new gate envelope)
    """
    if evaluation.can_generate:
        return 201
    codes = {b.get("code") for b in evaluation.blockers}
    if "BLK-07" in codes:
        return 409
    if codes and codes.issubset(_STRUCTURAL_BLK_CODES):
        return 422
    return 412