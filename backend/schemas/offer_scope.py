"""Component offer scope contract — sold vs calc-only dependencies."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

OFFER_SCOPE_CONTRACT_VERSION = "offer_scope_contract/v1"

CanonicalSoldModule = Literal[
    "FACE",
    "RETURN-CANT",
    "BACK",
    "LIGHTING",
    "ELECTRICAL",
    "FINISH",
    "MOUNTING",
]

CanonicalCalcModule = Literal[
    "GEOMETRY",
    "PERIMETER",
    "FACE_AREA",
    "LED_COUNT",
]

OfferScopeMode = Literal["full_product", "component_subset"]


class OfferScope(BaseModel):
    contract_version: Literal["offer_scope_contract/v1"] = OFFER_SCOPE_CONTRACT_VERSION
    mode: OfferScopeMode = "full_product"
    sold_modules: list[CanonicalSoldModule] = Field(default_factory=list)


class OfferScopeInput(BaseModel):
    """Lenient parse for resolver — unknown sold codes validated in resolver."""

    contract_version: str = OFFER_SCOPE_CONTRACT_VERSION
    mode: OfferScopeMode = "full_product"
    sold_modules: list[str] = Field(default_factory=list)


class OfferScopeResolveResult(BaseModel):
    use_legacy: bool
    mode: OfferScopeMode = "full_product"
    canonical_sold_modules: list[str] = Field(default_factory=list)
    runtime_sold_modules: set[str] = Field(default_factory=set)
    calc_modules: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
