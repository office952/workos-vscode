"""Local/dev seed for Material Registry smoke testing.

Creates a small, idempotent DEV-SMOKE dataset for authenticated UI/API
verification without changing production-oriented canonical material sets.

Contract:
- Inserts 6 materials with code prefix DEV-SMOKE- (if missing).
- Inserts minimal price history snapshots for 2 smoke materials.
- Safe to rerun: skips existing material codes and deduplicates history rows
  by a deterministic snapshot_source marker.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.inventory_material_price_history import Inventory_material_price_history
from models.inventory_materials import Inventory_materials


SMOKE_SOURCE = "dev_smoke_seed_v1"


DEV_SMOKE_MATERIALS: list[dict[str, Any]] = [
    {
        "code": "DEV-SMOKE-ACP-3MM",
        "name": "DEV Smoke ACP 3mm",
        "unit": "mp",
        "category": "Placi",
        "subcategory": "ACM / Alucobond / Dibond",
        "status": "missing_price",
        "stock_current": 12.0,
        "stock_min": 3.0,
        "stock_max": 30.0,
        "location": "A-01",
        "source_name": "Baduc",
        "source_url": "https://www.baduc.ro/metalurgice/2504-teava-dreptunghiulara",
        "source_review_status": "stale",
        "source_notes": "Reference-only smoke source. Do not auto-activate price.",
    },
    {
        "code": "DEV-SMOKE-PLEXI-5MM",
        "name": "DEV Smoke Plexiglas 5mm",
        "unit": "mp",
        "category": "Placi",
        "subcategory": "Plexiglas",
        "status": "needs_owner_input",
        "stock_current": 8.0,
        "location": "A-02",
        "source_name": "Supplier Catalog",
        "source_url": "https://www.folii-adezive.ro/oracal-651-intermediate-cal-p-793.html",
        "source_review_status": "needs_review",
        "source_notes": "Reference-only smoke source. Do not auto-activate price.",
    },
    {
        "code": "DEV-SMOKE-LED-MODULE",
        "name": "DEV Smoke LED Module",
        "unit": "buc",
        "category": "Parti electrice",
        "subcategory": "LED modules",
        "status": "active",
        "unit_cost": 2.75,
        "currency": "RON",
        "vat_percent": 19.0,
        "valid_from": datetime(2026, 6, 1, tzinfo=timezone.utc),
        "stock_current": 150.0,
        "stock_min": 40.0,
        "stock_max": 400.0,
        "source_name": "DEV Supplier A",
        "source_url": "https://www.folii-adezive.ro/oracal-8500-translucent-cal-p-805.html",
        "source_checked_at": datetime(2026, 6, 2, 8, 0, tzinfo=timezone.utc),
        "source_review_status": "reviewed",
        "source_reviewed_at": datetime(2026, 6, 2, 8, 10, tzinfo=timezone.utc),
        "source_reviewed_by": "local_dev_seed",
        "source_notes": "Reference-only smoke source. Do not auto-activate price.",
    },
    {
        "code": "DEV-SMOKE-ALU-PROFILE",
        "name": "DEV Smoke Alu Profile",
        "unit": "ml",
        "category": "Profile metalice",
        "subcategory": "Aluminiu / profil rama",
        "status": "active",
        "unit_cost": 21.0,
        "currency": "RON",
        "vat_percent": 19.0,
        "valid_from": datetime(2026, 6, 1, tzinfo=timezone.utc),
        "source_name": "Baduc",
        "source_url": "https://www.baduc.ro/metalurgice/2506-teava-patrata",
        "source_checked_at": datetime(2026, 6, 2, 8, 15, tzinfo=timezone.utc),
        "source_review_status": "accepted_override",
        "source_reviewed_at": datetime(2026, 6, 2, 8, 20, tzinfo=timezone.utc),
        "source_reviewed_by": "local_dev_seed",
        "source_notes": "Reference-only smoke source. Do not auto-activate price.",
        "sheet_format_type": "linear",
        "sheet_unit": "m",
        "sheet_thickness": 1.5,
        "sheet_thickness_unit": "mm",
        "format_source": "manual",
        "format_verified": True,
        "format_notes": "Smoke linear profile format",
    },
    {
        "code": "DEV-SMOKE-ADHESIVE",
        "name": "DEV Smoke Adhesive",
        "unit": "buc",
        "category": "Consumabile",
        "subcategory": "adezivi",
        "status": "active",
        "unit_cost": 17.5,
        "source_review_status": "missing",
    },
    {
        "code": "DEV-SMOKE-MOUNT-KIT",
        "name": "DEV Smoke Mount Kit",
        "unit": "set",
        "category": "legacy_misc_material",
        "status": "archived",
        "source_review_status": "missing",
        "stock_current": 0.0,
        "stock_min": 0.0,
        "stock_max": 0.0,
        "location": "ARCHIVE",
    },
]


PRICE_HISTORY_ROWS: list[dict[str, Any]] = [
    {
        "code": "DEV-SMOKE-LED-MODULE",
        "unit_cost": 2.75,
        "currency": "RON",
        "vat_percent": 19.0,
        "valid_from": datetime(2026, 6, 1, tzinfo=timezone.utc),
        "changed_by": "local_dev_seed",
        "change_reason": "Initial smoke baseline",
        "snapshot_source": SMOKE_SOURCE,
    },
    {
        "code": "DEV-SMOKE-ALU-PROFILE",
        "unit_cost": 21.0,
        "currency": "RON",
        "vat_percent": 19.0,
        "valid_from": datetime(2026, 6, 1, tzinfo=timezone.utc),
        "changed_by": "local_dev_seed",
        "change_reason": "Initial smoke baseline",
        "snapshot_source": SMOKE_SOURCE,
    },
]


async def seed_local_dev_material_registry_smoke_data() -> dict[str, int]:
    inserted_materials = 0
    updated_materials = 0
    skipped_materials = 0
    inserted_history = 0
    skipped_history = 0

    async with db_manager.async_session_maker() as session:
        material_by_code: dict[str, Inventory_materials] = {}

        for payload in DEV_SMOKE_MATERIALS:
            code = payload["code"]
            existing = (
                await session.execute(
                    select(Inventory_materials).where(Inventory_materials.code == code)
                )
            ).scalar_one_or_none()

            if existing is not None:
                changed = False
                for key in [
                    "category",
                    "subcategory",
                    "source_name",
                    "source_url",
                    "source_checked_at",
                    "source_notes",
                    "source_review_status",
                    "source_reviewed_at",
                    "source_reviewed_by",
                ]:
                    if key in payload:
                        next_value = payload[key]
                        if getattr(existing, key, None) != next_value:
                            setattr(existing, key, next_value)
                            changed = True
                if changed:
                    updated_materials += 1
                material_by_code[code] = existing
                skipped_materials += 1
                continue

            row = Inventory_materials(**payload)
            session.add(row)
            await session.flush()
            material_by_code[code] = row
            inserted_materials += 1

        for payload in PRICE_HISTORY_ROWS:
            code = payload["code"]
            row = material_by_code.get(code)
            if row is None:
                row = (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.code == code)
                    )
                ).scalar_one_or_none()
                if row is None:
                    skipped_history += 1
                    continue

            duplicate = (
                await session.execute(
                    select(Inventory_material_price_history).where(
                        Inventory_material_price_history.material_id == row.id,
                        Inventory_material_price_history.snapshot_source
                        == payload["snapshot_source"],
                        Inventory_material_price_history.change_reason
                        == payload["change_reason"],
                    )
                )
            ).scalar_one_or_none()

            if duplicate is not None:
                skipped_history += 1
                continue

            session.add(
                Inventory_material_price_history(
                    material_id=row.id,
                    unit_cost=payload["unit_cost"],
                    currency=payload["currency"],
                    vat_percent=payload["vat_percent"],
                    valid_from=payload["valid_from"],
                    changed_at=datetime.now(timezone.utc),
                    changed_by=payload["changed_by"],
                    change_reason=payload["change_reason"],
                    snapshot_source=payload["snapshot_source"],
                )
            )
            inserted_history += 1

        await session.commit()

    return {
        "inserted_materials": inserted_materials,
        "updated_materials": updated_materials,
        "skipped_materials": skipped_materials,
        "inserted_history": inserted_history,
        "skipped_history": skipped_history,
    }


async def _main() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    os.chdir(backend_dir)
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./local_dev.db")
    await db_manager.init_db()
    stats = await seed_local_dev_material_registry_smoke_data()
    print(
        "[seed_local_dev_material_registry_smoke_data] "
        f"inserted_materials={stats['inserted_materials']} "
        f"updated_materials={stats['updated_materials']} "
        f"skipped_materials={stats['skipped_materials']} "
        f"inserted_history={stats['inserted_history']} "
        f"skipped_history={stats['skipped_history']}"
    )


if __name__ == "__main__":
    asyncio.run(_main())
