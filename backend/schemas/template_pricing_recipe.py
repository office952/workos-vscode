"""Read-only Template Pricing Studio recipe schema (TEMPLATE_PRICING_STUDIO_V1)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

TEMPLATE_PRICING_RECIPE_VERSION = "1.0.0"

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


class TemplatePricingReadiness(BaseModel):
    technical_ready: bool = False
    commercial_ready: bool = False
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
    summary: TemplatePricingSummary
    recipe: list[TemplatePricingRecipeItem] = Field(default_factory=list)
    cpp_preview: TemplatePricingCppPreview
    eic_preview: TemplatePricingEicPreview
    readiness: TemplatePricingReadiness
    acm_acceptance: TemplatePricingAcmAcceptance
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
