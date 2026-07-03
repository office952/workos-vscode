"""Intake V4 sheet quote candidate policy foundation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.intake_v4_nesting_material_precision import (
    SheetNestingMaterialSplit,
    compute_sheet_quote_material_candidates,
)
from services.intake_v4_sheet_quote_candidate_policy_service import (
    DEFAULT_BUFFER_PERCENT,
    compute_recommended_auto_candidate,
    compute_sheet_quote_bbox_metrics,
    evaluate_manual_review_requirement,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "intake_v4"
PBL_GOLDEN = FIXTURES / "pbl_layere_golden_analysis.json"


def _pbl_layer_roles() -> dict:
    return {
        "layers": [
            {"layer_key": "Layer_x0020_1", "layer_name": "Layer_x0020_1", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
            {"layer_key": "Layer_x0020_2", "layer_name": "Layer_x0020_2", "confirmed_role": "face", "confirmation_state": "confirmed"},
            {"layer_key": "Layer_x0020_3", "layer_name": "Layer_x0020_3", "confirmed_role": "face", "confirmation_state": "confirmed"},
        ]
    }


def _empty_sheet_split() -> SheetNestingMaterialSplit:
    return SheetNestingMaterialSplit(
        face_area_sqm=0.5834,
        backing_area_sqm=None,
        config_id="sheet_3000x2000",
        fully_valid=True,
        mode="role_split",
        quantity_basis="sheet_nesting_role_split_quote_estimate",
        confidence="estimate_from_nesting_high",
    )


def _load_pbl_analysis() -> dict:
    return json.loads(PBL_GOLDEN.read_text(encoding="utf-8"))


def test_child_part_bbox_sum_appears_in_sheet_quote_material_candidates():
    analysis = _load_pbl_analysis()
    nesting = analysis.get("nesting") or {}
    candidates = compute_sheet_quote_material_candidates(
        nesting,
        analysis,
        _pbl_layer_roles(),
        eligible_face_area_sqm=0.6907,
        sheet_split_pre_floor=_empty_sheet_split(),
        selected_quote_sheet_area_sqm=0.6907,
        sheet_quantity_floor_applied=True,
    )
    assert candidates is not None
    assert candidates.child_part_bbox_sum_sqm is not None
    assert candidates.child_part_bbox_sum_sqm > 0
    assert candidates.semantic_group_bbox_sum_sqm is not None
    assert candidates.design_space_union_bbox_sqm is not None
    assert candidates.recommended_auto_candidate is not None
    assert candidates.selection is not None
    assert candidates.selection.is_applied_to_quote is False


def test_recommended_auto_candidate_uses_max_eligible_and_child_buffer():
    recommended = compute_recommended_auto_candidate(
        eligible_area_sqm=0.6907,
        child_part_bbox_sum_sqm=0.5834,
        face_union_bbox_sqm=1.1577,
        design_space_union_bbox_sqm=1.6607,
        buffer_percent=5.0,
    )
    assert recommended.buffer_percent == 5.0
    assert recommended.area_sqm == pytest.approx(max(0.6907, 0.5834 * 1.05), abs=0.0002)
    assert recommended.source == "child_part_bbox_sum_with_buffer"


def test_buffer_is_not_twenty_percent_default():
    recommended = compute_recommended_auto_candidate(
        eligible_area_sqm=1.0,
        child_part_bbox_sum_sqm=1.0,
        face_union_bbox_sqm=1.2,
        design_space_union_bbox_sqm=1.1,
    )
    assert recommended.buffer_percent == DEFAULT_BUFFER_PERCENT
    assert recommended.buffer_percent != 20.0
    assert recommended.area_sqm == pytest.approx(1.05, abs=0.0001)


def test_requires_manual_review_when_spread_above_threshold():
    requires, reason = evaluate_manual_review_requirement(
        eligible_area_sqm=1.2638,
        child_part_bbox_sum_sqm=1.1469,
        face_union_bbox_sqm=2.5238,
        design_space_union_bbox_sqm=2.1839,
        layout_occupied_area_sqm=2.5238,
        orphan_defs_split_placement_sqm=None,
        orphan_defs_part_count=0,
        operator_manual_footprint_sqm=None,
    )
    assert requires is True
    assert reason is not None
    assert "candidateSpread" in reason


def test_selection_remains_eligible_area_floor_preview_only():
    analysis = _load_pbl_analysis()
    candidates = compute_sheet_quote_material_candidates(
        analysis.get("nesting") or {},
        analysis,
        _pbl_layer_roles(),
        eligible_face_area_sqm=0.6907,
        sheet_split_pre_floor=_empty_sheet_split(),
        selected_quote_sheet_area_sqm=0.6907,
        sheet_quantity_floor_applied=True,
    )
    assert candidates is not None
    assert candidates.selected_quote_sheet_area_source == "eligible_area_floor"
    assert candidates.selected_quote_sheet_area_sqm == pytest.approx(0.6907)
    assert candidates.selection is not None
    assert candidates.selection.selected_source == "eligible_area_floor"
    assert candidates.selection.is_applied_to_quote is False


def test_pbl_has_no_orphan_defs_and_no_stale_orphan_review_reason():
    analysis = _load_pbl_analysis()
    metrics = compute_sheet_quote_bbox_metrics(analysis, _pbl_layer_roles())
    assert metrics.orphan_defs_part_count == 0
    candidates = compute_sheet_quote_material_candidates(
        analysis.get("nesting") or {},
        analysis,
        _pbl_layer_roles(),
        eligible_face_area_sqm=0.6907,
        sheet_split_pre_floor=_empty_sheet_split(),
        selected_quote_sheet_area_sqm=0.6907,
        sheet_quantity_floor_applied=True,
    )
    assert candidates is not None
    assert candidates.orphan_defs_split_placement_sqm is None
    reason = candidates.manual_review_reason or ""
    assert "orphan_defs" not in reason


def test_ana_maria_like_stale_orphans_trigger_manual_review():
    requires, reason = evaluate_manual_review_requirement(
        eligible_area_sqm=1.2638,
        child_part_bbox_sum_sqm=1.1469,
        face_union_bbox_sqm=1.4069,
        design_space_union_bbox_sqm=2.1839,
        layout_occupied_area_sqm=5.36,
        orphan_defs_split_placement_sqm=2.3211,
        orphan_defs_part_count=6,
        operator_manual_footprint_sqm=None,
        has_pseudo_or_unlayered_complexity=True,
    )
    assert requires is True
    assert "stale_orphan_defs" in (reason or "")
    assert "layoutOccupied/childPartBBox" in (reason or "")


def test_material_breakdown_does_not_write_execution_plan_or_tasks_json():
    from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown

    analysis = _load_pbl_analysis()
    payload = {
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
        "svg_analysis_json": analysis,
        "finish_setup": {
            "face_finish_type": "oracal_651",
            "return_finish_type": "paint",
            "backing_mode": "forex_10_no_bevel",
            "letter_group_finishes": [
                {"group_key": "Layer_x0020_2", "layer_name": "Layer_x0020_2", "face_area_m2": 0.35},
                {"group_key": "Layer_x0020_3", "layer_name": "Layer_x0020_3", "face_area_m2": 0.3407},
            ],
        },
        "quote_geometry": {
            "face_area_m2": 0.6907,
            "backing_area_m2": 0.6907,
            "letter_perimeter_m": 11.63,
            "return_material_perimeter_ml": 11.63,
        },
        "layer_role_setup": _pbl_layer_roles(),
        "execution_plan": {"tasks": [{"id": "keep-me"}]},
        "tasks_json": {"items": [{"task": "keep-me"}]},
    }
    before_execution = payload["execution_plan"]
    before_tasks = payload["tasks_json"]
    breakdown = build_intake_v4_material_breakdown("ws-policy-test", payload)
    assert payload["execution_plan"] == before_execution
    assert payload["tasks_json"] == before_tasks
    assert breakdown.sheet_quote_material_candidates is not None
    assert breakdown.sheet_quote_material_candidates.child_part_bbox_sum_sqm is not None
