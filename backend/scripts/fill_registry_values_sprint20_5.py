"""Sprint #20.5 — Registry Values Fill.

Applies canonical real prices / rates to the Sprint #20 stubs and
transitions all affected rows to `status='active'`.

Source values (provided by CFO, locked for audit):
  WORKCENTER RATES (RON/h):
    CNC_ROUTER      = 110
    PANEL_CUTTING   =  80
    LED_ASSEMBLY    = 110
    ASSEMBLY        = 100
    FINISHING       =  80
    INSTALL_PREP    =  90

  MATERIALS:
    MAT-ACP-3MM              = 75 RON/m²
    MAT-PLEXI-OPAL-3MM       = 75 RON/m²
    MAT-PLEXI-TRANSP-10MM    = 75 RON/m²
    MAT-PLEXI-OPAL-10MM      = 75 RON/m²
    MAT-LED-MODULE           =  1.4 RON/buc
    MAT-LED-PSU-12V          = 60 RON/buc
    MAT-PROFIL-ALU           = 20 RON/ml
    MAT-SURUBURI-GEN         =  0.5 RON/buc
    MAT-ADEZIV-SILICON       = 25 RON/buc
    MAT-CONSUMABILE-MONTAJ   = 20 RON/set

Script contract:
  - Idempotent: re-running on already-active rows is a no-op.
  - NO CostEngine / QuoteOrchestrator / quotes / orders / execution
    code is touched.
  - On completion, prints a machine-readable proof block with:
      * per-row PATCH outcome
      * full GET dump of both registries
      * final invariants: ALL_WORKCENTERS_ACTIVE = N/6,
                          ALL_MATERIALS_ACTIVE  = N/10
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Tuple

from core.database import db_manager
import models  # noqa: F401 - ensure all models are registered
from services.inventory_materials_admin_service import (
    get_inventory_material_by_code,
    list_inventory_materials_admin,
    patch_inventory_material_by_code,
)
from services.workcenter_rates_service import (
    get_workcenter_rate_by_code,
    list_workcenter_rates,
    update_workcenter_rate,
)

logger = logging.getLogger(__name__)

WORKCENTER_RATES: List[Tuple[str, float]] = [
    ("CNC_ROUTER", 110.0),
    ("PANEL_CUTTING", 80.0),
    ("LED_ASSEMBLY", 110.0),
    ("ASSEMBLY", 100.0),
    ("FINISHING", 80.0),
    ("INSTALL_PREP", 90.0),
]

MATERIAL_PRICES: List[Tuple[str, float]] = [
    ("MAT-ACP-3MM", 75.0),
    ("MAT-PLEXI-OPAL-3MM", 75.0),
    ("MAT-PLEXI-TRANSP-10MM", 75.0),
    ("MAT-PLEXI-OPAL-10MM", 75.0),
    ("MAT-LED-MODULE", 1.4),
    ("MAT-LED-PSU-12V", 60.0),
    ("MAT-PROFIL-ALU", 20.0),
    ("MAT-SURUBURI-GEN", 0.5),
    ("MAT-ADEZIV-SILICON", 25.0),
    ("MAT-CONSUMABILE-MONTAJ", 20.0),
]


async def _fill_workcenter_rates() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    async with db_manager.async_session_maker() as session:
        for code, rate in WORKCENTER_RATES:
            existing = await get_workcenter_rate_by_code(session, code)
            if existing is None:
                results.append(
                    {"code": code, "action": "SKIPPED_NOT_FOUND", "target_rate": rate}
                )
                continue
            row = await update_workcenter_rate(
                session,
                code,
                rate_per_hour=rate,
                status="active",
            )
            results.append(
                {
                    "code": code,
                    "action": "PATCHED",
                    "rate_per_hour": row["rate_per_hour"] if row else None,
                    "status": row["status"] if row else None,
                }
            )
    return results


async def _fill_material_prices() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    async with db_manager.async_session_maker() as session:
        for code, price in MATERIAL_PRICES:
            existing = await get_inventory_material_by_code(session, code)
            if existing is None:
                results.append(
                    {"code": code, "action": "SKIPPED_NOT_FOUND", "target_price": price}
                )
                continue
            row = await patch_inventory_material_by_code(
                session,
                code,
                unit_cost=price,
                status="active",
            )
            results.append(
                {
                    "code": code,
                    "action": "PATCHED",
                    "unit_cost": row["unit_cost"] if row else None,
                    "status": row["status"] if row else None,
                }
            )
    return results


async def _dump_registries() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    async with db_manager.async_session_maker() as session:
        wc = await list_workcenter_rates(session)
        mat = await list_inventory_materials_admin(session)
    return wc, mat


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")

    print("=" * 78)
    print("SPRINT #20.5 — REGISTRY VALUES FILL")
    print("=" * 78)

    await db_manager.init_db()

    print("\n[1/3] Patching workcenter_rates …")
    wc_results = await _fill_workcenter_rates()
    for r in wc_results:
        print(f"   {r}")

    print("\n[2/3] Patching inventory_materials …")
    mat_results = await _fill_material_prices()
    for r in mat_results:
        print(f"   {r}")

    print("\n[3/3] GET proof dumps …")
    wc_dump, mat_dump = await _dump_registries()

    wc_target_codes = {c for c, _ in WORKCENTER_RATES}
    mat_target_codes = {c for c, _ in MATERIAL_PRICES}

    wc_active = [r for r in wc_dump if r["code"] in wc_target_codes and r["status"] == "active"]
    mat_active = [r for r in mat_dump if r["code"] in mat_target_codes and r["status"] == "active"]

    print("\n--- GET /api/admin/workcenter-rates (filtered to canonical 6) ---")
    print(
        json.dumps(
            [r for r in wc_dump if r["code"] in wc_target_codes],
            indent=2,
            default=str,
        )
    )

    print("\n--- GET /api/admin/inventory-materials (filtered to canonical 10) ---")
    print(
        json.dumps(
            [r for r in mat_dump if r["code"] in mat_target_codes],
            indent=2,
            default=str,
        )
    )

    print("\n=" * 1 + "=" * 77)
    print("INVARIANT CHECK")
    print("=" * 78)
    print(f"ALL_WORKCENTERS_ACTIVE = {len(wc_active)}/6")
    print(f"ALL_MATERIALS_ACTIVE   = {len(mat_active)}/10")

    ok = len(wc_active) == 6 and len(mat_active) == 10
    verdict = "READY_FOR_TEMPLATE_SEED" if ok else "NOT_READY"
    print(f"VERDICT: {verdict}")
    print("=" * 78)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))