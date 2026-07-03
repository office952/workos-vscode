"""TPL-VOLUMETRIC-LETTERS — vector / production file readiness policy.

DWG is accepted as a source attachment but not auto-analyzed.
SVG layer analysis exists (VectorAssetService / SvgLayerAnalysisService) but geometry
is only trusted when vector_analysis_status=analyzed with explicit metrics source.
DXF has no parser — treated as attached_unanalyzed until manual review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from services.svg_manual_layer_mapping import (
    derive_vector_layer_mapping_status,
    letters_template_manually_mapped,
    normalize_svg_layer_mappings,
)

VECTOR_FILE_TYPES = frozenset({"svg", "dxf", "dwg", "other"})
VECTOR_ANALYSIS_STATUSES = frozenset({
    "not_provided",
    "attached_unanalyzed",
    "analyzed",
    "analysis_failed",
    "manual_review_approved",
})
VECTOR_LAYER_MAPPING_STATUSES = frozenset({
    "not_required",
    "pending",
    "mapped",
    "failed",
})
VECTOR_METRICS_SOURCES = frozenset({
    "manual",
    "svg_analysis",
    "dxf_analysis",
    "dwg_manual",
})

WARN_LETTERS_VECTOR_FILE_REQUIRED = "letters_vector_file_required"
WARN_DWG_ANALYSIS_NOT_SUPPORTED = "dwg_analysis_not_supported"
WARN_DXF_ANALYSIS_NOT_SUPPORTED = "dxf_analysis_not_supported"
WARN_VECTOR_MANUAL_REVIEW_REQUIRED = "vector_manual_review_required"
WARN_VECTOR_ANALYSIS_PENDING = "vector_analysis_pending"
WARN_VECTOR_ANALYSIS_FAILED = "vector_analysis_failed"
WARN_VECTOR_FILE_TYPE_UNSUPPORTED = "vector_file_type_unsupported"
WARN_VECTOR_LAYER_MAPPING_FAILED = "vector_layer_mapping_failed"
WARN_VECTOR_LAYER_MAPPING_PENDING = "vector_layer_mapping_pending"


@dataclass(frozen=True)
class VolumetricVectorReadinessResult:
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    vector_gate_satisfied: bool = False
    vector_file_present: bool = False


def infer_vector_file_type_from_name(filename: str) -> Optional[str]:
    name = (filename or "").strip().lower()
    if not name or "." not in name:
        return None
    ext = name.rsplit(".", 1)[-1]
    if ext == "svg":
        return "svg"
    if ext == "dxf":
        return "dxf"
    if ext == "dwg":
        return "dwg"
    return "other"


def _spec_bool(spec: dict[str, Any], key: str) -> Optional[bool]:
    val = spec.get(key)
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        low = val.strip().lower()
        if low in ("true", "1", "yes"):
            return True
        if low in ("false", "0", "no"):
            return False
    return None


def _file_is_present(spec: Optional[dict[str, Any]]) -> bool:
    if not spec:
        return False
    if _spec_bool(spec, "vector_file_present") is True:
        return True
    if str(spec.get("vector_file_name") or "").strip():
        return True
    if str(spec.get("vector_file_url") or "").strip():
        return True
    if spec.get("vector_attachment_id") is not None:
        return True
    return False


def _resolve_file_type(spec: dict[str, Any]) -> str:
    declared = str(spec.get("vector_file_type") or "").strip().lower()
    if declared in VECTOR_FILE_TYPES:
        return declared
    inferred = infer_vector_file_type_from_name(str(spec.get("vector_file_name") or ""))
    return inferred or "other"


def _svg_layer_mappings(spec: dict[str, Any]) -> dict[str, str]:
    try:
        return normalize_svg_layer_mappings(spec.get("svg_layer_mappings"))
    except ValueError:
        return {}


def _has_confirmed_geometry(spec: dict[str, Any]) -> bool:
    if str(spec.get("vector_metrics_source") or "").strip().lower() == "manual":
        return True
    face = spec.get("letter_face_area_m2")
    perimeter = spec.get("letter_perimeter_m")
    try:
        return face is not None and perimeter is not None and float(face) > 0 and float(perimeter) > 0
    except (TypeError, ValueError):
        return False


def _resolve_layer_mapping_status(spec: dict[str, Any]) -> str:
    explicit = str(spec.get("vector_layer_mapping_status") or "").strip().lower()
    if explicit in VECTOR_LAYER_MAPPING_STATUSES:
        return explicit
    return derive_vector_layer_mapping_status(_svg_layer_mappings(spec))


def _resolve_analysis_status(spec: dict[str, Any], file_type: str) -> str:
    raw = str(spec.get("vector_analysis_status") or "").strip().lower()
    if raw in VECTOR_ANALYSIS_STATUSES:
        return raw
    if _spec_bool(spec, "vector_manual_review_approved") is True:
        return "manual_review_approved"
    if file_type in ("dwg", "dxf", "other"):
        return "attached_unanalyzed"
    if file_type == "svg":
        return "attached_unanalyzed"
    return "not_provided"


def evaluate_volumetric_vector_readiness(
    product_spec: Optional[dict[str, Any]],
    *,
    template_level: bool = False,
) -> VolumetricVectorReadinessResult:
    """Evaluate vector file readiness for volumetric letters.

    template_level=True: template has no intake file — always warn file required.
    template_level=False: evaluate product_spec_json vector metadata.
    """
    if template_level or not product_spec:
        return VolumetricVectorReadinessResult(
            warnings=[WARN_LETTERS_VECTOR_FILE_REQUIRED],
            blockers=[],
            vector_gate_satisfied=False,
            vector_file_present=False,
        )

    if not _file_is_present(product_spec):
        return VolumetricVectorReadinessResult(
            warnings=[WARN_LETTERS_VECTOR_FILE_REQUIRED],
            blockers=[],
            vector_gate_satisfied=False,
            vector_file_present=False,
        )

    file_type = _resolve_file_type(product_spec)
    analysis_status = _resolve_analysis_status(product_spec, file_type)
    layer_status = _resolve_layer_mapping_status(product_spec)
    mappings = _svg_layer_mappings(product_spec)
    letters_mapped = letters_template_manually_mapped(mappings)
    manual_approved = (
        analysis_status == "manual_review_approved"
        or _spec_bool(product_spec, "vector_manual_review_approved") is True
    )

    warnings: list[str] = []
    blockers: list[str] = []
    gate = False

    if file_type == "other" and not manual_approved:
        warnings.append(WARN_VECTOR_FILE_TYPE_UNSUPPORTED)
        warnings.append(WARN_VECTOR_MANUAL_REVIEW_REQUIRED)

    elif file_type == "dwg":
        if manual_approved:
            gate = True
            warnings.append(WARN_DWG_ANALYSIS_NOT_SUPPORTED)
        else:
            warnings.append(WARN_DWG_ANALYSIS_NOT_SUPPORTED)
            warnings.append(WARN_VECTOR_MANUAL_REVIEW_REQUIRED)

    elif file_type == "dxf":
        if manual_approved:
            gate = True
            warnings.append(WARN_DXF_ANALYSIS_NOT_SUPPORTED)
        else:
            warnings.append(WARN_DXF_ANALYSIS_NOT_SUPPORTED)
            warnings.append(WARN_VECTOR_MANUAL_REVIEW_REQUIRED)

    elif file_type == "svg":
        if analysis_status == "analyzed":
            if layer_status == "failed":
                warnings.append(WARN_VECTOR_LAYER_MAPPING_FAILED)
            elif layer_status == "pending" and not letters_mapped:
                warnings.append(WARN_VECTOR_LAYER_MAPPING_PENDING)
            if manual_approved or _has_confirmed_geometry(product_spec):
                gate = True
            else:
                warnings.append(WARN_VECTOR_MANUAL_REVIEW_REQUIRED)
        elif analysis_status == "analysis_failed":
            warnings.append(WARN_VECTOR_ANALYSIS_FAILED)
            if manual_approved:
                gate = True
            else:
                if layer_status == "pending" and not letters_mapped:
                    warnings.append(WARN_VECTOR_LAYER_MAPPING_PENDING)
                warnings.append(WARN_VECTOR_MANUAL_REVIEW_REQUIRED)
        elif manual_approved:
            gate = True
            if layer_status == "pending" and not letters_mapped:
                warnings.append(WARN_VECTOR_LAYER_MAPPING_PENDING)
            warnings.append(WARN_VECTOR_ANALYSIS_PENDING)
        else:
            if layer_status == "pending" and not letters_mapped:
                warnings.append(WARN_VECTOR_LAYER_MAPPING_PENDING)
            warnings.append(WARN_VECTOR_ANALYSIS_PENDING)
            warnings.append(WARN_VECTOR_MANUAL_REVIEW_REQUIRED)

    else:
        warnings.append(WARN_VECTOR_FILE_TYPE_UNSUPPORTED)
        warnings.append(WARN_VECTOR_MANUAL_REVIEW_REQUIRED)

    return VolumetricVectorReadinessResult(
        warnings=warnings,
        blockers=blockers,
        vector_gate_satisfied=gate,
        vector_file_present=True,
    )
