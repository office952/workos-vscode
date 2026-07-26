"""Aggregate return/cant runtime state from persisted product_truth bridge."""

from __future__ import annotations

from typing import Any

DEPTH_TO_PROFILE_KEY: dict[int, str] = {
    30: "MAT-PROFIL-LATERAL-LITERE-30MM",
    60: "MAT-PROFIL-LATERAL-LITERE-60MM",
    80: "MAT-PROFIL-LATERAL-LITERE-80MM",
    100: "MAT-PROFIL-LATERAL-LITERE-100MM",
}


def _instances(payload_raw: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(payload_raw, dict):
        return []
    product_truth = payload_raw.get("product_truth")
    if not isinstance(product_truth, dict):
        return []
    components = product_truth.get("components")
    if not isinstance(components, dict):
        return []
    return_cant = components.get("return_cant")
    if not isinstance(return_cant, dict):
        return []
    instances = return_cant.get("instances")
    if not isinstance(instances, dict):
        return []
    return [row for row in instances.values() if isinstance(row, dict)]


def return_cant_runtime_state(payload_raw: dict[str, Any] | None) -> dict[str, Any]:
    rows = _instances(payload_raw)
    if not rows:
        return {
            "status": "missing",
            "blocker_code": "RETURN_CANT_MATERIAL_MISSING",
            "depth_mm": None,
            "material_profile": None,
            "finish_type": None,
            "layer_group_ids": [],
            "confirmation_state": None,
            "operator_blockers": ["RETURN_CANT_MATERIAL_MISSING"],
            "technical_blockers": [],
        }

    operator_blockers: list[str] = []
    technical_blockers: list[str] = []
    layer_group_ids: list[str] = []
    depths: list[int] = []
    finish_types: list[str] = []
    confirmation_states: list[str] = []
    material_profiles: list[str] = []

    for row in rows:
        for code in row.get("operator_blockers") or []:
            if isinstance(code, str) and code not in operator_blockers:
                operator_blockers.append(code)
        for code in row.get("technical_blockers") or []:
            if isinstance(code, str) and code not in technical_blockers:
                technical_blockers.append(code)
        for layer_id in row.get("layer_group_ids") or []:
            if isinstance(layer_id, str) and layer_id not in layer_group_ids:
                layer_group_ids.append(layer_id)
        profile = row.get("material_profile") if isinstance(row.get("material_profile"), dict) else {}
        depth = profile.get("width_mm")
        if isinstance(depth, (int, float)) and float(depth).is_integer():
            depths.append(int(depth))
        pricing_keys = row.get("pricing_keys") if isinstance(row.get("pricing_keys"), dict) else {}
        profile_key = pricing_keys.get("material_profile_width")
        if isinstance(profile_key, str):
            material_profiles.append(profile_key)
        finish_variant = row.get("finish_variant") if isinstance(row.get("finish_variant"), dict) else {}
        variant_type = finish_variant.get("type")
        if variant_type == "stock_color":
            stock = finish_variant.get("stock_color_label")
            finish_types.append(str(stock or "stock_color"))
        elif variant_type == "vinyl_application":
            finish_types.append("oracal_wrapped")
        elif variant_type == "paint_application":
            finish_types.append("ral_paint")
        state = row.get("confirmation_state")
        if isinstance(state, str):
            confirmation_states.append(state)

    depth_mm = depths[0] if depths and all(d == depths[0] for d in depths) else (max(depths) if depths else None)
    material_profile = material_profiles[0] if material_profiles else (
        DEPTH_TO_PROFILE_KEY.get(int(depth_mm)) if depth_mm in DEPTH_TO_PROFILE_KEY else None
    )
    all_confirmed = bool(confirmation_states) and all(state == "confirmed" for state in confirmation_states)
    values_present = depth_mm is not None and bool(material_profile) and bool(layer_group_ids)

    if not values_present:
        status = "missing"
        blocker_code = "RETURN_CANT_MATERIAL_MISSING"
    elif operator_blockers:
        status = "blocked"
        blocker_code = operator_blockers[0]
    elif all_confirmed:
        status = "confirmed"
        blocker_code = None
    else:
        status = "blocked"
        blocker_code = "RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED"

    return {
        "status": status,
        "blocker_code": blocker_code,
        "depth_mm": depth_mm,
        "material_profile": material_profile,
        "finish_type": finish_types[0] if finish_types else None,
        "layer_group_ids": layer_group_ids,
        "confirmation_state": "confirmed" if all_confirmed else "blocked",
        "operator_blockers": operator_blockers,
        "technical_blockers": technical_blockers,
    }
