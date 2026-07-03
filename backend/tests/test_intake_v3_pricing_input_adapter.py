"""Intake V3 pricing input adapter tests."""

from __future__ import annotations

from datetime import datetime, timezone

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    BLOCKER_MISSING_RETURN_DEPTH,
    BLOCKER_MISSING_RETURN_PAINT_COLOR,
    BLOCKER_UNCONFIRMED_LETTER_MODEL,
    WARNING_MATERIAL_ESTIMATE_ONLY,
    WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH,
)
from schemas.intake_v3 import (
    ConfirmedProductionModel,
    CutContourItem,
    CutContourModel,
    FaceFinishSpec,
    FinishAssignment,
    IntakeV3Workspace,
    LetterItem,
    LetterModel,
    RawSvgAnalysis,
    ReturnFinishSpec,
)
from services.intake_v3_pricing_input_adapter import (
    build_pricing_input_candidate,
    summarize_pricing_input,
    validate_pricing_input_candidate,
)


def _hub_confirmed_model() -> ConfirmedProductionModel:
    letters = [
        LetterItem(letter_id=f"L-{i:02d}", label="A", outer_contour_ids=[f"C-{i:02d}"])
        for i in range(1, 19)
    ]
    contours = [
        CutContourItem(contour_id=f"C-{i:02d}", role="outer", parent_letter_id=f"L-{i:02d}")
        for i in range(1, 19)
    ]
    contours.extend(
        CutContourItem(
            contour_id=f"H-{i:02d}",
            role="inner_hole",
            parent_letter_id=f"L-{i:02d}",
        )
        for i in range(1, 10)
    )
    return ConfirmedProductionModel(
        confirmed_by_user_id="op-1",
        confirmed_at=datetime.now(timezone.utc),
        letter_count=18,
        cut_contour_count=27,
        inner_hole_count=9,
        letter_model=LetterModel(letters=letters, count_confirmed=True),
        cut_contour_model=CutContourModel(
            contours=contours,
            outer_contour_count=18,
            inner_hole_count=9,
            cut_contour_count=27,
        ),
        confirmation_status="confirmed",
    )


def _complete_finish(**overrides) -> FinishAssignment:
    payload = {
        "assignment_mode": "all",
        "confirmed_by_operator": True,
        "face_finish": FaceFinishSpec(
            finish_type="oracal_8500",
            material_code="Oracal 8500",
            color_code="527",
            face_vinyl_roll_width_mm=1260,
            confirmed=True,
        ),
        "return_finish": ReturnFinishSpec(
            finish_type="oracal_651",
            material_code="Oracal 651",
            return_depth_mm=60,
            confirmed=True,
        ),
        "backing_finish": {"material": "Forex", "thickness_mm": 10, "confirmed": True},
    }
    payload.update(overrides)
    return FinishAssignment.model_validate(payload)


def _ready_workspace(**overrides) -> IntakeV3Workspace:
    payload = {
        "client_request": {
            "client_name": "Hub Media",
            "request_code": "INK-2026-0847",
            "width_mm": 9250,
            "height_mm": 550,
        },
        "confirmed_production_model": _hub_confirmed_model().model_dump(),
        "finish_assignment": _complete_finish().model_dump(),
        "material_intent": {"estimate_status": "complete"},
    }
    payload.update(overrides)
    return IntakeV3Workspace.model_validate(payload)


class TestPricingInputHappyPath:
    def test_hub_no_shared_support_ready(self):
        workspace = _ready_workspace()
        result = build_pricing_input_candidate(workspace)
        assert result.is_ready_for_quote is True
        assert result.candidate.production_counts.letter_count == 18
        assert result.candidate.production_counts.cut_contour_count == 27
        assert result.candidate.production_counts.inner_hole_count == 9
        assert result.candidate.support_mode == "no_shared_support"
        assert result.quote_input_payload["inventory_mutation_allowed"] is False
        valid, issues = validate_pricing_input_candidate(result)
        assert valid is True
        assert issues == []


class TestPricingInputBlockers:
    def test_face_vinyl_roll_width_blocker(self):
        finish = _complete_finish()
        finish.face_finish.face_vinyl_roll_width_mm = None
        result = build_pricing_input_candidate(_ready_workspace(finish_assignment=finish))
        assert BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH in result.adapter_blockers
        assert result.is_ready_for_quote is False

    def test_return_depth_blocker(self):
        finish = _complete_finish()
        finish.return_finish.return_depth_mm = None
        result = build_pricing_input_candidate(_ready_workspace(finish_assignment=finish))
        assert BLOCKER_MISSING_RETURN_DEPTH in result.adapter_blockers
        assert result.is_ready_for_quote is False

    def test_return_painted_color_blocker(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            return_finish=ReturnFinishSpec(finish_type="painted", confirmed=True),
        )
        result = build_pricing_input_candidate(_ready_workspace(finish_assignment=finish))
        assert BLOCKER_MISSING_RETURN_PAINT_COLOR in result.adapter_blockers

    def test_unconfirmed_vector_blocks(self):
        model = _hub_confirmed_model()
        model.confirmation_status = "pending"
        result = build_pricing_input_candidate(
            _ready_workspace(confirmed_production_model=model.model_dump())
        )
        assert BLOCKER_UNCONFIRMED_LETTER_MODEL in result.adapter_blockers
        assert result.is_ready_for_quote is False


class TestPricingInputWarnings:
    def test_material_estimate_only_warning_not_blocker(self):
        workspace = _ready_workspace()
        result = build_pricing_input_candidate(workspace)
        assert WARNING_MATERIAL_ESTIMATE_ONLY in result.candidate.readiness_summary.warning_codes
        assert result.is_ready_for_quote is True

    def test_raw_confirmed_mismatch_warning_only(self):
        workspace = _ready_workspace(
            raw_svg_analysis=RawSvgAnalysis(closed_contour_count=27),
        )
        result = build_pricing_input_candidate(workspace)
        assert WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH in (
            result.candidate.readiness_summary.warning_codes
        )
        assert result.is_ready_for_quote is True


class TestPricingInputBoundaries:
    def test_no_price_calculation(self):
        result = build_pricing_input_candidate(_ready_workspace())
        forbidden = {"total_price", "unit_price", "margin", "tva"}
        assert forbidden.isdisjoint(result.quote_input_payload.keys())
        summary = summarize_pricing_input(result)
        assert summary["has_price_fields"] is False

    def test_no_inventory_mutation(self):
        result = build_pricing_input_candidate(_ready_workspace())
        assert result.quote_input_payload["inventory_mutation_allowed"] is False
        assert "stock_movement" not in result.quote_input_payload

    def test_operation_flags_included(self):
        result = build_pricing_input_candidate(_ready_workspace())
        flags = result.candidate.operation_summary.flags
        assert flags.return_vinyl_application_required is True
        assert flags.face_vinyl_application_required is True
        assert flags.psu_packed_at_packaging is True
        assert "operation_flags" in result.quote_input_payload
