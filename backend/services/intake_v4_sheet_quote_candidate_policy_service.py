"""Intake V4 sheet quote candidate policy preview — internal review only (not CostEngine)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from services.intake_v4_nesting_material_precision import (
    SHEET_EXCLUDED_ROLES,
    SHEET_FACE_ROLES,
    _build_parts_metadata_index,
    _is_orphan_unassigned_split_part,
    _layer_role_for_name,
    _positive,
    classify_sheet_material_intent,
)

DEFAULT_BUFFER_PERCENT = 5.0
MIN_BUFFER_PERCENT = 0.0
MAX_BUFFER_PERCENT = 20.0
SPREAD_MANUAL_REVIEW_THRESHOLD = 1.35
SHELF_VS_CHILD_REVIEW_THRESHOLD = 1.75

ConfidenceLevel = Literal["low", "medium", "high"]
SelectionMode = Literal["current_floor", "auto_candidate_preview", "manual_override_preview"]


@dataclass(frozen=True)
class SheetQuoteBBoxMetrics:
    child_part_bbox_sum_sqm: float | None
    semantic_group_bbox_sum_sqm: float | None
    design_space_union_bbox_sqm: float | None
    design_space_union_bbox_with_buffer_sqm: float | None
    face_child_part_count: int
    orphan_defs_part_count: int


@dataclass(frozen=True)
class SheetQuoteRecommendedAutoCandidate:
    source: str
    area_sqm: float | None
    buffer_percent: float
    confidence: ConfidenceLevel
    reason: str


@dataclass(frozen=True)
class SheetQuoteSelectionPreview:
    selected_source: str
    final_area_sqm: float | None
    selection_mode: SelectionMode
    is_applied_to_quote: bool


@dataclass(frozen=True)
class SheetQuoteOperatorOverridePreview:
    enabled: bool
    width_cm: float | None
    height_cm: float | None
    area_sqm: float | None
    note: str | None


@dataclass(frozen=True)
class SheetQuoteCandidatePolicyPreview:
    bbox_metrics: SheetQuoteBBoxMetrics
    recommended_auto_candidate: SheetQuoteRecommendedAutoCandidate
    requires_manual_review: bool
    manual_review_reason: str | None
    operator_override: SheetQuoteOperatorOverridePreview
    selection: SheetQuoteSelectionPreview


def _part_items(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    parts_block = analysis.get("parts")
    if isinstance(parts_block, dict):
        raw = parts_block.get("items")
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
    if isinstance(parts_block, list):
        return [item for item in parts_block if isinstance(item, dict)]
    return []


def _part_bounds(item: dict[str, Any]) -> dict[str, Any]:
    bounds = item.get("bounds")
    return bounds if isinstance(bounds, dict) else {}


def _part_source(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("source")
    return source if isinstance(source, dict) else {}


def _part_bounding_area_sqm(item: dict[str, Any]) -> float:
    bounds = _part_bounds(item)
    area = _positive(bounds.get("boundingAreaSqm"))
    if area is not None:
        return area
    width = _positive(bounds.get("widthMm"))
    height = _positive(bounds.get("heightMm"))
    if width is None or height is None:
        return 0.0
    return (width * height) / 1_000_000.0


def _is_face_child_part(
    item: dict[str, Any],
    *,
    layer_role_setup: dict[str, Any] | None,
    parts_index: dict[str, dict[str, Any]],
    part_class_index: dict[str, dict[str, Any]],
) -> bool:
    part_id = str(item.get("id") or "")
    if _is_orphan_unassigned_split_part(part_id, parts_index.get(part_id)):
        return False
    part_class = part_class_index.get(part_id)
    if part_class and part_class.get("is_inner_hole"):
        return False
    if str(item.get("derivedPartKind") or "") == "inner-hole-package":
        return False
    source = _part_source(item)
    layer_id = str(source.get("layerId") or parts_index.get(part_id, {}).get("layer_id") or "")
    layer_name = str(source.get("layerName") or parts_index.get(part_id, {}).get("layer_name") or layer_id)
    layer_role = _layer_role_for_name(layer_role_setup, layer_id, layer_name)
    if layer_role in SHEET_EXCLUDED_ROLES:
        return False
    intent = classify_sheet_material_intent(part_meta=parts_index.get(part_id), layer_role=layer_role)
    return intent == "face" or layer_role in SHEET_FACE_ROLES


def _union_bbox_sqm(items: list[dict[str, Any]]) -> float | None:
    min_x = min_y = None
    max_x = max_y = None
    for item in items:
        bounds = _part_bounds(item)
        x = _positive(bounds.get("xMm"))
        y = _positive(bounds.get("yMm"))
        w = _positive(bounds.get("widthMm"))
        h = _positive(bounds.get("heightMm"))
        if x is None or y is None or w is None or h is None:
            continue
        min_x = x if min_x is None else min(min_x, x)
        min_y = y if min_y is None else min(min_y, y)
        max_x = x + w if max_x is None else max(max_x, x + w)
        max_y = y + h if max_y is None else max(max_y, y + h)
    if min_x is None or min_y is None or max_x is None or max_y is None:
        return None
    return round((max_x - min_x) * (max_y - min_y) / 1_000_000.0, 4)


def compute_sheet_quote_bbox_metrics(
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    *,
    buffer_percent: float = DEFAULT_BUFFER_PERCENT,
) -> SheetQuoteBBoxMetrics:
    parts_index = _build_parts_metadata_index(analysis)
    part_class_index = _part_classification_index(analysis, layer_role_setup)
    items = _part_items(analysis)

    face_items = [
        item
        for item in items
        if _is_face_child_part(
            item,
            layer_role_setup=layer_role_setup,
            parts_index=parts_index,
            part_class_index=part_class_index,
        )
    ]
    child_sum = round(sum(_part_bounding_area_sqm(item) for item in face_items), 4) if face_items else None

    semantic_sum = 0.0
    semantic_found = False
    layers = analysis.get("layers")
    if isinstance(layers, list):
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            layer_id = str(layer.get("id") or "")
            layer_name = str(layer.get("name") or layer_id)
            role = _layer_role_for_name(layer_role_setup, layer_id, layer_name)
            if role not in SHEET_FACE_ROLES:
                continue
            area = _positive(layer.get("filledAreaSqm")) or _positive(layer.get("boundingAreaSqm"))
            if area:
                semantic_sum += area
                semantic_found = True

    design_union = _union_bbox_sqm(face_items)
    buffer = max(MIN_BUFFER_PERCENT, min(MAX_BUFFER_PERCENT, buffer_percent))
    design_with_buffer = (
        round(design_union * (1.0 + buffer / 100.0), 4) if design_union is not None else None
    )

    orphan_count = sum(
        1
        for item in items
        if _is_orphan_unassigned_split_part(str(item.get("id") or ""), parts_index.get(str(item.get("id") or "")))
    )

    return SheetQuoteBBoxMetrics(
        child_part_bbox_sum_sqm=child_sum,
        semantic_group_bbox_sum_sqm=round(semantic_sum, 4) if semantic_found else None,
        design_space_union_bbox_sqm=design_union,
        design_space_union_bbox_with_buffer_sqm=design_with_buffer,
        face_child_part_count=len(face_items),
        orphan_defs_part_count=orphan_count,
    )


def _part_classification_index(
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    from services.intake_v4_nesting_material_precision import _part_classification_index as _index

    return _index(analysis, layer_role_setup)


def _candidate_spread(
    *,
    eligible_area_sqm: float | None,
    child_part_bbox_sum_sqm: float | None,
    face_union_bbox_sqm: float | None,
    design_space_union_bbox_sqm: float | None,
) -> float | None:
    values = [
        v
        for v in (
            eligible_area_sqm,
            child_part_bbox_sum_sqm,
            face_union_bbox_sqm,
            design_space_union_bbox_sqm,
        )
        if v is not None and v > 0
    ]
    if len(values) < 2:
        return None
    return max(values) / min(values)


def _confidence_from_spread(spread: float | None) -> ConfidenceLevel:
    if spread is None:
        return "low"
    if spread <= 1.15:
        return "high"
    if spread <= 1.35:
        return "medium"
    return "low"


def compute_recommended_auto_candidate(
    *,
    eligible_area_sqm: float | None,
    child_part_bbox_sum_sqm: float | None,
    face_union_bbox_sqm: float | None,
    design_space_union_bbox_sqm: float | None,
    buffer_percent: float = DEFAULT_BUFFER_PERCENT,
) -> SheetQuoteRecommendedAutoCandidate:
    buffer = max(MIN_BUFFER_PERCENT, min(MAX_BUFFER_PERCENT, buffer_percent))
    child_buffered = (
        round(child_part_bbox_sum_sqm * (1.0 + buffer / 100.0), 4)
        if child_part_bbox_sum_sqm is not None
        else None
    )
    eligible = _positive(eligible_area_sqm) or 0.0
    recommended = child_buffered
    if recommended is None:
        recommended = eligible if eligible > 0 else None
    else:
        recommended = max(eligible, recommended)

    spread = _candidate_spread(
        eligible_area_sqm=eligible_area_sqm,
        child_part_bbox_sum_sqm=child_part_bbox_sum_sqm,
        face_union_bbox_sqm=face_union_bbox_sqm,
        design_space_union_bbox_sqm=design_space_union_bbox_sqm,
    )
    confidence = _confidence_from_spread(spread)
    return SheetQuoteRecommendedAutoCandidate(
        source="child_part_bbox_sum_with_buffer",
        area_sqm=recommended,
        buffer_percent=buffer,
        confidence=confidence,
        reason=(
            f"max(eligible, childPartBBoxSum × {buffer:.0f}% buffer) — preview only, not quote final."
        ),
    )


def evaluate_manual_review_requirement(
    *,
    eligible_area_sqm: float | None,
    child_part_bbox_sum_sqm: float | None,
    face_union_bbox_sqm: float | None,
    design_space_union_bbox_sqm: float | None,
    layout_occupied_area_sqm: float | None,
    orphan_defs_split_placement_sqm: float | None,
    orphan_defs_part_count: int,
    operator_manual_footprint_sqm: float | None,
    has_pseudo_or_unlayered_complexity: bool = False,
    filled_area_missing_on_face_layers: bool = False,
) -> tuple[bool, str | None]:
    reasons: list[str] = []
    spread = _candidate_spread(
        eligible_area_sqm=eligible_area_sqm,
        child_part_bbox_sum_sqm=child_part_bbox_sum_sqm,
        face_union_bbox_sqm=face_union_bbox_sqm,
        design_space_union_bbox_sqm=design_space_union_bbox_sqm,
    )
    if spread is not None and spread > SPREAD_MANUAL_REVIEW_THRESHOLD:
        reasons.append(f"candidateSpread={spread:.2f}>{SPREAD_MANUAL_REVIEW_THRESHOLD}")
    if filled_area_missing_on_face_layers:
        reasons.append("face_layer_filled_area_missing")
    if has_pseudo_or_unlayered_complexity:
        reasons.append("pseudo_layer_or_unlayered_complexity")
    if orphan_defs_split_placement_sqm and orphan_defs_split_placement_sqm > 0:
        reasons.append("stale_orphan_defs_split_placement")
    if orphan_defs_part_count > 0:
        reasons.append("orphan_defs_parts_in_analysis")
    layout = _positive(layout_occupied_area_sqm)
    child = _positive(child_part_bbox_sum_sqm)
    if layout and child and layout / child > SHELF_VS_CHILD_REVIEW_THRESHOLD:
        reasons.append(f"layoutOccupied/childPartBBox>{SHELF_VS_CHILD_REVIEW_THRESHOLD}")
    if operator_manual_footprint_sqm and operator_manual_footprint_sqm > 0:
        reasons.append("operator_manual_corel_measurement_present")
    if not reasons:
        return False, None
    return True, "; ".join(reasons)


def operator_override_preview_from_payload(
    sheet_quote_override: dict[str, Any] | None,
) -> SheetQuoteOperatorOverridePreview:
    if not sheet_quote_override:
        return SheetQuoteOperatorOverridePreview(
            enabled=False, width_cm=None, height_cm=None, area_sqm=None, note=None
        )
    width = _positive(sheet_quote_override.get("widthCm") or sheet_quote_override.get("width_cm"))
    height = _positive(sheet_quote_override.get("heightCm") or sheet_quote_override.get("height_cm"))
    area = _positive(sheet_quote_override.get("areaSqm") or sheet_quote_override.get("area_sqm"))
    note = str(sheet_quote_override.get("reason") or "").strip() or None
    return SheetQuoteOperatorOverridePreview(
        enabled=True,
        width_cm=width,
        height_cm=height,
        area_sqm=area,
        note=note,
    )


def build_sheet_quote_candidate_policy_preview(
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    *,
    eligible_area_sqm: float | None,
    placement_footprint_face_sqm: float | None,
    face_union_bbox_sqm: float | None,
    layout_occupied_area_sqm: float | None,
    full_sheet_allocation_sqm: float | None,
    orphan_defs_split_placement_sqm: float | None,
    selected_quote_sheet_area_sqm: float | None,
    selected_quote_sheet_area_source: str | None,
    sheet_quote_override: dict[str, Any] | None = None,
) -> SheetQuoteCandidatePolicyPreview:
    bbox_metrics = compute_sheet_quote_bbox_metrics(analysis, layer_role_setup)
    operator_override = operator_override_preview_from_payload(sheet_quote_override)
    manual_footprint = operator_override.area_sqm

    layers = analysis.get("layers")
    pseudo_layers = 0
    face_filled_missing = False
    if isinstance(layers, list):
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            layer_id = str(layer.get("id") or "")
            if layer_id.startswith("pseudo:") or layer.get("layerKind") == "pseudo":
                pseudo_layers += 1
            layer_name = str(layer.get("name") or layer_id)
            role = _layer_role_for_name(layer_role_setup, layer_id, layer_name)
            if role in SHEET_FACE_ROLES and layer.get("filledAreaSqm") is None:
                face_filled_missing = True

    recommended = compute_recommended_auto_candidate(
        eligible_area_sqm=eligible_area_sqm,
        child_part_bbox_sum_sqm=bbox_metrics.child_part_bbox_sum_sqm,
        face_union_bbox_sqm=face_union_bbox_sqm,
        design_space_union_bbox_sqm=bbox_metrics.design_space_union_bbox_sqm,
    )
    requires_review, review_reason = evaluate_manual_review_requirement(
        eligible_area_sqm=eligible_area_sqm,
        child_part_bbox_sum_sqm=bbox_metrics.child_part_bbox_sum_sqm,
        face_union_bbox_sqm=face_union_bbox_sqm,
        design_space_union_bbox_sqm=bbox_metrics.design_space_union_bbox_sqm,
        layout_occupied_area_sqm=layout_occupied_area_sqm,
        orphan_defs_split_placement_sqm=orphan_defs_split_placement_sqm,
        orphan_defs_part_count=bbox_metrics.orphan_defs_part_count,
        operator_manual_footprint_sqm=manual_footprint,
        has_pseudo_or_unlayered_complexity=pseudo_layers > 0,
        filled_area_missing_on_face_layers=face_filled_missing,
    )

    selection_mode: SelectionMode = "current_floor"
    if operator_override.enabled and sheet_quote_override and sheet_quote_override.get("useForQuoteEstimate"):
        selection_mode = "manual_override_preview"

    selection = SheetQuoteSelectionPreview(
        selected_source=selected_quote_sheet_area_source or "eligible_area_floor",
        final_area_sqm=selected_quote_sheet_area_sqm,
        selection_mode=selection_mode,
        is_applied_to_quote=False,
    )

    _ = placement_footprint_face_sqm
    _ = full_sheet_allocation_sqm

    return SheetQuoteCandidatePolicyPreview(
        bbox_metrics=bbox_metrics,
        recommended_auto_candidate=recommended,
        requires_manual_review=requires_review,
        manual_review_reason=review_reason,
        operator_override=operator_override,
        selection=selection,
    )
