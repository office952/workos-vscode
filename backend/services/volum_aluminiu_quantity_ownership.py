"""Quantity ownership for TPL-VOLUM-ALUMINIU_v1 / modelare_cant.

Confirmed return_cant perimeter owns component separate-calc qty and product-total
when present. quote_geometry is a controlled compatibility bridge / demoted legacy
fallback — never silent dual authority; diverge → fail closed.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from services.volum_aluminiu_component_contract import (
    BOM_COMPONENT_ID,
    CANONICAL_PERIMETER_UNIT,
    COMMERCIAL_BASIS_SYNONYM,
    COMMERCIAL_LINE_CODE,
    COMMERCIAL_RULE_CODE,
    INTERNAL_RULE_CODE,
    MINI_MODULE_CODE,
    PERIMETER_QTY_DECIMALS,
    PRICING_COMPONENT_CODE,
    TEMPLATE_CODE,
    extract_return_cant_instances,
    instance_has_confirmed_perimeter,
    round_perimeter_m,
)

QUOTE_GEOMETRY_CLASSIFICATION_BRIDGE = "compatibility_bridge"
QUOTE_GEOMETRY_CLASSIFICATION_LEGACY = "legacy_fallback"
QUOTE_GEOMETRY_CLASSIFICATION_DIVERGED = "diverged_fail_closed"
QUOTE_GEOMETRY_CLASSIFICATION_ABSENT = "absent"


def sum_confirmed_perimeter_m(instances: Mapping[str, Any] | None) -> tuple[float | None, list[str]]:
    """Sum confirmed perimeters across return_cant instances. Fail closed if any unconfirmed."""
    rows = instances or {}
    if not rows:
        return None, ["RETURN_CANT_INSTANCE_MISSING"]

    total = 0.0
    blockers: list[str] = []
    for key, inst in rows.items():
        if not isinstance(inst, Mapping):
            blockers.append(f"RETURN_CANT_INSTANCE_INVALID:{key}")
            continue
        if not instance_has_confirmed_perimeter(inst):
            blockers.append(f"RETURN_CANT_UNCONFIRMED:{key}")
            continue
        geometry = inst.get("geometry") if isinstance(inst.get("geometry"), Mapping) else {}
        total += float(geometry["confirmed_perimeter_m"])

    if blockers:
        return None, blockers
    if total <= 0:
        return None, ["RETURN_CANT_PERIMETER_NON_POSITIVE"]
    return round_perimeter_m(total), []


def _evidence_perimeter_m(payload: Mapping[str, Any] | None) -> float | None:
    if not isinstance(payload, Mapping):
        return None
    geom = payload.get("quote_geometry")
    if not isinstance(geom, Mapping):
        return None
    try:
        evidence = float(geom.get("letter_perimeter_m"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if evidence <= 0:
        return None
    return round_perimeter_m(evidence)


def _hydrate_return_cant_instances(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Prefer existing PT instances; else project confirmation bag via bridge (read-only)."""
    instances = extract_return_cant_instances(payload)
    if instances:
        return instances
    if not isinstance(payload, Mapping):
        return {}
    from services.return_cant_product_truth_bridge import build_return_cant_runtime_product_truth

    working = dict(payload)
    subtree = build_return_cant_runtime_product_truth(working)
    components = subtree.get("components") if isinstance(subtree, Mapping) else None
    return_cant = components.get("return_cant") if isinstance(components, Mapping) else None
    rows = return_cant.get("instances") if isinstance(return_cant, Mapping) else None
    if not isinstance(rows, Mapping):
        return {}
    return {str(k): v for k, v in rows.items() if isinstance(v, Mapping)}


def resolve_product_total_perimeter_authority(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Product-total perimeter authority for aluminium return / VL letter_perimeter_m.

    Prefer confirmed Product Truth. quote_geometry may remain only as:
    - compatibility bridge (derived from confirmed, same unit, provenance), or
    - demoted legacy fallback when confirmed absent (explicit warning).
    Divergence fail-closes.
    """
    instances = _hydrate_return_cant_instances(payload)
    confirmed_m, confirm_blockers = sum_confirmed_perimeter_m(instances)
    evidence_m = _evidence_perimeter_m(payload)

    if confirmed_m is not None:
        if evidence_m is not None and evidence_m != confirmed_m:
            return {
                "schema": "volum_aluminiu_product_total_perimeter_v1",
                "ok": False,
                "fail_closed": True,
                "quantity_m": None,
                "quantity_ml": None,
                "unit": CANONICAL_PERIMETER_UNIT,
                "authority": None,
                "source": None,
                "confirmed_perimeter_m": confirmed_m,
                "evidence_perimeter_m": evidence_m,
                "quote_geometry_classification": QUOTE_GEOMETRY_CLASSIFICATION_DIVERGED,
                "divergence": True,
                "divergence_delta_m": round_perimeter_m(abs(confirmed_m - evidence_m)),
                "warnings": ["quote_geometry_diverged_from_confirmed_product_truth"],
                "blockers": ["RETURN_CANT_PERIMETER_DIVERGENCE"],
                "parent_unconfirmed_fallback_used": False,
            }
        return {
            "schema": "volum_aluminiu_product_total_perimeter_v1",
            "ok": True,
            "fail_closed": False,
            "quantity_m": confirmed_m,
            "quantity_ml": confirmed_m,
            "unit": CANONICAL_PERIMETER_UNIT,
            "authority": "confirmed_product_truth",
            "source": "product_truth.components.return_cant.confirmed_perimeter_m",
            "confirmed_perimeter_m": confirmed_m,
            "evidence_perimeter_m": evidence_m,
            "quote_geometry_classification": (
                QUOTE_GEOMETRY_CLASSIFICATION_BRIDGE
                if evidence_m is not None
                else QUOTE_GEOMETRY_CLASSIFICATION_ABSENT
            ),
            "divergence": False,
            "divergence_delta_m": 0.0 if evidence_m is not None else None,
            "warnings": [],
            "blockers": [],
            "parent_unconfirmed_fallback_used": False,
        }

    if evidence_m is not None:
        return {
            "schema": "volum_aluminiu_product_total_perimeter_v1",
            "ok": True,
            "fail_closed": False,
            "quantity_m": evidence_m,
            "quantity_ml": evidence_m,
            "unit": CANONICAL_PERIMETER_UNIT,
            "authority": "quote_geometry_legacy_fallback",
            "source": "quote_geometry.letter_perimeter_m",
            "confirmed_perimeter_m": None,
            "evidence_perimeter_m": evidence_m,
            "quote_geometry_classification": QUOTE_GEOMETRY_CLASSIFICATION_LEGACY,
            "divergence": False,
            "divergence_delta_m": None,
            "warnings": [
                "quote_geometry_legacy_fallback",
                "confirmed_product_truth_perimeter_missing",
            ],
            "blockers": list(confirm_blockers),
            "parent_unconfirmed_fallback_used": True,
        }

    return {
        "schema": "volum_aluminiu_product_total_perimeter_v1",
        "ok": False,
        "fail_closed": True,
        "quantity_m": None,
        "quantity_ml": None,
        "unit": CANONICAL_PERIMETER_UNIT,
        "authority": None,
        "source": None,
        "confirmed_perimeter_m": None,
        "evidence_perimeter_m": None,
        "quote_geometry_classification": QUOTE_GEOMETRY_CLASSIFICATION_ABSENT,
        "divergence": False,
        "divergence_delta_m": None,
        "warnings": [],
        "blockers": confirm_blockers or ["RETURN_CANT_PERIMETER_MISSING"],
        "parent_unconfirmed_fallback_used": False,
    }


def apply_confirmed_perimeter_quote_geometry_bridge(
    payload: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project confirmed perimeter into quote_geometry for legacy CPP/EIC path readers.

    Does not persist. On divergence, clears letter_perimeter_m so extractors fail closed.
    """
    working: dict[str, Any] = deepcopy(dict(payload or {}))
    authority = resolve_product_total_perimeter_authority(working)
    geom = working.get("quote_geometry")
    out_geom = dict(geom) if isinstance(geom, Mapping) else {}

    if authority.get("fail_closed") and authority.get("divergence"):
        out_geom.pop("letter_perimeter_m", None)
        out_geom["letter_perimeter_authority"] = {
            "status": "diverged_fail_closed",
            "classification": QUOTE_GEOMETRY_CLASSIFICATION_DIVERGED,
            "confirmed_perimeter_m": authority.get("confirmed_perimeter_m"),
            "evidence_perimeter_m": authority.get("evidence_perimeter_m"),
            "unit": CANONICAL_PERIMETER_UNIT,
            "decimals": PERIMETER_QTY_DECIMALS,
        }
        working["quote_geometry"] = out_geom
        working["volum_aluminiu_perimeter_authority"] = authority
        return working, authority

    if authority.get("authority") == "confirmed_product_truth" and authority.get("quantity_m") is not None:
        qty = float(authority["quantity_m"])
        out_geom["letter_perimeter_m"] = qty
        out_geom["letter_perimeter_authority"] = {
            "status": "derived_from_confirmed_product_truth",
            "classification": QUOTE_GEOMETRY_CLASSIFICATION_BRIDGE,
            "source": authority.get("source"),
            "unit": CANONICAL_PERIMETER_UNIT,
            "commercial_basis_synonym": COMMERCIAL_BASIS_SYNONYM,
            "read_only_bridge": True,
            "parallel_authority": False,
        }
        working["quote_geometry"] = out_geom
        working["letter_perimeter_m"] = qty
        working["volum_aluminiu_perimeter_authority"] = authority
        return working, authority

    if authority.get("authority") == "quote_geometry_legacy_fallback":
        out_geom["letter_perimeter_authority"] = {
            "status": "legacy_fallback_demoted",
            "classification": QUOTE_GEOMETRY_CLASSIFICATION_LEGACY,
            "source": "quote_geometry.letter_perimeter_m",
            "unit": CANONICAL_PERIMETER_UNIT,
            "parallel_authority": False,
            "note": "Demoted from silent dual-authority; confirmed Product Truth preferred when present",
        }
        working["quote_geometry"] = out_geom
        working["volum_aluminiu_perimeter_authority"] = authority
        return working, authority

    working["volum_aluminiu_perimeter_authority"] = authority
    if out_geom:
        working["quote_geometry"] = out_geom
    return working, authority


def resolve_component_quantity_from_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Component-owned qty resolver for separate calc — no parent unconfirmed fallback."""
    instances = extract_return_cant_instances(payload)
    if not instances:
        instances = _hydrate_return_cant_instances(payload)
    qty_m, blockers = sum_confirmed_perimeter_m(instances)
    evidence = _evidence_perimeter_m(payload)

    return {
        "schema": "volum_aluminiu_component_quantity_v1",
        "template_code": TEMPLATE_CODE,
        "mini_module_code": MINI_MODULE_CODE,
        "unit": CANONICAL_PERIMETER_UNIT,
        "commercial_basis_synonym": COMMERCIAL_BASIS_SYNONYM,
        "quantity_m": qty_m,
        "quantity_ml": qty_m,  # synonym — same magnitude
        "source": "product_truth.components.return_cant.confirmed_perimeter_m"
        if qty_m is not None
        else None,
        "evidence_perimeter_m": evidence,
        "evidence_drives_calc": False,
        "parent_unconfirmed_fallback_used": False,
        "blockers": blockers,
        "ok": qty_m is not None and not blockers,
    }


def build_derived_quantities(
    *,
    quantity_m: float,
    depth_mm: int | None,
    finish_type: str | None,
) -> dict[str, Any]:
    """Component-owned derived qty map (no EP materialization)."""
    derived: dict[str, Any] = {
        "return_profile_linear_meter": quantity_m,
        "return_profile_linear_ml": quantity_m,
        "depth_mm": depth_mm,
    }
    # Wrap/paint area formulas are depth-sensitive on child PT; surface intent only here.
    if depth_mm is not None and finish_type:
        token = finish_type.strip().lower()
        if token in {"oracal_651", "oracal_641", "oracal_wrapped", "oracal", "vinyl", "colantat"}:
            derived["return_wrap_linear_meter"] = quantity_m
            derived["return_wrap_note"] = "area formula remains child material formula_id return_wrap_area"
        if token in {"ral_paint", "vopsit_ral", "ral", "painted", "paint"}:
            derived["return_paint_linear_meter"] = quantity_m
            derived["return_paint_note"] = "consumption formula remains child formula_id return_paint_consumption"
    return derived


def build_quantity_and_ops_ownership_view() -> dict[str, Any]:
    return {
        "quantity_ownership": {
            "primary_input": "confirmed_perimeter_m",
            "unit": CANONICAL_PERIMETER_UNIT,
            "commercial_basis": COMMERCIAL_BASIS_SYNONYM,
            "resolver": "resolve_component_quantity_from_payload",
            "parent_dependency": {
                "field": "quote_geometry.letter_perimeter_m",
                "role": "compatibility_bridge_or_legacy_fallback",
                "classification": "controlled_not_parallel_authority",
                "may_drive_separate_calc": False,
                "product_total": (
                    "prefer confirmed Product Truth; project bridge; "
                    "legacy fallback only when confirmed absent; diverge fail-closed"
                ),
            },
            "remaining_parent_deps": [
                "letter_group / layer mapping for instance keys",
            ],
            "dual_id": {
                "bom_component_id": BOM_COMPONENT_ID,
                "pricing_component_code": PRICING_COMPONENT_CODE,
                "policy": "explicit_IDENTITY_MAP_alias_not_second_bom_owner",
            },
            "product_total_resolver": "resolve_product_total_perimeter_authority",
            "quote_geometry_bridge": "apply_confirmed_perimeter_quote_geometry_bridge",
        },
        "materials_ops_ownership": {
            "owner_template": TEMPLATE_CODE,
            "bom_component_id": BOM_COMPONENT_ID,
            "materials": [
                "MAT-PROFIL-LATERAL-LITERE-30MM|60MM|80MM|100MM → return_profile_linear_meter",
                "MAT-ORACAL-651 → return_wrap_area (finish-gated)",
                "MAT-VOPSEA-RAL* → return_paint_consumption (finish-gated)",
                "MAT-ADEZIV-CANT-LITERE → return_profile_adhesive",
            ],
            "operations": [
                "RETURN_PROFILE_MACHINE_FORMING → return_profile_machine_forming",
                "RETURN_PROFILE_FACE_BONDING → return_profile_face_bonding (Aggregate modelare_cant)",
                "PAINTING → return_painting_linear_meter (finish-gated)",
            ],
            "aggregate_provenance": "linked_module",
            "commercial_ref": {
                "line_code": COMMERCIAL_LINE_CODE,
                "rule_code": COMMERCIAL_RULE_CODE,
                "basis": COMMERCIAL_BASIS_SYNONYM,
            },
            "internal_cost_ref": {
                "rule_code": INTERNAL_RULE_CODE,
                "basis": COMMERCIAL_BASIS_SYNONYM,
            },
            "execution_materialization": False,
        },
    }
