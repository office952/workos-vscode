"""BUILD 4 — Seed material stubs for 6 real advertising production templates.

Adds materials needed by: Banner, Placa plexiglass, Autocolant/sticker,
Caseta luminoasa, Litere volumetrice, Mesh externalizat.

All stubs have `unit_cost=NULL` and `status="missing_price"` — no
commercial price is invented. Idempotent: re-running skips existing codes.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.inventory_materials import Inventory_materials
from seeds.material_canonical_naming import canonical_name_for_code, source_notes_for_code

logger = logging.getLogger(__name__)

BUILD4_MATERIAL_STUBS: List[Dict[str, Any]] = [
    # --- Banner / Mesh ---
    {
        "code": "MAT-BANNER-510",
        "name": "Banner PVC 510g/mp",
        "unit": "mp",
        "category": "banner",
    },
    {
        "code": "MAT-BANNER-440",
        "name": "Banner PVC 440g/mp (economic)",
        "unit": "mp",
        "category": "banner",
    },
    {
        "code": "MAT-MESH-270",
        "name": "Mesh perforat 270g/mp",
        "unit": "mp",
        "category": "mesh",
    },
    {
        "code": "MAT-BACKLIT-FILM",
        "name": "Folie backlit pentru print",
        "unit": "mp",
        "category": "banner",
    },
    {
        "code": "MAT-CAPSE-METAL",
        "name": "Capse metalice (ochiuri)",
        "unit": "buc",
        "category": "consumabile",
    },
    {
        "code": "MAT-TIV-BANDA",
        "name": "Bandă tiv / întărire margini",
        "unit": "ml",
        "category": "consumabile",
    },
    # --- Plexiglass ---
    {
        "code": "MAT-PLEXI-TRANSP-3MM",
        "name": "Plexiglas transparent 3mm",
        "unit": "mp",
        "category": "plexiglas",
    },
    {
        "code": "MAT-PLEXI-TRANSP-5MM",
        "name": "Plexiglas transparent 5mm",
        "unit": "mp",
        "category": "plexiglas",
    },
    {
        "code": "MAT-PLEXI-ALB-3MM",
        "name": "Plexiglas alb 3mm",
        "unit": "mp",
        "category": "plexiglas",
    },
    {
        "code": "MAT-PLEXI-COLOR-3MM",
        "name": "Plexiglas colorat 3mm",
        "unit": "mp",
        "category": "plexiglas",
    },
    {
        "code": "MAT-DISTANTIERE-INOX",
        "name": "Distanțiere inox montaj",
        "unit": "set",
        "category": "consumabile",
    },
    {
        "code": "MAT-FOLIE-PROTECTIE",
        "name": "Folie protecție suprafață",
        "unit": "mp",
        "category": "consumabile",
    },
    # --- Vinyl / Autocolant ---
    {
        "code": "MAT-VINYL-CALANDRAT",
        "name": "Vinyl autoadeziv calandrat",
        "unit": "mp",
        "category": "vinyl",
    },
    {
        "code": "MAT-VINYL-TURNAT",
        "name": "Vinyl autoadeziv turnat (cast)",
        "unit": "mp",
        "category": "vinyl",
    },
    {
        "code": "MAT-VINYL-TRANSPARENT",
        "name": "Vinyl transparent printabil",
        "unit": "mp",
        "category": "vinyl",
    },
    {
        "code": "MAT-LAMINARE-MAT",
        "name": "Folie laminare mat UV",
        "unit": "mp",
        "category": "laminare",
    },
    {
        "code": "MAT-LAMINARE-LUCIOS",
        "name": "Folie laminare lucios UV",
        "unit": "mp",
        "category": "laminare",
    },
    {
        "code": "MAT-TRANSFER-TAPE",
        "name": "Bandă transfer aplicare",
        "unit": "mp",
        "category": "consumabile",
    },
    # --- Caseta luminoasa ---
    {
        "code": "MAT-PROFIL-ALU-BOX",
        "name": "Profil aluminiu casetă luminoasă",
        "unit": "ml",
        "category": "profil_metal",
    },
    {
        "code": "MAT-POLICARBONAT-OPAL",
        "name": "Policarbonat opal difuzie",
        "unit": "mp",
        "category": "plexiglas",
    },
    {
        "code": "MAT-PANOU-SPATE-ALU",
        "name": "Panou spate aluminiu 0.5mm",
        "unit": "mp",
        "category": "panou_compozit",
    },
    {
        "code": "MAT-LED-STRIP",
        "name": "Bandă LED 12V",
        "unit": "ml",
        "category": "iluminat_led",
    },
    {
        "code": "MAT-LED-MODULE",
        "name": "Modul LED 12V",
        "unit": "buc",
        "category": "iluminat_led",
    },
    {
        "code": "MAT-CABLU-ELECTRIC",
        "name": "Cablu electric + conectori",
        "unit": "set",
        "category": "iluminat_led",
    },
    # --- Litere volumetrice ---
    {
        "code": "MAT-ACP-FATA-LITERE",
        "name": "plexiglas 3mm PMMA - opal",
        "unit": "mp",
        "category": "plexiglas",
    },
    {
        "code": "MAT-PROFIL-LATERAL-LITERE",
        "name": "Volum aluminiu — alege lățimea (30/60/80/100)",
        "unit": "ml",
        "category": "profil_metal",
    },
    {
        "code": "MAT-PROFIL-LATERAL-LITERE-30MM",
        "name": "Volum aluminiu 30 mm",
        "unit": "ml",
        "category": "profil_metal",
    },
    {
        "code": "MAT-PROFIL-LATERAL-LITERE-60MM",
        "name": "Volum aluminiu 60 mm",
        "unit": "ml",
        "category": "profil_metal",
    },
    {
        "code": "MAT-PROFIL-LATERAL-LITERE-80MM",
        "name": "Volum aluminiu 80 mm",
        "unit": "ml",
        "category": "profil_metal",
    },
    {
        "code": "MAT-PROFIL-LATERAL-LITERE-100MM",
        "name": "Volum aluminiu 100 mm",
        "unit": "ml",
        "category": "profil_metal",
    },
    {
        "code": "MAT-SPATE-PVC-LITERE",
        "name": "Forex 10 mm",
        "unit": "mp",
        "category": "forex",
    },
    {
        "code": "MAT-VOPSEA-RAL",
        "name": "Vopsea RAL spray — tub",
        "unit": "buc",
        "category": "consumabile",
    },
    {
        "code": "MAT-SABLON-MONTAJ",
        "name": "Șablon montaj litere — Forex 3 mm (material mp)",
        "unit": "mp",
        "category": "forex",
    },
    {
        "code": "MAT-SABLON-HARTIE",
        "name": "Șablon hârtie — montaj litere (material mp)",
        "unit": "mp",
        "category": "consumabile",
    },
    {
        "code": "MAT-ORACAL-641",
        "name": "Oracal 641",
        "unit": "mp",
        "category": "vinyl",
    },
    {
        "code": "MAT-ORACAL-651",
        "name": "Oracal 651",
        "unit": "mp",
        "category": "vinyl",
    },
    {
        "code": "MAT-ORACAL-8500",
        "name": "Oracal 8500",
        "unit": "mp",
        "category": "vinyl",
    },
    {
        "code": "MAT-VINYL-PRINT",
        "name": "Autocolant print față litere",
        "unit": "mp",
        "category": "vinyl",
    },
    {
        "code": "MAT-VINYL-PRINT-LAMINATED",
        "name": "Printat / Laminat",
        "unit": "mp",
        "category": "vinyl",
    },
    {
        "code": "MAT-PREMOUNT-BAR-STEEL",
        "name": "Bare pătrate oțel 30×30×1.5 mm premontaj",
        "unit": "ml",
        "category": "profil_metal",
    },
    {
        "code": "MAT-PREMOUNT-BAR-ALUMINUM",
        "name": "Bare pătrate aluminiu 30×30×1.5 mm premontaj",
        "unit": "ml",
        "category": "profil_metal",
    },
    {
        "code": "MAT-LED-PSU-12V",
        "name": "Sursă LED 12V — alege puterea (60/100/160/200 W)",
        "unit": "buc",
        "category": "iluminat_led",
    },
    {
        "code": "MAT-LED-PSU-12V-60W",
        "name": "Sursă LED 12V 60W",
        "unit": "buc",
        "category": "iluminat_led",
    },
    {
        "code": "MAT-LED-PSU-12V-100W",
        "name": "Sursă LED 12V 100W",
        "unit": "buc",
        "category": "iluminat_led",
    },
    {
        "code": "MAT-LED-PSU-12V-160W",
        "name": "Sursă LED 12V 160W",
        "unit": "buc",
        "category": "iluminat_led",
    },
    {
        "code": "MAT-LED-PSU-12V-200W",
        "name": "Sursă LED 12V 200W",
        "unit": "buc",
        "category": "iluminat_led",
    },
    # --- Ink / Print consumables ---
    {
        "code": "MAT-INK-ECOSOLVENT",
        "name": "Cerneală ecosolvent (set CMYK)",
        "unit": "set",
        "category": "consumabile_print",
    },
    {
        "code": "MAT-INK-UV",
        "name": "Cerneală UV (set CMYK)",
        "unit": "set",
        "category": "consumabile_print",
    },
]


async def seed_build4_materials() -> Dict[str, int]:
    """Seed BUILD 4 material stubs. Idempotent."""
    inserted = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        for mat in BUILD4_MATERIAL_STUBS:
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
                    source_notes=source_notes_for_code(
                        mat["code"], mat.get("source_notes")
                    ),
                    unit_cost=None,
                    status="missing_price",
                )
            )
            inserted += 1
        await session.commit()

    logger.info(
        "Seeded BUILD 4 materials: inserted=%d skipped=%d",
        inserted,
        skipped,
    )
    return {"inserted": inserted, "skipped": skipped}


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_build4_materials()
    print(
        f"[seed_build4_materials] inserted={stats['inserted']} "
        f"skipped={stats['skipped']}"
    )


if __name__ == "__main__":
    asyncio.run(_main())