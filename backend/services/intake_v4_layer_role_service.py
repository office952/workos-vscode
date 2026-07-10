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


# Persisted operator/canonical layer roles → derived selected_layer_refs.role values.
# `logo` is a LEGACY_BRIDGE alias for older persisted payloads; UI uses `printed_artwork`.
_SELECTED_LAYER_ROLE_MAP = {
    "face": "vector_litere",
    "printed_artwork": "vector_logo",
    "logo": "vector_logo",
}


def _derived_role_for_persisted_layer_role(persisted_role: str | None) -> str | None:
    token = str(persisted_role or "").strip().lower()
    if not token:
        return None
    return _SELECTED_LAYER_ROLE_MAP.get(token)


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


def derive_selected_layer_refs_from_setup(
    setup: IntakeV4LayerRoleSetup | None,
) -> list[IntakeV4SelectedLayerRef]:
    """Pure projection from canonical layer_role_setup to selected_layer_refs."""
    if setup is None or not setup.layers:
        return []

    if setup.confirmation_status != "complete":
        return []

    refs: list[IntakeV4SelectedLayerRef] = []
    seen_layer_ids: set[str] = set()
    for layer in setup.layers:
        if layer.confirmation_state != "confirmed":
            continue
        derived_role = _derived_role_for_persisted_layer_role(layer.confirmed_role)
        if derived_role is None:
            continue
        layer_id = str(layer.layer_id or "").strip()
        if not layer_id:
            raise ValueError("SELECTED_LAYER_REFS_AMBIGUOUS")
        if layer_id in seen_layer_ids:
            raise ValueError("SELECTED_LAYER_REFS_AMBIGUOUS")
        seen_layer_ids.add(layer_id)
        refs.append(
            IntakeV4SelectedLayerRef(
                layer_id=layer_id,
                role=derived_role,
                source="operator_confirmed_layer_role",
                confirmed=True,
            )
        )
    return refs


def selected_layer_refs_runtime_state(
    setup: IntakeV4LayerRoleSetup | None,
) -> dict[str, Any]:
    if setup is None or not setup.layers:
        return {"refs": [], "status": "missing", "blocker_code": "SELECTED_LAYER_REFS_MISSING"}

    if setup.confirmation_status != "complete":
        return {
            "refs": [],
            "status": "unconfirmed",
            "blocker_code": "SELECTED_LAYER_REFS_UNCONFIRMED",
        }

    try:
        refs = derive_selected_layer_refs_from_setup(setup)
    except ValueError:
        return {
            "refs": [],
            "status": "ambiguous",
            "blocker_code": "SELECTED_LAYER_REFS_AMBIGUOUS",
        }

    if not refs:
        return {
            "refs": [],
            "status": "confirmed",
            "blocker_code": "SELECTED_LAYER_REFS_EMPTY",
        }

    return {"refs": refs, "status": "confirmed", "blocker_code": None}


def sync_selected_layer_refs_on_payload(payload_raw: dict[str, Any], setup: IntakeV4LayerRoleSetup | None) -> None:
    """Persist derived selected_layer_refs on the workspace payload dict (single write path)."""
    runtime = selected_layer_refs_runtime_state(setup)
    svg_runtime = payload_raw.get("svg") if isinstance(payload_raw.get("svg"), dict) else {}
    if runtime["status"] == "confirmed":
        svg_runtime["selected_layer_refs"] = [item.model_dump(mode="json") for item in runtime["refs"]]
        payload_raw["svg"] = svg_runtime
        return
    svg_runtime.pop("selected_layer_refs", None)
    if svg_runtime:
        payload_raw["svg"] = svg_runtime
    else:
        payload_raw.pop("svg", None)
