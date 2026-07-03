from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from services.storage_key_validation import validate_storage_object_key


OWNER_TYPES = ("intake_request", "product_template", "standalone")
PARSE_STATUSES = ("pending", "parsed", "failed")


class SvgMetricsPreviewRequest(BaseModel):
    svg_text: str = Field(..., min_length=1, max_length=500000)


class SvgSanitizationMetadataSchema(BaseModel):
    original_file_has_doctype: bool
    analysis_sanitized: bool
    sanitization_reason: str | None = None
    source_file_name: str | None = None
    source_content_hash: str | None = None
    analysis_content_hash: str | None = None


class SvgLayerAnalysisRequest(BaseModel):
    svg_text: str = Field(..., min_length=1, max_length=500000)
    known_template_codes: list[str] | None = None
    source_file_name: str | None = Field(
        default=None,
        max_length=255,
        description="Original filename for sanitization metadata (analysis copy only).",
    )
    manual_layer_mappings: dict[str, str] | None = Field(
        default=None,
        description="Operator manual layer name → mapping target (intake svg_layer_mappings).",
    )


class SvgLayerMetricsPayloadSchema(BaseModel):
    bbox_width_mm: float | None = None
    bbox_height_mm: float | None = None
    bbox_area_m2: float | None = None
    path_perimeter_m: float | None = None
    path_area_m2: float | None = None
    metrics_confidence: str = "unavailable"


class SvgLayerAnalysisRowSchema(BaseModel):
    svg_layer_id: str
    svg_layer_name: str
    mapped_template_code: str | None = None
    mapping_status: str
    suggested_template_code: str | None = None
    human_description: str
    detected_kind: str
    metrics: SvgLayerMetricsPayloadSchema
    quote_input_suggestions: dict[str, float | int | None] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    mapped_by: str | None = None


class SvgLayerAnalysisResponse(BaseModel):
    parse_status: Literal["parsed", "parsed_sanitized", "failed"]
    error_code: str | None = None
    error_detail: str | None = None
    layers: list[SvgLayerAnalysisRowSchema] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    sanitization: SvgSanitizationMetadataSchema | None = None
    preview_svg: str | None = Field(
        default=None,
        description="Safe sanitized SVG for static operator preview (not pricing input).",
    )


class SvgMetrics(BaseModel):
    bbox_w_mm: float | None = None
    bbox_h_mm: float | None = None
    area_mm2_approx: float | None = None
    perimeter_mm_approx: float | None = None


class SvgMetricsParseResult(BaseModel):
    parse_status: Literal["parsed", "failed"]
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_detail: str | None = None
    metrics: SvgMetrics
    metrics_version: str = "v1"


class VectorAssetRegisterRequest(BaseModel):
    bucket_name: str = Field(..., min_length=3, max_length=63)
    object_key: str = Field(..., min_length=1, max_length=1024)
    original_filename: str = Field(..., min_length=1, max_length=255)
    content_type_reported: str | None = Field(default=None, max_length=255)
    file_size_bytes: int | None = Field(default=None, ge=1, le=10485760)
    owner_type: Literal["intake_request", "product_template", "standalone"] = "standalone"
    owner_id: int | None = Field(default=None, ge=1)
    source_format: Literal["svg"] = "svg"
    svg_text_dev: str | None = Field(default=None, max_length=500000)

    @field_validator("object_key")
    @classmethod
    def validate_object_key(cls, v: str) -> str:
        return validate_storage_object_key(v)

    @field_validator("original_filename")
    @classmethod
    def validate_original_filename(cls, v: str) -> str:
        if not v.lower().endswith(".svg"):
            raise ValueError("original_filename must end with .svg")
        return v


class VectorAssetDTO(BaseModel):
    id: int
    asset_code: str
    owner_type: Literal["intake_request", "product_template", "standalone"]
    owner_id: int | None = None
    original_filename: str
    bucket_name: str
    object_key: str
    source_format: Literal["svg"]
    content_type_reported: str | None = None
    file_size_bytes: int | None = None
    content_sha256: str | None = None
    parse_status: Literal["pending", "parsed", "failed"]
    parse_warnings: list[str] = Field(default_factory=list)
    parse_error_code: str | None = None
    parse_error_detail: str | None = None
    bbox_w_mm: float | None = None
    bbox_h_mm: float | None = None
    area_mm2_approx: float | None = None
    perimeter_mm_approx: float | None = None
    metrics_version: str
    created_by: str | None = None
    created_at: str
    updated_at: str


class VectorAssetRegisterResponse(BaseModel):
    asset: VectorAssetDTO


class VectorAssetPreviewResponse(BaseModel):
    parse_status: Literal["parsed", "failed"]
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_detail: str | None = None
    metrics: SvgMetrics
    metrics_version: str = "v1"


class VectorAssetRegisterNotPersistedReason(BaseModel):
    code: str
    detail: str


class VectorAssetSheetFitPreviewResponse(BaseModel):
    asset_id: int
    material_id: int
    bbox_w_mm: float | None = None
    bbox_h_mm: float | None = None
    material_usable_width_mm: float | None = None
    material_usable_height_mm: float | None = None
    material_usable_length_mm: float | None = None
    fits_without_rotation: bool = False
    fits_with_rotation: bool = False
    recommended_rotation: Literal["none", "rotate_90", "not_fit", "cannot_evaluate"]
    fit_status: Literal["fits", "fits_rotated", "not_fit", "cannot_evaluate"]
    fit_reason: str
    warnings: list[str] = Field(default_factory=list)
