"""Intake V3 production task generation dry-run — read-only preview, no ExecutionPlan/Task."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE, SUPPORT_MODE_SHARED_PENDING
from schemas.intake_v3 import (
    IntakeV3CandidateProductionTask,
    IntakeV3CandidateTaskDependency,
    IntakeV3CandidateTaskGroup,
    IntakeV3CandidateTaskInput,
    IntakeV3ProductionTaskDryRunResponse,
    IntakeV3ProductionTaskDryRunSummary,
    IntakeV3TaskDryRunBoundary,
    IntakeV3TaskGenerationBlocker,
    OperationFlags,
    SupportContext,
    TaskSeedCandidate,
)
from services.intake_v3_finish_material_service import derive_operation_flags_from_finishes
from services.intake_v3_material_quantity_breakdown_service import (
    Iv3SourceContext,
    extract_confirmed_production_model,
    extract_finish_assignments,
    extract_geometry_summary,
    load_iv3_source_context,
)
from services.intake_v3_order_production_readiness_service import (
    STATUS_READY,
    _has_finish_assignment_data,
    get_iv3_order_production_readiness,
    get_iv3_order_production_readiness_by_quote,
)
from services.intake_v3_pricing_input_adapter import _resolve_support_mode
from services.intake_v3_production_handoff_adapter import build_task_seed_candidates
from services.intake_v3_guarded_convert_to_order_service import check_existing_order_for_iv3_quote
from services.intake_v3_real_commercial_quote_creation_service import INTAKE_V3_SOURCE_MODULE

DRY_RUN_SCOPE = "production_task_generation_preview_only"

FUTURE_BUILDS = [
    "guarded execution plan creation",
    "guarded execution task creation",
    "assignment and scheduling",
    "inventory availability check",
]

TASK_GROUP_CATALOG: list[dict[str, Any]] = [
    {
        "group_key": "prepress",
        "title": "Prepress / verificare fișiere",
        "description": "Graphic verification, production model confirmation, CNC file preparation.",
        "sort_order": 1,
        "seed_codes": [
            "graphic_vector_preflight",
            "confirmed_production_model",
            "cnc_file_preparation",
        ],
    },
    {
        "group_key": "cnc_faces",
        "title": "CNC fețe plexiglas",
        "description": "CNC cutting and optional bevel on acrylic faces.",
        "sort_order": 2,
        "seed_codes": ["face_and_backing_cnc_cut"],
        "split_tasks": [
            {
                "candidate_task_id": "dryrun-cnc-face-cutting",
                "title": "CNC debitare fețe plexiglas",
                "operation_type": "cnc_cutting_preview",
                "station_hint": "CNC",
                "department_hint": "production_cnc",
                "source_seed": "face_and_backing_cnc_cut",
            },
            {
                "candidate_task_id": "dryrun-cnc-face-bevel",
                "title": "CNC șanfren fețe plexiglas",
                "operation_type": "cnc_bevel_preview",
                "station_hint": "CNC",
                "department_hint": "production_cnc",
                "source_seed": "face_and_backing_cnc_cut",
                "conditional_metric": "bevel_perimeter_ml",
            },
        ],
    },
    {
        "group_key": "cnc_backing",
        "title": "CNC backing Forex",
        "description": "CNC cutting Forex backing panels.",
        "sort_order": 3,
        "seed_codes": ["face_and_backing_cnc_cut"],
        "split_tasks": [
            {
                "candidate_task_id": "dryrun-cnc-backing-cutting",
                "title": "CNC debitare backing Forex",
                "operation_type": "cnc_cutting_preview",
                "station_hint": "CNC",
                "department_hint": "production_cnc",
                "source_seed": "face_and_backing_cnc_cut",
                "parallel_with": ["dryrun-cnc-face-cutting", "dryrun-return-side-forming"],
            },
        ],
    },
    {
        "group_key": "return_forming",
        "title": "Cant aluminiu / modelare cant",
        "description": "Return forming file prep, optional vinyl wrap, forming and bonding.",
        "sort_order": 4,
        "seed_codes": [
            "return_forming_file_preparation",
            "return_vinyl_application_workbench",
            "return_side_forming",
            "return_face_bonding",
        ],
    },
    {
        "group_key": "finishing",
        "title": "Finisaj / colantare",
        "description": "Return painting and face vinyl application when finish requires.",
        "sort_order": 5,
        "seed_codes": ["return_painting_after_assembly", "face_vinyl_application_final"],
    },
    {
        "group_key": "led_electrical",
        "title": "LED / electrică",
        "description": "LED installation, wiring, and per-letter light test on backing.",
        "sort_order": 6,
        "seed_codes": ["led_installation_wiring_and_light_test"],
    },
    {
        "group_key": "assembly",
        "title": "Asamblare litere",
        "description": "Final letter assembly on Forex backing.",
        "sort_order": 7,
        "seed_codes": ["letter_assembly_no_shared_support"],
    },
    {
        "group_key": "packaging",
        "title": "Ambalare / predare montaj",
        "description": "Stretch wrap, PSU packaging, and delivery/mounting handoff.",
        "sort_order": 8,
        "seed_codes": ["stretch_wrap_and_delivery_mounting_package"],
    },
]

SEED_STATION_MAP: dict[str, tuple[str, str]] = {
    "graphic_vector_preflight": ("graphics_workstation", "prepress"),
    "confirmed_production_model": ("graphics_workstation", "prepress"),
    "cnc_file_preparation": ("cnc_preparation_station", "prepress"),
    "return_forming_file_preparation": ("cnc_preparation_station", "return_forming"),
    "return_vinyl_application_workbench": ("workbench", "finishing"),
    "face_and_backing_cnc_cut": ("cnc_router", "production_cnc"),
    "return_side_forming": ("return_forming_machine", "return_forming"),
    "return_face_bonding": ("assembly_bench", "assembly"),
    "led_installation_wiring_and_light_test": ("electrical_bench", "electrical"),
    "letter_assembly_no_shared_support": ("assembly_bench", "assembly"),
    "return_painting_after_assembly": ("workbench", "finishing"),
    "face_vinyl_application_final": ("workbench", "finishing"),
    "stretch_wrap_and_delivery_mounting_package": ("packing_area", "packaging"),
}


def _blocker(
    code: str,
    message: str,
    *,
    source: str,
    severity: str = "blocking",
) -> IntakeV3TaskGenerationBlocker:
    return IntakeV3TaskGenerationBlocker(
        code=code,
        severity=severity,
        message=message,
        source=source,
    )


def _candidate_id(seed_code: str) -> str:
    return f"dryrun-{seed_code.replace('_', '-')}"


def _resolve_operation_flags(context: Iv3SourceContext) -> OperationFlags:
    workspace = context.workspace
    if workspace is None:
        return OperationFlags()
    if workspace.finish_assignment is None:
        return OperationFlags()
    support_mode = _resolve_support_mode(workspace)
    ctx = SupportContext(
        shared_support=support_mode == SUPPORT_MODE_SHARED_PENDING,
        illuminated=True,
    )
    return derive_operation_flags_from_finishes(workspace.finish_assignment, ctx)


def build_task_generation_blockers(
    context: Iv3SourceContext,
    *,
    production_readiness_status: str | None,
    has_confirmed_model: bool,
    has_finish_assignments: bool,
    material_breakdown_available: bool,
    geometry_quality: str,
) -> tuple[list[IntakeV3TaskGenerationBlocker], list[IntakeV3TaskGenerationBlocker]]:
    blockers: list[IntakeV3TaskGenerationBlocker] = []
    warnings: list[IntakeV3TaskGenerationBlocker] = []

    if not context.is_intake_v3:
        warnings.append(
            _blocker(
                "not_intake_v3_source",
                "Source is not an Intake V3 order/quote/workspace payload.",
                source="source_detection",
                severity="warning",
            )
        )
        return blockers, warnings

    if context.source_type == "quote" and context.order is None:
        warnings.append(
            _blocker(
                "missing_order",
                "No converted order yet — task dry-run uses quote/workspace snapshots only.",
                source="orders.id",
                severity="warning",
            )
        )

    if context.quote_linkage is None and context.source_type != "workspace":
        blockers.append(
            _blocker(
                "missing_intake_v3_linkage",
                "Intake V3 linkage is missing from quote notes.",
                source="quotes.notes.intake_v3_linkage_v1",
            )
        )

    if production_readiness_status and production_readiness_status not in {
        STATUS_READY,
        "ready_for_handoff_preview",
    }:
        if production_readiness_status.endswith("_blocked") or production_readiness_status == "blocked":
            blockers.append(
                _blocker(
                    "production_readiness_not_ready",
                    "Production readiness audit is not ready for handoff preview.",
                    source="production_readiness_status",
                )
            )
        else:
            warnings.append(
                _blocker(
                    "missing_production_readiness",
                    "Production readiness audit incomplete or not loaded for converted order.",
                    source="production_readiness_status",
                    severity="warning",
                )
            )

    if not has_confirmed_model:
        blockers.append(
            _blocker(
                "missing_confirmed_production_model",
                "Confirmed production model is required before task generation dry-run.",
                source="quote.notes.intake_v3_linkage_v1.snapshot.sections.confirmed_production_model_snapshot",
            )
        )

    if not has_finish_assignments:
        blockers.append(
            _blocker(
                "missing_finish_assignments",
                "Finish assignments are required before task generation dry-run.",
                source="quote.notes.intake_v3_linkage_v1.snapshot.sections.finish_assignment_snapshot",
            )
        )

    if not material_breakdown_available:
        warnings.append(
            _blocker(
                "missing_material_breakdown",
                "Material breakdown is unavailable — material inputs may be partial or missing.",
                source="material_breakdown",
                severity="warning",
            )
        )

    from services.intake_v3_geometry_metrics_snapshot_service import (
        parse_snapshot_from_sections,
        parse_snapshot_from_workspace,
    )

    geometry_snapshot = parse_snapshot_from_sections(context.sections)
    if geometry_snapshot is None:
        geometry_snapshot = parse_snapshot_from_workspace(context.workspace)
    effective_geometry_quality = geometry_quality
    if geometry_snapshot is not None:
        effective_geometry_quality = (
            "partial"
            if geometry_snapshot.geometry_status != "geometry_complete"
            else "calculated"
        )

    if effective_geometry_quality == "partial":
        warnings.append(
            _blocker(
                "geometry_partial",
                "Geometry metrics are partial — perimeter-dependent task inputs may be incomplete.",
                source="geometry_metrics_snapshot",
                severity="warning",
            )
        )

    template = context.product_template
    if template != PILOT_TEMPLATE_CODE:
        warnings.append(
            _blocker(
                "unsupported_product_template",
                f"Task dry-run preview supports {PILOT_TEMPLATE_CODE} only; got {template}.",
                source="workspace_identity_snapshot.template_code",
                severity="warning",
            )
        )

    return blockers, warnings


def _geometry_inputs(
    geometry_summary: Any,
    material_breakdown_available: bool,
) -> list[IntakeV3CandidateTaskInput]:
    quality = geometry_summary.calculation_quality or "calculated"
    if quality == "partial":
        input_quality = "partial"
    elif quality == "missing":
        input_quality = "missing"
    else:
        input_quality = "calculated" if material_breakdown_available else "partial"

    perimeter_quality = input_quality
    if getattr(geometry_summary, "operator_confirmed_layer_roles", False):
        perimeter_quality = "calculated"
    elif getattr(geometry_summary, "perimeter_classification_status", None) in {"partial", "missing"}:
        perimeter_quality = "partial" if geometry_summary.perimeter_classification_status == "partial" else "missing"
    elif getattr(geometry_summary, "perimeter_classification_source", None):
        perimeter_quality = "calculated"

    inputs = [
        IntakeV3CandidateTaskInput(
            label="Real letters",
            value=geometry_summary.real_letters_count,
            unit="letters",
            quality=input_quality,
        ),
        IntakeV3CandidateTaskInput(
            label="Closed contours",
            value=geometry_summary.closed_contours_count,
            unit="contours",
            quality=input_quality,
        ),
        IntakeV3CandidateTaskInput(
            label="Holes (not letters)",
            value=geometry_summary.inner_holes_count,
            unit="holes",
            quality=input_quality,
        ),
        IntakeV3CandidateTaskInput(
            label="Face cutting perimeter",
            value=getattr(geometry_summary, "face_cutting_perimeter_ml", None)
            or geometry_summary.total_letter_perimeter_ml,
            unit="ml",
            quality=perimeter_quality,
        ),
        IntakeV3CandidateTaskInput(
            label="Return material perimeter",
            value=geometry_summary.return_material_perimeter_ml,
            unit="ml",
            quality=perimeter_quality,
        ),
        IntakeV3CandidateTaskInput(
            label="Bevel perimeter",
            value=geometry_summary.bevel_perimeter_ml,
            unit="ml",
            quality=perimeter_quality,
        ),
    ]
    return inputs


def _classification_task_warnings(geometry_summary: Any) -> list[str]:
    codes: list[str] = []
    status = getattr(geometry_summary, "perimeter_classification_status", None)
    if status in {"partial", "missing"}:
        codes.append("geometry_partial")
    face = getattr(geometry_summary, "face_cutting_perimeter_ml", None) or geometry_summary.total_letter_perimeter_ml
    if not face or float(face) <= 0:
        codes.append("face_perimeter_missing")
    if not geometry_summary.return_material_perimeter_ml or float(geometry_summary.return_material_perimeter_ml) <= 0:
        codes.append("return_perimeter_missing")
    if not geometry_summary.bevel_perimeter_ml or float(geometry_summary.bevel_perimeter_ml) <= 0:
        codes.append("bevel_perimeter_missing")
    if getattr(geometry_summary, "operator_confirmed_layer_roles", False) is False:
        codes.append("layer_roles_unconfirmed")
    for warning in geometry_summary.warnings or []:
        if warning in {
            "backing_perimeter_missing",
            "return_perimeter_missing",
            "bevel_perimeter_missing",
            "contour_role_split_missing",
            "face_perimeter_missing",
        }:
            codes.append(warning)
    return list(dict.fromkeys(codes))


def _material_input(
    label: str,
    row: Any | None,
    availability_row: Any | None = None,
    procurement_row: Any | None = None,
) -> IntakeV3CandidateTaskInput:
    if row is None:
        return IntakeV3CandidateTaskInput(label=label, value=None, quality="missing")
    quality = row.quantity_quality or "calculated"
    availability_status = availability_row.availability_status if availability_row is not None else None
    procurement_status = procurement_row.procurement_status if procurement_row is not None else None
    return IntakeV3CandidateTaskInput(
        label=label,
        value=row.quantity,
        unit=row.unit,
        quality=quality,
        availability_status=availability_status,
        procurement_status=procurement_status,
    )


def _append_procurement_task_warnings(
    task_warnings: list[str],
    material_key: str | None,
    procurement_by_key: dict[str, Any],
) -> None:
    if not material_key:
        return
    procurement_row = procurement_by_key.get(material_key)
    if procurement_row is None:
        return
    status = procurement_row.procurement_status
    if status == "owner_decision_required":
        task_warnings.append(f"procurement_owner_decision_{material_key}")
    elif status == "purchase_recommended":
        task_warnings.append(f"procurement_purchase_recommended_{material_key}")
    elif status in {"manual_check", "unknown"}:
        task_warnings.append(f"procurement_manual_check_{material_key}")
    elif status == "indirect_consumable":
        task_warnings.append(f"procurement_indirect_consumable_{material_key}")


def _append_material_availability_task_warnings(
    task_warnings: list[str],
    material_key: str | None,
    availability_by_key: dict[str, Any],
) -> None:
    if not material_key:
        return
    availability_row = availability_by_key.get(material_key)
    if availability_row is None:
        return
    status = availability_row.availability_status
    if status == "shortage":
        task_warnings.append(f"material_shortage_{material_key}")
    elif status in {"manual_check", "no_match", "ambiguous_match", "unknown"}:
        task_warnings.append(f"material_availability_{status}_{material_key}")


def _task_from_seed(
    seed: TaskSeedCandidate,
    group_key: str,
    *,
    geometry_summary: Any,
    material_rows: dict[str, Any],
    material_breakdown_available: bool,
    blocking_codes: set[str],
    availability_by_key: dict[str, Any] | None = None,
    procurement_by_key: dict[str, Any] | None = None,
) -> IntakeV3CandidateProductionTask:
    station, department = SEED_STATION_MAP.get(
        seed.seed_code,
        (seed.required_station, "production"),
    )
    task_id = _candidate_id(seed.seed_code)
    inputs = _geometry_inputs(geometry_summary, material_breakdown_available)
    task_warnings: list[str] = []
    task_blockers: list[str] = []

    availability_map = availability_by_key or {}
    procurement_map = procurement_by_key or {}

    if seed.seed_code == "face_and_backing_cnc_cut":
        inputs.append(
            _material_input(
                "Face material",
                material_rows.get("plexiglas_face"),
                availability_map.get("plexiglas_face"),
                procurement_map.get("plexiglas_face"),
            )
        )
        inputs.append(
            _material_input(
                "Backing material",
                material_rows.get("forex_backing"),
                availability_map.get("forex_backing"),
                procurement_map.get("forex_backing"),
            )
        )
        _append_material_availability_task_warnings(task_warnings, "plexiglas_face", availability_map)
        _append_material_availability_task_warnings(task_warnings, "forex_backing", availability_map)
        _append_procurement_task_warnings(task_warnings, "plexiglas_face", procurement_map)
        _append_procurement_task_warnings(task_warnings, "forex_backing", procurement_map)
    elif seed.seed_code in {"return_side_forming", "return_face_bonding"}:
        inputs.append(
            _material_input(
                "Return material",
                material_rows.get("aluminum_return"),
                availability_map.get("aluminum_return"),
                procurement_map.get("aluminum_return"),
            )
        )
        _append_material_availability_task_warnings(task_warnings, "aluminum_return", availability_map)
        _append_procurement_task_warnings(task_warnings, "aluminum_return", procurement_map)
    elif seed.seed_code == "led_installation_wiring_and_light_test":
        inputs.append(
            _material_input(
                "LED modules",
                material_rows.get("led_modules"),
                availability_map.get("led_modules"),
                procurement_map.get("led_modules"),
            )
        )
        inputs.append(
            _material_input(
                "LED PSU",
                material_rows.get("led_power_supply"),
                availability_map.get("led_power_supply"),
                procurement_map.get("led_power_supply"),
            )
        )
        _append_material_availability_task_warnings(task_warnings, "led_modules", availability_map)
        _append_material_availability_task_warnings(task_warnings, "led_power_supply", availability_map)
        _append_procurement_task_warnings(task_warnings, "led_modules", procurement_map)
        _append_procurement_task_warnings(task_warnings, "led_power_supply", procurement_map)
    elif seed.seed_code in {"return_vinyl_application_workbench", "face_vinyl_application_final"}:
        inputs.append(
            _material_input(
                "Face vinyl",
                material_rows.get("face_vinyl"),
                availability_map.get("face_vinyl"),
                procurement_map.get("face_vinyl"),
            )
        )
        _append_material_availability_task_warnings(task_warnings, "face_vinyl", availability_map)
        _append_procurement_task_warnings(task_warnings, "face_vinyl", procurement_map)

    if "missing_confirmed_production_model" in blocking_codes:
        task_blockers.append("missing_confirmed_production_model")
    if "geometry_partial" in blocking_codes:
        task_warnings.append("geometry_partial")
    for code in _classification_task_warnings(geometry_summary):
        if code not in task_warnings:
            task_warnings.append(code)
    if not material_breakdown_available:
        task_warnings.append("missing_material_breakdown")

    return IntakeV3CandidateProductionTask(
        candidate_task_id=task_id,
        group_key=group_key,
        title=seed.display_name,
        description=f"Preview task from IV3 handoff seed {seed.seed_code}.",
        operation_type=f"{seed.source_operation_code}_preview",
        station_hint=station,
        department_hint=department,
        is_required=seed.active,
        is_conditional=not seed.active,
        condition_reason=None if seed.active else seed.active_reason,
        source_data=[
            "confirmed_production_model_snapshot",
            "material_breakdown.geometry_summary",
            f"task_seed.{seed.seed_code}",
        ],
        inputs_preview=inputs,
        output_preview=[seed.operator_instruction or seed.display_name],
        blocking_issues=task_blockers,
        warnings=task_warnings,
        will_create_real_task=False,
        seed_code=seed.seed_code,
    )


def _split_task_from_definition(
    definition: dict[str, Any],
    group_key: str,
    seed: TaskSeedCandidate | None,
    *,
    geometry_summary: Any,
    material_rows: dict[str, Any],
    material_breakdown_available: bool,
    blocking_codes: set[str],
    availability_by_key: dict[str, Any] | None = None,
    procurement_by_key: dict[str, Any] | None = None,
) -> IntakeV3CandidateProductionTask | None:
    metric_key = definition.get("conditional_metric")
    if metric_key:
        metric_value = getattr(geometry_summary, metric_key, None)
        if not metric_value or float(metric_value) <= 0:
            return None

    active = seed.active if seed is not None else True
    conditional = metric_key is not None
    inputs = _geometry_inputs(geometry_summary, material_breakdown_available)
    availability_map = availability_by_key or {}
    procurement_map = procurement_by_key or {}
    if "face" in definition["candidate_task_id"]:
        inputs.append(
            _material_input(
                "Face material",
                material_rows.get("plexiglas_face"),
                availability_map.get("plexiglas_face"),
                procurement_map.get("plexiglas_face"),
            )
        )
    if "backing" in definition["candidate_task_id"]:
        inputs.append(
            _material_input(
                "Backing material",
                material_rows.get("forex_backing"),
                availability_map.get("forex_backing"),
                procurement_map.get("forex_backing"),
            )
        )
    if "bevel" in definition["candidate_task_id"]:
        inputs.append(
            IntakeV3CandidateTaskInput(
                label="Bevel perimeter",
                value=getattr(geometry_summary, "bevel_perimeter_ml", None),
                unit="ml",
                quality=geometry_summary.calculation_quality or "partial",
            )
        )

    task_warnings: list[str] = []
    if not material_breakdown_available:
        task_warnings.append("missing_material_breakdown")
    if "face" in definition["candidate_task_id"]:
        _append_material_availability_task_warnings(task_warnings, "plexiglas_face", availability_map)
        _append_procurement_task_warnings(task_warnings, "plexiglas_face", procurement_map)
    if "backing" in definition["candidate_task_id"]:
        _append_material_availability_task_warnings(task_warnings, "forex_backing", availability_map)
        _append_procurement_task_warnings(task_warnings, "forex_backing", procurement_map)
    if geometry_summary.calculation_quality == "partial":
        task_warnings.append("geometry_partial")
    for code in _classification_task_warnings(geometry_summary):
        if code not in task_warnings:
            task_warnings.append(code)

    return IntakeV3CandidateProductionTask(
        candidate_task_id=str(definition["candidate_task_id"]),
        group_key=group_key,
        title=str(definition["title"]),
        description="Preview task for cutting acrylic faces from confirmed IV3 production model."
        if "face-cutting" in definition["candidate_task_id"]
        else "Preview task from IV3 production task dry-run.",
        operation_type=str(definition["operation_type"]),
        station_hint=str(definition.get("station_hint")),
        department_hint=str(definition.get("department_hint")),
        is_required=active and not conditional,
        is_conditional=conditional or not active,
        condition_reason=None if active else (seed.active_reason if seed else "inactive"),
        source_data=[
            "confirmed_production_model_snapshot",
            "material_breakdown.geometry_summary",
            f"task_seed.{definition.get('source_seed')}",
        ],
        inputs_preview=inputs,
        output_preview=[str(definition["title"])],
        blocking_issues=list(blocking_codes & {"missing_confirmed_production_model"}),
        warnings=task_warnings,
        will_create_real_task=False,
        seed_code=str(definition.get("source_seed")) if definition.get("source_seed") else None,
        parallel_with=list(definition.get("parallel_with") or []),
    )


def build_candidate_tasks(
    context: Iv3SourceContext,
    seeds: list[TaskSeedCandidate],
    *,
    geometry_summary: Any,
    material_rows: list[Any],
    material_breakdown_available: bool,
    blocking_codes: set[str],
    availability_by_key: dict[str, Any] | None = None,
    procurement_by_key: dict[str, Any] | None = None,
) -> tuple[list[IntakeV3CandidateProductionTask], list[IntakeV3CandidateTaskGroup]]:
    if blocking_codes & {"missing_confirmed_production_model"}:
        return [], []

    seed_by_code = {seed.seed_code: seed for seed in seeds}
    row_by_key = {row.material_key: row for row in material_rows}
    candidate_tasks: list[IntakeV3CandidateProductionTask] = []
    groups: list[IntakeV3CandidateTaskGroup] = []
    seen_task_ids: set[str] = set()

    for group_def in TASK_GROUP_CATALOG:
        group_key = str(group_def["group_key"])
        group_task_ids: list[str] = []
        split_defs = group_def.get("split_tasks") or []

        if split_defs:
            for split in split_defs:
                source_seed = str(split.get("source_seed", ""))
                seed = seed_by_code.get(source_seed)
                if seed is None or not seed.active:
                    continue
                task = _split_task_from_definition(
                    split,
                    group_key,
                    seed,
                    geometry_summary=geometry_summary,
                    material_rows=row_by_key,
                    material_breakdown_available=material_breakdown_available,
                    blocking_codes=blocking_codes,
                    availability_by_key=availability_by_key,
                    procurement_by_key=procurement_by_key,
                )
                if task is None:
                    continue
                if task.candidate_task_id not in seen_task_ids:
                    candidate_tasks.append(task)
                    seen_task_ids.add(task.candidate_task_id)
                    group_task_ids.append(task.candidate_task_id)
        else:
            for seed_code in group_def.get("seed_codes") or []:
                seed = seed_by_code.get(str(seed_code))
                if seed is None:
                    continue
                task_id = _candidate_id(seed.seed_code)
                if task_id in seen_task_ids:
                    continue
                if seed.seed_code == "face_and_backing_cnc_cut":
                    continue
                task = _task_from_seed(
                    seed,
                    group_key,
                    geometry_summary=geometry_summary,
                    material_rows=row_by_key,
                    material_breakdown_available=material_breakdown_available,
                    blocking_codes=blocking_codes,
                    availability_by_key=availability_by_key,
                    procurement_by_key=procurement_by_key,
                )
                candidate_tasks.append(task)
                seen_task_ids.add(task_id)
                group_task_ids.append(task_id)

        if not group_task_ids:
            continue

        active_seeds = [
            seed_by_code[code]
            for code in group_def.get("seed_codes") or []
            if code in seed_by_code
        ]
        group_required = any(seed.active for seed in active_seeds) or bool(group_task_ids)
        group_conditional = not group_required

        groups.append(
            IntakeV3CandidateTaskGroup(
                group_key=group_key,
                title=str(group_def["title"]),
                description=group_def.get("description"),
                sort_order=int(group_def.get("sort_order") or 0),
                candidate_task_ids=group_task_ids,
                is_required=group_required,
                is_conditional=group_conditional,
                condition_reason=None if group_required else "no_active_tasks_in_group",
            )
        )

    return candidate_tasks, groups


def build_task_dependencies(
    candidate_tasks: list[IntakeV3CandidateProductionTask],
    seeds: list[TaskSeedCandidate],
) -> list[IntakeV3CandidateTaskDependency]:
    task_ids = {task.candidate_task_id for task in candidate_tasks}
    seed_to_task: dict[str, str] = {}
    for task in candidate_tasks:
        if task.seed_code:
            seed_to_task.setdefault(task.seed_code, task.candidate_task_id)
    seed_to_task["face_and_backing_cnc_cut"] = "dryrun-cnc-face-cutting"

    dependencies: list[IntakeV3CandidateTaskDependency] = []
    seen: set[tuple[str, str]] = set()

    for seed in seeds:
        if not seed.active:
            continue
        to_id = seed_to_task.get(seed.seed_code)
        if to_id is None or to_id not in task_ids:
            continue
        for dep_seed in seed.depends_on:
            from_id = seed_to_task.get(dep_seed)
            if from_id is None or from_id not in task_ids:
                continue
            key = (from_id, to_id)
            if key in seen:
                continue
            seen.add(key)
            dependencies.append(
                IntakeV3CandidateTaskDependency(
                    from_candidate_task_id=from_id,
                    to_candidate_task_id=to_id,
                    dependency_type="blocks",
                    reason=f"{dep_seed} must complete before {seed.seed_code}.",
                )
            )

    extra_edges = [
        ("dryrun-cnc-file-preparation", "dryrun-cnc-face-cutting", "CNC cutting needs validated production files."),
        ("dryrun-letter-assembly-no-shared-support", "dryrun-stretch-wrap-and-delivery-mounting-package", "Packaging depends on assembly completion."),
    ]
    for from_id, to_id, reason in extra_edges:
        if from_id in task_ids and to_id in task_ids:
            key = (from_id, to_id)
            if key in seen:
                continue
            seen.add(key)
            dependencies.append(
                IntakeV3CandidateTaskDependency(
                    from_candidate_task_id=from_id,
                    to_candidate_task_id=to_id,
                    dependency_type="blocks",
                    reason=reason,
                )
            )

    return dependencies


def _boundary_flags() -> IntakeV3TaskDryRunBoundary:
    return IntakeV3TaskDryRunBoundary(
        dry_run_scope=DRY_RUN_SCOPE,
        would_create_execution_plan=False,
        would_create_execution_tasks=False,
        creates_execution_plan=False,
        creates_execution_tasks=False,
        creates_work_sessions=False,
        mutates_inventory=False,
        starts_production=False,
        modifies_order=False,
        modifies_quote=False,
        costengine_used=False,
    )


def _non_iv3_response(context: Iv3SourceContext) -> IntakeV3ProductionTaskDryRunResponse:
    boundary = _boundary_flags()
    warnings = [
        _blocker(
            "not_intake_v3_source",
            "Source is not an Intake V3 order/quote/workspace payload.",
            source="source_detection",
            severity="warning",
        )
    ]
    return IntakeV3ProductionTaskDryRunResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=context.source_type,
        source_id=context.source_id,
        order_id=context.order.id if context.order else None,
        quote_id=context.quote.id if context.quote else None,
        is_intake_v3=False,
        dry_run_scope=DRY_RUN_SCOPE,
        can_generate_real_tasks_now=False,
        boundary=boundary,
        warnings=warnings,
        future_builds=FUTURE_BUILDS,
        would_create_execution_plan=boundary.would_create_execution_plan,
        would_create_execution_tasks=boundary.would_create_execution_tasks,
        creates_execution_plan=boundary.creates_execution_plan,
        creates_execution_tasks=boundary.creates_execution_tasks,
        creates_work_sessions=boundary.creates_work_sessions,
        mutates_inventory=boundary.mutates_inventory,
        starts_production=boundary.starts_production,
        modifies_order=boundary.modifies_order,
        modifies_quote=boundary.modifies_quote,
        costengine_used=boundary.costengine_used,
    )


async def _resolve_production_readiness_status(
    db: AsyncSession,
    context: Iv3SourceContext,
) -> str | None:
    if context.order is not None:
        readiness = await get_iv3_order_production_readiness(db, context.order.id)
        return readiness.production_readiness_status
    if context.quote is not None:
        readiness = await get_iv3_order_production_readiness_by_quote(db, context.quote.id)
        return readiness.production_readiness_status
    return "workspace_preview"


async def build_task_dry_run_response(
    db: AsyncSession,
    context: Iv3SourceContext,
) -> IntakeV3ProductionTaskDryRunResponse:
    if not context.is_intake_v3:
        return _non_iv3_response(context)

    boundary = _boundary_flags()
    workspace_id = None
    if context.quote_linkage:
        workspace_id = context.quote_linkage.get("source_workspace_id")
    if context.order_linkage and not workspace_id:
        workspace_id = context.order_linkage.get("source_workspace_id")
    if context.source_type == "workspace":
        workspace_id = context.source_id

    confirmed = extract_confirmed_production_model(context)
    has_confirmed_model = confirmed is not None
    finish = extract_finish_assignments(context)
    sections = context.sections
    finish_snapshot = sections.get("finish_assignment_snapshot")
    has_finish = _has_finish_assignment_data(finish_snapshot, context.workspace) or finish is not None

    geometry_summary, _geometry_warnings = extract_geometry_summary(context)
    material_breakdown_available = has_confirmed_model and context.is_intake_v3

    from services.intake_v3_material_quantity_breakdown_service import resolve_material_quantity_rows

    material_rows: list[Any] = []
    if has_confirmed_model:
        material_rows, _ = resolve_material_quantity_rows(context, geometry_summary, finish)

    from services.intake_v3_material_availability_service import (
        availability_by_material_key,
        build_material_availability_response,
        downstream_summary_fields,
    )

    material_availability = await build_material_availability_response(db, context)
    availability_map = availability_by_material_key(material_availability)
    availability_fields = downstream_summary_fields(material_availability)

    from services.intake_v3_procurement_preview_service import (
        build_procurement_preview_response,
        downstream_summary_fields as procurement_summary_fields,
        procurement_by_material_key,
    )

    procurement_preview = await build_procurement_preview_response(
        db,
        order_id=context.order.id if context.order else None,
        quote_id=context.quote.id if context.quote else None,
        workspace_id=str(workspace_id) if workspace_id else None,
    )
    procurement_map = procurement_by_material_key(procurement_preview)
    procurement_fields = procurement_summary_fields(procurement_preview)

    production_readiness_status = await _resolve_production_readiness_status(db, context)

    blockers, warnings = build_task_generation_blockers(
        context,
        production_readiness_status=production_readiness_status,
        has_confirmed_model=has_confirmed_model,
        has_finish_assignments=has_finish,
        material_breakdown_available=material_breakdown_available,
        geometry_quality=geometry_summary.calculation_quality or "missing",
    )

    blocking_codes = {item.code for item in blockers if item.severity == "blocking"}

    seeds: list[TaskSeedCandidate] = []
    if context.workspace is not None and has_confirmed_model:
        flags = _resolve_operation_flags(context)
        seeds = build_task_seed_candidates(context.workspace, flags)

    candidate_tasks, candidate_groups = build_candidate_tasks(
        context,
        seeds,
        geometry_summary=geometry_summary,
        material_rows=material_rows,
        material_breakdown_available=material_breakdown_available,
        blocking_codes=blocking_codes,
        availability_by_key=availability_map,
        procurement_by_key=procurement_map,
    )
    dependencies = build_task_dependencies(candidate_tasks, seeds)

    order_id = context.order.id if context.order else None
    quote_id = context.quote.id if context.quote else None
    if order_id is None and quote_id is not None:
        linked_order = await check_existing_order_for_iv3_quote(db, quote_id)
        if linked_order is not None:
            order_id = linked_order.id

    from services.intake_v3_geometry_metrics_snapshot_service import (
        parse_snapshot_from_sections,
        parse_snapshot_from_workspace,
    )

    geometry_snapshot = parse_snapshot_from_sections(context.sections)
    if geometry_snapshot is None:
        geometry_snapshot = parse_snapshot_from_workspace(context.workspace)
    geometry_snapshot_available = geometry_snapshot is not None
    geometry_status = (
        geometry_snapshot.geometry_status
        if geometry_snapshot is not None
        else "geometry_missing"
    )

    from services.intake_v3_layer_role_confirmation_propagation_service import (
        downstream_propagation_fields,
    )
    from schemas.intake_v3 import IntakeV3TaskGenerationBlocker

    propagation_fields, _, stale_warning_pairs = downstream_propagation_fields(context)
    for code, message in stale_warning_pairs:
        warnings.append(
            IntakeV3TaskGenerationBlocker(
                code=code,
                severity="warning",
                message=message,
                source="layer_role_confirmation_propagation",
            )
        )
    if availability_fields.get("material_shortage_rows_count", 0) > 0:
        warnings.append(
            IntakeV3TaskGenerationBlocker(
                code="material_shortage_detected",
                severity="warning",
                message="One or more candidate tasks reference materials with estimated stock shortage.",
                source="material_availability",
            )
        )
    if availability_fields.get("material_manual_check_rows_count", 0) > 0:
        warnings.append(
            IntakeV3TaskGenerationBlocker(
                code="material_manual_check_required",
                severity="warning",
                message="Manual stock verification required for one or more task materials.",
                source="material_availability",
            )
        )
    if procurement_fields.get("procurement_owner_decision_required_count", 0) > 0:
        warnings.append(
            IntakeV3TaskGenerationBlocker(
                code="procurement_owner_decision_required",
                severity="warning",
                message="Owner procurement decision required for one or more task materials.",
                source="procurement_preview",
            )
        )
    if procurement_fields.get("procurement_purchase_recommended_count", 0) > 0:
        warnings.append(
            IntakeV3TaskGenerationBlocker(
                code="procurement_purchase_recommended",
                severity="warning",
                message="Purchase recommended for one or more task materials (preview only).",
                source="procurement_preview",
            )
        )
    if procurement_fields.get("procurement_manual_check_count", 0) > 0:
        warnings.append(
            IntakeV3TaskGenerationBlocker(
                code="procurement_manual_check_required",
                severity="warning",
                message="Procurement manual check required for one or more task materials.",
                source="procurement_preview",
            )
        )

    return IntakeV3ProductionTaskDryRunResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=context.source_type,
        source_id=context.source_id,
        order_id=order_id,
        quote_id=quote_id,
        source_workspace_id=str(workspace_id) if workspace_id else None,
        is_intake_v3=True,
        dry_run_scope=DRY_RUN_SCOPE,
        production_readiness_status=production_readiness_status,
        material_breakdown_available=material_breakdown_available,
        material_availability_available=availability_fields.get("material_availability_available", False),
        material_availability_status=availability_fields.get("material_availability_status"),
        material_shortage_rows_count=int(availability_fields.get("material_shortage_rows_count") or 0),
        material_manual_check_rows_count=int(availability_fields.get("material_manual_check_rows_count") or 0),
        material_indirect_consumables_count=int(availability_fields.get("material_indirect_consumables_count") or 0),
        procurement_preview_available=procurement_fields.get("procurement_preview_available", False),
        procurement_preview_status=procurement_fields.get("procurement_preview_status"),
        procurement_purchase_recommended_count=int(
            procurement_fields.get("procurement_purchase_recommended_count") or 0
        ),
        procurement_owner_decision_required_count=int(
            procurement_fields.get("procurement_owner_decision_required_count") or 0
        ),
        procurement_advance_recommended_count=int(
            procurement_fields.get("procurement_advance_recommended_count") or 0
        ),
        procurement_manual_check_count=int(procurement_fields.get("procurement_manual_check_count") or 0),
        geometry_snapshot_available=geometry_snapshot_available,
        geometry_status=geometry_status,
        can_generate_real_tasks_now=False,
        boundary=boundary,
        summary=IntakeV3ProductionTaskDryRunSummary(
            candidate_groups_count=len(candidate_groups),
            candidate_tasks_count=len(candidate_tasks),
            blocking_issues_count=len(blockers),
            warnings_count=len(warnings),
        ),
        candidate_task_groups=sorted(candidate_groups, key=lambda group: group.sort_order),
        candidate_tasks=candidate_tasks,
        dependencies=dependencies,
        blockers=blockers,
        warnings=warnings,
        future_builds=FUTURE_BUILDS,
        would_create_execution_plan=boundary.would_create_execution_plan,
        would_create_execution_tasks=boundary.would_create_execution_tasks,
        creates_execution_plan=boundary.creates_execution_plan,
        creates_execution_tasks=boundary.creates_execution_tasks,
        creates_work_sessions=boundary.creates_work_sessions,
        mutates_inventory=boundary.mutates_inventory,
        starts_production=boundary.starts_production,
        modifies_order=boundary.modifies_order,
        modifies_quote=boundary.modifies_quote,
        costengine_used=boundary.costengine_used,
        **propagation_fields,
    )


async def get_iv3_production_task_dry_run_for_order(
    db: AsyncSession,
    order_id: int,
) -> IntakeV3ProductionTaskDryRunResponse:
    context = await load_iv3_source_context(db, order_id=order_id)
    return await build_task_dry_run_response(db, context)


async def get_iv3_production_task_dry_run_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3ProductionTaskDryRunResponse:
    context = await load_iv3_source_context(db, quote_id=quote_id)
    return await build_task_dry_run_response(db, context)


async def get_iv3_production_task_dry_run_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3ProductionTaskDryRunResponse:
    context = await load_iv3_source_context(db, workspace_id=workspace_id)
    return await build_task_dry_run_response(db, context)
