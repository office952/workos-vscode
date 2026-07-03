"""Intake V4 production handoff preview — read-only, no ExecutionTask / stock."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.intake_v4 import (
    PILOT_V4_TEMPLATE_CODE,
    IntakeV4MaterialBreakdownResponse,
    IntakeV4ProductionHandoffIssue,
    IntakeV4ProductionHandoffMaterialJob,
    IntakeV4ProductionHandoffOperationGroup,
    IntakeV4ProductionHandoffPreviewResponse,
    IntakeV4ProductionHandoffTaskSeedPreview,
    IntakeV4ProductionHandoffTemplateAlignment,
    IntakeV4TaskPreviewResponse,
    IntakeV4WorkspacePayload,
)
from services.intake_v4_analysis_boundary_service import list_v4_analysis_boundary_blockers
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown_with_registry
from services.intake_v4_cnc_operation_dry_run_service import (
    CNC_TASK_DRY_RUN_SOURCE,
    CNC_TASK_DRY_RUN_SOURCE_COMPAT_FALLBACK,
    build_cnc_dry_run_from_operation_rows,
)
from services.intake_v4_edge_cant_dry_run_service import build_edge_cant_dry_run_from_operation_rows
from services.shared_edge_cant_rules import EDGE_CANT_TASK_DRY_RUN_SOURCE
from services.intake_v4_production_preview_service import build_v4_task_preview_response
from services.intake_v4_template_option_contract_service import collect_template_contract_handoff_issues
from services.tpl_volumetric_operation_keys_service import (
    evaluate_handoff_group_alignment,
    get_operation_spec,
    resolve_canonical_from_catalog,
    resolve_canonical_keys_from_catalog,
    summarize_template_operation_alignment,
)

_MATERIAL_JOB_SPECS: dict[str, dict[str, str]] = {
    "plexiglas_face": {
        "job_key": "face_plexiglas_cutting",
        "role": "face",
        "display_name": "Debitare față plexiglas",
    },
    "forex_backing": {
        "job_key": "forex_backing_cutting",
        "role": "backing",
        "display_name": "Debitare spate Forex",
    },
    "face_vinyl": {
        "job_key": "oracal_vinyl_cutting",
        "role": "face",
        "display_name": "Colantare / debitare Oracal",
    },
    "letter_face_print_vinyl": {
        "job_key": "print_vinyl_artwork",
        "role": "face",
        "display_name": "Print vinil față",
    },
    "letter_face_laminated_vinyl": {
        "job_key": "laminate_vinyl_artwork",
        "role": "face",
        "display_name": "Laminare print față",
    },
    "return_material": {
        "job_key": "return_profile_material",
        "role": "return",
        "display_name": "Cant / volum calculat",
    },
    "led_modules": {
        "job_key": "led_modules_install",
        "role": "electrical",
        "display_name": "Module LED",
    },
    "led_psu": {
        "job_key": "psu_electrical",
        "role": "electrical",
        "display_name": "Sursă LED 12V",
    },
}

_OPERATION_GROUPS: list[dict[str, Any]] = [
    {
        "group_key": "cnc_cutting",
        "title": "CNC / debitare față & spate",
        "description": "Pregătire fișiere și debitare plexiglas/Forex",
        "station_hint": "cnc_router",
        "operation_codes": ["cnc_file_preparation", "face_and_backing_cnc_cut"],
        "material_job_keys": ["face_plexiglas_cutting", "forex_backing_cutting"],
    },
    {
        "group_key": "vinyl_print_finish",
        "title": "Colantare / print față",
        "description": "Oracal, print sau laminare artwork",
        "station_hint": "workbench",
        "operation_codes": ["return_vinyl_application_workbench", "face_vinyl_application_final"],
        "material_job_keys": ["oracal_vinyl_cutting", "print_vinyl_artwork", "laminate_vinyl_artwork"],
    },
    {
        "group_key": "return_forming",
        "title": "Modelare cant / volum",
        "description": "Pregătire traseu și modelare profil lateral",
        "station_hint": "return_forming_machine",
        "operation_codes": ["return_forming_file_preparation", "return_side_forming"],
        "material_job_keys": ["return_profile_material"],
    },
    {
        "group_key": "return_bonding",
        "title": "Lipire cant la fețe",
        "description": "Cant modelat pe plexiglas",
        "station_hint": "assembly_bench",
        "operation_codes": ["return_face_bonding"],
        "material_job_keys": ["return_profile_material", "face_plexiglas_cutting"],
    },
    {
        "group_key": "led_electrical",
        "title": "Montaj LED / electric",
        "description": "Module LED, cablaj și surse",
        "station_hint": "electrical_bench",
        "operation_codes": ["led_installation_wiring_and_light_test"],
        "material_job_keys": ["led_modules_install", "psu_electrical"],
    },
    {
        "group_key": "assembly",
        "title": "Asamblare litere",
        "description": "Corp față+cant pe Forex",
        "station_hint": "assembly_bench",
        "operation_codes": ["letter_assembly_no_shared_support"],
        "material_job_keys": ["face_plexiglas_cutting", "forex_backing_cutting", "return_profile_material"],
    },
    {
        "group_key": "preflight_qc",
        "title": "Verificare / pregătire montaj",
        "description": "Preflight vector și pregătire livrare",
        "station_hint": "graphics_workstation",
        "operation_codes": [
            "graphic_vector_preflight",
            "confirmed_production_model",
            "stretch_wrap_and_delivery_mounting_package",
        ],
        "material_job_keys": [],
    },
]

_TASK_SEED_HINTS: dict[str, dict[str, Any]] = {
    "cnc_file_preparation": {
        "task_key": "cnc_file_prep",
        "role_hint": "cnc_preparation",
        "source_material_jobs": ["face_plexiglas_cutting", "forex_backing_cutting"],
    },
    "face_and_backing_cnc_cut": {
        "task_key": "cnc_face_back_cutting",
        "role_hint": "cnc_operator",
        "source_material_jobs": ["face_plexiglas_cutting", "forex_backing_cutting"],
    },
    "return_forming_file_preparation": {
        "task_key": "return_forming_prep",
        "role_hint": "cnc_preparation",
        "source_material_jobs": ["return_profile_material"],
    },
    "return_vinyl_application_workbench": {
        "task_key": "return_vinyl_workbench",
        "role_hint": "vinyl_operator",
        "source_material_jobs": ["oracal_vinyl_cutting", "return_profile_material"],
    },
    "return_side_forming": {
        "task_key": "return_side_forming",
        "role_hint": "return_forming_operator",
        "source_material_jobs": ["return_profile_material"],
    },
    "return_face_bonding": {
        "task_key": "return_face_bonding",
        "role_hint": "assembly_operator",
        "source_material_jobs": ["return_profile_material", "face_plexiglas_cutting"],
    },
    "led_installation_wiring_and_light_test": {
        "task_key": "led_installation",
        "role_hint": "electrical_operator",
        "source_material_jobs": ["led_modules_install", "psu_electrical"],
    },
    "letter_assembly_no_shared_support": {
        "task_key": "letter_assembly",
        "role_hint": "assembly_operator",
        "source_material_jobs": ["face_plexiglas_cutting", "forex_backing_cutting", "return_profile_material"],
    },
    "face_vinyl_application_final": {
        "task_key": "face_vinyl_final",
        "role_hint": "vinyl_operator",
        "source_material_jobs": ["oracal_vinyl_cutting", "print_vinyl_artwork", "laminate_vinyl_artwork"],
    },
    "graphic_vector_preflight": {
        "task_key": "vector_preflight",
        "role_hint": "graphic_design",
        "source_material_jobs": [],
    },
    "confirmed_production_model": {
        "task_key": "production_model_confirm",
        "role_hint": "graphic_design",
        "source_material_jobs": [],
    },
    "stretch_wrap_and_delivery_mounting_package": {
        "task_key": "delivery_prep",
        "role_hint": "assembly_operator",
        "source_material_jobs": [],
    },
}

_BLOCKER_MESSAGES: dict[str, str] = {
    "missing_svg_source_hash": "Lipsește hash SVG persistat.",
    "svg_not_analyzed": "SVG neanalizat.",
    "missing_svg_analysis_json": "Lipsește analysis bundle persistat.",
    "missing_layer_role_setup": "Lipsește layer role setup.",
    "layer_roles_incomplete": "Layer roles neconfirmate.",
    "missing_quote_geometry_perimeter": "Lipsește perimetrul din quote geometry.",
    "missing_quote_geometry_metrics": "Lipsesc metrici quote geometry.",
    "finish_setup_not_confirmed": "Finish setup neconfirmat.",
    "unsupported_template": "Template în afara pilotului V4.",
}


def _issue(code: str, *, severity: str = "warning", source: str, message: str | None = None) -> IntakeV4ProductionHandoffIssue:
    return IntakeV4ProductionHandoffIssue(
        code=code,
        severity=severity,  # type: ignore[arg-type]
        message=message or _BLOCKER_MESSAGES.get(code, code),
        source=source,
    )


def _material_jobs_from_breakdown(breakdown: IntakeV4MaterialBreakdownResponse) -> list[IntakeV4ProductionHandoffMaterialJob]:
    jobs: list[IntakeV4ProductionHandoffMaterialJob] = []
    for row in breakdown.material_rows + breakdown.consumable_rows:
        if row.quantity <= 0:
            continue
        spec = _MATERIAL_JOB_SPECS.get(row.material_key)
        if spec is None:
            continue
        row_warnings: list[str] = []
        if row.price_source == "missing":
            row_warnings.append("missing_pricing_registry_row")
        jobs.append(
            IntakeV4ProductionHandoffMaterialJob(
                job_key=spec["job_key"],
                material_code=row.material_code or row.registry_code,
                role=spec["role"],
                display_name=spec["display_name"],
                quantity_basis=row.quantity_basis,
                quantity=row.base_quantity or row.quantity,
                priced_quantity=row.priced_quantity,
                waste_percent=row.waste_percent,
                unit=row.unit,
                source="intake_v4_material_breakdown",
                confidence=row.confidence,
                creates_stock_reservation=False,
                quote_estimate_only=True,
                warnings=row_warnings,
            )
        )
    for prefix in ("artwork_plexiglas_", "artwork_return_"):
        for row in breakdown.material_rows:
            if not row.material_key.startswith(prefix) or row.quantity <= 0:
                continue
            suffix = row.material_key.replace("artwork_", "")
            jobs.append(
                IntakeV4ProductionHandoffMaterialJob(
                    job_key=f"artwork_{suffix}",
                    material_code=row.material_code or row.registry_code,
                    role="artwork",
                    display_name=row.display_name,
                    quantity_basis=row.quantity_basis,
                    quantity=row.base_quantity or row.quantity,
                    unit=row.unit,
                    confidence=row.confidence,
                    warnings=["artwork_volumetric_separate"] if "plexiglas" in row.material_key else [],
                )
            )
    return jobs


def _operation_groups_from_preview(
    material_jobs: list[IntakeV4ProductionHandoffMaterialJob],
    task_preview: IntakeV4TaskPreviewResponse,
) -> list[IntakeV4ProductionHandoffOperationGroup]:
    job_keys = {job.job_key for job in material_jobs}
    active_codes = {item.operation_code for item in task_preview.items if item.active}
    groups: list[IntakeV4ProductionHandoffOperationGroup] = []
    for spec in _OPERATION_GROUPS:
        related_jobs = [key for key in spec["material_job_keys"] if key in job_keys]
        related_ops = [code for code in spec["operation_codes"] if code in active_codes]
        active = bool(related_ops) or (not spec["material_job_keys"] and related_ops)
        if not spec["operation_codes"]:
            active = False
        elif not related_ops and spec["material_job_keys"] and not related_jobs:
            active = False
        elif not related_ops:
            active = False

        canonical_keys, alignment_info = evaluate_handoff_group_alignment(
            spec["group_key"],
            active=active,
            active_material_job_keys=job_keys,
        )
        template_alignment = IntakeV4ProductionHandoffTemplateAlignment(
            status=alignment_info.status,
            provisional=alignment_info.provisional,
            source=alignment_info.source,
            missing_keys=list(alignment_info.missing_keys),
            partial_keys=list(alignment_info.partial_keys),
        )

        groups.append(
            IntakeV4ProductionHandoffOperationGroup(
                group_key=spec["group_key"],
                title=spec["title"],
                description=spec.get("description"),
                station_hint=spec.get("station_hint"),
                operation_codes=canonical_keys or related_ops or list(spec["operation_codes"]),
                legacy_operation_codes=related_ops or list(spec["operation_codes"]),
                material_job_keys=related_jobs,
                canonical_operation_keys=canonical_keys,
                operation_code_source=(
                    "product_system_dossier" if canonical_keys else "operation_catalog_compat"
                ),
                template_alignment=template_alignment,
                active=active,
                inactive_reason=None if active else "missing_material_or_operation_data",
            )
        )
    return groups


def _task_seed_preview_from_items(
    task_preview: IntakeV4TaskPreviewResponse,
    material_jobs: list[IntakeV4ProductionHandoffMaterialJob],
) -> list[IntakeV4ProductionHandoffTaskSeedPreview]:
    available_jobs = {job.job_key for job in material_jobs}
    seeds: list[IntakeV4ProductionHandoffTaskSeedPreview] = []
    for item in task_preview.items:
        hints = _TASK_SEED_HINTS.get(item.operation_code, {})
        canonical_operation_keys = resolve_canonical_keys_from_catalog(item.operation_code)
        canonical_operation_key = (
            canonical_operation_keys[0]
            if canonical_operation_keys
            else resolve_canonical_from_catalog(item.operation_code)
        )
        operation_spec = get_operation_spec(canonical_operation_key or "")
        operation_code = canonical_operation_key or item.operation_code
        depends_on = [
            resolve_canonical_from_catalog(dep) or dep for dep in list(item.depends_on or [])
        ]
        station_hint = item.workcenter or hints.get("station_hint")
        role_hint = hints.get("role_hint")
        if operation_spec:
            station_hint = item.workcenter or operation_spec.station_hint
            role_hint = operation_spec.role_hint
        source_jobs = [
            key for key in hints.get("source_material_jobs", []) if key in available_jobs
        ]
        notes: list[str] = []
        if item.operator_instruction:
            notes.append(item.operator_instruction)
        notes.append("Preview seed — nu creează ExecutionTask.")
        seeds.append(
            IntakeV4ProductionHandoffTaskSeedPreview(
                task_key=hints.get("task_key", item.operation_code),
                title=item.label,
                operation_code=operation_code,
                legacy_operation_code=item.operation_code if canonical_operation_key else None,
                canonical_operation_key=canonical_operation_key,
                canonical_operation_keys=canonical_operation_keys,
                dossier_operation_key=operation_spec.dossier_operation_key if operation_spec else None,
                future_execution_task_type=(
                    operation_spec.future_execution_task_type if operation_spec else None
                ),
                operation_code_source=(
                    "product_system_dossier"
                    if canonical_operation_key
                    else "operation_catalog_compat"
                ),
                station_hint=station_hint,
                role_hint=role_hint,
                depends_on=depends_on,
                source_material_jobs=source_jobs,
                creates_execution_task=False,
                active=item.active,
                inactive_reason=item.inactive_reason,
                notes=notes,
            )
        )
    return seeds


def _collect_blockers_and_warnings(
    payload: IntakeV4WorkspacePayload,
    breakdown: IntakeV4MaterialBreakdownResponse | None,
) -> tuple[list[IntakeV4ProductionHandoffIssue], list[IntakeV4ProductionHandoffIssue]]:
    blockers: list[IntakeV4ProductionHandoffIssue] = []
    warnings: list[IntakeV4ProductionHandoffIssue] = []

    if payload.product_binding.template_code != PILOT_V4_TEMPLATE_CODE:
        blockers.append(
            _issue("unsupported_template", severity="blocking", source="product_binding.template_code")
        )

    for code in list_v4_analysis_boundary_blockers(payload):
        blockers.append(_issue(code, severity="blocking", source="analysis_boundary"))

    setup = payload.finish_setup
    if setup is None or not setup.confirmed:
        blockers.append(
            _issue("finish_setup_not_confirmed", severity="blocking", source="finish_setup")
        )
    else:
        if setup.illuminated is not False and not setup.psu_configuration:
            warnings.append(
                _issue("missing_psu_config", source="finish_setup.psu_configuration")
            )
        if setup.return_depth_mm is None:
            warnings.append(_issue("missing_return_depth", source="finish_setup.return_depth_mm"))
        if setup.illuminated is not False and setup.estimated_led_watts is None:
            warnings.append(_issue("missing_led_estimate", source="finish_setup.estimated_led_watts"))

    if breakdown:
        for warn in breakdown.warnings:
            severity = "info" if warn.severity == "info" else "warning"
            warnings.append(
                IntakeV4ProductionHandoffIssue(
                    code=warn.code,
                    severity=severity,  # type: ignore[arg-type]
                    message=warn.message,
                    source=warn.source,
                )
            )
        if breakdown.totals.contains_missing_prices:
            warnings.append(
                _issue("missing_pricing_registry_row", source="intake_v4_material_breakdown.totals")
            )

    for contract_issue in collect_template_contract_handoff_issues(payload):
        severity = contract_issue.severity
        if severity == "blocking":
            blockers.append(
                _issue(
                    contract_issue.code,
                    severity="blocking",
                    source=contract_issue.source,
                    message=contract_issue.message,
                )
            )
        else:
            warnings.append(
                IntakeV4ProductionHandoffIssue(
                    code=contract_issue.code,
                    severity=severity,  # type: ignore[arg-type]
                    message=contract_issue.message,
                    source=contract_issue.source,
                )
            )

    return blockers, warnings


async def build_intake_v4_production_handoff_preview(
    db: AsyncSession,
    workspace_id: str,
    payload_raw: dict[str, Any],
    payload: IntakeV4WorkspacePayload,
) -> IntakeV4ProductionHandoffPreviewResponse:
    """Read-only production handoff preview — quote estimate, no stock/tasks."""
    blockers, warnings = _collect_blockers_and_warnings(payload, breakdown=None)

    breakdown: IntakeV4MaterialBreakdownResponse | None = None
    material_jobs: list[IntakeV4ProductionHandoffMaterialJob] = []
    blocking_codes = {item.code for item in blockers if item.severity == "blocking"}
    can_build_breakdown = "unsupported_template" not in blocking_codes

    if can_build_breakdown and not blocking_codes:
        breakdown = await build_intake_v4_material_breakdown_with_registry(db, workspace_id, payload_raw)
        material_jobs = _material_jobs_from_breakdown(breakdown)
        _, extra_warnings = _collect_blockers_and_warnings(payload, breakdown)
        warnings = extra_warnings
    elif can_build_breakdown:
        try:
            breakdown = await build_intake_v4_material_breakdown_with_registry(db, workspace_id, payload_raw)
            material_jobs = _material_jobs_from_breakdown(breakdown)
            _, extra_warnings = _collect_blockers_and_warnings(payload, breakdown)
            warnings = extra_warnings
        except Exception:
            pass

    task_preview = build_v4_task_preview_response(
        workspace_id=workspace_id,
        template_code=payload.product_binding.template_code,
        payload=payload,
    )
    operation_groups = _operation_groups_from_preview(material_jobs, task_preview)
    task_seeds = _task_seed_preview_from_items(task_preview, material_jobs)

    handoff_group_dicts = [
        {
            "group_key": g.group_key,
            "template_alignment": (
                g.template_alignment.model_dump() if g.template_alignment else {}
            ),
        }
        for g in operation_groups
    ]
    alignment_summary = summarize_template_operation_alignment(
        handoff_groups=handoff_group_dicts,
    )

    production_notes = [
        "Preview producție — nu creează ExecutionTask, ExecutionPlan sau WorkSession.",
        "Cantitățile materiale provin din estimare ofertă (nesting/geometry), nu consum stoc.",
        "Total comercial și operații tarifate rămân în QuoteWizard / CostEngine.",
    ]

    operation_rows = list(breakdown.operation_rows or []) if breakdown else []
    legacy_cnc_mapping_used = not operation_rows
    compat_cnc_mapping_used = legacy_cnc_mapping_used
    cnc_task_source = CNC_TASK_DRY_RUN_SOURCE if operation_rows else CNC_TASK_DRY_RUN_SOURCE_COMPAT_FALLBACK
    cnc_operation_candidates = (
        build_cnc_dry_run_from_operation_rows(
            operation_rows,
            workspace_id=workspace_id,
            template_code=payload.product_binding.template_code,
            source_fingerprint="handoff_preview",
        )[1]
        if operation_rows
        else []
    )
    if operation_rows:
        warnings.append(
            _issue(
                "cnc_preview_from_operation_rows",
                severity="info",
                message="CNC operation preview aligned with material breakdown operation_rows.",
                source="cnc_task_dry_run",
            )
        )
    elif breakdown is not None:
        warnings.append(
            _issue(
                "cnc_dry_run_legacy_parallel_mapping",
                message="CNC preview uses compatibility fallback mapping because operation_rows are missing.",
                source="cnc_task_dry_run",
            )
        )

    edge_cant_operation_rows = list(breakdown.edge_cant_operation_rows or []) if breakdown else []
    edge_cant_task_source = EDGE_CANT_TASK_DRY_RUN_SOURCE if edge_cant_operation_rows else None
    edge_cant_operation_candidates = (
        build_edge_cant_dry_run_from_operation_rows(
            edge_cant_operation_rows,
            workspace_id=workspace_id,
            template_code=payload.product_binding.template_code,
            source_fingerprint="handoff_preview",
        )[1]
        if edge_cant_operation_rows
        else []
    )
    if edge_cant_operation_rows:
        warnings.append(
            _issue(
                "edge_cant_preview_from_operation_rows",
                severity="info",
                message="Edge/cant operation preview aligned with material breakdown edge_cant_operation_rows.",
                source="edge_cant_task_dry_run",
            )
        )

    return IntakeV4ProductionHandoffPreviewResponse(
        workspace_id=workspace_id,
        template_code=payload.product_binding.template_code,
        handoff_mode="preview_only",
        stock_consumption=False,
        creates_execution_tasks=False,
        creates_stock_reservations=False,
        quote_estimate_only=True,
        production_notes=production_notes,
        material_jobs=material_jobs,
        operation_groups=operation_groups,
        task_seed_preview=task_seeds,
        cnc_operation_candidates=cnc_operation_candidates,
        cnc_task_source=cnc_task_source,
        compat_cnc_mapping_used=compat_cnc_mapping_used,
        legacy_cnc_mapping_used=legacy_cnc_mapping_used,
        edge_cant_operation_candidates=edge_cant_operation_candidates,
        edge_cant_task_source=edge_cant_task_source,
        blockers=blockers,
        warnings=warnings,
        summary={
            "material_jobs_count": len(material_jobs),
            "operation_groups_count": sum(1 for g in operation_groups if g.active),
            "task_seed_preview_count": sum(1 for t in task_seeds if t.active),
            "blockers_count": len(blockers),
            "warnings_count": len(warnings),
            "has_material_breakdown": breakdown is not None,
            "cnc_task_source": cnc_task_source,
            "compat_cnc_mapping_used": compat_cnc_mapping_used,
            "legacy_cnc_mapping_used": legacy_cnc_mapping_used,
            "cnc_operation_candidate_count": len(cnc_operation_candidates),
            "edge_cant_task_source": edge_cant_task_source,
            "edge_cant_operation_candidate_count": len(edge_cant_operation_candidates),
            "template_operation_alignment": alignment_summary.to_dict(),
        },
    )
