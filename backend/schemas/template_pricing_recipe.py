"""Read-only Template Pricing Studio recipe schema (TEMPLATE_PRICING_STUDIO_V1)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

TEMPLATE_PRICING_RECIPE_VERSION = "1.2.0"

LaborClass = Literal[
    "LABOR_INTERNAL",
    "LABOR_COMMERCIAL",
    "MACHINE_OPERATION",
    "INTERNAL_SERVICE",
    "EXTERNAL_SERVICE",
    "INSTALLATION_SERVICE",
    "UNKNOWN_AMBIGUOUS",
    "LEGACY",
    "MISSING_RATE",
]

LaborRecipeRole = Literal[
    "assembly",
    "wiring",
    "finishing",
    "mounting",
    "packaging",
    "other",
]

LaborBasis = Literal[
    "hour",
    "minute",
    "buc",
    "ml",
    "mp",
    "set",
    "produs",
    "unknown",
]

LaborFormulaStatus = Literal[
    "FORMULA_CONFIRMED",
    "QUANTITY_KEY_CONFIRMED",
    "OPERATION_ONLY",
    "MISSING_OWNER_FORMULA",
    "LEGACY_METADATA",
    "NOT_APPLICABLE",
]

RecipeKind = Literal[
    "material",
    "machine_operation",
    "labor",
    "service",
    "commercial_line",
    "minimum",
    "adjustment",
    "unknown",
]

RecipeItemStatus = Literal[
    "active",
    "missing",
    "blocked",
    "warning",
    "inactive",
]

CostOrRateMeaning = Literal[
    "purchase_cost",
    "reusable_rate",
    "commercial_documented",
    "unknown",
]


class TemplatePricingRecipeItem(BaseModel):
    recipe_item_id: str
    recipe_kind: RecipeKind
    operator_name: str
    stable_code: str
    catalog_code: Optional[str] = None
    quantity_keys: list[str] = Field(default_factory=list)
    formula_owner: Optional[str] = None
    applicability: dict[str, Any] = Field(default_factory=dict)
    rate_source: Optional[str] = None
    cost_or_rate: CostOrRateMeaning = "unknown"
    cost_label_ro: Optional[str] = None
    unit: Optional[str] = None
    current_value: Optional[float] = None
    currency: Optional[str] = None
    status: RecipeItemStatus = "active"
    provenance: Optional[str] = None
    cpp_line_code: Optional[str] = None
    cpp_pricing_rule_code: Optional[str] = None
    eic_rule_code: Optional[str] = None
    typed_catalog: Optional[str] = None
    machine_family: Optional[str] = None
    data_quality_flags: list[str] = Field(default_factory=list)
    data_quality_message_ro: Optional[str] = None
    technical_ready: bool = False
    commercial_ready: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    editable: bool = False
    editability_reason_ro: str = "V1 este read-only — Studio compune, nu creează tarife."
    source_links: dict[str, str] = Field(default_factory=dict)
    legacy: bool = False
    confidence: Literal["high", "medium", "low"] = "medium"


class TemplatePricingSummary(BaseModel):
    total_items: int = 0
    materials: int = 0
    machine_operations: int = 0
    labor: int = 0
    services: int = 0
    commercial_lines: int = 0
    resolved: int = 0
    missing: int = 0
    blocked: int = 0
    warnings: int = 0
    registry_confirmed: int = 0
    registry_missing_price: int = 0


class TemplatePricingCppPreview(BaseModel):
    available: bool = False
    status: str = "not_requested"
    note_ro: str = (
        "Preview structural: liniile comerciale sunt listate din catalogul de reguli. "
        "Calculul cantitativ CPP necesită payload / workspace și nu este modificat aici."
    )
    line_codes: list[str] = Field(default_factory=list)
    blocked_line_codes: list[str] = Field(default_factory=list)
    subtotal: Optional[float] = None
    currency: Optional[str] = None


class TemplatePricingEicPreview(BaseModel):
    available: bool = False
    status: str = "not_requested"
    note_ro: str = (
        "Proveniență EIC: regulile interne sunt expuse ca referință. "
        "Nu se recalculează CostEngine / EIC în acest endpoint."
    )
    provenance_notes: list[str] = Field(default_factory=list)
    rule_codes: list[str] = Field(default_factory=list)


ActivationStatus = Literal[
    "ACTIVE_WITH_CONFIRMED_TRUTH",
    "ACTIVE_WITH_AI_DEFAULTS",
    "ACTIVE_WITH_WARNINGS",
    "BLOCKED",
]


class TemplatePricingReadiness(BaseModel):
    technical_ready: bool = False
    commercial_ready: bool = False
    activation_status: ActivationStatus = "BLOCKED"
    ai_defaults_active: bool = False
    demoted_blockers: list[str] = Field(default_factory=list)
    real_blockers_retained: list[str] = Field(default_factory=list)
    technical_notes_ro: list[str] = Field(default_factory=list)
    commercial_notes_ro: list[str] = Field(default_factory=list)
    inventory_notes_ro: list[str] = Field(default_factory=list)


class TemplatePricingAcmAcceptance(BaseModel):
    applies: bool = False
    shell_registry_confirmed: Optional[int] = None
    shell_registry_missing: Optional[int] = None
    treatment_commercial_lines_allowed: Optional[bool] = None
    blockers: list[str] = Field(default_factory=list)
    policy_ro: Optional[str] = None


class TemplateLaborRecipeItem(BaseModel):
    """Central rate + template-specific labor recipe (LABOR_RECIPE_CONTRACT_V1)."""

    labor_recipe_id: str
    template_code: str
    operation_code: str
    catalog_code: str
    workcenter_declared: Optional[str] = None
    operator_name: str
    labor_class: LaborClass = "UNKNOWN_AMBIGUOUS"
    recipe_role: LaborRecipeRole = "other"
    quantity_keys: list[str] = Field(default_factory=list)
    formula_id: Optional[str] = None
    formula_owner: Optional[str] = None
    formula_status: LaborFormulaStatus = "OPERATION_ONLY"
    formula_status_label_ro: Optional[str] = None
    formula_source: Optional[str] = None
    quantity_source: Optional[str] = None
    owner_confirmation_required: bool = False
    unresolved_reason: Optional[str] = None
    evidence_level: Optional[str] = None
    basis: LaborBasis = "unknown"
    rate_basis: Optional[str] = None
    standard_time: Optional[Any] = None
    multiplier: Optional[Any] = None
    minimum: Optional[Any] = None
    dependencies: dict[str, Any] = Field(default_factory=dict)
    base_rate_source: Optional[str] = None
    internal_cost_rate: Optional[float] = None
    commercial_rate: Optional[float] = None
    commercial_rate_status: Literal["available", "unavailable", "missing"] = "unavailable"
    unit: Optional[str] = None
    currency: Optional[str] = None
    status: RecipeItemStatus = "active"
    typed_catalog: Optional[str] = None
    data_quality_flags: list[str] = Field(default_factory=list)
    data_quality_message_ro: Optional[str] = None
    cpp_line_code: Optional[str] = None
    eic_rule_code: Optional[str] = None
    technical_ready: bool = False
    commercial_ready: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    editable: bool = False
    editability_reason_ro: str = (
        "V1 este read-only — tarif central în catalog; rețeta pe template."
    )
    source_links: dict[str, str] = Field(default_factory=dict)
    provenance: Optional[str] = None
    legacy: bool = False
    confidence: Literal["high", "medium", "low"] = "medium"
    decision_source: Optional[str] = None
    ai_decision_id: Optional[str] = None
    ai_default_value: Optional[float] = None
    ai_confidence: Optional[str] = None
    is_configurable: bool = False
    resolved_from: Optional[str] = None
    rationale_ro: Optional[str] = None
    review_trigger: Optional[str] = None


class TemplateLaborRecipeSummary(BaseModel):
    total: int = 0
    technical_ready: int = 0
    commercial_ready: int = 0
    missing_rate: int = 0
    warnings: int = 0
    ai_defaults_applied: int = 0


class AiOperationalDecisionItem(BaseModel):
    decision_id: str
    domain: str
    target_type: str
    target_code: str
    display_name_ro: str
    formula: str
    unit: str
    default_value: float
    resolved_value: float
    minimum: float
    maximum: Optional[float] = None
    currency: str = "EUR"
    quantity_key: Optional[str] = None
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    rationale_ro: str
    decision_source: str = "AI_DECISION"
    resolved_from: str = "AI_DECISION"
    configurable: bool = True
    has_override: bool = False
    review_trigger: Optional[str] = None
    status: str = "active"
    readiness_effect: str = "ACTIVE_WITH_AI_DEFAULTS"
    affected_templates: list[str] = Field(default_factory=list)
    template_code: Optional[str] = None
    precedence_order: list[str] = Field(default_factory=list)
    calibration_hooks: list[str] = Field(default_factory=list)
    demotes_blockers: list[str] = Field(default_factory=list)
    owner_confirmation_required: bool = False
    superseded_by: Optional[str] = None
    packaging_band: Optional[str] = None
    fragile_addon: Optional[float] = None
    psu_count: Optional[int] = None
    per_psu_rate: Optional[float] = None
    also_applies_to_operations: list[str] = Field(default_factory=list)


class TemplatePricingRecipeResponse(BaseModel):
    schema_version: str = TEMPLATE_PRICING_RECIPE_VERSION
    template_code: str
    template_name: Optional[str] = None
    template_version: Optional[str] = None
    lifecycle: Optional[str] = None
    usage_mode: Optional[str] = None
    editability_policy: str = "read_only_v1"
    ownership_note_ro: str = (
        "Cataloagele dețin tarifele reutilizabile. Template-ul deține rețeta. "
        "CPP calculează. EIC explică. Studio-ul doar compune și face lanțul vizibil."
    )
    labor_ownership_note_ro: str = (
        "Tariful central de manoperă e în catalog. "
        "Rețeta (formulă, cantitate, minim, aplicabilitate) e pe template. "
        "Tariful lipsă blochează doar pregătirea comercială, nu configurația tehnică."
    )
    ai_ownership_note_ro: str = (
        "Deciziile AI sunt default-uri operaționale configurabile. "
        "Precedență: măsurat > owner confirmat > catalog > AI > legacy. "
        "Timpul nu este baza primară de cost — se observă pentru calibrare."
    )
    summary: TemplatePricingSummary
    recipe: list[TemplatePricingRecipeItem] = Field(default_factory=list)
    labor_recipes: list[TemplateLaborRecipeItem] = Field(default_factory=list)
    labor_summary: TemplateLaborRecipeSummary = Field(
        default_factory=TemplateLaborRecipeSummary
    )
    ai_decisions: list[AiOperationalDecisionItem] = Field(default_factory=list)
    cpp_preview: TemplatePricingCppPreview
    eic_preview: TemplatePricingEicPreview
    readiness: TemplatePricingReadiness
    acm_acceptance: TemplatePricingAcmAcceptance
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
