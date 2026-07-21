"""Read-only separate calculation preview for TPL-VOLUM-ALUMINIU_v1."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class VolumAluminiuSeparateCalcPreviewRequest(BaseModel):
    """Payload-driven preview. No workspace persist. No quote/order write."""

    payload: dict[str, Any] = Field(default_factory=dict)
    currency: str = Field(default="RON", min_length=3, max_length=3)
    include_commercial_line: bool = True
    include_internal_cost_line: bool = True


class VolumAluminiuSeparateCalcPreviewResponse(BaseModel):
    schema_id: str = "volum_aluminiu_separate_calc_preview_v1"
    template_code: str
    mini_module_code: str
    persist: bool = False
    activation_required: bool = False
    publication_blocked: bool = True
    separate_calculation: str
    readiness: dict[str, Any] = Field(default_factory=dict)
    quantity: dict[str, Any] = Field(default_factory=dict)
    derived_quantities: dict[str, Any] = Field(default_factory=dict)
    instances: dict[str, Any] = Field(default_factory=dict)
    materials_ops_ownership: dict[str, Any] = Field(default_factory=dict)
    commercial: Optional[dict[str, Any]] = None
    internal_cost: Optional[dict[str, Any]] = None
    unit_trace: list[dict[str, Any]] = Field(default_factory=list)
    remaining_parent_deps: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    input_contract: dict[str, Any] = Field(default_factory=dict)
