"""Intake V4 task generation dry-run contract — read-only, no ExecutionTask / stock."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.intake_v4 import (
    PILOT_V4_TEMPLATE_CODE,
    TEMPLATE_OPTION_CONTRACT_VERSION,
    IntakeV4CncOperationRow,
    IntakeV4EdgeCantOperationRow,
    IntakeV4ProductionHandoffPreviewResponse,
    IntakeV4TaskGenerationAuditPreview,
    IntakeV4TaskGenerationDependencyEdge,
    IntakeV4TaskGenerationDryRunIssue,
    IntakeV4TaskGenerationDryRunResponse,
    IntakeV4TaskGenerationEstimatedInputs,
    IntakeV4TaskGenerationIdempotencyEntry,
    IntakeV4TaskGenerationTaskCandidate,
    IntakeV4WorkspacePayload,
)
from services.intake_v4_production_handoff_preview_service import (
    build_intake_v4_production_handoff_preview,
)
from services.intake_v4_cnc_operation_dry_run_service import (
    CNC_TASK_DRY_RUN_SOURCE,
    CNC_TASK_DRY_RUN_SOURCE_COMPAT_FALLBACK,
    build_cnc_dry_run_from_operation_rows,
    cnc_operation_row_to_task_candidate,
    should_skip_compat_bridge_cnc_material_job,
)
from services.intake_v4_edge_cant_dry_run_service import (
    build_edge_cant_dry_run_from_operation_rows,
    edge_cant_operation_row_to_task_candidate,
)
from services.shared_edge_cant_rules import EDGE_CANT_TASK_DRY_RUN_SOURCE
from services.intake_v4_material_breakdown_service import (
    build_intake_v4_material_breakdown_with_registry,
)
from services.intake_v4_template_option_contract_service import (
    evaluate_v4_template_option_contract,
)
from services.tpl_volumetric_operation_keys_service import (
    DOSSIER_OPERATION_KEYS,
    enrich_task_candidate_alignment,
    summarize_template_operation_alignment,
)

# Re-export canonical CNC dry-run source marker (operation_rows when available).

CATALOG_TO_DOSSIER_OPERATION: dict[str, str] = {
    "graphic_vector_preflight": "vector_prep",
    "confirmed_production_model": "vector_prep",
    "cnc_file_preparation": "vector_prep",
    "face_and_backing_cnc_cut": "face_cnc_cut",
    "return_forming_file_preparation": "side_forming",
    "return_vinyl_application_workbench": "vinyl_application",
    "return_side_forming": "side_forming",
    "return_face_bonding": "return_face_bonding",
    "led_installation_wiring_and_light_test": "led_install_letters",
    "letter_assembly_no_shared_support": "packaging_letters",
    "return_painting_after_assembly": "painting",
    "face_vinyl_application_final": "vinyl_application",
    "stretch_wrap_and_delivery_mounting_package": "packaging_letters",
}

MATERIAL_JOB_TO_OPERATION: dict[str, dict[str, Any]] = {
    "face_plexiglas_cutting": {
        "task_key": "cnc_face_cutting",
        "title": "Debitare fețe plexiglas",
        "operation_key": "face_cnc_cut",
        "operation_group": "cnc_cutting",
        "station_hint": "cnc_router",
        "role_hint": "cnc_operator",
        "material_codes": ["MAT-ACP-FATA-LITERE"],
    },
    "forex_backing_cutting": {
        "task_key": "cnc_backing_cutting",
        "title": "Debitare spate Forex",
        "operation_key": "back_cut",
        "operation_group": "cnc_cutting",
        "station_hint": "cnc_router",
        "role_hint": "cnc_operator",
        "material_codes": ["MAT-SPATE-PVC-LITERE"],
    },
    "oracal_vinyl_cutting": {
        "task_key": "oracal_vinyl_cutting",
        "title": "Tăiere colant Oracal",
        "operation_key": "vinyl_application",
        "operation_group": "vinyl_print_finish",
        "station_hint": "workbench",
        "role_hint": "vinyl_operator",
        "material_codes": ["MAT-ORACAL-651"],
    },
    "print_vinyl_artwork": {
        "task_key": "print_artwork",
        "title": "Print artwork",
        "operation_key": "vinyl_application",
        "operation_group": "vinyl_print_finish",
        "station_hint": "workbench",
        "role_hint": "vinyl_operator",
        "material_codes": ["MAT-VINYL-PRINT"],
    },
    "laminate_vinyl_artwork": {
        "task_key": "laminate_print",
        "title": "Laminare print",
        "operation_key": "vinyl_application",
        "operation_group": "vinyl_print_finish",
        "station_hint": "workbench",
        "role_hint": "vinyl_operator",
        "material_codes": ["MAT-VINYL-PRINT-LAMINATED"],
    },
    "return_profile_material": {
        "task_key": "return_side_forming",
        "title": "Modelare canturi",
        "operation_key": "side_forming",
        "operation_group": "return_forming",
        "station_hint": "return_forming_machine",
        "role_hint": "return_forming_operator",
        "material_codes": ["MAT-PROFIL-LATERAL-LITERE"],
    },
    "led_modules_install": {
        "task_key": "led_module_install",
        "title": "Montaj module LED",
        "operation_key": "led_install_letters",
        "operation_group": "led_electrical",
        "station_hint": "electrical_bench",
        "role_hint": "electrical_operator",
        "material_codes": ["MAT-LED-MODULE"],
    },
    "psu_electrical": {
        "task_key": "psu_electrical_wiring",
        "title": "Montare surse LED / cablaj",
        "operation_key": "electrical_letters",
        "operation_group": "led_electrical",
        "station_hint": "electrical_bench",
        "role_hint": "electrical_operator",
        "material_codes": ["MAT-LED-PSU-12V"],
    },
}

_DEPENDENCY_RULES: list[tuple[str, str, str, str, bool]] = [
    ("preflight_vector_and_layers", "cnc_file_preparation", "Vector/layer gate before CNC prep", "template_rule", False),
    ("cnc_file_preparation", "cnc_face_cutting", "CNC prep before face cutting (compat bridge)", "template_rule", False),
    ("cnc_file_preparation", "cnc_face_cutting_plexiglas_3mm", "CNC prep before face cutting", "template_rule", False),
    ("cnc_file_preparation", "cnc_backing_cutting", "CNC prep before backing cutting (compat bridge)", "template_rule", False),
    ("cnc_file_preparation", "cnc_backing_cutting_forex_10mm", "CNC prep before backing cutting", "template_rule", False),
    ("oracal_vinyl_cutting", "face_vinyl_application", "Vinyl cut before face application", "template_rule", False),
    ("print_artwork", "laminate_print", "Print before lamination", "template_rule", False),
    ("laminate_print", "face_vinyl_application", "Laminated print before application", "template_rule", False),
    ("return_side_forming", "return_face_bonding", "Formed return before bonding", "template_rule", False),
    ("cnc_face_cutting", "return_face_bonding", "Face must exist before return bonding (compat bridge)", "template_rule", False),
    ("cnc_face_cutting_plexiglas_3mm", "return_face_bonding", "Face must exist before return bonding", "template_rule", False),
    ("cnc_backing_cutting", "led_module_install", "Backing before LED install (compat bridge)", "template_rule", False),
    ("cnc_backing_cutting_forex_10mm", "led_module_install", "Backing before LED install", "template_rule", False),
    ("led_module_install", "psu_electrical_wiring", "LED modules before electrical wiring", "template_rule", False),
    ("return_face_bonding", "letter_assembly", "Return bonded before assembly", "template_rule", False),
    ("led_module_install", "letter_assembly", "LED before final assembly", "template_rule", False),
    ("psu_electrical_wiring", "letter_assembly", "Electrical before assembly", "template_rule", False),
    ("letter_assembly", "light_test_qc", "Assembly before light test", "template_rule", False),
    ("light_test_qc", "packaging_delivery_prep", "QC before packaging", "template_rule", False),
]

_PREFLIGHT_CANDIDATE = {
    "task_key": "preflight_vector_and_layers",
    "title": "Verificare fișier SVG și roluri layere",
    "operation_key": "vector_prep",
    "operation_group": "preflight_qc",
    "station_hint": "graphics_workstation",
    "role_hint": "graphic_design",
}

_CNC_PREP_CANDIDATE = {
    "task_key": "cnc_file_preparation",
    "title": "Pregătire fișiere CNC / producție",
    "operation_key": "vector_prep",
    "operation_group": "preflight_qc",
    "station_hint": "cnc_preparation_station",
    "role_hint": "cnc_preparation",
}

_ASSEMBLY_CANDIDATE = {
    "task_key": "letter_assembly",
    "title": "Asamblare litere",
    "operation_key": "assembly_letters",
    "operation_group": "assembly",
    "station_hint": "assembly_bench",
    "role_hint": "assembly_operator",
    "provisional": True,
}

_QC_CANDIDATE = {
    "task_key": "light_test_qc",
    "title": "Test lumină / verificare electrică",
    "operation_key": "qc_letters",
    "operation_group": "preflight_qc",
    "station_hint": "electrical_bench",
    "role_hint": "qc_operator",
}

_PACKAGING_CANDIDATE = {
    "task_key": "packaging_delivery_prep",
    "title": "Ambalare / pregătire livrare",
    "operation_key": "packaging_letters",
    "operation_group": "preflight_qc",
    "station_hint": "packing_area",
    "role_hint": "assembly_operator",
}

_RETURN_BONDING = {
    "task_key": "return_face_bonding",
    "title": "Lipire canturi pe fețe",
    "operation_key": "return_face_bonding",
    "operation_group": "return_bonding",
    "station_hint": "assembly_bench",
    "role_hint": "assembly_operator",
}

_FACE_VINYL_APPLY = {
    "task_key": "face_vinyl_application",
    "title": "Aplicare colant / print pe fețe",
    "operation_key": "vinyl_application",
    "operation_group": "vinyl_print_finish",
    "station_hint": "workbench",
    "role_hint": "vinyl_operator",
}


def _issue(
    code: str,
    *,
    severity: str = "warning",
    message: str,
    source: str,
) -> IntakeV4TaskGenerationDryRunIssue:
    return IntakeV4TaskGenerationDryRunIssue(
        code=code,
        severity=severity,  # type: ignore[arg-type]
        message=message,
        source=source,
    )


def _idempotency_key(workspace_id: str, template_code: str, task_key: str) -> str:
    return f"intake-v4:{workspace_id}:{template_code}:{task_key}"


def _analysis_hash(payload: IntakeV4WorkspacePayload) -> str | None:
    if payload.svg_source and payload.svg_source.file_hash:
        return payload.svg_source.file_hash
    return None


def _finish_fingerprint(payload: IntakeV4WorkspacePayload) -> str:
    setup = payload.finish_setup
    if setup is None:
        return hashlib.sha256(b"finish_setup_missing").hexdigest()
    raw = setup.model_dump(mode="json", exclude_none=True)
    encoded = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_fingerprint(analysis_hash: str | None, finish_fp: str) -> str:
    parts = [
        analysis_hash or "no_analysis_hash",
        finish_fp,
        TEMPLATE_OPTION_CONTRACT_VERSION,
    ]
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _operation_template_backed(operation_key: str | None, catalog_code: str | None) -> bool:
    if operation_key and operation_key in DOSSIER_OPERATION_KEYS:
        return True
    if catalog_code:
        mapped = CATALOG_TO_DOSSIER_OPERATION.get(catalog_code)
        if mapped and mapped in DOSSIER_OPERATION_KEYS:
            return True
    return False


def _candidate_from_spec(
    *,
    workspace_id: str,
    template_code: str,
    spec: dict[str, Any],
    source_material_jobs: list[str],
    quantity_basis: str | None,
    source_fingerprint: str,
    provisional_override: bool = False,
    catalog_code: str | None = None,
) -> IntakeV4TaskGenerationTaskCandidate:
    task_key = spec["task_key"]
    operation_key = spec.get("operation_key")
    template_backed = _operation_template_backed(operation_key, None)
    provisional = bool(spec.get("provisional")) or provisional_override or not template_backed
    alignment_fields = enrich_task_candidate_alignment(
        task_key=task_key,
        operation_key=operation_key,
        catalog_code=catalog_code,
        provisional=provisional,
    )
    provisional = alignment_fields.pop("provisional")
    template_backed = alignment_fields.pop("template_backed", template_backed)
    provisional_reason = alignment_fields.pop("provisional_reason", None)
    warnings: list[str] = []
    if provisional:
        warnings.append("provisional_task_candidate")
        if provisional_reason:
            warnings.append(f"provisional_reason:{provisional_reason}")
    if not template_backed:
        warnings.append("template_operation_mapping_missing")
    material_codes = list(spec.get("material_codes") or [])
    return IntakeV4TaskGenerationTaskCandidate(
        task_key=task_key,
        title=spec["title"],
        template_code=template_code,
        template_backed=template_backed,
        provisional=provisional,
        provisional_reason=provisional_reason,
        operation_key=operation_key,
        operation_group=spec.get("operation_group"),
        station_hint=spec.get("station_hint"),
        role_hint=spec.get("role_hint"),
        source_material_jobs=source_material_jobs,
        source_operation_groups=[spec["operation_group"]] if spec.get("operation_group") else [],
        estimated_inputs=IntakeV4TaskGenerationEstimatedInputs(
            material_codes=material_codes,
            quantity_basis=quantity_basis,
        ),
        creates_execution_task=False,
        idempotency_key=_idempotency_key(workspace_id, template_code, task_key),
        warnings=warnings,
        **alignment_fields,
    )


def _build_task_candidates(
    *,
    workspace_id: str,
    template_code: str,
    handoff: IntakeV4ProductionHandoffPreviewResponse,
    source_fingerprint: str,
    preview_provisional: bool,
    operation_rows: list | None = None,
    edge_cant_operation_rows: list | None = None,
) -> list[IntakeV4TaskGenerationTaskCandidate]:
    job_by_key = {job.job_key: job for job in handoff.material_jobs}
    active_job_keys = set(job_by_key.keys())
    candidates: dict[str, IntakeV4TaskGenerationTaskCandidate] = {}

    analysis_blockers = {
        b.code
        for b in handoff.blockers
        if b.severity == "blocking" and b.source.startswith(("analysis", "layer", "svg", "product"))
    }
    has_geometry_jobs = bool(active_job_keys & {"face_plexiglas_cutting", "forex_backing_cutting"})

    if not analysis_blockers:
        for spec in (_PREFLIGHT_CANDIDATE, _CNC_PREP_CANDIDATE):
            candidates[spec["task_key"]] = _candidate_from_spec(
                workspace_id=workspace_id,
                template_code=template_code,
                spec=spec,
                source_material_jobs=[],
                quantity_basis=None,
                source_fingerprint=source_fingerprint,
            )

    for job_key, spec in MATERIAL_JOB_TO_OPERATION.items():
        if job_key not in active_job_keys:
            continue
        if should_skip_compat_bridge_cnc_material_job(job_key, list(operation_rows or [])):
            continue
        job = job_by_key[job_key]
        candidates[spec["task_key"]] = _candidate_from_spec(
            workspace_id=workspace_id,
            template_code=template_code,
            spec=spec,
            source_material_jobs=[job_key],
            quantity_basis=job.quantity_basis,
            source_fingerprint=source_fingerprint,
            provisional_override=preview_provisional,
        )

    if "return_profile_material" in active_job_keys and "return_face_bonding" not in candidates:
        return_job = job_by_key.get("return_profile_material")
        candidates["return_face_bonding"] = _candidate_from_spec(
            workspace_id=workspace_id,
            template_code=template_code,
            spec=_RETURN_BONDING,
            source_material_jobs=["return_profile_material"],
            quantity_basis=return_job.quantity_basis if return_job else None,
            source_fingerprint=source_fingerprint,
        )

    vinyl_jobs = {"oracal_vinyl_cutting", "print_vinyl_artwork", "laminate_vinyl_artwork"}
    if active_job_keys & vinyl_jobs:
        candidates["face_vinyl_application"] = _candidate_from_spec(
            workspace_id=workspace_id,
            template_code=template_code,
            spec=_FACE_VINYL_APPLY,
            source_material_jobs=sorted(active_job_keys & vinyl_jobs),
            quantity_basis=None,
            source_fingerprint=source_fingerprint,
        )

    if has_geometry_jobs or len(active_job_keys) >= 2:
        candidates["letter_assembly"] = _candidate_from_spec(
            workspace_id=workspace_id,
            template_code=template_code,
            spec=_ASSEMBLY_CANDIDATE,
            source_material_jobs=sorted(active_job_keys),
            quantity_basis=None,
            source_fingerprint=source_fingerprint,
            provisional_override=True,
        )

    if active_job_keys & {"led_modules_install", "psu_electrical"}:
        candidates["light_test_qc"] = _candidate_from_spec(
            workspace_id=workspace_id,
            template_code=template_code,
            spec=_QC_CANDIDATE,
            source_material_jobs=sorted(active_job_keys & {"led_modules_install", "psu_electrical"}),
            quantity_basis=None,
            source_fingerprint=source_fingerprint,
        )

    if candidates:
        candidates["packaging_delivery_prep"] = _candidate_from_spec(
            workspace_id=workspace_id,
            template_code=template_code,
            spec=_PACKAGING_CANDIDATE,
            source_material_jobs=[],
            quantity_basis=None,
            source_fingerprint=source_fingerprint,
            )

    if operation_rows:
        for row in operation_rows:
            op_row = (
                row
                if isinstance(row, IntakeV4CncOperationRow)
                else IntakeV4CncOperationRow.model_validate(row)
            )
            cand = cnc_operation_row_to_task_candidate(
                op_row,
                workspace_id=workspace_id,
                template_code=template_code,
                source_fingerprint=source_fingerprint,
            )
            candidates[cand.task_key] = cand

    if edge_cant_operation_rows:
        for row in edge_cant_operation_rows:
            edge_row = (
                row
                if isinstance(row, IntakeV4EdgeCantOperationRow)
                else IntakeV4EdgeCantOperationRow.model_validate(row)
            )
            cand = edge_cant_operation_row_to_task_candidate(
                edge_row,
                workspace_id=workspace_id,
                template_code=template_code,
                source_fingerprint=source_fingerprint,
            )
            candidates[cand.task_key] = cand

    for seed in handoff.task_seed_preview:
        if not seed.active:
            continue
        if seed.task_key in candidates:
            existing = candidates[seed.task_key]
            candidates[seed.task_key] = existing.model_copy(
                update={
                    "depends_on": list(seed.depends_on or []),
                    "station_hint": existing.station_hint or seed.station_hint,
                    "role_hint": existing.role_hint or seed.role_hint,
                }
            )
            continue
        dossier_op = CATALOG_TO_DOSSIER_OPERATION.get(seed.operation_code, seed.operation_code)
        template_backed = _operation_template_backed(dossier_op, seed.operation_code)
        provisional = preview_provisional or not template_backed
        alignment_fields = enrich_task_candidate_alignment(
            task_key=seed.task_key,
            operation_key=dossier_op,
            catalog_code=seed.operation_code,
            provisional=provisional,
        )
        provisional = alignment_fields.pop("provisional")
        template_backed = alignment_fields.pop("template_backed", template_backed)
        provisional_reason = alignment_fields.pop("provisional_reason", None)
        warnings: list[str] = []
        if provisional:
            warnings.append("provisional_task_candidate")
            if provisional_reason:
                warnings.append(f"provisional_reason:{provisional_reason}")
        if not template_backed:
            warnings.append("template_operation_mapping_missing")
        candidates[seed.task_key] = IntakeV4TaskGenerationTaskCandidate(
            task_key=seed.task_key,
            title=seed.title,
            template_code=template_code,
            template_backed=template_backed,
            provisional=provisional,
            provisional_reason=provisional_reason,
            operation_key=dossier_op,
            operation_group=None,
            station_hint=seed.station_hint,
            role_hint=seed.role_hint,
            source_material_jobs=list(seed.source_material_jobs or []),
            depends_on=list(seed.depends_on or []),
            creates_execution_task=False,
            idempotency_key=_idempotency_key(workspace_id, template_code, seed.task_key),
            warnings=warnings,
            **alignment_fields,
        )

    return list(candidates.values())


def _build_dependency_graph(
    candidates: list[IntakeV4TaskGenerationTaskCandidate],
) -> list[IntakeV4TaskGenerationDependencyEdge]:
    active_keys = {c.task_key for c in candidates if c.active}
    edges: list[IntakeV4TaskGenerationDependencyEdge] = []
    seen: set[tuple[str, str]] = set()

    for candidate in candidates:
        for dep in candidate.depends_on:
            if dep in active_keys and candidate.task_key in active_keys:
                key = (dep, candidate.task_key)
                if key not in seen:
                    seen.add(key)
                    edges.append(
                        IntakeV4TaskGenerationDependencyEdge(
                            from_task_key=dep,
                            to_task_key=candidate.task_key,
                            reason="Catalog seed depends_on",
                            confidence="catalog_doc",
                            provisional=bool(candidate.provisional),
                        )
                    )

    for from_key, to_key, reason, confidence, provisional in _DEPENDENCY_RULES:
        if from_key in active_keys and to_key in active_keys:
            key = (from_key, to_key)
            if key not in seen:
                seen.add(key)
                edges.append(
                    IntakeV4TaskGenerationDependencyEdge(
                        from_task_key=from_key,
                        to_task_key=to_key,
                        reason=reason,
                        confidence=confidence,  # type: ignore[arg-type]
                        provisional=provisional,
                    )
                )
    return edges


def _build_idempotency_plan(
    *,
    workspace_id: str,
    template_code: str,
    candidates: list[IntakeV4TaskGenerationTaskCandidate],
    source_fingerprint: str,
) -> list[IntakeV4TaskGenerationIdempotencyEntry]:
    return [
        IntakeV4TaskGenerationIdempotencyEntry(
            task_key=c.task_key,
            idempotency_key=c.idempotency_key,
            source_fingerprint=source_fingerprint,
        )
        for c in candidates
        if c.active
    ]


def _merge_blockers_and_warnings(
    handoff: IntakeV4ProductionHandoffPreviewResponse,
    contract_blockers: list,
    contract_warnings: list,
    candidates: list[IntakeV4TaskGenerationTaskCandidate],
) -> tuple[list[IntakeV4TaskGenerationDryRunIssue], list[IntakeV4TaskGenerationDryRunIssue]]:
    blockers: list[IntakeV4TaskGenerationDryRunIssue] = []
    warnings: list[IntakeV4TaskGenerationDryRunIssue] = []

    for item in handoff.blockers:
        blockers.append(
            _issue(item.code, severity=item.severity, message=item.message, source=item.source)
        )
    for item in contract_blockers:
        blockers.append(
            _issue(item.code, severity=item.severity, message=item.message, source=item.source)
        )

    for item in handoff.warnings:
        warnings.append(
            _issue(item.code, severity=item.severity, message=item.message, source=item.source)
        )
    for item in contract_warnings:
        if item.severity != "blocking":
            warnings.append(
                _issue(item.code, severity=item.severity, message=item.message, source=item.source)
            )

    partial_alignment_groups = [
        g.group_key
        for g in handoff.operation_groups
        if g.active
        and g.template_alignment
        and g.template_alignment.status in ("partial", "missing")
    ]
    if partial_alignment_groups:
        warnings.append(
            _issue(
                "template_operation_alignment_partial",
                message=(
                    f"Operation groups with incomplete canonical alignment: "
                    f"{', '.join(partial_alignment_groups)}"
                ),
                source="template_operation_alignment",
            )
        )

    provisional_groups = [
        g.group_key for g in handoff.operation_groups if g.active and g.inactive_reason
    ]
    if provisional_groups:
        warnings.append(
            _issue(
                "production_preview_not_template_backed",
                message="Some operation groups are provisional in production handoff preview.",
                source="operation_groups",
            )
        )

    if not candidates:
        blockers.append(
            _issue(
                "material_jobs_missing",
                severity="blocking",
                message="No task candidates — material jobs or finish data insufficient.",
                source="task_candidates",
            )
        )

    provisional_count = sum(1 for c in candidates if c.provisional)
    if provisional_count:
        warnings.append(
            _issue(
                "provisional_task_candidates_present",
                message=f"{provisional_count} task candidate(s) are provisional — not safe for real generation.",
                source="task_candidates",
            )
        )

    if any(c.warnings for c in candidates if "template_operation_mapping_missing" in c.warnings):
        warnings.append(
            _issue(
                "template_operation_mapping_missing",
                message="One or more task candidates lack dossier operation mapping.",
                source="task_candidates",
            )
        )

    blockers.append(
        _issue(
            "dry_run_only_no_order",
            severity="blocking",
            message="Real task generation requires order binding — not available at Intake V4 workspace stage.",
            source="generation_boundary",
        )
    )

    return blockers, warnings


async def build_intake_v4_task_generation_dry_run(
    db: AsyncSession,
    workspace_id: str,
    payload_raw: dict[str, Any],
    payload: IntakeV4WorkspacePayload,
) -> IntakeV4TaskGenerationDryRunResponse:
    """Read-only task generation dry-run contract — no DB writes, no ExecutionTask."""
    handoff = await build_intake_v4_production_handoff_preview(
        db, workspace_id, payload_raw, payload
    )
    contract = evaluate_v4_template_option_contract(payload)

    preview_provisional = any(
        w.code == "production_preview_not_template_backed" for w in contract.warnings
    )

    analysis_hash = _analysis_hash(payload)
    finish_fp = _finish_fingerprint(payload)
    fingerprint = _source_fingerprint(analysis_hash, finish_fp)

    template_code = payload.product_binding.template_code

    breakdown = None
    operation_rows: list = []
    edge_cant_operation_rows: list = []
    if template_code == PILOT_V4_TEMPLATE_CODE:
        breakdown = await build_intake_v4_material_breakdown_with_registry(
            db, workspace_id, payload_raw
        )
        operation_rows = list(breakdown.operation_rows or [])
        edge_cant_operation_rows = list(breakdown.edge_cant_operation_rows or [])
    legacy_cnc_mapping_used = not operation_rows
    compat_cnc_mapping_used = legacy_cnc_mapping_used
    cnc_task_source = CNC_TASK_DRY_RUN_SOURCE if operation_rows else CNC_TASK_DRY_RUN_SOURCE_COMPAT_FALLBACK
    cnc_operation_candidates = (
        build_cnc_dry_run_from_operation_rows(
            operation_rows,
            workspace_id=workspace_id,
            template_code=template_code,
            source_fingerprint=fingerprint,
        )[1]
        if operation_rows
        else []
    )
    edge_cant_task_source = EDGE_CANT_TASK_DRY_RUN_SOURCE if edge_cant_operation_rows else None
    edge_cant_operation_candidates = (
        build_edge_cant_dry_run_from_operation_rows(
            edge_cant_operation_rows,
            workspace_id=workspace_id,
            template_code=template_code,
            source_fingerprint=fingerprint,
        )[1]
        if edge_cant_operation_rows
        else []
    )

    candidates = _build_task_candidates(
        workspace_id=workspace_id,
        template_code=template_code,
        handoff=handoff,
        source_fingerprint=fingerprint,
        preview_provisional=preview_provisional,
        operation_rows=operation_rows,
        edge_cant_operation_rows=edge_cant_operation_rows,
    )

    contract_blockers = [b for b in contract.blockers if b.severity == "blocking"]
    contract_warnings = contract.warnings

    blockers, warnings = _merge_blockers_and_warnings(
        handoff,
        contract_blockers,
        contract_warnings,
        candidates,
    )

    if legacy_cnc_mapping_used:
        warnings.append(
            _issue(
                "cnc_dry_run_legacy_parallel_mapping",
                message=(
                    "CNC dry-run compatibility fallback mapping used because operation_rows were unavailable."
                ),
                source="cnc_task_dry_run",
            )
        )
    else:
        warnings.append(
            _issue(
                "cnc_dry_run_from_operation_rows",
                severity="info",
                message="CNC dry-run candidates derived from material breakdown operation_rows.",
                source="cnc_task_dry_run",
            )
        )
        warnings.append(
            _issue(
                "dry_run_no_real_task",
                severity="info",
                message="Dry-run preview only — no real tasks created.",
                source="generation_boundary",
            )
        )
        warnings.append(
            _issue(
                "dry_run_stock_not_consumed",
                severity="info",
                message="Stock not consumed in dry-run preview.",
                source="generation_boundary",
            )
        )

    dependency_graph = _build_dependency_graph(candidates)
    idempotency_plan = _build_idempotency_plan(
        workspace_id=workspace_id,
        template_code=template_code,
        candidates=candidates,
        source_fingerprint=fingerprint,
    )

    active_candidates = [c for c in candidates if c.active]
    blocked_count = sum(1 for c in active_candidates if c.blockers)
    provisional_count = sum(1 for c in active_candidates if c.provisional)
    template_backed_count = sum(1 for c in active_candidates if c.template_backed and not c.provisional)

    candidate_dicts = [c.model_dump() for c in active_candidates]
    alignment_summary = summarize_template_operation_alignment(
        handoff_groups=[
            {
                "template_alignment": (
                    g.template_alignment.model_dump() if g.template_alignment else {}
                ),
            }
            for g in handoff.operation_groups
        ],
        task_candidates=candidate_dicts,
    )

    blocking_codes = {b.code for b in blockers if b.severity == "blocking"}
    can_generate = False  # always false in this build

    audit_preview = IntakeV4TaskGenerationAuditPreview(
        entity_id=workspace_id,
        would_create_count=len(active_candidates),
        blocked_count=blocked_count + len(blocking_codes),
        provisional_count=provisional_count,
        analysis_hash=analysis_hash,
        finish_fingerprint=finish_fp,
        template_code=template_code,
    )

    return IntakeV4TaskGenerationDryRunResponse(
        workspace_id=workspace_id,
        template_code=template_code,
        template_backed=template_code == PILOT_V4_TEMPLATE_CODE,
        can_generate_tasks=can_generate,
        task_candidates=candidates,
        dependency_graph=dependency_graph,
        idempotency_plan=idempotency_plan,
        blockers=blockers,
        warnings=warnings,
        audit_preview=audit_preview,
        cnc_task_source=cnc_task_source,
        cnc_operation_candidate_count=len(cnc_operation_candidates),
        cnc_operation_candidates=cnc_operation_candidates,
        compat_cnc_mapping_used=compat_cnc_mapping_used,
        legacy_cnc_mapping_used=legacy_cnc_mapping_used,
        edge_cant_operation_candidate_count=len(edge_cant_operation_candidates),
        edge_cant_operation_candidates=edge_cant_operation_candidates,
        edge_cant_task_source=edge_cant_task_source,
        summary={
            "task_candidates_count": len(candidates),
            "active_candidates_count": len(active_candidates),
            "template_backed_count": template_backed_count,
            "provisional_count": provisional_count,
            "dependency_edges_count": len(dependency_graph),
            "idempotency_entries_count": len(idempotency_plan),
            "blockers_count": len(blockers),
            "warnings_count": len(warnings),
            "source_fingerprint": fingerprint,
            "template_operation_alignment": alignment_summary.to_dict(),
            "cnc_task_source": cnc_task_source,
            "compat_cnc_mapping_used": compat_cnc_mapping_used,
            "legacy_cnc_mapping_used": legacy_cnc_mapping_used,
            "cnc_operation_candidate_count": len(cnc_operation_candidates),
            "edge_cant_task_source": edge_cant_task_source,
            "edge_cant_operation_candidate_count": len(edge_cant_operation_candidates),
            "idempotency_note": (
                "idempotency_key excludes analysis_hash to prevent duplicate clicks; "
                "source_fingerprint signals when regeneration is needed after reupload/finish change."
            ),
        },
    )
