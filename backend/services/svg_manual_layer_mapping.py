"""Manual SVG layer → template / role mapping (operator-confirmed, no geometry invention)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

MANUAL_LAYER_MAPPING_TARGETS = frozenset({
    "TPL-VOLUMETRIC-LETTERS",
    "support_bars",
    "mounting_reference",
    "ignore",
})

LETTERS_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"
SUPPORT_MAPPING_TARGETS = frozenset({"support_bars", "mounting_reference"})


def normalize_svg_layer_mappings(raw: Any) -> dict[str, str]:
    """Validate and normalize svg_layer_mappings from intake product_spec_json."""
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("product_spec_json.svg_layer_mappings must be a JSON object")
    out: dict[str, str] = {}
    for layer_name, target in raw.items():
        layer = str(layer_name).strip()
        mapped = str(target).strip()
        if not layer:
            raise ValueError("product_spec_json.svg_layer_mappings keys must be non-empty strings")
        if mapped not in MANUAL_LAYER_MAPPING_TARGETS:
            raise ValueError(
                "product_spec_json.svg_layer_mappings values must be one of: "
                f"{sorted(MANUAL_LAYER_MAPPING_TARGETS)}"
            )
        out[layer] = mapped
    return out


def derive_vector_layer_mapping_status(mappings: dict[str, str]) -> str:
    """Derive intake vector_layer_mapping_status from manual mappings."""
    if not mappings:
        return "pending"
    if letters_template_manually_mapped(mappings):
        return "mapped"
    return "pending"


def letters_template_manually_mapped(mappings: dict[str, str]) -> bool:
    return LETTERS_TEMPLATE_CODE in mappings.values()


def apply_manual_layer_mapping_to_row(
    row: Any,
    *,
    target: str,
    volumetric_quote_suggestions_fn,
) -> Any:
    """Return a new row dict/dataclass-like with manual mapping applied."""
    data = deepcopy(row.__dict__) if hasattr(row, "__dict__") else dict(row)

    blockers = [b for b in list(data.get("blockers") or []) if b != "svg_layer_unmapped"]
    warnings = list(data.get("warnings") or [])
    quote_suggestions: dict[str, float | int | None] = {}
    metrics = data.get("metrics")
    metrics_confidence = getattr(metrics, "metrics_confidence", None) if metrics else None
    if metrics_confidence is None and isinstance(metrics, dict):
        metrics_confidence = metrics.get("metrics_confidence")

    if target == "ignore":
        data["mapping_status"] = "ignored"
        data["mapped_template_code"] = None
        data["mapped_by"] = "manual"
        data["detected_kind"] = "ignored"
        data["quote_input_suggestions"] = {}
        data["blockers"] = sorted(set(blockers))
        data["warnings"] = warnings
        return data

    if target in SUPPORT_MAPPING_TARGETS:
        data["mapping_status"] = "mapped_manual"
        data["mapped_template_code"] = None
        data["mapped_by"] = "manual"
        data["detected_kind"] = target
        data["quote_input_suggestions"] = {}
        data["blockers"] = sorted(set(blockers))
        data["warnings"] = warnings
        return data

    if target == LETTERS_TEMPLATE_CODE:
        data["mapping_status"] = "mapped_manual"
        data["mapped_template_code"] = LETTERS_TEMPLATE_CODE
        data["mapped_by"] = "manual"
        data["detected_kind"] = "volumetric_letters"
        data["human_description"] = "Litere volumetrice — mapare manuală operator"

        if metrics is not None and metrics_confidence != "unavailable":
            quote_suggestions = volumetric_quote_suggestions_fn(metrics, warnings)
            if quote_suggestions.get("letter_perimeter_m") is None:
                blockers.append("manual_geometry_required")
            if metrics_confidence == "unavailable":
                blockers.extend(["metrics_unavailable", "manual_geometry_required"])
        else:
            blockers.extend(["metrics_unavailable", "manual_geometry_required"])

        data["quote_input_suggestions"] = quote_suggestions
        data["blockers"] = sorted(set(blockers))
        data["warnings"] = warnings
        return data

    return data


def apply_manual_layer_mappings(
    layers: list[Any],
    mappings: dict[str, str] | None,
    *,
    volumetric_quote_suggestions_fn,
) -> list[dict[str, Any]]:
    """Overlay operator manual mappings onto analyzed layers by svg_layer_name."""
    if not mappings:
        return [
            deepcopy(layer.__dict__) if hasattr(layer, "__dict__") else dict(layer)
            for layer in layers
        ]

    normalized = normalize_svg_layer_mappings(mappings)
    out: list[dict[str, Any]] = []
    for layer in layers:
        layer_name = getattr(layer, "svg_layer_name", None) or (
            layer.get("svg_layer_name") if isinstance(layer, dict) else None
        )
        if layer_name and layer_name in normalized:
            patched = apply_manual_layer_mapping_to_row(
                layer,
                target=normalized[layer_name],
                volumetric_quote_suggestions_fn=volumetric_quote_suggestions_fn,
            )
            out.append(patched)
        else:
            out.append(
                deepcopy(layer.__dict__) if hasattr(layer, "__dict__") else dict(layer)
            )
    return out
