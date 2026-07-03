"""Intake V3 finish & material workflow — pure service and readiness integration tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    BLOCKER_MISSING_GROUP_FINISH_ASSIGNMENT,
    BLOCKER_MISSING_RETURN_DEPTH,
    BLOCKER_MISSING_RETURN_PAINT_COLOR,
    WARNING_FACE_VINYL_AFTER_RETURN_PAINTING,
    WARNING_LETTER_CUSTOM_FINISH_ADVANCED_MODE,
    WARNING_MATERIAL_ESTIMATE_ONLY,
    WARNING_NO_SHARED_SUPPORT_PSU_PACKED,
    WARNING_RETURN_PAINT_REQUIRES_FACE_PROTECTION,
)
from schemas.intake_v3 import (
    ConfirmedProductionModel,
    CutContourItem,
    CutContourModel,
    FaceFinishSpec,
    FinishAssignment,
    FinishGroupAssignment,
    IntakeV3Workspace,
    LetterItem,
    LetterModel,
    MaterialIntent,
    ReturnFinishSpec,
    SupportContext,
)
from services.intake_v3_finish_material_service import (
    derive_material_intent,
    derive_operation_flags_from_finishes,
    material_intent_warnings,
    validate_finish_assignment,
)
from services.intake_v3_readiness_service import evaluate_intake_v3_readiness


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
            color_name="Pastel blue",
            face_vinyl_roll_width_mm=1260,
            confirmed=True,
        ),
        "return_finish": ReturnFinishSpec(
            finish_type="oracal_651",
            material_code="Oracal 651",
            color_code="055m",
            color_name="Int",
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


class TestFaceVinylRollWidth:
    def test_missing_roll_width_blocks(self):
        finish = _complete_finish()
        finish.face_finish.face_vinyl_roll_width_mm = None
        result = validate_finish_assignment(finish)
        assert any(b.code == BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH for b in result.blockers)

        workspace = _ready_workspace(finish_assignment=finish)
        report = evaluate_intake_v3_readiness(workspace)
        assert report.can_create_quote is False

    def test_roll_width_present_passes(self):
        finish = _complete_finish()
        result = validate_finish_assignment(finish)
        assert not any(b.code == BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH for b in result.blockers)


class TestReturnWrapped:
    def test_missing_depth_blocks(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            return_finish=ReturnFinishSpec(
                finish_type="oracal_wrapped",
                material_code="Oracal 651",
                confirmed=True,
            ),
        )
        result = validate_finish_assignment(finish)
        assert any(b.code == BLOCKER_MISSING_RETURN_DEPTH for b in result.blockers)

    def test_wrapped_operation_flags(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            return_finish=ReturnFinishSpec(
                finish_type="oracal_wrapped",
                material_code="Oracal 651",
                return_depth_mm=60,
                confirmed=True,
            ),
        )
        flags = derive_operation_flags_from_finishes(finish)
        assert flags.return_vinyl_application_required is True
        assert flags.return_painting_after_assembly_required is False


class TestReturnPainted:
    def test_painted_flags_and_face_protection_warning(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            return_finish=ReturnFinishSpec(
                finish_type="painted",
                color_code="RAL9005",
                color_name="Black",
                confirmed=True,
            ),
        )
        flags = derive_operation_flags_from_finishes(finish)
        assert flags.return_painting_after_assembly_required is True
        assert flags.return_vinyl_application_required is False
        result = validate_finish_assignment(finish)
        assert any(w.code == WARNING_RETURN_PAINT_REQUIRES_FACE_PROTECTION for w in result.warnings)

    def test_painted_plus_face_vinyl_forces_after_painting(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            face_finish=FaceFinishSpec(
                finish_type="oracal_8500",
                material_code="Oracal 8500",
                face_vinyl_roll_width_mm=1260,
                confirmed=True,
            ),
            return_finish=ReturnFinishSpec(
                finish_type="painted",
                color_code="RAL9005",
                confirmed=True,
            ),
        )
        flags = derive_operation_flags_from_finishes(finish)
        assert flags.face_vinyl_after_return_painting is True
        result = validate_finish_assignment(finish)
        assert any(w.code == WARNING_FACE_VINYL_AFTER_RETURN_PAINTING for w in result.warnings)

    def test_painted_missing_color_blocks(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            return_finish=ReturnFinishSpec(finish_type="painted", confirmed=True),
        )
        result = validate_finish_assignment(finish)
        assert any(b.code == BLOCKER_MISSING_RETURN_PAINT_COLOR for b in result.blockers)


class TestElectricalAndPSU:
    def test_no_shared_support_psu_packed(self):
        finish = _complete_finish()
        ctx = SupportContext(shared_support=False, illuminated=True)
        flags = derive_operation_flags_from_finishes(finish, ctx)
        assert flags.psu_packed_at_packaging is True
        assert flags.electrical_source_mounting_allowed is False

        intent = derive_material_intent(
            _hub_confirmed_model(),
            finish,
            support_context=ctx,
        )
        assert intent.power_supplies
        psu = intent.power_supplies[0]
        assert psu.packaging_required is True
        assert psu.mounted_on_shared_support is False

        result = validate_finish_assignment(finish, support_context=ctx)
        assert any(w.code == WARNING_NO_SHARED_SUPPORT_PSU_PACKED for w in result.warnings)

    def test_shared_support_allows_source_mounting(self):
        finish = _complete_finish()
        ctx = SupportContext(shared_support=True, illuminated=True)
        flags = derive_operation_flags_from_finishes(finish, ctx)
        assert flags.electrical_source_mounting_allowed is True

        intent = derive_material_intent(
            _hub_confirmed_model(),
            finish,
            support_context=ctx,
        )
        assert intent.power_supplies[0].mounted_on_shared_support is True


class TestMaterialIntent:
    def test_inventory_mutation_not_allowed(self):
        intent = MaterialIntent()
        assert intent.inventory_mutation_allowed is False
        with pytest.raises(ValidationError):
            MaterialIntent(inventory_mutation_allowed=True)

    def test_face_vinyl_roll_derived(self):
        finish = _complete_finish()
        intent = derive_material_intent(_hub_confirmed_model(), finish)
        face_rolls = [r for r in intent.roll_materials if r.source_finish == "face"]
        assert len(face_rolls) == 1
        assert face_rolls[0].roll_width_mm == 1260
        assert face_rolls[0].color_code == "527"

    def test_return_wrapped_roll_derived(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            return_finish=ReturnFinishSpec(
                finish_type="oracal_wrapped",
                material_code="Oracal 651",
                color_code="055m",
                return_depth_mm=60,
                confirmed=True,
            ),
        )
        intent = derive_material_intent(_hub_confirmed_model(), finish)
        return_rolls = [r for r in intent.roll_materials if r.source_finish == "return"]
        assert len(return_rolls) == 1

    def test_sheet_intents_for_face_and_backing(self):
        finish = _complete_finish()
        intent = derive_material_intent(_hub_confirmed_model(), finish)
        face_sheets = [s for s in intent.sheet_materials if s.source_component == "face"]
        backing_sheets = [s for s in intent.sheet_materials if s.source_component == "backing"]
        assert face_sheets and face_sheets[0].material == "Plexiglas"
        assert backing_sheets and backing_sheets[0].material == "Forex"
        assert backing_sheets[0].thickness_mm == 10
        assert backing_sheets[0].remaining_label == "Rest placă estimat"

    def test_painted_return_adds_face_protection_accessory(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            return_finish=ReturnFinishSpec(
                finish_type="painted",
                color_code="RAL9005",
                confirmed=True,
            ),
        )
        intent = derive_material_intent(_hub_confirmed_model(), finish)
        protection = [
            a for a in intent.accessories if a.category == "face_protection"
        ]
        assert protection
        assert protection[0].strict_inventory_tracking is False

    def test_material_estimate_warning_only(self):
        intent = derive_material_intent(_hub_confirmed_model(), _complete_finish())
        warnings = material_intent_warnings(intent)
        assert any(w.code == WARNING_MATERIAL_ESTIMATE_ONLY for w in warnings)


class TestFinishModes:
    def test_letter_custom_warning_not_blocker_when_confirmed(self):
        finish = _complete_finish(assignment_mode="letter_custom")
        result = validate_finish_assignment(finish)
        assert any(w.code == WARNING_LETTER_CUSTOM_FINISH_ADVANCED_MODE for w in result.warnings)
        assert result.is_valid is True

    def test_group_missing_assignment_blocks(self):
        finish = FinishAssignment(
            assignment_mode="group",
            groups=[
                FinishGroupAssignment(
                    group_id="g1",
                    group_label="Grup albastru",
                    face_finish=FaceFinishSpec(
                        finish_type="oracal_8500",
                        face_vinyl_roll_width_mm=1260,
                        confirmed=True,
                    ),
                    return_finish=ReturnFinishSpec(
                        finish_type="oracal_wrapped",
                        return_depth_mm=60,
                        confirmed=True,
                    ),
                    confirmed_by_operator=False,
                )
            ],
        )
        result = validate_finish_assignment(finish)
        assert any(b.code == BLOCKER_MISSING_GROUP_FINISH_ASSIGNMENT for b in result.blockers)


class TestReadinessHappyPath:
    def test_complete_workspace_ready_for_quote(self):
        workspace = _ready_workspace()
        report = evaluate_intake_v3_readiness(workspace)
        finish_blocker_codes = {b.code for b in report.blockers}
        assert BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH not in finish_blocker_codes
        assert BLOCKER_MISSING_RETURN_DEPTH not in finish_blocker_codes
        assert report.can_create_quote is True
        assert report.status == "ready_for_quote"
