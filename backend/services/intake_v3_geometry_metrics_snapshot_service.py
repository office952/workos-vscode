"""Intake V3 geometry metrics snapshot — technical inputs from confirmed model + SVG path analysis."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from schemas.intake_v3 import (
    GEOMETRY_METRICS_SNAPSHOT_VERSION,
    ConfirmedProductionModel,
    IntakeV3GeometryMetricAreas,
    IntakeV3GeometryMetricCounts,
    IntakeV3GeometryMetricDimensions,
    IntakeV3GeometryMetricPerimeters,
    IntakeV3GeometryMetricWarning,
    IntakeV3GeometryMetricsSnapshot,
    IntakeV3GeometryMetricsSnapshotResponse,
    IntakeV3OperationGeometryMetric,
    IntakeV3Workspace,
    RawSvgAnalysis,
)
from services.intake_v3_guarded_convert_to_order_service import check_existing_order_for_iv3_quote
from services.intake_v3_material_quantity_breakdown_service import (
    Iv3SourceContext,
    load_iv3_source_context,
)
from services.intake_v3_real_commercial_quote_creation_service import INTAKE_V3_SOURCE_MODULE
from services.svg_metrics_service import SvgMetricsService


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _positive_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _warning(code: str, message: str, *, source: str) -> IntakeV3GeometryMetricWarning:
    return IntakeV3GeometryMetricWarning(code=code, message=message, source=source)


def build_path_geometry_summary_from_svg_text(
    svg_text: str,
    *,
    source_file_name: str | None = None,
) -> dict[str, Any] | None:
    """Parse SVG paths once at upload — no CostEngine, no persistence of raw SVG."""
    from services.svg_sanitization_service import (
        WARN_SVG_SANITIZED_DOCTYPE_REMOVED,
        prepare_svg_text_for_safe_geometry_parsing,
    )

    prep = prepare_svg_text_for_safe_geometry_parsing(
        svg_text,
        source_file_name=source_file_name,
    )
    if not prep.ok:
        return {
            "parse_status": "failed",
            "error_code": prep.error_code,
            "error_detail": prep.error_detail,
            "operator_message": prep.operator_message,
            "warnings": list(prep.warnings),
        }

    parse_text = prep.svg_text or svg_text
    parsed = SvgMetricsService.parse_svg_metrics(parse_text)
    if parsed.parse_status != "parsed":
        return {
            "parse_status": parsed.parse_status,
            "error_code": parsed.error_code,
            "error_detail": parsed.error_detail,
            "warnings": list(parsed.warnings),
        }
    metrics = parsed.metrics
    summary_warnings = list(parsed.warnings)
    if WARN_SVG_SANITIZED_DOCTYPE_REMOVED in prep.warnings:
        summary_warnings = list(dict.fromkeys([*prep.warnings, *summary_warnings]))
    summary: dict[str, Any] = {
        "parse_status": parsed.parse_status,
        "metrics_version": parsed.metrics_version,
        "bbox_w_mm": metrics.bbox_w_mm,
        "bbox_h_mm": metrics.bbox_h_mm,
        "area_mm2_approx": metrics.area_mm2_approx,
        "perimeter_mm_approx": metrics.perimeter_mm_approx,
        "warnings": summary_warnings,
    }
    if prep.sanitization is not None:
        summary["sanitization"] = prep.sanitization.to_dict()
        summary["doctype_removed_for_safe_parse"] = True
    from services.intake_v3_svg_layer_path_geometry import build_layer_path_geometry_from_svg_text

    layer_data = build_layer_path_geometry_from_svg_text(parse_text)
    if layer_data:
        layer_warnings = layer_data.pop("warnings", [])
        summary.update(layer_data)
        summary["warnings"] = list(
            dict.fromkeys([*summary.get("warnings", []), *layer_warnings])
        )
    return summary


def snapshot_to_legacy_geometry_dict(snapshot: IntakeV3GeometryMetricsSnapshot) -> dict[str, Any]:
    """Flatten snapshot for material breakdown geometry source merging."""
    legacy: dict[str, Any] = {
        "geometry_metrics_snapshot": True,
        "geometry_snapshot_source": snapshot.metric_source,
        "geometry_status": snapshot.geometry_status,
        "real_letters_count": snapshot.counts.real_letter_count,
        "letter_count": snapshot.counts.real_letter_count,
        "cut_contour_count": snapshot.counts.cut_contour_count,
        "inner_hole_count": snapshot.counts.inner_hole_count,
        "width_mm": snapshot.dimensions.width_mm,
        "height_mm": snapshot.dimensions.height_mm,
        "depth_mm": snapshot.dimensions.depth_mm,
        "bounding_box_area_m2": snapshot.dimensions.area_m2,
        "face_area_m2": snapshot.areas.face_area_m2,
        "backing_area_m2": snapshot.areas.backing_area_m2,
        "vinyl_area_m2": snapshot.areas.vinyl_area_m2,
        "estimated_area_m2": snapshot.areas.estimated_area_m2,
    }
    per = snapshot.perimeters
    if per.face_cutting_perimeter_ml is not None:
        legacy["face_cutting_perimeter_ml"] = per.face_cutting_perimeter_ml
        legacy["cutting_perimeter_ml"] = per.cutting_perimeter_ml or per.face_cutting_perimeter_ml
    if per.total_letter_perimeter_ml is not None:
        legacy["total_letter_perimeter_ml"] = per.total_letter_perimeter_ml
        legacy["letter_perimeter_m"] = per.total_letter_perimeter_ml
    if per.return_material_perimeter_ml is not None:
        legacy["return_material_perimeter_ml"] = per.return_material_perimeter_ml
    if per.bevel_perimeter_ml is not None:
        legacy["bevel_perimeter_ml"] = per.bevel_perimeter_ml
    if per.face_cutting_perimeter_ml is not None:
        legacy["face_cutting_perimeter_ml"] = per.face_cutting_perimeter_ml
    classification = getattr(snapshot, "path_perimeter_classification", None)
    if isinstance(classification, dict):
        legacy["path_perimeter_classification"] = classification
        legacy["perimeter_classification_status"] = classification.get("classification_status")
        legacy["perimeter_classification_confidence"] = classification.get("confidence")
        legacy["geometry_path_perimeter_classification"] = True
    if snapshot.layer_role_confirmation_status:
        legacy["layer_role_confirmation_status"] = snapshot.layer_role_confirmation_status
    return legacy


def resolve_geometry_status(snapshot: IntakeV3GeometryMetricsSnapshot) -> str:
    if snapshot.counts.real_letter_count <= 0:
        return "geometry_missing"
    has_area = snapshot.areas.face_area_m2 is not None or snapshot.areas.estimated_area_m2 is not None
    has_any_perimeter = any(
        value is not None
        for value in (
            snapshot.perimeters.face_cutting_perimeter_ml,
            snapshot.perimeters.total_letter_perimeter_ml,
            snapshot.perimeters.return_material_perimeter_ml,
            snapshot.perimeters.bevel_perimeter_ml,
        )
    )
    if has_area and has_any_perimeter and snapshot.confidence == "high":
        return "geometry_complete"
    if has_area or snapshot.counts.cut_contour_count > 0:
        return "geometry_partial"
    return "geometry_missing"


def parse_snapshot_from_sections(sections: dict[str, Any]) -> IntakeV3GeometryMetricsSnapshot | None:
    raw = sections.get("geometry_metrics_snapshot")
    if not isinstance(raw, dict) or not raw:
        return None
    try:
        return IntakeV3GeometryMetricsSnapshot.model_validate(raw)
    except Exception:
        return None


def parse_snapshot_from_workspace(workspace: IntakeV3Workspace | None) -> IntakeV3GeometryMetricsSnapshot | None:
    if workspace is None or not workspace.geometry_metrics_snapshot:
        return None
    if isinstance(workspace.geometry_metrics_snapshot, dict):
        try:
            return IntakeV3GeometryMetricsSnapshot.model_validate(workspace.geometry_metrics_snapshot)
        except Exception:
            return None
    return None


def build_geometry_metrics_snapshot(
    *,
    workspace: IntakeV3Workspace | None,
    sections: dict[str, Any] | None = None,
    source_type: str,
    source_id: str,
    path_geometry_summary: dict[str, Any] | None = None,
) -> IntakeV3GeometryMetricsSnapshot:
    sections = sections or {}
    warnings: list[IntakeV3GeometryMetricWarning] = []
    source_keys: list[str] = []

    confirmed: ConfirmedProductionModel | None = None
    if workspace and workspace.confirmed_production_model:
        confirmed = workspace.confirmed_production_model
        source_keys.append("confirmed_production_model")
    else:
        raw_confirmed = sections.get("confirmed_production_model_snapshot")
        if isinstance(raw_confirmed, dict):
            try:
                confirmed = ConfirmedProductionModel.model_validate(raw_confirmed)
                source_keys.append("confirmed_production_model_snapshot")
            except Exception:
                confirmed = None

    counts = IntakeV3GeometryMetricCounts()
    if confirmed:
        counts = IntakeV3GeometryMetricCounts(
            real_letter_count=int(confirmed.letter_count or 0),
            cut_contour_count=int(confirmed.cut_contour_count or 0),
            inner_hole_count=int(confirmed.inner_hole_count or 0),
        )
    elif workspace and workspace.raw_svg_analysis:
        raw = workspace.raw_svg_analysis
        counts = IntakeV3GeometryMetricCounts(
            real_letter_count=0,
            cut_contour_count=int(raw.closed_contour_count or 0),
            inner_hole_count=int(raw.estimated_inner_hole_count or 0),
        )
        source_keys.append("raw_svg_analysis")

    dimensions = IntakeV3GeometryMetricDimensions()
    bbox_source = "estimated"
    if workspace:
        req = workspace.client_request
        width = _positive_float(req.width_mm)
        height = _positive_float(req.height_mm)
        depth = _positive_float(req.depth_mm)
        if width and height:
            dimensions = IntakeV3GeometryMetricDimensions(
                width_mm=width,
                height_mm=height,
                depth_mm=depth,
                area_m2=round((width * height) / 1_000_000.0, 6),
                bounding_box_source="confirmed_dimensions",
            )
            bbox_source = "confirmed_dimensions"
            source_keys.append("client_request.dimensions")

    path_summary = path_geometry_summary
    if path_summary is None and workspace and workspace.path_geometry_summary:
        path_summary = workspace.path_geometry_summary
    if path_summary is None and isinstance(sections.get("workspace_payload_snapshot"), dict):
        nested = sections["workspace_payload_snapshot"].get("path_geometry_summary")
        if isinstance(nested, dict):
            path_summary = nested

    if path_summary and path_summary.get("parse_status") == "parsed":
        source_keys.append("path_geometry_summary")
        bbox_w = _positive_float(path_summary.get("bbox_w_mm"))
        bbox_h = _positive_float(path_summary.get("bbox_h_mm"))
        if bbox_w and bbox_h and dimensions.width_mm is None:
            dimensions = IntakeV3GeometryMetricDimensions(
                width_mm=bbox_w,
                height_mm=bbox_h,
                area_m2=round((bbox_w * bbox_h) / 1_000_000.0, 6),
                bounding_box_source="path_bbox",
            )
            bbox_source = "path_bbox"

    areas = IntakeV3GeometryMetricAreas()
    area_quality = "missing"
    if path_summary and path_summary.get("parse_status") == "parsed":
        area_mm2 = _positive_float(path_summary.get("area_mm2_approx"))
        if area_mm2:
            area_m2 = round(area_mm2 / 1_000_000.0, 6)
            areas = IntakeV3GeometryMetricAreas(
                face_area_m2=area_m2,
                backing_area_m2=area_m2,
                estimated_area_m2=area_m2,
                vinyl_area_m2=area_m2,
            )
            area_quality = "path_derived"
    if areas.face_area_m2 is None and dimensions.area_m2 is not None:
        areas = IntakeV3GeometryMetricAreas(
            face_area_m2=dimensions.area_m2,
            backing_area_m2=dimensions.area_m2,
            estimated_area_m2=dimensions.area_m2,
            vinyl_area_m2=dimensions.area_m2,
        )
        area_quality = "estimated"
        warnings.append(
            _warning(
                "area_estimated_from_dimensions",
                "Face/backing area estimated from width × height — not path geometry.",
                source="client_request.dimensions",
            )
        )

    perimeters = IntakeV3GeometryMetricPerimeters()
    perimeter_present = False
    if not perimeter_present:
        warnings.append(
            _warning(
                "perimeter_missing",
                "Path perimeter is not available; downstream modules may use partial geometry.",
                source="geometry_metrics_snapshot.perimeters",
            )
        )

    operation_geometry = {
        "face_cutting": IntakeV3OperationGeometryMetric(
            available=counts.cut_contour_count > 0,
            quality="partial" if counts.cut_contour_count > 0 else "missing",
            basis=["cut_contour_count", "confirmed_production_model"],
        ),
        "backing_cutting": IntakeV3OperationGeometryMetric(
            available=areas.backing_area_m2 is not None,
            quality=area_quality if areas.backing_area_m2 else "missing",
            basis=["dimensions"] if areas.backing_area_m2 else [],
        ),
        "return_modeling": IntakeV3OperationGeometryMetric(
            available=False,
            quality="missing",
            basis=[],
        ),
        "bevel": IntakeV3OperationGeometryMetric(
            available=False,
            quality="missing",
            basis=[],
        ),
    }

    metric_sources: list[str] = []
    if confirmed:
        metric_sources.append("confirmed_model")
    if path_summary and path_summary.get("parse_status") == "parsed":
        metric_sources.append("svg_path_analysis")
    if area_quality == "estimated":
        metric_sources.append("estimated")
    metric_source = "mixed" if len(metric_sources) > 1 else (metric_sources[0] if metric_sources else "estimated")

    if metric_source == "svg_path_analysis" and confirmed:
        confidence = "medium"
    elif confirmed and area_quality == "estimated":
        confidence = "medium"
    elif confirmed:
        confidence = "partial"
    else:
        confidence = "low"

    template = PILOT_TEMPLATE_CODE
    if workspace:
        template = workspace.product_selection.template_code or PILOT_TEMPLATE_CODE

    snapshot = IntakeV3GeometryMetricsSnapshot(
        schema_version=GEOMETRY_METRICS_SNAPSHOT_VERSION,
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=source_type,
        source_id=source_id,
        template_key=template,
        generated_at=_utcnow_iso(),
        metric_source=metric_source,
        confidence=confidence,
        counts=counts,
        dimensions=dimensions,
        perimeters=perimeters,
        areas=areas,
        operation_geometry=operation_geometry,
        warnings=warnings,
        source_keys=list(dict.fromkeys(source_keys)),
        holes_not_letters=True,
    )
    snapshot = snapshot.model_copy(update={"geometry_status": resolve_geometry_status(snapshot)})

    from services.intake_v3_geometry_path_perimeter_classification_service import (
        classify_geometry_path_perimeters,
        merge_classification_into_geometry_snapshot,
    )

    layer_role_confirmation = None
    layer_role_confirmation_status = None
    if workspace and workspace.layer_role_confirmation_snapshot:
        layer_role_confirmation = workspace.layer_role_confirmation_snapshot
        if isinstance(layer_role_confirmation, dict):
            layer_role_confirmation_status = layer_role_confirmation.get("confirmation_status")
            source_keys.append("layer_role_confirmation_snapshot")
    elif isinstance(sections.get("layer_role_confirmation_snapshot"), dict):
        layer_role_confirmation = sections["layer_role_confirmation_snapshot"]
        layer_role_confirmation_status = layer_role_confirmation.get("confirmation_status")
        source_keys.append("layer_role_confirmation_snapshot")

    classification = classify_geometry_path_perimeters(
        workspace=workspace,
        sections=sections,
        path_summary=path_summary,
        confirmed=confirmed,
        template_key=template,
        layer_role_confirmation=layer_role_confirmation,
    )
    merged = merge_classification_into_geometry_snapshot(snapshot, classification)
    if "path_perimeter_classification" not in source_keys:
        source_keys.append("path_perimeter_classification")
    return merged.model_copy(
        update={
            "layer_role_confirmation_status": layer_role_confirmation_status or "missing",
            "source_keys": list(dict.fromkeys(source_keys)),
        }
    )


def persist_geometry_metrics_snapshot_to_payload(
    payload: dict[str, Any],
    snapshot: IntakeV3GeometryMetricsSnapshot,
) -> dict[str, Any]:
    updated = dict(payload)
    updated["geometry_metrics_snapshot"] = snapshot.model_dump(mode="json")
    return updated


def build_geometry_metrics_snapshot_response(
    context: Iv3SourceContext,
    *,
    snapshot: IntakeV3GeometryMetricsSnapshot | None = None,
) -> IntakeV3GeometryMetricsSnapshotResponse:
    if not context.is_intake_v3:
        return IntakeV3GeometryMetricsSnapshotResponse(
            source_module=INTAKE_V3_SOURCE_MODULE,
            source_type=context.source_type,
            source_id=context.source_id,
            order_id=context.order.id if context.order else None,
            is_intake_v3=False,
            snapshot_available=False,
            geometry_status="geometry_missing",
            warnings=[
                _warning(
                    "not_intake_v3_source",
                    "Source is not an Intake V3 order/quote/workspace payload.",
                    source="source_detection",
                )
            ],
        )

    if snapshot is None:
        snapshot = parse_snapshot_from_sections(context.sections)
    if snapshot is None:
        snapshot = parse_snapshot_from_workspace(context.workspace)
    if snapshot is None and context.workspace is not None:
        snapshot = build_geometry_metrics_snapshot(
            workspace=context.workspace,
            sections=context.sections,
            source_type=context.source_type,
            source_id=context.source_id,
        )

    workspace_id = None
    if context.quote_linkage:
        workspace_id = context.quote_linkage.get("source_workspace_id")
    if context.order_linkage and not workspace_id:
        workspace_id = context.order_linkage.get("source_workspace_id")
    if context.source_type == "workspace":
        workspace_id = context.source_id

    from services.intake_v3_layer_role_confirmation_propagation_service import (
        downstream_propagation_fields,
    )

    propagation_fields, _, stale_warning_pairs = downstream_propagation_fields(context)
    snapshot_warnings = list(snapshot.warnings) if snapshot else []
    for code, message in stale_warning_pairs:
        snapshot_warnings.append(
            _warning(code, message, source="layer_role_confirmation_propagation")
        )

    return IntakeV3GeometryMetricsSnapshotResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=context.source_type,
        source_id=context.source_id,
        order_id=context.order.id if context.order else None,
        quote_id=context.quote.id if context.quote else None,
        source_workspace_id=str(workspace_id) if workspace_id else None,
        is_intake_v3=True,
        snapshot_available=snapshot is not None,
        geometry_status=snapshot.geometry_status if snapshot else "geometry_missing",
        snapshot=snapshot,
        warnings=snapshot_warnings,
        **propagation_fields,
    )


async def get_geometry_metrics_snapshot_for_order(
    db: AsyncSession,
    order_id: int,
) -> IntakeV3GeometryMetricsSnapshotResponse:
    context = await load_iv3_source_context(db, order_id=order_id)
    return build_geometry_metrics_snapshot_response(context)


async def get_geometry_metrics_snapshot_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3GeometryMetricsSnapshotResponse:
    context = await load_iv3_source_context(db, quote_id=quote_id)
    if context.order is None and context.quote is not None:
        linked = await check_existing_order_for_iv3_quote(db, quote_id)
        if linked is not None:
            context.order = linked
    return build_geometry_metrics_snapshot_response(context)


async def get_geometry_metrics_snapshot_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3GeometryMetricsSnapshotResponse:
    context = await load_iv3_source_context(db, workspace_id=workspace_id)
    return build_geometry_metrics_snapshot_response(context)


def build_and_attach_geometry_snapshot_for_workspace_payload(
    payload: dict[str, Any],
    *,
    workspace_id: str,
) -> tuple[dict[str, Any], IntakeV3GeometryMetricsSnapshot]:
    workspace = IntakeV3Workspace.model_validate(payload)
    snapshot = build_geometry_metrics_snapshot(
        workspace=workspace,
        source_type="workspace",
        source_id=workspace_id,
        path_geometry_summary=workspace.path_geometry_summary,
    )
    return persist_geometry_metrics_snapshot_to_payload(payload, snapshot), snapshot
