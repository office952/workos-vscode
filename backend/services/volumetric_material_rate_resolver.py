"""Quote-time material rate aliases for TPL-VOLUMETRIC-LETTERS variant-priced materials.

CostEngine looks up unit_cost by the template material_code only. Tiered purchase
prices live on variant registry rows; this module copies the matching variant rate
onto the generic template code when quote_input carries the selection key.

Supported aliases (volumetric templates only):
  - MAT-PROFIL-LATERAL-LITERE  ← quote_input.return_depth_mm (30|60|80|100)
  - MAT-LED-PSU-12V            ← quote_input.selected_psu_watts or psu_watts (60|100|160|200)

No prices are hardcoded here — values must already be in material_rates from the registry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional

VOLUMETRIC_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"

# Owner-confirmed return/cant purchase tiers (EUR/ml) — registry codes only.
PROFILE_DEPTH_MM_TO_VARIANT_CODE: Dict[int, str] = {
    30: "MAT-PROFIL-LATERAL-LITERE-30MM",
    60: "MAT-PROFIL-LATERAL-LITERE-60MM",
    80: "MAT-PROFIL-LATERAL-LITERE-80MM",
    100: "MAT-PROFIL-LATERAL-LITERE-100MM",
}

PROFILE_DEPTH_VARIANT_CODES = frozenset(PROFILE_DEPTH_MM_TO_VARIANT_CODE.values())

TEMPLATE_PROFILE_CODE = "MAT-PROFIL-LATERAL-LITERE"

# Owner-confirmed LED PSU purchase tiers (RON/buc) — registry codes only.
PSU_WATTS_TO_VARIANT_CODE: Dict[int, str] = {
    60: "MAT-LED-PSU-12V-60W",
    100: "MAT-LED-PSU-12V-100W",
    160: "MAT-LED-PSU-12V-160W",
    200: "MAT-LED-PSU-12V-200W",
}

PSU_WATTAGE_VARIANT_CODES = frozenset(PSU_WATTS_TO_VARIANT_CODE.values())

TEMPLATE_PSU_CODE = "MAT-LED-PSU-12V"

# Resolution trace statuses (audit / quote-time diagnostics).
RESOLUTION_RESOLVED = "resolved"
RESOLUTION_MISSING_QUOTE_INPUT = "missing_quote_input"
RESOLUTION_MISSING_RETURN_DEPTH_MM = "missing_return_depth_mm"
RESOLUTION_UNSUPPORTED_RETURN_DEPTH_MM = "unsupported_return_depth_mm"
RESOLUTION_MISSING_PSU_WATTS_SELECTION = "missing_psu_watts_selection"
RESOLUTION_UNSUPPORTED_PSU_WATTS = "unsupported_psu_watts"
RESOLUTION_VARIANT_RATE_MISSING = "variant_rate_missing"
RESOLUTION_SKIPPED_NON_VOLUMETRIC_TEMPLATE = "skipped_non_volumetric_template"

OWNER_CONFIRMED_PROFILE_LABOR_NOTES = (
    "Owner-confirmed return labor (deferred in template costing): "
    "Return labor: RETURN_PROFILE_MACHINE_FORMING 5 EUR/ml, "
    "RETURN_PROFILE_FACE_BONDING 5 EUR/ml (workcenter per_linear_meter, separate from material)."
)

READINESS_WARNING_VARIANT_PRICING_READY = (
    "volumetric_profile_depth_variant_pricing:"
    f"{TEMPLATE_PROFILE_CODE}:registry_variants_active;"
    "quote_input.return_depth_mm required at pricing (30|60|80|100); "
    "generic row intentionally has no single unit_cost"
)

READINESS_BLOCKER_VARIANT_INCOMPLETE = "volumetric_profile_depth_variant_incomplete"

READINESS_WARNING_PSU_VARIANT_PRICING_READY = (
    "volumetric_psu_wattage_variant_pricing:"
    f"{TEMPLATE_PSU_CODE}:registry_variants_active;"
    "quote_input.selected_psu_watts or quote_input.psu_watts required at pricing "
    "(60|100|160|200); generic row intentionally has no single unit_cost"
)

READINESS_BLOCKER_PSU_VARIANT_INCOMPLETE = "volumetric_psu_wattage_variant_incomplete"


@dataclass(frozen=True)
class ProfileMaterialRateResolution:
    """Audit trace for profile lateral quote-time rate alias."""

    resolved_code: str
    source_code: Optional[str]
    return_depth_mm: Optional[int]
    unit_cost: Optional[float]
    currency: Optional[str]
    resolution_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PsuMaterialRateResolution:
    """Audit trace for LED PSU quote-time rate alias."""

    resolved_code: str
    source_code: Optional[str]
    selected_psu_watts: Optional[int]
    unit_cost: Optional[float]
    currency: Optional[str]
    resolution_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VolumetricMaterialRatesTrace:
    """Combined audit trace for volumetric variant-priced material aliases."""

    profile_lateral: ProfileMaterialRateResolution
    led_psu_12v: PsuMaterialRateResolution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_lateral": self.profile_lateral.to_dict(),
            "led_psu_12v": self.led_psu_12v.to_dict(),
        }


def is_volumetric_template_code(template_code: Optional[str]) -> bool:
    code = str(template_code or "").strip().upper()
    return "VOLUMETRIC" in code or code == VOLUMETRIC_TEMPLATE_CODE


def _coerce_return_depth_mm(
    quote_input: Mapping[str, Any],
) -> tuple[Optional[int], Optional[str]]:
    """Return (depth_mm, failure_status) where failure_status is a RESOLUTION_* constant."""
    if "return_depth_mm" not in quote_input:
        return None, RESOLUTION_MISSING_RETURN_DEPTH_MM
    raw = quote_input.get("return_depth_mm")
    if raw is None:
        return None, RESOLUTION_MISSING_RETURN_DEPTH_MM
    try:
        depth = int(round(float(raw)))
    except (TypeError, ValueError):
        return None, RESOLUTION_UNSUPPORTED_RETURN_DEPTH_MM
    if depth not in PROFILE_DEPTH_MM_TO_VARIANT_CODE:
        return None, RESOLUTION_UNSUPPORTED_RETURN_DEPTH_MM
    return depth, None


def resolve_profile_lateral_material_rate(
    material_rates: Mapping[str, float],
    quote_input: Optional[Mapping[str, Any]],
    *,
    template_code: Optional[str] = None,
    material_currencies: Optional[Mapping[str, str]] = None,
) -> ProfileMaterialRateResolution:
    """Resolve alias for TEMPLATE_PROFILE_CODE only; fail closed on ambiguity."""
    if template_code is not None and not is_volumetric_template_code(template_code):
        return ProfileMaterialRateResolution(
            resolved_code=TEMPLATE_PROFILE_CODE,
            source_code=None,
            return_depth_mm=None,
            unit_cost=None,
            currency=None,
            resolution_status=RESOLUTION_SKIPPED_NON_VOLUMETRIC_TEMPLATE,
        )

    if not quote_input:
        return ProfileMaterialRateResolution(
            resolved_code=TEMPLATE_PROFILE_CODE,
            source_code=None,
            return_depth_mm=None,
            unit_cost=None,
            currency=None,
            resolution_status=RESOLUTION_MISSING_QUOTE_INPUT,
        )

    depth_mm, depth_failure = _coerce_return_depth_mm(quote_input)
    if depth_failure is not None:
        return ProfileMaterialRateResolution(
            resolved_code=TEMPLATE_PROFILE_CODE,
            source_code=None,
            return_depth_mm=None,
            unit_cost=None,
            currency=None,
            resolution_status=depth_failure,
        )

    variant_code = PROFILE_DEPTH_MM_TO_VARIANT_CODE[depth_mm]
    variant_rate = material_rates.get(variant_code)
    currency = None
    if material_currencies:
        currency = material_currencies.get(variant_code) or material_currencies.get(
            TEMPLATE_PROFILE_CODE
        )

    if variant_rate is None or float(variant_rate) <= 0:
        return ProfileMaterialRateResolution(
            resolved_code=TEMPLATE_PROFILE_CODE,
            source_code=variant_code,
            return_depth_mm=depth_mm,
            unit_cost=None,
            currency=str(currency).strip() if currency else None,
            resolution_status=RESOLUTION_VARIANT_RATE_MISSING,
        )

    unit_cost = float(variant_rate)
    return ProfileMaterialRateResolution(
        resolved_code=TEMPLATE_PROFILE_CODE,
        source_code=variant_code,
        return_depth_mm=depth_mm,
        unit_cost=unit_cost,
        currency=str(currency).strip() if currency else None,
        resolution_status=RESOLUTION_RESOLVED,
    )


def _coerce_selected_psu_watts(
    quote_input: Mapping[str, Any],
) -> tuple[Optional[int], Optional[str]]:
    """Return (watts, failure_status). Requires explicit quote_input selection — no template default."""
    raw = None
    if "selected_psu_watts" in quote_input and quote_input.get("selected_psu_watts") is not None:
        raw = quote_input.get("selected_psu_watts")
    elif "psu_watts" in quote_input and quote_input.get("psu_watts") is not None:
        raw = quote_input.get("psu_watts")
    else:
        return None, RESOLUTION_MISSING_PSU_WATTS_SELECTION
    try:
        watts = int(round(float(raw)))
    except (TypeError, ValueError):
        return None, RESOLUTION_UNSUPPORTED_PSU_WATTS
    if watts not in PSU_WATTS_TO_VARIANT_CODE:
        return None, RESOLUTION_UNSUPPORTED_PSU_WATTS
    return watts, None


def resolve_led_psu_material_rate(
    material_rates: Mapping[str, float],
    quote_input: Optional[Mapping[str, Any]],
    *,
    template_code: Optional[str] = None,
    material_currencies: Optional[Mapping[str, str]] = None,
) -> PsuMaterialRateResolution:
    """Resolve alias for TEMPLATE_PSU_CODE only; fail closed without explicit wattage."""
    if template_code is not None and not is_volumetric_template_code(template_code):
        return PsuMaterialRateResolution(
            resolved_code=TEMPLATE_PSU_CODE,
            source_code=None,
            selected_psu_watts=None,
            unit_cost=None,
            currency=None,
            resolution_status=RESOLUTION_SKIPPED_NON_VOLUMETRIC_TEMPLATE,
        )

    if not quote_input:
        return PsuMaterialRateResolution(
            resolved_code=TEMPLATE_PSU_CODE,
            source_code=None,
            selected_psu_watts=None,
            unit_cost=None,
            currency=None,
            resolution_status=RESOLUTION_MISSING_QUOTE_INPUT,
        )

    psu_watts, psu_failure = _coerce_selected_psu_watts(quote_input)
    if psu_failure is not None:
        return PsuMaterialRateResolution(
            resolved_code=TEMPLATE_PSU_CODE,
            source_code=None,
            selected_psu_watts=None,
            unit_cost=None,
            currency=None,
            resolution_status=psu_failure,
        )

    variant_code = PSU_WATTS_TO_VARIANT_CODE[psu_watts]
    variant_rate = material_rates.get(variant_code)
    currency = None
    if material_currencies:
        currency = material_currencies.get(variant_code) or material_currencies.get(
            TEMPLATE_PSU_CODE
        )

    if variant_rate is None or float(variant_rate) <= 0:
        return PsuMaterialRateResolution(
            resolved_code=TEMPLATE_PSU_CODE,
            source_code=variant_code,
            selected_psu_watts=psu_watts,
            unit_cost=None,
            currency=str(currency).strip() if currency else None,
            resolution_status=RESOLUTION_VARIANT_RATE_MISSING,
        )

    return PsuMaterialRateResolution(
        resolved_code=TEMPLATE_PSU_CODE,
        source_code=variant_code,
        selected_psu_watts=psu_watts,
        unit_cost=float(variant_rate),
        currency=str(currency).strip() if currency else None,
        resolution_status=RESOLUTION_RESOLVED,
    )


def _apply_resolved_aliases(
    out: Dict[str, float],
    *,
    profile: ProfileMaterialRateResolution,
    psu: PsuMaterialRateResolution,
) -> None:
    if profile.resolution_status == RESOLUTION_RESOLVED and profile.unit_cost is not None:
        out[TEMPLATE_PROFILE_CODE] = profile.unit_cost
    if psu.resolution_status == RESOLUTION_RESOLVED and psu.unit_cost is not None:
        out[TEMPLATE_PSU_CODE] = psu.unit_cost


def resolve_volumetric_material_rates(
    material_rates: Mapping[str, float],
    quote_input: Optional[Mapping[str, Any]],
    *,
    template_code: Optional[str] = None,
    material_currencies: Optional[Mapping[str, str]] = None,
) -> Dict[str, float]:
    """Return a copy of material_rates with volumetric variant aliases applied when possible."""
    profile = resolve_profile_lateral_material_rate(
        material_rates,
        quote_input,
        template_code=template_code,
        material_currencies=material_currencies,
    )
    psu = resolve_led_psu_material_rate(
        material_rates,
        quote_input,
        template_code=template_code,
        material_currencies=material_currencies,
    )
    out: Dict[str, float] = dict(material_rates)
    _apply_resolved_aliases(out, profile=profile, psu=psu)
    return out


def resolve_volumetric_material_rates_with_trace(
    material_rates: Mapping[str, float],
    quote_input: Optional[Mapping[str, Any]],
    *,
    template_code: Optional[str] = None,
    material_currencies: Optional[Mapping[str, str]] = None,
) -> tuple[Dict[str, float], VolumetricMaterialRatesTrace]:
    """Apply volumetric aliases and return combined audit trace."""
    profile = resolve_profile_lateral_material_rate(
        material_rates,
        quote_input,
        template_code=template_code,
        material_currencies=material_currencies,
    )
    psu = resolve_led_psu_material_rate(
        material_rates,
        quote_input,
        template_code=template_code,
        material_currencies=material_currencies,
    )
    out: Dict[str, float] = dict(material_rates)
    _apply_resolved_aliases(out, profile=profile, psu=psu)
    return out, VolumetricMaterialRatesTrace(profile_lateral=profile, led_psu_12v=psu)


def inventory_row_price_complete(row: Any) -> bool:
    return (
        row is not None
        and row.unit_cost is not None
        and row.unit_cost > 0
        and bool(str(row.currency or "").strip())
        and row.vat_percent is not None
        and row.valid_from is not None
    )


def evaluate_profile_depth_variant_registry(
    rows_by_code: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    """True when all depth variant rows exist, active, and price-complete."""
    incomplete: list[str] = []
    for code in sorted(PROFILE_DEPTH_VARIANT_CODES):
        row = rows_by_code.get(code)
        if row is None:
            incomplete.append(f"{code}:missing")
            continue
        status = str(getattr(row, "status", None) or "").strip().lower()
        if status != "active":
            incomplete.append(f"{code}:status={status or 'unknown'}")
            continue
        if not inventory_row_price_complete(row):
            incomplete.append(f"{code}:price_incomplete")
    return len(incomplete) == 0, incomplete


def evaluate_psu_wattage_variant_registry(
    rows_by_code: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    """True when all PSU wattage variant rows exist, active, and price-complete."""
    incomplete: list[str] = []
    for code in sorted(PSU_WATTAGE_VARIANT_CODES):
        row = rows_by_code.get(code)
        if row is None:
            incomplete.append(f"{code}:missing")
            continue
        status = str(getattr(row, "status", None) or "").strip().lower()
        if status != "active":
            incomplete.append(f"{code}:status={status or 'unknown'}")
            continue
        if not inventory_row_price_complete(row):
            incomplete.append(f"{code}:price_incomplete")
    return len(incomplete) == 0, incomplete
