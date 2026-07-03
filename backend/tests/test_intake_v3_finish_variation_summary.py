"""Intake V3 finish variation summary — preview notes only, no CostEngine."""

from __future__ import annotations

from datetime import datetime, timezone

from schemas.intake_v3 import (
    ConfirmedProductionModel,
    CutContourItem,
    CutContourModel,
    FinishAssignment,
    FaceFinishSpec,
    IntakeV3Workspace,
    LetterItem,
    LetterModel,
    ReturnFinishSpec,
)
from services.intake_v3_finish_assignment_service import resolve_effective_finish_for_letter
from services.intake_v3_finish_variation_summary_service import build_finish_variation_summary
from services.intake_v3_pricing_input_adapter import build_pricing_input_candidate
from services.intake_v3_production_handoff_adapter import build_production_handoff_preview


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


def _payload(**overrides) -> dict:
    payload = {
        "client_request": {
            "client_name": "Hub Media",
            "request_code": "INK-2026-0847",
            "width_mm": 9250,
            "height_mm": 550,
        },
        "confirmed_production_model": _hub_confirmed_model().model_dump(mode="json"),
        "finish_assignment": _complete_finish().model_dump(mode="json"),
        "letter_group_finish_assignments": [],
        "letter_finish_assignments": [],
        "finish_assignment_status": "global_only",
        "material_intent": {"estimate_status": "complete"},
        "production_handoff": {"preview_only": True},
        "employee_preview_seed": {"non_executable": True, "preview_tasks": []},
    }
    payload.update(overrides)
    return payload


def _workspace(**overrides) -> IntakeV3Workspace:
    return IntakeV3Workspace.model_validate(_payload(**overrides))


class TestFinishVariationSummary:
    def test_no_assignments_uses_global_variation_only(self):
        summary = build_finish_variation_summary(_payload())
        assert summary.has_variations is False
        assert summary.total_letters == 18
        assert summary.default_letter_count == 18
        assert summary.group_assignment_count == 0
        assert summary.letter_override_count == 0
        assert len(summary.variations) == 1
        assert summary.variations[0].source_type == "global"
        assert summary.variations[0].letter_count == 18
        assert summary.pricing_preview_notes[0].startswith("Global finish applies")

    def test_group_assignment_creates_variation(self):
        summary = build_finish_variation_summary(
            _payload(
                letter_group_finish_assignments=[
                    {
                        "assignment_id": "grp-hub",
                        "label": "HUB",
                        "target_letter_ids": ["L-01", "L-02", "L-03"],
                        "face_finish": {
                            "finish_type": "oracal_8500",
                            "color_code": "527",
                            "color_name": "Pastel blue",
                        },
                        "enabled": True,
                    }
                ],
                finish_assignment_status="group_overrides",
            )
        )
        assert summary.has_variations is True
        group_variations = [v for v in summary.variations if v.source_type == "group"]
        assert len(group_variations) == 1
        assert group_variations[0].label == "HUB"
        assert group_variations[0].letter_count == 3
        assert summary.default_letter_count == 15
        assert any("grouped material/labor review" in note for note in summary.pricing_preview_notes)

    def test_letter_override_wins_over_group_without_duplicate_counting(self):
        summary = build_finish_variation_summary(
            _payload(
                letter_group_finish_assignments=[
                    {
                        "assignment_id": "grp-hub",
                        "label": "HUB",
                        "target_letter_ids": ["L-01", "L-02", "L-03"],
                        "face_finish": {
                            "finish_type": "oracal_8500",
                            "color_code": "527",
                            "color_name": "Pastel blue",
                        },
                        "enabled": True,
                    }
                ],
                letter_finish_assignments=[
                    {
                        "assignment_id": "letter-l01",
                        "target_letter_id": "L-01",
                        "face_finish": {
                            "finish_type": "oracal_8500",
                            "color_code": "302",
                            "color_name": "Red",
                        },
                        "enabled": True,
                    }
                ],
                finish_assignment_status="mixed",
            )
        )
        letter_vars = [v for v in summary.variations if v.source_type == "letter"]
        group_vars = [v for v in summary.variations if v.source_type == "group"]
        assert len(letter_vars) == 1
        assert letter_vars[0].letter_ids == ["L-01"]
        assert group_vars[0].letter_ids == ["L-02", "L-03"]
        assert summary.total_letters == 18
        assert sum(v.letter_count for v in summary.variations) == 18

    def test_disabled_assignment_ignored(self):
        summary = build_finish_variation_summary(
            _payload(
                letter_group_finish_assignments=[
                    {
                        "assignment_id": "grp-disabled",
                        "label": "DISABLED",
                        "target_letter_ids": ["L-01"],
                        "face_finish": {
                            "finish_type": "oracal_8500",
                            "color_code": "302",
                            "color_name": "Red",
                        },
                        "enabled": False,
                    }
                ],
            )
        )
        assert summary.has_variations is False
        assert summary.default_letter_count == 18
        assert all(v.source_type == "global" for v in summary.variations)

    def test_painted_variation_creates_operation_note(self):
        summary = build_finish_variation_summary(
            _payload(
                letter_group_finish_assignments=[
                    {
                        "assignment_id": "grp-paint",
                        "label": "PAINT",
                        "target_letter_ids": ["L-01"],
                        "return_finish": {
                            "finish_type": "painted",
                            "color_code": "9005",
                            "color_name": "Black",
                            "confirmed": True,
                        },
                        "enabled": True,
                    }
                ],
            )
        )
        painting = next(
            note for note in summary.operation_notes if note.operation_code == "return_painting"
        )
        assert painting.present is True
        effective = resolve_effective_finish_for_letter(
            _payload(
                letter_group_finish_assignments=[
                    {
                        "assignment_id": "grp-paint",
                        "label": "PAINT",
                        "target_letter_ids": ["L-01"],
                        "return_finish": {
                            "finish_type": "painted",
                            "color_code": "9005",
                            "color_name": "Black",
                            "confirmed": True,
                        },
                        "enabled": True,
                    }
                ],
            ),
            "L-01",
        )
        assert effective["return_painted_active"] is True
        assert effective["return_vinyl_active"] is False

    def test_wrapped_return_variation_creates_return_wrapping_note(self):
        summary = build_finish_variation_summary(
            _payload(
                letter_group_finish_assignments=[
                    {
                        "assignment_id": "grp-wrap",
                        "label": "WRAP",
                        "target_letter_ids": ["L-01"],
                        "return_finish": {
                            "finish_type": "oracal_wrapped",
                            "material_code": "Oracal 651",
                        },
                        "enabled": True,
                    }
                ],
            )
        )
        wrapping = next(
            note for note in summary.operation_notes if note.operation_code == "return_wrapping"
        )
        assert wrapping.present is True

    def test_pricing_input_includes_finish_variation_notes(self):
        workspace = _workspace(
            letter_group_finish_assignments=[
                {
                    "assignment_id": "grp-hub",
                    "label": "HUB",
                    "target_letter_ids": ["L-01", "L-02", "L-03"],
                    "face_finish": {"finish_type": "oracal_8500", "color_code": "527"},
                    "enabled": True,
                }
            ],
            finish_assignment_status="group_overrides",
        )
        result = build_pricing_input_candidate(workspace)
        assert result.candidate.requires_grouped_finish_review is True
        assert result.candidate.finish_variation_count >= 2
        assert any("grouped material/labor review" in note for note in result.candidate.finish_variation_notes)
        assert "unit_price" not in result.quote_input_payload
        assert "total_price" not in result.quote_input_payload

    def test_handoff_preview_includes_finish_variation_notes(self):
        workspace = _workspace(
            letter_group_finish_assignments=[
                {
                    "assignment_id": "grp-hub",
                    "label": "HUB",
                    "target_letter_ids": ["L-01", "L-02", "L-03"],
                    "face_finish": {"finish_type": "oracal_8500", "color_code": "527"},
                    "enabled": True,
                }
            ],
            finish_assignment_status="group_overrides",
        )
        result = build_production_handoff_preview(workspace)
        assert result.preview.non_executable is True
        assert result.preview.preview_only is True
        assert result.preview.requires_letter_group_visibility is True
        assert "HUB" in result.preview.group_labels
        assert any("letter IDs visible" in note for note in result.preview.finish_variation_handoff_notes)

    def test_no_side_effects(self):
        workspace = _workspace(
            letter_group_finish_assignments=[
                {
                    "assignment_id": "grp-safe",
                    "label": "SAFE",
                    "target_letter_ids": ["L-01"],
                    "face_finish": {"finish_type": "oracal_8500", "color_code": "527"},
                    "enabled": True,
                }
            ],
        )
        pricing = build_pricing_input_candidate(workspace)
        handoff = build_production_handoff_preview(workspace)
        assert pricing.quote_input_payload.get("inventory_mutation_allowed") is False
        assert handoff.preview.execution_plan_id is None
        for seed in handoff.preview.task_seeds:
            assert seed.execution_task_id is None
            assert seed.non_executable is True
