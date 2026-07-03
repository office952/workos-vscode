from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from models.inventory_material_price_history import Inventory_material_price_history
from models.inventory_materials import Inventory_materials


@pytest.mark.asyncio
async def test_history_row_inserted_on_price_governed_change(auth_client, db_session):
    row = Inventory_materials(
        code="MAT-HIST-001",
        name="History material",
        unit="mp",
        category="test",
        status="missing_price",
        supplier="Legacy Supplier",
    )
    db_session.add(row)
    await db_session.commit()

    response = auth_client.patch(
        "/api/admin/inventory-materials/MAT-HIST-001",
        json={
            "unit_cost": 12.5,
            "currency": "RON",
            "vat_percent": 19.0,
            "valid_from": "2026-06-02T00:00:00+00:00",
            "status": "active",
            "change_reason": "initial price governance",
        },
    )
    assert response.status_code == 200

    count = await db_session.scalar(
        select(func.count(Inventory_material_price_history.id)).where(
            Inventory_material_price_history.material_id == row.id
        )
    )
    assert int(count or 0) == 1


@pytest.mark.asyncio
async def test_no_history_row_when_non_price_field_changes(auth_client, db_session):
    row = Inventory_materials(
        code="MAT-HIST-002",
        name="Before rename",
        unit="mp",
        category="test",
        unit_cost=9.0,
        currency="RON",
        vat_percent=19.0,
        valid_from=datetime.now(timezone.utc),
        status="active",
    )
    db_session.add(row)
    await db_session.commit()

    response = auth_client.patch(
        "/api/admin/inventory-materials/MAT-HIST-002",
        json={"name": "After rename"},
    )
    assert response.status_code == 200

    count = await db_session.scalar(
        select(func.count(Inventory_material_price_history.id)).where(
            Inventory_material_price_history.material_id == row.id
        )
    )
    assert int(count or 0) == 0


@pytest.mark.asyncio
async def test_history_endpoint_returns_rows_newest_first(auth_client, db_session):
    row = Inventory_materials(
        code="MAT-HIST-READ-001",
        name="History read material",
        unit="mp",
        category="test",
        status="missing_price",
    )
    db_session.add(row)
    await db_session.commit()

    first = auth_client.patch(
        "/api/admin/inventory-materials/MAT-HIST-READ-001",
        json={
            "unit_cost": 10.0,
            "currency": "RON",
            "vat_percent": 19.0,
            "valid_from": "2026-06-02T00:00:00+00:00",
            "status": "active",
            "change_reason": "first",
        },
    )
    assert first.status_code == 200

    second = auth_client.patch(
        "/api/admin/inventory-materials/MAT-HIST-READ-001",
        json={
            "unit_cost": 11.0,
            "currency": "RON",
            "vat_percent": 19.0,
            "valid_from": "2026-06-03T00:00:00+00:00",
            "status": "active",
            "change_reason": "second",
        },
    )
    assert second.status_code == 200

    history = auth_client.get(
        "/api/admin/inventory-materials/MAT-HIST-READ-001/price-history"
    )
    assert history.status_code == 200
    payload = history.json()
    assert len(payload) >= 2
    assert payload[0]["change_reason"] == "second"
    assert payload[1]["change_reason"] == "first"


@pytest.mark.asyncio
async def test_source_metadata_patch_does_not_create_history(auth_client, db_session):
    row = Inventory_materials(
        code="MAT-SRC-001",
        name="Source metadata material",
        unit="mp",
        category="test",
        status="missing_price",
    )
    db_session.add(row)
    await db_session.commit()

    response = auth_client.patch(
        "/api/admin/inventory-materials/MAT-SRC-001",
        json={
            "source_name": "Furnizor exemplu",
            "source_url": "https://example.invalid/material",
            "source_checked_at": "2026-06-02T12:00:00+00:00",
            "source_notes": "observatie",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source_name"] == "Furnizor exemplu"
    assert body["source_url"] == "https://example.invalid/material"
    assert body["source_checked_at"] is not None
    assert body["source_notes"] == "observatie"
    assert body["status"] == "missing_price"

    count = await db_session.scalar(
        select(func.count(Inventory_material_price_history.id)).where(
            Inventory_material_price_history.material_id == row.id
        )
    )
    assert int(count or 0) == 0


@pytest.mark.asyncio
async def test_price_change_without_reason_is_rejected_and_does_not_write(auth_client, db_session):
    row = Inventory_materials(
        code="MAT-REASON-NEG-001",
        name="Reason negative",
        unit="mp",
        category="test",
        unit_cost=10.0,
        currency="RON",
        vat_percent=19.0,
        valid_from=datetime.now(timezone.utc),
        status="active",
    )
    db_session.add(row)
    await db_session.commit()

    before_updated_at = row.updated_at
    before_count = await db_session.scalar(
        select(func.count(Inventory_material_price_history.id)).where(
            Inventory_material_price_history.material_id == row.id
        )
    )

    response = auth_client.patch(
        "/api/admin/inventory-materials/MAT-REASON-NEG-001",
        json={"unit_cost": 11.5},
    )
    assert response.status_code == 400
    assert "change_reason" in str(response.json().get("detail", ""))

    await db_session.refresh(row)
    assert float(row.unit_cost) == 10.0
    assert row.updated_at == before_updated_at

    after_count = await db_session.scalar(
        select(func.count(Inventory_material_price_history.id)).where(
            Inventory_material_price_history.material_id == row.id
        )
    )
    assert int(after_count or 0) == int(before_count or 0)

    latest_reason = await db_session.scalar(
        select(Inventory_material_price_history.change_reason)
        .where(Inventory_material_price_history.material_id == row.id)
        .order_by(Inventory_material_price_history.changed_at.desc())
        .limit(1)
    )
    assert latest_reason is None


@pytest.mark.asyncio
async def test_price_change_with_reason_updates_and_writes_history(auth_client, db_session):
    row = Inventory_materials(
        code="MAT-REASON-POS-001",
        name="Reason positive",
        unit="mp",
        category="test",
        unit_cost=10.0,
        currency="RON",
        vat_percent=19.0,
        valid_from=datetime.now(timezone.utc),
        status="active",
    )
    db_session.add(row)
    await db_session.commit()

    response = auth_client.patch(
        "/api/admin/inventory-materials/MAT-REASON-POS-001",
        json={"unit_cost": 12.25, "change_reason": "pricing update"},
    )
    assert response.status_code == 200

    await db_session.refresh(row)
    assert float(row.unit_cost) == 12.25

    latest_reason = await db_session.scalar(
        select(Inventory_material_price_history.change_reason)
        .where(Inventory_material_price_history.material_id == row.id)
        .order_by(Inventory_material_price_history.changed_at.desc())
        .limit(1)
    )
    assert latest_reason == "pricing update"
