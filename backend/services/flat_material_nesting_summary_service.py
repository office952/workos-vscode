"""Compact admin/quote summary for flat material nesting handoff blocks."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from services.flat_material_offcut_foundation import sheet_nesting_requires_offcut_measurement
from services.sheet_source_selection_service import attach_sheet_source_selection_to_summary


def _profile_source_label(source: str | None, is_fallback: bool | None) -> str:
    if source == "material_registry":
        return "Material Registry"
    if source == "quote_input":
        return "Quote input"
    if source == "product_spec_json":
        return "Product spec"
    if is_fallback:
        return "fallback intern"
    if source == "default_profile_internal":
        return "fallback intern"
    return source or "necunoscut"


def _sheet_summary_entry(
    *,
    role: str,
    label: str,
    block: Mapping[str, Any],
    geometry_assumption: str | None = None,
) -> dict[str, Any]:
    material = block.get("material") or {}
    nesting = block.get("nesting") or {}
    entry: dict[str, Any] = {
        "role": role,
        "label": label,
        "enabled": bool(block.get("enabled")),
        "sheets_used": nesting.get("sheets_used"),
        "allocated_sheet_area_m2": nesting.get("allocated_sheet_area_m2"),
        "used_piece_bbox_area_m2": nesting.get("used_piece_bbox_area_m2"),
        "remaining_area_m2": nesting.get("remaining_area_m2"),
        "remaining_percent": nesting.get("remaining_percent"),
        "remaining_policy": nesting.get("remaining_policy"),
        "profile_source": material.get("source"),
        "profile_source_label": _profile_source_label(
            material.get("source"),
            material.get("is_default_fallback"),
        ),
        "is_default_fallback": material.get("is_default_fallback"),
        "sheet_width_mm": material.get("sheet_width_mm"),
        "sheet_height_mm": material.get("sheet_height_mm"),
        "pieces_count": (block.get("geometry") or {}).get("pieces_count"),
        "pieces_source": (block.get("geometry") or {}).get("pieces_source"),
        "nesting_method": nesting.get("method"),
        "is_fallback": nesting.get("is_fallback"),
        "real_offcut_measurement_required": sheet_nesting_requires_offcut_measurement(block),
    }
    if geometry_assumption:
        entry["geometry_assumption"] = geometry_assumption
    if not block.get("enabled"):
        entry["reason"] = block.get("reason")
    return entry


def build_flat_material_nesting_summary(
    *,
    face_vinyl_handoff: Mapping[str, Any] | None = None,
    plexiglass_face_nesting: Mapping[str, Any] | None = None,
    forex_backing_nesting: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "sheet_materials": [],
        "roll_materials": [],
        "real_offcut_measurement_required": False,
        "sheet_source_selection": [],
    }

    if isinstance(face_vinyl_handoff, dict) and face_vinyl_handoff.get("enabled"):
        nesting = face_vinyl_handoff.get("nesting") or {}
        summary["roll_materials"].append(
            {
                "role": "face_vinyl",
                "label": str(face_vinyl_handoff.get("material_label") or "Autocolant fețe"),
                "recommended_roll_length_m": nesting.get("recommended_roll_length_m"),
                "nested_roll_length_m": nesting.get("nested_roll_length_m"),
                "quantity_m2": nesting.get("quantity_m2")
                or face_vinyl_handoff.get("face_vinyl_used_sqm"),
                "pieces_count": nesting.get("pieces_count"),
                "method": nesting.get("method"),
            }
        )

    if isinstance(plexiglass_face_nesting, dict):
        material = plexiglass_face_nesting.get("material") or {}
        summary["sheet_materials"].append(
            _sheet_summary_entry(
                role="plexiglass_face",
                label=str(material.get("display_name") or "Plexiglas față"),
                block=plexiglass_face_nesting,
            )
        )
        if plexiglass_face_nesting.get("enabled"):
            geometry = plexiglass_face_nesting.get("geometry") or {}
            attach_sheet_source_selection_to_summary(
                summary,
                role="plexiglass_face",
                material_code=str(material.get("material_code") or "PLEXI_FACE_3MM"),
                thickness_mm=(
                    float(material["thickness_mm"])
                    if material.get("thickness_mm") is not None
                    else None
                ),
                pieces=geometry.get("pieces") if isinstance(geometry.get("pieces"), list) else [],
                material_profile=material,
            )

    if isinstance(forex_backing_nesting, dict):
        material = forex_backing_nesting.get("material") or {}
        geometry = forex_backing_nesting.get("geometry") or {}
        summary["sheet_materials"].append(
            _sheet_summary_entry(
                role="forex_backing",
                label=str(material.get("display_name") or "Forex spate"),
                block=forex_backing_nesting,
                geometry_assumption=geometry.get("geometry_assumption"),
            )
        )
        if forex_backing_nesting.get("enabled"):
            attach_sheet_source_selection_to_summary(
                summary,
                role="forex_backing",
                material_code=str(material.get("material_code") or "FOREX_BACKING_10MM"),
                thickness_mm=(
                    float(material["thickness_mm"])
                    if material.get("thickness_mm") is not None
                    else None
                ),
                pieces=geometry.get("pieces") if isinstance(geometry.get("pieces"), list) else [],
                material_profile=material,
            )

    summary["real_offcut_measurement_required"] = any(
        entry.get("real_offcut_measurement_required")
        for entry in summary["sheet_materials"]
        if entry.get("enabled")
    )
    return summary
