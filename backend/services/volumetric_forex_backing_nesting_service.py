"""Forex backing sheet nesting for TPL-VOLUMETRIC-LETTERS — sheet adapter only (no ml).

Quote snapshot contract: ``forex_backing_nesting`` is sibling to
``plexiglass_face_nesting`` and ``face_vinyl_handoff``.

MVP geometry: same ``letter_bounding_boxes`` as plexiglas face unless a
dedicated backing geometry source appears later.
"""

from __future__ import annotations

from typing import Any, Mapping

from services.flat_material_nesting import (
    estimate_sheet_nesting_from_profile,
    sheet_nesting_result_to_handoff_dict,
)
from services.flat_material_profile_resolver import (
    SOURCE_DEFAULT_INTERNAL,
    resolve_sheet_material_profile,
)
from services.volumetric_plexiglass_face_nesting_service import (
    PIECE_SOURCES_REAL,
    _resolve_pieces_context,
)

DEFAULT_FOREX_MATERIAL_CODE = "FOREX_BACKING_10MM"
GEOMETRY_ASSUMPTION_SAME_AS_FACE = "same_as_letter_face_bbox"


def build_forex_backing_nesting_for_quote(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
    registry_row: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``forex_backing_nesting`` block for quote/order snapshot handoff."""
    resolution = resolve_sheet_material_profile(
        DEFAULT_FOREX_MATERIAL_CODE,
        product_spec=product_spec,
        quote_input=quote_input,
        role="forex_backing",
        registry_row=registry_row,
    )
    profile = resolution.to_sheet_profile()
    flat_pieces, pieces_source, is_fallback = _resolve_pieces_context(
        quote_input,
        product_spec,
    )

    profile_source = resolution.source
    if resolution.is_default_fallback:
        profile_source = SOURCE_DEFAULT_INTERNAL

    material_block: dict[str, Any] = {
        "material_code": resolution.material_code,
        "display_name": resolution.display_name,
        "material_type": "sheet",
        "thickness_mm": resolution.thickness_mm,
        "sheet_width_mm": resolution.sheet_width_mm,
        "sheet_height_mm": resolution.sheet_height_mm,
        "source": profile_source,
        "is_default_fallback": resolution.is_default_fallback,
    }
    if resolution.registry_inventory_code:
        material_block["registry_inventory_code"] = resolution.registry_inventory_code
    if resolution.warnings:
        material_block["warnings"] = list(resolution.warnings)

    if not flat_pieces:
        return {
            "enabled": False,
            "reason": "missing_geometry",
            "material": material_block,
        }

    geometry_assumption: str | None = None
    if pieces_source in PIECE_SOURCES_REAL:
        geometry_assumption = GEOMETRY_ASSUMPTION_SAME_AS_FACE
    elif is_fallback:
        geometry_assumption = None
    else:
        return {
            "enabled": False,
            "reason": "missing_letter_pieces",
            "geometry": {"pieces_source": pieces_source, "pieces_count": len(flat_pieces)},
            "material": material_block,
        }

    nesting = estimate_sheet_nesting_from_profile(
        flat_pieces,
        profile,
        nesting_source=pieces_source or "letter_bounding_boxes",
    )

    if nesting.unplaceable_pieces:
        return {
            "enabled": False,
            "reason": "unplaceable_pieces",
            "material": material_block,
            "geometry": {
                "pieces_source": pieces_source,
                "pieces_count": len(flat_pieces),
                "geometry_assumption": geometry_assumption,
            },
            "nesting": {
                "method": "sheet_rectangular",
                "is_fallback": is_fallback,
                "unplaceable_pieces": list(nesting.unplaceable_pieces),
                "warnings": list(nesting.warnings),
            },
        }

    geometry_block: dict[str, Any] = {
        "pieces_source": pieces_source,
        "pieces_count": nesting.pieces_count,
    }
    if geometry_assumption:
        geometry_block["geometry_assumption"] = geometry_assumption

    return {
        "enabled": True,
        "material": material_block,
        "geometry": geometry_block,
        "nesting": sheet_nesting_result_to_handoff_dict(
            nesting,
            is_fallback=is_fallback,
            pieces_source=pieces_source or "unknown",
            profile=profile,
        ),
    }
