"""Owner-confirmed ACM/Bond panel purchase cost for preliminary costing."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, TypedDict

from core.database import db_manager
from seeds.material_canonical_naming import canonical_name_for_code, source_notes_for_code
from services.inventory_materials_admin_service import (
    get_inventory_material_by_code,
    patch_inventory_material_by_code,
)

OWNER_CONFIRMED_VALID_FROM = datetime(2026, 6, 4, tzinfo=timezone.utc)
OWNER_CONFIRMED_VAT_PERCENT = 19.0
CHANGE_REASON = "ACM/Bond panel owner-confirmed purchase cost"
SOURCE_NAME = "owner_confirmed_acm_bond_panel"
SOURCE_REVIEWED_BY = "seed_acm_owner_confirmed_prices"


class _PriceRow(TypedDict, total=False):
    code: str
    unit_cost: float
    currency: str
    name: str
    source_notes: str


OWNER_CONFIRMED_ACM_PRICES: List[_PriceRow] = [
    {
        "code": "MAT-SURUBURI-GEN",
        "unit_cost": 5.0,
        "currency": "EUR",
        "name": canonical_name_for_code("MAT-SURUBURI-GEN", "Suruburi / prinderi generale"),
        "source_notes": source_notes_for_code(
            "MAT-SURUBURI-GEN",
            (
                "Owner-confirmed: 5 EUR / standard assembly set / ACM boxed product. "
                "Self-drilling screws, rivets, washers — not wall anchors or site hardware."
            ),
        ),
    },
    {
        "code": "MAT-ACM-BOND-3MM",
        "unit_cost": 15.0,
        "currency": "EUR",
        "name": canonical_name_for_code("MAT-ACM-BOND-3MM", "Panou compozit aluminiu (ACM/ACP) 3 mm"),
        "source_notes": source_notes_for_code(
            "MAT-ACM-BOND-3MM",
            (
                "Owner-confirmed purchase: 15 EUR/mp (purchase, no markup). "
                "Support/premounting/background panel — not letter Forex backing."
            ),
        ),
    },
]

NEEDS_REVIEW_ACM_PRICES: List[_PriceRow] = [
    {
        "code": "MAT-ACM-BOND-4MM",
        "unit_cost": 15.0,
        "currency": "EUR",
        "name": canonical_name_for_code("MAT-ACM-BOND-4MM", "Panou compozit aluminiu (ACM/ACP) 4 mm"),
        "source_notes": source_notes_for_code(
            "MAT-ACM-BOND-4MM",
            "Preliminary placeholder — needs_owner_review until owner confirms 4 mm price.",
        ),
    },
]


def _already_applied(existing: Dict[str, Any], row: _PriceRow) -> bool:
    if str(existing.get("status") or "") != "active":
        return False
    if existing.get("unit_cost") != row["unit_cost"]:
        return False
    if str(existing.get("currency") or "").upper() != str(row["currency"]).upper():
        return False
    if str(existing.get("source_review_status") or "") != "accepted_override":
        return False
    return True


def _estimated_already_applied(existing: Dict[str, Any], row: _PriceRow) -> bool:
    if str(existing.get("status") or "") != "active":
        return False
    if existing.get("unit_cost") != row["unit_cost"]:
        return False
    if str(existing.get("source_review_status") or "") != "needs_review":
        return False
    return True


async def _apply_owner_rows(
    session: Any,
    rows: List[_PriceRow],
    *,
    results: List[Dict[str, Any]],
) -> tuple[int, int, int]:
    patched = skipped = not_found = 0
    for row in rows:
        code = row["code"]
        existing = await get_inventory_material_by_code(session, code)
        if existing is None:
            not_found += 1
            results.append({"code": code, "action": "SKIPPED_NOT_FOUND"})
            continue
        if _already_applied(existing, row):
            skipped += 1
            results.append({"code": code, "action": "SKIPPED_ALREADY_APPLIED"})
            continue
        patch_kwargs: Dict[str, Any] = {
            "unit_cost": row["unit_cost"],
            "currency": row["currency"],
            "vat_percent": OWNER_CONFIRMED_VAT_PERCENT,
            "valid_from": OWNER_CONFIRMED_VALID_FROM,
            "status": "active",
            "source_name": SOURCE_NAME,
            "source_checked_at": OWNER_CONFIRMED_VALID_FROM,
            "source_notes": row["source_notes"],
            "source_review_status": "accepted_override",
            "source_reviewed_at": OWNER_CONFIRMED_VALID_FROM,
            "source_reviewed_by": SOURCE_REVIEWED_BY,
            "change_reason": CHANGE_REASON,
            "changed_by": SOURCE_REVIEWED_BY,
            "snapshot_source": "seed_acm_owner_confirmed_prices",
        }
        if row.get("name"):
            patch_kwargs["name"] = row["name"]
        await patch_inventory_material_by_code(session, code, **patch_kwargs)
        patched += 1
        results.append({"code": code, "action": "PATCHED"})
    return patched, skipped, not_found


async def _apply_estimated_rows(
    session: Any,
    rows: List[_PriceRow],
    *,
    results: List[Dict[str, Any]],
) -> tuple[int, int, int]:
    patched = skipped = not_found = 0
    for row in rows:
        code = row["code"]
        existing = await get_inventory_material_by_code(session, code)
        if existing is None:
            not_found += 1
            results.append({"code": code, "action": "SKIPPED_NOT_FOUND"})
            continue
        if _estimated_already_applied(existing, row):
            skipped += 1
            results.append({"code": code, "action": "SKIPPED_ALREADY_APPLIED_ESTIMATED"})
            continue
        patch_kwargs: Dict[str, Any] = {
            "unit_cost": row["unit_cost"],
            "currency": row["currency"],
            "vat_percent": OWNER_CONFIRMED_VAT_PERCENT,
            "valid_from": OWNER_CONFIRMED_VALID_FROM,
            "status": "active",
            "source_name": SOURCE_NAME,
            "source_checked_at": OWNER_CONFIRMED_VALID_FROM,
            "source_notes": row["source_notes"],
            "source_review_status": "needs_review",
            "source_reviewed_at": OWNER_CONFIRMED_VALID_FROM,
            "source_reviewed_by": SOURCE_REVIEWED_BY,
            "change_reason": CHANGE_REASON,
            "changed_by": SOURCE_REVIEWED_BY,
            "snapshot_source": "seed_acm_owner_confirmed_prices",
        }
        if row.get("name"):
            patch_kwargs["name"] = row["name"]
        await patch_inventory_material_by_code(session, code, **patch_kwargs)
        patched += 1
        results.append({"code": code, "action": "PATCHED_ESTIMATED"})
    return patched, skipped, not_found


async def seed_acm_owner_confirmed_prices() -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    patched = skipped = not_found = 0

    async with db_manager.async_session_maker() as session:
        p, s, n = await _apply_owner_rows(
            session, OWNER_CONFIRMED_ACM_PRICES, results=results
        )
        patched += p
        skipped += s
        not_found += n

        p, s, n = await _apply_estimated_rows(
            session, NEEDS_REVIEW_ACM_PRICES, results=results
        )
        patched += p
        skipped += s
        not_found += n

        await session.commit()

    return {
        "patched": patched,
        "skipped": skipped,
        "not_found": not_found,
        "results": results,
    }
