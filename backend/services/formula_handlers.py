"""Formula handlers — enum-based, pure-Python cost formula registry.

Sprint #21.1 — CostEngine Additive Extension.

Canonical rules
---------------
- Handlers are pure functions (no I/O, no DB, no state). They receive
  immutable `params` (declared in the template) and immutable
  `quote_input` (provided per quote instance) and return a
  `FormulaResult`.
- There is NO string eval, NO exec, NO code execution of user-provided
  expressions. The only way to introduce a new formula is to add a new
  entry in `FORMULA_REGISTRY` with a typed Python implementation.
- Handlers NEVER raise on missing input. They MUST return
  `FormulaResult(resolved=False, error=...)` with a machine-readable
  error dict. The caller (CostEngine) is responsible for translating
  that into a `NEEDS_QUOTE_INPUT` error on the cost snapshot.
- Handlers NEVER fall back to 0 silently. A missing required input
  ALWAYS produces `resolved=False` — never a numeric zero masquerading
  as a valid cost.

Supported formulas (Sprint #21.1, min 6)
----------------------------------------
- ``cnc_time_from_path``   — minutes of CNC routing from path length,
                              with pass multiplier.
- ``plexi_diffuser_area``  — plexi diffuser m² from bounding area + margin.
- ``relief_material_area`` — relief plexi m² from front-face area × coverage.
- ``led_count_from_area``  — LED count from front-face area × density.
- ``led_psu_sizing``       — PSU count picked from allowed sizes given
                              the total LED load × safety factor.
- ``led_assembly_time``    — assembly minutes from LED count × throughput,
                              clamped to a minimum.

The registry is frozen at module import time. External callers MUST use
`resolve_formula(FormulaId, params, quote_input)` — they SHOULD NOT import
the private handler functions directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import ceil
from typing import Any, Callable, Dict, List, Mapping, Optional

from services.shared_edge_cant_rules import (
    EDGE_CANT_QUOTE_WASTE_PERCENT,
    compute_return_wrap_area_m2,
)
from services.volumetric_face_vinyl_service import RETURN_VINYL_BAND_EXTRA_MM


# ---------------------------------------------------------------------------
# Canonical error / unit strings (do NOT hand-write elsewhere)
# ---------------------------------------------------------------------------
ERR_MISSING_INPUT = "MISSING_INPUT"
ERR_INVALID_INPUT = "INVALID_INPUT"
ERR_INVALID_PARAM = "INVALID_PARAM"

UNIT_MINUTES = "min"
UNIT_AREA_M2 = "m2"
UNIT_COUNT = "count"


# ---------------------------------------------------------------------------
# FormulaId — the ONLY legal way to reference a formula from a template.
# ---------------------------------------------------------------------------
class FormulaId(str, Enum):
    CNC_TIME_FROM_PATH = "cnc_time_from_path"
    PLEXI_DIFFUSER_AREA = "plexi_diffuser_area"
    RELIEF_MATERIAL_AREA = "relief_material_area"
    LED_COUNT_FROM_AREA = "led_count_from_area"
    LED_PSU_SIZING = "led_psu_sizing"
    LED_ASSEMBLY_TIME = "led_assembly_time"
    # TPL-VOLUMETRIC-LETTERS (Product 001)
    LETTER_FACE_AREA = "letter_face_area"
    LETTER_PERIMETER = "letter_perimeter"
    PERIMETER_BASED_TIME = "perimeter_based_time"
    COUNT_BASED_TIME = "count_based_time"
    LED_PER_LETTER = "led_per_letter"
    PSU_COUNT = "psu_count"
    LETTER_COUNT_MATERIAL = "letter_count_material"
    PERIMETER_PASS_LINEAR_METER = "perimeter_pass_linear_meter"
    LED_MODULE_COUNT = "led_module_count"
    CEIL_QUOTE_INPUT_QUANTITY = "ceil_quote_input_quantity"
    # ACM casetted panel / cut letters (SVG layer template pack)
    RECTANGULAR_PANEL_AREA = "rectangular_panel_area"
    RECTANGULAR_PANEL_PERIMETER = "rectangular_panel_perimeter"
    FOLD_LENGTH_FROM_SIDES = "fold_length_from_sides"
    AREA_FROM_QUOTE_INPUT = "area_from_quote_input"
    PERIMETER_FROM_QUOTE_INPUT = "perimeter_from_quote_input"
    MOUNTING_BAR_TOTAL_LENGTH = "mounting_bar_total_length"
    PREMOUNT_BAR_LINEAR_METER = "premount_bar_linear_meter"
    FACE_VINYL_USED_SQM = "face_vinyl_used_sqm"
    SVG_GEOMETRY_READINESS_GATE = "svg_geometry_readiness_gate"
    MOUNTING_TEMPLATE_AREA = "mounting_template_area"
    # Return/cant linear quantity — component-owned perimeter (ml).
    # Demonstrated by volum_aluminiu_quantity_ownership (confirmed/legacy perimeter).
    RETURN_PROFILE_LINEAR_METER = "return_profile_linear_meter"
    # Return/cant Oracal wrap area (m²) — shared_edge_cant geometry.
    RETURN_WRAP_AREA = "return_wrap_area"


@dataclass(frozen=True)
class FormulaResult:
    """Outcome of a formula resolution.

    Attributes
    ----------
    value:
        Computed numeric value. Meaningful only when ``resolved`` is True.
        When ``resolved`` is False, this is ``None`` — NEVER ``0.0`` —
        to eliminate any ambiguity between "zero cost" and "missing".
    unit:
        Logical unit of ``value`` (``"min"``, ``"m2"``, ``"count"``).
        Always populated, even on failure, so callers can render the
        pending input schema.
    resolved:
        ``True`` iff all required inputs were present, valid, and the
        handler produced a numeric value. ``False`` in every other case,
        including invalid params or invalid input values.
    error:
        ``None`` when ``resolved`` is ``True``. Otherwise a dict with
        ``{"kind": str, "detail": str, "missing": list[str]}``. ``missing``
        is always a list (possibly empty for INVALID_* errors).
    breakdown:
        Handler-specific intermediate values (e.g. area used, density
        applied) that the caller can surface for traceability. Always a
        dict; may be empty on pure failure.
    """

    value: Optional[float]
    unit: str
    resolved: bool
    error: Optional[Dict[str, Any]] = None
    breakdown: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Internal helpers — shared by handlers
# ---------------------------------------------------------------------------
def _coerce_positive_float(
    source: Mapping[str, Any],
    key: str,
    missing: List[str],
    invalid: List[str],
    *,
    allow_zero: bool = False,
) -> Optional[float]:
    """Return ``source[key]`` coerced to a strictly positive float.

    Mutates ``missing`` / ``invalid`` with ``key`` on failure and returns
    ``None`` so the caller can continue collecting every missing input
    before returning a single combined error to the user.
    """
    if key not in source or source[key] is None:
        missing.append(key)
        return None
    try:
        val = float(source[key])
    except (TypeError, ValueError):
        invalid.append(key)
        return None
    if val < 0 or (val == 0 and not allow_zero):
        invalid.append(key)
        return None
    return val


def _coerce_positive_int(
    source: Mapping[str, Any],
    key: str,
    missing: List[str],
    invalid: List[str],
) -> Optional[int]:
    """Return ``source[key]`` coerced to a strictly positive int."""
    if key not in source or source[key] is None:
        missing.append(key)
        return None
    try:
        val = int(source[key])
    except (TypeError, ValueError):
        invalid.append(key)
        return None
    if val <= 0:
        invalid.append(key)
        return None
    return val


def _fail(
    unit: str,
    *,
    kind: str,
    detail: str,
    missing: Optional[List[str]] = None,
) -> FormulaResult:
    return FormulaResult(
        value=None,
        unit=unit,
        resolved=False,
        error={
            "kind": kind,
            "detail": detail,
            "missing": list(missing or []),
        },
    )


def _missing_or_invalid_result(
    unit: str,
    missing: List[str],
    invalid: List[str],
) -> Optional[FormulaResult]:
    """If ``missing`` or ``invalid`` are non-empty, return a failure result.
    Otherwise return ``None`` (caller continues with valid inputs).
    """
    if missing and not invalid:
        return _fail(
            unit,
            kind=ERR_MISSING_INPUT,
            detail=f"required quote_input keys missing: {missing}",
            missing=missing,
        )
    if invalid:
        # Invalid values always take precedence: they indicate a broken
        # quote_input, not just a not-yet-provided one.
        return _fail(
            unit,
            kind=ERR_INVALID_INPUT,
            detail=f"quote_input keys invalid: {invalid} (missing={missing})",
            missing=missing,
        )
    return None


# ---------------------------------------------------------------------------
# Handler implementations
# ---------------------------------------------------------------------------
def _handle_cnc_time_from_path(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Minutes of CNC routing.

    Formula:
        minutes = path_length / divisor_mm_per_min * passes

    Params (from template, all optional with safe defaults):
        - divisor_mm_per_min (float, default 2000): mm per minute the
          router traverses at the chosen feed/spindle combo.
        - min_minutes (float, default 0): lower clamp for the result.
        - passes (int > 0, OPTIONAL — Sprint #21.1.5): when present the
          handler treats ``passes`` as a TEMPLATE property (e.g. relief
          10 mm plexi = 4 passes at 3 mm/pass) and does NOT require
          ``passes`` in quote_input. When absent, falls back to the
          Sprint #21.1 contract and reads ``passes`` from quote_input.
        - path_length_key (str, OPTIONAL — Sprint #21.1.5, default
          ``"path_length_mm"``): the key under which the handler looks
          up path length in quote_input. Templates with multiple CNC
          operations in the same quote (plexi cut, ACP routing, relief
          cut) MUST set distinct keys (e.g. ``panel_cut_path_length_mm``,
          ``acp_route_path_length_mm``, ``relief_cut_path_length_mm``)
          so each operation reads its own geometry without collision.

    Quote inputs (Sprint #21.1 baseline):
        - path_length_mm (float > 0) — legacy key, still used when
          ``path_length_key`` is not declared in params.
        - passes (int > 0) — required ONLY if ``passes`` is NOT provided
          via params.

    Compatibility
    -------------
    All Sprint #21.1 tests remain green: templates that omit both
    ``passes`` and ``path_length_key`` in params still resolve from
    ``quote_input["path_length_mm"]`` and ``quote_input["passes"]``.
    No silent fallback to 0 — missing values still produce
    ``MISSING_INPUT`` errors (Sprint #21 rule #4).
    """
    try:
        divisor = float(params.get("divisor_mm_per_min", 2000.0))
        min_minutes = float(params.get("min_minutes", 0.0))
    except (TypeError, ValueError):
        return _fail(
            UNIT_MINUTES,
            kind=ERR_INVALID_PARAM,
            detail="divisor_mm_per_min / min_minutes must be numeric",
        )
    if divisor <= 0:
        return _fail(
            UNIT_MINUTES,
            kind=ERR_INVALID_PARAM,
            detail="divisor_mm_per_min must be > 0",
        )

    # Sprint #21.1.5: resolve effective path-length key (default = legacy).
    path_length_key = params.get("path_length_key", "path_length_mm")
    if not isinstance(path_length_key, str) or not path_length_key:
        return _fail(
            UNIT_MINUTES,
            kind=ERR_INVALID_PARAM,
            detail="path_length_key must be a non-empty string",
        )

    missing: List[str] = []
    invalid: List[str] = []
    path = _coerce_positive_float(quote_input, path_length_key, missing, invalid)

    # Sprint #21.1.5: passes-from-params takes precedence; fallback to
    # quote_input preserves the Sprint #21.1 contract.
    passes: Optional[int]
    passes_source: str
    if "passes" in params and params["passes"] is not None:
        raw_passes = params["passes"]
        try:
            passes_val = int(raw_passes)
        except (TypeError, ValueError):
            return _fail(
                UNIT_MINUTES,
                kind=ERR_INVALID_PARAM,
                detail="passes (template param) must be a positive integer",
            )
        if passes_val <= 0:
            return _fail(
                UNIT_MINUTES,
                kind=ERR_INVALID_PARAM,
                detail="passes (template param) must be > 0",
            )
        passes = passes_val
        passes_source = "params"
    else:
        passes = _coerce_positive_int(quote_input, "passes", missing, invalid)
        passes_source = "quote_input"

    fail = _missing_or_invalid_result(UNIT_MINUTES, missing, invalid)
    if fail is not None:
        return fail
    assert path is not None and passes is not None  # narrowing for type-checkers

    minutes = path / divisor * passes
    minutes = max(minutes, min_minutes)
    return FormulaResult(
        value=round(minutes, 4),
        unit=UNIT_MINUTES,
        resolved=True,
        breakdown={
            "path_length_mm": path,
            "path_length_key": path_length_key,
            "passes": passes,
            "passes_source": passes_source,
            "divisor_mm_per_min": divisor,
            "min_minutes": min_minutes,
        },
    )


def _handle_plexi_diffuser_area(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Plexi diffuser area in m² from bounding area and a margin strip.

    The diffuser is sized from the luminous area of the front face plus
    an edge margin on every side, then converted to m² for pricing.

    Formula:
        side_mm   = sqrt(bounding_area_m2 * 1_000_000)
        outer_mm  = side_mm + 2 * margin_mm
        area_m2   = (outer_mm ** 2) / 1_000_000

    Params:
        - margin_mm (float >= 0, default 75)

    Quote inputs:
        - personalization_bounding_area_m2 (float > 0)

    NOTE: Using a square approximation keeps the contract simple at the
    template level — the real bounding box is authoritative inside the
    shop-floor DXF step, not in cost preview. See
    spec__costengine_formula_extension.md §3.2.
    """
    try:
        margin_mm = float(params.get("margin_mm", 75.0))
    except (TypeError, ValueError):
        return _fail(
            UNIT_AREA_M2,
            kind=ERR_INVALID_PARAM,
            detail="margin_mm must be numeric",
        )
    if margin_mm < 0:
        return _fail(
            UNIT_AREA_M2,
            kind=ERR_INVALID_PARAM,
            detail="margin_mm must be >= 0",
        )

    missing: List[str] = []
    invalid: List[str] = []
    bbox = _coerce_positive_float(
        quote_input, "personalization_bounding_area_m2", missing, invalid
    )

    fail = _missing_or_invalid_result(UNIT_AREA_M2, missing, invalid)
    if fail is not None:
        return fail
    assert bbox is not None

    side_mm = (bbox * 1_000_000.0) ** 0.5
    outer_mm = side_mm + 2.0 * margin_mm
    area_m2 = (outer_mm * outer_mm) / 1_000_000.0
    return FormulaResult(
        value=round(area_m2, 4),
        unit=UNIT_AREA_M2,
        resolved=True,
        breakdown={
            "bounding_area_m2": bbox,
            "margin_mm": margin_mm,
            "side_mm": round(side_mm, 3),
            "outer_mm": round(outer_mm, 3),
        },
    )


def _handle_relief_material_area(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Relief plexi area in m² = front_face_area × coverage_pct.

    Params:
        - coverage_pct (float in (0, 1], default 0.30): fraction of the
          face occupied by relief pieces. Supports explicit override per
          template (e.g. dense floral reliefs push this higher).

    Quote inputs:
        - front_face_area_m2 (float > 0)
    """
    try:
        coverage = float(params.get("coverage_pct", 0.30))
    except (TypeError, ValueError):
        return _fail(
            UNIT_AREA_M2,
            kind=ERR_INVALID_PARAM,
            detail="coverage_pct must be numeric",
        )
    if not (0 < coverage <= 1):
        return _fail(
            UNIT_AREA_M2,
            kind=ERR_INVALID_PARAM,
            detail="coverage_pct must be in (0, 1]",
        )

    missing: List[str] = []
    invalid: List[str] = []
    face = _coerce_positive_float(quote_input, "front_face_area_m2", missing, invalid)

    fail = _missing_or_invalid_result(UNIT_AREA_M2, missing, invalid)
    if fail is not None:
        return fail
    assert face is not None

    area = face * coverage
    return FormulaResult(
        value=round(area, 4),
        unit=UNIT_AREA_M2,
        resolved=True,
        breakdown={
            "front_face_area_m2": face,
            "coverage_pct": coverage,
        },
    )


def _handle_led_count_from_area(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """LED count = ceil(front_face_area_m2 × leds_per_m2).

    Params:
        - leds_per_m2 (float > 0, default 55)

    Quote inputs:
        - front_face_area_m2 (float > 0)
    """
    try:
        density = float(params.get("leds_per_m2", 55.0))
    except (TypeError, ValueError):
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="leds_per_m2 must be numeric",
        )
    if density <= 0:
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="leds_per_m2 must be > 0",
        )

    missing: List[str] = []
    invalid: List[str] = []
    face = _coerce_positive_float(quote_input, "front_face_area_m2", missing, invalid)

    fail = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
    if fail is not None:
        return fail
    assert face is not None

    count = int(ceil(face * density))
    return FormulaResult(
        value=float(count),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown={
            "front_face_area_m2": face,
            "leds_per_m2": density,
        },
    )


def _handle_led_psu_sizing(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Number of PSUs needed given LED count and PSU size options.

    Formula:
        total_watts       = led_count * watts_per_led * safety_factor
        picked_psu_watts  = smallest option in psu_options_w >= total_watts,
                            else largest option (and count follows).
        psu_count         = ceil(total_watts / picked_psu_watts)

    Params:
        - watts_per_led   (float > 0, default 1.44)
        - safety_factor   (float >= 1, default 1.2)
        - psu_options_w   (list[float], default [60, 100, 200]). Must be
          strictly positive; sorted ascending internally.

    Quote inputs:
        - led_count (int > 0)
    """
    try:
        watts_per_led = float(params.get("watts_per_led", 1.44))
        safety = float(params.get("safety_factor", 1.2))
    except (TypeError, ValueError):
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="watts_per_led / safety_factor must be numeric",
        )
    if watts_per_led <= 0:
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="watts_per_led must be > 0",
        )
    if safety < 1:
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="safety_factor must be >= 1",
        )

    raw_options = params.get("psu_options_w", [60.0, 100.0, 200.0])
    try:
        options = sorted(float(x) for x in raw_options)
    except (TypeError, ValueError):
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="psu_options_w must be a list of numbers",
        )
    if not options or any(o <= 0 for o in options):
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="psu_options_w must be non-empty and strictly positive",
        )

    missing: List[str] = []
    invalid: List[str] = []
    led_count = _coerce_positive_int(quote_input, "led_count", missing, invalid)

    fail = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
    if fail is not None:
        return fail
    assert led_count is not None

    total_watts = led_count * watts_per_led * safety
    picked = next((o for o in options if o >= total_watts), options[-1])
    psu_count = int(ceil(total_watts / picked))
    return FormulaResult(
        value=float(psu_count),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown={
            "led_count": led_count,
            "watts_per_led": watts_per_led,
            "safety_factor": safety,
            "total_watts": round(total_watts, 3),
            "psu_watts_picked": picked,
            "psu_options_w": options,
        },
    )


def _handle_led_assembly_time(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Assembly time in minutes from LED count.

    Formula:
        minutes = max(led_count / leds_per_minute, min_minutes)

    Params:
        - leds_per_minute (float > 0, default 13)
        - min_minutes     (float >= 0, default 5)

    Quote inputs:
        - led_count (int > 0)
    """
    try:
        throughput = float(params.get("leds_per_minute", 13.0))
        min_minutes = float(params.get("min_minutes", 5.0))
    except (TypeError, ValueError):
        return _fail(
            UNIT_MINUTES,
            kind=ERR_INVALID_PARAM,
            detail="leds_per_minute / min_minutes must be numeric",
        )
    if throughput <= 0:
        return _fail(
            UNIT_MINUTES,
            kind=ERR_INVALID_PARAM,
            detail="leds_per_minute must be > 0",
        )
    if min_minutes < 0:
        return _fail(
            UNIT_MINUTES,
            kind=ERR_INVALID_PARAM,
            detail="min_minutes must be >= 0",
        )

    missing: List[str] = []
    invalid: List[str] = []
    led_count = _coerce_positive_int(quote_input, "led_count", missing, invalid)

    fail = _missing_or_invalid_result(UNIT_MINUTES, missing, invalid)
    if fail is not None:
        return fail
    assert led_count is not None

    minutes = max(led_count / throughput, min_minutes)
    return FormulaResult(
        value=round(minutes, 4),
        unit=UNIT_MINUTES,
        resolved=True,
        breakdown={
            "led_count": led_count,
            "leds_per_minute": throughput,
            "min_minutes": min_minutes,
        },
    )


def _handle_face_vinyl_used_sqm(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Mp folie folosită — nesting (recommended_roll × width) or face_area × 1.10 fallback."""
    from services.volumetric_face_vinyl_service import resolve_face_vinyl_used_sqm

    resolution = resolve_face_vinyl_used_sqm(quote_input)
    if resolution.value is None or resolution.value <= 0:
        return _fail(
            UNIT_AREA_M2,
            kind=ERR_MISSING_INPUT,
            detail=resolution.quantity_basis or "face_vinyl_used_sqm_unresolved",
            missing=["face_vinyl_used_sqm"],
        )
    breakdown: Dict[str, Any] = {
        "face_vinyl_used_sqm": resolution.value,
        "quantity_source": resolution.source,
        "quantity_basis": resolution.quantity_basis,
        "fallback_weak_estimate": resolution.fallback_weak_estimate,
    }
    if resolution.recommended_roll_length_m is not None:
        breakdown["recommended_roll_length_m"] = resolution.recommended_roll_length_m
    if resolution.material_width_m is not None:
        breakdown["material_width_m"] = resolution.material_width_m
    if resolution.face_area_sqm is not None:
        breakdown["face_area_sqm"] = resolution.face_area_sqm
    if resolution.warnings:
        breakdown["warnings"] = list(resolution.warnings)
    return FormulaResult(
        value=resolution.value,
        unit=UNIT_AREA_M2,
        resolved=True,
        breakdown=breakdown,
    )


def _handle_svg_geometry_readiness_gate(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Non-priced gate that validates the presence of a vector source."""
    vector_file = quote_input.get("vector_file")
    if not isinstance(vector_file, str) or not vector_file.strip():
        return _fail(
            UNIT_MINUTES,
            kind=ERR_MISSING_INPUT,
            detail="vector_file is required for svg geometry readiness",
            missing=["vector_file"],
        )
    piece_quantity = quote_input.get("letter_count")
    if piece_quantity is None:
        piece_quantity = quote_input.get("real_letters_count")
    if piece_quantity is None:
        piece_quantity = quote_input.get("led_module_count")

    return FormulaResult(
        value=0.0,
        unit=UNIT_MINUTES,
        resolved=True,
        breakdown={
            "vector_file": vector_file.strip(),
            "non_priced": True,
            "letter_count": piece_quantity,
        },
    )


def _handle_letter_face_area(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Area in m² from explicit quote_input (no SVG derivation).

    Quote inputs:
        - letter_face_area_m2 (default key)
        - or params.area_quote_input_key (e.g. mounting_template_area_m2)

    Params:
        - waste_pct (float >= 0, default 0): percent points (15 => +15%).
        - area_quote_input_key (str, optional)
    """
    try:
        waste_pct = float(params.get("waste_pct", 0.0))
    except (TypeError, ValueError):
        return _fail(
            UNIT_AREA_M2,
            kind=ERR_INVALID_PARAM,
            detail="waste_pct must be numeric",
        )

    area_key = str(params.get("area_quote_input_key") or "letter_face_area_m2").strip()
    if not area_key:
        area_key = "letter_face_area_m2"

    missing: List[str] = []
    invalid: List[str] = []
    area = _coerce_positive_float(quote_input, area_key, missing, invalid)
    err = _missing_or_invalid_result(UNIT_AREA_M2, missing, invalid)
    if err is not None:
        return err
    assert area is not None and waste_pct is not None
    adjusted = area * (1.0 + waste_pct / 100.0)
    return FormulaResult(
        value=round(adjusted, 6),
        unit=UNIT_AREA_M2,
        resolved=True,
        breakdown={
            area_key: area,
            "waste_pct": waste_pct,
        },
    )


def _handle_letter_perimeter(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Linear perimeter quantity in metres (ml in templates).

    Quote inputs:
        - letter_perimeter_m (default key)
        - or params.perimeter_quote_input_key (e.g. cut_perimeter_m)

    Params:
        - extra_pct (float >= 0, default 0)
        - perimeter_quote_input_key (str, optional)
    """
    try:
        extra_pct = float(params.get("extra_pct", 0.0))
    except (TypeError, ValueError):
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="extra_pct must be numeric",
        )

    perim_key = str(
        params.get("perimeter_quote_input_key") or "letter_perimeter_m"
    ).strip() or "letter_perimeter_m"

    missing: List[str] = []
    invalid: List[str] = []
    perim = _coerce_positive_float(quote_input, perim_key, missing, invalid)
    err = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
    if err is not None:
        return FormulaResult(
            value=err.value,
            unit=UNIT_COUNT,
            resolved=err.resolved,
            error=err.error,
            breakdown=err.breakdown,
        )
    assert perim is not None
    adjusted = perim * (1.0 + extra_pct / 100.0)
    return FormulaResult(
        value=round(adjusted, 6),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown={perim_key: perim, "extra_pct": extra_pct},
    )


def _handle_return_wrap_area(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Oracal wrap area (m²) for return/cant band — Model A technical quantity.

    Uses ``compute_return_wrap_area_m2`` (shared_edge_cant geometry + quote waste).
    Does **not** invent default return depth (pricing helper may use 60mm).

    Quote inputs:
        - letter_perimeter_m (or params.perimeter_quote_input_key)
        - return_depth_mm (or depth_mm when return_depth_mm absent)

    Params:
        - perimeter_quote_input_key (optional)
        - depth_quote_input_key (default return_depth_mm)
        - waste_percent (optional override; default EDGE_CANT_QUOTE_WASTE_PERCENT)
    """
    perim_key = str(
        params.get("perimeter_quote_input_key") or "letter_perimeter_m"
    ).strip() or "letter_perimeter_m"
    depth_key = str(
        params.get("depth_quote_input_key") or "return_depth_mm"
    ).strip() or "return_depth_mm"
    depth_lookup = depth_key
    if quote_input.get(depth_key) is None and quote_input.get("depth_mm") is not None:
        depth_lookup = "depth_mm"

    missing: List[str] = []
    invalid: List[str] = []
    perim = _coerce_positive_float(quote_input, perim_key, missing, invalid)
    depth = _coerce_positive_float(quote_input, depth_lookup, missing, invalid)
    err = _missing_or_invalid_result(UNIT_AREA_M2, missing, invalid)
    if err is not None:
        return FormulaResult(
            value=err.value,
            unit=UNIT_AREA_M2,
            resolved=err.resolved,
            error=err.error,
            breakdown=err.breakdown,
        )
    assert perim is not None and depth is not None

    try:
        waste_percent = float(
            params.get("waste_percent", EDGE_CANT_QUOTE_WASTE_PERCENT)
        )
    except (TypeError, ValueError):
        return _fail(
            UNIT_AREA_M2,
            kind=ERR_INVALID_PARAM,
            detail="waste_percent must be numeric",
        )
    if waste_percent < 0:
        return _fail(
            UNIT_AREA_M2,
            kind=ERR_INVALID_PARAM,
            detail="waste_percent must be >= 0",
        )

    area = compute_return_wrap_area_m2(
        perim,
        depth,
        waste_percent=waste_percent,
        band_extra_mm=RETURN_VINYL_BAND_EXTRA_MM,
    )
    if area <= 0:
        return _fail(
            UNIT_AREA_M2,
            kind=ERR_INVALID_INPUT,
            detail="return_wrap_area resolved to non-positive area",
            missing=[perim_key, depth_lookup],
        )
    return FormulaResult(
        value=area,
        unit=UNIT_AREA_M2,
        resolved=True,
        breakdown={
            perim_key: perim,
            depth_key: depth,
            "waste_percent": waste_percent,
            "band_extra_mm": RETURN_VINYL_BAND_EXTRA_MM,
            "area_m2": area,
        },
    )


def _handle_mounting_bar_total_length(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Total premount bar length (ml) — override or assembly width × bar count.

    Quote inputs (priority):
        1. mounting_bar_length_m — explicit total length override
        2. width_mm × mounting_bar_count (default count 2: top + bottom bar)

    Params:
        - override_quote_input_key (default mounting_bar_length_m)
        - bar_count_quote_input_key (default mounting_bar_count)
        - default_bar_count (default 2)
    """
    override_key = str(
        params.get("override_quote_input_key") or "mounting_bar_length_m"
    ).strip() or "mounting_bar_length_m"
    count_key = str(
        params.get("bar_count_quote_input_key") or "mounting_bar_count"
    ).strip() or "mounting_bar_count"

    missing: List[str] = []
    invalid: List[str] = []
    override = _coerce_positive_float(quote_input, override_key, missing, invalid)
    if override is None and override_key != "premount_bar_length_ml":
        missing.clear()
        invalid.clear()
        override_key = "premount_bar_length_ml"
        override = _coerce_positive_float(quote_input, override_key, missing, invalid)
    if override is not None and override > 0:
        return FormulaResult(
            value=round(override, 6),
            unit=UNIT_COUNT,
            resolved=True,
            breakdown={
                "override_used": True,
                override_key: override,
                "derived_total_length_m": override,
            },
        )

    missing.clear()
    invalid.clear()
    width_mm = _coerce_positive_float(quote_input, "width_mm", missing, invalid)
    if width_mm is None:
        err = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
        if err is not None:
            return err
        return _fail(
            UNIT_COUNT,
            kind=ERR_MISSING_INPUT,
            detail=f"{override_key} or width_mm required for premount bar length",
            missing=[override_key, "width_mm"],
        )

    raw_count = quote_input.get(count_key)
    if raw_count is None:
        try:
            bar_count = float(params.get("default_bar_count", 2))
        except (TypeError, ValueError):
            bar_count = 2.0
    else:
        try:
            bar_count = float(raw_count)
        except (TypeError, ValueError):
            invalid.append(count_key)
            bar_count = 0.0
    if bar_count <= 0:
        invalid.append(count_key)

    err = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
    if err is not None:
        return err

    assembly_width_m = width_mm / 1000.0
    total_m = assembly_width_m * bar_count
    return FormulaResult(
        value=round(total_m, 6),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown={
            "override_used": False,
            "width_mm": width_mm,
            "assembly_width_m": assembly_width_m,
            "mounting_bar_count": bar_count,
            "derived_total_length_m": total_m,
        },
    )


def _handle_perimeter_based_time(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Routing/forming time from perimeter length.

    Formula (template default):
        minutes = (letter_perimeter_m / speed_m_per_min) * passes

    Alternate param:
        minutes_per_meter — when set, minutes = letter_perimeter_m * minutes_per_meter * passes

    Params:
        - speed_m_per_min (float > 0, default 0.3)
        - minutes_per_meter (float > 0, optional override)
        - passes (int > 0, default 1)
        - min_minutes (float >= 0, default 0)

    Quote inputs:
        - letter_perimeter_m (default)
        - or params.perimeter_quote_input_key

    Params:
        - perimeter_quote_input_key (str, optional)
    """
    perim_key = str(
        params.get("perimeter_quote_input_key") or "letter_perimeter_m"
    ).strip() or "letter_perimeter_m"

    try:
        speed = float(params.get("speed_m_per_min", 0.3))
        min_minutes = float(params.get("min_minutes", 0.0))
        m_per_m = params.get("minutes_per_meter")
        minutes_per_meter = float(m_per_m) if m_per_m is not None else None
    except (TypeError, ValueError):
        return _fail(
            UNIT_MINUTES,
            kind=ERR_INVALID_PARAM,
            detail="speed_m_per_min / minutes_per_meter / min_minutes must be numeric",
        )

    passes: Optional[int]
    if "passes" in params and params["passes"] is not None:
        try:
            passes_val = int(params["passes"])
        except (TypeError, ValueError):
            return _fail(
                UNIT_MINUTES,
                kind=ERR_INVALID_PARAM,
                detail="passes must be a positive integer",
            )
        if passes_val <= 0:
            return _fail(
                UNIT_MINUTES,
                kind=ERR_INVALID_PARAM,
                detail="passes must be > 0",
            )
        passes = passes_val
    else:
        passes = 1

    missing: List[str] = []
    invalid: List[str] = []
    perim = _coerce_positive_float(quote_input, perim_key, missing, invalid)
    err = _missing_or_invalid_result(UNIT_MINUTES, missing, invalid)
    if err is not None:
        return err
    assert perim is not None

    if minutes_per_meter is not None:
        if minutes_per_meter <= 0:
            return _fail(
                UNIT_MINUTES,
                kind=ERR_INVALID_PARAM,
                detail="minutes_per_meter must be > 0",
            )
        minutes = perim * minutes_per_meter * passes
        mode = "minutes_per_meter"
    else:
        if speed <= 0:
            return _fail(
                UNIT_MINUTES,
                kind=ERR_INVALID_PARAM,
                detail="speed_m_per_min must be > 0",
            )
        minutes = (perim / speed) * passes
        mode = "speed_m_per_min"

    minutes = max(minutes, min_minutes)
    return FormulaResult(
        value=round(minutes, 4),
        unit=UNIT_MINUTES,
        resolved=True,
        breakdown={
            perim_key: perim,
            "passes": passes,
            "mode": mode,
            "speed_m_per_min": speed,
            "minutes_per_meter": minutes_per_meter,
            "min_minutes": min_minutes,
        },
    )


def _handle_rectangular_panel_area(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Panel face area m² from rectangular dimensions.

    Formula:
        area_m2 = (panel_width_mm * panel_height_mm) / 1e6 * (1 + waste_pct/100)

    Quote inputs:
        - panel_width_mm, panel_height_mm
    """
    try:
        waste_pct = float(params.get("waste_pct", 0.0))
    except (TypeError, ValueError):
        return _fail(UNIT_AREA_M2, kind=ERR_INVALID_PARAM, detail="waste_pct must be numeric")

    missing: List[str] = []
    invalid: List[str] = []
    w = _coerce_positive_float(quote_input, "panel_width_mm", missing, invalid)
    h = _coerce_positive_float(quote_input, "panel_height_mm", missing, invalid)
    err = _missing_or_invalid_result(UNIT_AREA_M2, missing, invalid)
    if err is not None:
        return err
    assert w is not None and h is not None
    area = (w * h) / 1_000_000.0 * (1.0 + waste_pct / 100.0)
    return FormulaResult(
        value=round(area, 6),
        unit=UNIT_AREA_M2,
        resolved=True,
        breakdown={
            "panel_width_mm": w,
            "panel_height_mm": h,
            "waste_pct": waste_pct,
        },
    )


def _handle_rectangular_panel_perimeter(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Rectangular panel perimeter in metres.

    Formula:
        perimeter_m = 2 * (width_mm + height_mm) / 1000
    """
    missing: List[str] = []
    invalid: List[str] = []
    w = _coerce_positive_float(quote_input, "panel_width_mm", missing, invalid)
    h = _coerce_positive_float(quote_input, "panel_height_mm", missing, invalid)
    err = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
    if err is not None:
        return err
    assert w is not None and h is not None
    perim = 2.0 * (w + h) / 1000.0
    return FormulaResult(
        value=round(perim, 6),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown={"panel_width_mm": w, "panel_height_mm": h},
    )


def _handle_fold_length_from_sides(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Fold / V-groove run length in metres from panel dims and fold_sides.

    Quote inputs:
        - panel_width_mm, panel_height_mm, fold_sides

    fold_sides values:
        - all (default): 2*(w+h)
        - top_bottom: 2*w
        - left_right: 2*h
    """
    missing: List[str] = []
    invalid: List[str] = []
    w = _coerce_positive_float(quote_input, "panel_width_mm", missing, invalid)
    h = _coerce_positive_float(quote_input, "panel_height_mm", missing, invalid)
    err = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
    if err is not None:
        return err
    assert w is not None and h is not None

    raw_sides = quote_input.get("fold_sides")
    if raw_sides is None or str(raw_sides).strip() == "":
        missing.append("fold_sides")
        err2 = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
        if err2 is not None:
            return err2

    sides = str(raw_sides).strip().lower().replace("-", "_").replace(" ", "_")
    if sides in {"all", "toate", "toate_laturile"}:
        length_mm = 2.0 * (w + h)
    elif sides in {"top_bottom", "sus_jos", "tb"}:
        length_mm = 2.0 * w
    elif sides in {"left_right", "stanga_dreapta", "lr"}:
        length_mm = 2.0 * h
    else:
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_INPUT,
            detail=f"unsupported fold_sides={raw_sides!r}",
            missing=["fold_sides"],
        )

    return FormulaResult(
        value=round(length_mm / 1000.0, 6),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown={
            "panel_width_mm": w,
            "panel_height_mm": h,
            "fold_sides": sides,
            "fold_length_mm": length_mm,
        },
    )


def _handle_mounting_template_area(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Template alias for mounting-template material lines (Forex / paper)."""
    merged = dict(params)
    merged.setdefault("area_quote_input_key", "mounting_template_area_m2")
    return _handle_letter_face_area(merged, quote_input)


def _handle_area_from_quote_input(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Alias of letter_face_area with explicit area_quote_input_key default."""
    area_key = str(params.get("area_quote_input_key") or "cut_area_m2").strip()
    merged = dict(params)
    merged["area_quote_input_key"] = area_key
    return _handle_letter_face_area(merged, quote_input)


def _handle_perimeter_from_quote_input(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Alias of letter_perimeter with explicit perimeter_quote_input_key default."""
    perim_key = str(params.get("perimeter_quote_input_key") or "cut_perimeter_m").strip()
    merged = dict(params)
    merged["perimeter_quote_input_key"] = perim_key
    return _handle_letter_perimeter(merged, quote_input)


def _handle_count_based_time(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Time from a discrete count (letters, units).

    Formula:
        minutes = letter_count * minutes_per_unit

    Params:
        - minutes_per_letter (float > 0, alias for minutes_per_unit)
        - minutes_per_unit (float > 0)
        - min_minutes (float >= 0, default 0)

    Quote inputs:
        - letter_count (int > 0)
    """
    try:
        per_unit = float(
            params.get(
                "minutes_per_letter",
                params.get("minutes_per_unit", 1.0),
            )
        )
        min_minutes = float(params.get("min_minutes", 0.0))
    except (TypeError, ValueError):
        return _fail(
            UNIT_MINUTES,
            kind=ERR_INVALID_PARAM,
            detail="minutes_per_letter / minutes_per_unit must be numeric",
        )
    if per_unit <= 0:
        return _fail(
            UNIT_MINUTES,
            kind=ERR_INVALID_PARAM,
            detail="minutes_per_letter must be > 0",
        )

    missing: List[str] = []
    invalid: List[str] = []
    count = _coerce_positive_int(quote_input, "letter_count", missing, invalid)
    err = _missing_or_invalid_result(UNIT_MINUTES, missing, invalid)
    if err is not None:
        return err
    assert count is not None
    minutes = max(count * per_unit, min_minutes)
    return FormulaResult(
        value=round(minutes, 4),
        unit=UNIT_MINUTES,
        resolved=True,
        breakdown={
            "letter_count": count,
            "minutes_per_unit": per_unit,
            "min_minutes": min_minutes,
        },
    )


def _handle_led_per_letter(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """LED module count.

    Perimeter pitch mode (TPL-VOLUMETRIC-LETTERS):
        When params include module_length_mm and module_gap_mm:
            pitch_mm = module_length_mm + module_gap_mm
            count = ceil(letter_perimeter_m * 1000 / pitch_mm)
        Quote input: letter_perimeter_m (required)

    Legacy letter mode:
        count = letter_count * modules_per_letter
        Quote input: letter_count (required)
    """
    use_perimeter_pitch = (
        "module_length_mm" in params and params.get("module_length_mm") is not None
        and "module_gap_mm" in params and params.get("module_gap_mm") is not None
    )

    if use_perimeter_pitch:
        try:
            module_length_mm = float(params.get("module_length_mm"))
            module_gap_mm = float(params.get("module_gap_mm"))
        except (TypeError, ValueError):
            return _fail(
                UNIT_COUNT,
                kind=ERR_INVALID_PARAM,
                detail="module_length_mm / module_gap_mm must be numeric",
            )
        pitch_mm = module_length_mm + module_gap_mm
        if module_length_mm <= 0 or module_gap_mm < 0 or pitch_mm <= 0:
            return _fail(
                UNIT_COUNT,
                kind=ERR_INVALID_PARAM,
                detail="module_length_mm must be > 0 and pitch (length+gap) must be > 0",
            )

        missing: List[str] = []
        invalid: List[str] = []
        perim_m = _coerce_positive_float(
            quote_input, "letter_perimeter_m", missing, invalid
        )
        err = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
        if err is not None:
            return err
        assert perim_m is not None
        total_mm = perim_m * 1000.0
        total = int(ceil(total_mm / pitch_mm))
        return FormulaResult(
            value=float(total),
            unit=UNIT_COUNT,
            resolved=True,
            breakdown={
                "mode": "perimeter_pitch",
                "letter_perimeter_m": perim_m,
                "total_letter_perimeter_mm": round(total_mm, 3),
                "module_length_mm": module_length_mm,
                "module_gap_mm": module_gap_mm,
                "pitch_mm": pitch_mm,
                "led_module_count": total,
            },
        )

    try:
        modules = float(params.get("modules_per_letter", 1.0))
    except (TypeError, ValueError):
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="modules_per_letter must be numeric",
        )
    if modules <= 0:
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="modules_per_letter must be > 0",
        )

    missing = []
    invalid = []
    count = _coerce_positive_int(quote_input, "letter_count", missing, invalid)
    err = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
    if err is not None:
        return err
    assert count is not None
    total = int(ceil(count * modules))
    return FormulaResult(
        value=float(total),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown={
            "mode": "letter_count",
            "letter_count": count,
            "modules_per_letter": modules,
        },
    )


def _handle_psu_count(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """PSU count from total LED load (no formula chaining).

    Formula:
        total_watts = led_module_count * watts_per_module
        psu_count   = ceil(total_watts / psu_watts)

    Params:
        - watts_per_module (float > 0, default 1.5)
        - psu_watts (float > 0, default 150)
        - modules_per_psu (int > 0, optional alternate: ceil(led/modules_per_psu))

    Quote inputs:
        - led_module_count (int > 0)
    """
    try:
        watts_per_module = float(params.get("watts_per_module", 1.5))
        psu_watts = float(params.get("psu_watts", 150.0))
    except (TypeError, ValueError):
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="watts_per_module / psu_watts must be numeric",
        )
    if watts_per_module <= 0 or psu_watts <= 0:
        return _fail(
            UNIT_COUNT,
            kind=ERR_INVALID_PARAM,
            detail="watts_per_module and psu_watts must be > 0",
        )

    missing: List[str] = []
    invalid: List[str] = []
    led_modules = _coerce_positive_int(
        quote_input, "led_module_count", missing, invalid
    )
    err = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
    if err is not None:
        return err
    assert led_modules is not None

    if "modules_per_psu" in params and params["modules_per_psu"] is not None:
        try:
            mpp = int(params["modules_per_psu"])
        except (TypeError, ValueError):
            return _fail(
                UNIT_COUNT,
                kind=ERR_INVALID_PARAM,
                detail="modules_per_psu must be a positive integer",
            )
        if mpp <= 0:
            return _fail(
                UNIT_COUNT,
                kind=ERR_INVALID_PARAM,
                detail="modules_per_psu must be > 0",
            )
        count = int(ceil(led_modules / mpp))
        mode = "modules_per_psu"
        breakdown = {
            "led_module_count": led_modules,
            "modules_per_psu": mpp,
        }
    else:
        total_watts = led_modules * watts_per_module
        count = int(ceil(total_watts / psu_watts))
        mode = "watts"
        breakdown = {
            "led_module_count": led_modules,
            "watts_per_module": watts_per_module,
            "total_watts": round(total_watts, 3),
            "psu_watts": psu_watts,
        }

    return FormulaResult(
        value=float(count),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown={**breakdown, "mode": mode},
    )


def _handle_letter_count_material(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Material quantity driven by letter count (e.g. paint sets).

    Quote inputs:
        - letter_count (int > 0)
    """
    missing: List[str] = []
    invalid: List[str] = []
    count = _coerce_positive_int(quote_input, "letter_count", missing, invalid)
    err = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
    if err is not None:
        return err
    assert count is not None
    return FormulaResult(
        value=float(count),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown={"letter_count": count},
    )


def _coerce_quote_input_bool(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return False


def _positive_int_param(
    params: Mapping[str, Any],
    *keys: str,
) -> tuple[int | None, str | None]:
    raw = None
    for key in keys:
        if params.get(key) is not None:
            raw = params.get(key)
            break
    if raw is None:
        return None, "required"
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None, "invalid"
    if value <= 0:
        return None, "invalid"
    return value, None


def _handle_perimeter_pass_linear_meter(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Linear metres for CNC routing: perimeter × pass_count.

    Quote inputs:
        - letter_perimeter_m (default key, or perimeter_quote_input_key)
        - optional bevel_quote_input_key (bool; default false when absent)

    Params:
        - pass_count or passes (int > 0) — static total passes, OR
        - base_pass_count + bevel_pass_count + bevel_quote_input_key — dynamic
        - cut_passes, bevel_passes (optional traceability ints)
        - perimeter_quote_input_key (optional)
        - material, notes (optional traceability strings)
    """
    bevel_key = params.get("bevel_quote_input_key")
    pass_count: int | None = None
    breakdown_extras: Dict[str, Any] = {}

    if bevel_key:
        base_pass, base_err = _positive_int_param(
            params, "base_pass_count", "cut_passes"
        )
        bevel_pass, bevel_err = _positive_int_param(
            params, "bevel_pass_count", "bevel_passes"
        )
        if base_err or bevel_err:
            return _fail(
                UNIT_COUNT,
                kind=ERR_INVALID_PARAM,
                detail=(
                    "base_pass_count (or cut_passes) and bevel_pass_count "
                    "(or bevel_passes) are required when bevel_quote_input_key is set"
                ),
            )
        assert base_pass is not None and bevel_pass is not None
        raw_bevel = quote_input.get(str(bevel_key).strip())
        default_applied = raw_bevel is None
        back_bevel_enabled = _coerce_quote_input_bool(raw_bevel)
        pass_count = base_pass + (bevel_pass if back_bevel_enabled else 0)
        breakdown_extras = {
            "base_pass_count": base_pass,
            "bevel_pass_count": bevel_pass,
            "bevel_quote_input_key": str(bevel_key).strip(),
            "back_bevel_enabled": back_bevel_enabled,
            "default_applied": default_applied,
        }
    else:
        pass_raw = params.get("pass_count")
        if pass_raw is None:
            pass_raw = params.get("passes")
        if pass_raw is None:
            return _fail(
                UNIT_COUNT,
                kind=ERR_INVALID_PARAM,
                detail="pass_count (or passes) is required",
            )
        try:
            pass_count = int(pass_raw)
        except (TypeError, ValueError):
            return _fail(
                UNIT_COUNT,
                kind=ERR_INVALID_PARAM,
                detail="pass_count must be a positive integer",
            )
        if pass_count <= 0:
            return _fail(
                UNIT_COUNT,
                kind=ERR_INVALID_PARAM,
                detail="pass_count must be a positive integer",
            )

    perim_res = _handle_letter_perimeter(params, quote_input)
    if not perim_res.resolved or perim_res.value is None:
        return perim_res

    perim_m = float(perim_res.value)
    total_ml = perim_m * float(pass_count)
    breakdown: Dict[str, Any] = {
        **(perim_res.breakdown or {}),
        "pass_count": pass_count,
        "total_pass_linear_m": round(total_ml, 6),
        **breakdown_extras,
    }
    if params.get("cut_passes") is not None:
        breakdown["cut_passes"] = params.get("cut_passes")
    if params.get("bevel_passes") is not None:
        breakdown["bevel_passes"] = params.get("bevel_passes")
    if params.get("material"):
        breakdown["material"] = str(params.get("material"))
    if params.get("notes"):
        breakdown["pass_notes"] = str(params.get("notes"))

    return FormulaResult(
        value=round(total_ml, 6),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown=breakdown,
    )


def _handle_ceil_quote_input_quantity(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """Whole-unit consumable quantity: ceil(positive quote_input estimate).

    Quote inputs (first match wins):
        - params.quote_input_key (default paint_tube_count)
        - params.fallback_quote_input_key (default estimated_paint_tubes)

    Returns charged integer quantity; never fractional units.
    """
    primary_key = str(
        params.get("quote_input_key") or "paint_tube_count"
    ).strip() or "paint_tube_count"
    fallback_key = str(
        params.get("fallback_quote_input_key") or "estimated_paint_tubes"
    ).strip() or "estimated_paint_tubes"

    missing: List[str] = []
    invalid: List[str] = []
    raw: Optional[float] = None
    key_used: Optional[str] = None

    for key in (primary_key, fallback_key):
        if key in quote_input and quote_input.get(key) is not None:
            raw = _coerce_positive_float(quote_input, key, missing, invalid)
            if raw is not None:
                key_used = key
                missing.clear()
                invalid.clear()
                break
            if key in missing:
                missing.remove(key)
            if key in invalid:
                invalid.remove(key)

    if raw is None:
        if invalid:
            return _missing_or_invalid_result(UNIT_COUNT, [], invalid) or _fail(
                UNIT_COUNT,
                kind=ERR_INVALID_INPUT,
                detail="paint tube estimate must be a positive number",
                missing=invalid,
            )
        return _fail(
            UNIT_COUNT,
            kind=ERR_MISSING_INPUT,
            detail=(
                f"requires quote_input {primary_key!r} or {fallback_key!r}"
            ),
            missing=[primary_key],
        )

    charged = int(ceil(raw))
    return FormulaResult(
        value=float(charged),
        unit=UNIT_COUNT,
        resolved=True,
        breakdown={
            "quote_input_key": key_used,
            "raw_estimate": raw,
            "charged_integer_quantity": charged,
        },
    )


def _handle_led_module_count(
    params: Mapping[str, Any],
    quote_input: Mapping[str, Any],
) -> FormulaResult:
    """LED module count for operation pricing.

    Quote inputs:
        - led_module_count (preferred)
        - or letter_perimeter_m when params include module_length_mm + module_gap_mm
    """
    missing: List[str] = []
    invalid: List[str] = []
    if "led_module_count" in quote_input and quote_input.get("led_module_count") is not None:
        count = _coerce_positive_int(
            quote_input, "led_module_count", missing, invalid
        )
        err = _missing_or_invalid_result(UNIT_COUNT, missing, invalid)
        if err is not None:
            return err
        assert count is not None
        return FormulaResult(
            value=float(count),
            unit=UNIT_COUNT,
            resolved=True,
            breakdown={"led_module_count": count, "mode": "quote_input"},
        )

    derived = _handle_led_per_letter(params, quote_input)
    if derived.resolved and derived.value is not None:
        return FormulaResult(
            value=derived.value,
            unit=UNIT_COUNT,
            resolved=True,
            breakdown={
                **(derived.breakdown or {}),
                "mode": "derived_perimeter_pitch",
            },
        )

    return _fail(
        UNIT_COUNT,
        kind=ERR_MISSING_INPUT,
        detail="led_module_count or derivable letter_perimeter_m with pitch params required",
        missing=["led_module_count"],
    )


# ---------------------------------------------------------------------------
# Registry + public resolver
# ---------------------------------------------------------------------------
HandlerFn = Callable[[Mapping[str, Any], Mapping[str, Any]], FormulaResult]

FORMULA_REGISTRY: Dict[FormulaId, HandlerFn] = {
    FormulaId.CNC_TIME_FROM_PATH: _handle_cnc_time_from_path,
    FormulaId.PLEXI_DIFFUSER_AREA: _handle_plexi_diffuser_area,
    FormulaId.RELIEF_MATERIAL_AREA: _handle_relief_material_area,
    FormulaId.LED_COUNT_FROM_AREA: _handle_led_count_from_area,
    FormulaId.LED_PSU_SIZING: _handle_led_psu_sizing,
    FormulaId.LED_ASSEMBLY_TIME: _handle_led_assembly_time,
    FormulaId.LETTER_FACE_AREA: _handle_letter_face_area,
    FormulaId.LETTER_PERIMETER: _handle_letter_perimeter,
    FormulaId.PERIMETER_BASED_TIME: _handle_perimeter_based_time,
    FormulaId.COUNT_BASED_TIME: _handle_count_based_time,
    FormulaId.LED_PER_LETTER: _handle_led_per_letter,
    FormulaId.PSU_COUNT: _handle_psu_count,
    FormulaId.LETTER_COUNT_MATERIAL: _handle_letter_count_material,
    FormulaId.PERIMETER_PASS_LINEAR_METER: _handle_perimeter_pass_linear_meter,
    FormulaId.LED_MODULE_COUNT: _handle_led_module_count,
    FormulaId.CEIL_QUOTE_INPUT_QUANTITY: _handle_ceil_quote_input_quantity,
    FormulaId.RECTANGULAR_PANEL_AREA: _handle_rectangular_panel_area,
    FormulaId.RECTANGULAR_PANEL_PERIMETER: _handle_rectangular_panel_perimeter,
    FormulaId.FOLD_LENGTH_FROM_SIDES: _handle_fold_length_from_sides,
    FormulaId.AREA_FROM_QUOTE_INPUT: _handle_area_from_quote_input,
    FormulaId.PERIMETER_FROM_QUOTE_INPUT: _handle_perimeter_from_quote_input,
    FormulaId.MOUNTING_BAR_TOTAL_LENGTH: _handle_mounting_bar_total_length,
    FormulaId.PREMOUNT_BAR_LINEAR_METER: _handle_mounting_bar_total_length,
    FormulaId.FACE_VINYL_USED_SQM: _handle_face_vinyl_used_sqm,
    FormulaId.SVG_GEOMETRY_READINESS_GATE: _handle_svg_geometry_readiness_gate,
    FormulaId.MOUNTING_TEMPLATE_AREA: _handle_mounting_template_area,
    # Same magnitude as letter perimeter (ml); depth/finish gates filter emission.
    FormulaId.RETURN_PROFILE_LINEAR_METER: _handle_letter_perimeter,
    FormulaId.RETURN_WRAP_AREA: _handle_return_wrap_area,
}


def known_formulas() -> List[str]:
    """Returns the list of canonical formula_id strings. Useful for
    diagnostics and for validators that want to check template JSON
    without importing the enum."""
    return [fid.value for fid in FORMULA_REGISTRY.keys()]


def resolve_formula(
    formula_id: str,
    params: Optional[Mapping[str, Any]],
    quote_input: Optional[Mapping[str, Any]],
) -> FormulaResult:
    """Resolve a formula by its canonical string id.

    Args:
      formula_id: Canonical string (must match `FormulaId` value).
      params:     Template-side parameters (trusted; usually constants).
      quote_input: Per-quote inputs. MAY be empty — handlers will then
                  return ``resolved=False`` with ``MISSING_INPUT``.

    Returns:
      ``FormulaResult``. Callers MUST inspect ``resolved`` before using
      ``value``. A ``resolved=False`` result with
      ``error["kind"] == "UNKNOWN_FORMULA"`` means the template referred
      to a formula that isn't registered — callers should treat that as
      a hard error (misconfigured template), distinct from missing input.
    """
    params = dict(params or {})
    quote_input = dict(quote_input or {})

    try:
        fid = FormulaId(formula_id)
    except ValueError:
        # Build the list of known ids only on error — cheap, explicit.
        return FormulaResult(
            value=None,
            unit="",
            resolved=False,
            error={
                "kind": "UNKNOWN_FORMULA",
                "detail": (
                    f"formula_id={formula_id!r} is not registered; "
                    f"known={known_formulas()}"
                ),
                "missing": [],
            },
        )

    handler = FORMULA_REGISTRY[fid]
    return handler(params, quote_input)