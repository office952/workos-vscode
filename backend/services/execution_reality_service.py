"""
ExecutionRealityService — WorkOS Execution Layer v1.

STRICT BOUNDARIES (non-negotiable):
  - Writes ONLY to the `execution_reality` table.
  - Does NOT modify the Order row. Does NOT modify the ExecutionPlan row.
  - Does NOT call any upstream service (CostEngine, QuoteOrchestrator,
    ProductSystemService). It does not import them either.
  - Totals are computed from this model's own rows only.
  - Missing or structurally invalid inputs raise explicit errors; there are
    NO `or 0`, `or None`, `or []`, `or "pcs"` fallbacks.
  - Materials captured here are OBSERVATIONAL ONLY. They do NOT update
    inventory, do NOT modify cost engine, do NOT modify order snapshot.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_reality import ExecutionReality
from services.task_work_session_service import (
    ROLE_PRIMARY,
    SESSION_STATUS_COMPLETED,
    SESSION_STATUS_ENDED,
    SESSION_TYPE_WORK,
    build_work_session_observation,
    close_work_session,
    compute_duration_minutes,
    ensure_session_id,
    has_active_session_for_employee,
    new_session_id,
)


class RealityInputError(Exception):
    """Raised when the caller sends malformed or missing reality data."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


def _iso_utc(dt_str: Optional[str]) -> datetime:
    """Parse an ISO-8601 UTC timestamp. No silent fallback to now()."""
    if dt_str is None or not isinstance(dt_str, str) or dt_str == "":
        raise RealityInputError("timestamp_missing")
    try:
        # Accept "...Z" too.
        s = dt_str.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(s)
    except ValueError as e:
        raise RealityInputError("timestamp_invalid", str(e))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _dt_to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


class ExecutionRealityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _get_row(self, order_id: int, *, for_update: bool = False) -> Optional[ExecutionReality]:
        stmt = select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def _get_or_create_row(self, order_id: int, order_code: str) -> ExecutionReality:
        row = await self._get_row(order_id)
        if row is not None:
            return row
        row = ExecutionReality(
            order_id=order_id,
            order_code=order_code,
            tasks_json="[]",
            total_actual_time_minutes=0.0,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    @staticmethod
    def _parse_tasks(raw: str) -> List[Dict[str, Any]]:
        if raw is None or raw == "":
            # empty shape, not a silent fallback: the model guarantees "[]" default,
            # but defensively treat empty string as no tasks.
            return []
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError) as e:
            raise RealityInputError("tasks_json_invalid", str(e))
        if not isinstance(parsed, list):
            raise RealityInputError("tasks_json_not_list")
        return parsed

    @staticmethod
    def _compute_total(tasks: List[Dict[str, Any]]) -> float:
        total = 0.0
        for t in tasks:
            duration = t.get("duration_minutes")
            if duration is not None:
                try:
                    parsed_duration = float(duration)
                except (TypeError, ValueError):
                    parsed_duration = 0.0
                if parsed_duration > 0:
                    total += parsed_duration
                    continue
            started_at = t.get("started_at")
            ended_at = t.get("ended_at")
            if started_at is None or ended_at is None:
                continue
            total += float(compute_duration_minutes(str(started_at), str(ended_at)))
        return round(total, 2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def start_task(
        self,
        order_id: int,
        order_code: str,
        task_id: str,
        timestamp: str,
        *,
        initial_fields: Optional[Dict[str, Any]] = None,
    ) -> ExecutionReality:
        if not isinstance(order_id, int) or order_id <= 0:
            raise RealityInputError("order_id_invalid")
        if not isinstance(order_code, str) or order_code == "":
            raise RealityInputError("order_code_invalid")
        if not isinstance(task_id, str) or task_id == "":
            raise RealityInputError("task_id_invalid")
        started_at = _iso_utc(timestamp)

        row = await self._get_or_create_row(order_id, order_code)
        tasks = self._parse_tasks(row.tasks_json)

        employee_id = None
        if initial_fields and initial_fields.get("employee_id") is not None:
            try:
                employee_id = int(initial_fields["employee_id"])
            except (TypeError, ValueError):
                employee_id = None

        if employee_id is not None:
            if has_active_session_for_employee(tasks, task_id=task_id, employee_id=employee_id):
                raise RealityInputError("task_already_started", task_id)
        else:
            for t in tasks:
                if t.get("task_id") == task_id and t.get("ended_at") is None and t.get("started_at"):
                    raise RealityInputError("task_already_started", task_id)

        started_iso = _dt_to_iso(started_at)
        employee_name = str(
            (initial_fields or {}).get("employee_name")
            or (initial_fields or {}).get("operator_name")
            or ""
        ).strip()

        if initial_fields and initial_fields.get("session_id"):
            observation: Dict[str, Any] = {
                "session_id": str(initial_fields["session_id"]),
                "task_id": task_id,
                "started_at": started_iso,
                "ended_at": None,
                "status": "in_progress",
                "session_type": SESSION_TYPE_WORK,
                "role": ROLE_PRIMARY,
                "source": str((initial_fields or {}).get("source") or "execution"),
            }
            for key, value in (initial_fields or {}).items():
                if value is not None and key not in observation:
                    observation[key] = value
        elif employee_id is not None and employee_name:
            observation = build_work_session_observation(
                task_id=task_id,
                employee_id=employee_id,
                employee_name=employee_name,
                started_at_iso=started_iso,
                role=str((initial_fields or {}).get("role") or ROLE_PRIMARY),
                session_type=str((initial_fields or {}).get("session_type") or SESSION_TYPE_WORK),
                source=str((initial_fields or {}).get("source") or "execution"),
                extra={
                    k: v
                    for k, v in (initial_fields or {}).items()
                    if k
                    not in {
                        "employee_id",
                        "employee_name",
                        "operator_name",
                        "role",
                        "session_type",
                        "source",
                        "session_id",
                    }
                    and v is not None
                },
            )
        else:
            observation = {
                "session_id": new_session_id(),
                "task_id": task_id,
                "started_at": started_iso,
                "ended_at": None,
            }
            if initial_fields:
                for key, value in initial_fields.items():
                    if value is not None:
                        observation[key] = value
        tasks.append(observation)
        row.tasks_json = json.dumps(tasks)
        row.total_actual_time_minutes = self._compute_total(tasks)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def end_task(
        self,
        order_id: int,
        task_id: str,
        timestamp: str,
        *,
        completion_fields: Optional[Dict[str, Any]] = None,
        employee_id: Optional[int] = None,
    ) -> ExecutionReality:
        if not isinstance(order_id, int) or order_id <= 0:
            raise RealityInputError("order_id_invalid")
        if not isinstance(task_id, str) or task_id == "":
            raise RealityInputError("task_id_invalid")
        ended_at = _iso_utc(timestamp)

        row = await self._get_row(order_id, for_update=True)
        if row is None:
            raise RealityInputError("reality_not_initialised", str(order_id))

        tasks = self._parse_tasks(row.tasks_json)
        matched = False
        ended_iso = _dt_to_iso(ended_at)
        is_completion = bool(
            completion_fields and completion_fields.get("completed_by_employee_id") is not None
        )
        close_status = SESSION_STATUS_COMPLETED if is_completion else SESSION_STATUS_ENDED

        for t in tasks:
            if t.get("task_id") != task_id:
                continue
            if t.get("ended_at") is not None:
                continue
            if employee_id is not None:
                try:
                    entry_employee = int(t.get("employee_id") or 0)
                except (TypeError, ValueError):
                    entry_employee = 0
                if entry_employee != employee_id:
                    continue
            started_raw = t.get("started_at")
            if started_raw is None:
                raise RealityInputError("task_missing_start", task_id)
            started_at = datetime.fromisoformat(str(started_raw).replace("Z", "+00:00"))
            if ended_at < started_at:
                raise RealityInputError("timestamp_before_start", task_id)
            ensure_session_id(t)
            close_work_session(
                t,
                ended_at_iso=ended_iso,
                status=close_status,
                completion_fields=completion_fields,
            )
            matched = True
            break
        if not matched:
            if is_completion and employee_id is not None:
                for t in tasks:
                    if t.get("task_id") != task_id:
                        continue
                    if not t.get("ended_at"):
                        continue
                    try:
                        completed_by = int(t.get("completed_by_employee_id") or 0)
                    except (TypeError, ValueError):
                        completed_by = 0
                    try:
                        entry_employee = int(t.get("employee_id") or 0)
                    except (TypeError, ValueError):
                        entry_employee = 0
                    if completed_by == employee_id or entry_employee == employee_id:
                        await self.db.refresh(row)
                        return row
            raise RealityInputError("task_not_started", task_id)

        row.tasks_json = json.dumps(tasks)
        row.total_actual_time_minutes = self._compute_total(tasks)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def compute_total(self, order_id: int) -> float:
        """Pure read. Never writes."""
        if not isinstance(order_id, int) or order_id <= 0:
            raise RealityInputError("order_id_invalid")
        row = await self._get_row(order_id)
        if row is None:
            return 0.0
        tasks = self._parse_tasks(row.tasks_json)
        return self._compute_total(tasks)

    async def get_by_order(self, order_id: int) -> Optional[ExecutionReality]:
        if not isinstance(order_id, int) or order_id <= 0:
            raise RealityInputError("order_id_invalid")
        return await self._get_row(order_id)

    # ------------------------------------------------------------------
    # Materials Capture (BUILD SET 3B)
    # OBSERVATIONAL ONLY — does NOT update inventory, cost engine, or order.
    # ------------------------------------------------------------------

    VALID_UNITS = frozenset([
        "buc", "m", "m2", "m3", "kg", "g", "l", "ml", "set", "role", "coli", "placi",
    ])

    @staticmethod
    def _parse_materials(raw: Optional[str]) -> List[Dict[str, Any]]:
        if raw is None or raw == "":
            return []
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError) as e:
            raise RealityInputError("materials_json_invalid", str(e))
        if not isinstance(parsed, list):
            raise RealityInputError("materials_json_not_list")
        return parsed

    @staticmethod
    def _validate_material_row(row: Dict[str, Any]) -> None:
        """Validate a single material row.

        Rules:
          - material_name required if no material_id
          - quantity > 0
          - unit must be in VALID_UNITS
        """
        material_id = row.get("material_id")
        material_name = row.get("material_name")

        # material_name required if no material_id
        if (material_id is None or str(material_id).strip() == "") and (
            material_name is None or str(material_name).strip() == ""
        ):
            raise RealityInputError(
                "material_name_required",
                "material_name is required when material_id is not provided",
            )

        # quantity > 0
        quantity = row.get("quantity")
        if quantity is None:
            raise RealityInputError("material_quantity_missing")
        try:
            qty_float = float(quantity)
        except (TypeError, ValueError):
            raise RealityInputError("material_quantity_invalid", str(quantity))
        if qty_float <= 0:
            raise RealityInputError("material_quantity_must_be_positive", str(qty_float))

        # unit valid
        unit = row.get("unit")
        if unit is None or str(unit).strip() == "":
            raise RealityInputError("material_unit_missing")
        if str(unit).strip().lower() not in ExecutionRealityService.VALID_UNITS:
            raise RealityInputError(
                "material_unit_invalid",
                f"'{unit}' not in {sorted(ExecutionRealityService.VALID_UNITS)}",
            )

    async def add_materials(
        self,
        order_id: int,
        materials: List[Dict[str, Any]],
    ) -> ExecutionReality:
        """Add one or more material rows to an existing ExecutionReality.

        Each row is validated individually. On any validation failure the
        entire batch is rejected (no partial writes).

        Does NOT update inventory. Does NOT modify cost engine.
        """
        if not isinstance(order_id, int) or order_id <= 0:
            raise RealityInputError("order_id_invalid")
        if not isinstance(materials, list) or len(materials) == 0:
            raise RealityInputError("materials_empty")

        # Validate all rows first (fail-fast, no partial writes)
        for idx, mat in enumerate(materials):
            if not isinstance(mat, dict):
                raise RealityInputError("material_row_not_dict", f"index={idx}")
            self._validate_material_row(mat)

        row = await self._get_row(order_id)
        if row is None:
            raise RealityInputError("reality_not_initialised", str(order_id))

        existing = self._parse_materials(row.materials_json)
        now_iso = datetime.now(timezone.utc).isoformat()

        for mat in materials:
            row_payload: Dict[str, Any] = {
                "material_id": mat.get("material_id") or None,
                "material_name": str(mat.get("material_name", "")).strip(),
                "quantity": float(mat["quantity"]),
                "unit": str(mat["unit"]).strip().lower(),
                "task_id": mat.get("task_id") or None,
                "added_at": mat.get("reported_at") or mat.get("added_at") or now_iso,
            }
            if mat.get("reported_by_employee_id") is not None:
                row_payload["reported_by_employee_id"] = mat.get("reported_by_employee_id")
            if mat.get("reported_by_employee_name"):
                row_payload["reported_by_employee_name"] = mat.get("reported_by_employee_name")
            if mat.get("consumption_notes"):
                row_payload["consumption_notes"] = mat.get("consumption_notes")
            existing.append(row_payload)

        row.materials_json = json.dumps(existing)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def update_material(
        self,
        order_id: int,
        material_index: int,
        updated: Dict[str, Any],
    ) -> ExecutionReality:
        """Update a single material row by index.

        Does NOT update inventory. Does NOT modify cost engine.
        """
        if not isinstance(order_id, int) or order_id <= 0:
            raise RealityInputError("order_id_invalid")
        if not isinstance(updated, dict):
            raise RealityInputError("material_row_not_dict")
        self._validate_material_row(updated)

        row = await self._get_row(order_id)
        if row is None:
            raise RealityInputError("reality_not_initialised", str(order_id))

        existing = self._parse_materials(row.materials_json)
        if material_index < 0 or material_index >= len(existing):
            raise RealityInputError("material_index_out_of_range", str(material_index))

        merged: Dict[str, Any] = {
            "material_id": updated.get("material_id") or None,
            "material_name": str(updated.get("material_name", "")).strip(),
            "quantity": float(updated["quantity"]),
            "unit": str(updated["unit"]).strip().lower(),
            "task_id": updated.get("task_id") or existing[material_index].get("task_id"),
            "added_at": existing[material_index].get("added_at", datetime.now(timezone.utc).isoformat()),
        }
        for opt in (
            "reported_by_employee_id",
            "reported_by_employee_name",
            "consumption_notes",
            "reported_at",
        ):
            if updated.get(opt) is not None:
                merged[opt] = updated.get(opt)
            elif existing[material_index].get(opt) is not None:
                merged[opt] = existing[material_index].get(opt)
        existing[material_index] = merged

        row.materials_json = json.dumps(existing)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def remove_material(
        self,
        order_id: int,
        material_index: int,
    ) -> ExecutionReality:
        """Remove a material row by index.

        Does NOT update inventory. Does NOT modify cost engine.
        """
        if not isinstance(order_id, int) or order_id <= 0:
            raise RealityInputError("order_id_invalid")

        row = await self._get_row(order_id)
        if row is None:
            raise RealityInputError("reality_not_initialised", str(order_id))

        existing = self._parse_materials(row.materials_json)
        if material_index < 0 or material_index >= len(existing):
            raise RealityInputError("material_index_out_of_range", str(material_index))

        existing.pop(material_index)
        row.materials_json = json.dumps(existing)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def get_materials(self, order_id: int) -> List[Dict[str, Any]]:
        """Read-only: return materials list for an order's reality."""
        if not isinstance(order_id, int) or order_id <= 0:
            raise RealityInputError("order_id_invalid")
        row = await self._get_row(order_id)
        if row is None:
            return []
        return self._parse_materials(row.materials_json)