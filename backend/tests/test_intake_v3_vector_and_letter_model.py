"""Intake V3 vector & letter model — pure service and readiness integration tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from data_models.intake_v3_contracts import (
    BLOCKER_CUT_CONTOUR_COUNT_MISMATCH,
    BLOCKER_INNER_HOLE_WITHOUT_PARENT_LETTER,
    BLOCKER_UNCONFIRMED_LETTER_MODEL,
    HUB_MEDIA_PRODUCTION_LETTER_MODEL,
    WARNING_IGNORED_OBJECTS_PRESENT,
    WARNING_LOW_RAW_ANALYSIS_CONFIDENCE,
    WARNING_MANY_COLORS_DETECTED,
    WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH,
)
from schemas.intake_v3 import (
    CutContourItem,
    FaceFinishSpec,
    FinishAssignment,
    IntakeV3Workspace,
    LetterItem,
    RawSvgAnalysis,
    RawSvgObject,
    ReturnFinishSpec,
)
from services.intake_v3_readiness_service import evaluate_intake_v3_readiness
from services.intake_v3_vector_model_service import (
    build_confirmed_production_model,
    summarize_raw_svg_analysis,
    validate_confirmed_production_model,
)


def _hub_letters() -> list[LetterItem]:
    letters: list[LetterItem] = []
    for i in range(1, 19):
        letter_id = f"L-{i:02d}"
        outer_id = f"C-OUT-{i:02d}"
        hole_ids: list[str] = []
        if i <= 9:
            hole_ids = [f"C-HOLE-{i:02d}"]
        letters.append(
            LetterItem(
                letter_id=letter_id,
                label=chr(64 + ((i - 1) % 26) + 1),
                outer_contour_ids=[outer_id],
                inner_hole_ids=hole_ids,
                has_inner_holes=bool(hole_ids),
                sequence_index=i,
            )
        )
    return letters


def _hub_contours(*, include_last_outer: bool = True) -> list[CutContourItem]:
    contours: list[CutContourItem] = []
    outer_limit = 18 if include_last_outer else 17
    for i in range(1, outer_limit + 1):
        contours.append(
            CutContourItem(
                contour_id=f"C-OUT-{i:02d}",
                role="outer",
                parent_letter_id=f"L-{i:02d}",
                source_object_id=f"raw-{i:02d}",
                sequence_index=i,
            )
        )
    for i in range(1, 10):
        contours.append(
            CutContourItem(
                contour_id=f"C-HOLE-{i:02d}",
                role="inner_hole",
                parent_letter_id=f"L-{i:02d}",
                source_object_id=f"raw-hole-{i:02d}",
                sequence_index=100 + i,
            )
        )
    return contours


def build_hub_media_production_fixture(*, confirmed: bool = True):
    """HUB MEDIA PRODUCTION — 18 letters, 27 cut contours, 9 inner holes."""
    raw = RawSvgAnalysis(
        path_count=27,
        polygon_count=0,
        closed_contour_count=27,
        detected_color_count=2,
        confidence=0.82,
        view_box="0 0 9250 550",
    )
    letters = _hub_letters()
    contours = _hub_contours()
    model = build_confirmed_production_model(
        letters=letters,
        contours=contours,
        confirmed_by_user_id="operator-hub",
        confirmation_status="confirmed" if confirmed else "pending",
        source_raw_analysis_id="raw-hub-001",
    )
    return raw, model


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


def _ready_workspace(**overrides) -> IntakeV3Workspace:
    raw, model = build_hub_media_production_fixture(confirmed=True)
    payload = {
        "client_request": {
            "client_name": "Hub Media",
            "request_code": "INK-2026-0847",
            "width_mm": 9250,
            "height_mm": 550,
            "depth_mm": 60,
        },
        "raw_svg_analysis": raw.model_dump(),
        "confirmed_production_model": model.model_dump(),
        "finish_assignment": _complete_finish().model_dump(),
        "material_intent": {"estimate_status": "complete"},
    }
    payload.update(overrides)
    return IntakeV3Workspace.model_validate(payload)


class TestHub18279Valid:
    def test_hub_18_27_9_valid_no_blocker_warning_only_on_mismatch(self):
        raw, model = build_hub_media_production_fixture(confirmed=True)
        validation = validate_confirmed_production_model(model, raw=raw)

        assert model.letter_count == HUB_MEDIA_PRODUCTION_LETTER_MODEL["letter_count"]
        assert model.cut_contour_count == HUB_MEDIA_PRODUCTION_LETTER_MODEL["cut_contour_count"]
        assert model.inner_hole_count == HUB_MEDIA_PRODUCTION_LETTER_MODEL["inner_hole_count"]
        assert validation.is_valid is True
        assert validation.blockers == []
        assert any(w.code == WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH for w in validation.warnings)


class TestHolesAreNotLetters:
    def test_inner_holes_linked_to_parent_letters(self):
        _, model = build_hub_media_production_fixture()
        holes = [c for c in model.cut_contour_model.contours if c.role == "inner_hole"]
        assert len(holes) == 9
        assert model.letter_count == 18
        assert model.cut_contour_count == 27
        for hole in holes:
            assert hole.parent_letter_id is not None
            assert hole.contour_id not in {letter.letter_id for letter in model.letter_model.letters}


class TestUnconfirmedModelBlocksReadiness:
    def test_draft_model_blocks_quote(self):
        workspace = _ready_workspace()
        workspace.confirmed_production_model.confirmation_status = "pending"
        report = evaluate_intake_v3_readiness(workspace)
        assert report.can_create_quote is False
        assert any(b.code == BLOCKER_UNCONFIRMED_LETTER_MODEL for b in report.blockers)

    def test_absent_model_blocks_quote(self):
        workspace = _ready_workspace(confirmed_production_model=None)
        report = evaluate_intake_v3_readiness(workspace)
        assert report.can_create_quote is False
        assert any(b.code == BLOCKER_UNCONFIRMED_LETTER_MODEL for b in report.blockers)


class TestConfirmedCoherentMismatchWarningOnly:
    def test_raw_27_confirmed_18_warning_not_blocker(self):
        workspace = _ready_workspace()
        report = evaluate_intake_v3_readiness(workspace)
        assert report.can_create_quote is True
        assert any(w.code == WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH for w in report.warnings)
        assert not any(b.code == WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH for b in report.blockers)


class TestCutContourCountMismatchBlocks:
    def test_declared_27_included_26_blocks(self):
        letters = _hub_letters()
        contours = _hub_contours(include_last_outer=False)
        model = build_confirmed_production_model(
            letters=letters,
            contours=contours,
            confirmed_by_user_id="operator-1",
        )
        model.cut_contour_count = 27
        validation = validate_confirmed_production_model(model)
        assert validation.is_valid is False
        assert any(b.code == BLOCKER_CUT_CONTOUR_COUNT_MISMATCH for b in validation.blockers)


class TestInnerHoleWithoutParentBlocks:
    def test_inner_hole_missing_parent_blocks(self):
        letters = _hub_letters()[:1]
        contours = [
            CutContourItem(contour_id="C-OUT-01", role="outer", parent_letter_id="L-01"),
            CutContourItem(contour_id="C-HOLE-01", role="inner_hole", parent_letter_id=None),
        ]
        model = build_confirmed_production_model(letters=letters, contours=contours)
        validation = validate_confirmed_production_model(model)
        assert validation.is_valid is False
        assert any(b.code == BLOCKER_INNER_HOLE_WITHOUT_PARENT_LETTER for b in validation.blockers)


class TestIgnoredObjectsExcludedFromCutCount:
    def test_ignored_contours_not_counted(self):
        letters = _hub_letters()[:2]
        contours = [
            CutContourItem(contour_id="C-OUT-01", role="outer", parent_letter_id="L-01"),
            CutContourItem(contour_id="C-OUT-02", role="outer", parent_letter_id="L-02"),
            CutContourItem(
                contour_id="C-GUIDE-01",
                role="guide",
                include_in_cut=False,
            ),
            CutContourItem(
                contour_id="C-IGN-01",
                role="ignored",
                include_in_cut=False,
            ),
        ]
        model = build_confirmed_production_model(
            letters=letters,
            contours=contours,
            ignored_object_count=2,
        )
        validation = validate_confirmed_production_model(model)
        assert model.cut_contour_count == 2
        assert validation.is_valid is True
        assert any(w.code == WARNING_IGNORED_OBJECTS_PRESENT for w in validation.warnings)


class TestManyColorsWarning:
    def test_many_colors_detected_warning(self):
        raw = RawSvgAnalysis(
            polygon_count=40,
            closed_contour_count=40,
            detected_color_count=14,
            raw_objects=[
                RawSvgObject(
                    object_id=f"poly-{i}",
                    object_type="polygon",
                    color=f"#color-{i}",
                )
                for i in range(14)
            ],
        )
        summary = summarize_raw_svg_analysis(raw)
        assert summary["detected_color_count"] == 14
        letters = [LetterItem(letter_id="L-01", label="A", outer_contour_ids=["C-01"])]
        contours = [CutContourItem(contour_id="C-01", role="outer", parent_letter_id="L-01")]
        model = build_confirmed_production_model(
            letters=letters,
            contours=contours,
            confirmation_status="pending",
        )
        validation = validate_confirmed_production_model(model, raw=raw)
        assert any(w.code == WARNING_MANY_COLORS_DETECTED for w in validation.warnings)
        assert any(b.code == BLOCKER_UNCONFIRMED_LETTER_MODEL for b in validation.blockers)


class TestLowConfidenceWarning:
    def test_low_confidence_warning(self):
        raw = RawSvgAnalysis(closed_contour_count=5, confidence=0.3)
        letters = [LetterItem(letter_id="L-01", label="A", outer_contour_ids=["C-01"])]
        contours = [CutContourItem(contour_id="C-01", role="outer", parent_letter_id="L-01")]
        model = build_confirmed_production_model(letters=letters, contours=contours)
        validation = validate_confirmed_production_model(model, raw=raw)
        assert any(w.code == WARNING_LOW_RAW_ANALYSIS_CONFIDENCE for w in validation.warnings)


class TestReadinessHappyPathWithConfirmedVectorModel:
    def test_ready_for_quote_when_vector_model_valid(self):
        workspace = _ready_workspace()
        report = evaluate_intake_v3_readiness(workspace)
        assert not any(b.code == BLOCKER_UNCONFIRMED_LETTER_MODEL for b in report.blockers)
        assert report.can_create_quote is True
        assert report.status == "ready_for_quote"
