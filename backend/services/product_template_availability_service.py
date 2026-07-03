from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_families import Product_families
from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from schemas.product_template_availability import (
    ProductTemplateAvailabilityItem,
    ProductTemplateAvailabilityResponse,
)
from services.active_template_scope import (
    is_owner_valid_active_template,
    normalize_template_code,
)
from services.template_architecture_scope import (
    OWNER_VALID_QUOTE_RUNTIME_TEMPLATE_CODES,
    template_matches_runtime_scope,
)


class ProductTemplateAvailabilityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_availability(
        self,
        *,
        offerable_only: bool = False,
        include_runtime_modules: bool = True,
        include_archived: bool = True,
    ) -> ProductTemplateAvailabilityResponse:
        templates = (
            (await self.db.execute(select(Product_templates).order_by(Product_templates.template_code.asc())))
            .scalars()
            .all()
        )
        links = (
            (await self.db.execute(select(ProductTemplateModuleLink))).scalars().all()
        )
        families = (
            (await self.db.execute(select(Product_families))).scalars().all()
        )

        family_by_id = {str(row.family_id): row for row in families if row.family_id}
        template_codes = {str(row.template_code) for row in templates if row.template_code}
        active_links = [link for link in links if link.active is not False]

        modules_by_parent: dict[str, list[str]] = defaultdict(list)
        parents_by_module: dict[str, list[str]] = defaultdict(list)
        missing_targets_by_parent: dict[str, list[str]] = defaultdict(list)
        missing_parents_by_module: dict[str, list[str]] = defaultdict(list)

        for link in active_links:
            parent_code = str(link.parent_template_code or "").strip()
            module_code = str(link.module_template_code or "").strip()
            if not parent_code or not module_code:
                continue
            modules_by_parent[parent_code].append(module_code)
            parents_by_module[module_code].append(parent_code)
            if module_code not in template_codes:
                missing_targets_by_parent[parent_code].append(module_code)
            if parent_code not in template_codes:
                missing_parents_by_module[module_code].append(parent_code)

        items = [
            self._build_item(
                template=row,
                family=family_by_id.get(str(row.family_id or "")),
                module_codes=sorted(set(modules_by_parent.get(str(row.template_code), []))),
                parent_codes=sorted(set(parents_by_module.get(str(row.template_code), []))),
                missing_module_codes=sorted(set(missing_targets_by_parent.get(str(row.template_code), []))),
                missing_parent_codes=sorted(set(missing_parents_by_module.get(str(row.template_code), []))),
            )
            for row in templates
        ]

        if offerable_only:
            items = [item for item in items if item.quote_offerable]
        if not include_runtime_modules:
            items = [item for item in items if not item.runtime_module]
        if not include_archived:
            items = [
                item
                for item in items
                if item.quote_offerable or item.runtime_module or item.status == "offerable"
            ]

        return ProductTemplateAvailabilityResponse(
            items=items,
            total=len(items),
            offerable_count=sum(1 for item in items if item.quote_offerable),
            runtime_module_count=sum(1 for item in items if item.runtime_module),
        )

    def _build_item(
        self,
        *,
        template: Product_templates,
        family: Product_families | None,
        module_codes: list[str],
        parent_codes: list[str],
        missing_module_codes: list[str],
        missing_parent_codes: list[str],
    ) -> ProductTemplateAvailabilityItem:
        template_code = str(template.template_code or "").strip()
        db_active = template.active is not False
        runtime_module = bool(parent_codes)
        is_parent = bool(module_codes)
        has_modules = bool(module_codes)
        owner_valid = is_owner_valid_active_template(template_code)
        runtime_valid = template_matches_runtime_scope(
            template_code,
            OWNER_VALID_QUOTE_RUNTIME_TEMPLATE_CODES,
        )

        status = "not_offerable"
        status_reason = "no_offer_contract"
        quote_offerable = False

        if not db_active:
            status = "archived"
            status_reason = "db_inactive"
        elif missing_parent_codes or missing_module_codes:
            status = "not_offerable"
            status_reason = "missing_required_modules"
        elif runtime_module:
            status = "runtime_module"
            status_reason = "runtime_module_only"
        elif not owner_valid:
            status = "experimental" if runtime_valid else "not_offerable"
            status_reason = "not_owner_valid"
        elif not has_modules:
            status = "not_offerable"
            status_reason = "missing_required_modules"
        elif is_parent:
            status = "offerable"
            status_reason = "owner_valid_parent_template"
            quote_offerable = True

        return ProductTemplateAvailabilityItem(
            template_id=int(template.id),
            template_code=template_code,
            family_id=str(template.family_id) if template.family_id else None,
            family_name=(str(template.family_name) if template.family_name else None)
            or (str(family.label) if family else None),
            description=str(template.description) if template.description else None,
            db_active=db_active,
            quote_offerable=quote_offerable,
            runtime_module=runtime_module,
            is_parent=is_parent,
            has_modules=has_modules,
            parent_codes=parent_codes,
            module_codes=module_codes,
            status=status,
            status_reason=status_reason,
        )
