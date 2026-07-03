"""Intake V3 Pydantic contracts — greenfield intake workspace shapes (no UI, no DB migration)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from data_models.intake_v3_contracts import (
    INTAKE_V3_CONTRACT_VERSION,
    INTAKE_V3_SCHEMA_VERSION,
    PILOT_TEMPLATE_CODE,
    SUPPORT_MODE_NO_SHARED,
)

# ---------------------------------------------------------------------------
# Shared literals
# ---------------------------------------------------------------------------

ReadinessStatus = Literal[
    "draft",
    "in_progress",
    "blocked_for_quote",
    "ready_for_quote",
    "quote_created",
    "production_handoff_ready",
]

ReadinessSeverity = Literal["blocker", "warning"]
ConfirmationStatus = Literal["pending", "confirmed", "rejected"]
AssignmentMode = Literal["all", "group", "letter_custom"]
ContourRole = Literal["outer", "inner_hole", "guide", "ignored", "unknown"]
GroupingMode = Literal["none", "by_word", "by_color", "by_operator_group", "custom"]
RawObjectType = Literal["path", "polygon", "rect", "group", "compound_path", "unknown"]
RawRoleGuess = Literal[
    "letter_candidate",
    "inner_hole_candidate",
    "guide_candidate",
    "ignored_candidate",
    "unknown",
]
EstimateStatus = Literal["not_started", "partial", "complete"]
MaterialItemEstimateStatus = Literal[
    "requires_geometry", "estimated", "owner_input_required", "not_started", "partial", "complete"
]
AdapterStatus = Literal["not_built", "ready", "blocked", "warnings"]

FinishType = Literal[
    "none",
    "vinyl",
    "paint",
    "raw_material",
    "oracal_8500",
    "oracal_651",
    "white_face",
    "printed_vinyl",
    "raw",
    "prefinished",
    "oracal_wrapped",
    "painted",
    "other",
]
FinishSource = Literal["face", "return"]
SheetSourceComponent = Literal["face", "backing", "panel", "other"]


# ---------------------------------------------------------------------------
# 5.1 ClientRequest
# ---------------------------------------------------------------------------


class ClientRequest(BaseModel):
    client_id: str | None = None
    client_name: str = ""
    request_code: str = ""
    job_title: str = ""
    delivery_type: str | None = None
    mounting_intent: str | None = None
    notes: str | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    depth_mm: float | None = None


# ---------------------------------------------------------------------------
# 5.2 ProductSelection
# ---------------------------------------------------------------------------


class ProductSelection(BaseModel):
    template_code: str = PILOT_TEMPLATE_CODE
    product_family: str | None = None
    product_variant: str | None = None
    template_version: str | None = None
    pilot_scope: bool = True


# ---------------------------------------------------------------------------
# 5.3 VectorAsset
# ---------------------------------------------------------------------------


class VectorAsset(BaseModel):
    file_name: str = ""
    file_hash: str | None = None
    mime_type: str | None = None
    source: str | None = None
    view_box: str | None = None
    declared_width_mm: float | None = None
    declared_height_mm: float | None = None
    upload_status: Literal["missing", "uploaded", "parsed", "failed"] = "missing"


# ---------------------------------------------------------------------------
# 5.4 RawSvgAnalysis — system detection only, NOT production truth
# ---------------------------------------------------------------------------


class RawSvgObject(BaseModel):
    object_id: str
    object_type: RawObjectType = "unknown"
    raw_role_guess: RawRoleGuess = "unknown"
    fill: str | None = None
    stroke: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    closed_contours: int = 0
    color: str | None = None
    layer_name: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)


class RawSvgAnalysis(BaseModel):
    """System detection only — NOT confirmed production model."""

    file_name: str = ""
    file_size_bytes: int = 0
    svg_width: str | None = None
    svg_height: str | None = None
    path_count: int = 0
    polygon_count: int = 0
    rect_count: int = 0
    closed_contour_count: int = 0
    open_path_count: int = 0
    raw_object_count: int = 0
    estimated_inner_hole_count: int = 0
    detected_color_count: int = 0
    detected_groups: list[str] = Field(default_factory=list)
    view_box: str | None = None
    warnings: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    raw_objects: list[RawSvgObject] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 5.6 LetterModel
# ---------------------------------------------------------------------------


class LetterGroup(BaseModel):
    group_id: str
    label: str = ""
    letter_ids: list[str] = Field(default_factory=list)


class LetterItem(BaseModel):
    letter_id: str
    label: str = ""
    word: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    outer_contour_ids: list[str] = Field(default_factory=list)
    inner_hole_ids: list[str] = Field(default_factory=list)
    has_inner_holes: bool = False
    linked_inner_hole_ids: list[str] = Field(default_factory=list)
    group_id: str | None = None
    sequence_index: int | None = None

    @model_validator(mode="after")
    def _sync_inner_hole_ids(self) -> LetterItem:
        if self.inner_hole_ids and not self.linked_inner_hole_ids:
            object.__setattr__(self, "linked_inner_hole_ids", list(self.inner_hole_ids))
        elif self.linked_inner_hole_ids and not self.inner_hole_ids:
            object.__setattr__(self, "inner_hole_ids", list(self.linked_inner_hole_ids))
        if self.inner_hole_ids or self.linked_inner_hole_ids:
            object.__setattr__(self, "has_inner_holes", True)
        return self


class LetterModel(BaseModel):
    letters: list[LetterItem] = Field(default_factory=list)
    groups: list[LetterGroup] = Field(default_factory=list)
    count_confirmed: bool = False
    grouping_mode: GroupingMode = "none"

    @property
    def letter_count(self) -> int:
        return len(self.letters)


# ---------------------------------------------------------------------------
# 5.7 CutContourModel
# ---------------------------------------------------------------------------


class CutContourItem(BaseModel):
    contour_id: str
    role: ContourRole = "unknown"
    parent_letter_id: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    include_in_cut: bool = True
    source_object_id: str | None = None
    sequence_index: int | None = None


class CutContourModel(BaseModel):
    contours: list[CutContourItem] = Field(default_factory=list)
    outer_contour_count: int = 0
    inner_hole_count: int = 0
    cut_contour_count: int = 0

    @model_validator(mode="after")
    def _sync_counts_from_contours(self) -> CutContourModel:
        if not self.contours:
            return self
        outer = sum(1 for c in self.contours if c.role == "outer" and c.include_in_cut)
        holes = sum(1 for c in self.contours if c.role == "inner_hole" and c.include_in_cut)
        cut = sum(1 for c in self.contours if c.include_in_cut and c.role not in {"guide", "ignored"})
        if self.outer_contour_count == 0 and outer:
            object.__setattr__(self, "outer_contour_count", outer)
        if self.inner_hole_count == 0 and holes:
            object.__setattr__(self, "inner_hole_count", holes)
        if self.cut_contour_count == 0 and cut:
            object.__setattr__(self, "cut_contour_count", cut)
        return self


# ---------------------------------------------------------------------------
# 5.5 ConfirmedProductionModel — operator-confirmed production truth
# ---------------------------------------------------------------------------


class ConfirmedProductionModel(BaseModel):
    confirmed_by_user_id: str | None = None
    confirmed_at: datetime | None = None
    letter_count: int = Field(ge=0)
    cut_contour_count: int = Field(ge=0)
    inner_hole_count: int = Field(ge=0, default=0)
    ignored_object_count: int = Field(ge=0, default=0)
    letter_model: LetterModel | None = None
    cut_contour_model: CutContourModel | None = None
    confirmation_status: ConfirmationStatus = "pending"
    source_raw_analysis_id: str | None = None
    operator_notes: str | None = None
    ignored_object_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _letter_count_is_not_auto_equal_to_contours(self) -> ConfirmedProductionModel:
        """Inner holes are not separate letters; letter_count may differ from cut_contour_count."""
        if self.letter_model and self.letter_model.letters:
            if self.letter_count != len(self.letter_model.letters):
                raise ValueError(
                    "letter_count must match letter_model.letters length when letters are provided"
                )
        hole_roles = 0
        if self.cut_contour_model:
            hole_roles = sum(
                1 for c in self.cut_contour_model.contours if c.role == "inner_hole"
            )
            if hole_roles and self.inner_hole_count == 0:
                object.__setattr__(self, "inner_hole_count", hole_roles)
        return self

    @property
    def is_confirmed(self) -> bool:
        return self.confirmation_status == "confirmed"


# ---------------------------------------------------------------------------
# Vector model validation (pure service output)
# ---------------------------------------------------------------------------


class VectorModelIssue(BaseModel):
    code: str
    severity: ReadinessSeverity
    message: str
    target_field: str | None = None


class VectorModelValidationResult(BaseModel):
    is_valid: bool = False
    blockers: list[VectorModelIssue] = Field(default_factory=list)
    warnings: list[VectorModelIssue] = Field(default_factory=list)
    summary: str = ""


# ---------------------------------------------------------------------------
# 5.8 FinishAssignment
# ---------------------------------------------------------------------------


class FaceFinishSpec(BaseModel):
    enabled: bool = True
    finish_type: FinishType = "none"
    material_code: str | None = None
    material_family: str | None = None
    color_code: str | None = None
    color_name: str | None = None
    face_vinyl_roll_width_mm: float | None = None
    requires_roll_width: bool = False
    confirmed: bool = False

    @property
    def material(self) -> str | None:
        return self.material_code

    @property
    def roll_width_mm(self) -> float | None:
        return self.face_vinyl_roll_width_mm

    @property
    def face_vinyl_active(self) -> bool:
        if not self.enabled:
            return False
        if self.finish_type in {"vinyl", "oracal_8500", "printed_vinyl"}:
            return True
        material = (self.material_code or "").lower()
        return "oracal" in material and "8500" in material


class ReturnFinishSpec(BaseModel):
    finish_type: FinishType = "none"
    material_code: str | None = None
    material_family: str | None = None
    color_code: str | None = None
    color_name: str | None = None
    return_depth_mm: float | None = None
    confirmed: bool = False

    @property
    def material(self) -> str | None:
        return self.material_code

    @property
    def depth_mm(self) -> float | None:
        return self.return_depth_mm

    @property
    def return_vinyl_active(self) -> bool:
        if self.return_painted_active:
            return False
        if self.finish_type in {"vinyl", "oracal_651", "oracal_wrapped"}:
            return True
        material = (self.material_code or "").lower()
        return "oracal" in material and "651" in material

    @property
    def return_painted_active(self) -> bool:
        return self.finish_type in {"paint", "painted"}

    @property
    def requires_vinyl_application(self) -> bool:
        return self.return_vinyl_active

    @property
    def requires_painting_after_assembly(self) -> bool:
        return self.return_painted_active


class BackingFinishSpec(BaseModel):
    material: str | None = None
    thickness_mm: float | None = None
    color: str | None = None
    bevel_enabled: bool | None = None
    confirmed: bool = False


class FinishGroupAssignment(BaseModel):
    group_id: str
    group_label: str = ""
    letter_ids: list[str] = Field(default_factory=list)
    face_finish: FaceFinishSpec = Field(default_factory=FaceFinishSpec)
    return_finish: ReturnFinishSpec = Field(default_factory=ReturnFinishSpec)
    backing_finish: BackingFinishSpec = Field(default_factory=BackingFinishSpec)
    confirmed_by_operator: bool = False


class FinishAssignment(BaseModel):
    assignment_mode: AssignmentMode = "all"
    face_finish: FaceFinishSpec = Field(default_factory=FaceFinishSpec)
    return_finish: ReturnFinishSpec = Field(default_factory=ReturnFinishSpec)
    backing_finish: BackingFinishSpec = Field(default_factory=BackingFinishSpec)
    confirmed_by_operator: bool = False
    groups: list[FinishGroupAssignment] = Field(default_factory=list)

    def active_groups(self) -> list[FinishGroupAssignment]:
        if self.assignment_mode == "group" and self.groups:
            return self.groups
        if self.assignment_mode == "all":
            return [
                FinishGroupAssignment(
                    group_id="__all__",
                    group_label="Toate literele",
                    face_finish=self.face_finish,
                    return_finish=self.return_finish,
                    backing_finish=self.backing_finish,
                    confirmed_by_operator=self.confirmed_by_operator,
                )
            ]
        return self.groups


class IntakeV3LetterGroupFinishAssignment(BaseModel):
    assignment_id: str = ""
    label: str = ""
    target_type: Literal["letter_group"] = "letter_group"
    target_letter_ids: list[str] = Field(default_factory=list)
    face_finish: FaceFinishSpec | None = None
    return_finish: ReturnFinishSpec | None = None
    backing_finish: BackingFinishSpec | None = None
    notes: str = ""
    enabled: bool = True


class IntakeV3LetterFinishAssignment(BaseModel):
    assignment_id: str = ""
    target_type: Literal["letter"] = "letter"
    target_letter_id: str
    face_finish: FaceFinishSpec | None = None
    return_finish: ReturnFinishSpec | None = None
    notes: str = ""
    enabled: bool = True


LayerFinishTargetType = Literal[
    "face",
    "return",
    "backing",
    "printed_artwork",
    "technical",
    "reference",
    "ignore",
]

LayerFinishAssignmentStatus = Literal["missing", "partial", "complete"]

PrintedArtworkPrintMethod = Literal[
    "printed_vinyl",
    "uv_print",
    "latex_print",
    "solvent_print",
    "other",
]

PrintedArtworkLaminateType = Literal["gloss", "matte", "dry_erase", "none", "other"]


class IntakeV3PrintedArtworkFinishSpec(BaseModel):
    enabled: bool = True
    print_method: PrintedArtworkPrintMethod | str | None = None
    media_family: str | None = None
    media_code: str | None = None
    laminate_enabled: bool = False
    laminate_type: PrintedArtworkLaminateType | str | None = None
    contour_cut: bool | None = None
    white_ink: bool = False
    white_backing: bool = False
    area_sqm: float | None = None
    waste_percent: float | None = None
    notes: str | None = None
    is_confirmed: bool = False
    confirmed_at: str | None = None
    confirmed_by: str | None = None


class IntakeV3LayerFinishAssignment(BaseModel):
    layer_key: str
    layer_name: str | None = None
    confirmed_role: str | None = None
    finish_target_type: LayerFinishTargetType | None = None
    face_finish: FaceFinishSpec | None = None
    return_finish: ReturnFinishSpec | None = None
    backing_finish: BackingFinishSpec | None = None
    printed_artwork_finish: IntakeV3PrintedArtworkFinishSpec | None = None
    material_family: str | None = None
    material_code: str | None = None
    color_code: str | None = None
    color_name: str | None = None
    swatch_hex: str | None = None
    is_confirmed: bool = False
    confirmed_by: str | None = None
    confirmed_at: str | None = None
    notes: str | None = None
    enabled: bool = True


class IntakeV3LayerFinishPreviewItem(BaseModel):
    layer_key: str
    layer_name: str | None = None
    confirmed_role: str | None = None
    finish_target_type: LayerFinishTargetType | None = None
    material_code: str | None = None
    color_code: str | None = None
    color_name: str | None = None
    is_confirmed: bool = False
    confirmation_status: Literal["confirmed", "pending", "not_required"] = "pending"
    print_method: str | None = None
    laminate_type: str | None = None
    contour_cut: bool | None = None
    white_ink: bool | None = None
    white_backing: bool | None = None
    area_sqm: float | None = None
    waste_percent: float | None = None
    artwork_notes: str | None = None


# ---------------------------------------------------------------------------
# Lighting / LED / PSU planning (workspace-level — not layer finish)
# ---------------------------------------------------------------------------

IlluminationMode = Literal[
    "frontlit",
    "backlit",
    "halo",
    "frontlit_and_halo",
    "non_illuminated",
    "unknown",
]

LedSystemType = Literal["modules", "strip", "neon_flex", "other"]

LightColorChoice = Literal["warm_white", "neutral_white", "cold_white", "rgb", "custom"]

PsuStrategy = Literal["auto", "manual", "packed_at_packaging", "not_required"]

LightingPlanStatus = Literal["missing", "partial", "complete", "not_required"]

PsuPlanUnitSource = Literal["auto", "manual"]


class IntakeV3PsuPlanUnit(BaseModel):
    capacity_w: float = Field(gt=0)
    quantity: int = Field(default=1, ge=1)
    label: str | None = None
    source: PsuPlanUnitSource = "manual"


class IntakeV3LightingPlan(BaseModel):
    enabled: bool = True
    illumination_mode: IlluminationMode | str = "unknown"
    led_system: LedSystemType | str | None = None
    light_color: LightColorChoice | str | None = None
    light_color_label: str | None = None
    module_power_w: float | None = Field(default=None, ge=0)
    module_count: int | None = Field(default=None, ge=0)
    modules_per_letter: float | None = Field(default=None, ge=0)
    estimated_total_watts: float | None = Field(default=None, ge=0)
    reserve_percent: float = Field(default=30.0, ge=0)
    required_watts_with_reserve: float | None = Field(default=None, ge=0)
    psu_strategy: PsuStrategy | str = "auto"
    psu_units: list[IntakeV3PsuPlanUnit] = Field(default_factory=list)
    psu_total_capacity_w: float | None = Field(default=None, ge=0)
    psu_reserve_w: float | None = None
    manual_override_reason: str | None = None
    psu_packed_at_packaging: bool = False
    applies_to_layer_keys: list[str] = Field(default_factory=list)
    notes: str | None = None
    is_confirmed: bool = False
    confirmed_at: str | None = None
    confirmed_by: str | None = None


class IntakeV3LightingSummary(BaseModel):
    enabled: bool = True
    illumination_mode: str | None = None
    led_system: str | None = None
    light_color: str | None = None
    light_color_label: str | None = None
    module_power_w: float | None = None
    module_count: int | None = None
    estimated_total_watts: float | None = None
    required_watts_with_reserve: float | None = None
    psu_strategy: str | None = None
    psu_units: list[IntakeV3PsuPlanUnit] = Field(default_factory=list)
    psu_total_capacity_w: float | None = None
    psu_reserve_w: float | None = None
    psu_packed_at_packaging: bool = False
    status: LightingPlanStatus = "missing"
    is_confirmed: bool = False
    warnings: list[str] = Field(default_factory=list)
    summary_message: str | None = None


class IntakeV3LightingPlanSummary(BaseModel):
    lighting_plan_status: LightingPlanStatus = "missing"
    is_required: bool = False
    is_confirmed: bool = False
    preview: IntakeV3LightingSummary = Field(default_factory=IntakeV3LightingSummary)


class IntakeV3LightingPlanValidationResult(BaseModel):
    is_valid: bool = False
    blockers: list[VectorModelIssue] = Field(default_factory=list)
    warnings: list[VectorModelIssue] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 5.9 MaterialIntent — estimates only
# ---------------------------------------------------------------------------


class RollMaterialIntent(BaseModel):
    material: str
    material_family: str | None = None
    roll_width_mm: float | None = None
    estimated_ml: float | None = None
    estimated_m2: float | None = None
    source_finish: FinishSource | None = None
    color_code: str | None = None
    color_name: str | None = None
    estimate_status: MaterialItemEstimateStatus = "requires_geometry"


class SheetMaterialIntent(BaseModel):
    material: str
    thickness_mm: float | None = None
    sheet_size: str | None = None
    estimated_m2: float | None = None
    estimated_sheet_count: int | None = None
    estimated_remaining_area_m2: float | None = Field(
        default=None,
        description="Rest placă estimat — not inventory loss",
    )
    remaining_label: str = "Rest placă estimat"
    source_component: SheetSourceComponent | None = None
    estimate_status: MaterialItemEstimateStatus = "requires_geometry"


class LedMaterialIntent(BaseModel):
    module_type: str | None = None
    estimated_module_count: int | None = None
    module_count: int | None = None
    power_w_per_module: float | None = None
    total_watts: float | None = None
    color_temperature_k: int | None = None
    estimate_status: MaterialItemEstimateStatus = "owner_input_required"


class PowerSupplyIntent(BaseModel):
    wattage: float | None = None
    power_w: float | None = None
    quantity: int = 1
    delivery_mode: Literal["pack_with_job", "mount_on_shared_support"] = "pack_with_job"
    packaging_required: bool = False
    mounted_on_shared_support: bool = False
    source_rule: str | None = None

    @model_validator(mode="after")
    def _sync_power_w(self) -> PowerSupplyIntent:
        if self.power_w is None and self.wattage is not None:
            object.__setattr__(self, "power_w", self.wattage)
        elif self.wattage is None and self.power_w is not None:
            object.__setattr__(self, "wattage", self.power_w)
        return self


class AccessoryIntent(BaseModel):
    name: str
    category: str | None = None
    strict_inventory_tracking: bool = False
    estimate_status: MaterialItemEstimateStatus = "estimated"


class MaterialIntent(BaseModel):
    roll_materials: list[RollMaterialIntent] = Field(default_factory=list)
    sheet_materials: list[SheetMaterialIntent] = Field(default_factory=list)
    led_materials: list[LedMaterialIntent] = Field(default_factory=list)
    power_supplies: list[PowerSupplyIntent] = Field(default_factory=list)
    accessories: list[AccessoryIntent] = Field(default_factory=list)
    estimate_status: EstimateStatus = "not_started"
    inventory_mutation_allowed: bool = False

    @field_validator("inventory_mutation_allowed")
    @classmethod
    def _inventory_mutation_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("MaterialIntent.inventory_mutation_allowed must remain false in Intake V3")
        return value


# ---------------------------------------------------------------------------
# Finish / material workflow (pure service output)
# ---------------------------------------------------------------------------


class SupportContext(BaseModel):
    shared_support: bool = False
    illuminated: bool = True


class OperationFlags(BaseModel):
    return_vinyl_application_required: bool = False
    return_painting_after_assembly_required: bool = False
    face_vinyl_application_required: bool = False
    face_vinyl_after_return_painting: bool = False
    psu_packed_at_packaging: bool = False
    electrical_source_mounting_allowed: bool = False


class FinishMaterialValidationResult(BaseModel):
    is_valid: bool = False
    blockers: list[VectorModelIssue] = Field(default_factory=list)
    warnings: list[VectorModelIssue] = Field(default_factory=list)
    summary: str = ""
    operation_flags: OperationFlags = Field(default_factory=OperationFlags)


# ---------------------------------------------------------------------------
# 5.10 ReadinessReport
# ---------------------------------------------------------------------------


class ReadinessIssue(BaseModel):
    code: str
    severity: ReadinessSeverity
    section: str
    message: str
    target_field: str | None = None
    action_label: str | None = None


class ReadinessReport(BaseModel):
    status: ReadinessStatus = "draft"
    blockers: list[ReadinessIssue] = Field(default_factory=list)
    warnings: list[ReadinessIssue] = Field(default_factory=list)
    completion_by_section: dict[str, float] = Field(default_factory=dict)
    can_create_quote: bool = False
    can_create_order: bool = False
    can_generate_production_handoff: bool = False
    next_action: str | None = None
    contract_version: str = INTAKE_V3_CONTRACT_VERSION


# ---------------------------------------------------------------------------
# 5.11 PricingInput — adapter toward quote_input, no pricing computation
# ---------------------------------------------------------------------------


class PricingInput(BaseModel):
    quote_input: dict[str, Any] = Field(default_factory=dict)
    source_intake_schema_version: str = INTAKE_V3_SCHEMA_VERSION
    adapter_status: AdapterStatus = "not_built"
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Pricing input adapter (maps facts — CostEngine calculates prices)
# ---------------------------------------------------------------------------


class PricingInputDimensions(BaseModel):
    width_mm: float | None = None
    height_mm: float | None = None
    depth_mm: float | None = None
    unit: str = "mm"
    area_m2: float | None = None


class PricingInputProductionCounts(BaseModel):
    letter_count: int = 0
    cut_contour_count: int = 0
    inner_hole_count: int = 0
    confirmed_model_status: ConfirmationStatus = "pending"
    letter_groups: list[str] = Field(default_factory=list)


class PricingInputFinishSummary(BaseModel):
    face_finish_type: str = "none"
    face_vinyl_enabled: bool = False
    face_material: str | None = None
    face_color_code: str | None = None
    face_color_name: str | None = None
    face_roll_width_mm: float | None = None
    return_finish_type: str = "none"
    return_wrapped: bool = False
    return_painted: bool = False
    return_depth_mm: float | None = None
    return_material: str | None = None
    return_color_code: str | None = None
    return_color_name: str | None = None
    backing_material: str | None = None
    backing_thickness_mm: float | None = None


class PricingInputMaterialSummary(BaseModel):
    roll_intents: int = 0
    sheet_intents: int = 0
    led_intents: int = 0
    psu_intents: int = 0
    accessory_intents: int = 0
    inventory_mutation_allowed: bool = False
    estimate_status: EstimateStatus = "not_started"


class PricingInputOperationSummary(BaseModel):
    flags: OperationFlags = Field(default_factory=OperationFlags)


class PricingInputReadinessSummary(BaseModel):
    status: ReadinessStatus = "draft"
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    can_create_quote: bool = False
    reason_summary: str | None = None


class PricingInputLine(BaseModel):
    line_id: str
    label: str
    value: str | int | float | bool | None = None
    category: str | None = None


class PricingInputCandidate(BaseModel):
    template_code: str = PILOT_TEMPLATE_CODE
    product_label: str = "Litere volumetrice luminoase"
    support_mode: str = SUPPORT_MODE_NO_SHARED
    dimensions: PricingInputDimensions = Field(default_factory=PricingInputDimensions)
    production_counts: PricingInputProductionCounts = Field(
        default_factory=PricingInputProductionCounts
    )
    finish_summary: PricingInputFinishSummary = Field(default_factory=PricingInputFinishSummary)
    material_summary: PricingInputMaterialSummary = Field(
        default_factory=PricingInputMaterialSummary
    )
    operation_summary: PricingInputOperationSummary = Field(
        default_factory=PricingInputOperationSummary
    )
    readiness_summary: PricingInputReadinessSummary = Field(
        default_factory=PricingInputReadinessSummary
    )
    summary_lines: list[PricingInputLine] = Field(default_factory=list)
    finish_variation_notes: list[str] = Field(default_factory=list)
    requires_grouped_finish_review: bool = False
    finish_variation_count: int = 0


class PricingInputAdapterResult(BaseModel):
    candidate: PricingInputCandidate = Field(default_factory=PricingInputCandidate)
    quote_input_payload: dict[str, Any] = Field(default_factory=dict)
    adapter_warnings: list[str] = Field(default_factory=list)
    adapter_blockers: list[str] = Field(default_factory=list)
    is_ready_for_quote: bool = False
    adapter_status: AdapterStatus = "ready"


# ---------------------------------------------------------------------------
# Production handoff adapter (preview only — not ExecutionPlan)
# ---------------------------------------------------------------------------


class ProductionFinishSummary(BaseModel):
    face_finish_type: str = "none"
    return_finish_type: str = "none"
    backing_material: str | None = None
    backing_thickness_mm: float | None = None
    face_color_code: str | None = None
    face_color_name: str | None = None
    return_color_code: str | None = None
    return_color_name: str | None = None
    face_roll_width_mm: float | None = None
    return_depth_mm: float | None = None


class ProductionMaterialSummary(BaseModel):
    face_material: str | None = None
    return_material: str | None = None
    backing_material: str | None = None
    led_summary: str | None = None
    psu_summary: str | None = None
    accessories: list[str] = Field(default_factory=list)
    inventory_mutation_allowed: bool = False


class ProductionCountsSummary(BaseModel):
    letter_count: int = 0
    cut_contour_count: int = 0
    inner_hole_count: int = 0


class TaskSeedDependency(BaseModel):
    seed_code: str
    display_name: str | None = None


class TaskSeedCandidate(BaseModel):
    seed_code: str
    display_name: str
    active: bool = True
    active_reason: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    required_skill: list[str] = Field(default_factory=list)
    required_station: str | None = None
    operator_instruction: str | None = None
    materials_referenced: list[str] = Field(default_factory=list)
    non_executable: bool = True
    source_operation_code: str
    employee_mobile_action_allowed: bool = False
    execution_plan_id: None = None
    execution_task_id: None = None


class ProductionHandoffPreview(BaseModel):
    template_code: str = PILOT_TEMPLATE_CODE
    product_label: str = "Litere volumetrice luminoase"
    support_mode: str = SUPPORT_MODE_NO_SHARED
    dimensions: PricingInputDimensions = Field(default_factory=PricingInputDimensions)
    counts: ProductionCountsSummary = Field(default_factory=ProductionCountsSummary)
    finish_summary: ProductionFinishSummary = Field(default_factory=ProductionFinishSummary)
    material_summary: ProductionMaterialSummary = Field(default_factory=ProductionMaterialSummary)
    task_seeds: list[TaskSeedCandidate] = Field(default_factory=list)
    non_executable: bool = True
    execution_plan_id: None = None
    employee_mobile_action_allowed: bool = False
    preview_only: bool = True
    finish_variation_handoff_notes: list[str] = Field(default_factory=list)
    requires_letter_group_visibility: bool = False
    group_labels: list[str] = Field(default_factory=list)
    letter_override_count: int = 0

    @field_validator("preview_only")
    @classmethod
    def _preview_only_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("ProductionHandoffPreview.preview_only must remain true")
        return value

    @field_validator("non_executable")
    @classmethod
    def _non_executable_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("ProductionHandoffPreview.non_executable must remain true")
        return value

    @field_validator("employee_mobile_action_allowed")
    @classmethod
    def _employee_action_not_allowed(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("ProductionHandoffPreview.employee_mobile_action_allowed must be false")
        return value


class ProductionHandoffAdapterResult(BaseModel):
    preview: ProductionHandoffPreview = Field(default_factory=ProductionHandoffPreview)
    adapter_warnings: list[str] = Field(default_factory=list)
    adapter_blockers: list[str] = Field(default_factory=list)
    is_ready_for_handoff: bool = False


# ---------------------------------------------------------------------------
# Workspace end-to-end preview (composition only — no quote/order/plan)
# ---------------------------------------------------------------------------

PreviewSectionStatus = Literal["missing", "blocked", "warning", "ready", "preview"]


class IntakeV3PreviewSectionStatus(BaseModel):
    section_code: str
    label: str
    status: PreviewSectionStatus = "missing"
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = ""


class IntakeV3BoundaryFlags(BaseModel):
    quote_creation_allowed: bool = False
    order_creation_allowed: bool = False
    execution_plan_creation_allowed: bool = False
    inventory_mutation_allowed: bool = False
    employee_mobile_action_allowed: bool = False
    preview_only: bool = True

    @field_validator("quote_creation_allowed", "order_creation_allowed", "execution_plan_creation_allowed")
    @classmethod
    def _shell_must_not_allow_execution(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("Intake V3 preview shell must not allow quote/order/plan creation")
        return value

    @field_validator("inventory_mutation_allowed", "employee_mobile_action_allowed")
    @classmethod
    def _shell_must_not_allow_side_effects(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("Intake V3 preview shell must not allow inventory or mobile actions")
        return value

    @field_validator("preview_only")
    @classmethod
    def _preview_only_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3BoundaryFlags.preview_only must remain true")
        return value


class IntakeV3VectorSummary(BaseModel):
    raw_summary: dict[str, Any] = Field(default_factory=dict)
    confirmed_letter_count: int = 0
    confirmed_cut_contour_count: int = 0
    confirmed_inner_hole_count: int = 0
    confirmation_status: ConfirmationStatus = "pending"
    raw_confirmed_mismatch_warning: bool = False


class IntakeV3FinishSummary(BaseModel):
    assignment_mode: AssignmentMode | None = None
    face_finish_type: str = "none"
    return_finish_type: str = "none"
    backing_material: str | None = None
    backing_thickness_mm: float | None = None
    face_vinyl_roll_width_mm: float | None = None
    return_depth_mm: float | None = None
    confirmed_by_operator: bool = False
    finish_assignment_status: str | None = None
    group_assignment_count: int = 0
    letter_override_count: int = 0
    finish_variations_present: bool = False
    assignment_summary: str | None = None
    layer_finish_assignment_status: LayerFinishAssignmentStatus | None = None
    layer_finish_assignment_count: int = 0
    layer_finish_confirmed_count: int = 0
    layer_finish_preview: list[IntakeV3LayerFinishPreviewItem] = Field(default_factory=list)


class IntakeV3MaterialSummary(BaseModel):
    roll_materials: int = 0
    sheet_materials: int = 0
    led_materials: int = 0
    power_supplies: int = 0
    accessories: int = 0
    estimate_status: EstimateStatus = "not_started"
    inventory_mutation_allowed: bool = False


class IntakeV3FinishVariationMaterialNote(BaseModel):
    role: str = ""
    material_code: str | None = None
    material_family: str | None = None
    finish_type: str = "none"
    color_label: str | None = None
    affected_letter_count: int = 0
    note: str = ""


class IntakeV3FinishVariationOperationNote(BaseModel):
    operation_code: str = ""
    present: bool = False
    note: str = ""


class IntakeV3FinishVariationItem(BaseModel):
    variation_id: str = ""
    source_type: Literal["global", "group", "letter"] = "global"
    label: str = ""
    letter_ids: list[str] = Field(default_factory=list)
    letter_count: int = 0
    face_finish_summary: str = ""
    return_finish_summary: str = ""
    backing_finish_summary: str = ""
    operations: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    notes: str = ""


class IntakeV3FinishVariationSummary(BaseModel):
    has_variations: bool = False
    assignment_mode: str = "global_only"
    total_letters: int = 0
    default_letter_count: int = 0
    group_assignment_count: int = 0
    letter_override_count: int = 0
    variations: list[IntakeV3FinishVariationItem] = Field(default_factory=list)
    material_notes: list[IntakeV3FinishVariationMaterialNote] = Field(default_factory=list)
    operation_notes: list[IntakeV3FinishVariationOperationNote] = Field(default_factory=list)
    pricing_preview_notes: list[str] = Field(default_factory=list)
    handoff_preview_notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


QuoteReadinessStatus = Literal["blocked", "warning", "ready_preview_only"]
QuoteReadinessItemSeverity = Literal["blocker", "warning", "info", "pass"]
QuoteReadinessItemStatus = Literal["fail", "warn", "info", "pass"]


class IntakeV3QuoteReadinessItem(BaseModel):
    code: str
    label: str
    severity: QuoteReadinessItemSeverity
    status: QuoteReadinessItemStatus
    message: str
    recommended_action: str | None = None
    source: str
    editable_here: bool = False
    related_section: str | None = None


class IntakeV3QuoteReadinessSummary(BaseModel):
    adapter_status: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    notes: list[str] = Field(default_factory=list)


class IntakeV3QuoteReadinessResult(BaseModel):
    status: QuoteReadinessStatus = "blocked"
    can_create_quote: bool = False
    preview_only: bool = True
    blockers: list[IntakeV3QuoteReadinessItem] = Field(default_factory=list)
    warnings: list[IntakeV3QuoteReadinessItem] = Field(default_factory=list)
    infos: list[IntakeV3QuoteReadinessItem] = Field(default_factory=list)
    checklist: list[IntakeV3QuoteReadinessItem] = Field(default_factory=list)
    operator_review_items: list[IntakeV3QuoteReadinessItem] = Field(default_factory=list)
    pricing_input_summary: IntakeV3QuoteReadinessSummary | None = None
    handoff_summary: IntakeV3QuoteReadinessSummary | None = None
    next_recommended_action: str | None = None

    @field_validator("can_create_quote")
    @classmethod
    def _quote_creation_disabled(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3QuoteReadinessResult.can_create_quote must remain false")
        return value

    @field_validator("preview_only")
    @classmethod
    def _preview_only_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3QuoteReadinessResult.preview_only must remain true")
        return value


class IntakeV3PreQuoteReviewSection(BaseModel):
    section_code: str
    label: str
    items: list[IntakeV3QuoteReadinessItem] = Field(default_factory=list)
    summary: str = ""


class IntakeV3PreQuoteReview(BaseModel):
    status: QuoteReadinessStatus = "blocked"
    can_create_quote: bool = False
    preview_only: bool = True
    sections: list[IntakeV3PreQuoteReviewSection] = Field(default_factory=list)
    blockers: list[IntakeV3QuoteReadinessItem] = Field(default_factory=list)
    warnings: list[IntakeV3QuoteReadinessItem] = Field(default_factory=list)
    infos: list[IntakeV3QuoteReadinessItem] = Field(default_factory=list)
    next_recommended_action: str | None = None

    @field_validator("can_create_quote")
    @classmethod
    def _prequote_quote_disabled(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3PreQuoteReview.can_create_quote must remain false")
        return value


QuoteCreationDryRunStatus = Literal["blocked", "ready_for_future_quote_step", "dry_run_only"]
QuoteCreationGuardPolicyStatus = Literal["disabled_by_default"]
QuoteCreationGuardReasonSeverity = Literal["info", "warning", "blocker"]


class IntakeV3QuoteCreationGuardReason(BaseModel):
    code: str
    severity: QuoteCreationGuardReasonSeverity = "info"
    message: str


class IntakeV3QuoteCreationEnableRequirement(BaseModel):
    requirement: str
    description: str | None = None


class IntakeV3QuoteCreationGuardPolicy(BaseModel):
    policy_status: QuoteCreationGuardPolicyStatus = "disabled_by_default"
    policy_code: str = "INTAKE_V3_QUOTE_CREATION_DISABLED_BY_DEFAULT"
    can_create_quote: bool = False
    real_quote_creation_enabled: bool = False
    disabled_by_policy: bool = True
    owner_confirmation_required: bool = True
    safe_to_dry_run: bool = True
    reasons: list[IntakeV3QuoteCreationGuardReason] = Field(default_factory=list)
    required_before_enable: list[str] = Field(default_factory=list)
    observed_preconditions: list[str] = Field(default_factory=list)
    enablement_policy_status: str = "owner_approval_required"
    final_blocker_check_available: bool = True

    @field_validator("can_create_quote", "real_quote_creation_enabled")
    @classmethod
    def _creation_flags_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3QuoteCreationGuardPolicy creation flags must remain false")
        return value

    @field_validator("disabled_by_policy", "owner_confirmation_required")
    @classmethod
    def _policy_lock_flags_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3QuoteCreationGuardPolicy lock flags must remain true")
        return value

    @field_validator("policy_status")
    @classmethod
    def _policy_status_disabled(cls, value: str) -> str:
        if value != "disabled_by_default":
            raise ValueError("IntakeV3QuoteCreationGuardPolicy.policy_status must remain disabled_by_default")
        return value


FinalBlockerSeverity = Literal["blocker", "warning", "info", "pass"]
QuoteCreationEnablementStatus = Literal["owner_approval_required"]
QuoteCreationRealStatus = Literal["blocked", "pass", "ready"]
OwnerDecisionStatus = Literal["required_not_present"]
SnapshotPolicyStatus = Literal["defined_not_executed"]
AntiDuplicatePolicyStatus = Literal["defined"]
RollbackPolicyStatus = Literal["defined"]
RealQuoteCreationEnablementReadinessStatus = Literal[
    "blocked_owner_decision_missing",
    "blocked_workspace_archived",
    "blocked",
]


class IntakeV3QuoteCreationEnablementRequirement(BaseModel):
    code: str
    requirement: str


class IntakeV3QuoteCreationEnablementBlocker(BaseModel):
    code: str
    severity: FinalBlockerSeverity = "blocker"
    message: str = ""


class IntakeV3OwnerApprovalContractPreview(BaseModel):
    owner_approval_required: bool = True
    owner_approval_present: bool = False
    approval_scope: str = "real_quote_creation_enablement"
    workspace_id: str = ""
    workspace_title: str = ""
    template_code: str = PILOT_TEMPLATE_CODE
    contract_note: str = ""

    @field_validator("owner_approval_required")
    @classmethod
    def _approval_required_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3OwnerApprovalContractPreview.owner_approval_required must remain true")
        return value

    @field_validator("owner_approval_present")
    @classmethod
    def _approval_present_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3OwnerApprovalContractPreview.owner_approval_present must remain false")
        return value


class IntakeV3QuoteCreationEnablementPolicy(BaseModel):
    enablement_status: QuoteCreationEnablementStatus = "owner_approval_required"
    can_enable_real_quote_creation: bool = False
    can_create_quote_now: bool = False
    owner_approval_required: bool = True
    owner_approval_present: bool = False
    policy_code: str = "INTAKE_V3_REAL_QUOTE_CREATION_REQUIRES_OWNER_APPROVAL"
    requirements: list[IntakeV3QuoteCreationEnablementRequirement] = Field(default_factory=list)
    blockers: list[IntakeV3QuoteCreationEnablementBlocker] = Field(default_factory=list)
    warnings: list[IntakeV3QuoteCreationEnablementBlocker] = Field(default_factory=list)
    observed_gates: list[str] = Field(default_factory=list)
    owner_approval_contract: IntakeV3OwnerApprovalContractPreview = Field(
        default_factory=IntakeV3OwnerApprovalContractPreview
    )
    preview_status: QuoteCreationRealStatus = "blocked"
    real_creation_status: QuoteCreationRealStatus = "blocked"
    final_blockers_checked: bool = True
    next_action: str = ""
    owner_decision_record_status: OwnerDecisionStatus = "required_not_present"
    snapshot_policy_status: SnapshotPolicyStatus = "defined_not_executed"
    anti_duplicate_policy_status: AntiDuplicatePolicyStatus = "defined"
    rollback_policy_status: RollbackPolicyStatus = "defined"
    real_quote_creation_enablement_readiness_status: RealQuoteCreationEnablementReadinessStatus = (
        "blocked_owner_decision_missing"
    )

    @field_validator("can_enable_real_quote_creation", "can_create_quote_now", "owner_approval_present")
    @classmethod
    def _enablement_flags_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3QuoteCreationEnablementPolicy enablement flags must remain false")
        return value

    @field_validator("owner_approval_required")
    @classmethod
    def _owner_approval_required_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3QuoteCreationEnablementPolicy.owner_approval_required must remain true")
        return value

    @field_validator("enablement_status")
    @classmethod
    def _enablement_status_locked(cls, value: str) -> str:
        if value != "owner_approval_required":
            raise ValueError(
                "IntakeV3QuoteCreationEnablementPolicy.enablement_status must remain owner_approval_required"
            )
        return value


class IntakeV3QuoteCreationFinalBlockerItem(BaseModel):
    code: str
    label: str
    severity: FinalBlockerSeverity = "blocker"
    category: str = ""
    message: str = ""
    affects_preview: bool = False
    affects_real_creation: bool = True


class IntakeV3QuoteCreationFinalBlockerCheck(BaseModel):
    final_blockers_checked: bool = True
    preview_status: QuoteCreationRealStatus = "blocked"
    real_creation_status: QuoteCreationRealStatus = "blocked"
    can_create_quote_now: bool = False
    items: list[IntakeV3QuoteCreationFinalBlockerItem] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    cost_engine_called: bool = False
    quote_creation_endpoint_called: bool = False
    quote_created: bool = False
    next_action: str = ""

    @field_validator("can_create_quote_now", "quote_created", "quote_creation_endpoint_called")
    @classmethod
    def _creation_flags_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3QuoteCreationFinalBlockerCheck creation flags must remain false")
        return value

    @field_validator("real_creation_status")
    @classmethod
    def _real_creation_status_blocked(cls, value: str) -> str:
        if value != "blocked":
            raise ValueError("IntakeV3QuoteCreationFinalBlockerCheck.real_creation_status must remain blocked")
        return value


class IntakeV3OwnerDecisionRequiredField(BaseModel):
    field_code: str
    field_type: str = ""
    description: str = ""
    required: bool = True
    present_in_build: bool = False

    @field_validator("present_in_build")
    @classmethod
    def _present_in_build_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3OwnerDecisionRequiredField.present_in_build must remain false")
        return value


class IntakeV3OwnerDecisionAuditRequirement(BaseModel):
    code: str
    requirement: str = ""


class IntakeV3OwnerDecisionRecordPolicy(BaseModel):
    owner_decision_record_required: bool = True
    owner_decision_record_present: bool = False
    owner_decision_status: OwnerDecisionStatus = "required_not_present"
    can_enable_real_quote_creation: bool = False
    decision_scope: str = "intake_v3_real_quote_creation"
    required_fields: list[IntakeV3OwnerDecisionRequiredField] = Field(default_factory=list)
    audit_requirements: list[IntakeV3OwnerDecisionAuditRequirement] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_action: str = ""

    @field_validator("owner_decision_record_required")
    @classmethod
    def _required_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3OwnerDecisionRecordPolicy.owner_decision_record_required must remain true")
        return value

    @field_validator("owner_decision_record_present", "can_enable_real_quote_creation")
    @classmethod
    def _flags_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3OwnerDecisionRecordPolicy enablement flags must remain false")
        return value


class IntakeV3QuoteSnapshotRequiredSection(BaseModel):
    section_code: str
    description: str = ""
    required: bool = True
    available_in_preview: bool = False


class IntakeV3QuoteSnapshotIntegrityRule(BaseModel):
    code: str
    rule: str = ""


class IntakeV3QuoteSnapshotPersistencePlanItem(BaseModel):
    target: str
    action: str
    executed: bool = False
    note: str = ""

    @field_validator("executed")
    @classmethod
    def _executed_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3QuoteSnapshotPersistencePlanItem.executed must remain false")
        return value


class IntakeV3QuoteSnapshotPolicy(BaseModel):
    snapshot_policy_defined: bool = True
    snapshot_persistence_executed: bool = False
    snapshot_policy_version: str = "intake_v3_quote_snapshot_v1"
    required_sections: list[IntakeV3QuoteSnapshotRequiredSection] = Field(default_factory=list)
    integrity_rules: list[IntakeV3QuoteSnapshotIntegrityRule] = Field(default_factory=list)
    persistence_plan: list[IntakeV3QuoteSnapshotPersistencePlanItem] = Field(default_factory=list)
    hash_marker_preview: str = "preview-only"
    next_action: str = ""

    @field_validator("snapshot_policy_defined")
    @classmethod
    def _defined_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3QuoteSnapshotPolicy.snapshot_policy_defined must remain true")
        return value

    @field_validator("snapshot_persistence_executed")
    @classmethod
    def _persistence_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3QuoteSnapshotPolicy.snapshot_persistence_executed must remain false")
        return value


class IntakeV3QuoteCreationDuplicateKey(BaseModel):
    key_code: str
    description: str = ""
    preview_value: str = ""


class IntakeV3QuoteCreationAntiDuplicatePolicy(BaseModel):
    anti_duplicate_policy_defined: bool = True
    duplicate_check_executed: bool = False
    quote_creation_idempotency_required: bool = True
    duplicate_key_strategy: list[IntakeV3QuoteCreationDuplicateKey] = Field(default_factory=list)
    would_block_if_existing_quote_found: bool = True
    blockers: list[str] = Field(default_factory=list)
    next_action: str = ""

    @field_validator("anti_duplicate_policy_defined", "quote_creation_idempotency_required")
    @classmethod
    def _policy_flags_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3QuoteCreationAntiDuplicatePolicy policy flags must remain true")
        return value

    @field_validator("duplicate_check_executed")
    @classmethod
    def _duplicate_check_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3QuoteCreationAntiDuplicatePolicy.duplicate_check_executed must remain false")
        return value


class IntakeV3QuoteCreationFailureMode(BaseModel):
    code: str
    severity: str = "blocker"
    description: str = ""


class IntakeV3QuoteCreationRecoveryAction(BaseModel):
    code: str
    action: str = ""


class IntakeV3QuoteCreationRecoveryPolicy(BaseModel):
    rollback_policy_defined: bool = True
    recovery_policy_defined: bool = True
    failure_modes: list[IntakeV3QuoteCreationFailureMode] = Field(default_factory=list)
    recovery_actions: list[IntakeV3QuoteCreationRecoveryAction] = Field(default_factory=list)
    manual_review_required_on_partial_failure: bool = True
    next_action: str = ""

    @field_validator("rollback_policy_defined", "recovery_policy_defined")
    @classmethod
    def _recovery_flags_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3QuoteCreationRecoveryPolicy policy flags must remain true")
        return value


class IntakeV3RealQuoteCreationEnablementReadiness(BaseModel):
    real_quote_creation_enablement_readiness_status: RealQuoteCreationEnablementReadinessStatus = (
        "blocked_owner_decision_missing"
    )
    can_create_quote_now: bool = False
    can_enable_real_quote_creation: bool = False
    owner_decision_record_required: bool = True
    owner_decision_record_present: bool = False
    snapshot_policy_defined: bool = True
    snapshot_persistence_executed: bool = False
    anti_duplicate_policy_defined: bool = True
    rollback_policy_defined: bool = True
    owner_decision_record_status: OwnerDecisionStatus = "required_not_present"
    snapshot_policy_status: SnapshotPolicyStatus = "defined_not_executed"
    anti_duplicate_policy_status: AntiDuplicatePolicyStatus = "defined"
    rollback_policy_status: RollbackPolicyStatus = "defined"
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_action: str = ""

    @field_validator(
        "can_create_quote_now",
        "can_enable_real_quote_creation",
        "owner_decision_record_present",
        "snapshot_persistence_executed",
    )
    @classmethod
    def _creation_flags_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3RealQuoteCreationEnablementReadiness creation flags must remain false")
        return value

    @field_validator("owner_decision_record_required", "snapshot_policy_defined", "anti_duplicate_policy_defined")
    @classmethod
    def _policy_defined_flags_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3RealQuoteCreationEnablementReadiness policy defined flags must remain true")
        return value


class IntakeV3QuoteCreationDryRunSafetyFlags(BaseModel):
    quote_creation_endpoint_called: bool = False
    quote_created: bool = False
    order_created: bool = False
    execution_plan_created: bool = False
    inventory_mutated: bool = False
    cost_engine_called: bool = False
    pricing_formula_modified: bool = False

    @field_validator(
        "quote_creation_endpoint_called",
        "quote_created",
        "order_created",
        "execution_plan_created",
        "inventory_mutated",
        "cost_engine_called",
        "pricing_formula_modified",
    )
    @classmethod
    def _safety_flags_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3QuoteCreationDryRunSafetyFlags must remain false in dry-run foundation")
        return value


class IntakeV3QuoteCreationDryRunPayloadPreview(BaseModel):
    workspace_id: str = ""
    template_code: str = PILOT_TEMPLATE_CODE
    product_label: str = ""
    job_title: str = ""
    client_name: str = ""
    request_code: str = ""
    dimensions: dict[str, Any] = Field(default_factory=dict)
    confirmed_letter_count: int = 0
    confirmed_cut_contour_count: int = 0
    confirmed_inner_hole_count: int = 0
    face_finish_type: str = "none"
    return_finish_type: str = "none"
    backing_material: str | None = None
    finish_variation_count: int = 0
    requires_grouped_finish_review: bool = False
    pricing_input_candidate_reference: dict[str, Any] = Field(default_factory=dict)
    pricing_notes: list[str] = Field(default_factory=list)
    handoff_notes: list[str] = Field(default_factory=list)
    operator_review_notes: list[str] = Field(default_factory=list)
    preview_only: bool = True


class IntakeV3QuoteCreationDryRunSnapshotPreview(BaseModel):
    workspace_payload_marker: str = ""
    raw_svg_analysis_reference: dict[str, Any] = Field(default_factory=dict)
    confirmed_production_model_snapshot: dict[str, Any] = Field(default_factory=dict)
    raw_vs_confirmed_boundary_note: str = ""
    finish_assignments_snapshot: dict[str, Any] = Field(default_factory=dict)
    finish_variation_summary_snapshot: dict[str, Any] = Field(default_factory=dict)
    pricing_input_preview_snapshot: dict[str, Any] = Field(default_factory=dict)
    prequote_review_snapshot: dict[str, Any] = Field(default_factory=dict)
    created_quote_id: None = None
    created_order_id: None = None
    execution_plan_id: None = None
    preview_only: bool = True


class IntakeV3QuoteCreationDryRun(BaseModel):
    dry_run_id: str = ""
    dry_run_only: bool = True
    can_create_quote_now: bool = False
    quote_creation_disabled_reason: str = ""
    readiness_status: QuoteReadinessStatus = "blocked"
    dry_run_status: QuoteCreationDryRunStatus = "blocked"
    would_block_real_quote_creation: bool = True
    would_use_workspace_id: str = ""
    would_use_workspace_code: str | None = None
    would_use_template_code: str = PILOT_TEMPLATE_CODE
    would_use_pricing_input_candidate: bool = False
    would_use_finish_variation_notes: bool = False
    would_use_production_handoff_preview: bool = False
    would_create_snapshot_preview: bool = True
    would_require_owner_confirmation: bool = True
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    payload_preview: IntakeV3QuoteCreationDryRunPayloadPreview = Field(
        default_factory=IntakeV3QuoteCreationDryRunPayloadPreview
    )
    snapshot_preview: IntakeV3QuoteCreationDryRunSnapshotPreview = Field(
        default_factory=IntakeV3QuoteCreationDryRunSnapshotPreview
    )
    pricing_input_preview_summary: IntakeV3QuoteReadinessSummary | None = None
    finish_variation_summary: IntakeV3FinishVariationSummary | None = None
    handoff_preview_summary: IntakeV3QuoteReadinessSummary | None = None
    safety_flags: IntakeV3QuoteCreationDryRunSafetyFlags = Field(
        default_factory=IntakeV3QuoteCreationDryRunSafetyFlags
    )
    guard_policy: IntakeV3QuoteCreationGuardPolicy = Field(
        default_factory=IntakeV3QuoteCreationGuardPolicy
    )
    next_action: str | None = None

    @field_validator("can_create_quote_now")
    @classmethod
    def _can_create_quote_now_disabled(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3QuoteCreationDryRun.can_create_quote_now must remain false")
        return value

    @field_validator("dry_run_only")
    @classmethod
    def _dry_run_only_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("IntakeV3QuoteCreationDryRun.dry_run_only must remain true")
        return value


CommercialQuoteBridgeStatus = Literal["disabled_by_policy", "blocked_by_missing_policy"]
CommercialQuoteMappingStatus = Literal[
    "mapped",
    "missing",
    "blocked_by_policy",
    "preview_only",
    "needs_owner_decision",
]


class IntakeV3CommercialQuoteMappingItem(BaseModel):
    source_field: str
    target_quote_field: str
    status: CommercialQuoteMappingStatus
    message: str


class IntakeV3CommercialQuoteMissingField(BaseModel):
    field_code: str
    label: str
    message: str
    severity: Literal["blocker", "warning", "info"] = "info"


class IntakeV3CommercialQuoteCandidatePayload(BaseModel):
    workspace_id: str = ""
    workspace_code: str | None = None
    workspace_title: str = ""
    source_module: str = "intake_v3"
    source_status: str = ""
    template_code: str = PILOT_TEMPLATE_CODE
    client_id: str | None = None
    client_name: str = ""
    request_code: str = ""
    job_title: str = ""
    product_label: str = ""
    dimensions: dict[str, Any] = Field(default_factory=dict)
    illuminated: bool | None = None
    support_mode: bool | None = None
    confirmed_letter_count: int = 0
    confirmed_cut_contour_count: int = 0
    confirmed_inner_hole_count: int = 0
    raw_svg_analysis_reference: dict[str, Any] = Field(default_factory=dict)
    confirmed_production_model_reference: dict[str, Any] = Field(default_factory=dict)
    finish_assignment_summary: dict[str, Any] = Field(default_factory=dict)
    finish_variation_summary_reference: dict[str, Any] = Field(default_factory=dict)
    material_notes: list[str] = Field(default_factory=list)
    operation_notes: list[str] = Field(default_factory=list)
    pricing_input_candidate_reference: dict[str, Any] = Field(default_factory=dict)
    pricing_notes: list[str] = Field(default_factory=list)
    requires_grouped_finish_review: bool = False
    production_handoff_preview_reference: dict[str, Any] = Field(default_factory=dict)
    handoff_non_executable: bool = True
    guard_policy_status: str = "disabled_by_default"
    owner_confirmation_required: bool = True
    dry_run_only: bool = True
    real_quote_disabled: bool = True
    preview_only: bool = True


class IntakeV3CommercialQuoteSnapshotPlan(BaseModel):
    workspace_payload_snapshot: bool = True
    confirmed_production_model_snapshot: bool = True
    raw_svg_analysis_reference: bool = True
    finish_assignment_snapshot: bool = True
    finish_variation_summary_snapshot: bool = True
    pricing_input_candidate_snapshot: bool = True
    prequote_review_snapshot: bool = True
    guard_policy_snapshot: bool = True
    operator_confirmation_snapshot: bool = True
    persistence_note: str = (
        "Snapshot plan preview only — no DB snapshot rows created in this build."
    )


class IntakeV3CommercialQuoteBridgeSafetyFlags(BaseModel):
    quote_creation_endpoint_called: bool = False
    quote_created: bool = False
    commercial_quote_created: bool = False
    order_created: bool = False
    execution_plan_created: bool = False
    inventory_mutated: bool = False
    cost_engine_called: bool = False
    pricing_formula_modified: bool = False

    @field_validator(
        "quote_creation_endpoint_called",
        "quote_created",
        "commercial_quote_created",
        "order_created",
        "execution_plan_created",
        "inventory_mutated",
        "cost_engine_called",
        "pricing_formula_modified",
    )
    @classmethod
    def _bridge_safety_flags_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError(
                "IntakeV3CommercialQuoteBridgeSafetyFlags must remain false in bridge foundation"
            )
        return value


class IntakeV3CommercialQuoteBridgePreview(BaseModel):
    bridge_status: CommercialQuoteBridgeStatus = "disabled_by_policy"
    can_create_commercial_quote: bool = False
    would_create_quote: bool = False
    quote_creation_endpoint_called: bool = False
    policy_code: str = ""
    candidate_payload: IntakeV3CommercialQuoteCandidatePayload = Field(
        default_factory=IntakeV3CommercialQuoteCandidatePayload
    )
    mapping_status: list[IntakeV3CommercialQuoteMappingItem] = Field(default_factory=list)
    missing_fields: list[IntakeV3CommercialQuoteMissingField] = Field(default_factory=list)
    blocked_fields: list[str] = Field(default_factory=list)
    preview_only_fields: list[str] = Field(default_factory=list)
    snapshot_plan: IntakeV3CommercialQuoteSnapshotPlan = Field(
        default_factory=IntakeV3CommercialQuoteSnapshotPlan
    )
    owner_confirmation_required: bool = True
    safety_flags: IntakeV3CommercialQuoteBridgeSafetyFlags = Field(
        default_factory=IntakeV3CommercialQuoteBridgeSafetyFlags
    )
    next_action: str = ""
    enablement_policy_status: str = "owner_approval_required"
    final_blockers_present: bool = True
    real_creation_status: QuoteCreationRealStatus = "blocked"
    owner_decision_record_status: OwnerDecisionStatus = "required_not_present"
    snapshot_policy_status: SnapshotPolicyStatus = "defined_not_executed"
    anti_duplicate_policy_status: AntiDuplicatePolicyStatus = "defined"
    rollback_policy_status: RollbackPolicyStatus = "defined"
    real_quote_creation_enablement_readiness_status: RealQuoteCreationEnablementReadinessStatus = (
        "blocked_owner_decision_missing"
    )

    @field_validator(
        "can_create_commercial_quote",
        "would_create_quote",
        "quote_creation_endpoint_called",
    )
    @classmethod
    def _bridge_creation_flags_must_stay_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError("IntakeV3CommercialQuoteBridgePreview creation flags must remain false")
        return value

    @field_validator("real_creation_status")
    @classmethod
    def _bridge_real_creation_blocked(cls, value: str) -> str:
        if value != "blocked":
            raise ValueError("IntakeV3CommercialQuoteBridgePreview.real_creation_status must remain blocked")
        return value


class IntakeV3WorkspacePreview(BaseModel):
    workspace_id: str = ""
    template_code: str = PILOT_TEMPLATE_CODE
    support_mode: str = SUPPORT_MODE_NO_SHARED
    section_statuses: list[IntakeV3PreviewSectionStatus] = Field(default_factory=list)
    readiness_report: ReadinessReport | None = None
    vector_summary: IntakeV3VectorSummary = Field(default_factory=IntakeV3VectorSummary)
    finish_summary: IntakeV3FinishSummary = Field(default_factory=IntakeV3FinishSummary)
    lighting_summary: IntakeV3LightingSummary = Field(default_factory=IntakeV3LightingSummary)
    finish_variation_summary: IntakeV3FinishVariationSummary | None = None
    quote_readiness: IntakeV3QuoteReadinessResult | None = None
    prequote_review: IntakeV3PreQuoteReview | None = None
    quote_creation_dry_run_available: bool = False
    commercial_quote_bridge_available: bool = False
    commercial_quote_bridge_status: CommercialQuoteBridgeStatus | Literal["unavailable"] = "unavailable"
    quote_creation_enablement_available: bool = False
    quote_creation_enablement_status: QuoteCreationEnablementStatus | Literal["unavailable"] = "unavailable"
    quote_creation_real_status: QuoteCreationRealStatus | Literal["unavailable"] = "unavailable"
    real_quote_creation_enablement_readiness_available: bool = False
    real_quote_creation_enablement_readiness_status: (
        RealQuoteCreationEnablementReadinessStatus | Literal["unavailable"]
    ) = "unavailable"
    owner_decision_record_status: OwnerDecisionStatus | Literal["unavailable"] = "unavailable"
    snapshot_policy_status: SnapshotPolicyStatus | Literal["unavailable"] = "unavailable"
    anti_duplicate_policy_status: AntiDuplicatePolicyStatus | Literal["unavailable"] = "unavailable"
    rollback_policy_status: RollbackPolicyStatus | Literal["unavailable"] = "unavailable"
    material_summary: IntakeV3MaterialSummary = Field(default_factory=IntakeV3MaterialSummary)
    pricing_input_candidate: PricingInputCandidate | None = None
    production_handoff_preview: ProductionHandoffPreview | None = None
    boundary_flags: IntakeV3BoundaryFlags = Field(default_factory=IntakeV3BoundaryFlags)
    preview_blockers: list[str] = Field(default_factory=list)
    preview_warnings: list[str] = Field(default_factory=list)
    is_ready_for_quote: bool = False
    is_ready_for_production_handoff_preview: bool = False
    created_quote_id: None = None
    created_order_id: None = None
    execution_plan_id: None = None


class IntakeV3PreviewBuildResult(BaseModel):
    preview: IntakeV3WorkspacePreview = Field(default_factory=IntakeV3WorkspacePreview)
    build_warnings: list[str] = Field(default_factory=list)
    build_blockers: list[str] = Field(default_factory=list)
    is_preview_complete: bool = False


# ---------------------------------------------------------------------------
# 5.12 ProductionHandoff — preview/seed only (legacy contract)
# ---------------------------------------------------------------------------


class ProductionTaskSeed(BaseModel):
    process_id: str
    display_name: str
    instruction_preview: str | None = None
    dependency_process_ids: list[str] = Field(default_factory=list)
    material_summary: str | None = None


class ProductionHandoff(BaseModel):
    preview_only: bool = True
    task_seed: list[ProductionTaskSeed] = Field(default_factory=list)
    materials_summary: list[str] = Field(default_factory=list)
    operator_instruction_preview: str | None = None
    source_rules: list[str] = Field(default_factory=list)

    @field_validator("preview_only")
    @classmethod
    def _preview_only_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("ProductionHandoff.preview_only must remain true in Intake V3")
        return value


# ---------------------------------------------------------------------------
# 5.13 EmployeePreviewSeed — non-executable mobile preview
# ---------------------------------------------------------------------------


class EmployeePreviewTask(BaseModel):
    task_title: str
    instruction_preview: str | None = None
    material_preview: str | None = None


class EmployeePreviewSeed(BaseModel):
    non_executable: bool = True
    preview_tasks: list[EmployeePreviewTask] = Field(default_factory=list)
    mobile_instruction_preview: str | None = None

    @field_validator("non_executable")
    @classmethod
    def _non_executable_must_stay_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("EmployeePreviewSeed.non_executable must remain true in Intake V3")
        return value


# ---------------------------------------------------------------------------
# Aggregate workspace payload (in-memory contract root for readiness service)
# ---------------------------------------------------------------------------


class IntakeV3Workspace(BaseModel):
    """In-memory Intake V3 workspace — draft payload root for readiness/preview services."""

    schema_version: str = INTAKE_V3_SCHEMA_VERSION
    contract_version: str = INTAKE_V3_CONTRACT_VERSION
    client_request: ClientRequest = Field(default_factory=ClientRequest)
    product_selection: ProductSelection = Field(default_factory=ProductSelection)
    vector_asset: VectorAsset | None = None
    raw_svg_analysis: RawSvgAnalysis | None = None
    raw_analysis_status: Literal["missing", "analyzed", "failed"] | None = None
    production_model_status: Literal["missing", "pending", "confirmed"] | None = None
    production_model_confirmed_at: datetime | None = None
    production_model_confirmed_by_user_id: str | None = None
    confirmed_production_model: ConfirmedProductionModel | None = None
    finish_assignment: FinishAssignment | None = None
    letter_group_finish_assignments: list[IntakeV3LetterGroupFinishAssignment] = Field(
        default_factory=list
    )
    letter_finish_assignments: list[IntakeV3LetterFinishAssignment] = Field(default_factory=list)
    finish_assignment_status: Literal[
        "global_only", "group_overrides", "letter_overrides", "mixed"
    ] | None = None
    layer_finish_assignments: list[IntakeV3LayerFinishAssignment] = Field(default_factory=list)
    layer_finish_assignment_status: LayerFinishAssignmentStatus | None = None
    lighting_plan: IntakeV3LightingPlan | None = None
    lighting_plan_status: LightingPlanStatus | None = None
    material_intent: MaterialIntent = Field(default_factory=MaterialIntent)
    pricing_input: PricingInput | None = None
    production_handoff: ProductionHandoff = Field(default_factory=ProductionHandoff)
    employee_preview_seed: EmployeePreviewSeed = Field(default_factory=EmployeePreviewSeed)
    readiness_report: ReadinessReport | None = None
    support_context: SupportContext | None = None
    path_geometry_summary: dict[str, Any] | None = None
    geometry_metrics_snapshot: dict[str, Any] | None = None
    layer_role_confirmation_snapshot: dict[str, Any] | None = None
    svg_source_fingerprint: str | None = None
    svg_dependent_state_warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Workspace persistence API contracts (draft only — no quote/order/plan writes)
# ---------------------------------------------------------------------------

WorkspaceDraftStatus = Literal[
    "draft",
    "collecting_data",
    "blocked",
    "ready_for_quote_preview",
    "archived",
]


class IntakeV3WorkspaceCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    template_code: str = PILOT_TEMPLATE_CODE
    payload: dict[str, Any] = Field(default_factory=dict)
    source_scenario: str | None = None


class IntakeV3WorkspaceUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: WorkspaceDraftStatus | None = None
    payload: dict[str, Any] | None = None
    preview_snapshot: dict[str, Any] | None = None


class IntakeV3WorkspaceSeedFromScenarioRequest(BaseModel):
    scenario: str
    title: str | None = None


class IntakeV3WorkspaceResponse(BaseModel):
    id: str
    workspace_code: str
    title: str
    template_code: str
    status: WorkspaceDraftStatus
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    readiness_status: str | None = None
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None


class IntakeV3WorkspaceListItem(BaseModel):
    id: str
    workspace_code: str
    title: str
    template_code: str
    status: WorkspaceDraftStatus
    readiness_status: str | None = None
    source_scenario: str | None = None
    updated_at: datetime | None = None


class IntakeV3WorkspaceListResponse(BaseModel):
    items: list[IntakeV3WorkspaceListItem] = Field(default_factory=list)
    total: int = 0


class IntakeV3QuoteReadinessResponse(BaseModel):
    workspace_id: str
    workspace_code: str
    quote_readiness: IntakeV3QuoteReadinessResult
    prequote_review: IntakeV3PreQuoteReview


class IntakeV3QuoteCreationDryRunResponse(BaseModel):
    workspace_id: str
    workspace_code: str
    dry_run: IntakeV3QuoteCreationDryRun


class IntakeV3QuoteCreationGuardPolicyResponse(BaseModel):
    workspace_id: str
    workspace_code: str
    guard_policy: IntakeV3QuoteCreationGuardPolicy


class IntakeV3CommercialQuoteBridgeResponse(BaseModel):
    workspace_id: str
    workspace_code: str
    bridge: IntakeV3CommercialQuoteBridgePreview


class IntakeV3QuoteCreationEnablementResponse(BaseModel):
    workspace_id: str
    workspace_code: str
    enablement_policy: IntakeV3QuoteCreationEnablementPolicy
    final_blocker_check: IntakeV3QuoteCreationFinalBlockerCheck
    dry_run_status: str | None = None
    bridge_status: str | None = None
    guard_policy_status: str | None = None


class IntakeV3RealQuoteCreationEnablementReadinessResponse(BaseModel):
    workspace_id: str
    workspace_code: str
    owner_decision_record_policy: IntakeV3OwnerDecisionRecordPolicy
    snapshot_policy: IntakeV3QuoteSnapshotPolicy
    anti_duplicate_policy: IntakeV3QuoteCreationAntiDuplicatePolicy
    recovery_policy: IntakeV3QuoteCreationRecoveryPolicy
    readiness: IntakeV3RealQuoteCreationEnablementReadiness
    enablement_status: str | None = None
    bridge_status: str | None = None
    guard_policy_status: str | None = None


# ---------------------------------------------------------------------------
# Guarded draft quote creation (first real Quote write from Intake V3)
# ---------------------------------------------------------------------------


class IntakeV3OwnerDecisionForQuoteCreation(BaseModel):
    decision_status: Literal["approved", "rejected", "revoked"]
    decision_reason: str
    approval_checkbox: bool

    @model_validator(mode="after")
    def _require_reason_when_approved(self) -> IntakeV3OwnerDecisionForQuoteCreation:
        if self.decision_status == "approved" and not self.decision_reason.strip():
            raise ValueError("decision_reason is required when decision_status is approved")
        return self


class IntakeV3CreateDraftQuoteRequest(BaseModel):
    owner_decision: IntakeV3OwnerDecisionForQuoteCreation
    expected_workspace_id: str
    expected_bridge_status: str = "disabled_by_policy"
    expected_enablement_status: str = "owner_approval_required"
    confirm_create_draft_only: bool
    confirm_no_order: bool
    confirm_no_execution: bool
    confirm_no_inventory: bool

    @model_validator(mode="after")
    def _require_explicit_confirmations(self) -> IntakeV3CreateDraftQuoteRequest:
        if not all(
            (
                self.confirm_create_draft_only,
                self.confirm_no_order,
                self.confirm_no_execution,
                self.confirm_no_inventory,
            )
        ):
            raise ValueError(
                "confirm_create_draft_only, confirm_no_order, confirm_no_execution, "
                "and confirm_no_inventory must all be true"
            )
        return self


class IntakeV3QuoteCreationSnapshotPayload(BaseModel):
    policy_version: str
    source_module: str
    source_workspace_id: str
    sections: dict[str, Any] = Field(default_factory=dict)
    integrity_rules: list[str] = Field(default_factory=list)
    raw_analysis_not_production_truth: bool = True
    holes_not_letters: bool = True


class IntakeV3CreatedDraftQuoteSummary(BaseModel):
    quote_id: int
    quote_code: str
    quote_status: str
    source_module: str
    source_workspace_id: str


class IntakeV3CreateDraftQuoteResponse(BaseModel):
    quote_created: bool
    quote_id: int
    quote_code: str
    quote_status: str
    source_module: str
    source_workspace_id: str
    snapshot_attached: bool
    owner_decision_record_attached: bool
    order_created: bool = False
    execution_plan_created: bool = False
    inventory_mutated: bool = False
    requires_pricing_review: bool = True
    cost_engine_called: bool = False


# ---------------------------------------------------------------------------
# Draft quote review + pricing handoff (read-only — post create-draft-quote)
# ---------------------------------------------------------------------------


class IntakeV3DraftQuoteReviewWarning(BaseModel):
    code: str
    message: str = ""


class IntakeV3DraftQuoteSnapshotSummary(BaseModel):
    snapshot_present: bool = False
    owner_decision_present: bool = False
    confirmed_model_present: bool = False
    finish_variation_present: bool = False
    finish_assignment_present: bool = False
    pricing_input_preview_present: bool = False
    raw_analysis_not_production_truth: bool = True
    holes_not_letters: bool = True
    section_keys: list[str] = Field(default_factory=list)
    integrity_markers: dict[str, Any] = Field(default_factory=dict)
    owner_decision_summary: dict[str, Any] = Field(default_factory=dict)


class IntakeV3DraftQuotePricingHandoff(BaseModel):
    pricing_handoff_status: str = "not_created"
    requires_pricing_review: bool = True
    cost_engine_called: bool = False
    final_price_present: bool = False
    pricing_review_items: list[str] = Field(default_factory=list)
    missing_pricing_inputs: list[str] = Field(default_factory=list)
    safe_next_actions: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)
    checklist: dict[str, bool] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class IntakeV3DraftQuoteConversionGuard(BaseModel):
    can_accept_quote: bool = False
    can_convert_to_order: bool = False
    conversion_blockers: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)


class IntakeV3DraftQuoteReview(BaseModel):
    review_status: str
    is_intake_v3_quote: bool = False
    quote_id: int | None = None
    quote_code: str | None = None
    quote_status: str | None = None
    source_module: str | None = None
    source_workspace_id: str | None = None
    source_workspace_code: str | None = None
    intake_code: str | None = None
    requires_pricing_review: bool = True
    pricing_status: str = "requires_review"
    snapshot_present: bool = False
    owner_decision_present: bool = False
    confirmed_model_present: bool = False
    finish_variation_present: bool = False
    can_accept_quote: bool = False
    can_convert_to_order: bool = False
    conversion_blockers: list[str] = Field(default_factory=list)
    pricing_review_items: list[str] = Field(default_factory=list)
    snapshot_summary: IntakeV3DraftQuoteSnapshotSummary = Field(
        default_factory=IntakeV3DraftQuoteSnapshotSummary
    )
    pricing_handoff: IntakeV3DraftQuotePricingHandoff = Field(
        default_factory=IntakeV3DraftQuotePricingHandoff
    )
    conversion_guard: IntakeV3DraftQuoteConversionGuard = Field(
        default_factory=IntakeV3DraftQuoteConversionGuard
    )
    warnings: list[IntakeV3DraftQuoteReviewWarning] = Field(default_factory=list)
    message: str | None = None
    totals_zero: bool = True
    cost_engine_called: bool = False
    pricing_review_completed: bool = False
    priced_draft: bool = False


# ---------------------------------------------------------------------------
# Pricing review completion (manual priced draft — no CostEngine)
# ---------------------------------------------------------------------------


class IntakeV3ManualPricingInput(BaseModel):
    currency: str = "EUR"
    subtotal: float = Field(ge=0)
    discount_amount: float = Field(ge=0, default=0)
    vat_percent: float = Field(ge=0)
    vat_amount: float = Field(ge=0)
    total: float = Field(ge=0)


class IntakeV3CompletePricingReviewRequest(BaseModel):
    pricing_method: str = "manual_review"
    currency: str = "EUR"
    subtotal: float = Field(ge=0)
    discount_amount: float = Field(ge=0, default=0)
    vat_percent: float = Field(ge=0)
    vat_amount: float = Field(ge=0)
    total: float = Field(ge=0)
    pricing_review_reason: str
    reviewer_confirmation: bool = False
    confirm_quote_stays_draft: bool = False
    confirm_no_order: bool = False
    confirm_no_execution: bool = False
    confirm_no_inventory: bool = False
    expected_quote_id: int | None = None
    expected_intake_code: str | None = None


class IntakeV3PricingReviewRecord(BaseModel):
    status: str
    method: str
    completed_at: str
    completed_by_user_id: str | int
    completed_by_display_name: str | None = None
    reason: str
    currency: str
    subtotal: float
    discount_amount: float
    vat_percent: float
    vat_amount: float
    total: float
    cost_engine_called: bool = False
    quote_stays_draft: bool = True
    priced_draft: bool = True


class IntakeV3CompletePricingReviewResponse(BaseModel):
    pricing_review_completed: bool
    quote_id: int
    quote_code: str
    quote_status: str
    source_module: str
    requires_pricing_review: bool
    priced_draft: bool
    pricing_method: str
    currency: str
    subtotal: float
    discount_amount: float
    vat_percent: float
    vat_amount: float
    total: float
    order_created: bool = False
    execution_plan_created: bool = False
    inventory_mutated: bool = False
    cost_engine_called: bool = False
    can_accept_quote: bool = False
    can_convert_to_order: bool = False


class IntakeV3PricingReviewCompletionState(BaseModel):
    review_status: str
    is_intake_v3_quote: bool = False
    quote_id: int | None = None
    quote_code: str | None = None
    quote_status: str | None = None
    intake_code: str | None = None
    source_workspace_id: str | None = None
    requires_pricing_review: bool = True
    pricing_review_completed: bool = False
    priced_draft: bool = False
    pricing_method: str | None = None
    subtotal: float | None = None
    total: float | None = None
    currency: str | None = None
    can_complete_pricing_review: bool = False
    can_accept_quote: bool = False
    can_convert_to_order: bool = False
    message: str | None = None
    warnings: list[str] = Field(default_factory=list)


class IntakeV3QuoteReadinessBlocker(BaseModel):
    code: str
    message: str = ""


class IntakeV3QuoteReadinessWarning(BaseModel):
    code: str
    message: str = ""


class IntakeV3QuoteAcceptGuardContract(BaseModel):
    requires_priced_draft: bool = True
    requires_pricing_review_completed: bool = True
    requires_owner_confirmation: bool = True
    requires_no_order_created: bool = True
    requires_no_execution_created: bool = True
    next_build_required: bool = True


class IntakeV3QuoteConvertGuardContract(BaseModel):
    requires_accepted_quote: bool = True
    requires_duplicate_order_check: bool = True
    requires_order_snapshot: bool = True
    requires_no_execution_creation_in_same_step: bool = True
    next_build_required: bool = True


class IntakeV3QuoteAcceptReadiness(BaseModel):
    accept_readiness_status: str
    can_accept_now: bool = False
    accept_action_enabled: bool = False
    is_accept_ready_preview: bool = False
    accept_blockers: list[IntakeV3QuoteReadinessBlocker] = Field(default_factory=list)
    accept_warnings: list[IntakeV3QuoteReadinessWarning] = Field(default_factory=list)
    accept_guard_contract: IntakeV3QuoteAcceptGuardContract = Field(
        default_factory=IntakeV3QuoteAcceptGuardContract
    )


class IntakeV3QuoteConvertReadiness(BaseModel):
    convert_readiness_status: str
    can_convert_now: bool = False
    convert_action_enabled: bool = False
    is_convert_ready_preview: bool = False
    convert_blockers: list[IntakeV3QuoteReadinessBlocker] = Field(default_factory=list)
    convert_warnings: list[IntakeV3QuoteReadinessWarning] = Field(default_factory=list)
    convert_guard_contract: IntakeV3QuoteConvertGuardContract = Field(
        default_factory=IntakeV3QuoteConvertGuardContract
    )


class IntakeV3QuoteAcceptConvertNextStep(BaseModel):
    code: str
    title: str = ""
    description: str = ""


class IntakeV3PricedDraftAcceptConvertReadiness(BaseModel):
    review_status: str
    is_intake_v3_quote: bool = False
    quote_id: int | None = None
    quote_code: str | None = None
    quote_status: str | None = None
    intake_code: str | None = None
    source_workspace_id: str | None = None
    pricing_review_completed: bool = False
    priced_draft: bool = False
    requires_pricing_review: bool = True
    final_price_present: bool = False
    order_exists: bool = False
    order_id: int | None = None
    execution_plan_exists: bool = False
    inventory_mutated: bool = False
    production_readiness_status: str | None = None
    production_readiness_blockers: list[str] = Field(default_factory=list)
    ready_for_handoff_preview: bool = False
    can_generate_execution_plan_now: bool = False
    can_generate_execution_tasks_now: bool = False
    can_mutate_inventory_now: bool = False
    can_start_production_now: bool = False
    accept: IntakeV3QuoteAcceptReadiness
    convert: IntakeV3QuoteConvertReadiness
    next_steps: list[IntakeV3QuoteAcceptConvertNextStep] = Field(default_factory=list)
    message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    no_order_created: bool = True
    no_execution_created: bool = True
    no_inventory_mutated: bool = True


class IntakeV3AcceptDecisionRecord(BaseModel):
    status: str
    accepted_at: str
    accepted_by_user_id: str | int
    accepted_by_display_name: str | None = None
    reason: str
    source: str = "operator"
    pricing_review_completed: bool = True
    quote_status_before: str
    quote_status_after: str
    order_created: bool = False
    execution_plan_created: bool = False
    execution_task_created: bool = False
    inventory_mutated: bool = False
    convert_separate: bool = True


class IntakeV3AcceptQuoteRequest(BaseModel):
    expected_quote_id: int | None = None
    expected_intake_code: str | None = None
    accept_decision: str = "approved"
    accept_reason: str
    acceptance_source: str = "operator"
    reviewer_confirmation: bool = False
    confirm_pricing_review_completed: bool = False
    confirm_quote_stays_commercial: bool = False
    confirm_no_order: bool = False
    confirm_no_execution: bool = False
    confirm_no_inventory: bool = False
    confirm_convert_separate: bool = False


class IntakeV3AcceptQuoteResponse(BaseModel):
    accepted: bool
    quote_id: int
    quote_code: str | None = None
    quote_status_before: str
    quote_status_after: str
    source_module: str
    accept_decision_record_attached: bool = True
    pricing_review_completed: bool = True
    order_created: bool = False
    execution_plan_created: bool = False
    execution_task_created: bool = False
    inventory_mutated: bool = False
    can_convert_now: bool = False
    convert_action_enabled: bool = False


class IntakeV3AcceptState(BaseModel):
    review_status: str
    is_intake_v3_quote: bool = False
    quote_id: int | None = None
    quote_code: str | None = None
    quote_status: str | None = None
    intake_code: str | None = None
    source_workspace_id: str | None = None
    pricing_review_completed: bool = False
    priced_draft: bool = False
    accept_completed: bool = False
    can_accept_now: bool = False
    accept_action_enabled: bool = False
    accept_blockers: list[str] = Field(default_factory=list)
    accept_decision_summary: IntakeV3AcceptDecisionRecord | None = None
    message: str | None = None
    warnings: list[str] = Field(default_factory=list)


class IntakeV3OrderSnapshotPayload(BaseModel):
    source_module: str = "intake_v3"
    source_quote_id: int
    source_workspace_id: str | None = None
    quote_intake_code: str | None = None
    quote_code: str | None = None
    created_from_guarded_convert: bool = True
    execution_plan_created: bool = False
    execution_task_created: bool = False
    inventory_mutated: bool = False
    production_started: bool = False
    commercial_currency_handoff: dict[str, Any] | None = None
    final_price: dict[str, Any] | None = None


class IntakeV3ConvertDecisionRecord(BaseModel):
    status: str
    converted_at: str
    converted_by_user_id: str | int
    converted_by_display_name: str | None = None
    reason: str
    source: str = "operator"
    quote_status: str
    order_id: int
    order_code: str | None = None
    order_status: str
    order_created: bool = True
    execution_plan_created: bool = False
    execution_task_created: bool = False
    inventory_mutated: bool = False
    production_started: bool = False
    production_separate: bool = True


class IntakeV3ConvertToOrderRequest(BaseModel):
    expected_quote_id: int | None = None
    expected_intake_code: str | None = None
    convert_decision: str = "approved"
    convert_reason: str
    conversion_source: str = "operator"
    reviewer_confirmation: bool = False
    confirm_quote_accepted: bool = False
    confirm_pricing_review_completed: bool = False
    confirm_create_order_only: bool = False
    confirm_no_execution_plan: bool = False
    confirm_no_execution_tasks: bool = False
    confirm_no_inventory: bool = False
    confirm_production_separate: bool = False


class IntakeV3ConvertToOrderResponse(BaseModel):
    converted: bool
    quote_id: int
    quote_code: str | None = None
    quote_status: str
    order_id: int
    order_code: str | None = None
    order_status: str
    source_module: str
    convert_decision_record_attached: bool = True
    order_created: bool = True
    execution_plan_created: bool = False
    execution_task_created: bool = False
    inventory_mutated: bool = False
    production_started: bool = False
    can_start_production_now: bool = False


class IntakeV3ConvertToOrderState(BaseModel):
    review_status: str
    is_intake_v3_quote: bool = False
    quote_id: int | None = None
    quote_code: str | None = None
    quote_status: str | None = None
    intake_code: str | None = None
    source_workspace_id: str | None = None
    accept_completed: bool = False
    pricing_review_completed: bool = False
    order_exists: bool = False
    existing_order_id: int | None = None
    existing_order_code: str | None = None
    convert_completed: bool = False
    can_convert_now: bool = False
    convert_action_enabled: bool = False
    convert_blockers: list[str] = Field(default_factory=list)
    order_snapshot_summary: IntakeV3OrderSnapshotPayload | None = None
    convert_decision_summary: IntakeV3ConvertDecisionRecord | None = None
    message: str | None = None
    warnings: list[str] = Field(default_factory=list)


class IntakeV3OrderMissingRequirement(BaseModel):
    code: str
    severity: str = "blocking"
    message: str
    source: str


class IntakeV3OrderAvailableDataSummary(BaseModel):
    has_order_linkage: bool = False
    has_quote_linkage: bool = False
    has_confirmed_model: bool = False
    has_finish_assignments: bool = False
    has_pricing_review: bool = False
    has_accept_decision: bool = False
    has_convert_decision: bool = False
    has_dimensions: bool = False
    has_text_or_artwork_summary: bool = False
    has_layer_summary: bool = False
    global_finish_summary: str | None = None
    group_overrides_count: int = 0
    letter_overrides_count: int = 0
    geometry_snapshot_available: bool = False
    geometry_status: str = "geometry_missing"
    perimeter_classification_status: str | None = None
    face_cutting_perimeter_available: bool = False
    backing_cutting_perimeter_available: bool = False
    return_material_perimeter_available: bool = False
    bevel_perimeter_available: bool = False
    layer_role_confirmation_status: str | None = None
    operator_confirmed_layer_roles_count: int = 0
    unconfirmed_layer_roles_count: int = 0
    ignored_layer_roles_count: int = 0
    perimeter_classification_confidence: str | None = None
    layer_role_confirmation_effective_source: str | None = None
    layer_role_confirmation_snapshot_stale: bool = False
    layer_role_confirmation_stale_reason: str | None = None
    layer_role_confirmation_can_refresh_quote_snapshot: bool = False
    material_availability_available: bool = False
    material_availability_status: str | None = None
    material_shortage_rows_count: int = 0
    material_manual_check_rows_count: int = 0
    material_indirect_consumables_count: int = 0
    procurement_preview_available: bool = False
    procurement_purchase_recommended_count: int = 0
    procurement_owner_decision_required_count: int = 0
    procurement_advance_recommended_count: int = 0
    procurement_manual_check_count: int = 0


class IntakeV3ProductionHandoffPreview(BaseModel):
    product_template: str | None = None
    production_model_summary: dict[str, Any] = Field(default_factory=dict)
    finish_summary: dict[str, Any] = Field(default_factory=dict)
    commercial_summary: dict[str, Any] = Field(default_factory=dict)
    production_boundaries: dict[str, Any] = Field(default_factory=dict)


class IntakeV3TaskGenerationPreviewContract(BaseModel):
    would_generate_execution_plan: bool = False
    would_generate_tasks_preview_only: bool = True
    candidate_task_groups: list[str] = Field(default_factory=list)
    requires_future_build: bool = True


class IntakeV3MaterialReadinessPreviewContract(BaseModel):
    would_check_materials_preview_only: bool = True
    materials_expected: list[str] = Field(default_factory=list)
    material_cost_breakdown: str = "future_build"
    inventory_check: str = "future_build"
    inventory_mutation_allowed: bool = False
    requires_future_build: bool = True


class IntakeV3OrderProductionReadinessResponse(BaseModel):
    order_id: int | None = None
    order_code: str | None = None
    quote_id: int | None = None
    quote_code: str | None = None
    source_module: str | None = None
    source_workspace_id: str | None = None
    is_intake_v3_order: bool = False
    created_from_guarded_convert: bool = False
    order_status: str | None = None
    production_readiness_status: str
    ready_for_handoff_preview: bool = False
    can_generate_execution_plan_now: bool = False
    can_generate_execution_tasks_now: bool = False
    can_mutate_inventory_now: bool = False
    can_start_production_now: bool = False
    available_data: IntakeV3OrderAvailableDataSummary = Field(
        default_factory=IntakeV3OrderAvailableDataSummary
    )
    missing_requirements: list[IntakeV3OrderMissingRequirement] = Field(default_factory=list)
    production_readiness_blockers: list[str] = Field(default_factory=list)
    handoff_preview: IntakeV3ProductionHandoffPreview = Field(
        default_factory=IntakeV3ProductionHandoffPreview
    )
    task_generation_preview_contract: IntakeV3TaskGenerationPreviewContract = Field(
        default_factory=IntakeV3TaskGenerationPreviewContract
    )
    material_readiness_preview_contract: IntakeV3MaterialReadinessPreviewContract = Field(
        default_factory=IntakeV3MaterialReadinessPreviewContract
    )
    execution_plan_created: bool = False
    execution_task_created: bool = False
    inventory_mutated: bool = False
    production_started: bool = False
    warnings: list[str] = Field(default_factory=list)


class IntakeV3WorkspacePreviewResponse(BaseModel):
    workspace_id: str
    workspace_code: str
    preview: IntakeV3WorkspacePreview
    build_warnings: list[str] = Field(default_factory=list)
    build_blockers: list[str] = Field(default_factory=list)
    is_preview_complete: bool = False


# ---------------------------------------------------------------------------
# Controlled field editor (allowlist patches only)
# ---------------------------------------------------------------------------


class IntakeV3FieldPatch(BaseModel):
    field_path: str
    value: Any


class IntakeV3WorkspaceFieldPatchRequest(BaseModel):
    patches: list[IntakeV3FieldPatch] = Field(default_factory=list)
    regenerate_preview: bool = True


class IntakeV3FieldPatchItemResult(BaseModel):
    field_path: str
    status: str
    message: str = ""


class IntakeV3WorkspaceFieldPatchResponse(BaseModel):
    workspace: IntakeV3WorkspaceResponse
    preview: IntakeV3WorkspacePreviewResponse | None = None
    applied_patches: list[IntakeV3FieldPatchItemResult] = Field(default_factory=list)
    rejected_patches: list[IntakeV3FieldPatchItemResult] = Field(default_factory=list)
    readiness_status: str | None = None


class IntakeV3EditableFieldDefinition(BaseModel):
    field_path: str
    label: str
    field_type: str
    enum_options: list[str] = Field(default_factory=list)
    description: str = ""
    required: bool = True
    min_value: float | None = None


class IntakeV3EditableFieldsResponse(BaseModel):
    fields: list[IntakeV3EditableFieldDefinition] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# SVG upload + raw analysis (draft workspace only — no production confirmation)
# ---------------------------------------------------------------------------


class IntakeV3SvgAnalysisWarning(BaseModel):
    code: str
    message: str = ""


class IntakeV3SvgUploadResponse(BaseModel):
    workspace: IntakeV3WorkspaceResponse
    preview: IntakeV3WorkspacePreviewResponse
    raw_svg_analysis: RawSvgAnalysis
    warnings: list[IntakeV3SvgAnalysisWarning] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Production model review (operator confirmation — not auto from raw analysis)
# ---------------------------------------------------------------------------


class IntakeV3ProductionModelReviewCandidate(BaseModel):
    suggested_letter_count: int | None = None
    suggested_cut_contour_count: int | None = None
    suggested_inner_hole_count: int | None = None
    raw_path_count: int = 0
    raw_closed_count: int = 0
    detected_groups: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source: str = "raw_svg_analysis"
    confirmed: bool = False
    template_code: str = PILOT_TEMPLATE_CODE


class IntakeV3ConfirmProductionModelRequest(BaseModel):
    letter_count: int = Field(gt=0)
    cut_contour_count: int = Field(ge=0)
    inner_hole_count: int = Field(ge=0)
    ignored_object_ids: list[str] = Field(default_factory=list)
    operator_notes: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    confirmed: bool = False


class IntakeV3ProductionModelReviewCandidateResponse(BaseModel):
    workspace_id: str
    review_candidate: IntakeV3ProductionModelReviewCandidate


class IntakeV3ConfirmProductionModelResponse(BaseModel):
    workspace: IntakeV3WorkspaceResponse
    preview: IntakeV3WorkspacePreviewResponse
    review_candidate: IntakeV3ProductionModelReviewCandidate | None = None
    confirmed_production_model: ConfirmedProductionModel
    readiness_status: str | None = None
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Finish assignment per letter / group API (payload only — no quote/order writes)
# ---------------------------------------------------------------------------


class IntakeV3ApplyFinishAssignmentsRequest(BaseModel):
    letter_group_finish_assignments: list[IntakeV3LetterGroupFinishAssignment] = Field(
        default_factory=list
    )
    letter_finish_assignments: list[IntakeV3LetterFinishAssignment] = Field(default_factory=list)
    regenerate_preview: bool = True


class IntakeV3FinishAssignmentTarget(BaseModel):
    letter_id: str
    label: str = ""
    sequence_index: int | None = None
    is_hole: bool = False


class IntakeV3FinishAssignmentTargetsResponse(BaseModel):
    workspace_id: str
    targets: list[IntakeV3FinishAssignmentTarget] = Field(default_factory=list)
    letter_count: int = 0


class IntakeV3FinishAssignmentSummary(BaseModel):
    finish_assignment_status: str = "global_only"
    group_assignment_count: int = 0
    letter_override_count: int = 0
    finish_variations_present: bool = False
    assignment_summary: str = ""
    warnings: list[str] = Field(default_factory=list)
    effective_finish_samples: list[dict[str, Any]] = Field(default_factory=list)


class IntakeV3FinishAssignmentValidationResult(BaseModel):
    is_valid: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = ""


class IntakeV3FinishAssignmentsStateResponse(BaseModel):
    workspace_id: str
    letter_group_finish_assignments: list[IntakeV3LetterGroupFinishAssignment] = Field(
        default_factory=list
    )
    letter_finish_assignments: list[IntakeV3LetterFinishAssignment] = Field(default_factory=list)
    finish_assignment_status: str | None = None
    summary: IntakeV3FinishAssignmentSummary = Field(default_factory=IntakeV3FinishAssignmentSummary)


class IntakeV3ApplyFinishAssignmentsResponse(BaseModel):
    workspace: IntakeV3WorkspaceResponse
    preview: IntakeV3WorkspacePreviewResponse | None = None
    summary: IntakeV3FinishAssignmentSummary
    validation: IntakeV3FinishAssignmentValidationResult


# ---------------------------------------------------------------------------
# Layer finish assignments API (payload only — no quote/order writes)
# ---------------------------------------------------------------------------


class IntakeV3LayerFinishAssignmentTarget(BaseModel):
    layer_key: str
    layer_name: str | None = None
    confirmed_role: str | None = None
    finish_target_type: LayerFinishTargetType | None = None
    requires_finish: bool = False
    confirmation_state: str | None = None


class IntakeV3LayerFinishAssignmentTargetsResponse(BaseModel):
    workspace_id: str
    targets: list[IntakeV3LayerFinishAssignmentTarget] = Field(default_factory=list)
    target_count: int = 0


class IntakeV3LayerFinishAssignmentSummary(BaseModel):
    layer_finish_assignment_status: LayerFinishAssignmentStatus = "missing"
    assignment_count: int = 0
    confirmed_count: int = 0
    pending_count: int = 0
    not_required_count: int = 0
    assignment_summary: str = ""
    preview_items: list[IntakeV3LayerFinishPreviewItem] = Field(default_factory=list)


class IntakeV3LayerFinishAssignmentValidationResult(BaseModel):
    is_valid: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = ""


class IntakeV3ApplyLayerFinishAssignmentsRequest(BaseModel):
    layer_finish_assignments: list[IntakeV3LayerFinishAssignment] = Field(default_factory=list)
    regenerate_preview: bool = True


class IntakeV3LayerFinishAssignmentsStateResponse(BaseModel):
    workspace_id: str
    layer_finish_assignments: list[IntakeV3LayerFinishAssignment] = Field(default_factory=list)
    layer_finish_assignment_status: LayerFinishAssignmentStatus | None = None
    summary: IntakeV3LayerFinishAssignmentSummary = Field(
        default_factory=IntakeV3LayerFinishAssignmentSummary
    )


class IntakeV3ApplyLayerFinishAssignmentsResponse(BaseModel):
    workspace: IntakeV3WorkspaceResponse
    preview: IntakeV3WorkspacePreviewResponse | None = None
    summary: IntakeV3LayerFinishAssignmentSummary
    validation: IntakeV3LayerFinishAssignmentValidationResult


class IntakeV3ApplyLightingPlanRequest(BaseModel):
    lighting_plan: IntakeV3LightingPlan
    regenerate_preview: bool = True


class IntakeV3LightingPlanStateResponse(BaseModel):
    workspace_id: str
    lighting_plan: IntakeV3LightingPlan
    lighting_plan_status: LightingPlanStatus | None = None
    summary: IntakeV3LightingPlanSummary = Field(default_factory=IntakeV3LightingPlanSummary)


class IntakeV3ApplyLightingPlanResponse(BaseModel):
    workspace: IntakeV3WorkspaceResponse
    preview: IntakeV3WorkspacePreviewResponse | None = None
    summary: IntakeV3LightingPlanSummary
    validation: IntakeV3LightingPlanValidationResult


# ---------------------------------------------------------------------------
# Material quantity / geometry / material cost breakdown (materials-only)
# ---------------------------------------------------------------------------


class IntakeV3MaterialBreakdownWarning(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    source: str


class IntakeV3GeometrySummary(BaseModel):
    product_template: str = PILOT_TEMPLATE_CODE
    source: str = "confirmed_production_model_snapshot"
    real_letters_count: int = 0
    closed_contours_count: int = 0
    holes_count: int = 0
    outer_contours_count: int = 0
    inner_holes_count: int = 0
    total_letter_perimeter_ml: float = 0.0
    return_material_perimeter_ml: float = 0.0
    cutting_perimeter_ml: float = 0.0
    bevel_perimeter_ml: float = 0.0
    face_area_m2: float = 0.0
    backing_area_m2: float = 0.0
    vinyl_area_m2: float = 0.0
    calculation_quality: str = "missing"
    geometry_snapshot_source: str | None = None
    face_cutting_perimeter_ml: float = 0.0
    perimeter_classification_status: str | None = None
    perimeter_classification_source: str | None = None
    operator_confirmed_layer_roles: bool = False
    perimeter_classification_confidence: str | None = None
    layer_role_confirmation_effective_source: str | None = None
    layer_role_confirmation_snapshot_stale: bool = False
    warnings: list[str] = Field(default_factory=list)


class IntakeV3MaterialQuantityRow(BaseModel):
    material_key: str
    display_name: str
    category: str
    quantity: float = 0.0
    unit: str
    quantity_source: str
    quantity_quality: str
    waste_percent: float | None = None
    quantity_with_waste: float = 0.0
    included: bool = True
    registry_code: str | None = None
    material_intent: str | None = None
    stock_tracking_class: str | None = None
    warnings: list[str] = Field(default_factory=list)


class IntakeV3MaterialCostRow(BaseModel):
    material_key: str
    display_name: str
    quantity: float = 0.0
    unit: str
    quantity_with_waste: float = 0.0
    unit_price: float | None = None
    currency: str = "EUR"
    price_source: str = "missing"
    material_cost: float | None = None
    cost_quality: str = "missing"
    included_in_total: bool = False
    warnings: list[str] = Field(default_factory=list)


class IntakeV3MaterialBreakdownTotals(BaseModel):
    material_cost_total: float = 0.0
    currency: str = "EUR"
    contains_estimates: bool = False
    contains_missing_prices: bool = False
    contains_missing_quantities: bool = False


class IntakeV3MaterialBreakdownResponse(BaseModel):
    source_module: str = "intake_v3"
    source_type: str
    source_id: str
    order_id: int | None = None
    quote_id: int | None = None
    source_workspace_id: str | None = None
    is_intake_v3: bool = False
    breakdown_scope: str = "materials_only_informative"
    includes_geometry: bool = True
    includes_material_quantities: bool = True
    includes_material_costs: bool = True
    includes_operations_cost: bool = False
    includes_labor_cost: bool = False
    includes_markup: bool = False
    includes_profit: bool = False
    inventory_mutation_allowed: bool = False
    costengine_used: bool = False
    geometry_summary: IntakeV3GeometrySummary = Field(default_factory=IntakeV3GeometrySummary)
    material_rows: list[IntakeV3MaterialQuantityRow] = Field(default_factory=list)
    cost_rows: list[IntakeV3MaterialCostRow] = Field(default_factory=list)
    totals: IntakeV3MaterialBreakdownTotals = Field(default_factory=IntakeV3MaterialBreakdownTotals)
    totals_by_currency: list[IntakeV3MaterialBreakdownTotals] = Field(default_factory=list)
    warnings: list[IntakeV3MaterialBreakdownWarning] = Field(default_factory=list)
    future_builds: list[str] = Field(default_factory=list)
    layer_role_confirmation_effective_source: str | None = None
    layer_role_confirmation_snapshot_source: str | None = None
    layer_role_confirmation_snapshot_stale: bool = False
    layer_role_confirmation_stale_reason: str | None = None
    downstream_uses_effective_source: bool = True


# ---------------------------------------------------------------------------
# Material availability (read-only inventory preview — no reservation/mutation)
# ---------------------------------------------------------------------------

AVAILABILITY_SCOPE_READ_ONLY = "read_only_material_availability_preview"


class IntakeV3MaterialAvailabilityMatch(BaseModel):
    match_strategy: str = "none"
    confidence: str = "low"
    inventory_material_id: int | None = None
    inventory_code: str | None = None
    inventory_name: str | None = None
    inventory_unit: str | None = None
    inventory_status: str | None = None
    source_review_status: str | None = None


class IntakeV3MaterialAvailabilityQuantity(BaseModel):
    required: float = 0.0
    required_unit: str
    required_with_waste: float | None = None
    available: float | None = None
    available_unit: str | None = None
    shortage: float | None = None
    unit_comparison: str = "not_applicable"


class IntakeV3MaterialAvailabilityWarning(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    source: str


class IntakeV3MaterialAvailabilityRow(BaseModel):
    material_key: str
    display_name: str
    category: str
    registry_code: str | None = None
    material_intent: str | None = None
    tracking_class: str = "stock_tracked"
    availability_status: str = "unknown"
    recommended_action: str = "manual_check"
    requires_operator_verification: bool = False
    recommends_manual_procurement: bool = False
    match: IntakeV3MaterialAvailabilityMatch = Field(default_factory=IntakeV3MaterialAvailabilityMatch)
    quantity: IntakeV3MaterialAvailabilityQuantity
    warnings: list[str] = Field(default_factory=list)


class IntakeV3MaterialAvailabilityBoundary(BaseModel):
    read_only: bool = True
    creates_stock_movement: bool = False
    reserves_inventory: bool = False
    mutates_inventory: bool = False
    creates_purchase_order: bool = False
    creates_execution_plan: bool = False
    creates_execution_tasks: bool = False
    costengine_used: bool = False
    modifies_order: bool = False
    modifies_quote: bool = False


class IntakeV3MaterialAvailabilitySummary(BaseModel):
    total_rows: int = 0
    available_count: int = 0
    shortage_count: int = 0
    manual_check_count: int = 0
    indirect_consumables_count: int = 0
    no_match_count: int = 0
    ambiguous_match_count: int = 0
    not_tracked_count: int = 0
    unknown_count: int = 0
    overall_status: str = "unknown"


class IntakeV3MaterialAvailabilityResponse(BaseModel):
    source_module: str = "intake_v3"
    source_type: str
    source_id: str
    workspace_id: str | None = None
    quote_id: int | None = None
    order_id: int | None = None
    is_intake_v3: bool = False
    availability_scope: str = AVAILABILITY_SCOPE_READ_ONLY
    material_breakdown_available: bool = False
    inventory_source_available: bool = True
    summary: IntakeV3MaterialAvailabilitySummary = Field(default_factory=IntakeV3MaterialAvailabilitySummary)
    rows: list[IntakeV3MaterialAvailabilityRow] = Field(default_factory=list)
    warnings: list[IntakeV3MaterialAvailabilityWarning] = Field(default_factory=list)
    boundary: IntakeV3MaterialAvailabilityBoundary = Field(
        default_factory=IntakeV3MaterialAvailabilityBoundary
    )


# ---------------------------------------------------------------------------
# Procurement preview (read-only — no PO / supplier order / inventory mutation)
# ---------------------------------------------------------------------------

PROCUREMENT_SCOPE_READ_ONLY = "read_only_procurement_preview"


class IntakeV3ProcurementQuantityHint(BaseModel):
    value: float | None = None
    unit: str | None = None
    source: str = "unknown"


class IntakeV3ProcurementSourceHint(BaseModel):
    source_name: str | None = None
    source_url: str | None = None
    source_review_status: str | None = None
    unit_cost_hint: float | None = None
    currency: str | None = None
    notes: str | None = None


class IntakeV3ProcurementPreviewRow(BaseModel):
    row_id: str
    material_key: str
    material_intent: str | None = None
    material_code: str | None = None
    display_name: str
    availability_status: str
    tracking_class: str | None = None
    required_quantity: IntakeV3ProcurementQuantityHint
    available_quantity: IntakeV3ProcurementQuantityHint | None = None
    shortage_quantity: IntakeV3ProcurementQuantityHint | None = None
    manual_check_reason: str | None = None
    procurement_status: str = "unknown"
    recommended_action: str = "manual_check"
    urgency: str = "normal"
    purchase_decision_type: str = "none"
    decision_required: bool = False
    decision_owner: str = "none"
    advance_recommended: bool = False
    is_expensive_material: bool = False
    is_indirect_consumable: bool = False
    requires_manual_stock_check: bool = False
    source_hint: IntakeV3ProcurementSourceHint = Field(default_factory=IntakeV3ProcurementSourceHint)
    warnings: list[str] = Field(default_factory=list)


class IntakeV3ProcurementPreviewSummary(BaseModel):
    rows_count: int = 0
    purchase_recommended_count: int = 0
    manual_check_count: int = 0
    owner_decision_required_count: int = 0
    advance_recommended_count: int = 0
    preventive_restock_count: int = 0
    indirect_consumable_count: int = 0
    no_action_count: int = 0
    warnings_count: int = 0
    overall_status: str = "unknown"


class IntakeV3ProcurementPreviewBoundary(BaseModel):
    read_only: bool = True
    creates_purchase_order: bool = False
    creates_supplier_order: bool = False
    reserves_inventory: bool = False
    creates_stock_movement: bool = False
    mutates_inventory: bool = False
    creates_execution_plan: bool = False
    creates_execution_tasks: bool = False
    modifies_order: bool = False
    modifies_quote: bool = False
    modifies_pricing: bool = False
    costengine_used: bool = False


class IntakeV3ProcurementPreviewWarning(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    source: str = "procurement_preview"


class IntakeV3ProcurementPreviewResponse(BaseModel):
    source_module: str = "intake_v3"
    source_type: str
    source_id: str
    workspace_id: str | None = None
    quote_id: int | None = None
    order_id: int | None = None
    is_intake_v3: bool = False
    procurement_scope: str = PROCUREMENT_SCOPE_READ_ONLY
    material_availability_available: bool = False
    summary: IntakeV3ProcurementPreviewSummary = Field(default_factory=IntakeV3ProcurementPreviewSummary)
    rows: list[IntakeV3ProcurementPreviewRow] = Field(default_factory=list)
    warnings: list[IntakeV3ProcurementPreviewWarning] = Field(default_factory=list)
    boundary: IntakeV3ProcurementPreviewBoundary = Field(default_factory=IntakeV3ProcurementPreviewBoundary)


# ---------------------------------------------------------------------------
# Geometry metrics snapshot (technical production inputs — not commercial truth)
# ---------------------------------------------------------------------------

GEOMETRY_METRICS_SNAPSHOT_VERSION = "geometry_metrics_snapshot_v1"


class IntakeV3GeometryMetricCounts(BaseModel):
    real_letter_count: int = 0
    cut_contour_count: int = 0
    inner_hole_count: int = 0


class IntakeV3GeometryMetricDimensions(BaseModel):
    width_mm: float | None = None
    height_mm: float | None = None
    depth_mm: float | None = None
    area_m2: float | None = None
    bounding_box_source: str = "estimated"


class IntakeV3GeometryMetricPerimeters(BaseModel):
    face_cutting_perimeter_ml: float | None = None
    backing_cutting_perimeter_ml: float | None = None
    return_material_perimeter_ml: float | None = None
    bevel_perimeter_ml: float | None = None
    total_letter_perimeter_ml: float | None = None
    cutting_perimeter_ml: float | None = None


class IntakeV3GeometryMetricAreas(BaseModel):
    face_area_m2: float | None = None
    backing_area_m2: float | None = None
    estimated_area_m2: float | None = None
    vinyl_area_m2: float | None = None


class IntakeV3OperationGeometryMetric(BaseModel):
    available: bool = False
    quality: str = "missing"
    basis: list[str] = Field(default_factory=list)


class IntakeV3GeometryMetricWarning(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    source: str = "geometry_metrics_snapshot"


class IntakeV3GeometryMetricsSnapshot(BaseModel):
    schema_version: str = GEOMETRY_METRICS_SNAPSHOT_VERSION
    source_module: str = "intake_v3"
    source_type: str = "workspace"
    source_id: str = ""
    template_key: str = PILOT_TEMPLATE_CODE
    generated_at: str | None = None
    metric_source: str = "estimated"
    confidence: str = "partial"
    counts: IntakeV3GeometryMetricCounts = Field(default_factory=IntakeV3GeometryMetricCounts)
    dimensions: IntakeV3GeometryMetricDimensions = Field(
        default_factory=IntakeV3GeometryMetricDimensions
    )
    perimeters: IntakeV3GeometryMetricPerimeters = Field(
        default_factory=IntakeV3GeometryMetricPerimeters
    )
    areas: IntakeV3GeometryMetricAreas = Field(default_factory=IntakeV3GeometryMetricAreas)
    operation_geometry: dict[str, IntakeV3OperationGeometryMetric] = Field(default_factory=dict)
    warnings: list[IntakeV3GeometryMetricWarning] = Field(default_factory=list)
    source_keys: list[str] = Field(default_factory=list)
    holes_not_letters: bool = True
    geometry_status: str = "geometry_partial"
    data_freshness: str = "snapshot_v1"
    path_perimeter_classification: dict[str, Any] | None = None
    layer_role_confirmation_status: str | None = None


LAYER_ROLE_CONFIRMATION_VERSION = "layer_role_confirmation_v1"

LayerRoleConfirmationStatus = Literal["complete", "partial", "missing"]
LayerRoleConfirmationState = Literal["confirmed", "ignored", "pending", "unconfirmed"]


class IntakeV3LayerRoleConfirmationMetric(BaseModel):
    perimeter_mm: float | None = None
    area_mm2: float | None = None
    closed_contour_count: int | None = None
    path_count: int | None = None
    polygon_count: int | None = None
    rect_count: int | None = None
    element_total: int | None = None


class IntakeV3LayerColorFillGroup(BaseModel):
    color: str
    label: str = ""
    element_count: int = 0
    kind: str = "fill"


class IntakeV3LayerColorEvidence(BaseModel):
    fills: list[str] = Field(default_factory=list)
    strokes: list[str] = Field(default_factory=list)
    dominant_fill: str | None = None
    dominant_stroke: str | None = None
    is_multicolor: bool = False
    fill_groups: list[IntakeV3LayerColorFillGroup] = Field(default_factory=list)


class IntakeV3LayerFontEvidence(BaseModel):
    has_text: bool = False
    font_families: list[str] = Field(default_factory=list)
    converted_to_paths: bool = False
    note: str | None = None


class IntakeV3LayerRoleConfirmationLayer(BaseModel):
    layer_key: str
    layer_id: str | None = None
    layer_name: str | None = None
    auto_role: str = "unknown"
    auto_confidence: str = "low"
    confirmed_role: str | None = None
    confirmed_confidence: str | None = None
    confirmation_state: LayerRoleConfirmationState = "pending"
    operator_note: str | None = None
    metrics: IntakeV3LayerRoleConfirmationMetric = Field(
        default_factory=IntakeV3LayerRoleConfirmationMetric
    )
    color_evidence: IntakeV3LayerColorEvidence | None = None
    font_evidence: IntakeV3LayerFontEvidence | None = None


class IntakeV3LayerRoleConfirmationWarning(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    source: str


class IntakeV3LayerRoleConfirmationSnapshot(BaseModel):
    schema_version: str = LAYER_ROLE_CONFIRMATION_VERSION
    source_module: str = "intake_v3"
    workspace_id: str = ""
    generated_from: str = "drawable_layer_summary.layers"
    confirmed_at: str | None = None
    confirmed_by: str | None = None
    confirmation_status: LayerRoleConfirmationStatus = "missing"
    layers: list[IntakeV3LayerRoleConfirmationLayer] = Field(default_factory=list)
    ignored_layers: list[str] = Field(default_factory=list)
    unknown_layers: list[str] = Field(default_factory=list)
    warnings: list[IntakeV3LayerRoleConfirmationWarning] = Field(default_factory=list)


class IntakeV3LayerRoleConfirmationUpdateLayer(BaseModel):
    layer_key: str
    confirmed_role: str
    confirmation_state: LayerRoleConfirmationState = "confirmed"
    operator_note: str | None = None


class IntakeV3LayerRoleConfirmationUpdateRequest(BaseModel):
    layers: list[IntakeV3LayerRoleConfirmationUpdateLayer] = Field(default_factory=list)


class IntakeV3LayerRoleConfirmationResponse(BaseModel):
    source_module: str | None = None
    source_type: str
    source_id: str
    order_id: int | None = None
    quote_id: int | None = None
    source_workspace_id: str | None = None
    is_intake_v3: bool = False
    snapshot_available: bool = False
    confirmation_status: LayerRoleConfirmationStatus = "missing"
    persisted: bool = False
    layer_role_confirmation_snapshot: IntakeV3LayerRoleConfirmationSnapshot | None = None
    warnings: list[IntakeV3LayerRoleConfirmationWarning] = Field(default_factory=list)
    downstream_consumers: list[str] = Field(
        default_factory=lambda: [
            "geometry_metrics_snapshot",
            "path_perimeter_classification",
            "material_breakdown",
            "production_readiness",
            "production_task_dry_run",
        ]
    )
    mutates_inventory: bool = False
    creates_execution_tasks: bool = False
    costengine_used: bool = False


class IntakeV3LayerRolePropagationCounts(BaseModel):
    effective_confirmed_layers: int = 0
    snapshot_confirmed_layers: int = 0
    changed_layers: int = 0
    unknown_layers: int = 0
    ignored_layers: int = 0


class IntakeV3LayerRoleSnapshotChangedLayer(BaseModel):
    layer_key: str
    snapshot_role: str | None = None
    effective_role: str | None = None
    change_type: str = "role_changed"


class IntakeV3LayerRolePropagationWarning(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    source: str = "layer_role_confirmation_propagation"


class IntakeV3LayerRolePropagationBoundary(BaseModel):
    modifies_quote_status: bool = False
    modifies_order_status: bool = False
    modifies_inventory: bool = False
    creates_execution_plan: bool = False
    creates_execution_tasks: bool = False
    costengine_used: bool = False


class IntakeV3LayerRoleConfirmationPropagationResponse(BaseModel):
    source_module: str = "intake_v3"
    source_type: str
    source_id: str
    workspace_id: str | None = None
    quote_id: int | None = None
    order_id: int | None = None
    is_intake_v3: bool = False
    effective_source: str = "missing"
    snapshot_source: str = "missing"
    layer_role_confirmation_status: str = "missing"
    effective_confirmed_at: str | None = None
    snapshot_confirmed_at: str | None = None
    is_snapshot_stale: bool = False
    stale_reason: str | None = None
    can_refresh_quote_snapshot: bool = False
    refresh_blocked_reason: str | None = None
    refresh_required_for_downstream_read: bool = False
    downstream_uses_effective_source: bool = True
    counts: IntakeV3LayerRolePropagationCounts = Field(default_factory=IntakeV3LayerRolePropagationCounts)
    changed_layers: list[IntakeV3LayerRoleSnapshotChangedLayer] = Field(default_factory=list)
    warnings: list[IntakeV3LayerRolePropagationWarning] = Field(default_factory=list)
    boundary: IntakeV3LayerRolePropagationBoundary = Field(default_factory=IntakeV3LayerRolePropagationBoundary)


class IntakeV3LayerRoleTechnicalSnapshotRefreshResponse(BaseModel):
    quote_id: int
    workspace_id: str
    refresh_status: str = "refreshed"
    is_snapshot_stale: bool = False
    effective_source: str = "missing"
    snapshot_source: str = "missing"
    layer_role_confirmation_status: str = "missing"
    warnings: list[IntakeV3LayerRolePropagationWarning] = Field(default_factory=list)
    boundary: IntakeV3LayerRolePropagationBoundary = Field(default_factory=IntakeV3LayerRolePropagationBoundary)
    modifies_quote_status: bool = False
    modifies_quote_pricing: bool = False
    modifies_order: bool = False
    creates_execution_plan: bool = False
    creates_execution_tasks: bool = False
    mutates_inventory: bool = False
    costengine_used: bool = False


class IntakeV3PathPerimeterClassificationMetric(BaseModel):
    value: float | None = None
    unit: str = "ml"
    quality: str = "missing"
    source: str | None = None
    basis: list[str] = Field(default_factory=list)


class IntakeV3PathPerimeterClassificationResponse(BaseModel):
    source_module: str | None = None
    source_type: str
    source_id: str
    order_id: int | None = None
    quote_id: int | None = None
    source_workspace_id: str | None = None
    is_intake_v3: bool = False
    classification_available: bool = False
    classification_status: str = "missing"
    geometry_status: str = "geometry_missing"
    path_perimeter_classification: dict[str, Any] | None = None
    warnings: list[IntakeV3GeometryMetricWarning] = Field(default_factory=list)
    downstream_consumers: list[str] = Field(
        default_factory=lambda: [
            "material_breakdown",
            "production_readiness",
            "production_task_dry_run",
        ]
    )
    layer_role_confirmation_effective_source: str | None = None
    layer_role_confirmation_snapshot_source: str | None = None
    layer_role_confirmation_snapshot_stale: bool = False
    layer_role_confirmation_stale_reason: str | None = None
    downstream_uses_effective_source: bool = True
    mutates_inventory: bool = False
    creates_execution_tasks: bool = False
    costengine_used: bool = False


class IntakeV3GeometryMetricsSnapshotResponse(BaseModel):
    source_module: str | None = None
    source_type: str
    source_id: str
    order_id: int | None = None
    quote_id: int | None = None
    source_workspace_id: str | None = None
    is_intake_v3: bool = False
    snapshot_available: bool = False
    geometry_status: str = "geometry_missing"
    snapshot: IntakeV3GeometryMetricsSnapshot | None = None
    warnings: list[IntakeV3GeometryMetricWarning] = Field(default_factory=list)
    downstream_consumers: list[str] = Field(
        default_factory=lambda: [
            "material_breakdown",
            "production_readiness",
            "production_task_dry_run",
        ]
    )
    layer_role_confirmation_effective_source: str | None = None
    layer_role_confirmation_snapshot_source: str | None = None
    layer_role_confirmation_snapshot_stale: bool = False
    layer_role_confirmation_stale_reason: str | None = None
    downstream_uses_effective_source: bool = True
    mutates_inventory: bool = False
    creates_execution_tasks: bool = False
    costengine_used: bool = False


# ---------------------------------------------------------------------------
# Production task generation dry-run (preview only — no ExecutionPlan/Task)
# ---------------------------------------------------------------------------


class IntakeV3TaskGenerationBlocker(BaseModel):
    code: str
    severity: str = "blocking"
    message: str
    source: str


class IntakeV3CandidateTaskInput(BaseModel):
    label: str
    value: str | int | float | bool | None = None
    unit: str | None = None
    quality: str = "calculated"
    availability_status: str | None = None
    procurement_status: str | None = None


class IntakeV3CandidateTaskDependency(BaseModel):
    from_candidate_task_id: str
    to_candidate_task_id: str
    dependency_type: str = "blocks"
    reason: str | None = None


class IntakeV3CandidateProductionTask(BaseModel):
    candidate_task_id: str
    group_key: str
    title: str
    description: str | None = None
    operation_type: str
    station_hint: str | None = None
    department_hint: str | None = None
    is_required: bool = True
    is_conditional: bool = False
    condition_reason: str | None = None
    source_data: list[str] = Field(default_factory=list)
    inputs_preview: list[IntakeV3CandidateTaskInput] = Field(default_factory=list)
    output_preview: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    will_create_real_task: bool = False
    seed_code: str | None = None
    parallel_with: list[str] = Field(default_factory=list)


class IntakeV3CandidateTaskGroup(BaseModel):
    group_key: str
    title: str
    description: str | None = None
    sort_order: int = 0
    candidate_task_ids: list[str] = Field(default_factory=list)
    is_required: bool = True
    is_conditional: bool = False
    condition_reason: str | None = None


class IntakeV3TaskDryRunBoundary(BaseModel):
    dry_run_scope: str = "production_task_generation_preview_only"
    would_create_execution_plan: bool = False
    would_create_execution_tasks: bool = False
    creates_execution_plan: bool = False
    creates_execution_tasks: bool = False
    creates_work_sessions: bool = False
    mutates_inventory: bool = False
    starts_production: bool = False
    modifies_order: bool = False
    modifies_quote: bool = False
    costengine_used: bool = False


class IntakeV3ProductionTaskDryRunSummary(BaseModel):
    candidate_groups_count: int = 0
    candidate_tasks_count: int = 0
    blocking_issues_count: int = 0
    warnings_count: int = 0


class IntakeV3ProductionTaskDryRunResponse(BaseModel):
    source_module: str | None = None
    source_type: str
    source_id: str
    order_id: int | None = None
    quote_id: int | None = None
    source_workspace_id: str | None = None
    is_intake_v3: bool = False
    dry_run_scope: str = "production_task_generation_preview_only"
    production_readiness_status: str | None = None
    material_breakdown_available: bool = False
    material_availability_available: bool = False
    material_availability_status: str | None = None
    material_shortage_rows_count: int = 0
    material_manual_check_rows_count: int = 0
    material_indirect_consumables_count: int = 0
    procurement_preview_available: bool = False
    procurement_preview_status: str | None = None
    procurement_purchase_recommended_count: int = 0
    procurement_owner_decision_required_count: int = 0
    procurement_advance_recommended_count: int = 0
    procurement_manual_check_count: int = 0
    geometry_snapshot_available: bool = False
    geometry_status: str = "geometry_missing"
    can_generate_real_tasks_now: bool = False
    would_create_execution_plan: bool = False
    would_create_execution_tasks: bool = False
    creates_execution_plan: bool = False
    creates_execution_tasks: bool = False
    creates_work_sessions: bool = False
    mutates_inventory: bool = False
    starts_production: bool = False
    modifies_order: bool = False
    modifies_quote: bool = False
    costengine_used: bool = False
    boundary: IntakeV3TaskDryRunBoundary = Field(default_factory=IntakeV3TaskDryRunBoundary)
    summary: IntakeV3ProductionTaskDryRunSummary = Field(
        default_factory=IntakeV3ProductionTaskDryRunSummary
    )
    candidate_task_groups: list[IntakeV3CandidateTaskGroup] = Field(default_factory=list)
    candidate_tasks: list[IntakeV3CandidateProductionTask] = Field(default_factory=list)
    dependencies: list[IntakeV3CandidateTaskDependency] = Field(default_factory=list)
    blockers: list[IntakeV3TaskGenerationBlocker] = Field(default_factory=list)
    warnings: list[IntakeV3TaskGenerationBlocker] = Field(default_factory=list)
    future_builds: list[str] = Field(default_factory=list)
    layer_role_confirmation_effective_source: str | None = None
    layer_role_confirmation_snapshot_source: str | None = None
    layer_role_confirmation_snapshot_stale: bool = False
    layer_role_confirmation_stale_reason: str | None = None
    downstream_uses_effective_source: bool = True
