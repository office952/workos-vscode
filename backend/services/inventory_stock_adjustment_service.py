from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from models.inventory_materials import Inventory_materials
from models.stock_movements import StockMovement
from services.closed_job_mutation_guard import assert_execution_open_for_material_mutation
from services.inventory_material_eligibility import is_stock_operational_material

logger = logging.getLogger(__name__)


class StockAdjustmentError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


@dataclass
class StockReversalResult:
    status: str
    original_movement_id: int
    reversal_movement_id: int
    material_id: int
    quantity: float
    old_stock: float
    new_stock: float
    material_status_non_operational_recovery: bool = False
    material_status: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "original_movement_id": self.original_movement_id,
            "reversal_movement_id": self.reversal_movement_id,
            "material_id": self.material_id,
            "quantity": self.quantity,
            "old_stock": self.old_stock,
            "new_stock": self.new_stock,
            "material_status_non_operational_recovery": self.material_status_non_operational_recovery,
            "material_status": self.material_status,
        }


class InventoryStockAdjustmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_movement(self, movement_id: int) -> Optional[StockMovement]:
        stmt = select(StockMovement).where(StockMovement.id == movement_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_existing_reversal(self, original_movement_id: int) -> Optional[StockMovement]:
        stmt = select(StockMovement).where(
            StockMovement.idempotency_key == f"reversal:{original_movement_id}"
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_material(self, material_id: int) -> Optional[Inventory_materials]:
        stmt = select(Inventory_materials).where(Inventory_materials.id == material_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def reverse_movement(
        self,
        movement_id: int,
        performed_by: str,
        reason: str,
    ) -> StockReversalResult:
        if not isinstance(movement_id, int) or movement_id <= 0:
            raise StockAdjustmentError("movement_id_invalid")
        if not performed_by or not isinstance(performed_by, str):
            raise StockAdjustmentError("performed_by_required")
        if not reason or not reason.strip():
            raise StockAdjustmentError("reason_required")

        original = await self._get_movement(movement_id)
        if original is None:
            raise StockAdjustmentError("movement_not_found", str(movement_id))

        if original.movement_type != "consumption":
            raise StockAdjustmentError("movement_not_reversible", original.movement_type or "unknown")

        if original.order_id is not None:
            try:
                await assert_execution_open_for_material_mutation(self.db, int(original.order_id))
            except HTTPException as exc:
                detail = exc.detail if isinstance(exc.detail, dict) else {}
                raise StockAdjustmentError(
                    str(detail.get("error") or "execution_closed_mutation_blocked"),
                    str(detail.get("message") or "execution reopen required"),
                ) from exc

        existing = await self._get_existing_reversal(original.id)
        if existing is not None:
            raise StockAdjustmentError(
                "stock_movement_already_reversed",
                f"existing_reversal_movement_id={existing.id}",
            )

        material = await self._get_material(original.material_id)
        if material is None:
            raise StockAdjustmentError("material_not_found", str(original.material_id))

        recovery_non_operational = False
        if not is_stock_operational_material(material.status):
            # Option B: allow recovery reversal for historical system deductions,
            # but keep strict blocking for non-system movements.
            is_system_deduction = (
                original.source_type == "execution_reality"
                and isinstance(original.idempotency_key, str)
                and original.idempotency_key.startswith("reality:")
            )
            if not is_system_deduction:
                raise StockAdjustmentError("material_inactive", material.status or "unknown")
            recovery_non_operational = True

        quantity = float(original.quantity or 0.0)
        if quantity <= 0:
            raise StockAdjustmentError("invalid_original_quantity", str(quantity))

        current_stock = float(material.stock_current or 0.0)
        new_stock = round(current_stock + quantity, 4)
        now = datetime.now(timezone.utc)

        material.stock_current = new_stock

        reversal = StockMovement(
            material_id=original.material_id,
            source_type="stock_movement_reversal",
            source_id=original.id,
            order_id=original.order_id,
            task_id=original.task_id,
            quantity=quantity,
            unit=original.unit,
            movement_type="reversal",
            old_stock=current_stock,
            new_stock=new_stock,
            performed_by=performed_by,
            performed_at=now,
            reason=reason.strip(),
            idempotency_key=f"reversal:{original.id}",
        )
        self.db.add(reversal)

        try:
            await self.db.commit()
        except Exception as exc:
            await self.db.rollback()
            logger.error("Failed to commit stock reversal for movement %s: %s", movement_id, exc)
            raise StockAdjustmentError("commit_failed", str(exc))

        await self.db.refresh(reversal)
        return StockReversalResult(
            status="reversed",
            original_movement_id=original.id,
            reversal_movement_id=reversal.id,
            material_id=original.material_id,
            quantity=quantity,
            old_stock=current_stock,
            new_stock=new_stock,
            material_status_non_operational_recovery=recovery_non_operational,
            material_status=material.status,
        )