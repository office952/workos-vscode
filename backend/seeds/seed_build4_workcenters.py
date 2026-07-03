"""BUILD 4 — Seed workcenter stubs for advertising production templates.

Adds workcenters needed by: Banner, Placa plexiglass, Autocolant/sticker,
Caseta luminoasa, Litere volumetrice, Mesh externalizat.

All have `rate_per_hour=NULL` and `status="missing_price"`.
Idempotent: re-running skips existing codes.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.workcenter_rates import Workcenter_rates

logger = logging.getLogger(__name__)

BUILD4_WORKCENTERS: List[Dict[str, Any]] = [
    {
        "code": "LARGE_FORMAT_PRINT",
        "label": "Imprimare format mare (ecosolvent/UV)",
        "notes": "Printer ecosolvent sau UV pentru banner, vinyl, mesh.",
    },
    {
        "code": "LASER_CUTTING",
        "label": "Tăiere laser",
        "notes": "Laser CO2 pentru plexiglas, PVC, lemn.",
    },
    {
        "code": "LAMINATION",
        "label": "Laminare (mat/lucios)",
        "notes": "Laminator pentru protecție UV pe vinyl/print.",
    },
    {
        "code": "CONTOUR_CUTTING",
        "label": "Tăiere contur (plotter)",
        "notes": "Plotter de tăiere pentru vinyl, autocolant, contur.",
    },
    {
        "code": "WELDING_BANNER",
        "label": "Sudură banner (tiv/îmbinare)",
        "notes": "Mașină sudură cu aer cald pentru banner PVC.",
    },
    {
        "code": "CAPSARE",
        "label": "Capsare (ochiuri metalice)",
        "notes": "Presă manuală/pneumatică pentru capse metalice.",
    },
    {
        "code": "ELECTRICAL_WIRING",
        "label": "Cablaj electric",
        "notes": "Montaj LED, surse, conectori, testare electrică.",
    },
    {
        "code": "PAINTING",
        "label": "Vopsire / lăcuire",
        "notes": "Cabină vopsire sau vopsire manuală RAL.",
    },
    {
        "code": "PREPRESS",
        "label": "Prepress / pregătire fișiere",
        "notes": "Pregătire fișiere print, vectorizare, verificare culori.",
    },
    {
        "code": "QC_INSPECTION",
        "label": "Control calitate",
        "notes": "Inspecție vizuală, măsurători, verificare conformitate.",
    },
    {
        "code": "PACKAGING",
        "label": "Ambalare / pregătire livrare",
        "notes": "Ambalare protecție, etichetare, pregătire transport.",
    },
    {
        "code": "EXTERNAL_SUBCONTRACT",
        "label": "Subcontractare externă",
        "notes": "Producție externalizată la furnizor (mesh, litere speciale).",
    },
]


async def seed_build4_workcenters() -> Dict[str, int]:
    """Seed BUILD 4 workcenter stubs. Idempotent."""
    inserted = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        for wc in BUILD4_WORKCENTERS:
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
        "Seeded BUILD 4 workcenters: inserted=%d skipped=%d",
        inserted,
        skipped,
    )
    return {"inserted": inserted, "skipped": skipped}


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_build4_workcenters()
    print(
        f"[seed_build4_workcenters] inserted={stats['inserted']} "
        f"skipped={stats['skipped']}"
    )


if __name__ == "__main__":
    asyncio.run(_main())