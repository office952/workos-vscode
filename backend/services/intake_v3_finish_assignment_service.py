"""Intake V3 per-letter / per-group finish assignments — payload only, no quote/order/runtime."""

from __future__ import annotations

import copy
import uuid
from typing import Any

from fastapi import HTTPException, status

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    BLOCKER_MISSING_RETURN_DEPTH,
    BLOCKER_MISSING_RETURN_PAINT_COLOR,
)
from schemas.intake_v3 import (
    BackingFinishSpec,
    ConfirmedProductionModel,
    FaceFinishSpec,
    FinishAssignment,
    FinishGroupAssignment,
    IntakeV3ApplyFinishAssignmentsRequest,
    IntakeV3FinishAssignmentSummary,
    IntakeV3FinishAssignmentTarget,
    IntakeV3FinishAssignmentValidationResult,
    IntakeV3LetterFinishAssignment,
    IntakeV3LetterGroupFinishAssignment,
    IntakeV3Workspace,
    ReturnFinishSpec,
)
from services.intake_v3_finish_material_service import validate_finish_assignment

WARNING_FINISH_ASSIGNMENT_VARIATIONS = "FINISH_ASSIGNMENT_VARIATIONS_PRESENT"


def _confirmed_model_from_payload(payload: dict[str, Any]) -> ConfirmedProductionModel | None:
    raw = payload.get("confirmed_production_model")
    if not isinstance(raw, dict):
        return None
    try:
        model = ConfirmedProductionModel.model_validate(raw)
    except Exception:
        return None
    if model.confirmation_status != "confirmed":
        return None
    return model


def _workspace_from_payload(payload: dict[str, Any]) -> IntakeV3Workspace:
    return IntakeV3Workspace.model_validate(payload)


def _hole_ids_from_model(model: ConfirmedProductionModel) -> set[str]:
    hole_ids: set[str] = set()
    cut = model.cut_contour_model
    if cut:
        for contour in cut.contours:
            if contour.role == "inner_hole":
                hole_ids.add(contour.contour_id)
    for letter in model.letter_model.letters if model.letter_model else []:
        hole_ids.update(letter.inner_hole_ids)
        hole_ids.update(letter.linked_inner_hole_ids)
    return hole_ids


def _letter_ids_from_model(model: ConfirmedProductionModel) -> set[str]:
    if model.letter_model and model.letter_model.letters:
        return {letter.letter_id for letter in model.letter_model.letters}
    return {f"L-{i:02d}" for i in range(1, model.letter_count + 1)}


def get_confirmed_letter_targets(payload: dict[str, Any]) -> list[IntakeV3FinishAssignmentTarget]:
    model = _confirmed_model_from_payload(payload)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "missing_confirmed_production_model",
                "message": "Confirm the production model before finish assignments.",
            },
        )

    targets: list[IntakeV3FinishAssignmentTarget] = []
    if model.letter_model and model.letter_model.letters:
        for letter in model.letter_model.letters:
            targets.append(
                IntakeV3FinishAssignmentTarget(
                    letter_id=letter.letter_id,
                    label=letter.label or letter.letter_id,
                    sequence_index=letter.sequence_index,
                    is_hole=False,
                )
            )
    else:
        for i in range(1, model.letter_count + 1):
            letter_id = f"L-{i:02d}"
            targets.append(
                IntakeV3FinishAssignmentTarget(
                    letter_id=letter_id,
                    label=str(i),
                    sequence_index=i,
                    is_hole=False,
                )
            )
    return targets


def _merge_face(base: FaceFinishSpec, override: FaceFinishSpec | None) -> FaceFinishSpec:
    if override is None:
        return base
    data = base.model_dump()
    for key, value in override.model_dump(exclude_unset=True).items():
        if value is not None:
            data[key] = value
    return FaceFinishSpec.model_validate(data)


def _merge_return(base: ReturnFinishSpec, override: ReturnFinishSpec | None) -> ReturnFinishSpec:
    if override is None:
        return base
    data = base.model_dump()
    for key, value in override.model_dump(exclude_unset=True).items():
        if value is not None:
            data[key] = value
    return ReturnFinishSpec.model_validate(data)


def _merge_backing(base: BackingFinishSpec, override: BackingFinishSpec | None) -> BackingFinishSpec:
    if override is None:
        return base
    data = base.model_dump()
    for key, value in override.model_dump(exclude_unset=True).items():
        if value is not None:
            data[key] = value
    return BackingFinishSpec.model_validate(data)


def _global_finish(payload: dict[str, Any]) -> FinishAssignment:
    finish = payload.get("finish_assignment")
    if isinstance(finish, dict):
        try:
            return FinishAssignment.model_validate(finish)
        except Exception:
            pass
    return FinishAssignment()


def _group_for_letter(
    letter_id: str,
    groups: list[IntakeV3LetterGroupFinishAssignment],
) -> IntakeV3LetterGroupFinishAssignment | None:
    for group in groups:
        if not group.enabled:
            continue
        if letter_id in group.target_letter_ids:
            return group
    return None


def _letter_override(
    letter_id: str,
    overrides: list[IntakeV3LetterFinishAssignment],
) -> IntakeV3LetterFinishAssignment | None:
    for item in overrides:
        if not item.enabled:
            continue
        if item.target_letter_id == letter_id:
            return item
    return None


def resolve_effective_finish_for_letter(
    payload: dict[str, Any],
    letter_id: str,
) -> dict[str, Any]:
    """Precedence: global → group → letter override."""
    global_finish = _global_finish(payload)
    groups = [
        IntakeV3LetterGroupFinishAssignment.model_validate(item)
        for item in payload.get("letter_group_finish_assignments", [])
        if isinstance(item, dict)
    ]
    letters = [
        IntakeV3LetterFinishAssignment.model_validate(item)
        for item in payload.get("letter_finish_assignments", [])
        if isinstance(item, dict)
    ]

    face = global_finish.face_finish
    ret = global_finish.return_finish
    backing = global_finish.backing_finish

    group = _group_for_letter(letter_id, groups)
    if group:
        face = _merge_face(face, group.face_finish)
        ret = _merge_return(ret, group.return_finish)
        backing = _merge_backing(backing, group.backing_finish)

    letter = _letter_override(letter_id, letters)
    if letter:
        face = _merge_face(face, letter.face_finish)
        ret = _merge_return(ret, letter.return_finish)

    return {
        "letter_id": letter_id,
        "face_finish": face.model_dump(mode="json"),
        "return_finish": ret.model_dump(mode="json"),
        "backing_finish": backing.model_dump(mode="json"),
        "face_vinyl_active": face.face_vinyl_active,
        "return_vinyl_active": ret.return_vinyl_active,
        "return_painted_active": ret.return_painted_active,
    }


def _normalize_group_assignments(
    groups: list[IntakeV3LetterGroupFinishAssignment],
) -> list[IntakeV3LetterGroupFinishAssignment]:
    normalized: list[IntakeV3LetterGroupFinishAssignment] = []
    seen_ids: set[str] = set()
    for group in groups:
        assignment_id = (group.assignment_id or "").strip() or f"grp-{uuid.uuid4().hex[:8]}"
        if assignment_id in seen_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "duplicate_assignment_id", "assignment_id": assignment_id},
            )
        seen_ids.add(assignment_id)
        normalized.append(group.model_copy(update={"assignment_id": assignment_id}))
    return normalized


def _normalize_letter_assignments(
    letters: list[IntakeV3LetterFinishAssignment],
) -> list[IntakeV3LetterFinishAssignment]:
    normalized: list[IntakeV3LetterFinishAssignment] = []
    seen_ids: set[str] = set()
    seen_letters: set[str] = set()
    for item in letters:
        assignment_id = (item.assignment_id or "").strip() or f"letter-{uuid.uuid4().hex[:8]}"
        if assignment_id in seen_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "duplicate_assignment_id", "assignment_id": assignment_id},
            )
        if item.target_letter_id in seen_letters:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "duplicate_letter_target",
                    "target_letter_id": item.target_letter_id,
                },
            )
        seen_ids.add(assignment_id)
        seen_letters.add(item.target_letter_id)
        normalized.append(item.model_copy(update={"assignment_id": assignment_id}))
    return normalized


def validate_finish_assignments(
    payload: dict[str, Any],
    request: IntakeV3ApplyFinishAssignmentsRequest,
) -> IntakeV3FinishAssignmentValidationResult:
    model = _confirmed_model_from_payload(payload)
    if model is None:
        return IntakeV3FinishAssignmentValidationResult(
            is_valid=False,
            blockers=["missing_confirmed_production_model"],
            warnings=[],
            summary="Confirmed production model is required.",
        )

    letter_ids = _letter_ids_from_model(model)
    hole_ids = _hole_ids_from_model(model)
    blockers: list[str] = []
    warnings: list[str] = []

    groups = _normalize_group_assignments(request.letter_group_finish_assignments)
    letters = _normalize_letter_assignments(request.letter_finish_assignments)
    global_finish = _global_finish(payload)

    all_targets: set[str] = set()
    for group in groups:
        for target in group.target_letter_ids:
            all_targets.add(target)
            if target in hole_ids or target.upper().startswith("C-HOLE"):
                blockers.append(f"hole_target_forbidden:{target}")
            elif target not in letter_ids:
                blockers.append(f"unknown_letter_id:{target}")

    for item in letters:
        target = item.target_letter_id
        if target in hole_ids or target.upper().startswith("C-HOLE"):
            blockers.append(f"hole_target_forbidden:{target}")
        elif target not in letter_ids:
            blockers.append(f"unknown_letter_id:{target}")

    if any(g.enabled for g in groups) or any(item.enabled for item in letters):
        warnings.append(WARNING_FINISH_ASSIGNMENT_VARIATIONS)

    # Validate effective finishes for enabled assignments
    probe_payload = copy.deepcopy(payload)
    probe_payload["letter_group_finish_assignments"] = [
        g.model_dump(mode="json") for g in groups
    ]
    probe_payload["letter_finish_assignments"] = [l.model_dump(mode="json") for l in letters]
    synced = _sync_finish_assignment_object(probe_payload, groups, letters, global_finish)
    probe_payload["finish_assignment"] = synced.model_dump(mode="json")
    workspace = _workspace_from_payload(probe_payload)
    validation = validate_finish_assignment(workspace)
    for issue in validation.blockers:
        blockers.append(issue.code)
    for issue in validation.warnings:
        warnings.append(issue.code)

    is_valid = len(blockers) == 0
    return IntakeV3FinishAssignmentValidationResult(
        is_valid=is_valid,
        blockers=blockers,
        warnings=warnings,
        summary="Finish assignments valid." if is_valid else f"{len(blockers)} blocker(s).",
    )


def _sync_finish_assignment_object(
    payload: dict[str, Any],
    groups: list[IntakeV3LetterGroupFinishAssignment],
    letters: list[IntakeV3LetterFinishAssignment],
    global_finish: FinishAssignment,
) -> FinishAssignment:
    enabled_groups = [group for group in groups if group.enabled]
    enabled_letters = [item for item in letters if item.enabled]

    finish_groups: list[FinishGroupAssignment] = []
    for group in enabled_groups:
        finish_groups.append(
            FinishGroupAssignment(
                group_id=group.assignment_id,
                group_label=group.label,
                letter_ids=list(group.target_letter_ids),
                face_finish=_merge_face(global_finish.face_finish, group.face_finish),
                return_finish=_merge_return(global_finish.return_finish, group.return_finish),
                backing_finish=_merge_backing(global_finish.backing_finish, group.backing_finish),
                confirmed_by_operator=True,
            )
        )

    mode = global_finish.assignment_mode or "all"
    if enabled_letters:
        mode = "letter_custom"
    elif enabled_groups:
        mode = "group"
    elif not enabled_groups and not enabled_letters:
        mode = global_finish.assignment_mode or "all"

    root_confirmed = global_finish.confirmed_by_operator
    if not root_confirmed:
        root_confirmed = (
            global_finish.face_finish.confirmed
            and global_finish.return_finish.confirmed
            and global_finish.backing_finish.confirmed
        )

    return global_finish.model_copy(
        update={
            "assignment_mode": mode,
            "groups": finish_groups,
            "confirmed_by_operator": root_confirmed or bool(enabled_groups or enabled_letters),
        }
    )


def _derive_assignment_status(
    groups: list[IntakeV3LetterGroupFinishAssignment],
    letters: list[IntakeV3LetterFinishAssignment],
) -> str:
    enabled_groups = [g for g in groups if g.enabled]
    enabled_letters = [l for l in letters if l.enabled]
    if enabled_groups and enabled_letters:
        return "mixed"
    if enabled_letters:
        return "letter_overrides"
    if enabled_groups:
        return "group_overrides"
    return "global_only"


def apply_finish_assignments_to_payload(
    payload: dict[str, Any],
    request: IntakeV3ApplyFinishAssignmentsRequest,
) -> tuple[dict[str, Any], IntakeV3FinishAssignmentSummary]:
    validation = validate_finish_assignments(payload, request)
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "invalid_finish_assignments",
                "blockers": validation.blockers,
                "warnings": validation.warnings,
            },
        )

    groups = _normalize_group_assignments(request.letter_group_finish_assignments)
    letters = _normalize_letter_assignments(request.letter_finish_assignments)
    global_finish = _global_finish(payload)

    updated = copy.deepcopy(payload)
    updated["letter_group_finish_assignments"] = [g.model_dump(mode="json") for g in groups]
    updated["letter_finish_assignments"] = [l.model_dump(mode="json") for l in letters]
    updated["finish_assignment_status"] = _derive_assignment_status(groups, letters)
    updated["finish_assignment"] = _sync_finish_assignment_object(
        updated, groups, letters, global_finish
    ).model_dump(mode="json")

    summary = summarize_finish_assignments(updated)
    return updated, summary


def summarize_finish_assignments(payload: dict[str, Any]) -> IntakeV3FinishAssignmentSummary:
    groups = payload.get("letter_group_finish_assignments") or []
    letters = payload.get("letter_finish_assignments") or []
    enabled_groups = [
        g for g in groups if isinstance(g, dict) and g.get("enabled", True)
    ]
    enabled_letters = [
        l for l in letters if isinstance(l, dict) and l.get("enabled", True)
    ]
    status_value = payload.get("finish_assignment_status") or "global_only"
    variations = bool(enabled_groups or enabled_letters)

    effective_samples: list[dict[str, Any]] = []
    model = _confirmed_model_from_payload(payload)
    if model:
        sample_ids = _letter_ids_from_model(model)
        for letter_id in sorted(sample_ids)[:5]:
            effective_samples.append(resolve_effective_finish_for_letter(payload, letter_id))

    return IntakeV3FinishAssignmentSummary(
        finish_assignment_status=status_value,
        group_assignment_count=len(enabled_groups),
        letter_override_count=len(enabled_letters),
        finish_variations_present=variations,
        assignment_summary=(
            f"{len(enabled_groups)} group assignment(s), {len(enabled_letters)} letter override(s)"
            if variations
            else "Using global finish only"
        ),
        warnings=[WARNING_FINISH_ASSIGNMENT_VARIATIONS] if variations else [],
        effective_finish_samples=effective_samples,
    )
