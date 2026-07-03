"""Intake V3 workspace preview composition tests."""

from __future__ import annotations

from datetime import datetime, timezone

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    BLOCKER_UNCONFIRMED_LETTER_MODEL,
    WARNING_MATERIAL_ESTIMATE_ONLY,
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
    TaskSeedCandidate,
)
from services.intake_v3_workspace_preview_service import (
    build_boundary_flags,
    build_intake_v3_workspace_preview,
    summarize_workspace_sections,
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
            "client_name": "HUB MEDIA PRODUCTION",
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


def _seed_index(seeds: list[TaskSeedCandidate], code: str) -> int:
    for index, seed in enumerate(seeds):
        if seed.seed_code == code:
            return index
    return -1


class TestPreviewHappyPathHub:
    def test_preview_happy_path_hub(self):
        result = build_intake_v3_workspace_preview(_ready_workspace())
        preview = result.preview
        assert preview.vector_summary.confirmed_letter_count == 18
        assert preview.vector_summary.confirmed_cut_contour_count == 27
        assert preview.vector_summary.confirmed_inner_hole_count == 9
        assert preview.readiness_report is not None
        assert preview.pricing_input_candidate is not None
        assert preview.production_handoff_preview is not None
        assert preview.boundary_flags.preview_only is True
        assert preview.created_quote_id is None
        assert preview.created_order_id is None
        assert preview.execution_plan_id is None
        assert result.is_preview_complete is True


class TestPreviewFaceRollWidthBlocker:
    def test_face_roll_width_blocker_propagates(self):
        finish = _complete_finish()
        finish.face_finish.face_vinyl_roll_width_mm = None
        result = build_intake_v3_workspace_preview(
            _ready_workspace(finish_assignment=finish.model_dump())
        )
        assert BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH in result.preview.preview_blockers
        finish_section = next(
            s for s in result.preview.section_statuses if s.section_code == "finish"
        )
        assert finish_section.status == "blocked"
        assert result.preview.is_ready_for_quote is False


class TestPreviewMaterialEstimateWarning:
    def test_material_estimate_only_warning(self):
        workspace = _ready_workspace(
            material_intent={"estimate_status": "partial", "inventory_mutation_allowed": False}
        )
        result = build_intake_v3_workspace_preview(workspace)
        material_section = next(
            s for s in result.preview.section_statuses if s.section_code == "material_intent"
        )
        assert material_section.status in {"warning", "ready"}
        assert WARNING_MATERIAL_ESTIMATE_ONLY in result.preview.preview_warnings or any(
            w.code == WARNING_MATERIAL_ESTIMATE_ONLY
            for w in (result.preview.readiness_report.warnings if result.preview.readiness_report else [])
        )


class TestPreviewBoundaryFlags:
    def test_boundary_flags_never_allow_execution(self):
        flags = build_boundary_flags(_ready_workspace())
        assert flags.quote_creation_allowed is False
        assert flags.order_creation_allowed is False
        assert flags.execution_plan_creation_allowed is False
        assert flags.inventory_mutation_allowed is False
        assert flags.employee_mobile_action_allowed is False
        assert flags.preview_only is True


class TestPreviewHandoffNonExecutable:
    def test_all_seeds_non_executable_without_execution_ids(self):
        result = build_intake_v3_workspace_preview(_ready_workspace())
        seeds = result.preview.production_handoff_preview.task_seeds  # type: ignore[union-attr]
        assert seeds
        for seed in seeds:
            assert seed.non_executable is True
            assert seed.execution_plan_id is None
            assert seed.execution_task_id is None
        assert result.preview.production_handoff_preview.non_executable is True  # type: ignore[union-attr]
        assert result.preview.production_handoff_preview.execution_plan_id is None  # type: ignore[union-attr]


class TestPreviewTaskOrderOwnerRules:
    def test_task_seed_order_matches_owner_rules(self):
        result = build_intake_v3_workspace_preview(_ready_workspace())
        seeds = result.preview.production_handoff_preview.task_seeds  # type: ignore[union-attr]
        rv = _seed_index(seeds, "return_vinyl_application_workbench")
        forming = _seed_index(seeds, "return_side_forming")
        assembly = _seed_index(seeds, "letter_assembly_no_shared_support")
        face = _seed_index(seeds, "face_vinyl_application_final")
        packaging = _seed_index(seeds, "stretch_wrap_and_delivery_mounting_package")

        return_vinyl = next(s for s in seeds if s.seed_code == "return_vinyl_application_workbench")
        side_forming = next(s for s in seeds if s.seed_code == "return_side_forming")
        assert "return_vinyl_application_workbench" in side_forming.depends_on
        assert rv < forming

        face_vinyl = next(s for s in seeds if s.seed_code == "face_vinyl_application_final")
        assert "letter_assembly_no_shared_support" in face_vinyl.depends_on
        assert assembly < face

        pack = next(s for s in seeds if s.seed_code == "stretch_wrap_and_delivery_mounting_package")
        assert any("PSU" in m for m in pack.materials_referenced)
        assert packaging >= 0


class TestPreviewUnconfirmedVectorBlocks:
    def test_unconfirmed_vector_blocks_readiness(self):
        model = _hub_confirmed_model()
        model.confirmation_status = "pending"
        result = build_intake_v3_workspace_preview(
            _ready_workspace(confirmed_production_model=model.model_dump())
        )
        assert BLOCKER_UNCONFIRMED_LETTER_MODEL in result.preview.preview_blockers
        vector_section = next(
            s for s in result.preview.section_statuses if s.section_code == "vector"
        )
        assert vector_section.status == "blocked"


class TestSummarizeWorkspaceSections:
    def test_section_codes_present(self):
        sections = summarize_workspace_sections(_ready_workspace())
        codes = {s.section_code for s in sections}
        assert codes == {
            "request",
            "template",
            "vector",
            "dimensions",
            "finish",
            "material_intent",
            "readiness",
            "pricing_input",
            "production_handoff",
        }
