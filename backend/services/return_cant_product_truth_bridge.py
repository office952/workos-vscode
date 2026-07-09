from __future__ import annotations

from typing import Any


DEPTH_TO_PROFILE_KEY: dict[int, str] = {
    30: "MAT-PROFIL-LATERAL-LITERE-30MM",
    60: "MAT-PROFIL-LATERAL-LITERE-60MM",
    80: "MAT-PROFIL-LATERAL-LITERE-80MM",
    100: "MAT-PROFIL-LATERAL-LITERE-100MM",
}

DEPTH_TO_RAL_PAINT_MATERIAL_KEY: dict[int, str] = {
    30: "MAT-VOPSEA-RAL-CANT-30MM",
    60: "MAT-VOPSEA-RAL-CANT-60MM",
    80: "MAT-VOPSEA-RAL-CANT-80MM",
    100: "MAT-VOPSEA-RAL-CANT-100MM",
}

VINYL_MATERIAL_KEYS: dict[str, str] = {
    "641": "MAT-ORACAL-641",
    "651": "MAT-ORACAL-651",
}

ARTWORK_ROLE_VALUES = {"printed_artwork", "logo", "policromie"}

STOCK_COLOR_LABELS: dict[str, str] = {
    "white_aluminum": "Alb",
    "black_aluminum": "Negru",
    "gold_aluminum": "Auriu",
    "mirror_silver": "Argintiu",
    "standard_aluminum": "Argintiu",
}

VINYL_FINISH_TO_SERIES: dict[str, str] = {
    "oracal_641": "641",
    "641": "641",
    "oracal_651": "651",
    "651": "651",
    "oracal_wrapped": "651",
    "oracal": "651",
    "vinyl": "651",
    "colantat": "651",
}

PAINT_FINISH_VALUES = {"ral_paint", "vopsit_ral", "ral", "painted", "paint"}


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed or None


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _positive_number(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def _supported_depth(value: Any) -> int | None:
    parsed = _positive_number(value)
    if parsed is None:
        return None
    if parsed.is_integer() and int(parsed) in DEPTH_TO_PROFILE_KEY:
        return int(parsed)
    return None


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _build_source_ref(source_kind: str, stable_key: str, row: dict[str, Any]) -> dict[str, Any]:
    source_ref: dict[str, Any] = {
        "source_label": _text(row.get("layer_name")) or stable_key,
        "source_role": "Vector Litere" if source_kind == "letter_group" else "Vector Logo",
    }
    if source_kind == "letter_group":
        source_ref["group_key"] = stable_key
    else:
        source_ref["layer_key"] = stable_key
    return source_ref


def _resolve_layer_group_ids(
    *,
    source_kind: str,
    stable_key: str,
    layer_role_setup: dict[str, Any] | None,
) -> list[str]:
    if not isinstance(layer_role_setup, dict):
        return []
    layers = layer_role_setup.get("layers")
    if not isinstance(layers, list):
        return []

    matched: list[str] = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_key = _text(layer.get("layer_key"))
        if layer_key != stable_key:
            continue
        if _lower(layer.get("confirmation_state")) != "confirmed":
            continue
        role = _lower(layer.get("confirmed_role") or layer.get("auto_role"))
        if source_kind == "letter_group" and role != "face":
            continue
        if source_kind == "artwork_layer" and role not in ARTWORK_ROLE_VALUES:
            continue
        matched.append(_text(layer.get("layer_id")) or layer_key)
    return _dedupe([value for value in matched if value])


def _resolve_finish_variant(
    *,
    finish_type: Any,
    color_code: Any,
    color_name: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any], list[str]]:
    token = _lower(finish_type)
    blockers: list[str] = []
    pricing_keys: dict[str, Any] = {}

    stock_label = STOCK_COLOR_LABELS.get(token)
    if stock_label is not None:
        return {
            "type": "stock_color",
            "stock_color_label": stock_label,
        }, pricing_keys, blockers

    if token in VINYL_FINISH_TO_SERIES:
        series = VINYL_FINISH_TO_SERIES[token]
        vinyl_key = VINYL_MATERIAL_KEYS.get(series)
        if vinyl_key is not None:
            pricing_keys["vinyl_material"] = vinyl_key
        pricing_keys["vinyl_application_labor"] = "RETURN_CANT_VINYL_APPLICATION_LABOR"
        if _text(color_code) is None:
            blockers.append("RETURN_CANT_PRICING_KEYS_MISSING")
        return {
            "type": "vinyl_application",
            "vinyl": {
                "material_family": "Folie autocolanta PVC",
                "series": f"Oracal {series}",
                "color_code": _text(color_code),
                "catalog_reference": f"vinyl_color_catalog:{series}:{_text(color_code)}" if _text(color_code) else None,
            },
        }, pricing_keys, blockers

    if token in PAINT_FINISH_VALUES:
        pricing_keys["ral_paint_labor"] = "RETURN_CANT_RAL_PAINT_LABOR"
        return {
            "type": "paint_application",
            "paint": {
                "system": "RAL",
                "ral_code": _text(color_code),
                "catalog_reference": f"paint_color_catalog:RAL:{_text(color_code)}" if _text(color_code) else None,
            },
        }, pricing_keys, blockers

    if token:
        blockers.append("RETURN_CANT_PRICING_KEYS_MISSING")
    return None, pricing_keys, blockers


def _build_geometry(quote_geometry: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = [
        "RETURN_CANT_CONFIRMED_PERIMETER_MISSING",
    ]
    evidence = None
    if isinstance(quote_geometry, dict):
        evidence = _positive_number(quote_geometry.get("letter_perimeter_m"))
    if evidence is not None:
        blockers.append("RETURN_CANT_PERIMETER_EVIDENCE_ONLY")
        return {
            "perimeter_source": "evidence_only",
            "evidence_perimeter_m": evidence,
        }, blockers
    return {
        "perimeter_source": "missing",
    }, blockers


def _build_instance(
    *,
    row: dict[str, Any],
    source_kind: str,
    stable_key: str,
    default_finish_type: Any,
    default_depth: Any,
    default_color_code: Any,
    default_color_name: Any,
    layer_role_setup: dict[str, Any] | None,
    quote_geometry: dict[str, Any] | None,
) -> dict[str, Any]:
    finish_type = row.get("return_finish_type") or default_finish_type
    depth_mm = _supported_depth(row.get("return_depth_mm") or default_depth)
    color_code = row.get("return_oracal_code") or default_color_code
    color_name = row.get("return_oracal_name") or default_color_name

    source_ref = _build_source_ref(source_kind, stable_key, row)
    layer_group_ids = _resolve_layer_group_ids(
        source_kind=source_kind,
        stable_key=stable_key,
        layer_role_setup=layer_role_setup,
    )
    finish_variant, pricing_keys, finish_blockers = _resolve_finish_variant(
        finish_type=finish_type,
        color_code=color_code,
        color_name=color_name,
    )
    geometry, geometry_blockers = _build_geometry(quote_geometry)

    blockers: list[str] = []
    if not source_ref:
        blockers.append("RETURN_CANT_SOURCE_REF_MISSING")
    if not layer_group_ids:
        blockers.append("RETURN_CANT_LAYER_GROUP_IDS_MISSING")
    if depth_mm is None:
        blockers.append("RETURN_CANT_PRICING_KEYS_MISSING")
    if finish_variant is None:
        blockers.append("RETURN_CANT_PRICING_KEYS_MISSING")
    blockers.extend(finish_blockers)
    blockers.extend(geometry_blockers)
    blockers.append("RETURN_CANT_COMPONENT_CONFIRMATION_MISSING")

    if depth_mm is not None:
        pricing_keys["material_profile_width"] = DEPTH_TO_PROFILE_KEY[depth_mm]
        if finish_variant is not None and finish_variant.get("type") == "paint_application":
            pricing_keys["ral_paint_material_by_width"] = DEPTH_TO_RAL_PAINT_MATERIAL_KEY[depth_mm]
    else:
        blockers.append("RETURN_CANT_PRICING_KEYS_MISSING")

    if finish_variant is not None and finish_variant.get("type") == "vinyl_application":
        if _text(color_code) is None:
            blockers.append("RETURN_CANT_PRICING_KEYS_MISSING")
    if finish_variant is not None and finish_variant.get("type") == "paint_application":
        if _text(color_code) is None:
            blockers.append("RETURN_CANT_PRICING_KEYS_MISSING")

    instance_key = f"letter_group:{stable_key}" if source_kind == "letter_group" else f"artwork_layer:{stable_key}"
    confirmation_state = "blocked"
    if finish_variant is None:
        confirmation_state = "missing"

    instance: dict[str, Any] = {
        "instance_key": instance_key,
        "source_kind": source_kind,
        "source_ref": source_ref,
        "geometry": geometry,
        "confirmation_state": confirmation_state,
        "blockers": _dedupe(blockers),
    }
    if layer_group_ids:
        instance["layer_group_ids"] = layer_group_ids
    if depth_mm is not None:
        instance["material_profile"] = {"width_mm": depth_mm}
    if finish_variant is not None:
        instance["finish_variant"] = finish_variant
    if pricing_keys:
        instance["pricing_keys"] = pricing_keys
    return instance


def build_return_cant_runtime_product_truth(payload_raw: dict[str, Any]) -> dict[str, Any]:
    finish_setup = payload_raw.get("finish_setup")
    layer_role_setup = payload_raw.get("layer_role_setup")
    quote_geometry = payload_raw.get("quote_geometry")

    if not isinstance(finish_setup, dict):
        return {
            "components": {
                "return_cant": {
                    "version": "v1",
                    "instances": {},
                }
            }
        }

    instances: dict[str, Any] = {}
    default_finish_type = finish_setup.get("return_finish_type")
    default_depth = finish_setup.get("return_depth_mm")
    default_color_code = finish_setup.get("return_oracal_code")
    default_color_name = finish_setup.get("return_oracal_name")

    for row in finish_setup.get("letter_group_finishes") or []:
        if not isinstance(row, dict):
            continue
        group_key = _text(row.get("group_key"))
        if group_key is None:
            continue
        instance = _build_instance(
            row=row,
            source_kind="letter_group",
            stable_key=group_key,
            default_finish_type=default_finish_type,
            default_depth=default_depth,
            default_color_code=default_color_code,
            default_color_name=default_color_name,
            layer_role_setup=layer_role_setup if isinstance(layer_role_setup, dict) else None,
            quote_geometry=quote_geometry if isinstance(quote_geometry, dict) else None,
        )
        instances[instance["instance_key"]] = instance

    for row in finish_setup.get("artwork_finishes") or []:
        if not isinstance(row, dict):
            continue
        layer_key = _text(row.get("layer_key"))
        if layer_key is None:
            continue
        instance = _build_instance(
            row=row,
            source_kind="artwork_layer",
            stable_key=layer_key,
            default_finish_type=default_finish_type,
            default_depth=default_depth,
            default_color_code=default_color_code,
            default_color_name=default_color_name,
            layer_role_setup=layer_role_setup if isinstance(layer_role_setup, dict) else None,
            quote_geometry=quote_geometry if isinstance(quote_geometry, dict) else None,
        )
        instances[instance["instance_key"]] = instance

    return {
        "components": {
            "return_cant": {
                "version": "v1",
                "instances": instances,
            }
        }
    }


def apply_return_cant_runtime_product_truth_bridge(payload_raw: dict[str, Any]) -> None:
    product_truth = payload_raw.setdefault("product_truth", {})
    if not isinstance(product_truth, dict):
        product_truth = {}
        payload_raw["product_truth"] = product_truth
    components = product_truth.setdefault("components", {})
    if not isinstance(components, dict):
        components = {}
        product_truth["components"] = components
    subtree = build_return_cant_runtime_product_truth(payload_raw)
    components["return_cant"] = subtree["components"]["return_cant"]


def clear_return_cant_runtime_product_truth(payload_raw: dict[str, Any]) -> None:
    product_truth = payload_raw.get("product_truth")
    if not isinstance(product_truth, dict):
        return
    components = product_truth.get("components")
    if not isinstance(components, dict):
        return
    components.pop("return_cant", None)
    if not components:
        product_truth.pop("components", None)
    if not product_truth:
        payload_raw.pop("product_truth", None)