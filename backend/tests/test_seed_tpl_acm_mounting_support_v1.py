"""Seed idempotency for TPL-ACM-BOXED-MOUNTING-SUPPORT_v1."""

from __future__ import annotations

import asyncio
import json

from sqlalchemy import select

from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from seeds.seed_tpl_acm_boxed_mounting_support_v1 import TEMPLATE_CODE, seed_tpl_acm_boxed_mounting_support_v1


def test_seed_tpl_acm_boxed_mounting_support_v1_idempotent(db_fixture) -> None:
    async def scenario():
        from seeds.seed_tpl_volumetric_letters_v2 import seed_tpl_volumetric_letters_v2

        await seed_tpl_volumetric_letters_v2()
        await seed_tpl_acm_boxed_mounting_support_v1()
        first = await seed_tpl_acm_boxed_mounting_support_v1()
        async with db_fixture.session_maker() as session:
            template = (
                await session.execute(
                    select(Product_templates).where(Product_templates.template_code == TEMPLATE_CODE)
                )
            ).scalar_one()
            dossier = (
                await session.execute(
                    select(ProductBlueprintDossier).where(ProductBlueprintDossier.template_id == template.id)
                )
            ).scalar_one()
            link = (
                await session.execute(
                    select(ProductTemplateModuleLink).where(
                        ProductTemplateModuleLink.module_template_code == TEMPLATE_CODE
                    )
                )
            ).scalar_one_or_none()
            components = json.loads(template.components_json or "[]")
            task_rules = json.loads(dossier.task_rules_json or "{}")
        return first, template, dossier, link, components, task_rules

    first, template, dossier, link, components, task_rules = asyncio.get_event_loop().run_until_complete(
        scenario()
    )
    assert first["template_action"] in {"created", "updated"}
    assert template.active is True
    assert len(components) == 3
    assert len(task_rules.get("tasks") or []) == 4
    assert link is not None
    assert link.relation_type == "optional_addon"
    assert link.pricing_mode == "separate_quote_line"
