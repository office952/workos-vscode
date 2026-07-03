"""Read-only SVG multi-layer analysis for preliminary quote preparation."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from typing import Any

from services.svg_layer_template_mapping import (
    DEFAULT_KNOWN_TEMPLATE_CODES,
    map_svg_layer_to_template,
)
from services.svg_metrics_service import SvgMetricsService, _local_name
from services.svg_manual_layer_mapping import apply_manual_layer_mappings
from services.svg_preview_service import build_safe_svg_preview
from services.svg_sanitization_service import (
    WARN_SVG_SANITIZED_DOCTYPE_REMOVED,
    sanitize_svg_for_analysis,
)


@dataclass(frozen=True)
class SvgLayerMetricsPayload:
    bbox_width_mm: float | None = None
    bbox_height_mm: float | None = None
    bbox_area_m2: float | None = None
    path_perimeter_m: float | None = None
    path_area_m2: float | None = None
    metrics_confidence: str = "unavailable"  # exact | estimated | unavailable


@dataclass(frozen=True)
class SvgLayerAnalysisRow:
    svg_layer_id: str
    svg_layer_name: str
    mapped_template_code: str | None
    mapping_status: str
    suggested_template_code: str | None
    human_description: str
    detected_kind: str
    metrics: SvgLayerMetricsPayload
    quote_input_suggestions: dict[str, float | int | None]
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    mapped_by: str | None = None


@dataclass(frozen=True)
class SvgLayerAnalysisResult:
    parse_status: str
    error_code: str | None = None
    error_detail: str | None = None
    layers: list[SvgLayerAnalysisRow] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    sanitization: dict[str, Any] | None = None
    preview_svg: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _layer_label(elem: ET.Element) -> str | None:
    for key, value in elem.attrib.items():
        local = key.split("}", 1)[-1]
        if local in {"label", "data-name"} and value and value.strip():
            return value.strip()
    layer_id = elem.attrib.get("id")
    if layer_id and layer_id.strip():
        return layer_id.strip()
    return None


def _is_layer_group(elem: ET.Element) -> bool:
    if _local_name(elem.tag) != "g":
        return False
    for key, value in elem.attrib.items():
        local = key.split("}", 1)[-1]
        if local == "groupmode" and str(value).strip().lower() == "layer":
            return True
    if elem.attrib.get("id") or any(
        k.split("}", 1)[-1] == "label" for k in elem.attrib
    ):
        return True
    return False


def _discover_layers(root: ET.Element) -> list[tuple[str, str, ET.Element]]:
    """Return (layer_id, layer_name, element) for each graphical layer group."""
    found: list[tuple[str, str, ET.Element]] = []
    seen_ids: set[str] = set()

    def _walk(parent: ET.Element, depth: int) -> None:
        for child in list(parent):
            if _local_name(child.tag) != "g":
                continue
            if not _is_layer_group(child) and depth > 0:
                continue
            name = _layer_label(child)
            if not name:
                _walk(child, depth + 1)
                continue
            layer_id = child.attrib.get("id") or f"layer-{len(found) + 1}"
            if layer_id in seen_ids:
                layer_id = f"{layer_id}-{len(found) + 1}"
            seen_ids.add(layer_id)
            found.append((layer_id, name, child))
            # Do not recurse into nested layer groups as separate top layers for v1

    _walk(root, 0)

    if not found:
        # Fallback: direct child groups with any id/label
        for idx, child in enumerate(list(root)):
            if _local_name(child.tag) != "g":
                continue
            name = _layer_label(child) or f"Layer {idx + 1}"
            layer_id = child.attrib.get("id") or f"layer-{idx + 1}"
            found.append((layer_id, name, child))

    return found


def _metrics_payload_from_parse(
    parsed_metrics,
    warnings: list[str],
) -> SvgLayerMetricsPayload:
    m = parsed_metrics
    has_unsupported_path = any(w == "unsupported_path" for w in warnings)
    has_curve_approx = any(
        w in {"path_curve_metrics_approximate", "path_arc_metrics_approximate"}
        or w.startswith("path_command_")
        for w in warnings
    )
    has_geometry = m.bbox_w_mm is not None and m.bbox_h_mm is not None
    if not has_geometry:
        return SvgLayerMetricsPayload(
            metrics_confidence="unavailable",
        )

    confidence = "estimated"
    if has_curve_approx:
        confidence = "estimated"
    elif has_unsupported_path and m.perimeter_mm_approx is None and m.area_mm2_approx is None:
        confidence = "unavailable"

    area_m2 = m.area_mm2_approx / 1_000_000.0 if m.area_mm2_approx else None
    perimeter_m = (
        m.perimeter_mm_approx / 1000.0 if m.perimeter_mm_approx else None
    )

    return SvgLayerMetricsPayload(
        bbox_width_mm=m.bbox_w_mm,
        bbox_height_mm=m.bbox_h_mm,
        bbox_area_m2=round(area_m2, 6) if area_m2 is not None else None,
        path_perimeter_m=round(perimeter_m, 6) if perimeter_m is not None else None,
        path_area_m2=round(area_m2, 6) if area_m2 is not None else None,
        metrics_confidence=confidence,
    )


def _acm_casetted_quote_suggestions(
    metrics: SvgLayerMetricsPayload,
    warnings: list[str],
) -> dict[str, float | int | None]:
    if metrics.metrics_confidence == "unavailable":
        return {
            "panel_width_mm": None,
            "panel_height_mm": None,
            "panel_area_m2": None,
            "panel_perimeter_m": None,
        }
    return {
        "panel_width_mm": metrics.bbox_width_mm,
        "panel_height_mm": metrics.bbox_height_mm,
        "panel_area_m2": metrics.bbox_area_m2,
        "panel_perimeter_m": metrics.path_perimeter_m,
        "acm_thickness_mm": 3,
        "return_depth_mm": None,
        "rear_lip_mm": 25,
        "fold_sides": None,
        "v_groove_angle_deg": 135,
        "frame_clearance_mm": None,
    }


def _cut_acm_quote_suggestions(
    metrics: SvgLayerMetricsPayload,
    warnings: list[str],
) -> dict[str, float | int | None]:
    if metrics.metrics_confidence == "unavailable":
        return {"cut_area_m2": None, "cut_perimeter_m": None}
    return {
        "cut_area_m2": metrics.path_area_m2,
        "cut_perimeter_m": metrics.path_perimeter_m,
        "acm_thickness_mm": 3,
    }


def _volumetric_quote_suggestions(
    metrics: SvgLayerMetricsPayload,
    warnings: list[str],
) -> dict[str, float | int | None]:
    """Suggestions only — never owner-confirmed geometry."""
    if metrics.metrics_confidence == "unavailable":
        return {
            "letter_face_area_m2": None,
            "letter_perimeter_m": None,
            "letter_count": None,
            "mounting_template_area_m2": None,
        }

    suggestions: dict[str, float | int | None] = {
        "letter_face_area_m2": metrics.path_area_m2,
        "letter_perimeter_m": metrics.path_perimeter_m,
        "letter_count": None,
        "mounting_template_area_m2": metrics.bbox_area_m2,
    }
    if metrics.metrics_confidence == "unavailable":
        suggestions["letter_perimeter_m"] = None
        suggestions["letter_face_area_m2"] = None
    return suggestions


class SvgLayerAnalysisService:
    @classmethod
    def analyze(
        cls,
        svg_text: str,
        *,
        known_template_codes: list[str] | None = None,
        active_template_codes: list[str] | None = None,
        source_file_name: str | None = None,
        manual_layer_mappings: dict[str, str] | None = None,
    ) -> SvgLayerAnalysisResult:
        codes = tuple(known_template_codes or DEFAULT_KNOWN_TEMPLATE_CODES)
        active_codes = (
            tuple(active_template_codes)
            if active_template_codes is not None
            else None
        )

        analysis_text = svg_text
        parse_status = "parsed"
        sanitization_meta: dict[str, Any] | None = None
        extra_warnings: list[str] = []

        base = SvgMetricsService.parse_svg_metrics(svg_text)
        if base.parse_status != "parsed":
            from services.svg_sanitization_service import (
                ERROR_SVG_UNSAFE_ENTITY_DECLARATION,
                OPERATOR_MESSAGE_SVG_UNSUPPORTED_XML,
                has_entity_declaration,
                has_internal_dtd_subset,
            )

            if has_entity_declaration(svg_text):
                return cls._failed_result(
                    error_code=ERROR_SVG_UNSAFE_ENTITY_DECLARATION,
                    error_detail="ENTITY declarations are not allowed",
                    warnings=[OPERATOR_MESSAGE_SVG_UNSUPPORTED_XML],
                )
            if has_internal_dtd_subset(svg_text):
                return cls._failed_result(
                    error_code="svg_unsafe_dtd_declaration",
                    error_detail="Internal DTD subsets are not allowed",
                    warnings=[OPERATOR_MESSAGE_SVG_UNSUPPORTED_XML],
                )
            if base.error_code != "xml_unsafe_construct":
                return cls._failed_result(
                    error_code=base.error_code,
                    error_detail=base.error_detail,
                    warnings=list(base.warnings),
                )

            sanitized_text, san_meta = sanitize_svg_for_analysis(
                svg_text,
                source_file_name=source_file_name,
            )
            if sanitized_text is None or san_meta is None:
                return cls._failed_result(
                    error_code=base.error_code,
                    error_detail=base.error_detail,
                    warnings=list(base.warnings),
                )

            base = SvgMetricsService.parse_svg_metrics(sanitized_text)
            if base.parse_status != "parsed":
                return cls._failed_result(
                    error_code=base.error_code,
                    error_detail=base.error_detail,
                    warnings=list(base.warnings),
                )

            analysis_text = sanitized_text
            parse_status = "parsed_sanitized"
            sanitization_meta = san_meta.to_dict()
            extra_warnings.append(WARN_SVG_SANITIZED_DOCTYPE_REMOVED)

        try:
            root = ET.fromstring(analysis_text)
        except ET.ParseError as exc:
            return cls._failed_result(
                error_code="invalid_xml",
                error_detail=str(exc),
            )

        if _local_name(root.tag) != "svg":
            return cls._failed_result(
                error_code="not_svg_root",
                error_detail="Root element must be <svg>",
            )

        layer_groups = _discover_layers(root)
        if not layer_groups:
            return SvgLayerAnalysisResult(
                parse_status=parse_status,
                warnings=[*extra_warnings, "no_svg_layers_found", *base.warnings],
                sanitization=sanitization_meta,
                preview_svg=build_safe_svg_preview(analysis_text),
                summary={
                    "layers_found": 0,
                    "layers_mapped": 0,
                    "layers_unmapped": 0,
                    "layers_calculable_preliminary": 0,
                    "layers_manual_geometry": 0,
                },
            )

        rows: list[SvgLayerAnalysisRow] = []
        for layer_id, layer_name, layer_elem in layer_groups:
            layer_svg = _subtree_as_mini_svg(root, layer_elem)
            layer_parse = SvgMetricsService.parse_svg_metrics(layer_svg)
            mapping = map_svg_layer_to_template(
                layer_name,
                known_template_codes=codes,
                active_template_codes=active_codes,
            )
            metrics = _metrics_payload_from_parse(
                layer_parse.metrics, list(layer_parse.warnings)
            )

            blockers = list(mapping.blockers)
            warnings = list(layer_parse.warnings)

            quote_suggestions: dict[str, float | int | None] = {}
            if mapping.mapped_template_code == "TPL-VOLUMETRIC-LETTERS":
                quote_suggestions = _volumetric_quote_suggestions(metrics, warnings)
                if metrics.metrics_confidence == "unavailable":
                    blockers.append("metrics_unavailable")
                    blockers.append("manual_geometry_required")
                elif quote_suggestions.get("letter_perimeter_m") is None:
                    blockers.append("manual_geometry_required")
            elif mapping.mapped_template_code == "TPL-ACM-CASSETTED-PANEL":
                quote_suggestions = _acm_casetted_quote_suggestions(metrics, warnings)
                if metrics.metrics_confidence == "unavailable":
                    blockers.append("metrics_unavailable")
                    blockers.append("manual_geometry_required")
                elif not quote_suggestions.get("panel_width_mm"):
                    blockers.append("manual_geometry_required")
            elif mapping.mapped_template_code == "TPL-CUT-ACM-LETTERS":
                quote_suggestions = _cut_acm_quote_suggestions(metrics, warnings)
                if metrics.metrics_confidence == "unavailable":
                    blockers.append("metrics_unavailable")
                    blockers.append("manual_geometry_required")
                elif not quote_suggestions.get("cut_area_m2"):
                    blockers.append("manual_geometry_required")
            elif mapping.mapping_status == "mapped":
                quote_suggestions = {}
                if metrics.metrics_confidence == "unavailable":
                    blockers.append("metrics_unavailable")
            else:
                quote_suggestions = {}

            rows.append(
                SvgLayerAnalysisRow(
                    svg_layer_id=layer_id,
                    svg_layer_name=layer_name,
                    mapped_template_code=mapping.mapped_template_code,
                    mapping_status=mapping.mapping_status,
                    suggested_template_code=mapping.suggested_template_code,
                    human_description=mapping.human_description,
                    detected_kind=mapping.detected_kind,
                    metrics=metrics,
                    quote_input_suggestions=quote_suggestions,
                    blockers=sorted(set(blockers)),
                    warnings=warnings,
                )
            )

        mapped = sum(1 for r in rows if r.mapping_status == "mapped")
        unmapped = sum(
            1
            for r in rows
            if r.mapping_status in {"unmapped", "ambiguous", "unsupported", "suggested"}
        )
        quote_ready_codes = (
            set(active_codes)
            if active_codes is not None
            else {
                "TPL-VOLUMETRIC-LETTERS",
                "TPL-ACM-CASSETTED-PANEL",
                "TPL-CUT-ACM-LETTERS",
            }
        )
        calculable = sum(
            1
            for r in rows
            if r.mapping_status == "mapped"
            and r.mapped_template_code in quote_ready_codes
            and "template_not_active_for_quote" not in r.blockers
            and "template_inactive" not in r.blockers
            and "manual_geometry_required" not in r.blockers
            and "metrics_unavailable" not in r.blockers
        )
        manual_geom = sum(
            1
            for r in rows
            if "manual_geometry_required" in r.blockers
            or "metrics_unavailable" in r.blockers
        )

        if manual_layer_mappings:
            patched = apply_manual_layer_mappings(
                rows,
                manual_layer_mappings,
                volumetric_quote_suggestions_fn=_volumetric_quote_suggestions,
            )
            rows = [cls._row_from_dict(item) for item in patched]
            mapped = sum(
                1
                for r in rows
                if r.mapping_status in {"mapped", "mapped_manual"}
            )
            unmapped = sum(
                1
                for r in rows
                if r.mapping_status in {"unmapped", "ambiguous", "unsupported", "suggested"}
            )
            calculable = sum(
                1
                for r in rows
                if r.mapping_status in {"mapped", "mapped_manual"}
                and r.mapped_template_code in quote_ready_codes
                and "template_not_active_for_quote" not in r.blockers
                and "template_inactive" not in r.blockers
                and "manual_geometry_required" not in r.blockers
                and "metrics_unavailable" not in r.blockers
            )
            manual_geom = sum(
                1
                for r in rows
                if "manual_geometry_required" in r.blockers
                or "metrics_unavailable" in r.blockers
            )

        preview_svg = build_safe_svg_preview(analysis_text)

        return SvgLayerAnalysisResult(
            parse_status=parse_status,
            layers=rows,
            warnings=[*extra_warnings, *base.warnings],
            sanitization=sanitization_meta,
            preview_svg=preview_svg,
            summary={
                "layers_found": len(rows),
                "layers_mapped": mapped,
                "layers_unmapped": unmapped,
                "layers_calculable_preliminary": calculable,
                "layers_manual_geometry": manual_geom,
            },
        )

    @staticmethod
    def _row_from_dict(data: dict[str, Any]) -> SvgLayerAnalysisRow:
        metrics_raw = data.get("metrics")
        if isinstance(metrics_raw, SvgLayerMetricsPayload):
            metrics = metrics_raw
        elif isinstance(metrics_raw, dict):
            metrics = SvgLayerMetricsPayload(**metrics_raw)
        else:
            metrics = SvgLayerMetricsPayload()
        return SvgLayerAnalysisRow(
            svg_layer_id=str(data.get("svg_layer_id") or ""),
            svg_layer_name=str(data.get("svg_layer_name") or ""),
            mapped_template_code=data.get("mapped_template_code"),
            mapping_status=str(data.get("mapping_status") or "unmapped"),
            suggested_template_code=data.get("suggested_template_code"),
            human_description=str(data.get("human_description") or ""),
            detected_kind=str(data.get("detected_kind") or ""),
            metrics=metrics,
            quote_input_suggestions=dict(data.get("quote_input_suggestions") or {}),
            blockers=list(data.get("blockers") or []),
            warnings=list(data.get("warnings") or []),
            mapped_by=data.get("mapped_by"),
        )

    @staticmethod
    def _failed_result(
        *,
        error_code: str | None,
        error_detail: str | None,
        warnings: list[str] | None = None,
    ) -> SvgLayerAnalysisResult:
        return SvgLayerAnalysisResult(
            parse_status="failed",
            error_code=error_code,
            error_detail=error_detail,
            warnings=list(warnings or []),
            summary={
                "layers_found": 0,
                "layers_mapped": 0,
                "layers_unmapped": 0,
                "layers_calculable_preliminary": 0,
                "layers_manual_geometry": 0,
            },
        )


def _subtree_as_mini_svg(root: ET.Element, layer_elem: ET.Element) -> str:
    """Wrap layer subtree in svg shell inheriting root dimensions."""
    attrs = " ".join(
        f'{k}="{v}"'
        for k, v in root.attrib.items()
        if k in {"width", "height", "viewBox", "xmlns"}
        or k.startswith("{") and "svg" in k
    )
    if "xmlns" not in root.attrib:
        attrs = f'xmlns="http://www.w3.org/2000/svg" {attrs}'.strip()
    inner = ET.tostring(layer_elem, encoding="unicode")
    return f"<svg {attrs}>{inner}</svg>"
