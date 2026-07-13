"""Owner-confirmed commercial rates for TPL-ACM-BOXED-MOUNTING-SUPPORT_v1.

Commercial basis is EUR/lm and EUR/mp (not RON/h workcenter hourly for quote/CPP).
Machine minutes remain internal/EIC capacity hints only.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, TypedDict

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.workcenter_rates import Workcenter_rates

logger = logging.getLogger(__name__)

CHANGE_REASON = "ACM boxed mounting owner-confirmed commercial rates (2026-07-13)"


class _WorkcenterRow(TypedDict):
    code: str
    label: str
    rate_basis: str
    rate_per_linear_meter: float
    currency: str
    status: str
    notes: str


OWNER_ACM_BOXED_WORKCENTERS: List[_WorkcenterRow] = [
    {
        "code": "ACM_PANEL_CUTTING",
        "label": "Debitare panou ACM casetat",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 1.5,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-confirmed: 1.5 EUR/lm canonical cutting-path length (panel_perimeter_m). "
            "Machine time is internal/EIC only — not commercial hourly pricing."
        ),
    },
    {
        "code": "ACM_V_GROOVE",
        "label": "Frezare V-groove ACM casetat",
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 3.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-confirmed: 3 EUR/lm canonical V-groove/fold-line length (fold_length_m). "
            "fold_length_m × 2.5 min/m remains internal capacity/EIC only."
        ),
    },
    {
        "code": "ACM_BOXED_ASSEMBLY",
        "label": "Asamblare suport ACM casetat",
        "rate_basis": "per_square_meter",
        "rate_per_linear_meter": 15.0,
        "currency": "EUR",
        "status": "active",
        "notes": (
            "Owner-confirmed: 15 EUR/mp visible boxed-product area; minimum 20 EUR/product "
            "applied in CPP. One commercial assembly line V1 — fold/mount tasks remain internal."
        ),
    },
]


def _row_matches(existing: Dict[str, Any], row: _WorkcenterRow) -> bool:
    return (
        str(existing.get("status") or "") == row["status"]
        and str(existing.get("rate_basis") or "") == row["rate_basis"]
        and float(existing.get("rate_per_linear_meter") or 0) == row["rate_per_linear_meter"]
        and str(existing.get("currency") or "").upper() == row["currency"].upper()
    )


async def seed_acm_boxed_mounting_owner_rates() -> Dict[str, Any]:
    from services.workcenter_rates_service import _row_to_dict

    results: List[Dict[str, Any]] = []
    inserted = patched = skipped = 0

    async with db_manager.async_session_maker() as session:
        for row in OWNER_ACM_BOXED_WORKCENTERS:
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

            if _row_matches(_row_to_dict(existing), row):
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

    stats = {
        "inserted": inserted,
        "patched": patched,
        "skipped": skipped,
        "results": results,
        "change_reason": CHANGE_REASON,
    }
    logger.info("seed_acm_boxed_mounting_owner_rates: %s", stats)
    return stats
