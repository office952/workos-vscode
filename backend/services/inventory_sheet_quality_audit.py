from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from models.inventory_materials import Inventory_materials


@dataclass
class InventorySheetQualityAuditItem:
    material_id: str
    material_name: str
    category: str | None
    status: Literal["valid", "not_applicable", "invalid"]
    issue_code: str | None = None
    message: str = ""
    recommended_action: str = ""
    would_block_intake_assist: bool = False


@dataclass
class InventorySheetQualityAuditReport:
    total_records_checked: int = 0
    valid_count: int = 0
    not_applicable_count: int = 0
    invalid_count: int = 0
    items: list[InventorySheetQualityAuditItem] = field(default_factory=list)


def _check_required_non_empty_str(value: Any, field: str) -> str | None:
    """Return value if valid string, None if missing, otherwise raise."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be string when provided")
    stripped = value.strip()
    if not stripped:
        return None
    return stripped


def _check_material_status(value: Any) -> str | None:
    """Validate and normalize material status."""
    if value is None:
        return None
    raw = str(value or "").lower().strip()
    if raw not in {"active", "missing_price", "needs_owner_input", "unknown"}:
        raise ValueError("material.status has unsupported value")
    return raw


def _check_inventory_unit(value: Any) -> str | None:
    """Validate and normalize inventory unit."""
    if value is None:
        return None
    raw = str(value or "").lower().strip()
    mapping = {
        "mp": "sqm",
        "m2": "sqm",
        "sqm": "sqm",
        "buc": "pcs",
        "pcs": "pcs",
        "ml": "ml",
        "sheet": "sheet",
    }
    if raw not in mapping:
        raise ValueError("material.unit has unsupported value")
    return mapping[raw]


def _check_sheet_type(value: Any) -> str | None:
    """Validate and normalize sheet format type."""
    if value is None:
        return "unknown"
    raw = str(value or "").lower().strip()
    if raw not in {"none", "sheet", "roll", "linear", "piece", "unknown"}:
        raise ValueError("material.sheet_format_type has unsupported value")
    return raw


def _check_sheet_unit(value: Any) -> str:
    """Validate sheet unit."""
    if value is None:
        return "unknown"
    raw = str(value or "").lower().strip()
    if raw not in {"mm", "cm", "m", "unknown"}:
        raise ValueError("material.sheet_unit has unsupported value")
    return raw


def _check_format_source(value: Any) -> str:
    """Validate format source."""
    if value is None:
        return "unknown"
    raw = str(value or "").lower().strip()
    if raw not in {"manual", "supplier", "imported", "unknown"}:
        raise ValueError("material.format_source has unsupported value")
    return raw


def _as_positive_number(value: Any) -> float | None:
    """Convert to positive number or None."""
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise ValueError("value must be numeric when provided")
    if num <= 0:
        raise ValueError("value must be > 0 when provided")
    return num


def audit_inventory_material_record(material: Inventory_materials) -> InventorySheetQualityAuditItem:
    """
    Audit a single inventory material record without mutation.

    Returns audit item with status and issue classification.

    Status classification:
    - valid: material can be used in IntakeAssist sheet assist
    - not_applicable: material is non-sheet type (expected, not a problem)
    - invalid: material would fail contract validation
    """
    try:
        material_id = _check_required_non_empty_str(material.code, "material.code")
        material_name = _check_required_non_empty_str(material.name, "material.name")
        category = material.category

        if material_id is None or material_name is None:
            return InventorySheetQualityAuditItem(
                material_id=material.code or "unknown",
                material_name=material.name or "unknown",
                category=category,
                status="invalid",
                issue_code="missing_required_field",
                message="Material is missing required code or name",
                recommended_action="Populate material.code and material.name",
                would_block_intake_assist=True,
            )

        material_status = _check_material_status(material.status)
        if material_status is None:
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="invalid",
                issue_code="missing_required_field",
                message="Material status is missing or empty",
                recommended_action="Set material.status to one of: active, missing_price, needs_owner_input",
                would_block_intake_assist=True,
            )

        try:
            material_unit = _check_inventory_unit(material.unit)
        except ValueError:
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="invalid",
                issue_code="invalid_unit",
                message="Material unit is invalid or not supported",
                recommended_action="Set material.unit to one of: mp/m2/sqm, buc/pcs, ml, sheet",
                would_block_intake_assist=True,
            )
        if material_unit is None:
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="invalid",
                issue_code="invalid_unit",
                message="Material unit is invalid or not supported",
                recommended_action="Set material.unit to one of: mp/m2/sqm, buc/pcs, ml, sheet",
                would_block_intake_assist=True,
            )

        sheet_type = _check_sheet_type(material.sheet_format_type)
        if sheet_type != "sheet":
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="not_applicable",
                issue_code=None,
                message="Material is not sheet type; not applicable for sheet fit check",
                recommended_action="N/A",
                would_block_intake_assist=False,
            )

        try:
            sheet_unit = _check_sheet_unit(material.sheet_unit)
        except ValueError:
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="invalid",
                issue_code="missing_configuration",
                message="Sheet material has unsupported sheet_unit",
                recommended_action="Set material.sheet_unit to one of: mm, cm, m",
                would_block_intake_assist=True,
            )
        if sheet_unit == "unknown":
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="invalid",
                issue_code="missing_configuration",
                message="Sheet material is missing or has invalid sheet_unit",
                recommended_action="Set material.sheet_unit to one of: mm, cm, m",
                would_block_intake_assist=True,
            )

        try:
            sheet_width = (
                _as_positive_number(material.sheet_width)
                if material.sheet_width is not None
                else None
            )
            sheet_height = (
                _as_positive_number(material.sheet_height)
                if material.sheet_height is not None
                else None
            )
        except ValueError:
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="invalid",
                issue_code="invalid_dimensions",
                message="Sheet dimensions must be positive numbers",
                recommended_action="Set material.sheet_width and material.sheet_height to numbers > 0",
                would_block_intake_assist=True,
            )

        if sheet_width is None or sheet_height is None:
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="invalid",
                issue_code="missing_configuration",
                message="Sheet material is missing sheet_width or sheet_height",
                recommended_action="Set material.sheet_width and material.sheet_height to positive numbers",
                would_block_intake_assist=True,
            )

        try:
            usable_width = (
                _as_positive_number(material.usable_width)
                if material.usable_width is not None
                else None
            )
            usable_height = (
                _as_positive_number(material.usable_height)
                if material.usable_height is not None
                else None
            )
        except ValueError:
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="invalid",
                issue_code="invalid_dimensions",
                message="Usable dimensions must be positive numbers when provided",
                recommended_action="Set material.usable_width and material.usable_height to numbers > 0",
                would_block_intake_assist=True,
            )

        if usable_width is not None and usable_width > sheet_width:
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="invalid",
                issue_code="partial_payload",
                message="Sheet material has usable_width > sheet_width (constraint violation)",
                recommended_action="Set material.usable_width <= material.sheet_width or set usable_width to null",
                would_block_intake_assist=True,
            )

        if usable_height is not None and usable_height > sheet_height:
            return InventorySheetQualityAuditItem(
                material_id=material_id,
                material_name=material_name,
                category=category,
                status="invalid",
                issue_code="partial_payload",
                message="Sheet material has usable_height > sheet_height (constraint violation)",
                recommended_action="Set material.usable_height <= material.sheet_height or set usable_height to null",
                would_block_intake_assist=True,
            )

        _check_format_source(material.format_source)

        return InventorySheetQualityAuditItem(
            material_id=material_id,
            material_name=material_name,
            category=category,
            status="valid",
            issue_code=None,
            message="Material passes inventory sheet format contract validation",
            recommended_action="N/A",
            would_block_intake_assist=False,
        )

    except ValueError as exc:
        return InventorySheetQualityAuditItem(
            material_id=material.code or "unknown",
            material_name=material.name or "unknown",
            category=material.category,
            status="invalid",
            issue_code="unexpected_shape",
            message=f"Unexpected data shape: {str(exc)}",
            recommended_action="Review and correct material data",
            would_block_intake_assist=True,
        )
    except Exception as exc:
        return InventorySheetQualityAuditItem(
            material_id=material.code or "unknown",
            material_name=material.name or "unknown",
            category=material.category,
            status="invalid",
            issue_code="unexpected_shape",
            message=f"Audit error: {str(exc)}",
            recommended_action="Investigate and correct material data",
            would_block_intake_assist=True,
        )


async def audit_inventory_sheet_quality(
    db_session: Any,
) -> InventorySheetQualityAuditReport:
    """
    Audit all inventory materials for sheet format contract compliance.

    Read-only operation. No mutations performed.

    Returns report with total counts and per-record audit items.
    """
    from sqlalchemy import select

    query = select(Inventory_materials).order_by(Inventory_materials.id)
    result = await db_session.execute(query)
    materials = result.scalars().all()

    report = InventorySheetQualityAuditReport(total_records_checked=len(materials))

    for material in materials:
        audit_item = audit_inventory_material_record(material)
        report.items.append(audit_item)

        if audit_item.status == "valid":
            report.valid_count += 1
        elif audit_item.status == "not_applicable":
            report.not_applicable_count += 1
        else:
            report.invalid_count += 1

    return report
