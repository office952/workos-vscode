"""Template labor recipe extraction — application contract (no DB table).

Central catalog owns reusable rates. Template owns ops, formulas, qty keys.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Optional

from services.pricing_typed_catalog import (
    LABOR_CODES,
    SERVICE_CODES,
    classify_workcenter_typed_catalog,
)

LaborClass = str  # LABOR_INTERNAL | LABOR_COMMERCIAL | … (see CP0)

# Known WC aliases found on component modules — map to catalog codes when stable.
WC_ALIAS_TO_CATALOG: dict[str, str] = {
    "WC_ASSEMBLY": "ASSEMBLY",
    "WC_ELECTRICAL": "ELECTRICAL_WIRING",
    "WC_PACK": "PACKAGING",
    "WC_FINISH": "FACE_VINYL_APPLICATION_LABOR",
    "WC_PAINT": "PAINTING",
    "WC_FORMING": "RETURN_PROFILE_MACHINE_FORMING",
}

CPP_LABOR_CROSSWALK: dict[str, str] = {
    "ACM_BOXED_ASSEMBLY": "acm_boxed_assembly",
    "SITE_INSTALLATION_STANDARD": "montaj",
    "FACE_VINYL_APPLICATION_LABOR": "logo_application",
}


def _parse_json(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (list, dict)):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


def resolve_catalog_code(workcenter: str) -> str:
    wc = str(workcenter or "").strip()
    if not wc:
        return ""
    return WC_ALIAS_TO_CATALOG.get(wc.upper(), wc)


def recipe_role_for_code(code: str) -> str:
    c = str(code or "").upper()
    if "WIR" in c or "ELECTR" in c or "LED" in c:
        return "wiring"
    if "ASSEMB" in c or "BOND" in c:
        return "assembly"
    if "FINISH" in c or "VINYL" in c or "PAINT" in c or "LAMIN" in c:
        return "finishing"
    if "INSTALL" in c or "MOUNT" in c or "SITE_" in c:
        return "mounting"
    if "PACK" in c or "PREPRESS" in c or "QC_" in c:
        return "packaging"
    return "other"


def basis_from_rate_basis(rate_basis: str | None, unit: str | None) -> str:
    rb = str(rate_basis or "").lower()
    u = str(unit or "").lower()
    if "hour" in rb or u in {"h", "ora", "hour"}:
        return "hour"
    if "minute" in rb or u in {"min", "minute"}:
        return "minute"
    if "piece" in rb or "per_piece" in rb or u in {"buc", "pcs", "piece"}:
        return "buc"
    if "linear" in rb or u in {"ml", "m", "lm"}:
        return "ml"
    if "square" in rb or u in {"m2", "mp", "sqm"}:
        return "mp"
    if "set" in rb or u == "set":
        return "set"
    if "product" in rb or "locatie" in u:
        return "produs"
    return "unknown"


def labor_class_for(
    *,
    typed_catalog: str,
    catalog_code: str,
    status: str,
    has_commercial_map: bool,
) -> str:
    if status == "missing" or status == "MISSING_RATE":
        return "MISSING_RATE"
    tc = typed_catalog
    code = catalog_code.upper()
    if tc == "machine_operation":
        return "MACHINE_OPERATION"
    if code == "SITE_INSTALLATION_STANDARD" or tc == "service" and "INSTALL" in code:
        return "INSTALLATION_SERVICE"
    if code == "EXTERNAL_SUBCONTRACT":
        return "EXTERNAL_SERVICE"
    if tc == "service":
        return "INTERNAL_SERVICE"
    if tc == "labor":
        return "LABOR_COMMERCIAL" if has_commercial_map else "LABOR_INTERNAL"
    if tc == "unknown":
        return "UNKNOWN_AMBIGUOUS"
    return "LEGACY"


def iter_template_operations(row: Any) -> list[dict[str, Any]]:
    """Flatten operations from operations_json + component.operations."""
    ops: list[dict[str, Any]] = []
    top = _parse_json(getattr(row, "operations_json", None))
    if isinstance(top, list):
        for op in top:
            if isinstance(op, dict):
                ops.append({**op, "_source": "operations_json"})
    components = _parse_json(getattr(row, "components_json", None))
    if isinstance(components, list):
        for comp in components:
            if not isinstance(comp, dict):
                continue
            comp_id = str(comp.get("component_id") or comp.get("id") or "")
            for op in comp.get("operations") or []:
                if isinstance(op, dict):
                    ops.append(
                        {
                            **op,
                            "_source": "components_json",
                            "_component_id": comp_id,
                        }
                    )
    return ops


def quantity_keys_from_op(op: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    req = op.get("requires_quote_input") or op.get("quantity_keys") or []
    if isinstance(req, list):
        keys.extend(str(x) for x in req if x)
    elif isinstance(req, str) and req.strip():
        keys.append(req.strip())
    fp = op.get("formula_params")
    if isinstance(fp, dict):
        for k in ("quantity_key", "qty_key", "input_key"):
            if fp.get(k):
                keys.append(str(fp[k]))
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def build_labor_recipes(
    *,
    template_code: str,
    row: Any,
    registry_by_code: dict[str, dict[str, Any]],
    commercial_line_by_catalog: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Derive labor_recipes[] from template ops joined to central catalog."""
    commercial_line_by_catalog = commercial_line_by_catalog or {}
    recipes: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    # Collapse ops that appear both on operations_json and nested components.
    seen_op_formula: set[tuple[str, str, str]] = set()

    for op in iter_template_operations(row):
        raw_wc = str(op.get("workcenter") or op.get("workcenter_code") or "").strip()
        op_code = str(op.get("code") or op.get("operation_code") or "").strip()
        # Prefer a known pricing code on the op over a generic workcenter (e.g. ASSEMBLY).
        op_typed = classify_workcenter_typed_catalog(op_code) if op_code else "unknown"
        if op_typed in {"labor", "service", "machine_operation"}:
            catalog_code = resolve_catalog_code(op_code)
        elif raw_wc:
            catalog_code = resolve_catalog_code(raw_wc)
        else:
            continue
        if not op_code:
            op_code = catalog_code
        typed = classify_workcenter_typed_catalog(catalog_code)
        # Include labor + labor-adjacent services that operators treat as manoperă/serviciu
        if typed not in {"labor", "service", "unknown"}:
            continue
        if typed == "unknown" and catalog_code.upper() not in LABOR_CODES | SERVICE_CODES:
            # Keep unknown WC_* aliases that look labor-ish
            if not (
                catalog_code.upper().startswith("WC_")
                or "LABOR" in catalog_code.upper()
                or "ASSEMB" in catalog_code.upper()
            ):
                continue
        formula_id = op.get("formula_id") or op.get("formula")
        formula_token = str(formula_id).strip() if formula_id else "nof"
        component_id = str(op.get("_component_id") or "").strip()
        op_key = (op_code, catalog_code, formula_token)
        if op_key in seen_op_formula:
            continue
        # Stable identity: template + op + catalog + formula (+ component when present).
        identity_parts = [
            template_code,
            "labor_recipe",
            op_code,
            catalog_code,
            formula_token,
        ]
        if component_id:
            identity_parts.append(component_id)
        recipe_id = "::".join(identity_parts)
        if recipe_id in seen_ids:
            continue
        seen_ids.add(recipe_id)
        seen_op_formula.add(op_key)

        reg = registry_by_code.get(catalog_code) or registry_by_code.get(catalog_code.upper())
        quote_priced = op.get("quote_priced")
        if quote_priced is None:
            quote_priced = op.get("is_quote_priced")
        internal_only = bool(op.get("internal_only") or quote_priced is False)

        status = "active"
        blockers: list[str] = []
        warnings: list[str] = []
        flags: list[str] = []
        value = None
        currency = None
        unit = None
        rate_basis = None
        rate_source = "missing"
        dq_msg = None

        if reg:
            flags = list(reg.get("data_quality_flags") or [])
            value = reg.get("base_cost")
            currency = reg.get("currency")
            unit = reg.get("unit")
            rate_basis = reg.get("rate_basis")
            rate_source = "pricing_registry"
            dq_msg = reg.get("data_quality_message_ro")
            conf = str(reg.get("confidence") or "").lower()
            st = str(reg.get("status") or "").lower()
            if value is None or conf == "missing" or st == "missing_price":
                status = "missing"
                blockers.append("MISSING_CATALOG_RATE")
            elif flags:
                status = "warning"
                warnings.append("RATE_BASIS_COLUMN_MISMATCH")
        else:
            status = "missing"
            blockers.append("MISSING_CATALOG_RATE")
            if typed == "unknown":
                warnings.append("UNKNOWN_WORKCENTER_ALIAS")

        cpp_line = commercial_line_by_catalog.get(catalog_code) or CPP_LABOR_CROSSWALK.get(
            catalog_code.upper()
        )
        labor_class = labor_class_for(
            typed_catalog=typed,
            catalog_code=catalog_code,
            status=status,
            has_commercial_map=bool(cpp_line),
        )
        qty_keys = quantity_keys_from_op(op)
        technical_ready = bool(op_code and (formula_id or qty_keys or internal_only))
        commercial_ready = status == "active" and not internal_only and value is not None

        display = str(
            op.get("label")
            or op.get("name")
            or (reg or {}).get("display_name")
            or op_code
        )

        recipes.append(
            {
                "labor_recipe_id": recipe_id,
                "template_code": template_code,
                "operation_code": op_code,
                "catalog_code": catalog_code,
                "workcenter_declared": raw_wc,
                "operator_name": display,
                "labor_class": labor_class,
                "recipe_role": recipe_role_for_code(catalog_code),
                "quantity_keys": qty_keys,
                "formula_id": str(formula_id) if formula_id else None,
                "formula_owner": str(op.get("_source") or "product_template"),
                "basis": basis_from_rate_basis(rate_basis, unit),
                "rate_basis": rate_basis,
                "standard_time": op.get("standard_time") or op.get("standard_minutes"),
                "multiplier": op.get("complexity_multiplier") or op.get("multiplier"),
                "minimum": op.get("minimum") or op.get("min_charge"),
                "dependencies": {
                    "quote_priced": quote_priced,
                    "internal_only": internal_only,
                    "component_id": op.get("_component_id"),
                },
                "base_rate_source": rate_source,
                "internal_cost_rate": value,
                "commercial_rate": value if cpp_line and value is not None else None,
                "commercial_rate_status": (
                    "available"
                    if cpp_line and value is not None
                    else "unavailable"
                    if not cpp_line
                    else "missing"
                ),
                "unit": unit,
                "currency": currency,
                "status": status,
                "typed_catalog": typed,
                "data_quality_flags": flags,
                "data_quality_message_ro": dq_msg,
                "cpp_line_code": cpp_line,
                "eic_rule_code": None,
                "technical_ready": technical_ready,
                "commercial_ready": commercial_ready,
                "blockers": blockers,
                "warnings": warnings,
                "editable": False,
                "editability_reason_ro": (
                    "V1 este read-only — tarif central în catalog; rețeta pe template."
                ),
                "source_links": {
                    "pricing_manopera": (
                        f"/inventory/pricing?template={template_code}&catalog=manopera"
                    )
                },
                "provenance": f"template_op:{op.get('_source')}:{op_code}",
                "legacy": catalog_code.upper() != raw_wc.upper()
                or typed == "unknown",
                "confidence": "high"
                if status == "active" and technical_ready
                else "medium"
                if technical_ready
                else "low",
            }
        )

    # Catalog-only labor rows are NOT template recipes — ownership stays split.
    recipes.sort(key=lambda r: (r.get("recipe_role") or "", r.get("labor_recipe_id") or ""))
    return recipes


def merge_labor_from_pricing_recipe_items(
    *,
    template_code: str,
    pricing_items: Iterable[Any],
    existing: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Promote flat Studio labor/service rows when ops_json has no labor recipe yet.

    Used for VL registry-linked labor truth (often no ops workcenter). Does not invent rates.
    """
    out = list(existing)
    seen_catalog = {str(r.get("catalog_code") or "").upper() for r in out}
    seen_ids = {str(r.get("labor_recipe_id") or "") for r in out}

    for item in pricing_items:
        kind = getattr(item, "recipe_kind", None) or (
            item.get("recipe_kind") if isinstance(item, dict) else None
        )
        catalog_code = str(
            getattr(item, "catalog_code", None)
            or (item.get("catalog_code") if isinstance(item, dict) else None)
            or ""
        ).strip()
        stable_code = str(
            getattr(item, "stable_code", None)
            or (item.get("stable_code") if isinstance(item, dict) else None)
            or ""
        ).strip()
        if kind in {"labor", "service"}:
            if not catalog_code:
                catalog_code = stable_code
        elif kind == "commercial_line" and catalog_code:
            pass
        else:
            continue
        if not catalog_code or catalog_code.upper() in seen_catalog:
            continue
        typed = classify_workcenter_typed_catalog(catalog_code)
        if typed not in {"labor", "service"}:
            continue

        link_token = "registry_link" if kind != "commercial_line" else "commercial_link"
        op_token = stable_code or catalog_code
        recipe_id = (
            f"{template_code}::labor_recipe::{op_token}::{catalog_code}::{link_token}"
        )
        if recipe_id in seen_ids:
            continue

        status = str(getattr(item, "status", None) or "missing")
        value = getattr(item, "current_value", None)
        if isinstance(item, dict):
            status = str(item.get("status") or status)
            value = item.get("current_value")
        flags = list(
            getattr(item, "data_quality_flags", None)
            or (item.get("data_quality_flags") if isinstance(item, dict) else None)
            or []
        )
        qty_keys = list(
            getattr(item, "quantity_keys", None)
            or (item.get("quantity_keys") if isinstance(item, dict) else None)
            or []
        )
        unit = getattr(item, "unit", None) or (
            item.get("unit") if isinstance(item, dict) else None
        )
        currency = getattr(item, "currency", None) or (
            item.get("currency") if isinstance(item, dict) else None
        )
        operator_name = str(
            getattr(item, "operator_name", None)
            or (item.get("operator_name") if isinstance(item, dict) else None)
            or catalog_code
        )
        dq_msg = getattr(item, "data_quality_message_ro", None) or (
            item.get("data_quality_message_ro") if isinstance(item, dict) else None
        )
        cpp_line = getattr(item, "cpp_line_code", None) or (
            item.get("cpp_line_code") if isinstance(item, dict) else None
        ) or CPP_LABOR_CROSSWALK.get(catalog_code.upper())
        blockers = list(
            getattr(item, "blockers", None)
            or (item.get("blockers") if isinstance(item, dict) else None)
            or []
        )
        warnings = list(
            getattr(item, "warnings", None)
            or (item.get("warnings") if isinstance(item, dict) else None)
            or []
        )
        if kind == "commercial_line":
            warnings.append("COMMERCIAL_LINE_LABOR_REFERENCE")
        else:
            warnings.append("REGISTRY_LINKED_LABOR_NO_OPS_FORMULA")
        technical_ready = bool(qty_keys) or kind == "commercial_line"
        commercial_ready = status == "active" and value is not None
        formula_owner = (
            "commercial_rule_catalog_ref"
            if kind == "commercial_line"
            else "pricing_registry_template_filter"
        )
        provenance = (
            "commercial_rule:labor_catalog_ref"
            if kind == "commercial_line"
            else "pricing_registry:template_linked_labor"
        )

        out.append(
            {
                "labor_recipe_id": recipe_id,
                "template_code": template_code,
                "operation_code": op_token,
                "catalog_code": catalog_code,
                "workcenter_declared": catalog_code,
                "operator_name": operator_name,
                "labor_class": labor_class_for(
                    typed_catalog=typed,
                    catalog_code=catalog_code,
                    status=status if status != "warning" else "active",
                    has_commercial_map=bool(cpp_line),
                )
                if status != "missing"
                else "MISSING_RATE",
                "recipe_role": recipe_role_for_code(catalog_code),
                "quantity_keys": qty_keys,
                "formula_id": None,
                "formula_owner": formula_owner,
                "basis": basis_from_rate_basis(None, unit),
                "rate_basis": None,
                "standard_time": None,
                "multiplier": None,
                "minimum": None,
                "dependencies": {"quote_priced": None, "internal_only": False},
                "base_rate_source": "pricing_registry",
                "internal_cost_rate": value,
                "commercial_rate": value if cpp_line and value is not None else None,
                "commercial_rate_status": (
                    "available"
                    if cpp_line and value is not None
                    else "unavailable"
                ),
                "unit": unit,
                "currency": currency,
                "status": status,
                "typed_catalog": typed,
                "data_quality_flags": flags,
                "data_quality_message_ro": dq_msg,
                "cpp_line_code": cpp_line,
                "eic_rule_code": None,
                "technical_ready": technical_ready,
                "commercial_ready": commercial_ready,
                "blockers": blockers,
                "warnings": warnings,
                "editable": False,
                "editability_reason_ro": (
                    "V1 este read-only — tarif central în catalog; rețeta pe template."
                ),
                "source_links": {
                    "pricing_manopera": (
                        f"/inventory/pricing?template={template_code}&catalog=manopera"
                    )
                },
                "provenance": provenance,
                "legacy": True,
                "confidence": "medium" if status == "active" else "low",
            }
        )
        seen_catalog.add(catalog_code.upper())
        seen_ids.add(recipe_id)

    out.sort(key=lambda r: (r.get("recipe_role") or "", r.get("labor_recipe_id") or ""))
    return out
