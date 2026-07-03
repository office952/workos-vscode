"""CNC router pass policy for TPL-VOLUMETRIC-LETTERS — read-only estimates, no CostEngine edits.

Owner rules (documented in docs/architecture/TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md):
- CNC_ROUTER rate: 1.5 EUR/ml/pass (excl. TVA) via workcenter registry
- Face plexiglas 3 mm: 1 cut + 1 bevel = 2 passes when face bevel active (template default)
- Forex 10 mm back: ceil(depth / 3.5 mm) cut passes; optional bevel 7 mm adds ceil(7/3.5)=2 passes
"""

from __future__ import annotations

import math
from typing import Any, Mapping

DEFAULT_CNC_RATE_EUR_PER_ML_PASS = 1.5
DEFAULT_MAX_DEPTH_PER_PASS_MM = 3.5
DEFAULT_FACE_PLEXI_THICKNESS_MM = 3.0
DEFAULT_FOREX_BACKING_THICKNESS_MM = 10.0
DEFAULT_FOREX_BEVEL_DEPTH_MM = 7.0

CNC_PERIMETER_QUOTE_INPUT_KEY = "cnc_cutting_perimeter_ml"


def passes_for_depth_mm(*, depth_mm: float, max_depth_per_pass_mm: float = DEFAULT_MAX_DEPTH_PER_PASS_MM) -> int:
    """Owner rule: ceil(depth / max_depth_per_pass), minimum 1 when depth > 0."""
    if depth_mm <= 0:
        return 0
    step = max_depth_per_pass_mm if max_depth_per_pass_mm > 0 else DEFAULT_MAX_DEPTH_PER_PASS_MM
    return max(1, math.ceil(depth_mm / step))


def face_plexi_cnc_passes(*, face_bevel_enabled: bool = True) -> dict[str, int]:
    """Face plexi: 1 cut pass; +1 bevel pass when bevel active (template face_cnc_cut default)."""
    cut = 1
    bevel = 1 if face_bevel_enabled else 0
    return {"cut_passes": cut, "bevel_passes": bevel, "total_passes": cut + bevel}


def forex_backing_cnc_passes(
    *,
    cut_depth_mm: float = DEFAULT_FOREX_BACKING_THICKNESS_MM,
    back_bevel_enabled: bool = False,
    bevel_depth_mm: float = DEFAULT_FOREX_BEVEL_DEPTH_MM,
    max_depth_per_pass_mm: float = DEFAULT_MAX_DEPTH_PER_PASS_MM,
) -> dict[str, int]:
    """Forex backing: cut passes from full thickness; bevel passes when operator enables back bevel."""
    cut = passes_for_depth_mm(depth_mm=cut_depth_mm, max_depth_per_pass_mm=max_depth_per_pass_mm)
    bevel = (
        passes_for_depth_mm(depth_mm=bevel_depth_mm, max_depth_per_pass_mm=max_depth_per_pass_mm)
        if back_bevel_enabled
        else 0
    )
    return {"cut_passes": cut, "bevel_passes": bevel, "total_passes": cut + bevel}


def resolve_cnc_cutting_perimeter_ml(geometry: Mapping[str, Any]) -> float | None:
    """Canonical CNC debit perimeter: outer face letters + inner holes (not LED-only outer)."""
    for key in (
        CNC_PERIMETER_QUOTE_INPUT_KEY,
        "cnc_cutting_perimeter_ml",
        "face_cutting_perimeter_ml",
        "cutting_perimeter_ml",
        "letter_perimeter_m",
    ):
        raw = geometry.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return round(value, 6)
    return None


def estimate_cnc_router_cost_eur(
    *,
    perimeter_ml: float,
    total_passes: int,
    rate_eur_per_ml_pass: float = DEFAULT_CNC_RATE_EUR_PER_ML_PASS,
) -> float | None:
    if perimeter_ml <= 0 or total_passes <= 0:
        return None
    return round(perimeter_ml * total_passes * rate_eur_per_ml_pass, 4)


def build_cnc_operation_estimate_preview(
    geometry: Mapping[str, Any],
    *,
    face_bevel_enabled: bool = True,
    back_bevel_enabled: bool = False,
    backing_active: bool = False,
    rate_eur_per_ml_pass: float = DEFAULT_CNC_RATE_EUR_PER_ML_PASS,
) -> dict[str, Any]:
    """Read-only CNC pass/cost preview for Intake V4 audits — not CostEngine output."""
    perimeter_ml = resolve_cnc_cutting_perimeter_ml(geometry)
    face = face_plexi_cnc_passes(face_bevel_enabled=face_bevel_enabled)
    face_cost = (
        estimate_cnc_router_cost_eur(
            perimeter_ml=perimeter_ml,
            total_passes=face["total_passes"],
            rate_eur_per_ml_pass=rate_eur_per_ml_pass,
        )
        if perimeter_ml is not None
        else None
    )

    backing: dict[str, Any] | None = None
    if backing_active:
        forex = forex_backing_cnc_passes(back_bevel_enabled=back_bevel_enabled)
        backing = {
            **forex,
            "material": "Forex 10mm",
            "bevel_depth_mm": DEFAULT_FOREX_BEVEL_DEPTH_MM if back_bevel_enabled else None,
            "estimated_cost_eur": estimate_cnc_router_cost_eur(
                perimeter_ml=perimeter_ml,
                total_passes=forex["total_passes"],
                rate_eur_per_ml_pass=rate_eur_per_ml_pass,
            )
            if perimeter_ml is not None
            else None,
        }

    return {
        "cnc_perimeter_ml": perimeter_ml,
        "cnc_perimeter_quote_input_key": CNC_PERIMETER_QUOTE_INPUT_KEY,
        "rate_eur_per_ml_pass": rate_eur_per_ml_pass,
        "face_plexi": {
            **face,
            "face_bevel_enabled": face_bevel_enabled,
            "estimated_cost_eur": face_cost,
        },
        "forex_backing": backing,
        "led_perimeter_ml": geometry.get("led_perimeter_ml"),
        "return_material_perimeter_ml": geometry.get("return_material_perimeter_ml"),
    }
