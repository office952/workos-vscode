"""Operational Reports API — read-only workforce/execution reality reports."""
from __future__ import annotations

import logging
from typing import Optional

from core.database import get_db
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, Query
from services.operational_reports_service import OperationalReportsService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/operational-reports",
    tags=["operational-reports"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/summary")
async def get_operational_reports_summary(
    from_date: Optional[str] = Query(None, description="ISO date lower bound"),
    to_date: Optional[str] = Query(None, description="ISO date upper bound"),
    employee_id: Optional[int] = Query(None, ge=1),
    order_id: Optional[int] = Query(None, ge=1),
    category: Optional[str] = Query(
        "all",
        description="all | employee_activity | task_reality | materials | field_installation | completeness",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Read-only operational reports over collected execution reality."""
    svc = OperationalReportsService(db)
    return await svc.build_summary(
        from_date=from_date,
        to_date=to_date,
        employee_id=employee_id,
        order_id=order_id,
        category=category,
    )
