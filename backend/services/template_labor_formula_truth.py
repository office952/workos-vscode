"""Labor formula truth classification — LABOR_RECIPE_CONTRACT_V1_CLOSURE.

Attaches confirmed quantity keys and formula_status without inventing productivity.
"""

from __future__ import annotations

from typing import Any, Optional

# Evidence-backed VL quantity keys only (see VL_LABOR_FORMULA_EVIDENCE_MATRIX.md).
# Do NOT bind led_assembly_time defaults (throughput invent risk).
VL_QUANTITY_KEY_BY_CATALOG: dict[str, list[str]] = {
    "RETURN_PROFILE_FACE_BONDING": ["letter_perimeter_m"],
    "FACE_VINYL_APPLICATION_LABOR": ["letter_face_area_m2"],
    "LAMINATION": ["letter_face_area_m2"],
    "PAINTING": ["letter_perimeter_m"],
    "RETURN_CANT_RAL_PAINT_LABOR": ["letter_perimeter_m"],
    "RETURN_CANT_VINYL_APPLICATION_LABOR": ["letter_perimeter_m"],
    "LARGE_FORMAT_PRINT": ["letter_face_area_m2"],
    "LED_ASSEMBLY": ["letter_led_module_count"],
}

VL_MISSING_OWNER_CATALOGS: frozenset[str] = frozenset({"PACKAGING"})

VL_OPERATION_ONLY_CATALOGS: frozenset[str] = frozenset(
    {"PREPRESS", "ELECTRICAL_WIRING"}
)

# Commercial fixed-basis rules — formula confirmed without inventing rates.
COMMERCIAL_FIXED_FORMULA_OPS: frozenset[str] = frozenset({"MONTAJ"})

FORMULA_STATUS_LABEL_RO: dict[str, str] = {
    "FORMULA_CONFIRMED": "Formulă confirmată",
    "QUANTITY_KEY_CONFIRMED": "Cantitate preluată din Product Truth",
    "OPERATION_ONLY": "Operație definită, formulă lipsă",
    "MISSING_OWNER_FORMULA": "Necesită confirmare owner",
    "LEGACY_METADATA": "Metadate legacy — nefolosite",
    "NOT_APPLICABLE": "Nu se aplică",
}


def _registered_formula_ids() -> set[str]:
    try:
        from services.formula_handlers import FORMULA_REGISTRY

        return {str(k.value if hasattr(k, "value") else k) for k in FORMULA_REGISTRY}
    except Exception:
        return set()


def classify_labor_formula_truth(
    recipe: dict[str, Any],
    *,
    registered_formula_ids: Optional[set[str]] = None,
) -> dict[str, Any]:
    """Mutate-safe: returns additive truth fields for a labor recipe dict."""
    registered = registered_formula_ids if registered_formula_ids is not None else _registered_formula_ids()
    catalog = str(recipe.get("catalog_code") or "").strip().upper()
    op_code = str(recipe.get("operation_code") or "").strip().upper()
    formula_id = recipe.get("formula_id")
    formula_token = str(formula_id).strip() if formula_id else ""
    qty_keys = list(recipe.get("quantity_keys") or [])
    formula_owner = str(recipe.get("formula_owner") or "")
    warnings = list(recipe.get("warnings") or [])

    # Attach evidence-backed VL quantity keys (no productivity).
    mapped_keys = VL_QUANTITY_KEY_BY_CATALOG.get(catalog) or []
    if mapped_keys and not qty_keys:
        qty_keys = list(mapped_keys)
        recipe = {**recipe, "quantity_keys": qty_keys}

    status = "OPERATION_ONLY"
    formula_source: Optional[str] = None
    quantity_source: Optional[str] = None
    owner_confirmation_required = False
    unresolved_reason: Optional[str] = None
    evidence_level = "absent"

    if op_code in COMMERCIAL_FIXED_FORMULA_OPS or (
        formula_owner.startswith("commercial_rule") and catalog == "SITE_INSTALLATION_STANDARD"
    ):
        status = "FORMULA_CONFIRMED"
        formula_source = "commercial_rules_volumetric_v2:site_installation_standard"
        quantity_source = "fixed_locatie"
        evidence_level = "canonical"
    elif formula_token and formula_token in registered:
        # Registered handler — only confirm if not a known invent-risk throughput formula
        # unbound to this template recipe. led_assembly_time is deliberately excluded.
        if formula_token == "led_assembly_time":
            status = "QUANTITY_KEY_CONFIRMED" if qty_keys else "OPERATION_ONLY"
            formula_source = None
            quantity_source = "letter_led_module_count" if qty_keys else None
            unresolved_reason = (
                "led_assembly_time există în registry dar productivitatea default "
                "nu este confirmată owner pentru VL — folosim doar quantity key."
            )
            owner_confirmation_required = True
            evidence_level = "active"
            warnings.append("LED_ASSEMBLY_TIME_NOT_BOUND")
        else:
            status = "FORMULA_CONFIRMED"
            formula_source = f"formula_handlers:{formula_token}"
            evidence_level = "canonical"
    elif formula_token and formula_token not in registered:
        # Seed/op name without registered handler
        if qty_keys:
            status = "QUANTITY_KEY_CONFIRMED"
            quantity_source = ",".join(qty_keys)
            formula_source = f"legacy_unregistered:{formula_token}"
            warnings.append("LEGACY_FORMULA_NAME_UNREGISTERED")
            evidence_level = "active"
        else:
            status = "LEGACY_METADATA"
            formula_source = f"legacy_unregistered:{formula_token}"
            owner_confirmation_required = True
            unresolved_reason = (
                f"formula_id '{formula_token}' nu este în FORMULA_REGISTRY."
            )
            evidence_level = "reference"
    elif catalog in VL_MISSING_OWNER_CATALOGS:
        status = "MISSING_OWNER_FORMULA"
        owner_confirmation_required = True
        unresolved_reason = "Regulă comercială ambalare pending (VOL_V2_PACKAGING_PENDING)."
        evidence_level = "active"
    elif catalog in VL_OPERATION_ONLY_CATALOGS and not qty_keys:
        status = "OPERATION_ONLY"
        owner_confirmation_required = True
        unresolved_reason = (
            "Operație cunoscută; baza de consum (buc/circuit/job) neconfirmată."
        )
        evidence_level = "active"
    elif qty_keys:
        status = "QUANTITY_KEY_CONFIRMED"
        quantity_source = ",".join(qty_keys)
        formula_source = "product_truth_or_commercial_quantity"
        evidence_level = "canonical" if catalog in VL_QUANTITY_KEY_BY_CATALOG else "active"
    elif formula_owner in {
        "pricing_registry_template_filter",
        "commercial_rule_catalog_ref",
    }:
        status = "OPERATION_ONLY"
        owner_confirmation_required = True
        unresolved_reason = "Legătură catalog fără formulă/cantitate confirmată."
        evidence_level = "active"
    else:
        status = "OPERATION_ONLY"
        owner_confirmation_required = True
        unresolved_reason = "Consum de manoperă neconfirmat."
        evidence_level = "absent"

    # technical_ready: confirmed formula or confirmed quantity key
    technical_ready = status in {"FORMULA_CONFIRMED", "QUANTITY_KEY_CONFIRMED"}
    if recipe.get("formula_id") or qty_keys:
        # Ops-derived with any formula/qty also technical when already set true
        technical_ready = technical_ready or bool(recipe.get("technical_ready"))

    out = {
        **recipe,
        "quantity_keys": qty_keys,
        "formula_status": status,
        "formula_status_label_ro": FORMULA_STATUS_LABEL_RO.get(status, status),
        "formula_source": formula_source,
        "quantity_source": quantity_source,
        "owner_confirmation_required": owner_confirmation_required,
        "unresolved_reason": unresolved_reason,
        "evidence_level": evidence_level,
        "technical_ready": technical_ready,
        "warnings": warnings,
    }
    return out


def enrich_labor_recipes_formula_truth(
    recipes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    registered = _registered_formula_ids()
    return [
        classify_labor_formula_truth(r, registered_formula_ids=registered) for r in recipes
    ]
