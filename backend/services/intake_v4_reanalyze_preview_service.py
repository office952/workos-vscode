"""Intake V4 re-analyze preview — read-only before/after diff (no persistence)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.intake_v4_nesting_material_precision import (
    SheetNestingMaterialSplit,
    compute_eligible_sheet_face_area_sum_sqm,
    compute_sheet_nesting_material_split,
    compute_sheet_quote_material_candidates,
    resolve_active_sheet_layout,
    _build_parts_metadata_index,
    _part_classification_index,
    _placement_sheet_quote_bucket,
    backing_layer_confirmed,
)


@dataclass(frozen=True)
class ReanalyzePreviewSnapshot:
    orphan_defs_split_placement_sqm: float | None
    placements_count: int
    layout_occupied_sqm: float | None
    face_union_bbox_sqm: float | None
    selected_quantity_sqm: float | None
    requires_manual_review: bool
    manual_review_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _count_face_placements(
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    nesting: dict[str, Any] | None,
) -> int:
    sheet, _, _ = resolve_active_sheet_layout(nesting)
    if sheet is None:
        return 0
    parts_index = _build_parts_metadata_index(analysis)
    part_class_index = _part_classification_index(analysis, layer_role_setup)
    backing_confirmed = backing_layer_confirmed(layer_role_setup)
    count = 0
    for placement in sheet.get("placements") or []:
        if not isinstance(placement, dict):
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
            count += 1
    return count


def build_reanalyze_preview_snapshot(
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    *,
    sheet_quote_override: dict[str, Any] | None = None,
) -> ReanalyzePreviewSnapshot | None:
    if not isinstance(analysis, dict):
        return None
    nesting = analysis.get("nesting") if isinstance(analysis.get("nesting"), dict) else {}
    eligible_face_area_sum = compute_eligible_sheet_face_area_sum_sqm(analysis, layer_role_setup)
    sheet_split = compute_sheet_nesting_material_split(
        nesting,
        analysis,
        layer_role_setup,
        face_area=eligible_face_area_sum,
        backing_area=None,
    )
    if sheet_split is None:
        return None

    selected_sqm = eligible_face_area_sum if sheet_split.fully_valid else sheet_split.face_area_sqm
    floor_applied = bool(
        eligible_face_area_sum is not None
        and sheet_split.face_area_sqm is not None
        and eligible_face_area_sum > (sheet_split.face_area_sqm or 0) + 1e-9
    )
    candidates = compute_sheet_quote_material_candidates(
        nesting,
        analysis,
        layer_role_setup,
        eligible_face_area_sqm=eligible_face_area_sum,
        sheet_split_pre_floor=sheet_split,
        selected_quote_sheet_area_sqm=selected_sqm,
        sheet_quantity_floor_applied=floor_applied,
        sheet_quote_override=sheet_quote_override,
    )
    if candidates is None:
        return None

    return ReanalyzePreviewSnapshot(
        orphan_defs_split_placement_sqm=candidates.orphan_defs_split_placement_sqm,
        placements_count=_count_face_placements(analysis, layer_role_setup, nesting),
        layout_occupied_sqm=candidates.layout_occupied_area_sqm,
        face_union_bbox_sqm=candidates.face_union_bbox_sqm,
        selected_quantity_sqm=candidates.selected_quote_sheet_area_sqm,
        requires_manual_review=candidates.requires_manual_review,
        manual_review_reason=candidates.manual_review_reason,
    )


def compare_reanalyze_preview(
    *,
    persisted_analysis: dict[str, Any],
    fresh_analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    sheet_quote_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    before = build_reanalyze_preview_snapshot(
        persisted_analysis,
        layer_role_setup,
        sheet_quote_override=sheet_quote_override,
    )
    after = build_reanalyze_preview_snapshot(
        fresh_analysis,
        layer_role_setup,
        sheet_quote_override=sheet_quote_override,
    )
    if before is None or after is None:
        return {
            "before": before.to_dict() if before else None,
            "after": after.to_dict() if after else None,
            "selected_quantity_unchanged": False,
            "persists_changes": False,
            "stale_snapshot_detected": False,
            "preview_available": False,
        }

    stale = bool(
        (before.orphan_defs_split_placement_sqm or 0) > 0
        or (before.manual_review_reason or "").find("orphan_defs") >= 0
        or (before.manual_review_reason or "").find("stale_orphan") >= 0
    )
    return {
        "before": before.to_dict(),
        "after": after.to_dict(),
        "selected_quantity_unchanged": before.selected_quantity_sqm == after.selected_quantity_sqm,
        "persists_changes": False,
        "stale_snapshot_detected": stale,
        "preview_available": True,
    }
