"""Intake V3 architecture contracts — validation and readiness skeleton tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_DIMENSIONS,
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    BLOCKER_MISSING_FINISH_ASSIGNMENT,
    BLOCKER_MISSING_RETURN_DEPTH,
    BLOCKER_UNCONFIRMED_LETTER_MODEL,
    HUB_MEDIA_PRODUCTION_LETTER_MODEL,
    OWNER_OPERATIONAL_RULES,
    OWNER_OPERATIONAL_RULE_DETAILS,
    REFERENCE_TASK_ORDER_NO_SHARED_SUPPORT,
)
from schemas.intake_v3 import (
    ConfirmedProductionModel,
    CutContourItem,
    CutContourModel,
    EmployeePreviewSeed,
    FaceFinishSpec,
    FinishAssignment,
    FinishGroupAssignment,
    IntakeV3Workspace,
    LetterItem,
    LetterModel,
    MaterialIntent,
    ProductionHandoff,
    RawSvgAnalysis,
    ReturnFinishSpec,
)
from services.intake_v3_readiness_service import (
    build_reference_production_handoff_seed,
    evaluate_intake_v3_readiness,
    owner_operational_rule_summaries,
)


def _hub_letters() -> list[LetterItem]:
    return [
        LetterItem(letter_id=f"L-{i:02d}", label=chr(64 + ((i - 1) % 26) + 1))
        for i in range(1, 19)
    ]


def _hub_contours() -> list[CutContourItem]:
    contours: list[CutContourItem] = []
    for i in range(1, 19):
        contours.append(
            CutContourItem(contour_id=f"C-OUT-{i:02d}", role="outer", parent_letter_id=f"L-{i:02d}")
        )
    for i in range(1, 10):
        contours.append(
            CutContourItem(
                contour_id=f"C-HOLE-{i:02d}",
                role="inner_hole",
                parent_letter_id=f"L-{i:02d}",
            )
        )
    return contours


def _hub_confirmed_model(*, confirmed: bool = True) -> ConfirmedProductionModel:
    return ConfirmedProductionModel(
        confirmed_by_user_id="operator-1",
        confirmed_at=datetime.now(timezone.utc),
        letter_count=18,
        cut_contour_count=27,
        inner_hole_count=9,
        ignored_object_count=0,
        letter_model=LetterModel(letters=_hub_letters(), count_confirmed=confirmed),
        cut_contour_model=CutContourModel(
            contours=_hub_contours(),
            outer_contour_count=18,
            inner_hole_count=9,
            cut_contour_count=27,
        ),
        confirmation_status="confirmed" if confirmed else "pending",
    )


def _complete_finish() -> FinishAssignment:
    return FinishAssignment(
        assignment_mode="all",
        confirmed_by_operator=True,
        face_finish=FaceFinishSpec(
            finish_type="oracal_8500",
            material_code="Oracal 8500",
            color_code="527",
            color_name="Pastel blue",
            face_vinyl_roll_width_mm=1260,
        ),
        return_finish=ReturnFinishSpec(
            finish_type="oracal_651",
            material_code="Oracal 651",
            color_code="055m",
            color_name="Int",
            return_depth_mm=60,
        ),
    )


def _base_workspace(**overrides) -> IntakeV3Workspace:
    payload = {
        "client_request": {
            "client_name": "Hub Media",
            "request_code": "INK-2026-0847",
            "width_mm": 9250,
            "height_mm": 550,
            "depth_mm": 60,
        },
        "confirmed_production_model": _hub_confirmed_model(),
        "finish_assignment": _complete_finish(),
        "material_intent": {"estimate_status": "complete"},
    }
    payload.update(overrides)
    return IntakeV3Workspace.model_validate(payload)


class TestHubModel18279:
    def test_letter_count_differs_from_cut_contour_count_is_valid(self):
        model = _hub_confirmed_model()
        assert model.letter_count == HUB_MEDIA_PRODUCTION_LETTER_MODEL["letter_count"]
        assert model.cut_contour_count == HUB_MEDIA_PRODUCTION_LETTER_MODEL["cut_contour_count"]
        assert model.inner_hole_count == HUB_MEDIA_PRODUCTION_LETTER_MODEL["inner_hole_count"]
        assert model.letter_count != model.cut_contour_count

    def test_inner_holes_are_not_letters(self):
        model = _hub_confirmed_model()
        holes = [c for c in model.cut_contour_model.contours if c.role == "inner_hole"]
        assert len(holes) == 9
        letter_ids = {letter.letter_id for letter in model.letter_model.letters}
        for hole in holes:
            assert hole.contour_id not in letter_ids


class TestRawVsConfirmedSeparation:
    def test_raw_27_confirmed_18_is_valid_and_warning_not_blocker_when_confirmed(self):
        workspace = _base_workspace(
            raw_svg_analysis={"closed_contour_count": 27},
            confirmed_production_model=_hub_confirmed_model(confirmed=True),
        )
        report = evaluate_intake_v3_readiness(workspace)
        assert report.can_create_quote is True
        assert not any(b.code == BLOCKER_UNCONFIRMED_LETTER_MODEL for b in report.blockers)
        assert any(w.code == "RAW_CONFIRMED_LETTER_COUNT_MISMATCH" for w in report.warnings)

    def test_unconfirmed_model_blocks_quote(self):
        workspace = _base_workspace(
            raw_svg_analysis={"closed_contour_count": 27},
            confirmed_production_model=_hub_confirmed_model(confirmed=False),
        )
        report = evaluate_intake_v3_readiness(workspace)
        assert report.can_create_quote is False
        assert any(b.code == BLOCKER_UNCONFIRMED_LETTER_MODEL for b in report.blockers)


class TestReadinessBlockers:
    def test_missing_face_vinyl_roll_width_blocks_quote(self):
        finish = _complete_finish()
        finish.face_finish.face_vinyl_roll_width_mm = None
        workspace = _base_workspace(finish_assignment=finish)
        report = evaluate_intake_v3_readiness(workspace)
        assert report.status == "blocked_for_quote"
        assert report.can_create_quote is False
        assert any(b.code == BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH for b in report.blockers)

    def test_missing_return_depth_blocks_quote(self):
        finish = _complete_finish()
        finish.return_finish.return_depth_mm = None
        workspace = _base_workspace(finish_assignment=finish)
        report = evaluate_intake_v3_readiness(workspace)
        assert any(b.code == BLOCKER_MISSING_RETURN_DEPTH for b in report.blockers)

    def test_missing_dimensions_blocks_quote(self):
        workspace = _base_workspace(
            client_request={
                "client_name": "Hub Media",
                "request_code": "INK-2026-0847",
            }
        )
        report = evaluate_intake_v3_readiness(workspace)
        assert any(b.code == BLOCKER_MISSING_DIMENSIONS for b in report.blockers)

    def test_missing_finish_assignment_blocks_when_group_unconfirmed(self):
        finish = FinishAssignment(
            assignment_mode="group",
            groups=[
                FinishGroupAssignment(
                    group_id="g1",
                    group_label="Grup albastru",
                    face_finish=FaceFinishSpec(
                        finish_type="oracal_8500",
                        material_code="Oracal 8500",
                        face_vinyl_roll_width_mm=1260,
                    ),
                    return_finish=ReturnFinishSpec(
                        finish_type="oracal_651",
                        material_code="Oracal 651",
                        return_depth_mm=60,
                    ),
                    confirmed_by_operator=False,
                )
            ],
        )
        workspace = _base_workspace(finish_assignment=finish)
        report = evaluate_intake_v3_readiness(workspace)
        assert any(b.code == BLOCKER_MISSING_FINISH_ASSIGNMENT for b in report.blockers)


class TestReadyForQuoteHappyPath:
    def test_complete_payload_is_ready_for_quote(self):
        workspace = _base_workspace()
        report = evaluate_intake_v3_readiness(workspace)
        assert report.blockers == []
        assert report.can_create_quote is True
        assert report.status == "ready_for_quote"
        assert report.can_generate_production_handoff is True


class TestPreviewContracts:
    def test_material_intent_cannot_mutate_inventory(self):
        intent = MaterialIntent()
        assert intent.inventory_mutation_allowed is False
        with pytest.raises(ValidationError):
            MaterialIntent(inventory_mutation_allowed=True)

    def test_production_handoff_preview_only(self):
        handoff = ProductionHandoff()
        assert handoff.preview_only is True
        with pytest.raises(ValidationError):
            ProductionHandoff(preview_only=False)

    def test_employee_preview_seed_non_executable(self):
        seed = EmployeePreviewSeed()
        assert seed.non_executable is True
        with pytest.raises(ValidationError):
            EmployeePreviewSeed(non_executable=False)


class TestOwnerOperationalRulesDocumented:
    def test_owner_rules_constants_exist(self):
        assert "face_vinyl_after_assembly_and_back" in OWNER_OPERATIONAL_RULES
        assert "return_vinyl_before_side_forming" in OWNER_OPERATIONAL_RULES
        assert "no_shared_support_psu_at_packaging" in OWNER_OPERATIONAL_RULES
        assert "shared_support_electrical_task_allowed" in OWNER_OPERATIONAL_RULES

    def test_reference_task_order_has_twelve_steps(self):
        order = build_reference_production_handoff_seed()
        assert len(order) == 12
        assert order == list(REFERENCE_TASK_ORDER_NO_SHARED_SUPPORT)
        assert "Colantare fețe litere" in order[-3]
        assert "Ambalare / predare" in order[-1]

    def test_owner_rule_details_not_enforced_in_execution(self):
        summaries = owner_operational_rule_summaries()
        assert len(summaries) == len(OWNER_OPERATIONAL_RULE_DETAILS)
        assert all(rule["enforced_in_execution"] is False for rule in summaries)
