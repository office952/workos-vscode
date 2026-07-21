"""TPL-VOLUM-ALUMINIU_v1 component contract helpers — separate calc honesty.

No activation. No ComponentTemplate table. Geometry consume-only.
"""

from __future__ import annotations

from typing import Any, Mapping

TEMPLATE_CODE = "TPL-VOLUM-ALUMINIU_v1"
PARENT_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"
MINI_MODULE_CODE = "modelare_cant"
INSTANCE_SCHEMA_ID = "letter_group_instances.sidewall"
PT_CONTAINER = "product_truth.components.return_cant"
SHARED_CONTRACT_KEY = "volumetric_return_side"

# Dual identity (documented coupling — not two BOM owners)
BOM_COMPONENT_ID = "comp_volum_aluminiu_module"
PRICING_COMPONENT_CODE = "comp_lateral_litere"

CANONICAL_PERIMETER_UNIT = "m"
COMMERCIAL_BASIS_SYNONYM = "ml"  # 1 ml = 1 m; no conversion
PERIMETER_QTY_DECIMALS = 6

ALLOWED_DEPTH_MM: frozenset[int] = frozenset({30, 60, 80, 100})

ALLOWED_PERIMETER_SOURCES = frozenset(
    {
        "missing",
        "evidence_only",
        "operator_confirmed",
        "imported_verified_truth",
        "system_migration_verified",
    }
)
ALLOWED_CONFIRMED_PERIMETER_SOURCES = frozenset(
    {
        "operator_confirmed",
        "imported_verified_truth",
        "system_migration_verified",
    }
)
ALLOWED_CONFIRMATION_STATES = frozenset({"missing", "draft", "blocked", "confirmed"})
ALLOWED_CONFIRMATION_SOURCES = frozenset(
    {
        "operator_component_confirmation",
        "imported_verified_truth",
        "system_migration_verified",
    }
)

COMMERCIAL_LINE_CODE = "modelare_cant_aluminiu"
COMMERCIAL_RULE_CODE = "VOL_V2_RETURN_PROFILE_ML"
INTERNAL_RULE_CODE = "INT_VOL_V2_RETURN_ML"

PUBLICATION_REMAINS_BLOCKED = True
ACTIVATION_FORBIDDEN_IN_THIS_BUILD = True


def _positive_number(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def round_perimeter_m(value: float) -> float:
    return round(float(value), PERIMETER_QTY_DECIMALS)


def validate_confirmed_perimeter(
    *,
    confirmed_perimeter_m: Any,
    confirmed_perimeter_source: Any,
    unit: Any = CANONICAL_PERIMETER_UNIT,
) -> tuple[float | None, list[str]]:
    """Return (qty_m, blockers). Fail closed on unknown unit / non-positive / bad source."""
    blockers: list[str] = []
    unit_token = str(unit or "").strip().lower()
    if unit_token not in {"m", "ml", "meter", "metre", "meters", "metres"}:
        blockers.append("RETURN_CANT_PERIMETER_UNIT_INVALID")
        return None, blockers

    qty = _positive_number(confirmed_perimeter_m)
    if qty is None:
        blockers.append("RETURN_CANT_PERIMETER_NON_POSITIVE")
        return None, blockers

    source = str(confirmed_perimeter_source or "").strip()
    if source not in ALLOWED_CONFIRMED_PERIMETER_SOURCES:
        blockers.append("RETURN_CANT_PERIMETER_SOURCE_INVALID")
        return None, blockers

    return round_perimeter_m(qty), blockers


def extract_return_cant_instances(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    product_truth = payload.get("product_truth")
    if not isinstance(product_truth, Mapping):
        return {}
    components = product_truth.get("components")
    if not isinstance(components, Mapping):
        return {}
    return_cant = components.get("return_cant")
    if not isinstance(return_cant, Mapping):
        return {}
    instances = return_cant.get("instances")
    if not isinstance(instances, Mapping):
        return {}
    return {str(k): v for k, v in instances.items() if isinstance(v, Mapping)}


def instance_has_confirmed_perimeter(instance: Mapping[str, Any]) -> bool:
    geometry = instance.get("geometry") if isinstance(instance.get("geometry"), Mapping) else {}
    qty, blockers = validate_confirmed_perimeter(
        confirmed_perimeter_m=geometry.get("confirmed_perimeter_m"),
        confirmed_perimeter_source=geometry.get("confirmed_perimeter_source")
        or geometry.get("perimeter_source"),
        unit=geometry.get("unit") or CANONICAL_PERIMETER_UNIT,
    )
    if qty is None or blockers:
        return False
    state = str(instance.get("confirmation_state") or "").strip()
    source = str(instance.get("confirmation_source") or "").strip()
    if state != "confirmed":
        return False
    if source and source not in ALLOWED_CONFIRMATION_SOURCES:
        return False
    return True


def build_input_contract_view() -> dict[str, Any]:
    return {
        "template_code": TEMPLATE_CODE,
        "parent_template_code": PARENT_TEMPLATE_CODE,
        "mini_module_code": MINI_MODULE_CODE,
        "instance_schema_id": INSTANCE_SCHEMA_ID,
        "pt_container": PT_CONTAINER,
        "shared_contract_key": SHARED_CONTRACT_KEY,
        "canonical_perimeter_unit": CANONICAL_PERIMETER_UNIT,
        "commercial_basis_synonym": COMMERCIAL_BASIS_SYNONYM,
        "unit_note": "1 ml commercial = 1 m confirmed perimeter; no silent conversion",
        "allowed_depth_mm": sorted(ALLOWED_DEPTH_MM),
        "required_inputs": [
            {
                "key": "confirmed_perimeter_m",
                "path": f"{PT_CONTAINER}.instances.*.geometry.confirmed_perimeter_m",
                "unit": CANONICAL_PERIMETER_UNIT,
                "owner": "operator_confirm → product_truth",
                "drives_separate_calc": True,
            },
            {
                "key": "return_depth_mm",
                "path": f"{PT_CONTAINER}.instances.*.material_profile.width_mm",
                "unit": "mm",
                "owner": "component",
                "drives_separate_calc": True,
            },
            {
                "key": "finish_variant",
                "path": f"{PT_CONTAINER}.instances.*.finish_variant",
                "unit": None,
                "owner": "component",
                "drives_separate_calc": True,
            },
        ],
        "evidence_only_inputs": [
            {
                "key": "letter_perimeter_m",
                "path": "quote_geometry.letter_perimeter_m",
                "unit": CANONICAL_PERIMETER_UNIT,
                "maps_to": "geometry.evidence_perimeter_m",
                "drives_separate_calc": False,
            }
        ],
        "confirmation": {
            "state_field": "confirmation_state",
            "allowed_states": sorted(ALLOWED_CONFIRMATION_STATES),
            "allowed_sources": sorted(ALLOWED_CONFIRMATION_SOURCES),
            "forbidden_as_sole_confirmation": [
                "step1_layer_confirmation",
                "finish_setup.confirmed",
                "row confirmed",
                "quote_geometry.letter_perimeter_m",
                "analyzer evidence",
            ],
        },
        "provenance": {
            "allowed_perimeter_sources": sorted(ALLOWED_PERIMETER_SOURCES),
            "allowed_confirmed_perimeter_sources": sorted(ALLOWED_CONFIRMED_PERIMETER_SOURCES),
            "geometry_inputs_consume_only": True,
            "no_file_parse_in_workos": True,
        },
        "identity": {
            "bom_component_id": BOM_COMPONENT_ID,
            "pricing_component_code": PRICING_COMPONENT_CODE,
            "dual_id_policy": "bom_owner_vs_pricing_stub_documented",
        },
        "commercial": {
            "line_code": COMMERCIAL_LINE_CODE,
            "rule_code": COMMERCIAL_RULE_CODE,
            "basis": COMMERCIAL_BASIS_SYNONYM,
            "anti_hourly": True,
        },
        "internal_cost": {
            "rule_code": INTERNAL_RULE_CODE,
            "basis": COMMERCIAL_BASIS_SYNONYM,
            "anti_hourly": True,
        },
        "publication": {
            "remains_blocked": PUBLICATION_REMAINS_BLOCKED,
            "activation_forbidden_in_this_build": ACTIVATION_FORBIDDEN_IN_THIS_BUILD,
            "known_required_inactive_child": TEMPLATE_CODE,
        },
    }


def evaluate_separate_calculation_readiness(
    instances: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Contract-level separate-calc readiness (not publication / activation)."""
    rows = instances or {}
    if not rows:
        return {
            "status": "blocked",
            "separate_calculation": "FAIL",
            "reasons": ["RETURN_CANT_INSTANCE_MISSING"],
            "instance_count": 0,
            "confirmed_instance_count": 0,
            "publication_blocked": True,
            "activation_allowed": False,
        }

    confirmed = 0
    blockers: list[str] = []
    for key, inst in rows.items():
        if not isinstance(inst, Mapping):
            blockers.append(f"RETURN_CANT_INSTANCE_INVALID:{key}")
            continue
        if instance_has_confirmed_perimeter(inst):
            confirmed += 1
            continue
        for code in inst.get("blockers") or []:
            if isinstance(code, str) and code not in blockers:
                blockers.append(code)
        if "RETURN_CANT_CONFIRMED_PERIMETER_MISSING" not in blockers:
            blockers.append("RETURN_CANT_CONFIRMED_PERIMETER_MISSING")
        if str(inst.get("confirmation_state") or "") != "confirmed":
            if "RETURN_CANT_COMPONENT_CONFIRMATION_PENDING" not in blockers:
                blockers.append("RETURN_CANT_COMPONENT_CONFIRMATION_PENDING")

    if confirmed == len(rows) and confirmed > 0:
        return {
            "status": "ready",
            "separate_calculation": "PASS",
            "reasons": [],
            "instance_count": len(rows),
            "confirmed_instance_count": confirmed,
            "publication_blocked": True,
            "activation_allowed": False,
            "note": "Contract-complete for separate calc preview; publication/activation still blocked",
        }

    if confirmed > 0:
        return {
            "status": "partial",
            "separate_calculation": "PASS_WITH_WARNINGS",
            "reasons": blockers or ["RETURN_CANT_PARTIAL_CONFIRMATION"],
            "instance_count": len(rows),
            "confirmed_instance_count": confirmed,
            "publication_blocked": True,
            "activation_allowed": False,
        }

    return {
        "status": "blocked",
        "separate_calculation": "FAIL",
        "reasons": blockers or ["RETURN_CANT_CONFIRMED_PERIMETER_MISSING"],
        "instance_count": len(rows),
        "confirmed_instance_count": 0,
        "publication_blocked": True,
        "activation_allowed": False,
    }
