from __future__ import annotations

import pytest
from sqlalchemy import select

from models.inventory_materials import Inventory_materials
from models.suppliers import Suppliers


@pytest.mark.asyncio
async def test_supplier_id_and_legacy_supplier_text_can_coexist(auth_client, db_session):
    supplier = Suppliers(code="SUP-001", name="Supplier 001")
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    material = Inventory_materials(
        code="MAT-SUP-001",
        name="Supplier linked material",
        unit="mp",
        category="test",
        status="missing_price",
        supplier="Legacy Supplier Name",
    )
    db_session.add(material)
    await db_session.commit()

    response = auth_client.patch(
        "/api/admin/inventory-materials/MAT-SUP-001",
        json={"supplier_id": supplier.id},
    )
    assert response.status_code == 200

    refreshed = (
        await db_session.execute(
            select(Inventory_materials).where(Inventory_materials.code == "MAT-SUP-001")
        )
    ).scalar_one()

    assert refreshed.supplier_id == supplier.id
    assert refreshed.supplier == "Legacy Supplier Name"
