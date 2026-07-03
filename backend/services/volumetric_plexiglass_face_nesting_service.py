"""Plexiglas face sheet nesting for TPL-VOLUMETRIC-LETTERS — sheet adapter only (no ml).

Quote snapshot contract: ``plexiglass_face_nesting`` is sibling to ``face_vinyl_handoff``,
never nested under vinyl. Consumption is sheets + m² + remaining sheet area — never roll ml.

Material profile priority via ``flat_material_profile_resolver``:
1. quote_input / product_spec overrides
2. Material Registry / Inventory when available
3. default_profile_internal (3050×2030)
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from services.flat_material_nesting import (
    FlatPiece,
    SheetMaterialProfile,
    SheetNestingResult,
    estimate_sheet_nesting_from_profile,
    sheet_nesting_result_to_handoff_dict,
)
from services.flat_material_profile_resolver import (
    SOURCE_DEFAULT_INTERNAL,
    SOURCE_QUOTE_INPUT,
    resolve_plexiglass_face_material_code,
    resolve_sheet_material_profile,
)

PROFILE_SOURCE_DEFAULT_INTERNAL = SOURCE_DEFAULT_INTERNAL
PROFILE_SOURCE_QUOTE_INPUT = SOURCE_QUOTE_INPUT
PROFILE_SOURCE_PRODUCT_SPEC = "product_spec_json"

PIECE_SOURCES_REAL = frozenset({"letter_bounding_boxes", "face_vinyl_pieces"})


def resolve_plexiglass_face_profile(
    quote_input: Mapping[str, Any] | None = None,
    product_spec: Mapping[str, Any] | None = None,
    *,
    registry_row: Mapping[str, Any] | None = None,
) -> tuple[SheetMaterialProfile, str, str, bool]:
    """Resolve sheet profile; returns (profile, source_key, display_name, is_default_fallback)."""
    material_code = resolve_plexiglass_face_material_code(quote_input, product_spec)
    resolution = resolve_sheet_material_profile(
        material_code,
        product_spec=product_spec,
        quote_input=quote_input,
        role="plexiglass_face",
        registry_row=registry_row,
    )
    profile = resolution.to_sheet_profile()
    source = resolution.source
    if resolution.is_default_fallback:
        source = SOURCE_DEFAULT_INTERNAL
    return profile, source, resolution.display_name, resolution.is_default_fallback


def _resolve_pieces_context(
    quote_input: Mapping[str, Any] | None,
    product_spec: Mapping[str, Any] | None,
) -> tuple[list[FlatPiece], str | None, bool]:
    """Return (flat_pieces, pieces_source, is_fallback)."""
    qi = quote_input or {}
    ps = product_spec or {}

    for key in ("letter_bounding_boxes", "face_vinyl_pieces"):
        boxes = ps.get(key) or qi.get(key)
        if isinstance(boxes, list) and boxes:
            from services.flat_material_nesting import flat_pieces_from_bounding_boxes

            pieces = flat_pieces_from_bounding_boxes(boxes, default_source=key)
            if pieces:
                return pieces, key, False

    from services.volumetric_face_vinyl_service import collect_nesting_pieces

    nesting_pieces, source = collect_nesting_pieces(qi, product_spec=ps)
    if not nesting_pieces:
        return [], None, False

    if source == "assembly_bbox":
        flat = [
            FlatPiece(
                piece_id=str(p.piece_id or "assembly"),
                width_mm=p.width_mm,
                height_mm=p.height_mm,
                label=p.label,
                source="assembly_bbox",
            )
            for p in nesting_pieces
        ]
        return flat, "assembly_bbox", True

    flat = [
        FlatPiece(
            piece_id=str(p.piece_id or f"piece_{index + 1}"),
            width_mm=p.width_mm,
            height_mm=p.height_mm,
            label=p.label,
            source=source,
        )
        for index, p in enumerate(nesting_pieces)
    ]
    return flat, source, source not in PIECE_SOURCES_REAL


def build_plexiglass_face_nesting_for_quote(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
    registry_row: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``plexiglass_face_nesting`` block for quote/order snapshot handoff."""
    profile, profile_source, display_name, is_default_fallback = resolve_plexiglass_face_profile(
        quote_input,
        product_spec,
        registry_row=registry_row,
    )
    resolution = resolve_sheet_material_profile(
        profile.material_code,
        product_spec=product_spec,
        quote_input=quote_input,
        role="plexiglass_face",
        registry_row=registry_row,
    )
    flat_pieces, pieces_source, is_fallback = _resolve_pieces_context(
        quote_input,
        product_spec,
    )

    material_block: dict[str, Any] = {
        "material_code": profile.material_code,
        "display_name": display_name,
        "material_type": "sheet",
        "thickness_mm": profile.thickness_mm,
        "source": profile_source,
        "is_default_fallback": is_default_fallback,
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

    if pieces_source not in PIECE_SOURCES_REAL and not is_fallback:
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
            "geometry": {
                "pieces_source": pieces_source,
                "pieces_count": len(flat_pieces),
            },
            "material": material_block,
            "nesting": {
                "method": "sheet_rectangular",
                "is_fallback": is_fallback,
                "unplaceable_pieces": list(nesting.unplaceable_pieces),
                "warnings": list(nesting.warnings),
            },
        }

    material_block.update(
        {
            "sheet_width_mm": resolution.sheet_width_mm,
            "sheet_height_mm": resolution.sheet_height_mm,
        }
    )

    return {
        "enabled": True,
        "material": material_block,
        "geometry": {
            "pieces_source": pieces_source,
            "pieces_count": nesting.pieces_count,
        },
        "nesting": sheet_nesting_result_to_handoff_dict(
            nesting,
            is_fallback=is_fallback,
            pieces_source=pieces_source or "unknown",
            profile=profile,
        ),
    }


def estimate_plexiglass_face_sheet_nesting(
    product_spec: Mapping[str, Any] | None,
    *,
    profile: SheetMaterialProfile | None = None,
    rotation_allowed: bool = True,
    nesting_source: str = "letter_bounding_boxes",
) -> SheetNestingResult:
    """Sheet rectangular nesting for letter face plexiglas using shared geometry."""
    flat_pieces, src, _fallback = _resolve_pieces_context(None, product_spec)
    if profile is None:
        prof, _, _, _ = resolve_plexiglass_face_profile(None, product_spec)
    else:
        prof = profile
    return estimate_sheet_nesting_from_profile(
        flat_pieces,
        prof,
        rotation_allowed=rotation_allowed,
        nesting_source=src or nesting_source,
    )


def build_plexiglass_face_nesting_block(
    product_spec: Mapping[str, Any] | None,
    *,
    profile: SheetMaterialProfile | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    """Backward-compatible wrapper — prefer ``build_plexiglass_face_nesting_for_quote``."""
    if not enabled:
        return {"enabled": False}
    return build_plexiglass_face_nesting_for_quote(None, product_spec=product_spec)


def build_flat_material_nesting_summary(
    product_spec: Mapping[str, Any] | None,
    *,
    quote_input: Mapping[str, Any] | None = None,
    roll_width_mm: Optional[float] = None,
) -> dict[str, Any]:
    """Optional cross-material nesting summary — does not replace handoff blocks."""
    from services.flat_material_nesting_summary_service import (
        build_flat_material_nesting_summary as _build_summary,
    )
    from services.volumetric_face_vinyl_service import build_face_vinyl_handoff_for_quote
    from services.volumetric_forex_backing_nesting_service import (
        build_forex_backing_nesting_for_quote,
    )

    ps = product_spec or {}
    qi = quote_input or {}
    vinyl = build_face_vinyl_handoff_for_quote(qi, product_spec=ps)
    plexi = build_plexiglass_face_nesting_for_quote(qi, product_spec=ps)
    forex = build_forex_backing_nesting_for_quote(qi, product_spec=ps)
    return _build_summary(
        face_vinyl_handoff=vinyl,
        plexiglass_face_nesting=plexi,
        forex_backing_nesting=forex,
    )
