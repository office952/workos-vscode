"""
InventoryDeductionService — BUILD 16: Inventory Operational Loop.

Controlled stock deduction from ExecutionReality material consumption.

STRICT BOUNDARIES:
  - Only deducts stock for material rows that have a valid material_id
    linking to inventory_materials.
  - Free-text rows (material_id is None or empty) are NEVER deducted.
  - Deduction requires the ExecutionReality to exist.
  - Duplicate deductions are prevented via idempotency_key.
  - Insufficient stock blocks deduction (no negative stock allowed).
  - Every deduction atomically: updates stock_current, creates StockMovement.
  - Does NOT modify Quote, Order, Snapshot, CostEngine, or any other module.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_reality import ExecutionReality
from models.inventory_materials import Inventory_materials
from models.stock_movements import StockMovement
from services.inventory_material_eligibility import is_stock_operational_material

logger = logging.getLogger(__name__)


class DeductionError(Exception):
    """Raised when deduction cannot proceed."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


@dataclass
class DeductionRowResult:
    """Result for a single material row deduction attempt."""
    material_index: int
    status: str  # "deducted" | "not_linked" | "already_deducted" | "insufficient_stock" | "material_not_found" | "invalid_quantity" | "material_not_stock_operational"
    material_id: Optional[int] = None
    material_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    old_stock: Optional[float] = None
    new_stock: Optional[float] = None
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "material_index": self.material_index,
            "status": self.status,
            "material_id": self.material_id,
            "material_name": self.material_name,
            "quantity": self.quantity,
            "unit": self.unit,
            "old_stock": self.old_stock,
            "new_stock": self.new_stock,
            "message": self.message,
        }


@dataclass
class DeductionResult:
    """Aggregate result for a deduction operation."""
    order_id: int
    reality_id: int
    total_rows: int
    deducted_count: int
    skipped_count: int
    blocked_count: int
    rows: List[DeductionRowResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "reality_id": self.reality_id,
            "total_rows": self.total_rows,
            "deducted_count": self.deducted_count,
            "skipped_count": self.skipped_count,
            "blocked_count": self.blocked_count,
            "rows": [r.to_dict() for r in self.rows],
        }


class InventoryDeductionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _make_idempotency_key(self, reality_id: int, material_index: int) -> str:
        """Create a unique key to prevent duplicate deductions."""
        return f"reality:{reality_id}:mat_idx:{material_index}"

    async def _check_already_deducted(self, idempotency_key: str) -> bool:
        """Check if this deduction has already been performed."""
        stmt = select(StockMovement).where(
            StockMovement.idempotency_key == idempotency_key
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _get_inventory_material(self, material_id: int) -> Optional[Inventory_materials]:
        """Fetch inventory material by ID."""
        stmt = select(Inventory_materials).where(Inventory_materials.id == material_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_reality(self, order_id: int) -> Optional[ExecutionReality]:
        """Fetch ExecutionReality by order_id."""
        stmt = select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_deduction_status(self, order_id: int) -> Dict[str, Any]:
        """Get deduction eligibility status for all material rows in an ExecutionReality.

        Returns per-row status without performing any mutation.
        """
        reality = await self._get_reality(order_id)
        if reality is None:
            return {
                "order_id": order_id,
                "reality_exists": False,
                "rows": [],
                "summary": {"total": 0, "eligible": 0, "not_linked": 0, "already_deducted": 0},
            }

        # BUILD 18: If reality is invalid, return blocked status
        if reality.is_invalid:
            return {
                "order_id": order_id,
                "reality_exists": True,
                "reality_id": reality.id,
                "reality_invalid": True,
                "rows": [],
                "summary": {"total": 0, "eligible": 0, "not_linked": 0, "already_deducted": 0},
                "blocked_reason": "Reality invalidată — deducerea stoc este blocată",
            }

        materials = self._parse_materials(reality.materials_json)
        rows = []
        eligible = 0
        not_linked = 0
        already_deducted = 0
        non_operational_blocked = 0

        for idx, mat in enumerate(materials):
            mat_id_raw = mat.get("material_id")
            if mat_id_raw is None or str(mat_id_raw).strip() == "":
                rows.append({
                    "index": idx,
                    "material_name": mat.get("material_name", ""),
                    "quantity": mat.get("quantity"),
                    "unit": mat.get("unit"),
                    "status": "not_linked",
                    "message": "Material fără legătură la inventar (observațional)",
                })
                not_linked += 1
                continue

            try:
                mat_id_int = int(mat_id_raw)
            except (TypeError, ValueError):
                rows.append({
                    "index": idx,
                    "material_name": mat.get("material_name", ""),
                    "quantity": mat.get("quantity"),
                    "unit": mat.get("unit"),
                    "status": "not_linked",
                    "message": f"material_id invalid: {mat_id_raw}",
                })
                not_linked += 1
                continue

            idem_key = self._make_idempotency_key(reality.id, idx)
            if await self._check_already_deducted(idem_key):
                rows.append({
                    "index": idx,
                    "material_id": mat_id_int,
                    "material_name": mat.get("material_name", ""),
                    "quantity": mat.get("quantity"),
                    "unit": mat.get("unit"),
                    "status": "already_deducted",
                    "message": "Deja dedus din stoc",
                })
                already_deducted += 1
                continue

            # Check inventory material exists
            inv_mat = await self._get_inventory_material(mat_id_int)
            if inv_mat is None:
                rows.append({
                    "index": idx,
                    "material_id": mat_id_int,
                    "material_name": mat.get("material_name", ""),
                    "quantity": mat.get("quantity"),
                    "unit": mat.get("unit"),
                    "status": "material_not_found",
                    "message": f"Material ID {mat_id_int} nu există în inventar",
                })
                not_linked += 1
                continue

            if not is_stock_operational_material(inv_mat.status):
                rows.append({
                    "index": idx,
                    "material_id": mat_id_int,
                    "material_name": mat.get("material_name", "") or inv_mat.name,
                    "quantity": mat.get("quantity"),
                    "unit": mat.get("unit"),
                    "status": "material_not_stock_operational",
                    "material_status": inv_mat.status,
                    "message": f"Material status non-operațional pentru stoc: {inv_mat.status}",
                })
                non_operational_blocked += 1
                continue

            quantity = mat.get("quantity", 0)
            current_stock = inv_mat.stock_current or 0.0
            if quantity > current_stock:
                rows.append({
                    "index": idx,
                    "material_id": mat_id_int,
                    "material_name": mat.get("material_name", "") or inv_mat.name,
                    "quantity": quantity,
                    "unit": mat.get("unit"),
                    "status": "insufficient_stock",
                    "current_stock": current_stock,
                    "message": f"Stoc insuficient: necesar {quantity}, disponibil {current_stock}",
                })
                eligible += 1  # Still eligible but will be blocked at deduction time
                continue

            rows.append({
                "index": idx,
                "material_id": mat_id_int,
                "material_name": mat.get("material_name", "") or inv_mat.name,
                "quantity": quantity,
                "unit": mat.get("unit"),
                "status": "eligible",
                "current_stock": current_stock,
                "message": "Eligibil pentru deducere",
            })
            eligible += 1

        return {
            "order_id": order_id,
            "reality_exists": True,
            "reality_id": reality.id,
            "rows": rows,
            "summary": {
                "total": len(materials),
                "eligible": eligible,
                "not_linked": not_linked,
                "already_deducted": already_deducted,
                "non_operational_blocked": non_operational_blocked,
            },
        }

    async def deduct_materials(
        self,
        order_id: int,
        performed_by: str,
        reason: Optional[str] = None,
        material_indices: Optional[List[int]] = None,
    ) -> DeductionResult:
        """Deduct linked materials from inventory based on ExecutionReality.

        Only processes material rows that:
        1. Have a valid material_id linking to inventory_materials
        2. Have not already been deducted (idempotency check)
        3. Have sufficient stock available

        Free-text rows (no material_id) are skipped with status 'not_linked'.

        Args:
            order_id: The order whose ExecutionReality to process.
            performed_by: User/operator performing the deduction.
            reason: Optional reason/note for the deduction.
            material_indices: Optional list of specific indices to deduct.
                If None, all eligible rows are processed.

        Returns:
            DeductionResult with per-row outcomes.
        """
        if not isinstance(order_id, int) or order_id <= 0:
            raise DeductionError("order_id_invalid")
        if not performed_by or not isinstance(performed_by, str):
            raise DeductionError("performed_by_required")

        reality = await self._get_reality(order_id)
        if reality is None:
            raise DeductionError("reality_not_found", str(order_id))

        # BUILD 18: Block deduction on invalid realities
        if reality.is_invalid:
            raise DeductionError(
                "reality_invalid",
                "Cannot deduct stock from an invalidated ExecutionReality"
            )

        materials = self._parse_materials(reality.materials_json)
        if not materials:
            raise DeductionError("no_materials", "ExecutionReality has no material rows")

        # Determine which indices to process
        if material_indices is not None:
            indices_to_process = material_indices
        else:
            indices_to_process = list(range(len(materials)))

        results: List[DeductionRowResult] = []
        deducted_count = 0
        skipped_count = 0
        blocked_count = 0
        now = datetime.now(timezone.utc)

        for idx in indices_to_process:
            if idx < 0 or idx >= len(materials):
                results.append(DeductionRowResult(
                    material_index=idx,
                    status="invalid_index",
                    message=f"Index {idx} out of range (0-{len(materials)-1})",
                ))
                blocked_count += 1
                continue

            mat = materials[idx]
            mat_id_raw = mat.get("material_id")

            # Check if material_id is present (linked vs free-text)
            if mat_id_raw is None or str(mat_id_raw).strip() == "":
                results.append(DeductionRowResult(
                    material_index=idx,
                    status="not_linked",
                    material_name=mat.get("material_name", ""),
                    message="Material fără legătură la inventar (observațional doar)",
                ))
                skipped_count += 1
                continue

            # Parse material_id as integer
            try:
                mat_id_int = int(mat_id_raw)
            except (TypeError, ValueError):
                results.append(DeductionRowResult(
                    material_index=idx,
                    status="not_linked",
                    material_name=mat.get("material_name", ""),
                    message=f"material_id invalid: {mat_id_raw}",
                ))
                skipped_count += 1
                continue

            # Idempotency check
            idem_key = self._make_idempotency_key(reality.id, idx)
            if await self._check_already_deducted(idem_key):
                results.append(DeductionRowResult(
                    material_index=idx,
                    status="already_deducted",
                    material_id=mat_id_int,
                    material_name=mat.get("material_name", ""),
                    message="Deja dedus din stoc (idempotent)",
                ))
                skipped_count += 1
                continue

            # Fetch inventory material
            inv_mat = await self._get_inventory_material(mat_id_int)
            if inv_mat is None:
                results.append(DeductionRowResult(
                    material_index=idx,
                    status="material_not_found",
                    material_id=mat_id_int,
                    material_name=mat.get("material_name", ""),
                    message=f"Material ID {mat_id_int} nu există în inventar",
                ))
                blocked_count += 1
                continue

            # Contract hardening: prevent deductions on non-operational material statuses.
            if not is_stock_operational_material(inv_mat.status):
                results.append(DeductionRowResult(
                    material_index=idx,
                    status="material_not_stock_operational",
                    material_id=mat_id_int,
                    material_name=inv_mat.name,
                    message=f"Material status non-operațional pentru stoc: {inv_mat.status}",
                ))
                blocked_count += 1
                continue

            # Validate quantity
            quantity = mat.get("quantity")
            if quantity is None or not isinstance(quantity, (int, float)) or quantity <= 0:
                results.append(DeductionRowResult(
                    material_index=idx,
                    status="invalid_quantity",
                    material_id=mat_id_int,
                    material_name=inv_mat.name,
                    message=f"Cantitate invalidă: {quantity}",
                ))
                blocked_count += 1
                continue

            quantity_float = float(quantity)
            current_stock = float(inv_mat.stock_current or 0.0)

            # Insufficient stock check
            if quantity_float > current_stock:
                results.append(DeductionRowResult(
                    material_index=idx,
                    status="insufficient_stock",
                    material_id=mat_id_int,
                    material_name=inv_mat.name,
                    quantity=quantity_float,
                    unit=mat.get("unit", ""),
                    old_stock=current_stock,
                    message=f"Stoc insuficient: necesar {quantity_float}, disponibil {current_stock}",
                ))
                blocked_count += 1
                continue

            # Perform atomic deduction
            new_stock = round(current_stock - quantity_float, 4)
            inv_mat.stock_current = new_stock

            # Create stock movement record
            movement = StockMovement(
                material_id=mat_id_int,
                source_type="execution_reality",
                source_id=reality.id,
                order_id=order_id,
                task_id=mat.get("task_id"),
                quantity=quantity_float,
                unit=mat.get("unit", ""),
                movement_type="consumption",
                old_stock=current_stock,
                new_stock=new_stock,
                performed_by=performed_by,
                performed_at=now,
                reason=reason or "Deducere stoc din ExecutionReality",
                idempotency_key=idem_key,
            )
            self.db.add(movement)

            results.append(DeductionRowResult(
                material_index=idx,
                status="deducted",
                material_id=mat_id_int,
                material_name=inv_mat.name,
                quantity=quantity_float,
                unit=mat.get("unit", ""),
                old_stock=current_stock,
                new_stock=new_stock,
                message=f"Dedus: {quantity_float} {mat.get('unit', '')} din stoc",
            ))
            deducted_count += 1

        # Commit all changes atomically
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to commit stock deductions for order {order_id}: {e}")
            raise DeductionError("commit_failed", str(e))

        return DeductionResult(
            order_id=order_id,
            reality_id=reality.id,
            total_rows=len(materials),
            deducted_count=deducted_count,
            skipped_count=skipped_count,
            blocked_count=blocked_count,
            rows=results,
        )

    async def get_movements_for_order(self, order_id: int) -> List[Dict[str, Any]]:
        """Get all stock movements for an order (read-only)."""
        stmt = (
            select(StockMovement)
            .where(StockMovement.order_id == order_id)
            .order_by(StockMovement.performed_at.desc())
        )
        result = await self.db.execute(stmt)
        movements = result.scalars().all()
        return [
            {
                "id": m.id,
                "material_id": m.material_id,
                "source_type": m.source_type,
                "source_id": m.source_id,
                "order_id": m.order_id,
                "task_id": m.task_id,
                "quantity": m.quantity,
                "unit": m.unit,
                "movement_type": m.movement_type,
                "old_stock": m.old_stock,
                "new_stock": m.new_stock,
                "performed_by": m.performed_by,
                "performed_at": m.performed_at.isoformat() if m.performed_at else None,
                "reason": m.reason,
                "idempotency_key": m.idempotency_key,
            }
            for m in movements
        ]

    async def get_recent_movements(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent stock movements across all orders (read-only)."""
        stmt = (
            select(StockMovement)
            .order_by(StockMovement.performed_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        movements = result.scalars().all()
        return [
            {
                "id": m.id,
                "material_id": m.material_id,
                "source_type": m.source_type,
                "source_id": m.source_id,
                "order_id": m.order_id,
                "task_id": m.task_id,
                "quantity": m.quantity,
                "unit": m.unit,
                "movement_type": m.movement_type,
                "old_stock": m.old_stock,
                "new_stock": m.new_stock,
                "performed_by": m.performed_by,
                "performed_at": m.performed_at.isoformat() if m.performed_at else None,
                "reason": m.reason,
            }
            for m in movements
        ]

    @staticmethod
    def _parse_materials(raw: Optional[str]) -> List[Dict[str, Any]]:
        if raw is None or raw == "":
            return []
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return []
        if not isinstance(parsed, list):
            return []
        return parsed