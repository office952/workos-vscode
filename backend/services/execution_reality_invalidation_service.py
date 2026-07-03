"""
ExecutionRealityInvalidationService — BUILD 18: Data Quality & Invalid Reality Marker.

Handles invalidation and restoration of ExecutionReality records.

STRICT BOUNDARIES:
  - Does NOT delete ExecutionReality records.
  - Does NOT mutate Quote, Order, Snapshot, CostEngine.
  - Does NOT silently reverse stock movements.
  - Invalid reason is REQUIRED.
  - Permission is enforced at router level (reality.invalidate / reality.restore_valid).
  - If stock was already deducted, invalidation is allowed but marks
    stock_reconciliation_required = True.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_reality import ExecutionReality
from models.stock_movements import StockMovement

logger = logging.getLogger(__name__)


class InvalidationError(Exception):
    """Raised when invalidation/restoration cannot proceed."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


class ExecutionRealityInvalidationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_reality_by_id(self, reality_id: int) -> Optional[ExecutionReality]:
        stmt = select(ExecutionReality).where(ExecutionReality.id == reality_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def _has_stock_movements(self, reality_id: int) -> bool:
        """Check if any stock movements exist for this reality."""
        stmt = select(StockMovement).where(
            StockMovement.source_type == "execution_reality",
            StockMovement.source_id == reality_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def invalidate(
        self,
        reality_id: int,
        reason: str,
        performed_by: str,
    ) -> Dict[str, Any]:
        """Invalidate an ExecutionReality record.

        Rules:
        - Record must exist.
        - Reason is required (non-empty).
        - Already-invalid records return idempotent success.
        - If stock was already deducted, invalidation proceeds but marks
          stock_reconciliation_required = True.
        - Does NOT delete the record.
        - Does NOT reverse stock movements.

        Returns:
            Dict with invalidation result including quality_status.
        """
        if not reason or not isinstance(reason, str) or reason.strip() == "":
            raise InvalidationError("reason_required", "Invalid reason is required")
        if not performed_by or not isinstance(performed_by, str):
            raise InvalidationError("performed_by_required")

        row = await self._get_reality_by_id(reality_id)
        if row is None:
            raise InvalidationError("reality_not_found", str(reality_id))

        # Idempotent: already invalid
        if row.is_invalid:
            return self._build_quality_status(row, stock_deducted=await self._has_stock_movements(reality_id))

        # Check if stock was already deducted
        stock_deducted = await self._has_stock_movements(reality_id)

        now = datetime.now(timezone.utc)
        row.is_invalid = True
        row.invalidated_at = now
        row.invalidated_by = performed_by
        row.invalid_reason = reason.strip()
        row.stock_reconciliation_required = stock_deducted
        # Clear any restoration fields
        row.restored_at = None
        row.restored_by = None
        row.restored_reason = None

        await self.db.commit()
        await self.db.refresh(row)

        logger.info(
            "ExecutionReality %d invalidated by %s. Reason: %s. Stock reconciliation: %s",
            reality_id, performed_by, reason.strip(), stock_deducted,
        )

        return self._build_quality_status(row, stock_deducted=stock_deducted)

    async def restore_valid(
        self,
        reality_id: int,
        reason: str,
        performed_by: str,
    ) -> Dict[str, Any]:
        """Restore an invalid ExecutionReality record to valid state.

        Rules:
        - Record must exist and be currently invalid.
        - Reason is required.
        - If stock_reconciliation_required is True, restoration is BLOCKED
          (stock state would be inconsistent).
        - Does NOT reverse any previous invalidation metadata (kept for audit).

        Returns:
            Dict with restored quality_status.
        """
        if not reason or not isinstance(reason, str) or reason.strip() == "":
            raise InvalidationError("reason_required", "Restore reason is required")
        if not performed_by or not isinstance(performed_by, str):
            raise InvalidationError("performed_by_required")

        row = await self._get_reality_by_id(reality_id)
        if row is None:
            raise InvalidationError("reality_not_found", str(reality_id))

        if not row.is_invalid:
            raise InvalidationError("reality_not_invalid", "Record is already valid")

        # Block restoration if stock reconciliation is required
        if row.stock_reconciliation_required:
            raise InvalidationError(
                "restoration_blocked_stock_reconciliation",
                "Cannot restore: stock was deducted from this reality before invalidation. "
                "Manual stock reconciliation is required first.",
            )

        now = datetime.now(timezone.utc)
        row.is_invalid = False
        row.restored_at = now
        row.restored_by = performed_by
        row.restored_reason = reason.strip()
        # Keep invalidated_at/by/reason for audit trail

        await self.db.commit()
        await self.db.refresh(row)

        logger.info(
            "ExecutionReality %d restored to valid by %s. Reason: %s",
            reality_id, performed_by, reason.strip(),
        )

        stock_deducted = await self._has_stock_movements(reality_id)
        return self._build_quality_status(row, stock_deducted=stock_deducted)

    async def get_quality_status(self, reality_id: int) -> Dict[str, Any]:
        """Get the data quality status of an ExecutionReality record."""
        row = await self._get_reality_by_id(reality_id)
        if row is None:
            raise InvalidationError("reality_not_found", str(reality_id))

        stock_deducted = await self._has_stock_movements(reality_id)
        return self._build_quality_status(row, stock_deducted=stock_deducted)

    def _build_quality_status(self, row: ExecutionReality, stock_deducted: bool) -> Dict[str, Any]:
        """Build the quality status DTO for a reality record."""
        warnings = []

        if row.is_invalid:
            warnings.append("Reality invalidată — exclusă din rapoarte și deduceri stoc")
            if row.stock_reconciliation_required:
                warnings.append(
                    "Reconciliere stoc necesară: stocul a fost dedus înainte de invalidare"
                )

        return {
            "reality_id": row.id,
            "order_id": row.order_id,
            "order_code": row.order_code,
            "is_invalid": bool(row.is_invalid),
            "invalidated_at": row.invalidated_at.isoformat() if row.invalidated_at else None,
            "invalidated_by": row.invalidated_by,
            "invalid_reason": row.invalid_reason,
            "stock_reconciliation_required": bool(row.stock_reconciliation_required),
            "stock_deducted": stock_deducted,
            "restored_at": row.restored_at.isoformat() if row.restored_at else None,
            "restored_by": row.restored_by,
            "restored_reason": row.restored_reason,
            "warnings": warnings,
        }