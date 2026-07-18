"""Intake V4 operator workspace contracts — decoupled from Intake V3 form/payload."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schemas.ai_informational_layer import (
    AiInformationalBoundaryFlags,
    AiInformationalConfirmationContract,
    AiInformationalSuggestionEnvelope,
    AiInformationalSuggestionItem,
)
from schemas.offer_scope import CanonicalSoldModule, OfferScope, OfferScopeMode
from schemas.sold_scope_dependency import SoldScopeDependencyValidationResult

INTAKE_V4_SCHEMA_VERSION = "1.0.0"
PILOT_V4_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"
TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE = "TPL-VOLUMETRIC-FACE-BACK-PREP"
TPL_VOLUMETRIC_FACE_BACK_PREP_V1_VERSION = "v1-cnc-only"

LayerConfirmationState = Literal["pending", "confirmed", "ignored"]
LayerSetupStatus = Literal["missing", "partial", "complete"]
WorkspaceDraftStatus = Literal["draft", "collecting_data", "blocked", "ready_for_quote_preview", "archived"]
SvgUploadStatus = Literal["missing", "analyzed", "failed"]


class IntakeV4ClientRequest(BaseModel):
    client_name: str | None = None
    job_title: str | None = None
    width_mm: float | None = None
    height_mm: float | None = None


class IntakeV4ProductBinding(BaseModel):
    template_code: str
    template_id: int | None = None
    template_label: str | None = None
    product_family: str | None = None
    product_family_name: str | None = None
    bound_at: datetime | None = None


class IntakeV4SvgSource(BaseModel):
    file_name: str
    file_size_bytes: int = Field(ge=0)
    file_hash: str | None = None
    upload_status: SvgUploadStatus = "missing"


class IntakeV4LayerRoleLayer(BaseModel):
    layer_key: str
    layer_id: str | None = None
    layer_name: str | None = None
    auto_role: str = "unknown"
    auto_confidence: str = "low"
    confirmed_role: str | None = None
    confirmation_state: LayerConfirmationState = "pending"
    operator_note: str | None = None
    path_count: int | None = None
    dominant_fill: str | None = None


class IntakeV4LayerBindingContract(BaseModel):
    layer_key: str
    source_layer_name: str | None = None
    detected_kind: str | None = None
    suggested_semantic_role: str | None = None
    confirmed_semantic_role: str | None = None
    target_template_code: str | None = None
    binding_status: Literal["pending", "suggested", "confirmed", "ignored"] = "pending"


class IntakeV4LayerRoleSetup(BaseModel):
    confirmation_status: LayerSetupStatus = "missing"
    layers: list[IntakeV4LayerRoleLayer] = Field(default_factory=list)
    layer_bindings: list[IntakeV4LayerBindingContract] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class IntakeV4SelectedLayerRef(BaseModel):
    layer_id: str = Field(min_length=1)
    role: Literal["vector_litere", "vector_logo"]
    source: Literal["operator_confirmed_layer_role"] = "operator_confirmed_layer_role"
    confirmed: bool = True


class IntakeV4SvgRuntime(BaseModel):
    selected_layer_refs: list[IntakeV4SelectedLayerRef] = Field(default_factory=list)


class IntakeV4LetterGroupFinish(BaseModel):
    group_key: str
    layer_name: str | None = None
    source_fill_color: str | None = None
    face_area_m2: float | None = None
    perimeter_m: float | None = None
    element_count: int | None = None
    face_finish_type: str | None = "oracal_651"
    face_oracal_code: str | None = None
    face_oracal_name: str | None = None
    return_finish_type: str | None = "white_aluminum"
    return_oracal_code: str | None = None
    return_oracal_name: str | None = None
    return_depth_mm: float | None = None
    face_vinyl_roll_width_mm: float | None = None
    backing_mode: Literal["none", "forex_10_no_bevel", "forex_10_with_bevel"] | None = None
    confirmed: bool = False


class IntakeV4ArtworkFinish(BaseModel):
    layer_key: str
    layer_name: str | None = None
    display_name: str | None = None
    source_layer_name: str | None = None
    original_detected_label: str | None = None
    position_hint: str | None = None
    execution_type: str | None = "needs_decision"
    color_mode: str | None = "unknown"
    print_transparency: Literal["standard", "translucent", "transparent"] = "standard"
    material_code: str | None = None
    face_personalization_method: Literal["none_raw_plexi", "oracal", "print_laminate"] | None = None
    face_roll_width_mm: float | None = None
    print_roll_width_mm: float | None = None
    lamination_roll_width_mm: float | None = None
    print_required: bool | None = None
    lamination_required: bool | None = None
    roll_side_retraction_mm: float | None = None
    roll_total_retraction_mm: float | None = None
    face_oracal_code: str | None = None
    face_oracal_name: str | None = None
    print_material_code: str | None = None
    lamination_material_code: str | None = None
    estimated_area_m2: float | None = None
    element_count: int | None = None
    distinct_fill_count: int | None = None
    return_finish_type: str | None = "white_aluminum"
    return_oracal_code: str | None = None
    return_oracal_name: str | None = None
    return_depth_mm: float | None = None
    backing_mode: Literal["none", "forex_10_no_bevel", "forex_10_with_bevel"] | None = None
    confirmed: bool = False


class IntakeV4ArtworkComplexityDecision(BaseModel):
    artwork_id: str
    operator_application: Literal["vinyl_cut", "print_on_vinyl_laminated", "manual_review"]
    accepted_system_recommendation: bool = False
    override_manual_vinyl_cut: bool = False
    operator_note: str | None = None


class IntakeV4CommercialInputs(BaseModel):
    markup_percent: float = 35.0
    discount_percent: float = 0.0
    vat_percent: float = 19.0
    manual_adjustment_ron: float = 0.0


class IntakeV4MountingSolution(BaseModel):
    """Canonical mounting solution or installation-template-only sentinel.

    Product System support children use ``kind=product_system_template`` (or omit kind)
    with a non-empty ``template_code``. Installation template without ACM/metal uses
    ``kind=installation_template`` and ``template_code=None``.
    """

    kind: Literal["product_system_template", "installation_template"] | None = None
    template_code: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_mounting_solution_shape(self) -> IntakeV4MountingSolution:
        kind = (self.kind or "").strip() or None
        code = (self.template_code or "").strip() or None
        if kind == "installation_template":
            if code:
                raise ValueError(
                    "installation_template mounting_solution must not set template_code"
                )
            self.template_code = None
            self.kind = "installation_template"
            return self
        if not code:
            raise ValueError("product_system_template mounting_solution requires template_code")
        self.template_code = code
        if kind is None:
            self.kind = "product_system_template"
        return self


class IntakeV4FinishSetup(BaseModel):
    face_finish_type: str | None = None
    face_vinyl_roll_width_mm: float | None = None
    finish_target: Literal["face", "cant", "artwork", "back", "all"] | None = None
    return_finish_type: str | None = None
    volum_aluminum_module_template_code: str | None = None
    return_oracal_code: str | None = None
    return_oracal_name: str | None = None
    return_depth_mm: float | None = None
    illuminated: bool = True
    lighting_system_type: str | None = "led_modules"
    light_color: str | None = "neutral"
    led_module_power_w: float | None = 0.75
    led_strip_power_w_per_ml: float | None = 5.0
    led_module_count: int | None = None
    letter_led_strip_length_m: float | None = None
    emblem_led_strip_length_m: float | None = None
    total_led_strip_length_m: float | None = None
    estimated_led_watts: float | None = None
    required_psu_watts: float | None = None
    selected_psu_watts: int | None = None
    psu_configuration: list[int] = Field(default_factory=list)
    psu_allocation_status: str | None = None
    letter_group_finishes: list[IntakeV4LetterGroupFinish] = Field(default_factory=list)
    artwork_finishes: list[IntakeV4ArtworkFinish] = Field(default_factory=list)
    artwork_complexity_decisions: list[IntakeV4ArtworkComplexityDecision] = Field(default_factory=list)
    backing_mode: Literal["none", "forex_10_no_bevel", "forex_10_with_bevel"] | None = "forex_10_no_bevel"
    back_bevel_enabled: bool | None = None
    mounting_template_enabled: bool | None = None
    mounting_template_area_m2: float | None = None
    mounting_template_material_type: Literal["forex", "paper"] | None = None
    mounting_scope: (
        Literal[
            "none",
            "preparation_only",
            "preparation_and_site_installation",
            "no_mounting",
            "mounting_included",
            "mounting_external",
            "to_be_decided",
        ]
        | None
    ) = None
    site_installation_included: bool | None = None
    mounting_solution: IntakeV4MountingSolution | None = None
    mounting_system: Literal["direct_wall", "steel_bars", "aluminum_bars", "acm_panel"] | None = None
    mounting_bar_profile: str | None = None
    support_type: str | None = None
    # Modular process config (typed Intake → ProductDefinition → resolver). Not pricing.
    mains_cable_length_m: float | None = None
    power_supply_service_corner: (
        Literal["TOP_LEFT", "TOP_RIGHT", "BOTTOM_LEFT", "BOTTOM_RIGHT", "MANUAL_CONFIRMED"] | None
    ) = None
    service_screw_finish: Literal["NATURAL", "PAINTED_TO_MATCH_CANT"] | None = None
    emblem_lighting_mode: Literal["excluded", "area_lit", "needs_decision"] = "area_lit"
    letter_led_module_count: int | None = None
    emblem_led_module_count: int | None = None
    total_led_module_count: int | None = None
    commercial_inputs: IntakeV4CommercialInputs | None = None
    confirmed: bool = False
    internal_draft_quote_confirmed: bool = False
    # Component-aware SVG assignment (Product System authority). JSON document — no DB migration.
    svg_component_bindings: list[dict[str, Any]] = Field(default_factory=list)
    # Typed Alucobond/support selection (synced from SUPPORT_CONTOUR binding; must not be dropped).
    svg_support_selection: dict[str, Any] | None = None
    # Technical wall fixing system (Brat otel vertical, …) — independent of commercial mounting_scope.
    mounting_fixing_system: dict[str, Any] | None = None
    # ACP shell-common electrical + per-zone illumination intents (guarded; no invented LED/PSU qty).
    acp_electrical_configuration: dict[str, Any] | None = None


class IntakeV4AnalysisPersistRequest(BaseModel):
    file_name: str
    file_size_bytes: int = Field(ge=0)
    svg_analysis_json: dict[str, Any]
    layer_role_setup: IntakeV4LayerRoleSetup


class IntakeV4AnalysisBundleRequest(BaseModel):
    file_name: str
    file_size_bytes: int = Field(ge=0)
    svg_text: str = Field(min_length=1)
    svg_analysis_json: dict[str, Any]
    layer_role_setup: IntakeV4LayerRoleSetup


class IntakeV4FinishSetupUpdateRequest(IntakeV4FinishSetup):
    """Operator finish setup for Step 2 — must set confirmed=true to advance readiness."""


class IntakeV4WorkspacePayload(BaseModel):
    schema_version: str = INTAKE_V4_SCHEMA_VERSION
    client: IntakeV4ClientRequest = Field(default_factory=IntakeV4ClientRequest)
    product_binding: IntakeV4ProductBinding
    intake_request_code: str | None = None
    offer_method: str | None = None
    analyzer_mode: Literal["analyzer_first", "template_hint", "template_locked"] | None = None
    template_hint_code: str | None = None
    selected_template_code: str | None = None
    source: str | None = None
    work_intake_context: dict[str, Any] = Field(default_factory=dict)
    svg_source: IntakeV4SvgSource | None = None
    svg: IntakeV4SvgRuntime | None = None
    svg_source_text: str | None = None
    svg_analysis_json: dict[str, Any] | None = None
    path_geometry_summary: dict[str, Any] | None = None
    quote_geometry: dict[str, Any] | None = None
    layer_role_setup: IntakeV4LayerRoleSetup | None = None
    layer_role_review: dict[str, Any] | None = None
    product_composition_recommendation: dict[str, Any] | None = None
    product_composition_confirmed: dict[str, Any] | None = None
    product_truth: dict[str, Any] | None = None
    terminology_mode: str | None = None
    finish_setup: IntakeV4FinishSetup | None = None
    offer_scope: OfferScope | None = None
    offer_scope_confirmed: dict[str, Any] | None = None
    offer_scope_dependency_validation: SoldScopeDependencyValidationResult | None = None
    sheet_quote_override: dict[str, Any] | None = None


class IntakeV4WorkspaceCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    template_code: str = PILOT_V4_TEMPLATE_CODE
    client_name: str | None = None
    job_title: str | None = None
    intake_request_code: str | None = None
    offer_method: str | None = None
    analyzer_mode: Literal["analyzer_first", "template_hint", "template_locked"] | None = None
    template_hint_code: str | None = None
    selected_template_code: str | None = None
    source: str | None = None


class IntakeV4EnsureWorkspaceForIntakeRequestBody(BaseModel):
    intake_request_code: str = Field(min_length=1, max_length=64)
    offer_method: str | None = None
    analyzer_mode: Literal["analyzer_first", "template_hint", "template_locked"] | None = None
    template_hint_code: str | None = None
    selected_template_code: str | None = None
    source: str | None = None


class IntakeV4ProductCompositionConfirmationRequest(BaseModel):
    confirmed: bool = True
    items: list[dict[str, Any]] = Field(default_factory=list)
    operator_note: str | None = None


class IntakeV4OfferScopeSaveRequest(BaseModel):
    mode: OfferScopeMode
    sold_modules: list[CanonicalSoldModule] = Field(default_factory=list)
    confirmed: bool = True
    operator_note: str | None = None
    dependency_confirmation_codes: list[str] = Field(default_factory=list)


class IntakeV4WorkspaceResponse(BaseModel):
    id: str
    workspace_code: str
    title: str
    template_code: str
    status: WorkspaceDraftStatus
    payload: dict[str, Any]
    readiness_status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class IntakeV4WorkspaceListResponse(BaseModel):
    items: list[IntakeV4WorkspaceResponse] = Field(default_factory=list)
    total: int = 0


class IntakeV4LayerRoleUpdateItem(BaseModel):
    layer_key: str
    confirmed_role: str
    confirmation_state: LayerConfirmationState = "confirmed"
    operator_note: str | None = None


class IntakeV4LayerRoleUpdateRequest(BaseModel):
    layers: list[IntakeV4LayerRoleUpdateItem]


class IntakeV4SvgUploadResponse(BaseModel):
    workspace: IntakeV4WorkspaceResponse
    layer_role_setup: IntakeV4LayerRoleSetup
    warnings: list[str] = Field(default_factory=list)


class IntakeV4ProductSystemOperation(BaseModel):
    code: str
    label: str
    workcenter: str | None = None
    sequence: int
    component_ref: str | None = None
    active: bool = True
    inactive_reason: str | None = None


class IntakeV4ProductSystemModuleLink(BaseModel):
    module_template_id: int | None = None
    module_template_code: str
    module_template_label: str | None = None
    relation_type: str = "optional_addon"
    trigger_field: str
    trigger_value: Any = None
    input_mapping: dict[str, Any] = Field(default_factory=dict)
    default_values: dict[str, Any] = Field(default_factory=dict)
    pricing_mode: str = "separate_quote_line"
    execution_mode: str = "linked_child_work"
    active: bool = True
    notes: str | None = None


class IntakeV4ProductSystemBindingResponse(BaseModel):
    workspace_id: str
    template_code: str
    template_id: int | None = None
    template_label: str | None = None
    product_family: str | None = None
    product_family_name: str | None = None
    operation_count: int = 0
    component_count: int = 0
    template_active: bool = False
    module_links: list[IntakeV4ProductSystemModuleLink] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class IntakeV4TaskPreviewItem(BaseModel):
    operation_code: str
    label: str
    workcenter: str | None = None
    sequence: int
    component_ref: str | None = None
    active: bool
    inactive_reason: str | None = None
    source: Literal["product_system", "operation_catalog"] = "operation_catalog"
    depends_on: list[str] = Field(default_factory=list)
    required_skill: list[str] = Field(default_factory=list)
    active_reason: str | None = None
    operator_instruction: str | None = None


class IntakeV4TaskPreviewResponse(BaseModel):
    workspace_id: str
    template_code: str
    items: list[IntakeV4TaskPreviewItem] = Field(default_factory=list)
    preview_only: bool = True
    operation_flags: dict[str, Any] | None = None
    preview_engine: str = "v3_operation_catalog"


class IntakeV4PricingInputPreviewResponse(BaseModel):
    workspace_id: str
    template_code: str
    is_ready_for_quote: bool = False
    adapter_status: str = "blocked"
    adapter_blockers: list[str] = Field(default_factory=list)
    adapter_warnings: list[str] = Field(default_factory=list)
    quote_input_payload: dict[str, Any] = Field(default_factory=dict)
    operation_flags: dict[str, Any] = Field(default_factory=dict)
    production_counts: dict[str, Any] = Field(default_factory=dict)
    finish_summary: dict[str, Any] = Field(default_factory=dict)
    readiness_status: str | None = None
    requires_grouped_finish_review: bool = False
    preview_only: bool = True


class IntakeV4MaterialBreakdownWarning(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    source: str


class IntakeV4SheetQuoteRecommendedAutoCandidate(BaseModel):
    source: str
    area_sqm: float | None = None
    buffer_percent: float = 5.0
    confidence: Literal["low", "medium", "high"] = "low"
    reason: str = ""


class IntakeV4SheetQuoteSelectionPreview(BaseModel):
    selected_source: str
    final_area_sqm: float | None = None
    selection_mode: Literal["current_floor", "auto_candidate_preview", "manual_override_preview"] = (
        "current_floor"
    )
    is_applied_to_quote: bool = False


class IntakeV4SheetQuoteOperatorOverridePreview(BaseModel):
    enabled: bool = False
    width_cm: float | None = None
    height_cm: float | None = None
    area_sqm: float | None = None
    note: str | None = None


class IntakeV4SheetQuoteMaterialCandidates(BaseModel):
    """Debug/compare sheet material quote area candidates — does not drive pricing alone."""

    eligible_face_area_sqm: float | None = None
    placement_footprint_face_sqm: float | None = None
    face_union_bbox_sqm: float | None = None
    layout_occupied_area_sqm: float | None = None
    full_sheet_allocation_sqm: float | None = None
    unknown_placement_sqm: float | None = None
    orphan_defs_split_placement_sqm: float | None = None
    operator_manual_footprint_sqm: float | None = None
    operator_manual_footprint_width_cm: float | None = None
    operator_manual_footprint_height_cm: float | None = None
    operator_manual_use_for_quote_estimate: bool = False
    selected_quote_sheet_area_sqm: float | None = None
    selected_quote_sheet_area_source: str | None = None
    child_part_bbox_sum_sqm: float | None = None
    semantic_group_bbox_sum_sqm: float | None = None
    design_space_union_bbox_sqm: float | None = None
    design_space_union_bbox_with_buffer_sqm: float | None = None
    nesting_shelf_occupied_sqm: float | None = None
    recommended_auto_candidate: IntakeV4SheetQuoteRecommendedAutoCandidate | None = None
    requires_manual_review: bool = False
    manual_review_reason: str | None = None
    operator_override: IntakeV4SheetQuoteOperatorOverridePreview | None = None
    selection: IntakeV4SheetQuoteSelectionPreview | None = None


class IntakeV4SheetFootprintOverrideRequest(BaseModel):
    selected_footprint_source: str = Field(
        default="operator_manual_footprint",
        description=(
            "Operator-selected footprint source for internal material review: "
            "eligible_area_floor, face_union_bbox, layout_occupied_area, "
            "operator_manual_footprint, full_sheet_allocation."
        ),
    )
    width_cm: float | None = Field(default=None, gt=0, description="Required for operator_manual_footprint.")
    height_cm: float | None = Field(default=None, gt=0, description="Required for operator_manual_footprint.")
    reason: str = Field(default="", max_length=500)
    applies_to: list[str] = Field(
        default_factory=lambda: ["plexiglas_face", "forex_backing"],
        description="Material keys receiving the selected footprint when enabled for estimate.",
    )
    use_for_quote_estimate: bool = Field(
        default=True,
        description="When true, internal material estimate uses the selected footprint source.",
    )


class IntakeV4SheetFootprintOverrideResponse(BaseModel):
    enabled: bool = True
    source: Literal["operator_manual_footprint"] = "operator_manual_footprint"
    selected_footprint_source: str | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    area_sqm: float | None = None
    reason: str = ""
    applies_to: list[str] = Field(default_factory=list)
    use_for_quote_estimate: bool = False
    created_by: str | None = None
    created_at: str | None = None


class IntakeV4ReanalyzePreviewRequest(BaseModel):
    svg_analysis_json: dict[str, Any] = Field(
        description="Fresh client-side nest2 analysis JSON for read-only compare (not persisted).",
    )


class IntakeV4ReanalyzePreviewSnapshot(BaseModel):
    orphan_defs_split_placement_sqm: float | None = None
    placements_count: int = 0
    layout_occupied_sqm: float | None = None
    face_union_bbox_sqm: float | None = None
    selected_quantity_sqm: float | None = None
    requires_manual_review: bool = False
    manual_review_reason: str | None = None


class IntakeV4ReanalyzePreviewResponse(BaseModel):
    workspace_id: str
    before: IntakeV4ReanalyzePreviewSnapshot | None = None
    after: IntakeV4ReanalyzePreviewSnapshot | None = None
    selected_quantity_unchanged: bool = False
    persists_changes: bool = False
    stale_snapshot_detected: bool = False
    preview_available: bool = False


class IntakeV4NestingMaterialRow(BaseModel):
    material_key: str
    display_name: str
    nesting_kind: Literal["sheet", "roll"]
    config_id: str | None = None
    source_layer: str | None = None
    quantity: float = 0.0
    unit: str
    efficiency_percent: float | None = None
    waste_area_sqm: float | None = None
    sheets_used: int | None = None
    consumed_length_mm: float | None = None


class IntakeV4MaterialQuantityRow(BaseModel):
    material_key: str
    display_name: str
    category: Literal["material", "consumable", "nesting"]
    quantity: float = 0.0
    unit: str
    quantity_source: str
    quantity_quality: str
    waste_percent: float | None = None
    quantity_with_waste: float = 0.0
    registry_code: str | None = None
    unit_price: float | None = None
    currency: str = "EUR"
    material_cost: float | None = None
    price_source: str = "missing"
    warnings: list[str] = Field(default_factory=list)
    # Quote material costing contract (estimate for quoting — not stock consumption).
    material_code: str | None = None
    material_name: str | None = None
    quantity_basis: str | None = None
    base_quantity: float | None = None
    priced_quantity: float | None = None
    estimated_cost: float | None = None
    confidence: str = "estimate_for_quote"
    consumption_mode: Literal["quote_estimate"] = "quote_estimate"
    source_part_ids: list[str] = Field(default_factory=list)
    trace_markers: list[str] = Field(default_factory=list)


class IntakeV4MaterialBreakdownTotals(BaseModel):
    material_cost_total: float = 0.0
    estimated_cost_total: float = 0.0
    currency: str = "EUR"
    contains_estimates: bool = False
    contains_missing_prices: bool = False


class IntakeV4CncOperationRow(BaseModel):
    """CNC operation preview row — operation/labor, not a material consumption row."""

    key: str
    display_name: str
    operation_type: str
    material_family: str | None = None
    material_name: str | None = None
    thickness_mm: float | None = None
    quantity: float = 0.0
    unit: str = "ml"
    basis_key: str = ""
    basis_label: str = ""
    passes: int = 1
    depth_per_pass_mm: float | None = None
    owner_pass_override: bool = False
    operation_equivalent_quantity: float | None = None
    operation_equivalent_unit: str | None = None
    pricing_rate_key: str | None = None
    unit_price: float | None = None
    estimated_cost: float | None = None
    pricing_status: str = "missing_rate"
    tpl_operation_key: str | None = None
    dossier_operation_key: str | None = None
    operation_catalog_key: str | None = None
    production_task_type: str | None = None
    workstation_key: str | None = None
    required_skill_key: str | None = None
    registry_skill_code: str | None = None
    machine_type: str | None = None
    required_machine_key: str | None = None
    workcenter_code: str | None = None
    operational_operation_code: str | None = None
    resource_mapping_status: Literal["mapped", "pending_mapping"] = "pending_mapping"
    mapping_gaps: list[str] = Field(default_factory=list)
    material_key: str | None = None
    consumes_stock_now: bool = False
    creates_task_now: bool = False
    warnings: list[str] = Field(default_factory=list)


class IntakeV4EdgeCantOperationRow(BaseModel):
    """Edge/cant operation preview row — separate from CNC operation_rows."""

    key: str
    display_name: str
    operation_type: str
    material_family: str | None = None
    material_name: str | None = None
    thickness_mm: float | None = None
    quantity: float = 0.0
    unit: str = "ml"
    basis_key: str = ""
    basis_label: str = ""
    passes: int = 1
    depth_per_pass_mm: float | None = None
    owner_pass_override: bool = False
    operation_equivalent_quantity: float | None = None
    operation_equivalent_unit: str | None = None
    pricing_rate_key: str | None = None
    unit_price: float | None = None
    estimated_cost: float | None = None
    pricing_status: str = "missing_rate"
    tpl_operation_key: str | None = None
    dossier_operation_key: str | None = None
    operation_catalog_key: str | None = None
    production_task_type: str | None = None
    workstation_key: str | None = None
    required_skill_key: str | None = None
    registry_skill_code: str | None = None
    machine_type: str | None = None
    required_machine_key: str | None = None
    workcenter_code: str | None = None
    operational_operation_code: str | None = None
    resource_mapping_status: Literal["mapped", "pending_mapping"] = "pending_mapping"
    mapping_gaps: list[str] = Field(default_factory=list)
    material_key: str | None = None
    consumes_stock_now: bool = False
    creates_task_now: bool = False
    source: str = "shared_edge_cant_rules"
    warnings: list[str] = Field(default_factory=list)


class IntakeV4NestingPreviewWarning(BaseModel):
    code: str
    severity: str = "info"
    message: str


class IntakeV4NestingPreviewSheetLayout(BaseModel):
    config_id: str
    display_label: str
    sheet_width_mm: float | None = None
    sheet_length_mm: float | None = None
    material_target: str | None = None
    sheets_used: int = 0
    used_sheet_area_sqm: float | None = None
    parts_bounding_area_sqm: float | None = None
    efficiency_percent: float | None = None
    placed_items_count: int = 0
    unplaced_items_count: int = 0
    placement_count: int = 0
    is_active_for_breakdown: bool = False
    layout_kind: Literal["active_breakdown", "alternative_variant"] = "alternative_variant"
    breakdown_note: str | None = None


class IntakeV4NestingPreviewRollJob(BaseModel):
    roll_config_id: str
    roll_width_mm: float | None = None
    source_layer_name: str | None = None
    layer_role: str | None = None
    color_key: str | None = None
    used_roll_area_sqm: float | None = None
    consumed_length_mm: float | None = None
    placed_items_count: int = 0
    efficiency_percent: float | None = None
    is_active_for_breakdown: bool = False
    layout_kind: Literal["active_breakdown", "alternative_variant"] = "alternative_variant"
    material_target: str | None = None


class IntakeV4NestingPreviewSummary(BaseModel):
    sheet_layouts: int = 0
    roll_layouts: int = 0
    active_sheet_layouts: int = 0
    active_roll_layouts: int = 0
    alternative_layouts: int = 0
    nestable_parts: int = 0
    holes_excluded: int = 0
    artwork_parts: int = 0


class IntakeV4NestingPreviewBoundary(BaseModel):
    preview_only: bool = True
    mutates_inventory: bool = False
    uses_stock: bool = False
    creates_execution_plan: bool = False
    creates_execution_tasks: bool = False
    consumes_stock: bool = False
    used_for_stock_reservation: bool = False


class IntakeV4NestingPreviewPartRow(BaseModel):
    part_id: str
    source_layer_name: str | None = None
    layer_role: str | None = None
    part_kind: Literal["face_part", "artwork_part", "hole", "backing_part", "unknown"] = "unknown"
    material_intent: Literal["face", "backing"] | None = None
    nestable: bool = False
    counts_as_material_piece: bool = False
    bounds_width_mm: float | None = None
    bounds_height_mm: float | None = None
    area_sqm: float | None = None
    perimeter_ml: float | None = None
    nesting_target: str | None = None
    placement_x_mm: float | None = None
    placement_y_mm: float | None = None
    counted_in_material_lines: list[str] = Field(default_factory=list)
    preview_shape: Literal["bounding_box"] = "bounding_box"


class IntakeV4NestingPreviewMaterialTrace(BaseModel):
    material_key: str
    display_name: str
    reported_quantity: float = 0.0
    unit: str
    quantity_basis: str | None = None
    quantity_source: str | None = None
    source_part_ids: list[str] = Field(default_factory=list)
    active_sheet_config_id: str | None = None
    breakdown_mode: str | None = None
    uses_placement_footprint: bool = False
    uses_full_sheet_stock_proration: bool = False


class IntakeV4NestingPreviewResponse(BaseModel):
    preview_mode: Literal["bounding_box_mvp"] = "bounding_box_mvp"
    preview_only: bool = True
    mutates_inventory: bool = False
    uses_stock: bool = False
    source: str = "intake_v4_workspace"
    workspace_id: str | None = None
    disclaimer: str
    active_sheet_config_id: str | None = None
    breakdown_uses_single_active_layout: bool = True
    boundary: IntakeV4NestingPreviewBoundary = Field(default_factory=IntakeV4NestingPreviewBoundary)
    summary: IntakeV4NestingPreviewSummary = Field(default_factory=IntakeV4NestingPreviewSummary)
    sheets: list[IntakeV4NestingPreviewSheetLayout] = Field(default_factory=list)
    rolls: list[IntakeV4NestingPreviewRollJob] = Field(default_factory=list)
    parts: list[IntakeV4NestingPreviewPartRow] = Field(default_factory=list)
    material_traces: list[IntakeV4NestingPreviewMaterialTrace] = Field(default_factory=list)
    warnings: list[IntakeV4NestingPreviewWarning] = Field(default_factory=list)


class IntakeV4MaterialBreakdownResponse(BaseModel):
    workspace_id: str
    template_code: str
    breakdown_scope: str = "quote_material_cost_estimate"
    costing_purpose: str = "quote_material_cost_estimate"
    consumption_mode: Literal["quote_estimate_not_stock"] = "quote_estimate_not_stock"
    policy_version: str = "intake_v4_quote_material_cost_estimate_v1"
    quote_waste_percent_default: float = 20.0
    includes_nesting: bool = True
    includes_consumables: bool = True
    includes_pricing_hints: bool = True
    stock_consumption: bool = False
    nesting_rows: list[IntakeV4NestingMaterialRow] = Field(default_factory=list)
    material_rows: list[IntakeV4MaterialQuantityRow] = Field(default_factory=list)
    consumable_rows: list[IntakeV4MaterialQuantityRow] = Field(default_factory=list)
    operation_rows: list[IntakeV4CncOperationRow] = Field(default_factory=list)
    edge_cant_operation_rows: list[IntakeV4EdgeCantOperationRow] = Field(default_factory=list)
    totals: IntakeV4MaterialBreakdownTotals = Field(default_factory=IntakeV4MaterialBreakdownTotals)
    warnings: list[IntakeV4MaterialBreakdownWarning] = Field(default_factory=list)
    nesting_preview: IntakeV4NestingPreviewResponse | None = None
    sheet_quote_material_candidates: IntakeV4SheetQuoteMaterialCandidates | None = None


class IntakeV4InternalDraftQuoteConfirmationRequest(BaseModel):
    confirmed: bool = True


class IntakeV4CreateDraftQuoteRequest(BaseModel):
    confirm_create_draft_only: bool
    confirm_no_order: bool
    confirm_no_execution: bool
    confirm_no_inventory: bool
    confirm_internal_draft_quote: bool
    decision_reason: str = "Operator approved draft quote from Intake V4 Confirm step."
    client_analysis_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="SHA-256 hex of SVG bytes the operator confirms (must match persisted svg_source.file_hash).",
    )

    @model_validator(mode="after")
    def _require_explicit_confirmations(self) -> IntakeV4CreateDraftQuoteRequest:
        if not all(
            (
                self.confirm_create_draft_only,
                self.confirm_no_order,
                self.confirm_no_execution,
                self.confirm_no_inventory,
                self.confirm_internal_draft_quote,
            )
        ):
            raise ValueError(
                "confirm_create_draft_only, confirm_no_order, confirm_no_execution, "
                "confirm_no_inventory, and confirm_internal_draft_quote must all be true"
            )
        return self


class IntakeV4CreateDraftQuoteResponse(BaseModel):
    quote_created: bool
    quote_id: int
    quote_code: str
    quote_status: str
    source_module: str
    source_workspace_id: str
    quote_input_payload: dict[str, Any] = Field(default_factory=dict)
    snapshot_attached: bool = True
    requires_pricing_review: bool = True
    client_send_allowed: bool = False
    accept_allowed: bool = False
    convert_to_order_allowed: bool = False
    production_allowed: bool = False
    order_created: bool = False
    execution_plan_created: bool = False
    inventory_mutated: bool = False


class IntakeV4QuoteHandoffPreviewResponse(BaseModel):
    workspace_id: str
    workspace_readiness_status: str | None = None
    handoff_allowed: bool = False
    status_label: Literal[
        "HANDOFF_ALLOWED",
        "QUOTE_HANDOFF_BLOCKED",
        "REVIEW_REQUIRED",
        "ACTION_NEEDED",
        "READY_FOR_INTERNAL_DRAFT_REVIEW",
    ] = "QUOTE_HANDOFF_BLOCKED"
    blockers: list[str] = Field(default_factory=list)
    can_create_internal_draft_quote: bool = False
    requires_operator_confirmation: bool = True
    operator_confirmation_complete: bool = False
    fatal_blockers: list[str] = Field(default_factory=list)
    review_warnings: list[str] = Field(default_factory=list)
    # Aggregate info traces (dossier/authority/identity) — visible, never gate accept/convert/production.
    diagnostic_warnings: list[str] = Field(default_factory=list)
    client_send_allowed: bool = False
    accept_allowed: bool = False
    convert_to_order_allowed: bool = False
    production_allowed: bool = False
    preview_only: bool = True


class IntakeV4ProductionHandoffMaterialJob(BaseModel):
    job_key: str
    material_code: str | None = None
    role: str | None = None
    display_name: str
    quantity_basis: str | None = None
    quantity: float = 0.0
    priced_quantity: float | None = None
    waste_percent: float | None = None
    unit: str
    source: str = "intake_v4_material_breakdown"
    confidence: str = "estimate_for_quote"
    creates_stock_reservation: bool = False
    quote_estimate_only: bool = True
    warnings: list[str] = Field(default_factory=list)


class IntakeV4ProductionHandoffTemplateAlignment(BaseModel):
    status: Literal["aligned", "partial", "missing", "not_applicable"] = "missing"
    provisional: bool = False
    source: str = "TPL-VOLUMETRIC-LETTERS canonical operation registry"
    missing_keys: list[str] = Field(default_factory=list)
    partial_keys: list[str] = Field(default_factory=list)


class IntakeV4ProductionHandoffOperationGroup(BaseModel):
    group_key: str
    title: str
    description: str | None = None
    station_hint: str | None = None
    operation_codes: list[str] = Field(default_factory=list)
    legacy_operation_codes: list[str] = Field(default_factory=list)
    material_job_keys: list[str] = Field(default_factory=list)
    canonical_operation_keys: list[str] = Field(default_factory=list)
    operation_code_source: Literal["product_system_dossier", "operation_catalog_compat"] = (
        "product_system_dossier"
    )
    template_alignment: IntakeV4ProductionHandoffTemplateAlignment | None = None
    active: bool = True
    inactive_reason: str | None = None


class IntakeV4ProductionHandoffTaskSeedPreview(BaseModel):
    task_key: str
    title: str
    operation_code: str
    legacy_operation_code: str | None = None
    canonical_operation_key: str | None = None
    canonical_operation_keys: list[str] = Field(default_factory=list)
    dossier_operation_key: str | None = None
    future_execution_task_type: str | None = None
    operation_code_source: Literal["product_system_dossier", "operation_catalog_compat"] = (
        "product_system_dossier"
    )
    station_hint: str | None = None
    role_hint: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    source_material_jobs: list[str] = Field(default_factory=list)
    creates_execution_task: bool = False
    active: bool = True
    inactive_reason: str | None = None
    notes: list[str] = Field(default_factory=list)


class IntakeV4ProductionHandoffIssue(BaseModel):
    code: str
    severity: Literal["blocking", "warning", "info"] = "warning"
    message: str
    source: str


class IntakeV4CncOperationDryRunCandidate(BaseModel):
    """CNC preview candidate derived from material breakdown operation_rows."""

    candidate_key: str
    title: str
    operation_key: str
    operation_type: str
    material_key: str | None = None
    material_label: str | None = None
    quantity: float = 0.0
    unit: str = "ml"
    operation_equivalent_quantity: float | None = None
    passes: int = 1
    owner_pass_override: bool = False
    basis_label: str = ""
    pricing_status: str = "missing_rate"
    estimated_cost: float | None = None
    required_machine_key: str | None = None
    machine_type: str | None = None
    workstation_key: str | None = None
    required_skill_key: str | None = None
    registry_skill_code: str | None = None
    operation_catalog_key: str | None = None
    dossier_operation_key: str | None = None
    tpl_operation_key: str | None = None
    production_task_type: str | None = None
    resource_mapping_status: Literal["mapped", "pending_mapping"] = "pending_mapping"
    mapping_gaps: list[str] = Field(default_factory=list)
    consumes_stock_now: bool = False
    creates_task_now: bool = False
    source: str = "operation_rows"
    warnings: list[str] = Field(default_factory=list)


class IntakeV4EdgeCantOperationDryRunCandidate(BaseModel):
    """Edge/cant preview candidate derived from material breakdown edge_cant_operation_rows."""

    candidate_key: str
    title: str
    operation_key: str
    operation_type: str
    material_key: str | None = None
    material_label: str | None = None
    quantity: float = 0.0
    unit: str = "ml"
    operation_equivalent_quantity: float | None = None
    passes: int = 1
    owner_pass_override: bool = False
    basis_label: str = ""
    pricing_status: str = "missing_rate"
    estimated_cost: float | None = None
    required_machine_key: str | None = None
    machine_type: str | None = None
    workstation_key: str | None = None
    required_skill_key: str | None = None
    registry_skill_code: str | None = None
    operation_catalog_key: str | None = None
    dossier_operation_key: str | None = None
    tpl_operation_key: str | None = None
    production_task_type: str | None = None
    resource_mapping_status: Literal["mapped", "pending_mapping"] = "pending_mapping"
    mapping_gaps: list[str] = Field(default_factory=list)
    consumes_stock_now: bool = False
    creates_task_now: bool = False
    source: str = "shared_edge_cant_rules"
    warnings: list[str] = Field(default_factory=list)


class IntakeV4ProductionHandoffPreviewResponse(BaseModel):
    workspace_id: str
    template_code: str
    handoff_mode: Literal["preview_only"] = "preview_only"
    stock_consumption: bool = False
    creates_execution_tasks: bool = False
    creates_stock_reservations: bool = False
    quote_estimate_only: bool = True
    production_notes: list[str] = Field(default_factory=list)
    material_jobs: list[IntakeV4ProductionHandoffMaterialJob] = Field(default_factory=list)
    operation_groups: list[IntakeV4ProductionHandoffOperationGroup] = Field(default_factory=list)
    task_seed_preview: list[IntakeV4ProductionHandoffTaskSeedPreview] = Field(default_factory=list)
    cnc_operation_candidates: list[IntakeV4CncOperationDryRunCandidate] = Field(default_factory=list)
    cnc_task_source: str | None = None
    compat_cnc_mapping_used: bool = False
    legacy_cnc_mapping_used: bool = False
    edge_cant_operation_candidates: list[IntakeV4EdgeCantOperationDryRunCandidate] = Field(
        default_factory=list
    )
    edge_cant_task_source: str | None = None
    blockers: list[IntakeV4ProductionHandoffIssue] = Field(default_factory=list)
    warnings: list[IntakeV4ProductionHandoffIssue] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


TEMPLATE_OPTION_CONTRACT_VERSION = "tpl_volumetric_option_contract_v1"


class IntakeV4TemplateContractCanonicalRow(BaseModel):
    discovered_option: str
    blueprint_rule: str
    template_option: str
    material_intent: str
    pricing_code_blk18: str
    costengine_field: str
    production_material_job: str
    production_operation_group: str
    future_task_seed: str
    status: Literal["aligned", "partial", "missing", "provisional"]
    notes: str = ""


class IntakeV4TemplateContractIssue(BaseModel):
    code: str
    severity: Literal["blocking", "warning", "info"] = "warning"
    message: str
    source: str
    option_key: str | None = None


class IntakeV4TemplateFormContractField(BaseModel):
    field_key: str
    label: str
    owner: Literal["product_system_dossier", "intake_v4_operator", "pricing_registry", "quote_wizard"]
    current_runtime_owner: Literal["product_system_dossier", "intake_v4_hardcoded_form", "quote_wizard_default"]
    alignment_status: Literal["canonical", "mapped", "adapter_only", "missing_in_v4"]
    allowed_values: list[Any] = Field(default_factory=list)
    default_value: Any = None
    v4_field_key: str | None = None
    source: str
    notes: list[str] = Field(default_factory=list)


class IntakeV4TemplateFormContractResponse(BaseModel):
    workspace_id: str
    template_code: str
    contract_version: str = TEMPLATE_OPTION_CONTRACT_VERSION
    intended_form_authority: str = "ProductSystem + Blueprint Dossier variants_json + quote_input contract"
    current_runtime_authority: str = "Intake V4 hardcoded form with ProductSystem binding and adapter warnings"
    alignment_status: Literal["aligned", "partial", "blocked"] = "partial"
    template_active: bool = False
    dossier_status: str | None = None
    dossier_source: Literal[
        "product_blueprint_dossier",
        "static_contract_fallback",
        "canonical_template_contract",
    ] = "static_contract_fallback"
    ui_must_not_invent_final_options: bool = True
    variant_fields: list[IntakeV4TemplateFormContractField] = Field(default_factory=list)
    canonical_rows: list[IntakeV4TemplateContractCanonicalRow] = Field(default_factory=list)
    warnings: list[IntakeV4TemplateContractIssue] = Field(default_factory=list)
    blockers: list[IntakeV4TemplateContractIssue] = Field(default_factory=list)
    discovered_v4_values: dict[str, Any] = Field(default_factory=dict)


class IntakeV4TaskGenerationDryRunIssue(BaseModel):
    code: str
    severity: Literal["blocking", "warning", "info"] = "warning"
    message: str
    source: str


class IntakeV4TaskGenerationEstimatedInputs(BaseModel):
    material_codes: list[str] = Field(default_factory=list)
    quantity_basis: str | None = None
    quantity: float | None = None
    unit: str | None = None
    passes: int | None = None
    operation_equivalent_quantity: float | None = None
    owner_pass_override: bool | None = None
    basis_label: str | None = None
    pricing_status: str | None = None
    preview_source: str | None = None
    required_machine_key: str | None = None
    machine_type: str | None = None
    workstation_key: str | None = None
    required_skill_key: str | None = None
    registry_skill_code: str | None = None
    operation_catalog_key: str | None = None
    mapping_gaps: list[str] = Field(default_factory=list)
    consumes_stock_now: bool = False
    creates_task_now: bool = False


class IntakeV4TaskGenerationTaskCandidate(BaseModel):
    task_key: str
    title: str
    template_code: str
    template_backed: bool = True
    provisional: bool = False
    provisional_reason: str | None = None
    operation_key: str | None = None
    canonical_operation_key: str | None = None
    template_alignment_status: Literal["aligned", "partial", "missing", "not_applicable"] | None = None
    dossier_backed: bool = False
    critical_for_execution: bool = False
    future_execution_task_type: str | None = None
    operation_group: str | None = None
    station_hint: str | None = None
    role_hint: str | None = None
    source_material_jobs: list[str] = Field(default_factory=list)
    source_operation_groups: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    estimated_inputs: IntakeV4TaskGenerationEstimatedInputs = Field(
        default_factory=IntakeV4TaskGenerationEstimatedInputs
    )
    creates_execution_task: bool = False
    idempotency_key: str
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    active: bool = True
    inactive_reason: str | None = None


class IntakeV4TaskGenerationDependencyEdge(BaseModel):
    from_task_key: str
    to_task_key: str
    reason: str
    confidence: Literal["template_rule", "catalog_doc", "provisional"] = "template_rule"
    provisional: bool = False


class IntakeV4TaskGenerationIdempotencyEntry(BaseModel):
    task_key: str
    idempotency_key: str
    source_fingerprint: str
    duplicate_policy: str = "do_not_create_duplicate; require explicit regeneration"


class IntakeV4TaskGenerationAuditPreview(BaseModel):
    event_type: str = "intake_v4_task_generation_dry_run"
    entity_type: str = "IntakeV4Workspace"
    entity_id: str
    source: str = "intake_v4_task_generation_dry_run_service"
    would_create_count: int = 0
    blocked_count: int = 0
    provisional_count: int = 0
    analysis_hash: str | None = None
    finish_fingerprint: str | None = None
    template_code: str
    template_contract_version: str = TEMPLATE_OPTION_CONTRACT_VERSION


class IntakeV4TaskGenerationDryRunResponse(BaseModel):
    dry_run_mode: Literal["task_generation_preview_only"] = "task_generation_preview_only"
    creates_execution_tasks: bool = False
    writes_to_production: bool = False
    stock_consumption: bool = False
    dry_run_only: bool = True
    workspace_id: str
    template_code: str
    template_backed: bool = True
    can_generate_tasks: bool = False
    task_candidates: list[IntakeV4TaskGenerationTaskCandidate] = Field(default_factory=list)
    dependency_graph: list[IntakeV4TaskGenerationDependencyEdge] = Field(default_factory=list)
    idempotency_plan: list[IntakeV4TaskGenerationIdempotencyEntry] = Field(default_factory=list)
    blockers: list[IntakeV4TaskGenerationDryRunIssue] = Field(default_factory=list)
    warnings: list[IntakeV4TaskGenerationDryRunIssue] = Field(default_factory=list)
    audit_preview: IntakeV4TaskGenerationAuditPreview | None = None
    cnc_task_source: str | None = None
    cnc_operation_candidate_count: int = 0
    cnc_operation_candidates: list[IntakeV4CncOperationDryRunCandidate] = Field(default_factory=list)
    compat_cnc_mapping_used: bool = False
    legacy_cnc_mapping_used: bool = False
    edge_cant_operation_candidate_count: int = 0
    edge_cant_operation_candidates: list[IntakeV4EdgeCantOperationDryRunCandidate] = Field(
        default_factory=list
    )
    edge_cant_task_source: str | None = None
    summary: dict[str, Any] = Field(default_factory=dict)


FUTURE_GENERATION_CONTRACT_VERSION = "intake_v4_task_generation_v1"


class IntakeV4LinkedQuoteSummary(BaseModel):
    exists: bool = False
    quote_id: int | None = None
    quote_code: str | None = None
    status: str | None = None
    requires_pricing_review: bool | None = None
    snapshot_valid: bool = False
    analysis_hash_synced: bool | None = None


class IntakeV4LinkedOrderSummary(BaseModel):
    exists: bool = False
    order_id: int | None = None
    order_code: str | None = None
    status: str | None = None
    has_execution_plan: bool = False
    source_quote_id: int | None = None


class IntakeV4FutureGenerationContract(BaseModel):
    contract_version: str = FUTURE_GENERATION_CONTRACT_VERSION
    target_entity: Literal["Order"] = "Order"
    target_order_id: int | None = None
    requires_owner_confirmation: bool = True
    requires_idempotency_check: bool = True
    requires_analysis_hash_sync: bool = True
    requires_quote_accepted: bool = True
    requires_order_ready: bool = True
    would_create_execution_tasks: bool = False
    would_write_execution_plan: bool = False
    next_action_label: str = "Create production tasks"
    next_action_enabled: bool = False


class IntakeV4OrderBoundTaskReadinessResponse(BaseModel):
    readiness_mode: Literal["order_bound_task_generation_readiness"] = (
        "order_bound_task_generation_readiness"
    )
    creates_execution_tasks: bool = False
    writes_to_production: bool = False
    stock_consumption: bool = False
    dry_run_only: bool = True
    order_bound_readiness: bool = True
    workspace_id: str
    template_code: str
    linked_quote: IntakeV4LinkedQuoteSummary = Field(default_factory=IntakeV4LinkedQuoteSummary)
    linked_order: IntakeV4LinkedOrderSummary = Field(default_factory=IntakeV4LinkedOrderSummary)
    can_generate_real_tasks: bool = False
    can_generate_reason: str | None = None
    owner_confirmation_required: bool = True
    pricing_review: dict[str, Any] = Field(default_factory=dict)
    owner_approval: dict[str, Any] = Field(default_factory=dict)
    v4_order_conversion: dict[str, Any] = Field(default_factory=dict)
    blockers: list[IntakeV4TaskGenerationDryRunIssue] = Field(default_factory=list)
    warnings: list[IntakeV4TaskGenerationDryRunIssue] = Field(default_factory=list)
    dry_run_summary: dict[str, Any] = Field(default_factory=dict)
    idempotency_summary: dict[str, Any] = Field(default_factory=dict)
    pricing_status: dict[str, Any] = Field(default_factory=dict)
    template_contract_status: dict[str, Any] = Field(default_factory=dict)
    template_operation_alignment: dict[str, Any] = Field(default_factory=dict)
    analysis_hash_status: dict[str, Any] = Field(default_factory=dict)
    future_generation_contract: IntakeV4FutureGenerationContract = Field(
        default_factory=IntakeV4FutureGenerationContract
    )


class IntakeV4CompletePricingReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_quote_id: int | None = None
    expected_intake_code: str | None = None
    reviewer_confirmation: bool = False
    confirm_quote_stays_draft: bool = False
    confirm_no_order: bool = False
    confirm_no_execution: bool = False
    confirm_no_inventory: bool = False
    pricing_review_reason: str
    pricing_method: str = "quote_priced_review"
    client_analysis_hash: str | None = None


class IntakeV4OwnerApprovalRequest(BaseModel):
    decision_reason: str
    acknowledged_no_execution_tasks: bool = False
    acknowledged_no_stock_consumption: bool = False
    acknowledged_warnings: list[str] = Field(default_factory=list)
    acknowledged_blockers: list[str] = Field(default_factory=list)
    client_analysis_hash: str | None = None
    expected_quote_id: int | None = None


class IntakeV4AcceptQuoteRequest(BaseModel):
    expected_quote_id: int | None = None
    expected_intake_code: str | None = None
    accept_decision: str = "approved"
    accept_reason: str
    acceptance_source: str = "intake_v4_operator"
    reviewer_confirmation: bool = False
    confirm_pricing_review_completed: bool = False
    confirm_no_order: bool = False
    confirm_no_execution: bool = False
    confirm_no_inventory: bool = False
    confirm_convert_separate: bool = False
    confirm_owner_decisions_acknowledged: bool = False


class IntakeV4ConvertToOrderRequest(BaseModel):
    expected_quote_id: int | None = None
    expected_intake_code: str | None = None
    convert_decision: str = "approved"
    convert_reason: str = ""
    conversion_source: str = "intake_v4_operator"
    reviewer_confirmation: bool = False
    confirm_quote_accepted: bool = False
    confirm_pricing_review_completed: bool = False
    confirm_create_order_only: bool = False
    confirm_no_execution_plan: bool = False
    confirm_no_execution_tasks: bool = False
    confirm_no_inventory: bool = False
    confirm_production_separate: bool = False


class IntakeV4CommercialSpineStateResponse(BaseModel):
    quote_exists: bool = False
    is_iv4_quote: bool = False
    quote_id: int | None = None
    quote_code: str | None = None
    quote_status: str | None = None
    intake_code: str | None = None
    workspace_id: str | None = None
    requires_pricing_review: bool | None = None
    pricing_review: dict[str, Any] = Field(default_factory=dict)
    owner_approval: dict[str, Any] = Field(default_factory=dict)
    quote_accepted: bool = False
    quote_commercial_totals: dict[str, Any] = Field(default_factory=dict)
    v4_order_conversion: dict[str, Any] = Field(default_factory=dict)
    creates_execution_tasks: bool = False
    writes_execution_plan: bool = False
    stock_consumption: bool = False
    owner_approval_persisted: bool = False
    v4_quote_to_order_enabled: bool = True


AI_SEMANTIC_SUGGESTED_KIND = Literal[
    "letters",
    "logo_or_emblem",
    "artwork",
    "shape_symbol",
    "mixed",
    "unknown",
]


class IntakeV4AiSemanticClassificationBoundaryFlags(AiInformationalBoundaryFlags):
    """Intake V4 semantic assist boundary flags — alias of cross-cutting AI informational flags."""


class IntakeV4AiSemanticClassificationRenderPreview(BaseModel):
    available: bool = False
    png_preview_token: str | None = None
    note: str | None = None


class IntakeV4AiSemanticClassificationSystemClassification(BaseModel):
    counts_as_letters: bool = False
    counts_as_artwork: bool = False
    counts_as_logo: bool = False


class IntakeV4AiSemanticClassificationGroupGeometry(BaseModel):
    outer_contours_count: int = 0
    inner_holes_count: int = 0
    area_sqm: float | None = None
    outer_perimeter_ml: float | None = None
    inner_hole_perimeter_ml: float | None = None
    cutting_perimeter_ml: float | None = None
    return_perimeter_ml: float | None = None
    bbox_mm: dict[str, Any] | None = None


class IntakeV4AiSemanticClassificationGroup(BaseModel):
    group_id: str
    source_layer: str
    operator_role: str
    geometry: IntakeV4AiSemanticClassificationGroupGeometry
    current_system_classification: IntakeV4AiSemanticClassificationSystemClassification


class IntakeV4AiSemanticClassificationCandidatePayload(BaseModel):
    workspace_id: str
    template_id: str
    source_file_type: Literal["svg"] = "svg"
    render_preview: IntakeV4AiSemanticClassificationRenderPreview = Field(
        default_factory=IntakeV4AiSemanticClassificationRenderPreview
    )
    groups: list[IntakeV4AiSemanticClassificationGroup] = Field(default_factory=list)


class IntakeV4AiSemanticClassificationSuggestion(BaseModel):
    group_id: str
    suggested_kind: AI_SEMANTIC_SUGGESTED_KIND
    suggested_text: str | None = None
    suggested_label: str | None = None
    confidence: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    requires_operator_confirmation: bool = True
    boundary_flags: AiInformationalBoundaryFlags = Field(default_factory=AiInformationalBoundaryFlags)


class IntakeV4AiSemanticClassificationSuggestionResponse(BaseModel):
    schema_version: str = "ai_semantic_classification_suggestion_v1"
    suggestions: list[IntakeV4AiSemanticClassificationSuggestion] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class IntakeV4OperatorSemanticConfirmationContract(AiInformationalConfirmationContract):
    """Legacy name — same contract as AI informational confirmation."""


class IntakeV4AiSemanticClassificationPreviewResponse(BaseModel):
    workspace_id: str
    template_code: str
    preview_only: bool = True
    ai_not_called: bool = True
    candidate_payload: IntakeV4AiSemanticClassificationCandidatePayload
    mock_suggestion: IntakeV4AiSemanticClassificationSuggestionResponse
    boundary_flags: AiInformationalBoundaryFlags = Field(default_factory=AiInformationalBoundaryFlags)
    operator_confirmation_contract: AiInformationalConfirmationContract = Field(
        default_factory=AiInformationalConfirmationContract
    )


class IntakeV4AiInformationalAssistPreviewResponse(BaseModel):
    workspace_id: str
    template_code: str
    preview_only: bool = True
    ai_not_called: bool = True
    context: Literal["intake_v4_svg_review"] = "intake_v4_svg_review"
    candidate_payload: IntakeV4AiSemanticClassificationCandidatePayload
    mock_suggestions: list[AiInformationalSuggestionItem] = Field(default_factory=list)
    informational_envelope: AiInformationalSuggestionEnvelope
    boundary_flags: AiInformationalBoundaryFlags = Field(default_factory=AiInformationalBoundaryFlags)
    operator_confirmation_contract: AiInformationalConfirmationContract = Field(
        default_factory=AiInformationalConfirmationContract
    )
    mock_suggestion: IntakeV4AiSemanticClassificationSuggestionResponse | None = None


FaceBackPrepComponentKey = Literal["FACE_PLEXI", "BACK_FOREX", "GENERAL"]
FaceBackPrepTaskStation = Literal["prepress", "cnc", "finishing", "packing"]
FaceBackPrepCostRowStatus = Literal[
    "calculated",
    "missing_price",
    "manual_required",
    "optional",
    "calculated_when_enabled",
    "skipped",
]
FaceBackPrepPriceSource = Literal["fixed_rule", "prices_registry", "manual", "missing", "derived_candidate"]
FaceBackPrepPerimeterConfidence = Literal["high", "derived_candidate", "manual_required"]


class IntakeV4FaceBackPrepComponentSnapshot(BaseModel):
    material_key: str
    material_source: str = "prices_registry"
    registry_code: str | None = None
    thickness_mm: float
    area_sqm: float | None = None
    cut_length_ml: float | None = None
    shanfren_length_ml: float | None = None
    shanfren_required: bool = False
    shanfren_enabled: bool = False
    area_source: str | None = None
    cut_length_source: str | None = None
    shanfren_length_source: str | None = None


class IntakeV4FaceBackPrepComponents(BaseModel):
    face_plexi: IntakeV4FaceBackPrepComponentSnapshot
    back_forex: IntakeV4FaceBackPrepComponentSnapshot


class IntakeV4FaceBackPrepMaterialCostRow(BaseModel):
    component: FaceBackPrepComponentKey
    material_key: str
    material_label: str
    registry_code: str | None = None
    thickness_mm: float
    quantity: float
    unit: Literal["sqm"] = "sqm"
    unit_price: float | None = None
    currency: str = "EUR"
    price_source: FaceBackPrepPriceSource = "prices_registry"
    cost: float | None = None
    status: FaceBackPrepCostRowStatus = "calculated"


class IntakeV4FaceBackPrepOperationCostRow(BaseModel):
    operation_key: str
    label: str
    component: FaceBackPrepComponentKey
    task_key: str
    quantity: float
    unit: Literal["ml"] = "ml"
    unit_price: float | None = None
    pass_count: int = 1
    currency: str = "EUR"
    price_source: FaceBackPrepPriceSource = "fixed_rule"
    cost: float | None = None
    status: FaceBackPrepCostRowStatus = "calculated"
    perimeter_source: str | None = None
    perimeter_confidence: FaceBackPrepPerimeterConfidence | None = None
    is_vector_perimeter_source: bool = True


class IntakeV4FaceBackPrepTaskDraft(BaseModel):
    task_key: str
    label: str
    station: FaceBackPrepTaskStation
    component: FaceBackPrepComponentKey
    order_index: int
    depends_on: list[str] = Field(default_factory=list)
    cost_rows: list[str] = Field(default_factory=list)
    creates_real_task: bool = False
    preview_only: bool = True


class IntakeV4FaceBackPrepCostDraftTotals(BaseModel):
    material_cost: float | None = None
    operation_cost: float | None = None
    total_internal_cost: float | None = None
    currency: str = "EUR"


class IntakeV4FaceBackPrepCostDraftWarning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "error"] = "warning"
    source: str | None = None


class IntakeV4FaceBackPrepCostDraftResponse(BaseModel):
    workspace_id: str | None = None
    template_key: str = TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE
    version: str = TPL_VOLUMETRIC_FACE_BACK_PREP_V1_VERSION
    preview_only: bool = True
    currency: str = "EUR"
    components: IntakeV4FaceBackPrepComponents
    materials: list[IntakeV4FaceBackPrepMaterialCostRow] = Field(default_factory=list)
    operations: list[IntakeV4FaceBackPrepOperationCostRow] = Field(default_factory=list)
    task_drafts: list[IntakeV4FaceBackPrepTaskDraft] = Field(default_factory=list)
    totals: IntakeV4FaceBackPrepCostDraftTotals = Field(default_factory=IntakeV4FaceBackPrepCostDraftTotals)
    missing_prices: list[str] = Field(default_factory=list)
    manual_inputs_required: list[str] = Field(default_factory=list)
    warnings: list[IntakeV4FaceBackPrepCostDraftWarning] = Field(default_factory=list)
    creates_real_tasks: bool = False
    consumes_stock: bool = False
    creates_quote: bool = False
    cnc_rate_eur_per_ml: float = 1.5
