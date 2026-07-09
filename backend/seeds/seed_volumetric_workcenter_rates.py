"""Product 001 — TPL-VOLUMETRIC-LETTERS operation/service workcenter rates.

Owner-provided unit-based labor (EUR, excluding TVA) and idempotent
template patch for volumetric letter operations.

No prices in CostEngine — rates live in workcenter_rates registry only.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, TypedDict

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.product_templates import Product_templates
from models.workcenter_rates import Workcenter_rates
from seeds.seed_build4_templates import (
    _flatten_materials,
    _flatten_operations,
    _volumetric_letters_components,
)

logger = logging.getLogger(__name__)

TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"

RETURN_PROFILE_MACHINE_FORMING_CODE = "RETURN_PROFILE_MACHINE_FORMING"
RETURN_PROFILE_FACE_BONDING_CODE = "RETURN_PROFILE_FACE_BONDING"
RETURN_CANT_VINYL_APPLICATION_LABOR_CODE = "RETURN_CANT_VINYL_APPLICATION_LABOR"
RETURN_CANT_RAL_PAINT_LABOR_CODE = "RETURN_CANT_RAL_PAINT_LABOR"

TVA_RATE_NOTE = (
    "Owner-defined quote pricing rate. Stored excluding TVA; "
    "TVA configured separately."
)


class _WorkcenterRow(TypedDict):
    code: str
    label: str
    rate_basis: str
    rate_per_linear_meter: float
    currency: str
    status: str
    notes: str


# Owner-provided service rates — purchase/labor, no markup in registry rate.
OWNER_VOLUMETRIC_LABOR_WORKCENTERS: List[_WorkcenterRow] = [
    {
        "code": RETURN_PROFILE_MACHINE_FORMING_CODE,
        "label": "Modelare cant profil litere — utilaj",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 5.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-provided service rate: utilaj modelare cant = 5 EUR/ml "
            "(purchase/labor, no commercial markup). "
            "TPL-VOLUMETRIC-LETTERS operation side_forming; quantity from letter_perimeter_m. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": RETURN_PROFILE_FACE_BONDING_CODE,
        "label": "Lipire cant profil pe față litere",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 5.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-provided service rate: lipire cant pe față = 5 EUR/ml "
            "(purchase/labor, no commercial markup). "
            "TPL-VOLUMETRIC-LETTERS operation return_face_bonding; quantity from total graphic perimeter / return_material_perimeter_ml. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "PREPRESS",
        "label": "Pregătire vector / prepress litere",
        "rate_basis": "per_piece",
        "rate_per_linear_meter": 2.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-defined: 2 EUR/letter (excluding TVA). "
            "TPL-VOLUMETRIC-LETTERS operation vector_prep; quantity from letter_count. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "CNC_ROUTER",
        "label": "CNC router — tăiere/debitare",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 1.5,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-defined: 1.5 EUR/ml/pass (excluding TVA). "
            "Quantity = letter_perimeter_m × pass_count from formula_params. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "WC_METAL_FAB",
        "label": "Servicii debitare metale — lăcătușerie",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 1.5,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-defined: 1.5 EUR/ml pentru debitare și pregătire bare metalice premontaj. "
            "Zona de lucru Utilaje: WC_METAL_FAB. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "LARGE_FORMAT_PRINT",
        "label": "Serviciu print autocolant",
        "rate_basis": "per_square_meter",
        "rate_per_linear_meter": 8.5,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-confirmed: serviciu print = 8.5 EUR/mp excluding TVA. "
            "Material MAT-VINYL-PRINT remains separate at 1.5 EUR/mp. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "LAMINATION",
        "label": "Serviciu laminare print",
        "rate_basis": "per_square_meter",
        "rate_per_linear_meter": 5.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-confirmed: laminare print = 5 EUR/mp excluding TVA. "
            "Used when printed/laminated vinyl finish is selected. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "LED_ASSEMBLY",
        "label": "Montaj module LED",
        "rate_basis": "per_piece",
        "rate_per_linear_meter": 0.05,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner reference 0.20 RON/module, manually converted at 5.2 RON/EUR "
            "and commercially rounded to 0.05 EUR/module. Not live FX. "
            "TPL-VOLUMETRIC-LETTERS operation led_install_letters; quantity from led_module_count. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "ELECTRICAL_WIRING",
        "label": "Cablaj electric litere",
        "rate_basis": "per_piece",
        "rate_per_linear_meter": 2.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-defined: 2 EUR/letter (excluding TVA). "
            "TPL-VOLUMETRIC-LETTERS operation electrical_letters; quantity from letter_count. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "PAINTING",
        "label": "Vopsire RAL — serviciu perimetru",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 4.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-defined: 4 EUR/ml perimeter (excluding TVA). "
            "Material MAT-VOPSEA-RAL remains separate consumable. "
            "TPL-VOLUMETRIC-LETTERS operation painting; quantity from letter_perimeter_m. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": RETURN_CANT_RAL_PAINT_LABOR_CODE,
        "label": "Manopera vopsit RAL pe cant",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 1.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-confirmed: return_cant RAL paint labor = 1 EUR/ml excluding TVA. "
            "Dedicated return_cant paint_application labor row; do not replace with generic PAINTING. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "VINYL_APPLICATION",
        "label": "Aplicare autocolant / Oracal (legacy)",
        "rate_basis": "per_square_meter",
        "rate_per_linear_meter": 3.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Legacy rate — superseded by FACE_VINYL_APPLICATION_LABOR for TPL-VOLUMETRIC-LETTERS "
            "face vinyl labor (5 EUR/mp). Retained for registry compatibility."
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "FACE_VINYL_APPLICATION_LABOR",
        "label": "Manoperă aplicare folie fețe litere",
        "rate_basis": "per_square_meter",
        "rate_per_linear_meter": 5.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-confirmed: 5 EUR/mp excluding TVA for face vinyl application labor. "
            "Quantity from face_vinyl_used_sqm (nesting preferred). "
            "Material Oracal/print remains separate."
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": RETURN_CANT_VINYL_APPLICATION_LABOR_CODE,
        "label": "Aplicare folie autocolanta pe cant",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 1.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-confirmed: return_cant vinyl application labor = 1 EUR/ml excluding TVA. "
            "Dedicated return_cant vinyl_application labor row; do not replace with FACE_VINYL_APPLICATION_LABOR or VINYL_APPLICATION. "
            + TVA_RATE_NOTE
        ),
    },
    {
        "code": "PACKAGING",
        "label": "Ambalare litere volumetrice",
        "rate_basis": "per_square_meter",
        "rate_per_linear_meter": 10.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-defined: 10 EUR/mp (excluding TVA). "
            "TPL-VOLUMETRIC-LETTERS operation packaging_letters; quantity from letter_face_area_m2. "
            + TVA_RATE_NOTE
        ),
    },
]


def _labor_row_matches(existing: Dict[str, Any], row: _WorkcenterRow) -> bool:
    return (
        str(existing.get("status") or "") == row["status"]
        and str(existing.get("rate_basis") or "") == row["rate_basis"]
        and float(existing.get("rate_per_linear_meter") or 0) == row["rate_per_linear_meter"]
        and str(existing.get("currency") or "").upper() == row["currency"].upper()
    )


async def seed_volumetric_workcenter_rates() -> Dict[str, Any]:
    """Upsert volumetric labor workcenters. Idempotent."""
    results: List[Dict[str, Any]] = []
    inserted = 0
    patched = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        for row in OWNER_VOLUMETRIC_LABOR_WORKCENTERS:
            code = row["code"]
            existing = (
                await session.execute(
                    select(Workcenter_rates).where(Workcenter_rates.code == code)
                )
            ).scalar_one_or_none()

            if existing is None:
                session.add(
                    Workcenter_rates(
                        code=code,
                        label=row["label"],
                        rate_per_hour=None,
                        rate_per_linear_meter=row["rate_per_linear_meter"],
                        rate_basis=row["rate_basis"],
                        currency=row["currency"],
                        status=row["status"],
                        is_active=row["status"] == "active",
                        notes=row["notes"],
                    )
                )
                inserted += 1
                results.append({"code": code, "action": "INSERTED"})
                continue

            from services.workcenter_rates_service import _row_to_dict

            if _labor_row_matches(_row_to_dict(existing), row):
                skipped += 1
                results.append({"code": code, "action": "SKIPPED_ALREADY_APPLIED"})
                continue

            existing.label = row["label"]
            existing.rate_per_hour = None
            existing.rate_per_linear_meter = row["rate_per_linear_meter"]
            existing.rate_basis = row["rate_basis"]
            existing.currency = row["currency"]
            existing.status = row["status"]
            existing.is_active = row["status"] == "active"
            existing.notes = row["notes"]
            patched += 1
            results.append({"code": code, "action": "PATCHED"})

        await session.commit()

    logger.info(
        "Volumetric labor workcenters: inserted=%d patched=%d skipped=%d",
        inserted,
        patched,
        skipped,
    )
    return {
        "inserted": inserted,
        "patched": patched,
        "skipped": skipped,
        "results": results,
    }


async def patch_tpl_volumetric_letters_template() -> Dict[str, Any]:
    """Refresh TPL-VOLUMETRIC-LETTERS components_json from canonical seed fn."""
    components = _volumetric_letters_components()
    ops = _flatten_operations(components)
    mats = _flatten_materials(components)
    payload = json.dumps(components, ensure_ascii=False)

    async with db_manager.async_session_maker() as session:
        row = (
            await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == TEMPLATE_CODE
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return {"template_code": TEMPLATE_CODE, "action": "SKIPPED_NOT_FOUND"}

        if row.components_json == payload:
            return {"template_code": TEMPLATE_CODE, "action": "SKIPPED_UNCHANGED"}

        row.components_json = payload
        row.operations_json = json.dumps(ops, ensure_ascii=False)
        row.required_materials_json = json.dumps(mats, ensure_ascii=False)
        await session.commit()
        return {"template_code": TEMPLATE_CODE, "action": "PATCHED"}


async def seed_volumetric_operations_and_rates() -> Dict[str, Any]:
    wc = await seed_volumetric_workcenter_rates()
    tpl = await patch_tpl_volumetric_letters_template()
    return {"workcenters": wc, "template": tpl}
