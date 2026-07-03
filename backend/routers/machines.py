"""
Machines Registry API — read-only endpoints for the frontend Utilaje page.

Provides:
  GET /api/v1/machines          → list all machines
  GET /api/v1/machines/{code}   → get single machine by code
  GET /api/v1/machines/stats    → summary stats (running/idle/maintenance counts)
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

def _is_missing_machines_table_error(exc: Exception) -> bool:
    """Return True when DB error indicates public.machines is missing."""
    if "relation \"machines\" does not exist" in str(exc).lower():
        return True
    if isinstance(exc, DBAPIError) and exc.orig is not None:
        return exc.orig.__class__.__name__ == "UndefinedTableError"
    return False


async def _machines_table_exists(db: AsyncSession) -> bool:
    """Check if machines exists without throwing on missing relation (PG + SQLite)."""
    try:
        sqlite_probe = await db.execute(
            text(
                "SELECT 1 FROM sqlite_master "
                "WHERE type = 'table' AND name = 'machines' LIMIT 1"
            )
        )
        return sqlite_probe.scalar() is not None
    except Exception:
        pass

    result = await db.execute(text("SELECT to_regclass('public.machines')"))
    return result.scalar() is not None

router = APIRouter(
    prefix="/api/v1/machines",
    tags=["machines"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/stats")
async def get_machines_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Return summary stats for the machines registry."""
    try:
        if not await _machines_table_exists(db):
            logger.warning("Machines table missing; returning empty stats payload")
            return {
                "total": 0,
                "available": 0,
                "statusCounts": {},
                "typeCounts": {},
            }

        total_sql = text("SELECT COUNT(*) FROM machines WHERE is_active = true")
        total = int((await db.execute(total_sql)).scalar() or 0)

        available_sql = text(
            "SELECT COUNT(*) FROM machines WHERE is_active = true AND is_available = true"
        )
        available = int((await db.execute(available_sql)).scalar() or 0)

        # Group by operational_status
        status_sql = text(
            "SELECT operational_status, COUNT(*) as cnt "
            "FROM machines WHERE is_active = true "
            "GROUP BY operational_status"
        )
        result = await db.execute(status_sql)
        status_counts = {row[0]: row[1] for row in result}

        # Group by machine_type
        type_sql = text(
            "SELECT machine_type, COUNT(*) as cnt "
            "FROM machines WHERE is_active = true "
            "GROUP BY machine_type ORDER BY cnt DESC"
        )
        result = await db.execute(type_sql)
        type_counts = {row[0]: row[1] for row in result}

        return {
            "total": total,
            "available": available,
            "statusCounts": status_counts,
            "typeCounts": type_counts,
        }
    except Exception as e:
        if _is_missing_machines_table_error(e):
            logger.warning("Machines table missing during stats query; returning empty stats payload")
            return {
                "total": 0,
                "available": 0,
                "statusCounts": {},
                "typeCounts": {},
            }
        logger.error(f"Error fetching machines stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_machines(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """List all active machines from the registry."""
    try:
        if not await _machines_table_exists(db):
            logger.warning("Machines table missing; returning empty machine list")
            return []

        sql = text(
            "SELECT id, machine_code, name, description, machine_type, "
            "workcenter_code, operational_status, is_available, "
            "manufacturer, model, year_acquired, capabilities, "
            "capacity_metadata, is_active, created_at, updated_at "
            "FROM machines WHERE is_active = true "
            "ORDER BY workcenter_code, machine_code ASC"
        )
        result = await db.execute(sql)
        rows = []
        for row in result.mappings():
            d = dict(row)
            # Convert capabilities array to list for JSON serialization
            if d.get("capabilities") and isinstance(d["capabilities"], list):
                d["capabilities"] = list(d["capabilities"])
            # Convert capacity_metadata to dict
            if d.get("capacity_metadata") is None:
                d["capacity_metadata"] = {}
            for dt_field in ("created_at", "updated_at"):
                val = d.get(dt_field)
                if val is not None and hasattr(val, "isoformat"):
                    d[dt_field] = val.isoformat()
            rows.append(d)
        return rows
    except Exception as e:
        if _is_missing_machines_table_error(e):
            logger.warning("Machines table missing during list query; returning empty machine list")
            return []
        logger.error(f"Error listing machines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}")
async def get_machine(code: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get a single machine by its code."""
    try:
        if not await _machines_table_exists(db):
            raise HTTPException(status_code=404, detail=f"Machine '{code}' not found")

        sql = text(
            "SELECT id, machine_code, name, description, machine_type, "
            "workcenter_code, operational_status, is_available, "
            "manufacturer, model, year_acquired, capabilities, "
            "capacity_metadata, is_active, created_at, updated_at "
            "FROM machines WHERE machine_code = :code LIMIT 1"
        )
        result = await db.execute(sql, {"code": code})
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Machine '{code}' not found")
        d = dict(row)
        if d.get("capabilities") and isinstance(d["capabilities"], list):
            d["capabilities"] = list(d["capabilities"])
        if d.get("capacity_metadata") is None:
            d["capacity_metadata"] = {}
        for dt_field in ("created_at", "updated_at"):
            val = d.get(dt_field)
            if val is not None and hasattr(val, "isoformat"):
                d[dt_field] = val.isoformat()
        return d
    except HTTPException:
        raise
    except Exception as e:
        if _is_missing_machines_table_error(e):
            raise HTTPException(status_code=404, detail=f"Machine '{code}' not found")
        logger.error(f"Error fetching machine {code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))