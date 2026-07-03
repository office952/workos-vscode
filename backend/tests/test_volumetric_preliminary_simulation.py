"""Preliminary volumetric simulate-cost — no 500 on illuminated frontlit payloads."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from core.database import get_db
from dependencies.auth import get_current_user
from models.product_templates import Product_templates
from routers.product_system_cost_simulation import router
from services.product_system_cost_simulation_service import ProductSystemCostSimulationService

FRONTLIT_QUOTE_INPUT = {
    "width_mm": 4800.001029,
    "height_mm": 599.999655,
    "depth_mm": 60,
    "return_depth_mm": 60,
    "letter_count": 11,
    "letter_perimeter_m": 22.29574,
    "letter_face_area_m2": 1.466571,
    "illumination_type": "frontlit",
    "lighting_system_type": "led_modules",
    "led_module_watts": 1.44,
    "led_module_count": 223,
    "selected_psu_watts": 200,
    "psu_watts": 200,
    "face_finish_type": "oracal_651",
    "face_vinyl_color_code": "651-020",
    "face_vinyl_color_name": "Golden yellow",
    "volume_finish": "none",
    "mounting_system": "direct_wall",
    "mounting_template_enabled": False,
}


@pytest.mark.asyncio
async def test_simulate_cost_frontlit_volumetric_does_not_500(db_session) -> None:
    tpl = (
        await db_session.execute(
            select(Product_templates).where(
                Product_templates.template_code == "TPL-VOLUMETRIC-LETTERS"
            )
        )
    ).scalar_one_or_none()
    if tpl is None:
        pytest.skip("TPL-VOLUMETRIC-LETTERS not seeded in test DB")

    svc = ProductSystemCostSimulationService(db_session)
    result = await svc.simulate(
        template_id=tpl.id,
        quantity=1,
        quote_input=dict(FRONTLIT_QUOTE_INPUT),
        pricing={"margin_pct": 25, "vat_pct": 21, "discount_pct": 0},
        simulation_context={
            "source": "volumetric_quote_flow",
            "reason": "Product 001 preliminary volumetric costing",
        },
    )

    assert result.status in {"simulated", "blocked"}
    assert "ImportError" not in " ".join(result.blocked_reasons)
    assert result.cost_result.get("total_cost", 0) > 0


@pytest.mark.asyncio
async def test_simulate_cost_router_frontlit_returns_200_not_500(db_fixture) -> None:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-user"}

    async def _db_override():
        async with db_fixture.session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _db_override

    async with db_fixture.session_maker() as session:
        tpl = (
            await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == "TPL-VOLUMETRIC-LETTERS"
                )
            )
        ).scalar_one_or_none()
    if tpl is None:
        pytest.skip("TPL-VOLUMETRIC-LETTERS not seeded in test DB")

    client = TestClient(app)
    response = client.post(
        "/api/v1/product-system/simulate-cost",
        json={
            "template_id": tpl.id,
            "quantity": 1,
            "quote_input": FRONTLIT_QUOTE_INPUT,
            "pricing": {"margin_pct": 25, "vat_pct": 21, "discount_pct": 0},
            "simulation_context": {
                "source": "volumetric_quote_flow",
                "reason": "Product 001 preliminary volumetric costing",
            },
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] in {"simulated", "blocked", "error"}
    assert body["status"] != "error" or "ImportError" not in str(body.get("blocked_reasons"))
