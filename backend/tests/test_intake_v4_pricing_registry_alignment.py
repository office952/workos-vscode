"""Intake V4 material breakdown — alignment with /inventory/pricing (BLK-18 bridge)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from schemas.intake_v4 import IntakeV4MaterialQuantityRow
from sqlalchemy import select

from models.inventory_materials import Inventory_materials
from seeds.seed_build4_templates import seed_build4_templates
from seeds.seed_volumetric_owner_confirmed_prices import seed_volumetric_owner_confirmed_prices
from services.intake_v4_material_breakdown_service import (
    _apply_registry_prices,
    resolve_v4_registry_material_price,
)


@pytest.mark.asyncio
async def test_resolve_v4_price_uses_pricing_dict_not_loose_row_scan():
    pricing = {"MAT-ORACAL-651": {"unit_cost": 5.0, "currency": "EUR", "source": "inventory_materials"}}
    price, currency, source = await resolve_v4_registry_material_price(
        None,  # type: ignore[arg-type]
        "MAT-ORACAL-651",
        pricing_cache=pricing,
    )
    assert price == 5.0
    assert currency == "EUR"
    assert source == "pricing_registry"


@pytest.mark.asyncio
async def test_incomplete_inventory_row_excluded_like_cost_engine():
    """Row with unit_cost but missing vat/valid_from is not in pricing dict → missing."""
    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as lookup:
        lookup.return_value = {}
        price, _, source = await resolve_v4_registry_material_price(
            None,  # type: ignore[arg-type]
            "MAT-ORACAL-651",
        )
    assert price is None
    assert source == "missing"


@pytest.mark.asyncio
async def test_apply_registry_prices_no_owner_fallback():
    row = IntakeV4MaterialQuantityRow(
        material_key="face_vinyl",
        display_name="Vinil",
        category="material",
        quantity=1.0,
        base_quantity=1.0,
        unit="m2",
        quantity_basis="roll_nesting_quote_estimate",
        quantity_source="nesting",
        quantity_quality="estimated",
        priced_quantity=1.0,
        quantity_with_waste=1.0,
        registry_code="MAT-ORACAL-651",
        material_code="MAT-ORACAL-651",
        price_source="missing",
    )
    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as lookup:
        lookup.return_value = {
            "MAT-ORACAL-651": {"unit_cost": 5.0, "currency": "EUR", "source": "inventory_materials"}
        }
        enriched = await _apply_registry_prices(None, [row])  # type: ignore[arg-type]
    assert enriched[0].price_source == "pricing_registry"
    assert enriched[0].price_source != "owner_fallback"
    assert enriched[0].estimated_cost == 5.0


async def _seed_material_stubs(session) -> None:
    """Minimal rows so volumetric price seed can PATCH owner-confirmed costs."""
    codes = [
        ("MAT-ACP-FATA-LITERE", "mp"),
        ("MAT-SPATE-PVC-LITERE", "mp"),
        ("MAT-ORACAL-651", "mp"),
        ("MAT-VINYL-PRINT", "mp"),
        ("MAT-VINYL-PRINT-LAMINATED", "mp"),
        ("MAT-LED-MODULE", "buc"),
        ("MAT-PROFIL-LATERAL-LITERE-30MM", "ml"),
        ("MAT-PROFIL-LATERAL-LITERE-60MM", "ml"),
        ("MAT-PROFIL-LATERAL-LITERE-80MM", "ml"),
        ("MAT-PROFIL-LATERAL-LITERE-100MM", "ml"),
        ("MAT-LED-PSU-12V-60W", "buc"),
        ("MAT-LED-PSU-12V-100W", "buc"),
        ("MAT-LED-PSU-12V-160W", "buc"),
        ("MAT-LED-PSU-12V-200W", "buc"),
    ]
    for code, unit in codes:
        exists = (
            await session.execute(select(Inventory_materials).where(Inventory_materials.code == code))
        ).scalar_one_or_none()
        if exists:
            continue
        session.add(
            Inventory_materials(
                code=code,
                name=code,
                unit=unit,
                category="test",
                status="missing_price",
            )
        )
    await session.commit()


class TestIntakeV4PricingRegistrySeededBridge:
    @pytest.fixture(scope="class")
    def seeded_db(self):
        from tests._db_fixture import IsolatedDBFixture

        fixture = IsolatedDBFixture(prefix="intake_v4_pricing_align_")
        fixture.setup()
        asyncio.get_event_loop().run_until_complete(seed_build4_templates())

        async def _seed():
            async with fixture.session_maker() as session:
                await _seed_material_stubs(session)
            await seed_volumetric_owner_confirmed_prices()

        asyncio.get_event_loop().run_until_complete(_seed())
        yield fixture
        fixture.teardown()

    @pytest.mark.asyncio
    async def test_volumetric_seed_codes_in_pricing_dict(self, seeded_db):
        async with seeded_db.session_maker() as session:
            from services.inventory_materials_admin_service import load_material_cost_dict, load_material_pricing_dict

            pricing = await load_material_pricing_dict(session)
            costs = await load_material_cost_dict(session)
            for code in (
                "MAT-ORACAL-651",
                "MAT-ACP-FATA-LITERE",
                "MAT-SPATE-PVC-LITERE",
                "MAT-PROFIL-LATERAL-LITERE-60MM",
                "MAT-LED-MODULE",
                "MAT-LED-PSU-12V-100W",
                "MAT-VINYL-PRINT",
                "MAT-VINYL-PRINT-LAMINATED",
            ):
                assert code in pricing, f"{code} missing from load_material_pricing_dict"
                assert code in costs
                unit_price, currency, source = await resolve_v4_registry_material_price(
                    session,
                    code,
                    pricing_cache=pricing,
                )
                assert source == "pricing_registry"
                assert unit_price is not None and unit_price > 0
                assert currency == "EUR"
