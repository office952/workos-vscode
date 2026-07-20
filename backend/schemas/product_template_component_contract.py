"""Component contracts without a component_templates table.

A component contract is a child / dual-role Product Template plus composition-edge
usage_mode + instance_schema_id, with a derived used-by map.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ComponentContractUsedByEdge(BaseModel):
    parent_template_code: str
    parent_template_id: Optional[int] = None
    link_id: Optional[int] = None
    relation_type: Optional[str] = None
    usage_mode: Optional[str] = None
    instance_schema_id: Optional[str] = None
    pricing_mode: Optional[str] = None
    execution_mode: Optional[str] = None
    active: bool = True


class ComponentContractChildEdge(BaseModel):
    module_template_code: str
    module_template_id: Optional[int] = None
    link_id: Optional[int] = None
    relation_type: Optional[str] = None
    usage_mode: Optional[str] = None
    instance_schema_id: Optional[str] = None
    pricing_mode: Optional[str] = None
    execution_mode: Optional[str] = None
    active: bool = True
    policy_component_only: bool = False
    policy_root_offerable: bool = False
    policy_reason: Optional[str] = None


class ProductTemplateComponentContractView(BaseModel):
    template_code: str
    template_id: int
    db_active: bool
    publication_status: Optional[str] = None
    role: str
    usage_mode_policy: dict[str, Any] = Field(default_factory=dict)
    used_by: list[ComponentContractUsedByEdge] = Field(default_factory=list)
    children: list[ComponentContractChildEdge] = Field(default_factory=list)
    instance_schema_hints: list[str] = Field(default_factory=list)
    no_component_templates_table: bool = True
    contract_version: str = "product_template_component_contract_v1"


class ComponentContractLinkPatchRequest(BaseModel):
    usage_mode: Optional[str] = None
    instance_schema_id: Optional[str] = None
