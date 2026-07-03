"""Intake V3 workspace draft persistence HTTP surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
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
    IntakeV3EditableFieldsResponse,
    IntakeV3FinishAssignmentTargetsResponse,
    IntakeV3FinishAssignmentsStateResponse,
    IntakeV3LayerFinishAssignmentTargetsResponse,
    IntakeV3LayerFinishAssignmentsStateResponse,
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
    IntakeV3OrderProductionReadinessResponse,
    IntakeV3MaterialBreakdownResponse,
    IntakeV3MaterialAvailabilityResponse,
    IntakeV3ProcurementPreviewResponse,
    IntakeV3ProductionTaskDryRunResponse,
    IntakeV3GeometryMetricsSnapshotResponse,
    IntakeV3LayerRoleConfirmationResponse,
    IntakeV3LayerRoleConfirmationUpdateRequest,
    IntakeV3LayerRoleConfirmationPropagationResponse,
    IntakeV3LayerRoleTechnicalSnapshotRefreshResponse,
    IntakeV3PathPerimeterClassificationResponse,
    IntakeV3SvgUploadResponse,
    IntakeV3WorkspaceCreateRequest,
    IntakeV3WorkspaceFieldPatchRequest,
    IntakeV3WorkspaceFieldPatchResponse,
    IntakeV3WorkspaceListResponse,
    IntakeV3WorkspacePreviewResponse,
    IntakeV3WorkspaceResponse,
    IntakeV3WorkspaceSeedFromScenarioRequest,
    IntakeV3WorkspaceUpdateRequest,
)
from services.intake_v3_workspace_field_editor_service import get_editable_fields_metadata
from services.intake_v3_workspace_service import (
    archive_intake_v3_workspace,
    attach_svg_raw_analysis_to_workspace,
    build_preview_for_workspace_record,
    confirm_production_model_for_workspace,
    create_intake_v3_workspace,
    get_finish_assignment_targets_for_workspace,
    get_finish_assignments_state_for_workspace,
    get_layer_finish_assignment_targets_for_workspace,
    get_layer_finish_assignments_state_for_workspace,
    get_intake_v3_workspace,
    get_production_model_review_candidate_for_workspace,
    get_quote_readiness_for_workspace,
    get_quote_creation_dry_run_for_workspace,
    get_quote_creation_guard_policy_for_workspace,
    get_commercial_quote_bridge_for_workspace,
    get_quote_creation_enablement_for_workspace,
    get_real_quote_creation_enablement_readiness_for_workspace,
    create_guarded_draft_quote_for_workspace,
    get_draft_quote_review_for_workspace,
    get_draft_quote_review_for_quote,
    get_pricing_review_state_for_workspace,
    get_pricing_review_state_for_quote,
    complete_pricing_review_for_workspace,
    complete_pricing_review_for_quote,
    get_accept_convert_readiness_for_workspace,
    get_accept_convert_readiness_for_quote,
    get_accept_state_for_workspace,
    get_accept_state_for_quote,
    accept_iv3_priced_draft_for_workspace,
    accept_iv3_priced_draft_for_quote,
    get_convert_to_order_state_for_workspace,
    get_convert_to_order_state_for_quote,
    convert_iv3_accepted_quote_for_workspace,
    convert_iv3_accepted_quote_for_quote,
    get_order_production_readiness_for_order,
    get_order_production_readiness_for_quote,
    get_order_production_readiness_for_workspace,
    get_material_breakdown_for_order,
    get_material_breakdown_for_quote,
    get_material_breakdown_for_workspace,
    get_material_availability_for_order,
    get_material_availability_for_quote,
    get_material_availability_for_workspace,
    get_procurement_preview_for_order,
    get_procurement_preview_for_quote,
    get_procurement_preview_for_workspace,
    get_production_task_dry_run_for_order,
    get_production_task_dry_run_for_quote,
    get_production_task_dry_run_for_workspace,
    get_geometry_metrics_snapshot_for_order,
    get_geometry_metrics_snapshot_for_quote,
    get_geometry_metrics_snapshot_for_workspace,
    get_path_perimeter_classification_for_order,
    get_path_perimeter_classification_for_quote,
    get_path_perimeter_classification_for_workspace,
    get_layer_role_confirmation_for_order,
    get_layer_role_confirmation_for_quote,
    get_layer_role_confirmation_for_workspace,
    save_layer_role_confirmation_for_workspace,
    get_layer_role_propagation_for_order,
    get_layer_role_propagation_for_quote,
    get_layer_role_propagation_for_workspace,
    refresh_quote_layer_role_technical_snapshot,
    list_intake_v3_workspaces,
    patch_finish_assignments_for_workspace,
    patch_layer_finish_assignments_for_workspace,
    patch_lighting_plan_for_workspace,
    get_lighting_plan_state_for_workspace,
    patch_intake_v3_workspace_fields,
    seed_workspace_from_preview_scenario,
    update_intake_v3_workspace,
)

# DEPRECATED: V3 workspace endpoints superseded by V4. Router disabled from auto-discovery.
# V3 services are still imported by V4 as shared libraries — do not delete this file.
_deprecated_router = APIRouter(
    prefix="/api/v1/intake-v3",
    tags=["intake-v3-workspaces"],
    dependencies=[Depends(get_current_user)],
)


@_deprecated_router.get("/workspaces", response_model=IntakeV3WorkspaceListResponse)
async def list_workspaces(
    include_archived: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> IntakeV3WorkspaceListResponse:
    return await list_intake_v3_workspaces(db, include_archived=include_archived)


@_deprecated_router.get("/workspaces/editable-fields", response_model=IntakeV3EditableFieldsResponse)
async def get_editable_fields() -> IntakeV3EditableFieldsResponse:
    return get_editable_fields_metadata()


@_deprecated_router.post("/workspaces", response_model=IntakeV3WorkspaceResponse, status_code=201)
async def create_workspace(
    request: IntakeV3WorkspaceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3WorkspaceResponse:
    return await create_intake_v3_workspace(db, request, current_user)


@_deprecated_router.get("/workspaces/{workspace_id}", response_model=IntakeV3WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3WorkspaceResponse:
    return await get_intake_v3_workspace(db, workspace_id)


@_deprecated_router.patch("/workspaces/{workspace_id}", response_model=IntakeV3WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    request: IntakeV3WorkspaceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3WorkspaceResponse:
    return await update_intake_v3_workspace(db, workspace_id, request, current_user)


@_deprecated_router.patch(
    "/workspaces/{workspace_id}/fields",
    response_model=IntakeV3WorkspaceFieldPatchResponse,
)
async def patch_workspace_fields(
    workspace_id: str,
    request: IntakeV3WorkspaceFieldPatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3WorkspaceFieldPatchResponse:
    return await patch_intake_v3_workspace_fields(db, workspace_id, request, current_user)


@_deprecated_router.post("/workspaces/{workspace_id}/archive", response_model=IntakeV3WorkspaceResponse)
async def archive_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3WorkspaceResponse:
    return await archive_intake_v3_workspace(db, workspace_id, current_user)


@_deprecated_router.get("/workspaces/{workspace_id}/preview", response_model=IntakeV3WorkspacePreviewResponse)
async def get_workspace_preview(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3WorkspacePreviewResponse:
    return await build_preview_for_workspace_record(db, workspace_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/quote-readiness",
    response_model=IntakeV3QuoteReadinessResponse,
)
async def get_workspace_quote_readiness(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3QuoteReadinessResponse:
    return await get_quote_readiness_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/quote-creation-dry-run",
    response_model=IntakeV3QuoteCreationDryRunResponse,
)
async def get_workspace_quote_creation_dry_run(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3QuoteCreationDryRunResponse:
    return await get_quote_creation_dry_run_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/quote-creation-guard-policy",
    response_model=IntakeV3QuoteCreationGuardPolicyResponse,
)
async def get_workspace_quote_creation_guard_policy(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3QuoteCreationGuardPolicyResponse:
    return await get_quote_creation_guard_policy_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/commercial-quote-bridge",
    response_model=IntakeV3CommercialQuoteBridgeResponse,
)
async def get_workspace_commercial_quote_bridge(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3CommercialQuoteBridgeResponse:
    return await get_commercial_quote_bridge_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/quote-creation-enablement",
    response_model=IntakeV3QuoteCreationEnablementResponse,
)
async def get_workspace_quote_creation_enablement(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3QuoteCreationEnablementResponse:
    return await get_quote_creation_enablement_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/real-quote-creation-enablement-readiness",
    response_model=IntakeV3RealQuoteCreationEnablementReadinessResponse,
)
async def get_workspace_real_quote_creation_enablement_readiness(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3RealQuoteCreationEnablementReadinessResponse:
    return await get_real_quote_creation_enablement_readiness_for_workspace(db, workspace_id)


@_deprecated_router.post(
    "/workspaces/{workspace_id}/create-draft-quote",
    response_model=IntakeV3CreateDraftQuoteResponse,
    status_code=201,
)
async def create_workspace_guarded_draft_quote(
    workspace_id: str,
    request: IntakeV3CreateDraftQuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3CreateDraftQuoteResponse:
    return await create_guarded_draft_quote_for_workspace(db, workspace_id, request, current_user)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/draft-quote-review",
    response_model=IntakeV3DraftQuoteReview,
)
async def get_workspace_draft_quote_review(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3DraftQuoteReview:
    return await get_draft_quote_review_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/draft-review",
    response_model=IntakeV3DraftQuoteReview,
)
async def get_quote_draft_review(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3DraftQuoteReview:
    return await get_draft_quote_review_for_quote(db, quote_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/pricing-review-state",
    response_model=IntakeV3PricingReviewCompletionState,
)
async def get_quote_pricing_review_state(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3PricingReviewCompletionState:
    return await get_pricing_review_state_for_quote(db, quote_id)


@_deprecated_router.post(
    "/quotes/{quote_id}/complete-pricing-review",
    response_model=IntakeV3CompletePricingReviewResponse,
)
async def complete_quote_pricing_review(
    quote_id: int,
    request: IntakeV3CompletePricingReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3CompletePricingReviewResponse:
    return await complete_pricing_review_for_quote(db, quote_id, request, current_user)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/pricing-review-state",
    response_model=IntakeV3PricingReviewCompletionState,
)
async def get_workspace_pricing_review_state(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3PricingReviewCompletionState:
    return await get_pricing_review_state_for_workspace(db, workspace_id)


@_deprecated_router.post(
    "/workspaces/{workspace_id}/complete-pricing-review",
    response_model=IntakeV3CompletePricingReviewResponse,
)
async def complete_workspace_pricing_review(
    workspace_id: str,
    request: IntakeV3CompletePricingReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3CompletePricingReviewResponse:
    return await complete_pricing_review_for_workspace(db, workspace_id, request, current_user)


@_deprecated_router.get(
    "/quotes/{quote_id}/accept-convert-readiness",
    response_model=IntakeV3PricedDraftAcceptConvertReadiness,
)
async def get_quote_accept_convert_readiness(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3PricedDraftAcceptConvertReadiness:
    return await get_accept_convert_readiness_for_quote(db, quote_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/accept-convert-readiness",
    response_model=IntakeV3PricedDraftAcceptConvertReadiness,
)
async def get_workspace_accept_convert_readiness(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3PricedDraftAcceptConvertReadiness:
    return await get_accept_convert_readiness_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/accept-state",
    response_model=IntakeV3AcceptState,
)
async def get_quote_accept_state(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3AcceptState:
    return await get_accept_state_for_quote(db, quote_id)


@_deprecated_router.post(
    "/quotes/{quote_id}/accept",
    response_model=IntakeV3AcceptQuoteResponse,
)
async def accept_quote_guarded(
    quote_id: int,
    request: IntakeV3AcceptQuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3AcceptQuoteResponse:
    return await accept_iv3_priced_draft_for_quote(db, quote_id, request, current_user)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/accept-state",
    response_model=IntakeV3AcceptState,
)
async def get_workspace_accept_state(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3AcceptState:
    return await get_accept_state_for_workspace(db, workspace_id)


@_deprecated_router.post(
    "/workspaces/{workspace_id}/accept",
    response_model=IntakeV3AcceptQuoteResponse,
)
async def accept_workspace_guarded(
    workspace_id: str,
    request: IntakeV3AcceptQuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3AcceptQuoteResponse:
    return await accept_iv3_priced_draft_for_workspace(db, workspace_id, request, current_user)


@_deprecated_router.get(
    "/quotes/{quote_id}/convert-to-order-state",
    response_model=IntakeV3ConvertToOrderState,
)
async def get_quote_convert_to_order_state(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ConvertToOrderState:
    return await get_convert_to_order_state_for_quote(db, quote_id)


@_deprecated_router.post(
    "/quotes/{quote_id}/convert-to-order",
    response_model=IntakeV3ConvertToOrderResponse,
)
async def convert_quote_to_order_guarded(
    quote_id: int,
    request: IntakeV3ConvertToOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3ConvertToOrderResponse:
    return await convert_iv3_accepted_quote_for_quote(db, quote_id, request, current_user)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/convert-to-order-state",
    response_model=IntakeV3ConvertToOrderState,
)
async def get_workspace_convert_to_order_state(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ConvertToOrderState:
    return await get_convert_to_order_state_for_workspace(db, workspace_id)


@_deprecated_router.post(
    "/workspaces/{workspace_id}/convert-to-order",
    response_model=IntakeV3ConvertToOrderResponse,
)
async def convert_workspace_to_order_guarded(
    workspace_id: str,
    request: IntakeV3ConvertToOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3ConvertToOrderResponse:
    return await convert_iv3_accepted_quote_for_workspace(db, workspace_id, request, current_user)


@_deprecated_router.get(
    "/orders/{order_id}/production-readiness",
    response_model=IntakeV3OrderProductionReadinessResponse,
)
async def get_order_production_readiness(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3OrderProductionReadinessResponse:
    return await get_order_production_readiness_for_order(db, order_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/order-production-readiness",
    response_model=IntakeV3OrderProductionReadinessResponse,
)
async def get_quote_order_production_readiness(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3OrderProductionReadinessResponse:
    return await get_order_production_readiness_for_quote(db, quote_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/order-production-readiness",
    response_model=IntakeV3OrderProductionReadinessResponse,
)
async def get_workspace_order_production_readiness(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3OrderProductionReadinessResponse:
    return await get_order_production_readiness_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/orders/{order_id}/material-breakdown",
    response_model=IntakeV3MaterialBreakdownResponse,
)
async def get_order_material_breakdown(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3MaterialBreakdownResponse:
    return await get_material_breakdown_for_order(db, order_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/material-breakdown",
    response_model=IntakeV3MaterialBreakdownResponse,
)
async def get_quote_material_breakdown(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3MaterialBreakdownResponse:
    return await get_material_breakdown_for_quote(db, quote_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/material-breakdown",
    response_model=IntakeV3MaterialBreakdownResponse,
)
async def get_workspace_material_breakdown(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3MaterialBreakdownResponse:
    return await get_material_breakdown_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/orders/{order_id}/material-availability",
    response_model=IntakeV3MaterialAvailabilityResponse,
)
async def get_order_material_availability(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3MaterialAvailabilityResponse:
    return await get_material_availability_for_order(db, order_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/material-availability",
    response_model=IntakeV3MaterialAvailabilityResponse,
)
async def get_quote_material_availability(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3MaterialAvailabilityResponse:
    return await get_material_availability_for_quote(db, quote_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/material-availability",
    response_model=IntakeV3MaterialAvailabilityResponse,
)
async def get_workspace_material_availability(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3MaterialAvailabilityResponse:
    return await get_material_availability_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/orders/{order_id}/procurement-preview",
    response_model=IntakeV3ProcurementPreviewResponse,
)
async def get_order_procurement_preview(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ProcurementPreviewResponse:
    return await get_procurement_preview_for_order(db, order_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/procurement-preview",
    response_model=IntakeV3ProcurementPreviewResponse,
)
async def get_quote_procurement_preview(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ProcurementPreviewResponse:
    return await get_procurement_preview_for_quote(db, quote_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/procurement-preview",
    response_model=IntakeV3ProcurementPreviewResponse,
)
async def get_workspace_procurement_preview(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ProcurementPreviewResponse:
    return await get_procurement_preview_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/orders/{order_id}/production-task-dry-run",
    response_model=IntakeV3ProductionTaskDryRunResponse,
)
async def get_order_production_task_dry_run(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ProductionTaskDryRunResponse:
    return await get_production_task_dry_run_for_order(db, order_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/production-task-dry-run",
    response_model=IntakeV3ProductionTaskDryRunResponse,
)
async def get_quote_production_task_dry_run(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ProductionTaskDryRunResponse:
    return await get_production_task_dry_run_for_quote(db, quote_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/production-task-dry-run",
    response_model=IntakeV3ProductionTaskDryRunResponse,
)
async def get_workspace_production_task_dry_run(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ProductionTaskDryRunResponse:
    return await get_production_task_dry_run_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/orders/{order_id}/geometry-metrics-snapshot",
    response_model=IntakeV3GeometryMetricsSnapshotResponse,
)
async def get_order_geometry_metrics_snapshot(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3GeometryMetricsSnapshotResponse:
    return await get_geometry_metrics_snapshot_for_order(db, order_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/geometry-metrics-snapshot",
    response_model=IntakeV3GeometryMetricsSnapshotResponse,
)
async def get_quote_geometry_metrics_snapshot(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3GeometryMetricsSnapshotResponse:
    return await get_geometry_metrics_snapshot_for_quote(db, quote_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/geometry-metrics-snapshot",
    response_model=IntakeV3GeometryMetricsSnapshotResponse,
)
async def get_workspace_geometry_metrics_snapshot(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3GeometryMetricsSnapshotResponse:
    return await get_geometry_metrics_snapshot_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/orders/{order_id}/geometry-path-perimeter-classification",
    response_model=IntakeV3PathPerimeterClassificationResponse,
)
async def get_order_geometry_path_perimeter_classification(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3PathPerimeterClassificationResponse:
    return await get_path_perimeter_classification_for_order(db, order_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/geometry-path-perimeter-classification",
    response_model=IntakeV3PathPerimeterClassificationResponse,
)
async def get_quote_geometry_path_perimeter_classification(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3PathPerimeterClassificationResponse:
    return await get_path_perimeter_classification_for_quote(db, quote_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/geometry-path-perimeter-classification",
    response_model=IntakeV3PathPerimeterClassificationResponse,
)
async def get_workspace_geometry_path_perimeter_classification(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3PathPerimeterClassificationResponse:
    return await get_path_perimeter_classification_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/layer-role-confirmation",
    response_model=IntakeV3LayerRoleConfirmationResponse,
)
async def get_workspace_layer_role_confirmation(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3LayerRoleConfirmationResponse:
    return await get_layer_role_confirmation_for_workspace(db, workspace_id)


@_deprecated_router.put(
    "/workspaces/{workspace_id}/layer-role-confirmation",
    response_model=IntakeV3LayerRoleConfirmationResponse,
)
async def save_workspace_layer_role_confirmation(
    workspace_id: str,
    request: IntakeV3LayerRoleConfirmationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3LayerRoleConfirmationResponse:
    return await save_layer_role_confirmation_for_workspace(
        db,
        workspace_id,
        request,
        current_user.id,
    )


@_deprecated_router.get(
    "/quotes/{quote_id}/layer-role-confirmation",
    response_model=IntakeV3LayerRoleConfirmationResponse,
)
async def get_quote_layer_role_confirmation(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3LayerRoleConfirmationResponse:
    return await get_layer_role_confirmation_for_quote(db, quote_id)


@_deprecated_router.get(
    "/orders/{order_id}/layer-role-confirmation",
    response_model=IntakeV3LayerRoleConfirmationResponse,
)
async def get_order_layer_role_confirmation(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3LayerRoleConfirmationResponse:
    return await get_layer_role_confirmation_for_order(db, order_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/layer-role-confirmation/propagation",
    response_model=IntakeV3LayerRoleConfirmationPropagationResponse,
)
async def get_workspace_layer_role_propagation(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3LayerRoleConfirmationPropagationResponse:
    return await get_layer_role_propagation_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/quotes/{quote_id}/layer-role-confirmation/propagation",
    response_model=IntakeV3LayerRoleConfirmationPropagationResponse,
)
async def get_quote_layer_role_propagation(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3LayerRoleConfirmationPropagationResponse:
    return await get_layer_role_propagation_for_quote(db, quote_id)


@_deprecated_router.get(
    "/orders/{order_id}/layer-role-confirmation/propagation",
    response_model=IntakeV3LayerRoleConfirmationPropagationResponse,
)
async def get_order_layer_role_propagation(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3LayerRoleConfirmationPropagationResponse:
    return await get_layer_role_propagation_for_order(db, order_id)


@_deprecated_router.post(
    "/quotes/{quote_id}/layer-role-confirmation/refresh-technical-snapshot",
    response_model=IntakeV3LayerRoleTechnicalSnapshotRefreshResponse,
)
async def refresh_quote_layer_role_technical_snapshot_endpoint(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3LayerRoleTechnicalSnapshotRefreshResponse:
    return await refresh_quote_layer_role_technical_snapshot(db, quote_id)


@_deprecated_router.post("/workspaces/seed-from-scenario", response_model=IntakeV3WorkspaceResponse, status_code=201)
async def seed_workspace_from_scenario(
    request: IntakeV3WorkspaceSeedFromScenarioRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3WorkspaceResponse:
    return await seed_workspace_from_preview_scenario(db, request, current_user)


@_deprecated_router.post(
    "/workspaces/{workspace_id}/svg",
    response_model=IntakeV3SvgUploadResponse,
)
async def upload_workspace_svg(
    workspace_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3SvgUploadResponse:
    raw_bytes = await file.read()
    return await attach_svg_raw_analysis_to_workspace(
        db,
        workspace_id,
        file_name=file.filename or "upload.svg",
        content_type=file.content_type,
        raw_bytes=raw_bytes,
        current_user=current_user,
    )


@_deprecated_router.get(
    "/workspaces/{workspace_id}/production-model/review-candidate",
    response_model=IntakeV3ProductionModelReviewCandidateResponse,
)
async def get_production_model_review_candidate(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ProductionModelReviewCandidateResponse:
    return await get_production_model_review_candidate_for_workspace(db, workspace_id)


@_deprecated_router.post(
    "/workspaces/{workspace_id}/production-model/confirm",
    response_model=IntakeV3ConfirmProductionModelResponse,
)
async def confirm_production_model(
    workspace_id: str,
    request: IntakeV3ConfirmProductionModelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3ConfirmProductionModelResponse:
    return await confirm_production_model_for_workspace(db, workspace_id, request, current_user)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/finish-assignments/targets",
    response_model=IntakeV3FinishAssignmentTargetsResponse,
)
async def get_finish_assignment_targets(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3FinishAssignmentTargetsResponse:
    return await get_finish_assignment_targets_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/finish-assignments",
    response_model=IntakeV3FinishAssignmentsStateResponse,
)
async def get_finish_assignments(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3FinishAssignmentsStateResponse:
    return await get_finish_assignments_state_for_workspace(db, workspace_id)


@_deprecated_router.patch(
    "/workspaces/{workspace_id}/finish-assignments",
    response_model=IntakeV3ApplyFinishAssignmentsResponse,
)
async def patch_finish_assignments(
    workspace_id: str,
    request: IntakeV3ApplyFinishAssignmentsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3ApplyFinishAssignmentsResponse:
    return await patch_finish_assignments_for_workspace(db, workspace_id, request, current_user)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/layer-finish-assignments/targets",
    response_model=IntakeV3LayerFinishAssignmentTargetsResponse,
)
async def get_layer_finish_assignment_targets(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3LayerFinishAssignmentTargetsResponse:
    return await get_layer_finish_assignment_targets_for_workspace(db, workspace_id)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/layer-finish-assignments",
    response_model=IntakeV3LayerFinishAssignmentsStateResponse,
)
async def get_layer_finish_assignments(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3LayerFinishAssignmentsStateResponse:
    return await get_layer_finish_assignments_state_for_workspace(db, workspace_id)


@_deprecated_router.patch(
    "/workspaces/{workspace_id}/layer-finish-assignments",
    response_model=IntakeV3ApplyLayerFinishAssignmentsResponse,
)
async def patch_layer_finish_assignments(
    workspace_id: str,
    request: IntakeV3ApplyLayerFinishAssignmentsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3ApplyLayerFinishAssignmentsResponse:
    return await patch_layer_finish_assignments_for_workspace(db, workspace_id, request, current_user)


@_deprecated_router.get(
    "/workspaces/{workspace_id}/lighting-plan",
    response_model=IntakeV3LightingPlanStateResponse,
)
async def get_lighting_plan(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3LightingPlanStateResponse:
    return await get_lighting_plan_state_for_workspace(db, workspace_id)


@_deprecated_router.patch(
    "/workspaces/{workspace_id}/lighting-plan",
    response_model=IntakeV3ApplyLightingPlanResponse,
)
async def patch_lighting_plan(
    workspace_id: str,
    request: IntakeV3ApplyLightingPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV3ApplyLightingPlanResponse:
    return await patch_lighting_plan_for_workspace(db, workspace_id, request, current_user)
