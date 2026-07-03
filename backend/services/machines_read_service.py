"""
M19 — Machines Registry Read Service.

Read-only service that queries the `machines` table created by M19 DB execution.

Safety guarantees:
  - No DB writes. No mutations. No side effects.
  - Idempotent: same input + same DB state → same output.
  - Gated by `settings.registry_machines_live` at the caller level.

Forbidden:
  - No INSERT / UPDATE / DELETE.
  - No telemetry (telemetry boundary).
  - No operator assignment (operator boundary).
  - No maintenance scheduling (maintenance boundary).
  - No Execution Reality integration.
  - No Shop Floor runtime integration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MachinesReadService:
    """Read-only access to public.machines (M19 registry)."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_code(self, machine_code: str) -> Optional[Dict[str, Any]]:
        """Fetch a single machine by its unique code.

        Returns None if not found. Never writes.
        """
        sql = text(
            "SELECT id, machine_code, name, description, machine_type, "
            "workcenter_code, operational_status, is_available, "
            "manufacturer, model, year_acquired, capabilities, "
            "capacity_metadata, is_active, created_at, updated_at "
            "FROM machines WHERE machine_code = :code LIMIT 1"
        )
        result = await self._db.execute(sql, {"code": machine_code})
        row = result.mappings().first()
        if not row:
            return None
        return dict(row)

    async def exists(self, machine_code: str) -> bool:
        """Check if a machine code exists in the registry."""
        sql = text("SELECT 1 FROM machines WHERE machine_code = :code LIMIT 1")
        result = await self._db.execute(sql, {"code": machine_code})
        return result.scalar() is not None

    async def is_active(self, machine_code: str) -> Optional[bool]:
        """Check if a machine is active. Returns None if not found."""
        sql = text(
            "SELECT is_active FROM machines WHERE machine_code = :code LIMIT 1"
        )
        result = await self._db.execute(sql, {"code": machine_code})
        row = result.scalar()
        if row is None:
            return None
        return bool(row)

    async def machine_available(self, machine_code: str) -> Dict[str, Any]:
        """Check machine readiness: exists, is_active, is_available, operational_status=active.

        Returns a dict with:
          - found: bool
          - active: bool (False if not found)
          - available: bool (False if not found or is_available=false)
          - operational: bool (False if operational_status != 'active')
          - machine: dict or None

        This method does NOT enforce telemetry/operator/maintenance boundaries.
        """
        machine = await self.get_by_code(machine_code)
        if machine is None:
            return {
                "found": False,
                "active": False,
                "available": False,
                "operational": False,
                "machine": None,
            }
        is_active = bool(machine.get("is_active", False))
        is_available = bool(machine.get("is_available", False))
        is_operational = machine.get("operational_status") == "active"
        return {
            "found": True,
            "active": is_active,
            "available": is_available,
            "operational": is_operational,
            "machine": machine,
        }

    async def check_readiness(self) -> Dict[str, Any]:
        """Check if the machines registry is ready (table exists, has data).

        Returns:
          - ready: bool
          - row_count: int
          - active_count: int
          - available_count: int
        """
        try:
            count_sql = text("SELECT COUNT(*) FROM machines")
            active_sql = text("SELECT COUNT(*) FROM machines WHERE is_active = true")
            available_sql = text(
                "SELECT COUNT(*) FROM machines WHERE is_available = true AND is_active = true"
            )
            total = int((await self._db.execute(count_sql)).scalar() or 0)
            active = int((await self._db.execute(active_sql)).scalar() or 0)
            available = int((await self._db.execute(available_sql)).scalar() or 0)
            return {
                "ready": total > 0,
                "row_count": total,
                "active_count": active,
                "available_count": available,
            }
        except Exception as exc:
            logger.warning("Machines registry readiness check failed: %s", exc)
            return {
                "ready": False,
                "row_count": 0,
                "active_count": 0,
                "available_count": 0,
            }

    async def get_by_type(self, machine_type: str) -> List[Dict[str, Any]]:
        """Fetch all machines of a given type.

        Returns empty list if none found. Never writes.
        """
        sql = text(
            "SELECT id, machine_code, name, description, machine_type, "
            "workcenter_code, operational_status, is_available, "
            "manufacturer, model, year_acquired, capabilities, "
            "capacity_metadata, is_active, created_at, updated_at "
            "FROM machines WHERE machine_type = :mtype ORDER BY machine_code ASC"
        )
        result = await self._db.execute(sql, {"mtype": machine_type})
        return [dict(r) for r in result.mappings().all()]

    async def get_by_workcenter(self, workcenter_code: str) -> List[Dict[str, Any]]:
        """Fetch all machines assigned to a given workcenter.

        Returns empty list if none found. Never writes.
        """
        sql = text(
            "SELECT id, machine_code, name, description, machine_type, "
            "workcenter_code, operational_status, is_available, "
            "manufacturer, model, year_acquired, capabilities, "
            "capacity_metadata, is_active, created_at, updated_at "
            "FROM machines WHERE workcenter_code = :wc ORDER BY machine_code ASC"
        )
        result = await self._db.execute(sql, {"wc": workcenter_code})
        return [dict(r) for r in result.mappings().all()]

    async def list_all_codes(self, active_only: bool = True) -> List[str]:
        """Return all machine codes (optionally only active ones)."""
        if active_only:
            sql = text(
                "SELECT machine_code FROM machines WHERE is_active = true ORDER BY machine_code ASC"
            )
        else:
            sql = text("SELECT machine_code FROM machines ORDER BY machine_code ASC")
        result = await self._db.execute(sql)
        return [row[0] for row in result.all()]

    async def check_capability(self, machine_code: str, capability: str) -> Dict[str, Any]:
        """Check if a machine has a specific capability.

        Returns:
          - found: bool (machine exists)
          - has_capability: bool (capability in machine.capabilities array)
          - capabilities: list (all capabilities of the machine)
        """
        machine = await self.get_by_code(machine_code)
        if machine is None:
            return {
                "found": False,
                "has_capability": False,
                "capabilities": [],
            }
        capabilities = machine.get("capabilities") or []
        return {
            "found": True,
            "has_capability": capability in capabilities,
            "capabilities": capabilities,
        }