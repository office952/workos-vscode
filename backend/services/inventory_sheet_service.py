from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.inventory_materials import Inventory_materials
from schemas.inventory import InventorySheetPayloadContract
from services.inventory_sheet_format import compute_sheet_fit_status


_ALLOWED_SHEET_TYPES = {"none", "sheet", "roll", "linear", "piece", "unknown"}
_ALLOWED_SHEET_UNITS = {"mm", "cm", "m", "unknown"}
_ALLOWED_FORMAT_SOURCES = {"manual", "supplier", "imported", "unknown"}
_ALLOWED_MATERIAL_STATUS = {"active", "missing_price", "needs_owner_input", "unknown"}


@dataclass
class InventorySheetContractError(Exception):
    code: str
    message: str
    field: str


def _as_non_empty_str(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise InventorySheetContractError(
            code="invalid_type",
            message=f"{field} must be a string",
            field=field,
        )
    out = value.strip()
    if not out:
        raise InventorySheetContractError(
            code="missing_required_field",
            message=f"{field} is required",
            field=field,
        )
    return out


def _normalized_material_status(value: Any) -> str:
    raw = _as_non_empty_str(value, "material.status").lower()
    if raw not in _ALLOWED_MATERIAL_STATUS:
        raise InventorySheetContractError(
            code="invalid_enum",
            message="material.status has unsupported value",
            field="material.status",
        )
    return raw


def _normalized_inventory_unit(value: Any) -> str:
    raw = _as_non_empty_str(value, "material.unit").lower()
    mapping = {
        "mp": "sqm",
        "m2": "sqm",
        "sqm": "sqm",
        "buc": "pcs",
        "pcs": "pcs",
        "ml": "ml",
        "sheet": "sheet",
    }
    unit = mapping.get(raw)
    if unit is None:
        raise InventorySheetContractError(
            code="invalid_enum",
            message="material.unit has unsupported value",
            field="material.unit",
        )
    return unit


def _normalized_sheet_type(value: Any) -> str:
    raw = _as_non_empty_str(value, "material.sheet_format_type").lower()
    if raw not in _ALLOWED_SHEET_TYPES:
        raise InventorySheetContractError(
            code="invalid_enum",
            message="material.sheet_format_type has unsupported value",
            field="material.sheet_format_type",
        )
    return raw


def _normalized_sheet_unit(value: Any, field: str) -> str:
    raw = _as_non_empty_str(value, field).lower()
    if raw not in _ALLOWED_SHEET_UNITS:
        raise InventorySheetContractError(
            code="invalid_enum",
            message=f"{field} has unsupported value",
            field=field,
        )
    return raw


def _normalized_format_source(value: Any) -> str:
    raw = _as_non_empty_str(value, "material.format_source").lower()
    if raw not in _ALLOWED_FORMAT_SOURCES:
        raise InventorySheetContractError(
            code="invalid_enum",
            message="material.format_source has unsupported value",
            field="material.format_source",
        )
    return raw


def _as_positive_optional_number(value: Any, field: str) -> float | None:
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        raise InventorySheetContractError(
            code="invalid_type",
            message=f"{field} must be numeric when provided",
            field=field,
        ) from exc
    if num <= 0:
        raise InventorySheetContractError(
            code="invalid_value",
            message=f"{field} must be > 0 when provided",
            field=field,
        )
    return num


def _validate_dimensions(width: Any, height: Any, unit: Any) -> tuple[float, float, str] | None:
    if width is None and height is None and unit is None:
        return None

    if width is None or height is None:
        raise InventorySheetContractError(
            code="partial_dimensions",
            message="dimensions.width and dimensions.height must both be provided",
            field="dimensions",
        )

    width_num = _as_positive_optional_number(width, "dimensions.width")
    height_num = _as_positive_optional_number(height, "dimensions.height")
    assert width_num is not None and height_num is not None

    if not isinstance(unit, str):
        raise InventorySheetContractError(
            code="invalid_type",
            message="dimensions.unit must be a string",
            field="dimensions.unit",
        )

    normalized_unit = unit.strip().lower()
    if normalized_unit not in {"mm", "cm", "m"}:
        raise InventorySheetContractError(
            code="invalid_enum",
            message="dimensions.unit has unsupported value",
            field="dimensions.unit",
        )

    return width_num, height_num, normalized_unit


def build_inventory_sheet_payload(
    *,
    materials: list[Inventory_materials],
    dimensions: dict[str, Any] | None,
    constraints: dict[str, Any] | None,
) -> dict[str, Any]:
    piece_dimensions = _validate_dimensions(
        (dimensions or {}).get("width"),
        (dimensions or {}).get("height"),
        (dimensions or {}).get("unit"),
    )

    rotation_value = (constraints or {}).get("rotation_allowed", True)
    if not isinstance(rotation_value, bool):
        raise InventorySheetContractError(
            code="invalid_type",
            message="constraints.rotation_allowed must be boolean",
            field="constraints.rotation_allowed",
        )

    if not materials:
        payload = InventorySheetPayloadContract(
            source="backend",
            assist_available=False,
            items=[],
            warnings=[],
            blockers=["No backend sheet format is configured for matching materials."],
        )
        return payload.model_dump()

    items: list[dict[str, Any]] = []
    has_configured_sheet = False

    for mat in materials:
        material_id = _as_non_empty_str(mat.code, "material.code")
        material_name = _as_non_empty_str(mat.name, "material.name")
        category = _as_non_empty_str(mat.category, "material.category")
        status = _normalized_material_status(mat.status)
        unit = _normalized_inventory_unit(mat.unit)
        sheet_type = _normalized_sheet_type(mat.sheet_format_type)
        sheet_unit = _normalized_sheet_unit(mat.sheet_unit, "material.sheet_unit")
        thickness_unit = _normalized_sheet_unit(mat.sheet_thickness_unit or "unknown", "material.sheet_thickness_unit")
        format_source = _normalized_format_source(mat.format_source)

        width = _as_positive_optional_number(mat.sheet_width, "material.sheet_width")
        height = _as_positive_optional_number(mat.sheet_height, "material.sheet_height")
        usable_width = _as_positive_optional_number(mat.usable_width, "material.usable_width")
        usable_height = _as_positive_optional_number(mat.usable_height, "material.usable_height")
        thickness = _as_positive_optional_number(mat.sheet_thickness, "material.sheet_thickness")

        if sheet_type == "sheet":
            if width is None or height is None:
                raise InventorySheetContractError(
                    code="missing_required_field",
                    message="sheet materials require sheet_width and sheet_height",
                    field="material.sheet_dimensions",
                )
            if sheet_unit == "unknown":
                raise InventorySheetContractError(
                    code="missing_required_field",
                    message="sheet materials require explicit sheet_unit",
                    field="material.sheet_unit",
                )
            has_configured_sheet = True

        if usable_width is not None and width is not None and usable_width > width:
            raise InventorySheetContractError(
                code="invalid_value",
                message="material.usable_width must be <= material.sheet_width",
                field="material.usable_width",
            )
        if usable_height is not None and height is not None and usable_height > height:
            raise InventorySheetContractError(
                code="invalid_value",
                message="material.usable_height must be <= material.sheet_height",
                field="material.usable_height",
            )

        if piece_dimensions is None or sheet_type != "sheet":
            fit_status = "unknown"
            fit_reason = "Cannot compute fit check: dimensions or sheet format are unavailable."
            warnings = []
        else:
            piece_w, piece_h, piece_unit = piece_dimensions
            fit_result = compute_sheet_fit_status(
                piece_width=piece_w,
                piece_height=piece_h,
                piece_unit=piece_unit,
                sheet_width=width,
                sheet_height=height,
                sheet_unit=sheet_unit,
                usable_width=usable_width,
                usable_height=usable_height,
                rotation_allowed=rotation_value,
            )
            fit_status = fit_result.fit_status
            fit_reason = fit_result.fit_reason
            warnings = list(fit_result.warnings)

        item = {
            "material_id": material_id,
            "material_name": material_name,
            "category": category,
            "status": status,
            "unit": unit,
            "sheet_format": {
                "type": sheet_type,
                "width": width,
                "height": height,
                "unit": sheet_unit,
                "usable_width": usable_width,
                "usable_height": usable_height,
                "thickness": thickness,
                "thickness_unit": thickness_unit,
                "verified": bool(mat.format_verified),
                "source": format_source,
            },
            "fit_status": fit_status,
            "fit_reason": fit_reason,
            "warnings": warnings,
            "requires_review": True,
        }
        items.append(item)

    if not has_configured_sheet:
        payload = InventorySheetPayloadContract(
            source="backend",
            assist_available=False,
            items=[],
            warnings=[],
            blockers=["No backend sheet format is configured for matching materials."],
        )
        return payload.model_dump()

    payload = InventorySheetPayloadContract(
        source="backend",
        assist_available=True,
        items=items,
        warnings=[],
        blockers=[],
    )
    return payload.model_dump()
