"""Canonical active-scope compile result — Letters Slice 1.

Defines scope only. Does not calculate money or generate execution tasks.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.offer_scope import OfferScopeMode

ACTIVE_SCOPE_CONTRACT_VERSION = "active_scope_contract/v1"
ACTIVE_SCOPE_RESOLVER_VERSION = "letters_slice1_active_scope/v1"

DependencyClass = Literal[
    "hard_technical",
    "conditional",
    "composition_only",
    "commercial",
    "execution",
]


class ActiveScopeDependency(BaseModel):
    code: str
    dependency_class: DependencyClass
    reason: str
    required_by: list[str] = Field(default_factory=list)


class ActiveScopeResult(BaseModel):
    """Compiled active scope for Letters Slice 1 consumers."""

    contract_version: str = ACTIVE_SCOPE_CONTRACT_VERSION
    resolver_version: str = ACTIVE_SCOPE_RESOLVER_VERSION
    template_code: str
    mode: OfferScopeMode = "full_product"
    use_legacy_full_product: bool = True
    sold_module_codes: list[str] = Field(default_factory=list)
    active_runtime_modules: list[str] = Field(default_factory=list)
    inactive_runtime_modules: list[str] = Field(default_factory=list)
    calculation_prerequisites: list[str] = Field(default_factory=list)
    commercial_scope_modules: list[str] = Field(default_factory=list)
    execution_scope_modules: list[str] = Field(default_factory=list)
    composition_excluded_operations: list[str] = Field(default_factory=list)
    dependencies: list[ActiveScopeDependency] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)

    def active_set(self) -> set[str]:
        return set(self.active_runtime_modules)

    def commercial_set(self) -> set[str]:
        return set(self.commercial_scope_modules)

    def execution_set(self) -> set[str]:
        return set(self.execution_scope_modules)
