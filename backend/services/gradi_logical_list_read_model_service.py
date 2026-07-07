"""Read-only Gradi logical list read model.

Builds a logical trace from existing Intake V6 material-breakdown, priced dry-run,
and finish preferences. It does not calculate prices or mutate runtime state.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.cnc_machine_operation_pricing_read_model_service import (
    build_cnc_operation_pricing_overrides,
    build_shared_plexiglas_face_batch_overrides,
    resolve_cnc_perimeter_ml,
)
from services.intake_v4_nesting_material_precision import (
    compute_roll_nesting_vinyl_area_by_layer,
)
from services.intake_v6_material_breakdown_service import get_material_breakdown_for_workspace
from services.intake_v6_priced_quote_dry_run_service import build_intake_v6_priced_quote_dry_run
from services.intake_v6_workspace_service import _get_record_or_404, _json_loads
from services.shared_material_color_catalog_registry import (
    build_inventory_key_preview,
    get_compatible_cnc_operations,
    get_material_variant,
    resolve_oracal_variant,
    resolve_ral_variant,
)
from services.shared_vinyl_material_catalog import (
    get_oracal_profile_by_series,
    resolve_oracal_series_from_face_finish,
    resolve_owner_oracal_price_eur_per_sqm,
)

CORE_CATEGORY_MATERIALS = "MATERIALE"
CORE_CATEGORY_SERVICES = "SERVICII_OPERATII"
CORE_CATEGORY_LABOR = "MANOPERA"
ORACAL_BASIS_ROLL_NESTING = "roll_nesting_quote_estimate"
ORACAL_BASIS_AREA_FALLBACK = "area_with_waste_fallback"
MATERIAL_CATALOG_SOURCE = "shared_material_color_catalog_registry"
MATERIAL_CATALOG_VERSION = "readonly_seedless_v1"


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        return dumped if isinstance(dumped, dict) else {}
    if hasattr(value, "dict"):
        dumped = value.dict()
        return dumped if isinstance(dumped, dict) else {}
    return {
        key: getattr(value, key)
        for key in dir(value)
        if not key.startswith("_") and not callable(getattr(value, key))
    }


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _positive(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _rows(source: Any, attr: str) -> list[dict[str, Any]]:
    return [_as_dict(row) for row in _as_list(getattr(source, attr, []))]


def _row_key(row: dict[str, Any]) -> str:
    return str(row.get("material_key") or row.get("key") or row.get("operation_key") or row.get("code") or "")


def _row_label(row: dict[str, Any]) -> str:
    return str(row.get("display_name") or row.get("title") or row.get("label") or _row_key(row))


def _row_cost(row: dict[str, Any]) -> float | None:
    for key in ("estimated_cost", "material_cost", "subtotal"):
        value = row.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _sum_cost(rows: list[dict[str, Any]]) -> float | None:
    total = sum(float(value) for row in rows if (value := _row_cost(row)) is not None)
    return round(total, 4) if rows else None


def _sum_quantity(rows: list[dict[str, Any]]) -> float | None:
    total = sum(float(value) for row in rows if isinstance((value := row.get("quantity")), (int, float)))
    return round(total, 6) if rows else None


def _source(row: dict[str, Any]) -> str | None:
    return row.get("price_source") or row.get("pricing_status") or row.get("source")


def _cost(row: dict[str, Any]) -> float | None:
    return _row_cost(row)


def _child_ref(row: dict[str, Any]) -> dict[str, Any]:
    child = {
        "key": _row_key(row),
        "label": _row_label(row),
        "quantity": row.get("quantity"),
        "unit": row.get("unit"),
        "subtotal": _row_cost(row),
        "currency": row.get("currency"),
        "runtime_source": _source(row),
        "basis": row.get("quantity_basis") or row.get("basis_label") or row.get("basis_type"),
    }
    for key in (
        "series",
        "selected_series",
        "material_code",
        "source_part_ids",
        "trace_markers",
        "inventory_consumption_key",
        "inventory_color_keys",
        "group_keys",
        "color_breakdown",
    ):
        value = row.get(key)
        if value is not None:
            child[key] = value
    return child


def _set_catalog_metadata(
    target: dict[str, Any],
    *,
    material_variant_code: str | None,
    inventory_status: str,
    catalog_color_code: str | None = None,
    catalog_color_name: str | None = None,
    stock_identity_status: str | None = None,
) -> None:
    target["material_variant_code"] = material_variant_code
    target["inventory_status"] = inventory_status
    target["material_catalog_source"] = MATERIAL_CATALOG_SOURCE
    target["material_catalog_version"] = MATERIAL_CATALOG_VERSION

    if material_variant_code is None:
        target["inventory_key_preview"] = None
        target["stock_identity_status"] = stock_identity_status or "unknown"
        target["material_family"] = None
        target["material_series"] = None
        target["catalog_color_code"] = catalog_color_code
        target["catalog_color_name"] = catalog_color_name
        target["cnc_processable"] = False
        target["compatible_cnc_operations"] = []
        return

    variant = get_material_variant(material_variant_code)
    if variant is None:
        target["inventory_key_preview"] = None
        target["stock_identity_status"] = stock_identity_status or "unknown"
        target["material_family"] = None
        target["material_series"] = None
        target["catalog_color_code"] = catalog_color_code
        target["catalog_color_name"] = catalog_color_name
        target["cnc_processable"] = False
        target["compatible_cnc_operations"] = []
        return

    preview = build_inventory_key_preview(material_variant_code)
    target["inventory_key_preview"] = preview.preview_key
    target["stock_identity_status"] = stock_identity_status or preview.stock_identity_status
    target["material_family"] = variant.family_code
    target["material_series"] = variant.series_code
    target["catalog_color_code"] = catalog_color_code if catalog_color_code is not None else variant.color_code
    target["catalog_color_name"] = catalog_color_name if catalog_color_name is not None else variant.color_name
    target["cnc_processable"] = bool(variant.cnc_processable)
    target["compatible_cnc_operations"] = list(get_compatible_cnc_operations(material_variant_code))


def _enrich_oracal_color_breakdown_entry(series: str, entry: dict[str, Any]) -> None:
    color_code = str(entry.get("color_code") or "").strip()
    color_name = str(entry.get("color_name") or "").strip() or ("Unknown" if not color_code else None)
    variant = resolve_oracal_variant(series, color_code or None)
    if variant is None:
        _set_catalog_metadata(
            entry,
            material_variant_code=None,
            inventory_status="catalog_variant_missing",
            catalog_color_code=color_code or "UNKNOWN",
            catalog_color_name=color_name,
            stock_identity_status="unknown",
        )
        return

    _set_catalog_metadata(
        entry,
        material_variant_code=variant.material_variant_code,
        inventory_status="inventory_key_preview_ready" if color_code else "color_missing",
        catalog_color_code=color_code or "UNKNOWN",
        catalog_color_name=color_name or variant.color_name,
    )


def _enrich_oracal_child_row(child: dict[str, Any]) -> None:
    series = str(child.get("series") or child.get("selected_series") or "").strip()
    color_breakdown = child.get("color_breakdown") if isinstance(child.get("color_breakdown"), list) else []
    for entry in color_breakdown:
        if isinstance(entry, dict):
            _enrich_oracal_color_breakdown_entry(series, entry)

    single_color_entries = [entry for entry in color_breakdown if isinstance(entry, dict) and str(entry.get("color_code") or "").strip()]
    if len(single_color_entries) == 1:
        color_code = str(single_color_entries[0].get("color_code") or "").strip()
        color_name = str(single_color_entries[0].get("color_name") or "").strip() or None
        variant = resolve_oracal_variant(series, color_code)
        if variant is not None:
            _set_catalog_metadata(
                child,
                material_variant_code=variant.material_variant_code,
                inventory_status="inventory_key_preview_ready",
                catalog_color_code=color_code,
                catalog_color_name=color_name or variant.color_name,
            )
            return

    variant = resolve_oracal_variant(series, None)
    _set_catalog_metadata(
        child,
        material_variant_code=variant.material_variant_code if variant else None,
        inventory_status="pending_catalog_model" if len(single_color_entries) > 1 else "color_missing",
        catalog_color_code="UNKNOWN",
        catalog_color_name="Unknown",
        stock_identity_status="roll_pending" if variant else "unknown",
    )


def _resolve_plexiglas_variant_code(row: dict[str, Any], finish: dict[str, Any]) -> str:
    label = f"{row.get('display_label', '')} {row.get('material_name', '')}".lower()
    if "clear" in label or str(finish.get("face_finish_type") or "").strip().lower() == "plexiglas_clear":
        return "PLEXIGLAS_3MM_CLEAR"
    return "PLEXIGLAS_3MM_OPAL"


def _enrich_logical_list_material_metadata(rows: list[dict[str, Any]], finish: dict[str, Any]) -> None:
    by_id = {str(row.get("line_id")): row for row in rows if isinstance(row, dict)}

    oracal_parent = by_id.get("material.face_oracal")
    if isinstance(oracal_parent, dict):
        for child in oracal_parent.get("child_rows") or []:
            if isinstance(child, dict):
                _enrich_oracal_child_row(child)
        child_families = sorted({str(child.get("material_family")) for child in oracal_parent.get("child_rows") or [] if child.get("material_family")})
        _set_catalog_metadata(
            oracal_parent,
            material_variant_code=None,
            inventory_status="split_by_child_rows",
            stock_identity_status="not_required",
        )
        oracal_parent["material_series"] = str(oracal_parent.get("selected_series") or "multiple")
        oracal_parent["material_family"] = child_families[0] if len(child_families) == 1 else None
        oracal_parent["catalog_color_code"] = "UNKNOWN"
        oracal_parent["catalog_color_name"] = "Unknown"

    for line_id in ("material.plexiglas_face", "material.logo_plexiglas_face"):
        row = by_id.get(line_id)
        if not isinstance(row, dict):
            continue
        variant_code = _resolve_plexiglas_variant_code(row, finish)
        _set_catalog_metadata(
            row,
            material_variant_code=variant_code,
            inventory_status="batch_missing",
        )
        for child in row.get("child_rows") or []:
            if isinstance(child, dict):
                _set_catalog_metadata(
                    child,
                    material_variant_code=variant_code,
                    inventory_status="batch_missing",
                )

    forex_row = by_id.get("material.forex_backing")
    if isinstance(forex_row, dict):
        _set_catalog_metadata(
            forex_row,
            material_variant_code="FOREX_10MM_WHITE",
            inventory_status="batch_missing",
        )
        for child in forex_row.get("child_rows") or []:
            if isinstance(child, dict):
                _set_catalog_metadata(
                    child,
                    material_variant_code="FOREX_10MM_WHITE",
                    inventory_status="batch_missing",
                )

    return_row = by_id.get("material.return_profile")
    if isinstance(return_row, dict):
        return_finish = str(finish.get("return_finish_type") or finish.get("return_finish_system") or "").strip().lower()
        if return_finish in {"ral_paint", "ral", "paint", "vopsit", "painted"}:
            ral_code = str(finish.get("paint_ral_code") or finish.get("ral_color") or "").strip()
            paint_finish = str(finish.get("paint_finish") or "matte").strip().lower() or "matte"
            if ral_code:
                variant = resolve_ral_variant(ral_code, paint_finish)
                if variant is not None:
                    _set_catalog_metadata(
                        return_row,
                        material_variant_code=variant.material_variant_code,
                        inventory_status="process_pending",
                        catalog_color_code=variant.color_code,
                        catalog_color_name=str(finish.get("paint_ral_name") or variant.color_name),
                    )
                else:
                    _set_catalog_metadata(
                        return_row,
                        material_variant_code=None,
                        inventory_status="catalog_variant_missing",
                        catalog_color_code=ral_code.replace(" ", "_").upper(),
                        catalog_color_name=str(finish.get("paint_ral_name") or "").strip() or None,
                        stock_identity_status="process_pending",
                    )
                    return_row["material_family"] = "PAINT"
                    return_row["material_series"] = "RAL_PAINT"
            else:
                _set_catalog_metadata(
                    return_row,
                    material_variant_code=None,
                    inventory_status="ral_code_missing",
                    catalog_color_code="UNKNOWN",
                    catalog_color_name="Unknown",
                    stock_identity_status="unknown",
                )
                return_row["material_family"] = "PAINT"
                return_row["material_series"] = "RAL_PAINT"
        else:
            _set_catalog_metadata(
                return_row,
                material_variant_code="ALUMINUM_RETURN_GENERIC",
                inventory_status="inventory_key_preview_ready",
                catalog_color_code="UNKNOWN",
                catalog_color_name="Unknown",
            )


def _find(rows: list[dict[str, Any]], *tokens: str) -> list[dict[str, Any]]:
    lowered = [token.lower() for token in tokens]
    found: list[dict[str, Any]] = []
    for row in rows:
        haystack = f"{_row_key(row)} {_row_label(row)}".lower()
        if all(token in haystack for token in lowered):
            found.append(row)
    return found


def _first(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    return rows[0] if rows else None


def _line(
    *,
    line_id: str,
    display_label: str,
    category: str,
    formula_code: str,
    component_code: str | None,
    module_code: str | None,
    rows: list[dict[str, Any]] | None = None,
    status: str | None = None,
    gaps: list[str] | None = None,
    warnings: list[str] | None = None,
    blockers: list[str] | None = None,
    preferences: dict[str, Any] | None = None,
    quantity: float | int | None = None,
    unit: str | None = None,
    subtotal: float | None = None,
    currency: str | None = None,
    runtime_source: str | None = None,
    formula_status: str = "proposed_binding",
) -> dict[str, Any]:
    child_rows = [_child_ref(row) for row in (rows or [])]
    first = (rows or [None])[0]
    resolved_quantity = quantity if quantity is not None else (_sum_quantity(rows or []) if rows else None)
    resolved_unit = unit if unit is not None else (first.get("unit") if first else None)
    resolved_subtotal = subtotal if subtotal is not None else _sum_cost(rows or [])
    resolved_currency = currency if currency is not None else (first.get("currency") if first else None)
    resolved_source = runtime_source if runtime_source is not None else (_source(first) if first else None)
    resolved_status = status or ("MATCHED" if rows else "PARTIAL")
    resolved_source_part_ids = sorted(
        {
            str(part_id)
            for row in (rows or [])
            for part_id in (row.get("source_part_ids") or [])
            if isinstance(part_id, str) and part_id.strip()
        }
    )
    resolved_trace_markers = sorted(
        {
            str(marker)
            for row in (rows or [])
            for marker in (row.get("trace_markers") or [])
            if isinstance(marker, str) and marker.strip()
        }
    )
    return {
        "line_id": line_id,
        "display_label": display_label,
        "category": category,
        "product_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "component_code": component_code,
        "module_code": module_code,
        "formula_code_proposed": formula_code,
        "formula_version_proposed": "v1",
        "formula_status": formula_status,
        "status": resolved_status,
        "quantity": resolved_quantity,
        "unit": resolved_unit,
        "subtotal": resolved_subtotal,
        "currency": resolved_currency,
        "runtime_source": resolved_source,
        "child_rows": child_rows,
        "source_part_ids": resolved_source_part_ids,
        "trace_markers": resolved_trace_markers,
        "preferences": preferences or {},
        "gaps": gaps or [],
        "warnings": warnings or [],
        "blockers": blockers or [],
    }


def _finish(payload: dict[str, Any]) -> dict[str, Any]:
    finish = payload.get("finish_setup")
    return finish if isinstance(finish, dict) else {}


def _svg_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    analysis = payload.get("svg_analysis_json")
    return analysis if isinstance(analysis, dict) else {}


def _layer_role_setup(payload: dict[str, Any]) -> dict[str, Any] | None:
    layer_role_setup = payload.get("layer_role_setup")
    return layer_role_setup if isinstance(layer_role_setup, dict) else None


def _quote_geometry(payload: dict[str, Any]) -> dict[str, Any]:
    geometry = payload.get("quote_geometry")
    return geometry if isinstance(geometry, dict) else {}


def _has_confirmed_letter_face_content(payload: dict[str, Any]) -> bool:
    finish = _finish(payload)
    setup = _layer_role_setup(payload)
    groups = finish.get("letter_group_finishes") or []
    if isinstance(groups, list) and groups:
        return True
    layers = setup.get("layers") if isinstance(setup, dict) else None
    if isinstance(layers, list):
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            if str(layer.get("confirmation_state") or "").strip().lower() == "ignored":
                continue
            role = str(layer.get("confirmed_role") or layer.get("auto_role") or "").strip().lower()
            if role == "face":
                return True
    return False


def _oracal_preferences(finish: dict[str, Any]) -> list[dict[str, Any]]:
    prefs: list[dict[str, Any]] = []
    for row in finish.get("letter_group_finishes") or []:
        if isinstance(row, dict) and str(row.get("face_finish_type") or "").startswith("oracal"):
            prefs.append(row)
    for row in finish.get("artwork_finishes") or []:
        if not isinstance(row, dict):
            continue
        method = str(row.get("face_personalization_method") or "")
        material = str(row.get("material_code") or "")
        if method == "oracal" or material.startswith("ORACAL"):
            prefs.append(row)
    return prefs


def _artwork_preferences(finish: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in (finish.get("artwork_finishes") or []) if isinstance(row, dict)]


def _resolve_oracal_series(pref: dict[str, Any]) -> str | None:
    face_finish_type = str(pref.get("face_finish_type") or "").strip().lower()
    series = resolve_oracal_series_from_face_finish(face_finish_type)
    if series:
        return series
    material_code = str(pref.get("material_code") or "").strip().upper().replace("-", "_")
    if material_code in {"ORACAL_641", "MAT_ORACAL_641"}:
        return "641"
    if material_code in {"ORACAL_651", "MAT_ORACAL_651"}:
        return "651"
    if material_code in {"ORACAL_8500", "MAT_ORACAL_8500", "MAT_ORACAL_8500_TRANSLUCENT"}:
        return "8500"
    if str(pref.get("face_personalization_method") or "").strip().lower() == "oracal":
        return "651"
    return None


def _oracal_role(pref: dict[str, Any]) -> str:
    return "LOGO_FACE" if pref.get("layer_key") else "LETTER_FACE"


def _pref_candidates(pref: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    candidates: list[str] = []
    for key in (
        "group_key",
        "layer_key",
        "layer_name",
        "display_name",
        "source_layer_name",
        "original_detected_label",
    ):
        raw = pref.get(key)
        if not isinstance(raw, str):
            continue
        token = raw.strip()
        if token and token not in seen:
            seen.add(token)
            candidates.append(token)
    return candidates


def _analysis_layer_area(analysis: dict[str, Any], candidates: list[str]) -> tuple[float | None, str | None]:
    if not candidates:
        return None, None
    candidate_set = {candidate.strip() for candidate in candidates if candidate.strip()}
    for layer in analysis.get("layers") or []:
        if not isinstance(layer, dict):
            continue
        layer_id = str(layer.get("id") or "").strip()
        layer_name = str(layer.get("name") or "").strip()
        if layer_id not in candidate_set and layer_name not in candidate_set:
            continue
        area = _positive(layer.get("filledAreaSqm")) or _positive(layer.get("boundingAreaSqm"))
        if area is not None:
            return round(area, 4), layer_id or layer_name
    return None, None


def _first_present_area(pref: dict[str, Any]) -> float | None:
    for key in ("face_area_m2", "estimated_area_m2"):
        area = _positive(pref.get(key))
        if area is not None:
            return round(area, 4)
    return None


def _runtime_material_quantity(rows: list[dict[str, Any]]) -> float | None:
    for row in rows:
        quantity = _positive(row.get("quantity"))
        if quantity is not None:
            return round(quantity, 4)
        quantity = _positive(row.get("base_quantity"))
        if quantity is not None:
            return round(quantity, 4)
    return None


def _runtime_material_total_quantity(rows: list[dict[str, Any]]) -> float | None:
    total = 0.0
    found = False
    for row in rows:
        quantity = _positive(row.get("quantity"))
        if quantity is None:
            quantity = _positive(row.get("base_quantity"))
        if quantity is None:
            continue
        total += quantity
        found = True
    return round(total, 4) if found else None


def _runtime_material_subtotal(rows: list[dict[str, Any]]) -> float | None:
    subtotal = _sum_cost(rows)
    return round(subtotal, 4) if subtotal is not None else None


def _runtime_material_source_part_ids(rows: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(part_id)
            for row in rows
            for part_id in (row.get("source_part_ids") or [])
            if isinstance(part_id, str) and part_id.strip()
        }
    )


def _runtime_material_rows_with_prefix(rows: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    return [row for row in rows if _row_key(row).startswith(prefix)]


def _build_oracal_fallback_rows(
    *,
    workspace_payload: dict[str, Any],
    oracal_prefs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    analysis = _svg_analysis(workspace_payload)
    nesting = analysis.get("nesting") if isinstance(analysis.get("nesting"), dict) else None
    layer_role_setup = _layer_role_setup(workspace_payload)
    roll_area_by_layer = compute_roll_nesting_vinyl_area_by_layer(
        nesting,
        layer_role_setup=layer_role_setup,
    )

    source_groups: list[dict[str, Any]] = []
    series_totals: dict[str, dict[str, Any]] = {}
    source_roles: set[str] = set()
    affected_group_keys: list[str] = []

    for pref in oracal_prefs:
        series = _resolve_oracal_series(pref)
        if not series:
            continue
        candidates = _pref_candidates(pref)
        area = None
        area_source = None
        matched_layer = None
        for candidate in candidates:
            candidate_area = _positive(roll_area_by_layer.get(candidate))
            if candidate_area is not None:
                area = round(candidate_area, 4)
                area_source = ORACAL_BASIS_ROLL_NESTING
                matched_layer = candidate
                break
        if area is None:
            area = _first_present_area(pref)
            if area is not None:
                area_source = ORACAL_BASIS_AREA_FALLBACK
        if area is None:
            area, matched_layer = _analysis_layer_area(analysis, candidates)
            if area is not None:
                area_source = ORACAL_BASIS_AREA_FALLBACK

        profile = get_oracal_profile_by_series(series)
        tariff = resolve_owner_oracal_price_eur_per_sqm(series)
        tariff_value = tariff[0] if tariff else None
        tariff_currency = tariff[1] if tariff else None
        tariff_source = tariff[2] if tariff else None
        subtotal = round(area * tariff_value, 4) if area is not None and tariff_value is not None else None
        role = _oracal_role(pref)
        source_roles.add(role)
        group_ref = str(
            pref.get("group_key")
            or pref.get("layer_key")
            or matched_layer
            or (candidates[0] if candidates else "oracal_pref")
        )
        affected_group_keys.append(group_ref)
        source_groups.append(
            {
                "group_key": group_ref,
                "source_role": role,
                "series": series,
                "material_code": f"ORACAL_{series}",
                "inventory_consumption_key": f"ORACAL_{series}_{str(pref.get('face_oracal_code') or 'UNSPECIFIED').strip() or 'UNSPECIFIED'}",
                "color_code": pref.get("face_oracal_code"),
                "color_name": pref.get("face_oracal_name"),
                "quantity": area,
                "unit": "m2" if area is not None else None,
                "subtotal": subtotal,
                "currency": tariff_currency,
                "quantity_source": area_source,
                "matched_layer": matched_layer,
            }
        )
        bucket = series_totals.setdefault(
            series,
            {
                "series": series,
                "quantity": 0.0,
                "subtotal": 0.0,
                "has_quantity": False,
                "has_subtotal": False,
                "material_code": f"ORACAL_{series}",
                "material_name": profile.display_name if profile else f"Oracal {series}",
                "tariff_source": tariff_source,
                "tariff_status": "OWNER_CONFIRMED_INTERIM" if tariff_value is not None else "MISSING",
                "tariff_eur_per_m2": tariff_value,
                "roll_widths_mm": set(),
                "group_keys": [],
                "quantity_sources": set(),
                "color_codes": set(),
                "color_breakdown": {},
            },
        )
        if area is not None:
            bucket["quantity"] += area
            bucket["has_quantity"] = True
        if subtotal is not None:
            bucket["subtotal"] += subtotal
            bucket["has_subtotal"] = True
        if isinstance(pref.get("face_vinyl_roll_width_mm"), (int, float)):
            bucket["roll_widths_mm"].add(int(pref["face_vinyl_roll_width_mm"]))
        elif isinstance(pref.get("face_roll_width_mm"), (int, float)):
            bucket["roll_widths_mm"].add(int(pref["face_roll_width_mm"]))
        if area_source:
            bucket["quantity_sources"].add(area_source)
        bucket["group_keys"].append(group_ref)
        color_code = str(pref.get("face_oracal_code") or "").strip()
        color_name = str(pref.get("face_oracal_name") or "").strip() or None
        if color_code:
            bucket["color_codes"].add(color_code)
            color_bucket = bucket["color_breakdown"].setdefault(
                color_code,
                {
                    "color_code": color_code,
                    "color_name": color_name,
                    "quantity": 0.0,
                    "subtotal": 0.0,
                    "has_quantity": False,
                    "has_subtotal": False,
                    "group_keys": [],
                    "inventory_consumption_key": f"ORACAL_{series}_{color_code}",
                },
            )
            if area is not None:
                color_bucket["quantity"] += area
                color_bucket["has_quantity"] = True
            if subtotal is not None:
                color_bucket["subtotal"] += subtotal
                color_bucket["has_subtotal"] = True
            color_bucket["group_keys"].append(group_ref)

    synthetic_rows: list[dict[str, Any]] = []
    for series in sorted(series_totals):
        bucket = series_totals[series]
        synthetic_rows.append(
            {
                "material_key": f"face_vinyl_{series}",
                "display_name": f"Vinil fata Oracal {series}",
                "quantity": round(bucket["quantity"], 4) if bucket["has_quantity"] else None,
                "unit": "m2" if bucket["has_quantity"] else None,
                "estimated_cost": round(bucket["subtotal"], 4) if bucket["has_subtotal"] else None,
                "material_cost": round(bucket["subtotal"], 4) if bucket["has_subtotal"] else None,
                "currency": "EUR" if bucket["has_subtotal"] else None,
                "price_source": bucket["tariff_source"],
                "series": series,
                "selected_series": series,
                "material_code": bucket["material_code"],
                "inventory_consumption_key": f"ORACAL_{series}",
                "inventory_color_keys": sorted(bucket["color_codes"]),
                "group_keys": list(bucket["group_keys"]),
                "color_breakdown": [
                    {
                        "color_code": color_bucket["color_code"],
                        "color_name": color_bucket["color_name"],
                        "quantity": round(color_bucket["quantity"], 4) if color_bucket["has_quantity"] else None,
                        "unit": "m2" if color_bucket["has_quantity"] else None,
                        "subtotal": round(color_bucket["subtotal"], 4) if color_bucket["has_subtotal"] else None,
                        "currency": "EUR" if color_bucket["has_subtotal"] else None,
                        "group_keys": list(color_bucket["group_keys"]),
                        "inventory_consumption_key": color_bucket["inventory_consumption_key"],
                    }
                    for color_bucket in bucket["color_breakdown"].values()
                ],
                "quantity_basis": (
                    next(iter(bucket["quantity_sources"]))
                    if len(bucket["quantity_sources"]) == 1
                    else "mixed_oracal_area_sources"
                ),
            }
        )

    area_missing = any(group.get("quantity") is None for group in source_groups)
    tariff_missing = any(group.get("subtotal") is None for group in source_groups)
    total_quantity = _sum_quantity(synthetic_rows)
    total_subtotal = _sum_cost(synthetic_rows)
    primary_series = None
    if series_totals:
        primary_series = max(
            series_totals.items(),
            key=lambda item: (item[1]["quantity"] if item[1]["has_quantity"] else 0.0, item[0]),
        )[0]
    primary_bucket = series_totals.get(primary_series or "")
    series_codes = sorted(series_totals)
    is_multi_series = len(series_codes) > 1
    top_level_label = "Vinil fata Oracal"
    if is_multi_series:
        top_level_label = f"Vinil fata Oracal - consum pe serii {' + '.join(series_codes)}"
    elif primary_series:
        top_level_label = f"Vinil fata Oracal {primary_series}"
    metadata = {
        "display_label": top_level_label,
        "status": (
            "PARTIAL"
            if area_missing or tariff_missing
            else "PARTIAL_TARIFF_CONFIRMATION_REQUIRED"
        ),
        "gaps": (["ORACAL_AREA_SOURCE_MISSING"] if area_missing else []) + (["ORACAL_TARIFF_MISSING"] if tariff_missing else []),
        "warnings": [],
        "runtime_source": "logical_oracal_fallback_from_finish_and_nesting",
        "preferences": {
            "oracal_preference_count": len(oracal_prefs),
            "selected_series": "multiple" if is_multi_series else primary_series,
            "series_count": len(series_totals),
        },
        "quantity": total_quantity,
        "unit": "m2" if total_quantity is not None else None,
        "subtotal": total_subtotal,
        "currency": "EUR" if total_subtotal is not None else None,
        "material_code": "ORACAL_MULTIPLE" if is_multi_series else (f"ORACAL_{primary_series}" if primary_series else None),
        "material_name": "Oracal mixed series" if is_multi_series else (primary_bucket.get("material_name") if primary_bucket else None),
        "series": "multiple" if is_multi_series else primary_series,
        "selected_series": "multiple" if is_multi_series else primary_series,
        "usage_kind": "face_vinyl",
        "compatible_surface": "plexiglas_face",
        "material_tariff_source": "multiple_owner_series_rates" if is_multi_series else (primary_bucket.get("tariff_source") if primary_bucket else None),
        "tariff_source": "multiple_owner_series_rates" if is_multi_series else (primary_bucket.get("tariff_source") if primary_bucket else None),
        "material_tariff_eur_per_m2": None if is_multi_series else (primary_bucket.get("tariff_eur_per_m2") if primary_bucket else None),
        "tariff_eur_per_m2": None if is_multi_series else (primary_bucket.get("tariff_eur_per_m2") if primary_bucket else None),
        "tariff_status": "MIXED_OWNER_CONFIRMED_INTERIM" if is_multi_series and not tariff_missing else (
            "MISSING" if tariff_missing else "OWNER_CONFIRMED_INTERIM"
        ),
        "width_mm": (
            sorted(primary_bucket["roll_widths_mm"])[0]
            if primary_bucket and len(primary_bucket["roll_widths_mm"]) == 1
            else None
        ),
        "nesting_group": (
            "ORACAL_MULTIPLE_FACE_VINYL_BATCH"
            if is_multi_series
            else (f"ORACAL_{primary_series}_FACE_VINYL_BATCH" if primary_series else "ORACAL_FACE_VINYL_BATCH")
        ),
        "inventory_consumption_mode": "split_by_series_color" if is_multi_series else "single_series",
        "inventory_consumption_key": "ORACAL_MULTIPLE" if is_multi_series else (f"ORACAL_{primary_series}" if primary_series else None),
        "inventory_series_keys": [f"ORACAL_{series}" for series in series_codes],
        "source_roles": sorted(source_roles),
        "affected_group_keys": affected_group_keys,
        "source_groups": source_groups,
        "series_breakdown": [
            {
                "series": bucket["series"],
                "material_code": bucket["material_code"],
                "material_name": bucket["material_name"],
                "quantity": round(bucket["quantity"], 4) if bucket["has_quantity"] else None,
                "unit": "m2" if bucket["has_quantity"] else None,
                "subtotal": round(bucket["subtotal"], 4) if bucket["has_subtotal"] else None,
                "currency": "EUR" if bucket["has_subtotal"] else None,
                "tariff_source": bucket["tariff_source"],
                "tariff_status": bucket["tariff_status"],
                "tariff_eur_per_m2": bucket["tariff_eur_per_m2"],
                "roll_widths_mm": sorted(bucket["roll_widths_mm"]),
                "group_keys": bucket["group_keys"],
                "inventory_consumption_key": f"ORACAL_{bucket['series']}",
                "inventory_color_keys": sorted(bucket["color_codes"]),
                "color_breakdown": [
                    {
                        "color_code": color_bucket["color_code"],
                        "color_name": color_bucket["color_name"],
                        "quantity": round(color_bucket["quantity"], 4) if color_bucket["has_quantity"] else None,
                        "unit": "m2" if color_bucket["has_quantity"] else None,
                        "subtotal": round(color_bucket["subtotal"], 4) if color_bucket["has_subtotal"] else None,
                        "currency": "EUR" if color_bucket["has_subtotal"] else None,
                        "group_keys": list(color_bucket["group_keys"]),
                        "inventory_consumption_key": color_bucket["inventory_consumption_key"],
                    }
                    for color_bucket in bucket["color_breakdown"].values()
                ],
            }
            for bucket in (series_totals[series] for series in sorted(series_totals))
        ],
    }
    return synthetic_rows, metadata


def build_gradi_logical_list_read_model_from_runtime(
    *,
    workspace_payload: dict[str, Any],
    material_breakdown: Any,
    priced_dry_run: dict[str, Any],
) -> dict[str, Any]:
    finish = _finish(workspace_payload)
    composition_recommendation = (
        workspace_payload.get("product_composition_recommendation")
        if isinstance(workspace_payload.get("product_composition_recommendation"), dict)
        else None
    )
    composition_confirmation = (
        workspace_payload.get("product_composition_confirmed")
        if isinstance(workspace_payload.get("product_composition_confirmed"), dict)
        else None
    )
    geometry = _quote_geometry(workspace_payload)
    material_rows = _rows(material_breakdown, "material_rows")
    consumable_rows = _rows(material_breakdown, "consumable_rows")
    operation_rows = _rows(material_breakdown, "operation_rows")
    edge_rows = _rows(material_breakdown, "edge_cant_operation_rows")
    commercial_lines = [row for row in (priced_dry_run.get("commercial_line_items") or []) if isinstance(row, dict)]
    totals = _as_dict(getattr(material_breakdown, "totals", {}))
    all_rows = material_rows + consumable_rows + operation_rows + edge_rows
    warnings = [str(_as_dict(warning).get("code") or warning) for warning in _as_list(getattr(material_breakdown, "warnings", []))]
    response_warnings: list[str] = []
    response_blockers: list[str] = []

    def mat(key: str) -> list[dict[str, Any]]:
        return [row for row in material_rows if _row_key(row) == key]

    def con(key: str) -> list[dict[str, Any]]:
        return [row for row in consumable_rows if _row_key(row) == key]

    def op(key: str) -> list[dict[str, Any]]:
        return [row for row in operation_rows if _row_key(row) == key]

    oracal_rows = _find(all_rows, "oracal") or [
        row for row in material_rows if _row_key(row).startswith("face_vinyl_")
    ]
    oracal_prefs = _oracal_preferences(finish)
    fallback_oracal_rows: list[dict[str, Any]] = []
    fallback_oracal_meta: dict[str, Any] = {}
    if oracal_prefs and not oracal_rows:
        fallback_oracal_rows, fallback_oracal_meta = _build_oracal_fallback_rows(
            workspace_payload=workspace_payload,
            oracal_prefs=oracal_prefs,
        )
    effective_oracal_rows = oracal_rows or fallback_oracal_rows
    if oracal_prefs and not effective_oracal_rows:
        response_warnings.append("ORACAL_MATERIAL_RUNTIME_ROW_MISSING")

    artwork_prefs = _artwork_preferences(finish)
    artwork_area = geometry.get("artwork_area_m2")

    required_psu = finish.get("required_psu_watts")
    selected_psu = finish.get("selected_psu_watts")
    if isinstance(required_psu, (int, float)) and isinstance(selected_psu, (int, float)) and selected_psu < required_psu:
        response_warnings.append("PSU_UNDERSIZED")
        response_blockers.append("PSU_UNDERSIZED")

    if "roll_nesting_color_split_missing" in warnings:
        response_warnings.append("ORACAL_ROLL_COLOR_SPLIT_MISSING")
    if "backing_area_fallback_used" in warnings:
        response_warnings.append("BACKING_AREA_FALLBACK_USED")

    print_material_rows = _find(material_rows, "print_vinyl")
    lamination_material_rows = _find(material_rows, "laminated_vinyl")
    print_service_rows = _find(operation_rows, "print_service")
    lamination_service_rows = _find(operation_rows, "lamination_service")
    application_service_rows = _find(operation_rows, "application_service")
    has_confirmed_letter_face_content = _has_confirmed_letter_face_content(workspace_payload)

    logo_runtime_plexi_rows = _runtime_material_rows_with_prefix(material_rows, "artwork_plexiglas_")
    if not logo_runtime_plexi_rows and not has_confirmed_letter_face_content:
        logo_runtime_plexi_rows = mat("plexiglas_face")
    logo_runtime_plexi_quantity = _runtime_material_total_quantity(logo_runtime_plexi_rows)
    logo_runtime_plexi_subtotal = _runtime_material_subtotal(logo_runtime_plexi_rows)
    logo_runtime_plexi_source_part_ids = _runtime_material_source_part_ids(logo_runtime_plexi_rows)
    linked_logo_backing_rows = _runtime_material_rows_with_prefix(material_rows, "artwork_forex_backing_")
    forex_rows = mat("forex_backing") + linked_logo_backing_rows

    rows: list[dict[str, Any]] = [
        *([_line(line_id="material.plexiglas_face", display_label="Plexiglas 3 mm / fata litere", category=CORE_CATEGORY_MATERIALS, component_code="comp_face_litere", module_code="debitare_fata", formula_code="MATERIAL_PLEXI_FACE_BY_AREA_V1", rows=mat("plexiglas_face"))] if has_confirmed_letter_face_content else []),
        _line(line_id="material.logo_plexiglas_face", display_label="Plexiglas 3 mm / embleme/logo", category=CORE_CATEGORY_MATERIALS, component_code="comp_logo_face", module_code="finisaje", formula_code="MATERIAL_PLEXI_LOGO_FACE_BY_AREA_V1", rows=logo_runtime_plexi_rows or None, status=("PARTIAL" if logo_runtime_plexi_quantity is None else None), quantity=(logo_runtime_plexi_quantity if logo_runtime_plexi_quantity is not None else artwork_area if isinstance(artwork_area, (int, float)) else None), unit="m2", subtotal=logo_runtime_plexi_subtotal, gaps=(["LOGO_PLEXI_STRUCTURAL_RUNTIME_ROW_MISSING"] if logo_runtime_plexi_quantity is None else []), warnings=(["Structural logo/emblem plexiglas row is logical only until runtime material row exists."] if logo_runtime_plexi_quantity is None else []), preferences={"artwork_layer_count": len(artwork_prefs)}),
        *([_line(line_id="material.forex_backing", display_label="Forex 10 mm / spate litere", category=CORE_CATEGORY_MATERIALS, component_code="comp_spate_litere", module_code="debitare_spate", formula_code="MATERIAL_FOREX_BACK_BY_AREA_V1", rows=forex_rows, status="PARTIAL" if "backing_area_fallback_used" in warnings else None, gaps=["BACKING_AREA_FALLBACK_USED"] if "backing_area_fallback_used" in warnings else [], warnings=(["LINKED_LOGO_BACKING_FALLBACK_USED"] if linked_logo_backing_rows else []))] if has_confirmed_letter_face_content or forex_rows else []),
        *([
        _line(
            line_id="material.face_oracal",
            display_label=fallback_oracal_meta.get("display_label") or "Vinil fata Oracal 651",
            category=CORE_CATEGORY_MATERIALS,
            component_code="comp_face_litere",
            module_code="finisaje",
            formula_code="MATERIAL_ORACAL_FACE_BY_NESTED_AREA_V1",
            rows=effective_oracal_rows,
            status=fallback_oracal_meta.get("status") if fallback_oracal_meta else ("PARTIAL" if oracal_prefs and not oracal_rows else None),
            gaps=fallback_oracal_meta.get("gaps") if fallback_oracal_meta else (["ORACAL_MATERIAL_RUNTIME_ROW_MISSING"] if oracal_prefs and not oracal_rows else []),
            warnings=fallback_oracal_meta.get("warnings") if fallback_oracal_meta else (["Oracal preferences exist but runtime material row is missing."] if oracal_prefs and not oracal_rows else []),
            preferences=fallback_oracal_meta.get("preferences") if fallback_oracal_meta else {"oracal_preference_count": len(oracal_prefs)},
            quantity=fallback_oracal_meta.get("quantity") if fallback_oracal_meta else None,
            unit=fallback_oracal_meta.get("unit") if fallback_oracal_meta else None,
            subtotal=fallback_oracal_meta.get("subtotal") if fallback_oracal_meta else None,
            currency=fallback_oracal_meta.get("currency") if fallback_oracal_meta else None,
            runtime_source=fallback_oracal_meta.get("runtime_source") if fallback_oracal_meta else None,
        )
        ] if effective_oracal_rows or fallback_oracal_meta or oracal_prefs else []),
        *([
        _line(line_id="material.print", display_label="Material print Orafol", category=CORE_CATEGORY_MATERIALS, component_code="comp_finisaj_litere", module_code="finisaje", formula_code="MATERIAL_PRINT_BY_NESTED_AREA_V1", rows=print_material_rows, status="SPLIT_IN_RUNTIME", gaps=["PRINT_ROWS_AGGREGATED_FOR_LOGICAL_LIST"])
        ] if print_material_rows else []),
        *([
        _line(line_id="material.lamination", display_label="Material laminare Orafol", category=CORE_CATEGORY_MATERIALS, component_code="comp_finisaj_litere", module_code="finisaje", formula_code="MATERIAL_LAMINATION_BY_NESTED_AREA_V1", rows=lamination_material_rows, status="SPLIT_IN_RUNTIME", gaps=["LAMINATION_ROWS_AGGREGATED_FOR_LOGICAL_LIST"])
        ] if lamination_material_rows else []),
        _line(line_id="material.return_profile", display_label="Cant / volum litere + interioare + artwork", category=CORE_CATEGORY_MATERIALS, component_code="comp_lateral_litere", module_code="modelare_cant", formula_code="MATERIAL_CANT_BY_PERIMETER_DEPTH_V1", rows=mat("return_material"), warnings=["Cant labor is intentionally separate and depth-independent in current runtime trace."]),
        _line(line_id="material.led_modules", display_label="Module LED", category=CORE_CATEGORY_MATERIALS, component_code="comp_led_litere", module_code="sistem_led", formula_code="MATERIAL_LED_MODULES_BY_AREA_DENSITY_V1", rows=con("led_modules"), formula_status="legacy_unversioned", gaps=["FORMULA_TRACE_MISSING"]),
        _line(line_id="material.led_psu", display_label="Sursa LED 12V", category=CORE_CATEGORY_MATERIALS, component_code="comp_led_litere", module_code="sistem_led", formula_code="MATERIAL_PSU_BY_POWER_SAFETY_FACTOR_V1", rows=con("led_psu"), formula_status="legacy_unversioned", preferences={"required_psu_watts": required_psu, "selected_psu_watts": selected_psu, "psu_configuration": finish.get("psu_configuration")}, warnings=["PSU_UNDERSIZED"] if "PSU_UNDERSIZED" in response_warnings else [], blockers=["PSU_UNDERSIZED"] if "PSU_UNDERSIZED" in response_blockers else []),
        _line(line_id="material.adhesive_cant", display_label="Adeziv lipire cant pe fete litere", category=CORE_CATEGORY_MATERIALS, component_code="comp_lateral_litere", module_code="modelare_cant", formula_code="MATERIAL_ADHESIVE_CANT_BY_PERIMETER_V1", rows=con("adhesive_return_to_face")),
        _line(line_id="material.adhesive_led", display_label="Adeziv suplimentar module LED", category=CORE_CATEGORY_MATERIALS, component_code="comp_led_litere", module_code="sistem_led", formula_code="MATERIAL_ADHESIVE_LED_BY_MODULE_COUNT_V1", rows=con("adhesive_led_modules")),
        _line(line_id="material.wire_letters", display_label="Cablu electric MYYUP 2 x 0.75", category=CORE_CATEGORY_MATERIALS, component_code="comp_led_litere", module_code="sistem_led", formula_code="MATERIAL_CABLE_LOW_VOLTAGE_BY_RULE_V1", rows=con("wire_letters_myyup_2x075")),
        _line(line_id="material.wire_supply", display_label="Cablu electric MYYUP 2 x 1.5 alimentare 220V", category=CORE_CATEGORY_MATERIALS, component_code="comp_led_litere", module_code="sistem_led", formula_code="MATERIAL_CABLE_SUPPLY_BY_RULE_V1", rows=con("wire_supply_myyup_2x15")),
        _line(line_id="material.mounting_accessories", display_label="Accesorii montaj / conectori", category=CORE_CATEGORY_MATERIALS, component_code="comp_finisaj_litere", module_code="finisaje", formula_code="MATERIAL_MOUNTING_ACCESSORIES_BY_COST_PERCENT_V1", rows=con("mounting_accessories_percent"), formula_status="legacy_unversioned", gaps=["COMMERCIAL_FORMULA_UNVERSIONED"]),
        _line(line_id="service.cnc_face", display_label="Debitare CNC fata Plexiglas", category=CORE_CATEGORY_SERVICES, component_code="comp_face_litere", module_code="debitare_fata", formula_code="SERVICE_CNC_FACE_CUT_BY_CONTOUR_LENGTH_V1", rows=op("cnc_face_cutting_plexiglas_3mm")),
        _line(line_id="service.cnc_face_bevel", display_label="Canal plat ghidaj fata Plexiglas", category=CORE_CATEGORY_SERVICES, component_code="comp_face_litere", module_code="debitare_fata", formula_code="SERVICE_CNC_FACE_BEVEL_BY_CONTOUR_LENGTH_V1", rows=op("cnc_face_bevel_plexiglas_3mm")),
        _line(line_id="service.cnc_back", display_label="Debitare CNC spate Forex", category=CORE_CATEGORY_SERVICES, component_code="comp_spate_litere", module_code="debitare_spate", formula_code="SERVICE_CNC_BACK_CUT_BY_CONTOUR_LENGTH_V1", rows=op("cnc_backing_cutting_forex_10mm"), status="PARTIAL", gaps=["DRY_RUN_BACK_CNC_M2_DEV_BRIDGE"], warnings=["Material is m2; CNC service is contour ml; dry-run commercial bridge remains m2."]),
        *([
        _line(line_id="service.print", display_label="Serviciu print", category=CORE_CATEGORY_SERVICES, component_code="comp_finisaj_litere", module_code="finisaje", formula_code="SERVICE_PRINT_BY_AREA_V1", rows=print_service_rows, status="SPLIT_IN_RUNTIME", gaps=["PRINT_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST"])
        ] if print_service_rows else []),
        *([
        _line(line_id="service.lamination", display_label="Serviciu laminare X-PRO", category=CORE_CATEGORY_SERVICES, component_code="comp_finisaj_litere", module_code="finisaje", formula_code="SERVICE_LAMINATION_BY_AREA_V1", rows=lamination_service_rows, status="SPLIT_IN_RUNTIME", formula_status="legacy_unversioned", gaps=["LAMINATION_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST"])
        ] if lamination_service_rows else []),
        *([
        _line(line_id="service.application", display_label="Serviciu aplicare", category=CORE_CATEGORY_SERVICES, component_code="comp_finisaj_litere", module_code="finisaje", formula_code="SERVICE_APPLICATION_BY_AREA_V1", rows=application_service_rows, status="SPLIT_IN_RUNTIME", formula_status="legacy_unversioned", gaps=["APPLICATION_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST"])
        ] if application_service_rows else []),
        _line(line_id="labor.cant_glue", display_label="Lipire cant / volum pe fata litere", category=CORE_CATEGORY_LABOR, component_code="comp_lateral_litere", module_code="modelare_cant", formula_code="LABOR_CANT_GLUE_BY_PERIMETER_V1", rows=edge_rows, warnings=["Current runtime keeps cant labor constant across 60/80/100 depth variants."]),
    ]

    plexiglas_overrides = build_shared_plexiglas_face_batch_overrides(
        letter_face_row=(
            {
                **(_first(logo_runtime_plexi_rows) if logo_runtime_plexi_rows else _first(mat("plexiglas_face")) or {}),
                "quantity": logo_runtime_plexi_quantity if not has_confirmed_letter_face_content else (_first(mat("plexiglas_face")) or {}).get("quantity"),
                "estimated_cost": logo_runtime_plexi_subtotal if not has_confirmed_letter_face_content else (_first(mat("plexiglas_face")) or {}).get("estimated_cost"),
                "source_part_ids": logo_runtime_plexi_source_part_ids if not has_confirmed_letter_face_content else (_first(mat("plexiglas_face")) or {}).get("source_part_ids"),
            }
            if (logo_runtime_plexi_rows or mat("plexiglas_face"))
            else None
        ),
        logo_face_area_m2=(logo_runtime_plexi_quantity if logo_runtime_plexi_quantity is not None else artwork_area if isinstance(artwork_area, (int, float)) else None),
        has_letter_face_content=has_confirmed_letter_face_content,
    )
    cnc_perimeter_ml = resolve_cnc_perimeter_ml(geometry)
    cnc_overrides = build_cnc_operation_pricing_overrides(
        face_cut_row=_first(op("cnc_face_cutting_plexiglas_3mm")),
        face_flat_recess_row=_first(op("cnc_face_bevel_plexiglas_3mm")),
        back_cut_row=_first(op("cnc_backing_cutting_forex_10mm")),
        back_flat_recess_row=_first(op("cnc_backing_bevel_forex_10mm")),
        face_cut_quantity_fallback_ml=cnc_perimeter_ml,
        face_flat_recess_quantity_fallback_ml=cnc_perimeter_ml,
        back_cut_quantity_fallback_ml=cnc_perimeter_ml,
    )
    line_overrides = {**plexiglas_overrides, **cnc_overrides}
    for row in rows:
        override = line_overrides.get(str(row.get("line_id")))
        if override:
            row.update(override)

    _enrich_logical_list_material_metadata(rows, finish)

    composition_items = (
        composition_recommendation.get("composition_items")
        if isinstance(composition_recommendation, dict)
        else []
    )
    if not isinstance(composition_items, list):
        composition_items = []
    item_by_role = {
        str(item.get("component_role")): item
        for item in composition_items
        if isinstance(item, dict) and item.get("component_role")
    }
    for row in rows:
        if not isinstance(row, dict):
            continue
        line_id = str(row.get("line_id") or "")
        component_code = str(row.get("component_code") or "")
        role = "volumetric_logo" if "logo" in line_id or "logo" in component_code else "volumetric_letters"
        item = item_by_role.get(role)
        if isinstance(item, dict):
            row["source_composition_item_id"] = item.get("composition_item_id")
            row["source_template_code"] = item.get("template_code")
            row["source_component_role"] = item.get("component_role")

    if fallback_oracal_meta:
        oracal_row = next((row for row in rows if row.get("line_id") == "material.face_oracal"), None)
        if isinstance(oracal_row, dict):
            oracal_row.update(
                {
                    key: value
                    for key, value in fallback_oracal_meta.items()
                    if key
                    not in {
                        "display_label",
                        "status",
                        "gaps",
                        "warnings",
                        "preferences",
                        "quantity",
                        "unit",
                        "subtotal",
                        "currency",
                        "runtime_source",
                    }
                }
            )
            if "ORACAL_ROLL_COLOR_SPLIT_MISSING" in response_warnings:
                oracal_row["warnings"] = sorted(set(list(oracal_row.get("warnings") or []) + ["ORACAL_ROLL_COLOR_SPLIT_MISSING"]))

    logo_plexi_row = next((row for row in rows if row.get("line_id") == "material.logo_plexiglas_face"), None)
    if isinstance(logo_plexi_row, dict) and logo_runtime_plexi_source_part_ids:
        logo_plexi_row["source_part_ids"] = logo_runtime_plexi_source_part_ids

    if artwork_prefs and not (isinstance(logo_plexi_row, dict) and logo_plexi_row.get("status") == "MATCHED"):
        response_warnings.append("LOGO_PLEXI_STRUCTURAL_RUNTIME_ROW_MISSING")

    core_codes = {CORE_CATEGORY_MATERIALS, CORE_CATEGORY_SERVICES, CORE_CATEGORY_LABOR}
    return {
        "read_only": True,
        "source": "gradi_logical_list_read_model_v1",
        "workspace_id": priced_dry_run.get("workspace_id") or getattr(material_breakdown, "workspace_id", None),
        "workspace_code": priced_dry_run.get("workspace_code"),
        "template_code": priced_dry_run.get("template_code") or getattr(material_breakdown, "template_code", None),
        "product_composition_recommendation": composition_recommendation,
        "product_composition_confirmed": composition_confirmation,
        "composition_items": composition_items,
        "fixture_hint": "gradi-curat.svg",
        "categories": ["TOATE", CORE_CATEGORY_MATERIALS, "SERVICII / OPERATII", CORE_CATEGORY_LABOR],
        "core_row_count": len(rows),
        "target_core_row_count": 21,
        "core_rows_complete": len(rows) == 21,
        "rows": rows,
        "excluded_extra_commercial_lines": [
            line
            for line in commercial_lines
            if line.get("code") in {"ambalare", "montaj"}
        ],
        "warnings": sorted(set(response_warnings)),
        "blockers": sorted(set(response_blockers)),
        "runtime_totals": {
            "material_breakdown": totals,
            "priced_quote_dry_run": priced_dry_run.get("commercial_totals"),
        },
        "validation": {
            "no_duplicate_primary_tabs": True,
            "ambalare_montaj_excluded_from_core_rows": True,
            "categories_valid": all(row["category"] in core_codes for row in rows),
            "formula_trace_metadata_present": all(row.get("formula_code_proposed") and row.get("formula_version_proposed") for row in rows),
        },
    }


async def get_gradi_logical_list_read_model(
    db: AsyncSession,
    workspace_id: str,
) -> dict[str, Any]:
    record = await _get_record_or_404(db, str(workspace_id))
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    material_breakdown = await get_material_breakdown_for_workspace(db, str(workspace_id))
    priced_dry_run = await build_intake_v6_priced_quote_dry_run(db, str(workspace_id))
    return build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=payload_raw,
        material_breakdown=material_breakdown,
        priced_dry_run=priced_dry_run,
    )