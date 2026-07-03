"""Intake V3 vector & letter model — pure in-memory services (no DB, no SVG parser)."""

from __future__ import annotations

from datetime import datetime, timezone

from data_models.intake_v3_contracts import (
    BLOCKER_CUT_CONTOUR_COUNT_MISMATCH,
    BLOCKER_INNER_HOLE_WITHOUT_PARENT_LETTER,
    BLOCKER_LETTER_WITHOUT_OUTER_CONTOUR,
    BLOCKER_MISSING_CUT_CONTOUR_MODEL,
    BLOCKER_MISSING_LETTER_COUNT,
    BLOCKER_UNCONFIRMED_LETTER_MODEL,
    LOW_RAW_ANALYSIS_CONFIDENCE_THRESHOLD,
    MANY_COLORS_DETECTED_THRESHOLD,
    WARNING_IGNORED_OBJECTS_PRESENT,
    WARNING_LOW_RAW_ANALYSIS_CONFIDENCE,
    WARNING_MANY_COLORS_DETECTED,
    WARNING_POSSIBLE_GUIDES_DETECTED,
    WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH,
    WARNING_UNKNOWN_CONTOUR_ROLES_PRESENT,
)
from schemas.intake_v3 import (
    ConfirmationStatus,
    ConfirmedProductionModel,
    CutContourItem,
    CutContourModel,
    GroupingMode,
    LetterItem,
    LetterModel,
    RawSvgAnalysis,
    VectorModelIssue,
    VectorModelValidationResult,
)


def _issue(
    *,
    code: str,
    severity: str,
    message: str,
    target_field: str | None = None,
) -> VectorModelIssue:
    return VectorModelIssue(
        code=code,
        severity=severity,  # type: ignore[arg-type]
        message=message,
        target_field=target_field,
    )


def _count_included_cut_contours(contours: list[CutContourItem]) -> int:
    return sum(
        1
        for contour in contours
        if contour.include_in_cut and contour.role not in {"guide", "ignored"}
    )


def summarize_raw_svg_analysis(raw: RawSvgAnalysis) -> dict[str, object]:
    """Return a compact summary of raw SVG detection (not production truth)."""
    object_summary: list[dict[str, object]] = []
    for obj in raw.raw_objects[:20]:
        object_summary.append(
            {
                "object_id": obj.object_id,
                "object_type": obj.object_type,
                "raw_role_guess": obj.raw_role_guess,
                "closed_contours": obj.closed_contours,
                "color": obj.color,
            }
        )
    return {
        "path_count": raw.path_count,
        "polygon_count": raw.polygon_count,
        "rect_count": raw.rect_count,
        "closed_contour_count": raw.closed_contour_count,
        "detected_color_count": raw.detected_color_count,
        "detected_groups": list(raw.detected_groups),
        "view_box": raw.view_box,
        "warnings": list(raw.warnings),
        "confidence": raw.confidence,
        "raw_object_count": len(raw.raw_objects),
        "raw_object_summary": object_summary,
    }


def build_confirmed_production_model(
    *,
    letters: list[LetterItem],
    contours: list[CutContourItem],
    grouping_mode: GroupingMode = "none",
    ignored_object_count: int = 0,
    confirmed_by_user_id: str | None = None,
    confirmation_status: ConfirmationStatus = "confirmed",
    operator_notes: str | None = None,
    source_raw_analysis_id: str | None = None,
    count_confirmed: bool = True,
) -> ConfirmedProductionModel:
    """Build operator-confirmed production model from explicit letter/contour input."""
    outer_count = sum(1 for c in contours if c.role == "outer" and c.include_in_cut)
    hole_count = sum(1 for c in contours if c.role == "inner_hole" and c.include_in_cut)
    cut_count = _count_included_cut_contours(contours)

    letter_model = LetterModel(
        letters=letters,
        count_confirmed=count_confirmed,
        grouping_mode=grouping_mode,
    )
    cut_contour_model = CutContourModel(
        contours=contours,
        outer_contour_count=outer_count,
        inner_hole_count=hole_count,
        cut_contour_count=cut_count,
    )

    return ConfirmedProductionModel(
        confirmed_by_user_id=confirmed_by_user_id,
        confirmed_at=datetime.now(timezone.utc) if confirmation_status == "confirmed" else None,
        letter_count=len(letters),
        cut_contour_count=cut_count,
        inner_hole_count=hole_count,
        ignored_object_count=ignored_object_count,
        letter_model=letter_model,
        cut_contour_model=cut_contour_model,
        confirmation_status=confirmation_status,
        source_raw_analysis_id=source_raw_analysis_id,
        operator_notes=operator_notes,
    )


def validate_confirmed_production_model(
    model: ConfirmedProductionModel,
    *,
    raw: RawSvgAnalysis | None = None,
) -> VectorModelValidationResult:
    """Validate confirmed production model coherence; raw mismatch is warning only."""
    blockers: list[VectorModelIssue] = []
    warnings: list[VectorModelIssue] = []

    if model.confirmation_status != "confirmed":
        blockers.append(
            _issue(
                code=BLOCKER_UNCONFIRMED_LETTER_MODEL,
                severity="blocker",
                message="Modelul de producție nu este confirmat de operator.",
                target_field="confirmation_status",
            )
        )

    if model.letter_count <= 0:
        blockers.append(
            _issue(
                code=BLOCKER_MISSING_LETTER_COUNT,
                severity="blocker",
                message="Numărul de litere confirmate lipsește sau este zero.",
                target_field="letter_count",
            )
        )

    cut_model = model.cut_contour_model
    if cut_model is None or not cut_model.contours:
        blockers.append(
            _issue(
                code=BLOCKER_MISSING_CUT_CONTOUR_MODEL,
                severity="blocker",
                message="Modelul de contururi CNC lipsește.",
                target_field="cut_contour_model",
            )
        )
    else:
        included_count = _count_included_cut_contours(cut_model.contours)
        if model.cut_contour_count != included_count:
            blockers.append(
                _issue(
                    code=BLOCKER_CUT_CONTOUR_COUNT_MISMATCH,
                    severity="blocker",
                    message=(
                        f"cut_contour_count={model.cut_contour_count} nu corespunde "
                        f"contururilor incluse={included_count}."
                    ),
                    target_field="cut_contour_count",
                )
            )

        for contour in cut_model.contours:
            if (
                contour.role == "inner_hole"
                and contour.include_in_cut
                and not contour.parent_letter_id
            ):
                blockers.append(
                    _issue(
                        code=BLOCKER_INNER_HOLE_WITHOUT_PARENT_LETTER,
                        severity="blocker",
                        message=(
                            f"Golul interior {contour.contour_id} nu are literă-mamă asociată."
                        ),
                        target_field=f"cut_contour_model.contours.{contour.contour_id}.parent_letter_id",
                    )
                )

        if any(c.role == "unknown" for c in cut_model.contours):
            warnings.append(
                _issue(
                    code=WARNING_UNKNOWN_CONTOUR_ROLES_PRESENT,
                    severity="warning",
                    message="Există contururi cu rol necunoscut în modelul confirmat.",
                    target_field="cut_contour_model.contours",
                )
            )

        if any(c.role == "guide" for c in cut_model.contours):
            warnings.append(
                _issue(
                    code=WARNING_POSSIBLE_GUIDES_DETECTED,
                    severity="warning",
                    message="Există contururi marcate ca ghid în modelul confirmat.",
                    target_field="cut_contour_model.contours",
                )
            )

    letter_model = model.letter_model
    if letter_model and letter_model.letters and cut_model and cut_model.contours:
        outer_by_letter: dict[str, int] = {}
        for contour in cut_model.contours:
            if contour.role == "outer" and contour.include_in_cut and contour.parent_letter_id:
                outer_by_letter[contour.parent_letter_id] = (
                    outer_by_letter.get(contour.parent_letter_id, 0) + 1
                )
        for letter in letter_model.letters:
            has_outer = (
                letter.outer_contour_ids
                or outer_by_letter.get(letter.letter_id, 0) > 0
            )
            if not has_outer:
                blockers.append(
                    _issue(
                        code=BLOCKER_LETTER_WITHOUT_OUTER_CONTOUR,
                        severity="blocker",
                        message=f"Litera {letter.letter_id} nu are contur exterior asociat.",
                        target_field=f"letter_model.letters.{letter.letter_id}.outer_contour_ids",
                    )
                )

    if model.ignored_object_count > 0:
        warnings.append(
            _issue(
                code=WARNING_IGNORED_OBJECTS_PRESENT,
                severity="warning",
                message=f"{model.ignored_object_count} obiecte ignorate în modelul confirmat.",
                target_field="ignored_object_count",
            )
        )

    if raw is not None:
        if raw.closed_contour_count > 0 and raw.closed_contour_count != model.letter_count:
            warnings.append(
                _issue(
                    code=WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH,
                    severity="warning",
                    message=(
                        "Analiza brută și modelul confirmat diferă la număr de contururi/litere — "
                        "operatorul a confirmat modelul de producție."
                    ),
                    target_field="letter_count",
                )
            )
        if raw.confidence is not None and raw.confidence < LOW_RAW_ANALYSIS_CONFIDENCE_THRESHOLD:
            warnings.append(
                _issue(
                    code=WARNING_LOW_RAW_ANALYSIS_CONFIDENCE,
                    severity="warning",
                    message="Încrederea analizei brute SVG este scăzută.",
                    target_field="raw_svg_analysis.confidence",
                )
            )
        if raw.detected_color_count >= MANY_COLORS_DETECTED_THRESHOLD:
            warnings.append(
                _issue(
                    code=WARNING_MANY_COLORS_DETECTED,
                    severity="warning",
                    message="Vectorul brut conține multe culori detectate — necesită confirmare operator.",
                    target_field="raw_svg_analysis.detected_color_count",
                )
            )
        guide_guesses = sum(1 for obj in raw.raw_objects if obj.raw_role_guess == "guide_candidate")
        if guide_guesses > 0:
            warnings.append(
                _issue(
                    code=WARNING_POSSIBLE_GUIDES_DETECTED,
                    severity="warning",
                    message="Analiza brută a detectat posibile ghiduri în vector.",
                    target_field="raw_svg_analysis.raw_objects",
                )
            )

    is_valid = len(blockers) == 0
    summary = "Model confirmat valid." if is_valid else f"{len(blockers)} blocker(i) în modelul confirmat."
    return VectorModelValidationResult(
        is_valid=is_valid,
        blockers=blockers,
        warnings=warnings,
        summary=summary,
    )
