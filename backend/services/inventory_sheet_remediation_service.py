from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory_materials import Inventory_materials
from models.inventory_sheet_remediation_audit_events import (
    Inventory_sheet_remediation_audit_events,
)
from schemas.auth import UserResponse
from schemas.inventory import (
    InventorySheetRemediationExecutionRequest,
    InventorySheetRemediationExecutionResponse,
    InventorySheetRemediationExecutionSnapshot,
)
from services.inventory_sheet_format import validate_sheet_format_payload
from services.inventory_sheet_quality_audit import audit_inventory_material_record


ALLOWED_SHEET_REMEDIATION_FIELDS: frozenset[str] = frozenset(
    {
        "sheet_format_type",
        "sheet_width",
        "sheet_height",
        "sheet_unit",
        "sheet_thickness",
        "sheet_thickness_unit",
        "usable_width",
        "usable_height",
        "format_source",
        "format_verified",
        "format_notes",
    }
)

SUPPORTED_ISSUE_CODES_FOR_THIS_ENDPOINT: frozenset[str] = frozenset(
    {
        "missing_configuration",
        "invalid_dimensions",
        "partial_payload",
    }
)


@dataclass
class InventorySheetRemediationExecutionError(Exception):
    code: str
    message: str
    field: str | None = None
    status_code: int = 422


def _sheet_format_snapshot(material: Inventory_materials) -> dict[str, Any]:
    return {
        "sheet_format_type": material.sheet_format_type,
        "sheet_width": material.sheet_width,
        "sheet_height": material.sheet_height,
        "sheet_unit": material.sheet_unit,
        "sheet_thickness": material.sheet_thickness,
        "sheet_thickness_unit": material.sheet_thickness_unit,
        "usable_width": material.usable_width,
        "usable_height": material.usable_height,
        "format_source": material.format_source,
        "format_verified": material.format_verified,
        "format_notes": material.format_notes,
    }


def _build_sheet_payload(material: Inventory_materials) -> dict[str, Any]:
    return {
        "sheet_format_type": material.sheet_format_type,
        "sheet_width": material.sheet_width,
        "sheet_height": material.sheet_height,
        "sheet_unit": material.sheet_unit,
        "sheet_thickness": material.sheet_thickness,
        "sheet_thickness_unit": material.sheet_thickness_unit,
        "usable_width": material.usable_width,
        "usable_height": material.usable_height,
        "format_source": material.format_source,
        "format_verified": material.format_verified,
        "format_notes": material.format_notes,
    }


def _normalize_request(body: InventorySheetRemediationExecutionRequest) -> tuple[str, dict[str, Any], str]:
    if body.confirm is not True:
        raise InventorySheetRemediationExecutionError(
            code="confirm_required",
            message="confirm must be true for remediation execution",
            field="confirm",
            status_code=422,
        )

    reason = (body.reason or "").strip()
    if not reason:
        raise InventorySheetRemediationExecutionError(
            code="reason_required",
            message="reason is required",
            field="reason",
            status_code=422,
        )

    if body.issue_code not in SUPPORTED_ISSUE_CODES_FOR_THIS_ENDPOINT:
        raise InventorySheetRemediationExecutionError(
            code="unsupported_issue_code",
            message="issue_code is not supported by this endpoint",
            field="issue_code",
            status_code=422,
        )

    proposed_values = body.proposed_values.model_dump(exclude_none=True)
    if not proposed_values:
        raise InventorySheetRemediationExecutionError(
            code="proposed_values_required",
            message="proposed_values must include at least one field",
            field="proposed_values",
            status_code=422,
        )

    unknown = set(proposed_values) - ALLOWED_SHEET_REMEDIATION_FIELDS
    if unknown:
        field_name = sorted(unknown)[0]
        raise InventorySheetRemediationExecutionError(
            code="proposed_field_not_allowed",
            message=f"Field '{field_name}' is not allowed for this remediation endpoint",
            field=f"proposed_values.{field_name}",
            status_code=422,
        )

    return body.issue_code, proposed_values, reason


def _apply_proposed_values(material: Inventory_materials, proposed_values: dict[str, Any]) -> None:
    for key, value in proposed_values.items():
        setattr(material, key, value)


def _as_snapshot(material: Inventory_materials) -> InventorySheetRemediationExecutionSnapshot:
    audit_item = audit_inventory_material_record(material)
    return InventorySheetRemediationExecutionSnapshot(
        sheet_format=_sheet_format_snapshot(material),
        audit_status=audit_item.status,
        issue_code=audit_item.issue_code,
    )


def _as_snapshot_from_values(
    *,
    sheet_format: dict[str, Any],
    audit_status: str,
    issue_code: str | None,
) -> InventorySheetRemediationExecutionSnapshot:
    return InventorySheetRemediationExecutionSnapshot(
        sheet_format=sheet_format,
        audit_status=audit_status,
        issue_code=issue_code,
    )


async def _create_audit_event(
    db: AsyncSession,
    *,
    material_id: str,
    issue_code: str,
    old_values: dict[str, Any],
    new_values: dict[str, Any],
    changed_by: str,
    reason: str,
    validation_result_before: dict[str, Any],
    validation_result_after: dict[str, Any],
) -> Inventory_sheet_remediation_audit_events:
    event = Inventory_sheet_remediation_audit_events(
        event_type="inventory_sheet_remediation_applied",
        entity_type="InventoryMaterial",
        entity_id=material_id,
        issue_code=issue_code,
        old_values=old_values,
        new_values=new_values,
        changed_by=changed_by,
        changed_at=datetime.now(timezone.utc),
        reason=reason,
        validation_result_before=validation_result_before,
        validation_result_after=validation_result_after,
        source="admin_manual_remediation",
    )
    db.add(event)
    return event


async def apply_inventory_sheet_remediation(
    *,
    db: AsyncSession,
    current_user: UserResponse,
    material_id: str,
    body: InventorySheetRemediationExecutionRequest,
) -> InventorySheetRemediationExecutionResponse:
    if "," in material_id:
        raise InventorySheetRemediationExecutionError(
            code="multiple_material_ids_not_allowed",
            message="Only one material_id is allowed per request",
            field="material_id",
            status_code=422,
        )

    issue_code, proposed_values, reason = _normalize_request(body)

    material = (
        await db.execute(
            select(Inventory_materials).where(Inventory_materials.code == material_id)
        )
    ).scalar_one_or_none()
    if material is None:
        raise InventorySheetRemediationExecutionError(
            code="material_not_found",
            message=f"inventory_material '{material_id}' not found",
            field="material_id",
            status_code=404,
        )

    pre_audit_item = audit_inventory_material_record(material)
    if pre_audit_item.status != "invalid" or pre_audit_item.issue_code is None:
        raise InventorySheetRemediationExecutionError(
            code="issue_mismatch",
            message="Material is not currently in an invalid audit state",
            field="issue_code",
            status_code=422,
        )

    if pre_audit_item.issue_code != issue_code:
        raise InventorySheetRemediationExecutionError(
            code="issue_mismatch",
            message=(
                f"Requested issue_code '{issue_code}' does not match current issue "
                f"'{pre_audit_item.issue_code}'"
            ),
            field="issue_code",
            status_code=422,
        )

    before_snapshot = _sheet_format_snapshot(material)
    validation_before = {
        "audit_status": pre_audit_item.status,
        "issue_code": pre_audit_item.issue_code,
        "message": pre_audit_item.message,
    }

    before_response = _as_snapshot_from_values(
        sheet_format=before_snapshot,
        audit_status=pre_audit_item.status,
        issue_code=pre_audit_item.issue_code,
    )

    try:
        _apply_proposed_values(material, proposed_values)
        validate_sheet_format_payload(_build_sheet_payload(material))

        post_audit_item = audit_inventory_material_record(material)
        if post_audit_item.status != "valid":
            raise InventorySheetRemediationExecutionError(
                code="validation_failed",
                message="Post-change audit is not valid",
                field="proposed_values",
                status_code=422,
            )

    except InventorySheetRemediationExecutionError:
        await db.rollback()
        raise
    except ValueError as exc:
        await db.rollback()
        raise InventorySheetRemediationExecutionError(
            code="validation_failed",
            message=str(exc),
            field="proposed_values",
            status_code=422,
        )

    try:
        validation_after = {
            "audit_status": post_audit_item.status,
            "issue_code": post_audit_item.issue_code,
            "message": post_audit_item.message,
        }

        event = await _create_audit_event(
            db,
            material_id=material.code,
            issue_code=issue_code,
            old_values=before_snapshot,
            new_values=_sheet_format_snapshot(material),
            changed_by=current_user.id,
            reason=reason,
            validation_result_before=validation_before,
            validation_result_after=validation_after,
        )

        await db.commit()
        await db.refresh(material)
        await db.refresh(event)

    except Exception as exc:
        await db.rollback()
        raise InventorySheetRemediationExecutionError(
            code="audit_log_unavailable",
            message=f"Audit log unavailable: {str(exc)}",
            field="audit_log",
            status_code=503,
        )

    return InventorySheetRemediationExecutionResponse(
        source="backend",
        operation="inventory_sheet_remediation",
        status="applied",
        material_id=material.code,
        issue_code=issue_code,
        before=before_response,
        after=_as_snapshot(material),
        audit_event_id=str(event.id),
        warnings=[],
    )
