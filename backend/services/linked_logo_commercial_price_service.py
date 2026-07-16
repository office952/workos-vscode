"""Linked-logo commercial line expansion for CommercialPriceProposal (letters root)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.commercial_rules_volumetric_v2 import (
    LOGO_LINKED_CHILD_COMMERCIAL_RULE_TEMPLATES,
    CommercialRuleDefinition,
)
from models.workcenter_rates import Workcenter_rates
from schemas.commercial_price_proposal import CommercialOwnerDecision, CommercialPriceLine
from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE

SEGMENT_SEP = "::"

# Incomplete material stub — never treat as commercial laminate tariff.
FORBIDDEN_LAMINATION_STUB_CODE = "SVC-LAMINATION-SERVICE"
CURRENCY_CONVERSION_SOURCE = "company_commercial_settings.eur_to_ron_rate"


@dataclass(frozen=True)
class _ResolvedRegistryRate:
    pricing_code: str
    unit_price_source: float
    source_currency: str
    rate_basis: str
    status: str
    label: str


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


async def _load_registry_operation_rate(
    db: AsyncSession,
    pricing_code: str,
) -> _ResolvedRegistryRate | None:
    """Read existing workcenter_rates row — never invent prices or use forbidden stubs."""
    code = _text(pricing_code).upper()
    if not code or code == FORBIDDEN_LAMINATION_STUB_CODE:
        return None
    row = (
        await db.execute(select(Workcenter_rates).where(Workcenter_rates.code == code).limit(1))
    ).scalar_one_or_none()
    if row is None:
        return None
    status = _text(row.status).lower() or "missing_price"
    if status != "active" or not bool(row.is_active):
        return None
    basis = _text(row.rate_basis).lower() or "per_hour"
    # Square-meter commercial ops store the mp rate in rate_per_linear_meter column historically.
    amount = _positive(row.rate_per_linear_meter)
    if basis == "per_hour":
        # Commercial logo finish must never use hourly rates.
        return None
    if amount is None:
        return None
    currency = _text(row.currency).upper()
    if not currency:
        return None
    return _ResolvedRegistryRate(
        pricing_code=code,
        unit_price_source=float(amount),
        source_currency=currency,
        rate_basis=basis,
        status=status,
        label=_text(row.label) or code,
    )


async def _canonical_eur_to_ron_rate(db: AsyncSession) -> tuple[float | None, str | None]:
    """Read persisted company FX without inventing/bootstrapping a diagnostic rate.

    Unlike get_eur_to_ron_rate(), this path fails closed when eur_to_ron_rate is NULL.
    It does not write DEFAULT_EUR_TO_RON_RATE into the commercial logo binding path.
    """
    from models.company_commercial_settings import CompanyCommercialSettings

    row = (
        await db.execute(
            select(CompanyCommercialSettings).order_by(CompanyCommercialSettings.id.asc()).limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        return None, "company_commercial_settings_row_missing"
    rate = getattr(row, "eur_to_ron_rate", None)
    if rate is None:
        return None, "eur_to_ron_rate_unset"
    try:
        value = float(rate)
    except (TypeError, ValueError):
        return None, "eur_to_ron_rate_invalid"
    if value <= 0:
        return None, "eur_to_ron_rate_invalid"
    return value, None


async def _normalize_unit_price_to_cpp_ron(
    db: AsyncSession,
    *,
    unit_price: float,
    source_currency: str,
) -> tuple[float | None, float | None, str | None, str | None]:
    """Canonical EUR→RON via persisted company settings. Fail closed if unset."""
    currency = _text(source_currency).upper()
    if not currency:
        return None, None, None, "source_currency_missing"
    if currency == "RON":
        return float(unit_price), 1.0, "identity", None
    if currency != "EUR":
        return None, None, None, f"unsupported_source_currency={currency}"
    rate, err = await _canonical_eur_to_ron_rate(db)
    if rate is None:
        return None, None, None, f"currency_conversion_unavailable:{err or 'unknown'}"
    return round(float(unit_price) * rate, 6), rate, CURRENCY_CONVERSION_SOURCE, None


def _build_segment_line(
    rule: CommercialRuleDefinition,
    *,
    quantity: float | None,
    segment_key: str,
    display_name: str,
    unit_price: float | None,
    owner_decision_required: bool,
    warnings: list[str],
    source: str,
    registry_pricing_code: str | None = None,
    source_currency: str | None = None,
    cpp_currency: str | None = None,
    currency_conversion_rate: float | None = None,
    currency_conversion_source: str | None = None,
) -> CommercialPriceLine:
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
        source=source,
        owner_decision_required=owner_decision_required,
        warnings=warnings,
        segment_key=segment_key,
        layer_identity=segment_key,
        linked_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        registry_pricing_code=registry_pricing_code,
        source_currency=source_currency,
        cpp_currency=cpp_currency,
        currency_conversion_rate=currency_conversion_rate,
        currency_conversion_source=currency_conversion_source,
    )


async def build_linked_logo_commercial_lines(
    *,
    db: AsyncSession,
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
    registry_cache: dict[str, _ResolvedRegistryRate | None] = {}

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
                continue

            warnings = list(rule.warnings)
            unit_price = rule.documented_unit_price
            owner_required = bool(rule.owner_decision_required) or unit_price is None
            source = rule.source
            registry_code: str | None = None
            source_currency: str | None = rule.documented_unit_price_currency
            cpp_currency: str | None = "RON" if unit_price is not None else None
            fx_rate: float | None = None
            fx_source: str | None = None

            mapped_code = _text(rule.registry_pricing_code).upper() or None
            if mapped_code:
                registry_code = mapped_code
                if mapped_code not in registry_cache:
                    registry_cache[mapped_code] = await _load_registry_operation_rate(db, mapped_code)
                resolved = registry_cache[mapped_code]
                if resolved is None:
                    unit_price = None
                    owner_required = True
                    warnings.append(
                        f"registry_lookup_missed:{mapped_code};configure_at=/inventory/pricing"
                    )
                    source = f"{rule.source}:registry_unresolved"
                else:
                    ron_price, fx_rate, fx_source, fx_error = await _normalize_unit_price_to_cpp_ron(
                        db,
                        unit_price=resolved.unit_price_source,
                        source_currency=resolved.source_currency,
                    )
                    if ron_price is None:
                        unit_price = None
                        owner_required = True
                        warnings.append(
                            f"BLOCKED_BY_CANONICAL_CURRENCY_CONVERSION:{fx_error or 'unknown'}"
                        )
                        source = f"{rule.source}:currency_gate_blocked"
                        source_currency = resolved.source_currency
                        cpp_currency = None
                    else:
                        unit_price = ron_price
                        owner_required = False
                        source_currency = resolved.source_currency
                        cpp_currency = "RON"
                        source = (
                            f"pricing_registry:operation:{resolved.pricing_code}"
                            f":{resolved.source_currency}->{cpp_currency}"
                        )
                        warnings.append(
                            f"registry_bound={resolved.pricing_code};"
                            f"source_unit_price={resolved.unit_price_source};"
                            f"rate_basis={resolved.rate_basis}"
                        )

            line = _build_segment_line(
                rule,
                quantity=quantity,
                segment_key=segment_key,
                display_name=display_name,
                unit_price=unit_price,
                owner_decision_required=owner_required,
                warnings=warnings,
                source=source,
                registry_pricing_code=registry_code,
                source_currency=source_currency,
                cpp_currency=cpp_currency,
                currency_conversion_rate=fx_rate,
                currency_conversion_source=fx_source,
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
