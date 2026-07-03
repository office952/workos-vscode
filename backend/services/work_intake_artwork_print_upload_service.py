"""Server-backed artwork print file upload for Work Intake V2 policromie assignments."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.intake_requests import Intake_requestsService
from validators.intake_product_spec import validate_intake_product_spec

logger = logging.getLogger(__name__)

STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage" / "intake_artwork_prints"
_MAX_PRINT_BYTES = 25 * 1024 * 1024
_ALLOWED_EXTENSIONS = frozenset({
    ".pdf",
    ".ai",
    ".eps",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".psd",
})


def sanitize_artwork_print_filename(raw_name: str) -> str:
    base = (raw_name or "").strip().replace("\\", "/").split("/")[-1]
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    suffix = Path(base).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Extensie neacceptată: {suffix or '(lipsă)'}. Acceptate: PDF, AI, EPS, PNG, JPG, TIFF, PSD."
        )
    if base in {"", ".", ".."}:
        raise ValueError("Filename is not valid")
    return base


class WorkIntakeArtworkPrintUploadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.intake_service = Intake_requestsService(db)

    async def upload(
        self,
        *,
        intake_code: str,
        layer_id: str,
        upload: UploadFile,
    ) -> dict[str, Any]:
        code = (intake_code or "").strip()
        layer = (layer_id or "").strip()
        if not code or not layer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "ok": False,
                    "code": "invalid_request",
                    "error": "intake_code and layer_id are required",
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
            filename = sanitize_artwork_print_filename(raw_name)
        except ValueError as exc:
            return {"ok": False, "code": "invalid_file", "error": str(exc)}

        suffix = Path(filename).suffix.lower()
        if suffix not in _ALLOWED_EXTENSIONS:
            return {
                "ok": False,
                "code": "invalid_file",
                "error": f"Extensie neacceptată: {suffix or '(lipsă)'}. Acceptate: PDF, AI, EPS, PNG, JPG, TIFF, PSD.",
            }

        raw_bytes = await upload.read()
        if not raw_bytes:
            return {"ok": False, "code": "invalid_file", "error": "Fișierul este gol."}
        if len(raw_bytes) > _MAX_PRINT_BYTES:
            return {
                "ok": False,
                "code": "invalid_file",
                "error": f"Fișierul depășește limita de {_MAX_PRINT_BYTES} bytes.",
            }

        storage_dir = STORAGE_ROOT / code / layer
        storage_dir.mkdir(parents=True, exist_ok=True)
        storage_path = storage_dir / filename
        storage_path.write_bytes(raw_bytes)
        logger.info("Stored artwork print upload at %s", storage_path)

        uploaded_at = datetime.now(timezone.utc).isoformat()
        content_type = (upload.content_type or "").strip().lower() or "application/octet-stream"
        print_file = {
            "fileName": raw_name.strip() or filename,
            "storedFileName": filename,
            "sizeBytes": len(raw_bytes),
            "contentType": content_type,
            "uploadedAt": uploaded_at,
        }

        existing_spec: dict[str, Any] = {}
        if intake.product_spec_json:
            try:
                parsed = json.loads(intake.product_spec_json)
                if isinstance(parsed, dict):
                    existing_spec = parsed
            except json.JSONDecodeError:
                existing_spec = {}

        assignments = existing_spec.get("svgArtworkFinishAssignments")
        if not isinstance(assignments, list):
            assignments = []

        updated_rows: list[dict[str, Any]] = []
        matched = False
        for item in assignments:
            if not isinstance(item, dict):
                continue
            row_layer_id = str(item.get("layerId") or "").strip()
            if row_layer_id == layer:
                merged_row = {**item, "printFile": print_file}
                updated_rows.append(merged_row)
                matched = True
            else:
                updated_rows.append(item)

        if not matched:
            layer_name = layer
            pending = existing_spec.get("svgArtworkLayersPending")
            if isinstance(pending, list):
                for pending_item in pending:
                    if not isinstance(pending_item, dict):
                        continue
                    if str(pending_item.get("layerId") or "").strip() == layer:
                        layer_name = str(pending_item.get("layerName") or layer).strip() or layer
                        break
            updated_rows.append(
                {
                    "layerId": layer,
                    "layerName": layer_name,
                    "executionType": "needs_decision",
                    "colorMode": "polychrome",
                    "confirmedByOperator": False,
                    "printFile": print_file,
                }
            )

        merged_spec = {
            **existing_spec,
            "svgArtworkFinishAssignments": updated_rows,
        }
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

        return {
            "ok": True,
            "intake_code": code,
            "layer_id": layer,
            "print_file": print_file,
            "product_spec_json": product_spec_json,
        }
