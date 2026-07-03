"""Owner rules for Intake V4 RAL spray material estimation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from services.intake_v4_volumetric_return_metrics_service import return_finish_active

RAL_PAINT_SPRAY_MATERIAL_CODE = "MAT-VOPSEA-RAL"
# Legacy fallback prices — prefer DB via resolve_ral_paint_price()
RAL_PAINT_SPRAY_OWNER_RON_PER_TUBE = 50.0
RAL_PAINT_SPRAY_OWNER_EUR_PER_TUBE = 10.0
RAL_PAINT_SPRAY_COVERAGE_M_PER_TUBE = 15.0
PRICE_SOURCE_OWNER_RAL_PAINT_SPRAY = "intake_v4_owner_ral_paint_spray_50ron_15m"


def resolve_ral_paint_price(prices: dict[str, float] | None) -> float:
    """Resolve RAL paint price from DB, fallback to legacy constant."""
    if prices and RAL_PAINT_SPRAY_MATERIAL_CODE in prices:
        return prices[RAL_PAINT_SPRAY_MATERIAL_CODE]
    return RAL_PAINT_SPRAY_OWNER_EUR_PER_TUBE
VOLUME_FINISH_PAINT_RAL = "paint_after_face_miter_bond"

RAL_RETURN_FINISH_TYPES = frozenset({"ral_paint", "painted", "paint", VOLUME_FINISH_PAINT_RAL})


@dataclass(frozen=True)
class IntakeV4RalPaintEstimate:
    painted_return_m: float
    letter_painted_return_m: float
    artwork_painted_return_m: float
    raw_tubes: float
    charged_tubes: int
    material_cost_eur: float
    paint_ral_code: str | None = None
    paint_ral_name: str | None = None
    all_letter_returns_painted: bool = False


def _token(raw: Any) -> str:
    return str(raw or "").strip().lower()


def _text(raw: Any) -> str | None:
    value = str(raw or "").strip()
    return value or None


def _positive(raw: Any) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def return_finish_requires_ral_paint(raw: Any) -> bool:
    return _token(raw) in RAL_RETURN_FINISH_TYPES


def _dict_rows(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    return [row for row in raw if isinstance(row, dict)]


def _layer_perimeter_m(
    analysis: dict[str, Any],
    *,
    layer_key: str,
    layer_name: str,
) -> float | None:
    layers = analysis.get("layers")
    if not isinstance(layers, list):
        return None
    lookup = {value for value in (layer_key, layer_name) if value}
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id = str(layer.get("id") or "")
        name = str(layer.get("name") or layer_id)
        if not lookup.intersection({layer_id, name}):
            continue
        perimeter_m = _positive(layer.get("perimeterMl")) or _positive(layer.get("perimeter_ml"))
        if perimeter_m is not None:
            return perimeter_m
        perimeter_mm = _positive(layer.get("perimeterMm")) or _positive(layer.get("perimeter_mm"))
        if perimeter_mm is not None:
            return perimeter_mm / 1000.0
    return None


def _row_perimeter_m(row: dict[str, Any], analysis: dict[str, Any]) -> float | None:
    for key in ("perimeter_m", "return_perimeter_m", "return_perimeter_ml", "perimeterMl", "perimeter_ml"):
        value = _positive(row.get(key))
        if value is not None:
            return value
    layer_key = str(row.get("group_key") or row.get("layer_key") or "")
    layer_name = str(row.get("layer_name") or layer_key)
    if layer_key or layer_name:
        return _layer_perimeter_m(analysis, layer_key=layer_key, layer_name=layer_name)
    return None


def _geometry_first_positive(geometry: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _positive(geometry.get(key))
        if value is not None:
            return value
    return None


def _paint_color_from_rows(
    *,
    default_row: dict[str, Any],
    letter_groups: list[dict[str, Any]],
    artwork_finishes: list[dict[str, Any]],
    default_return_finish: str | None,
) -> tuple[str | None, str | None]:
    rows = [*letter_groups, *artwork_finishes]
    for row in rows:
        finish = row.get("return_finish_type") or default_return_finish
        if not return_finish_requires_ral_paint(finish):
            continue
        code = _text(row.get("return_oracal_code"))
        name = _text(row.get("return_oracal_name"))
        if code or name:
            return code, name
    return _text(default_row.get("return_oracal_code")), _text(default_row.get("return_oracal_name"))


def _letter_painted_return_m(
    *,
    letter_groups: list[dict[str, Any]],
    default_return_finish: str | None,
    geometry: dict[str, Any],
    analysis: dict[str, Any],
    artwork_painted_return_m: float,
) -> tuple[float, bool]:
    if letter_groups:
        total = 0.0
        active_count = 0
        painted_count = 0
        for group in letter_groups:
            finish = group.get("return_finish_type") or default_return_finish
            if not return_finish_active(str(finish or "")):
                continue
            active_count += 1
            if not return_finish_requires_ral_paint(finish):
                continue
            painted_count += 1
            total += _row_perimeter_m(group, analysis) or 0.0
        return round(total, 4), bool(active_count and active_count == painted_count)

    if not return_finish_requires_ral_paint(default_return_finish):
        return 0.0, False

    letter_m = _geometry_first_positive(
        geometry,
        "letter_return_perimeter_ml",
        "total_letter_perimeter_ml",
        "letter_perimeter_m",
    )
    if letter_m is None:
        total_m = _geometry_first_positive(geometry, "return_material_perimeter_ml", "return_perimeter_m")
        if total_m is not None and artwork_painted_return_m > 0:
            letter_m = max(total_m - artwork_painted_return_m, 0.0)
        else:
            letter_m = total_m
    return round(letter_m or 0.0, 4), bool(letter_m and letter_m > 0)


def _artwork_painted_return_m(
    *,
    artwork_finishes: list[dict[str, Any]],
    default_return_finish: str | None,
    geometry: dict[str, Any],
    analysis: dict[str, Any],
) -> float:
    painted_rows = [
        row
        for row in artwork_finishes
        if return_finish_requires_ral_paint(row.get("return_finish_type") or default_return_finish)
    ]
    if not painted_rows:
        return 0.0
    total = 0.0
    for row in painted_rows:
        total += _row_perimeter_m(row, analysis) or 0.0
    if total <= 0 and len(painted_rows) == 1:
        total = _geometry_first_positive(geometry, "artwork_return_perimeter_ml") or 0.0
    return round(total, 4)


def estimate_intake_v4_ral_paint_spray(
    *,
    finish_setup: dict[str, Any],
    geometry: dict[str, Any],
    analysis: dict[str, Any] | None = None,
    default_return_finish: str | None = None,
) -> IntakeV4RalPaintEstimate | None:
    """Estimate whole RAL spray tubes from the painted cant perimeter.

    Owner rule: one 50 RON spray tube covers 15 linear meters of cant.
    The quantity charged to the quote is whole tubes: ceil(painted_m / 15).
    """
    setup = finish_setup if isinstance(finish_setup, dict) else {}
    geom = geometry if isinstance(geometry, dict) else {}
    svg_analysis = analysis if isinstance(analysis, dict) else {}
    default_finish = default_return_finish or _text(setup.get("return_finish_type"))
    letter_groups = _dict_rows(setup.get("letter_group_finishes"))
    artwork_finishes = _dict_rows(setup.get("artwork_finishes"))

    artwork_m = _artwork_painted_return_m(
        artwork_finishes=artwork_finishes,
        default_return_finish=default_finish,
        geometry=geom,
        analysis=svg_analysis,
    )
    letter_m, all_letter_returns_painted = _letter_painted_return_m(
        letter_groups=letter_groups,
        default_return_finish=default_finish,
        geometry=geom,
        analysis=svg_analysis,
        artwork_painted_return_m=artwork_m,
    )
    total_m = round(letter_m + artwork_m, 4)
    if total_m <= 0:
        return None

    raw_tubes = total_m / RAL_PAINT_SPRAY_COVERAGE_M_PER_TUBE
    charged_tubes = max(1, int(math.ceil(raw_tubes)))
    code, name = _paint_color_from_rows(
        default_row=setup,
        letter_groups=letter_groups,
        artwork_finishes=artwork_finishes,
        default_return_finish=default_finish,
    )
    return IntakeV4RalPaintEstimate(
        painted_return_m=total_m,
        letter_painted_return_m=letter_m,
        artwork_painted_return_m=artwork_m,
        raw_tubes=round(raw_tubes, 4),
        charged_tubes=charged_tubes,
        material_cost_eur=round(charged_tubes * RAL_PAINT_SPRAY_OWNER_EUR_PER_TUBE, 4),
        paint_ral_code=code,
        paint_ral_name=name,
        all_letter_returns_painted=all_letter_returns_painted,
    )
