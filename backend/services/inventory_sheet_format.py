from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VALID_FORMAT_TYPES = {"none", "sheet", "roll", "linear", "piece", "unknown"}
VALID_UNITS = {"mm", "cm", "m", "unknown"}
VALID_FORMAT_SOURCES = {"manual", "supplier", "imported", "unknown"}


@dataclass
class FitCheckResult:
    fit_status: str
    fit_reason: str
    warnings: list[str] = field(default_factory=list)


def _as_positive_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def validate_sheet_format_payload(values: dict[str, Any]) -> None:
    """Validate sheet format domain constraints for inventory materials.

    Raises ValueError on invalid combinations. Missing fields remain allowed
    for backward compatibility and non-sheet materials.
    """

    format_type = str(values.get("sheet_format_type") or "unknown").strip().lower()
    if format_type not in VALID_FORMAT_TYPES:
        raise ValueError(f"Invalid sheet_format_type '{format_type}'. Allowed: {sorted(VALID_FORMAT_TYPES)}")

    sheet_unit = str(values.get("sheet_unit") or "unknown").strip().lower()
    if sheet_unit not in VALID_UNITS:
        raise ValueError(f"Invalid sheet_unit '{sheet_unit}'. Allowed: {sorted(VALID_UNITS)}")

    thickness_unit = str(values.get("sheet_thickness_unit") or "unknown").strip().lower()
    if thickness_unit not in VALID_UNITS:
        raise ValueError(
            f"Invalid sheet_thickness_unit '{thickness_unit}'. Allowed: {sorted(VALID_UNITS)}"
        )

    format_source = str(values.get("format_source") or "unknown").strip().lower()
    if format_source not in VALID_FORMAT_SOURCES:
        raise ValueError(f"Invalid format_source '{format_source}'. Allowed: {sorted(VALID_FORMAT_SOURCES)}")

    sheet_width = _as_positive_number(values.get("sheet_width"))
    sheet_height = _as_positive_number(values.get("sheet_height"))
    usable_width = _as_positive_number(values.get("usable_width"))
    usable_height = _as_positive_number(values.get("usable_height"))
    sheet_thickness = _as_positive_number(values.get("sheet_thickness"))

    for key, num in [
        ("sheet_width", sheet_width),
        ("sheet_height", sheet_height),
        ("usable_width", usable_width),
        ("usable_height", usable_height),
        ("sheet_thickness", sheet_thickness),
    ]:
        raw = values.get(key)
        if raw is None:
            continue
        if num is None:
            raise ValueError(f"{key} must be a numeric value when provided")
        if num <= 0:
            raise ValueError(f"{key} must be > 0 when provided")

    if format_type == "sheet":
        if usable_width is not None and sheet_width is not None and usable_width > sheet_width:
            raise ValueError("usable_width must be <= sheet_width")
        if usable_height is not None and sheet_height is not None and usable_height > sheet_height:
            raise ValueError("usable_height must be <= sheet_height")


def compute_sheet_fit_status(
    *,
    piece_width: float | None,
    piece_height: float | None,
    piece_unit: str | None,
    sheet_width: float | None,
    sheet_height: float | None,
    sheet_unit: str | None,
    usable_width: float | None,
    usable_height: float | None,
    rotation_allowed: bool,
) -> FitCheckResult:
    """Compute a minimal read-only fit check.

    This helper intentionally does NOT perform nesting, stock reservation,
    or any cost/quote logic.
    """

    warnings: list[str] = []

    p_w = _as_positive_number(piece_width)
    p_h = _as_positive_number(piece_height)
    s_w = _as_positive_number(sheet_width)
    s_h = _as_positive_number(sheet_height)

    if p_w is None or p_h is None or p_w <= 0 or p_h <= 0:
        warnings.append("Piece dimensions are missing or invalid.")
        return FitCheckResult(
            fit_status="unknown",
            fit_reason="Cannot compute fit check: piece dimensions are missing or invalid.",
            warnings=warnings,
        )

    if s_w is None or s_h is None or s_w <= 0 or s_h <= 0:
        warnings.append("Sheet dimensions are missing or invalid.")
        return FitCheckResult(
            fit_status="unknown",
            fit_reason="Cannot compute fit check: sheet format dimensions are missing.",
            warnings=warnings,
        )

    p_unit = (piece_unit or "unknown").strip().lower()
    s_unit = (sheet_unit or "unknown").strip().lower()
    if p_unit == "" or p_unit not in VALID_UNITS:
        p_unit = "unknown"
    if s_unit == "" or s_unit not in VALID_UNITS:
        s_unit = "unknown"

    if p_unit == "unknown" or s_unit == "unknown":
        warnings.append("Piece or sheet unit is unknown.")
        return FitCheckResult(
            fit_status="unknown",
            fit_reason="Cannot compute fit check: piece/sheet unit missing.",
            warnings=warnings,
        )

    if p_unit != s_unit:
        warnings.append("Piece and sheet units do not match.")
        return FitCheckResult(
            fit_status="unknown",
            fit_reason="Cannot compute fit check: unit mismatch.",
            warnings=warnings,
        )

    e_w = usable_width if usable_width is not None and usable_width > 0 else s_w
    e_h = usable_height if usable_height is not None and usable_height > 0 else s_h

    if p_w <= e_w and p_h <= e_h:
        return FitCheckResult(
            fit_status="fits",
            fit_reason="Fits on configured sheet format (orientation as entered).",
            warnings=warnings,
        )

    if rotation_allowed and p_h <= e_w and p_w <= e_h:
        return FitCheckResult(
            fit_status="fits_rotated",
            fit_reason="Fits only when rotated.",
            warnings=warnings,
        )

    return FitCheckResult(
        fit_status="does_not_fit",
        fit_reason="Does not fit on configured sheet format.",
        warnings=warnings,
    )
