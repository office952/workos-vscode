"""Upstream technical material requirement contract (quantity + ownership).

Freeze-time only. Does NOT:
- read Inventory / Pricing Registry / EIC heuristics
- coerce null → 0
- dedupe by material_code alone
- populate material_inputs / readiness
- rematerialize ExecutionPlan
"""

from __future__ import annotations

from typing import Any, Mapping

from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateComponent,
    ProductAggregateMaterial,
)
from services.formula_handlers import resolve_formula
from services.product_aggregate_planning_duration_service import (
    collect_planning_duration_facts,
)
from services.volumetric_quote_input_policy import normalize_face_finish_type

CONTRACT_VERSION = "technical_material_requirement/v1"

# Model E must never be used as technical quantity source.
REJECTED_QUANTITY_SOURCES = frozenset(
    {
        "inventory",
        "stock",
        "pricing_registry",
        "estimated_internal_cost",
        "cost_engine_heuristic",
    }
)

# Face finish alternatives without formula_params.gate in older seeds.
# Keyed by (material_code, component_ref) → required face_finish_type.
_FACE_FINISH_COMPONENT_GATES: dict[tuple[str, str], str] = {
    ("MAT-ORACAL-651", "comp_face_litere"): "oracal_651",
    ("MAT-VINYL-PRINT", "comp_face_litere"): "printed_vinyl",
    ("MAT-VINYL-PRINT-LAMINATED", "comp_face_litere"): "printed_laminated_vinyl",
}

# Generic parent lateral profile without depth gate — emit only when no sized
# depth variant is selected (depth unknown) OR when depth is explicitly unset.
# When a concrete depth is selected, sized child rows win and generic is suppressed.
_GENERIC_LATERAL_PROFILE_CODES = frozenset({"MAT-PROFIL-LATERAL-LITERE"})


def _as_facts(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = dict(payload or {})
    facts = collect_planning_duration_facts(payload)
    qg = payload.get("quote_geometry")
    if isinstance(qg, dict):
        for key, value in qg.items():
            if value is not None and key not in facts:
                facts[str(key)] = value
    fs = payload.get("finish_setup")
    if isinstance(fs, dict):
        for key, value in fs.items():
            if value is not None and key not in facts:
                facts[str(key)] = value
    # Canonical aliases used by gates / formulas.
    if "return_depth_mm" not in facts and facts.get("depth_mm") is not None:
        facts["return_depth_mm"] = facts["depth_mm"]
    if "face_finish_type" in facts:
        facts["face_finish_type"] = normalize_face_finish_type(facts.get("face_finish_type"))
    return facts


def _gate_dict(mat: ProductAggregateMaterial) -> dict[str, Any]:
    params = mat.formula_params if isinstance(mat.formula_params, dict) else {}
    gate = params.get("gate")
    return dict(gate) if isinstance(gate, dict) else {}


def _variant_discriminator(gate: Mapping[str, Any], *, face_finish: str | None = None) -> str | None:
    parts: list[str] = []
    for key in sorted(gate.keys()):
        parts.append(f"{key}={gate[key]}")
    if face_finish and not any(p.startswith("face_finish_type=") for p in parts):
        parts.append(f"face_finish_type={face_finish}")
    return ";".join(parts) if parts else None


def _requirement_id(mat: ProductAggregateMaterial, variant: str | None) -> str:
    bits = [
        str(mat.source_template_code or "").strip() or "tpl?",
        str(mat.component_ref or "").strip() or "comp?",
        str(mat.material_code or "").strip() or "mat?",
        str(mat.provenance or "").strip() or "prov?",
        variant or "novariant",
    ]
    return "|".join(bits)


def _coerce_gate_value(key: str, raw: Any) -> Any:
    if raw is None:
        return None
    if key.endswith("_mm") or key in {"return_depth_mm", "depth_mm"}:
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return raw
    if key == "face_finish_type":
        return normalize_face_finish_type(raw)
    if isinstance(raw, str):
        return raw.strip().lower()
    return raw


def _gate_matches(gate: Mapping[str, Any], facts: Mapping[str, Any]) -> bool:
    if not gate:
        return True
    for key, expected in gate.items():
        actual = facts.get(key)
        if key == "return_depth_mm" and actual is None:
            actual = facts.get("depth_mm")
        exp_n = _coerce_gate_value(str(key), expected)
        act_n = _coerce_gate_value(str(key), actual)
        if act_n is None:
            return False
        if exp_n != act_n:
            return False
    return True


def _face_finish_gate_for(mat: ProductAggregateMaterial) -> dict[str, Any] | None:
    code = str(mat.material_code or "").strip()
    cref = str(mat.component_ref or "").strip()
    expected = _FACE_FINISH_COMPONENT_GATES.get((code, cref))
    if expected is None:
        return None
    return {"face_finish_type": expected}


def _is_active_variant(mat: ProductAggregateMaterial, facts: Mapping[str, Any]) -> bool:
    gate = _gate_dict(mat)
    if gate and not _gate_matches(gate, facts):
        return False

    face_gate = _face_finish_gate_for(mat)
    if face_gate is not None and not _gate_matches(face_gate, facts):
        return False

    # Suppress generic lateral profile when a concrete depth is selected.
    code = str(mat.material_code or "").strip()
    if code in _GENERIC_LATERAL_PROFILE_CODES:
        depth = facts.get("return_depth_mm")
        if depth is None:
            depth = facts.get("depth_mm")
        if depth is not None:
            return False

    return True


def _owner_scope_for(mat: ProductAggregateMaterial) -> str:
    if mat.provenance == "linked_module":
        return "component_linked_module"
    if mat.provenance == "parent":
        return "component_parent"
    return "component"


def _evaluate_quantity(
    mat: ProductAggregateMaterial,
    facts: Mapping[str, Any],
) -> ProductAggregateMaterial:
    """Attach quantity contract fields. Never invent from inventory/pricing."""
    gate = _gate_dict(mat)
    face_gate = _face_finish_gate_for(mat) or {}
    merged_gate = {**face_gate, **gate}
    variant = _variant_discriminator(
        merged_gate,
        face_finish=str(face_gate.get("face_finish_type") or "") or None,
    )
    req_id = _requirement_id(mat, variant)
    owner = _owner_scope_for(mat)
    formula_id = (mat.formula_id or "").strip() or None
    params = dict(mat.formula_params or {})
    # Gates are selection metadata — strip before formula resolve.
    params.pop("gate", None)

    if not formula_id:
        return mat.model_copy(
            update={
                "requirement_id": req_id,
                "quantity": None,
                "quantity_status": "reference_only",
                "quantity_model": "D",
                "variant_discriminator": variant,
                "quantity_formula_id": None,
                "quantity_input_keys": [],
                "owner_scope": owner,
            }
        )

    result = resolve_formula(formula_id, params, dict(facts))
    if result.resolved and result.value is not None:
        # Explicit reject of zero masquerading from missing truth is handled by
        # formula handlers (resolved=False). A real zero is allowed if resolved.
        input_keys = sorted(
            {
                str(k)
                for k in (result.breakdown or {}).keys()
                if not str(k).startswith("_")
            }
        )
        return mat.model_copy(
            update={
                "requirement_id": req_id,
                "quantity": float(result.value),
                "quantity_status": "derived",
                "quantity_model": "A",
                "variant_discriminator": variant,
                "quantity_formula_id": formula_id,
                "quantity_input_keys": input_keys,
                "owner_scope": owner,
                # Prefer formula unit when template unit absent.
                "unit": mat.unit or (result.unit if result.unit else mat.unit),
            }
        )

    err = result.error or {}
    kind = str(err.get("kind") or "SOURCE_MISSING")
    missing = [str(x) for x in (err.get("missing") or []) if x]
    return mat.model_copy(
        update={
            "requirement_id": req_id,
            "quantity": None,
            "quantity_status": "source_missing",
            "quantity_model": "A",
            "variant_discriminator": variant,
            "quantity_formula_id": formula_id,
            "quantity_input_keys": missing,
            "owner_scope": owner,
            "status": "present" if kind != "UNKNOWN_FORMULA" else "present",
        }
    )


def apply_technical_material_requirements(
    aggregate: ProductAggregate,
    payload: Mapping[str, Any] | None,
) -> ProductAggregate:
    """Filter inactive variants and evaluate Model A/D quantities at freeze time."""
    facts = _as_facts(payload)
    materials_out: list[ProductAggregateMaterial] = []
    for mat in aggregate.materials:
        if not _is_active_variant(mat, facts):
            continue
        materials_out.append(_evaluate_quantity(mat, facts))

    components_out: list[ProductAggregateComponent] = []
    for comp in aggregate.components:
        comp_mats: list[ProductAggregateMaterial] = []
        for mat in comp.materials:
            if not _is_active_variant(mat, facts):
                continue
            comp_mats.append(_evaluate_quantity(mat, facts))
        components_out.append(comp.model_copy(update={"materials": comp_mats}))

    return aggregate.model_copy(
        update={
            "materials": materials_out,
            "components": components_out,
        }
    )


def assert_no_rejected_quantity_source(source: str | None) -> None:
    token = str(source or "").strip().lower()
    if token in REJECTED_QUANTITY_SOURCES:
        raise ValueError(f"rejected_technical_quantity_source:{token}")
