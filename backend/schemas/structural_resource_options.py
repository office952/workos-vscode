"""Pydantic schemas for Shared Technical Resource Options (read-only)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StructuralMaterialOption(BaseModel):
    code: str
    label: str
    family: str
    base_material: str
    status: str
    version: int = 1
    aliases: list[str] = Field(default_factory=list)
    compatible_profile_shapes: list[str] = Field(default_factory=list)
    allowed_finishes: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class StructuralProfileOption(BaseModel):
    code: str
    label: str
    shape: str
    width_mm: float
    height_mm: float
    wall_thickness_mm: float
    compatible_material_codes: list[str] = Field(default_factory=list)
    status: str
    version: int = 1
    aliases: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class ComponentAcceptedOptions(BaseModel):
    component_template_code: str
    capability: str
    accepted_material_codes: list[str] = Field(default_factory=list)
    accepted_profile_shapes: list[str] = Field(default_factory=list)
    accepted_profile_codes: list[str] = Field(default_factory=list)
    dimension_rule: str | None = None
    crossbar_rule: str | None = None
    total_fit_allowance_mm: float | None = None
    crossbar_spacing_by_material: dict[str, float] = Field(default_factory=dict)
    profile_gate: str | None = None


class StructuralResourceOptionsResponse(BaseModel):
    registry_version: str
    materials: list[StructuralMaterialOption] = Field(default_factory=list)
    profiles: list[StructuralProfileOption] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
