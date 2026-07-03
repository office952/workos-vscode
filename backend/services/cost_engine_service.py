"""
CostEngineService — calculates CostResult from a ProductDefinition.

Canonical rules:
  - Calculates cost, does NOT modify ProductDefinition.
  - No commercial decisions here (no margin, no discount, no VAT).
  - Missing cost data is marked explicitly in CostResult.validation.
  - Caller (Quotes) decides how to react to an invalid CostResult.

Default rates can be overridden through PricingContext.overhead_profile_id
(a real rate registry would be introduced later; for now, profiles are
static in-memory — this is explicitly documented in the log).
"""

from __future__ import annotations

import copy
from typing import Dict, List, Optional

from data_models.product_contracts import (
    CostLine,
    CostRequest,
    CostResult,
    CostValidation,
    ProductDefinition,
    ProductLayer,
)
from services.quote_input_line_gate import should_skip_quote_input_gated_line


# ---------------------------------------------------------------------------
# Static overhead profiles (TEMPORARY — to be replaced by a registry)
# ---------------------------------------------------------------------------
_OVERHEAD_PROFILES: Dict[str, Dict[str, float]] = {
    "default": {
        "labour_rate_ron_per_hour": 80.0,
        "machine_rate_ron_per_hour": 40.0,
        "overhead_pct": 0.12,  # 12% on top of materials+labour+machine
        "external_cost_pct": 0.0,
    }
}


class CostEngineService:
    def _lookup_material_unit_cost(self, material_id: str) -> float:
        """Hook for subclasses to provide a unit cost. Base returns 0 (missing)."""
        return 0.0

    def calculate(self, request: CostRequest) -> CostResult:
        pd = request.product_definition
        ctx = request.pricing_context

        # If ProductDefinition is invalid, we still return a structured CostResult
        # marked invalid — we do NOT silently fallback.
        if not pd or not getattr(pd, "validation", None) or not pd.validation.is_valid:
            return CostResult(
                is_valid=False,
                currency=ctx.currency or "RON",
                validation=CostValidation(
                    missing_cost_data=["product_definition_invalid"],
                    warnings=(pd.validation.warnings if pd and pd.validation else []),
                ),
            )

        profile = _OVERHEAD_PROFILES.get(ctx.overhead_profile_id or "default") or _OVERHEAD_PROFILES["default"]
        labour_rate = float(profile["labour_rate_ron_per_hour"])
        machine_rate = float(profile["machine_rate_ron_per_hour"])
        overhead_pct = float(profile["overhead_pct"])

        breakdown: List[CostLine] = []
        missing_cost: List[str] = []
        warnings: List[str] = []

        materials_cost = 0.0
        labour_cost = 0.0
        machine_cost = 0.0
        external_cost = 0.0
        total_minutes = 0.0

        # We do NOT mutate pd — operate on read-only view / copies.
        layers: List[ProductLayer] = list(pd.layers or [])
        if not layers:
            missing_cost.append("no_layers")

        for layer in layers:
            # Materials: for each material in layer, check if we have a unit_cost.
            # In this foundation version, we do not have a unit cost registry wired.
            # We MUST mark this as missing explicitly.
            if layer.material and layer.material.material_id:
                # Look for a synthetic "mat_qty_*" component carrying requested qty
                mat_qty = 0.0
                for comp in layer.components:
                    if comp.component_id.startswith("mat_qty_"):
                        mat_qty = float(comp.quantity or 0)
                        break

                unit_cost = float(self._lookup_material_unit_cost(layer.material.material_id) or 0)
                if unit_cost <= 0:
                    missing_cost.append(f"unit_cost[{layer.material.material_id}]")
                line_total = unit_cost * mat_qty * max(pd.quantity, 1)
                breakdown.append(
                    CostLine(
                        type="material",
                        name=f"{layer.material.material_id}|{layer.material.name}",
                        quantity=mat_qty * max(pd.quantity, 1),
                        unit=layer.material.unit or "pcs",
                        unit_cost=unit_cost,
                        total=line_total,
                    )
                )
                materials_cost += line_total
            else:
                warnings.append(f"layer_without_material[{layer.layer_id}]")

            # Processes -> labour + machine
            for proc in layer.processes:
                minutes = float(proc.estimated_time_minutes or 0) * max(pd.quantity, 1)
                if minutes <= 0:
                    warnings.append(f"process_zero_minutes[{proc.process_id}]")
                    continue
                total_minutes += minutes
                hours = minutes / 60.0

                lab_total = hours * labour_rate
                labour_cost += lab_total
                breakdown.append(
                    CostLine(
                        type="labour",
                        name=f"labour:{proc.process_id}",
                        quantity=round(hours, 4),
                        unit="h",
                        unit_cost=labour_rate,
                        total=lab_total,
                    )
                )

                if proc.machine_type:
                    mac_total = hours * machine_rate
                    machine_cost += mac_total
                    breakdown.append(
                        CostLine(
                            type="machine",
                            name=f"machine:{proc.machine_type}",
                            quantity=round(hours, 4),
                            unit="h",
                            unit_cost=machine_rate,
                            total=mac_total,
                        )
                    )

        # Overhead on top of subtotal
        subtotal = materials_cost + labour_cost + machine_cost + external_cost
        overhead_cost = subtotal * overhead_pct
        if overhead_pct > 0:
            breakdown.append(
                CostLine(
                    type="overhead",
                    name=f"overhead:{ctx.overhead_profile_id or 'default'}",
                    quantity=1,
                    unit="pct",
                    unit_cost=overhead_pct,
                    total=overhead_cost,
                )
            )

        total_cost = subtotal + overhead_cost

        # Validity: valid only if no missing cost data.
        # If materials_cost is 0 because all unit_costs were missing, is_valid=False.
        is_valid = len(missing_cost) == 0

        return CostResult(
            is_valid=is_valid,
            currency=ctx.currency or "RON",
            materials_cost=round(materials_cost, 2),
            labour_cost=round(labour_cost, 2),
            machine_cost=round(machine_cost, 2),
            external_cost=round(external_cost, 2),
            overhead_cost=round(overhead_cost, 2),
            total_cost=round(total_cost, 2),
            estimated_time_minutes=round(total_minutes, 2),
            breakdown=breakdown,
            validation=CostValidation(
                missing_cost_data=missing_cost,
                warnings=warnings,
            ),
        )


# ---------------------------------------------------------------------------
# Runtime registry for material unit costs — minimal injector to avoid
# silent fallback. The caller can provide a dict { material_id: unit_cost }.
# If absent, missing_cost_data is populated as above.
# ---------------------------------------------------------------------------
class CostEngineWithMaterialRates(CostEngineService):
    """Cost engine variant with an injected material_id -> unit_cost registry.

    Lookup is by material_id (exact match). Rates MUST be in the same
    currency as PricingContext.currency (base: RON)."""

    def __init__(self, material_unit_costs: Optional[Dict[str, float]] = None):
        self.material_unit_costs = material_unit_costs or {}

    def _lookup_material_unit_cost(self, material_id: str) -> float:
        return float(self.material_unit_costs.get(material_id, 0.0) or 0.0)


# ===========================================================================
# Sprint #16 — CostEngine v2 — COMPONENT-AWARE CALCULATION (read-only)
# ---------------------------------------------------------------------------
# New public function: build_execution_layers_from_components
#
# GOAL:
#   Compute cost per component using the hierarchical shape produced by
#   Sprint #15 (components_json where each component owns its own
#   `materials[]` and `operations[]`). If the template still stores the
#   legacy flat shape (or components_json is a string[] / missing), fall
#   back to the flat `required_materials_json` + `operations_json` and
#   group everything under a synthetic `comp_flat_legacy` component so the
#   output schema stays stable.
#
# STRICT BOUNDARIES:
#   - Does NOT mutate the template.
#   - Does NOT touch CostEngineService.calculate() — callers that already
#     rely on it (quote_orchestrator) keep working unchanged.
#   - Does NOT talk to the database. The caller provides explicit rate
#     contexts (material_rates + workcenter_rates), which is how the rest
#     of this module already works (see CostEngineWithMaterialRates).
#   - Does NOT invent endpoints or tables.
#   - Does NOT apply margin / VAT / discount — this is COST only.
#
# ERROR SEMANTICS (explicit, no silent zero):
#   - MATERIAL_RATE_MISSING  → material_code absent from `material_rates`
#     or rate is null/<=0. Recorded on the component `errors[]` with
#     `path = "components[i].materials[j]"`, the cost contribution of
#     that single line is 0 (so totals stay finite), and the result's
#     top-level `is_valid=False`.
#   - WORKCENTER_RATE_MISSING → workcenter absent from `workcenter_rates`
#     or rate null/<=0. Recorded the same way. is_valid=False.
#   - COMPONENT_EMPTY → warning only (no error). Component with 0 ops AND
#     0 materials returns 0.00. Does NOT flip is_valid to False.
#
# OUTPUT SCHEMA (stable):
#   {
#     "is_valid": bool,
#     "source": "hierarchical" | "flat_legacy",
#     "total_material_cost": float,
#     "total_operation_cost": float,
#     "total_cost": float,
#     "components": [
#       {
#         "component_id": str,
#         "type": str,
#         "name": str,
#         "material_cost": float,
#         "operation_cost": float,
#         "total_component_cost": float,
#         "materials_detail":  [ { "material_code", "quantity", "unit",
#                                  "unit_cost", "line_total", "path" }, ... ],
#         "operations_detail": [ { "code", "workcenter", "estimated_minutes",
#                                  "hours", "rate_per_hour", "line_total",
#                                  "path" }, ... ],
#         "errors":   [ { "kind", "path", "detail" }, ... ],
#         "warnings": [ { "kind", "path", "detail" }, ... ],
#       }, ...
#     ],
#     "errors":   [ ... merged from components ... ],
#     "warnings": [ ... merged from components ... ],
#   }
# ===========================================================================

import json as _json
from dataclasses import dataclass, field
from typing import Any, List as _List, Dict as _Dict


# --- Error / warning kinds (canonical strings; do NOT hand-write elsewhere) ---
ERR_MATERIAL_RATE_MISSING = "MATERIAL_RATE_MISSING"
ERR_WORKCENTER_RATE_MISSING = "WORKCENTER_RATE_MISSING"
ERR_WORKCENTER_LINEAR_METER_QUANTITY_MISSING = (
    "WORKCENTER_LINEAR_METER_QUANTITY_MISSING"
)
ERR_WORKCENTER_PIECE_QUANTITY_MISSING = "WORKCENTER_PIECE_QUANTITY_MISSING"
ERR_WORKCENTER_AREA_QUANTITY_MISSING = "WORKCENTER_AREA_QUANTITY_MISSING"
WARN_COMPONENT_EMPTY = "COMPONENT_EMPTY"

# Sprint #21.1 — additive error kinds for formula-based lines.
# NEEDS_QUOTE_INPUT: a formula_based line declared `requires_quote_input`
#   keys that were not provided in ComponentCostContext.quote_input (or
#   were provided but invalid). The line contributes 0 to cost AND the
#   result.is_valid becomes False. It is NEVER silently treated as zero.
# FORMULA_UNKNOWN:   a line referenced a `formula_id` that is not in the
#   canonical FORMULA_REGISTRY. Hard misconfiguration of the template.
ERR_NEEDS_QUOTE_INPUT = "NEEDS_QUOTE_INPUT"
ERR_FORMULA_UNKNOWN = "FORMULA_UNKNOWN"
ERR_FORMULA_INVALID = "FORMULA_INVALID"
ERR_CURRENCY_MISMATCH = "CURRENCY_MISMATCH"

# BLK-18 — Cost Engine Boundary Sprint: registry-sourced rate error codes.
# These are emitted when the CostEngine resolves rates from live registries
# (via load_material_cost_dict / load_workcenter_rate_dict bridges) and
# encounters missing or unresolvable entries.
BLK18_MATERIAL_COST_NOT_IN_REGISTRY = "BLK18:MATERIAL_COST_NOT_IN_REGISTRY"
BLK18_WORKCENTER_RATE_NOT_IN_REGISTRY = "BLK18:WORKCENTER_RATE_NOT_IN_REGISTRY"
BLK18_MACHINE_RATE_RESOLUTION_FAILED = "BLK18:MACHINE_RATE_RESOLUTION_FAILED"
BLK18_CONFIG_FALLBACK_USED = "BLK18:CONFIG_FALLBACK_USED"  # warning, not error
BLK18_REGISTRY_RATE_OVERRIDDEN = "BLK18:REGISTRY_RATE_OVERRIDDEN"  # info, not error


@dataclass
class ComponentCostContext:
    """Explicit rate contexts passed by the caller.

    - material_rates   : { material_code : unit_cost (RON / unit) }
    - workcenter_rates : { workcenter    : rate_per_hour (RON / h) }
    - quantity         : how many units of the template we are costing
    - quote_input      : Sprint #21.1 — per-quote-instance inputs consumed
                         by `calculation_type="formula_based"` lines.
                         IGNORED for static lines, so adding `quote_input`
                         to an existing context can NEVER change the result
                         of a legacy template.

    Both rate-map keys are case-sensitive and must match the strings stored
    in the template exactly. Missing entries are NOT silently defaulted.
    """

    material_rates: _Dict[str, float] = field(default_factory=dict)
    workcenter_rates: _Dict[str, Any] = field(default_factory=dict)
    quantity: int = 1  # how many units of the template we are costing
    quote_input: _Dict[str, Any] = field(default_factory=dict)
    base_currency: str = ""
    material_currencies: _Dict[str, str] = field(default_factory=dict)
    workcenter_currencies: _Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def normalize_currency(value: Any) -> str:
        return str(value or "").strip().upper()

    def material_currency_mismatch(
        self, *, code: str, path: str
    ) -> Optional[_Dict[str, str]]:
        """Return a CURRENCY_MISMATCH error dict when row currency != base."""
        if not self.base_currency:
            return None
        row_currency = self.material_currencies.get(code)
        if not row_currency:
            return None
        base = self.normalize_currency(self.base_currency)
        row = self.normalize_currency(row_currency)
        if row == base:
            return None
        return {
            "kind": ERR_CURRENCY_MISMATCH,
            "path": path,
            "detail": (
                f"material:{code}:row_currency={row}:base_currency={base}"
            ),
        }

    def workcenter_currency_mismatch(
        self, *, workcenter: str, path: str
    ) -> Optional[_Dict[str, str]]:
        if not self.base_currency:
            return None
        row_currency = self.workcenter_currencies.get(workcenter)
        if not row_currency:
            return None
        base = self.normalize_currency(self.base_currency)
        row = self.normalize_currency(row_currency)
        if row == base:
            return None
        return {
            "kind": ERR_CURRENCY_MISMATCH,
            "path": path,
            "detail": (
                f"workcenter:{workcenter}:row_currency={row}:base_currency={base}"
            ),
        }

    def material_rate(self, code: str) -> Optional[float]:
        if not code:
            return None
        val = self.material_rates.get(code)
        if val is None:
            return None
        try:
            v = float(val)
        except (TypeError, ValueError):
            return None
        return v if v > 0 else None

    def workcenter_rate(self, wc: str) -> Optional[float]:
        spec = self.workcenter_rate_spec(wc)
        if not spec or str(spec.get("rate_basis") or "") != "per_hour":
            return None
        return self._as_positive_float(spec.get("rate_per_hour"))

    def workcenter_rate_spec(self, wc: str) -> Optional[_Dict[str, Any]]:
        if not wc:
            return None
        val = self.workcenter_rates.get(wc)
        if val is None:
            return None

        if isinstance(val, dict):
            basis = str(val.get("rate_basis") or "per_hour").strip().lower()
            if basis not in {
                "per_hour",
                "per_linear_meter",
                "per_piece",
                "per_square_meter",
            }:
                return None
            return {
                "rate_basis": basis,
                "rate_per_hour": self._as_positive_float(val.get("rate_per_hour")),
                "rate_per_linear_meter": self._as_positive_float(
                    val.get("rate_per_linear_meter")
                ),
            }

        per_hour = self._as_positive_float(val)
        if per_hour is None:
            return None
        return {
            "rate_basis": "per_hour",
            "rate_per_hour": per_hour,
            "rate_per_linear_meter": None,
        }

    @staticmethod
    def _as_positive_float(val: Any) -> Optional[float]:
        try:
            v = float(val)
        except (TypeError, ValueError):
            return None
        return v if v > 0 else None


def _parse_json_field(raw: Any) -> Any:
    """Parse a JSON-encoded template field. Returns None if not parseable.

    Accepts already-decoded lists/dicts for convenience (the ORM sometimes
    returns them pre-parsed in other contexts).
    """
    if raw is None or raw == "":
        return None
    if isinstance(raw, (list, dict)):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        return _json.loads(raw)
    except (ValueError, TypeError):
        return None


def _detect_hierarchical(components_parsed: Any) -> bool:
    """True iff components_json holds the Sprint #15 hierarchical shape:
    a non-empty list whose first object-typed entry owns `materials` or
    `operations` arrays. A bare `string[]` (legacy) or plain objects
    without those arrays are NOT hierarchical.
    """
    if not isinstance(components_parsed, list) or not components_parsed:
        return False
    for entry in components_parsed:
        if isinstance(entry, dict):
            if isinstance(entry.get("materials"), list) or isinstance(
                entry.get("operations"), list
            ):
                return True
    return False


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        f = float(val)
    except (TypeError, ValueError):
        return default
    return f


def _extract_linear_meter_quantity(
    operation: _Dict[str, Any],
    *,
    formula_breakdown: Optional[_Dict[str, Any]] = None,
    formula_id: Optional[str] = None,
    formula_value: Optional[float] = None,
) -> Optional[float]:
    """Extract linear-meter quantity from explicit or equivalent fields.

    Accepted keys include canonical `total_cut_perimeter_m` and practical
    equivalents from existing templates/formulas. When a formula-based
    operation uses ``letter_perimeter``, the resolved metres may be taken
    from ``formula_breakdown`` / ``formula_value`` (no price literals).
    """
    for key in (
        "total_cut_perimeter_m",
        "linear_meter_quantity_m",
        "linear_meters",
        "cut_perimeter_m",
        "path_length_m",
    ):
        value = _safe_float(operation.get(key), 0.0)
        if value > 0:
            return value

    path_mm = _safe_float(operation.get("path_length_mm"), 0.0)
    if path_mm > 0:
        return path_mm / 1000.0

    breakdown = formula_breakdown
    if breakdown is None:
        raw = operation.get("formula_breakdown")
        breakdown = raw if isinstance(raw, dict) else None
    if isinstance(breakdown, dict):
        for key in (
            "total_pass_linear_m",
            "total_cut_perimeter_m",
            "linear_meter_quantity_m",
            "derived_total_length_m",
            "mounting_bar_length_m",
            "premount_bar_length_ml",
            "adjusted_perimeter_m",
            "letter_perimeter_m",
            "cut_perimeter_m",
            "path_length_m",
        ):
            value = _safe_float(breakdown.get(key), 0.0)
            if value > 0:
                return value
        path_mm = _safe_float(breakdown.get("path_length_mm"), 0.0)
        if path_mm > 0:
            return path_mm / 1000.0

    if formula_id in {"letter_perimeter", "perimeter_pass_linear_meter"} and (
        formula_value is not None
    ):
        value = _safe_float(formula_value, 0.0)
        if value > 0:
            return value

    if isinstance(breakdown, dict):
        total_pass = _safe_float(breakdown.get("total_pass_linear_m"), 0.0)
        if total_pass > 0:
            return total_pass

    return None


def _extract_piece_quantity(
    operation: _Dict[str, Any],
    *,
    formula_breakdown: Optional[_Dict[str, Any]] = None,
    formula_id: Optional[str] = None,
    formula_value: Optional[float] = None,
) -> Optional[float]:
    """Extract discrete piece/module/letter count for per_piece pricing."""
    breakdown = formula_breakdown
    if breakdown is None:
        raw = operation.get("formula_breakdown")
        breakdown = raw if isinstance(raw, dict) else None
    if isinstance(breakdown, dict):
        for key in ("letter_count", "led_module_count", "piece_count"):
            value = _safe_float(breakdown.get(key), 0.0)
            if value > 0:
                return value

    if formula_id in {"letter_count_material", "led_module_count"} and (
        formula_value is not None
    ):
        value = _safe_float(formula_value, 0.0)
        if value > 0:
            return value

    return None


def _extract_square_meter_quantity(
    operation: _Dict[str, Any],
    *,
    formula_breakdown: Optional[_Dict[str, Any]] = None,
    formula_id: Optional[str] = None,
    formula_value: Optional[float] = None,
) -> Optional[float]:
    """Extract area in m² for per_square_meter pricing."""
    breakdown = formula_breakdown
    if breakdown is None:
        raw = operation.get("formula_breakdown")
        breakdown = raw if isinstance(raw, dict) else None
    if isinstance(breakdown, dict):
        for key in (
            "letter_face_area_m2",
            "mounting_template_area_m2",
            "area_m2",
            "adjusted_area_m2",
            "face_vinyl_used_sqm",
        ):
            value = _safe_float(breakdown.get(key), 0.0)
            if value > 0:
                return value

    if formula_id in {"letter_face_area", "area_from_quote_input", "face_vinyl_used_sqm"} and (
        formula_value is not None
    ):
        value = _safe_float(formula_value, 0.0)
        if value > 0:
            return value

    return None


# ---------------------------------------------------------------------------
# Sprint #21.1 — formula-based detection + resolution
# ---------------------------------------------------------------------------
def _is_formula_based(entry: _Dict[str, Any]) -> bool:
    """True iff the material/operation entry declares itself formula-based.

    A line is formula-based **only** when `calculation_type == "formula_based"`
    (case-insensitive). Any other value — including missing / None / the
    explicit "static" — keeps the pre-Sprint-21.1 behaviour untouched.
    """
    if not isinstance(entry, dict):
        return False
    ct = entry.get("calculation_type")
    if not isinstance(ct, str):
        return False
    return ct.strip().lower() == "formula_based"


def _resolve_formula_line(
    entry: _Dict[str, Any],
    quote_input: _Dict[str, Any],
    expected_unit: str,
    path: str,
) -> _Dict[str, Any]:
    """Resolve a single formula-based line.

    Returns a dict with:
      - ``ok`` (bool): resolved successfully.
      - ``value`` (float | None): computed magnitude (quantity or minutes).
      - ``error`` (dict | None): engine-level error to record on the
        component, with canonical `kind` already mapped (NEEDS_QUOTE_INPUT,
        FORMULA_UNKNOWN, FORMULA_INVALID).
      - ``breakdown`` (dict): handler-provided intermediate values.

    The caller is responsible for:
      - multiplying ``value`` by the quantity multiplier,
      - translating the numeric value into money using the right rate,
      - appending the produced error (if any) to the component's errors.

    This helper NEVER raises and NEVER returns a numeric value together
    with a missing-input error — the two outcomes are strictly exclusive.
    """
    from services.formula_handlers import FormulaResult, resolve_formula

    formula_id = entry.get("formula_id")
    params = entry.get("formula_params") or {}
    required = entry.get("requires_quote_input") or []

    if not isinstance(formula_id, str) or not formula_id:
        return {
            "ok": False,
            "value": None,
            "breakdown": {},
            "error": {
                "kind": ERR_FORMULA_INVALID,
                "path": path,
                "detail": (
                    "formula_based line is missing a non-empty `formula_id`"
                ),
            },
        }
    if not isinstance(params, dict):
        return {
            "ok": False,
            "value": None,
            "breakdown": {},
            "error": {
                "kind": ERR_FORMULA_INVALID,
                "path": path,
                "detail": "`formula_params` must be an object",
            },
        }

    # Pre-check: any declared required key that is absent (or None) in the
    # quote_input must surface as NEEDS_QUOTE_INPUT, even if the handler
    # didn't technically consume it. This preserves the template author's
    # declared contract and gives the UI a stable "missing fields" list.
    declared_missing: _List[str] = []
    if isinstance(required, list):
        for key in required:
            if not isinstance(key, str) or not key:
                continue
            if key not in quote_input or quote_input.get(key) is None:
                declared_missing.append(key)

    if declared_missing:
        return {
            "ok": False,
            "value": None,
            "breakdown": {"missing": declared_missing},
            "error": {
                "kind": ERR_NEEDS_QUOTE_INPUT,
                "path": path,
                "detail": (
                    f"formula_based line requires quote_input keys "
                    f"{declared_missing} (formula_id={formula_id!r})"
                ),
            },
        }

    result: FormulaResult = resolve_formula(formula_id, params, quote_input)

    if result.resolved and result.value is not None:
        return {
            "ok": True,
            "value": float(result.value),
            "breakdown": dict(result.breakdown or {}),
            "error": None,
        }

    err = result.error or {}
    err_kind = str(err.get("kind", ""))
    missing = list(err.get("missing") or [])

    if err_kind == "UNKNOWN_FORMULA":
        return {
            "ok": False,
            "value": None,
            "breakdown": {},
            "error": {
                "kind": ERR_FORMULA_UNKNOWN,
                "path": path,
                "detail": str(err.get("detail") or "unknown formula_id"),
            },
        }
    if err_kind == "MISSING_INPUT":
        return {
            "ok": False,
            "value": None,
            "breakdown": {"missing": missing},
            "error": {
                "kind": ERR_NEEDS_QUOTE_INPUT,
                "path": path,
                "detail": (
                    f"formula_based line requires quote_input keys {missing} "
                    f"(formula_id={formula_id!r})"
                ),
            },
        }
    # INVALID_INPUT / INVALID_PARAM / any other failure surfaces as
    # FORMULA_INVALID — a hard, non-recoverable error: it means someone
    # passed a bogus value, not that they forgot to fill it in.
    return {
        "ok": False,
        "value": None,
        "breakdown": {"missing": missing},
        "error": {
            "kind": ERR_FORMULA_INVALID,
            "path": path,
            "detail": str(err.get("detail") or f"formula {formula_id!r} failed"),
        },
    }


def _normalize_component_meta(raw: Any, index: int) -> _Dict[str, str]:
    """Extract canonical {component_id, type, name} from a raw component entry.

    Used for both hierarchical objects and the flat-legacy synthetic wrapper.
    """
    if isinstance(raw, dict):
        cid = str(raw.get("component_id") or raw.get("id") or f"comp_{index + 1}") or f"comp_{index + 1}"
        ctype = str(raw.get("type") or "STRUCTURA").upper()
        cname = str(raw.get("name") or "")
        return {"component_id": cid, "type": ctype, "name": cname}
    if isinstance(raw, str):
        return {
            "component_id": f"comp_legacy_{index + 1}",
            "type": "STRUCTURA",
            "name": raw.strip(),
        }
    return {"component_id": f"comp_{index + 1}", "type": "STRUCTURA", "name": ""}


def _cost_one_component(
    raw_component: _Dict[str, Any],
    materials: _List[_Dict[str, Any]],
    operations: _List[_Dict[str, Any]],
    ctx: ComponentCostContext,
    path_prefix: str,
    index: int,
) -> _Dict[str, Any]:
    """Compute cost for a single component. Returns the component block
    that matches the documented output schema.
    """
    meta = _normalize_component_meta(raw_component, index)

    errors: _List[_Dict[str, str]] = []
    warnings: _List[_Dict[str, str]] = []
    materials_detail: _List[_Dict[str, Any]] = []
    operations_detail: _List[_Dict[str, Any]] = []

    material_cost = 0.0
    operation_cost = 0.0

    qty_multiplier = max(int(ctx.quantity or 1), 1)

    # --- Materials ------------------------------------------------------
    for j, mat in enumerate(materials or []):
        mat_path = f"{path_prefix}.materials[{j}]"
        if not isinstance(mat, dict):
            errors.append(
                {
                    "kind": ERR_MATERIAL_RATE_MISSING,
                    "path": mat_path,
                    "detail": "material row is not an object",
                }
            )
            continue
        code = str(mat.get("materialCode") or mat.get("material_code") or "").strip()
        unit = str(mat.get("unit") or "")

        skip_reason = should_skip_quote_input_gated_line(mat, ctx.quote_input or {})
        if skip_reason:
            materials_detail.append(
                {
                    "material_code": code,
                    "quantity": 0.0,
                    "unit": unit,
                    "unit_cost": 0.0,
                    "line_total": 0.0,
                    "path": mat_path,
                    "skipped": True,
                    "skip_reason": skip_reason,
                    "resolved": True,
                }
            )
            continue

        # Sprint #21.1 — resolve the `quantity` source for this line.
        # - STATIC (default, unchanged): pull from `mat["quantity"]`.
        # - FORMULA_BASED: resolve via `resolve_formula`, collect any
        #   NEEDS_QUOTE_INPUT / FORMULA_* errors, and treat the line as
        #   zero-cost only in the failure branch (while marking the
        #   result invalid).
        formula_breakdown: Optional[_Dict[str, Any]] = None
        formula_id_used: Optional[str] = None
        if _is_formula_based(mat):
            formula_id_used = str(mat.get("formula_id") or "")
            res = _resolve_formula_line(
                entry=mat,
                quote_input=ctx.quote_input or {},
                expected_unit=unit,
                path=mat_path,
            )
            if not res["ok"]:
                errors.append(res["error"])  # type: ignore[arg-type]
                materials_detail.append(
                    {
                        "material_code": code,
                        "quantity": 0.0,
                        "unit": unit,
                        "unit_cost": 0.0,
                        "line_total": 0.0,
                        "path": mat_path,
                        "calculation_type": "formula_based",
                        "formula_id": formula_id_used,
                        "formula_breakdown": res.get("breakdown") or {},
                        "resolved": False,
                    }
                )
                continue
            qty = float(res["value"] or 0.0) * qty_multiplier
            formula_breakdown = res.get("breakdown") or {}
        else:
            qty = _safe_float(mat.get("quantity"), 0.0) * qty_multiplier

        rate = ctx.material_rate(code)
        if rate is None:
            errors.append(
                {
                    "kind": ERR_MATERIAL_RATE_MISSING,
                    "path": mat_path,
                    "detail": (
                        f"no unit_cost for material_code={code!r}"
                        if code
                        else "material_code is empty"
                    ),
                }
            )
            line_total = 0.0
            unit_cost = 0.0
        else:
            unit_cost = rate
            mismatch = ctx.material_currency_mismatch(code=code, path=mat_path)
            if mismatch:
                errors.append(mismatch)
                line_total = 0.0
            else:
                line_total = round(unit_cost * qty, 4)
                material_cost += line_total
        mat_detail_row: _Dict[str, Any] = {
            "material_code": code,
            "quantity": qty,
            "unit": unit,
            "unit_cost": unit_cost,
            "line_total": round(line_total, 2),
            "path": mat_path,
        }
        if formula_id_used is not None:
            mat_detail_row["calculation_type"] = "formula_based"
            mat_detail_row["formula_id"] = formula_id_used
            mat_detail_row["formula_breakdown"] = formula_breakdown or {}
            mat_detail_row["resolved"] = True
        materials_detail.append(mat_detail_row)

    # --- Operations -----------------------------------------------------
    for j, op in enumerate(operations or []):
        op_path = f"{path_prefix}.operations[{j}]"
        if not isinstance(op, dict):
            errors.append(
                {
                    "kind": ERR_WORKCENTER_RATE_MISSING,
                    "path": op_path,
                    "detail": "operation row is not an object",
                }
            )
            continue
        code = str(op.get("code") or "").strip()
        wc = str(op.get("workcenter") or "").strip()

        from services.template_operation_policy import (
            is_internal_only_operation,
            should_skip_operation_costing,
        )

        op_skip_reason = should_skip_quote_input_gated_line(op, ctx.quote_input or {})
        if op_skip_reason:
            operations_detail.append(
                {
                    "code": code,
                    "workcenter": wc,
                    "estimated_minutes": 0.0,
                    "hours": 0.0,
                    "rate_per_hour": 0.0,
                    "rate_per_linear_meter": 0.0,
                    "linear_meters": 0.0,
                    "piece_quantity": 0.0,
                    "area_m2": 0.0,
                    "line_total": 0.0,
                    "path": op_path,
                    "skipped": True,
                    "skip_reason": op_skip_reason,
                    "resolved": True,
                }
            )
            continue

        if should_skip_operation_costing(op):
            minutes = _safe_float(
                op.get("estimatedMinutes") or op.get("estimated_minutes"), 0.0
            ) * qty_multiplier
            skip_basis = (
                "internal_only"
                if is_internal_only_operation(op)
                else "not_quote_priced"
            )
            operations_detail.append(
                {
                    "code": code,
                    "workcenter": wc,
                    "estimated_minutes": minutes,
                    "hours": round(minutes / 60.0, 4),
                    "rate_basis": skip_basis,
                    "rate_per_hour": 0.0,
                    "rate_per_linear_meter": 0.0,
                    "linear_meters": 0.0,
                    "piece_quantity": 0.0,
                    "area_m2": 0.0,
                    "line_total": 0.0,
                    "path": op_path,
                    "internal_only": is_internal_only_operation(op),
                    "quote_priced": False,
                    "duration_calibration_only": True,
                    "resolved": True,
                }
            )
            continue

        rate_spec = ctx.workcenter_rate_spec(wc)
        rate_basis = (
            str(rate_spec.get("rate_basis") or "per_hour")
            if rate_spec
            else "per_hour"
        )

        # Sprint #21.1 — resolve formula quantity or static minutes.
        op_formula_breakdown: Optional[_Dict[str, Any]] = None
        op_formula_id_used: Optional[str] = None
        op_formula_value: Optional[float] = None
        if _is_formula_based(op):
            op_formula_id_used = str(op.get("formula_id") or "")
            res = _resolve_formula_line(
                entry=op,
                quote_input=ctx.quote_input or {},
                expected_unit="min" if rate_basis == "per_hour" else "count",
                path=op_path,
            )
            if not res["ok"]:
                errors.append(res["error"])  # type: ignore[arg-type]
                operations_detail.append(
                    {
                        "code": code,
                        "workcenter": wc,
                        "estimated_minutes": 0.0,
                        "hours": 0.0,
                        "rate_per_hour": 0.0,
                        "line_total": 0.0,
                        "path": op_path,
                        "calculation_type": "formula_based",
                        "formula_id": op_formula_id_used,
                        "formula_breakdown": res.get("breakdown") or {},
                        "resolved": False,
                    }
                )
                continue
            op_formula_value = float(res["value"] or 0.0)
            op_formula_breakdown = res.get("breakdown") or {}
            if rate_basis == "per_hour":
                minutes = op_formula_value * qty_multiplier
            else:
                minutes = 0.0
        else:
            minutes = _safe_float(
                op.get("estimatedMinutes") or op.get("estimated_minutes"), 0.0
            ) * qty_multiplier

        hours = minutes / 60.0
        if not rate_spec:
            errors.append(
                {
                    "kind": ERR_WORKCENTER_RATE_MISSING,
                    "path": op_path,
                    "detail": (
                        f"no rate configuration for workcenter={wc!r}"
                        if wc
                        else "workcenter is empty"
                    ),
                }
            )
            line_total = 0.0
            rate_per_hour = 0.0
            rate_per_linear_meter = 0.0
            linear_meters = 0.0
            piece_quantity = 0.0
            area_m2 = 0.0
        else:
            rate_per_hour = _safe_float(rate_spec.get("rate_per_hour"), 0.0)
            rate_per_linear_meter = _safe_float(
                rate_spec.get("rate_per_linear_meter"), 0.0
            )
            linear_meters = 0.0
            piece_quantity = 0.0
            area_m2 = 0.0
            line_total = 0.0

            if rate_basis == "per_linear_meter":
                linear_meters = (
                    _extract_linear_meter_quantity(
                        op,
                        formula_breakdown=op_formula_breakdown,
                        formula_id=op_formula_id_used,
                        formula_value=op_formula_value,
                    )
                    or 0.0
                )
                if linear_meters <= 0:
                    errors.append(
                        {
                            "kind": ERR_WORKCENTER_LINEAR_METER_QUANTITY_MISSING,
                            "path": op_path,
                            "detail": (
                                "rate_basis='per_linear_meter' requires "
                                "letter_perimeter_m or equivalent linear quantity"
                            ),
                        }
                    )
                elif rate_per_linear_meter <= 0:
                    errors.append(
                        {
                            "kind": ERR_WORKCENTER_RATE_MISSING,
                            "path": op_path,
                            "detail": (
                                f"no rate_per_linear_meter for workcenter={wc!r}"
                            ),
                        }
                    )
                else:
                    wc_mismatch = ctx.workcenter_currency_mismatch(
                        workcenter=wc, path=op_path
                    )
                    if wc_mismatch:
                        errors.append(wc_mismatch)
                    else:
                        line_total = round(rate_per_linear_meter * linear_meters, 4)
                        operation_cost += line_total
            elif rate_basis == "per_piece":
                piece_quantity = (
                    _extract_piece_quantity(
                        op,
                        formula_breakdown=op_formula_breakdown,
                        formula_id=op_formula_id_used,
                        formula_value=op_formula_value,
                    )
                    or 0.0
                )
                if piece_quantity <= 0:
                    errors.append(
                        {
                            "kind": ERR_WORKCENTER_PIECE_QUANTITY_MISSING,
                            "path": op_path,
                            "detail": (
                                "rate_basis='per_piece' requires "
                                "letter_count or led_module_count quantity"
                            ),
                        }
                    )
                elif rate_per_linear_meter <= 0:
                    errors.append(
                        {
                            "kind": ERR_WORKCENTER_RATE_MISSING,
                            "path": op_path,
                            "detail": (
                                f"no per_piece unit rate for workcenter={wc!r}"
                            ),
                        }
                    )
                else:
                    wc_mismatch = ctx.workcenter_currency_mismatch(
                        workcenter=wc, path=op_path
                    )
                    if wc_mismatch:
                        errors.append(wc_mismatch)
                    else:
                        line_total = round(rate_per_linear_meter * piece_quantity, 4)
                        operation_cost += line_total
            elif rate_basis == "per_square_meter":
                area_m2 = (
                    _extract_square_meter_quantity(
                        op,
                        formula_breakdown=op_formula_breakdown,
                        formula_id=op_formula_id_used,
                        formula_value=op_formula_value,
                    )
                    or 0.0
                )
                if area_m2 <= 0:
                    errors.append(
                        {
                            "kind": ERR_WORKCENTER_AREA_QUANTITY_MISSING,
                            "path": op_path,
                            "detail": (
                                "rate_basis='per_square_meter' requires "
                                "letter_face_area_m2 or equivalent area quantity"
                            ),
                        }
                    )
                elif rate_per_linear_meter <= 0:
                    errors.append(
                        {
                            "kind": ERR_WORKCENTER_RATE_MISSING,
                            "path": op_path,
                            "detail": (
                                f"no per_square_meter unit rate for workcenter={wc!r}"
                            ),
                        }
                    )
                else:
                    wc_mismatch = ctx.workcenter_currency_mismatch(
                        workcenter=wc, path=op_path
                    )
                    if wc_mismatch:
                        errors.append(wc_mismatch)
                    else:
                        line_total = round(rate_per_linear_meter * area_m2, 4)
                        operation_cost += line_total
            else:
                if rate_per_hour <= 0:
                    errors.append(
                        {
                            "kind": ERR_WORKCENTER_RATE_MISSING,
                            "path": op_path,
                            "detail": (
                                f"no rate_per_hour for workcenter={wc!r}"
                            ),
                        }
                    )
                else:
                    wc_mismatch = ctx.workcenter_currency_mismatch(
                        workcenter=wc, path=op_path
                    )
                    if wc_mismatch:
                        errors.append(wc_mismatch)
                    else:
                        line_total = round(rate_per_hour * hours, 4)
                        operation_cost += line_total
        op_detail_row: _Dict[str, Any] = {
            "code": code,
            "workcenter": wc,
            "estimated_minutes": minutes,
            "hours": round(hours, 4),
            "rate_basis": rate_basis,
            "rate_per_hour": rate_per_hour,
            "rate_per_linear_meter": rate_per_linear_meter,
            "linear_meters": round(linear_meters, 4),
            "piece_quantity": round(piece_quantity, 4),
            "area_m2": round(area_m2, 4),
            "line_total": round(line_total, 2),
            "path": op_path,
        }
        if op_formula_id_used is not None:
            op_detail_row["calculation_type"] = "formula_based"
            op_detail_row["formula_id"] = op_formula_id_used
            op_detail_row["formula_breakdown"] = op_formula_breakdown or {}
            op_detail_row["resolved"] = True
        operations_detail.append(op_detail_row)

    # --- Empty component is a WARNING (not an error) --------------------
    if not (materials or operations):
        warnings.append(
            {
                "kind": WARN_COMPONENT_EMPTY,
                "path": path_prefix,
                "detail": f"component {meta['component_id']!r} has no materials and no operations",
            }
        )

    total_component_cost = round(material_cost + operation_cost, 2)

    return {
        "component_id": meta["component_id"],
        "type": meta["type"],
        "name": meta["name"],
        "material_cost": round(material_cost, 2),
        "operation_cost": round(operation_cost, 2),
        "total_component_cost": total_component_cost,
        "materials_detail": materials_detail,
        "operations_detail": operations_detail,
        "errors": errors,
        "warnings": warnings,
    }


def build_execution_layers_from_components(
    product_template: _Dict[str, Any],
    context: Optional[ComponentCostContext] = None,
) -> _Dict[str, Any]:
    """Sprint #16 — component-aware cost layer.

    See the module-level contract block above for the full schema and
    error semantics.

    Args:
      product_template: raw template dict as stored in `product_templates`
        (with `components_json`, `operations_json`, `required_materials_json`
        still being JSON strings — they are parsed here).
      context: ComponentCostContext with material_rates + workcenter_rates.
        If omitted, every line will produce a *_RATE_MISSING error.

    Returns:
      dict matching the schema described in the module contract.
    """
    ctx = context or ComponentCostContext()
    template = product_template or {}

    components_parsed = _parse_json_field(template.get("components_json"))
    ops_parsed = _parse_json_field(template.get("operations_json")) or []
    mats_parsed = _parse_json_field(template.get("required_materials_json")) or []

    hierarchical = _detect_hierarchical(components_parsed)

    component_blocks: _List[_Dict[str, Any]] = []

    if hierarchical:
        # ---- HIERARCHICAL branch (Sprint #15 shape) --------------------
        for i, raw_c in enumerate(components_parsed):  # type: ignore[arg-type]
            # Guaranteed to be a dict here (_detect_hierarchical checked at least one).
            # Non-dict stragglers are normalized for safety.
            if not isinstance(raw_c, dict):
                raw_c = {"component_id": f"comp_{i + 1}"}
            component_blocks.append(
                _cost_one_component(
                    raw_component=raw_c,
                    materials=list(raw_c.get("materials") or []),
                    operations=list(raw_c.get("operations") or []),
                    ctx=ctx,
                    path_prefix=f"components[{i}]",
                    index=i,
                )
            )
        source = "hierarchical"
    else:
        # ---- FLAT LEGACY branch ---------------------------------------
        # Everything is folded into ONE synthetic component so the output
        # schema is stable. Its type is STRUCTURA by convention; the
        # `_flat_legacy` suffix in component_id signals the fallback.
        synthetic = {
            "component_id": "comp_flat_legacy",
            "type": "STRUCTURA",
            "name": "Legacy flat template (fallback)",
        }
        component_blocks.append(
            _cost_one_component(
                raw_component=synthetic,
                materials=list(mats_parsed or []),
                operations=list(ops_parsed or []),
                ctx=ctx,
                path_prefix="components[0]",
                index=0,
            )
        )
        source = "flat_legacy"

    # --- Aggregates -----------------------------------------------------
    total_material_cost = round(sum(c["material_cost"] for c in component_blocks), 2)
    total_operation_cost = round(sum(c["operation_cost"] for c in component_blocks), 2)
    total_cost = round(total_material_cost + total_operation_cost, 2)

    merged_errors: _List[_Dict[str, str]] = []
    merged_warnings: _List[_Dict[str, str]] = []
    for c in component_blocks:
        merged_errors.extend(c["errors"])
        merged_warnings.extend(c["warnings"])

    is_valid = len(merged_errors) == 0

    return {
        "is_valid": is_valid,
        "source": source,
        "total_material_cost": total_material_cost,
        "total_operation_cost": total_operation_cost,
        "total_cost": total_cost,
        "components": component_blocks,
        "errors": merged_errors,
        "warnings": merged_warnings,
    }