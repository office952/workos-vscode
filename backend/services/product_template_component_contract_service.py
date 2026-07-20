"""Component contract read/patch — child PT + links; no CT table."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from schemas.product_template_component_contract import (
    ComponentContractChildEdge,
    ComponentContractLinkPatchRequest,
    ComponentContractUsedByEdge,
    ProductTemplateComponentContractView,
)
from services.product_template_publication_service import normalize_publication_status
from services.template_usage_mode_policy import get_template_usage_mode_policy

_INSTANCE_SCHEMA_HINTS: dict[str, list[str]] = {
    "TPL-VOLUMETRIC-LETTERS_v2": [
        "letter_group_instances",
        "component_placements",
        "acm_panel_instance",
    ],
    "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1": ["acm_panel_component_instance_v1"],
    "TPL-VOLUM-ALUMINIU_v1": ["letter_group_instances.sidewall"],
    "TPL-METAL-PREMOUNT-STRUCTURE_v1": ["component_placements.mounting"],
}


class ProductTemplateComponentContractService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _load_template(self, template_code: str) -> Product_templates:
        code = (template_code or "").strip()
        if not code:
            raise HTTPException(status_code=400, detail={"error": "template_code_required"})
        row = (
            await self.db.execute(
                select(Product_templates).where(Product_templates.template_code == code).limit(1)
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "template_not_found", "template_code": code},
            )
        return row

    async def get_contract(self, template_code: str) -> ProductTemplateComponentContractView:
        row = await self._load_template(template_code)
        code = str(row.template_code)
        links = (await self.db.execute(select(ProductTemplateModuleLink))).scalars().all()

        used_by: list[ComponentContractUsedByEdge] = []
        children: list[ComponentContractChildEdge] = []
        for link in links:
            parent = str(link.parent_template_code or "").strip()
            module = str(link.module_template_code or "").strip()
            if module == code:
                used_by.append(
                    ComponentContractUsedByEdge(
                        parent_template_code=parent,
                        parent_template_id=int(link.parent_template_id)
                        if link.parent_template_id is not None
                        else None,
                        link_id=int(link.id) if link.id is not None else None,
                        relation_type=str(link.relation_type) if link.relation_type else None,
                        usage_mode=getattr(link, "usage_mode", None),
                        instance_schema_id=getattr(link, "instance_schema_id", None),
                        pricing_mode=str(link.pricing_mode) if link.pricing_mode else None,
                        execution_mode=str(link.execution_mode) if link.execution_mode else None,
                        active=link.active is not False,
                    )
                )
            if parent == code:
                child_policy = get_template_usage_mode_policy(module)
                children.append(
                    ComponentContractChildEdge(
                        module_template_code=module,
                        module_template_id=int(link.module_template_id)
                        if link.module_template_id is not None
                        else None,
                        link_id=int(link.id) if link.id is not None else None,
                        relation_type=str(link.relation_type) if link.relation_type else None,
                        usage_mode=getattr(link, "usage_mode", None),
                        instance_schema_id=getattr(link, "instance_schema_id", None),
                        pricing_mode=str(link.pricing_mode) if link.pricing_mode else None,
                        execution_mode=str(link.execution_mode) if link.execution_mode else None,
                        active=link.active is not False,
                        policy_component_only=bool(child_policy.component_only) if child_policy else False,
                        policy_root_offerable=bool(child_policy.root_offerable) if child_policy else False,
                        policy_reason=child_policy.reason if child_policy else None,
                    )
                )

        policy = get_template_usage_mode_policy(code)
        if used_by and not (policy and policy.root_offerable):
            role = "child_component"
        elif used_by and policy and policy.root_offerable:
            role = "dual_role"
        elif policy and policy.component_only:
            role = "component_only"
        elif policy and policy.root_offerable:
            role = "root_product"
        else:
            role = "template"

        return ProductTemplateComponentContractView(
            template_code=code,
            template_id=int(row.id),
            db_active=row.active is not False,
            publication_status=normalize_publication_status(
                getattr(row, "publication_status", None)
            ),
            role=role,
            usage_mode_policy=(
                {
                    "root_offerable": policy.root_offerable,
                    "linked_child_allowed": policy.linked_child_allowed,
                    "candidate_only": policy.candidate_only,
                    "component_only": policy.component_only,
                    "owner_go_required": policy.owner_go_required,
                    "reason": policy.reason,
                }
                if policy
                else {}
            ),
            used_by=sorted(used_by, key=lambda e: e.parent_template_code),
            children=sorted(children, key=lambda e: e.module_template_code),
            instance_schema_hints=_INSTANCE_SCHEMA_HINTS.get(code, []),
            no_component_templates_table=True,
        )

    async def patch_link(
        self,
        link_id: int,
        body: ComponentContractLinkPatchRequest,
    ) -> ComponentContractChildEdge:
        link = (
            await self.db.execute(
                select(ProductTemplateModuleLink).where(ProductTemplateModuleLink.id == link_id).limit(1)
            )
        ).scalar_one_or_none()
        if link is None:
            raise HTTPException(status_code=404, detail={"error": "link_not_found", "link_id": link_id})

        if body.usage_mode is not None:
            link.usage_mode = body.usage_mode.strip() or None
        if body.instance_schema_id is not None:
            link.instance_schema_id = body.instance_schema_id.strip() or None

        await self.db.commit()
        await self.db.refresh(link)

        module = str(link.module_template_code or "")
        child_policy = get_template_usage_mode_policy(module)
        return ComponentContractChildEdge(
            module_template_code=module,
            module_template_id=int(link.module_template_id) if link.module_template_id is not None else None,
            link_id=int(link.id),
            relation_type=str(link.relation_type) if link.relation_type else None,
            usage_mode=getattr(link, "usage_mode", None),
            instance_schema_id=getattr(link, "instance_schema_id", None),
            pricing_mode=str(link.pricing_mode) if link.pricing_mode else None,
            execution_mode=str(link.execution_mode) if link.execution_mode else None,
            active=link.active is not False,
            policy_component_only=bool(child_policy.component_only) if child_policy else False,
            policy_root_offerable=bool(child_policy.root_offerable) if child_policy else False,
            policy_reason=child_policy.reason if child_policy else None,
        )
