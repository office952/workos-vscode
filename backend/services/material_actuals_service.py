"""Canonical material actuals — real movement + frozen valuation only.

planned BOM ≠ actual · reservation ≠ actual · commercial price forbidden.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory_materials import Inventory_materials
from models.inventory_material_price_history import Inventory_material_price_history
from models.stock_movements import StockMovement
from services.closed_job_mutation_guard import assert_execution_open_for_material_mutation

MOVEMENT_CONSUMPTION = "consumption"
MOVEMENT_RETURN = "return"
MOVEMENT_SCRAP = "scrap"
MOVEMENT_ADJUSTMENT = "adjustment"

REASON_MATERIAL_VALUATION_UNAVAILABLE = "material_valuation_unavailable"
REASON_MATERIAL_MOVEMENT_MISSING = "material_movement_missing"
REASON_RETURN_UNRESOLVED = "material_return_unresolved"
REASON_UNIT_MISMATCH = "material_unit_mismatch"
REASON_UNAUTHORIZED = "material_actual_unauthorized"
REASON_WRONG_JOB = "material_movement_wrong_job"
REASON_PLANNED_BOM_REJECTED = "planned_bom_not_actual"
REASON_RESERVATION_REJECTED = "reservation_not_actual"
REASON_IDEMPOTENT_REPLAY = "material_actual_idempotent_replay"
REASON_UNRELATED_RETURN = "material_return_unrelated"

VALUATION_METHOD = "inventory_unit_cost_at_movement"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MaterialActualsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _load_material(self, material_id: int) -> Inventory_materials:
        row = (
            await self.db.execute(
                select(Inventory_materials).where(Inventory_materials.id == material_id)
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail={"error": "material_not_found"})
        return row

    async def _freeze_valuation(self, material_id: int) -> dict[str, Any]:
        price_history = (
            await self.db.execute(
                select(Inventory_material_price_history)
                .where(Inventory_material_price_history.material_id == material_id)
                .order_by(Inventory_material_price_history.changed_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        material = await self._load_material(material_id)
        unit_cost = (
            price_history.unit_cost
            if price_history and price_history.unit_cost is not None
            else material.unit_cost
        )
        currency = (
            price_history.currency
            if price_history and price_history.currency
            else material.currency
        )
        if unit_cost is None or not currency:
            return {
                "available": False,
                "unit_cost_snapshot": None,
                "currency_snapshot": None,
                "valuation_method": None,
                "valuation_provenance": None,
                "extended_cost_snapshot": None,
                "price_history_id_snapshot": None,
                "reason": REASON_MATERIAL_VALUATION_UNAVAILABLE,
            }
        provenance = (
            "inventory_material_price_history"
            if price_history and price_history.unit_cost is not None
            else "inventory_materials.unit_cost"
        )
        return {
            "available": True,
            "unit_cost_snapshot": float(unit_cost),
            "currency_snapshot": str(currency),
            "valuation_method": VALUATION_METHOD,
            "valuation_provenance": provenance,
            "price_history_id_snapshot": (
                price_history.id if price_history and price_history.unit_cost is not None else None
            ),
            "reason": None,
        }

    async def _get_by_idempotency(self, key: str) -> StockMovement | None:
        return (
            await self.db.execute(
                select(StockMovement).where(StockMovement.idempotency_key == key)
            )
        ).scalar_one_or_none()

    def _reject_non_actual_source(self, source_type: str) -> None:
        st = (source_type or "").strip().lower()
        if st in {"planned_bom", "bom", "plan", "product_aggregate", "quote"}:
            raise HTTPException(status_code=422, detail={"error": REASON_PLANNED_BOM_REJECTED})
        if st in {"reservation", "reserve", "soft_reserve"}:
            raise HTTPException(status_code=422, detail={"error": REASON_RESERVATION_REJECTED})

    async def record_issue(
        self,
        *,
        order_id: int,
        material_id: int,
        quantity: float,
        unit: str,
        actor_id: str,
        idempotency_key: str,
        task_id: str | None = None,
        source_type: str = "manual_material_actual",
        source_id: int = 0,
        reason: str | None = None,
    ) -> dict[str, Any]:
        self._reject_non_actual_source(source_type)
        if quantity <= 0:
            raise HTTPException(status_code=422, detail={"error": "quantity_must_be_positive"})
        existing = await self._get_by_idempotency(idempotency_key)
        if existing is not None:
            return {"status": REASON_IDEMPOTENT_REPLAY, "movement_id": existing.id}
        await assert_execution_open_for_material_mutation(self.db, order_id)

        material = await self._load_material(material_id)
        mat_unit = str(getattr(material, "unit", "") or "").strip()
        if mat_unit and unit.strip() and mat_unit.lower() != unit.strip().lower():
            raise HTTPException(status_code=422, detail={"error": REASON_UNIT_MISMATCH})

        valuation = await self._freeze_valuation(material_id)
        old_stock = float(material.stock_current or 0)
        if quantity > old_stock:
            raise HTTPException(status_code=422, detail={"error": "insufficient_stock"})
        new_stock = round(old_stock - quantity, 4)
        material.stock_current = new_stock

        extended = (
            round(quantity * float(valuation["unit_cost_snapshot"]), 4)
            if valuation["available"]
            else None
        )
        movement = StockMovement(
            material_id=material_id,
            source_type=source_type,
            source_id=source_id,
            order_id=order_id,
            task_id=task_id,
            quantity=quantity,
            unit=unit,
            movement_type=MOVEMENT_CONSUMPTION,
            old_stock=old_stock,
            new_stock=new_stock,
            performed_by=actor_id,
            performed_at=_utc_now(),
            reason=reason or "Canonical material issue/consume",
            idempotency_key=idempotency_key,
            unit_cost_snapshot=valuation["unit_cost_snapshot"],
            currency_snapshot=valuation["currency_snapshot"],
            valuation_method=valuation["valuation_method"],
            valuation_provenance=valuation["valuation_provenance"],
            extended_cost_snapshot=extended,
            price_history_id_snapshot=valuation["price_history_id_snapshot"],
        )
        self.db.add(movement)
        await self.db.flush()
        return {
            "status": "recorded",
            "movement_id": movement.id,
            "material_cost_status": "complete" if valuation["available"] else "incomplete",
            "reason": valuation.get("reason"),
        }

    async def record_return(
        self,
        *,
        order_id: int,
        reverses_movement_id: int,
        quantity: float,
        actor_id: str,
        idempotency_key: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._get_by_idempotency(idempotency_key)
        if existing is not None:
            return {"status": REASON_IDEMPOTENT_REPLAY, "movement_id": existing.id}
        await assert_execution_open_for_material_mutation(self.db, order_id)

        original = (
            await self.db.execute(
                select(StockMovement).where(StockMovement.id == reverses_movement_id)
            )
        ).scalar_one_or_none()
        if original is None or original.movement_type != MOVEMENT_CONSUMPTION:
            raise HTTPException(status_code=422, detail={"error": REASON_UNRELATED_RETURN})
        if int(original.order_id or 0) != int(order_id):
            raise HTTPException(status_code=422, detail={"error": REASON_WRONG_JOB})
        if original.extended_cost_snapshot is None or original.unit_cost_snapshot is None:
            raise HTTPException(
                status_code=422, detail={"error": REASON_MATERIAL_VALUATION_UNAVAILABLE}
            )
        if quantity <= 0 or quantity > float(original.quantity):
            raise HTTPException(status_code=422, detail={"error": "return_quantity_invalid"})

        material = await self._load_material(int(original.material_id))
        old_stock = float(material.stock_current or 0)
        new_stock = round(old_stock + quantity, 4)
        material.stock_current = new_stock

        ratio = quantity / float(original.quantity)
        extended = round(float(original.extended_cost_snapshot) * ratio, 4)
        movement = StockMovement(
            material_id=int(original.material_id),
            source_type="material_return",
            source_id=int(original.id),
            order_id=order_id,
            task_id=original.task_id,
            quantity=quantity,
            unit=original.unit,
            movement_type=MOVEMENT_RETURN,
            old_stock=old_stock,
            new_stock=new_stock,
            performed_by=actor_id,
            performed_at=_utc_now(),
            reason=reason or "Return against original consumption",
            idempotency_key=idempotency_key,
            unit_cost_snapshot=float(original.unit_cost_snapshot),
            currency_snapshot=original.currency_snapshot,
            valuation_method=original.valuation_method,
            valuation_provenance="reversal_of_frozen_consumption",
            extended_cost_snapshot=extended,
            price_history_id_snapshot=original.price_history_id_snapshot,
            reverses_movement_id=int(original.id),
        )
        self.db.add(movement)
        await self.db.flush()
        return {"status": "recorded", "movement_id": movement.id}

    async def record_scrap(
        self,
        *,
        order_id: int,
        material_id: int,
        quantity: float,
        unit: str,
        actor_id: str,
        idempotency_key: str,
        scrap_reason: str,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        if not (scrap_reason or "").strip():
            raise HTTPException(status_code=422, detail={"error": "scrap_reason_required"})
        if quantity <= 0:
            raise HTTPException(status_code=422, detail={"error": "quantity_must_be_positive"})
        existing = await self._get_by_idempotency(idempotency_key)
        if existing is not None:
            return {"status": REASON_IDEMPOTENT_REPLAY, "movement_id": existing.id}
        await assert_execution_open_for_material_mutation(self.db, order_id)

        material = await self._load_material(material_id)
        valuation = await self._freeze_valuation(material_id)
        old_stock = float(material.stock_current or 0)
        if quantity > old_stock:
            raise HTTPException(status_code=422, detail={"error": "insufficient_stock"})
        new_stock = round(old_stock - quantity, 4)
        material.stock_current = new_stock
        extended = (
            round(quantity * float(valuation["unit_cost_snapshot"]), 4)
            if valuation["available"]
            else None
        )
        movement = StockMovement(
            material_id=material_id,
            source_type="material_scrap",
            source_id=0,
            order_id=order_id,
            task_id=task_id,
            quantity=quantity,
            unit=unit,
            movement_type=MOVEMENT_SCRAP,
            old_stock=old_stock,
            new_stock=new_stock,
            performed_by=actor_id,
            performed_at=_utc_now(),
            reason=scrap_reason.strip(),
            idempotency_key=idempotency_key,
            unit_cost_snapshot=valuation["unit_cost_snapshot"],
            currency_snapshot=valuation["currency_snapshot"],
            valuation_method=valuation["valuation_method"],
            valuation_provenance=valuation["valuation_provenance"],
            extended_cost_snapshot=extended,
            price_history_id_snapshot=valuation["price_history_id_snapshot"],
        )
        self.db.add(movement)
        await self.db.flush()
        return {
            "status": "recorded",
            "movement_id": movement.id,
            "material_cost_status": "complete" if valuation["available"] else "incomplete",
            "distinct_from_consumption": True,
        }

    async def material_actual_basis(self, order_id: int) -> dict[str, Any]:
        movements = list(
            (
                await self.db.execute(
                    select(StockMovement).where(StockMovement.order_id == order_id)
                )
            ).scalars().all()
        )
        consumptions = [m for m in movements if m.movement_type == MOVEMENT_CONSUMPTION]
        returns = [m for m in movements if m.movement_type == MOVEMENT_RETURN]
        scraps = [m for m in movements if m.movement_type == MOVEMENT_SCRAP]

        if not consumptions and not scraps:
            return {
                "available": False,
                "value": None,
                "material_cost_status": "incomplete",
                "material_valuation_status": "unavailable",
                "reason": REASON_MATERIAL_MOVEMENT_MISSING,
            }

        cost_rows = consumptions + scraps
        if any(m.extended_cost_snapshot is None for m in cost_rows):
            return {
                "available": False,
                "value": None,
                "material_cost_status": "incomplete",
                "material_valuation_status": "unavailable",
                "reason": REASON_MATERIAL_VALUATION_UNAVAILABLE,
            }

        for ret in returns:
            if ret.reverses_movement_id is None:
                return {
                    "available": False,
                    "value": None,
                    "material_cost_status": "incomplete",
                    "material_valuation_status": "unavailable",
                    "reason": REASON_RETURN_UNRESOLVED,
                }
            if ret.extended_cost_snapshot is None:
                return {
                    "available": False,
                    "value": None,
                    "material_cost_status": "incomplete",
                    "material_valuation_status": "unavailable",
                    "reason": REASON_MATERIAL_VALUATION_UNAVAILABLE,
                }

        currencies = {m.currency_snapshot for m in cost_rows + returns}
        if len(currencies) != 1 or None in currencies:
            return {
                "available": False,
                "value": None,
                "material_cost_status": "incomplete",
                "material_valuation_status": "unavailable",
                "reason": REASON_MATERIAL_VALUATION_UNAVAILABLE,
            }

        total = sum(float(m.extended_cost_snapshot) for m in cost_rows)
        total -= sum(float(m.extended_cost_snapshot) for m in returns)
        return {
            "available": True,
            "value": round(total, 4),
            "currency": currencies.pop(),
            "material_cost_status": "complete",
            "material_valuation_status": "frozen",
            "reason": None,
            "provenance": "stock_movements.frozen_valuation",
            "consumption_count": len(consumptions),
            "return_count": len(returns),
            "scrap_count": len(scraps),
        }

    def serialize_movement(self, movement: StockMovement, *, include_valuation: bool) -> dict[str, Any]:
        row: dict[str, Any] = {
            "id": movement.id,
            "order_id": movement.order_id,
            "task_id": movement.task_id,
            "material_id": movement.material_id,
            "quantity": movement.quantity,
            "unit": movement.unit,
            "movement_type": movement.movement_type,
            "performed_at": movement.performed_at.isoformat() if movement.performed_at else None,
            "performed_by": movement.performed_by,
            "idempotency_key": movement.idempotency_key,
            "reverses_movement_id": movement.reverses_movement_id,
            "reason": movement.reason,
        }
        if include_valuation:
            row.update(
                {
                    "unit_cost_snapshot": movement.unit_cost_snapshot,
                    "currency_snapshot": movement.currency_snapshot,
                    "valuation_method": movement.valuation_method,
                    "valuation_provenance": movement.valuation_provenance,
                    "extended_cost_snapshot": movement.extended_cost_snapshot,
                }
            )
        return row
