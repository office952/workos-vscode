"""Intake V4 operator manual sheet footprint override for quote material review."""

from __future__ import annotations

import pytest

from services.intake_v4_nesting_material_precision import (
    SheetNestingMaterialSplit,
    compute_sheet_quote_material_candidates,
)
from services.intake_v4_sheet_footprint_override_service import (
    apply_operator_footprint_to_sheet_material_quantities,
    compute_operator_manual_footprint_sqm,
    resolve_sheet_quote_selection_with_override,
    sheet_quote_override_from_payload,
)


def _ana_maria_override(*, use_for_quote_estimate: bool) -> dict:
    return {
        "enabled": True,
        "source": "operator_manual_footprint",
        "selectedFootprintSource": "operator_manual_footprint",
        "widthCm": 192.67,
        "heightCm": 143.389,
        "areaSqm": compute_operator_manual_footprint_sqm(192.67, 143.389),
        "reason": "Manual Corel layout footprint",
        "appliesTo": ["plexiglas_face", "forex_backing"],
        "useForQuoteEstimate": use_for_quote_estimate,
    }


def test_compute_operator_manual_footprint_sqm_ana_maria():
    area = compute_operator_manual_footprint_sqm(192.67, 143.389)
    assert area == pytest.approx(2.7627, abs=0.0001)


def test_sheet_quote_override_from_payload_normalizes_snake_case():
    payload = {
        "sheet_quote_override": {
            "width_cm": 100.0,
            "height_cm": 50.0,
            "use_for_quote_estimate": False,
        }
    }
    override = sheet_quote_override_from_payload(payload)
    assert override is not None
    assert override["widthCm"] == 100.0
    assert override["heightCm"] == 50.0
    assert override["areaSqm"] == 0.5
    assert override["useForQuoteEstimate"] is False


def test_validate_sheet_footprint_requires_note():
    from services.intake_v4_sheet_footprint_override_service import validate_sheet_footprint_override_request

    with pytest.raises(ValueError, match="note_required"):
        validate_sheet_footprint_override_request(
            selected_footprint_source="operator_manual_footprint",
            width_cm=192.67,
            height_cm=143.389,
            reason="",
            use_for_quote_estimate=False,
            eligible_face_area_sqm=1.2638,
        )


def test_validate_sheet_footprint_rejects_below_eligible_when_estimate_enabled():
    from services.intake_v4_sheet_footprint_override_service import validate_sheet_footprint_override_request

    with pytest.raises(ValueError, match="footprint_below_eligible_area"):
        validate_sheet_footprint_override_request(
            selected_footprint_source="operator_manual_footprint",
            width_cm=100.0,
            height_cm=50.0,
            reason="Măsurat în Corel",
            use_for_quote_estimate=True,
            eligible_face_area_sqm=1.2638,
        )


def test_build_sheet_quote_override_record_includes_audit_fields():
    from services.intake_v4_sheet_footprint_override_service import build_sheet_quote_override_record

    record = build_sheet_quote_override_record(
        selected_footprint_source="operator_manual_footprint",
        width_cm=192.67,
        height_cm=143.389,
        reason="Măsurat în Corel: 192.67 × 143.389 cm",
        applies_to=["plexiglas_face", "forex_backing"],
        use_for_quote_estimate=False,
        created_by="operator@test",
    )
    assert record["is_applied_to_quote"] is False
    assert record["use_for_quote_review"] is True
    assert record["selectedFootprintSource"] == "operator_manual_footprint"
    assert record["createdAt"]
    assert record["updatedAt"]


def test_build_sheet_quote_override_record_candidate_source_without_dimensions():
    from services.intake_v4_sheet_footprint_override_service import build_sheet_quote_override_record

    record = build_sheet_quote_override_record(
        selected_footprint_source="face_union_bbox",
        reason="Operator a ales face union bbox",
        applies_to=["plexiglas_face", "forex_backing"],
        use_for_quote_estimate=True,
        created_by="operator@test",
    )
    assert record["selectedFootprintSource"] == "face_union_bbox"
    assert "widthCm" not in record
    assert record["useForQuoteEstimate"] is True


def test_resolve_selection_without_estimate_keeps_eligible_floor():
    override = _ana_maria_override(use_for_quote_estimate=False)
    selected_sqm, source, manual_sqm = resolve_sheet_quote_selection_with_override(
        eligible_face_area_sqm=1.2638,
        base_selected_sqm=1.2638,
        sheet_quantity_floor_applied=True,
        override=override,
    )
    assert manual_sqm == pytest.approx(2.7627, abs=0.0001)
    assert selected_sqm == pytest.approx(1.2638, abs=0.0001)
    assert source == "eligible_area_floor"


def test_resolve_selection_with_estimate_uses_max_eligible_and_manual():
    override = _ana_maria_override(use_for_quote_estimate=True)
    selected_sqm, source, manual_sqm = resolve_sheet_quote_selection_with_override(
        eligible_face_area_sqm=1.2638,
        base_selected_sqm=1.2638,
        sheet_quantity_floor_applied=True,
        override=override,
    )
    assert manual_sqm == pytest.approx(2.7627, abs=0.0001)
    assert selected_sqm == pytest.approx(2.7627, abs=0.0001)
    assert source == "operator_manual_footprint"


def test_apply_operator_footprint_false_leaves_quantities_unchanged():
    override = _ana_maria_override(use_for_quote_estimate=False)
    face, backing, applied = apply_operator_footprint_to_sheet_material_quantities(
        sheet_face_qty=1.2638,
        sheet_backing_qty=1.2638,
        override=override,
    )
    assert applied is False
    assert face == pytest.approx(1.2638)
    assert backing == pytest.approx(1.2638)


def test_apply_operator_footprint_true_raises_sheet_rows():
    override = _ana_maria_override(use_for_quote_estimate=True)
    override["selectedFootprintSource"] = "operator_manual_footprint"
    face, backing, applied = apply_operator_footprint_to_sheet_material_quantities(
        sheet_face_qty=1.2638,
        sheet_backing_qty=1.2638,
        override=override,
    )
    assert applied is True
    assert face == pytest.approx(2.7627, abs=0.0001)
    assert backing == pytest.approx(2.7627, abs=0.0001)


def test_apply_operator_footprint_face_union_bbox_source():
    from services.intake_v4_sheet_footprint_override_service import SheetFootprintCandidateAreas

    override = {
        "enabled": True,
        "selectedFootprintSource": "face_union_bbox",
        "useForQuoteEstimate": True,
        "appliesTo": ["plexiglas_face", "forex_backing"],
    }
    candidate_areas = SheetFootprintCandidateAreas(
        eligible_face_area_sqm=1.2638,
        placement_footprint_face_sqm=1.1469,
        face_union_bbox_sqm=2.5238,
        layout_occupied_area_sqm=2.5238,
        full_sheet_allocation_sqm=6.0,
    )
    face, backing, applied = apply_operator_footprint_to_sheet_material_quantities(
        sheet_face_qty=1.2638,
        sheet_backing_qty=1.2638,
        override=override,
        candidate_areas=candidate_areas,
        eligible_face_area_sqm=1.2638,
        base_selected_sqm=1.2638,
        sheet_quantity_floor_applied=True,
    )
    assert applied is True
    assert face == pytest.approx(2.5238, abs=0.0001)
    assert backing == pytest.approx(2.5238, abs=0.0001)


def test_resolve_selection_with_face_union_bbox_source():
    from services.intake_v4_sheet_footprint_override_service import SheetFootprintCandidateAreas

    override = {
        "enabled": True,
        "selectedFootprintSource": "face_union_bbox",
        "useForQuoteEstimate": True,
    }
    candidate_areas = SheetFootprintCandidateAreas(
        eligible_face_area_sqm=1.2638,
        placement_footprint_face_sqm=1.1469,
        face_union_bbox_sqm=2.5238,
        layout_occupied_area_sqm=2.5238,
        full_sheet_allocation_sqm=6.0,
    )
    selected_sqm, source, manual_sqm = resolve_sheet_quote_selection_with_override(
        eligible_face_area_sqm=1.2638,
        base_selected_sqm=1.2638,
        sheet_quantity_floor_applied=True,
        override=override,
        candidate_areas=candidate_areas,
    )
    assert manual_sqm is None
    assert selected_sqm == pytest.approx(2.5238, abs=0.0001)
    assert source == "face_union_bbox"


def _empty_sheet_split() -> SheetNestingMaterialSplit:
    return SheetNestingMaterialSplit(
        face_area_sqm=None,
        backing_area_sqm=None,
        config_id="sheet_3000x2000",
        fully_valid=False,
        mode="prorated_fallback",
        quantity_basis="sheet_nesting_prorated_fallback",
        confidence="estimate_from_nesting_medium",
    )


def test_compute_candidates_includes_operator_manual_without_changing_default_selection():
    nesting = {"sheets": [{"configId": "sheet_3000x2000", "sheetsUsed": 1, "usedSheetAreaSqm": 6.0}]}
    override = _ana_maria_override(use_for_quote_estimate=False)
    candidates = compute_sheet_quote_material_candidates(
        nesting,
        {},
        {},
        eligible_face_area_sqm=1.2638,
        sheet_split_pre_floor=_empty_sheet_split(),
        selected_quote_sheet_area_sqm=1.2638,
        sheet_quantity_floor_applied=True,
        sheet_quote_override=override,
    )
    assert candidates is not None
    assert candidates.operator_manual_footprint_sqm == pytest.approx(2.7627, abs=0.0001)
    assert candidates.operator_manual_footprint_width_cm == pytest.approx(192.67)
    assert candidates.operator_manual_use_for_quote_estimate is False
    assert candidates.selected_quote_sheet_area_sqm == pytest.approx(1.2638)
    assert candidates.selected_quote_sheet_area_source == "eligible_area_floor"


def test_compute_candidates_pbl_without_override_unchanged():
    nesting = {"sheets": [{"configId": "sheet_3000x2000", "sheetsUsed": 1, "usedSheetAreaSqm": 6.0}]}
    candidates = compute_sheet_quote_material_candidates(
        nesting,
        {},
        {},
        eligible_face_area_sqm=0.6907,
        sheet_split_pre_floor=_empty_sheet_split(),
        selected_quote_sheet_area_sqm=0.6907,
        sheet_quantity_floor_applied=True,
        sheet_quote_override=None,
    )
    assert candidates is not None
    assert candidates.operator_manual_footprint_sqm is None
    assert candidates.selected_quote_sheet_area_sqm == pytest.approx(0.6907)
    assert candidates.selected_quote_sheet_area_source == "eligible_area_floor"


def test_material_breakdown_does_not_touch_execution_plan_or_tasks_json():
    from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown

    payload = {
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
        "svg_analysis_json": {
            "nesting": {
                "sheets": [
                    {
                        "configId": "sheet_3000x2000",
                        "sheetsUsed": 1,
                        "usedSheetAreaSqm": 6.0,
                    }
                ]
            },
            "layers": [{"id": "L1", "name": "L1", "filledAreaSqm": 1.2638}],
        },
        "finish_setup": {
            "face_finish_type": "oracal_651",
            "return_finish_type": "paint",
            "backing_mode": "forex_10_no_bevel",
        },
        "quote_geometry": {
            "face_area_m2": 1.2638,
            "backing_area_m2": 1.2638,
            "letter_perimeter_m": 2.0,
            "return_material_perimeter_ml": 2.0,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "L1",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
        },
        "execution_plan": {"tasks": [{"id": "keep-me"}]},
        "tasks_json": {"items": [{"task": "keep-me"}]},
        "sheet_quote_override": _ana_maria_override(use_for_quote_estimate=False),
    }
    before_execution = payload["execution_plan"]
    before_tasks = payload["tasks_json"]
    breakdown = build_intake_v4_material_breakdown("ws-footprint-test", payload)
    assert payload["execution_plan"] == before_execution
    assert payload["tasks_json"] == before_tasks
    assert breakdown.sheet_quote_material_candidates is not None
    assert breakdown.sheet_quote_material_candidates.operator_manual_footprint_sqm == pytest.approx(
        2.7627, abs=0.0001
    )
