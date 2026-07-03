"""Intake V3 workspace draft persistence — CRUD only, no quote/order/plan/inventory."""

from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from models.intake_v3_workspace import IntakeV3WorkspaceRecord
from schemas.auth import UserResponse
from schemas.intake_v3 import (
    IntakeV3ApplyFinishAssignmentsRequest,
    IntakeV3ApplyFinishAssignmentsResponse,
    IntakeV3ApplyLayerFinishAssignmentsRequest,
    IntakeV3ApplyLayerFinishAssignmentsResponse,
    IntakeV3ApplyLightingPlanRequest,
    IntakeV3ApplyLightingPlanResponse,
    IntakeV3LightingPlanStateResponse,
    IntakeV3ConfirmProductionModelRequest,
    IntakeV3ConfirmProductionModelResponse,
    IntakeV3FinishAssignmentTargetsResponse,
    IntakeV3FinishAssignmentsStateResponse,
    IntakeV3LayerFinishAssignmentTargetsResponse,
    IntakeV3LayerFinishAssignmentsStateResponse,
    IntakeV3PreviewBuildResult,
    IntakeV3ProductionModelReviewCandidateResponse,
    IntakeV3QuoteReadinessResponse,
    IntakeV3QuoteCreationDryRunResponse,
    IntakeV3QuoteCreationGuardPolicyResponse,
    IntakeV3CommercialQuoteBridgeResponse,
    IntakeV3QuoteCreationEnablementResponse,
    IntakeV3RealQuoteCreationEnablementReadinessResponse,
    IntakeV3CreateDraftQuoteRequest,
    IntakeV3CreateDraftQuoteResponse,
    IntakeV3DraftQuoteReview,
    IntakeV3CompletePricingReviewRequest,
    IntakeV3CompletePricingReviewResponse,
    IntakeV3PricingReviewCompletionState,
    IntakeV3PricedDraftAcceptConvertReadiness,
    IntakeV3AcceptQuoteRequest,
    IntakeV3AcceptQuoteResponse,
    IntakeV3AcceptState,
    IntakeV3ConvertToOrderRequest,
    IntakeV3ConvertToOrderResponse,
    IntakeV3ConvertToOrderState,
    IntakeV3SvgAnalysisWarning,
    IntakeV3SvgUploadResponse,
    IntakeV3Workspace,
    IntakeV3WorkspaceCreateRequest,
    IntakeV3WorkspaceFieldPatchRequest,
    IntakeV3WorkspaceFieldPatchResponse,
    IntakeV3WorkspaceListItem,
    IntakeV3WorkspaceListResponse,
    IntakeV3WorkspacePreviewResponse,
    IntakeV3WorkspaceResponse,
    IntakeV3WorkspaceSeedFromScenarioRequest,
    IntakeV3WorkspaceUpdateRequest,
    WorkspaceDraftStatus,
)
from services.intake_v3_finish_assignment_service import (
    apply_finish_assignments_to_payload,
    get_confirmed_letter_targets,
    summarize_finish_assignments,
    validate_finish_assignments,
)
from services.intake_v3_layer_finish_assignment_service import (
    apply_layer_finish_assignments_to_payload,
    draft_layer_finish_assignments,
    get_layer_finish_targets,
    summarize_layer_finish_assignments,
    validate_layer_finish_assignments,
)
from services.intake_v3_lighting_plan_service import (
    apply_lighting_plan_to_payload,
    draft_lighting_plan,
    summarize_lighting_plan,
    validate_lighting_plan,
)
from services.intake_v3_production_model_review_service import (
    apply_confirmed_production_model_to_payload,
    build_production_model_review_candidate_from_payload,
    require_review_candidate_or_raise,
)
from services.intake_v3_svg_analysis_service import (
    analyze_svg_content,
    build_vector_asset_from_validation,
    validate_svg_upload,
)
from services.intake_v3_preview_fixtures import (
    SUPPORTED_INTAKE_V3_PREVIEW_SCENARIOS,
    build_intake_v3_preview_workspace_for_scenario,
)
from services.intake_v3_readiness_service import evaluate_intake_v3_readiness
from services.intake_v3_workspace_field_editor_service import apply_validated_field_patches_or_raise
from services.intake_v3_workspace_preview_service import build_intake_v3_workspace_preview
from services.intake_v3_quote_creation_dry_run_service import (
    build_intake_v3_quote_creation_dry_run,
)
from services.intake_v3_quote_creation_guard_policy_service import (
    evaluate_quote_creation_guard_policy,
)
from services.intake_v3_commercial_quote_bridge_service import (
    build_commercial_quote_bridge_preview,
    commercial_quote_bridge_status_label,
    is_commercial_quote_bridge_available,
)
from services.intake_v3_quote_creation_enablement_policy_service import (
    evaluate_quote_creation_enablement_policy,
)
from services.intake_v3_quote_creation_final_blocker_service import (
    evaluate_quote_creation_final_blockers,
)
from services.intake_v3_real_quote_creation_enablement_readiness_service import (
    evaluate_real_quote_creation_enablement_readiness,
)
from services.intake_v3_real_commercial_quote_creation_service import (
    create_guarded_draft_quote_from_intake_v3_workspace,
)
from services.intake_v3_draft_quote_review_service import (
    get_intake_v3_draft_quote_review,
    get_intake_v3_draft_quote_review_by_workspace,
)
from services.intake_v3_quote_pricing_review_completion_service import (
    complete_intake_v3_quote_pricing_review,
    complete_intake_v3_quote_pricing_review_by_workspace,
    get_pricing_review_completion_state,
    get_pricing_review_completion_state_by_workspace,
)
from services.intake_v3_quote_readiness_service import (
    build_prequote_review,
    evaluate_intake_v3_quote_readiness,
)

FORBIDDEN_PERSISTENCE_KEYS = frozenset(
    {
        "created_quote_id",
        "created_order_id",
        "execution_plan_id",
        "execution_task_id",
        "stock_movement_id",
        "quote_id",
        "order_id",
    }
)

BOUNDARY_FLAG_KEYS = frozenset(
    {
        "quote_creation_allowed",
        "order_creation_allowed",
        "execution_plan_creation_allowed",
        "inventory_mutation_allowed",
        "employee_mobile_action_allowed",
    }
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _strip_forbidden_keys(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for key, value in data.items():
            if key in FORBIDDEN_PERSISTENCE_KEYS:
                continue
            cleaned[key] = _strip_forbidden_keys(value)
        return cleaned
    if isinstance(data, list):
        return [_strip_forbidden_keys(item) for item in data]
    return data


def _force_safe_boundary_flags(data: dict[str, Any]) -> None:
    boundary = data.get("boundary_flags")
    if isinstance(boundary, dict):
        for key in BOUNDARY_FLAG_KEYS:
            boundary[key] = False
        boundary["preview_only"] = True


def sanitize_intake_v3_workspace_payload(raw: dict[str, Any]) -> IntakeV3Workspace:
    """Ensure persisted workspace payload cannot enable real commercial/production actions."""
    data = _strip_forbidden_keys(copy.deepcopy(raw))

    material_intent = data.get("material_intent")
    if isinstance(material_intent, dict):
        material_intent["inventory_mutation_allowed"] = False

    production_handoff = data.get("production_handoff")
    if isinstance(production_handoff, dict):
        production_handoff["preview_only"] = True

    employee_preview_seed = data.get("employee_preview_seed")
    if isinstance(employee_preview_seed, dict):
        employee_preview_seed["non_executable"] = True

    pricing_input = data.get("pricing_input")
    if isinstance(pricing_input, dict):
        pricing_input.pop("quote_id", None)
        pricing_input.pop("order_id", None)

    _force_safe_boundary_flags(data)

    return IntakeV3Workspace.model_validate(data)


def _workspace_code() -> str:
    return f"IV3-{uuid.uuid4().hex[:8].upper()}"


def _derive_readiness_status(workspace: IntakeV3Workspace) -> str:
    report = evaluate_intake_v3_readiness(workspace)
    if report.blockers:
        return "blocked_for_quote"
    if report.can_create_quote:
        return "ready_for_quote"
    return "in_progress"


def _derive_workspace_status(workspace: IntakeV3Workspace, readiness_status: str) -> WorkspaceDraftStatus:
    if readiness_status == "blocked_for_quote":
        return "blocked"
    if readiness_status == "ready_for_quote":
        return "ready_for_quote_preview"
    if workspace.confirmed_production_model or workspace.finish_assignment:
        return "collecting_data"
    return "draft"


def _record_to_response(record: IntakeV3WorkspaceRecord) -> IntakeV3WorkspaceResponse:
    metadata = _json_loads(record.metadata_json, {})
    return IntakeV3WorkspaceResponse(
        id=record.id,
        workspace_code=record.workspace_code,
        title=record.title,
        template_code=record.template_code,
        status=record.status,  # type: ignore[arg-type]
        payload=_json_loads(record.payload_json, {}),
        metadata=metadata if isinstance(metadata, dict) else {},
        readiness_status=record.readiness_status,
        created_by_user_id=record.created_by_user_id,
        updated_by_user_id=record.updated_by_user_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
        archived_at=record.archived_at,
    )


def _record_to_list_item(record: IntakeV3WorkspaceRecord) -> IntakeV3WorkspaceListItem:
    metadata = _json_loads(record.metadata_json, {})
    source_scenario = metadata.get("source_scenario") if isinstance(metadata, dict) else None
    return IntakeV3WorkspaceListItem(
        id=record.id,
        workspace_code=record.workspace_code,
        title=record.title,
        template_code=record.template_code,
        status=record.status,  # type: ignore[arg-type]
        readiness_status=record.readiness_status,
        source_scenario=source_scenario,
        updated_at=record.updated_at,
    )


async def _get_record_or_404(db: AsyncSession, workspace_id: str) -> IntakeV3WorkspaceRecord:
    result = await db.execute(
        select(IntakeV3WorkspaceRecord).where(IntakeV3WorkspaceRecord.id == workspace_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "workspace_not_found", "workspace_id": workspace_id})
    return record


async def create_intake_v3_workspace(
    db: AsyncSession,
    request: IntakeV3WorkspaceCreateRequest,
    current_user: UserResponse,
) -> IntakeV3WorkspaceResponse:
    workspace = sanitize_intake_v3_workspace_payload(request.payload)
    readiness_status = _derive_readiness_status(workspace)
    status = _derive_workspace_status(workspace, readiness_status)
    metadata: dict[str, Any] = {}
    if request.source_scenario:
        metadata["source_scenario"] = request.source_scenario

    record = IntakeV3WorkspaceRecord(
        id=str(uuid.uuid4()),
        workspace_code=_workspace_code(),
        title=request.title.strip(),
        template_code=request.template_code or PILOT_TEMPLATE_CODE,
        status=status,
        payload_json=_json_dumps(workspace.model_dump(mode="json")),
        readiness_status=readiness_status,
        metadata_json=_json_dumps(metadata),
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _record_to_response(record)


async def get_intake_v3_workspace(db: AsyncSession, workspace_id: str) -> IntakeV3WorkspaceResponse:
    record = await _get_record_or_404(db, workspace_id)
    return _record_to_response(record)


async def list_intake_v3_workspaces(
    db: AsyncSession,
    *,
    include_archived: bool = False,
) -> IntakeV3WorkspaceListResponse:
    query = select(IntakeV3WorkspaceRecord).order_by(IntakeV3WorkspaceRecord.updated_at.desc())
    if not include_archived:
        query = query.where(IntakeV3WorkspaceRecord.archived_at.is_(None))
    result = await db.execute(query)
    records = list(result.scalars().all())
    items = [_record_to_list_item(record) for record in records]
    return IntakeV3WorkspaceListResponse(items=items, total=len(items))


async def update_intake_v3_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3WorkspaceUpdateRequest,
    current_user: UserResponse,
) -> IntakeV3WorkspaceResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(status_code=400, detail={"error": "workspace_archived", "workspace_id": workspace_id})

    if request.title is not None:
        record.title = request.title.strip()

    if request.payload is not None:
        workspace = sanitize_intake_v3_workspace_payload(request.payload)
        record.payload_json = _json_dumps(workspace.model_dump(mode="json"))
        record.readiness_status = _derive_readiness_status(workspace)
        if request.status is None:
            record.status = _derive_workspace_status(workspace, record.readiness_status)

    if request.status is not None:
        record.status = request.status

    if request.preview_snapshot is not None:
        snapshot = _strip_forbidden_keys(copy.deepcopy(request.preview_snapshot))
        if isinstance(snapshot, dict):
            _force_safe_boundary_flags(snapshot)
        record.preview_snapshot_json = _json_dumps(snapshot)

    record.updated_by_user_id = current_user.id
    record.updated_at = _utcnow()
    await db.commit()
    await db.refresh(record)
    return _record_to_response(record)


async def archive_intake_v3_workspace(
    db: AsyncSession,
    workspace_id: str,
    current_user: UserResponse,
) -> IntakeV3WorkspaceResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is None:
        record.archived_at = _utcnow()
        record.status = "archived"
        record.updated_by_user_id = current_user.id
        record.updated_at = _utcnow()
        await db.commit()
        await db.refresh(record)
    return _record_to_response(record)


async def seed_workspace_from_preview_scenario(
    db: AsyncSession,
    request: IntakeV3WorkspaceSeedFromScenarioRequest,
    current_user: UserResponse,
) -> IntakeV3WorkspaceResponse:
    if request.scenario not in SUPPORTED_INTAKE_V3_PREVIEW_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unknown_preview_scenario",
                "scenario": request.scenario,
                "supported_scenarios": list(SUPPORTED_INTAKE_V3_PREVIEW_SCENARIOS),
            },
        )

    workspace = build_intake_v3_preview_workspace_for_scenario(request.scenario)
    title = request.title or f"Draft — {request.scenario.replace('_', ' ')}"
    payload = workspace.model_dump(mode="json")
    if workspace.confirmed_production_model is not None:
        from services.intake_v3_geometry_metrics_snapshot_service import (
            build_geometry_metrics_snapshot,
            persist_geometry_metrics_snapshot_to_payload,
        )

        geometry_snapshot = build_geometry_metrics_snapshot(
            workspace=workspace,
            source_type="workspace",
            source_id="scenario_seed",
        )
        payload = persist_geometry_metrics_snapshot_to_payload(payload, geometry_snapshot)
    create_request = IntakeV3WorkspaceCreateRequest(
        title=title,
        template_code=workspace.product_selection.template_code,
        payload=payload,
        source_scenario=request.scenario,
    )
    return await create_intake_v3_workspace(db, create_request, current_user)


async def build_preview_for_workspace_record(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3WorkspacePreviewResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    workspace = sanitize_intake_v3_workspace_payload(payload if isinstance(payload, dict) else {})
    build_result: IntakeV3PreviewBuildResult = build_intake_v3_workspace_preview(workspace)

    record.readiness_status = _derive_readiness_status(workspace)
    if record.status != "archived":
        record.status = _derive_workspace_status(workspace, record.readiness_status)
    record.preview_snapshot_json = _json_dumps(build_result.model_dump(mode="json"))
    record.updated_at = _utcnow()
    await db.commit()

    return IntakeV3WorkspacePreviewResponse(
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        preview=build_result.preview,
        build_warnings=build_result.build_warnings,
        build_blockers=build_result.build_blockers,
        is_preview_complete=build_result.is_preview_complete,
    )


async def patch_intake_v3_workspace_fields(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3WorkspaceFieldPatchRequest,
    current_user: UserResponse,
) -> IntakeV3WorkspaceFieldPatchResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(
            status_code=400,
            detail={"error": "workspace_archived", "workspace_id": workspace_id},
        )

    payload = _json_loads(record.payload_json, {})
    updated_payload, applied, new_title = apply_validated_field_patches_or_raise(
        payload if isinstance(payload, dict) else {},
        request.patches,
    )

    if new_title:
        record.title = new_title

    workspace = sanitize_intake_v3_workspace_payload(updated_payload)
    record.payload_json = _json_dumps(updated_payload)
    record.readiness_status = _derive_readiness_status(workspace)
    record.status = _derive_workspace_status(workspace, record.readiness_status)
    record.updated_by_user_id = current_user.id
    record.updated_at = _utcnow()
    await db.commit()
    await db.refresh(record)

    preview_response: IntakeV3WorkspacePreviewResponse | None = None
    if request.regenerate_preview:
        preview_response = await build_preview_for_workspace_record(db, workspace_id)

    return IntakeV3WorkspaceFieldPatchResponse(
        workspace=_record_to_response(record),
        preview=preview_response,
        applied_patches=applied,
        rejected_patches=[],
        readiness_status=record.readiness_status,
    )


async def attach_svg_raw_analysis_to_workspace(
    db: AsyncSession,
    workspace_id: str,
    *,
    file_name: str,
    content_type: str | None,
    raw_bytes: bytes,
    current_user: UserResponse,
) -> IntakeV3SvgUploadResponse:
    """Validate SVG, run raw analysis, persist in workspace payload — no quote/order/plan writes."""
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(
            status_code=400,
            detail={"error": "workspace_archived", "workspace_id": workspace_id},
        )

    validation = validate_svg_upload(
        raw_name=file_name,
        content_type=content_type,
        raw_bytes=raw_bytes,
    )
    analysis, _ = analyze_svg_content(
        file_name=validation.file_name,
        file_size_bytes=validation.file_size_bytes,
        svg_text=validation.svg_text,
    )
    vector_asset = build_vector_asset_from_validation(validation, analysis)

    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}

    previous_file_hash = None
    previous_vector = payload.get("vector_asset")
    if isinstance(previous_vector, dict):
        previous_file_hash = previous_vector.get("file_hash")

    payload["vector_asset"] = vector_asset.model_dump(mode="json")
    payload["raw_svg_analysis"] = analysis.model_dump(mode="json")
    payload["raw_analysis_status"] = "analyzed"
    from services.intake_v3_geometry_metrics_snapshot_service import (
        build_path_geometry_summary_from_svg_text,
    )

    path_summary = build_path_geometry_summary_from_svg_text(
        validation.svg_text,
        source_file_name=validation.file_name,
    )
    if path_summary is not None:
        payload["path_geometry_summary"] = path_summary

    from services.intake_v3_svg_replace_invalidation_service import (
        invalidate_svg_dependent_workspace_state,
        should_invalidate_svg_dependent_state,
    )

    svg_source_replaced = should_invalidate_svg_dependent_state(
        {"vector_asset": previous_vector} if isinstance(previous_vector, dict) else {},
        new_file_hash=validation.file_hash,
    )

    if svg_source_replaced:
        payload, _ = invalidate_svg_dependent_workspace_state(payload)
    else:
        payload.pop("svg_dependent_state_warnings", None)

    from services.intake_v3_layer_role_confirmation_service import (
        reconcile_layer_role_confirmation_after_path_geometry_update,
    )

    payload, _ = reconcile_layer_role_confirmation_after_path_geometry_update(
        payload,
        workspace_id=workspace_id,
        path_summary=path_summary,
        svg_source_replaced=svg_source_replaced,
    )
    from services.intake_v3_geometry_metrics_snapshot_service import (
        build_and_attach_geometry_snapshot_for_workspace_payload,
    )

    payload, _ = build_and_attach_geometry_snapshot_for_workspace_payload(
        payload,
        workspace_id=workspace_id,
    )
    # Deliberately do NOT auto-confirm production model on SVG upload.
    # Dependent operator state is cleared on source replace via invalidate_svg_dependent_workspace_state.

    workspace = sanitize_intake_v3_workspace_payload(payload)
    record.payload_json = _json_dumps(workspace.model_dump(mode="json"))
    record.readiness_status = _derive_readiness_status(workspace)
    record.status = _derive_workspace_status(workspace, record.readiness_status)
    record.updated_by_user_id = current_user.id
    record.updated_at = _utcnow()
    await db.commit()
    await db.refresh(record)

    preview_response = await build_preview_for_workspace_record(db, workspace_id)

    warning_items = [
        IntakeV3SvgAnalysisWarning(code=code, message=code.replace("_", " ").title())
        for code in analysis.warnings
    ]

    return IntakeV3SvgUploadResponse(
        workspace=_record_to_response(record),
        preview=preview_response,
        raw_svg_analysis=analysis,
        warnings=warning_items,
    )


async def get_production_model_review_candidate_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3ProductionModelReviewCandidateResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}
    candidate = require_review_candidate_or_raise(payload)
    return IntakeV3ProductionModelReviewCandidateResponse(
        workspace_id=record.id,
        review_candidate=candidate,
    )


async def confirm_production_model_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3ConfirmProductionModelRequest,
    current_user: UserResponse,
) -> IntakeV3ConfirmProductionModelResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(
            status_code=400,
            detail={"error": "workspace_archived", "workspace_id": workspace_id},
        )

    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}

    updated_payload, confirmed_model, warnings = apply_confirmed_production_model_to_payload(
        payload,
        request,
        confirmed_by_user_id=current_user.id,
    )
    from services.intake_v3_geometry_metrics_snapshot_service import (
        build_and_attach_geometry_snapshot_for_workspace_payload,
    )

    updated_payload, _geometry_snapshot = build_and_attach_geometry_snapshot_for_workspace_payload(
        updated_payload,
        workspace_id=workspace_id,
    )

    workspace = sanitize_intake_v3_workspace_payload(updated_payload)
    record.payload_json = _json_dumps(workspace.model_dump(mode="json"))
    record.readiness_status = _derive_readiness_status(workspace)
    record.status = _derive_workspace_status(workspace, record.readiness_status)
    record.updated_by_user_id = current_user.id
    record.updated_at = _utcnow()
    await db.commit()
    await db.refresh(record)

    preview_response = await build_preview_for_workspace_record(db, workspace_id)
    review_candidate = build_production_model_review_candidate_from_payload(updated_payload)

    return IntakeV3ConfirmProductionModelResponse(
        workspace=_record_to_response(record),
        preview=preview_response,
        review_candidate=review_candidate,
        confirmed_production_model=confirmed_model,
        readiness_status=record.readiness_status,
        warnings=warnings,
    )


async def get_finish_assignment_targets_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3FinishAssignmentTargetsResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}
    targets = get_confirmed_letter_targets(payload)
    return IntakeV3FinishAssignmentTargetsResponse(
        workspace_id=record.id,
        targets=targets,
        letter_count=len(targets),
    )


async def get_finish_assignments_state_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3FinishAssignmentsStateResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}
    workspace = sanitize_intake_v3_workspace_payload(payload)
    summary = summarize_finish_assignments(payload)
    return IntakeV3FinishAssignmentsStateResponse(
        workspace_id=record.id,
        letter_group_finish_assignments=workspace.letter_group_finish_assignments,
        letter_finish_assignments=workspace.letter_finish_assignments,
        finish_assignment_status=workspace.finish_assignment_status,
        summary=summary,
    )


async def patch_finish_assignments_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3ApplyFinishAssignmentsRequest,
    current_user: UserResponse,
) -> IntakeV3ApplyFinishAssignmentsResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(
            status_code=400,
            detail={"error": "workspace_archived", "workspace_id": workspace_id},
        )

    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}

    validation = validate_finish_assignments(payload, request)
    updated_payload, summary = apply_finish_assignments_to_payload(payload, request)

    workspace = sanitize_intake_v3_workspace_payload(updated_payload)
    record.payload_json = _json_dumps(workspace.model_dump(mode="json"))
    record.readiness_status = _derive_readiness_status(workspace)
    record.status = _derive_workspace_status(workspace, record.readiness_status)
    record.updated_by_user_id = current_user.id
    record.updated_at = _utcnow()
    await db.commit()
    await db.refresh(record)

    preview_response = None
    if request.regenerate_preview:
        preview_response = await build_preview_for_workspace_record(db, workspace_id)

    return IntakeV3ApplyFinishAssignmentsResponse(
        workspace=_record_to_response(record),
        preview=preview_response,
        summary=summary,
        validation=validation,
    )


async def get_layer_finish_assignment_targets_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3LayerFinishAssignmentTargetsResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}
    targets = get_layer_finish_targets(payload)
    return IntakeV3LayerFinishAssignmentTargetsResponse(
        workspace_id=record.id,
        targets=targets,
        target_count=len(targets),
    )


async def get_layer_finish_assignments_state_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3LayerFinishAssignmentsStateResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}
    assignments = draft_layer_finish_assignments(payload)
    summary = summarize_layer_finish_assignments(payload)
    workspace = sanitize_intake_v3_workspace_payload(payload)
    return IntakeV3LayerFinishAssignmentsStateResponse(
        workspace_id=record.id,
        layer_finish_assignments=assignments,
        layer_finish_assignment_status=workspace.layer_finish_assignment_status,
        summary=summary,
    )


async def patch_layer_finish_assignments_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3ApplyLayerFinishAssignmentsRequest,
    current_user: UserResponse,
) -> IntakeV3ApplyLayerFinishAssignmentsResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(
            status_code=400,
            detail={"error": "workspace_archived", "workspace_id": workspace_id},
        )

    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}

    validation = validate_layer_finish_assignments(payload, request)
    updated_payload, summary = apply_layer_finish_assignments_to_payload(
        payload,
        request,
        confirmed_by=str(current_user.id),
    )

    workspace = sanitize_intake_v3_workspace_payload(updated_payload)
    record.payload_json = _json_dumps(workspace.model_dump(mode="json"))
    record.readiness_status = _derive_readiness_status(workspace)
    record.status = _derive_workspace_status(workspace, record.readiness_status)
    record.updated_by_user_id = current_user.id
    record.updated_at = _utcnow()
    await db.commit()
    await db.refresh(record)

    preview_response = None
    if request.regenerate_preview:
        preview_response = await build_preview_for_workspace_record(db, workspace_id)

    return IntakeV3ApplyLayerFinishAssignmentsResponse(
        workspace=_record_to_response(record),
        preview=preview_response,
        summary=summary,
        validation=validation,
    )


async def get_lighting_plan_state_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3LightingPlanStateResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}
    plan = draft_lighting_plan(payload)
    summary = summarize_lighting_plan(payload)
    workspace = sanitize_intake_v3_workspace_payload(payload)
    return IntakeV3LightingPlanStateResponse(
        workspace_id=record.id,
        lighting_plan=plan,
        lighting_plan_status=workspace.lighting_plan_status,
        summary=summary,
    )


async def patch_lighting_plan_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3ApplyLightingPlanRequest,
    current_user: UserResponse,
) -> IntakeV3ApplyLightingPlanResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(
            status_code=400,
            detail={"error": "workspace_archived", "workspace_id": workspace_id},
        )

    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}

    validation = validate_lighting_plan(payload, request)
    updated_payload, summary = apply_lighting_plan_to_payload(
        payload,
        request,
        confirmed_by=str(current_user.id),
    )

    workspace = sanitize_intake_v3_workspace_payload(updated_payload)
    record.payload_json = _json_dumps(workspace.model_dump(mode="json"))
    record.readiness_status = _derive_readiness_status(workspace)
    record.status = _derive_workspace_status(workspace, record.readiness_status)
    record.updated_by_user_id = current_user.id
    record.updated_at = _utcnow()
    await db.commit()
    await db.refresh(record)

    preview_response = None
    if request.regenerate_preview:
        preview_response = await build_preview_for_workspace_record(db, workspace_id)

    return IntakeV3ApplyLightingPlanResponse(
        workspace=_record_to_response(record),
        preview=preview_response,
        summary=summary,
        validation=validation,
    )


async def get_quote_readiness_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3QuoteReadinessResponse:
    """Read-only quote readiness — no preview snapshot persistence or quote creation."""
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    workspace = sanitize_intake_v3_workspace_payload(payload if isinstance(payload, dict) else {})
    archived = record.archived_at is not None

    build_result: IntakeV3PreviewBuildResult = build_intake_v3_workspace_preview(workspace)
    preview = build_result.preview

    quote_readiness = evaluate_intake_v3_quote_readiness(
        workspace,
        preview,
        workspace_title=record.title,
        workspace_archived=archived,
    )
    prequote_review = build_prequote_review(
        workspace,
        preview,
        workspace_title=record.title,
        workspace_archived=archived,
    )

    return IntakeV3QuoteReadinessResponse(
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        quote_readiness=quote_readiness,
        prequote_review=prequote_review,
    )


async def get_quote_creation_dry_run_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3QuoteCreationDryRunResponse:
    """Read-only quote creation dry-run — no quote endpoint, no DB writes."""
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    workspace = sanitize_intake_v3_workspace_payload(payload if isinstance(payload, dict) else {})
    archived = record.archived_at is not None

    build_result: IntakeV3PreviewBuildResult = build_intake_v3_workspace_preview(workspace)
    preview = build_result.preview

    dry_run = build_intake_v3_quote_creation_dry_run(
        workspace,
        preview,
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        workspace_title=record.title,
        workspace_archived=archived,
    )

    return IntakeV3QuoteCreationDryRunResponse(
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        dry_run=dry_run,
    )


async def get_quote_creation_guard_policy_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3QuoteCreationGuardPolicyResponse:
    """Read-only quote creation guard policy — no quote endpoint, no DB writes."""
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    workspace = sanitize_intake_v3_workspace_payload(payload if isinstance(payload, dict) else {})
    archived = record.archived_at is not None

    build_result: IntakeV3PreviewBuildResult = build_intake_v3_workspace_preview(workspace)
    preview = build_result.preview

    dry_run = build_intake_v3_quote_creation_dry_run(
        workspace,
        preview,
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        workspace_title=record.title,
        workspace_archived=archived,
    )
    guard_policy = evaluate_quote_creation_guard_policy(
        workspace,
        preview,
        dry_run,
        workspace_archived=archived,
    )

    return IntakeV3QuoteCreationGuardPolicyResponse(
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        guard_policy=guard_policy,
    )


async def get_commercial_quote_bridge_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3CommercialQuoteBridgeResponse:
    """Read-only commercial quote bridge preview — no quote endpoint, no DB writes."""
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    workspace = sanitize_intake_v3_workspace_payload(payload if isinstance(payload, dict) else {})
    archived = record.archived_at is not None

    build_result: IntakeV3PreviewBuildResult = build_intake_v3_workspace_preview(workspace)
    preview = build_result.preview

    bridge = build_commercial_quote_bridge_preview(
        workspace,
        preview,
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        workspace_title=record.title,
        workspace_archived=archived,
    )

    return IntakeV3CommercialQuoteBridgeResponse(
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        bridge=bridge,
    )


async def get_quote_creation_enablement_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3QuoteCreationEnablementResponse:
    """Read-only quote creation enablement + final blocker check — no quote endpoint, no DB writes."""
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    workspace = sanitize_intake_v3_workspace_payload(payload if isinstance(payload, dict) else {})
    archived = record.archived_at is not None

    build_result: IntakeV3PreviewBuildResult = build_intake_v3_workspace_preview(workspace)
    preview = build_result.preview

    dry_run = build_intake_v3_quote_creation_dry_run(
        workspace,
        preview,
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        workspace_title=record.title,
        workspace_archived=archived,
    )
    guard_policy = evaluate_quote_creation_guard_policy(
        workspace,
        preview,
        dry_run,
        workspace_archived=archived,
    )
    bridge = build_commercial_quote_bridge_preview(
        workspace,
        preview,
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        workspace_title=record.title,
        workspace_archived=archived,
    )
    final_blocker_check = evaluate_quote_creation_final_blockers(
        workspace,
        preview,
        dry_run,
        guard_policy,
        bridge,
        workspace_archived=archived,
    )
    enablement_policy = evaluate_quote_creation_enablement_policy(
        workspace,
        preview,
        dry_run=dry_run,
        guard_policy=guard_policy,
        bridge=bridge,
        final_blocker_check=final_blocker_check,
        workspace_title=record.title,
        workspace_archived=archived,
    )

    return IntakeV3QuoteCreationEnablementResponse(
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        enablement_policy=enablement_policy,
        final_blocker_check=final_blocker_check,
        dry_run_status=dry_run.dry_run_status,
        bridge_status=bridge.bridge_status,
        guard_policy_status=guard_policy.policy_status,
    )


async def get_real_quote_creation_enablement_readiness_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3RealQuoteCreationEnablementReadinessResponse:
    """Read-only real quote creation enablement readiness — no quote endpoint, no DB writes."""
    record = await _get_record_or_404(db, workspace_id)
    payload = _json_loads(record.payload_json, {})
    workspace = sanitize_intake_v3_workspace_payload(payload if isinstance(payload, dict) else {})
    archived = record.archived_at is not None

    build_result: IntakeV3PreviewBuildResult = build_intake_v3_workspace_preview(workspace)
    preview = build_result.preview

    dry_run = build_intake_v3_quote_creation_dry_run(
        workspace,
        preview,
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        workspace_title=record.title,
        workspace_archived=archived,
    )
    guard_policy = evaluate_quote_creation_guard_policy(
        workspace,
        preview,
        dry_run,
        workspace_archived=archived,
    )
    bridge = build_commercial_quote_bridge_preview(
        workspace,
        preview,
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        workspace_title=record.title,
        workspace_archived=archived,
    )
    final_blocker_check = evaluate_quote_creation_final_blockers(
        workspace,
        preview,
        dry_run,
        guard_policy,
        bridge,
        workspace_archived=archived,
    )
    enablement_policy = evaluate_quote_creation_enablement_policy(
        workspace,
        preview,
        dry_run=dry_run,
        guard_policy=guard_policy,
        bridge=bridge,
        final_blocker_check=final_blocker_check,
        workspace_title=record.title,
        workspace_archived=archived,
    )
    bundle = evaluate_real_quote_creation_enablement_readiness(
        workspace,
        preview,
        bridge,
        enablement_policy,
        final_blocker_check,
        workspace_archived=archived,
    )

    return IntakeV3RealQuoteCreationEnablementReadinessResponse(
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        owner_decision_record_policy=bundle["owner_decision_record_policy"],
        snapshot_policy=bundle["snapshot_policy"],
        anti_duplicate_policy=bundle["anti_duplicate_policy"],
        recovery_policy=bundle["recovery_policy"],
        readiness=bundle["readiness"],
        enablement_status=enablement_policy.enablement_status,
        bridge_status=bridge.bridge_status,
        guard_policy_status=guard_policy.policy_status,
    )


async def create_guarded_draft_quote_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3CreateDraftQuoteRequest,
    current_user: UserResponse,
) -> IntakeV3CreateDraftQuoteResponse:
    """Guarded draft quote creation — Quote row only, no order/execution/inventory."""
    return await create_guarded_draft_quote_from_intake_v3_workspace(
        db,
        workspace_id,
        request,
        current_user,
    )


async def get_draft_quote_review_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3DraftQuoteReview:
    """Read-only draft quote review for workspace-linked IV3 quote."""
    return await get_intake_v3_draft_quote_review_by_workspace(db, workspace_id)


async def get_draft_quote_review_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3DraftQuoteReview:
    """Read-only draft quote review by quote id."""
    return await get_intake_v3_draft_quote_review(db, quote_id)


async def get_pricing_review_state_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3PricingReviewCompletionState:
    return await get_pricing_review_completion_state_by_workspace(db, workspace_id)


async def get_pricing_review_state_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3PricingReviewCompletionState:
    return await get_pricing_review_completion_state(db, quote_id)


async def complete_pricing_review_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3CompletePricingReviewRequest,
    current_user: UserResponse,
) -> IntakeV3CompletePricingReviewResponse:
    return await complete_intake_v3_quote_pricing_review_by_workspace(
        db, workspace_id, request, current_user
    )


async def complete_pricing_review_for_quote(
    db: AsyncSession,
    quote_id: int,
    request: IntakeV3CompletePricingReviewRequest,
    current_user: UserResponse,
) -> IntakeV3CompletePricingReviewResponse:
    return await complete_intake_v3_quote_pricing_review(db, quote_id, request, current_user)


async def get_accept_convert_readiness_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3PricedDraftAcceptConvertReadiness:
    from services.intake_v3_priced_draft_accept_convert_readiness_service import (
        get_iv3_priced_draft_accept_convert_readiness_by_workspace,
    )

    return await get_iv3_priced_draft_accept_convert_readiness_by_workspace(db, workspace_id)


async def get_accept_convert_readiness_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3PricedDraftAcceptConvertReadiness:
    from services.intake_v3_priced_draft_accept_convert_readiness_service import (
        get_iv3_priced_draft_accept_convert_readiness,
    )

    return await get_iv3_priced_draft_accept_convert_readiness(db, quote_id)


async def get_accept_state_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3AcceptState:
    from services.intake_v3_guarded_accept_flow_service import get_iv3_accept_state_by_workspace

    return await get_iv3_accept_state_by_workspace(db, workspace_id)


async def get_accept_state_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3AcceptState:
    from services.intake_v3_guarded_accept_flow_service import get_iv3_accept_state

    return await get_iv3_accept_state(db, quote_id)


async def accept_iv3_priced_draft_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3AcceptQuoteRequest,
    current_user: UserResponse,
) -> IntakeV3AcceptQuoteResponse:
    from services.intake_v3_guarded_accept_flow_service import accept_iv3_priced_draft_quote_by_workspace

    return await accept_iv3_priced_draft_quote_by_workspace(db, workspace_id, request, current_user)


async def accept_iv3_priced_draft_for_quote(
    db: AsyncSession,
    quote_id: int,
    request: IntakeV3AcceptQuoteRequest,
    current_user: UserResponse,
) -> IntakeV3AcceptQuoteResponse:
    from services.intake_v3_guarded_accept_flow_service import accept_iv3_priced_draft_quote

    return await accept_iv3_priced_draft_quote(db, quote_id, request, current_user)


async def get_convert_to_order_state_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3ConvertToOrderState:
    from services.intake_v3_guarded_convert_to_order_service import get_iv3_convert_to_order_state_by_workspace

    return await get_iv3_convert_to_order_state_by_workspace(db, workspace_id)


async def get_convert_to_order_state_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3ConvertToOrderState:
    from services.intake_v3_guarded_convert_to_order_service import get_iv3_convert_to_order_state

    return await get_iv3_convert_to_order_state(db, quote_id)


async def convert_iv3_accepted_quote_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3ConvertToOrderRequest,
    current_user: UserResponse,
) -> IntakeV3ConvertToOrderResponse:
    from services.intake_v3_guarded_convert_to_order_service import convert_iv3_accepted_quote_to_order_by_workspace

    return await convert_iv3_accepted_quote_to_order_by_workspace(db, workspace_id, request, current_user)


async def convert_iv3_accepted_quote_for_quote(
    db: AsyncSession,
    quote_id: int,
    request: IntakeV3ConvertToOrderRequest,
    current_user: UserResponse,
) -> IntakeV3ConvertToOrderResponse:
    from services.intake_v3_guarded_convert_to_order_service import convert_iv3_accepted_quote_to_order

    return await convert_iv3_accepted_quote_to_order(db, quote_id, request, current_user)


async def get_order_production_readiness_for_order(
    db: AsyncSession,
    order_id: int,
):
    from services.intake_v3_order_production_readiness_service import get_iv3_order_production_readiness

    return await get_iv3_order_production_readiness(db, order_id)


async def get_order_production_readiness_for_quote(
    db: AsyncSession,
    quote_id: int,
):
    from services.intake_v3_order_production_readiness_service import (
        get_iv3_order_production_readiness_by_quote,
    )

    return await get_iv3_order_production_readiness_by_quote(db, quote_id)


async def get_order_production_readiness_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v3_order_production_readiness_service import (
        get_iv3_order_production_readiness_by_workspace,
    )

    return await get_iv3_order_production_readiness_by_workspace(db, workspace_id)


async def get_material_breakdown_for_order(
    db: AsyncSession,
    order_id: int,
):
    from services.intake_v3_material_quantity_breakdown_service import (
        get_intake_v3_material_quantity_breakdown_for_order,
    )

    return await get_intake_v3_material_quantity_breakdown_for_order(db, order_id)


async def get_material_breakdown_for_quote(
    db: AsyncSession,
    quote_id: int,
):
    from services.intake_v3_material_quantity_breakdown_service import (
        get_intake_v3_material_quantity_breakdown_for_quote,
    )

    return await get_intake_v3_material_quantity_breakdown_for_quote(db, quote_id)


async def get_material_breakdown_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v3_material_quantity_breakdown_service import (
        get_intake_v3_material_quantity_breakdown_for_workspace,
    )

    return await get_intake_v3_material_quantity_breakdown_for_workspace(db, workspace_id)


async def get_material_availability_for_order(
    db: AsyncSession,
    order_id: int,
):
    from services.intake_v3_material_availability_service import (
        get_material_availability_for_order as _get,
    )

    return await _get(db, order_id)


async def get_material_availability_for_quote(
    db: AsyncSession,
    quote_id: int,
):
    from services.intake_v3_material_availability_service import (
        get_material_availability_for_quote as _get,
    )

    return await _get(db, quote_id)


async def get_material_availability_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v3_material_availability_service import (
        get_material_availability_for_workspace as _get,
    )

    return await _get(db, workspace_id)


async def get_procurement_preview_for_order(
    db: AsyncSession,
    order_id: int,
):
    from services.intake_v3_procurement_preview_service import (
        get_procurement_preview_for_order as _get,
    )

    return await _get(db, order_id)


async def get_procurement_preview_for_quote(
    db: AsyncSession,
    quote_id: int,
):
    from services.intake_v3_procurement_preview_service import (
        get_procurement_preview_for_quote as _get,
    )

    return await _get(db, quote_id)


async def get_procurement_preview_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v3_procurement_preview_service import (
        get_procurement_preview_for_workspace as _get,
    )

    return await _get(db, workspace_id)


async def get_production_task_dry_run_for_order(
    db: AsyncSession,
    order_id: int,
):
    from services.intake_v3_production_task_dry_run_service import (
        get_iv3_production_task_dry_run_for_order,
    )

    return await get_iv3_production_task_dry_run_for_order(db, order_id)


async def get_production_task_dry_run_for_quote(
    db: AsyncSession,
    quote_id: int,
):
    from services.intake_v3_production_task_dry_run_service import (
        get_iv3_production_task_dry_run_for_quote,
    )

    return await get_iv3_production_task_dry_run_for_quote(db, quote_id)


async def get_production_task_dry_run_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v3_production_task_dry_run_service import (
        get_iv3_production_task_dry_run_for_workspace,
    )

    return await get_iv3_production_task_dry_run_for_workspace(db, workspace_id)


async def get_geometry_metrics_snapshot_for_order(
    db: AsyncSession,
    order_id: int,
):
    from services.intake_v3_geometry_metrics_snapshot_service import (
        get_geometry_metrics_snapshot_for_order as _get,
    )

    return await _get(db, order_id)


async def get_geometry_metrics_snapshot_for_quote(
    db: AsyncSession,
    quote_id: int,
):
    from services.intake_v3_geometry_metrics_snapshot_service import (
        get_geometry_metrics_snapshot_for_quote as _get,
    )

    return await _get(db, quote_id)


async def get_geometry_metrics_snapshot_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v3_geometry_metrics_snapshot_service import (
        get_geometry_metrics_snapshot_for_workspace as _get,
    )

    return await _get(db, workspace_id)


async def get_path_perimeter_classification_for_order(
    db: AsyncSession,
    order_id: int,
):
    from services.intake_v3_geometry_path_perimeter_classification_service import (
        get_path_perimeter_classification_for_order as _get,
    )

    return await _get(db, order_id)


async def get_path_perimeter_classification_for_quote(
    db: AsyncSession,
    quote_id: int,
):
    from services.intake_v3_geometry_path_perimeter_classification_service import (
        get_path_perimeter_classification_for_quote as _get,
    )

    return await _get(db, quote_id)


async def get_path_perimeter_classification_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v3_geometry_path_perimeter_classification_service import (
        get_path_perimeter_classification_for_workspace as _get,
    )

    return await _get(db, workspace_id)


async def get_layer_role_confirmation_for_order(
    db: AsyncSession,
    order_id: int,
):
    from services.intake_v3_layer_role_confirmation_service import (
        get_layer_role_confirmation_for_order as _get,
    )

    return await _get(db, order_id)


async def get_layer_role_confirmation_for_quote(
    db: AsyncSession,
    quote_id: int,
):
    from services.intake_v3_layer_role_confirmation_service import (
        get_layer_role_confirmation_for_quote as _get,
    )

    return await _get(db, quote_id)


async def get_layer_role_confirmation_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v3_layer_role_confirmation_service import (
        get_layer_role_confirmation_for_workspace as _get,
    )

    return await _get(db, workspace_id)


async def get_layer_role_propagation_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v3_layer_role_confirmation_propagation_service import (
        get_layer_role_confirmation_propagation_for_workspace as _get,
    )

    return await _get(db, workspace_id)


async def get_layer_role_propagation_for_quote(
    db: AsyncSession,
    quote_id: int,
):
    from services.intake_v3_layer_role_confirmation_propagation_service import (
        get_layer_role_confirmation_propagation_for_quote as _get,
    )

    return await _get(db, quote_id)


async def get_layer_role_propagation_for_order(
    db: AsyncSession,
    order_id: int,
):
    from services.intake_v3_layer_role_confirmation_propagation_service import (
        get_layer_role_confirmation_propagation_for_order as _get,
    )

    return await _get(db, order_id)


async def refresh_quote_layer_role_technical_snapshot(
    db: AsyncSession,
    quote_id: int,
):
    from services.intake_v3_layer_role_confirmation_propagation_service import (
        refresh_quote_iv3_technical_snapshots_from_workspace as _refresh,
    )

    return await _refresh(db, quote_id)


async def save_layer_role_confirmation_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request,
    current_user_id: str | None,
):
    from services.intake_v3_layer_role_confirmation_service import (
        save_layer_role_confirmation_for_workspace as _save,
    )

    return await _save(db, workspace_id, request, current_user_id)
