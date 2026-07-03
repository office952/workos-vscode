"""Seed script for the canonical Workcenter Rates registry (Sprint #20).

Seeds 6 canonical workcenters, all with `rate_per_hour=NULL` and
`status="missing_price"`. No commercial rate is invented — owner must
PATCH each row with a real rate before it flips to `active`.

Idempotent: re-running skips any code that already exists.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401 - ensure all models are registered with Base.metadata
from models.workcenter_rates import Workcenter_rates

logger = logging.getLogger(__name__)

CANONICAL_WORKCENTERS: List[Dict[str, Any]] = [
    {
        "code": "CNC_ROUTER",
        "label": "Frezare CNC (router)",
        "notes": "Frezare ACP / Dibond / plexiglas pe router CNC.",
    },
    {
        "code": "PANEL_CUTTING",
        "label": "Debitare panou",
        "notes": "Debitare panouri la dimensiune (ACP, plexiglas, etc.).",
    },
    {
        "code": "LED_ASSEMBLY",
        "label": "Asamblare module LED + sursa",
        "notes": "Montaj module LED, conectare sursa alimentare, test iluminare.",
    },
    {
        "code": "ASSEMBLY",
        "label": "Asamblare generala",
        "notes": "Asamblare corp panou, structura, fixare componente.",
    },
    {
        "code": "FINISHING",
        "label": "Finisare / curatare",
        "notes": "Debavurare, curatare, verificare estetica finala.",
    },
    {
        "code": "INSTALL_PREP",
        "label": "Pregatire montaj / ambalare",
        "notes": "Ambalare, pregatire kit montaj la beneficiar.",
    },
]


async def seed_workcenter_rates() -> Dict[str, int]:
    """Seed canonical workcenter rates. Returns stats dict."""
    inserted = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        for wc in CANONICAL_WORKCENTERS:
            existing = await session.execute(
                select(Workcenter_rates).where(Workcenter_rates.code == wc["code"])
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue
            session.add(
                Workcenter_rates(
                    code=wc["code"],
                    label=wc["label"],
                    rate_per_hour=None,
                    currency="RON",
                    status="missing_price",
                    notes=wc["notes"],
                )
            )
            inserted += 1
        await session.commit()

    logger.info(
        "Seeded workcenter_rates: inserted=%d skipped=%d", inserted, skipped
    )
    return {"inserted": inserted, "skipped": skipped}


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_workcenter_rates()
    print(
        f"[seed_workcenter_rates] inserted={stats['inserted']} "
        f"skipped={stats['skipped']}"
    )


if __name__ == "__main__":
    asyncio.run(_main())