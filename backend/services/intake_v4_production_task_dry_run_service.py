"""Intake V4 production task dry-run — reuses V3 dry-run builders (Sprint 2)."""

from __future__ import annotations

from schemas.intake_v3 import (
    IntakeV3ProductionTaskDryRunResponse,
    IntakeV3ProductionTaskDryRunSummary,
    IntakeV3TaskGenerationBlocker,
)
from schemas.intake_v4 import IntakeV4WorkspacePayload
from services.intake_v3_material_quantity_breakdown_service import (
    Iv3SourceContext,
    extract_geometry_summary,
)
from services.intake_v3_production_handoff_adapter import build_task_seed_candidates
from services.intake_v3_production_task_dry_run_service import (
    DRY_RUN_SCOPE,
    FUTURE_BUILDS,
    _boundary_flags,
    _blocker,
    build_candidate_tasks,
    build_task_dependencies,
    build_task_generation_blockers,
)
from services.intake_v4_finish_adapter import (
    build_v3_workspace_from_v4_payload,
    derive_operation_flags_from_v4_finish,
    finish_assignment_from_v4_setup,
)
from services.intake_v4_operator_task_labels import operator_task_label_for_seed
from services.intake_v4_production_preview_service import _apply_v4_lighting_gates
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown
from services.intake_v4_cnc_operation_dry_run_service import (
    CNC_TASK_DRY_RUN_SOURCE,
    build_iv3_cnc_candidate_tasks_from_operation_rows,
)


def _artwork_warnings(payload: IntakeV4WorkspacePayload) -> list[IntakeV3TaskGenerationBlocker]:
    warnings: list[IntakeV3TaskGenerationBlocker] = []
    setup = payload.finish_setup
    if not setup or not setup.artwork_finishes:
        return warnings
    for row in setup.artwork_finishes:
        if (row.execution_type or "needs_decision") == "needs_decision":
            warnings.append(
                _blocker(
                    "artwork_execution_undecided",
                    f"Artwork „{row.layer_name or row.layer_key}” — alege metoda execuție.",
                    source="finish_setup.artwork_finishes",
                    severity="warning",
                )
            )
    return warnings


def build_v4_production_task_dry_run(
    *,
    workspace_id: str,
    payload: IntakeV4WorkspacePayload,
) -> IntakeV3ProductionTaskDryRunResponse:
    v3_workspace = build_v3_workspace_from_v4_payload(payload)
    finish = finish_assignment_from_v4_setup(payload.finish_setup)
    illuminated = payload.finish_setup.illuminated is not False if payload.finish_setup else True

    sections: dict[str, object] = {}
    if v3_workspace.confirmed_production_model is not None:
        sections["confirmed_production_model_snapshot"] = (
            v3_workspace.confirmed_production_model.model_dump(mode="json")
        )
    if v3_workspace.finish_assignment is not None:
        sections["finish_assignment_snapshot"] = v3_workspace.finish_assignment.model_dump(mode="json")
    if v3_workspace.path_geometry_summary:
        sections["geometry_metrics_snapshot"] = dict(v3_workspace.path_geometry_summary)

    context = Iv3SourceContext(
        source_type="workspace",
        source_id=workspace_id,
        is_intake_v3=True,
        order=None,
        quote=None,
        quote_linkage={"source_workspace_id": workspace_id},
        order_linkage=None,
        sections=sections,
        linkage_sections={},
        workspace=v3_workspace,
        product_template=payload.product_binding.template_code,
    )

    has_confirmed = (
        v3_workspace.confirmed_production_model is not None
        and (v3_workspace.confirmed_production_model.letter_count or 0) > 0
    )
    has_finish = finish is not None

    geometry_summary, _geo_warnings = extract_geometry_summary(context)
    geometry_quality = geometry_summary.calculation_quality or "missing"

    blockers, warnings = build_task_generation_blockers(
        context,
        production_readiness_status="workspace_preview",
        has_confirmed_model=has_confirmed,
        has_finish_assignments=has_finish,
        material_breakdown_available=has_confirmed and has_finish,
        geometry_quality=geometry_quality,
    )
    warnings.extend(_artwork_warnings(payload))

    flags = derive_operation_flags_from_v4_finish(
        finish,
        illuminated=illuminated,
        shared_support=False,
    )
    seeds = build_task_seed_candidates(v3_workspace, flags)
    _apply_v4_lighting_gates(seeds, illuminated)

    blocking_codes = {item.code for item in blockers if item.severity == "blocking"}
    candidate_tasks, candidate_groups = build_candidate_tasks(
        context,
        seeds,
        geometry_summary=geometry_summary,
        material_rows=[],
        material_breakdown_available=False,
        blocking_codes=blocking_codes,
        availability_by_key={},
        procurement_by_key={},
    )
    candidate_tasks = [
        task.model_copy(
            update={
                "title": operator_task_label_for_seed(task.seed_code or "", task.title),
            }
        )
        for task in candidate_tasks
    ]
    dependencies = build_task_dependencies(candidate_tasks, seeds)

    breakdown = build_intake_v4_material_breakdown(workspace_id, payload.model_dump(mode="json"))
    operation_rows = list(breakdown.operation_rows or [])
    if operation_rows:
        cnc_tasks, cnc_groups = build_iv3_cnc_candidate_tasks_from_operation_rows(operation_rows)
        candidate_tasks = [
            t for t in candidate_tasks
            if t.group_key != "cnc_operation_rows" and t.seed_code != "face_and_backing_cnc_cut"
        ]
        candidate_tasks.extend(cnc_tasks)
        candidate_groups = [g for g in candidate_groups if g.group_key != "cnc_operation_rows"]
        candidate_groups.extend(cnc_groups)
        warnings.append(
            _blocker(
                "cnc_preview_from_operation_rows",
                "CNC production preview uses material breakdown operation_rows.",
                source="cnc_task_dry_run",
                severity="info",
            )
        )

    boundary = _boundary_flags()
    blocking_issues = sum(len(t.blocking_issues) for t in candidate_tasks)

    return IntakeV3ProductionTaskDryRunResponse(
        source_module="intake_v4",
        source_type="intake_v4_workspace",
        source_id=workspace_id,
        source_workspace_id=workspace_id,
        is_intake_v3=True,
        dry_run_scope=DRY_RUN_SCOPE,
        production_readiness_status="workspace_preview",
        material_breakdown_available=has_confirmed and has_finish,
        geometry_snapshot_available=geometry_quality not in {"missing", ""},
        geometry_status=(
            "geometry_ready" if geometry_quality == "calculated" else geometry_quality
        ),
        can_generate_real_tasks_now=False,
        boundary=boundary,
        summary=IntakeV3ProductionTaskDryRunSummary(
            candidate_groups_count=len(candidate_groups),
            candidate_tasks_count=len(candidate_tasks),
            blocking_issues_count=blocking_issues,
            warnings_count=len(warnings),
        ),
        candidate_task_groups=candidate_groups,
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
    )
