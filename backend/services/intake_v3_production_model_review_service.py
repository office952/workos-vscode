"""Intake V3 production model review — operator confirms counts from raw SVG analysis."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from schemas.intake_v3 import (
    ConfirmedProductionModel,
    CutContourItem,
    IntakeV3ConfirmProductionModelRequest,
    IntakeV3ProductionModelReviewCandidate,
    IntakeV3Workspace,
    LetterItem,
    RawSvgAnalysis,
)
from services.intake_v3_vector_model_service import build_confirmed_production_model

WARNING_COUNT_SUM_MISMATCH = "COUNT_SUM_MISMATCH"
WARNING_CONFIRM_WITHOUT_OPERATOR_NOTES = "CONFIRM_WITHOUT_OPERATOR_NOTES"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _raw_from_payload(payload: dict[str, Any]) -> RawSvgAnalysis | None:
    raw = payload.get("raw_svg_analysis")
    if not isinstance(raw, dict):
        return None
    try:
        return RawSvgAnalysis.model_validate(raw)
    except Exception:
        return None


def _source_marker(payload: dict[str, Any], raw: RawSvgAnalysis) -> str:
    vector = payload.get("vector_asset")
    if isinstance(vector, dict):
        file_hash = vector.get("file_hash")
        if file_hash:
            return str(file_hash)
        file_name = vector.get("file_name")
        if file_name:
            return str(file_name)
    if raw.file_name:
        return raw.file_name
    return "raw_svg_analysis"


def build_production_model_review_candidate_from_payload(
    payload: dict[str, Any],
) -> IntakeV3ProductionModelReviewCandidate | None:
    """Build review candidate from raw SVG analysis — not a confirmed model."""
    raw = _raw_from_payload(payload)
    if raw is None:
        return None

    return IntakeV3ProductionModelReviewCandidate(
        suggested_letter_count=None,
        suggested_cut_contour_count=raw.closed_contour_count or raw.path_count,
        suggested_inner_hole_count=raw.estimated_inner_hole_count,
        raw_path_count=raw.path_count,
        raw_closed_count=raw.closed_contour_count,
        detected_groups=list(raw.detected_groups),
        warnings=list(raw.warnings),
        confidence=raw.confidence,
        source="raw_svg_analysis",
        confirmed=False,
        template_code=PILOT_TEMPLATE_CODE,
    )


def validate_confirmed_production_model_input(
    request: IntakeV3ConfirmProductionModelRequest,
) -> list[str]:
    """Return validation error messages; empty list means input is acceptable."""
    errors: list[str] = []
    if not request.confirmed:
        errors.append("confirmed must be true for production model confirmation.")
    if request.letter_count <= 0:
        errors.append("letter_count must be greater than 0.")
    if request.cut_contour_count < request.letter_count:
        errors.append("cut_contour_count must be greater than or equal to letter_count.")
    if request.inner_hole_count < 0:
        errors.append("inner_hole_count cannot be negative.")
    return errors


def _collect_confirm_warnings(request: IntakeV3ConfirmProductionModelRequest) -> list[str]:
    warnings: list[str] = []
    expected_sum = request.letter_count + request.inner_hole_count
    if request.cut_contour_count != expected_sum:
        warnings.append(WARNING_COUNT_SUM_MISMATCH)
        if not (request.operator_notes or "").strip():
            warnings.append(WARNING_CONFIRM_WITHOUT_OPERATOR_NOTES)
    return warnings


def _build_placeholder_geometry(
    *,
    letter_count: int,
    inner_hole_count: int,
    cut_contour_count: int,
    ignored_object_ids: list[str],
) -> tuple[list[LetterItem], list[CutContourItem]]:
    """Synthetic letter/contour placeholders for count-based operator confirmation."""
    letters: list[LetterItem] = []
    contours: list[CutContourItem] = []

    for i in range(1, letter_count + 1):
        letter_id = f"L-{i:02d}"
        outer_id = f"C-OUT-{i:02d}"
        hole_ids: list[str] = []
        if i <= inner_hole_count:
            hole_ids = [f"C-HOLE-{i:02d}"]
        letters.append(
            LetterItem(
                letter_id=letter_id,
                label=str(i),
                outer_contour_ids=[outer_id],
                inner_hole_ids=hole_ids,
                has_inner_holes=bool(hole_ids),
                sequence_index=i,
            )
        )
        contours.append(
            CutContourItem(
                contour_id=outer_id,
                role="outer",
                parent_letter_id=letter_id,
                sequence_index=i,
            )
        )

    for i in range(1, inner_hole_count + 1):
        contours.append(
            CutContourItem(
                contour_id=f"C-HOLE-{i:02d}",
                role="inner_hole",
                parent_letter_id=f"L-{i:02d}",
                sequence_index=100 + i,
            )
        )

    included = len(contours)
    extra_needed = cut_contour_count - included
    for j in range(extra_needed):
        extra_id = f"C-EXTRA-{j + 1:02d}"
        source_id = ignored_object_ids[j] if j < len(ignored_object_ids) else None
        contours.append(
            CutContourItem(
                contour_id=extra_id,
                role="ignored",
                include_in_cut=True,
                source_object_id=source_id,
                sequence_index=200 + j,
            )
        )

    return letters, contours


def apply_confirmed_production_model_to_payload(
    payload: dict[str, Any],
    request: IntakeV3ConfirmProductionModelRequest,
    *,
    confirmed_by_user_id: str,
) -> tuple[dict[str, Any], ConfirmedProductionModel, list[str]]:
    """Apply operator-confirmed counts to workspace payload; raw analysis is preserved."""
    raw = _raw_from_payload(payload)
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "missing_raw_svg_analysis", "message": "Upload and analyze SVG first."},
        )

    errors = validate_confirmed_production_model_input(request)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_production_model_input", "messages": errors},
        )

    warnings = _collect_confirm_warnings(request)
    letters, contours = _build_placeholder_geometry(
        letter_count=request.letter_count,
        inner_hole_count=request.inner_hole_count,
        cut_contour_count=request.cut_contour_count,
        ignored_object_ids=list(request.ignored_object_ids),
    )

    model = build_confirmed_production_model(
        letters=letters,
        contours=contours,
        ignored_object_count=len(request.ignored_object_ids),
        confirmed_by_user_id=confirmed_by_user_id,
        confirmation_status="confirmed",
        operator_notes=request.operator_notes,
        source_raw_analysis_id=_source_marker(payload, raw),
        count_confirmed=True,
    )
    model = model.model_copy(
        update={
            "letter_count": request.letter_count,
            "cut_contour_count": request.cut_contour_count,
            "inner_hole_count": request.inner_hole_count,
            "ignored_object_ids": list(request.ignored_object_ids),
        }
    )

    updated = dict(payload)
    updated["confirmed_production_model"] = model.model_dump(mode="json")
    updated["production_model_status"] = "confirmed"
    updated["production_model_confirmed_at"] = _utcnow().isoformat()
    updated["production_model_confirmed_by_user_id"] = confirmed_by_user_id
    # raw_svg_analysis and vector_asset intentionally preserved.

    return updated, model, warnings


def require_review_candidate_or_raise(payload: dict[str, Any]) -> IntakeV3ProductionModelReviewCandidate:
    candidate = build_production_model_review_candidate_from_payload(payload)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "missing_raw_svg_analysis",
                "message": "Upload and analyze an SVG before reviewing the production model.",
            },
        )
    return candidate


def workspace_has_confirmed_production_model(workspace: IntakeV3Workspace) -> bool:
    model = workspace.confirmed_production_model
    return model is not None and model.confirmation_status == "confirmed"
