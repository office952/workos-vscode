"""Linked-logo commercial line expansion for CommercialPriceProposal (letters root)."""

from __future__ import annotations

from typing import Any

from data.commercial_rules_volumetric_v2 import (
    LOGO_LINKED_CHILD_COMMERCIAL_RULE_TEMPLATES,
    CommercialRuleDefinition,
)
from schemas.commercial_price_proposal import CommercialOwnerDecision, CommercialPriceLine
from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE

SEGMENT_SEP = "::"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _positive(raw: Any) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def _linked_logo_segments(pd_linked: Any, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve commercially evaluable logo segments (confirmed binding preferred)."""
    linked = _as_dict(pd_linked)
    segments = [
        _as_dict(segment)
        for segment in _as_list(linked.get("segments"))
        if isinstance(segment, dict)
        and _text(segment.get("binding_status")) == "confirmed"
        and _text(segment.get("owning_template_code")) == VOLUMETRIC_LOGO_TEMPLATE_CODE
    ]
    if segments:
        return sorted(segments, key=lambda segment: _text(segment.get("segment_key")))

    # Fallback: geometry/artwork identity when PD linked block absent in quote_input-only previews.
    geometry = _as_dict(payload.get("quote_geometry"))
    boxes = _as_list(geometry.get("artwork_boxes"))
    out: list[dict[str, Any]] = []
    for box in boxes:
        row = _as_dict(box)
        key = _text(row.get("layer_key"))
        if not key:
            continue
        out.append(
            {
                "segment_key": key,
                "display_name": _text(row.get("layer_name")) or key,
                "owning_template_code": VOLUMETRIC_LOGO_TEMPLATE_CODE,
                "binding_status": "confirmed",
                "composition_role": "linked_logo_segment",
            }
        )
    return sorted(out, key=lambda segment: _text(segment.get("segment_key")))


def _box_for_segment(payload: dict[str, Any], segment_key: str) -> dict[str, Any]:
    geometry = _as_dict(payload.get("quote_geometry"))
    for box in _as_list(geometry.get("artwork_boxes")):
        row = _as_dict(box)
        if _text(row.get("layer_key")) == segment_key:
            return row
    return {}


def _return_for_segment(payload: dict[str, Any], segment_key: str) -> dict[str, Any]:
    geometry = _as_dict(payload.get("quote_geometry"))
    for row in _as_list(geometry.get("artwork_return_layers")):
        item = _as_dict(row)
        if _text(item.get("layer_key")) == segment_key:
            return item
    return {}


def _finish_for_segment(payload: dict[str, Any], segment_key: str) -> dict[str, Any]:
    finish = _as_dict(payload.get("finish_setup"))
    for row in _as_list(finish.get("artwork_finishes")):
        item = _as_dict(row)
        if _text(item.get("layer_key")) == segment_key:
            return item
    return {}


def _segment_area_m2(payload: dict[str, Any], segment_key: str) -> float | None:
    finish = _finish_for_segment(payload, segment_key)
    area = _positive(finish.get("estimated_area_m2"))
    if area is not None:
        return area
    box = _box_for_segment(payload, segment_key)
    return _positive(box.get("area_m2"))


def _segment_perimeter_ml(payload: dict[str, Any], segment_key: str) -> float | None:
    ret = _return_for_segment(payload, segment_key)
    peri = _positive(ret.get("return_perimeter_ml"))
    if peri is not None:
        return peri
    # Approximate from bbox when return layer missing: 2*(w+h)/1000
    box = _box_for_segment(payload, segment_key)
    width = _positive(box.get("width_mm"))
    height = _positive(box.get("height_mm"))
    if width is None or height is None:
        return None
    return round(2.0 * (width + height) / 1000.0, 4)


def _logo_illumination_active(payload: dict[str, Any]) -> bool:
    finish = _as_dict(payload.get("finish_setup"))
    if finish.get("illuminated") is False:
        return False
    mode = _text(finish.get("emblem_lighting_mode")).lower() or "area_lit"
    if mode in {"excluded", "none", "off"}:
        return False
    lighting = _text(finish.get("lighting_system_type")).lower()
    if lighting in {"none", "off", ""}:
        # Prefer explicit emblem mode when lighting_system_type absent.
        return mode in {"area_lit", "front_lit", "needs_decision"} or bool(
            _positive(finish.get("emblem_led_module_count"))
        )
    return True


def _segment_led_modules(payload: dict[str, Any], segment_key: str, segment_keys: list[str]) -> float | None:
    if not _logo_illumination_active(payload):
        return None
    finish = _as_dict(payload.get("finish_setup"))
    emblem_total = _positive(finish.get("emblem_led_module_count"))
    if emblem_total is None:
        return None
    areas = {key: _segment_area_m2(payload, key) or 0.0 for key in segment_keys}
    total_area = sum(areas.values())
    if total_area <= 0:
        # Equal split when areas unavailable.
        return round(emblem_total / max(len(segment_keys), 1), 4)
    share = areas.get(segment_key, 0.0) / total_area
    return round(emblem_total * share, 4)


def _print_laminate_required(finish: dict[str, Any]) -> tuple[bool, bool, bool]:
    execution = _text(finish.get("execution_type") or finish.get("face_personalization_method")).lower()
    print_required = finish.get("print_required")
    lam_required = finish.get("lamination_required")
    if print_required is None:
        print_required = execution in {"print", "print_laminate", "printed_artwork"} or bool(
            finish.get("print_material_code")
        )
    if lam_required is None:
        lam_required = execution in {"print_laminate", "laminate"} or bool(finish.get("lamination_material_code"))
    application_required = bool(print_required or lam_required)
    return bool(print_required), bool(lam_required), application_required


def _quantity_for_rule(
    rule: CommercialRuleDefinition,
    *,
    payload: dict[str, Any],
    segment_key: str,
    segment_keys: list[str],
) -> float | None:
    area = _segment_area_m2(payload, segment_key)
    peri = _segment_perimeter_ml(payload, segment_key)
    finish = _finish_for_segment(payload, segment_key)
    print_required, lam_required, application_required = _print_laminate_required(finish)

    if rule.line_code == "logo_face_cnc":
        return peri
    if rule.line_code == "logo_return_cant":
        return peri
    if rule.line_code == "logo_back_cnc":
        return area
    if rule.line_code == "logo_print":
        return area if print_required else None
    if rule.line_code == "logo_laminate":
        return area if lam_required else None
    if rule.line_code == "logo_application":
        return area if application_required else None
    if rule.line_code == "logo_led_modules":
        return _segment_led_modules(payload, segment_key, segment_keys)
    return None


def _build_segment_line(
    rule: CommercialRuleDefinition,
    *,
    quantity: float | None,
    segment_key: str,
    display_name: str,
) -> CommercialPriceLine:
    unit_price = rule.documented_unit_price
    subtotal = None
    if unit_price is not None and quantity is not None and rule.basis_type not in ("unknown",):
        subtotal = round(float(quantity) * float(unit_price), 4)

    line_code = f"{rule.line_code}{SEGMENT_SEP}{segment_key}"
    label = f"{rule.label} — {display_name}"
    return CommercialPriceLine(
        code=line_code,
        label=label,
        module_code=rule.module_code,
        component_code=rule.component_code,
        basis_type=rule.basis_type,
        quantity=quantity,
        unit=rule.unit,
        commercial_unit_price=unit_price,
        subtotal=subtotal,
        pricing_rule_code=rule.pricing_rule_code,
        source=rule.source,
        owner_decision_required=rule.owner_decision_required or unit_price is None,
        warnings=list(rule.warnings),
        segment_key=segment_key,
        layer_identity=segment_key,
        linked_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
    )


def build_linked_logo_commercial_lines(
    *,
    payload: dict[str, Any],
    pd_linked_segments: Any,
) -> tuple[list[CommercialPriceLine], list[CommercialOwnerDecision]]:
    """Emit per-logo commercial lines once; never uses EIC totals or hourly rates."""
    segments = _linked_logo_segments(pd_linked_segments, payload)
    if not segments:
        return [], []

    segment_keys = [_text(segment.get("segment_key")) for segment in segments if _text(segment.get("segment_key"))]
    lines: list[CommercialPriceLine] = []
    owner_decisions: list[CommercialOwnerDecision] = []
    seen_owner: set[str] = set()

    for segment in segments:
        segment_key = _text(segment.get("segment_key"))
        if not segment_key:
            continue
        display_name = _text(segment.get("display_name")) or segment_key
        for rule in LOGO_LINKED_CHILD_COMMERCIAL_RULE_TEMPLATES:
            quantity = _quantity_for_rule(
                rule,
                payload=payload,
                segment_key=segment_key,
                segment_keys=segment_keys,
            )
            if quantity is None and rule.line_code in {
                "logo_print",
                "logo_laminate",
                "logo_application",
                "logo_led_modules",
            }:
                # Dimension not applicable for this logo instance.
                continue
            if quantity is None and rule.documented_unit_price is not None:
                # Geometry missing for a priced body rule — still emit fail-visible line.
                pass
            line = _build_segment_line(
                rule,
                quantity=quantity,
                segment_key=segment_key,
                display_name=display_name,
            )
            lines.append(line)
            if line.owner_decision_required and rule.owner_decision_code:
                if rule.owner_decision_code not in seen_owner:
                    seen_owner.add(rule.owner_decision_code)
                    owner_decisions.append(
                        CommercialOwnerDecision(
                            code=rule.owner_decision_code,
                            label=rule.label,
                            module_code=rule.module_code,
                            detail=rule.owner_decision_detail,
                        )
                    )

    return lines, owner_decisions
