from __future__ import annotations

import json

import pytest

from models.inventory_materials import Inventory_materials
from models.product_templates import Product_templates
from services.product_readiness_service import ProductReadinessService


PRODUCT_001_REQUIRED_CODES = [
    "MAT_ACM_PANEL_3MM",
    "MAT_ACM_PANEL_4MM",
    "MAT_RECT_TUBE_PROFILE_MAIN",
    "MAT_RECT_TUBE_PROFILE_RIB",
    "MAT_FASTENERS_CSK_SELF_DRILL",
    "MAT_ADHESIVE_SEALANT",
]

PRODUCT_001_OPTIONAL_FACE_FINISH_CODES = [
    "MAT_VINYL_PRINT_LAMINATED",
    "MAT_ORACAL_641",
    "MAT_ORACAL_651",
]


@pytest.mark.asyncio
async def test_product_001_optional_face_finish_unresolved_warns_when_template_inactive(db_session):
    for code in PRODUCT_001_REQUIRED_CODES:
        db_session.add(
            Inventory_materials(
                code=code,
                name=code,
                unit="pcs",
                category="product_001",
                status="missing_price",
            )
        )

    template = Product_templates(
        template_code="PRODUCT-001-DRAFT",
        family_id="signage",
        family_name="Signage",
        components_json=json.dumps([]),
        operations_json=json.dumps([]),
        required_materials_json=json.dumps(
            [{"material_code": c, "quantity": 1, "unit": "pcs"} for c in PRODUCT_001_REQUIRED_CODES]
            + [{"material_code": c, "quantity": 1, "unit": "pcs"} for c in PRODUCT_001_OPTIONAL_FACE_FINISH_CODES]
        ),
        active=False,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    readiness = await ProductReadinessService(db_session).evaluate_template_readiness(template.id)
    blockers = readiness["technical_readiness"]["blockers"]
    warnings = readiness["technical_readiness"]["warnings"]

    assert "template_inactive" in blockers
    assert any(str(w).startswith("material_registry_missing:MAT_VINYL_PRINT_LAMINATED") for w in warnings)
    assert any(str(w).startswith("material_registry_missing:MAT_ORACAL_641") for w in warnings)
    assert any(str(w).startswith("material_registry_missing:MAT_ORACAL_651") for w in warnings)
