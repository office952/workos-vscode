"""Server-backed production work file upload/download for Work Intake."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from services.intake_requests import Intake_requestsService
from validators.intake_product_spec import validate_intake_product_spec

logger = logging.getLogger(__name__)

STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage" / "intake_work_files"
_MAX_WORK_FILE_BYTES = 50 * 1024 * 1024
_ALLOWED_EXTENSIONS = frozenset({
    ".cdr",
    ".pdf",
    ".svg",
    ".dxf",
    ".ai",
    ".eps",
    ".zip",
    ".dwg",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".psd",
})

WORK_FILE_ROLES = frozenset({
    "master_work_file",
    "cnc_source",
    "print_source",
    "cut_source",
    "modeling_source",
    "reference",
})

WORK_FILE_USABLE_FOR = frozenset({
    "cnc",
    "print",
    "cutter_plotter",
    "modeling",
    "mounting",
    "sales",
    "general_production",
})


def sanitize_work_file_filename(raw_name: str) -> str:
    base = (raw_name or "").strip().replace("\\", "/").split("/")[-1]
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    suffix = Path(base).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise ValueError(
            "Extensie neacceptată. Acceptate: CDR, PDF, SVG, DXF, AI, EPS, ZIP, DWG, PNG, JPG, TIFF, PSD."
        )
    if base in {"", ".", ".."}:
        raise ValueError("Filename is not valid")
    return base


def _work_file_download_path(intake_code: str, file_id: str) -> str:
    return (
        f"/api/v1/entities/intake_requests/by-code/{intake_code}/work-files/{file_id}/download"
    )


class WorkIntakeWorkFileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.intake_service = Intake_requestsService(db)

    async def upload(
        self,
        *,
        intake_code: str,
        upload: UploadFile,
        uploaded_by: str | None = None,
    ) -> dict[str, Any]:
        code = (intake_code or "").strip()
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "ok": False,
                    "code": "invalid_request",
                    "error": "intake_code is required",
                },
            )

        intake = await self.intake_service.get_by_field("code", code)
        if not intake:
            return {
                "ok": False,
                "code": "intake_not_found",
                "error": f"Intake request {code} was not found.",
            }

        raw_name = upload.filename or ""
        try:
            stored_name = sanitize_work_file_filename(raw_name)
        except ValueError as exc:
            return {"ok": False, "code": "invalid_file", "error": str(exc)}

        raw_bytes = await upload.read()
        if not raw_bytes:
            return {"ok": False, "code": "invalid_file", "error": "Fișierul este gol."}
        if len(raw_bytes) > _MAX_WORK_FILE_BYTES:
            return {
                "ok": False,
                "code": "invalid_file",
                "error": f"Fișierul depășește limita de {_MAX_WORK_FILE_BYTES} bytes.",
            }

        file_id = uuid.uuid4().hex
        storage_dir = STORAGE_ROOT / code
        storage_dir.mkdir(parents=True, exist_ok=True)
        disk_name = f"{file_id}_{stored_name}"
        storage_path = storage_dir / disk_name
        storage_path.write_bytes(raw_bytes)
        logger.info("Stored intake work file at %s", storage_path)

        uploaded_at = datetime.now(timezone.utc).isoformat()
        content_type = (upload.content_type or "").strip().lower() or "application/octet-stream"
        extension = Path(stored_name).suffix.lower()
        display_name = raw_name.strip() or stored_name

        work_file: dict[str, Any] = {
            "id": file_id,
            "fileName": display_name,
            "storedFileName": disk_name,
            "fileUrl": _work_file_download_path(code, file_id),
            "mimeType": content_type,
            "extension": extension,
            "sizeBytes": len(raw_bytes),
            "role": "master_work_file",
            "usableFor": ["cnc", "print", "cutter_plotter", "modeling", "general_production"],
            "uploadedAt": uploaded_at,
            "isPrimary": True,
        }
        if uploaded_by:
            work_file["uploadedBy"] = uploaded_by

        existing_spec: dict[str, Any] = {}
        if intake.product_spec_json:
            try:
                parsed = json.loads(intake.product_spec_json)
                if isinstance(parsed, dict):
                    existing_spec = parsed
            except json.JSONDecodeError:
                existing_spec = {}

        existing_rows = existing_spec.get("workFileAttachments")
        rows: list[dict[str, Any]] = []
        if isinstance(existing_rows, list):
            for item in existing_rows:
                if isinstance(item, dict):
                    row = dict(item)
                    if work_file.get("isPrimary"):
                        row["isPrimary"] = False
                    rows.append(row)

        rows.append(work_file)
        merged_spec = {**existing_spec, "workFileAttachments": rows}

        try:
            product_spec_json = validate_intake_product_spec(merged_spec) or {}
        except ValueError as exc:
            logger.error("product_spec_json validation failed for %s: %s", code, exc)
            return {
                "ok": False,
                "code": "invalid_file",
                "error": f"Validarea product_spec_json a eșuat: {exc}",
            }

        updated = await self.intake_service.update(
            intake.id,
            {"product_spec_json": json.dumps(product_spec_json, ensure_ascii=False)},
        )
        if not updated:
            return {
                "ok": False,
                "code": "intake_not_found",
                "error": f"Intake request {code} could not be updated.",
            }

        saved_rows = product_spec_json.get("workFileAttachments") or []
        saved = next((r for r in saved_rows if r.get("id") == file_id), work_file)

        return {
            "ok": True,
            "intake_code": code,
            "work_file": saved,
            "product_spec_json": product_spec_json,
        }

    async def download(
        self,
        *,
        intake_code: str,
        file_id: str,
    ) -> FileResponse | dict[str, Any]:
        code = (intake_code or "").strip()
        fid = (file_id or "").strip()
        if not code or not fid:
            return {
                "ok": False,
                "code": "invalid_request",
                "error": "intake_code and file_id are required",
            }

        intake = await self.intake_service.get_by_field("code", code)
        if not intake:
            return {
                "ok": False,
                "code": "intake_not_found",
                "error": f"Intake request {code} was not found.",
            }

        existing_spec: dict[str, Any] = {}
        if intake.product_spec_json:
            try:
                parsed = json.loads(intake.product_spec_json)
                if isinstance(parsed, dict):
                    existing_spec = parsed
            except json.JSONDecodeError:
                existing_spec = {}

        rows = existing_spec.get("workFileAttachments")
        if not isinstance(rows, list):
            return {"ok": False, "code": "invalid_request", "error": "Work file not found."}

        match = next(
            (row for row in rows if isinstance(row, dict) and str(row.get("id") or "").strip() == fid),
            None,
        )
        if not match:
            return {"ok": False, "code": "invalid_request", "error": "Work file not found."}

        stored_name = str(match.get("storedFileName") or "").strip()
        if not stored_name:
            return {"ok": False, "code": "invalid_request", "error": "Work file storage reference missing."}

        storage_path = STORAGE_ROOT / code / stored_name
        if not storage_path.is_file():
            return {"ok": False, "code": "invalid_request", "error": "Work file missing on storage."}

        download_name = str(match.get("fileName") or stored_name).strip() or stored_name
        media_type = str(match.get("mimeType") or "application/octet-stream")

        return FileResponse(
            path=str(storage_path),
            media_type=media_type,
            filename=download_name,
        )
