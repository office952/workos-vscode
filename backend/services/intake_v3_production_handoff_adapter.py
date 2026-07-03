"""Intake V3 production handoff adapter — preview task seeds (not ExecutionPlan)."""

from __future__ import annotations

from data_models.intake_v3_contracts import (
    SUPPORT_MODE_NO_SHARED,
    SUPPORT_MODE_SHARED_PENDING,
    WARNING_SHARED_SUPPORT_PENDING,
)
from schemas.intake_v3 import (
    IntakeV3Workspace,
    OperationFlags,
    PricingInputDimensions,
    ProductionCountsSummary,
    ProductionFinishSummary,
    ProductionHandoffAdapterResult,
    ProductionHandoffPreview,
    ProductionMaterialSummary,
    SupportContext,
    TaskSeedCandidate,
    VectorModelIssue,
)
from services.intake_v3_finish_material_service import (
    derive_material_intent,
    derive_operation_flags_from_finishes,
)
from services.intake_v3_finish_variation_summary_service import build_finish_variation_summary
from services.intake_v3_pricing_input_adapter import _build_finish_summary, _resolve_support_mode
from services.intake_v3_readiness_service import evaluate_intake_v3_readiness


def _operation_catalog() -> list[dict[str, object]]:
    return [
        {
            "seed_code": "graphic_vector_preflight",
            "display_name": "Verificare grafică / vectorizare",
            "required_skill": ["graphic_design", "vector_preflight"],
            "required_station": "graphics_workstation",
            "operator_instruction": "Verifică SVG, straturi și pregătire pentru model producție.",
        },
        {
            "seed_code": "confirmed_production_model",
            "display_name": "Confirmare model producție din vector",
            "required_skill": ["graphic_design", "vector_preflight"],
            "required_station": "graphics_workstation",
            "operator_instruction": "Confirmă litere, contururi și goluri interioare.",
        },
        {
            "seed_code": "cnc_file_preparation",
            "display_name": "Pregătire fișiere CNC pentru debitare față/spate",
            "required_skill": ["cnc_file_preparation"],
            "required_station": "cnc_preparation_station",
            "operator_instruction": "Pregătește fișiere debitare față plexiglas și spate Forex.",
        },
        {
            "seed_code": "return_forming_file_preparation",
            "display_name": "Pregătire fișier / traseu pentru modelare cant",
            "required_skill": ["return_forming_file_preparation"],
            "required_station": "cnc_preparation_station",
            "operator_instruction": "Pregătește traseul pentru modelarea cantului.",
        },
        {
            "seed_code": "return_vinyl_application_workbench",
            "display_name": "Colantare cant la banc de lucru",
            "required_skill": ["vinyl_application_workbench"],
            "required_station": "workbench",
            "operator_instruction": "Colantează cantul pe bandă plată înainte de modelare.",
        },
        {
            "seed_code": "face_and_backing_cnc_cut",
            "display_name": "Debitare față plexiglas și spate Forex la CNC",
            "required_skill": ["cnc_router_operation"],
            "required_station": "cnc_router",
            "operator_instruction": "Debitează fețele și spatele Forex la CNC.",
        },
        {
            "seed_code": "return_side_forming",
            "display_name": "Modelare canturi aluminiu",
            "required_skill": ["return_forming_machine_operation"],
            "required_station": "return_forming_machine",
            "operator_instruction": "Modelează canturile din aluminiu.",
        },
        {
            "seed_code": "return_face_bonding",
            "display_name": "Lipire canturi pe fețele din plexiglas",
            "required_skill": ["letter_assembly"],
            "required_station": "assembly_bench",
            "operator_instruction": "Lipește canturile modelate pe fețele din plexiglas.",
        },
        {
            "seed_code": "led_installation_wiring_and_light_test",
            "display_name": "Montaj LED, cablare LED și test aprindere fiecare literă",
            "required_skill": ["led_installation", "electrical_wiring_basic"],
            "required_station": "electrical_bench",
            "operator_instruction": "Montează LED, cablare și test aprindere per literă.",
        },
        {
            "seed_code": "letter_assembly_no_shared_support",
            "display_name": "Asamblare litere pe spate Forex",
            "required_skill": ["letter_assembly"],
            "required_station": "assembly_bench",
            "operator_instruction": "Asamblează corp față+cant pe Forex cu autoforante.",
        },
        {
            "seed_code": "return_painting_after_assembly",
            "display_name": "Protejare față, vopsire cant litere și îndepărtare protecție după uscare",
            "required_skill": ["vinyl_application_workbench"],
            "required_station": "workbench",
            "operator_instruction": "Protejează fața, vopsește cantul, usucă, îndepărtează protecția.",
        },
        {
            "seed_code": "face_vinyl_application_final",
            "display_name": "Colantare finală fețe litere",
            "required_skill": ["face_vinyl_application"],
            "required_station": "workbench",
            "operator_instruction": "Colantează fețele litere după asamblare.",
        },
        {
            "seed_code": "stretch_wrap_and_delivery_mounting_package",
            "display_name": "Infoliere cu folie stretch și pregătire colet pentru livrare / montaj",
            "required_skill": ["packing_preparation"],
            "required_station": "packing_area",
            "operator_instruction": "Infoliere stretch, surse în colet, accesorii și note montaj.",
        },
    ]


def build_task_seed_candidates(
    workspace: IntakeV3Workspace,
    operation_flags: OperationFlags | None = None,
) -> list[TaskSeedCandidate]:
    """Build conceptual task seed candidates from operation catalog and flags."""
    flags = operation_flags
    if flags is None:
        finish = workspace.finish_assignment
        support_mode = _resolve_support_mode(workspace)
        ctx = SupportContext(
            shared_support=support_mode == SUPPORT_MODE_SHARED_PENDING,
            illuminated=True,
        )
        flags = (
            derive_operation_flags_from_finishes(finish, ctx)
            if finish
            else OperationFlags()
        )

    material = derive_material_intent(workspace)
    finish_summary = _build_finish_summary(workspace)

    seeds: list[TaskSeedCandidate] = []
    for op in _operation_catalog():
        code = str(op["seed_code"])
        active = True
        active_reason = "always_active_for_volumetric_pilot"
        depends_on: list[str] = []
        materials: list[str] = []

        if code == "graphic_vector_preflight":
            active = workspace.vector_asset is not None or workspace.raw_svg_analysis is not None
            active_reason = "vector_asset_or_analysis_present"
        elif code == "confirmed_production_model":
            depends_on = ["graphic_vector_preflight"]
            active = workspace.confirmed_production_model is not None
        elif code == "cnc_file_preparation":
            depends_on = ["confirmed_production_model"]
        elif code == "return_forming_file_preparation":
            depends_on = ["confirmed_production_model"]
        elif code == "return_vinyl_application_workbench":
            active = flags.return_vinyl_application_required
            active_reason = "return_wrapped_finish"
            depends_on = ["return_forming_file_preparation"]
        elif code == "face_and_backing_cnc_cut":
            depends_on = ["cnc_file_preparation"]
            materials = ["Plexiglas", finish_summary.backing_material or "Forex"]
        elif code == "return_side_forming":
            depends_on = ["return_forming_file_preparation"]
            if flags.return_vinyl_application_required:
                depends_on.append("return_vinyl_application_workbench")
        elif code == "return_face_bonding":
            depends_on = ["face_and_backing_cnc_cut", "return_side_forming"]
        elif code == "led_installation_wiring_and_light_test":
            depends_on = ["face_and_backing_cnc_cut"]
            materials = ["LED modules"]
        elif code == "letter_assembly_no_shared_support":
            depends_on = ["return_face_bonding", "led_installation_wiring_and_light_test"]
        elif code == "return_painting_after_assembly":
            active = flags.return_painting_after_assembly_required
            active_reason = "return_painted_finish"
            depends_on = ["letter_assembly_no_shared_support"]
        elif code == "face_vinyl_application_final":
            active = flags.face_vinyl_application_required
            active_reason = "face_vinyl_enabled"
            depends_on = ["letter_assembly_no_shared_support"]
            if flags.face_vinyl_after_return_painting:
                depends_on = ["return_painting_after_assembly"]
        elif code == "stretch_wrap_and_delivery_mounting_package":
            depends_on = ["letter_assembly_no_shared_support"]
            if flags.face_vinyl_application_required:
                depends_on.append("face_vinyl_application_final")
            if flags.return_painting_after_assembly_required:
                depends_on.append("return_painting_after_assembly")
            if flags.psu_packed_at_packaging:
                materials.append("PSU calculate în colet")

        seeds.append(
            TaskSeedCandidate(
                seed_code=code,
                display_name=str(op["display_name"]),
                active=active,
                active_reason=active_reason if active else "inactive_by_finish_or_context",
                depends_on=depends_on,
                required_skill=list(op["required_skill"]),  # type: ignore[arg-type]
                required_station=str(op["required_station"]),
                operator_instruction=str(op["operator_instruction"]),
                materials_referenced=materials,
                non_executable=True,
                source_operation_code=code,
                employee_mobile_action_allowed=False,
            )
        )

    if material.accessories:
        for seed in seeds:
            if seed.seed_code == "stretch_wrap_and_delivery_mounting_package" and seed.active:
                seed.materials_referenced.extend(
                    [a.name for a in material.accessories if a.category == "packaging"]
                )

    return seeds


def build_production_handoff_preview(workspace: IntakeV3Workspace) -> ProductionHandoffAdapterResult:
    """Build production handoff preview from workspace — not executable."""
    readiness = evaluate_intake_v3_readiness(workspace)
    support_mode = _resolve_support_mode(workspace)
    support_ctx = SupportContext(
        shared_support=support_mode == SUPPORT_MODE_SHARED_PENDING,
        illuminated=True,
    )
    flags = (
        derive_operation_flags_from_finishes(workspace.finish_assignment, support_ctx)
        if workspace.finish_assignment
        else OperationFlags()
    )
    task_seeds = build_task_seed_candidates(workspace, flags)

    confirmed = workspace.confirmed_production_model
    counts = ProductionCountsSummary()
    if confirmed:
        counts = ProductionCountsSummary(
            letter_count=confirmed.letter_count,
            cut_contour_count=confirmed.cut_contour_count,
            inner_hole_count=confirmed.inner_hole_count,
        )

    req = workspace.client_request
    finish = _build_finish_summary(workspace)
    material = derive_material_intent(workspace, support_context=support_ctx)

    mat_summary = ProductionMaterialSummary(
        face_material=finish.face_material or "Plexiglas",
        return_material=finish.return_material,
        backing_material=finish.backing_material or "Forex",
        led_summary=material.led_materials[0].module_type if material.led_materials else None,
        psu_summary=(
            f"quantity={material.power_supplies[0].quantity}"
            if material.power_supplies
            else None
        ),
        accessories=[a.name for a in material.accessories],
        inventory_mutation_allowed=False,
    )

    prod_finish = ProductionFinishSummary(
        face_finish_type=finish.face_finish_type,
        return_finish_type=finish.return_finish_type,
        backing_material=finish.backing_material,
        backing_thickness_mm=finish.backing_thickness_mm,
        face_color_code=finish.face_color_code,
        face_color_name=finish.face_color_name,
        return_color_code=finish.return_color_code,
        return_color_name=finish.return_color_name,
        face_roll_width_mm=finish.face_roll_width_mm,
        return_depth_mm=finish.return_depth_mm,
    )

    dimensions = PricingInputDimensions(
        width_mm=req.width_mm,
        height_mm=req.height_mm,
        depth_mm=req.depth_mm,
    )

    adapter_warnings = [w.message for w in readiness.warnings]
    if support_mode == SUPPORT_MODE_SHARED_PENDING:
        adapter_warnings.append(
            "Suport comun pending — logica finală surse/montaj nu este confirmată."
        )
    if flags.psu_packed_at_packaging:
        adapter_warnings.append(
            "Fără suport comun: sursele calculate se includ în colet la ambalare."
        )

    blocker_codes = [b.code for b in readiness.blockers]
    is_ready = readiness.can_create_quote and readiness.can_generate_production_handoff

    variation_summary = build_finish_variation_summary(workspace.model_dump(mode="json"))
    group_labels = [
        item.label for item in variation_summary.variations if item.source_type == "group"
    ]

    preview = ProductionHandoffPreview(
        template_code=workspace.product_selection.template_code,
        support_mode=support_mode,
        dimensions=dimensions,
        counts=counts,
        finish_summary=prod_finish,
        material_summary=mat_summary,
        task_seeds=task_seeds,
        finish_variation_handoff_notes=list(variation_summary.handoff_preview_notes),
        requires_letter_group_visibility=variation_summary.has_variations,
        group_labels=group_labels,
        letter_override_count=variation_summary.letter_override_count,
    )

    return ProductionHandoffAdapterResult(
        preview=preview,
        adapter_warnings=adapter_warnings,
        adapter_blockers=blocker_codes,
        is_ready_for_handoff=is_ready,
    )


def validate_production_handoff_preview(
    result: ProductionHandoffAdapterResult,
) -> tuple[bool, list[VectorModelIssue]]:
    """Validate preview is non-executable and has no employee hardcoding."""
    issues: list[VectorModelIssue] = []
    preview = result.preview
    if not preview.non_executable:
        issues.append(
            VectorModelIssue(
                code="HANDOFF_MUST_BE_NON_EXECUTABLE",
                severity="blocker",
                message="ProductionHandoffPreview must be non_executable",
            )
        )
    if preview.employee_mobile_action_allowed:
        issues.append(
            VectorModelIssue(
                code="EMPLOYEE_MOBILE_NOT_ALLOWED",
                severity="blocker",
                message="employee_mobile_action_allowed must be false",
            )
        )
    forbidden_names = {"florin", "călin", "calin", "octavian", "goghi", "cristi"}
    for seed in preview.task_seeds:
        blob = f"{seed.operator_instruction} {seed.display_name}".lower()
        for name in forbidden_names:
            if name in blob:
                issues.append(
                    VectorModelIssue(
                        code="HARDCODED_EMPLOYEE_NAME",
                        severity="blocker",
                        message=f"Task seed must not hardcode employee name: {name}",
                        target_field=seed.seed_code,
                    )
                )
        if seed.execution_plan_id is not None or seed.execution_task_id is not None:
            issues.append(
                VectorModelIssue(
                    code="EXECUTION_ID_NOT_ALLOWED",
                    severity="blocker",
                    message="Task seed must not have execution IDs",
                    target_field=seed.seed_code,
                )
            )
    if _resolve_support_mode_from_preview(preview) == SUPPORT_MODE_NO_SHARED:
        active_codes = {s.seed_code for s in preview.task_seeds if s.active}
        if "electrical_source_mounting" in active_codes:
            issues.append(
                VectorModelIssue(
                    code="SOURCE_MOUNTING_NOT_ALLOWED",
                    severity="blocker",
                    message="No shared support must not activate source mounting task",
                )
            )
    return len(issues) == 0, issues


def _resolve_support_mode_from_preview(preview: ProductionHandoffPreview) -> str:
    return preview.support_mode
