"""Vinyl / roll adapter over generic flat-material nesting.

Roll rectangular nesting lives in ``flat_material_nesting``; this module
preserves the face-vinyl public API used by ``volumetric_face_vinyl_service``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from services.flat_material_nesting import (
    DEFAULT_SPACING_MM,
    FlatPiece,
    RollFlatPlacement,
    RollNestingResult,
    estimate_roll_rectangular_nesting,
)

INTERNAL_WASTE_FACTOR = 1.10
ROTATIONS_DEG = (0, 90, 180, 270)


@dataclass(frozen=True)
class FaceVinylPiece:
    piece_id: str
    width_mm: float
    height_mm: float
    label: Optional[str] = None
    source: str = "vector_piece"
    area_sqm: Optional[float] = None


@dataclass(frozen=True)
class PiecePlacement:
    piece_id: str
    label: Optional[str]
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotation_deg: int


@dataclass
class PieceBasedNestingResult:
    nesting_method: str = "piece_based_rectangular"
    nesting_source: str = "none"
    is_fallback: bool = False
    roll_width_mm: Optional[float] = None
    material_width_m: Optional[float] = None
    spacing_mm: float = DEFAULT_SPACING_MM
    pieces_count: int = 0
    nested_roll_length_m: Optional[float] = None
    recommended_roll_length_m: Optional[float] = None
    quantity_m2: Optional[float] = None
    rotation_allowed: bool = True
    roll_width_missing: bool = False
    geometry_missing: bool = False
    oversized_piece: bool = False
    placements: List[PiecePlacement] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _to_flat_piece(piece: FaceVinylPiece) -> FlatPiece:
    return FlatPiece(
        piece_id=piece.piece_id,
        width_mm=piece.width_mm,
        height_mm=piece.height_mm,
        label=piece.label,
        source=piece.source,
    )


def _from_roll_result(raw: RollNestingResult) -> PieceBasedNestingResult:
    return PieceBasedNestingResult(
        nesting_method=raw.nesting_method,
        nesting_source=raw.nesting_source,
        is_fallback=raw.is_fallback,
        roll_width_mm=raw.roll_width_mm,
        material_width_m=raw.material_width_m,
        spacing_mm=raw.spacing_mm,
        pieces_count=raw.pieces_count,
        nested_roll_length_m=raw.nested_roll_length_m,
        recommended_roll_length_m=raw.recommended_roll_length_m,
        quantity_m2=raw.quantity_m2,
        rotation_allowed=raw.rotation_allowed,
        roll_width_missing=raw.roll_width_missing,
        geometry_missing=raw.geometry_missing,
        oversized_piece=raw.oversized_piece,
        placements=[
            PiecePlacement(
                piece_id=p.piece_id,
                label=p.label,
                x_mm=p.x_mm,
                y_mm=p.y_mm,
                width_mm=p.width_mm,
                height_mm=p.height_mm,
                rotation_deg=p.rotation_deg,
            )
            for p in raw.placements
        ],
        warnings=list(raw.warnings),
    )


def estimate_piece_based_rectangular_nesting(
    pieces: Sequence[FaceVinylPiece],
    *,
    roll_width_mm: Optional[float],
    rotation_allowed: bool = True,
    nesting_source: str = "letter_bounding_boxes",
    spacing_mm: float = DEFAULT_SPACING_MM,
    apply_internal_waste: bool = True,
) -> PieceBasedNestingResult:
    """Face-vinyl roll nesting — delegates to ``flat_material_nesting``."""
    flat_pieces = [_to_flat_piece(p) for p in pieces]
    raw = estimate_roll_rectangular_nesting(
        flat_pieces,
        roll_width_mm=roll_width_mm,
        rotation_allowed=rotation_allowed,
        nesting_source=nesting_source,
        spacing_mm=spacing_mm,
        apply_internal_waste=apply_internal_waste,
    )
    return _from_roll_result(raw)
