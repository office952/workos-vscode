"""Seed Product 001 material registry entries for v1.1 (no commercial prices).

This seed is intentionally non-commercial:
- inserts Product 001 material codes only
- keeps unit_cost as NULL
- keeps status as missing_price / needs_owner_input
- does not activate pricing

Material vocabulary (interim, owner-approved direction):
- ProductSystem / CostEngine / quotes for litere volumetrice: TPL-VOLUMETRIC-LETTERS
  and operational MAT-*-LITERE / shared LED stubs (exact-code matching; no aliases).
- Product 001 MAT_* rows: owner-confirmed BOM / dossier inputs; cross-referenced below
  via source_notes only — not runtime aliases.

Operational volumetric codes with no Product 001 BOM row in this seed (BUILD 4 / inventory):
MAT-SPATE-PVC-LITERE (display: Forex 10 mm spate litere — cod istoric, nu redenumit),
MAT-LED-MODULE, MAT-LED-PSU-12V, MAT-SABLON-MONTAJ, MAT-VOPSEA-RAL.
Panou ACM (MAT_ACM_PANEL_*) = suport premontaj opțional, nu spate literă.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Tuple

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.inventory_materials import Inventory_materials

logger = logging.getLogger(__name__)

# Reference-only map for developers; not imported by application logic.
PRODUCT_001_TO_VOLUMETRIC_CROSSWALK: Tuple[Tuple[str, str], ...] = (
    ("MAT_ACM_PANEL_3MM", "MAT-ACP-FATA-LITERE"),
    ("MAT_ACM_PANEL_4MM", "MAT-ACP-FATA-LITERE"),
    ("MAT_RECT_TUBE_PROFILE_MAIN", "MAT-PROFIL-LATERAL-LITERE"),
    ("MAT_RECT_TUBE_PROFILE_RIB", "MAT-PROFIL-LATERAL-LITERE"),
    ("MAT_FASTENERS_CSK_SELF_DRILL", "MAT-CONSUMABILE-MONTAJ"),
    ("MAT_ADHESIVE_SEALANT", "MAT-CONSUMABILE-MONTAJ"),
    ("MAT_VINYL_PRINT_LAMINATED", "(face/finish option — not MAT-VOPSEA-RAL)"),
    ("MAT_ORACAL_641", "(face/finish option — not MAT-VOPSEA-RAL)"),
    ("MAT_ORACAL_651", "(face/finish option — not MAT-VOPSEA-RAL)"),
    ("MAT_ORACAL_8500_TRANSLUCENT", "(translucent face film — not MAT-VOPSEA-RAL)"),
)

# Operational TPL-VOLUMETRIC-LETTERS codes without a Product 001 MAT_* row above.
VOLUMETRIC_OPERATIONAL_CODES_WITHOUT_PRODUCT_001_BOM: Tuple[str, ...] = (
    "MAT-SPATE-PVC-LITERE",
    "MAT-LED-MODULE",
    "MAT-LED-PSU-12V",
    "MAT-VOPSEA-RAL",
    "MAT-SABLON-MONTAJ",
)

_CROSSREF = (
    "Cross-reference only (not a runtime alias). "
    "Owner-confirmed BOM material for Product 001. "
    "Do not rename operational template codes without owner-approved migration. "
)

PRODUCT_001_MATERIAL_ROWS: List[Dict[str, Any]] = [
    {
        "code": "MAT_ACM_PANEL_3MM",
        "name": "Alucobond / ACM panel sheet 3mm",
        "unit": "m2",
        "category": "product_001",
        "status": "needs_owner_input",
        "source_notes": (
            _CROSSREF
            + "Operational volumetric template TPL-VOLUMETRIC-LETTERS currently uses "
            "MAT-ACP-FATA-LITERE for letter face (mp, letter_face_area). "
            "This row is the 3mm ACM panel BOM variant; thickness choice is separate from template code."
        ),
    },
    {
        "code": "MAT_ACM_PANEL_4MM",
        "name": "Alucobond / ACM panel sheet 4mm",
        "unit": "m2",
        "category": "product_001",
        "status": "needs_owner_input",
        "source_notes": (
            _CROSSREF
            + "Operational volumetric template TPL-VOLUMETRIC-LETTERS currently uses "
            "MAT-ACP-FATA-LITERE for letter face (mp, letter_face_area). "
            "This row is the 4mm ACM panel BOM variant; thickness choice is separate from template code."
        ),
    },
    {
        "code": "MAT_RECT_TUBE_PROFILE_MAIN",
        "name": "Metal rectangular tube main frame",
        "unit": "m",
        "category": "product_001",
        "status": "missing_price",
        "source_notes": (
            _CROSSREF
            + "Volumetric template uses MAT-PROFIL-LATERAL-LITERE for lateral letter profile "
            "(ml, letter_perimeter). Rectangular tube main frame may be a different structural role — "
            "requires owner decision before treating as equivalent."
        ),
    },
    {
        "code": "MAT_RECT_TUBE_PROFILE_RIB",
        "name": "Metal rectangular tube internal ribs",
        "unit": "m",
        "category": "product_001",
        "status": "missing_price",
        "source_notes": (
            _CROSSREF
            + "Volumetric template uses MAT-PROFIL-LATERAL-LITERE for lateral letter profile. "
            "Internal ribs may not map 1:1 to lateral profile stock — requires owner decision."
        ),
    },
    {
        "code": "MAT_FASTENERS_CSK_SELF_DRILL",
        "name": "Countersunk/conical self-drilling screws",
        "unit": "set",
        "category": "product_001",
        "status": "missing_price",
        "source_notes": (
            _CROSSREF
            + "Operational template bundles fasteners under MAT-CONSUMABILE-MONTAJ (FINISAJ component). "
            "This row is the explicit owner BOM line for screws."
        ),
    },
    {
        "code": "MAT_ADHESIVE_SEALANT",
        "name": "Assembly adhesive and sealant",
        "unit": "buc",
        "category": "product_001",
        "status": "missing_price",
        "source_notes": (
            _CROSSREF
            + "Operational template may include adhesive within MAT-CONSUMABILE-MONTAJ; "
            "this row is the explicit owner BOM line for adhesive/sealant."
        ),
    },
    {
        "code": "MAT_VINYL_PRINT_LAMINATED",
        "name": "Printed and laminated vinyl",
        "unit": "m2",
        "category": "product_001_optional",
        "status": "needs_owner_input",
        "source_notes": (
            _CROSSREF
            + "Optional face/finish path for Product 001; not the same as operational MAT-VOPSEA-RAL "
            "(RAL paint, conditional paint_finish). Requires product option decision at intake/dossier."
        ),
    },
    {
        "code": "MAT_ORACAL_641",
        "name": "Oracal 641 vinyl",
        "unit": "m2",
        "category": "product_001_optional",
        "status": "needs_owner_input",
        "source_notes": (
            _CROSSREF
            + "Optional vinyl face finish; alternative to paint (MAT-VOPSEA-RAL) on volumetric template. "
            "Requires product option decision — not a runtime alias for MAT-ACP-FATA-LITERE."
        ),
    },
    {
        "code": "MAT_ORACAL_651",
        "name": "Oracal 651 vinyl",
        "unit": "m2",
        "category": "product_001_optional",
        "status": "needs_owner_input",
        "source_notes": (
            _CROSSREF
            + "Optional vinyl face finish; alternative to paint (MAT-VOPSEA-RAL) on volumetric template. "
            "Requires product option decision — not a runtime alias for MAT-ACP-FATA-LITERE."
        ),
    },
    {
        "code": "MAT_ORACAL_8500_TRANSLUCENT",
        "name": "Oracal 8500 translucent",
        "unit": "m2",
        "category": "folii_translucente_firme_luminoase",
        "status": "needs_owner_input",
        "source_notes": (
            _CROSSREF
            + "Translucent face film for illuminated letters; pairs with operational LED codes "
            "(MAT-LED-MODULE, MAT-LED-PSU-12V) on TPL-VOLUMETRIC-LETTERS — no Product 001 MAT_* LED row. "
            "Not equivalent to MAT-VOPSEA-RAL; requires product option decision."
        ),
    },
]


async def seed_product_001_material_registry_v1_1() -> Dict[str, int]:
    inserted = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        for mat in PRODUCT_001_MATERIAL_ROWS:
            existing = await session.execute(
                select(Inventory_materials).where(Inventory_materials.code == mat["code"])
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            session.add(
                Inventory_materials(
                    code=mat["code"],
                    name=mat["name"],
                    unit=mat["unit"],
                    category=mat["category"],
                    unit_cost=None,
                    status=mat["status"],
                    source_notes=mat.get("source_notes"),
                )
            )
            inserted += 1

        await session.commit()

    logger.info(
        "Seeded Product 001 material registry v1.1: inserted=%d skipped=%d",
        inserted,
        skipped,
    )
    return {"inserted": inserted, "skipped": skipped}


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_product_001_material_registry_v1_1()
    print(
        "[seed_product_001_material_registry_v1_1] "
        f"inserted={stats['inserted']} skipped={stats['skipped']}"
    )


if __name__ == "__main__":
    asyncio.run(_main())
