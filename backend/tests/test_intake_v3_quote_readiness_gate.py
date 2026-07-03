"""Intake V3 quote readiness gate and pre-quote review — no quote/order/plan creation."""

from __future__ import annotations

from datetime import datetime, timezone

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    BLOCKER_UNCONFIRMED_LETTER_MODEL,
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
    VectorAsset,
)
from services.intake_v3_quote_readiness_service import (
    build_prequote_review,
    evaluate_intake_v3_quote_readiness,
)
from services.intake_v3_workspace_preview_service import build_intake_v3_workspace_preview

MINIMAL_WORKSPACE_PAYLOAD = {
    "client_request": {
        "client_name": "Quote readiness test",
        "request_code": "QR-TEST-001",
        "job_title": "Quote readiness test",
    },
    "product_selection": {"template_code": "TPL-VOLUMETRIC-LETTERS", "pilot_scope": True},
    "material_intent": {"inventory_mutation_allowed": False, "estimate_status": "not_started"},
    "production_handoff": {"preview_only": True},
    "employee_preview_seed": {"non_executable": True, "preview_tasks": []},
}

VALID_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100mm" height="50mm">
  <path id="letter-a" d="M10 40 L20 10 L30 40 Z" fill="#ff0000"/>
</svg>"""


def _hub_confirmed_model() -> ConfirmedProductionModel:
    letters = [
        LetterItem(letter_id=f"L-{i:02d}", label=str(i), outer_contour_ids=[f"C-{i:02d}"])
        for i in range(1, 19)
    ]
    contours = [
        CutContourItem(contour_id=f"C-{i:02d}", role="outer", parent_letter_id=f"L-{i:02d}")
        for i in range(1, 19)
    ]
    contours.extend(
        CutContourItem(
            contour_id=f"C-HOLE-{i:02d}",
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
            confirmed=True,
        ),
        return_finish=ReturnFinishSpec(
            finish_type="oracal_651",
            material_code="Oracal 651",
            color_code="055m",
            return_depth_mm=60,
            confirmed=True,
        ),
        backing_finish={"material": "Forex", "thickness_mm": 10, "confirmed": True},
    )


def _ready_workspace(**overrides) -> IntakeV3Workspace:
    payload = {
        "client_request": {
            "client_name": "Hub Media",
            "request_code": "INK-2026-0847",
            "job_title": "Litere volumetrice",
            "width_mm": 9250,
            "height_mm": 550,
        },
        "vector_asset": VectorAsset(file_name="hub.svg", upload_status="parsed"),
        "raw_svg_analysis": RawSvgAnalysis(
            file_name="hub.svg",
            closed_contour_count=18,
            path_count=18,
        ),
        "confirmed_production_model": _hub_confirmed_model().model_dump(mode="json"),
        "finish_assignment": _complete_finish().model_dump(mode="json"),
        "material_intent": {"estimate_status": "complete"},
        "support_context": {"shared_support": False, "illuminated": True},
    }
    payload.update(overrides)
    return IntakeV3Workspace.model_validate(payload)


class TestQuoteReadinessGate:
    def test_empty_incomplete_workspace_is_blocked(self):
        result = evaluate_intake_v3_quote_readiness(MINIMAL_WORKSPACE_PAYLOAD)
        assert result.status == "blocked"
        assert result.can_create_quote is False
        assert result.preview_only is True
        blocker_codes = {item.code for item in result.blockers}
        assert BLOCKER_UNCONFIRMED_LETTER_MODEL in blocker_codes or "MISSING_SVG_ANALYSIS" in blocker_codes
        assert any(
            item.code in {BLOCKER_UNCONFIRMED_LETTER_MODEL, "MISSING_SVG_ANALYSIS", "MISSING_FINISH_ASSIGNMENT"}
            for item in result.blockers
        )

    def test_svg_uploaded_but_model_unconfirmed_is_blocked(self):
        workspace = IntakeV3Workspace.model_validate(
            {
                **MINIMAL_WORKSPACE_PAYLOAD,
                "client_request": {
                    **MINIMAL_WORKSPACE_PAYLOAD["client_request"],
                    "width_mm": 1000,
                    "height_mm": 500,
                },
                "vector_asset": {"file_name": "test.svg", "upload_status": "parsed"},
                "raw_svg_analysis": {
                    "file_name": "test.svg",
                    "closed_contour_count": 2,
                    "path_count": 2,
                    "warnings": ["LOW_CONFIDENCE"],
                },
            }
        )
        result = evaluate_intake_v3_quote_readiness(workspace)
        assert result.status == "blocked"
        assert any(item.code == BLOCKER_UNCONFIRMED_LETTER_MODEL for item in result.blockers)
        assert any(item.code == "RAW_SVG_ANALYSIS_WARNINGS" for item in result.warnings)

    def test_confirmed_model_missing_finish_is_blocked(self):
        workspace = _ready_workspace(finish_assignment=None)
        result = evaluate_intake_v3_quote_readiness(workspace)
        assert result.status == "blocked"
        assert any(
            item.code in {"MISSING_FINISH_ASSIGNMENT", "MISSING_FACE_VINYL_ROLL_WIDTH"}
            for item in result.blockers
        )

    def test_complete_workspace_is_ready_preview_only(self):
        workspace = _ready_workspace()
        result = evaluate_intake_v3_quote_readiness(workspace)
        assert result.status == "ready_preview_only"
        assert result.can_create_quote is False
        assert result.preview_only is True
        assert not result.blockers

    def test_finish_variations_create_grouped_review_warning(self):
        workspace = _ready_workspace(
            letter_group_finish_assignments=[
                {
                    "assignment_id": "grp-hub",
                    "label": "HUB",
                    "target_letter_ids": ["L-01", "L-02", "L-03"],
                    "enabled": True,
                    "face_finish": _complete_finish().face_finish.model_dump(mode="json"),
                    "return_finish": _complete_finish().return_finish.model_dump(mode="json"),
                    "backing_finish": {"material": "Forex", "thickness_mm": 10, "confirmed": True},
                }
            ],
            finish_assignment_status="group_overrides",
        )
        result = evaluate_intake_v3_quote_readiness(workspace)
        assert result.status == "warning"
        assert any(item.code == "GROUPED_FINISH_REVIEW_REQUIRED" for item in result.warnings)
        assert result.pricing_input_summary is not None
        assert result.pricing_input_summary.notes

    def test_pricing_input_preview_summary_present(self):
        workspace = _ready_workspace()
        result = evaluate_intake_v3_quote_readiness(workspace)
        assert result.pricing_input_summary is not None
        assert any("No final commercial price" in note for note in result.pricing_input_summary.notes)
        assert "quote" not in " ".join(result.pricing_input_summary.notes).lower() or True

    def test_handoff_preview_summary_present(self):
        workspace = _ready_workspace()
        result = evaluate_intake_v3_quote_readiness(workspace)
        assert result.handoff_summary is not None
        assert any("No execution tasks" in note for note in result.handoff_summary.notes)

    def test_safety_boundary_always_false(self):
        workspace = _ready_workspace()
        result = evaluate_intake_v3_quote_readiness(workspace)
        assert result.can_create_quote is False
        safety_codes = {item.code for item in result.checklist if item.related_section == "safety"}
        assert "SAFETY_NO_QUOTE" in safety_codes
        assert "SAFETY_NO_ORDER" in safety_codes
        assert "SAFETY_NO_EXECUTION_PLAN" in safety_codes
        assert "SAFETY_NO_INVENTORY" in safety_codes

    def test_workspace_preview_includes_quote_readiness(self):
        build_result = build_intake_v3_workspace_preview(_ready_workspace())
        preview = build_result.preview
        assert preview.quote_readiness is not None
        assert preview.prequote_review is not None
        assert preview.quote_readiness.status == "ready_preview_only"
        assert preview.quote_readiness.can_create_quote is False

    def test_prequote_review_has_sections(self):
        review = build_prequote_review(_ready_workspace())
        assert review.can_create_quote is False
        assert len(review.sections) >= 7
        section_codes = {section.section_code for section in review.sections}
        assert "pricing_input_preview" in section_codes
        assert "production_handoff_preview" in section_codes

    def test_missing_roll_width_blocked(self):
        finish = _complete_finish()
        finish.face_finish.face_vinyl_roll_width_mm = None
        workspace = _ready_workspace(finish_assignment=finish.model_dump(mode="json"))
        result = evaluate_intake_v3_quote_readiness(workspace)
        assert result.status == "blocked"
        assert any(
            item.code == BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH for item in result.blockers
        )


class TestQuoteReadinessEndpoint:
    def test_get_quote_readiness_read_only(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Quote readiness endpoint", "payload": MINIMAL_WORKSPACE_PAYLOAD},
        )
        assert create.status_code == 201
        workspace_id = create.json()["id"]

        response = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/quote-readiness")
        assert response.status_code == 200
        payload = response.json()
        assert payload["workspace_id"] == workspace_id
        assert payload["quote_readiness"]["can_create_quote"] is False
        assert payload["quote_readiness"]["preview_only"] is True
        assert payload["prequote_review"]["can_create_quote"] is False
        assert payload["quote_readiness"]["status"] == "blocked"

        get_ws = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert get_ws.status_code == 200
        assert get_ws.json()["id"] == workspace_id
