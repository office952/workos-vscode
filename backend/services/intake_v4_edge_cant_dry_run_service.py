"""Intake V4 edge/cant operation rows → task dry-run candidates (read-only preview)."""

from __future__ import annotations

from schemas.intake_v4 import (
    IntakeV4EdgeCantOperationDryRunCandidate,
    IntakeV4EdgeCantOperationRow,
    IntakeV4TaskGenerationEstimatedInputs,
    IntakeV4TaskGenerationTaskCandidate,
)
from services.shared_edge_cant_rules import EDGE_CANT_TASK_DRY_RUN_SOURCE
from services.tpl_volumetric_operation_keys_service import enrich_task_candidate_alignment


def _idempotency_key(workspace_id: str, template_code: str, task_key: str) -> str:
    return f"intake-v4:{workspace_id}:{template_code}:{task_key}"


def edge_cant_operation_row_to_dry_run_candidate(
    row: IntakeV4EdgeCantOperationRow,
) -> IntakeV4EdgeCantOperationDryRunCandidate:
    warnings = list(row.warnings or [])
    if row.pricing_status == "missing_rate":
        warnings.append("edge_cant_operation_rate_missing")
    if row.resource_mapping_status == "pending_mapping" and row.mapping_gaps:
        warnings.append("operation_catalog_key_pending")
    warnings.append("dry_run_preview_no_real_task")
    warnings.append("stock_not_consumed")

    return IntakeV4EdgeCantOperationDryRunCandidate(
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
        source=row.source or EDGE_CANT_TASK_DRY_RUN_SOURCE,
        warnings=warnings,
    )


def edge_cant_operation_row_to_task_candidate(
    row: IntakeV4EdgeCantOperationRow,
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
    warnings.append(f"edge_cant_preview_source:{EDGE_CANT_TASK_DRY_RUN_SOURCE}")
    if row.pricing_status == "missing_rate":
        warnings.append("edge_cant_operation_rate_missing")
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
        preview_source=EDGE_CANT_TASK_DRY_RUN_SOURCE,
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
        operation_group="edge_cant_operations",
        station_hint=row.workstation_key,
        role_hint=row.required_skill_key,
        source_material_jobs=[row.material_key] if row.material_key else [],
        source_operation_groups=["edge_cant_operations"],
        estimated_inputs=estimated,
        creates_execution_task=False,
        idempotency_key=_idempotency_key(workspace_id, template_code, task_key),
        warnings=warnings,
        future_execution_task_type=future_execution_task_type,
        **alignment_fields,
    )


def build_edge_cant_dry_run_from_operation_rows(
    operation_rows: list[IntakeV4EdgeCantOperationRow],
    *,
    workspace_id: str,
    template_code: str,
    source_fingerprint: str,
) -> tuple[list[IntakeV4TaskGenerationTaskCandidate], list[IntakeV4EdgeCantOperationDryRunCandidate]]:
    task_candidates: list[IntakeV4TaskGenerationTaskCandidate] = []
    dry_run_candidates: list[IntakeV4EdgeCantOperationDryRunCandidate] = []

    for row in operation_rows:
        dry_run_candidates.append(edge_cant_operation_row_to_dry_run_candidate(row))
        task_candidates.append(
            edge_cant_operation_row_to_task_candidate(
                row,
                workspace_id=workspace_id,
                template_code=template_code,
                source_fingerprint=source_fingerprint,
            )
        )

    return task_candidates, dry_run_candidates
