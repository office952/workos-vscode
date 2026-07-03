"""Invalidate workspace operator state when SVG source is replaced."""

from __future__ import annotations

from typing import Any

WARN_SVG_DEPENDENT_STATE_INVALIDATED = "svg_dependent_state_invalidated_after_svg_replace"


def _vector_file_hash(payload: dict[str, Any]) -> str | None:
    vector = payload.get("vector_asset")
    if not isinstance(vector, dict):
        return None
    file_hash = vector.get("file_hash")
    if file_hash is None:
        return None
    text = str(file_hash).strip()
    return text or None


def should_invalidate_svg_dependent_state(
    payload: dict[str, Any],
    *,
    new_file_hash: str,
) -> bool:
    """True when a previously saved SVG is replaced by a different file."""
    previous_hash = _vector_file_hash(payload)
    if previous_hash is None:
        return False
    return previous_hash != new_file_hash


def invalidate_svg_dependent_workspace_state(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Clear operator-confirmed state that depends on the previous SVG source."""
    warnings: list[str] = []
    updated = dict(payload)

    if updated.get("confirmed_production_model") is not None:
        updated.pop("confirmed_production_model", None)
        updated["production_model_status"] = "pending"
        updated["production_model_confirmed_at"] = None
        updated["production_model_confirmed_by_user_id"] = None
        warnings.append(WARN_SVG_DEPENDENT_STATE_INVALIDATED)

    finish = updated.get("finish_assignment")
    if isinstance(finish, dict) and finish.get("confirmed_by_operator") is True:
        finish = dict(finish)
        finish["confirmed_by_operator"] = False
        updated["finish_assignment"] = finish
        if WARN_SVG_DEPENDENT_STATE_INVALIDATED not in warnings:
            warnings.append(WARN_SVG_DEPENDENT_STATE_INVALIDATED)

    layer_finishes = updated.get("layer_finish_assignments")
    if isinstance(layer_finishes, list):
        normalized: list[Any] = []
        changed = False
        for entry in layer_finishes:
            if not isinstance(entry, dict):
                normalized.append(entry)
                continue
            item = dict(entry)
            if item.get("is_confirmed") is True:
                item["is_confirmed"] = False
                changed = True
            normalized.append(item)
        if changed:
            updated["layer_finish_assignments"] = normalized
            updated["layer_finish_assignment_status"] = "pending"
            if WARN_SVG_DEPENDENT_STATE_INVALIDATED not in warnings:
                warnings.append(WARN_SVG_DEPENDENT_STATE_INVALIDATED)

    lighting = updated.get("lighting_plan")
    if isinstance(lighting, dict) and lighting.get("is_confirmed") is True:
        lighting = dict(lighting)
        lighting["is_confirmed"] = False
        updated["lighting_plan"] = lighting
        updated["lighting_plan_status"] = "pending"
        if WARN_SVG_DEPENDENT_STATE_INVALIDATED not in warnings:
            warnings.append(WARN_SVG_DEPENDENT_STATE_INVALIDATED)

    vector = updated.get("vector_asset")
    if isinstance(vector, dict) and vector.get("file_hash"):
        updated["svg_source_fingerprint"] = vector.get("file_hash")

    existing = updated.get("svg_dependent_state_warnings")
    merged_warnings = list(existing) if isinstance(existing, list) else []
    for code in warnings:
        if code not in merged_warnings:
            merged_warnings.append(code)
    if merged_warnings:
        updated["svg_dependent_state_warnings"] = merged_warnings

    return updated, warnings
