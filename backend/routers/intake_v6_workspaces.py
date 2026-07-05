"""Intake V6 HTTP surface."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.auth import UserResponse
from schemas.intake_v3 import IntakeV3ProductionTaskDryRunResponse
from schemas.intake_v6 import (
    IntakeV6AcceptQuoteRequest,
    IntakeV6AiInformationalAssistPreviewResponse,
    IntakeV6AiSemanticClassificationPreviewResponse,
    IntakeV6AnalysisBundleRequest,
    IntakeV6CommercialSpineStateResponse,
    IntakeV6CompletePricingReviewRequest,
    IntakeV6ConvertToOrderRequest,
    IntakeV6CreateDraftQuoteRequest,
    IntakeV6CreateDraftQuoteResponse,
    IntakeV6FaceBackPrepCostDraftResponse,
    IntakeV6FinishSetup,
    IntakeV6InternalDraftQuoteConfirmationRequest,
    IntakeV6LayerRoleUpdateRequest,
    IntakeV6MaterialBreakdownResponse,
    IntakeV6NestingPreviewResponse,
    IntakeV6OrderBoundTaskReadinessResponse,
    IntakeV6OfferHandoffRequest,
    IntakeV6OwnerApprovalRequest,
    IntakeV6PricedQuoteWriteRequest,
    IntakeV6PricingInputPreviewResponse,
    IntakeV6ProductCompositionConfirmationRequest,
    IntakeV6ProductionHandoffPreviewResponse,
    IntakeV6ProductSystemBindingResponse,
    IntakeV6QuoteHandoffPreviewResponse,
    IntakeV6QuoteSnapshotV2CreateRequest,
    IntakeV6ReanalyzePreviewRequest,
    IntakeV6ReanalyzePreviewResponse,
    IntakeV6SheetFootprintOverrideRequest,
    IntakeV6SheetFootprintOverrideResponse,
    IntakeV6SvgUploadResponse,
    IntakeV6TaskGenerationDryRunResponse,
    IntakeV6TaskPreviewResponse,
    IntakeV6TemplateFormContractResponse,
    IntakeV6EnsureWorkspaceForIntakeRequestBody,
    IntakeV6WorkspaceCreateRequest,
    IntakeV6WorkspaceListResponse,
    IntakeV6WorkspaceResponse,
)
from seeds.seed_intake_v6_unified_pricing import V6_MATERIAL_PRICES, V6_WORKCENTER_RATES
from seeds.seed_tpl_volumetric_letters_v2 import seed_tpl_volumetric_letters_v2
from services.inventory_materials_admin_service import load_material_pricing_dict
from services.intake_v6_commercial_quote_service import get_quote_handoff_preview_for_workspace
from services.intake_v6_priced_quote_dry_run_service import build_intake_v6_priced_quote_dry_run
from services.intake_v6_priced_quote_write_service import write_intake_v6_priced_quote_totals
from services.intake_v6_quote_snapshot_v2_service import create_v6_quote_snapshot_v2
from services.intake_v6_material_breakdown_service import (
    get_material_breakdown_for_workspace,
    get_nesting_preview_for_workspace,
)
from services.intake_v6_offer_handoff_service import handoff_intake_v6_workspace_to_offer
from services.intake_v6_quote_to_order_service import (
    accept_v6_quote,
    complete_v6_pricing_review,
    convert_v6_quote_to_order,
    get_v6_commercial_spine_state,
    persist_v6_owner_approval,
)
from services.intake_v6_template_option_contract_service import get_template_form_contract_for_workspace
from services.intake_v6_workspace_service import (
    create_draft_quote_for_intake_v6_workspace,
    create_intake_v6_workspace,
    ensure_intake_v6_workspace_for_intake_request,
    get_ai_informational_assist_candidate_for_workspace,
    get_ai_semantic_classification_candidate_for_workspace,
    get_intake_v6_workspace,
    get_order_bound_task_readiness_for_workspace,
    get_pricing_input_preview_for_workspace,
    get_product_system_binding_for_workspace,
    get_production_handoff_preview_for_workspace,
    get_production_task_dry_run_for_workspace,
    get_task_generation_dry_run_for_workspace,
    get_task_preview_for_workspace,
    list_intake_v6_workspaces,
    preview_reanalyze_for_intake_v6_workspace,
    save_analysis_bundle_for_intake_v6_workspace,
    save_finish_setup_for_intake_v6_workspace,
    save_internal_draft_quote_confirmation_for_workspace,
    save_layer_roles_for_intake_v6_workspace,
    save_product_composition_confirmation_for_workspace,
    save_sheet_footprint_override_for_intake_v6_workspace,
    upload_svg_to_intake_v6_workspace,
)
from services.gradi_logical_list_read_model_service import get_gradi_logical_list_read_model
from services.form_system_contract_backbone_service import build_form_system_contract_map
from services.linked_template_runtime_segment_extraction_service import (
    extract_linked_template_segments_from_workspace_payload,
)
from services.letter_group_finish_readiness_service import (
    build_letter_group_finish_readiness_from_workspace_payload,
)
from services.tpl_volumetric_face_back_prep_cost_draft_service import (
    get_tpl_volumetric_face_back_prep_cost_draft_for_workspace,
)
from services.workcenter_rates_service import load_workcenter_rate_pricing_dict


router = APIRouter(
    prefix="/api/v1/intake-v6",
    tags=["intake-v6-workspaces"],
    dependencies=[Depends(get_current_user)],
)


def _workspace_code_v6() -> str:
    return f"IV6-{uuid.uuid4().hex[:8].upper()}"


def _record_to_v6_response(record: IntakeV6WorkspaceRecord) -> IntakeV6WorkspaceResponse:
    import json

    try:
        payload = json.loads(record.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    return IntakeV6WorkspaceResponse(
        id=record.id,
        workspace_code=record.workspace_code,
        title=record.title,
        template_code=record.template_code,
        status=record.status,  # type: ignore[arg-type]
        payload=payload,
        readiness_status=record.readiness_status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/pricing-snapshot")
async def get_intake_v6_pricing_snapshot(
    db: AsyncSession = Depends(get_db),
) -> dict:
    materials = await load_material_pricing_dict(db)
    rates = await load_workcenter_rate_pricing_dict(db)
    required_material_codes = [item["code"] for item in V6_MATERIAL_PRICES]
    required_rate_codes = [item["code"] for item in V6_WORKCENTER_RATES]
    missing_materials = [code for code in required_material_codes if code not in materials]
    missing_rates = [code for code in required_rate_codes if code not in rates]
    return {
        "surface": "intake-v6",
        "pricing_policy": "db_registry_only",
        "materials_ready": len(missing_materials) == 0,
        "rates_ready": len(missing_rates) == 0,
        "pricing_ready": len(missing_materials) == 0 and len(missing_rates) == 0,
        "required_material_count": len(required_material_codes),
        "required_rate_count": len(required_rate_codes),
        "missing_materials": missing_materials,
        "missing_rates": missing_rates,
        "materials": {code: materials.get(code) for code in required_material_codes if code in materials},
        "workcenter_rates": {code: rates.get(code) for code in required_rate_codes if code in rates},
    }


@router.post("/workspaces", response_model=IntakeV6WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace_v6(
    request: IntakeV6WorkspaceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6WorkspaceResponse:
    created = await create_intake_v6_workspace(db, request, current_user)
    return created


@router.post("/workspaces/ensure-for-intake-request", response_model=IntakeV6WorkspaceResponse)
async def ensure_workspace_for_intake_request_v6(
    request: IntakeV6EnsureWorkspaceForIntakeRequestBody,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6WorkspaceResponse:
    return await ensure_intake_v6_workspace_for_intake_request(
        db,
        request.intake_request_code,
        current_user,
        offer_method=request.offer_method,
        analyzer_mode=request.analyzer_mode,
        template_hint_code=request.template_hint_code,
        selected_template_code=request.selected_template_code,
        source=request.source,
    )


@router.get("/workspaces", response_model=IntakeV6WorkspaceListResponse)
async def list_workspaces_v6(
    include_archived: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> IntakeV6WorkspaceListResponse:
    return await list_intake_v6_workspaces(db, include_archived=include_archived)


@router.get("/workspaces/{workspace_id}", response_model=IntakeV6WorkspaceResponse)
async def get_workspace_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6WorkspaceResponse:
    return await get_intake_v6_workspace(db, workspace_id)


@router.post("/workspaces/{workspace_id}/svg", response_model=IntakeV6SvgUploadResponse)
async def upload_workspace_svg_v6(
    workspace_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6SvgUploadResponse:
    raw_bytes = await file.read()
    return await upload_svg_to_intake_v6_workspace(
        db,
        workspace_id,
        file_name=file.filename or "upload.svg",
        content_type=file.content_type,
        raw_bytes=raw_bytes,
        current_user=current_user,
    )


@router.put("/workspaces/{workspace_id}/analysis-bundle", response_model=IntakeV6WorkspaceResponse)
async def save_analysis_bundle_v6(
    workspace_id: str,
    request: IntakeV6AnalysisBundleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6WorkspaceResponse:
    return await save_analysis_bundle_for_intake_v6_workspace(db, workspace_id, request, current_user)


@router.put("/workspaces/{workspace_id}/layer-roles", response_model=IntakeV6WorkspaceResponse)
async def update_layer_roles_v6(
    workspace_id: str,
    request: IntakeV6LayerRoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6WorkspaceResponse:
    return await save_layer_roles_for_intake_v6_workspace(db, workspace_id, request, current_user)


@router.put("/workspaces/{workspace_id}/finish-setup", response_model=IntakeV6WorkspaceResponse)
async def update_finish_setup_v6(
    workspace_id: str,
    request: IntakeV6FinishSetup,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6WorkspaceResponse:
    return await save_finish_setup_for_intake_v6_workspace(db, workspace_id, request, current_user)


@router.put("/workspaces/{workspace_id}/product-composition-confirmation", response_model=IntakeV6WorkspaceResponse)
async def update_product_composition_confirmation_v6(
    workspace_id: str,
    request: IntakeV6ProductCompositionConfirmationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6WorkspaceResponse:
    return await save_product_composition_confirmation_for_workspace(
        db,
        workspace_id,
        confirmed=request.confirmed,
        items=request.items,
        operator_note=request.operator_note,
        current_user=current_user,
    )


@router.put(
    "/workspaces/{workspace_id}/operator/sheet-footprint-override",
    response_model=IntakeV6SheetFootprintOverrideResponse,
)
async def update_sheet_footprint_override_v6(
    workspace_id: str,
    request: IntakeV6SheetFootprintOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6SheetFootprintOverrideResponse:
    return await save_sheet_footprint_override_for_intake_v6_workspace(
        db, workspace_id, request, current_user
    )


@router.post(
    "/workspaces/{workspace_id}/reanalyze-preview",
    response_model=IntakeV6ReanalyzePreviewResponse,
)
async def post_reanalyze_preview_v6(
    workspace_id: str,
    request: IntakeV6ReanalyzePreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6ReanalyzePreviewResponse:
    return await preview_reanalyze_for_intake_v6_workspace(db, workspace_id, request, current_user)


@router.get(
    "/workspaces/{workspace_id}/product-system-binding",
    response_model=IntakeV6ProductSystemBindingResponse,
)
async def get_product_system_binding_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6ProductSystemBindingResponse:
    return await get_product_system_binding_for_workspace(db, workspace_id)


@router.get("/workspaces/{workspace_id}/linked-template-segments")
async def get_linked_template_segments_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    workspace = await get_intake_v6_workspace(db, workspace_id)
    payload = workspace.payload if isinstance(workspace.payload, dict) else {}
    product_binding = payload.get("product_binding") if isinstance(payload.get("product_binding"), dict) else {}
    root_template_code = workspace.template_code
    backbone = build_form_system_contract_map(root_template_code)
    linked_template_composition = backbone.get("linked_template_composition", {})
    runtime_segments = extract_linked_template_segments_from_workspace_payload(
        root_template_code=root_template_code,
        workspace_payload=payload,
        linked_template_composition=linked_template_composition,
    )
    return {
        "workspace_id": workspace_id,
        "workspace_record_id": workspace.id,
        "workspace_code": workspace.workspace_code,
        "root_template_code": root_template_code,
        "product_binding_template_code": product_binding.get("template_code"),
        "linked_template_composition": linked_template_composition,
        "linked_template_runtime_segments": runtime_segments,
        "downstream_write_intent": backbone.get("downstream_write_intent", {}),
        "read_only": True,
    }


@router.get("/workspaces/{workspace_id}/letter-group-finish-readiness")
async def get_letter_group_finish_readiness_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    workspace = await get_intake_v6_workspace(db, workspace_id)
    payload = workspace.payload if isinstance(workspace.payload, dict) else {}
    product_binding = payload.get("product_binding") if isinstance(payload.get("product_binding"), dict) else {}
    readiness = build_letter_group_finish_readiness_from_workspace_payload(
        payload=payload,
        root_template_code=workspace.template_code,
    )
    return {
        "read_only": True,
        "workspace_id": workspace_id,
        "workspace_record_id": workspace.id,
        "workspace_code": workspace.workspace_code,
        "root_template_code": workspace.template_code,
        "product_binding_template_code": product_binding.get("template_code"),
        **readiness,
    }


@router.get(
    "/workspaces/{workspace_id}/template-form-contract",
    response_model=IntakeV6TemplateFormContractResponse,
)
async def get_template_form_contract_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6TemplateFormContractResponse:
    return await get_template_form_contract_for_workspace(db, workspace_id)


@router.post("/product-system/templates/volumetric-letters-v2")
async def promote_volumetric_letters_v2_template_v6(
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    result = await seed_tpl_volumetric_letters_v2()
    result["created_from"] = "intake-v6/operator-ui"
    result["requested_by"] = getattr(current_user, "email", None) or getattr(current_user, "username", None)
    return result


@router.get("/workspaces/{workspace_id}/task-preview", response_model=IntakeV6TaskPreviewResponse)
async def get_task_preview_v6(
    workspace_id: str,
    face_finish_type: str | None = None,
    return_finish_type: str | None = None,
    illuminated: bool | None = None,
    lighting_system_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6TaskPreviewResponse:
    override: dict[str, object] = {}
    if face_finish_type is not None:
        override["face_finish_type"] = face_finish_type
    if return_finish_type is not None:
        override["return_finish_type"] = return_finish_type
    if illuminated is not None:
        override["illuminated"] = illuminated
    if lighting_system_type is not None:
        override["lighting_system_type"] = lighting_system_type
    return await get_task_preview_for_workspace(db, workspace_id, finish_override=override or None)


@router.get(
    "/workspaces/{workspace_id}/material-breakdown",
    response_model=IntakeV6MaterialBreakdownResponse,
)
async def get_material_breakdown_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6MaterialBreakdownResponse:
    return await get_material_breakdown_for_workspace(db, workspace_id)


@router.get("/workspaces/{workspace_id}/logical-list-read-model")
async def get_logical_list_read_model_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await get_gradi_logical_list_read_model(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/volumetric-face-back-prep/cost-draft",
    response_model=IntakeV6FaceBackPrepCostDraftResponse,
)
async def get_volumetric_face_back_prep_cost_draft_v6(
    workspace_id: str,
    shanfren_forex: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> IntakeV6FaceBackPrepCostDraftResponse:
    return await get_tpl_volumetric_face_back_prep_cost_draft_for_workspace(
        db, workspace_id, shanfren_forex_override=shanfren_forex
    )


@router.get(
    "/workspaces/{workspace_id}/nesting-preview",
    response_model=IntakeV6NestingPreviewResponse,
)
async def get_nesting_preview_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6NestingPreviewResponse:
    return await get_nesting_preview_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/pricing-input-preview",
    response_model=IntakeV6PricingInputPreviewResponse,
)
async def get_pricing_input_preview_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6PricingInputPreviewResponse:
    return await get_pricing_input_preview_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/production-handoff-preview",
    response_model=IntakeV6ProductionHandoffPreviewResponse,
)
async def get_production_handoff_preview_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6ProductionHandoffPreviewResponse:
    return await get_production_handoff_preview_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/production-task-dry-run",
    response_model=IntakeV3ProductionTaskDryRunResponse,
)
async def get_production_task_dry_run_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ProductionTaskDryRunResponse:
    return await get_production_task_dry_run_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/task-generation-dry-run",
    response_model=IntakeV6TaskGenerationDryRunResponse,
)
async def get_task_generation_dry_run_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6TaskGenerationDryRunResponse:
    return await get_task_generation_dry_run_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/order-bound-task-readiness",
    response_model=IntakeV6OrderBoundTaskReadinessResponse,
)
async def get_order_bound_task_readiness_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6OrderBoundTaskReadinessResponse:
    return await get_order_bound_task_readiness_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/ai-informational-assist-candidate",
    response_model=IntakeV6AiInformationalAssistPreviewResponse,
)
async def get_ai_informational_assist_candidate_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6AiInformationalAssistPreviewResponse:
    return await get_ai_informational_assist_candidate_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/ai-semantic-classification-candidate",
    response_model=IntakeV6AiSemanticClassificationPreviewResponse,
)
async def get_ai_semantic_classification_candidate_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6AiSemanticClassificationPreviewResponse:
    return await get_ai_semantic_classification_candidate_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/quote-handoff-preview",
    response_model=IntakeV6QuoteHandoffPreviewResponse,
)
async def get_quote_handoff_preview_v6(
    workspace_id: str,
    client_analysis_hash: str | None = Query(default=None, min_length=64, max_length=64),
    db: AsyncSession = Depends(get_db),
) -> IntakeV6QuoteHandoffPreviewResponse:
    return await get_quote_handoff_preview_for_workspace(
        db, workspace_id, client_analysis_hash=client_analysis_hash
    )


@router.get("/workspaces/{workspace_id}/priced-quote-dry-run")
async def get_priced_quote_dry_run_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await build_intake_v6_priced_quote_dry_run(db, workspace_id)


@router.post("/workspaces/{workspace_id}/priced-quote/write")
async def write_priced_quote_v6(
    workspace_id: str,
    request: IntakeV6PricedQuoteWriteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    operator_identifier = current_user.email or current_user.name or str(current_user.id)
    return await write_intake_v6_priced_quote_totals(
        db,
        workspace_id,
        quote_id=request.quote_id,
        expected_total_gross=request.expected_total_gross,
        expected_pricing_hash=request.expected_pricing_hash,
        operator_confirmation=request.operator_confirmation,
        operator_identifier=operator_identifier,
    )


@router.post("/workspaces/{workspace_id}/handoff-to-offer")
async def handoff_to_offer_v6(
    workspace_id: str,
    request: IntakeV6OfferHandoffRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    return await handoff_intake_v6_workspace_to_offer(
        db,
        workspace_id,
        client_analysis_hash=request.client_analysis_hash,
        expected_total_gross=request.expected_total_gross,
        expected_pricing_hash=request.expected_pricing_hash,
        operator_confirmation=request.operator_confirmation,
        current_user=current_user,
    )


@router.post("/workspaces/{workspace_id}/quotes/{quote_id}/snapshot-v2")
async def create_quote_snapshot_v2_v6(
    workspace_id: str,
    quote_id: int,
    request: IntakeV6QuoteSnapshotV2CreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    operator_identifier = current_user.email or current_user.name or str(current_user.id)
    return await create_v6_quote_snapshot_v2(
        db,
        quote_id=quote_id,
        workspace_id=workspace_id,
        operator_confirmation=request.operator_confirmation,
        expected_grand_total=request.expected_grand_total,
        expected_pricing_hash=request.expected_pricing_hash,
        created_by=operator_identifier,
    )


@router.put(
    "/workspaces/{workspace_id}/internal-draft-quote-confirmation",
    response_model=IntakeV6WorkspaceResponse,
)
async def save_internal_draft_quote_confirmation_v6(
    workspace_id: str,
    request: IntakeV6InternalDraftQuoteConfirmationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6WorkspaceResponse:
    return await save_internal_draft_quote_confirmation_for_workspace(
        db, workspace_id, confirmed=request.confirmed, current_user=current_user
    )


@router.post(
    "/workspaces/{workspace_id}/create-draft-quote",
    response_model=IntakeV6CreateDraftQuoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_draft_quote_v6(
    workspace_id: str,
    request: IntakeV6CreateDraftQuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6CreateDraftQuoteResponse:
    return await create_draft_quote_for_intake_v6_workspace(db, workspace_id, request, current_user)


@router.get("/quotes/{quote_id}/commercial-spine-state", response_model=IntakeV6CommercialSpineStateResponse)
async def get_quote_commercial_spine_state_v6(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6CommercialSpineStateResponse:
    return IntakeV6CommercialSpineStateResponse.model_validate(
        await get_v6_commercial_spine_state(db, quote_id=quote_id)
    )


@router.get(
    "/workspaces/{workspace_id}/commercial-spine-state",
    response_model=IntakeV6CommercialSpineStateResponse,
)
async def get_workspace_commercial_spine_state_v6(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV6CommercialSpineStateResponse:
    return IntakeV6CommercialSpineStateResponse.model_validate(
        await get_v6_commercial_spine_state(db, workspace_id=workspace_id)
    )


@router.post("/quotes/{quote_id}/complete-pricing-review")
async def complete_quote_pricing_review_v6(
    quote_id: int,
    request: IntakeV6CompletePricingReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await complete_v6_pricing_review(db, quote_id, request.model_dump(), current_user)


@router.post("/quotes/{quote_id}/owner-approval")
async def post_quote_owner_approval_v6(
    quote_id: int,
    request: IntakeV6OwnerApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await persist_v6_owner_approval(db, quote_id, request.model_dump(), current_user)


@router.post("/quotes/{quote_id}/accept")
async def accept_quote_v6(
    quote_id: int,
    request: IntakeV6AcceptQuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await accept_v6_quote(db, quote_id, request.model_dump(), current_user)


@router.post("/quotes/{quote_id}/convert-to-order")
async def convert_quote_to_order_v6(
    quote_id: int,
    request: IntakeV6ConvertToOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await convert_v6_quote_to_order(db, quote_id, request.model_dump(), current_user)


@router.post(
    "/workspaces/from-v4/{source_workspace_id}",
    response_model=IntakeV6WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def clone_workspace_from_v4(
    source_workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV6WorkspaceResponse:
    result = await db.execute(
        select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == source_workspace_id)
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail={"error": "source_workspace_not_found"})
    now = datetime.now(timezone.utc)
    record = IntakeV6WorkspaceRecord(
        id=str(uuid.uuid4()),
        workspace_code=_workspace_code_v6(),
        title=f"{source.title} Â· Intake V6",
        template_code=source.template_code,
        status=source.status,
        payload_json=source.payload_json,
        readiness_status=source.readiness_status,
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _record_to_v6_response(record)



