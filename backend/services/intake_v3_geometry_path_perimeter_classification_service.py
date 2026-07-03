"""Intake V3 geometry path perimeter classification — role-based, no invented perimeters."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from schemas.intake_v3 import (
    ConfirmedProductionModel,
    IntakeV3GeometryMetricPerimeters,
    IntakeV3GeometryMetricWarning,
    IntakeV3GeometryMetricsSnapshot,
    IntakeV3PathPerimeterClassificationResponse,
    IntakeV3Workspace,
    RawSvgAnalysis,
)
from services.intake_v3_material_quantity_breakdown_service import (
    Iv3SourceContext,
    extract_confirmed_production_model,
    load_iv3_source_context,
)
from services.intake_v3_geometry_metrics_snapshot_service import (
    build_geometry_metrics_snapshot,
    parse_snapshot_from_sections,
    parse_snapshot_from_workspace,
)
from services.intake_v3_real_commercial_quote_creation_service import INTAKE_V3_SOURCE_MODULE

PATH_PERIMETER_CLASSIFICATION_VERSION = "path_perimeter_classification_v1"

ROLE_SYNONYMS: dict[str, tuple[str, ...]] = {
    "face": ("face", "fata", "plexi", "plexiglas", "letters", "letter", "litere", "litera"),
    "letters": ("letters", "letter", "litere", "litera", "face", "fata"),
    "backing": ("backing", "spate", "forex", "back", "pvc"),
    "support_panel": ("dibond", "dibond", "acm", "alucobond", "support", "panel"),
    "frame": ("cadru", "frame", "rama"),
    "return": ("return", "cant", "profil", "lateral", "return_material"),
    "bevel": ("bevel", "sanfren", "chamfer"),
    "vinyl": ("vinyl", "colant", "oracal", "folie"),
    "inner_hole": ("hole", "holes", "gol", "goluri", "inner", "counter", "void"),
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_svg_layer_role(layer_name: str | None, explicit_role: str | None = None) -> str:
    if explicit_role:
        normalized = explicit_role.strip().lower()
        if normalized in ROLE_SYNONYMS or normalized == "unknown":
            return normalized
    if not layer_name:
        return "unknown"
    token = layer_name.strip().lower()
    token = re.sub(r"[^a-z0-9_\- ]+", " ", token)
    for role, synonyms in ROLE_SYNONYMS.items():
        for synonym in synonyms:
            if synonym in token or token == synonym:
                return role
    return "unknown"


def _warning(code: str, message: str, *, source: str) -> dict[str, str]:
    return {"code": code, "severity": "warning", "message": message, "source": source}


def _metric_entry(
    value: float | None,
    *,
    quality: str,
    source: str | None,
    basis: list[str],
) -> dict[str, Any]:
    return {
        "value": value,
        "unit": "ml",
        "quality": quality,
        "source": source,
        "basis": basis,
    }


def _mm_to_ml(perimeter_mm: float | None) -> float | None:
    if perimeter_mm is None or perimeter_mm <= 0:
        return None
    return round(perimeter_mm / 1000.0, 6)


def _positive_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def extract_path_geometry_summary(context: Iv3SourceContext) -> dict[str, Any] | None:
    if context.workspace and context.workspace.path_geometry_summary:
        summary = context.workspace.path_geometry_summary
        return summary if isinstance(summary, dict) else None
    nested = context.sections.get("workspace_payload_snapshot")
    if isinstance(nested, dict):
        summary = nested.get("path_geometry_summary")
        if isinstance(summary, dict):
            return summary
    return None


def extract_geometry_metrics_snapshot(context: Iv3SourceContext) -> IntakeV3GeometryMetricsSnapshot | None:
    snapshot = parse_snapshot_from_sections(context.sections)
    if snapshot is None:
        snapshot = parse_snapshot_from_workspace(context.workspace)
    return snapshot


def extract_layer_role_mapping(context: Iv3SourceContext) -> list[dict[str, Any]]:
    mapping: list[dict[str, Any]] = []
    raw = None
    if context.workspace and context.workspace.raw_svg_analysis:
        raw = context.workspace.raw_svg_analysis
    elif isinstance(context.sections.get("raw_svg_analysis_reference"), dict):
        analysis = context.sections["raw_svg_analysis_reference"].get("analysis")
        if isinstance(analysis, dict):
            try:
                raw = RawSvgAnalysis.model_validate(analysis)
            except Exception:
                raw = None
    if raw is None:
        return mapping
    for group_id in raw.detected_groups:
        role = normalize_svg_layer_role(group_id)
        mapping.append(
            {
                "layer_id": group_id,
                "layer_name": group_id,
                "normalized_role": role,
                "mapping_source": "detected_group_id",
                "confidence": "medium" if role != "unknown" else "low",
            }
        )
    return mapping


def classify_geometry_path_perimeters(
    *,
    workspace: IntakeV3Workspace | None,
    sections: dict[str, Any] | None,
    path_summary: dict[str, Any] | None,
    confirmed: ConfirmedProductionModel | None,
    template_key: str = PILOT_TEMPLATE_CODE,
    layer_role_confirmation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sections = sections or {}
    warnings: list[dict[str, str]] = []
    classified_layers: list[dict[str, Any]] = []
    unclassified_layers: list[dict[str, Any]] = []

    if template_key != PILOT_TEMPLATE_CODE:
        return {
            "schema_version": PATH_PERIMETER_CLASSIFICATION_VERSION,
            "classification_status": "unsupported",
            "classification_source": "template",
            "confidence": "low",
            "classified_at": _utcnow_iso(),
            "perimeters": {
                "face_cutting_perimeter_ml": _metric_entry(None, quality="missing", source=None, basis=[]),
                "backing_cutting_perimeter_ml": _metric_entry(None, quality="missing", source=None, basis=[]),
                "return_material_perimeter_ml": _metric_entry(None, quality="missing", source=None, basis=[]),
                "bevel_perimeter_ml": _metric_entry(None, quality="missing", source=None, basis=[]),
            },
            "classified_layers": [],
            "unclassified_layers": [],
            "contour_split": {},
            "warnings": [
                _warning(
                    "unsupported_template",
                    "Path perimeter classification is not supported for this template.",
                    source="template_key",
                )
            ],
        }

    if not path_summary or path_summary.get("parse_status") != "parsed":
        warnings.append(
            _warning(
                "path_geometry_summary_missing",
                "Path geometry summary is missing or not parsed — perimeter classification unavailable.",
                source="path_geometry_summary",
            )
        )
        return {
            "schema_version": PATH_PERIMETER_CLASSIFICATION_VERSION,
            "classification_status": "missing",
            "classification_source": "path_geometry_summary",
            "confidence": "low",
            "classified_at": _utcnow_iso(),
            "perimeters": {
                "face_cutting_perimeter_ml": _metric_entry(None, quality="missing", source=None, basis=[]),
                "backing_cutting_perimeter_ml": _metric_entry(None, quality="missing", source=None, basis=[]),
                "return_material_perimeter_ml": _metric_entry(None, quality="missing", source=None, basis=[]),
                "bevel_perimeter_ml": _metric_entry(None, quality="missing", source=None, basis=[]),
            },
            "classified_layers": [],
            "unclassified_layers": [],
            "contour_split": {},
            "warnings": warnings,
        }

    layers = path_summary.get("layers") or []
    if not layers:
        warnings.append(
            _warning(
                "layer_metrics_missing",
                "Path geometry summary has no layer breakdown — role classification unavailable.",
                source="path_geometry_summary.layers",
            )
        )

    role_totals_mm: dict[str, float] = {}
    role_sources: dict[str, set[str]] = {}
    role_quality: dict[str, str] = {}
    outer_mm = 0.0
    inner_mm = 0.0
    outer_has = False
    inner_has = False
    face_roles = ("face", "letters")
    ignored_layers: list[dict[str, Any]] = []

    from services.intake_v3_layer_role_confirmation_service import (
        build_layer_role_confirmation_lookup,
        layer_key_from_path_layer,
    )

    confirmation_lookup: dict[str, Any] = {}
    if layer_role_confirmation:
        from schemas.intake_v3 import (
            IntakeV3LayerRoleConfirmationLayer,
            IntakeV3LayerRoleConfirmationSnapshot,
        )

        try:
            confirmation_lookup = build_layer_role_confirmation_lookup(
                IntakeV3LayerRoleConfirmationSnapshot.model_validate(layer_role_confirmation)
            )
        except Exception:
            confirmation_lookup = {}
            if isinstance(layer_role_confirmation, dict):
                for layer in layer_role_confirmation.get("layers") or []:
                    if not isinstance(layer, dict) or not layer.get("layer_key"):
                        continue
                    try:
                        entry = IntakeV3LayerRoleConfirmationLayer.model_validate(layer)
                        confirmation_lookup[entry.layer_key] = entry
                    except Exception:
                        continue

    def _resolve_layer_role(layer: dict[str, Any]) -> tuple[str | None, str, str, str, str | None]:
        layer_key = layer_key_from_path_layer(layer)
        layer_id = layer.get("layer_id") or layer.get("layer_name") or "unknown"
        layer_name = layer.get("layer_name") or layer_id
        confirmed_entry = confirmation_lookup.get(layer_key)
        if confirmed_entry is not None:
            state = confirmed_entry.confirmation_state
            confirmed_role = confirmed_entry.confirmed_role
            if state == "ignored" or confirmed_role == "ignore":
                return None, str(layer_id), "ignore", "high", "ignored"
            if state == "confirmed" and confirmed_role:
                role = confirmed_role if confirmed_role != "letters" else "face"
                if role in {"unknown", "ignore", "reference", "drill"}:
                    return None, str(layer_id), role, "high", state
                return role, str(layer_id), role, "high", state
        auto_role = normalize_svg_layer_role(str(layer_name or layer_id))
        if auto_role == "letters":
            auto_role = "face"
        confidence = "medium" if auto_role != "unknown" else "low"
        return auto_role if auto_role != "unknown" else None, str(layer_id), auto_role, confidence, None

    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id = layer.get("layer_id") or layer.get("layer_name") or "unknown"
        layer_name = layer.get("layer_name") or layer_id
        role, resolved_id, display_role, role_confidence, confirmation_state = _resolve_layer_role(layer)
        perimeter_mm = _positive_float(layer.get("perimeter_mm"))
        mapping_source = (
            "layer_role_confirmation_snapshot"
            if confirmation_state in {"confirmed", "ignored"}
            else ("layer_name" if display_role != "unknown" else "unknown")
        )
        entry = {
            "layer_id": layer_id,
            "layer_name": layer_name,
            "normalized_role": display_role,
            "perimeter_mm": perimeter_mm,
            "closed_contour_count": layer.get("closed_contour_count"),
            "mapping_source": mapping_source,
            "confidence": role_confidence,
            "confirmation_state": confirmation_state or "pending",
        }
        if confirmation_state == "ignored":
            ignored_layers.append(entry)
            continue
        if role is None or perimeter_mm is None:
            unclassified_layers.append(entry)
            continue
        classified_layers.append(entry)
        role_totals_mm[role] = role_totals_mm.get(role, 0.0) + (perimeter_mm or 0.0)
        role_sources.setdefault(role, set()).add(str(resolved_id))
        role_quality[role] = (
            "high"
            if role_confidence == "high"
            else ("partial" if role_quality.get(role) == "high" else role_confidence)
        )
        if role in face_roles:
            outer_mm += perimeter_mm or 0.0
            outer_has = True
        elif role == "inner_hole":
            inner_mm += perimeter_mm or 0.0
            inner_has = True

    face_mm = sum(role_totals_mm.get(r, 0.0) for r in face_roles)
    backing_mm = role_totals_mm.get("backing", 0.0)
    return_mm = role_totals_mm.get("return", 0.0)
    bevel_mm = role_totals_mm.get("bevel", 0.0)

    face_ml = _mm_to_ml(face_mm if face_mm > 0 else None)
    backing_ml = _mm_to_ml(backing_mm if backing_mm > 0 else None)
    return_ml = _mm_to_ml(return_mm if return_mm > 0 else None)
    bevel_ml = _mm_to_ml(bevel_mm if bevel_mm > 0 else None)

    if face_ml is None:
        warnings.append(
            _warning(
                "face_perimeter_missing",
                "Face cutting perimeter could not be attributed to a mapped letter/face layer.",
                source="path_perimeter_classification.face",
            )
        )
    if backing_ml is None:
        warnings.append(
            _warning(
                "backing_perimeter_missing",
                "Backing cutting perimeter is missing — no mapped backing/Forex layer path metrics.",
                source="path_perimeter_classification.backing",
            )
        )
    if return_ml is None:
        warnings.append(
            _warning(
                "return_perimeter_missing",
                "Return/cant perimeter is missing — no mapped return layer path metrics.",
                source="path_perimeter_classification.return",
            )
        )
    if bevel_ml is None:
        warnings.append(
            _warning(
                "bevel_perimeter_missing",
                "Bevel perimeter is missing — bevel is not assumed equal to face perimeter.",
                source="path_perimeter_classification.bevel",
            )
        )

    contour_split = dict(path_summary.get("contour_split") or {})
    if outer_has or inner_has:
        contour_split["outer_contour_perimeter_mm"] = round(outer_mm, 6) if outer_has else None
        contour_split["inner_hole_perimeter_mm"] = round(inner_mm, 6) if inner_has else None
        contour_split["total_cutting_perimeter_mm"] = round(outer_mm + inner_mm, 6) if (outer_has or inner_has) else None
        contour_split["split_quality"] = "calculated" if outer_has and inner_has else "partial"
    split_quality = contour_split.get("split_quality") or "missing"
    if split_quality != "calculated":
        warnings.append(
            _warning(
                "contour_role_split_missing",
                "Outer/inner contour perimeter split is not available from path summary.",
                source="path_geometry_summary.contour_split",
            )
        )

    populated = [face_ml, backing_ml, return_ml, bevel_ml]
    if all(v is None for v in populated):
        status = "missing"
        confidence = "low"
    elif all(v is not None for v in populated):
        status = "complete"
        confidence = "high" if confirmation_lookup else ("high" if confirmed else "medium")
    else:
        status = "partial"
        confidence = "partial"

    sources = ["path_geometry_summary"]
    if confirmed:
        sources.append("confirmed_model")
    if confirmation_lookup:
        sources.append("layer_role_confirmation_snapshot")
    elif any(entry.get("mapping_source") == "detected_group_id" for entry in classified_layers):
        sources.append("layer_role_mapping")

    def _perimeter_quality(role_key: str, value: float | None) -> str:
        if value is None:
            return "missing"
        return role_quality.get(role_key, "medium")

    def _perimeter_source(role_key: str, value: float | None) -> str | None:
        if value is None:
            return None
        if confirmation_lookup and role_quality.get(role_key) == "high":
            return "layer_role_confirmation_snapshot+path_geometry_summary"
        return "path_geometry_summary+layer_role_mapping"

    if confirmation_lookup and any(entry.confirmation_state == "pending" for entry in confirmation_lookup.values()):
        warnings.append(
            _warning(
                "layer_roles_unconfirmed",
                "Some SVG layer roles remain unconfirmed by the operator.",
                source="layer_role_confirmation_snapshot",
            )
        )

    return {
        "schema_version": PATH_PERIMETER_CLASSIFICATION_VERSION,
        "classification_status": status,
        "classification_source": "mixed" if len(sources) > 1 else sources[0],
        "confidence": confidence,
        "classified_at": _utcnow_iso(),
        "perimeters": {
            "face_cutting_perimeter_ml": _metric_entry(
                face_ml,
                quality=_perimeter_quality("face", face_ml),
                source=_perimeter_source("face", face_ml),
                basis=list(role_sources.get("face", set()) | role_sources.get("letters", set())),
            ),
            "backing_cutting_perimeter_ml": _metric_entry(
                backing_ml,
                quality=_perimeter_quality("backing", backing_ml),
                source=_perimeter_source("backing", backing_ml),
                basis=list(role_sources.get("backing", set())),
            ),
            "return_material_perimeter_ml": _metric_entry(
                return_ml,
                quality=_perimeter_quality("return", return_ml),
                source=_perimeter_source("return", return_ml),
                basis=list(role_sources.get("return", set())),
            ),
            "bevel_perimeter_ml": _metric_entry(
                bevel_ml,
                quality=_perimeter_quality("bevel", bevel_ml),
                source=_perimeter_source("bevel", bevel_ml),
                basis=list(role_sources.get("bevel", set())),
            ),
        },
        "classified_layers": classified_layers,
        "unclassified_layers": unclassified_layers,
        "ignored_layers": ignored_layers,
        "contour_split": contour_split,
        "warnings": warnings,
    }


def merge_classification_into_geometry_snapshot(
    snapshot: IntakeV3GeometryMetricsSnapshot,
    classification: dict[str, Any],
) -> IntakeV3GeometryMetricsSnapshot:
    perimeters = dict(snapshot.perimeters.model_dump())
    classified = classification.get("perimeters") or {}

    def _apply(key: str, perimeter_key: str) -> None:
        entry = classified.get(key) or {}
        value = entry.get("value")
        quality = entry.get("quality")
        if value is not None and quality in {"high", "medium"}:
            perimeters[perimeter_key] = value
            if perimeter_key == "face_cutting_perimeter_ml":
                perimeters["cutting_perimeter_ml"] = value
                perimeters["total_letter_perimeter_ml"] = value

    _apply("face_cutting_perimeter_ml", "face_cutting_perimeter_ml")
    _apply("backing_cutting_perimeter_ml", "backing_cutting_perimeter_ml")
    _apply("return_material_perimeter_ml", "return_material_perimeter_ml")
    _apply("bevel_perimeter_ml", "bevel_perimeter_ml")

    extra = dict(snapshot.model_dump(mode="json"))
    extra["perimeters"] = perimeters
    extra["path_perimeter_classification"] = classification
    extra["source_keys"] = list(
        dict.fromkeys([*(snapshot.source_keys or []), "path_perimeter_classification"])
    )

    new_warnings = list(snapshot.warnings)
    generic_missing = "perimeter_missing"
    if any(perimeters.get(k) for k in ("face_cutting_perimeter_ml", "total_letter_perimeter_ml")):
        new_warnings = [w for w in new_warnings if w.code != generic_missing]
    for item in classification.get("warnings") or []:
        if isinstance(item, dict):
            new_warnings.append(
                IntakeV3GeometryMetricWarning(
                    code=item.get("code", "classification_warning"),
                    message=item.get("message", ""),
                    source=item.get("source", "path_perimeter_classification"),
                    severity=item.get("severity", "warning"),
                )
            )

    op = dict(snapshot.operation_geometry or {})
    face_q = (classified.get("face_cutting_perimeter_ml") or {}).get("quality", "missing")
    op["face_cutting"] = {
        "available": perimeters.get("face_cutting_perimeter_ml") is not None,
        "quality": face_q if face_q != "missing" else "partial",
        "basis": (classified.get("face_cutting_perimeter_ml") or {}).get("basis") or [],
    }
    backing_q = (classified.get("backing_cutting_perimeter_ml") or {}).get("quality", "missing")
    op["backing_cutting"] = {
        "available": perimeters.get("backing_cutting_perimeter_ml") is not None,
        "quality": backing_q,
        "basis": (classified.get("backing_cutting_perimeter_ml") or {}).get("basis") or [],
    }
    op["return_modeling"] = {
        "available": perimeters.get("return_material_perimeter_ml") is not None,
        "quality": (classified.get("return_material_perimeter_ml") or {}).get("quality", "missing"),
        "basis": (classified.get("return_material_perimeter_ml") or {}).get("basis") or [],
    }
    op["bevel"] = {
        "available": perimeters.get("bevel_perimeter_ml") is not None,
        "quality": (classified.get("bevel_perimeter_ml") or {}).get("quality", "missing"),
        "basis": (classified.get("bevel_perimeter_ml") or {}).get("basis") or [],
    }
    extra["operation_geometry"] = op
    extra["warnings"] = new_warnings

    updated = IntakeV3GeometryMetricsSnapshot.model_validate(extra)
    from services.intake_v3_geometry_metrics_snapshot_service import resolve_geometry_status

    return updated.model_copy(update={"geometry_status": resolve_geometry_status(updated)})


def build_path_perimeter_classification_response(
    context: Iv3SourceContext,
) -> IntakeV3PathPerimeterClassificationResponse:
    if not context.is_intake_v3:
        return IntakeV3PathPerimeterClassificationResponse(
            source_module=INTAKE_V3_SOURCE_MODULE,
            source_type=context.source_type,
            source_id=context.source_id,
            is_intake_v3=False,
            classification_available=False,
            classification_status="missing",
            warnings=[
                IntakeV3GeometryMetricWarning(
                    code="not_intake_v3_source",
                    message="Source is not an Intake V3 order/quote/workspace payload.",
                    source="source_detection",
                )
            ],
        )

    path_summary = extract_path_geometry_summary(context)
    confirmed = extract_confirmed_production_model(context)
    template = PILOT_TEMPLATE_CODE
    if context.workspace:
        template = context.workspace.product_selection.template_code or PILOT_TEMPLATE_CODE

    layer_role_confirmation = None
    if context.workspace and context.workspace.layer_role_confirmation_snapshot:
        layer_role_confirmation = context.workspace.layer_role_confirmation_snapshot
    elif isinstance(context.sections.get("layer_role_confirmation_snapshot"), dict):
        layer_role_confirmation = context.sections["layer_role_confirmation_snapshot"]

    classification = classify_geometry_path_perimeters(
        workspace=context.workspace,
        sections=context.sections,
        path_summary=path_summary,
        confirmed=confirmed,
        template_key=template,
        layer_role_confirmation=layer_role_confirmation,
    )

    snapshot = extract_geometry_metrics_snapshot(context)
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

    warning_models = [
        IntakeV3GeometryMetricWarning(
            code=item.get("code", "classification_warning"),
            message=item.get("message", ""),
            source=item.get("source", "path_perimeter_classification"),
            severity=item.get("severity", "warning"),
        )
        for item in classification.get("warnings") or []
        if isinstance(item, dict)
    ]

    from services.intake_v3_layer_role_confirmation_propagation_service import (
        downstream_propagation_fields,
    )

    propagation_fields, _, stale_warning_pairs = downstream_propagation_fields(context)
    for code, message in stale_warning_pairs:
        warning_models.append(
            IntakeV3GeometryMetricWarning(
                code=code,
                message=message,
                source="layer_role_confirmation_propagation",
                severity="warning",
            )
        )

    return IntakeV3PathPerimeterClassificationResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=context.source_type,
        source_id=context.source_id,
        order_id=context.order.id if context.order else None,
        quote_id=context.quote.id if context.quote else None,
        source_workspace_id=str(workspace_id) if workspace_id else None,
        is_intake_v3=True,
        classification_available=classification.get("classification_status") != "missing",
        classification_status=str(classification.get("classification_status") or "missing"),
        geometry_status=snapshot.geometry_status if snapshot else "geometry_missing",
        path_perimeter_classification=classification,
        warnings=warning_models,
        **propagation_fields,
    )


async def get_path_perimeter_classification_for_order(
    db: AsyncSession, order_id: int
) -> IntakeV3PathPerimeterClassificationResponse:
    context = await load_iv3_source_context(db, order_id=order_id)
    return build_path_perimeter_classification_response(context)


async def get_path_perimeter_classification_for_quote(
    db: AsyncSession, quote_id: int
) -> IntakeV3PathPerimeterClassificationResponse:
    context = await load_iv3_source_context(db, quote_id=quote_id)
    return build_path_perimeter_classification_response(context)


async def get_path_perimeter_classification_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3PathPerimeterClassificationResponse:
    context = await load_iv3_source_context(db, workspace_id=workspace_id)
    if context.workspace is None:
        raise HTTPException(status_code=404, detail={"error": "workspace_not_found"})
    return build_path_perimeter_classification_response(context)
