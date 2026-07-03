"""Intake V4 owner Oracal face vinyl pricing — series-specific, excluding TVA."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from services.shared_vinyl_material_catalog import (
    ORACAL_641_OWNER_EUR_PER_M2,
    ORACAL_651_OWNER_EUR_PER_M2,
    ORACAL_8500_OWNER_EUR_PER_M2,
    OWNER_ORACAL_PRICE_SOURCE_PREFIX,
    resolve_oracal_profile_from_face_finish,
    resolve_oracal_series_from_face_finish,
    resolve_owner_oracal_price_eur_per_sqm,
)

# Backward-compatible aliases — values sourced from shared_vinyl_material_catalog.
INTAKE_V4_ORACAL_641_EUR_PER_M2 = ORACAL_641_OWNER_EUR_PER_M2
INTAKE_V4_ORACAL_651_EUR_PER_M2 = ORACAL_651_OWNER_EUR_PER_M2
INTAKE_V4_ORACAL_8500_EUR_PER_M2 = ORACAL_8500_OWNER_EUR_PER_M2

_OWNER_ORACAL_FACE_SERIES = frozenset({"641", "651", "8500"})


def resolve_intake_v4_oracal_face_series(face_finish: str | None) -> str | None:
    return resolve_oracal_series_from_face_finish(face_finish)


def resolve_intake_v4_owner_oracal_face_price(
    series: str,
) -> tuple[float, str, str] | None:
    return resolve_owner_oracal_price_eur_per_sqm(series)


def is_intake_v4_owner_oracal_price_source(price_source: str | None) -> bool:
    if not price_source:
        return False
    return any(
        part.startswith(OWNER_ORACAL_PRICE_SOURCE_PREFIX)
        for part in price_source.split("|")
    )


def _positive(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def face_oracal_vinyl_areas_by_series(
    letter_groups: list[Any],
    default_face_finish: str,
    total_area: float | None,
    *,
    roll_area_by_layer: dict[str, float] | None = None,
) -> dict[str, float]:
    """Split quote vinyl area into owner-priced Oracal 641 / 651 / 8500 buckets (excl. TVA)."""
    per_series: dict[str, float] = defaultdict(float)

    if letter_groups:
        for group in letter_groups:
            if not isinstance(group, dict):
                continue
            face_finish = str(group.get("face_finish_type") or default_face_finish)
            series = resolve_intake_v4_oracal_face_series(face_finish)
            if series not in _OWNER_ORACAL_FACE_SERIES:
                continue
            layer_name = str(group.get("layer_name") or group.get("group_key") or "")
            group_key = str(group.get("group_key") or "")
            area = None
            if roll_area_by_layer is not None:
                if layer_name:
                    area = _positive(roll_area_by_layer.get(layer_name))
                if area is None and group_key:
                    area = _positive(roll_area_by_layer.get(group_key))
            if area is None:
                area = _positive(group.get("face_area_m2"))
            if area:
                per_series[series] += area
    else:
        series = resolve_intake_v4_oracal_face_series(default_face_finish)
        if series in _OWNER_ORACAL_FACE_SERIES and total_area:
            per_series[series] = float(total_area)

    if per_series:
        if roll_area_by_layer is not None:
            return {series: round(area, 4) for series, area in per_series.items() if area > 0}
        group_total = sum(per_series.values())
        if total_area and group_total > 0:
            scale = float(total_area) / group_total
            return {series: round(area * scale, 4) for series, area in per_series.items() if area > 0}
        return {series: round(area, 4) for series, area in per_series.items() if area > 0}

    if total_area:
        series = resolve_intake_v4_oracal_face_series(default_face_finish)
        if series in _OWNER_ORACAL_FACE_SERIES:
            return {series: round(float(total_area), 4)}
    return {}


def letter_groups_use_oracal_8500_vinyl(
    letter_groups: list[Any],
    default_face_finish: str,
) -> bool:
    if letter_groups:
        for group in letter_groups:
            if not isinstance(group, dict):
                continue
            face_finish = str(group.get("face_finish_type") or default_face_finish)
            if resolve_intake_v4_oracal_face_series(face_finish) == "8500":
                return True
        return False
    return resolve_intake_v4_oracal_face_series(default_face_finish) == "8500"


def resolve_intake_v4_oracal_profile_for_face_finish(face_finish: str | None):
    """Adapter to shared catalog — for tests and future Intake V4 UI migration."""
    return resolve_oracal_profile_from_face_finish(face_finish)
