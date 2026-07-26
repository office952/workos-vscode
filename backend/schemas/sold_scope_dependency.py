"""Sold-scope dependency validation result contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DependencySeverity = Literal["blocker", "confirmation_required", "warning"]


class SoldScopeDependencyIssue(BaseModel):
    severity: DependencySeverity
    code: str
    message: str
    capability: str | None = None


class SoldScopeDependencyValidationResult(BaseModel):
    valid: bool = True
    valid_for_save: bool = True
    valid_for_confirmation: bool = True
    blockers: list[SoldScopeDependencyIssue] = Field(default_factory=list)
    confirmations_required: list[SoldScopeDependencyIssue] = Field(default_factory=list)
    warnings: list[SoldScopeDependencyIssue] = Field(default_factory=list)
    satisfied_capabilities: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)
    resolved_calc_modules: list[str] = Field(default_factory=list)
