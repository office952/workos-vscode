"""Quote-time ACM/Bond panel material alias by acm_thickness_mm.

Templates TPL-ACM-CASSETTED-PANEL and TPL-CUT-ACM-LETTERS reference the generic
registry code MAT-ACM-BOND-PANEL; variant rows hold owner-confirmed purchase costs.

No prices hardcoded — values must exist in material_rates from the registry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional

ACM_TEMPLATE_CODES = frozenset(
    {
        "TPL-ACM-CASSETTED-PANEL",
        "TPL-CUT-ACM-LETTERS",
    }
)

TEMPLATE_ACM_BOND_CODE = "MAT-ACM-BOND-PANEL"

ACM_THICKNESS_MM_TO_VARIANT_CODE: Dict[int, str] = {
    3: "MAT-ACM-BOND-3MM",
    4: "MAT-ACM-BOND-4MM",
}

RESOLUTION_RESOLVED = "resolved"
RESOLUTION_SKIPPED_NON_ACM_TEMPLATE = "skipped_non_acm_template"
RESOLUTION_MISSING_QUOTE_INPUT = "missing_quote_input"
RESOLUTION_MISSING_ACM_THICKNESS = "missing_acm_thickness_mm"
RESOLUTION_UNSUPPORTED_ACM_THICKNESS = "unsupported_acm_thickness_mm"
RESOLUTION_VARIANT_RATE_MISSING = "variant_rate_missing"


@dataclass(frozen=True)
class AcmBondMaterialRateResolution:
    resolved_code: str
    source_code: Optional[str]
    acm_thickness_mm: Optional[int]
    unit_cost: Optional[float]
    currency: Optional[str]
    resolution_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def is_acm_bond_template_code(template_code: Optional[str]) -> bool:
    return str(template_code or "").strip().upper() in ACM_TEMPLATE_CODES


def _coerce_acm_thickness_mm(
    quote_input: Mapping[str, Any],
) -> tuple[Optional[int], Optional[str]]:
    if "acm_thickness_mm" not in quote_input:
        return None, RESOLUTION_MISSING_ACM_THICKNESS
    raw = quote_input.get("acm_thickness_mm")
    if raw is None:
        return None, RESOLUTION_MISSING_ACM_THICKNESS
    try:
        thickness = int(round(float(raw)))
    except (TypeError, ValueError):
        return None, RESOLUTION_UNSUPPORTED_ACM_THICKNESS
    if thickness not in ACM_THICKNESS_MM_TO_VARIANT_CODE:
        return None, RESOLUTION_UNSUPPORTED_ACM_THICKNESS
    return thickness, None


def resolve_acm_bond_panel_material_rate(
    material_rates: Mapping[str, float],
    quote_input: Optional[Mapping[str, Any]],
    *,
    template_code: Optional[str] = None,
    material_currencies: Optional[Mapping[str, str]] = None,
) -> AcmBondMaterialRateResolution:
    if template_code is not None and not is_acm_bond_template_code(template_code):
        return AcmBondMaterialRateResolution(
            resolved_code=TEMPLATE_ACM_BOND_CODE,
            source_code=None,
            acm_thickness_mm=None,
            unit_cost=None,
            currency=None,
            resolution_status=RESOLUTION_SKIPPED_NON_ACM_TEMPLATE,
        )

    if not quote_input:
        return AcmBondMaterialRateResolution(
            resolved_code=TEMPLATE_ACM_BOND_CODE,
            source_code=None,
            acm_thickness_mm=None,
            unit_cost=None,
            currency=None,
            resolution_status=RESOLUTION_MISSING_QUOTE_INPUT,
        )

    thickness_mm, failure = _coerce_acm_thickness_mm(quote_input)
    if failure is not None:
        return AcmBondMaterialRateResolution(
            resolved_code=TEMPLATE_ACM_BOND_CODE,
            source_code=None,
            acm_thickness_mm=None,
            unit_cost=None,
            currency=None,
            resolution_status=failure,
        )

    variant_code = ACM_THICKNESS_MM_TO_VARIANT_CODE[thickness_mm]
    variant_rate = material_rates.get(variant_code)
    currency = None
    if material_currencies:
        currency = material_currencies.get(variant_code) or material_currencies.get(
            TEMPLATE_ACM_BOND_CODE
        )

    if variant_rate is None or float(variant_rate) <= 0:
        return AcmBondMaterialRateResolution(
            resolved_code=TEMPLATE_ACM_BOND_CODE,
            source_code=variant_code,
            acm_thickness_mm=thickness_mm,
            unit_cost=None,
            currency=str(currency).strip() if currency else None,
            resolution_status=RESOLUTION_VARIANT_RATE_MISSING,
        )

    return AcmBondMaterialRateResolution(
        resolved_code=TEMPLATE_ACM_BOND_CODE,
        source_code=variant_code,
        acm_thickness_mm=thickness_mm,
        unit_cost=float(variant_rate),
        currency=str(currency).strip() if currency else None,
        resolution_status=RESOLUTION_RESOLVED,
    )


def resolve_acm_bond_material_rates(
    material_rates: Mapping[str, float],
    quote_input: Optional[Mapping[str, Any]],
    *,
    template_code: Optional[str] = None,
    material_currencies: Optional[Mapping[str, str]] = None,
) -> Dict[str, float]:
    resolution = resolve_acm_bond_panel_material_rate(
        material_rates,
        quote_input,
        template_code=template_code,
        material_currencies=material_currencies,
    )
    out: Dict[str, float] = dict(material_rates)
    if resolution.resolution_status == RESOLUTION_RESOLVED and resolution.unit_cost is not None:
        out[TEMPLATE_ACM_BOND_CODE] = resolution.unit_cost
    return out
