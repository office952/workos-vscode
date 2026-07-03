"""Server-backed SVG upload + analysis for Work Intake V2."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.intake_requests import Intake_requestsService
from services.svg_layer_analysis_service import SvgLayerAnalysisService
from services.svg_metrics_service import _MAX_SVG_BYTES
from services.work_intake_svg_spec_mapper import (
    build_vector_spec_updates,
    sanitize_upload_filename,
)
from validators.intake_product_spec import validate_intake_product_spec

logger = logging.getLogger(__name__)

STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage" / "intake_svg_uploads"


class WorkIntakeSvgUploadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.intake_service = Intake_requestsService(db)

    async def upload_and_analyze(
        self,
        *,
        intake_code: str,
        upload: UploadFile,
    ) -> dict[str, Any]:
        code = (intake_code or "").strip()
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"ok": False, "code": "invalid_request", "error": "intake_code is required"},
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
            filename = sanitize_upload_filename(raw_name)
        except ValueError as exc:
            return {"ok": False, "code": "invalid_svg", "error": str(exc)}

        content_type = (upload.content_type or "").strip().lower()
        if content_type and "svg" not in content_type and content_type != "application/octet-stream":
            return {
                "ok": False,
                "code": "invalid_svg",
                "error": f"Tip MIME neacceptat: {content_type}",
            }

        raw_bytes = await upload.read()
        if not raw_bytes:
            return {"ok": False, "code": "invalid_svg", "error": "Fișierul este gol."}

        if len(raw_bytes) > _MAX_SVG_BYTES:
            return {
                "ok": False,
                "code": "invalid_svg",
                "error": f"Fișierul depășește limita de {_MAX_SVG_BYTES} bytes.",
            }

        try:
            svg_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return {
                "ok": False,
                "code": "invalid_svg",
                "error": "SVG-ul trebuie să fie text UTF-8.",
            }

        if "<svg" not in svg_text.lower():
            return {
                "ok": False,
                "code": "invalid_svg",
                "error": "Conținutul nu pare a fi SVG valid.",
            }

        storage_dir = STORAGE_ROOT / code
        storage_dir.mkdir(parents=True, exist_ok=True)
        storage_path = storage_dir / filename
        storage_path.write_bytes(raw_bytes)
        logger.info("Stored intake SVG upload at %s", storage_path)

        analysis = SvgLayerAnalysisService.analyze(
            svg_text,
            source_file_name=filename,
        )

        if analysis.parse_status not in {"parsed", "parsed_sanitized"}:
            return {
                "ok": False,
                "code": "parse_failed",
                "error": analysis.error_detail or analysis.error_code or "Analiza SVG a eșuat.",
                "vector_parse_status": "failed",
            }

        selected_at = datetime.now(timezone.utc).isoformat()
        vector_updates = build_vector_spec_updates(
            filename=filename,
            size_bytes=len(raw_bytes),
            content_type=content_type or "image/svg+xml",
            svg_text=svg_text,
            analysis=analysis,
            selected_at=selected_at,
        )

        existing_spec: dict[str, Any] = {}
        if intake.product_spec_json:
            try:
                parsed = json.loads(intake.product_spec_json)
                if isinstance(parsed, dict):
                    existing_spec = parsed
            except json.JSONDecodeError:
                existing_spec = {}

        merged_spec = {**existing_spec, **vector_updates}
        try:
            product_spec_json = validate_intake_product_spec(merged_spec) or {}
        except ValueError as exc:
            logger.error("product_spec_json validation failed for %s: %s", code, exc)
            return {
                "ok": False,
                "code": "parse_failed",
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

        detected_layers = [
            {
                "id": layer["id"],
                "label": layer["label"],
                "element_count": layer["element_count"],
                "suggested_role": layer["suggested_role"],
                "confirmed_role": layer["confirmed_role"],
            }
            for layer in (product_spec_json.get("vector_detected_layers") or [])
        ]

        return {
            "ok": True,
            "intake_code": code,
            "filename": filename,
            "size_bytes": len(raw_bytes),
            "content_type": content_type or "image/svg+xml",
            "vector_parse_status": product_spec_json.get("vector_parse_status"),
            "vector_svg_viewbox": product_spec_json.get("vector_svg_viewbox"),
            "vector_detected_layer_count": product_spec_json.get("vector_detected_layer_count"),
            "vector_detected_layers": detected_layers,
            "product_spec_json": product_spec_json,
        }
