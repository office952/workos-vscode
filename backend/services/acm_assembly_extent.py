"""Shared AcmPanel assembly extent contract (mm).

Explicit keys: assembly_width_mm / assembly_height_mm — never overload panel_*.
Mirror: frontend/src/lib/intakeV6/acmPanel/assemblyExtent.ts
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional, Sequence

ASSEMBLY_DIMENSION_TOLERANCE_MM = 1.0


def _num(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        n = float(value)
        return n if n == n and abs(n) != float("inf") else None
    if isinstance(value, str) and value.strip():
        try:
            n = float(value)
        except ValueError:
            return None
        return n if n == n and abs(n) != float("inf") else None
    return None


def _format_mm(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(round(value, 1))


def _panel_xy(panel: Mapping[str, Any]) -> tuple[float, float]:
    pos = panel.get("position") if isinstance(panel.get("position"), Mapping) else {}
    x = _num(pos.get("x_mm")) if pos else None
    y = _num(pos.get("y_mm")) if pos else None
    if x is None:
        x = _num(panel.get("x_mm")) or 0.0
    if y is None:
        y = _num(panel.get("y_mm")) or 0.0
    return float(x), float(y)


def _panel_has_explicit_position(panel: Mapping[str, Any]) -> bool:
    pos = panel.get("position") if isinstance(panel.get("position"), Mapping) else {}
    if pos and (_num(pos.get("x_mm")) is not None or _num(pos.get("y_mm")) is not None):
        return True
    return _num(panel.get("x_mm")) is not None or _num(panel.get("y_mm")) is not None


def compute_acm_assembly_extent(
    *,
    panels: Sequence[Mapping[str, Any]] | None = None,
    assembly_dimensions: Mapping[str, Any] | None = None,
    envelope_width_mm: Any = None,
    envelope_height_mm: Any = None,
) -> dict[str, Any]:
    """Return assembly_width_mm / assembly_height_mm + source + warnings."""
    warnings: list[str] = []
    valid: list[tuple[float, float, float, float]] = []
    positioned_count = 0

    for raw in panels or []:
        if not isinstance(raw, Mapping):
            continue
        w = _num(raw.get("width_mm"))
        h = _num(raw.get("height_mm"))
        if w is None or h is None or w <= 0 or h <= 0:
            continue
        if _panel_has_explicit_position(raw):
            positioned_count += 1
        x, y = _panel_xy(raw)
        valid.append((x, y, w, h))

    asm = assembly_dimensions if isinstance(assembly_dimensions, Mapping) else {}
    asm_w = _num(asm.get("width_mm"))
    asm_h = _num(asm.get("height_mm"))

    if not valid:
        if asm_w is not None and asm_h is not None and asm_w > 0 and asm_h > 0:
            return {
                "assembly_width_mm": asm_w,
                "assembly_height_mm": asm_h,
                "source": "assembly_dimensions",
                "warnings": warnings,
                "envelope_ignored_for_multi_panel": False,
            }
        return {
            "assembly_width_mm": None,
            "assembly_height_mm": None,
            "source": "none",
            "warnings": warnings,
            "envelope_ignored_for_multi_panel": False,
        }

    min_x = min(p[0] for p in valid)
    max_x = max(p[0] + p[2] for p in valid)
    min_y = min(p[1] for p in valid)
    max_y = max(p[1] + p[3] for p in valid)
    extent_w = max_x - min_x
    extent_h = max_y - min_y
    if extent_w <= 0 or extent_h <= 0:
        return {
            "assembly_width_mm": None,
            "assembly_height_mm": None,
            "source": "none",
            "warnings": ["Geometrie panouri insuficientă pentru assembly extent."],
            "envelope_ignored_for_multi_panel": False,
        }

    assembly_width = extent_w
    assembly_height = extent_h
    source = "panel_extent" if len(valid) > 1 else "single_panel"

    # Multi-panel without positions collapses to a stack at origin — trust assembly_dimensions.
    positions_unreliable = len(valid) > 1 and positioned_count < 2
    if (
        positions_unreliable
        and asm_w is not None
        and asm_h is not None
        and asm_w > 0
        and asm_h > 0
    ):
        warnings.append(
            "Poziții panouri lipsă/incomplete — folosesc assembly_dimensions pentru ansamblu."
        )
        assembly_width = asm_w
        assembly_height = asm_h
        source = "assembly_dimensions"
    elif len(valid) > 1:
        if asm_w is not None and asm_h is not None and asm_w > 0 and asm_h > 0:
            if (
                abs(asm_w - extent_w) <= ASSEMBLY_DIMENSION_TOLERANCE_MM
                and abs(asm_h - extent_h) <= ASSEMBLY_DIMENSION_TOLERANCE_MM
            ):
                assembly_width = asm_w
                assembly_height = asm_h
                source = "assembly_dimensions"
            else:
                warnings.append(
                    f"assembly_dimensions ({_format_mm(asm_w)}×{_format_mm(asm_h)}) "
                    f"diferă de extent panouri ({_format_mm(extent_w)}×{_format_mm(extent_h)}) "
                    "— folosesc extent panouri."
                )
                source = "panel_extent"
    else:
        only_w, only_h = valid[0][2], valid[0][3]
        if asm_w is not None and asm_h is not None and asm_w > 0 and asm_h > 0:
            if (
                abs(asm_w - only_w) <= ASSEMBLY_DIMENSION_TOLERANCE_MM
                and abs(asm_h - only_h) <= ASSEMBLY_DIMENSION_TOLERANCE_MM
            ):
                assembly_width = asm_w
                assembly_height = asm_h
                source = "assembly_dimensions"
            else:
                assembly_width = only_w
                assembly_height = only_h
                source = "single_panel"
        else:
            assembly_width = only_w
            assembly_height = only_h
            source = "single_panel"

    envelope_ignored = False
    envelope_w = _num(envelope_width_mm)
    envelope_h = _num(envelope_height_mm)
    if (
        len(valid) > 1
        and envelope_w is not None
        and abs(envelope_w - assembly_width) > ASSEMBLY_DIMENSION_TOLERANCE_MM
    ):
        envelope_ignored = True
        warnings.append(
            f"Envelope contour ({_format_mm(envelope_w)}×{_format_mm(envelope_h or 0)}) "
            "nu este overall assembly — ignorat pentru ansamblu."
        )

    return {
        "assembly_width_mm": assembly_width,
        "assembly_height_mm": assembly_height,
        "source": source,
        "warnings": warnings,
        "envelope_ignored_for_multi_panel": envelope_ignored,
    }


def read_panels_for_assembly_extent(
    finish: Mapping[str, Any] | None,
    acm_instance: Mapping[str, Any] | None = None,
) -> tuple[list[Mapping[str, Any]], Optional[Mapping[str, Any]], Optional[float], Optional[float]]:
    """Collect panels + assembly_dimensions + envelope from finish / instance."""
    finish_d = finish if isinstance(finish, Mapping) else {}
    inst = acm_instance if isinstance(acm_instance, Mapping) else None
    if inst is None:
        inst = finish_d.get("acm_panel_instance") if isinstance(finish_d.get("acm_panel_instance"), Mapping) else None

    panels: list[Mapping[str, Any]] = []
    geom = inst.get("geometry") if isinstance(inst, Mapping) else None
    if isinstance(geom, Mapping) and isinstance(geom.get("panels"), list) and geom["panels"]:
        panels = [p for p in geom["panels"] if isinstance(p, Mapping)]

    segmented = finish_d.get("segmented_background")
    if not panels and isinstance(segmented, Mapping) and isinstance(segmented.get("panels"), list):
        panels = [p for p in segmented["panels"] if isinstance(p, Mapping)]

    assembly_dimensions = None
    if isinstance(segmented, Mapping) and isinstance(segmented.get("assembly_dimensions"), Mapping):
        assembly_dimensions = segmented.get("assembly_dimensions")

    envelope_w = None
    envelope_h = None
    if isinstance(geom, Mapping):
        envelope_w = _num(geom.get("width_mm"))
        envelope_h = _num(geom.get("height_mm"))

    return panels, assembly_dimensions, envelope_w, envelope_h


def inject_assembly_extent_keys(
    values: MutableMapping[str, Any],
    *,
    finish: Mapping[str, Any] | None = None,
    acm_instance: Mapping[str, Any] | None = None,
) -> list[str]:
    """Write assembly_width_mm / assembly_height_mm into values. Returns warnings."""
    panels, assembly_dimensions, envelope_w, envelope_h = read_panels_for_assembly_extent(
        finish, acm_instance or values.get("acm_panel_instance")
    )
    # Prefer proposal assembly_dimensions when confirmed segmented absent
    if assembly_dimensions is None and isinstance(finish, Mapping):
        prop = finish.get("segmented_background")
        # already handled; also check values proposal after projection
    if assembly_dimensions is None:
        prop = values.get("segmented_background_proposal")
        if isinstance(prop, Mapping) and isinstance(prop.get("assembly_dimensions"), Mapping):
            assembly_dimensions = prop.get("assembly_dimensions")
        if not panels and isinstance(prop, Mapping) and isinstance(prop.get("panels"), list):
            panels = [p for p in prop["panels"] if isinstance(p, Mapping)]

    result = compute_acm_assembly_extent(
        panels=panels,
        assembly_dimensions=assembly_dimensions,
        envelope_width_mm=envelope_w,
        envelope_height_mm=envelope_h,
    )
    if result["assembly_width_mm"] is not None:
        values["assembly_width_mm"] = result["assembly_width_mm"]
    if result["assembly_height_mm"] is not None:
        values["assembly_height_mm"] = result["assembly_height_mm"]
    values["assembly_extent_source"] = result["source"]
    if result["envelope_ignored_for_multi_panel"]:
        values["assembly_extent_envelope_ignored"] = True
    return list(result["warnings"] or [])

