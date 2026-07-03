"""Intake V3 native layer finish assignments — payload only, no quote/order/runtime."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_BACKING_FINISH_CONFIRMATION,
    BLOCKER_MISSING_FACE_FINISH_CONFIRMATION,
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT,
    BLOCKER_MISSING_RETURN_DEPTH,
    BLOCKER_MISSING_RETURN_FINISH_CONFIRMATION,
    BLOCKER_MISSING_RETURN_PAINT_COLOR,
    BLOCKER_PENDING_LAYER_FINISH,
    BLOCKER_UNCONFIRMED_LAYER_FINISH,
    BLOCKER_MISSING_PRINTED_ARTWORK_CONTOUR_DECISION,
    BLOCKER_MISSING_PRINTED_ARTWORK_LAMINATE_TYPE,
    BLOCKER_MISSING_PRINTED_ARTWORK_PRINT_METHOD,
    BLOCKER_MISSING_PRINTED_ARTWORK_SETUP,
    BLOCKER_UNCONFIRMED_PRINTED_ARTWORK,
)
from schemas.intake_v3 import (
    BackingFinishSpec,
    FaceFinishSpec,
    FinishAssignment,
    IntakeV3ApplyLayerFinishAssignmentsRequest,
    IntakeV3LayerFinishAssignment,
    IntakeV3LayerFinishAssignmentSummary,
    IntakeV3LayerFinishAssignmentTarget,
    IntakeV3LayerFinishAssignmentValidationResult,
    IntakeV3LayerFinishPreviewItem,
    IntakeV3LayerRoleConfirmationSnapshot,
    IntakeV3PrintedArtworkFinishSpec,
    IntakeV3Workspace,
    LayerFinishAssignmentStatus,
    LayerFinishTargetType,
    ReturnFinishSpec,
    VectorModelIssue,
)

LAYER_FINISH_REQUIRING_ROLES: frozenset[str] = frozenset({"face", "return", "backing", "vinyl"})
ARTWORK_FINISH_ROLES: frozenset[str] = frozenset(
    {"printed_artwork", "logo", "artwork", "policromie"}
)
LAYER_FINISH_EXEMPT_ROLES: frozenset[str] = frozenset(
    {
        "inner_hole",
        "ignore",
        "reference",
        "unknown",
        "drill",
        "support_panel",
        "frame",
        "bevel",
    }
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _positive(value: float | int | None) -> bool:
    return value is not None and float(value) > 0


def uses_native_layer_finish(payload: dict[str, Any]) -> bool:
    assignments = payload.get("layer_finish_assignments")
    status_value = payload.get("layer_finish_assignment_status")
    if isinstance(assignments, list) and len(assignments) > 0:
        return True
    return status_value in {"missing", "partial", "complete"}


def is_artwork_role(role: str | None) -> bool:
    return (role or "unknown").lower() in ARTWORK_FINISH_ROLES


def resolve_finish_target_type(role: str | None) -> LayerFinishTargetType:
    token = (role or "unknown").lower()
    if token in {"face", "vinyl"}:
        return "face"
    if token == "return":
        return "return"
    if token == "backing":
        return "backing"
    if token in {"printed_artwork", "logo", "policromie", "artwork"}:
        return "printed_artwork"
    if token in {"ignore", "reference"}:
        return "ignore"
    if token in LAYER_FINISH_EXEMPT_ROLES:
        return "technical"
    return "technical"


def layer_requires_finish(role: str | None, confirmation_state: str | None = None) -> bool:
    if confirmation_state == "ignored":
        return False
    token = (role or "unknown").lower()
    if token in LAYER_FINISH_EXEMPT_ROLES or token in {"ignore", "reference", "unknown"}:
        return False
    if is_artwork_role(token):
        return True
    return token in LAYER_FINISH_REQUIRING_ROLES


def _issue(code: str, message: str, *, target_field: str | None = None) -> VectorModelIssue:
    return VectorModelIssue(code=code, severity="blocker", message=message, target_field=target_field)


def _layer_snapshot(payload: dict[str, Any]) -> IntakeV3LayerRoleConfirmationSnapshot | None:
    raw = payload.get("layer_role_confirmation_snapshot")
    if isinstance(raw, dict):
        try:
            return IntakeV3LayerRoleConfirmationSnapshot.model_validate(raw)
        except Exception:
            return None
    return None


def _existing_assignments(payload: dict[str, Any]) -> dict[str, IntakeV3LayerFinishAssignment]:
    raw = payload.get("layer_finish_assignments")
    if not isinstance(raw, list):
        return {}
    result: dict[str, IntakeV3LayerFinishAssignment] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            assignment = IntakeV3LayerFinishAssignment.model_validate(item)
        except Exception:
            continue
        result[assignment.layer_key] = assignment
    return result


def draft_layer_finish_assignments(payload: dict[str, Any]) -> list[IntakeV3LayerFinishAssignment]:
    snapshot = _layer_snapshot(payload)
    if snapshot is None or not snapshot.layers:
        return list(_existing_assignments(payload).values())

    existing = _existing_assignments(payload)
    drafts: list[IntakeV3LayerFinishAssignment] = []
    for layer in snapshot.layers:
        role = layer.confirmed_role or layer.auto_role
        target_type = resolve_finish_target_type(role)
        current = existing.get(layer.layer_key)
        if current is not None:
            drafts.append(
                current.model_copy(
                    update={
                        "layer_name": current.layer_name or layer.layer_name,
                        "confirmed_role": current.confirmed_role or role,
                        "finish_target_type": current.finish_target_type or target_type,
                    }
                )
            )
            continue
        artwork_finish = None
        if target_type == "printed_artwork" or is_artwork_role(role):
            area_sqm = None
            if layer.metrics and layer.metrics.area_mm2 is not None:
                area_sqm = round(float(layer.metrics.area_mm2) / 1_000_000, 6)
            artwork_finish = IntakeV3PrintedArtworkFinishSpec(enabled=True, area_sqm=area_sqm)
        drafts.append(
            IntakeV3LayerFinishAssignment(
                layer_key=layer.layer_key,
                layer_name=layer.layer_name,
                confirmed_role=role,
                finish_target_type=target_type,
                printed_artwork_finish=artwork_finish,
                enabled=layer_requires_finish(role, layer.confirmation_state),
            )
        )
    return drafts


def get_layer_finish_targets(payload: dict[str, Any]) -> list[IntakeV3LayerFinishAssignmentTarget]:
    snapshot = _layer_snapshot(payload)
    if snapshot is None or not snapshot.layers:
        return []
    targets: list[IntakeV3LayerFinishAssignmentTarget] = []
    for layer in snapshot.layers:
        role = layer.confirmed_role or layer.auto_role
        targets.append(
            IntakeV3LayerFinishAssignmentTarget(
                layer_key=layer.layer_key,
                layer_name=layer.layer_name,
                confirmed_role=role,
                finish_target_type=resolve_finish_target_type(role),
                requires_finish=layer_requires_finish(role, layer.confirmation_state),
                confirmation_state=layer.confirmation_state,
            )
        )
    return targets


def _validate_face_spec(
    label: str,
    face: FaceFinishSpec | None,
    *,
    is_confirmed: bool,
) -> list[VectorModelIssue]:
    if face is None:
        return [
            _issue(
                BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT,
                f"Layer {label} requires face finish setup.",
                target_field="face_finish",
            )
        ]
    issues: list[VectorModelIssue] = []
    if not is_confirmed and not face.confirmed:
        issues.append(
            _issue(
                BLOCKER_UNCONFIRMED_LAYER_FINISH,
                f"Layer {label} face finish is not confirmed.",
                target_field="is_confirmed",
            )
        )
    if face.face_vinyl_active and not _positive(face.face_vinyl_roll_width_mm):
        issues.append(
            _issue(
                BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
                f"Layer {label} requires face vinyl roll width.",
                target_field="face_finish.face_vinyl_roll_width_mm",
            )
        )
    if face.face_vinyl_active and not (face.color_code or face.color_name):
        issues.append(
            _issue(
                BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT,
                f"Layer {label} requires face color selection.",
                target_field="face_finish.color_code",
            )
        )
    return issues


def _validate_return_spec(
    label: str,
    ret: ReturnFinishSpec | None,
    *,
    is_confirmed: bool,
) -> list[VectorModelIssue]:
    if ret is None:
        return [
            _issue(
                BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT,
                f"Layer {label} requires return/cant finish setup.",
                target_field="return_finish",
            )
        ]
    issues: list[VectorModelIssue] = []
    if not is_confirmed and not ret.confirmed:
        issues.append(
            _issue(
                BLOCKER_UNCONFIRMED_LAYER_FINISH,
                f"Layer {label} return finish is not confirmed.",
                target_field="is_confirmed",
            )
        )
    if ret.return_vinyl_active and not _positive(ret.return_depth_mm):
        issues.append(
            _issue(
                BLOCKER_MISSING_RETURN_DEPTH,
                f"Layer {label} requires return depth.",
                target_field="return_finish.return_depth_mm",
            )
        )
    if ret.return_painted_active and not (ret.color_code or ret.color_name):
        issues.append(
            _issue(
                BLOCKER_MISSING_RETURN_PAINT_COLOR,
                f"Layer {label} requires return paint color.",
                target_field="return_finish.color_code",
            )
        )
    return issues


def _validate_backing_spec(
    label: str,
    backing: BackingFinishSpec | None,
    *,
    is_confirmed: bool,
) -> list[VectorModelIssue]:
    if backing is None:
        return [
            _issue(
                BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT,
                f"Layer {label} requires backing finish setup.",
                target_field="backing_finish",
            )
        ]
    if not is_confirmed and not backing.confirmed:
        return [
            _issue(
                BLOCKER_UNCONFIRMED_LAYER_FINISH,
                f"Layer {label} backing finish is not confirmed.",
                target_field="is_confirmed",
            )
        ]
    return []


def _validate_printed_artwork_spec(
    label: str,
    artwork: IntakeV3PrintedArtworkFinishSpec | None,
    *,
    is_confirmed: bool,
) -> list[VectorModelIssue]:
    if artwork is None or not artwork.enabled:
        return [
            _issue(
                BLOCKER_MISSING_PRINTED_ARTWORK_SETUP,
                f'Layer "{label}" requires printed artwork setup.',
                target_field="printed_artwork_finish.enabled",
            )
        ]
    issues: list[VectorModelIssue] = []
    if not artwork.print_method:
        issues.append(
            _issue(
                BLOCKER_MISSING_PRINTED_ARTWORK_PRINT_METHOD,
                f'Layer "{label}" requires a print method.',
                target_field="printed_artwork_finish.print_method",
            )
        )
    if artwork.laminate_enabled and not artwork.laminate_type:
        issues.append(
            _issue(
                BLOCKER_MISSING_PRINTED_ARTWORK_LAMINATE_TYPE,
                f'Layer "{label}" requires laminate type when laminate is enabled.',
                target_field="printed_artwork_finish.laminate_type",
            )
        )
    if artwork.contour_cut is None:
        issues.append(
            _issue(
                BLOCKER_MISSING_PRINTED_ARTWORK_CONTOUR_DECISION,
                f'Layer "{label}" requires an explicit contour cut decision.',
                target_field="printed_artwork_finish.contour_cut",
            )
        )
    if not is_confirmed and not artwork.is_confirmed:
        issues.append(
            _issue(
                BLOCKER_UNCONFIRMED_PRINTED_ARTWORK,
                f'Layer "{label}" needs printed artwork setup confirmation.',
                target_field="printed_artwork_finish.is_confirmed",
            )
        )
    return issues


def validate_layer_finish_assignment_entry(
    assignment: IntakeV3LayerFinishAssignment,
) -> list[VectorModelIssue]:
    if not assignment.enabled:
        return []
    role = (assignment.confirmed_role or "").lower()
    if not layer_requires_finish(role):
        return []
    label = assignment.layer_name or assignment.layer_key
    target = assignment.finish_target_type or resolve_finish_target_type(role)
    if target == "face":
        return _validate_face_spec(label, assignment.face_finish, is_confirmed=assignment.is_confirmed)
    if target == "return":
        return _validate_return_spec(label, assignment.return_finish, is_confirmed=assignment.is_confirmed)
    if target == "backing":
        return _validate_backing_spec(label, assignment.backing_finish, is_confirmed=assignment.is_confirmed)
    if target == "printed_artwork" or is_artwork_role(role):
        return _validate_printed_artwork_spec(
            label,
            assignment.printed_artwork_finish,
            is_confirmed=assignment.is_confirmed,
        )
    return []


def collect_layer_finish_issues(payload: dict[str, Any]) -> tuple[list[VectorModelIssue], list[VectorModelIssue]]:
    if not uses_native_layer_finish(payload):
        return [], []
    assignments = draft_layer_finish_assignments(payload)
    blockers: list[VectorModelIssue] = []
    for assignment in assignments:
        blockers.extend(validate_layer_finish_assignment_entry(assignment))
    return blockers, []


def _derive_layer_finish_status(
    assignments: list[IntakeV3LayerFinishAssignment],
) -> LayerFinishAssignmentStatus:
    required = [a for a in assignments if a.enabled and layer_requires_finish(a.confirmed_role)]
    if not required:
        return "complete"
    confirmed = [a for a in required if a.is_confirmed]
    if not confirmed:
        return "missing"
    if len(confirmed) < len(required):
        return "partial"
    pending = [a for a in required if validate_layer_finish_assignment_entry(a)]
    if pending:
        return "partial"
    return "complete"


def _preview_item(assignment: IntakeV3LayerFinishAssignment) -> IntakeV3LayerFinishPreviewItem:
    role = assignment.confirmed_role
    requires = layer_requires_finish(role)
    if not requires:
        status: str = "not_required"
    elif assignment.is_confirmed and not validate_layer_finish_assignment_entry(assignment):
        status = "confirmed"
    else:
        status = "pending"
    material_code = assignment.material_code
    color_code = assignment.color_code
    color_name = assignment.color_name
    target = assignment.finish_target_type or resolve_finish_target_type(role)
    if target == "face" and assignment.face_finish:
        material_code = material_code or assignment.face_finish.material_code
        color_code = color_code or assignment.face_finish.color_code
        color_name = color_name or assignment.face_finish.color_name
    elif target == "return" and assignment.return_finish:
        material_code = material_code or assignment.return_finish.material_code
        color_code = color_code or assignment.return_finish.color_code
        color_name = color_name or assignment.return_finish.color_name
    elif target == "backing" and assignment.backing_finish:
        material_code = material_code or assignment.backing_finish.material
    elif (target == "printed_artwork" or is_artwork_role(role)) and assignment.printed_artwork_finish:
        artwork = assignment.printed_artwork_finish
        material_code = artwork.media_code or artwork.media_family
    return IntakeV3LayerFinishPreviewItem(
        layer_key=assignment.layer_key,
        layer_name=assignment.layer_name,
        confirmed_role=role,
        finish_target_type=target,
        material_code=material_code,
        color_code=color_code,
        color_name=color_name,
        is_confirmed=assignment.is_confirmed,
        confirmation_status=status,  # type: ignore[arg-type]
        print_method=assignment.printed_artwork_finish.print_method
        if assignment.printed_artwork_finish
        else None,
        laminate_type=assignment.printed_artwork_finish.laminate_type
        if assignment.printed_artwork_finish and assignment.printed_artwork_finish.laminate_enabled
        else (
            assignment.printed_artwork_finish.laminate_type
            if assignment.printed_artwork_finish
            and not assignment.printed_artwork_finish.laminate_enabled
            and assignment.printed_artwork_finish.laminate_type
            else None
        ),
        contour_cut=assignment.printed_artwork_finish.contour_cut
        if assignment.printed_artwork_finish
        else None,
        white_ink=assignment.printed_artwork_finish.white_ink if assignment.printed_artwork_finish else None,
        white_backing=assignment.printed_artwork_finish.white_backing
        if assignment.printed_artwork_finish
        else None,
        area_sqm=assignment.printed_artwork_finish.area_sqm if assignment.printed_artwork_finish else None,
        waste_percent=assignment.printed_artwork_finish.waste_percent
        if assignment.printed_artwork_finish
        else None,
        artwork_notes=assignment.printed_artwork_finish.notes if assignment.printed_artwork_finish else None,
    )


def summarize_layer_finish_assignments(payload: dict[str, Any]) -> IntakeV3LayerFinishAssignmentSummary:
    assignments = draft_layer_finish_assignments(payload)
    preview_items = [_preview_item(a) for a in assignments]
    required = [a for a in assignments if a.enabled and layer_requires_finish(a.confirmed_role)]
    confirmed = [a for a in required if a.is_confirmed and not validate_layer_finish_assignment_entry(a)]
    pending = [a for a in required if a not in confirmed]
    not_required = [a for a in assignments if not layer_requires_finish(a.confirmed_role)]
    status = payload.get("layer_finish_assignment_status")
    if not isinstance(status, str) or status not in {"missing", "partial", "complete"}:
        status = _derive_layer_finish_status(assignments)
    summary = (
        f"{len(confirmed)}/{len(required)} productive layers confirmed"
        if required
        else "No productive layer finish required"
    )
    return IntakeV3LayerFinishAssignmentSummary(
        layer_finish_assignment_status=status,  # type: ignore[arg-type]
        assignment_count=len(assignments),
        confirmed_count=len(confirmed),
        pending_count=len(pending),
        not_required_count=len(not_required),
        assignment_summary=summary,
        preview_items=preview_items,
    )


def _sync_global_finish_from_layer_assignments(
    payload: dict[str, Any],
    assignments: list[IntakeV3LayerFinishAssignment],
) -> dict[str, Any]:
    updated = copy.deepcopy(payload)
    finish = FinishAssignment()
    all_required_confirmed = True
    for assignment in assignments:
        if not assignment.enabled:
            continue
        role = (assignment.confirmed_role or "").lower()
        target = assignment.finish_target_type or resolve_finish_target_type(role)
        if target == "printed_artwork" or is_artwork_role(role):
            continue
        if target == "face" and assignment.face_finish is not None:
            finish.face_finish = assignment.face_finish
        elif target == "return" and assignment.return_finish is not None:
            finish.return_finish = assignment.return_finish
        elif target == "backing" and assignment.backing_finish is not None:
            finish.backing_finish = assignment.backing_finish
        if layer_requires_finish(role) and (
            not assignment.is_confirmed or validate_layer_finish_assignment_entry(assignment)
        ):
            all_required_confirmed = False
    finish.confirmed_by_operator = all_required_confirmed and bool(
        [a for a in assignments if layer_requires_finish(a.confirmed_role)]
    )
    updated["finish_assignment"] = finish.model_dump(mode="json")
    return updated


def validate_layer_finish_assignments(
    payload: dict[str, Any],
    request: IntakeV3ApplyLayerFinishAssignmentsRequest,
) -> IntakeV3LayerFinishAssignmentValidationResult:
    snapshot = _layer_snapshot(payload)
    known_keys = {layer.layer_key for layer in snapshot.layers} if snapshot else set()
    blockers: list[str] = []
    warnings: list[str] = []

    for assignment in request.layer_finish_assignments:
        if snapshot and assignment.layer_key not in known_keys:
            blockers.append(f"unknown_layer_key:{assignment.layer_key}")
            continue
        blockers.extend(item.code for item in validate_layer_finish_assignment_entry(assignment))

    is_valid = len(blockers) == 0
    summary = "Layer finish assignments valid." if is_valid else "Layer finish assignments blocked."
    return IntakeV3LayerFinishAssignmentValidationResult(
        is_valid=is_valid,
        blockers=sorted(set(blockers)),
        warnings=warnings,
        summary=summary,
    )


def apply_layer_finish_assignments_to_payload(
    payload: dict[str, Any],
    request: IntakeV3ApplyLayerFinishAssignmentsRequest,
    *,
    confirmed_by: str | None = None,
) -> tuple[dict[str, Any], IntakeV3LayerFinishAssignmentSummary]:
    validation = validate_layer_finish_assignments(payload, request)
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "invalid_layer_finish_assignments",
                "validation": validation.model_dump(mode="json"),
            },
        )

    updated = copy.deepcopy(payload)
    normalized: list[IntakeV3LayerFinishAssignment] = []
    for item in request.layer_finish_assignments:
        data = item.model_dump(mode="json")
        if item.is_confirmed and not item.confirmed_at:
            data["confirmed_at"] = _utcnow_iso()
        if item.is_confirmed and confirmed_by:
            data["confirmed_by"] = confirmed_by
        artwork_raw = data.get("printed_artwork_finish")
        if isinstance(artwork_raw, dict) and item.is_confirmed:
            if not artwork_raw.get("confirmed_at"):
                artwork_raw["confirmed_at"] = _utcnow_iso()
            if confirmed_by:
                artwork_raw["confirmed_by"] = confirmed_by
            artwork_raw["is_confirmed"] = True
            data["printed_artwork_finish"] = artwork_raw
        normalized.append(IntakeV3LayerFinishAssignment.model_validate(data))

    status_value = _derive_layer_finish_status(normalized)
    updated["layer_finish_assignments"] = [a.model_dump(mode="json") for a in normalized]
    updated["layer_finish_assignment_status"] = status_value
    updated = _sync_global_finish_from_layer_assignments(updated, normalized)
    summary = summarize_layer_finish_assignments(updated)
    return updated, summary
