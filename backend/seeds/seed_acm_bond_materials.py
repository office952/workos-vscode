"""ACM/Bond panel material stubs for SVG layer template pack.

MAT-ACM-BOND-3MM: owner-confirmed price applied via seed_acm_owner_confirmed_prices.
MAT-ACM-BOND-4MM: stub only — needs_owner_review until price confirmed.
MAT-ACM-BOND-PANEL: generic alias row (no single unit_cost).
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

ACM_BOND_MATERIAL_STUBS: List[Dict[str, Any]] = [
    {
        "code": "MAT-ACM-BOND-PANEL",
        "name": "Panou ACM / Dibond / Alucobond (alias grosime)",
        "unit": "mp",
        "category": "panou_compozit",
        "source_notes": (
            "Generic template alias — resolved at quote time from quote_input.acm_thickness_mm "
            "to MAT-ACM-BOND-3MM or MAT-ACM-BOND-4MM. Not letter Forex backing."
        ),
    },
    {
        "code": "MAT-ACM-BOND-3MM",
        "name": "Panou ACM / Bond / Dibond 3 mm",
        "unit": "mp",
        "category": "panou_compozit",
    },
    {
        "code": "MAT-ACM-BOND-4MM",
        "name": "Panou ACM / Bond / Dibond 4 mm",
        "unit": "mp",
        "category": "panou_compozit",
        "source_notes": "Thickness variant — price needs owner review unless confirmed.",
    },
]


async def seed_acm_bond_materials() -> Dict[str, Any]:
    inserted = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        for stub in ACM_BOND_MATERIAL_STUBS:
            existing = await session.execute(
                select(Inventory_materials).where(
                    Inventory_materials.code == stub["code"]
                )
            )
            if existing.scalar_one_or_none() is not None:
                skipped += 1
                continue
            session.add(
                Inventory_materials(
                    code=stub["code"],
                    name=canonical_name_for_code(stub["code"], stub["name"]),
                    unit=stub["unit"],
                    category=stub.get("category"),
                    source_notes=source_notes_for_code(
                        stub["code"], stub.get("source_notes")
                    ),
                    status="missing_price",
                    unit_cost=None,
                )
            )
            inserted += 1
        await session.commit()

    return {"inserted": inserted, "skipped": skipped}
