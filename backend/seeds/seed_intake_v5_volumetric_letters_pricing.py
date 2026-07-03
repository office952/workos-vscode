"""Seed Intake V5 pricing for TPL-VOLUMETRIC-LETTERS.

Idempotent dev/owner pricing seed for the simplified V5 intake path. The template
mapping stays structural in the blueprint dossier; this file only persists the
material unit costs and workcenter rates used by that mapping.
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

logger = logging.getLogger(__name__)

MATERIAL_PRICES: list[dict[str, Any]] = [
    {"code": "MAT-ACP-FATA-LITERE", "name": "PMMA / plexiglas acrilic 3 mm — față litere", "unit": "mp", "unit_cost": 16.0, "category": "plexiglas"},
    {"code": "MAT-SPATE-PVC-LITERE", "name": "PVC expandat 10 mm", "unit": "mp", "unit_cost": 16.0, "category": "forex"},
    {"code": "MAT-PROFIL-LATERAL-LITERE-30MM", "name": "Profil aluminiu return/cant 30 mm", "unit": "ml", "unit_cost": 2.0, "category": "profil_metal"},
    {"code": "MAT-PROFIL-LATERAL-LITERE-60MM", "name": "Profil aluminiu return/cant 60 mm", "unit": "ml", "unit_cost": 3.0, "category": "profil_metal"},
    {"code": "MAT-PROFIL-LATERAL-LITERE-80MM", "name": "Profil aluminiu return/cant 80 mm", "unit": "ml", "unit_cost": 4.0, "category": "profil_metal"},
    {"code": "MAT-PROFIL-LATERAL-LITERE-100MM", "name": "Profil aluminiu return/cant 100 mm", "unit": "ml", "unit_cost": 5.0, "category": "profil_metal"},
    {"code": "MAT-ORACAL-641", "name": "Folie autocolantă PVC — Oracal 641 Economy Cal", "unit": "mp", "unit_cost": 6.5, "category": "vinyl"},
    {"code": "MAT-ORACAL-651", "name": "Folie autocolantă PVC — Oracal 651", "unit": "mp", "unit_cost": 9.0, "category": "vinyl"},
    {"code": "MAT-ORACAL-8500", "name": "Folie autocolantă PVC — Oracal 8500 Translucent Cal", "unit": "mp", "unit_cost": 20.0, "category": "vinyl"},
    {"code": "MAT-VINYL-PRINT", "name": "Folie autocolantă PVC — print față litere", "unit": "mp", "unit_cost": 1.5, "category": "vinyl"},
    {"code": "MAT-VINYL-PRINT-LAMINATED", "name": "Folie autocolantă PVC — print + laminare față litere", "unit": "mp", "unit_cost": 10.0, "category": "vinyl"},
    {"code": "MAT-LED-MODULE", "name": "Modul LED 12V — backlit", "unit": "buc", "unit_cost": 0.5, "category": "iluminat_led"},
    {"code": "MAT-LED-STRIP", "name": "Bandă LED 12V", "unit": "ml", "unit_cost": 2.0, "category": "iluminat_led"},
    {"code": "MAT-LED-PSU-12V-60W", "name": "Sursă LED 12V 60W", "unit": "buc", "unit_cost": 12.0, "category": "iluminat_led"},
    {"code": "MAT-LED-PSU-12V-100W", "name": "Sursă LED 12V 100W", "unit": "buc", "unit_cost": 16.0, "category": "iluminat_led"},
    {"code": "MAT-LED-PSU-12V-160W", "name": "Sursă LED 12V 160W", "unit": "buc", "unit_cost": 20.0, "category": "iluminat_led"},
    {"code": "MAT-LED-PSU-12V-200W", "name": "Sursă LED 12V 200W", "unit": "buc", "unit_cost": 40.0, "category": "iluminat_led"},
    {"code": "MAT-VOPSEA-RAL", "name": "Vopsea RAL spray — tub", "unit": "buc", "unit_cost": 10.0, "category": "consumabile"},
    {"code": "MAT-PREMOUNT-BAR-STEEL", "name": "Țeavă pătrată oțel 30×30×1.5 mm", "unit": "ml", "unit_cost": 2.0, "category": "profil_metal"},
    {"code": "MAT-PREMOUNT-BAR-ALUMINUM", "name": "Țeavă pătrată aluminiu 30×30×1.5 mm", "unit": "ml", "unit_cost": 3.5, "category": "profil_metal"},
    {"code": "MAT-SABLON-MONTAJ", "name": "Șablon montaj Forex 3 mm", "unit": "mp", "unit_cost": 8.0, "category": "forex"},
    {"code": "MAT-SABLON-HARTIE", "name": "Șablon montaj hârtie", "unit": "mp", "unit_cost": 2.0, "category": "consumabile"},
    {"code": "MAT-CONSUMABILE-MONTAJ", "name": "Consumabile montaj", "unit": "set", "unit_cost": 5.0, "category": "consumabile"},
]

WORKCENTER_RATES: list[dict[str, Any]] = [
    {"code": "PREPRESS", "label": "Pregătire vector / prepress litere", "rate": 2.0, "basis": "per_piece"},
    {"code": "CNC_ROUTER", "label": "CNC router — tăiere/debitare", "rate": 1.5, "basis": "per_linear_meter"},
    {"code": "WC_METAL_FAB", "label": "Servicii debitare metale — lăcătușerie", "rate": 1.5, "basis": "per_linear_meter"},
    {"code": "RETURN_PROFILE_MACHINE_FORMING", "label": "Modelare cant profil litere — utilaj", "rate": 5.0, "basis": "per_linear_meter"},
    {"code": "RETURN_PROFILE_FACE_BONDING", "label": "Lipire cant profil pe față litere", "rate": 7.0, "basis": "per_linear_meter"},
    {"code": "PAINTING", "label": "Vopsire RAL — serviciu perimetru", "rate": 4.0, "basis": "per_linear_meter"},
    {"code": "FACE_VINYL_APPLICATION_LABOR", "label": "Manoperă aplicare folie fețe litere", "rate": 5.0, "basis": "per_square_meter"},
    {"code": "LARGE_FORMAT_PRINT", "label": "Serviciu print autocolant", "rate": 8.5, "basis": "per_square_meter"},
    {"code": "LAMINATION", "label": "Serviciu laminare print", "rate": 5.0, "basis": "per_square_meter"},
    {"code": "LED_ASSEMBLY", "label": "Montaj module LED", "rate": 0.05, "basis": "per_piece"},
    {"code": "ELECTRICAL_WIRING", "label": "Cablaj electric litere", "rate": 2.0, "basis": "per_piece"},
    {"code": "PACKAGING", "label": "Ambalare litere volumetrice", "rate": 10.0, "basis": "per_square_meter"},
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


async def seed_intake_v5_volumetric_letters_pricing() -> dict[str, int]:
    inserted_materials = 0
    updated_materials = 0
    inserted_rates = 0
    updated_rates = 0
    now = datetime.now(timezone.utc)

    async with db_manager.async_session_maker() as session:
        for item in MATERIAL_PRICES:
            row = (await session.execute(
                select(Inventory_materials).where(Inventory_materials.code == item["code"])
            )).scalar_one_or_none()
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
            row.status = "active"
            row.source_name = "owner_seed_intake_v5_volumetric_letters"
            row.source_notes = "Seeded for simplified V5 template pricing; edit in inventory registry for owner prices."
            row.source_checked_at = now

        for item in WORKCENTER_RATES:
            row = (await session.execute(
                select(Workcenter_rates).where(Workcenter_rates.code == item["code"])
            )).scalar_one_or_none()
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
            row.notes = "Seeded for simplified V5 template pricing; edit in workcenter rates registry for owner prices."
            for column, value in _rate_columns(item["rate"], item["basis"]).items():
                setattr(row, column, value)

        await session.commit()

    stats = {
        "inserted_materials": inserted_materials,
        "updated_materials": updated_materials,
        "inserted_rates": inserted_rates,
        "updated_rates": updated_rates,
    }
    logger.info("Seeded Intake V5 volumetric letters pricing: %s", stats)
    return stats


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_intake_v5_volumetric_letters_pricing()
    print(f"[seed_intake_v5_volumetric_letters_pricing] {stats}")


if __name__ == "__main__":
    asyncio.run(_main())
