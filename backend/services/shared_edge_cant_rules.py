"""Shared edge/cant rules — ProductSystem foundation (cant/volum length, adhesive, Oracal 651 wrap).

Preview-only outputs: no stock consumption, no real tasks, no ExecutionPlan writes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from schemas.intake_v4 import IntakeV4EdgeCantOperationRow, IntakeV4MaterialQuantityRow
from services.intake_v4_consumables_adhesive_wiring_service import (
    ADHESIVE_BOTTLE_ML,
    ADHESIVE_BOTTLE_PRICE_RON,
    MATERIAL_CODE_ADHESIVE,
    owner_ron_to_eur,
    owner_ron_to_eur_display,
)
from services.shared_vinyl_material_catalog import (
    ORACAL_651_OWNER_EUR_PER_M2,
    VinylApplication,
    get_oracal_profile_by_series,
    is_vinyl_application_allowed,
    profiles_for_vinyl_application,
    resolve_owner_oracal_price_eur_per_sqm,
)
from services.volumetric_face_vinyl_service import RETURN_VINYL_BAND_EXTRA_MM

SHARED_EDGE_CANT_SOURCE = "shared_edge_cant_rules"
EDGE_CANT_TASK_DRY_RUN_SOURCE = SHARED_EDGE_CANT_SOURCE

EDGE_CANT_QUOTE_WASTE_PERCENT = 20.0
EDGE_CANT_ADHESIVE_ML_PER_ML = 2.0
EDGE_CANT_BOND_OWNER_EUR_PER_ML = 5.0

EDGE_CANT_BOND_OPERATION_KEY = "edge_cant_bond_to_face"
EDGE_CANT_ORACAL_WRAP_OPERATION_KEY = "edge_cant_oracal_wrap"

BASIS_EDGE_CANT_PERIMETER = "perimeter_with_waste"
BASIS_EDGE_CANT_ADHESIVE = "adhesive_return_to_face_ml_per_ml_cant"
BASIS_EDGE_CANT_ORACAL_AREA = "edge_cant_oracal_wrapped_area_m2"

EDGE_CANT_ORACAL_SERIES = "651"
EDGE_CANT_ORACAL_MATERIAL_KEY = "edge_cant_oracal_651"
EDGE_CANT_LINEAR_UNIT = "m"

_RETURN_ORACAL_WRAPPED_FINISHES = frozenset({"oracal_wrapped", "colantat", "oracal"})

PRICE_SOURCE_EDGE_CANT_ADHESIVE = "intake_v4_owner_consumable_adhesive"
PRICE_SOURCE_EDGE_CANT_BOND_OWNER_RATE = "intake_v4_owner_edge_cant_bond_5eur_per_ml_total_graphic"


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def return_finish_requires_oracal_651_wrap(return_finish: str | None) -> bool:
    token = str(return_finish or "").strip().lower()
    return token in _RETURN_ORACAL_WRAPPED_FINISHES


def apply_edge_cant_quote_waste(
    calculated_ml: float | None,
    *,
    waste_percent: float = EDGE_CANT_QUOTE_WASTE_PERCENT,
) -> tuple[float, float, float]:
    """Return (calculated_ml, quote_ml, waste_percent) — quote = calculated × (1 + waste%)."""
    if calculated_ml is None or calculated_ml <= 0:
        return 0.0, 0.0, waste_percent
    base = float(calculated_ml)
    priced = round(base * (1.0 + waste_percent / 100.0), 4)
    return base, priced, waste_percent


def resolve_oracal_wrapped_return_perimeter_ml(
    letter_groups: list[Any],
    default_return_finish: str,
    *,
    total_return_ml: float | None = None,
    letter_return_ml: float | None = None,
) -> float | None:
    """Perimeter (ml) of letter groups whose cant finish requires Oracal 651 wrap."""
    if letter_groups:
        wrapped_ml = 0.0
        has_wrapped_group = False
        has_group_perimeter = False
        for group in letter_groups:
            if not isinstance(group, dict):
                continue
            ret = str(group.get("return_finish_type") or default_return_finish)
            if not return_finish_requires_oracal_651_wrap(ret):
                continue
            has_wrapped_group = True
            perimeter = _positive(group.get("perimeter_m"))
            if perimeter:
                wrapped_ml += perimeter
                has_group_perimeter = True
        if has_group_perimeter and wrapped_ml > 0:
            return wrapped_ml
        if has_wrapped_group:
            return total_return_ml or letter_return_ml
        return None
    if return_finish_requires_oracal_651_wrap(default_return_finish):
        return total_return_ml or letter_return_ml
    return None


def resolve_edge_cant_material_basis_ml(
    *,
    letter_return_ml: float | None,
    total_return_ml: float | None,
) -> float | None:
    """Calculated cant/volum length used for aluminum return material row (combined when applicable)."""
    return total_return_ml or letter_return_ml


def resolve_edge_cant_adhesive_basis_ml(
    letter_return_ml: float | None,
    *,
    total_return_ml: float | None = None,
    artwork_return_ml: float | None = None,
) -> float | None:
    """Letter-only cant for adhesive — excludes artwork return perimeter."""
    if letter_return_ml is not None and letter_return_ml > 0:
        return letter_return_ml
    if total_return_ml is not None and artwork_return_ml is not None:
        derived = total_return_ml - artwork_return_ml
        if derived > 0:
            return derived
    return None


@dataclass(frozen=True)
class EdgeCantRuleInput:
    template_key: str = "TPL-VOLUMETRIC-LETTERS"
    product_type: str = "volumetric_letters"
    edge_mode: str | None = None
    edge_depth_mm: float | None = None
    edge_finish_key: str | None = None
    edge_material_key: str | None = None
    edge_base_perimeter_m: float | None = None
    edge_calculated_perimeter_m: float | None = None
    edge_quote_waste_factor: float = EDGE_CANT_QUOTE_WASTE_PERCENT
    letter_count: int | None = None
    geometry_source: str | None = None
    finish_setup_source: str | None = None
    letter_return_ml: float | None = None
    total_return_ml: float | None = None
    artwork_return_ml: float | None = None
    letter_groups: list[Any] = field(default_factory=list)
    default_return_finish: str = "white_aluminum"


@dataclass
class EdgeCantRuleResult:
    edge_present: bool = False
    edge_label: str = "Cant / volum"
    edge_material_label: str | None = None
    edge_finish_label: str | None = None
    calculated_edge_length_m: float = 0.0
    quote_edge_length_m: float = 0.0
    waste_factor: float = EDGE_CANT_QUOTE_WASTE_PERCENT
    waste_length_m: float = 0.0
    adhesive_ml: float = 0.0
    adhesive_rule_key: str = BASIS_EDGE_CANT_ADHESIVE
    vinyl_series_if_wrapped: str | None = None
    vinyl_application_key: str | None = None
    oracal_wrapped_perimeter_ml: float | None = None
    oracal_wrapped_quote_perimeter_ml: float | None = None
    operation_rows: list[IntakeV4EdgeCantOperationRow] = field(default_factory=list)
    consumable_rows: list[IntakeV4MaterialQuantityRow] = field(default_factory=list)
    material_rows: list[IntakeV4MaterialQuantityRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source: str = SHARED_EDGE_CANT_SOURCE


def resolve_edge_cant_oracal_651_profile() -> Any:
    """Oracal 651 profile for cant/volum wrapping — never 641 or 8500."""
    profile = get_oracal_profile_by_series(EDGE_CANT_ORACAL_SERIES)
    if profile is None:
        return None
    if not is_vinyl_application_allowed(EDGE_CANT_ORACAL_SERIES, VinylApplication.RETURN_CANT_VOLUM_WRAPPING):
        return None
    return profile


def build_edge_cant_adhesive_consumable_row(applicable_return_perimeter_ml: float) -> IntakeV4MaterialQuantityRow:
    quantity_ml = round(applicable_return_perimeter_ml * EDGE_CANT_ADHESIVE_ML_PER_ML, 4)
    unit_ron_per_ml = ADHESIVE_BOTTLE_PRICE_RON / ADHESIVE_BOTTLE_ML
    unit_eur_precise = owner_ron_to_eur(unit_ron_per_ml)
    bottles_required = int(math.ceil(quantity_ml / ADHESIVE_BOTTLE_ML))
    bottle_eur_display = owner_ron_to_eur_display(ADHESIVE_BOTTLE_PRICE_RON)
    estimated_cost = round(quantity_ml * unit_eur_precise, 2)

    return IntakeV4MaterialQuantityRow(
        material_key="adhesive_return_to_face",
        display_name="Adeziv lipire cant pe fețe litere",
        material_name="Adeziv lipire cant pe fețe litere",
        category="consumable",
        quantity=quantity_ml,
        base_quantity=quantity_ml,
        priced_quantity=quantity_ml,
        unit="ml",
        quantity_basis=BASIS_EDGE_CANT_ADHESIVE,
        quantity_source=(
            f"{SHARED_EDGE_CANT_SOURCE}|letter_return_perimeter_m×{EDGE_CANT_ADHESIVE_ML_PER_ML}"
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
        price_source=PRICE_SOURCE_EDGE_CANT_ADHESIVE,
        warnings=[
            f"Flacoane necesare: {bottles_required} × {int(ADHESIVE_BOTTLE_ML)} ml "
            f"({bottle_eur_display} EUR/flacon, excl. TVA)"
        ],
    )


def compute_return_wrap_area_m2(
    perimeter_m: float,
    return_depth_mm: float,
    *,
    waste_percent: float = EDGE_CANT_QUOTE_WASTE_PERCENT,
    band_extra_mm: float = RETURN_VINYL_BAND_EXTRA_MM,
) -> float:
    """Technical Oracal wrap area (m²) for return/cant band.

    Same geometry as ``build_edge_cant_oracal_651_material_row`` without pricing
    and without inventing a default depth. Callers must supply positive inputs.
    """
    base_ml, priced_ml, _waste_pct = apply_edge_cant_quote_waste(
        float(perimeter_m),
        waste_percent=waste_percent,
    )
    if priced_ml <= 0 or base_ml <= 0:
        return 0.0
    band_width_m = (float(return_depth_mm) + float(band_extra_mm)) / 1000.0
    if band_width_m <= 0:
        return 0.0
    return round(priced_ml * band_width_m, 4)


def build_edge_cant_oracal_651_material_row(
    *,
    wrapped_calculated_ml: float,
    return_depth_mm: float | None,
    waste_percent: float = EDGE_CANT_QUOTE_WASTE_PERCENT,
) -> IntakeV4MaterialQuantityRow | None:
    profile = resolve_edge_cant_oracal_651_profile()
    if profile is None:
        return None

    base_ml, priced_ml, waste_pct = apply_edge_cant_quote_waste(
        wrapped_calculated_ml,
        waste_percent=waste_percent,
    )
    if priced_ml <= 0:
        return None

    depth_mm = float(return_depth_mm or 60)
    area_m2 = compute_return_wrap_area_m2(
        wrapped_calculated_ml,
        depth_mm,
        waste_percent=waste_percent,
    )

    owner_price = resolve_owner_oracal_price_eur_per_sqm(EDGE_CANT_ORACAL_SERIES)
    unit_price: float | None = None
    price_source = "missing"
    estimated_cost: float | None = None
    if owner_price:
        unit_price, _, price_source_key = owner_price
        price_source = f"{SHARED_EDGE_CANT_SOURCE}|{price_source_key}"
        estimated_cost = round(area_m2 * unit_price, 4)

    registry_code = profile.breakdown_material_code or profile.registry_code

    return IntakeV4MaterialQuantityRow(
        material_key=EDGE_CANT_ORACAL_MATERIAL_KEY,
        display_name="Oracal 651 / cant volum",
        material_name="Oracal 651 / cant volum",
        category="material",
        quantity=area_m2,
        base_quantity=area_m2,
        priced_quantity=area_m2,
        unit="m2",
        quantity_basis=BASIS_EDGE_CANT_ORACAL_AREA,
        quantity_source=(
            f"{SHARED_EDGE_CANT_SOURCE}|quote_edge_m={priced_ml}|band_mm={depth_mm + RETURN_VINYL_BAND_EXTRA_MM}"
        ),
        quantity_quality="calculated",
        confidence="estimate_for_quote",
        consumption_mode="quote_estimate",
        waste_percent=waste_pct,
        quantity_with_waste=area_m2,
        registry_code=registry_code,
        material_code=registry_code,
        unit_price=unit_price,
        price_source=price_source,
        currency="EUR",
        material_cost=estimated_cost,
        estimated_cost=estimated_cost,
        warnings=list(profile.warnings[:2]) if profile.warnings else [],
    )


def _bond_operation_row(bond_basis_ml: float) -> IntakeV4EdgeCantOperationRow:
    quantity = round(bond_basis_ml, 4)
    return IntakeV4EdgeCantOperationRow(
        key=EDGE_CANT_BOND_OPERATION_KEY,
        display_name="Lipire cant / volum pe față litere",
        operation_type="assembly",
        quantity=quantity,
        unit=EDGE_CANT_LINEAR_UNIT,
        basis_key="return_material_perimeter_ml",
        basis_label="Perimetru grafica totala / cant total (lipire)",
        operation_equivalent_quantity=quantity,
        operation_equivalent_unit=EDGE_CANT_LINEAR_UNIT,
        pricing_rate_key="workcenter_rates:RETURN_PROFILE_FACE_BONDING:per_linear_meter",
        unit_price=None,
        estimated_cost=None,
        pricing_status="missing_rate",
        tpl_operation_key="return_face_bonding",
        dossier_operation_key="return_face_bonding",
        workstation_key="assembly_bench",
        required_skill_key="assembly_operator",
        material_key="return_material",
        material_name="Cant / volum",
        consumes_stock_now=False,
        creates_task_now=False,
        source=SHARED_EDGE_CANT_SOURCE,
        warnings=[
            "dry_run_preview_no_real_task",
            "stock_not_consumed",
            "pricing_registry:RETURN_PROFILE_FACE_BONDING",
        ],
    )


def _oracal_wrap_operation_row(quote_wrapped_ml: float) -> IntakeV4EdgeCantOperationRow:
    return IntakeV4EdgeCantOperationRow(
        key=EDGE_CANT_ORACAL_WRAP_OPERATION_KEY,
        display_name="Aplicare Oracal 651 pe cant / volum",
        operation_type="vinyl_application",
        quantity=round(quote_wrapped_ml, 4),
        unit=EDGE_CANT_LINEAR_UNIT,
        basis_key=BASIS_EDGE_CANT_PERIMETER,
        basis_label="Cant / volum pentru preț (Oracal 651)",
        pricing_status="missing_rate",
        tpl_operation_key="return_vinyl_workbench",
        dossier_operation_key="return_vinyl_application_workbench",
        operation_catalog_key="return_vinyl_application_workbench",
        workstation_key="workbench",
        required_skill_key="vinyl_operator",
        material_key=EDGE_CANT_ORACAL_MATERIAL_KEY,
        material_name="Oracal 651 / cant volum",
        consumes_stock_now=False,
        creates_task_now=False,
        source=SHARED_EDGE_CANT_SOURCE,
        warnings=["dry_run_preview_no_real_task", "stock_not_consumed"],
    )


def evaluate_edge_cant_rules(input_data: EdgeCantRuleInput) -> EdgeCantRuleResult:
    material_basis_ml = resolve_edge_cant_material_basis_ml(
        letter_return_ml=input_data.letter_return_ml,
        total_return_ml=input_data.total_return_ml,
    )
    adhesive_basis_ml = resolve_edge_cant_adhesive_basis_ml(
        input_data.letter_return_ml,
        total_return_ml=input_data.total_return_ml,
        artwork_return_ml=input_data.artwork_return_ml,
    )

    if material_basis_ml is None and adhesive_basis_ml is None:
        return EdgeCantRuleResult(source=SHARED_EDGE_CANT_SOURCE)

    calc_ml, quote_ml, waste_pct = apply_edge_cant_quote_waste(
        material_basis_ml,
        waste_percent=input_data.edge_quote_waste_factor,
    )

    result = EdgeCantRuleResult(
        edge_present=True,
        calculated_edge_length_m=calc_ml,
        quote_edge_length_m=quote_ml,
        waste_factor=waste_pct,
        waste_length_m=round(quote_ml - calc_ml, 4) if quote_ml > calc_ml else 0.0,
        source=SHARED_EDGE_CANT_SOURCE,
    )

    if adhesive_basis_ml is not None and adhesive_basis_ml > 0:
        result.adhesive_ml = round(adhesive_basis_ml * EDGE_CANT_ADHESIVE_ML_PER_ML, 4)

    wrapped_ml = resolve_oracal_wrapped_return_perimeter_ml(
        input_data.letter_groups,
        input_data.default_return_finish,
        total_return_ml=input_data.total_return_ml,
        letter_return_ml=input_data.letter_return_ml,
    )
    if wrapped_ml is not None and wrapped_ml > 0:
        _, wrapped_quote_ml, _ = apply_edge_cant_quote_waste(
            wrapped_ml,
            waste_percent=input_data.edge_quote_waste_factor,
        )
        result.oracal_wrapped_perimeter_ml = wrapped_ml
        result.oracal_wrapped_quote_perimeter_ml = wrapped_quote_ml
        result.vinyl_series_if_wrapped = EDGE_CANT_ORACAL_SERIES
        result.vinyl_application_key = VinylApplication.RETURN_CANT_VOLUM_WRAPPING.value

        oracal_row = build_edge_cant_oracal_651_material_row(
            wrapped_calculated_ml=wrapped_ml,
            return_depth_mm=input_data.edge_depth_mm,
            waste_percent=input_data.edge_quote_waste_factor,
        )
        if oracal_row is not None:
            result.material_rows.append(oracal_row)

        result.operation_rows.append(_oracal_wrap_operation_row(wrapped_quote_ml))

    if material_basis_ml is not None and material_basis_ml > 0:
        result.operation_rows.append(_bond_operation_row(material_basis_ml))

    # Guard: 641/8500 must never appear on edge cant vinyl
    for profile in profiles_for_vinyl_application(VinylApplication.RETURN_CANT_VOLUM_WRAPPING):
        if profile.series in {"641", "8500"}:
            result.warnings.append(f"unexpected_edge_cant_vinyl_series:{profile.series}")

    return result


def edge_cant_profiles_forbidden_on_wrap() -> tuple[str, ...]:
    """Series that must not be used for cant/volum Oracal wrap."""
    return ("641", "8500")
