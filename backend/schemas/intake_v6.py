"""Intake V6 operator workspace contracts.

This module gives Intake V6 its own public schema namespace while the validated
V4-compatible payload is being ported service-by-service.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.intake_v4 import (
    INTAKE_V4_SCHEMA_VERSION,
    PILOT_V4_TEMPLATE_CODE,
    TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE,
    TPL_VOLUMETRIC_FACE_BACK_PREP_V1_VERSION,
    IntakeV4AcceptQuoteRequest,
    IntakeV4AiInformationalAssistPreviewResponse,
    IntakeV4AiSemanticClassificationPreviewResponse,
    IntakeV4AnalysisBundleRequest,
    IntakeV4ArtworkComplexityDecision,
    IntakeV4ArtworkFinish,
    IntakeV4ClientRequest,
    IntakeV4CommercialSpineStateResponse,
    IntakeV4CompletePricingReviewRequest,
    IntakeV4ConvertToOrderRequest,
    IntakeV4CreateDraftQuoteRequest,
    IntakeV4CreateDraftQuoteResponse,
    IntakeV4FaceBackPrepCostDraftResponse,
    IntakeV4FinishSetup,
    IntakeV4InternalDraftQuoteConfirmationRequest,
    IntakeV4LayerRoleLayer,
    IntakeV4LayerRoleSetup,
    IntakeV4LayerRoleUpdateRequest,
    IntakeV4MaterialBreakdownResponse,
    IntakeV4NestingPreviewResponse,
    IntakeV4OrderBoundTaskReadinessResponse,
    IntakeV4OwnerApprovalRequest,
    IntakeV4PricingInputPreviewResponse,
    IntakeV4ProductBinding,
    IntakeV4ProductionHandoffPreviewResponse,
    IntakeV4ProductSystemBindingResponse,
    IntakeV4QuoteHandoffPreviewResponse,
    IntakeV4ReanalyzePreviewRequest,
    IntakeV4ReanalyzePreviewResponse,
    IntakeV4ReanalyzePreviewSnapshot,
    IntakeV4SheetFootprintOverrideRequest,
    IntakeV4SheetFootprintOverrideResponse,
    IntakeV4SvgSource,
    IntakeV4SvgUploadResponse,
    IntakeV4TaskGenerationDryRunResponse,
    IntakeV4TaskPreviewResponse,
    IntakeV4TemplateFormContractResponse,
    IntakeV4EnsureWorkspaceForIntakeRequestBody,
    IntakeV4WorkspaceCreateRequest,
    IntakeV4WorkspaceListResponse,
    IntakeV4WorkspacePayload,
    IntakeV4WorkspaceResponse,
    LayerConfirmationState,
    LayerSetupStatus,
    SvgUploadStatus,
    WorkspaceDraftStatus,
)

INTAKE_V6_SCHEMA_VERSION = INTAKE_V4_SCHEMA_VERSION
PILOT_V6_TEMPLATE_CODE = PILOT_V4_TEMPLATE_CODE

IntakeV6AcceptQuoteRequest = IntakeV4AcceptQuoteRequest
IntakeV6AiInformationalAssistPreviewResponse = IntakeV4AiInformationalAssistPreviewResponse
IntakeV6AiSemanticClassificationPreviewResponse = IntakeV4AiSemanticClassificationPreviewResponse
IntakeV6AnalysisBundleRequest = IntakeV4AnalysisBundleRequest
IntakeV6ArtworkComplexityDecision = IntakeV4ArtworkComplexityDecision
IntakeV6ArtworkFinish = IntakeV4ArtworkFinish
IntakeV6ClientRequest = IntakeV4ClientRequest
IntakeV6CommercialSpineStateResponse = IntakeV4CommercialSpineStateResponse
IntakeV6CompletePricingReviewRequest = IntakeV4CompletePricingReviewRequest
IntakeV6ConvertToOrderRequest = IntakeV4ConvertToOrderRequest
IntakeV6CreateDraftQuoteRequest = IntakeV4CreateDraftQuoteRequest
IntakeV6CreateDraftQuoteResponse = IntakeV4CreateDraftQuoteResponse
IntakeV6FaceBackPrepCostDraftResponse = IntakeV4FaceBackPrepCostDraftResponse
IntakeV6FinishSetup = IntakeV4FinishSetup
IntakeV6InternalDraftQuoteConfirmationRequest = IntakeV4InternalDraftQuoteConfirmationRequest
IntakeV6LayerRoleLayer = IntakeV4LayerRoleLayer
IntakeV6LayerRoleSetup = IntakeV4LayerRoleSetup
IntakeV6LayerRoleUpdateRequest = IntakeV4LayerRoleUpdateRequest
IntakeV6MaterialBreakdownResponse = IntakeV4MaterialBreakdownResponse
IntakeV6NestingPreviewResponse = IntakeV4NestingPreviewResponse
IntakeV6OwnerApprovalRequest = IntakeV4OwnerApprovalRequest
IntakeV6PricingInputPreviewResponse = IntakeV4PricingInputPreviewResponse
IntakeV6ProductBinding = IntakeV4ProductBinding
IntakeV6ProductionHandoffPreviewResponse = IntakeV4ProductionHandoffPreviewResponse
IntakeV6ProductSystemBindingResponse = IntakeV4ProductSystemBindingResponse
IntakeV6QuoteHandoffPreviewResponse = IntakeV4QuoteHandoffPreviewResponse
IntakeV6ReanalyzePreviewRequest = IntakeV4ReanalyzePreviewRequest
IntakeV6ReanalyzePreviewResponse = IntakeV4ReanalyzePreviewResponse
IntakeV6ReanalyzePreviewSnapshot = IntakeV4ReanalyzePreviewSnapshot
IntakeV6SheetFootprintOverrideRequest = IntakeV4SheetFootprintOverrideRequest
IntakeV6SheetFootprintOverrideResponse = IntakeV4SheetFootprintOverrideResponse
IntakeV6SvgSource = IntakeV4SvgSource
IntakeV6SvgUploadResponse = IntakeV4SvgUploadResponse
IntakeV6TaskGenerationDryRunResponse = IntakeV4TaskGenerationDryRunResponse
IntakeV6TaskPreviewResponse = IntakeV4TaskPreviewResponse
IntakeV6TemplateFormContractResponse = IntakeV4TemplateFormContractResponse
IntakeV6WorkspaceCreateRequest = IntakeV4WorkspaceCreateRequest
IntakeV6EnsureWorkspaceForIntakeRequestBody = IntakeV4EnsureWorkspaceForIntakeRequestBody
IntakeV6WorkspaceListResponse = IntakeV4WorkspaceListResponse
IntakeV6WorkspacePayload = IntakeV4WorkspacePayload
IntakeV6WorkspaceResponse = IntakeV4WorkspaceResponse


class IntakeV6OrderBoundTaskReadinessResponse(IntakeV4OrderBoundTaskReadinessResponse):
    v4_order_conversion: dict[str, Any] = Field(default_factory=dict, exclude=True)
    v6_order_conversion: dict[str, Any] = Field(default_factory=dict)


class IntakeV6AiInformationalAssistPreviewResponse(BaseModel):
    workspace_id: str
    template_code: str
    preview_only: bool
    ai_not_called: bool
    context: Literal["intake_v6_svg_review"] = "intake_v6_svg_review"
    candidate_payload: dict[str, Any]
    mock_suggestions: list[dict[str, Any]] = Field(default_factory=list)
    informational_envelope: dict[str, Any]
    boundary_flags: dict[str, Any]
    operator_confirmation_contract: dict[str, Any]
    mock_suggestion: dict[str, Any] | None = None


class IntakeV6AiSemanticClassificationPreviewResponse(BaseModel):
    workspace_id: str
    template_code: str
    preview_only: bool
    ai_not_called: bool
    candidate_payload: dict[str, Any]
    mock_suggestion: dict[str, Any]
    boundary_flags: dict[str, Any]
    operator_confirmation_contract: dict[str, Any]


class IntakeV6TemplateFormContractResponse(BaseModel):
    workspace_id: str
    template_code: str
    contract_version: str = "tpl_volumetric_option_contract_v1"
    intended_form_authority: str = "ProductSystem + Blueprint Dossier variants_json + quote_input contract"
    current_runtime_authority: str = "Intake V6 operator form with ProductSystem binding and adapter warnings"
    alignment_status: Literal["aligned", "partial", "blocked"] = "partial"
    template_active: bool = False
    dossier_status: str | None = None
    dossier_source: Literal["product_blueprint_dossier", "static_contract_fallback"] = "static_contract_fallback"
    ui_must_not_invent_final_options: bool = True
    variant_fields: list[dict[str, Any]] = Field(default_factory=list)
    canonical_rows: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    discovered_v6_values: dict[str, Any] = Field(default_factory=dict)


class IntakeV6CommercialSpineStateResponse(BaseModel):
    quote_exists: bool
    is_v6_quote: bool = False
    quote_id: int | None = None
    quote_code: str | None = None
    quote_status: str | None = None
    intake_code: str | None = None
    workspace_id: str | None = None
    requires_pricing_review: bool | None = None
    pricing_review: dict[str, Any] = Field(default_factory=dict)
    owner_approval: dict[str, Any] = Field(default_factory=dict)
    snapshot_v2: dict[str, Any] = Field(default_factory=dict)
    quote_accepted: bool = False
    quote_commercial_totals: dict[str, Any] = Field(default_factory=dict)
    v6_order_conversion: dict[str, Any] = Field(default_factory=dict)
    creates_execution_tasks: bool = False
    writes_execution_plan: bool = False
    stock_consumption: bool = False
    owner_approval_persisted: bool = False
    v6_quote_to_order_enabled: bool = True


class IntakeV6PricedQuoteWriteRequest(BaseModel):
    quote_id: int
    expected_total_gross: float
    expected_pricing_hash: str | None = None
    operator_confirmation: bool = True


class IntakeV6OfferHandoffRequest(BaseModel):
    client_analysis_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="SHA-256 hex of SVG bytes the operator confirms for V6 offer handoff.",
    )
    expected_total_gross: float
    expected_pricing_hash: str | None = None
    operator_confirmation: bool = True


class IntakeV6QuoteSnapshotV2CreateRequest(BaseModel):
    operator_confirmation: bool = True
    expected_grand_total: float | None = None
    expected_pricing_hash: str | None = None
