"""Position-independent layer instance identity for Intake V6 linked logos."""

from __future__ import annotations

import re
from typing import Any

POSITIONAL_LOGO_ID_PATTERN = re.compile(
    r"^logo(?:[_-])?(?:stanga|dreapta|left|right|sus|jos|top|bottom)(?:[_-]|$)",
    re.IGNORECASE,
)
POSITIONAL_LOGO_NAME_PATTERN = re.compile(
    r"logo(?:\s|_|-)*(?:stanga|dreapta|centru|center|middle|left|right|sus|jos|top|bottom)",
    re.IGNORECASE,
)
NEUTRAL_LOGO_INSTANCE_PATTERN = re.compile(r"^logo_instance_\d{3}$")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def format_neutral_logo_instance_id(index: int) -> str:
    safe_index = max(1, int(index))
    return f"logo_instance_{safe_index:03d}"


def is_neutral_logo_instance_id(value: Any) -> bool:
    return bool(NEUTRAL_LOGO_INSTANCE_PATTERN.match(_text(value)))


def is_positional_logo_identity(layer_id: Any = None, layer_name: Any = None) -> bool:
    layer_id_text = _text(layer_id)
    layer_name_text = _text(layer_name)
    if layer_id_text and POSITIONAL_LOGO_ID_PATTERN.search(layer_id_text):
        return True
    if layer_name_text and POSITIONAL_LOGO_NAME_PATTERN.search(layer_name_text):
        return True
    return False


def canonical_segment_key(*, layer_key: str, layer: dict[str, Any] | None = None) -> str:
    """Resolve stable neutral segment key; never derive from geometry."""
    layer_data = _as_dict(layer)
    resolved_layer_key = _text(layer_key)
    layer_id = _text(layer_data.get("layer_id"))
    layer_name = _text(layer_data.get("layer_name"))

    if layer_id and not is_positional_logo_identity(layer_id, layer_name):
        if is_positional_logo_identity(resolved_layer_key, layer_name):
            return layer_id
        return layer_id

    if resolved_layer_key and not is_positional_logo_identity(resolved_layer_key, layer_name):
        return resolved_layer_key

    return resolved_layer_key or layer_id


def index_layers_by_identity(layers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for layer in layers:
        layer_key = _text(layer.get("layer_key") or layer.get("layer_id"))
        if not layer_key:
            continue
        canonical = canonical_segment_key(layer_key=layer_key, layer=layer)
        indexed[layer_key] = layer
        indexed[canonical] = layer
        layer_id = _text(layer.get("layer_id"))
        if layer_id:
            indexed[layer_id] = layer
    return indexed


def resolve_finish_row(
    *,
    key: str,
    finishes_by_key: dict[str, tuple[int, dict[str, Any]]],
    layers_by_identity: dict[str, dict[str, Any]],
) -> tuple[int | None, dict[str, Any]]:
    if key in finishes_by_key:
        return finishes_by_key[key]
    layer = layers_by_identity.get(key)
    if layer:
        canonical = canonical_segment_key(layer_key=key, layer=layer)
        if canonical in finishes_by_key:
            return finishes_by_key[canonical]
    return None, {}


def resolve_binding_row(
    *,
    key: str,
    bindings_by_key: dict[str, tuple[int, dict[str, Any]]],
    layers_by_identity: dict[str, dict[str, Any]],
) -> tuple[int | None, dict[str, Any]]:
    if key in bindings_by_key:
        return bindings_by_key[key]
    layer = layers_by_identity.get(key)
    if layer:
        canonical = canonical_segment_key(layer_key=key, layer=layer)
        if canonical in bindings_by_key:
            return bindings_by_key[canonical]
    return None, {}


def canonical_candidate_keys(
    *,
    layers: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    finishes: list[dict[str, Any]],
    linked_template_code: str,
    logo_layer_roles: set[str],
    is_logoish,
) -> list[str]:
    keys: set[str] = set()
    layers_by_identity = index_layers_by_identity(layers)

    for binding in bindings:
        if _text(binding.get("target_template_code")).upper() != _text(linked_template_code).upper():
            continue
        raw_key = _text(binding.get("layer_key"))
        if not raw_key:
            continue
        layer = layers_by_identity.get(raw_key)
        keys.add(canonical_segment_key(layer_key=raw_key, layer=layer))

    for layer in layers:
        layer_key = _text(layer.get("layer_key") or layer.get("layer_id"))
        if not layer_key:
            continue
        role = _text(layer.get("confirmed_role") or layer.get("auto_role")).lower()
        if role in logo_layer_roles and (is_logoish(layer_key) or is_logoish(layer.get("layer_name"))):
            keys.add(canonical_segment_key(layer_key=layer_key, layer=layer))

    for finish in finishes:
        finish_key = _text(finish.get("layer_key"))
        if not finish_key:
            continue
        if is_logoish(finish_key) or is_logoish(finish.get("layer_name")):
            layer = layers_by_identity.get(finish_key)
            keys.add(canonical_segment_key(layer_key=finish_key, layer=layer))

    return sorted(keys)


def artwork_finish_for_segment(payload: dict[str, Any], segment_key: str) -> dict[str, Any] | None:
    finish_setup = _as_dict(payload.get("finish_setup"))
    finishes = _as_list(finish_setup.get("artwork_finishes"))
    layers = _as_list(_as_dict(payload.get("layer_role_setup")).get("layers"))
    layers_by_identity = index_layers_by_identity(layers)
    canonical = canonical_segment_key(
        layer_key=segment_key,
        layer=layers_by_identity.get(segment_key),
    )
    aliases = {segment_key, canonical}
    layer = layers_by_identity.get(segment_key)
    if layer:
        layer_id = _text(layer.get("layer_id"))
        layer_key = _text(layer.get("layer_key"))
        aliases.update(value for value in (layer_id, layer_key) if value)

    for finish in finishes:
        finish_key = _text(_as_dict(finish).get("layer_key"))
        if finish_key in aliases:
            return _as_dict(finish)
    return None
