"""Intake V4 owner consumables — adhesive bonding + wiring for illuminated volumetric letters."""

from __future__ import annotations

import math
from typing import Any

from schemas.intake_v4 import IntakeV4MaterialBreakdownWarning, IntakeV4MaterialQuantityRow

OWNER_EUR_RATE_RON = 5.1

# Legacy fallback prices — prefer DB via intake_v4_template_pricing_resolver
# Adhesive — cant to face bonding
ADHESIVE_ML_PER_ML_CANT = 2.0
# Adhesive — supplemental bonding per LED module (production assumption)
ADHESIVE_ML_PER_LED_MODULE = 0.2
ADHESIVE_BOTTLE_ML = 50.0
ADHESIVE_BOTTLE_PRICE_RON = 30.0

# Wire MYYUP 2×0.75 — per letter/segment
WIRE_LETTERS_ML_PER_SEGMENT = 1.0
WIRE_LETTERS_PRICE_RON_PER_ML = 1.9

# Wire MYYUP 2×1.5 — job supply 220V
WIRE_SUPPLY_ML_PER_JOB = 5.0
WIRE_SUPPLY_PRICE_RON_PER_ML = 3.9

BASIS_ADHESIVE_RETURN_TO_FACE = "adhesive_return_to_face_ml_per_ml_cant"
BASIS_ADHESIVE_LED_MODULES = "adhesive_led_modules_ml_per_module"
BASIS_WIRE_LETTERS_PER_SEGMENT = "wire_letters_myyup_2x075_per_segment"
BASIS_WIRE_SUPPLY_PER_JOB = "wire_supply_myyup_2x15_per_job"

PRICE_SOURCE_ADHESIVE = "intake_v4_owner_consumable_adhesive"
PRICE_SOURCE_WIRE_LETTERS = "intake_v4_owner_consumable_wire_letters"
PRICE_SOURCE_WIRE_SUPPLY = "intake_v4_owner_consumable_wire_supply"
MATERIAL_CODE_ADHESIVE = "MAT-ADEZIV-CANT-LITERE"
MATERIAL_CODE_WIRE_LETTERS = "MAT-CABLU-MYYUP-2X075"
MATERIAL_CODE_WIRE_SUPPLY = "MAT-CABLU-MYYUP-2X15"


def is_intake_v4_owner_consumable_price_source(price_source: str | None) -> bool:
    return bool(price_source and price_source.startswith("intake_v4_owner_consumable"))


def owner_ron_to_eur(ron: float) -> float:
    return ron / OWNER_EUR_RATE_RON


def owner_ron_to_eur_display(ron: float) -> float:
    return round(owner_ron_to_eur(ron), 1)


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def resolve_real_letter_or_segment_count(
    geom_sources: list[dict[str, Any] | None],
) -> int | None:
    """Letters/segments for wiring — real letters only, never artwork."""
    for source in geom_sources:
        if not isinstance(source, dict):
            continue
        real = source.get("real_letters_count")
        if isinstance(real, int) and real > 0:
            return real
        if real is not None:
            try:
                parsed = int(float(real))
                if parsed > 0:
                    return parsed
            except (TypeError, ValueError):
                pass
        letter_count = source.get("letter_count")
        if isinstance(letter_count, int) and letter_count > 0:
            return letter_count
        if letter_count is not None:
            try:
                parsed = int(float(letter_count))
                if parsed > 0:
                    return parsed
            except (TypeError, ValueError):
                pass
    return None


def resolve_letter_return_perimeter_ml_for_adhesive(
    letter_return_ml: float | None,
    *,
    total_return_ml: float | None,
    artwork_return_ml: float | None,
) -> float | None:
    """
    Cant/return for real letter faces — excludes artwork return perimeter.

    Prefer letter_return_perimeter_ml (canonical letter-only cant). If absent,
    derive from total minus artwork when both are known.
    """
    if letter_return_ml is not None and letter_return_ml > 0:
        return letter_return_ml
    if total_return_ml is not None and artwork_return_ml is not None:
        derived = total_return_ml - artwork_return_ml
        if derived > 0:
            return derived
    return None


def build_adhesive_return_to_face_row(
    applicable_return_perimeter_ml: float,
) -> IntakeV4MaterialQuantityRow:
    from services.shared_edge_cant_rules import build_edge_cant_adhesive_consumable_row

    return build_edge_cant_adhesive_consumable_row(applicable_return_perimeter_ml)


def build_adhesive_led_modules_row(led_module_count: int) -> IntakeV4MaterialQuantityRow:
    """Supplemental adhesive per mounted LED module — same bottle pricing as cant adhesive."""
    quantity_ml = round(float(led_module_count) * ADHESIVE_ML_PER_LED_MODULE, 4)
    unit_ron_per_ml = ADHESIVE_BOTTLE_PRICE_RON / ADHESIVE_BOTTLE_ML
    unit_eur_precise = owner_ron_to_eur(unit_ron_per_ml)
    bottles_required = int(math.ceil(quantity_ml / ADHESIVE_BOTTLE_ML))
    bottle_eur_display = owner_ron_to_eur_display(ADHESIVE_BOTTLE_PRICE_RON)
    estimated_cost = round(quantity_ml * unit_eur_precise, 2)

    return IntakeV4MaterialQuantityRow(
        material_key="adhesive_led_modules",
        display_name="Adeziv suplimentar module LED",
        material_name="Adeziv suplimentar module LED",
        category="consumable",
        quantity=quantity_ml,
        base_quantity=quantity_ml,
        priced_quantity=quantity_ml,
        unit="ml",
        quantity_basis=BASIS_ADHESIVE_LED_MODULES,
        quantity_source=(
            f"led_module_count×{ADHESIVE_ML_PER_LED_MODULE}"
            f"|bottles_required={bottles_required}"
        ),
        quantity_quality="calculated",
        confidence="estimate_formula",
        consumption_mode="quote_estimate",
        waste_percent=None,
        quantity_with_waste=quantity_ml,
        registry_code=MATERIAL_CODE_ADHESIVE,
        material_code=MATERIAL_CODE_ADHESIVE,
        unit_price=unit_eur_precise,
        currency="EUR",
        material_cost=estimated_cost,
        estimated_cost=estimated_cost,
        price_source=PRICE_SOURCE_ADHESIVE,
        warnings=[
            f"Presupunere producție: {ADHESIVE_ML_PER_LED_MODULE} ml / modul LED lipit suplimentar.",
            f"Flacoane necesare: {bottles_required} × {int(ADHESIVE_BOTTLE_ML)} ml "
            f"({bottle_eur_display} EUR/flacon, excl. TVA)",
        ],
    )


def build_wire_letters_myyup_row(segment_count: int) -> IntakeV4MaterialQuantityRow:
    quantity_ml = float(segment_count) * WIRE_LETTERS_ML_PER_SEGMENT
    unit_eur_precise = owner_ron_to_eur(WIRE_LETTERS_PRICE_RON_PER_ML)
    estimated_cost = round(quantity_ml * unit_eur_precise, 2)

    return IntakeV4MaterialQuantityRow(
        material_key="wire_letters_myyup_2x075",
        display_name="Cablu electric MYYUP 2 x 0.75",
        material_name="Cablu electric MYYUP 2 x 0.75",
        category="consumable",
        quantity=quantity_ml,
        base_quantity=quantity_ml,
        priced_quantity=quantity_ml,
        unit="ml",
        quantity_basis=BASIS_WIRE_LETTERS_PER_SEGMENT,
        quantity_source=f"real_letters_or_segments×{WIRE_LETTERS_ML_PER_SEGMENT}",
        quantity_quality="calculated",
        confidence="estimate_formula",
        consumption_mode="quote_estimate",
        waste_percent=None,
        quantity_with_waste=quantity_ml,
        registry_code=MATERIAL_CODE_WIRE_LETTERS,
        material_code=MATERIAL_CODE_WIRE_LETTERS,
        unit_price=unit_eur_precise,
        currency="EUR",
        material_cost=estimated_cost,
        estimated_cost=estimated_cost,
        price_source=PRICE_SOURCE_WIRE_LETTERS,
    )


def build_wire_supply_myyup_row() -> IntakeV4MaterialQuantityRow:
    quantity_ml = WIRE_SUPPLY_ML_PER_JOB
    unit_eur_precise = owner_ron_to_eur(WIRE_SUPPLY_PRICE_RON_PER_ML)
    estimated_cost = round(quantity_ml * unit_eur_precise, 2)

    return IntakeV4MaterialQuantityRow(
        material_key="wire_supply_myyup_2x15",
        display_name="Cablu electric MYYUP 2 x 1.5 alimentare 220V",
        material_name="Cablu electric MYYUP 2 x 1.5 alimentare 220V",
        category="consumable",
        quantity=quantity_ml,
        base_quantity=quantity_ml,
        priced_quantity=quantity_ml,
        unit="ml",
        quantity_basis=BASIS_WIRE_SUPPLY_PER_JOB,
        quantity_source=f"job_supply_fixed_{WIRE_SUPPLY_ML_PER_JOB}ml",
        quantity_quality="calculated",
        confidence="estimate_formula",
        consumption_mode="quote_estimate",
        waste_percent=None,
        quantity_with_waste=quantity_ml,
        registry_code=MATERIAL_CODE_WIRE_SUPPLY,
        material_code=MATERIAL_CODE_WIRE_SUPPLY,
        unit_price=unit_eur_precise,
        currency="EUR",
        material_cost=estimated_cost,
        estimated_cost=estimated_cost,
        price_source=PRICE_SOURCE_WIRE_SUPPLY,
    )


def append_volumetric_adhesive_and_wiring_consumables(
    *,
    geom_sources: list[dict[str, Any] | None],
    letter_return_ml: float | None,
    total_return_ml: float | None,
    artwork_return_ml: float | None,
    illuminated: bool,
    led_module_count: int | None,
    consumable_rows: list[IntakeV4MaterialQuantityRow],
    warnings: list[IntakeV4MaterialBreakdownWarning],
) -> None:
    segment_count = resolve_real_letter_or_segment_count(geom_sources)
    if segment_count is None or segment_count <= 0:
        return

    adhesive_basis_ml = resolve_letter_return_perimeter_ml_for_adhesive(
        letter_return_ml,
        total_return_ml=total_return_ml,
        artwork_return_ml=artwork_return_ml,
    )
    if adhesive_basis_ml is not None and adhesive_basis_ml > 0:
        consumable_rows.append(build_adhesive_return_to_face_row(adhesive_basis_ml))

    if not illuminated:
        return

    if led_module_count is not None and led_module_count > 0:
        consumable_rows.append(build_adhesive_led_modules_row(led_module_count))

    consumable_rows.append(build_wire_letters_myyup_row(segment_count))
    consumable_rows.append(build_wire_supply_myyup_row())
