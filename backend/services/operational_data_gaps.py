"""Operational data-gap summaries for Dashboard honesty notices.

Read-only aggregates — no pricing math, no salary→tariff, no util invention.
Separates: Pricing Registry rates · Cost Intern (HR analytics) · Capacity unknowns.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.cost_engine_config import CostEngineConfigService
from services.pricing_registry_service import PricingRegistryService


async def build_operational_data_gaps(
    db: AsyncSession,
    *,
    calendar_shift_util_available: bool = False,
) -> dict[str, Any]:
    """Build structured dataGaps + operator-facing notice strings."""
    registry = await PricingRegistryService(db).build_registry()
    summary = registry.get("summary") or {}
    items = list(registry.get("items") or [])

    missing_items = [i for i in items if i.get("status") == "missing_price"]
    missing_materials = [
        i for i in missing_items if i.get("pricing_kind") == "material"
    ]
    missing_rates = [
        i for i in missing_items if i.get("pricing_kind") == "operation_rate"
    ]

    def _codes(rows: list[dict[str, Any]], limit: int = 12) -> list[str]:
        out: list[str] = []
        for row in rows[:limit]:
            code = str(row.get("pricing_code") or "").strip()
            if code:
                out.append(code)
        return out

    cost_cfg = await CostEngineConfigService(db).compute_base_config()
    warnings = list(cost_cfg.get("warnings") or [])
    employee_invalid = [w for w in warnings if str(w).startswith("employee_invalid:")]
    cost_valid = bool(cost_cfg.get("valid"))

    missing_price_count = int(summary.get("missing_price") or len(missing_items) or 0)
    pricing_owner_needed = missing_price_count > 0
    cost_owner_needed = (not cost_valid) or bool(employee_invalid)
    capacity_unknown = not calendar_shift_util_available

    pricing_notice = (
        f"Pricing Registry: {missing_price_count} rate/price lipsă "
        f"({len(missing_materials)} materiale, {len(missing_rates)} operații/WC) — "
        "Owner data needed; fără reprice retroactiv, fără amestec comercial↔intern."
        if pricing_owner_needed
        else "Pricing Registry: fără missing_price pe itemele active din registry."
    )
    cost_notice = (
        f"Cost Intern (HR analytics/profitability — NU tarif client): "
        f"{len(employee_invalid)} angajați productivi incompleți "
        f"(cost_lunar_firma / ore_productive_luna); base-config valid={cost_valid}."
        if cost_owner_needed
        else "Cost Intern: base-config valid pentru angajați productivi (analytics only)."
    )
    capacity_notice = (
        "Capacitate: util calendar/shift necunoscut — afișăm load planificat 0–100; "
        "Utilaje fără semnal job rămân GAP (nu tarif comercial)."
        if capacity_unknown
        else "Capacitate: semnal calendar/shift disponibil."
    )

    return {
        "pricing": {
            "domain": "pricing_registry",
            "missingPriceCount": missing_price_count,
            "missingMaterialCount": len(missing_materials),
            "missingOperationRateCount": len(missing_rates),
            "ownerDataNeeded": pricing_owner_needed,
            "sampleCodes": _codes(missing_items),
            "boundary": (
                "Material cost ≠ commercial markup ≠ internal op rate. "
                "Dashboard does not invent client tariffs."
            ),
            "notice": pricing_notice,
        },
        "costIntern": {
            "domain": "hr_internal_cost",
            "valid": cost_valid,
            "incompleteEmployeeCount": len(employee_invalid),
            "warnings": warnings[:20],
            "ownerDataNeeded": cost_owner_needed,
            "boundary": (
                "Employee cost = analytics / profitability only — NEVER client price."
            ),
            "notice": cost_notice,
        },
        "capacity": {
            "domain": "capacity_feasibility",
            "calendarShiftUtilAvailable": calendar_shift_util_available,
            "unknown": capacity_unknown,
            "ownerDataNeeded": capacity_unknown,
            "boundary": (
                "Capacity / planned-load / machine util ≠ commercial tariff."
            ),
            "notice": capacity_notice,
        },
    }


def data_gap_notices(data_gaps: dict[str, Any]) -> list[str]:
    """Flatten gap notices for operationalTruth.notices (pricing/cost/capacity first)."""
    notices: list[str] = []
    for key in ("pricing", "costIntern", "capacity"):
        block = data_gaps.get(key) or {}
        notice = block.get("notice")
        if notice:
            notices.append(str(notice))
    return notices
