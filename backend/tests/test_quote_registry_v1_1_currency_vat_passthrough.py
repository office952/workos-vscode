from __future__ import annotations

from datetime import datetime, timezone

import pytest

from models.inventory_materials import Inventory_materials
from services.inventory_materials_admin_service import load_material_cost_dict


@pytest.mark.asyncio
async def test_registry_loader_keeps_only_pricing_complete_active_rows(db_session):
    db_session.add_all(
        [
            Inventory_materials(
                code="MAT-Q-READY",
                name="Ready",
                unit="mp",
                category="test",
                unit_cost=25.0,
                currency="RON",
                vat_percent=19.0,
                valid_from=datetime.now(timezone.utc),
                status="active",
            ),
            Inventory_materials(
                code="MAT-Q-INCOMPLETE",
                name="Incomplete",
                unit="mp",
                category="test",
                unit_cost=30.0,
                currency=None,
                vat_percent=19.0,
                valid_from=datetime.now(timezone.utc),
                status="active",
            ),
            Inventory_materials(
                code="MAT-Q-MISSING-PRICE",
                name="Missing price",
                unit="mp",
                category="test",
                unit_cost=None,
                status="missing_price",
            ),
        ]
    )
    await db_session.commit()

    out = await load_material_cost_dict(db_session)
    assert out.get("MAT-Q-READY") == 25.0
    assert "MAT-Q-INCOMPLETE" not in out
    assert "MAT-Q-MISSING-PRICE" not in out
