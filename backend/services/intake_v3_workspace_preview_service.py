"""Intake V3 workspace end-to-end preview — composes readiness, adapters, boundary flags."""

from __future__ import annotations

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_DIMENSIONS,
    BLOCKER_UNCONFIRMED_LETTER_MODEL,
    WARNING_MATERIAL_ESTIMATE_ONLY,
    WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH,
)
from schemas.intake_v3 import (
    IntakeV3BoundaryFlags,
    IntakeV3FinishSummary,
    IntakeV3LightingSummary,
    IntakeV3MaterialSummary,
    IntakeV3PreviewBuildResult,
    IntakeV3PreviewSectionStatus,
    IntakeV3VectorSummary,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
    ReadinessIssue,
)
from services.intake_v3_finish_material_service import (
    derive_material_intent,
    material_intent_warnings,
    validate_finish_assignment,
)
from services.intake_v3_pricing_input_adapter import (
    _resolve_support_mode,
    build_pricing_input_candidate,
)
from services.intake_v3_production_handoff_adapter import build_production_handoff_preview
from services.intake_v3_finish_assignment_service import summarize_finish_assignments
from services.intake_v3_finish_variation_summary_service import build_finish_variation_summary
from services.intake_v3_quote_readiness_service import (
    build_prequote_review,
    evaluate_intake_v3_quote_readiness,
)
from services.intake_v3_quote_creation_dry_run_service import (
    is_quote_creation_dry_run_available,
)
from services.intake_v3_commercial_quote_bridge_service import (
    commercial_quote_bridge_status_label,
    is_commercial_quote_bridge_available,
)
from services.intake_v3_quote_creation_final_blocker_service import (
    is_quote_creation_enablement_available,
    quote_creation_enablement_status_label,
)
from services.intake_v3_real_quote_creation_enablement_readiness_service import (
    is_real_quote_creation_enablement_readiness_available,
    real_quote_creation_enablement_readiness_status_label,
)
from services.intake_v3_readiness_service import evaluate_intake_v3_readiness
from services.intake_v3_vector_model_service import (
    summarize_raw_svg_analysis,
    validate_confirmed_production_model,
)
from services.intake_v3_workspace_field_editor_service import resolve_workspace_support_context

SECTION_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("request", "Cerere / workspace"),
    ("template", "Template produs"),
    ("vector", "Vector & model litere"),
    ("dimensions", "Dimensiuni"),
    ("finish", "Finisaje"),
    ("material_intent", "Material intent"),
    ("readiness", "Readiness"),
    ("quote_readiness", "Quote readiness gate"),
    ("pricing_input", "Pricing input preview"),
    ("production_handoff", "Production handoff preview"),
)


def build_boundary_flags(_workspace: IntakeV3Workspace | None = None) -> IntakeV3BoundaryFlags:
    """Preview shell boundary — never allows quote/order/plan/inventory/mobile actions."""
    return IntakeV3BoundaryFlags()


def _workspace_id(workspace: IntakeV3Workspace) -> str:
    code = (workspace.client_request.request_code or "").strip()
    if code:
        return code
    client = (workspace.client_request.client_name or "").strip()
    if client:
        return f"WS-{client.replace(' ', '-')[:32]}"
    return "WS-DRAFT"


def _issue_codes(issues: list[ReadinessIssue]) -> list[str]:
    return [item.code for item in issues]


def _section_from_issues(
    *,
    section_code: str,
    label: str,
    blockers: list[str],
    warnings: list[str],
    summary: str,
    default_missing: bool = False,
) -> IntakeV3PreviewSectionStatus:
    if default_missing and not blockers and not warnings:
        return IntakeV3PreviewSectionStatus(
            section_code=section_code,
            label=label,
            status="missing",
            summary=summary or "Date lipsă",
        )
    if blockers:
        status = "blocked"
    elif warnings:
        status = "warning"
    elif section_code in {"pricing_input", "production_handoff"}:
        status = "preview"
    else:
        status = "ready"
    return IntakeV3PreviewSectionStatus(
        section_code=section_code,
        label=label,
        status=status,  # type: ignore[arg-type]
        blockers=blockers,
        warnings=warnings,
        summary=summary,
    )


def _build_vector_summary(workspace: IntakeV3Workspace) -> IntakeV3VectorSummary:
    raw_summary: dict[str, object] = {}
    if workspace.raw_svg_analysis is not None:
        raw_summary = summarize_raw_svg_analysis(workspace.raw_svg_analysis)

    confirmed = workspace.confirmed_production_model
    mismatch = any(
        w.code == WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH
        for w in (workspace.readiness_report.warnings if workspace.readiness_report else [])
    )
    if not mismatch and workspace.readiness_report:
        mismatch = WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH in _issue_codes(
            workspace.readiness_report.warnings
        )

    if confirmed is None:
        return IntakeV3VectorSummary(raw_summary=raw_summary)

    return IntakeV3VectorSummary(
        raw_summary=raw_summary,
        confirmed_letter_count=confirmed.letter_count,
        confirmed_cut_contour_count=confirmed.cut_contour_count,
        confirmed_inner_hole_count=confirmed.inner_hole_count,
        confirmation_status=confirmed.confirmation_status,
        raw_confirmed_mismatch_warning=mismatch,
    )


def _build_finish_summary(workspace: IntakeV3Workspace) -> IntakeV3FinishSummary:
    from services.intake_v3_layer_finish_assignment_service import summarize_layer_finish_assignments

    finish = workspace.finish_assignment
    if finish is None or not finish.active_groups():
        base = IntakeV3FinishSummary()
    else:
        group = finish.active_groups()[0]
        base = IntakeV3FinishSummary(
            assignment_mode=finish.assignment_mode,
            face_finish_type=group.face_finish.finish_type,
            return_finish_type=group.return_finish.finish_type,
            backing_material=group.backing_finish.material,
            backing_thickness_mm=group.backing_finish.thickness_mm,
            face_vinyl_roll_width_mm=group.face_finish.face_vinyl_roll_width_mm,
            return_depth_mm=group.return_finish.return_depth_mm,
            confirmed_by_operator=finish.confirmed_by_operator,
        )

    assignment_summary = summarize_finish_assignments(workspace.model_dump(mode="json"))
    layer_summary = summarize_layer_finish_assignments(workspace.model_dump(mode="json"))
    return base.model_copy(
        update={
            "finish_assignment_status": assignment_summary.finish_assignment_status,
            "group_assignment_count": assignment_summary.group_assignment_count,
            "letter_override_count": assignment_summary.letter_override_count,
            "finish_variations_present": assignment_summary.finish_variations_present,
            "assignment_summary": assignment_summary.assignment_summary,
            "layer_finish_assignment_status": layer_summary.layer_finish_assignment_status,
            "layer_finish_assignment_count": layer_summary.assignment_count,
            "layer_finish_confirmed_count": layer_summary.confirmed_count,
            "layer_finish_preview": layer_summary.preview_items,
        }
    )


def _build_lighting_summary(workspace: IntakeV3Workspace) -> IntakeV3LightingSummary:
    from services.intake_v3_lighting_plan_service import summarize_lighting_plan

    return summarize_lighting_plan(workspace.model_dump(mode="json")).preview


def _build_material_summary(workspace: IntakeV3Workspace) -> IntakeV3MaterialSummary:
    material = derive_material_intent(workspace)
    return IntakeV3MaterialSummary(
        roll_materials=len(material.roll_materials),
        sheet_materials=len(material.sheet_materials),
        led_materials=len(material.led_materials),
        power_supplies=len(material.power_supplies),
        accessories=len(material.accessories),
        estimate_status=material.estimate_status,
        inventory_mutation_allowed=False,
    )


def summarize_workspace_sections(workspace: IntakeV3Workspace) -> list[IntakeV3PreviewSectionStatus]:
    """Build per-section status cards for UI shell."""
    readiness = evaluate_intake_v3_readiness(workspace)
    pricing = build_pricing_input_candidate(workspace)
    handoff = build_production_handoff_preview(workspace)
    support_mode = _resolve_support_mode(workspace)

    readiness_blockers = _issue_codes(readiness.blockers)
    readiness_warnings = _issue_codes(readiness.warnings)

    request_blockers: list[str] = []
    if not workspace.client_request.client_name.strip():
        request_blockers.append("MISSING_CLIENT_NAME")
    if not workspace.client_request.request_code.strip():
        request_blockers.append("MISSING_REQUEST_CODE")

    vector_blockers = [
        code
        for code in readiness_blockers
        if code
        in {
            BLOCKER_UNCONFIRMED_LETTER_MODEL,
            "MISSING_LETTER_COUNT",
            "MISSING_CUT_CONTOUR_MODEL",
            "CUT_CONTOUR_COUNT_MISMATCH",
        }
    ]
    vector_warnings = [
        code
        for code in readiness_warnings
        if code.startswith("RAW_") or code in {WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH}
    ]

    dimension_blockers = [
        code for code in readiness_blockers if code == BLOCKER_MISSING_DIMENSIONS
    ]

    finish_blockers = [
        code
        for code in readiness_blockers
        if code
        in {
            "MISSING_FACE_VINYL_ROLL_WIDTH",
            "MISSING_RETURN_DEPTH",
            "MISSING_RETURN_PAINT_COLOR",
            "MISSING_GROUP_FINISH_ASSIGNMENT",
            "MISSING_FINISH_ASSIGNMENT",
            "MISSING_FACE_FINISH_CONFIRMATION",
            "MISSING_RETURN_FINISH_CONFIRMATION",
            "MISSING_BACKING_FINISH_CONFIRMATION",
            "UNSUPPORTED_FINISH_MODE",
        }
    ]
    finish_warnings = [
        code
        for code in readiness_warnings
        if code.startswith("RETURN_") or code.startswith("FACE_") or code.startswith("LETTER_")
    ]

    material_warnings = [
        code
        for code in readiness_warnings
        if code in {WARNING_MATERIAL_ESTIMATE_ONLY, "NO_SHARED_SUPPORT_PSU_PACKED"}
    ]

    confirmed = workspace.confirmed_production_model
    vector_summary_text = (
        f"Litere {confirmed.letter_count}, contururi {confirmed.cut_contour_count}, "
        f"goluri {confirmed.inner_hole_count}"
        if confirmed
        else "Model neconfirmat"
    )

    sections = [
        _section_from_issues(
            section_code="request",
            label="Cerere / workspace",
            blockers=request_blockers,
            warnings=[],
            summary=workspace.client_request.client_name or "—",
        ),
        _section_from_issues(
            section_code="template",
            label="Template produs",
            blockers=[],
            warnings=[],
            summary=workspace.product_selection.template_code,
        ),
        _section_from_issues(
            section_code="vector",
            label="Vector & model litere",
            blockers=vector_blockers,
            warnings=vector_warnings,
            summary=vector_summary_text,
        ),
        _section_from_issues(
            section_code="dimensions",
            label="Dimensiuni",
            blockers=dimension_blockers,
            warnings=[],
            summary=(
                f"{workspace.client_request.width_mm}×{workspace.client_request.height_mm} mm"
                if workspace.client_request.width_mm and workspace.client_request.height_mm
                else "Dimensiuni lipsă"
            ),
        ),
        _section_from_issues(
            section_code="finish",
            label="Finisaje",
            blockers=finish_blockers,
            warnings=finish_warnings,
            summary=(
                f"Față {workspace.finish_assignment.face_finish.finish_type}"
                if workspace.finish_assignment
                else "Finisaje neconfigurate"
            ),
        ),
        _section_from_issues(
            section_code="material_intent",
            label="Material intent",
            blockers=[],
            warnings=material_warnings,
            summary=f"Estimate: {workspace.material_intent.estimate_status}",
        ),
        _section_from_issues(
            section_code="readiness",
            label="Readiness",
            blockers=readiness_blockers,
            warnings=readiness_warnings,
            summary=f"Status: {readiness.status}",
        ),
        _section_from_issues(
            section_code="pricing_input",
            label="Pricing input preview",
            blockers=pricing.adapter_blockers,
            warnings=pricing.adapter_warnings,
            summary="Fără calcul preț — doar mapare facts",
            default_missing=False,
        ),
        _section_from_issues(
            section_code="production_handoff",
            label="Production handoff preview",
            blockers=handoff.adapter_blockers,
            warnings=handoff.adapter_warnings,
            summary=f"Support: {support_mode}; seeds: {len(handoff.preview.task_seeds)}",
        ),
    ]
    return sections


def build_intake_v3_workspace_preview(workspace: IntakeV3Workspace) -> IntakeV3PreviewBuildResult:
    """Compose full Intake V3 preview from existing services — no quote/order/plan side effects."""
    readiness = evaluate_intake_v3_readiness(workspace)
    workspace.readiness_report = readiness

    if workspace.confirmed_production_model is not None:
        validate_confirmed_production_model(
            workspace.confirmed_production_model,
            raw=workspace.raw_svg_analysis,
        )

    if workspace.finish_assignment is not None:
        support_ctx = resolve_workspace_support_context(workspace)
        validate_finish_assignment(workspace, support_context=support_ctx)

    support_ctx = resolve_workspace_support_context(workspace)
    material = derive_material_intent(workspace, support_context=support_ctx)
    for warn in material_intent_warnings(material):
        if not any(w.code == warn.code for w in readiness.warnings):
            readiness.warnings.append(
                ReadinessIssue(
                    code=warn.code,
                    severity="warning",
                    section="materiale",
                    message=warn.message,
                    target_field=warn.target_field,
                )
            )

    pricing = build_pricing_input_candidate(workspace)
    handoff = build_production_handoff_preview(workspace)
    finish_variation_summary = build_finish_variation_summary(workspace.model_dump(mode="json"))
    sections = summarize_workspace_sections(workspace)
    boundary = build_boundary_flags(workspace)

    preview_blockers = list(dict.fromkeys(b.code for b in readiness.blockers))
    preview_blockers.extend(b for b in pricing.adapter_blockers if b not in preview_blockers)
    preview_warnings = list(
        dict.fromkeys(
            [w.code for w in readiness.warnings]
            + pricing.adapter_warnings
            + handoff.adapter_warnings
        )
    )

    preview = IntakeV3WorkspacePreview(
        workspace_id=_workspace_id(workspace),
        template_code=workspace.product_selection.template_code,
        support_mode=_resolve_support_mode(workspace),
        section_statuses=sections,
        readiness_report=readiness,
        vector_summary=_build_vector_summary(workspace),
        finish_summary=_build_finish_summary(workspace),
        lighting_summary=_build_lighting_summary(workspace),
        finish_variation_summary=finish_variation_summary,
        material_summary=_build_material_summary(workspace),
        pricing_input_candidate=pricing.candidate,
        production_handoff_preview=handoff.preview,
        boundary_flags=boundary,
        preview_blockers=preview_blockers,
        preview_warnings=preview_warnings,
        is_ready_for_quote=pricing.is_ready_for_quote,
        is_ready_for_production_handoff_preview=handoff.is_ready_for_handoff,
        created_quote_id=None,
        created_order_id=None,
        execution_plan_id=None,
    )

    quote_readiness = evaluate_intake_v3_quote_readiness(workspace, preview)
    prequote_review = build_prequote_review(workspace, preview)
    preview = preview.model_copy(
        update={
            "quote_readiness": quote_readiness,
            "prequote_review": prequote_review,
        }
    )

    quote_section_blockers = [item.code for item in quote_readiness.blockers]
    quote_section_warnings = [item.code for item in quote_readiness.warnings]
    sections.append(
        _section_from_issues(
            section_code="quote_readiness",
            label="Quote readiness gate",
            blockers=quote_section_blockers,
            warnings=quote_section_warnings,
            summary=f"Quote readiness: {quote_readiness.status}",
        )
    )
    preview = preview.model_copy(update={"section_statuses": sections})

    dry_run_available = is_quote_creation_dry_run_available(workspace, preview)
    bridge_available = is_commercial_quote_bridge_available(workspace, preview)
    bridge_status = (
        commercial_quote_bridge_status_label(workspace)
        if bridge_available
        else "unavailable"
    )
    preview = preview.model_copy(
        update={
            "quote_creation_dry_run_available": dry_run_available,
            "commercial_quote_bridge_available": bridge_available,
            "commercial_quote_bridge_status": bridge_status,
            "quote_creation_enablement_available": is_quote_creation_enablement_available(
                workspace,
                preview,
            ),
            "quote_creation_enablement_status": (
                quote_creation_enablement_status_label()
                if bridge_available
                else "unavailable"
            ),
            "quote_creation_real_status": "blocked" if bridge_available else "unavailable",
            "real_quote_creation_enablement_readiness_available": (
                is_real_quote_creation_enablement_readiness_available(workspace, preview)
            ),
            "real_quote_creation_enablement_readiness_status": (
                real_quote_creation_enablement_readiness_status_label()
                if bridge_available
                else "unavailable"
            ),
            "owner_decision_record_status": (
                "required_not_present" if bridge_available else "unavailable"
            ),
            "snapshot_policy_status": (
                "defined_not_executed" if bridge_available else "unavailable"
            ),
            "anti_duplicate_policy_status": ("defined" if bridge_available else "unavailable"),
            "rollback_policy_status": ("defined" if bridge_available else "unavailable"),
        }
    )

    is_complete = (
        preview.vector_summary.confirmed_letter_count > 0
        and preview.pricing_input_candidate is not None
        and preview.production_handoff_preview is not None
    )

    return IntakeV3PreviewBuildResult(
        preview=preview,
        build_warnings=preview_warnings,
        build_blockers=preview_blockers,
        is_preview_complete=is_complete,
    )
