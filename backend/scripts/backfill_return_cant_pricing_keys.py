from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db_manager
import models  # noqa: F401
from models.inventory_materials import Inventory_materials
from models.workcenter_rates import Workcenter_rates

SCRIPT_NAME = "backfill_return_cant_pricing_keys"
SOURCE_NAME = "return_cant_runtime_backfill_alignment_v1"

TARGET_MATERIAL_ROWS: List[Dict[str, Any]] = [
    {
        "code": "MAT-VOPSEA-RAL-CANT-30MM",
        "name": "Vopsire RAL cant 30 mm - material",
        "unit": "ml",
        "unit_cost": 2.0,
        "currency": "EUR",
        "category": "consumabile",
        "status": "active",
        "source_review_status": "accepted_override",
        "source_notes": "Owner-confirmed return_cant RAL material 30 mm runtime backfill. No legacy row changes.",
    },
    {
        "code": "MAT-VOPSEA-RAL-CANT-60MM",
        "name": "Vopsire RAL cant 60 mm - material",
        "unit": "ml",
        "unit_cost": 2.5,
        "currency": "EUR",
        "category": "consumabile",
        "status": "active",
        "source_review_status": "accepted_override",
        "source_notes": "Owner-confirmed return_cant RAL material 60 mm runtime backfill. No legacy row changes.",
    },
    {
        "code": "MAT-VOPSEA-RAL-CANT-80MM",
        "name": "Vopsire RAL cant 80 mm - material",
        "unit": "ml",
        "unit_cost": 3.0,
        "currency": "EUR",
        "category": "consumabile",
        "status": "active",
        "source_review_status": "accepted_override",
        "source_notes": "Owner-confirmed return_cant RAL material 80 mm runtime backfill. No legacy row changes.",
    },
    {
        "code": "MAT-VOPSEA-RAL-CANT-100MM",
        "name": "Vopsire RAL cant 100 mm - material",
        "unit": "ml",
        "unit_cost": 4.0,
        "currency": "EUR",
        "category": "consumabile",
        "status": "active",
        "source_review_status": "accepted_override",
        "source_notes": "Owner-confirmed return_cant RAL material 100 mm runtime backfill. No legacy row changes.",
    },
]

TARGET_WORKCENTER_ROWS: List[Dict[str, Any]] = [
    {
        "code": "RETURN_CANT_VINYL_APPLICATION_LABOR",
        "label": "Aplicare folie autocolanta pe cant",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 1.0,
        "currency": "EUR",
        "status": "active",
        "is_active": True,
        "notes": "Owner-confirmed return_cant vinyl application labor runtime backfill. No legacy row changes.",
    },
    {
        "code": "RETURN_CANT_RAL_PAINT_LABOR",
        "label": "Manopera vopsit RAL pe cant",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 1.0,
        "currency": "EUR",
        "status": "active",
        "is_active": True,
        "notes": "Owner-confirmed return_cant RAL paint labor runtime backfill. No legacy row changes.",
    },
]


def _float_equal(left: Any, right: Any) -> bool:
    try:
        return abs(float(left) - float(right)) < 1e-9
    except Exception:
        return False


def _material_core_snapshot(row: Inventory_materials) -> Dict[str, Any]:
    return {
        "name": row.name,
        "unit": row.unit,
        "unit_cost": float(row.unit_cost) if row.unit_cost is not None else None,
        "currency": row.currency,
        "status": row.status,
    }


def _workcenter_core_snapshot(row: Workcenter_rates) -> Dict[str, Any]:
    return {
        "label": row.label,
        "rate_basis": row.rate_basis,
        "rate_per_linear_meter": (
            float(row.rate_per_linear_meter)
            if row.rate_per_linear_meter is not None
            else None
        ),
        "currency": row.currency,
        "status": row.status,
        "is_active": bool(row.is_active),
    }


def _material_expected_snapshot(target: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": target["name"],
        "unit": target["unit"],
        "unit_cost": float(target["unit_cost"]),
        "currency": target["currency"],
        "status": target["status"],
    }


def _workcenter_expected_snapshot(target: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "label": target["label"],
        "rate_basis": target["rate_basis"],
        "rate_per_linear_meter": float(target["rate_per_linear_meter"]),
        "currency": target["currency"],
        "status": target["status"],
        "is_active": bool(target["is_active"]),
    }


def _material_matches(row: Inventory_materials, target: Dict[str, Any]) -> bool:
    expected = _material_expected_snapshot(target)
    actual = _material_core_snapshot(row)
    return (
        actual["name"] == expected["name"]
        and actual["unit"] == expected["unit"]
        and _float_equal(actual["unit_cost"], expected["unit_cost"])
        and actual["currency"] == expected["currency"]
        and actual["status"] == expected["status"]
    )


def _workcenter_matches(row: Workcenter_rates, target: Dict[str, Any]) -> bool:
    expected = _workcenter_expected_snapshot(target)
    actual = _workcenter_core_snapshot(row)
    return (
        actual["label"] == expected["label"]
        and actual["rate_basis"] == expected["rate_basis"]
        and _float_equal(actual["rate_per_linear_meter"], expected["rate_per_linear_meter"])
        and actual["currency"] == expected["currency"]
        and actual["status"] == expected["status"]
        and actual["is_active"] == expected["is_active"]
    )


async def backfill_return_cant_pricing_keys(session: AsyncSession) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "inserted": [],
        "already_ok": [],
        "conflicts": [],
        "skipped": [],
    }

    for target in TARGET_MATERIAL_ROWS:
        code = target["code"]
        rows = (
            await session.execute(
                select(Inventory_materials).where(Inventory_materials.code == code)
            )
        ).scalars().all()

        if not rows:
            session.add(
                Inventory_materials(
                    code=code,
                    name=target["name"],
                    category=target["category"],
                    unit=target["unit"],
                    unit_cost=target["unit_cost"],
                    currency=target["currency"],
                    status=target["status"],
                    source_name=SOURCE_NAME,
                    source_notes=target["source_notes"],
                    source_review_status=target["source_review_status"],
                    source_reviewed_by=SCRIPT_NAME,
                )
            )
            report["inserted"].append({"entity": "material", "code": code})
            continue

        if len(rows) > 1:
            report["conflicts"].append(
                {
                    "entity": "material",
                    "code": code,
                    "reason": "multiple_existing_rows",
                    "existing_count": len(rows),
                    "expected": _material_expected_snapshot(target),
                }
            )
            continue

        row = rows[0]
        if _material_matches(row, target):
            report["already_ok"].append({"entity": "material", "code": code})
            continue

        report["conflicts"].append(
            {
                "entity": "material",
                "code": code,
                "reason": "existing_row_differs",
                "existing": _material_core_snapshot(row),
                "expected": _material_expected_snapshot(target),
            }
        )

    for target in TARGET_WORKCENTER_ROWS:
        code = target["code"]
        rows = (
            await session.execute(
                select(Workcenter_rates).where(Workcenter_rates.code == code)
            )
        ).scalars().all()

        if not rows:
            session.add(
                Workcenter_rates(
                    code=code,
                    label=target["label"],
                    rate_per_hour=None,
                    rate_per_linear_meter=target["rate_per_linear_meter"],
                    rate_basis=target["rate_basis"],
                    currency=target["currency"],
                    status=target["status"],
                    is_active=target["is_active"],
                    notes=target["notes"],
                )
            )
            report["inserted"].append({"entity": "workcenter_rate", "code": code})
            continue

        if len(rows) > 1:
            report["conflicts"].append(
                {
                    "entity": "workcenter_rate",
                    "code": code,
                    "reason": "multiple_existing_rows",
                    "existing_count": len(rows),
                    "expected": _workcenter_expected_snapshot(target),
                }
            )
            continue

        row = rows[0]
        if _workcenter_matches(row, target):
            report["already_ok"].append({"entity": "workcenter_rate", "code": code})
            continue

        report["conflicts"].append(
            {
                "entity": "workcenter_rate",
                "code": code,
                "reason": "existing_row_differs",
                "existing": _workcenter_core_snapshot(row),
                "expected": _workcenter_expected_snapshot(target),
            }
        )

    await session.commit()

    report["summary"] = {
        "inserted": len(report["inserted"]),
        "already_ok": len(report["already_ok"]),
        "conflicts": len(report["conflicts"]),
        "skipped": len(report["skipped"]),
    }
    return report


async def _main() -> int:
    await db_manager.init_db()
    async with db_manager.async_session_maker() as session:
        report = await backfill_return_cant_pricing_keys(session)
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 1 if report["summary"]["conflicts"] else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))