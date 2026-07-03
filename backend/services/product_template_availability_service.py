from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_families import Product_families
from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from schemas.product_template_availability import (
    ProductTemplateAvailabilityItem,
    ProductTemplateCompositionModule,
    ProductTemplateAvailabilityResponse,
)
from data.shared_volumetric_component_contracts import get_shared_volumetric_component_summaries_for_template
from services.active_template_scope import (
    is_owner_valid_active_template,
    normalize_template_code,
)
from services.template_architecture_scope import (
    OWNER_VALID_QUOTE_RUNTIME_TEMPLATE_CODES,
    template_matches_runtime_scope,
)


# Catalog metadata for the current Product System composition view.
# Kept backend-side so the UI renders role labels instead of deriving them
# from template_code naming conventions. This can move to dossier/DB metadata
# once those fields become canonical.
ROLE_METADATA_BY_MODULE_CODE: dict[str, tuple[str, str, str, int]] = {
    "TPL-VOLUMETRIC-FACE_v1": ("front_face", "Fata litera", "Fata vizuala debitata din plexiglas.", 10),
    "TPL-VOLUMETRIC-BACK_v1": ("back_panel", "Spate litera", "Spatele literei / inchidere corp.", 20),
    "TPL-VOLUM-ALUMINIU_v1": ("sidewall_return", "Cant / laterale", "Volum/cant lateral din aluminiu.", 30),
    "TPL-VOLUMETRIC-LED_v1": ("lighting", "LED / iluminare", "Sistem de iluminare al produsului.", 40),
    "TPL-VOLUMETRIC-FINISH_v1": ("finishes", "Finisaje", "Folie, print, laminare sau finisaje vizuale.", 50),
    "TPL-METAL-PREMOUNT-STRUCTURE_v1": ("mounting_structure", "Structura montaj", "Structura suport/montaj, optionala dupa caz.", 60),
    "TPL-VOLUMETRIC-LOGO-FACE_v1": ("logo_front_face", "Fata logo", "Fata vizuala pentru logo volumetric.", 10),
    "TPL-VOLUMETRIC-LOGO-RETURN_v1": ("logo_return", "Return / cant logo", "Cant/return lateral pentru logo.", 20),
    "TPL-VOLUMETRIC-LOGO-BACK_v1": ("logo_back", "Spate logo", "Spate/inchidere logo.", 30),
    "TPL-VOLUMETRIC-LOGO-LIGHTING_v1": ("logo_lighting", "Iluminare logo", "Sistem iluminare/electrica pentru logo.", 40),
    "TPL-VOLUMETRIC-LOGO-FINISH_v1": ("logo_finishes", "Finisaje logo", "Finisaje vizuale pentru logo.", 50),
    "TPL-VOLUMETRIC-LOGO-MOUNTING_v1": ("logo_mounting", "Montaj logo", "Montaj/suport pentru logo.", 60),
}


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
        links_by_parent: dict[str, list[ProductTemplateModuleLink]] = defaultdict(list)
        parents_by_module: dict[str, list[str]] = defaultdict(list)
        missing_targets_by_parent: dict[str, list[str]] = defaultdict(list)
        missing_parents_by_module: dict[str, list[str]] = defaultdict(list)

        for link in active_links:
            parent_code = str(link.parent_template_code or "").strip()
            module_code = str(link.module_template_code or "").strip()
            if not parent_code or not module_code:
                continue
            modules_by_parent[parent_code].append(module_code)
            links_by_parent[parent_code].append(link)
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
                module_links=links_by_parent.get(str(row.template_code), []),
                module_parent_counts={code: len(set(parents)) for code, parents in parents_by_module.items()},
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
        module_links: list[ProductTemplateModuleLink],
        module_parent_counts: dict[str, int],
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

        role = self._resolve_product_system_role(
            db_active=db_active,
            quote_offerable=quote_offerable,
            runtime_module=runtime_module,
            is_parent=is_parent,
            has_modules=has_modules,
            parent_codes=parent_codes,
            missing_module_codes=missing_module_codes,
            missing_parent_codes=missing_parent_codes,
        )

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
            product_system_role=role["product_system_role"],
            display_group=role["display_group"],
            importance_rank=role["importance_rank"],
            owner_decision_required=role["owner_decision_required"],
            readiness_reason=role["readiness_reason"],
            ui_label=role["ui_label"],
            ui_description=role["ui_description"],
            parent_product_codes=parent_codes,
            child_module_codes=module_codes,
            shared_with_product_codes=parent_codes if len(parent_codes) > 1 else [],
            composition_modules=self._build_composition_modules(
                product_system_role=str(role["product_system_role"]),
                module_links=module_links,
                module_parent_counts=module_parent_counts,
            ),
            shared_component_contracts=get_shared_volumetric_component_summaries_for_template(template_code),
        )

    def _build_composition_modules(
        self,
        *,
        product_system_role: str,
        module_links: list[ProductTemplateModuleLink],
        module_parent_counts: dict[str, int],
    ) -> list[ProductTemplateCompositionModule]:
        if product_system_role not in {"offerable_product", "candidate_product"}:
            return []

        modules: list[ProductTemplateCompositionModule] = []
        for index, link in enumerate(module_links, start=1):
            module_code = str(link.module_template_code or "").strip()
            if not module_code:
                continue
            role_key, role_label, ui_hint, default_sort = ROLE_METADATA_BY_MODULE_CODE.get(
                module_code,
                (
                    module_code.lower().replace("-", "_").replace(".", "_"),
                    module_code,
                    None,
                    index * 10,
                ),
            )
            relation_type = str(link.relation_type or "").strip() or None
            optional_or_conditional = relation_type == "optional_addon"
            module_product_system_role = (
                "shared_component" if module_parent_counts.get(module_code, 0) > 1 else "internal_module"
            )
            modules.append(
                ProductTemplateCompositionModule(
                    role_key=role_key,
                    role_label=role_label,
                    module_template_code=module_code,
                    module_product_system_role=module_product_system_role,
                    relation_type=relation_type,
                    is_required=not optional_or_conditional,
                    sort_order=default_sort,
                    ui_hint=ui_hint,
                    status_label="Optional / conditionat" if optional_or_conditional else "Modul intern activ",
                )
            )

        return sorted(modules, key=lambda item: (item.sort_order, item.module_template_code))

    def _resolve_product_system_role(
        self,
        *,
        db_active: bool,
        quote_offerable: bool,
        runtime_module: bool,
        is_parent: bool,
        has_modules: bool,
        parent_codes: list[str],
        missing_module_codes: list[str],
        missing_parent_codes: list[str],
    ) -> dict[str, object]:
        if quote_offerable and is_parent and has_modules and db_active:
            return {
                "product_system_role": "offerable_product",
                "display_group": "active_products",
                "importance_rank": 10,
                "owner_decision_required": False,
                "readiness_reason": "Produs valid pentru ofertare in Work Intake.",
                "ui_label": "Produs activ pentru ofertare",
                "ui_description": "Poate fi ales ca produs initial in Work Intake.",
            }

        if runtime_module and parent_codes and db_active:
            if len(parent_codes) > 1:
                return {
                    "product_system_role": "shared_component",
                    "display_group": "shared_components",
                    "importance_rank": 40,
                    "owner_decision_required": False,
                    "readiness_reason": "Componenta folosita de mai multe produse parinte.",
                    "ui_label": "Componenta comuna",
                    "ui_description": "Reutilizata de mai multe produse parinte; nu se alege direct in Work Intake.",
                }
            return {
                "product_system_role": "internal_module",
                "display_group": "internal_modules",
                "importance_rank": 30,
                "owner_decision_required": False,
                "readiness_reason": f"Modul intern activ folosit de {parent_codes[0]}.",
                "ui_label": "Modul intern activ",
                "ui_description": "Folosit de produse parinte. Nu se alege direct in Work Intake.",
            }

        if db_active and is_parent and has_modules and not runtime_module and not quote_offerable:
            return {
                "product_system_role": "candidate_product",
                "display_group": "candidate_products",
                "importance_rank": 20,
                "owner_decision_required": True,
                "readiness_reason": "Produs structural existent, dar necesita GO owner pentru ofertare.",
                "ui_label": "Produs in pregatire",
                "ui_description": "Nu apare in Work Intake pana la GO owner.",
            }

        missing_contract = bool(missing_module_codes or missing_parent_codes or (is_parent and not has_modules))
        return {
            "product_system_role": "archived_experimental",
            "display_group": "archived_experimental",
            "importance_rank": 50,
            "owner_decision_required": missing_contract or db_active,
            "readiness_reason": "Scos din flow activ sau experimental." if not missing_contract else "Lipseste contract critic de module sau linkuri.",
            "ui_label": "Arhivat / experimental",
            "ui_description": "Scos din flow activ sau experimental.",
        }
