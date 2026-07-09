"""Layer role setup for Intake V4 — derived from SVG path geometry."""

from __future__ import annotations

from typing import Any

from schemas.intake_v4 import (
    IntakeV4LayerRoleLayer,
    IntakeV4LayerRoleSetup,
    IntakeV4SelectedLayerRef,
)
from services.intake_v3_geometry_path_perimeter_classification_service import (
    normalize_svg_layer_role,
)


_SELECTED_LAYER_ROLE_MAP = {
    "face": "vector_litere",
    "logo": "vector_logo",
}


def _layer_key(layer: dict[str, Any]) -> str:
    layer_id = layer.get("layer_id")
    if isinstance(layer_id, str) and layer_id.strip():
        return layer_id.strip()
    layer_name = layer.get("layer_name")
    if isinstance(layer_name, str) and layer_name.strip():
        return layer_name.strip()
    return "unknown"


def _auto_role(layer: dict[str, Any]) -> tuple[str, str]:
    layer_name = layer.get("layer_name")
    layer_id = layer.get("layer_id")
    name = layer_name if isinstance(layer_name, str) and layer_name.strip() else None
    if name is None and isinstance(layer_id, str) and layer_id.strip():
        name = layer_id.strip()
    role = normalize_svg_layer_role(name)
    confidence = "high" if role not in {"unknown", "reference"} else "low"
    return role, confidence


def build_layer_role_setup_from_path_summary(
    path_summary: dict[str, Any] | None,
) -> IntakeV4LayerRoleSetup:
    if not path_summary or path_summary.get("parse_status") != "parsed":
        return IntakeV4LayerRoleSetup(confirmation_status="missing", layers=[], warnings=[])

    layers_raw = path_summary.get("layers")
    if not isinstance(layers_raw, list):
        return IntakeV4LayerRoleSetup(confirmation_status="missing", layers=[], warnings=[])

    layers: list[IntakeV4LayerRoleLayer] = []
    for entry in layers_raw:
        if not isinstance(entry, dict):
            continue
        auto_role, auto_confidence = _auto_role(entry)
        color_evidence = entry.get("color_evidence")
        dominant_fill = None
        if isinstance(color_evidence, dict):
            dominant = color_evidence.get("dominant_fill")
            if isinstance(dominant, str):
                dominant_fill = dominant
        layers.append(
            IntakeV4LayerRoleLayer(
                layer_key=_layer_key(entry),
                layer_id=entry.get("layer_id") if isinstance(entry.get("layer_id"), str) else None,
                layer_name=entry.get("layer_name") if isinstance(entry.get("layer_name"), str) else None,
                auto_role=auto_role,
                auto_confidence=auto_confidence,
                path_count=entry.get("path_count") if isinstance(entry.get("path_count"), int) else None,
                dominant_fill=dominant_fill,
            )
        )

    if not layers:
        return IntakeV4LayerRoleSetup(confirmation_status="missing", layers=[], warnings=[])

    return IntakeV4LayerRoleSetup(
        confirmation_status="partial",
        layers=layers,
        warnings=[],
    )


def merge_layer_roles_after_reupload(
    draft: IntakeV4LayerRoleSetup,
    previous: IntakeV4LayerRoleSetup | None,
) -> IntakeV4LayerRoleSetup:
    if previous is None:
        return draft

    prev_by_key = {layer.layer_key: layer for layer in previous.layers}
    merged: list[IntakeV4LayerRoleLayer] = []
    for layer in draft.layers:
        prev = prev_by_key.get(layer.layer_key)
        if prev is None:
            merged.append(layer)
            continue
        if prev.confirmation_state in {"confirmed", "ignored"} and prev.confirmed_role:
            merged.append(
                layer.model_copy(
                    update={
                        "confirmed_role": prev.confirmed_role,
                        "confirmation_state": prev.confirmation_state,
                        "operator_note": prev.operator_note,
                    }
                )
            )
        else:
            merged.append(layer)

    confirmed = sum(1 for layer in merged if layer.confirmation_state in {"confirmed", "ignored"})
    status = "complete" if confirmed == len(merged) and merged else "partial" if confirmed else "missing"
    warnings = list(draft.warnings)
    if {layer.layer_key for layer in draft.layers} != {layer.layer_key for layer in previous.layers}:
        warnings.append("layer_set_changed_after_svg_reupload")

    return draft.model_copy(update={"layers": merged, "confirmation_status": status, "warnings": warnings})


def apply_layer_role_updates(
    setup: IntakeV4LayerRoleSetup,
    updates: list[dict[str, Any]],
) -> IntakeV4LayerRoleSetup:
    lookup = {item["layer_key"]: item for item in updates if item.get("layer_key")}
    merged_layers: list[IntakeV4LayerRoleLayer] = []
    for layer in setup.layers:
        patch = lookup.get(layer.layer_key)
        if patch is None:
            merged_layers.append(layer)
            continue
        merged_layers.append(
            layer.model_copy(
                update={
                    "confirmed_role": patch.get("confirmed_role"),
                    "confirmation_state": patch.get("confirmation_state", "confirmed"),
                    "operator_note": patch.get("operator_note"),
                }
            )
        )

    confirmed = sum(1 for layer in merged_layers if layer.confirmation_state in {"confirmed", "ignored"})
    total = len(merged_layers)
    if total == 0:
        status = "missing"
    elif confirmed == total:
        status = "complete"
    elif confirmed > 0:
        status = "partial"
    else:
        status = "missing"

    return setup.model_copy(update={"layers": merged_layers, "confirmation_status": status})


def selected_layer_refs_runtime_state(
    setup: IntakeV4LayerRoleSetup | None,
) -> dict[str, Any]:
    if setup is None or not setup.layers:
        return {"refs": [], "status": "missing", "blocker_code": "SELECTED_LAYER_REFS_MISSING"}

    candidate_layers = [
        layer
        for layer in setup.layers
        if _SELECTED_LAYER_ROLE_MAP.get(str(layer.confirmed_role or layer.auto_role or "").strip().lower())
    ]
    if setup.confirmation_status != "complete":
        return {
            "refs": [],
            "status": "unconfirmed",
            "blocker_code": "SELECTED_LAYER_REFS_UNCONFIRMED",
        }
    if not candidate_layers:
        return {"refs": [], "status": "missing", "blocker_code": "SELECTED_LAYER_REFS_MISSING"}

    refs: list[IntakeV4SelectedLayerRef] = []
    seen_layer_ids: set[str] = set()
    for layer in candidate_layers:
        if layer.confirmation_state != "confirmed":
            return {
                "refs": [],
                "status": "unconfirmed",
                "blocker_code": "SELECTED_LAYER_REFS_UNCONFIRMED",
            }
        layer_id = str(layer.layer_id or "").strip()
        role = _SELECTED_LAYER_ROLE_MAP.get(str(layer.confirmed_role or "").strip().lower())
        if not layer_id or not role or layer_id in seen_layer_ids:
            return {
                "refs": [],
                "status": "ambiguous",
                "blocker_code": "SELECTED_LAYER_REFS_AMBIGUOUS",
            }
        seen_layer_ids.add(layer_id)
        refs.append(
            IntakeV4SelectedLayerRef(
                layer_id=layer_id,
                role=role,
                source="operator_confirmed_layer_role",
                confirmed=True,
            )
        )

    return {"refs": refs, "status": "confirmed", "blocker_code": None}
