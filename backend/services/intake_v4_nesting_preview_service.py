"""Intake V4 read-only nesting diagnostic preview — does not alter material calculations."""

from __future__ import annotations

from typing import Any, Literal

from schemas.intake_v4 import (
    IntakeV4MaterialQuantityRow,
    IntakeV4NestingPreviewBoundary,
    IntakeV4NestingPreviewMaterialTrace,
    IntakeV4NestingPreviewPartRow,
    IntakeV4NestingPreviewResponse,
    IntakeV4NestingPreviewRollJob,
    IntakeV4NestingPreviewSheetLayout,
    IntakeV4NestingPreviewSummary,
    IntakeV4NestingPreviewWarning,
)
from services.intake_v4_nesting_material_precision import (
    SHEET_EXCLUDED_ROLES,
    SHEET_FACE_ROLES,
    _build_parts_metadata_index,
    _layer_role_for_name,
    _part_classification_index,
    _placement_area_sqm,
    _positive,
    backing_layer_confirmed,
    classify_sheet_material_intent,
    compute_sheet_nesting_material_split,
    resolve_active_sheet_layout,
)

SHEET_CONFIG_DIMS_MM: dict[str, tuple[float, float]] = {
    "sheet_3000x2000": (3000.0, 2000.0),
    "sheet_3000x1500": (3000.0, 1500.0),
    "sheet_4000x1500": (4000.0, 1500.0),
    "sheet_1300x900": (1300.0, 900.0),
    "sheet_1220x2440": (1220.0, 2440.0),
}

SHEET_MATERIAL_TARGETS: dict[str, str] = {
    "sheet_3000x2000": "plexiglas / ACM sheet stock",
    "sheet_3000x1500": "plexiglas / ACM sheet stock",
    "sheet_4000x1500": "plexiglas / ACM sheet stock",
    "sheet_1300x900": "Forex / ACM 1300×900",
    "sheet_1220x2440": "sheet stock 1220×2440",
}

PREVIEW_MODE = "bounding_box_mvp"
PREVIEW_DISCLAIMER = (
    "Preview diagnostic: nu consumă stoc și nu reprezintă toolpath real. "
    "MVP folosește dreptunghiuri bounding box pe piese, nu formă exactă CNC."
)

_PREVIEW_BOUNDARY = IntakeV4NestingPreviewBoundary()


def _resolve_part_kind(
    *,
    layer_role: str | None,
    material_intent: Literal["face", "backing"] | None,
    is_inner_hole: bool,
) -> Literal["face_part", "artwork_part", "hole", "backing_part", "unknown"]:
    if is_inner_hole:
        return "hole"
    role = (layer_role or "").strip().lower()
    if role in SHEET_EXCLUDED_ROLES or role in {"printed_artwork", "logo", "policromie"}:
        return "artwork_part"
    if material_intent == "backing" or role in {"backing", "support_panel"}:
        return "backing_part"
    if material_intent == "face" or role in SHEET_FACE_ROLES:
        return "face_part"
    return "unknown"


def _material_lines_for_intent(
    intent: Literal["face", "backing"] | None,
    layer_role: str | None,
    *,
    on_active_sheet: bool,
) -> list[str]:
    lines: list[str] = []
    role = (layer_role or "").strip().lower()
    if role in SHEET_EXCLUDED_ROLES:
        if role == "printed_artwork":
            lines.extend(["artwork_*_print_vinyl", "artwork_*_laminated_vinyl"])
        return lines
    if intent == "face" and on_active_sheet:
        lines.append("plexiglas_face")
    if intent == "backing" and on_active_sheet:
        lines.append("forex_backing")
    if intent == "face" or role in SHEET_FACE_ROLES:
        lines.append("face_vinyl")
    return lines


def _build_sheet_layouts(
    nesting: dict[str, Any],
    active_config_id: str | None,
    sheet_split_mode: str,
) -> list[IntakeV4NestingPreviewSheetLayout]:
    layouts: list[IntakeV4NestingPreviewSheetLayout] = []
    for sheet in nesting.get("sheets") or []:
        if not isinstance(sheet, dict):
            continue
        config_id = str(sheet.get("configId") or "sheet")
        placed_count = int(sheet.get("placedItemsCount") or 0)
        has_placements = placed_count > 0 or len(sheet.get("placements") or []) > 0
        dims = SHEET_CONFIG_DIMS_MM.get(config_id)
        width_mm = dims[0] if dims else None
        length_mm = dims[1] if dims else None
        is_active = config_id == active_config_id and has_placements
        layouts.append(
            IntakeV4NestingPreviewSheetLayout(
                config_id=config_id,
                display_label=config_id.replace("_", " "),
                sheet_width_mm=width_mm,
                sheet_length_mm=length_mm,
                material_target=SHEET_MATERIAL_TARGETS.get(config_id, "sheet stock"),
                sheets_used=int(sheet.get("sheetsUsed") or 0),
                used_sheet_area_sqm=_positive(sheet.get("usedSheetAreaSqm")),
                parts_bounding_area_sqm=_positive(sheet.get("partsBoundingAreaSqm")),
                efficiency_percent=_positive(sheet.get("efficiencyPercent")),
                placed_items_count=placed_count,
                unplaced_items_count=int(sheet.get("unplacedItemsCount") or 0),
                placement_count=len(sheet.get("placements") or []),
                is_active_for_breakdown=is_active,
                layout_kind="active_breakdown" if is_active else "alternative_variant",
                breakdown_note=(
                    f"Layout activ pentru calcul intern Material Breakdown ({sheet_split_mode})"
                    if is_active
                    else "Variantă alternativă — nu intră în Material Breakdown"
                ),
            )
        )
    return layouts


def _build_roll_jobs(
    nesting: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
) -> list[IntakeV4NestingPreviewRollJob]:
    best_by_layer: dict[str, tuple[float, int, str]] = {}
    jobs_out: list[IntakeV4NestingPreviewRollJob] = []

    for roll in nesting.get("rolls") or []:
        if not isinstance(roll, dict):
            continue
        roll_width = _positive(roll.get("rollWidthMm"))
        for job in roll.get("jobs") or []:
            if not isinstance(job, dict):
                continue
            placed = int(job.get("placedItemsCount") or 0)
            if job.get("placedItemsCount") is not None and placed <= 0:
                continue
            layer_name = str(job.get("sourceLayerName") or "")
            layer_role = _layer_role_for_name(layer_role_setup, layer_name, layer_name)
            area = _positive(job.get("usedRollAreaSqm"))
            if area is None:
                consumed = _positive(job.get("consumedLengthMm"))
                if consumed and roll_width:
                    area = (roll_width * consumed) / 1_000_000.0
            if area is None:
                continue
            key = layer_name or str(job.get("colorKey") or "roll")
            prev = best_by_layer.get(key)
            if prev is None or area < prev[0]:
                best_by_layer[key] = (area, int(roll_width or 0), str(job.get("colorKey") or ""))

    for roll in nesting.get("rolls") or []:
        if not isinstance(roll, dict):
            continue
        roll_width = _positive(roll.get("rollWidthMm"))
        for job in roll.get("jobs") or []:
            if not isinstance(job, dict):
                continue
            placed = int(job.get("placedItemsCount") or 0)
            if job.get("placedItemsCount") is not None and placed <= 0:
                continue
            layer_name = str(job.get("sourceLayerName") or "")
            layer_role = _layer_role_for_name(layer_role_setup, layer_name, layer_name)
            area = _positive(job.get("usedRollAreaSqm"))
            consumed = _positive(job.get("consumedLengthMm"))
            if area is None and consumed and roll_width:
                area = (roll_width * consumed) / 1_000_000.0
            key = layer_name or str(job.get("colorKey") or "roll")
            best = best_by_layer.get(key)
            is_active = best is not None and area == best[0] and int(roll_width or 0) == best[1]
            jobs_out.append(
                IntakeV4NestingPreviewRollJob(
                    roll_config_id=str(roll.get("configId") or f"roll_{int(roll_width or 0)}"),
                    roll_width_mm=roll_width,
                    source_layer_name=layer_name or None,
                    layer_role=layer_role,
                    color_key=str(job.get("colorKey")) if job.get("colorKey") else None,
                    used_roll_area_sqm=area,
                    consumed_length_mm=consumed,
                    placed_items_count=placed,
                    efficiency_percent=_positive(job.get("efficiencyPercent")),
                    is_active_for_breakdown=is_active and layer_role not in SHEET_EXCLUDED_ROLES,
                    layout_kind="active_breakdown" if is_active else "alternative_variant",
                    material_target="face_vinyl" if layer_role in SHEET_FACE_ROLES else None,
                )
            )
    return jobs_out


def _build_part_rows(
    nesting: dict[str, Any],
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    active_config_id: str | None,
) -> tuple[list[IntakeV4NestingPreviewPartRow], int]:
    parts_index = _build_parts_metadata_index(analysis)
    part_class_index = _part_classification_index(analysis, layer_role_setup)
    rows: list[IntakeV4NestingPreviewPartRow] = []
    holes_excluded = 0
    active_sheet = next(
        (s for s in (nesting.get("sheets") or []) if isinstance(s, dict) and s.get("configId") == active_config_id),
        None,
    )
    if not isinstance(active_sheet, dict):
        return rows, holes_excluded

    for placement in active_sheet.get("placements") or []:
        if not isinstance(placement, dict):
            continue
        part_id = str(placement.get("partId") or "")
        part_class = part_class_index.get(part_id)
        is_inner_hole = bool(part_class and part_class.get("is_inner_hole"))
        if is_inner_hole:
            holes_excluded += 1
            continue
        layer_name = str(placement.get("sourceLayerName") or "")
        part_meta = parts_index.get(part_id)
        if part_meta and part_meta.get("layer_name"):
            layer_name = str(part_meta.get("layer_name"))
        layer_id = str((part_meta or {}).get("layer_id") or layer_name)
        layer_role = _layer_role_for_name(layer_role_setup, layer_id, layer_name)
        intent = classify_sheet_material_intent(part_meta=part_meta, layer_role=layer_role)
        width = _positive(placement.get("placedWidthMm"))
        height = _positive(placement.get("placedHeightMm"))
        area = _placement_area_sqm(placement)
        material_lines = _material_lines_for_intent(intent, layer_role, on_active_sheet=True)
        if intent == "backing" and not backing_layer_confirmed(layer_role_setup):
            material_lines = []
        nestable = bool(part_class.get("nestable")) if part_class else intent in {"face", "backing"}
        counts_piece = bool(part_class.get("counts_as_material_piece")) if part_class else intent == "face"
        rows.append(
            IntakeV4NestingPreviewPartRow(
                part_id=part_id,
                source_layer_name=layer_name or None,
                layer_role=layer_role,
                part_kind=_resolve_part_kind(
                    layer_role=layer_role,
                    material_intent=intent,
                    is_inner_hole=False,
                ),
                material_intent=intent,
                nestable=nestable,
                counts_as_material_piece=counts_piece,
                bounds_width_mm=width,
                bounds_height_mm=height,
                area_sqm=round(area, 6) if area > 0 else None,
                perimeter_ml=_positive((part_meta or {}).get("perimeter_ml")),
                nesting_target=f"sheet:{active_config_id}",
                placement_x_mm=_positive(placement.get("xMm")),
                placement_y_mm=_positive(placement.get("yMm")),
                counted_in_material_lines=material_lines,
                preview_shape="bounding_box",
            )
        )
    return rows, holes_excluded


def _build_material_traces(
    material_rows: list[IntakeV4MaterialQuantityRow],
    sheet_split: Any,
    parts: list[IntakeV4NestingPreviewPartRow],
) -> list[IntakeV4NestingPreviewMaterialTrace]:
    traces: list[IntakeV4NestingPreviewMaterialTrace] = []
    for row in material_rows:
        source_part_ids: list[str] = []
        if row.material_key == "plexiglas_face":
            source_part_ids = [p.part_id for p in parts if "plexiglas_face" in p.counted_in_material_lines]
        elif row.material_key == "forex_backing":
            source_part_ids = [p.part_id for p in parts if "forex_backing" in p.counted_in_material_lines]
        elif row.material_key == "face_vinyl":
            source_part_ids = [p.part_id for p in parts if "face_vinyl" in p.counted_in_material_lines]
        traces.append(
            IntakeV4NestingPreviewMaterialTrace(
                material_key=row.material_key,
                display_name=row.display_name,
                reported_quantity=row.base_quantity or row.quantity,
                unit=row.unit,
                quantity_basis=row.quantity_basis,
                quantity_source=row.quantity_source,
                source_part_ids=source_part_ids,
                active_sheet_config_id=sheet_split.config_id,
                breakdown_mode=sheet_split.mode,
                uses_placement_footprint=sheet_split.mode
                in {"role_split", "part_kind", "single_face", "single_backing", "partial_role_split"},
                uses_full_sheet_stock_proration=sheet_split.mode == "prorated_fallback",
            )
        )
    return traces


def build_intake_v4_nesting_preview(
    payload_raw: dict[str, Any],
    *,
    workspace_id: str = "",
    material_rows: list[IntakeV4MaterialQuantityRow],
    face_area: float | None,
    backing_area: float | None,
) -> IntakeV4NestingPreviewResponse:
    analysis = payload_raw.get("svg_analysis_json") if isinstance(payload_raw.get("svg_analysis_json"), dict) else {}
    nesting = analysis.get("nesting") if isinstance(analysis.get("nesting"), dict) else {}
    layer_role_setup = payload_raw.get("layer_role_setup") if isinstance(payload_raw.get("layer_role_setup"), dict) else None

    active_sheet, active_config_id, _ = resolve_active_sheet_layout(nesting)
    sheet_split = compute_sheet_nesting_material_split(
        nesting,
        analysis,
        layer_role_setup,
        face_area=face_area,
        backing_area=backing_area,
    )

    warnings: list[IntakeV4NestingPreviewWarning] = [
        IntakeV4NestingPreviewWarning(code="read_only_diagnostic", severity="info", message=PREVIEW_DISCLAIMER)
    ]
    if not nesting:
        warnings.append(
            IntakeV4NestingPreviewWarning(
                code="missing_nesting",
                severity="warning",
                message="Lipsește blocul svg_analysis_json.nesting — preview indisponibil.",
            )
        )
        return IntakeV4NestingPreviewResponse(
            preview_mode=PREVIEW_MODE,
            preview_only=True,
            mutates_inventory=False,
            uses_stock=False,
            source="intake_v4_workspace",
            workspace_id=workspace_id or None,
            disclaimer=PREVIEW_DISCLAIMER,
            boundary=_PREVIEW_BOUNDARY,
            active_sheet_config_id=None,
            breakdown_uses_single_active_layout=True,
            sheets=[],
            rolls=[],
            parts=[],
            material_traces=[],
            warnings=warnings,
        )

    alt_count = sum(1 for s in (nesting.get("sheets") or []) if isinstance(s, dict))
    if alt_count > 1:
        warnings.append(
            IntakeV4NestingPreviewWarning(
                code="multiple_sheet_variants",
                severity="info",
                message=(
                    f"{alt_count} sheet layout variants in nesting output; "
                    "material breakdown uses one active layout only (not summed)."
                ),
            )
        )

    parts, holes_excluded = _build_part_rows(nesting, analysis, layer_role_setup, active_config_id)
    sheets = _build_sheet_layouts(nesting, active_config_id, sheet_split.mode)
    rolls = _build_roll_jobs(nesting, layer_role_setup)
    active_sheet_count = sum(1 for s in sheets if s.is_active_for_breakdown)
    active_roll_count = sum(1 for r in rolls if r.is_active_for_breakdown)
    artwork_parts = sum(1 for p in parts if p.part_kind == "artwork_part")
    nestable_parts = sum(1 for p in parts if p.nestable)

    if not backing_layer_confirmed(layer_role_setup):
        warnings.append(
            IntakeV4NestingPreviewWarning(
                code="backing_not_confirmed",
                severity="info",
                message="Backing neconfirmat — Forex/backing sheet layouts sunt alternative/inactive, fără estimate material.",
            )
        )

    summary = IntakeV4NestingPreviewSummary(
        sheet_layouts=len(sheets),
        roll_layouts=len({j.roll_config_id for j in rolls}),
        active_sheet_layouts=active_sheet_count,
        active_roll_layouts=active_roll_count,
        alternative_layouts=max(0, len(sheets) - active_sheet_count) + max(0, len(rolls) - active_roll_count),
        nestable_parts=nestable_parts,
        holes_excluded=holes_excluded,
        artwork_parts=artwork_parts,
    )

    plexi_parts = [p for p in parts if "plexiglas_face" in p.counted_in_material_lines]
    if plexi_parts:
        sum_area = round(sum(p.area_sqm or 0 for p in plexi_parts), 4)
        warnings.append(
            IntakeV4NestingPreviewWarning(
                code="plexiglas_face_footprint",
                severity="info",
                message=(
                    f"Plexiglas face: {len(plexi_parts)} parts, Σ placement bbox = {sum_area} m² "
                    f"(breakdown reports {sheet_split.face_area_sqm} m² via {sheet_split.mode})."
                ),
            )
        )

    return IntakeV4NestingPreviewResponse(
        preview_mode=PREVIEW_MODE,
        preview_only=True,
        mutates_inventory=False,
        uses_stock=False,
        source="intake_v4_workspace",
        workspace_id=workspace_id or None,
        disclaimer=PREVIEW_DISCLAIMER,
        boundary=_PREVIEW_BOUNDARY,
        summary=summary,
        active_sheet_config_id=active_config_id,
        breakdown_uses_single_active_layout=True,
        sheets=sheets,
        rolls=rolls,
        parts=parts,
        material_traces=_build_material_traces(material_rows, sheet_split, parts),
        warnings=warnings,
    )
