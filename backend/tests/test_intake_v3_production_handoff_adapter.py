"""Intake V3 production handoff adapter tests."""

from __future__ import annotations

from datetime import datetime, timezone

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    SUPPORT_MODE_SHARED_PENDING,
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
    ReturnFinishSpec,
    SupportContext,
    TaskSeedCandidate,
)
from services.intake_v3_finish_material_service import derive_operation_flags_from_finishes
from services.intake_v3_production_handoff_adapter import (
    build_production_handoff_preview,
    build_task_seed_candidates,
    validate_production_handoff_preview,
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
        "vector_asset": {"file_name": "hub.svg", "upload_status": "parsed"},
        "confirmed_production_model": _hub_confirmed_model().model_dump(),
        "finish_assignment": _complete_finish().model_dump(),
        "material_intent": {"estimate_status": "complete"},
    }
    payload.update(overrides)
    return IntakeV3Workspace.model_validate(payload)


def _active_seed(codes: list[TaskSeedCandidate], code: str) -> TaskSeedCandidate:
    for s in codes:
        if s.seed_code == code:
            return s
    raise AssertionError(f"seed {code} not found")


class TestHandoffHappyPath:
    def test_no_shared_support_generates_expected_seeds(self):
        workspace = _ready_workspace()
        result = build_production_handoff_preview(workspace)
        active = [s for s in result.preview.task_seeds if s.active]
        active_codes = {s.seed_code for s in active}
        expected = {
            "confirmed_production_model",
            "cnc_file_preparation",
            "return_forming_file_preparation",
            "return_vinyl_application_workbench",
            "face_and_backing_cnc_cut",
            "return_side_forming",
            "return_face_bonding",
            "led_installation_wiring_and_light_test",
            "letter_assembly_no_shared_support",
            "face_vinyl_application_final",
            "stretch_wrap_and_delivery_mounting_package",
        }
        assert expected.issubset(active_codes)
        for seed in result.preview.task_seeds:
            assert seed.non_executable is True
            assert seed.execution_plan_id is None
            assert seed.execution_task_id is None
        valid, issues = validate_production_handoff_preview(result)
        assert valid is True
        assert issues == []


class TestReturnVinylDependencies:
    def test_return_vinyl_before_forming(self):
        workspace = _ready_workspace()
        seeds = build_task_seed_candidates(workspace)
        vinyl = _active_seed(seeds, "return_vinyl_application_workbench")
        forming = _active_seed(seeds, "return_side_forming")
        assert vinyl.active is True
        assert "return_vinyl_application_workbench" in forming.depends_on

    def test_not_wrapped_no_return_vinyl_seed_active(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            return_finish=ReturnFinishSpec(finish_type="raw", confirmed=True),
        )
        workspace = _ready_workspace(finish_assignment=finish)
        seeds = build_task_seed_candidates(workspace)
        vinyl = _active_seed(seeds, "return_vinyl_application_workbench")
        assert vinyl.active is False


class TestReturnPaintedAndFaceVinyl:
    def test_return_painted_after_assembly(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            return_finish=ReturnFinishSpec(
                finish_type="painted",
                color_code="RAL9005",
                confirmed=True,
            ),
        )
        workspace = _ready_workspace(finish_assignment=finish)
        seeds = build_task_seed_candidates(workspace)
        paint = _active_seed(seeds, "return_painting_after_assembly")
        assert paint.active is True
        assert "letter_assembly_no_shared_support" in paint.depends_on

    def test_face_vinyl_after_assembly(self):
        workspace = _ready_workspace()
        seeds = build_task_seed_candidates(workspace)
        face = _active_seed(seeds, "face_vinyl_application_final")
        assert face.active is True
        assert "letter_assembly_no_shared_support" in face.depends_on

    def test_face_vinyl_after_return_painting_when_both(self):
        finish = FinishAssignment(
            assignment_mode="all",
            confirmed_by_operator=True,
            face_finish=FaceFinishSpec(
                finish_type="oracal_8500",
                face_vinyl_roll_width_mm=1260,
                confirmed=True,
            ),
            return_finish=ReturnFinishSpec(
                finish_type="painted",
                color_code="RAL9005",
                confirmed=True,
            ),
        )
        workspace = _ready_workspace(finish_assignment=finish)
        seeds = build_task_seed_candidates(workspace)
        face = _active_seed(seeds, "face_vinyl_application_final")
        assert "return_painting_after_assembly" in face.depends_on


class TestAssemblyDependencies:
    def test_assembly_depends_on_led(self):
        workspace = _ready_workspace()
        seeds = build_task_seed_candidates(workspace)
        assembly = _active_seed(seeds, "letter_assembly_no_shared_support")
        assert "led_installation_wiring_and_light_test" in assembly.depends_on


class TestPSUPackaging:
    def test_no_shared_support_psu_in_packaging(self):
        workspace = _ready_workspace()
        result = build_production_handoff_preview(workspace)
        packaging = _active_seed(result.preview.task_seeds, "stretch_wrap_and_delivery_mounting_package")
        assert any("PSU" in m for m in packaging.materials_referenced)
        active_codes = {s.seed_code for s in result.preview.task_seeds if s.active}
        assert "electrical_source_mounting" not in active_codes


class TestNonExecutable:
    def test_handoff_not_executable(self):
        result = build_production_handoff_preview(_ready_workspace())
        assert result.preview.non_executable is True
        assert result.preview.employee_mobile_action_allowed is False
        assert result.preview.preview_only is True


class TestNoHardcodedEmployees:
    def test_seeds_use_skills_not_names(self):
        result = build_production_handoff_preview(_ready_workspace())
        for seed in result.preview.task_seeds:
            assert seed.required_skill
            assert seed.required_station
            blob = f"{seed.operator_instruction} {seed.display_name}".lower()
            for name in ("florin", "călin", "octavian"):
                assert name not in blob


class TestReadinessBlocksHandoff:
    def test_blockers_stop_handoff_ready(self):
        finish = _complete_finish()
        finish.face_finish.face_vinyl_roll_width_mm = None
        result = build_production_handoff_preview(_ready_workspace(finish_assignment=finish))
        assert BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH in result.adapter_blockers
        assert result.is_ready_for_handoff is False


class TestSharedSupportPending:
    def test_shared_support_pending_warning_no_false_mounting(self):
        workspace = _ready_workspace(
            client_request={
                "client_name": "Hub",
                "request_code": "X",
                "width_mm": 9250,
                "height_mm": 550,
                "mounting_intent": "suport comun ACM",
            }
        )
        result = build_production_handoff_preview(workspace)
        assert result.preview.support_mode == SUPPORT_MODE_SHARED_PENDING
        assert any("pending" in w.lower() or "suport" in w.lower() for w in result.adapter_warnings)
        active_codes = {s.seed_code for s in result.preview.task_seeds if s.active}
        assert "electrical_source_mounting" not in active_codes
        flags = derive_operation_flags_from_finishes(
            workspace.finish_assignment,
            SupportContext(shared_support=True, illuminated=True),
        )
        assert flags.electrical_source_mounting_allowed is True
