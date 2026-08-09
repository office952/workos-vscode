"""Profitability Actual Material Input — frozen stock-movement provenance for V1.

Derives from StockMovement rows written by MaterialActualsService / inventory deduction.
Uses freeze-on-write valuation only. Never live catalog or commercial selling price.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from services.material_actuals_service import MaterialActualsService

MATERIAL_INPUT_CONTRACT = "profitability_actual_material_input/v1"
MATERIAL_IDENTITY_AUTHORITY = "inventory_materials.id"
QUANTITY_AUTHORITY = "stock_movements.quantity_net_of_returns_and_legacy_reversals"
COST_AUTHORITY = "stock_movements.extended_cost_snapshot"
FREEZE_POINT = "stock_movement_write_time"
VALUATION_METHOD = "inventory_unit_cost_at_movement"


async def build_profitability_actual_material_input(
    db: AsyncSession,
    *,
    order_id: int,
) -> dict[str, Any]:
    """Canonical factual + frozen-cost material input for Profitability.

    Planned BOM / reservation / commercial prices are never sources.
    Empty or incomplete valuation → status incomplete (fail-closed).
    """
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    execution_plan_id = plan.id if plan is not None else None

    computed = await MaterialActualsService(db).compute_material_actuals(order_id)
    raw_lines = list(computed.get("lines") or [])

    # Aggregate by material identity + task + unit (no anonymous combined cost).
    buckets: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in raw_lines:
        key = (
            row.get("material_id"),
            str(row.get("task_id") or ""),
            str(row.get("unit") or ""),
            row.get("currency"),
        )
        sign = int(row.get("quantity_sign") or 1)
        qty = float(row.get("quantity") or 0) * sign
        cost = float(row.get("extended_cost_snapshot") or 0) * sign
        if key not in buckets:
            buckets[key] = {
                "material_id": row.get("material_id"),
                "material_code": row.get("material_code"),
                "material_name": row.get("material_name"),
                "task_id": row.get("task_id"),
                "unit": row.get("unit"),
                "currency": row.get("currency"),
                "quantity": 0.0,
                "total_cost": 0.0,
                "rate_used": row.get("unit_cost_snapshot"),
                "valuation_method": row.get("valuation_method"),
                "valuation_provenance": row.get("valuation_provenance"),
                "movement_ids": [],
            }
        buckets[key]["quantity"] = round(float(buckets[key]["quantity"]) + qty, 4)
        buckets[key]["total_cost"] = round(float(buckets[key]["total_cost"]) + cost, 4)
        buckets[key]["movement_ids"].append(row.get("movement_id"))
        # Prefer issue/scrap rate when present (returns reuse original freeze).
        if sign > 0 and row.get("unit_cost_snapshot") is not None:
            buckets[key]["rate_used"] = row.get("unit_cost_snapshot")

    lines = []
    for bucket in buckets.values():
        qty = float(bucket["quantity"])
        if abs(qty) < 1e-12 and abs(float(bucket["total_cost"])) < 1e-12:
            continue
        rate = bucket.get("rate_used")
        if rate is None and qty != 0:
            rate = round(float(bucket["total_cost"]) / qty, 6)
        lines.append(
            {
                "material_id": bucket["material_id"],
                "material_code": bucket["material_code"],
                "material_name": bucket["material_name"],
                "task_id": bucket["task_id"],
                "quantity": bucket["quantity"],
                "unit": bucket["unit"],
                "rate_used": rate,
                "currency": bucket["currency"],
                "total_cost": bucket["total_cost"],
                "valuation_method": bucket.get("valuation_method") or VALUATION_METHOD,
                "valuation_provenance": bucket.get("valuation_provenance"),
                "movement_ids": bucket["movement_ids"],
                "cost_authority": COST_AUTHORITY,
                "quantity_authority": QUANTITY_AUTHORITY,
            }
        )

    lines.sort(
        key=lambda r: (
            int(r.get("material_id") or 0),
            str(r.get("task_id") or ""),
            str(r.get("unit") or ""),
        )
    )

    if not computed.get("available"):
        return {
            "contract": MATERIAL_INPUT_CONTRACT,
            "status": "incomplete",
            "order_id": order_id,
            "execution_plan_id": execution_plan_id,
            "material_identity_authority": MATERIAL_IDENTITY_AUTHORITY,
            "quantity_authority": QUANTITY_AUTHORITY,
            "cost_authority": COST_AUTHORITY,
            "freeze_point": FREEZE_POINT,
            "reason": computed.get("reason"),
            "lines": lines,
            "totals": {
                "line_count": len(lines),
                "total_material_cost": None,
                "currency": None,
            },
            "planned_bom_included": False,
            "commercial_price_used": False,
            "live_catalog_repriced": False,
            "labor_included": False,
            "machine_run_included": False,
            "write_authority": "material_actuals_service|inventory_deduction_service",
        }

    return {
        "contract": MATERIAL_INPUT_CONTRACT,
        "status": "ok",
        "order_id": order_id,
        "execution_plan_id": execution_plan_id,
        "material_identity_authority": MATERIAL_IDENTITY_AUTHORITY,
        "quantity_authority": QUANTITY_AUTHORITY,
        "cost_authority": COST_AUTHORITY,
        "freeze_point": FREEZE_POINT,
        "reason": None,
        "lines": lines,
        "totals": {
            "line_count": len(lines),
            "total_material_cost": computed.get("value"),
            "currency": computed.get("currency"),
            "consumption_count": computed.get("consumption_count"),
            "return_count": computed.get("return_count"),
            "scrap_count": computed.get("scrap_count"),
            "legacy_reversal_count": computed.get("legacy_reversal_count"),
        },
        "material_cost_status": computed.get("material_cost_status"),
        "material_valuation_status": computed.get("material_valuation_status"),
        "provenance": computed.get("provenance"),
        "planned_bom_included": False,
        "commercial_price_used": False,
        "live_catalog_repriced": False,
        "labor_included": False,
        "machine_run_included": False,
        "write_authority": "material_actuals_service|inventory_deduction_service",
    }


def require_material_input_ok(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("status") != "ok":
        raise HTTPException(
            status_code=422,
            detail={
                "error": payload.get("reason") or "actual_material_input_incomplete",
            },
        )
    return payload
