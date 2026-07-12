"""Persist canonical logo layer_bindings on explicit composition confirmation."""

from __future__ import annotations

from typing import Any

from services.intake_v6_layer_identity import canonical_segment_key, index_layers_by_identity
from services.intake_v6_product_composition_recommendation_service import (
    LOGO_ROLES,
    LOGO_TEMPLATE_CODE,
)

BINDING_SOURCE = "operator_composition_confirmation_v1"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _role(layer: dict[str, Any]) -> str:
    return _text(layer.get("confirmed_role") or layer.get("auto_role")).lower()


def _is_logoish(value: Any) -> bool:
    text = str(value or "").lower()
    return "logo" in text or "sigla" in text or "siglă" in text or "emblem" in text


def _layers_by_key(layers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return index_layers_by_identity(layers)


def _is_logo_template_item(item: dict[str, Any]) -> bool:
    component_role = _text(item.get("component_role"))
    template_code = _text(item.get("template_code"))
    return component_role == "volumetric_logo" or template_code == LOGO_TEMPLATE_CODE


def _is_logo_binding_row(binding: dict[str, Any]) -> bool:
    target = _text(binding.get("target_template_code"))
    if target == LOGO_TEMPLATE_CODE:
        return True
    role = _text(binding.get("confirmed_semantic_role") or binding.get("suggested_semantic_role"))
    return role in LOGO_ROLES


def _logo_binding_row(
    *,
    layer_key: str,
    layer: dict[str, Any],
    target_template_code: str,
) -> dict[str, Any]:
    role = _role(layer) or "printed_artwork"
    return {
        "layer_key": layer_key,
        "source_layer_name": _text(layer.get("layer_name")) or None,
        "suggested_semantic_role": role,
        "confirmed_semantic_role": role,
        "target_template_code": target_template_code,
        "binding_status": "confirmed",
    }


def persist_logo_layer_bindings_from_composition_confirmation(
    payload_raw: dict[str, Any],
    *,
    confirmed: bool,
    confirmed_items: list[dict[str, Any]] | None,
) -> None:
    """Write layer_role_setup.layer_bindings[] for logo segments on explicit confirm only."""
    if not confirmed:
        return

    setup = _as_dict(payload_raw.get("layer_role_setup"))
    layers = [_as_dict(layer) for layer in _as_list(setup.get("layers")) if isinstance(layer, dict)]
    layers_by_key = _layers_by_key(layers)

    existing_bindings = [_as_dict(binding) for binding in _as_list(setup.get("layer_bindings")) if isinstance(binding, dict)]
    preserved_bindings = [binding for binding in existing_bindings if not _is_logo_binding_row(binding)]

    logo_bindings_by_key: dict[str, dict[str, Any]] = {}
    for binding in existing_bindings:
        if not _is_logo_binding_row(binding):
            continue
        key = _text(binding.get("layer_key"))
        if key:
            logo_bindings_by_key[key] = binding

    items = [_as_dict(item) for item in _as_list(confirmed_items) if isinstance(item, dict)]
    seen_in_confirmation: set[str] = set()
    for item in items:
        if not _is_logo_template_item(item):
            continue
        target_template_code = _text(item.get("template_code")) or LOGO_TEMPLATE_CODE
        for raw_layer_key in _as_list(item.get("source_layer_ids")):
            layer_key = _text(raw_layer_key)
            if not layer_key:
                continue
            layer = layers_by_key.get(layer_key)
            if not layer:
                continue
            canonical_key = canonical_segment_key(layer_key=layer_key, layer=layer)
            if canonical_key in seen_in_confirmation:
                continue
            role = _role(layer)
            if role not in LOGO_ROLES and not _is_logoish(layer_key) and not _is_logoish(layer.get("layer_name")):
                continue
            seen_in_confirmation.add(canonical_key)
            logo_bindings_by_key[canonical_key] = _logo_binding_row(
                layer_key=canonical_key,
                layer=layer,
                target_template_code=target_template_code,
            )

    merged_logo_bindings = [logo_bindings_by_key[key] for key in sorted(logo_bindings_by_key)]
    setup["layer_bindings"] = preserved_bindings + merged_logo_bindings
    payload_raw["layer_role_setup"] = setup
