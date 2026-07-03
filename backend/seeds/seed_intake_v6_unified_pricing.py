"""Seed unified Intake V6 pricing registries.

V6 keeps V4 operator math/results, but every commercial unit price must be
present in inventory_materials or workcenter_rates so formulas do not depend on
scattered owner constants.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.inventory_materials import Inventory_materials
from models.workcenter_rates import Workcenter_rates
from seeds.seed_intake_v5_volumetric_letters_pricing import MATERIAL_PRICES, WORKCENTER_RATES as BASE_WORKCENTER_RATES

logger = logging.getLogger(__name__)

EXTRA_MATERIAL_PRICES: list[dict[str, Any]] = [
    {
        "code": "SVC-LAMINATION-SERVICE",
        "name": "Serviciu laminare print autocolant",
        "unit": "mp",
        "unit_cost": 5.0,
        "category": "servicii_productie",
    },
    {
        "code": "MAT-ADEZIV-CANT-LITERE",
        "name": "Adeziv lipire cant / module LED",
        "unit": "ml",
        "unit_cost": 30.0 / 50.0 / 5.1,
        "category": "consumabile",
    },
    {
        "code": "MAT-CABLU-MYYUP-2X075",
        "name": "Cablu electric MYYUP 2 x 0.75",
        "unit": "ml",
        "unit_cost": 1.9 / 5.1,
        "category": "consumabile_electrice",
    },
    {
        "code": "MAT-CABLU-MYYUP-2X15",
        "name": "Cablu electric MYYUP 2 x 1.5 alimentare 220V",
        "unit": "ml",
        "unit_cost": 3.9 / 5.1,
        "category": "consumabile_electrice",
    },
]

V6_MATERIAL_PRICES = [*MATERIAL_PRICES, *EXTRA_MATERIAL_PRICES]
V6_WORKCENTER_RATES = [
    {
        **item,
        "rate": 5.0,
        "label": "Lipire cant profil pe față litere — rată V4 unificată",
    }
    if item["code"] == "RETURN_PROFILE_FACE_BONDING"
    else item
    for item in BASE_WORKCENTER_RATES
]


def _rate_columns(rate: float, basis: str) -> dict[str, Any]:
    values: dict[str, Any] = {
        "rate_per_hour": None,
        "rate_per_linear_meter": None,
    }
    if basis == "per_hour":
        values["rate_per_hour"] = rate
    else:
        values["rate_per_linear_meter"] = rate
    return values


async def seed_intake_v6_unified_pricing() -> dict[str, int]:
    inserted_materials = 0
    updated_materials = 0
    inserted_rates = 0
    updated_rates = 0
    now = datetime.now(timezone.utc)

    async with db_manager.async_session_maker() as session:
        for item in V6_MATERIAL_PRICES:
            row = (
                await session.execute(
                    select(Inventory_materials).where(Inventory_materials.code == item["code"])
                )
            ).scalar_one_or_none()
            if row is None:
                row = Inventory_materials(
                    code=item["code"],
                    name=item["name"],
                    unit=item["unit"],
                    category=item["category"],
                )
                session.add(row)
                inserted_materials += 1
            else:
                updated_materials += 1
            row.name = item["name"]
            row.unit = item["unit"]
            row.category = item["category"]
            row.unit_cost = item["unit_cost"]
            row.currency = "EUR"
            row.vat_percent = 0
            row.valid_from = now
            row.status = "active"
            row.source_name = "owner_seed_intake_v6_unified_pricing"
            row.source_notes = "Unified V4/V6 intake pricing source; edit in inventory registry."
            row.source_checked_at = now
            row.source_review_status = "accepted_override"
            row.source_reviewed_at = now
            row.source_reviewed_by = "seed_intake_v6_unified_pricing"

        for item in V6_WORKCENTER_RATES:
            row = (
                await session.execute(
                    select(Workcenter_rates).where(Workcenter_rates.code == item["code"])
                )
            ).scalar_one_or_none()
            if row is None:
                row = Workcenter_rates(code=item["code"], label=item["label"])
                session.add(row)
                inserted_rates += 1
            else:
                updated_rates += 1
            row.label = item["label"]
            row.rate_basis = item["basis"]
            row.currency = "EUR"
            row.status = "active"
            row.is_active = True
            row.notes = "Unified V4/V6 intake pricing source; edit in workcenter rates registry."
            for column, value in _rate_columns(item["rate"], item["basis"]).items():
                setattr(row, column, value)

        await session.commit()

    stats = {
        "inserted_materials": inserted_materials,
        "updated_materials": updated_materials,
        "inserted_rates": inserted_rates,
        "updated_rates": updated_rates,
    }
    logger.info("Seeded Intake V6 unified pricing: %s", stats)
    return stats


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_intake_v6_unified_pricing()
    print(f"[seed_intake_v6_unified_pricing] {stats}")


if __name__ == "__main__":
    asyncio.run(_main())
