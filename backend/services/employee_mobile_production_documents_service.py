"""Production document handoff for Employee Mobile — intake work files on assigned orders."""

from __future__ import annotations

from fastapi import HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.production_document_handoff_service import (
    BLOCKED_DOCUMENT_SOURCES,
    BLOCKED_DOCUMENT_TYPES,
    BLOCKED_URL_FRAGMENTS,
    employee_mobile_work_file_download_path,
    load_intake_work_files_for_order,
    merge_production_documents,
    normalize_intake_work_file_for_mobile,
    resolve_order_intake_code,
)
from services.work_intake_work_file_service import STORAGE_ROOT, WorkIntakeWorkFileService

__all__ = [
    "BLOCKED_DOCUMENT_SOURCES",
    "BLOCKED_DOCUMENT_TYPES",
    "BLOCKED_URL_FRAGMENTS",
    "employee_mobile_work_file_download_path",
    "merge_production_documents",
    "normalize_intake_work_file_document",
    "load_intake_work_files_for_order",
    "resolve_order_intake_code",
    "employee_has_assigned_order_task",
    "download_order_work_file_for_employee",
    "work_file_exists_on_disk",
]


def normalize_intake_work_file_document(row: dict, *, order_id: int):
    return normalize_intake_work_file_for_mobile(row, order_id=order_id)


async def employee_has_assigned_order_task(
    db: AsyncSession,
    *,
    employee_id: int,
    order_id: int,
) -> bool:
    plan_sql = text("SELECT tasks_json FROM execution_plan WHERE order_id = :oid LIMIT 1")
    plan_row = (await db.execute(plan_sql, {"oid": order_id})).mappings().first()
    if not plan_row:
        return False

    reality_sql = text("SELECT tasks_json FROM execution_reality WHERE order_id = :oid LIMIT 1")
    reality_row = (await db.execute(reality_sql, {"oid": order_id})).mappings().first()

    def _parse_json_list(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            try:
                import json

                parsed = json.loads(val)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return []

    reality_lookup = {
        str(rt.get("task_id") or ""): rt
        for rt in _parse_json_list(reality_row.get("tasks_json") if reality_row else [])
        if isinstance(rt, dict)
    }

    for plan_task in _parse_json_list(plan_row.get("tasks_json")):
        if not isinstance(plan_task, dict):
            continue
        task_id = str(plan_task.get("task_id") or "")
        rt = reality_lookup.get(task_id, {})
        plan_ctx = {"assigned_employee_id": plan_task.get("assigned_employee_id")}
        reality_ctx = {
            "employee_id": rt.get("employee_id"),
            "completed_by_employee_id": rt.get("completed_by_employee_id"),
        }
        from services.employee_mobile_tasks_service import task_belongs_to_employee

        if task_belongs_to_employee(plan_ctx, reality_ctx, employee_id):
            return True
    return False


async def download_order_work_file_for_employee(
    db: AsyncSession,
    *,
    order_id: int,
    file_id: str,
    employee_id: int,
) -> FileResponse:
    if not await employee_has_assigned_order_task(db, employee_id=employee_id, order_id=order_id):
        raise HTTPException(status_code=403, detail={"error": "task_not_assigned_to_employee"})

    intake_code = await resolve_order_intake_code(db, order_id)
    if not intake_code:
        raise HTTPException(status_code=404, detail={"error": "order_intake_not_linked"})

    service = WorkIntakeWorkFileService(db)
    result = await service.download(intake_code=intake_code, file_id=file_id)
    if isinstance(result, dict):
        code = str(result.get("code") or "invalid_request")
        status = 404 if code == "intake_not_found" else 400
        raise HTTPException(status_code=status, detail={"error": code, "message": result.get("error")})
    return result


def work_file_exists_on_disk(intake_code: str, stored_file_name: str) -> bool:
    path = STORAGE_ROOT / intake_code / stored_file_name
    return path.is_file()
