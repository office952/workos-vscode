"""Seed script for canonical inventory material stubs (Sprint #20).

Seeds 10 stub materials for the first real production template
(ACP backlit routed panel). All stubs have `unit_cost=NULL` and
`status="missing_price"` — no commercial price is invented.

Idempotent: re-running skips any `code` that already exists.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401 - ensure all models are registered
from models.inventory_materials import Inventory_materials
from seeds.material_canonical_naming import canonical_name_for_code, source_notes_for_code

logger = logging.getLogger(__name__)

CANONICAL_MATERIAL_STUBS: List[Dict[str, Any]] = [
    {
        "code": "MAT-ACP-3MM",
        "name": "ACP / Dibond 3mm",
        "unit": "mp",
        "category": "panou_compozit",
    },
    {
        "code": "MAT-PLEXI-OPAL-3MM",
        "name": "Plexiglas opal 3mm",
        "unit": "mp",
        "category": "plexiglas",
    },
    {
        "code": "MAT-PLEXI-TRANSP-10MM",
        "name": "Plexiglas transparent 10mm",
        "unit": "mp",
        "category": "plexiglas",
    },
    {
        "code": "MAT-PLEXI-OPAL-10MM",
        "name": "Plexiglas opal 10mm",
        "unit": "mp",
        "category": "plexiglas",
    },
    {
        "code": "MAT-LED-MODULE",
        "name": "Modul LED (rezistent apa, backlit)",
        "unit": "buc",
        "category": "iluminat_led",
    },
    {
        "code": "MAT-LED-PSU-12V",
        "name": "Sursa alimentare LED 12V",
        "unit": "buc",
        "category": "iluminat_led",
    },
    {
        "code": "MAT-PROFIL-ALU",
        "name": "Profil aluminiu structura",
        "unit": "ml",
        "category": "profil_metal",
    },
    {
        "code": "MAT-SURUBURI-GEN",
        "name": "Suruburi / prinderi generale",
        "unit": "set",
        "category": "consumabile",
    },
    {
        "code": "MAT-ADEZIV-SILICON",
        "name": "Adeziv / silicon montaj",
        "unit": "buc",
        "category": "consumabile",
    },
    {
        "code": "MAT-CONSUMABILE-MONTAJ",
        "name": "Consumabile montaj (banda, capse etc.)",
        "unit": "set",
        "category": "consumabile",
    },
]


async def seed_inventory_material_stubs() -> Dict[str, int]:
    """Seed canonical material stubs with status='missing_price'. Idempotent."""
    inserted = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        for mat in CANONICAL_MATERIAL_STUBS:
            existing = await session.execute(
                select(Inventory_materials).where(
                    Inventory_materials.code == mat["code"]
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue
            session.add(
                Inventory_materials(
                    code=mat["code"],
                    name=canonical_name_for_code(mat["code"], mat["name"]),
                    unit=mat["unit"],
                    category=mat["category"],
                    source_notes=source_notes_for_code(mat["code"]),
                    unit_cost=None,
                    status="missing_price",
                )
            )
            inserted += 1
        await session.commit()

    logger.info(
        "Seeded inventory_materials stubs: inserted=%d skipped=%d",
        inserted,
        skipped,
    )
    return {"inserted": inserted, "skipped": skipped}


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_inventory_material_stubs()
    print(
        f"[seed_inventory_material_stubs] inserted={stats['inserted']} "
        f"skipped={stats['skipped']}"
    )


if __name__ == "__main__":
    asyncio.run(_main())