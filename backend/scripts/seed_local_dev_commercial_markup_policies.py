"""Local/dev seed for commercial markup policies.

Creates idempotent DEV-SMOKE-safe policies used only for local smoke.
This data is NOT commercial truth and must not be used as production policy.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.commercial_markup_policies import Commercial_markup_policies


SEED_POLICIES: list[dict[str, Any]] = [
    {
        "scope_type": "global",
        "scope_value": "global",
        "markup_type": "percent",
        "markup_percent": 10.0,
        "markup_fixed": None,
        "currency": "RON",
        "rounding_mode": "nearest_0_10",
        "applies_to": "material_cost",
        "status": "draft",
        "priority": 100,
        "notes": "Local dev smoke markup policy, not commercial truth (global draft)",
    },
    {
        "scope_type": "category",
        "scope_value": "Folii",
        "markup_type": "percent",
        "markup_percent": 12.5,
        "markup_fixed": None,
        "currency": "RON",
        "rounding_mode": "nearest_0_10",
        "applies_to": "material_cost",
        "status": "active",
        "priority": 40,
        "notes": "Local dev smoke markup policy, not commercial truth (category Folii)",
    },
    {
        "scope_type": "category",
        "scope_value": "Profile metalice",
        "markup_type": "percent",
        "markup_percent": 9.0,
        "markup_fixed": None,
        "currency": "RON",
        "rounding_mode": "nearest_0_50",
        "applies_to": "material_cost",
        "status": "active",
        "priority": 45,
        "notes": "Local dev smoke markup policy, not commercial truth (category Profile metalice)",
    },
    {
        "scope_type": "material",
        "scope_value": "DEV-SMOKE-LED-MODULE",
        "markup_type": "hybrid",
        "markup_percent": 8.0,
        "markup_fixed": 0.5,
        "currency": "RON",
        "rounding_mode": "nearest_0_10",
        "applies_to": "material_cost",
        "status": "active",
        "priority": 10,
        "notes": "Local dev smoke markup policy, not commercial truth (material override)",
    },
    {
        "scope_type": "material",
        "scope_value": "DEV-SMOKE-MOUNT-KIT",
        "markup_type": "fixed",
        "markup_percent": None,
        "markup_fixed": 1.0,
        "currency": "RON",
        "rounding_mode": "nearest_1",
        "applies_to": "material_cost",
        "status": "archived",
        "priority": 20,
        "notes": "Local dev smoke markup policy, not commercial truth (archived sample)",
    },
]


async def seed_local_dev_commercial_markup_policies() -> dict[str, int]:
    inserted = 0
    updated = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        for payload in SEED_POLICIES:
            existing = (
                await session.execute(
                    select(Commercial_markup_policies).where(
                        Commercial_markup_policies.scope_type == payload["scope_type"],
                        Commercial_markup_policies.scope_value == payload["scope_value"],
                        Commercial_markup_policies.status == payload["status"],
                        Commercial_markup_policies.priority == payload["priority"],
                    )
                )
            ).scalar_one_or_none()

            if existing is None:
                session.add(Commercial_markup_policies(**payload))
                inserted += 1
                continue

            changed = False
            for key, value in payload.items():
                if getattr(existing, key, None) != value:
                    setattr(existing, key, value)
                    changed = True

            if changed:
                updated += 1
            else:
                skipped += 1

        await session.commit()

    return {"inserted": inserted, "updated": updated, "skipped": skipped}


async def _main() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    os.chdir(backend_dir)
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./local_dev.db")
    await db_manager.init_db()
    stats = await seed_local_dev_commercial_markup_policies()
    print(
        "[seed_local_dev_commercial_markup_policies] "
        f"inserted={stats['inserted']} updated={stats['updated']} skipped={stats['skipped']}"
    )


if __name__ == "__main__":
    asyncio.run(_main())