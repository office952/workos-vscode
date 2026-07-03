"""Intake V4 workspace HTTP surface — decoupled from Intake V3."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from schemas.intake_v4 import (
    IntakeV4AnalysisBundleRequest,
    IntakeV4AiInformationalAssistPreviewResponse,
    IntakeV4AiSemanticClassificationPreviewResponse,
    IntakeV4CreateDraftQuoteRequest,
    IntakeV4CreateDraftQuoteResponse,
    IntakeV4FaceBackPrepCostDraftResponse,
    IntakeV4FinishSetup,
    IntakeV4InternalDraftQuoteConfirmationRequest,
    IntakeV4LayerRoleUpdateRequest,
    IntakeV4MaterialBreakdownResponse,
    IntakeV4QuoteHandoffPreviewResponse,
    IntakeV4NestingPreviewResponse,
    IntakeV4OrderBoundTaskReadinessResponse,
    IntakeV4PricingInputPreviewResponse,
    IntakeV4ProductionHandoffPreviewResponse,
    IntakeV4ProductSystemBindingResponse,
    IntakeV4ReanalyzePreviewRequest,
    IntakeV4ReanalyzePreviewResponse,
    IntakeV4SheetFootprintOverrideRequest,
    IntakeV4SheetFootprintOverrideResponse,
    IntakeV4SvgUploadResponse,
    IntakeV4TemplateFormContractResponse,
    IntakeV4TaskGenerationDryRunResponse,
    IntakeV4TaskPreviewResponse,
    IntakeV4WorkspaceCreateRequest,
    IntakeV4WorkspaceListResponse,
    IntakeV4WorkspaceResponse,
)
from schemas.intake_v3 import IntakeV3ProductionTaskDryRunResponse
from services.intake_v4_material_breakdown_service import (
    get_material_breakdown_for_workspace,
    get_nesting_preview_for_workspace,
)
from services.intake_v4_commercial_quote_service import get_quote_handoff_preview_for_workspace
from services.tpl_volumetric_face_back_prep_cost_draft_service import (
    get_tpl_volumetric_face_back_prep_cost_draft_for_workspace,
)
from services.intake_v4_workspace_service import (
    create_intake_v4_workspace,
    create_draft_quote_for_intake_v4_workspace,
    get_ai_informational_assist_candidate_for_workspace,
    get_ai_semantic_classification_candidate_for_workspace,
    get_intake_v4_workspace,
    get_order_bound_task_readiness_for_workspace,
    get_pricing_input_preview_for_workspace,
    get_product_system_binding_for_workspace,
    get_production_handoff_preview_for_workspace,
    get_production_task_dry_run_for_workspace,
    get_task_generation_dry_run_for_workspace,
    get_task_preview_for_workspace,
    list_intake_v4_workspaces,
    save_analysis_bundle_for_intake_v4_workspace,
    save_finish_setup_for_intake_v4_workspace,
    save_internal_draft_quote_confirmation_for_workspace,
    save_layer_roles_for_intake_v4_workspace,
    preview_reanalyze_for_intake_v4_workspace,
    save_sheet_footprint_override_for_intake_v4_workspace,
    upload_svg_to_intake_v4_workspace,
)
from services.intake_v4_template_option_contract_service import (
    get_template_form_contract_for_workspace,
)
from seeds.seed_tpl_volumetric_letters_v2 import seed_tpl_volumetric_letters_v2

router = APIRouter(
    prefix="/api/v1/intake-v4",
    tags=["intake-v4-workspaces"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/workspaces", response_model=IntakeV4WorkspaceListResponse)
async def list_workspaces(
    include_archived: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> IntakeV4WorkspaceListResponse:
    return await list_intake_v4_workspaces(db, include_archived=include_archived)


@router.post("/workspaces", response_model=IntakeV4WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: IntakeV4WorkspaceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV4WorkspaceResponse:
    return await create_intake_v4_workspace(db, request, current_user)


@router.get("/workspaces/{workspace_id}", response_model=IntakeV4WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4WorkspaceResponse:
    return await get_intake_v4_workspace(db, workspace_id)


@router.post("/workspaces/{workspace_id}/svg", response_model=IntakeV4SvgUploadResponse)
async def upload_workspace_svg(
    workspace_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV4SvgUploadResponse:
    raw_bytes = await file.read()
    return await upload_svg_to_intake_v4_workspace(
        db,
        workspace_id,
        file_name=file.filename or "upload.svg",
        content_type=file.content_type,
        raw_bytes=raw_bytes,
        current_user=current_user,
    )


@router.put("/workspaces/{workspace_id}/analysis-bundle", response_model=IntakeV4WorkspaceResponse)
async def save_analysis_bundle(
    workspace_id: str,
    request: IntakeV4AnalysisBundleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV4WorkspaceResponse:
    return await save_analysis_bundle_for_intake_v4_workspace(db, workspace_id, request, current_user)


@router.put("/workspaces/{workspace_id}/layer-roles", response_model=IntakeV4WorkspaceResponse)
async def update_layer_roles(
    workspace_id: str,
    request: IntakeV4LayerRoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV4WorkspaceResponse:
    return await save_layer_roles_for_intake_v4_workspace(db, workspace_id, request, current_user)


@router.put("/workspaces/{workspace_id}/finish-setup", response_model=IntakeV4WorkspaceResponse)
async def update_finish_setup(
    workspace_id: str,
    request: IntakeV4FinishSetup,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV4WorkspaceResponse:
    return await save_finish_setup_for_intake_v4_workspace(db, workspace_id, request, current_user)


@router.put(
    "/workspaces/{workspace_id}/operator/sheet-footprint-override",
    response_model=IntakeV4SheetFootprintOverrideResponse,
)
async def update_sheet_footprint_override(
    workspace_id: str,
    request: IntakeV4SheetFootprintOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV4SheetFootprintOverrideResponse:
    return await save_sheet_footprint_override_for_intake_v4_workspace(
        db, workspace_id, request, current_user
    )


@router.post(
    "/workspaces/{workspace_id}/reanalyze-preview",
    response_model=IntakeV4ReanalyzePreviewResponse,
)
async def post_reanalyze_preview(
    workspace_id: str,
    request: IntakeV4ReanalyzePreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV4ReanalyzePreviewResponse:
    return await preview_reanalyze_for_intake_v4_workspace(db, workspace_id, request, current_user)


@router.get(
    "/workspaces/{workspace_id}/product-system-binding",
    response_model=IntakeV4ProductSystemBindingResponse,
)
async def get_product_system_binding(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4ProductSystemBindingResponse:
    return await get_product_system_binding_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/template-form-contract",
    response_model=IntakeV4TemplateFormContractResponse,
)
async def get_template_form_contract(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4TemplateFormContractResponse:
    return await get_template_form_contract_for_workspace(db, workspace_id)


@router.post("/product-system/templates/volumetric-letters-v2")
async def promote_volumetric_letters_v2_template(
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    """Create/update TPL-VOLUMETRIC-LETTERS_v2 from the V4 operator contract."""
    result = await seed_tpl_volumetric_letters_v2()
    result["created_from"] = "intake-v4/operator-ui"
    result["requested_by"] = getattr(current_user, "email", None) or getattr(current_user, "username", None)
    return result


@router.get("/workspaces/{workspace_id}/task-preview", response_model=IntakeV4TaskPreviewResponse)
async def get_task_preview(
    workspace_id: str,
    face_finish_type: str | None = None,
    return_finish_type: str | None = None,
    illuminated: bool | None = None,
    lighting_system_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4TaskPreviewResponse:
    override: dict[str, object] = {}
    if face_finish_type is not None:
        override["face_finish_type"] = face_finish_type
    if return_finish_type is not None:
        override["return_finish_type"] = return_finish_type
    if illuminated is not None:
        override["illuminated"] = illuminated
    if lighting_system_type is not None:
        override["lighting_system_type"] = lighting_system_type
    return await get_task_preview_for_workspace(
        db,
        workspace_id,
        finish_override=override or None,
    )


@router.get(
    "/workspaces/{workspace_id}/material-breakdown",
    response_model=IntakeV4MaterialBreakdownResponse,
)
async def get_material_breakdown(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4MaterialBreakdownResponse:
    return await get_material_breakdown_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/volumetric-face-back-prep/cost-draft",
    response_model=IntakeV4FaceBackPrepCostDraftResponse,
)
async def get_volumetric_face_back_prep_cost_draft(
    workspace_id: str,
    shanfren_forex: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> IntakeV4FaceBackPrepCostDraftResponse:
    return await get_tpl_volumetric_face_back_prep_cost_draft_for_workspace(
        db,
        workspace_id,
        shanfren_forex_override=shanfren_forex,
    )


@router.get(
    "/workspaces/{workspace_id}/nesting-preview",
    response_model=IntakeV4NestingPreviewResponse,
)
async def get_nesting_preview(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4NestingPreviewResponse:
    return await get_nesting_preview_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/pricing-input-preview",
    response_model=IntakeV4PricingInputPreviewResponse,
)
async def get_pricing_input_preview(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4PricingInputPreviewResponse:
    return await get_pricing_input_preview_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/production-handoff-preview",
    response_model=IntakeV4ProductionHandoffPreviewResponse,
)
async def get_production_handoff_preview(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4ProductionHandoffPreviewResponse:
    return await get_production_handoff_preview_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/production-task-dry-run",
    response_model=IntakeV3ProductionTaskDryRunResponse,
)
async def get_production_task_dry_run(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV3ProductionTaskDryRunResponse:
    return await get_production_task_dry_run_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/task-generation-dry-run",
    response_model=IntakeV4TaskGenerationDryRunResponse,
)
async def get_task_generation_dry_run(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4TaskGenerationDryRunResponse:
    return await get_task_generation_dry_run_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/order-bound-task-readiness",
    response_model=IntakeV4OrderBoundTaskReadinessResponse,
)
async def get_order_bound_task_readiness(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4OrderBoundTaskReadinessResponse:
    return await get_order_bound_task_readiness_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/ai-informational-assist-candidate",
    response_model=IntakeV4AiInformationalAssistPreviewResponse,
)
async def get_ai_informational_assist_candidate(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4AiInformationalAssistPreviewResponse:
    return await get_ai_informational_assist_candidate_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/ai-semantic-classification-candidate",
    response_model=IntakeV4AiSemanticClassificationPreviewResponse,
)
async def get_ai_semantic_classification_candidate(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4AiSemanticClassificationPreviewResponse:
    return await get_ai_semantic_classification_candidate_for_workspace(db, workspace_id)


@router.get(
    "/workspaces/{workspace_id}/quote-handoff-preview",
    response_model=IntakeV4QuoteHandoffPreviewResponse,
)
async def get_quote_handoff_preview(
    workspace_id: str,
    client_analysis_hash: str | None = Query(default=None, min_length=64, max_length=64),
    db: AsyncSession = Depends(get_db),
) -> IntakeV4QuoteHandoffPreviewResponse:
    return await get_quote_handoff_preview_for_workspace(
        db,
        workspace_id,
        client_analysis_hash=client_analysis_hash,
    )


@router.put(
    "/workspaces/{workspace_id}/internal-draft-quote-confirmation",
    response_model=IntakeV4WorkspaceResponse,
)
async def save_internal_draft_quote_confirmation(
    workspace_id: str,
    request: IntakeV4InternalDraftQuoteConfirmationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV4WorkspaceResponse:
    return await save_internal_draft_quote_confirmation_for_workspace(
        db,
        workspace_id,
        confirmed=request.confirmed,
        current_user=current_user,
    )


@router.post(
    "/workspaces/{workspace_id}/create-draft-quote",
    response_model=IntakeV4CreateDraftQuoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_draft_quote(
    workspace_id: str,
    request: IntakeV4CreateDraftQuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> IntakeV4CreateDraftQuoteResponse:
    return await create_draft_quote_for_intake_v4_workspace(db, workspace_id, request, current_user)
