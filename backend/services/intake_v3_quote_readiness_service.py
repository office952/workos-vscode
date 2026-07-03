"""Intake V3 quote readiness gate — pre-quote review only, no quote/order/plan creation."""

from __future__ import annotations

from typing import Any, Literal

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_DIMENSIONS,
    BLOCKER_UNCONFIRMED_LETTER_MODEL,
    PILOT_TEMPLATE_CODE,
)
from schemas.intake_v3 import (
    IntakeV3FinishVariationSummary,
    IntakeV3PreQuoteReview,
    IntakeV3PreQuoteReviewSection,
    IntakeV3QuoteReadinessItem,
    IntakeV3QuoteReadinessResult,
    IntakeV3QuoteReadinessSummary,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
    PricingInputAdapterResult,
    ProductionHandoffAdapterResult,
    ReadinessIssue,
    ReadinessReport,
)
from services.intake_v3_finish_variation_summary_service import build_finish_variation_summary
from services.intake_v3_pricing_input_adapter import build_pricing_input_candidate
from services.intake_v3_production_handoff_adapter import build_production_handoff_preview
from services.intake_v3_readiness_service import evaluate_intake_v3_readiness
from services.intake_v3_quote_creation_guard_policy_service import (
    build_quote_creation_policy_readiness_item,
)
from services.intake_v3_workspace_field_editor_service import resolve_workspace_support_context

QuoteReadinessStatus = Literal["blocked", "warning", "ready_preview_only"]
ItemSeverity = Literal["blocker", "warning", "info", "pass"]
ItemStatus = Literal["fail", "warn", "info", "pass"]

PREQUOTE_SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("workspace", "Workspace", "workspace"),
    ("client_product", "Client / product data", "client_product"),
    ("svg_vector", "SVG / vector", "svg_vector"),
    ("finishes", "Finishes", "finishes"),
    ("pricing_input_preview", "Pricing input preview", "pricing_input_preview"),
    ("production_handoff_preview", "Production handoff preview", "production_handoff_preview"),
    ("safety", "Safety boundary", "safety"),
)


def _positive(value: float | int | None) -> bool:
    try:
        return value is not None and float(value) > 0
    except (TypeError, ValueError):
        return False


def _item(
    *,
    code: str,
    label: str,
    severity: ItemSeverity,
    status: ItemStatus,
    message: str,
    source: str,
    recommended_action: str | None = None,
    editable_here: bool = False,
    related_section: str | None = None,
) -> IntakeV3QuoteReadinessItem:
    return IntakeV3QuoteReadinessItem(
        code=code,
        label=label,
        severity=severity,
        status=status,
        message=message,
        recommended_action=recommended_action,
        source=source,
        editable_here=editable_here,
        related_section=related_section,
    )


def _from_readiness_issue(issue: ReadinessIssue, *, related_section: str) -> IntakeV3QuoteReadinessItem:
    status: ItemStatus = "fail" if issue.severity == "blocker" else "warn"
    severity: ItemSeverity = "blocker" if issue.severity == "blocker" else "warning"
    return _item(
        code=issue.code,
        label=issue.code.replace("_", " ").title(),
        severity=severity,
        status=status,
        message=issue.message,
        recommended_action=issue.action_label,
        source="readiness_service",
        editable_here=issue.target_field is not None,
        related_section=related_section,
    )


def _dimensions_present(workspace: IntakeV3Workspace) -> bool:
    req = workspace.client_request
    if _positive(req.width_mm) and _positive(req.height_mm):
        return True
    asset = workspace.vector_asset
    return bool(
        asset
        and _positive(asset.declared_width_mm)
        and _positive(asset.declared_height_mm)
    )


def _support_mode_present(workspace: IntakeV3Workspace) -> bool:
    ctx = resolve_workspace_support_context(workspace)
    return bool(ctx and getattr(ctx, "shared_support", None) is not None)


def _illuminated_present(workspace: IntakeV3Workspace) -> bool:
    ctx = workspace.support_context or resolve_workspace_support_context(workspace)
    return ctx is not None and ctx.illuminated is not None


def classify_quote_readiness_blockers(
    items: list[IntakeV3QuoteReadinessItem],
) -> list[IntakeV3QuoteReadinessItem]:
    return [item for item in items if item.severity == "blocker" and item.status == "fail"]


def classify_quote_readiness_warnings(
    items: list[IntakeV3QuoteReadinessItem],
) -> list[IntakeV3QuoteReadinessItem]:
    return [item for item in items if item.severity == "warning" and item.status == "warn"]


def derive_quote_readiness_items(
    workspace: IntakeV3Workspace,
    *,
    readiness: ReadinessReport | None = None,
    pricing: PricingInputAdapterResult | None = None,
    handoff: ProductionHandoffAdapterResult | None = None,
    finish_variation_summary: IntakeV3FinishVariationSummary | None = None,
    workspace_title: str | None = None,
    workspace_archived: bool = False,
) -> list[IntakeV3QuoteReadinessItem]:
    """Build checklist items from workspace payload and preview fragments."""
    readiness = readiness or evaluate_intake_v3_readiness(workspace)
    pricing = pricing or build_pricing_input_candidate(workspace)
    handoff = handoff or build_production_handoff_preview(workspace)
    finish_variation_summary = finish_variation_summary or build_finish_variation_summary(
        workspace.model_dump(mode="json")
    )

    items: list[IntakeV3QuoteReadinessItem] = []

    # 6.1 Workspace
    items.append(
        _item(
            code="WORKSPACE_PAYLOAD_PRESENT",
            label="Workspace payload",
            severity="pass",
            status="pass",
            message="Workspace payload is present.",
            source="workspace",
            related_section="workspace",
        )
    )
    if workspace_archived:
        items.append(
            _item(
                code="WORKSPACE_ARCHIVED",
                label="Workspace archived",
                severity="blocker",
                status="fail",
                message="Archived workspaces cannot proceed to quote creation.",
                recommended_action="Restore or create a new draft workspace.",
                source="workspace_record",
                related_section="workspace",
            )
        )
    else:
        items.append(
            _item(
                code="WORKSPACE_NOT_ARCHIVED",
                label="Workspace not archived",
                severity="pass",
                status="pass",
                message="Workspace is active (not archived).",
                source="workspace_record",
                related_section="workspace",
            )
        )

    template_code = (workspace.product_selection.template_code or "").strip()
    if template_code:
        items.append(
            _item(
                code="TEMPLATE_CODE_PRESENT",
                label="Template code",
                severity="pass",
                status="pass",
                message=f"Template code present: {template_code}.",
                source="product_selection",
                related_section="workspace",
            )
        )
    else:
        items.append(
            _item(
                code="MISSING_TEMPLATE_CODE",
                label="Template code",
                severity="blocker",
                status="fail",
                message="Product template code is required.",
                recommended_action="Select TPL-VOLUMETRIC-LETTERS.",
                source="product_selection",
                related_section="workspace",
            )
        )

    title_value = (workspace_title or workspace.client_request.job_title or "").strip()
    if title_value:
        items.append(
            _item(
                code="TITLE_PRESENT",
                label="Title / job label",
                severity="pass",
                status="pass",
                message="Workspace title or job title is present.",
                source="workspace",
                related_section="workspace",
            )
        )
    else:
        items.append(
            _item(
                code="MISSING_TITLE",
                label="Title / job label",
                severity="warning",
                status="warn",
                message="No workspace title or job title — operator should verify identity.",
                recommended_action="Set job title in controlled fields.",
                source="workspace",
                editable_here=True,
                related_section="workspace",
            )
        )

    # 6.2 Client / product
    if template_code == PILOT_TEMPLATE_CODE:
        items.append(
            _item(
                code="PRODUCT_TEMPLATE_VOLUMETRIC",
                label="Volumetric template",
                severity="pass",
                status="pass",
                message="Pilot template TPL-VOLUMETRIC-LETTERS selected.",
                source="product_selection",
                related_section="client_product",
            )
        )
    else:
        items.append(
            _item(
                code="UNSUPPORTED_TEMPLATE_FOR_QUOTE_PREVIEW",
                label="Template scope",
                severity="warning",
                status="warn",
                message=f"Template {template_code or '—'} is outside pilot quote-readiness scope.",
                source="product_selection",
                related_section="client_product",
            )
        )

    if _dimensions_present(workspace):
        items.append(
            _item(
                code="DIMENSIONS_PRESENT",
                label="Dimensions",
                severity="pass",
                status="pass",
                message="Width and height are present.",
                source="client_request",
                related_section="client_product",
            )
        )
    else:
        items.append(
            _item(
                code=BLOCKER_MISSING_DIMENSIONS,
                label="Dimensions",
                severity="blocker",
                status="fail",
                message="Width and height are required before quote readiness.",
                recommended_action="Complete dimensions in controlled fields.",
                source="readiness_service",
                editable_here=True,
                related_section="client_product",
            )
        )

    if _support_mode_present(workspace):
        support_ctx = resolve_workspace_support_context(workspace)
        mode = "shared" if support_ctx.shared_support else "no_shared"
        items.append(
            _item(
                code="SUPPORT_MODE_PRESENT",
                label="Support mode",
                severity="pass",
                status="pass",
                message=f"Support mode resolved: {mode}.",
                source="support_context",
                related_section="client_product",
            )
        )
    else:
        items.append(
            _item(
                code="MISSING_SUPPORT_MODE",
                label="Support mode",
                severity="warning",
                status="warn",
                message="Support mode not explicitly set — defaults applied.",
                source="support_context",
                editable_here=True,
                related_section="client_product",
            )
        )

    if _illuminated_present(workspace):
        illuminated = (
            workspace.support_context.illuminated
            if workspace.support_context
            else resolve_workspace_support_context(workspace).illuminated
        )
        items.append(
            _item(
                code="ILLUMINATED_FLAG_PRESENT",
                label="Illuminated flag",
                severity="pass",
                status="pass",
                message=f"Illuminated flag present: {illuminated}.",
                source="support_context",
                related_section="client_product",
            )
        )
    else:
        items.append(
            _item(
                code="MISSING_ILLUMINATED_FLAG",
                label="Illuminated flag",
                severity="warning",
                status="warn",
                message="Illuminated flag missing — verify lighting intent.",
                source="support_context",
                editable_here=True,
                related_section="client_product",
            )
        )

    # 6.3 SVG / vector
    raw = workspace.raw_svg_analysis
    vector_asset = workspace.vector_asset
    if raw and raw.closed_contour_count > 0:
        items.append(
            _item(
                code="SVG_UPLOADED_AND_ANALYZED",
                label="Raw SVG analysis",
                severity="pass",
                status="pass",
                message=f"Raw SVG analyzed — {raw.closed_contour_count} closed contour(s).",
                source="raw_svg_analysis",
                related_section="svg_vector",
            )
        )
    elif vector_asset and vector_asset.upload_status != "missing":
        items.append(
            _item(
                code="SVG_UPLOADED_PENDING_ANALYSIS",
                label="Raw SVG analysis",
                severity="warning",
                status="warn",
                message="SVG uploaded but raw analysis is incomplete.",
                recommended_action="Re-upload SVG or wait for analysis.",
                source="vector_asset",
                related_section="svg_vector",
            )
        )
    else:
        items.append(
            _item(
                code="MISSING_SVG_ANALYSIS",
                label="Raw SVG analysis",
                severity="blocker",
                status="fail",
                message="Raw SVG upload and analysis are required.",
                recommended_action="Upload SVG and review raw analysis.",
                source="vector_asset",
                related_section="svg_vector",
            )
        )

    if raw and raw.warnings:
        items.append(
            _item(
                code="RAW_SVG_ANALYSIS_WARNINGS",
                label="Raw analysis warnings",
                severity="warning",
                status="warn",
                message=f"Raw SVG analysis has {len(raw.warnings)} warning(s) — operator review recommended.",
                recommended_action="Review raw SVG warnings before quote step.",
                source="raw_svg_analysis",
                related_section="svg_vector",
            )
        )
    elif raw:
        items.append(
            _item(
                code="RAW_ANALYSIS_WARNINGS_REVIEWED",
                label="Raw analysis warnings",
                severity="pass",
                status="pass",
                message="No raw SVG analysis warnings.",
                source="raw_svg_analysis",
                related_section="svg_vector",
            )
        )

    confirmed = workspace.confirmed_production_model
    if confirmed and confirmed.confirmation_status == "confirmed" and confirmed.letter_count > 0:
        items.append(
            _item(
                code="CONFIRMED_PRODUCTION_MODEL",
                label="Confirmed production model",
                severity="pass",
                status="pass",
                message="Production model confirmed by operator.",
                source="confirmed_production_model",
                related_section="svg_vector",
            )
        )
        items.append(
            _item(
                code="LETTER_COUNT_CONFIRMED",
                label="Letter count",
                severity="pass",
                status="pass",
                message=f"Letter count confirmed: {confirmed.letter_count}.",
                source="confirmed_production_model",
                related_section="svg_vector",
            )
        )
        items.append(
            _item(
                code="CUT_CONTOUR_COUNT_CONFIRMED",
                label="Cut contour count",
                severity="pass",
                status="pass",
                message=f"Cut contour count confirmed: {confirmed.cut_contour_count}.",
                source="confirmed_production_model",
                related_section="svg_vector",
            )
        )
        items.append(
            _item(
                code="INNER_HOLES_CONFIRMED",
                label="Inner holes",
                severity="pass",
                status="pass",
                message=f"Inner hole count confirmed: {confirmed.inner_hole_count}.",
                source="confirmed_production_model",
                related_section="svg_vector",
            )
        )
    else:
        items.append(
            _item(
                code=BLOCKER_UNCONFIRMED_LETTER_MODEL,
                label="Confirmed production model",
                severity="blocker",
                status="fail",
                message="Production model is not confirmed by operator.",
                recommended_action="Confirm letter model in production model review.",
                source="confirmed_production_model",
                related_section="svg_vector",
            )
        )

    items.append(
        _item(
            code="RAW_ANALYSIS_SEPARATE_FROM_MODEL",
            label="Raw vs confirmed model",
            severity="info",
            status="info",
            message="Raw SVG analysis remains separate from confirmed production model.",
            source="architecture",
            related_section="svg_vector",
        )
    )

    # 6.4 Finishes — map readiness finish blockers/warnings
    finish = workspace.finish_assignment
    if finish is not None and finish.active_groups():
        items.append(
            _item(
                code="GLOBAL_FINISH_PRESENT",
                label="Global finish assignment",
                severity="pass",
                status="pass",
                message="Global finish assignment is configured.",
                source="finish_assignment",
                related_section="finishes",
            )
        )
    else:
        items.append(
            _item(
                code="MISSING_FINISH_ASSIGNMENT",
                label="Global finish assignment",
                severity="blocker",
                status="fail",
                message="Finish assignment is missing or incomplete.",
                recommended_action="Configure face, return, and backing finishes.",
                source="finish_assignment",
                editable_here=True,
                related_section="finishes",
            )
        )

    for issue in readiness.blockers:
        if issue.section == "finisaje" and issue.code not in {item.code for item in items}:
            items.append(_from_readiness_issue(issue, related_section="finishes"))
    for issue in readiness.warnings:
        if issue.section in {"finisaje", "materiale"} and issue.code not in {item.code for item in items}:
            items.append(_from_readiness_issue(issue, related_section="finishes"))

    from services.intake_v3_layer_finish_assignment_service import (
        summarize_layer_finish_assignments,
        uses_native_layer_finish,
    )

    if uses_native_layer_finish(workspace.model_dump(mode="json")):
        layer_summary = summarize_layer_finish_assignments(workspace.model_dump(mode="json"))
        if layer_summary.layer_finish_assignment_status == "complete":
            items.append(
                _item(
                    code="LAYER_FINISH_ASSIGNMENTS_COMPLETE",
                    label="Layer finish assignments",
                    severity="pass",
                    status="pass",
                    message=layer_summary.assignment_summary,
                    source="layer_finish_assignments",
                    related_section="finishes",
                )
            )
        else:
            items.append(
                _item(
                    code="LAYER_FINISH_ASSIGNMENTS_INCOMPLETE",
                    label="Layer finish assignments",
                    severity="blocker",
                    status="fail",
                    message=layer_summary.assignment_summary,
                    recommended_action="Confirm finish setup for each productive layer.",
                    source="layer_finish_assignments",
                    editable_here=True,
                    related_section="finishes",
                )
            )

    if finish_variation_summary:
        items.append(
            _item(
                code="FINISH_VARIATION_SUMMARY_GENERATED",
                label="Finish variation summary",
                severity="pass",
                status="pass",
                message="Finish variation summary generated for preview.",
                source="finish_variation_summary",
                related_section="finishes",
            )
        )
        if finish_variation_summary.has_variations:
            items.append(
                _item(
                    code="GROUPED_FINISH_REVIEW_REQUIRED",
                    label="Grouped finish review",
                    severity="warning",
                    status="warn",
                    message="Finish variations require grouped review before final quote.",
                    recommended_action="Review finish variation summary and group assignments.",
                    source="finish_variation_summary",
                    related_section="finishes",
                )
            )

    # 6.5 Pricing input preview
    if pricing.candidate and pricing.adapter_status in {"ready", "warnings"}:
        items.append(
            _item(
                code="PRICING_INPUT_CANDIDATE_PRESENT",
                label="Pricing input candidate",
                severity="pass",
                status="pass",
                message="Pricing input candidate built — preview facts only.",
                source="pricing_input_adapter",
                related_section="pricing_input_preview",
            )
        )
    else:
        items.append(
            _item(
                code="PRICING_INPUT_CANDIDATE_MISSING",
                label="Pricing input candidate",
                severity="blocker",
                status="fail",
                message="Pricing input preview candidate is missing or blocked.",
                recommended_action="Resolve readiness blockers to build pricing input preview.",
                source="pricing_input_adapter",
                related_section="pricing_input_preview",
            )
        )

    if pricing.adapter_blockers:
        for code in pricing.adapter_blockers:
            if code not in {item.code for item in items}:
                items.append(
                    _item(
                        code=code,
                        label=code.replace("_", " ").title(),
                        severity="blocker",
                        status="fail",
                        message=f"Pricing input blocked: {code}.",
                        source="pricing_input_adapter",
                        related_section="pricing_input_preview",
                    )
                )
    else:
        items.append(
            _item(
                code="PRICING_INPUT_NO_BLOCKERS",
                label="Pricing input blockers",
                severity="pass",
                status="pass",
                message="Pricing input preview has no adapter blockers.",
                source="pricing_input_adapter",
                related_section="pricing_input_preview",
            )
        )

    if finish_variation_summary and finish_variation_summary.has_variations:
        notes = finish_variation_summary.pricing_preview_notes or pricing.candidate.finish_variation_notes
        if notes:
            items.append(
                _item(
                    code="FINISH_VARIATION_PRICING_NOTES",
                    label="Finish variation pricing notes",
                    severity="info",
                    status="info",
                    message=notes[0],
                    source="finish_variation_summary",
                    related_section="pricing_input_preview",
                )
            )

    items.append(
        _item(
            code="NO_FINAL_COMMERCIAL_PRICE",
            label="No final price",
            severity="info",
            status="info",
            message="Pricing input preview only — no final commercial price is calculated here.",
            source="boundary",
            related_section="pricing_input_preview",
        )
    )

    # 6.6 Production handoff preview
    preview_handoff = handoff.preview
    if preview_handoff and handoff.is_ready_for_handoff:
        items.append(
            _item(
                code="HANDOFF_PREVIEW_PRESENT",
                label="Handoff preview",
                severity="pass",
                status="pass",
                message="Production handoff preview is available.",
                source="production_handoff_adapter",
                related_section="production_handoff_preview",
            )
        )
    else:
        items.append(
            _item(
                code="HANDOFF_PREVIEW_MISSING",
                label="Handoff preview",
                severity="blocker",
                status="fail",
                message="Production handoff preview is missing or blocked.",
                recommended_action="Resolve blockers to build handoff preview.",
                source="production_handoff_adapter",
                related_section="production_handoff_preview",
            )
        )

    if preview_handoff.non_executable and preview_handoff.preview_only:
        items.append(
            _item(
                code="HANDOFF_NON_EXECUTABLE",
                label="Handoff non-executable",
                severity="info",
                status="info",
                message="Production handoff preview only — no execution tasks are created.",
                source="production_handoff_adapter",
                related_section="production_handoff_preview",
            )
        )

    if finish_variation_summary and finish_variation_summary.has_variations:
        labels = [
            v.label
            for v in finish_variation_summary.variations
            if v.source_type == "group" and v.label
        ]
        items.append(
            _item(
                code="HANDOFF_GROUP_LABELS_PRESERVED",
                label="Group labels / letter IDs",
                severity="pass" if labels else "warning",
                status="pass" if labels else "warn",
                message=(
                    f"Group labels preserved for handoff preview: {', '.join(labels)}."
                    if labels
                    else "Finish variations present — verify group labels in handoff preview."
                ),
                source="production_handoff_adapter",
                related_section="production_handoff_preview",
            )
        )

    items.append(
        _item(
            code="NO_EXECUTION_TASKS_CREATED",
            label="No execution tasks",
            severity="info",
            status="info",
            message="No execution tasks or plans are created in Intake V3 preview.",
            source="boundary",
            related_section="production_handoff_preview",
        )
    )

    # 6.7 Safety
    for code, label, message in (
        ("SAFETY_NO_QUOTE", "No quote created", "Quote creation is disabled in this foundation build."),
        ("SAFETY_NO_ORDER", "No order created", "Order creation is disabled in this foundation build."),
        (
            "SAFETY_NO_EXECUTION_PLAN",
            "No execution plan",
            "Execution plan creation is disabled in this foundation build.",
        ),
        ("SAFETY_NO_INVENTORY", "No inventory mutation", "Inventory is not mutated in Intake V3 preview."),
        (
            "SAFETY_PREVIEW_ONLY",
            "Preview-only boundary",
            "Intake V3 remains preview-only — quote creation intentionally disabled.",
        ),
    ):
        items.append(
            _item(
                code=code,
                label=label,
                severity="info",
                status="info",
                message=message,
                source="boundary",
                related_section="safety",
            )
        )

    items.append(build_quote_creation_policy_readiness_item())

    return items


QUOTE_GATE_WARNING_CODES = frozenset(
    {
        "GROUPED_FINISH_REVIEW_REQUIRED",
        "RAW_SVG_ANALYSIS_WARNINGS",
        "RAW_CONFIRMED_LETTER_COUNT_MISMATCH",
        "MISSING_TITLE",
        "UNSUPPORTED_TEMPLATE_FOR_QUOTE_PREVIEW",
    }
)


def _derive_status(
    blockers: list[IntakeV3QuoteReadinessItem],
    warnings: list[IntakeV3QuoteReadinessItem],
) -> QuoteReadinessStatus:
    if blockers:
        return "blocked"
    if any(item.code in QUOTE_GATE_WARNING_CODES for item in warnings):
        return "warning"
    return "ready_preview_only"


def _next_action(
    blockers: list[IntakeV3QuoteReadinessItem],
    warnings: list[IntakeV3QuoteReadinessItem],
) -> str:
    if blockers:
        return blockers[0].recommended_action or blockers[0].message
    if warnings:
        return "Review warnings before the future quote creation step."
    return (
        "Workspace appears ready for a future quote creation step — "
        "quote creation is intentionally disabled in this foundation build."
    )


def _operator_review_items(
    items: list[IntakeV3QuoteReadinessItem],
) -> list[IntakeV3QuoteReadinessItem]:
    codes = {
        "RAW_SVG_ANALYSIS_WARNINGS",
        "GROUPED_FINISH_REVIEW_REQUIRED",
        "FINISH_VARIATION_PRICING_NOTES",
        "MISSING_TITLE",
        "RAW_CONFIRMED_LETTER_COUNT_MISMATCH",
    }
    return [
        item
        for item in items
        if item.code in codes
        or item.severity in {"blocker", "warning"}
        and item.status in {"fail", "warn"}
        and item.related_section in {"svg_vector", "finishes", "pricing_input_preview"}
    ]


def _pricing_summary(
    pricing: PricingInputAdapterResult,
    finish_variation_summary: IntakeV3FinishVariationSummary | None,
) -> IntakeV3QuoteReadinessSummary:
    notes = ["Pricing input preview only. No final commercial price is calculated here."]
    if finish_variation_summary and finish_variation_summary.pricing_preview_notes:
        notes.extend(finish_variation_summary.pricing_preview_notes[:3])
    elif pricing.candidate.finish_variation_notes:
        notes.extend(pricing.candidate.finish_variation_notes[:3])
    return IntakeV3QuoteReadinessSummary(
        adapter_status=pricing.adapter_status,
        blocker_count=len(pricing.adapter_blockers),
        warning_count=len(pricing.adapter_warnings),
        notes=notes,
    )


def _handoff_summary(
    handoff: ProductionHandoffAdapterResult,
    finish_variation_summary: IntakeV3FinishVariationSummary | None,
) -> IntakeV3QuoteReadinessSummary:
    notes = ["Production handoff preview only. No execution tasks are created."]
    preview = handoff.preview
    if finish_variation_summary and finish_variation_summary.handoff_preview_notes:
        notes.extend(finish_variation_summary.handoff_preview_notes[:3])
    notes.append(f"Task seed previews: {len(preview.task_seeds)} (all non-executable).")
    return IntakeV3QuoteReadinessSummary(
        adapter_status="ready" if handoff.is_ready_for_handoff else "blocked",
        blocker_count=len(handoff.adapter_blockers),
        warning_count=len(handoff.adapter_warnings),
        notes=notes,
    )


def evaluate_intake_v3_quote_readiness(
    payload: dict[str, Any] | IntakeV3Workspace,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    *,
    workspace_title: str | None = None,
    workspace_archived: bool = False,
) -> IntakeV3QuoteReadinessResult:
    """Evaluate quote readiness gate — always preview-only, never enables quote creation."""
    if isinstance(payload, dict):
        workspace = IntakeV3Workspace.model_validate(payload)
    else:
        workspace = payload

    readiness = (
        workspace_preview.readiness_report
        if workspace_preview and workspace_preview.readiness_report
        else evaluate_intake_v3_readiness(workspace)
    )
    pricing = build_pricing_input_candidate(workspace)
    handoff = build_production_handoff_preview(workspace)
    finish_variation_summary = (
        workspace_preview.finish_variation_summary
        if workspace_preview and workspace_preview.finish_variation_summary
        else build_finish_variation_summary(workspace.model_dump(mode="json"))
    )

    checklist = derive_quote_readiness_items(
        workspace,
        readiness=readiness,
        pricing=pricing,
        handoff=handoff,
        finish_variation_summary=finish_variation_summary,
        workspace_title=workspace_title,
        workspace_archived=workspace_archived,
    )
    blockers = classify_quote_readiness_blockers(checklist)
    warnings = classify_quote_readiness_warnings(checklist)
    infos = [item for item in checklist if item.severity == "info"]
    status = _derive_status(blockers, warnings)

    return IntakeV3QuoteReadinessResult(
        status=status,
        can_create_quote=False,
        preview_only=True,
        blockers=blockers,
        warnings=warnings,
        infos=infos,
        checklist=checklist,
        operator_review_items=_operator_review_items(checklist),
        pricing_input_summary=_pricing_summary(pricing, finish_variation_summary),
        handoff_summary=_handoff_summary(handoff, finish_variation_summary),
        next_recommended_action=_next_action(blockers, warnings),
    )


def build_prequote_review(
    payload: dict[str, Any] | IntakeV3Workspace,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    *,
    workspace_title: str | None = None,
    workspace_archived: bool = False,
) -> IntakeV3PreQuoteReview:
    """Structured pre-quote review sections for operator checklist UI."""
    result = evaluate_intake_v3_quote_readiness(
        payload,
        workspace_preview,
        workspace_title=workspace_title,
        workspace_archived=workspace_archived,
    )
    by_section: dict[str, list[IntakeV3QuoteReadinessItem]] = {
        code: [] for code, _, _ in PREQUOTE_SECTIONS
    }
    for item in result.checklist:
        key = item.related_section or "workspace"
        if key not in by_section:
            by_section[key] = []
        by_section[key].append(item)

    sections: list[IntakeV3PreQuoteReviewSection] = []
    for section_code, label, key in PREQUOTE_SECTIONS:
        section_items = by_section.get(key, [])
        fails = sum(1 for i in section_items if i.status == "fail")
        warns = sum(1 for i in section_items if i.status == "warn")
        if fails:
            summary = f"{fails} blocker(s) in this section."
        elif warns:
            summary = f"{warns} warning(s) — review recommended."
        elif section_items:
            summary = "Section checks passed or informational."
        else:
            summary = "No items."
        sections.append(
            IntakeV3PreQuoteReviewSection(
                section_code=section_code,
                label=label,
                items=section_items,
                summary=summary,
            )
        )

    return IntakeV3PreQuoteReview(
        status=result.status,
        can_create_quote=False,
        preview_only=True,
        sections=sections,
        blockers=result.blockers,
        warnings=result.warnings,
        infos=result.infos,
        next_recommended_action=result.next_recommended_action,
    )
