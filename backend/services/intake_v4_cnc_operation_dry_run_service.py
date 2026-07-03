"""Intake V4 CNC operation rows → task dry-run candidates (read-only preview)."""

from __future__ import annotations

from typing import Any

from schemas.intake_v4 import (
    IntakeV4CncOperationDryRunCandidate,
    IntakeV4CncOperationRow,
    IntakeV4TaskGenerationEstimatedInputs,
    IntakeV4TaskGenerationTaskCandidate,
)
from services.tpl_volumetric_operation_keys_service import enrich_task_candidate_alignment

CNC_TASK_DRY_RUN_SOURCE = "operation_rows"
CNC_TASK_DRY_RUN_SOURCE_COMPAT_FALLBACK = "legacy_parallel_mapping"
# Backward-compatible alias kept for existing imports.
CNC_TASK_DRY_RUN_SOURCE_LEGACY = CNC_TASK_DRY_RUN_SOURCE_COMPAT_FALLBACK

_CNC_COMPAT_BRIDGE_JOB_KEYS = frozenset({"face_plexiglas_cutting", "forex_backing_cutting"})


def _idempotency_key(workspace_id: str, template_code: str, task_key: str) -> str:
    return f"intake-v4:{workspace_id}:{template_code}:{task_key}"


def _pricing_status_label(pricing_status: str | None) -> str:
    if pricing_status == "missing_rate":
        return "Preț neconfigurat / necesită tarif operație CNC"
    return pricing_status or "missing_rate"


def cnc_operation_row_to_dry_run_candidate(row: IntakeV4CncOperationRow) -> IntakeV4CncOperationDryRunCandidate:
    warnings = list(row.warnings or [])
    if row.pricing_status == "missing_rate":
        warnings.append("cnc_operation_rate_missing")
    if row.resource_mapping_status == "pending_mapping" and row.mapping_gaps:
        warnings.append("operation_catalog_key_pending")
    warnings.append("dry_run_preview_no_real_task")
    warnings.append("stock_not_consumed")

    return IntakeV4CncOperationDryRunCandidate(
        candidate_key=row.key,
        title=row.display_name,
        operation_key=row.key,
        operation_type=row.operation_type,
        material_key=row.material_key,
        material_label=row.material_name,
        quantity=row.quantity,
        unit=row.unit,
        operation_equivalent_quantity=row.operation_equivalent_quantity,
        passes=row.passes,
        owner_pass_override=row.owner_pass_override,
        basis_label=row.basis_label or row.basis_key,
        pricing_status=row.pricing_status,
        estimated_cost=row.estimated_cost,
        required_machine_key=row.required_machine_key,
        machine_type=row.machine_type,
        workstation_key=row.workstation_key,
        required_skill_key=row.required_skill_key,
        registry_skill_code=row.registry_skill_code,
        operation_catalog_key=row.operation_catalog_key,
        dossier_operation_key=row.dossier_operation_key,
        tpl_operation_key=row.tpl_operation_key,
        production_task_type=row.production_task_type,
        resource_mapping_status=row.resource_mapping_status,
        mapping_gaps=list(row.mapping_gaps or []),
        consumes_stock_now=row.consumes_stock_now,
        creates_task_now=row.creates_task_now,
        source=CNC_TASK_DRY_RUN_SOURCE,
        warnings=warnings,
    )


def cnc_operation_row_to_task_candidate(
    row: IntakeV4CncOperationRow,
    *,
    workspace_id: str,
    template_code: str,
    source_fingerprint: str,
) -> IntakeV4TaskGenerationTaskCandidate:
    operation_key = row.dossier_operation_key or row.tpl_operation_key or row.key
    task_key = row.tpl_operation_key or row.key
    alignment_fields = enrich_task_candidate_alignment(
        task_key=task_key,
        operation_key=operation_key,
        catalog_code=row.operation_catalog_key,
        provisional=row.resource_mapping_status == "pending_mapping",
    )
    provisional = alignment_fields.pop("provisional", False)
    template_backed = alignment_fields.pop("template_backed", False)
    provisional_reason = alignment_fields.pop("provisional_reason", None)
    aligned_future = alignment_fields.pop("future_execution_task_type", None)
    future_execution_task_type = row.production_task_type or aligned_future

    warnings: list[str] = list(row.warnings or [])
    warnings.append(f"cnc_preview_source:{CNC_TASK_DRY_RUN_SOURCE}")
    if row.pricing_status == "missing_rate":
        warnings.append("cnc_operation_rate_missing")
    if row.resource_mapping_status == "pending_mapping":
        warnings.append("operation_catalog_key_pending")
        for gap in row.mapping_gaps or []:
            warnings.append(f"mapping_gap:{gap}")
    warnings.append("no_real_task_created")
    warnings.append("consumes_stock_now_false")

    estimated = IntakeV4TaskGenerationEstimatedInputs(
        material_codes=[row.material_key] if row.material_key else [],
        quantity_basis=row.basis_key or None,
        quantity=row.quantity,
        unit=row.unit,
        passes=row.passes,
        operation_equivalent_quantity=row.operation_equivalent_quantity,
        owner_pass_override=row.owner_pass_override,
        basis_label=row.basis_label or None,
        pricing_status=row.pricing_status,
        preview_source=CNC_TASK_DRY_RUN_SOURCE,
        required_machine_key=row.required_machine_key,
        machine_type=row.machine_type,
        workstation_key=row.workstation_key,
        required_skill_key=row.required_skill_key,
        registry_skill_code=row.registry_skill_code,
        operation_catalog_key=row.operation_catalog_key,
        mapping_gaps=list(row.mapping_gaps or []),
        consumes_stock_now=row.consumes_stock_now,
        creates_task_now=row.creates_task_now,
    )

    return IntakeV4TaskGenerationTaskCandidate(
        task_key=task_key,
        title=row.display_name,
        template_code=template_code,
        template_backed=template_backed,
        provisional=provisional,
        provisional_reason=provisional_reason,
        operation_key=operation_key,
        operation_group="cnc_cutting",
        station_hint=row.workstation_key,
        role_hint=row.required_skill_key,
        source_material_jobs=[],
        source_operation_groups=["cnc_cutting"],
        estimated_inputs=estimated,
        creates_execution_task=False,
        idempotency_key=_idempotency_key(workspace_id, template_code, task_key),
        warnings=warnings,
        future_execution_task_type=future_execution_task_type,
        **alignment_fields,
    )


def build_cnc_dry_run_from_operation_rows(
    operation_rows: list[IntakeV4CncOperationRow],
    *,
    workspace_id: str,
    template_code: str,
    source_fingerprint: str,
) -> tuple[list[IntakeV4TaskGenerationTaskCandidate], list[IntakeV4CncOperationDryRunCandidate]]:
    task_candidates = [
        cnc_operation_row_to_task_candidate(
            row,
            workspace_id=workspace_id,
            template_code=template_code,
            source_fingerprint=source_fingerprint,
        )
        for row in operation_rows
    ]
    dry_run_candidates = [cnc_operation_row_to_dry_run_candidate(row) for row in operation_rows]
    return task_candidates, dry_run_candidates


def should_skip_compat_bridge_cnc_material_job(
    job_key: str,
    operation_rows: list[IntakeV4CncOperationRow],
) -> bool:
    return bool(operation_rows) and job_key in _CNC_COMPAT_BRIDGE_JOB_KEYS


# Backward-compatible alias for older callers.
def should_skip_legacy_cnc_material_job(job_key: str, operation_rows: list[IntakeV4CncOperationRow]) -> bool:
    return should_skip_compat_bridge_cnc_material_job(job_key, operation_rows)


def build_iv3_cnc_candidate_tasks_from_operation_rows(
    operation_rows: list[IntakeV4CncOperationRow],
) -> tuple[list[Any], list[Any]]:
    """Build V3 compatibility dry-run CNC preview tasks from material breakdown rows."""
    from schemas.intake_v3 import IntakeV3CandidateProductionTask, IntakeV3CandidateTaskGroup, IntakeV3CandidateTaskInput

    tasks: list[IntakeV3CandidateProductionTask] = []
    task_ids: list[str] = []
    for row in operation_rows:
        candidate_id = f"cnc_op:{row.key}"
        task_ids.append(candidate_id)
        inputs: list[IntakeV3CandidateTaskInput] = [
            IntakeV3CandidateTaskInput(
                label="Cantitate",
                value=round(row.quantity, 4),
                unit=row.unit,
                quality="calculated",
            ),
        ]
        if row.passes and row.passes > 1:
            inputs.append(
                IntakeV3CandidateTaskInput(
                    label="Treceri",
                    value=row.passes,
                    unit="pass",
                    quality="calculated",
                )
            )
        if row.operation_equivalent_quantity is not None:
            inputs.append(
                IntakeV3CandidateTaskInput(
                    label="Echivalent utilaj",
                    value=round(row.operation_equivalent_quantity, 4),
                    unit=row.operation_equivalent_unit or "ml-pass",
                    quality="calculated",
                )
            )
        if row.workstation_key:
            inputs.append(
                IntakeV3CandidateTaskInput(
                    label="Stație",
                    value=row.workstation_key,
                    quality="catalog",
                )
            )
        if row.required_machine_key:
            inputs.append(
                IntakeV3CandidateTaskInput(
                    label="Utilaj",
                    value=row.required_machine_key,
                    quality="catalog",
                )
            )
        if row.required_skill_key:
            inputs.append(
                IntakeV3CandidateTaskInput(
                    label="Skill",
                    value=row.required_skill_key,
                    quality="catalog",
                )
            )
        inputs.append(
            IntakeV3CandidateTaskInput(
                label="Sursă preview",
                value=CNC_TASK_DRY_RUN_SOURCE,
                quality="catalog",
            )
        )
        if row.basis_label:
            inputs.append(
                IntakeV3CandidateTaskInput(
                    label="Bază",
                    value=row.basis_label,
                    quality="calculated",
                )
            )

        warnings: list[str] = [f"cnc_preview_source:{CNC_TASK_DRY_RUN_SOURCE}", "no_real_task_created"]
        if row.pricing_status == "missing_rate":
            warnings.append(_pricing_status_label(row.pricing_status))
        for gap in row.mapping_gaps or []:
            warnings.append(f"mapping_gap:{gap}")

        tasks.append(
            IntakeV3CandidateProductionTask(
                candidate_task_id=candidate_id,
                group_key="cnc_operation_rows",
                title=row.display_name,
                description=row.basis_label,
                operation_type=row.operation_type,
                station_hint=row.workstation_key,
                department_hint=row.required_skill_key,
                source_data=[CNC_TASK_DRY_RUN_SOURCE],
                inputs_preview=inputs,
                warnings=warnings,
                will_create_real_task=False,
                seed_code=row.tpl_operation_key,
            )
        )

    group = IntakeV3CandidateTaskGroup(
        group_key="cnc_operation_rows",
        title="Operații CNC (operation_rows)",
        description="Preview din Material Breakdown — nu catalog V3 face_cnc_cut agregat.",
        sort_order=5,
        candidate_task_ids=task_ids,
    )
    return tasks, [group]
