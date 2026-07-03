"""Intake V3 finish & material workflow — pure in-memory services (no DB, no pricing, no inventory)."""

from __future__ import annotations

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_BACKING_FINISH_CONFIRMATION,
    BLOCKER_MISSING_FACE_FINISH_CONFIRMATION,
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    BLOCKER_MISSING_FINISH_ASSIGNMENT,
    BLOCKER_MISSING_GROUP_FINISH_ASSIGNMENT,
    BLOCKER_MISSING_RETURN_DEPTH,
    BLOCKER_MISSING_RETURN_FINISH_CONFIRMATION,
    BLOCKER_MISSING_RETURN_PAINT_COLOR,
    BLOCKER_UNSUPPORTED_FINISH_MODE,
    WARNING_FACE_VINYL_AFTER_RETURN_PAINTING,
    WARNING_LETTER_CUSTOM_FINISH_ADVANCED_MODE,
    WARNING_MATERIAL_ESTIMATE_ONLY,
    WARNING_NO_SHARED_SUPPORT_PSU_PACKED,
    WARNING_RETURN_PAINT_REQUIRES_FACE_PROTECTION,
)
from schemas.intake_v3 import (
    AccessoryIntent,
    ConfirmedProductionModel,
    EstimateStatus,
    FaceFinishSpec,
    FinishAssignment,
    FinishGroupAssignment,
    FinishMaterialValidationResult,
    IntakeV3Workspace,
    LedMaterialIntent,
    MaterialIntent,
    OperationFlags,
    PowerSupplyIntent,
    ReturnFinishSpec,
    RollMaterialIntent,
    SheetMaterialIntent,
    SupportContext,
    VectorModelIssue,
)


def _positive(value: float | int | None) -> bool:
    try:
        return value is not None and float(value) > 0
    except (TypeError, ValueError):
        return False


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


def _face_finish_active(face: FaceFinishSpec) -> bool:
    return face.enabled and face.finish_type not in {"none", "white_face"}


def _return_finish_active(ret: ReturnFinishSpec) -> bool:
    return ret.finish_type not in {"none", "raw", "prefinished", "raw_material"}


def _backing_finish_active(group: FinishGroupAssignment) -> bool:
    backing = group.backing_finish
    return bool(backing.material) or _positive(backing.thickness_mm)


def _group_needs_confirmation(group: FinishGroupAssignment) -> bool:
    return (
        _face_finish_active(group.face_finish)
        or _return_finish_active(group.return_finish)
        or _backing_finish_active(group)
    )


def derive_operation_flags_from_finishes(
    finish: FinishAssignment,
    support_context: SupportContext | None = None,
) -> OperationFlags:
    """Derive operation catalog flags from finish assignment."""
    ctx = support_context or SupportContext()
    flags = OperationFlags()
    primary = finish.active_groups()[0] if finish.active_groups() else None
    if primary is None:
        return flags

    face = primary.face_finish
    ret = primary.return_finish

    flags.return_vinyl_application_required = ret.requires_vinyl_application
    flags.return_painting_after_assembly_required = ret.requires_painting_after_assembly
    flags.face_vinyl_application_required = face.face_vinyl_active
    flags.face_vinyl_after_return_painting = (
        face.face_vinyl_active and ret.return_painted_active
    )

    if ctx.illuminated:
        if ctx.shared_support:
            flags.electrical_source_mounting_allowed = True
        else:
            flags.psu_packed_at_packaging = True
            flags.electrical_source_mounting_allowed = False

    return flags


def validate_finish_assignment(
    finish_or_workspace: FinishAssignment | IntakeV3Workspace,
    *,
    support_context: SupportContext | None = None,
) -> FinishMaterialValidationResult:
    """Validate finish assignment; returns blockers, warnings, and operation flags."""
    if isinstance(finish_or_workspace, IntakeV3Workspace):
        finish = finish_or_workspace.finish_assignment
        if finish is None:
            return FinishMaterialValidationResult(
                is_valid=True,
                summary="No finish assignment present.",
            )
    else:
        finish = finish_or_workspace

    blockers: list[VectorModelIssue] = []
    warnings: list[VectorModelIssue] = []

    if finish.assignment_mode not in {"all", "group", "letter_custom"}:
        blockers.append(
            _issue(
                code=BLOCKER_UNSUPPORTED_FINISH_MODE,
                severity="blocker",
                message=f"Mod finisaj necunoscut: {finish.assignment_mode}.",
                target_field="assignment_mode",
            )
        )

    if finish.assignment_mode == "letter_custom":
        warnings.append(
            _issue(
                code=WARNING_LETTER_CUSTOM_FINISH_ADVANCED_MODE,
                severity="warning",
                message="Mod letter_custom este avansat — necesită confirmare explicită pe literă.",
                target_field="assignment_mode",
            )
        )

    for group in finish.active_groups():
        label = group.group_label or group.group_id

        if _face_finish_active(group.face_finish):
            if not group.confirmed_by_operator and not group.face_finish.confirmed:
                blockers.append(
                    _issue(
                        code=BLOCKER_MISSING_FACE_FINISH_CONFIRMATION,
                        severity="blocker",
                        message=f"Finisaj față neconfirmat pentru {label}.",
                        target_field=f"groups.{group.group_id}.face_finish.confirmed",
                    )
                )
            if group.face_finish.face_vinyl_active and not _positive(
                group.face_finish.face_vinyl_roll_width_mm
            ):
                blockers.append(
                    _issue(
                        code=BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
                        severity="blocker",
                        message=f"Lipsește lățimea rolei pentru față ({label}).",
                        target_field="face_vinyl_roll_width_mm",
                    )
                )

        if _return_finish_active(group.return_finish):
            if not group.confirmed_by_operator and not group.return_finish.confirmed:
                blockers.append(
                    _issue(
                        code=BLOCKER_MISSING_RETURN_FINISH_CONFIRMATION,
                        severity="blocker",
                        message=f"Finisaj cant neconfirmat pentru {label}.",
                        target_field=f"groups.{group.group_id}.return_finish.confirmed",
                    )
                )
            if group.return_finish.return_vinyl_active and not _positive(
                group.return_finish.return_depth_mm
            ):
                blockers.append(
                    _issue(
                        code=BLOCKER_MISSING_RETURN_DEPTH,
                        severity="blocker",
                        message=f"Lipsește adâncimea cantului pentru {label}.",
                        target_field="return_depth_mm",
                    )
                )
            if group.return_finish.return_painted_active and not (
                group.return_finish.color_code or group.return_finish.color_name
            ):
                blockers.append(
                    _issue(
                        code=BLOCKER_MISSING_RETURN_PAINT_COLOR,
                        severity="blocker",
                        message=f"Lipsește culoarea vopselei cant pentru {label}.",
                        target_field="return_finish.color_code",
                    )
                )
            if group.return_finish.return_painted_active:
                warnings.append(
                    _issue(
                        code=WARNING_RETURN_PAINT_REQUIRES_FACE_PROTECTION,
                        severity="warning",
                        message=f"Vopsirea cantului necesită protecție față pentru {label}.",
                        target_field=f"groups.{group.group_id}.return_finish.finish_type",
                    )
                )

        if _backing_finish_active(group):
            if not group.confirmed_by_operator and not group.backing_finish.confirmed:
                blockers.append(
                    _issue(
                        code=BLOCKER_MISSING_BACKING_FINISH_CONFIRMATION,
                        severity="blocker",
                        message=f"Finisaj spate neconfirmat pentru {label}.",
                        target_field=f"groups.{group.group_id}.backing_finish.confirmed",
                    )
                )

        if _group_needs_confirmation(group) and not group.confirmed_by_operator:
            if finish.assignment_mode == "group":
                blockers.append(
                    _issue(
                        code=BLOCKER_MISSING_GROUP_FINISH_ASSIGNMENT,
                        severity="blocker",
                        message=f"Grupul {label} nu are finisaj confirmat de operator.",
                        target_field=f"groups.{group.group_id}.confirmed_by_operator",
                    )
                )
            blockers.append(
                _issue(
                    code=BLOCKER_MISSING_FINISH_ASSIGNMENT,
                    severity="blocker",
                    message=f"Finisajul pentru {label} nu este confirmat de operator.",
                    target_field=f"groups.{group.group_id}.confirmed_by_operator",
                )
            )

    flags = derive_operation_flags_from_finishes(finish, support_context)

    if flags.face_vinyl_after_return_painting:
        warnings.append(
            _issue(
                code=WARNING_FACE_VINYL_AFTER_RETURN_PAINTING,
                severity="warning",
                message=(
                    "Colantarea feței se face după vopsirea cantului, uscare și îndepărtare protecție."
                ),
                target_field="face_finish.finish_type",
            )
        )

    ctx = support_context or SupportContext()
    if ctx.illuminated and not ctx.shared_support:
        warnings.append(
            _issue(
                code=WARNING_NO_SHARED_SUPPORT_PSU_PACKED,
                severity="warning",
                message="Fără suport comun: sursele calculate se includ în colet la ambalare.",
                target_field="support_context.shared_support",
            )
        )

    is_valid = len(blockers) == 0
    summary = "Finisaje valide." if is_valid else f"{len(blockers)} blocker(i) la finisaje."
    return FinishMaterialValidationResult(
        is_valid=is_valid,
        blockers=blockers,
        warnings=warnings,
        summary=summary,
        operation_flags=flags,
    )


def derive_material_intent(
    workspace_or_model: IntakeV3Workspace | ConfirmedProductionModel,
    finish_assignment: FinishAssignment | None = None,
    *,
    support_context: SupportContext | None = None,
    illuminated: bool = True,
) -> MaterialIntent:
    """Derive conceptual MaterialIntent from confirmed model and finishes — estimate only."""
    if isinstance(workspace_or_model, IntakeV3Workspace):
        workspace = workspace_or_model
        confirmed = workspace.confirmed_production_model
        finish = finish_assignment or workspace.finish_assignment
        letter_count = confirmed.letter_count if confirmed else 0
    else:
        confirmed = workspace_or_model
        finish = finish_assignment
        letter_count = confirmed.letter_count

    ctx = support_context or SupportContext(illuminated=illuminated)
    rolls: list[RollMaterialIntent] = []
    sheets: list[SheetMaterialIntent] = []
    leds: list[LedMaterialIntent] = []
    psus: list[PowerSupplyIntent] = []
    accessories: list[AccessoryIntent] = []

    primary = finish.active_groups()[0] if finish and finish.active_groups() else None

    if primary:
        face = primary.face_finish
        ret = primary.return_finish
        backing = primary.backing_finish

        if face.face_vinyl_active:
            rolls.append(
                RollMaterialIntent(
                    material=face.material_code or "Oracal face vinyl",
                    material_family=face.material_family or "oracal_roll",
                    roll_width_mm=face.face_vinyl_roll_width_mm,
                    source_finish="face",
                    color_code=face.color_code,
                    color_name=face.color_name,
                    estimate_status="requires_geometry",
                )
            )

        if ret.return_vinyl_active:
            rolls.append(
                RollMaterialIntent(
                    material=ret.material_code or "Oracal return vinyl",
                    material_family=ret.material_family or "oracal_roll",
                    source_finish="return",
                    color_code=ret.color_code,
                    color_name=ret.color_name,
                    estimate_status="requires_geometry",
                )
            )

        sheets.append(
            SheetMaterialIntent(
                material="Plexiglas",
                thickness_mm=None,
                source_component="face",
                remaining_label="Rest placă estimat",
                estimate_status="requires_geometry",
            )
        )

        backing_material = backing.material or "Forex"
        backing_thickness = backing.thickness_mm or 10.0
        sheets.append(
            SheetMaterialIntent(
                material=backing_material,
                thickness_mm=backing_thickness,
                source_component="backing",
                remaining_label="Rest placă estimat",
                estimate_status="requires_geometry",
            )
        )

        if ret.return_painted_active:
            accessories.append(
                AccessoryIntent(
                    name="Folie protecție față pentru vopsire cant",
                    category="face_protection",
                    strict_inventory_tracking=False,
                    estimate_status="estimated",
                )
            )

    accessories.extend(
        [
            AccessoryIntent(
                name="Autoforante mici cu cap îngropat",
                category="assembly_fastener",
                strict_inventory_tracking=False,
                estimate_status="estimated",
            ),
            AccessoryIntent(
                name="Folie stretch ambalare",
                category="packaging",
                strict_inventory_tracking=False,
                estimate_status="estimated",
            ),
        ]
    )

    if ctx.illuminated:
        leds.append(
            LedMaterialIntent(
                module_type="LED module volumetric",
                estimated_module_count=None,
                power_w_per_module=None,
                estimate_status="owner_input_required",
            )
        )
        psu = PowerSupplyIntent(
            quantity=1,
            packaging_required=not ctx.shared_support,
            mounted_on_shared_support=ctx.shared_support,
            source_rule=(
                "no_shared_support_psu_at_packaging"
                if not ctx.shared_support
                else "shared_support_electrical_task_allowed"
            ),
        )
        if ctx.shared_support:
            psu.delivery_mode = "mount_on_shared_support"
        else:
            psu.delivery_mode = "pack_with_job"
        psus.append(psu)

    has_geometry = letter_count > 0
    top_status: EstimateStatus = "not_started"
    if primary and has_geometry:
        top_status = "partial"
    elif primary:
        top_status = "partial"

    intent = MaterialIntent(
        roll_materials=rolls,
        sheet_materials=sheets,
        led_materials=leds,
        power_supplies=psus,
        accessories=accessories,
        estimate_status=top_status,
    )
    return intent


def material_intent_warnings(intent: MaterialIntent) -> list[VectorModelIssue]:
    """Warnings for incomplete material estimates — not blockers for quote."""
    warnings: list[VectorModelIssue] = []
    incomplete = any(
        item.estimate_status in {"requires_geometry", "owner_input_required"}
        for item in (
            list(intent.roll_materials)
            + list(intent.sheet_materials)
            + list(intent.led_materials)
            + list(intent.accessories)
        )
    )
    if incomplete or intent.estimate_status in {"not_started", "partial"}:
        warnings.append(
            _issue(
                code=WARNING_MATERIAL_ESTIMATE_ONLY,
                severity="warning",
                message="MaterialIntent conține estimări conceptuale — fără mutație inventory.",
                target_field="material_intent.estimate_status",
            )
        )
    return warnings
