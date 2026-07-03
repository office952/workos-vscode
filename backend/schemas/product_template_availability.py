from __future__ import annotations

from pydantic import BaseModel, Field


class ProductTemplateAvailabilityItem(BaseModel):
    template_id: int
    template_code: str
    family_id: str | None = None
    family_name: str | None = None
    description: str | None = None
    db_active: bool
    quote_offerable: bool
    runtime_module: bool
    is_parent: bool
    has_modules: bool
    parent_codes: list[str] = Field(default_factory=list)
    module_codes: list[str] = Field(default_factory=list)
    status: str
    status_reason: str


class ProductTemplateAvailabilityResponse(BaseModel):
    items: list[ProductTemplateAvailabilityItem] = Field(default_factory=list)
    total: int = 0
    offerable_count: int = 0
    runtime_module_count: int = 0
