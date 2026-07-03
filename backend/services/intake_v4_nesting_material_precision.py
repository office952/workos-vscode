"""Intake V4 — nesting-based material quantity precision (quote estimate, not stock)."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Literal

BASIS_SHEET_NESTING_ROLE_SPLIT = "sheet_nesting_role_split_quote_estimate"
BASIS_SHEET_NESTING_PART_KIND = "sheet_nesting_part_kind_quote_estimate"
BASIS_SHEET_NESTING_PRORATED_FALLBACK = "sheet_nesting_prorated_fallback"
BASIS_PRINT_AREA = "print_area_quote_estimate"
BASIS_LAMINATE_AREA = "laminate_area_quote_estimate"

CONFIDENCE_NESTING_HIGH = "estimate_from_nesting_high"
CONFIDENCE_NESTING_MEDIUM = "estimate_from_nesting_medium"
CONFIDENCE_AREA_FALLBACK = "estimate_fallback_area"
CONFIDENCE_PERIMETER = "estimate_fallback_perimeter"
CONFIDENCE_FORMULA = "estimate_formula"
CONFIDENCE_MISSING_METADATA = "estimate_missing_metadata"

ORPHAN_UNASSIGNED_SPLIT_PART_RE = re.compile(r"^split_layer_\d+_\d+$")

SHEET_FACE_ROLES = frozenset({"face"})
SHEET_BACKING_ROLES = frozenset({"backing", "support_panel"})
SHEET_EXCLUDED_ROLES = frozenset({"printed_artwork", "ignored", "artwork"})
DERIVED_FACE_KINDS = frozenset({"relief-insert", "diffuser-plate"})
DERIVED_BACKING_KINDS = frozenset({"back-cover-plate", "wall-strip-plate"})

SheetSplitMode = Literal[
    "role_split",
    "part_kind",
    "partial_role_split",
    "prorated_fallback",
    "single_face",
    "single_backing",
    "none",
]


@dataclass(frozen=True)
class SheetNestingMaterialSplit:
    face_area_sqm: float | None
    backing_area_sqm: float | None
    config_id: str | None
    fully_valid: bool
    mode: SheetSplitMode
    quantity_basis: str
    confidence: str
    classified_placements: int = 0
    unclassified_placements: int = 0
    used_sheet_area_sqm: float | None = None


@dataclass(frozen=True)
class SheetQuoteRecommendedAutoCandidate:
    source: str
    area_sqm: float | None
    buffer_percent: float
    confidence: str
    reason: str


@dataclass(frozen=True)
class SheetQuoteSelectionPreview:
    selected_source: str
    final_area_sqm: float | None
    selection_mode: str
    is_applied_to_quote: bool


@dataclass(frozen=True)
class SheetQuoteOperatorOverridePreview:
    enabled: bool
    width_cm: float | None
    height_cm: float | None
    area_sqm: float | None
    note: str | None


@dataclass(frozen=True)
class SheetQuoteMaterialCandidates:
    eligible_face_area_sqm: float | None
    placement_footprint_face_sqm: float | None
    face_union_bbox_sqm: float | None
    layout_occupied_area_sqm: float | None
    full_sheet_allocation_sqm: float | None
    unknown_placement_sqm: float | None
    orphan_defs_split_placement_sqm: float | None
    operator_manual_footprint_sqm: float | None
    operator_manual_footprint_width_cm: float | None
    operator_manual_footprint_height_cm: float | None
    operator_manual_use_for_quote_estimate: bool
    selected_quote_sheet_area_sqm: float | None
    selected_quote_sheet_area_source: str
    child_part_bbox_sum_sqm: float | None = None
    semantic_group_bbox_sum_sqm: float | None = None
    design_space_union_bbox_sqm: float | None = None
    design_space_union_bbox_with_buffer_sqm: float | None = None
    nesting_shelf_occupied_sqm: float | None = None
    recommended_auto_candidate: SheetQuoteRecommendedAutoCandidate | None = None
    requires_manual_review: bool = False
    manual_review_reason: str | None = None
    operator_override: SheetQuoteOperatorOverridePreview | None = None
    selection: SheetQuoteSelectionPreview | None = None


@dataclass(frozen=True)
class RollNestingVinylEstimate:
    area_sqm: float | None
    fully_valid: bool
    job_count: int
    color_keys: frozenset[str]


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _is_orphan_unassigned_split_part(part_id: str, part_meta: dict[str, Any] | None) -> bool:
    """Unassigned split_layer_N_M parts from defs/clipPath geometry (no layer metadata)."""
    if part_meta and (part_meta.get("layer_name") or part_meta.get("layer_id")):
        return False
    return bool(ORPHAN_UNASSIGNED_SPLIT_PART_RE.match(part_id))


def _placement_sheet_quote_bucket(
    placement: dict[str, Any],
    *,
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    parts_index: dict[str, dict[str, Any]],
    part_class_index: dict[str, dict[str, Any]],
    backing_confirmed: bool,
) -> Literal["face", "backing", "artwork", "orphan_defs", "hole", "unknown"]:
    part_id = str(placement.get("partId") or "")
    part_class = part_class_index.get(part_id)
    if part_class and part_class.get("is_inner_hole"):
        return "hole"
    part_meta = parts_index.get(part_id)
    if _is_orphan_unassigned_split_part(part_id, part_meta):
        return "orphan_defs"
    layer_name = str(placement.get("sourceLayerName") or "")
    if part_meta and part_meta.get("layer_name"):
        layer_name = str(part_meta.get("layer_name"))
    layer_id = str((part_meta or {}).get("layer_id") or layer_name)
    layer_role = _layer_role_for_name(layer_role_setup, layer_id, layer_name)
    if layer_role in SHEET_EXCLUDED_ROLES:
        return "artwork"
    intent = classify_sheet_material_intent(part_meta=part_meta, layer_role=layer_role)
    if intent == "backing" and not backing_confirmed:
        return "unknown"
    if intent == "face":
        return "face"
    if intent == "backing":
        return "backing"
    return "unknown"


def _face_union_bbox_sqm(placements: list[dict[str, Any]]) -> float | None:
    xs: list[float] = []
    ys: list[float] = []
    x2: list[float] = []
    y2: list[float] = []
    for placement in placements:
        x = _positive(placement.get("xMm"))
        y = _positive(placement.get("yMm"))
        w = _positive(placement.get("placedWidthMm"))
        h = _positive(placement.get("placedHeightMm"))
        if x is None or y is None or w is None or h is None:
            continue
        xs.append(x)
        ys.append(y)
        x2.append(x + w)
        y2.append(y + h)
    if not xs:
        return None
    return round((max(x2) - min(xs)) * (max(y2) - min(ys)) / 1_000_000.0, 4)


def compute_sheet_quote_material_candidates(
    nesting: dict[str, Any] | None,
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    *,
    eligible_face_area_sqm: float | None,
    sheet_split_pre_floor: SheetNestingMaterialSplit,
    selected_quote_sheet_area_sqm: float | None,
    sheet_quantity_floor_applied: bool,
    sheet_quote_override: dict[str, Any] | None = None,
) -> SheetQuoteMaterialCandidates | None:
    sheet, _, _ = resolve_active_sheet_layout(nesting)
    if sheet is None:
        return None

    parts_index = _build_parts_metadata_index(analysis)
    part_class_index = _part_classification_index(analysis, layer_role_setup)
    backing_confirmed = backing_layer_confirmed(layer_role_setup)
    placements = [p for p in (sheet.get("placements") or []) if isinstance(p, dict)]

    unknown_sqm = 0.0
    orphan_sqm = 0.0
    face_placements: list[dict[str, Any]] = []
    for placement in placements:
        area = _placement_area_sqm(placement)
        if area <= 0:
            continue
        bucket = _placement_sheet_quote_bucket(
            placement,
            analysis=analysis,
            layer_role_setup=layer_role_setup,
            parts_index=parts_index,
            part_class_index=part_class_index,
            backing_confirmed=backing_confirmed,
        )
        if bucket == "face":
            face_placements.append(placement)
        elif bucket == "orphan_defs":
            orphan_sqm += area
        elif bucket == "unknown":
            unknown_sqm += area

    used_width = _positive(sheet.get("usedWidthMm"))
    consumed_length = _positive(sheet.get("consumedLengthMm"))
    layout_occupied = (
        round((used_width * consumed_length) / 1_000_000.0, 4)
        if used_width and consumed_length
        else None
    )

    from services.intake_v4_sheet_footprint_override_service import (
        SheetFootprintCandidateAreas,
        resolve_sheet_quote_selection_with_override,
    )

    override_width = _positive((sheet_quote_override or {}).get("widthCm"))
    override_height = _positive((sheet_quote_override or {}).get("heightCm"))
    manual_sqm_pre = None
    if override_width and override_height:
        from services.intake_v4_sheet_footprint_override_service import compute_operator_manual_footprint_sqm

        manual_sqm_pre = compute_operator_manual_footprint_sqm(override_width, override_height)

    candidate_areas = SheetFootprintCandidateAreas(
        eligible_face_area_sqm=_positive(eligible_face_area_sqm),
        placement_footprint_face_sqm=sheet_split_pre_floor.face_area_sqm,
        face_union_bbox_sqm=_face_union_bbox_sqm(face_placements),
        layout_occupied_area_sqm=layout_occupied,
        full_sheet_allocation_sqm=_positive(sheet.get("usedSheetAreaSqm")),
        operator_manual_footprint_sqm=manual_sqm_pre,
    )

    selected_sqm, selected_source, manual_sqm = resolve_sheet_quote_selection_with_override(
        eligible_face_area_sqm=eligible_face_area_sqm,
        base_selected_sqm=selected_quote_sheet_area_sqm,
        sheet_quantity_floor_applied=sheet_quantity_floor_applied,
        override=sheet_quote_override,
        candidate_areas=candidate_areas,
    )
    use_for_estimate = bool((sheet_quote_override or {}).get("useForQuoteEstimate"))

    from services.intake_v4_sheet_quote_candidate_policy_service import build_sheet_quote_candidate_policy_preview

    policy = build_sheet_quote_candidate_policy_preview(
        analysis,
        layer_role_setup,
        eligible_area_sqm=_positive(eligible_face_area_sqm),
        placement_footprint_face_sqm=sheet_split_pre_floor.face_area_sqm,
        face_union_bbox_sqm=_face_union_bbox_sqm(face_placements),
        layout_occupied_area_sqm=layout_occupied,
        full_sheet_allocation_sqm=_positive(sheet.get("usedSheetAreaSqm")),
        orphan_defs_split_placement_sqm=round(orphan_sqm, 4) if orphan_sqm > 0 else None,
        selected_quote_sheet_area_sqm=selected_sqm,
        selected_quote_sheet_area_source=selected_source,
        sheet_quote_override=sheet_quote_override,
    )

    return SheetQuoteMaterialCandidates(
        eligible_face_area_sqm=_positive(eligible_face_area_sqm),
        placement_footprint_face_sqm=sheet_split_pre_floor.face_area_sqm,
        face_union_bbox_sqm=_face_union_bbox_sqm(face_placements),
        layout_occupied_area_sqm=layout_occupied,
        full_sheet_allocation_sqm=_positive(sheet.get("usedSheetAreaSqm")),
        unknown_placement_sqm=round(unknown_sqm, 4) if unknown_sqm > 0 else None,
        orphan_defs_split_placement_sqm=round(orphan_sqm, 4) if orphan_sqm > 0 else None,
        operator_manual_footprint_sqm=manual_sqm,
        operator_manual_footprint_width_cm=override_width,
        operator_manual_footprint_height_cm=override_height,
        operator_manual_use_for_quote_estimate=use_for_estimate,
        selected_quote_sheet_area_sqm=selected_sqm,
        selected_quote_sheet_area_source=selected_source,
        child_part_bbox_sum_sqm=policy.bbox_metrics.child_part_bbox_sum_sqm,
        semantic_group_bbox_sum_sqm=policy.bbox_metrics.semantic_group_bbox_sum_sqm,
        design_space_union_bbox_sqm=policy.bbox_metrics.design_space_union_bbox_sqm,
        design_space_union_bbox_with_buffer_sqm=policy.bbox_metrics.design_space_union_bbox_with_buffer_sqm,
        nesting_shelf_occupied_sqm=layout_occupied,
        recommended_auto_candidate=policy.recommended_auto_candidate,
        requires_manual_review=policy.requires_manual_review,
        manual_review_reason=policy.manual_review_reason,
        operator_override=policy.operator_override,
        selection=policy.selection,
    )


def _placement_area_sqm(placement: dict[str, Any]) -> float:
    width = _positive(placement.get("placedWidthMm"))
    height = _positive(placement.get("placedHeightMm"))
    if width is None or height is None:
        return 0.0
    return (width * height) / 1_000_000.0


def _build_parts_metadata_index(analysis: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parts_block = analysis.get("parts")
    items: list[Any] = []
    if isinstance(parts_block, dict):
        raw_items = parts_block.get("items")
        if isinstance(raw_items, list):
            items = raw_items
    elif isinstance(parts_block, list):
        items = parts_block

    index: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        part_id = str(item.get("id") or "")
        if not part_id:
            continue
        source = item.get("source") if isinstance(item.get("source"), dict) else {}
        index[part_id] = {
            "layer_id": str(source.get("layerId") or ""),
            "layer_name": str(source.get("layerName") or ""),
            "derived_part_kind": str(item.get("derivedPartKind") or "").strip() or None,
            "material_label": str(item.get("materialLabel") or "").strip() or None,
        }
        base_id = part_id.rsplit("_q", 1)[0]
        if base_id != part_id and base_id not in index:
            index[base_id] = index[part_id]
    return index


def backing_layer_confirmed(layer_role_setup: dict[str, Any] | None) -> bool:
    """True when operator confirmed at least one layer with backing role."""
    if not isinstance(layer_role_setup, dict):
        return False
    layers = layer_role_setup.get("layers")
    if not isinstance(layers, list):
        return False
    for entry in layers:
        if not isinstance(entry, dict):
            continue
        role = str(entry.get("confirmed_role") or "").strip().lower()
        state = str(entry.get("confirmation_state") or "").strip().lower()
        if role == "backing" and state == "confirmed":
            return True
    return False


def _part_classification_index(
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if not analysis or not isinstance(layer_role_setup, dict):
        return {}
    try:
        from services.intake_v4_letter_part_classification_service import classify_letter_parts_from_analysis

        result = classify_letter_parts_from_analysis(analysis, layer_role_setup)
    except Exception:
        return {}
    return {
        str(row.get("part_id") or ""): row
        for row in (result.get("parts") or [])
        if isinstance(row, dict) and row.get("part_id")
    }


def _layer_role_for_name(
    layer_role_setup: dict[str, Any] | None,
    layer_id: str,
    layer_name: str,
) -> str | None:
    if not isinstance(layer_role_setup, dict):
        return None
    layers = layer_role_setup.get("layers")
    if not isinstance(layers, list):
        return None
    for entry in layers:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("layer_key") or "")
        lid = str(entry.get("layer_id") or "")
        lname = str(entry.get("layer_name") or "")
        if key not in {layer_id, layer_name} and lid != layer_id and lname != layer_name:
            continue
        if entry.get("confirmation_state") == "ignored":
            return None
        role = str(entry.get("confirmed_role") or entry.get("auto_role") or "").strip().lower()
        return role or None
    return None


def classify_sheet_material_intent(
    *,
    part_meta: dict[str, Any] | None,
    layer_role: str | None,
) -> Literal["face", "backing"] | None:
    kind = (part_meta or {}).get("derived_part_kind")
    if kind in DERIVED_BACKING_KINDS:
        return "backing"
    if kind in DERIVED_FACE_KINDS:
        return "face"

    role = (layer_role or "").strip().lower()
    if role in SHEET_BACKING_ROLES:
        return "backing"
    if role in SHEET_FACE_ROLES:
        return "face"

    label = str((part_meta or {}).get("material_label") or "").lower()
    if any(token in label for token in ("forex", "capac spate", "pereti", "backing")):
        return "backing"
    if any(token in label for token in ("plexiglas", "difuzor", "față", "fata", "face")):
        return "face"
    return None


def _pick_best_sheet_layout(nesting: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str | None, bool]:
    if not isinstance(nesting, dict):
        return None, None, False
    best_sheet: dict[str, Any] | None = None
    best_score: tuple[float, float] | None = None
    best_config: str | None = None
    fully_valid = True
    for sheet in nesting.get("sheets") or []:
        if not isinstance(sheet, dict):
            continue
        sheets_used = int(sheet.get("sheetsUsed") or 0)
        if sheets_used <= 0:
            continue
        placed = sheet.get("placedItemsCount")
        if placed is not None and int(placed) <= 0:
            continue
        used_area = _positive(sheet.get("usedSheetAreaSqm"))
        if used_area is None:
            continue
        if int(sheet.get("unplacedItemsCount") or 0) > 0:
            fully_valid = False
        efficiency = _positive(sheet.get("efficiencyPercent"))
        eff_score = efficiency if efficiency is not None else 0.0
        # Prefer highest nesting efficiency; tie-break by lowest consumed sheet area.
        score = (eff_score, -used_area)
        if best_score is None or score > best_score:
            best_score = score
            best_config = str(sheet.get("configId") or "sheet")
            best_sheet = sheet
    return best_sheet, best_config, fully_valid


def resolve_active_sheet_layout(
    nesting: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, str | None, bool]:
    """Sheet layout selected for material breakdown (highest efficiency among placed layouts)."""
    return _pick_best_sheet_layout(nesting)


def compute_eligible_sheet_face_area_sum_sqm(
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    *,
    letter_groups: list[Any] | None = None,
    artwork_finishes: list[Any] | None = None,
) -> float | None:
    """Sum eligible volumetric face area (m²) for sheet-material quantity floor.

    Prefers persisted ``letter_group_finishes.face_area_m2`` for non-artwork layers,
    then face-role layer ``filledAreaSqm`` from analysis. Excludes printed artwork.
    """
    artwork_layer_keys = {
        str(row.get("layer_key") or "")
        for row in (artwork_finishes or [])
        if isinstance(row, dict) and row.get("layer_key")
    }
    total = 0.0
    found = False
    if letter_groups:
        for group in letter_groups:
            if not isinstance(group, dict):
                continue
            layer_key = str(group.get("group_key") or group.get("layer_key") or "")
            layer_name = str(group.get("layer_name") or layer_key)
            if layer_key in artwork_layer_keys:
                continue
            role = _layer_role_for_name(layer_role_setup, layer_key, layer_name)
            if role in SHEET_EXCLUDED_ROLES:
                continue
            area = _positive(group.get("face_area_m2"))
            if area:
                total += area
                found = True
        if found and total > 0:
            return round(total, 4)

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
                total += area
                found = True
        if found and total > 0:
            return round(total, 4)
    return None


def apply_sheet_material_quantity_floor(
    split: SheetNestingMaterialSplit,
    *,
    eligible_face_area_sqm: float | None,
) -> tuple[SheetNestingMaterialSplit, bool]:
    """Raise sheet face/backing quote quantities to at least eligible part area sum.

    Nesting placement footprints may be smaller than true filled areas when parts are
  split or rotated; sheet material estimates must not undercount below eligible area.
    """
    floor = _positive(eligible_face_area_sqm)
    if floor is None:
        return split, False

    face_qty = split.face_area_sqm
    backing_qty = split.backing_area_sqm
    floored = False

    if face_qty is not None and face_qty + 1e-9 < floor:
        face_qty = round(floor, 4)
        floored = True

    if not floored:
        return split, False

    return (
        SheetNestingMaterialSplit(
            face_area_sqm=face_qty,
            backing_area_sqm=backing_qty,
            config_id=split.config_id,
            fully_valid=split.fully_valid,
            mode=split.mode,
            quantity_basis=split.quantity_basis,
            confidence=split.confidence,
            classified_placements=split.classified_placements,
            unclassified_placements=split.unclassified_placements,
            used_sheet_area_sqm=split.used_sheet_area_sqm,
        ),
        True,
    )


def _allocate_prorated_sheet_area(
    sheet_area_sqm: float,
    face_area: float | None,
    backing_area: float | None,
) -> tuple[float | None, float | None]:
    face = _positive(face_area)
    backing = _positive(backing_area)
    if face and backing:
        denom = face + backing
        if denom <= 0:
            return None, None
        return round(sheet_area_sqm * face / denom, 4), round(sheet_area_sqm * backing / denom, 4)
    if face:
        return round(sheet_area_sqm, 4), None
    if backing:
        return None, round(sheet_area_sqm, 4)
    return round(sheet_area_sqm, 4), None


def compute_sheet_nesting_material_split(
    nesting: dict[str, Any] | None,
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    *,
    face_area: float | None,
    backing_area: float | None,
) -> SheetNestingMaterialSplit:
    sheet, config_id, fully_valid = _pick_best_sheet_layout(nesting)
    if sheet is None:
        return SheetNestingMaterialSplit(
            face_area_sqm=None,
            backing_area_sqm=None,
            config_id=None,
            fully_valid=False,
            mode="none",
            quantity_basis=BASIS_SHEET_NESTING_PRORATED_FALLBACK,
            confidence=CONFIDENCE_MISSING_METADATA,
        )

    used_sheet = _positive(sheet.get("usedSheetAreaSqm"))
    if used_sheet is None:
        return SheetNestingMaterialSplit(
            face_area_sqm=None,
            backing_area_sqm=None,
            config_id=config_id,
            fully_valid=False,
            mode="none",
            quantity_basis=BASIS_SHEET_NESTING_PRORATED_FALLBACK,
            confidence=CONFIDENCE_MISSING_METADATA,
        )

    parts_index = _build_parts_metadata_index(analysis)
    part_class_index = _part_classification_index(analysis, layer_role_setup)
    backing_confirmed = backing_layer_confirmed(layer_role_setup)
    placements = [p for p in (sheet.get("placements") or []) if isinstance(p, dict)]

    face_pl = 0.0
    backing_pl = 0.0
    unknown_pl = 0.0
    classified = 0
    unclassified = 0
    used_part_kind_only = False

    for placement in placements:
        area = _placement_area_sqm(placement)
        if area <= 0:
            continue
        part_id = str(placement.get("partId") or "")
        part_class = part_class_index.get(part_id)
        if part_class and part_class.get("is_inner_hole"):
            continue
        part_meta = parts_index.get(part_id)
        if _is_orphan_unassigned_split_part(part_id, part_meta):
            continue
        layer_name = str(placement.get("sourceLayerName") or "")
        if part_meta and part_meta.get("layer_name"):
            layer_name = str(part_meta.get("layer_name"))
        layer_id = str((part_meta or {}).get("layer_id") or layer_name)
        layer_role = _layer_role_for_name(layer_role_setup, layer_id, layer_name)
        if layer_role in SHEET_EXCLUDED_ROLES:
            continue
        intent = classify_sheet_material_intent(part_meta=part_meta, layer_role=layer_role)
        if intent == "backing" and not backing_confirmed:
            continue
        if intent == "face":
            face_pl += area
            classified += 1
            if part_meta and part_meta.get("derived_part_kind") in DERIVED_FACE_KINDS:
                used_part_kind_only = True
        elif intent == "backing":
            backing_pl += area
            classified += 1
            if part_meta and part_meta.get("derived_part_kind") in DERIVED_BACKING_KINDS:
                used_part_kind_only = True
        else:
            unknown_pl += area
            unclassified += 1

    total_pl = face_pl + backing_pl + unknown_pl
    confidence = CONFIDENCE_NESTING_HIGH if fully_valid else CONFIDENCE_NESTING_MEDIUM

    if total_pl <= 0:
        face_qty, backing_qty = _allocate_prorated_sheet_area(used_sheet, face_area, backing_area)
        return SheetNestingMaterialSplit(
            face_area_sqm=face_qty,
            backing_area_sqm=backing_qty,
            config_id=config_id,
            fully_valid=fully_valid,
            mode="prorated_fallback",
            quantity_basis=BASIS_SHEET_NESTING_PRORATED_FALLBACK,
            confidence=CONFIDENCE_NESTING_MEDIUM,
            used_sheet_area_sqm=used_sheet,
        )

    if unknown_pl <= 0 and face_pl > 0 and backing_pl > 0:
        basis = BASIS_SHEET_NESTING_PART_KIND if used_part_kind_only else BASIS_SHEET_NESTING_ROLE_SPLIT
        return SheetNestingMaterialSplit(
            face_area_sqm=round(face_pl, 4),
            backing_area_sqm=round(backing_pl, 4),
            config_id=config_id,
            fully_valid=fully_valid,
            mode="part_kind" if used_part_kind_only else "role_split",
            quantity_basis=basis,
            confidence=confidence,
            classified_placements=classified,
            unclassified_placements=0,
            used_sheet_area_sqm=used_sheet,
        )

    if (face_pl > 0 or backing_pl > 0) and unknown_pl > 0:
        geom_face = _positive(face_area)
        geom_backing = _positive(backing_area)
        if geom_face and geom_backing:
            geom_denom = geom_face + geom_backing
            face_effective = face_pl + unknown_pl * (geom_face / geom_denom)
            backing_effective = backing_pl + unknown_pl * (geom_backing / geom_denom)
            return SheetNestingMaterialSplit(
                face_area_sqm=round(face_effective, 4),
                backing_area_sqm=round(backing_effective, 4),
                config_id=config_id,
                fully_valid=fully_valid,
                mode="partial_role_split",
                quantity_basis=BASIS_SHEET_NESTING_ROLE_SPLIT,
                confidence=CONFIDENCE_NESTING_MEDIUM,
                classified_placements=classified,
                unclassified_placements=unclassified,
                used_sheet_area_sqm=used_sheet,
            )

    if face_pl > 0 and backing_pl <= 0:
        return SheetNestingMaterialSplit(
            face_area_sqm=round(face_pl, 4),
            backing_area_sqm=None,
            config_id=config_id,
            fully_valid=fully_valid,
            mode="single_face",
            quantity_basis=BASIS_SHEET_NESTING_ROLE_SPLIT,
            confidence=confidence,
            classified_placements=classified,
            unclassified_placements=unclassified,
            used_sheet_area_sqm=used_sheet,
        )

    if backing_pl > 0 and face_pl <= 0:
        return SheetNestingMaterialSplit(
            face_area_sqm=None,
            backing_area_sqm=round(backing_pl, 4),
            config_id=config_id,
            fully_valid=fully_valid,
            mode="single_backing",
            quantity_basis=BASIS_SHEET_NESTING_ROLE_SPLIT,
            confidence=confidence,
            classified_placements=classified,
            unclassified_placements=unclassified,
            used_sheet_area_sqm=used_sheet,
        )

    face_qty, backing_qty = _allocate_prorated_sheet_area(used_sheet, face_area, backing_area)
    return SheetNestingMaterialSplit(
        face_area_sqm=face_qty,
        backing_area_sqm=backing_qty,
        config_id=config_id,
        fully_valid=fully_valid,
        mode="prorated_fallback",
        quantity_basis=BASIS_SHEET_NESTING_PRORATED_FALLBACK,
        confidence=CONFIDENCE_NESTING_MEDIUM,
        unclassified_placements=unclassified,
        used_sheet_area_sqm=used_sheet,
    )


def _roll_job_layer_role(
    job: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
) -> str | None:
    layer_name = str(job.get("sourceLayerName") or "")
    if not layer_name:
        return None
    return _layer_role_for_name(layer_role_setup, layer_name, layer_name)


def _roll_nesting_vinyl_best_jobs(
    nesting: dict[str, Any] | None,
    *,
    layer_role_setup: dict[str, Any] | None = None,
) -> dict[tuple[str, str], tuple[float, bool]]:
    """Best roll area per (source layer, color) across alternative roll widths."""
    if not isinstance(nesting, dict):
        return {}
    best_by_job: dict[tuple[str, str], tuple[float, bool]] = {}
    for roll in nesting.get("rolls") or []:
        if not isinstance(roll, dict):
            continue
        roll_width_mm = _positive(roll.get("rollWidthMm"))
        for job in roll.get("jobs") or []:
            if not isinstance(job, dict):
                continue
            placed = int(job.get("placedItemsCount") or 0)
            if job.get("placedItemsCount") is not None and placed <= 0:
                continue
            layer_name = str(job.get("sourceLayerName") or "")
            layer_role = _roll_job_layer_role(job, layer_role_setup)
            if layer_role in SHEET_EXCLUDED_ROLES:
                continue
            if layer_role is not None and layer_role not in SHEET_FACE_ROLES:
                continue
            area = _positive(job.get("usedRollAreaSqm"))
            if area is None:
                consumed_mm = _positive(job.get("consumedLengthMm"))
                if consumed_mm and roll_width_mm:
                    area = (roll_width_mm * consumed_mm) / 1_000_000.0
            if area is None:
                continue
            job_valid = int(job.get("unplacedItemsCount") or 0) == 0
            color = str(job.get("colorKey") or layer_name or "roll")
            key = (layer_name, color)
            prev = best_by_job.get(key)
            if prev is None or area < prev[0]:
                best_by_job[key] = (area, job_valid)
    return best_by_job


def compute_roll_nesting_vinyl_estimate(
    nesting: dict[str, Any] | None,
    *,
    layer_role_setup: dict[str, Any] | None = None,
) -> RollNestingVinylEstimate:
    best_by_job = _roll_nesting_vinyl_best_jobs(nesting, layer_role_setup=layer_role_setup)
    if not best_by_job:
        return RollNestingVinylEstimate(None, False, 0, frozenset())

    color_keys = frozenset(
        color for (_, color) in best_by_job.keys()
    )
    total = round(sum(area for area, _ in best_by_job.values()), 4)
    fully_valid = all(valid for _, valid in best_by_job.values())
    return RollNestingVinylEstimate(
        total,
        fully_valid,
        len(best_by_job),
        color_keys,
    )


def compute_roll_nesting_vinyl_area_by_layer(
    nesting: dict[str, Any] | None,
    *,
    layer_role_setup: dict[str, Any] | None = None,
) -> dict[str, float]:
    """Quote roll vinyl area (m²) attributed to each source layer name."""
    best_by_job = _roll_nesting_vinyl_best_jobs(nesting, layer_role_setup=layer_role_setup)
    if not best_by_job:
        return {}
    per_layer: dict[str, float] = defaultdict(float)
    for (layer_name, _), (area, _) in best_by_job.items():
        if not layer_name:
            continue
        per_layer[layer_name] += area
    return {layer: round(total, 4) for layer, total in per_layer.items()}
