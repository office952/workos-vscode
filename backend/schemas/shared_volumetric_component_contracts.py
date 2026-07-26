from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SharedVolumetricComponentProfile(BaseModel):
    profile_key: str
    profile_label: str
    template_code: str
    module_template_code: str
    role_label: str
    behavior_notes: list[str] = Field(default_factory=list)
    template_config: dict[str, Any] = Field(default_factory=dict)
    not_confirmed: list[str] = Field(default_factory=list)


class SharedVolumetricTemplateBinding(BaseModel):
    template_code: str
    profile_key: str
    module_template_code: str
    module_code: str | None = None
    role_label: str
    template_config: dict[str, Any] = Field(default_factory=dict)


class SharedVolumetricComponentContract(BaseModel):
    component_key: str
    display_name: str
    purpose: str
    shared_truth_fields: list[str] = Field(default_factory=list)
    profiles: list[SharedVolumetricComponentProfile] = Field(default_factory=list)
    template_bindings: list[SharedVolumetricTemplateBinding] = Field(default_factory=list)
    confidence: str
    owner_decision: str
    forbidden_runtime_behavior: list[str] = Field(default_factory=list)


class SharedVolumetricComponentSummary(BaseModel):
    component_key: str
    display_name: str
    profile_key: str
    module_template_code: str
    confidence: str
    owner_decision: str
    shared_truth_fields: list[str] = Field(default_factory=list)
    not_confirmed: list[str] = Field(default_factory=list)
    calculation_strategy_key: str | None = None
    strategy_source_template_code: str | None = None
    strategy_status: str | None = None
    strategy_meaning: str | None = None
    required_truth: list[str] = Field(default_factory=list)
    shared_module_template_code: str | None = None
    legacy_replaced_by: str | None = None
    reserved_module_template_code: str | None = None
