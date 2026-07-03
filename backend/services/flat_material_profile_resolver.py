"""Resolve sheet material profiles for flat-material nesting.

Priority:
1. ``quote_input`` / ``product_spec`` explicit overrides (role-aware)
2. Inventory / Material Registry row when provided
3. Documented internal default profile (``is_default_fallback=True``)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory_materials import Inventory_materials
from services.flat_material_nesting import SheetMaterialProfile

SOURCE_QUOTE_INPUT = "quote_input"
SOURCE_PRODUCT_SPEC = "product_spec_json"
SOURCE_MATERIAL_REGISTRY = "material_registry"
SOURCE_DEFAULT_INTERNAL = "default_profile_internal"

REMAINING_POLICY = "estimated_sheet_remainder_reusable"

INVENTORY_CODE_ALIASES: dict[str, tuple[str, ...]] = {
    "PLEXI_FACE_3MM": (
        "MAT-PLEXI-TRANSP-3MM",
        "MAT-PLEXI-ALB-3MM",
        "MAT-PLEXI-COLOR-3MM",
    ),
    "PLEXI_FACE_5MM": ("MAT-PLEXI-TRANSP-5MM",),
    "FOREX_BACKING_10MM": ("MAT-SPATE-PVC-LITERE",),
}

ROLE_DISPLAY_NAMES: dict[str, str] = {
    "plexiglass_face": "Plexiglas față",
    "forex_backing": "Forex spate",
}

ROLE_OVERRIDE_KEYS: dict[str, dict[str, tuple[str, ...]]] = {
    "plexiglass_face": {
        "width": ("plexiglass_sheet_width_mm", "sheet_width_mm"),
        "height": ("plexiglass_sheet_height_mm", "sheet_height_mm"),
        "usable_width": ("plexiglass_usable_width_mm", "usable_width_mm"),
        "usable_height": ("plexiglass_usable_height_mm", "usable_height_mm"),
        "thickness": ("plexiglass_face_thickness_mm", "letter_face_thickness_mm"),
    },
    "forex_backing": {
        "width": ("forex_backing_sheet_width_mm", "forex_sheet_width_mm", "sheet_width_mm"),
        "height": ("forex_backing_sheet_height_mm", "forex_sheet_height_mm", "sheet_height_mm"),
        "usable_width": ("forex_backing_usable_width_mm", "usable_width_mm"),
        "usable_height": ("forex_backing_usable_height_mm", "usable_height_mm"),
        "thickness": ("forex_backing_thickness_mm", "forex_thickness_mm"),
    },
}


@dataclass(frozen=True)
class SheetMaterialProfileResolution:
    material_code: str
    material_type: str = "sheet"
    sheet_width_mm: float = 0.0
    sheet_height_mm: float = 0.0
    usable_width_mm: Optional[float] = None
    usable_height_mm: Optional[float] = None
    thickness_mm: Optional[float] = None
    source: str = SOURCE_DEFAULT_INTERNAL
    is_default_fallback: bool = True
    warnings: tuple[str, ...] = field(default_factory=tuple)
    display_name: str = ""
    registry_inventory_code: Optional[str] = None

    def to_sheet_profile(self) -> SheetMaterialProfile:
        nest_w = self.usable_width_mm if self.usable_width_mm else self.sheet_width_mm
        nest_h = self.usable_height_mm if self.usable_height_mm else self.sheet_height_mm
        return SheetMaterialProfile(
            material_code=self.material_code,
            material_type=self.material_type,
            sheet_width_mm=nest_w,
            sheet_height_mm=nest_h,
            spacing_mm=10.0,
            thickness_mm=self.thickness_mm,
            raw_sheet_width_mm=self.sheet_width_mm,
            raw_sheet_height_mm=self.sheet_height_mm,
        )


def _positive_float(raw: Any) -> Optional[float]:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def _positive_int_thickness(raw: Any) -> Optional[int]:
    val = _positive_float(raw)
    if val is None:
        return None
    return int(round(val))


def _first_positive(mapping: Mapping[str, Any], keys: Sequence[str]) -> Optional[float]:
    for key in keys:
        val = _positive_float(mapping.get(key))
        if val is not None:
            return val
    return None


def _resolve_thickness_for_role(
    material_code: str,
    role: Optional[str],
    qi: Mapping[str, Any],
    ps: Mapping[str, Any],
) -> Optional[int]:
    role_keys = ROLE_OVERRIDE_KEYS.get(role or "", {}).get("thickness", ())
    for source in (qi, ps):
        for key in role_keys:
            thickness = _positive_int_thickness(source.get(key))
            if thickness is not None:
                return thickness
    if material_code.startswith("PLEXI_FACE_") and material_code.endswith("MM"):
        suffix = material_code[len("PLEXI_FACE_") : -len("MM")]
        try:
            return int(suffix)
        except ValueError:
            return None
    if material_code == "FOREX_BACKING_10MM":
        return 10
    return None


def _default_profile_for_code(
    material_code: str,
    *,
    thickness_mm: Optional[int] = None,
) -> SheetMaterialProfileResolution:
    thickness = thickness_mm
    if material_code.startswith("PLEXI_FACE_"):
        if thickness is None and material_code.endswith("MM"):
            try:
                thickness = int(material_code[len("PLEXI_FACE_") : -len("MM")])
            except ValueError:
                thickness = 3
        display = f"Plexiglas față {thickness or 3} mm"
    elif material_code == "FOREX_BACKING_10MM":
        thickness = thickness or 10
        display = f"Forex spate {thickness} mm"
    else:
        display = material_code

    return SheetMaterialProfileResolution(
        material_code=material_code,
        material_type="sheet",
        sheet_width_mm=3050.0,
        sheet_height_mm=2030.0,
        usable_width_mm=3050.0,
        usable_height_mm=2030.0,
        thickness_mm=float(thickness or 3),
        source=SOURCE_DEFAULT_INTERNAL,
        is_default_fallback=True,
        warnings=("missing_sheet_profile_in_registry",),
        display_name=display,
    )


def _profile_from_registry_row(
    material_code: str,
    row: Mapping[str, Any],
    *,
    thickness_mm: Optional[int] = None,
) -> Optional[SheetMaterialProfileResolution]:
    width = _positive_float(row.get("sheet_width"))
    height = _positive_float(row.get("sheet_height"))
    if width is None or height is None:
        return None

    usable_w = _positive_float(row.get("usable_width")) or width
    usable_h = _positive_float(row.get("usable_height")) or height
    thickness = _positive_int_thickness(row.get("sheet_thickness")) or thickness_mm
    name = str(row.get("name") or material_code).strip()
    inventory_code = str(row.get("code") or "").strip() or None

    return SheetMaterialProfileResolution(
        material_code=material_code,
        material_type="sheet",
        sheet_width_mm=width,
        sheet_height_mm=height,
        usable_width_mm=usable_w,
        usable_height_mm=usable_h,
        thickness_mm=float(thickness) if thickness is not None else None,
        source=SOURCE_MATERIAL_REGISTRY,
        is_default_fallback=False,
        warnings=(),
        display_name=name,
        registry_inventory_code=inventory_code,
    )


def resolve_sheet_material_profile(
    material_code: str,
    *,
    product_spec: Mapping[str, Any] | None = None,
    quote_input: Mapping[str, Any] | None = None,
    role: str | None = None,
    registry_row: Mapping[str, Any] | None = None,
) -> SheetMaterialProfileResolution:
    """Resolve a sheet profile synchronously (optional registry row from caller)."""
    qi = quote_input or {}
    ps = product_spec or {}
    role_keys = ROLE_OVERRIDE_KEYS.get(role or {}, {})
    thickness = _resolve_thickness_for_role(material_code, role, qi, ps)

    sheet_w: Optional[float] = None
    sheet_h: Optional[float] = None
    usable_w: Optional[float] = None
    usable_h: Optional[float] = None
    source = SOURCE_DEFAULT_INTERNAL
    warnings: list[str] = []

    for mapping, src in ((qi, SOURCE_QUOTE_INPUT), (ps, SOURCE_PRODUCT_SPEC)):
        w = _first_positive(mapping, role_keys.get("width", ()))
        h = _first_positive(mapping, role_keys.get("height", ()))
        uw = _first_positive(mapping, role_keys.get("usable_width", ()))
        uh = _first_positive(mapping, role_keys.get("usable_height", ()))
        if w is not None and h is not None:
            sheet_w, sheet_h = w, h
            usable_w = uw or w
            usable_h = uh or h
            source = src
            break
        if w is not None:
            sheet_w = w
            source = src
        if h is not None:
            sheet_h = h
            source = src

    if sheet_w is not None and sheet_h is not None:
        role_label = ROLE_DISPLAY_NAMES.get(role or "", material_code)
        if role == "plexiglass_face":
            display = f"Plexiglas față {thickness or 3} mm"
        elif role == "forex_backing":
            display = f"Forex spate {thickness or 10} mm"
        else:
            display = role_label
        return SheetMaterialProfileResolution(
            material_code=material_code,
            material_type="sheet",
            sheet_width_mm=sheet_w,
            sheet_height_mm=sheet_h,
            usable_width_mm=usable_w or sheet_w,
            usable_height_mm=usable_h or sheet_h,
            thickness_mm=float(thickness) if thickness is not None else None,
            source=source,
            is_default_fallback=False,
            warnings=tuple(warnings),
            display_name=display,
        )

    if registry_row is not None:
        from_registry = _profile_from_registry_row(
            material_code,
            registry_row,
            thickness_mm=thickness,
        )
        if from_registry is not None:
            return from_registry
        warnings.append("registry_row_missing_sheet_dimensions")

    default = _default_profile_for_code(material_code, thickness_mm=thickness)
    if warnings:
        return SheetMaterialProfileResolution(
            material_code=default.material_code,
            material_type=default.material_type,
            sheet_width_mm=default.sheet_width_mm,
            sheet_height_mm=default.sheet_height_mm,
            usable_width_mm=default.usable_width_mm,
            usable_height_mm=default.usable_height_mm,
            thickness_mm=default.thickness_mm,
            source=default.source,
            is_default_fallback=True,
            warnings=tuple(default.warnings) + tuple(warnings),
            display_name=default.display_name,
        )
    return default


def resolve_plexiglass_face_material_code(
    quote_input: Mapping[str, Any] | None = None,
    product_spec: Mapping[str, Any] | None = None,
) -> str:
    qi = quote_input or {}
    ps = product_spec or {}
    thickness = (
        _positive_int_thickness(qi.get("plexiglass_face_thickness_mm"))
        or _positive_int_thickness(ps.get("plexiglass_face_thickness_mm"))
        or _positive_int_thickness(qi.get("letter_face_thickness_mm"))
        or _positive_int_thickness(ps.get("letter_face_thickness_mm"))
        or 3
    )
    return f"PLEXI_FACE_{thickness}MM"


async def load_registry_row_for_material_code(
    db: AsyncSession,
    material_code: str,
) -> Optional[dict[str, Any]]:
    """Load first matching inventory row for a nesting material code."""
    aliases = INVENTORY_CODE_ALIASES.get(material_code, ())
    if not aliases:
        return None
    rows = (
        await db.execute(
            select(Inventory_materials).where(Inventory_materials.code.in_(aliases))
        )
    ).scalars().all()
    by_code = {str(row.code): row for row in rows}
    for alias in aliases:
        row = by_code.get(alias)
        if row is None:
            continue
        return {
            "code": row.code,
            "name": row.name,
            "sheet_width": row.sheet_width,
            "sheet_height": row.sheet_height,
            "usable_width": row.usable_width,
            "usable_height": row.usable_height,
            "sheet_thickness": row.sheet_thickness,
            "sheet_format_type": row.sheet_format_type,
        }
    return None


async def resolve_sheet_material_profile_async(
    db: AsyncSession,
    material_code: str,
    *,
    product_spec: Mapping[str, Any] | None = None,
    quote_input: Mapping[str, Any] | None = None,
    role: str | None = None,
) -> SheetMaterialProfileResolution:
    """Async resolver that can load inventory registry rows."""
    registry_row = await load_registry_row_for_material_code(db, material_code)
    return resolve_sheet_material_profile(
        material_code,
        product_spec=product_spec,
        quote_input=quote_input,
        role=role,
        registry_row=registry_row,
    )
