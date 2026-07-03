"""Generic flat-material nesting foundation — roll and sheet adapters.

Geometric pieces (``FlatPiece``) are material-agnostic: width/height in mm only.
Material profiles select the adapter:

* ``material_type=roll`` → ``estimate_roll_rectangular_nesting`` (ml + mp)
* ``material_type=sheet`` → ``estimate_sheet_rectangular_nesting`` (sheets + mp)

Vinyl face nesting wraps the roll adapter via ``face_vinyl_piece_nesting``.
Plexiglas / Forex / ACM sheet nesting uses the sheet adapter directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional, Sequence, Tuple

DEFAULT_SPACING_MM = 10.0
INTERNAL_WASTE_FACTOR = 1.10
ROTATIONS_DEG = (0, 90, 180, 270)


@dataclass(frozen=True)
class FlatPiece:
    """Material-agnostic flat piece geometry — no consumption fields."""

    piece_id: str
    width_mm: float
    height_mm: float
    label: Optional[str] = None
    quantity: int = 1
    source: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RollFlatPlacement:
    piece_id: str
    label: Optional[str]
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotation_deg: int


@dataclass(frozen=True)
class SheetFlatPlacement:
    piece_id: str
    label: Optional[str]
    sheet_index: int
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotation_deg: int


@dataclass(frozen=True)
class RollMaterialProfile:
    material_code: str
    material_type: str = "roll"
    roll_width_mm: float = 0.0
    spacing_mm: float = DEFAULT_SPACING_MM


@dataclass(frozen=True)
class SheetMaterialProfile:
    material_code: str
    material_type: str = "sheet"
    sheet_width_mm: float = 0.0
    sheet_height_mm: float = 0.0
    spacing_mm: float = DEFAULT_SPACING_MM
    thickness_mm: Optional[float] = None
    raw_sheet_width_mm: Optional[float] = None
    raw_sheet_height_mm: Optional[float] = None


@dataclass
class RollNestingResult:
    material_type: str = "roll"
    nesting_method: str = "piece_based_rectangular"
    nesting_source: str = "letter_bounding_boxes"
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
    placements: List[RollFlatPlacement] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SheetNestingResult:
    material_type: str = "sheet"
    nesting_method: str = "sheet_rectangular"
    nesting_source: str = "letter_bounding_boxes"
    sheet_width_mm: Optional[float] = None
    sheet_height_mm: Optional[float] = None
    spacing_mm: float = DEFAULT_SPACING_MM
    pieces_count: int = 0
    sheets_used: int = 0
    allocated_sheet_area_m2: Optional[float] = None
    used_piece_bbox_area_m2: Optional[float] = None
    waste_area_m2: Optional[float] = None
    waste_percent: Optional[float] = None
    remaining_area_m2: Optional[float] = None
    remaining_percent: Optional[float] = None
    remaining_policy: Optional[str] = None
    rotation_allowed: bool = True
    geometry_missing: bool = False
    sheet_size_missing: bool = False
    unplaceable_pieces: List[str] = field(default_factory=list)
    placements: List[SheetFlatPlacement] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def expand_flat_pieces(pieces: Sequence[FlatPiece]) -> List[FlatPiece]:
    """Expand ``quantity`` into individual unit pieces with stable ids."""
    expanded: List[FlatPiece] = []
    for piece in pieces:
        qty = max(1, int(piece.quantity or 1))
        for index in range(qty):
            suffix = f"_{index + 1}" if qty > 1 else ""
            expanded.append(
                FlatPiece(
                    piece_id=f"{piece.piece_id}{suffix}",
                    width_mm=piece.width_mm,
                    height_mm=piece.height_mm,
                    label=piece.label,
                    quantity=1,
                    source=piece.source,
                    metadata=dict(piece.metadata),
                )
            )
    return expanded


def flat_pieces_from_bounding_boxes(
    boxes: Sequence[Mapping[str, Any]],
    *,
    default_source: str = "letter_bounding_boxes",
) -> List[FlatPiece]:
    """Build ``FlatPiece`` list from ``letter_bounding_boxes`` / spec entries."""
    out: List[FlatPiece] = []
    for index, entry in enumerate(boxes):
        if not isinstance(entry, dict):
            continue
        try:
            w = float(entry.get("width_mm"))
            h = float(entry.get("height_mm"))
        except (TypeError, ValueError):
            continue
        if w <= 0 or h <= 0:
            continue
        piece_id = str(entry.get("piece_id") or entry.get("id") or f"piece_{index + 1}").strip()
        label = str(entry.get("label") or entry.get("name") or "").strip() or None
        qty_raw = entry.get("quantity", 1)
        try:
            qty = max(1, int(qty_raw))
        except (TypeError, ValueError):
            qty = 1
        source = str(entry.get("source") or default_source).strip() or default_source
        out.append(
            FlatPiece(
                piece_id=piece_id,
                width_mm=w,
                height_mm=h,
                label=label,
                quantity=qty,
                source=source,
            )
        )
    return out


def _orientations(
    piece: FlatPiece,
    rotation_allowed: bool,
) -> List[Tuple[float, float, int]]:
    seen: set[Tuple[float, float]] = set()
    out: List[Tuple[float, float, int]] = []
    for deg in ROTATIONS_DEG if rotation_allowed else (0,):
        if deg in (0, 180):
            w, h = piece.width_mm, piece.height_mm
        else:
            w, h = piece.height_mm, piece.width_mm
        key = (round(w, 4), round(h, 4))
        if key in seen:
            continue
        seen.add(key)
        out.append((w, h, deg))
    return out


def _piece_fits_sheet(
    piece: FlatPiece,
    sheet_width_mm: float,
    sheet_height_mm: float,
    rotation_allowed: bool,
) -> bool:
    for w, h, _rot in _orientations(piece, rotation_allowed):
        if w <= sheet_width_mm + 1e-6 and h <= sheet_height_mm + 1e-6:
            return True
    return False


def estimate_roll_rectangular_nesting(
    pieces: Sequence[FlatPiece],
    *,
    roll_width_mm: Optional[float],
    rotation_allowed: bool = True,
    nesting_source: str = "letter_bounding_boxes",
    spacing_mm: float = DEFAULT_SPACING_MM,
    apply_internal_waste: bool = True,
) -> RollNestingResult:
    """Shelf packing on fixed roll width; rotations in 90° steps when allowed."""
    is_fallback = nesting_source in {"assembly_bbox", "none"}
    method = "fallback_weak_estimate" if is_fallback else "piece_based_rectangular"
    expanded = expand_flat_pieces(pieces)

    result = RollNestingResult(
        nesting_method=method,
        nesting_source=nesting_source,
        is_fallback=is_fallback,
        pieces_count=len(expanded),
        rotation_allowed=rotation_allowed,
        spacing_mm=float(spacing_mm),
    )

    if roll_width_mm is None or roll_width_mm <= 0:
        result.roll_width_missing = True
        result.warnings.append("roll_width_missing")
        return result

    result.roll_width_mm = float(roll_width_mm)
    result.material_width_m = round(float(roll_width_mm) / 1000.0, 6)

    if not expanded:
        result.geometry_missing = True
        result.warnings.append("geometry_missing")
        return result

    gap = max(0.0, float(spacing_mm))
    ordered = sorted(expanded, key=lambda p: max(p.width_mm, p.height_mm), reverse=True)

    shelves: List[List[float]] = []
    placements: List[RollFlatPlacement] = []

    for piece in ordered:
        placed = False
        for w, h, rot in _orientations(piece, rotation_allowed):
            if w > roll_width_mm + 1e-6:
                continue
            for shelf in shelves:
                remaining = roll_width_mm - shelf[0]
                need = w if shelf[0] <= 1e-6 else w + gap
                if need <= remaining + 1e-6:
                    x = shelf[0] + (gap if shelf[0] > 1e-6 else 0.0)
                    shelf[0] = x + w
                    shelf[1] = max(shelf[1], h)
                    placements.append(
                        RollFlatPlacement(
                            piece_id=piece.piece_id,
                            label=piece.label,
                            x_mm=round(x, 3),
                            y_mm=round(shelf[2], 3),
                            width_mm=round(w, 3),
                            height_mm=round(h, 3),
                            rotation_deg=rot,
                        )
                    )
                    placed = True
                    break
            if placed:
                break

        if placed:
            continue

        for w, h, rot in _orientations(piece, rotation_allowed):
            if w <= roll_width_mm + 1e-6:
                y_offset = sum(s[1] for s in shelves)
                shelves.append([w, h, y_offset])
                placements.append(
                    RollFlatPlacement(
                        piece_id=piece.piece_id,
                        label=piece.label,
                        x_mm=0.0,
                        y_mm=round(y_offset, 3),
                        width_mm=round(w, 3),
                        height_mm=round(h, 3),
                        rotation_deg=rot,
                    )
                )
                placed = True
                break

        if not placed:
            result.oversized_piece = True
            result.warnings.append("piece_wider_than_roll")
            return result

    nested_mm = sum(shelf[1] for shelf in shelves)
    nested_m = nested_mm / 1000.0
    result.nested_roll_length_m = round(nested_m, 4)
    recommended = nested_m * (INTERNAL_WASTE_FACTOR if apply_internal_waste else 1.0)
    result.recommended_roll_length_m = round(recommended, 4)
    if result.material_width_m is not None and result.recommended_roll_length_m is not None:
        result.quantity_m2 = round(result.recommended_roll_length_m * result.material_width_m, 6)
    result.placements = placements
    return result


def estimate_sheet_rectangular_nesting(
    pieces: Sequence[FlatPiece],
    *,
    sheet_width_mm: Optional[float],
    sheet_height_mm: Optional[float],
    rotation_allowed: bool = True,
    nesting_source: str = "letter_bounding_boxes",
    spacing_mm: float = DEFAULT_SPACING_MM,
) -> SheetNestingResult:
    """Shelf/row packing on fixed sheet size; opens new sheets as needed."""
    expanded = expand_flat_pieces(pieces)
    result = SheetNestingResult(
        nesting_source=nesting_source,
        pieces_count=len(expanded),
        rotation_allowed=rotation_allowed,
        spacing_mm=float(spacing_mm),
    )

    if sheet_width_mm is None or sheet_height_mm is None or sheet_width_mm <= 0 or sheet_height_mm <= 0:
        result.sheet_size_missing = True
        result.warnings.append("sheet_size_missing")
        return result

    sw = float(sheet_width_mm)
    sh = float(sheet_height_mm)
    result.sheet_width_mm = sw
    result.sheet_height_mm = sh

    if not expanded:
        result.geometry_missing = True
        result.warnings.append("geometry_missing")
        return result

    unplaceable: List[str] = []
    for piece in expanded:
        if not _piece_fits_sheet(piece, sw, sh, rotation_allowed):
            unplaceable.append(piece.piece_id)
    if unplaceable:
        result.unplaceable_pieces = unplaceable
        result.warnings.append("unplaceable_pieces")
        return result

    gap = max(0.0, float(spacing_mm))
    ordered = sorted(expanded, key=lambda p: max(p.width_mm, p.height_mm), reverse=True)

    sheet_shelves: List[List[List[float]]] = []
    placements: List[SheetFlatPlacement] = []

    for piece in ordered:
        placed = False
        for sheet_index, shelves in enumerate(sheet_shelves):
            for w, h, rot in _orientations(piece, rotation_allowed):
                if w > sw + 1e-6:
                    continue
                for shelf in shelves:
                    remaining = sw - shelf[0]
                    need = w if shelf[0] <= 1e-6 else w + gap
                    if need > remaining + 1e-6:
                        continue
                    y = shelf[2]
                    if y + h > sh + 1e-6:
                        continue
                    x = shelf[0] + (gap if shelf[0] > 1e-6 else 0.0)
                    shelf[0] = x + w
                    shelf[1] = max(shelf[1], h)
                    placements.append(
                        SheetFlatPlacement(
                            piece_id=piece.piece_id,
                            label=piece.label,
                            sheet_index=sheet_index,
                            x_mm=round(x, 3),
                            y_mm=round(y, 3),
                            width_mm=round(w, 3),
                            height_mm=round(h, 3),
                            rotation_deg=rot,
                        )
                    )
                    placed = True
                    break
                if placed:
                    break
            if placed:
                break

        if placed:
            continue

        for sheet_index, shelves in enumerate(sheet_shelves):
            for w, h, rot in _orientations(piece, rotation_allowed):
                if w > sw + 1e-6:
                    continue
                y_offset = sum(s[1] for s in shelves)
                if shelves:
                    y_offset += gap
                if y_offset + h > sh + 1e-6:
                    continue
                shelves.append([w, h, y_offset])
                placements.append(
                    SheetFlatPlacement(
                        piece_id=piece.piece_id,
                        label=piece.label,
                        sheet_index=sheet_index,
                        x_mm=0.0,
                        y_mm=round(y_offset, 3),
                        width_mm=round(w, 3),
                        height_mm=round(h, 3),
                        rotation_deg=rot,
                    )
                )
                placed = True
                break
            if placed:
                break

        if placed:
            continue

        for w, h, rot in _orientations(piece, rotation_allowed):
            if w <= sw + 1e-6 and h <= sh + 1e-6:
                sheet_index = len(sheet_shelves)
                sheet_shelves.append([[w, h, 0.0]])
                placements.append(
                    SheetFlatPlacement(
                        piece_id=piece.piece_id,
                        label=piece.label,
                        sheet_index=sheet_index,
                        x_mm=0.0,
                        y_mm=0.0,
                        width_mm=round(w, 3),
                        height_mm=round(h, 3),
                        rotation_deg=rot,
                    )
                )
                placed = True
                break

        if not placed:
            result.unplaceable_pieces = [piece.piece_id]
            result.warnings.append("packing_failed")
            return result

    result.sheets_used = len(sheet_shelves)
    sheet_area_m2 = (sw * sh) / 1_000_000.0
    result.allocated_sheet_area_m2 = round(sheet_area_m2 * result.sheets_used, 6)
    used_m2 = sum(p.width_mm * p.height_mm for p in placements) / 1_000_000.0
    result.used_piece_bbox_area_m2 = round(used_m2, 6)
    if result.allocated_sheet_area_m2 is not None:
        remainder = max(0.0, result.allocated_sheet_area_m2 - used_m2)
        result.remaining_area_m2 = round(remainder, 6)
        result.waste_area_m2 = result.remaining_area_m2
        if result.allocated_sheet_area_m2 > 0:
            pct = round(100.0 * remainder / result.allocated_sheet_area_m2, 2)
            result.remaining_percent = pct
            result.waste_percent = pct
        result.remaining_policy = "estimated_sheet_remainder_reusable"
    result.placements = placements
    return result


def sheet_nesting_result_to_handoff_dict(
    nesting: SheetNestingResult,
    *,
    is_fallback: bool,
    pieces_source: str,
    profile: SheetMaterialProfile | None = None,
) -> dict[str, Any]:
    """Serialize sheet nesting for quote/order handoff blocks."""
    method = nesting.nesting_method
    if is_fallback and nesting.placements:
        method = "sheet_rectangular_fallback"

    raw_w = (
        profile.raw_sheet_width_mm
        if profile and profile.raw_sheet_width_mm
        else nesting.sheet_width_mm
    )
    raw_h = (
        profile.raw_sheet_height_mm
        if profile and profile.raw_sheet_height_mm
        else nesting.sheet_height_mm
    )

    return {
        "method": method,
        "material_type": nesting.material_type,
        "is_fallback": is_fallback,
        "pieces_source": pieces_source,
        "sheets_used": nesting.sheets_used,
        "sheet_width_mm": raw_w,
        "sheet_height_mm": raw_h,
        "nesting_sheet_width_mm": nesting.sheet_width_mm,
        "nesting_sheet_height_mm": nesting.sheet_height_mm,
        "allocated_sheet_area_m2": nesting.allocated_sheet_area_m2,
        "used_piece_bbox_area_m2": nesting.used_piece_bbox_area_m2,
        "remaining_area_m2": nesting.remaining_area_m2,
        "remaining_percent": nesting.remaining_percent,
        "remaining_policy": nesting.remaining_policy,
        "waste_area_m2": nesting.waste_area_m2,
        "waste_percent": nesting.waste_percent,
        "pieces_count": nesting.pieces_count,
        "spacing_mm": nesting.spacing_mm,
        "unplaceable_pieces": list(nesting.unplaceable_pieces),
        "placements": [
            {
                "piece_id": p.piece_id,
                "label": p.label,
                "sheet_index": p.sheet_index,
                "x_mm": p.x_mm,
                "y_mm": p.y_mm,
                "width_mm": p.width_mm,
                "height_mm": p.height_mm,
                "rotation_deg": p.rotation_deg,
            }
            for p in nesting.placements
        ],
        "warnings": list(nesting.warnings),
    }


def estimate_roll_nesting_from_profile(
    pieces: Sequence[FlatPiece],
    profile: RollMaterialProfile,
    *,
    rotation_allowed: bool = True,
    nesting_source: str = "letter_bounding_boxes",
    apply_internal_waste: bool = True,
) -> RollNestingResult:
    return estimate_roll_rectangular_nesting(
        pieces,
        roll_width_mm=profile.roll_width_mm,
        rotation_allowed=rotation_allowed,
        nesting_source=nesting_source,
        spacing_mm=profile.spacing_mm,
        apply_internal_waste=apply_internal_waste,
    )


def estimate_sheet_nesting_from_profile(
    pieces: Sequence[FlatPiece],
    profile: SheetMaterialProfile,
    *,
    rotation_allowed: bool = True,
    nesting_source: str = "letter_bounding_boxes",
) -> SheetNestingResult:
    return estimate_sheet_rectangular_nesting(
        pieces,
        sheet_width_mm=profile.sheet_width_mm,
        sheet_height_mm=profile.sheet_height_mm,
        rotation_allowed=rotation_allowed,
        nesting_source=nesting_source,
        spacing_mm=profile.spacing_mm,
    )
