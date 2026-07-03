"""Face vinyl (letter faces) task instructions and estimated nesting — TPL-VOLUMETRIC-LETTERS.

Separate from return-vinyl / cant band linear consumption (see estimate_return_vinyl_linear_consumption).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from services.face_vinyl_piece_nesting import (
    DEFAULT_SPACING_MM,
    FaceVinylPiece,
    PieceBasedNestingResult,
    estimate_piece_based_rectangular_nesting,
)
from services.task_preparation_readiness_service import extract_quote_input_from_snapshot
from services.volumetric_finish_assignment_service import (
    build_face_vinyl_operator_instructions,
    build_return_vinyl_operator_instructions,
    resolve_volumetric_operational_quote_input,
)
from services.volumetric_quote_input_policy import (
    normalize_face_finish_type,
    normalize_mounting_system,
)

FACE_VINYL_PROCESS_ID = "vinyl_application"
FACE_VINYL_DISPLAY_NAME = "Colantare fețe litere"
FACE_VINYL_APPLICATION_TARGET = "letter_faces"
WASTE_FACTOR = 1.10

# Return vinyl (cant) — documented linear rule; not used for face-vinyl tasks.
RETURN_VINYL_BAND_EXTRA_MM = 10

PIECE_SOURCES = frozenset({"letter_bounding_boxes", "face_vinyl_pieces", "product_spec_piece"})
FALLBACK_SOURCES = frozenset({"assembly_bbox", "none"})


@dataclass(frozen=True)
class NestingPiece:
    """Backward-compatible piece shape for tests and legacy callers."""

    width_mm: float
    height_mm: float
    area_sqm: Optional[float] = None
    piece_id: Optional[str] = None
    label: Optional[str] = None
    source: str = "vector_piece"


@dataclass
class FaceVinylNestingResult:
    nesting_width_mm: Optional[float] = None
    nesting_method: str = "estimated_shelf"
    nesting_source: str = "none"
    is_fallback: bool = False
    pieces_count: int = 0
    nested_roll_length_m: Optional[float] = None
    recommended_roll_length_m: Optional[float] = None
    material_width_m: Optional[float] = None
    quantity_m2: Optional[float] = None
    rotation_allowed: bool = True
    roll_width_missing: bool = False
    geometry_missing: bool = False
    oversized_piece: bool = False
    spacing_mm: float = DEFAULT_SPACING_MM
    placements: List[dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def extract_product_spec_from_snapshot(snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        return {}
    for key in ("product_spec_json", "product_spec"):
        raw = snapshot.get(key)
        if isinstance(raw, dict):
            return dict(raw)
        if isinstance(raw, str) and raw.strip():
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
    quote_snapshot = snapshot.get("quote_snapshot")
    if isinstance(quote_snapshot, dict):
        nested = quote_snapshot.get("product_spec_json") or quote_snapshot.get("product_spec")
        if isinstance(nested, dict):
            return dict(nested)
    return {}


def has_face_vinyl_application(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> bool:
    """True only when the order/spec explicitly selects face vinyl — never from generic task title."""
    qi = resolve_volumetric_operational_quote_input(quote_input, product_spec=product_spec)
    ps = product_spec or {}

    target = str(qi.get("vinyl_application_target") or ps.get("vinyl_application_target") or "").strip().lower()
    if target == FACE_VINYL_APPLICATION_TARGET:
        return True

    face = normalize_face_finish_type(qi.get("face_finish_type") or ps.get("face_finish_type"))
    if face != "none":
        return True

    for raw_enabled in (qi.get("face_vinyl_enabled"), ps.get("face_vinyl_enabled")):
        if raw_enabled is True:
            return True
        if isinstance(raw_enabled, str) and raw_enabled.strip().lower() in {"true", "1", "yes", "on"}:
            return True

    return False


def is_rotation_allowed_for_face_vinyl(quote_input: Mapping[str, Any] | None) -> bool:
    qi = quote_input or {}
    raw = qi.get("face_vinyl_rotation_allowed")
    if isinstance(raw, bool):
        return raw
    face = normalize_face_finish_type(qi.get("face_finish_type"))
    if face == "oracal_651":
        return True
    if face in {"printed_vinyl", "printed_laminated_vinyl"}:
        return False
    return False


def _positive_float(raw: Any) -> Optional[float]:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def resolve_face_vinyl_roll_width_mm(quote_input: Mapping[str, Any] | None) -> Optional[float]:
    """Material roll width from order selection only — no default."""
    qi = quote_input or {}
    return _positive_float(qi.get("face_vinyl_roll_width_mm"))


def resolve_face_area_sqm(quote_input: Mapping[str, Any] | None) -> Optional[float]:
    qi = quote_input or {}
    return _positive_float(qi.get("letter_face_area_m2"))


def _parse_piece_entries(
    raw_boxes: Any,
    *,
    default_source: str,
) -> List[NestingPiece]:
    pieces: List[NestingPiece] = []
    if not isinstance(raw_boxes, list):
        return pieces
    for index, entry in enumerate(raw_boxes):
        if not isinstance(entry, dict):
            continue
        w = _positive_float(entry.get("width_mm"))
        h = _positive_float(entry.get("height_mm"))
        if w is None or h is None:
            continue
        piece_id = str(entry.get("piece_id") or entry.get("id") or f"piece_{index + 1}").strip()
        label = str(entry.get("label") or entry.get("name") or "").strip() or None
        area = _positive_float(entry.get("area_sqm"))
        src = str(entry.get("source") or default_source).strip() or default_source
        pieces.append(
            NestingPiece(
                width_mm=w,
                height_mm=h,
                area_sqm=area,
                piece_id=piece_id,
                label=label,
                source=src,
            )
        )
    return pieces


def collect_nesting_pieces(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> Tuple[List[NestingPiece], str]:
    qi = quote_input or {}
    ps = product_spec or {}

    for key, source in (
        ("letter_bounding_boxes", "letter_bounding_boxes"),
        ("face_vinyl_pieces", "face_vinyl_pieces"),
    ):
        raw = qi.get(key) or ps.get(key)
        pieces = _parse_piece_entries(raw, default_source=source)
        if pieces:
            return pieces, source

    width = _positive_float(
        qi.get("width_mm")
        or qi.get("vector_suggested_assembly_width_mm")
        or ps.get("vector_suggested_assembly_width_mm")
    )
    height = _positive_float(
        qi.get("height_mm")
        or qi.get("vector_suggested_assembly_height_mm")
        or ps.get("vector_suggested_assembly_height_mm")
    )
    if width is not None and height is not None:
        area = resolve_face_area_sqm(qi)
        return [
            NestingPiece(
                width_mm=width,
                height_mm=height,
                area_sqm=area,
                piece_id="assembly",
                source="assembly_bbox",
            )
        ], "assembly_bbox"

    return [], "none"


def _to_face_vinyl_pieces(pieces: List[NestingPiece]) -> List[FaceVinylPiece]:
    out: List[FaceVinylPiece] = []
    for index, piece in enumerate(pieces):
        out.append(
            FaceVinylPiece(
                piece_id=str(piece.piece_id or f"piece_{index + 1}"),
                label=piece.label,
                width_mm=piece.width_mm,
                height_mm=piece.height_mm,
                source=piece.source or "vector_piece",
                area_sqm=piece.area_sqm,
            )
        )
    return out


def _nesting_result_from_piece_based(raw: PieceBasedNestingResult) -> FaceVinylNestingResult:
    return FaceVinylNestingResult(
        nesting_width_mm=raw.roll_width_mm,
        nesting_method=raw.nesting_method,
        nesting_source=raw.nesting_source,
        is_fallback=raw.is_fallback,
        pieces_count=raw.pieces_count,
        nested_roll_length_m=raw.nested_roll_length_m,
        recommended_roll_length_m=raw.recommended_roll_length_m,
        material_width_m=raw.material_width_m,
        quantity_m2=raw.quantity_m2,
        rotation_allowed=raw.rotation_allowed,
        roll_width_missing=raw.roll_width_missing,
        geometry_missing=raw.geometry_missing,
        oversized_piece=raw.oversized_piece,
        spacing_mm=raw.spacing_mm,
        placements=[
            {
                "piece_id": p.piece_id,
                "label": p.label,
                "x_mm": p.x_mm,
                "y_mm": p.y_mm,
                "width_mm": p.width_mm,
                "height_mm": p.height_mm,
                "rotation_deg": p.rotation_deg,
            }
            for p in raw.placements
        ],
        warnings=list(raw.warnings),
    )


def estimate_face_vinyl_nesting(
    pieces: List[NestingPiece],
    *,
    roll_width_mm: Optional[float],
    rotation_allowed: bool = True,
    nesting_source: str = "assembly_bbox",
    spacing_mm: float = DEFAULT_SPACING_MM,
) -> FaceVinylNestingResult:
    raw = estimate_piece_based_rectangular_nesting(
        _to_face_vinyl_pieces(pieces),
        roll_width_mm=roll_width_mm,
        rotation_allowed=rotation_allowed,
        nesting_source=nesting_source,
        spacing_mm=spacing_mm,
    )
    return _nesting_result_from_piece_based(raw)


def estimate_return_vinyl_linear_consumption(
    *,
    cant_width_mm: float,
    perimeter_m: float,
    roll_width_mm: Optional[float] = None,
) -> dict[str, Any]:
    """Return-vinyl band rule (cant aluminiu) — not face nesting."""
    band_width_mm = float(cant_width_mm) + RETURN_VINYL_BAND_EXTRA_MM
    recommended_length_m = round(float(perimeter_m) * WASTE_FACTOR, 4)
    payload: dict[str, Any] = {
        "application_target": "aluminum_return",
        "band_width_mm": band_width_mm,
        "recommended_length_m": recommended_length_m,
    }
    if roll_width_mm and roll_width_mm > 0:
        bands = int(float(roll_width_mm) // band_width_mm)
        if bands > 0:
            payload["bands_per_roll"] = bands
            payload["roll_length_m_needed"] = round(recommended_length_m / bands, 4)
    return payload


def resolve_vinyl_material_label(quote_input: Mapping[str, Any] | None) -> str:
    qi = quote_input or {}
    face = normalize_face_finish_type(qi.get("face_finish_type"))
    if face == "oracal_651":
        material_name = "Oracal 651"
    elif face == "printed_vinyl":
        material_name = "Autocolant print"
    elif face == "printed_laminated_vinyl":
        material_name = "Autocolant print + laminare"
    else:
        material_name = "Autocolant față litere"

    code = str(qi.get("face_vinyl_color_code") or "").strip()
    color_name = str(qi.get("face_vinyl_color_name") or "").strip()
    if code and color_name:
        return f"{material_name} — {code} {color_name}"
    if code:
        return f"{material_name} — {code}"
    return material_name


def _material_short_label(quote_input: Mapping[str, Any] | None) -> str:
    qi = quote_input or {}
    face = normalize_face_finish_type(qi.get("face_finish_type"))
    if face == "oracal_651":
        return "Oracal 651"
    if face == "printed_vinyl":
        return "Autocolant print"
    if face == "printed_laminated_vinyl":
        return "Autocolant print + laminare"
    return "Autocolant față litere"


def _color_line(quote_input: Mapping[str, Any] | None) -> Optional[str]:
    qi = quote_input or {}
    code = str(qi.get("face_vinyl_color_code") or "").strip()
    color_name = str(qi.get("face_vinyl_color_name") or "").strip()
    if code and color_name:
        return f"{code} {color_name}"
    if code:
        return code
    if color_name:
        return color_name
    return None


def _fmt_ro_number(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def _operational_steps(quote_input: Mapping[str, Any] | None) -> List[str]:
    return [
        "Verifică autocolantul și culoarea înainte de aplicare.",
        "Curăță fețele din plexiglas înainte de colantare.",
        "Aplică autocolantul pe fețele literelor, curat și aliniat.",
        "Evită bulele, cutele și tensiunile în material.",
        "Finisează marginile după forma fiecărei litere.",
        "Verifică aspectul final înainte de predarea mai departe.",
    ]


def build_return_vinyl_task_instructions(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> str | None:
    """Operator instructions for cant/return vinyl — operational copy only."""
    return build_return_vinyl_operator_instructions(
        quote_input,
        product_spec=product_spec,
    )


@dataclass(frozen=True)
class FaceVinylUsedSqmResolution:
    """Pricing quantity basis for face vinyl material + application labor (mp folie folosită)."""

    value: Optional[float]
    source: str  # nesting | fallback_face_area | none
    quantity_basis: str
    face_vinyl_used_sqm: Optional[float] = None
    recommended_roll_length_m: Optional[float] = None
    material_width_m: Optional[float] = None
    face_area_sqm: Optional[float] = None
    fallback_weak_estimate: bool = False
    warnings: Tuple[str, ...] = ()


def resolve_face_vinyl_used_sqm(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> FaceVinylUsedSqmResolution:
    """Resolve mp of folie folosită for pricing — nesting first, then face_area × 1.10 fallback."""
    if not has_face_vinyl_application(quote_input, product_spec=product_spec):
        return FaceVinylUsedSqmResolution(
            value=None,
            source="none",
            quantity_basis="face_vinyl_not_selected",
        )

    qi = resolve_volumetric_operational_quote_input(quote_input, product_spec=product_spec)
    roll_width_mm = resolve_face_vinyl_roll_width_mm(qi)
    face_area = resolve_face_area_sqm(qi)
    rotation_allowed = is_rotation_allowed_for_face_vinyl(qi)
    pieces, nesting_source = collect_nesting_pieces(qi, product_spec=product_spec)
    nesting = estimate_face_vinyl_nesting(
        pieces,
        roll_width_mm=roll_width_mm,
        rotation_allowed=rotation_allowed,
        nesting_source=nesting_source,
    )

    width_m = nesting.material_width_m
    rec_len = nesting.recommended_roll_length_m
    if (
        width_m is not None
        and rec_len is not None
        and float(rec_len) > 0
        and not nesting.roll_width_missing
        and not nesting.geometry_missing
        and not nesting.oversized_piece
    ):
        used = nesting.quantity_m2
        if used is None:
            used = round(float(rec_len) * width_m, 6)
        return FaceVinylUsedSqmResolution(
            value=used,
            source="nesting",
            quantity_basis="recommended_roll_length_m × material_width_m",
            face_vinyl_used_sqm=used,
            recommended_roll_length_m=float(rec_len),
            material_width_m=width_m,
            face_area_sqm=face_area,
            fallback_weak_estimate=nesting.is_fallback,
            warnings=tuple(nesting.warnings),
        )

    if face_area is not None and face_area > 0:
        used = round(float(face_area) * WASTE_FACTOR, 6)
        warnings: list[str] = list(nesting.warnings)
        if nesting.roll_width_missing:
            warnings.append("roll_width_missing")
        if nesting.geometry_missing:
            warnings.append("geometry_missing")
        warnings.append("fallback_face_area_with_waste")
        return FaceVinylUsedSqmResolution(
            value=used,
            source="fallback_face_area",
            quantity_basis="face_area_sqm × 1.10 (estimare minimă)",
            face_vinyl_used_sqm=used,
            face_area_sqm=face_area,
            fallback_weak_estimate=True,
            warnings=tuple(warnings),
        )

    return FaceVinylUsedSqmResolution(
        value=None,
        source="none",
        quantity_basis="missing_geometry",
        warnings=tuple(nesting.warnings),
    )


def _build_nesting_handoff_block(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
    resolution: FaceVinylUsedSqmResolution,
) -> dict[str, Any]:
    qi = quote_input or {}
    pieces, nesting_source = collect_nesting_pieces(qi, product_spec=product_spec)
    nesting = estimate_face_vinyl_nesting(
        pieces,
        roll_width_mm=resolve_face_vinyl_roll_width_mm(qi),
        rotation_allowed=is_rotation_allowed_for_face_vinyl(qi),
        nesting_source=nesting_source,
    )
    color_line = _color_line(qi)
    material_block: dict[str, Any] = {
        "name": _material_short_label(qi),
        "roll_width_mm": resolve_face_vinyl_roll_width_mm(qi),
    }
    if color_line:
        parts = color_line.split(" ", 1)
        material_block["color_code"] = parts[0]
        if len(parts) > 1:
            material_block["color_name"] = parts[1]

    return {
        "enabled": True,
        "material": material_block,
        "nesting": {
            "method": nesting.nesting_method,
            "is_fallback": nesting.is_fallback,
            "spacing_mm": nesting.spacing_mm,
            "recommended_roll_length_m": nesting.recommended_roll_length_m,
            "nested_roll_length_m": nesting.nested_roll_length_m,
            "material_width_m": nesting.material_width_m,
            "quantity_m2": resolution.face_vinyl_used_sqm,
            "pieces_count": nesting.pieces_count,
            "rotations_allowed": list((0, 90, 180, 270) if nesting.rotation_allowed else (0,)),
            "placements": nesting.placements,
            "nesting_source": nesting.nesting_source,
        },
    }


def build_face_vinyl_handoff_for_quote(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Persisted on quote/order snapshot for execution plan + pricing audit."""
    resolution = resolve_face_vinyl_used_sqm(quote_input, product_spec=product_spec)
    metadata = build_face_vinyl_task_metadata(quote_input, product_spec=product_spec)
    nesting_block = _build_nesting_handoff_block(
        quote_input,
        product_spec=product_spec,
        resolution=resolution,
    )
    return {
        "face_vinyl_used_sqm": resolution.face_vinyl_used_sqm,
        "quantity_basis": resolution.quantity_basis,
        "quantity_source": resolution.source,
        "fallback_weak_estimate": resolution.fallback_weak_estimate,
        "recommended_roll_length_m": resolution.recommended_roll_length_m,
        "material_width_m": resolution.material_width_m,
        "face_vinyl_metadata": metadata,
        "warnings": list(resolution.warnings),
        **nesting_block,
    }


def build_face_vinyl_task_metadata(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    qi = quote_input or {}
    face_area = resolve_face_area_sqm(qi)
    roll_width = resolve_face_vinyl_roll_width_mm(qi)
    rotation_allowed = is_rotation_allowed_for_face_vinyl(qi)
    pieces, nesting_source = collect_nesting_pieces(qi, product_spec=product_spec)
    nesting = estimate_face_vinyl_nesting(
        pieces,
        roll_width_mm=roll_width,
        rotation_allowed=rotation_allowed,
        nesting_source=nesting_source,
    )

    metadata: dict[str, Any] = {
        "vinyl_application_target": FACE_VINYL_APPLICATION_TARGET,
        "vinyl_material_name": _material_short_label(qi),
        "face_vinyl_color_code": str(qi.get("face_vinyl_color_code") or "").strip() or None,
        "face_vinyl_color_name": str(qi.get("face_vinyl_color_name") or "").strip() or None,
        "face_area_sqm": face_area,
        "roll_width_mm": roll_width,
        "nesting_method": nesting.nesting_method,
        "nesting_source": nesting.nesting_source,
        "is_fallback": nesting.is_fallback,
        "pieces_count": nesting.pieces_count,
        "nested_roll_length_m": nesting.nested_roll_length_m,
        "recommended_roll_length_m": nesting.recommended_roll_length_m,
        "material_width_m": nesting.material_width_m,
        "quantity_m2": nesting.quantity_m2,
        "spacing_mm": nesting.spacing_mm,
        "placements": nesting.placements,
        "rotation_allowed": rotation_allowed,
    }
    if nesting.roll_width_missing:
        metadata["nesting_warning"] = "roll_width_missing"
    elif nesting.geometry_missing:
        metadata["nesting_warning"] = "geometry_missing"
    elif nesting.is_fallback:
        metadata["nesting_warning"] = "fallback_weak_estimate"
    return metadata


def build_face_vinyl_task_instructions(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> str:
    """Operator-facing instructions — no internal pricing/reserve/method labels."""
    qi = resolve_volumetric_operational_quote_input(quote_input, product_spec=product_spec)
    if qi.get("letter_group_face_vinyl_handoff") or qi.get("face_vinyl_enabled") is True:
        return build_face_vinyl_operator_instructions(quote_input, product_spec=product_spec)

    metadata = build_face_vinyl_task_metadata(qi, product_spec=product_spec)
    material_label = resolve_vinyl_material_label(qi)
    color_line = _color_line(qi)
    roll_width = metadata.get("roll_width_mm")
    nested_len = metadata.get("nested_roll_length_m")
    is_fallback = bool(metadata.get("is_fallback"))

    sections: List[str] = []

    sections.append("CE FAC ACUM")
    sections.append("")
    sections.append(
        "Colantezi fețele din plexiglas ale literelor cu autocolantul selectat."
    )

    sections.append("")
    sections.append("DATE TEHNICE")
    sections.append("")
    sections.append(f"Material autocolant: {material_label}")
    if color_line:
        sections.append(f"Culoare: {color_line}")
    if roll_width:
        sections.append(f"Lățime rolă: {int(roll_width)} mm")
    if nested_len is not None and float(nested_len) > 0:
        if is_fallback:
            sections.append(
                f"Material estimat pentru pregătire: {_fmt_ro_number(float(nested_len))} ml"
            )
        else:
            sections.append(f"Lungime pregătire: {_fmt_ro_number(float(nested_len))} ml")
            sections.append("Nesting: calculat pe piesele literelor")
    elif not roll_width:
        sections.append(
            "Lățimea materialului selectat nu este setată; verifică manual încadrarea."
        )

    # Pași de lucru
    sections.append("")
    sections.append("PAȘI DE LUCRU")
    sections.append("")
    for index, step in enumerate(_operational_steps(qi), start=1):
        sections.append(f"{index}. {step}")

    return "\n".join(sections)


def _normalize_process_id(task: dict) -> str:
    return str(task.get("process_id") or "").strip().lower()


def apply_face_vinyl_taxonomy_to_task(
    task: dict,
    *,
    quote_input: Mapping[str, Any] | None,
    product_spec: Mapping[str, Any] | None = None,
    set_owner_instructions: bool = False,
) -> dict:
    updated = dict(task)
    if _normalize_process_id(updated) != FACE_VINYL_PROCESS_ID:
        return updated

    updated["display_name"] = FACE_VINYL_DISPLAY_NAME
    updated["name"] = FACE_VINYL_DISPLAY_NAME
    updated["vinyl_application_target"] = FACE_VINYL_APPLICATION_TARGET
    metadata = build_face_vinyl_task_metadata(quote_input, product_spec=product_spec)
    updated["face_vinyl_metadata"] = metadata
    if set_owner_instructions:
        updated["instructions"] = build_face_vinyl_task_instructions(
            quote_input,
            product_spec=product_spec,
        )
    return updated


def apply_face_vinyl_taxonomy_to_plan_tasks(
    tasks: List[Any],
    *,
    quote_input: Mapping[str, Any] | None,
    product_spec: Mapping[str, Any] | None = None,
    set_owner_instructions: bool = False,
) -> Tuple[List[Any], str]:
    if not isinstance(tasks, list):
        return tasks, "invalid_tasks"

    applicable = has_face_vinyl_application(quote_input, product_spec=product_spec)
    before = json.dumps(tasks, sort_keys=True, ensure_ascii=False)

    if not applicable:
        filtered = [
            entry
            for entry in tasks
            if not (isinstance(entry, dict) and _normalize_process_id(entry) == FACE_VINYL_PROCESS_ID)
        ]
        after = json.dumps(filtered, sort_keys=True, ensure_ascii=False)
        if before == after:
            return filtered, "unchanged"
        return filtered, "filtered_no_face_vinyl"

    updated: List[Any] = []
    for entry in tasks:
        if isinstance(entry, dict):
            updated.append(
                apply_face_vinyl_taxonomy_to_task(
                    entry,
                    quote_input=quote_input,
                    product_spec=product_spec,
                    set_owner_instructions=set_owner_instructions,
                )
            )
        else:
            updated.append(entry)

    after = json.dumps(updated, sort_keys=True, ensure_ascii=False)
    if before == after:
        return updated, "unchanged"
    return updated, "updated"


def recalculate_plan_total_minutes(tasks: List[Any]) -> float:
    total = 0.0
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        raw = entry.get("estimated_time_minutes")
        if isinstance(raw, bool):
            continue
        if isinstance(raw, (int, float)):
            total += float(raw)
    return total


def apply_face_vinyl_from_order_snapshot(
    tasks: List[Any],
    snapshot: Mapping[str, Any] | None,
    *,
    set_owner_instructions: bool = False,
) -> Tuple[List[Any], str]:
    quote_input = extract_quote_input_from_snapshot(snapshot or {})
    product_spec = extract_product_spec_from_snapshot(snapshot or {})
    return apply_face_vinyl_taxonomy_to_plan_tasks(
        tasks,
        quote_input=quote_input,
        product_spec=product_spec,
        set_owner_instructions=set_owner_instructions,
    )
