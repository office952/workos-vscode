"""Intake V4 — operator sheet footprint source selection for material review (not stock)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

SHEET_FOOTPRINT_OVERRIDE_SOURCE = "operator_manual_footprint"
DEFAULT_SHEET_FOOTPRINT_APPLIES_TO = frozenset({"plexiglas_face", "forex_backing"})

OperatorFootprintSource = Literal[
    "eligible_area_floor",
    "face_union_bbox",
    "layout_occupied_area",
    "operator_manual_footprint",
    "full_sheet_allocation",
    "placement_footprint_face",
]

OPERATOR_SELECTABLE_FOOTPRINT_SOURCES: frozenset[str] = frozenset(
    {
        "eligible_area_floor",
        "face_union_bbox",
        "layout_occupied_area",
        "operator_manual_footprint",
        "full_sheet_allocation",
    }
)


@dataclass(frozen=True)
class SheetFootprintCandidateAreas:
    eligible_face_area_sqm: float | None
    placement_footprint_face_sqm: float | None
    face_union_bbox_sqm: float | None
    layout_occupied_area_sqm: float | None
    full_sheet_allocation_sqm: float | None
    operator_manual_footprint_sqm: float | None = None


def compute_operator_manual_footprint_sqm(width_cm: float, height_cm: float) -> float:
    """Corel layout rectangle: width_cm × height_cm / 10_000 → m²."""
    return round(float(width_cm) * float(height_cm) / 10_000.0, 4)


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def normalize_sheet_footprint_applies_to(values: list[str] | None) -> list[str]:
    if not values:
        return sorted(DEFAULT_SHEET_FOOTPRINT_APPLIES_TO)
    allowed = [str(v).strip() for v in values if str(v).strip() in DEFAULT_SHEET_FOOTPRINT_APPLIES_TO]
    return allowed or sorted(DEFAULT_SHEET_FOOTPRINT_APPLIES_TO)


def _read_selected_footprint_source(raw: dict[str, Any]) -> str | None:
    source = raw.get("selectedFootprintSource") or raw.get("selected_footprint_source")
    if not source:
        return None
    normalized = str(source).strip()
    return normalized if normalized in OPERATOR_SELECTABLE_FOOTPRINT_SOURCES else None


def sheet_quote_override_from_payload(payload_raw: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload_raw, dict):
        return None
    raw = payload_raw.get("sheet_quote_override")
    if not isinstance(raw, dict):
        return None
    width_cm = _positive(raw.get("widthCm") if raw.get("widthCm") is not None else raw.get("width_cm"))
    height_cm = _positive(raw.get("heightCm") if raw.get("heightCm") is not None else raw.get("height_cm"))
    selected_source = _read_selected_footprint_source(raw)
    area_sqm = _positive(raw.get("areaSqm") if raw.get("areaSqm") is not None else raw.get("area_sqm"))
    if area_sqm is None and width_cm is not None and height_cm is not None:
        area_sqm = compute_operator_manual_footprint_sqm(width_cm, height_cm)
    use_for_quote = bool(
        raw.get("useForQuoteEstimate") if "useForQuoteEstimate" in raw else raw.get("use_for_quote_estimate")
    )
    if selected_source is None and width_cm is None and height_cm is None and not use_for_quote:
        return None
    if selected_source == "operator_manual_footprint" and (width_cm is None or height_cm is None):
        return None
    return {
        "enabled": True,
        "source": SHEET_FOOTPRINT_OVERRIDE_SOURCE,
        "selectedFootprintSource": selected_source,
        "widthCm": width_cm,
        "heightCm": height_cm,
        "areaSqm": area_sqm,
        "reason": str(raw.get("reason") or "").strip(),
        "appliesTo": normalize_sheet_footprint_applies_to(raw.get("appliesTo") or raw.get("applies_to")),
        "useForQuoteEstimate": use_for_quote,
        "createdBy": raw.get("createdBy") or raw.get("created_by"),
        "createdAt": raw.get("createdAt") or raw.get("created_at"),
    }


def build_sheet_quote_override_record(
    *,
    selected_footprint_source: str,
    reason: str,
    applies_to: list[str] | None,
    use_for_quote_estimate: bool,
    created_by: str | None,
    width_cm: float | None = None,
    height_cm: float | None = None,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if selected_footprint_source not in OPERATOR_SELECTABLE_FOOTPRINT_SOURCES:
        raise ValueError("invalid_footprint_source")
    area_sqm: float | None = None
    width_value: float | None = None
    height_value: float | None = None
    if selected_footprint_source == "operator_manual_footprint":
        if width_cm is None or height_cm is None:
            raise ValueError("invalid_dimensions")
        width_value = round(float(width_cm), 4)
        height_value = round(float(height_cm), 4)
        area_sqm = compute_operator_manual_footprint_sqm(width_value, height_value)
    now = datetime.now(timezone.utc).isoformat()
    created_at = None
    if isinstance(previous, dict):
        created_at = previous.get("createdAt") or previous.get("created_at")
    record: dict[str, Any] = {
        "enabled": True,
        "source": SHEET_FOOTPRINT_OVERRIDE_SOURCE,
        "selectedFootprintSource": selected_footprint_source,
        "reason": reason.strip(),
        "appliesTo": normalize_sheet_footprint_applies_to(applies_to),
        "useForQuoteEstimate": bool(use_for_quote_estimate),
        "use_for_quote_review": True,
        "is_applied_to_quote": False,
        "createdBy": created_by if created_at is None else (previous or {}).get("createdBy") or created_by,
        "createdAt": created_at or now,
        "updatedAt": now,
    }
    if width_value is not None:
        record["widthCm"] = width_value
    if height_value is not None:
        record["heightCm"] = height_value
    if area_sqm is not None:
        record["areaSqm"] = area_sqm
    return record


def validate_sheet_footprint_override_request(
    *,
    selected_footprint_source: str,
    width_cm: float | None,
    height_cm: float | None,
    reason: str,
    use_for_quote_estimate: bool,
    eligible_face_area_sqm: float | None,
    candidate_areas: SheetFootprintCandidateAreas | None = None,
    full_sheet_sqm: float | None = 6.0,
) -> tuple[float | None, list[str]]:
    if selected_footprint_source not in OPERATOR_SELECTABLE_FOOTPRINT_SOURCES:
        raise ValueError("invalid_footprint_source")
    warnings: list[str] = []
    area_sqm: float | None = None
    if selected_footprint_source == "operator_manual_footprint":
        if width_cm is None or height_cm is None or width_cm <= 0 or height_cm <= 0:
            raise ValueError("invalid_dimensions")
        if not reason.strip():
            raise ValueError("note_required")
        area_sqm = compute_operator_manual_footprint_sqm(width_cm, height_cm)
        eligible = _positive(eligible_face_area_sqm)
        if use_for_quote_estimate and eligible is not None and area_sqm < eligible - 1e-9:
            raise ValueError("footprint_below_eligible_area")
        full_sheet = _positive(full_sheet_sqm)
        if full_sheet is not None and area_sqm > full_sheet + 1e-9:
            warnings.append("footprint_exceeds_full_sheet")
        return area_sqm, warnings

    if use_for_quote_estimate and candidate_areas is not None:
        area_sqm = resolve_footprint_area_for_source(selected_footprint_source, candidate_areas)
        if area_sqm is None:
            raise ValueError("footprint_source_unavailable")
    return area_sqm, warnings


def resolve_footprint_area_for_source(
    source: str,
    candidates: SheetFootprintCandidateAreas,
) -> float | None:
    if source == "eligible_area_floor":
        return _positive(candidates.eligible_face_area_sqm)
    if source == "placement_footprint_face":
        return _positive(candidates.placement_footprint_face_sqm)
    if source == "face_union_bbox":
        return _positive(candidates.face_union_bbox_sqm)
    if source == "layout_occupied_area":
        return _positive(candidates.layout_occupied_area_sqm)
    if source == "full_sheet_allocation":
        return _positive(candidates.full_sheet_allocation_sqm)
    if source == "operator_manual_footprint":
        manual = _positive(candidates.operator_manual_footprint_sqm)
        if manual is not None:
            return manual
        return None
    return None


def resolve_operator_footprint_target(
    *,
    override: dict[str, Any] | None,
    eligible_face_area_sqm: float | None,
    base_selected_sqm: float | None,
    sheet_quantity_floor_applied: bool,
    candidate_areas: SheetFootprintCandidateAreas | None = None,
) -> tuple[float | None, str, float | None, bool]:
    """Returns (selected_sqm, selected_source, operator_manual_footprint_sqm, apply_to_material_rows)."""
    manual_sqm = _positive((override or {}).get("areaSqm")) if override else None
    default_source: Literal["eligible_area_floor", "placement_footprint_face", "none"] = (
        "eligible_area_floor" if sheet_quantity_floor_applied else "placement_footprint_face"
    )
    if base_selected_sqm is None:
        default_source = "none"

    if not override or not override.get("useForQuoteEstimate"):
        return _positive(base_selected_sqm), default_source, manual_sqm, False

    selected_source = _read_selected_footprint_source(override) or (
        SHEET_FOOTPRINT_OVERRIDE_SOURCE if manual_sqm else default_source
    )
    if candidate_areas is not None:
        candidate_areas = SheetFootprintCandidateAreas(
            eligible_face_area_sqm=candidate_areas.eligible_face_area_sqm,
            placement_footprint_face_sqm=candidate_areas.placement_footprint_face_sqm,
            face_union_bbox_sqm=candidate_areas.face_union_bbox_sqm,
            layout_occupied_area_sqm=candidate_areas.layout_occupied_area_sqm,
            full_sheet_allocation_sqm=candidate_areas.full_sheet_allocation_sqm,
            operator_manual_footprint_sqm=manual_sqm or candidate_areas.operator_manual_footprint_sqm,
        )
        target_sqm = resolve_footprint_area_for_source(selected_source, candidate_areas)
        if target_sqm is not None:
            return target_sqm, selected_source, manual_sqm, True

    if manual_sqm:
        eligible = _positive(eligible_face_area_sqm) or 0.0
        return max(eligible, manual_sqm), SHEET_FOOTPRINT_OVERRIDE_SOURCE, manual_sqm, True

    return _positive(base_selected_sqm), default_source, manual_sqm, False


def resolve_sheet_quote_selection_with_override(
    *,
    eligible_face_area_sqm: float | None,
    base_selected_sqm: float | None,
    sheet_quantity_floor_applied: bool,
    override: dict[str, Any] | None,
    candidate_areas: SheetFootprintCandidateAreas | None = None,
) -> tuple[float | None, str, float | None]:
    """Returns (selected_sqm, selected_source, operator_manual_footprint_sqm)."""
    selected_sqm, selected_source, manual_sqm, _ = resolve_operator_footprint_target(
        override=override,
        eligible_face_area_sqm=eligible_face_area_sqm,
        base_selected_sqm=base_selected_sqm,
        sheet_quantity_floor_applied=sheet_quantity_floor_applied,
        candidate_areas=candidate_areas,
    )
    return selected_sqm, selected_source, manual_sqm


def apply_operator_footprint_to_sheet_material_quantities(
    *,
    sheet_face_qty: float | None,
    sheet_backing_qty: float | None,
    override: dict[str, Any] | None,
    candidate_areas: SheetFootprintCandidateAreas | None = None,
    eligible_face_area_sqm: float | None = None,
    base_selected_sqm: float | None = None,
    sheet_quantity_floor_applied: bool = False,
) -> tuple[float | None, float | None, bool]:
    """Raise face/backing m² when operator selected a footprint source for internal review."""
    target_sqm, _, _, apply = resolve_operator_footprint_target(
        override=override,
        eligible_face_area_sqm=eligible_face_area_sqm,
        base_selected_sqm=base_selected_sqm,
        sheet_quantity_floor_applied=sheet_quantity_floor_applied,
        candidate_areas=candidate_areas,
    )
    if not apply or target_sqm is None:
        return sheet_face_qty, sheet_backing_qty, False
    applies = set((override or {}).get("appliesTo") or DEFAULT_SHEET_FOOTPRINT_APPLIES_TO)
    face_qty = sheet_face_qty
    backing_qty = sheet_backing_qty
    if "plexiglas_face" in applies and face_qty is not None:
        face_qty = max(face_qty, target_sqm)
    elif "plexiglas_face" in applies:
        face_qty = target_sqm
    if "forex_backing" in applies and backing_qty is not None:
        backing_qty = max(backing_qty, target_sqm)
    elif "forex_backing" in applies:
        backing_qty = target_sqm
    return face_qty, backing_qty, True
