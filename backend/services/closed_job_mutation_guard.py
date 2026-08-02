"""Reject material/cost mutations against an explicitly closed execution job.

Closed execution is immutable until an authorized reopen with reason.
Silent margin recalculation after closure is forbidden.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.actual_cost_policy import ExecutionJobClosure

REASON_EXECUTION_CLOSED_MUTATION_BLOCKED = "execution_closed_mutation_blocked"
REASON_EXECUTION_REOPEN_REQUIRED = "execution_reopen_required"


async def assert_execution_open_for_material_mutation(
    db: AsyncSession,
    order_id: int,
) -> None:
    """Block StockMovement writes while job closure status is closed."""
    if not isinstance(order_id, int) or order_id <= 0:
        return
    closure = (
        await db.execute(
            select(ExecutionJobClosure).where(ExecutionJobClosure.order_id == order_id)
        )
    ).scalar_one_or_none()
    if closure is None:
        return
    status = str(closure.status or "").strip().lower()
    if status == "closed":
        raise HTTPException(
            status_code=409,
            detail={
                "error": REASON_EXECUTION_CLOSED_MUTATION_BLOCKED,
                "reason": REASON_EXECUTION_REOPEN_REQUIRED,
                "order_id": order_id,
                "closure_status": status,
                "message": (
                    "Lucrarea este închisă. Redeschiderea autorizată este obligatorie "
                    "înainte de mișcări materiale sau corecții de cost."
                ),
            },
        )
