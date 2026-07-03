"""Seed script for the canonical Product Families registry.

Ensures the canonical families exist and are active. The seed is idempotent:
missing rows are created, existing canonical rows are updated only when their
canonical metadata or active flag drifted, and unrelated rows are untouched.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import List, Dict, Any

from sqlalchemy import select

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from core.database import db_manager
from models.product_families import Product_families
import models  # noqa: F401  - ensure all models registered

logger = logging.getLogger(__name__)

CANONICAL_FAMILIES: List[Dict[str, Any]] = [
    {
        "family_id": "print_large_format",
        "label": "Print format mare",
        "category": "print",
        "description": "Imprimare pe banner, PVC, folie, backlit",
    },
    {
        "family_id": "casete_luminoase",
        "label": "Casete luminoase",
        "category": "semnalistica",
        "description": "Casete luminoase cu LED, frontlit/backlit",
    },
    {
        "family_id": "litere_volumetrice",
        "label": "Litere volumetrice",
        "category": "semnalistica",
        "description": "Litere 3D volumetrice luminoase sau neluminoase",
    },
    {
        "family_id": "colantari_auto",
        "label": "Colantări auto",
        "category": "colantari",
        "description": "Colantare vehicule, parțiale sau integrale",
    },
    {
        "family_id": "semnalistica_interioara",
        "label": "Semnalistică interioară",
        "category": "semnalistica",
        "description": "Plăcuțe, indicatoare și semnalistică pentru spații interioare",
    },
    {
        "family_id": "semnalistica_exterioara",
        "label": "Semnalistică exterioară",
        "category": "semnalistica",
        "description": "Semnalistică exterioară, totemuri, indicatoare stradale",
    },
    {
        "family_id": "panouri_publicitare",
        "label": "Panouri publicitare",
        "category": "publicitate",
        "description": "Panouri publicitare mari, billboarduri",
    },
    {
        "family_id": "textile_banner",
        "label": "Textile și banner",
        "category": "print",
        "description": "Banner textil, flag-uri, steaguri publicitare",
    },
    {
        "family_id": "cnc_debitare",
        "label": "Debitare CNC",
        "category": "productie",
        "description": "Debitare CNC pentru PVC, acril, aluminiu, lemn",
    },
    {
        "family_id": "servicii_montaj",
        "label": "Servicii montaj",
        "category": "servicii",
        "description": "Servicii de montaj și instalare la beneficiar",
    },
    # Sprint #20 — Product Registry Foundation. Added to support the upcoming
    # real production template `TPL-ACP-LIGHT-ROUTED` (ACP backlit routed panel).
    # No existing family is renamed or removed; this is an additive extension.
    {
        "family_id": "panouri_acp_iluminate",
        "label": "Panouri ACP Iluminate",
        "category": "semnalistica",
        "description": "Panouri ACP/Dibond iluminate din spate, cu frezare CNC.",
    },
    # BUILD 4 — Additional families for real advertising-production templates.
    # Maps: TPL-PLEXI-PLATE → plexi_cnc, TPL-VINYL-STICKER → vinyl_stickers,
    # TPL-MESH-EXTERNALIZED → externalized_print.
    {
        "family_id": "plexi_cnc",
        "label": "Plexiglass / Debitare CNC",
        "category": "productie",
        "description": "Plăci plexiglas — tăiere laser/CNC, finisare muchii, montaj distanțiere.",
    },
    {
        "family_id": "vinyl_stickers",
        "label": "Autocolant / Sticker",
        "category": "colantari",
        "description": "Autocolante și stickere — print vinyl, laminare UV, tăiere contur.",
    },
    {
        "family_id": "externalized_print",
        "label": "Print externalizat",
        "category": "print",
        "description": "Producție externalizată — mesh, bannere subcontractate la furnizor extern.",
    },
]


async def seed_product_families() -> Dict[str, int]:
    """Seed canonical product families. Returns stats dict."""
    created = 0
    updated = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        for fam in CANONICAL_FAMILIES:
            existing_result = await session.execute(
                select(Product_families).where(
                    Product_families.family_id == fam["family_id"]
                )
            )
            existing = existing_result.scalar_one_or_none()
            if existing is None:
                session.add(Product_families(active=True, **fam))
                created += 1
                continue

            changed = False
            for field in ("label", "category", "description"):
                new_value = fam.get(field)
                if getattr(existing, field) != new_value:
                    setattr(existing, field, new_value)
                    changed = True

            if existing.active is not True:
                existing.active = True
                changed = True

            if changed:
                updated += 1
            else:
                skipped += 1

        await session.commit()

        active_total_result = await session.execute(
            select(Product_families).where(Product_families.active.is_(True))
        )
        active_total = len(active_total_result.scalars().all())

    logger.info(
        "Seeded product_families: created=%d updated=%d skipped=%d active_total=%d",
        created,
        updated,
        skipped,
        active_total,
    )
    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "active_total": active_total,
    }


async def _main():
    await db_manager.init_db()
    stats = await seed_product_families()
    print(f"created: {stats['created']}")
    print(f"updated/skipped: {stats['updated']}/{stats['skipped']}")
    print(f"active total: {stats['active_total']}")


if __name__ == "__main__":
    asyncio.run(_main())