"""Analyzer-first product composition recommendation for Intake V6.

Builds a read-model/payload fragment only. It does not create quotes, orders,
ProductAggregate, TaskGraph, ExecutionPlan, seeds, migrations, or DB writes by
itself.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from data.product_system.svg_component_binding_contract import (
    ACM_BOXED_SUPPORT,
    STALE_BOND_CASETAT,
)

LETTERS_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO_v1"
# Legacy string-only placeholder — never new-selection authority.
SUPPORT_TEMPLATE_LEGACY_CODE = STALE_BOND_CASETAT
SUPPORT_TEMPLATE_PENDING_CODE = STALE_BOND_CASETAT  # alias for older imports/tests
SUPPORT_TEMPLATE_LIVE_CODE = ACM_BOXED_SUPPORT

PRODUCT_COMPOSITION_SOURCE = "analyzer_rules_v1"
PRODUCT_COMPOSITION_NOT_CONFIRMED = "PRODUCT_COMPOSITION_NOT_CONFIRMED"
SUPPORT_TEMPLATE_PENDING = "SUPPORT_TEMPLATE_PENDING"
SUPPORT_TEMPLATE_LEGACY_REDIRECT = "SUPPORT_TEMPLATE_LEGACY_REDIRECTED_TO_ACM"

LETTER_ROLES = {"face", "letter_face", "vector_letters", "volumetric_letters"}
LOGO_ROLES = {"logo", "printed_artwork", "constructive_vector", "volumetric_logo", "logo_face"}
SUPPORT_ROLES = {"support_panel", "backing_panel", "acp_support", "box_background", "frame"}
IGNORE_ROLES = {"ignore", "ignored", "reference", "drill", "inner_hole"}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


def _role(layer: dict[str, Any]) -> str:
    return _lower(layer.get("confirmed_role") or layer.get("auto_role"))


def _layer_key(layer: dict[str, Any], index: int) -> str:
    return _text(layer.get("layer_key") or layer.get("layer_id") or layer.get("layer_name") or f"layer-{index + 1}")


def _source_label(layer: dict[str, Any], key: str) -> str:
    return _text(layer.get("layer_name") or layer.get("layer_id") or key)


def _is_generated_logo_side_label(label: str, key: str, file_name: str) -> bool:
    normalized = label.strip().lower().replace("-", " ")
    key_normalized = key.strip().lower().replace("-", " ")
    if normalized not in {"logo stanga", "logo dreapta"} and key_normalized not in {"logo stanga", "logo dreapta"}:
        return False
    return file_name.lower() in {"logo.svg", "logo"}


def _display_label_for_layer(layer: dict[str, Any], key: str, source_label: str, file_name: str, sequence: int) -> str:
    role = _role(layer)
    if role in LETTER_ROLES:
        return source_label if source_label and not source_label.startswith("pseudo:") else f"Litere volumetrice {sequence}"
    if role in LOGO_ROLES:
        if _is_generated_logo_side_label(source_label, key, file_name):
            return "Logo volumetric"
        if source_label and "logo" in source_label.lower() and file_name.lower() != "logo.svg":
            return source_label
        return "Logo volumetric" if sequence == 1 else f"Logo volumetric {sequence}"
    if role in SUPPORT_ROLES:
        return source_label if source_label else "Fundal / suport"
    if role in IGNORE_ROLES:
        return source_label if source_label else "Referinta / ignorat"
    return source_label or f"Strat {sequence}"


def _operator_role_for(layer: dict[str, Any]) -> str:
    role = _role(layer)
    if role in LETTER_ROLES:
        return "volumetric_letters"
    if role in LOGO_ROLES:
        return "volumetric_logo"
    if role in SUPPORT_ROLES:
        return "support_panel"
    if role in {"inner_hole"}:
        return "inner_cutout"
    if role == "drill":
        return "mounting_holes"
    if role == "ignore":
        return "ignore"
    if role == "reference":
        return "reference"
    return "reference" if role in IGNORE_ROLES else "volumetric_logo" if "logo" in _lower(layer.get("layer_name")) else "reference"


def _role_review(payload: dict[str, Any]) -> dict[str, Any]:
    setup = _as_dict(payload.get("layer_role_setup"))
    layers = [_as_dict(layer) for layer in _as_list(setup.get("layers")) if isinstance(layer, dict)]
    svg_source = _as_dict(payload.get("svg_source"))
    file_name = _text(svg_source.get("file_name"))
    reviewed: list[dict[str, Any]] = []
    logo_index = 0
    letter_index = 0
    support_index = 0
    for index, layer in enumerate(layers):
        key = _layer_key(layer, index)
        source_label = _source_label(layer, key)
        operator_role = _operator_role_for(layer)
        if operator_role == "volumetric_logo":
            logo_index += 1
            sequence = logo_index
        elif operator_role == "volumetric_letters":
            letter_index += 1
            sequence = letter_index
        elif operator_role == "support_panel":
            support_index += 1
            sequence = support_index
        else:
            sequence = index + 1
        reviewed.append(
            {
                "layer_id": key,
                "source_label": source_label,
                "display_label": _display_label_for_layer(layer, key, source_label, file_name, sequence),
                "original_label": source_label,
                "operator_role": operator_role,
                "technical_role": _role(layer) or "unknown",
                "role_source": "confirmed" if layer.get("confirmation_state") == "confirmed" else "suggested",
                "confidence": layer.get("auto_confidence") or "low",
                "geometry_ref": {"layer_key": key},
                "color_refs": [layer.get("dominant_fill")] if layer.get("dominant_fill") else [],
                "status": layer.get("confirmation_state") or "pending",
            }
        )
    return {"roles": reviewed}


def _template_item(*, template_code: str, role: str, reason: str, source_layer_ids: list[str], confidence: str = "high", status: str = "suggested") -> dict[str, Any]:
    return {
        "template_code": template_code,
        "role_in_composition": role,
        "reason": reason,
        "source_layer_ids": source_layer_ids,
        "confidence": confidence,
        "status": status,
    }


def _composition_item(*, item_id: str, template_code: str, component_role: str, source_layer_ids: list[str], status: str = "suggested") -> dict[str, Any]:
    return {
        "composition_item_id": item_id,
        "template_code": template_code,
        "component_role": component_role,
        "source_layer_ids": source_layer_ids,
        "source_group_ids": source_layer_ids,
        "shared_module_policy": "dedupe_common_operations",
        "status": status,
    }


def build_product_composition_recommendation(payload: dict[str, Any]) -> dict[str, Any]:
    review = _role_review(payload)
    roles = review["roles"]
    letter_layers = [role["layer_id"] for role in roles if role.get("operator_role") == "volumetric_letters" and role.get("status") != "ignored"]
    logo_layers = [role["layer_id"] for role in roles if role.get("operator_role") == "volumetric_logo" and role.get("status") != "ignored"]
    support_layers = [role["layer_id"] for role in roles if role.get("operator_role") == "support_panel" and role.get("status") != "ignored"]

    recommended_templates: list[dict[str, Any]] = []
    composition_items: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if letter_layers:
        recommended_templates.append(
            _template_item(
                template_code=LETTERS_TEMPLATE_CODE,
                role="letters",
                reason="Confirmed volumetric letter/vector roles exist in SVG analysis.",
                source_layer_ids=letter_layers,
            )
        )
        composition_items.append(
            _composition_item(
                item_id="letters",
                template_code=LETTERS_TEMPLATE_CODE,
                component_role="volumetric_letters",
                source_layer_ids=letter_layers,
            )
        )

    if logo_layers:
        recommended_templates.append(
            _template_item(
                template_code=LOGO_TEMPLATE_CODE,
                role="logo_vector_atipic",
                reason="Confirmed constructive logo/vector-atipic roles exist in SVG analysis.",
                source_layer_ids=logo_layers,
            )
        )
        composition_items.append(
            _composition_item(
                item_id="logo",
                template_code=LOGO_TEMPLATE_CODE,
                component_role="volumetric_logo",
                source_layer_ids=logo_layers,
            )
        )

    if support_layers:
        # Live authority is ACM boxed support. TPL-BOND-CASETAT remains a
        # legacy string-only alias (not seeded, not new-selection authority).
        recommended_templates.append(
            _template_item(
                template_code=SUPPORT_TEMPLATE_LIVE_CODE,
                role="support_panel",
                reason=(
                    "Support/background contour detected; maps to live optional component "
                    f"{SUPPORT_TEMPLATE_LIVE_CODE} (legacy alias {SUPPORT_TEMPLATE_LEGACY_CODE} is not authority)."
                ),
                source_layer_ids=support_layers,
                confidence="medium",
                status="available_optional",
            )
        )
        composition_items.append(
            _composition_item(
                item_id="support",
                template_code=SUPPORT_TEMPLATE_LIVE_CODE,
                component_role="support_panel",
                source_layer_ids=support_layers,
                status="available_optional",
            )
        )
        warnings.append(
            {
                "code": SUPPORT_TEMPLATE_LEGACY_REDIRECT,
                "message": (
                    "Suport/fundal detectat; authority live este Panou Alucobond casetat "
                    f"({SUPPORT_TEMPLATE_LIVE_CODE}). {SUPPORT_TEMPLATE_LEGACY_CODE} este legacy/deprecated."
                ),
            }
        )

    if not recommended_templates:
        blockers.append(
            {
                "code": "NO_PRODUCT_COMPONENT_DETECTED",
                "message": "Nu exista roluri constructive confirmate pentru recomandare de template.",
            }
        )

    if letter_layers and logo_layers and support_layers:
        composition_type = "letters_plus_logo_plus_support"
    elif letter_layers and logo_layers:
        composition_type = "letters_plus_logo"
    elif logo_layers:
        composition_type = "logo_only"
    elif letter_layers:
        composition_type = "letters_only"
    elif support_layers:
        composition_type = "support_only_pending"
    else:
        composition_type = "undetermined"

    return {
        "status": "needs_confirmation" if recommended_templates else "blocked",
        "composition_type": composition_type,
        "source": PRODUCT_COMPOSITION_SOURCE,
        "recommended_templates": recommended_templates,
        "composition_items": composition_items,
        "shared_modules_policy": {
            "dedupe_common_operations": True,
            "graphic_verification_scope": "assembly",
            "file_preparation_scope": "assembly",
            "light_test_scope": "assembly",
            "packaging_scope": "assembly",
        },
        "blockers": blockers,
        "warnings": warnings,
        "generated_at": _utcnow_iso(),
    }


def build_layer_role_review(payload: dict[str, Any]) -> dict[str, Any]:
    return _role_review(payload)


def apply_product_composition_recommendation(payload_raw: dict[str, Any]) -> None:
    payload_raw["terminology_mode"] = "constructive_vector"
    payload_raw["layer_role_review"] = build_layer_role_review(payload_raw)
    payload_raw["product_composition_recommendation"] = build_product_composition_recommendation(payload_raw)
    existing_confirmation = payload_raw.get("product_composition_confirmed")
    if not isinstance(existing_confirmation, dict):
        payload_raw["product_composition_confirmed"] = {
            "confirmed": False,
            "confirmed_at": None,
            "confirmed_by": None,
            "items": [],
        }
