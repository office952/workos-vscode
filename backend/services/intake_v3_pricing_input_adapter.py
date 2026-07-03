"""Intake V3 pricing input adapter — maps workspace facts to quote_input candidate (no pricing)."""

from __future__ import annotations

from data_models.intake_v3_contracts import (
    PRICING_ADAPTER_FORBIDDEN_KEYS,
    SUPPORT_MODE_NO_SHARED,
    SUPPORT_MODE_SHARED_PENDING,
)
from schemas.intake_v3 import (
    IntakeV3Workspace,
    PricingInputAdapterResult,
    PricingInputCandidate,
    PricingInputDimensions,
    PricingInputFinishSummary,
    PricingInputLine,
    PricingInputMaterialSummary,
    PricingInputOperationSummary,
    PricingInputProductionCounts,
    PricingInputReadinessSummary,
    SupportContext,
    VectorModelIssue,
)
from services.intake_v3_finish_material_service import (
    derive_material_intent,
    derive_operation_flags_from_finishes,
    material_intent_warnings,
    validate_finish_assignment,
)
from services.intake_v3_finish_variation_summary_service import build_finish_variation_summary
from services.intake_v3_readiness_service import evaluate_intake_v3_readiness
from services.intake_v3_workspace_field_editor_service import resolve_workspace_support_context


def _resolve_support_mode(workspace: IntakeV3Workspace) -> str:
    ctx = resolve_workspace_support_context(workspace)
    if ctx.shared_support:
        return SUPPORT_MODE_SHARED_PENDING
    intent = (workspace.client_request.mounting_intent or "").lower()
    if "shared" in intent or "suport" in intent and "comun" in intent:
        return SUPPORT_MODE_SHARED_PENDING
    return SUPPORT_MODE_NO_SHARED


def _build_finish_summary(workspace: IntakeV3Workspace) -> PricingInputFinishSummary:
    finish = workspace.finish_assignment
    if finish is None or not finish.active_groups():
        return PricingInputFinishSummary()
    group = finish.active_groups()[0]
    face = group.face_finish
    ret = group.return_finish
    backing = group.backing_finish
    return PricingInputFinishSummary(
        face_finish_type=face.finish_type,
        face_vinyl_enabled=face.face_vinyl_active,
        face_material=face.material_code,
        face_color_code=face.color_code,
        face_color_name=face.color_name,
        face_roll_width_mm=face.face_vinyl_roll_width_mm,
        return_finish_type=ret.finish_type,
        return_wrapped=ret.return_vinyl_active,
        return_painted=ret.return_painted_active,
        return_depth_mm=ret.return_depth_mm,
        return_material=ret.material_code,
        return_color_code=ret.color_code,
        return_color_name=ret.color_name,
        backing_material=backing.material,
        backing_thickness_mm=backing.thickness_mm,
    )


def build_pricing_input_candidate(workspace: IntakeV3Workspace) -> PricingInputAdapterResult:
    """Map IntakeV3Workspace to PricingInput candidate — no price calculation."""
    readiness = evaluate_intake_v3_readiness(workspace)
    support_mode = _resolve_support_mode(workspace)
    support_ctx = resolve_workspace_support_context(workspace)

    confirmed = workspace.confirmed_production_model
    production = PricingInputProductionCounts()
    if confirmed:
        production = PricingInputProductionCounts(
            letter_count=confirmed.letter_count,
            cut_contour_count=confirmed.cut_contour_count,
            inner_hole_count=confirmed.inner_hole_count,
            confirmed_model_status=confirmed.confirmation_status,
            letter_groups=[
                g.label or g.group_id
                for g in (confirmed.letter_model.groups if confirmed.letter_model else [])
            ],
        )

    req = workspace.client_request
    dimensions = PricingInputDimensions(
        width_mm=req.width_mm,
        height_mm=req.height_mm,
        depth_mm=req.depth_mm,
    )
    if req.width_mm and req.height_mm:
        dimensions.area_m2 = round((req.width_mm * req.height_mm) / 1_000_000, 4)

    material = derive_material_intent(workspace, support_context=support_ctx)
    mat_warnings = material_intent_warnings(material)
    finish_validation = validate_finish_assignment(workspace, support_context=support_ctx)
    flags = finish_validation.operation_flags

    material_summary = PricingInputMaterialSummary(
        roll_intents=len(material.roll_materials),
        sheet_intents=len(material.sheet_materials),
        led_intents=len(material.led_materials),
        psu_intents=len(material.power_supplies),
        accessory_intents=len(material.accessories),
        inventory_mutation_allowed=False,
        estimate_status=material.estimate_status,
    )

    blocker_codes = [b.code for b in readiness.blockers]
    warning_codes = [w.code for w in readiness.warnings]
    adapter_warnings = [w.message for w in readiness.warnings]
    for w in mat_warnings:
        if w.code not in warning_codes:
            warning_codes.append(w.code)
            adapter_warnings.append(w.message)

    readiness_summary = PricingInputReadinessSummary(
        status=readiness.status,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        can_create_quote=readiness.can_create_quote,
        reason_summary=readiness.next_action,
    )

    variation_summary = build_finish_variation_summary(workspace.model_dump(mode="json"))
    finish_variation_notes = list(variation_summary.pricing_preview_notes)
    requires_grouped_finish_review = variation_summary.has_variations
    finish_variation_count = len(variation_summary.variations)

    candidate = PricingInputCandidate(
        template_code=workspace.product_selection.template_code,
        product_label=workspace.product_selection.product_family or "Litere volumetrice luminoase",
        support_mode=support_mode,
        dimensions=dimensions,
        production_counts=production,
        finish_summary=_build_finish_summary(workspace),
        material_summary=material_summary,
        operation_summary=PricingInputOperationSummary(flags=flags),
        readiness_summary=readiness_summary,
        summary_lines=[
            PricingInputLine(
                line_id="letters",
                label="Litere confirmate",
                value=production.letter_count,
                category="production",
            ),
            PricingInputLine(
                line_id="cut_contours",
                label="Contururi CNC",
                value=production.cut_contour_count,
                category="production",
            ),
        ],
        finish_variation_notes=finish_variation_notes,
        requires_grouped_finish_review=requires_grouped_finish_review,
        finish_variation_count=finish_variation_count,
    )

    quote_input_payload: dict[str, object] = {
        "intake_schema_version": workspace.schema_version,
        "template_code": candidate.template_code,
        "support_mode": support_mode,
        "letter_count": production.letter_count,
        "cut_contour_count": production.cut_contour_count,
        "inner_hole_count": production.inner_hole_count,
        "width_mm": dimensions.width_mm,
        "height_mm": dimensions.height_mm,
        "depth_mm": dimensions.depth_mm,
        "face_finish_type": candidate.finish_summary.face_finish_type,
        "face_vinyl_enabled": candidate.finish_summary.face_vinyl_enabled,
        "face_vinyl_roll_width_mm": candidate.finish_summary.face_roll_width_mm,
        "return_finish_type": candidate.finish_summary.return_finish_type,
        "return_depth_mm": candidate.finish_summary.return_depth_mm,
        "return_wrapped": candidate.finish_summary.return_wrapped,
        "return_painted": candidate.finish_summary.return_painted,
        "backing_material": candidate.finish_summary.backing_material,
        "backing_thickness_mm": candidate.finish_summary.backing_thickness_mm,
        "inventory_mutation_allowed": False,
        "operation_flags": flags.model_dump(),
        "readiness_status": readiness.status,
        "can_create_quote": readiness.can_create_quote,
    }

    adapter_status = "ready" if readiness.can_create_quote else "blocked"
    if warning_codes and adapter_status == "ready":
        adapter_status = "warnings"

    return PricingInputAdapterResult(
        candidate=candidate,
        quote_input_payload=quote_input_payload,
        adapter_warnings=adapter_warnings,
        adapter_blockers=blocker_codes,
        is_ready_for_quote=readiness.can_create_quote,
        adapter_status=adapter_status,  # type: ignore[arg-type]
    )


def validate_pricing_input_candidate(
    result: PricingInputAdapterResult,
) -> tuple[bool, list[VectorModelIssue]]:
    """Validate adapter output — no commercial price keys, inventory mutation false."""
    issues: list[VectorModelIssue] = []
    for key in result.quote_input_payload:
        if key in PRICING_ADAPTER_FORBIDDEN_KEYS:
            issues.append(
                VectorModelIssue(
                    code="PRICING_ADAPTER_FORBIDDEN_KEY",
                    severity="blocker",
                    message=f"Adapter must not emit commercial key: {key}",
                    target_field=f"quote_input_payload.{key}",
                )
            )
    if result.quote_input_payload.get("inventory_mutation_allowed") is not False:
        issues.append(
            VectorModelIssue(
                code="INVENTORY_MUTATION_NOT_ALLOWED",
                severity="blocker",
                message="inventory_mutation_allowed must remain false",
                target_field="quote_input_payload.inventory_mutation_allowed",
            )
        )
    stock_keys = {"stock_movement", "deduct_inventory", "reserve_stock"}
    for key in stock_keys:
        if key in result.quote_input_payload:
            issues.append(
                VectorModelIssue(
                    code="INVENTORY_MUTATION_NOT_ALLOWED",
                    severity="blocker",
                    message=f"Adapter must not emit inventory key: {key}",
                    target_field=f"quote_input_payload.{key}",
                )
            )
    return len(issues) == 0, issues


def summarize_pricing_input(result: PricingInputAdapterResult) -> dict[str, object]:
    """Compact summary for docs/tests."""
    c = result.candidate
    return {
        "template_code": c.template_code,
        "support_mode": c.support_mode,
        "letter_count": c.production_counts.letter_count,
        "cut_contour_count": c.production_counts.cut_contour_count,
        "inner_hole_count": c.production_counts.inner_hole_count,
        "is_ready_for_quote": result.is_ready_for_quote,
        "blocker_count": len(result.adapter_blockers),
        "warning_count": len(result.adapter_warnings),
        "has_price_fields": any(
            k in result.quote_input_payload for k in PRICING_ADAPTER_FORBIDDEN_KEYS
        ),
    }
