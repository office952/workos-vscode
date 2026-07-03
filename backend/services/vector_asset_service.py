from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory_materials import Inventory_materials
from models.vector_assets import Vector_assets
from schemas.auth import UserResponse
from schemas.vector_assets import (
    SvgMetricsParseResult,
    VectorAssetDTO,
    VectorAssetRegisterRequest,
    VectorAssetSheetFitPreviewResponse,
)
from services.storage_key_validation import validate_storage_object_key
from services.svg_layer_analysis_service import SvgLayerAnalysisService
from services.svg_metrics_service import SvgMetricsService


def _now_iso(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.isoformat()


def _to_mm(value: float | None, unit: str | None) -> float | None:
    if value is None:
        return None
    normalized_unit = (unit or "unknown").strip().lower()
    if normalized_unit == "mm":
        return float(value)
    if normalized_unit == "cm":
        return float(value) * 10.0
    if normalized_unit == "m":
        return float(value) * 1000.0
    return None


class VectorAssetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_dto(row: Vector_assets) -> VectorAssetDTO:
        warnings: list[str] = []
        try:
            raw = json.loads(row.parse_warnings_json or "[]")
            if isinstance(raw, list):
                warnings = [str(item) for item in raw]
        except Exception:
            warnings = ["warnings_json_decode_failed"]

        return VectorAssetDTO(
            id=row.id,
            asset_code=row.asset_code,
            owner_type=row.owner_type,
            owner_id=row.owner_id,
            original_filename=row.original_filename,
            bucket_name=row.bucket_name,
            object_key=row.object_key,
            source_format="svg",
            content_type_reported=row.content_type_reported,
            file_size_bytes=row.file_size_bytes,
            content_sha256=row.content_sha256,
            parse_status=row.parse_status,
            parse_warnings=warnings,
            parse_error_code=row.parse_error_code,
            parse_error_detail=row.parse_error_detail,
            bbox_w_mm=row.bbox_w_mm,
            bbox_h_mm=row.bbox_h_mm,
            area_mm2_approx=row.area_mm2_approx,
            perimeter_mm_approx=row.perimeter_mm_approx,
            metrics_version=row.metrics_version,
            created_by=row.created_by,
            created_at=_now_iso(row.created_at),
            updated_at=_now_iso(row.updated_at),
        )

    @staticmethod
    def _make_asset_code() -> str:
        return f"VAS-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _validate_register_request(req: VectorAssetRegisterRequest) -> None:
        if req.source_format.lower() != "svg":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="source_format must be svg")

        if not req.original_filename.lower().endswith(".svg"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="original_filename must end with .svg")

        validate_storage_object_key(req.object_key)

        if req.content_type_reported and "svg" not in req.content_type_reported.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="content_type_reported must indicate SVG when provided",
            )

        if req.file_size_bytes is not None and req.file_size_bytes > 500000:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file_size_bytes exceeds svg limit")

    async def preview_metrics(self, *, svg_text: str) -> SvgMetricsParseResult:
        parsed = SvgMetricsService.parse_svg_metrics(svg_text)
        return SvgMetricsParseResult(
            parse_status=parsed.parse_status,
            warnings=parsed.warnings,
            error_code=parsed.error_code,
            error_detail=parsed.error_detail,
            metrics={
                "bbox_w_mm": parsed.metrics.bbox_w_mm,
                "bbox_h_mm": parsed.metrics.bbox_h_mm,
                "area_mm2_approx": parsed.metrics.area_mm2_approx,
                "perimeter_mm_approx": parsed.metrics.perimeter_mm_approx,
            },
            metrics_version=parsed.metrics_version,
        )

    async def analyze_layers(
        self,
        *,
        svg_text: str,
        known_template_codes: list[str] | None = None,
        active_template_codes: list[str] | None = None,
        source_file_name: str | None = None,
        manual_layer_mappings: dict[str, str] | None = None,
    ) -> dict:
        if active_template_codes is None:
            from services.active_template_scope import load_quote_active_template_codes

            active_template_codes = await load_quote_active_template_codes(self.db)
        result = SvgLayerAnalysisService.analyze(
            svg_text,
            known_template_codes=known_template_codes,
            active_template_codes=active_template_codes,
            source_file_name=source_file_name,
            manual_layer_mappings=manual_layer_mappings,
        )
        return result.to_dict()

    async def register_from_storage(
        self,
        *,
        req: VectorAssetRegisterRequest,
        current_user: UserResponse,
    ) -> VectorAssetDTO:
        self._validate_register_request(req)

        existing = (
            await self.db.execute(select(Vector_assets).where(Vector_assets.object_key == req.object_key))
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="object_key already registered")

        if not req.svg_text_dev:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "svg_text_dev is required in Sprint A when direct storage content read is not implemented"
                ),
            )

        parsed = SvgMetricsService.parse_svg_metrics(req.svg_text_dev)
        warnings_json = json.dumps(parsed.warnings, ensure_ascii=True)
        content_sha256 = hashlib.sha256(req.svg_text_dev.encode("utf-8")).hexdigest()

        row = Vector_assets(
            asset_code=self._make_asset_code(),
            owner_type=req.owner_type,
            owner_id=req.owner_id,
            original_filename=req.original_filename,
            bucket_name=req.bucket_name,
            object_key=req.object_key,
            source_format="svg",
            content_type_reported=req.content_type_reported,
            file_size_bytes=req.file_size_bytes,
            content_sha256=content_sha256,
            parse_status=parsed.parse_status,
            parse_warnings_json=warnings_json,
            parse_error_code=parsed.error_code,
            parse_error_detail=parsed.error_detail,
            bbox_w_mm=parsed.metrics.bbox_w_mm,
            bbox_h_mm=parsed.metrics.bbox_h_mm,
            area_mm2_approx=parsed.metrics.area_mm2_approx,
            perimeter_mm_approx=parsed.metrics.perimeter_mm_approx,
            metrics_version=parsed.metrics_version,
            created_by=(current_user.email if current_user and current_user.email else None),
        )

        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)

        return self._to_dto(row)

    async def get_asset(self, *, asset_id: int) -> VectorAssetDTO:
        row = (await self.db.execute(select(Vector_assets).where(Vector_assets.id == asset_id))).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="vector asset not found")
        return self._to_dto(row)

    async def get_sheet_fit_preview(self, *, asset_id: int, material_id: int) -> VectorAssetSheetFitPreviewResponse:
        asset = (await self.db.execute(select(Vector_assets).where(Vector_assets.id == asset_id))).scalar_one_or_none()
        if asset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="vector asset not found")

        material = (
            await self.db.execute(select(Inventory_materials).where(Inventory_materials.id == material_id))
        ).scalar_one_or_none()
        if material is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="inventory material not found")

        warnings: list[str] = []
        bbox_w_mm = asset.bbox_w_mm
        bbox_h_mm = asset.bbox_h_mm

        if asset.parse_status != "parsed":
            return VectorAssetSheetFitPreviewResponse(
                asset_id=asset.id,
                material_id=material.id,
                bbox_w_mm=bbox_w_mm,
                bbox_h_mm=bbox_h_mm,
                material_usable_width_mm=None,
                material_usable_height_mm=None,
                material_usable_length_mm=None,
                fits_without_rotation=False,
                fits_with_rotation=False,
                recommended_rotation="cannot_evaluate",
                fit_status="cannot_evaluate",
                fit_reason="Asset parse_status is not parsed.",
                warnings=["asset_not_parsed"],
            )

        if bbox_w_mm is None or bbox_h_mm is None or bbox_w_mm <= 0 or bbox_h_mm <= 0:
            return VectorAssetSheetFitPreviewResponse(
                asset_id=asset.id,
                material_id=material.id,
                bbox_w_mm=bbox_w_mm,
                bbox_h_mm=bbox_h_mm,
                material_usable_width_mm=None,
                material_usable_height_mm=None,
                material_usable_length_mm=None,
                fits_without_rotation=False,
                fits_with_rotation=False,
                recommended_rotation="cannot_evaluate",
                fit_status="cannot_evaluate",
                fit_reason="Asset bbox metrics are missing or invalid.",
                warnings=["asset_bbox_missing"],
            )

        sheet_type = (material.sheet_format_type or "unknown").strip().lower()
        if sheet_type not in {"sheet", "roll"}:
            return VectorAssetSheetFitPreviewResponse(
                asset_id=asset.id,
                material_id=material.id,
                bbox_w_mm=bbox_w_mm,
                bbox_h_mm=bbox_h_mm,
                material_usable_width_mm=None,
                material_usable_height_mm=None,
                material_usable_length_mm=None,
                fits_without_rotation=False,
                fits_with_rotation=False,
                recommended_rotation="cannot_evaluate",
                fit_status="cannot_evaluate",
                fit_reason="Material does not have sheet/roll format for fit evaluation.",
                warnings=["unsupported_sheet_format_type"],
            )

        material_usable_width_mm = _to_mm(
            material.usable_width if material.usable_width and material.usable_width > 0 else material.sheet_width,
            material.sheet_unit,
        )
        material_usable_height_mm = _to_mm(
            material.usable_height if material.usable_height and material.usable_height > 0 else material.sheet_height,
            material.sheet_unit,
        )

        # For current inventory schema, length follows usable height when no dedicated roll length exists.
        material_usable_length_mm = material_usable_height_mm

        if material_usable_width_mm is None or material_usable_height_mm is None:
            return VectorAssetSheetFitPreviewResponse(
                asset_id=asset.id,
                material_id=material.id,
                bbox_w_mm=bbox_w_mm,
                bbox_h_mm=bbox_h_mm,
                material_usable_width_mm=material_usable_width_mm,
                material_usable_height_mm=material_usable_height_mm,
                material_usable_length_mm=material_usable_length_mm,
                fits_without_rotation=False,
                fits_with_rotation=False,
                recommended_rotation="cannot_evaluate",
                fit_status="cannot_evaluate",
                fit_reason="Material usable dimensions are missing or unit is unsupported.",
                warnings=["material_usable_dimensions_missing"],
            )

        fits_without_rotation = bbox_w_mm <= material_usable_width_mm and bbox_h_mm <= material_usable_height_mm
        fits_with_rotation = bbox_h_mm <= material_usable_width_mm and bbox_w_mm <= material_usable_height_mm

        if fits_without_rotation:
            fit_status = "fits"
            fit_reason = "Asset fits material usable dimensions without rotation."
            recommended_rotation = "none"
        elif fits_with_rotation:
            fit_status = "fits_rotated"
            fit_reason = "Asset fits only when rotated by 90 degrees."
            recommended_rotation = "rotate_90"
        else:
            fit_status = "not_fit"
            fit_reason = "Asset does not fit material usable dimensions."
            recommended_rotation = "not_fit"

        if sheet_type == "roll":
            warnings.append("roll_format_uses_height_as_length_proxy")

        return VectorAssetSheetFitPreviewResponse(
            asset_id=asset.id,
            material_id=material.id,
            bbox_w_mm=bbox_w_mm,
            bbox_h_mm=bbox_h_mm,
            material_usable_width_mm=material_usable_width_mm,
            material_usable_height_mm=material_usable_height_mm,
            material_usable_length_mm=material_usable_length_mm,
            fits_without_rotation=fits_without_rotation,
            fits_with_rotation=fits_with_rotation,
            recommended_rotation=recommended_rotation,
            fit_status=fit_status,
            fit_reason=fit_reason,
            warnings=warnings,
        )
