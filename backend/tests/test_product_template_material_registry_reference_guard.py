from __future__ import annotations

import json

import pytest

from models.inventory_materials import Inventory_materials
from models.product_templates import Product_templates
from services.product_readiness_service import ProductReadinessService


@pytest.mark.asyncio
async def test_active_template_blocks_when_required_material_missing_from_registry(db_session):
    template = Product_templates(
        template_code="TPL-REG-GUARD-001",
        family_id="signage",
        family_name="Signage",
        components_json=json.dumps([]),
        operations_json=json.dumps([]),
        required_materials_json=json.dumps([
            {"materialCode": "MAT-MISSING-REG", "quantity": 1, "unit": "pcs"}
        ]),
        active=True,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    readiness = await ProductReadinessService(db_session).evaluate_template_readiness(template.id)
    blockers = readiness["technical_readiness"]["blockers"]
    assert any(str(b).startswith("material_registry_missing:MAT-MISSING-REG") for b in blockers)


@pytest.mark.asyncio
async def test_active_template_blocks_when_material_is_unpriced_or_incomplete(db_session):
    db_session.add(
        Inventory_materials(
            code="MAT-INCOMPLETE",
            name="Incomplete",
            unit="pcs",
            category="test",
            unit_cost=None,
            status="active",
        )
    )
    template = Product_templates(
        template_code="TPL-REG-GUARD-002",
        family_id="signage",
        family_name="Signage",
        components_json=json.dumps([
            {
                "component_id": "comp-1",
                "materials": [{"material_code": "MAT-INCOMPLETE", "quantity": 1}],
            }
        ]),
        operations_json=json.dumps([]),
        required_materials_json=json.dumps([]),
        active=True,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    readiness = await ProductReadinessService(db_session).evaluate_template_readiness(template.id)
    blockers = readiness["technical_readiness"]["blockers"]
    assert any(str(b).startswith("active_material_price_incomplete:MAT-INCOMPLETE") for b in blockers)
