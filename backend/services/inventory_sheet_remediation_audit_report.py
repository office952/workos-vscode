from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory_sheet_remediation_audit_events import (
    Inventory_sheet_remediation_audit_events,
)
from schemas.inventory import (
    InventorySheetRemediationAuditTrailByIssueCode,
    InventorySheetRemediationAuditTrailByStatus,
    InventorySheetRemediationAuditTrailEvent,
    InventorySheetRemediationAuditTrailFilters,
    InventorySheetRemediationAuditTrailResponse,
    InventorySheetRemediationAuditTrailSummary,
    InventorySheetRemediationOperationStatus,
)


@dataclass
class InventorySheetRemediationAuditTrailError(Exception):
    code: str
    message: str
    field: str | None = None
    status_code: int = 422


def _status_from_event_type(event_type: str) -> InventorySheetRemediationOperationStatus:
    if event_type == "inventory_sheet_remediation_applied":
        return "applied"
    return "failed"


def _build_filtered_query(
    *,
    material_id: str | None,
    issue_code: str | None,
    changed_by: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    operation_status: InventorySheetRemediationOperationStatus | None,
):
    query = select(Inventory_sheet_remediation_audit_events)

    if material_id:
        query = query.where(Inventory_sheet_remediation_audit_events.entity_id == material_id)
    if issue_code:
        query = query.where(Inventory_sheet_remediation_audit_events.issue_code == issue_code)
    if changed_by:
        query = query.where(Inventory_sheet_remediation_audit_events.changed_by == changed_by)
    if date_from is not None:
        query = query.where(Inventory_sheet_remediation_audit_events.changed_at >= date_from)
    if date_to is not None:
        query = query.where(Inventory_sheet_remediation_audit_events.changed_at <= date_to)
    if operation_status == "applied":
        query = query.where(
            Inventory_sheet_remediation_audit_events.event_type
            == "inventory_sheet_remediation_applied"
        )
    elif operation_status == "failed":
        query = query.where(
            Inventory_sheet_remediation_audit_events.event_type
            != "inventory_sheet_remediation_applied"
        )

    return query


def _as_event(row: Inventory_sheet_remediation_audit_events) -> InventorySheetRemediationAuditTrailEvent:
    return InventorySheetRemediationAuditTrailEvent(
        audit_event_id=str(row.id),
        material_id=row.entity_id,
        issue_code=row.issue_code,
        reason=row.reason,
        changed_by=row.changed_by,
        changed_at=row.changed_at.isoformat() if row.changed_at else "",
        source=row.source,
        operation_status=_status_from_event_type(row.event_type),
        old_values=row.old_values or {},
        new_values=row.new_values or {},
        validation_result_before=row.validation_result_before or {},
        validation_result_after=row.validation_result_after or {},
    )


def _build_summary(rows: list[Inventory_sheet_remediation_audit_events], returned_events: int) -> InventorySheetRemediationAuditTrailSummary:
    by_issue = InventorySheetRemediationAuditTrailByIssueCode()
    by_status = InventorySheetRemediationAuditTrailByStatus()

    for row in rows:
        if row.issue_code == "missing_required_field":
            by_issue.missing_required_field += 1
        elif row.issue_code == "missing_configuration":
            by_issue.missing_configuration += 1
        elif row.issue_code == "invalid_unit":
            by_issue.invalid_unit += 1
        elif row.issue_code == "invalid_dimensions":
            by_issue.invalid_dimensions += 1
        elif row.issue_code == "partial_payload":
            by_issue.partial_payload += 1
        elif row.issue_code == "unexpected_shape":
            by_issue.unexpected_shape += 1

        if _status_from_event_type(row.event_type) == "applied":
            by_status.applied += 1
        else:
            by_status.failed += 1

    return InventorySheetRemediationAuditTrailSummary(
        total_events=len(rows),
        returned_events=returned_events,
        by_issue_code=by_issue,
        by_status=by_status,
    )


async def get_inventory_sheet_remediation_audit_trail(
    *,
    db: AsyncSession,
    material_id: str | None,
    issue_code: str | None,
    changed_by: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    operation_status: InventorySheetRemediationOperationStatus | None,
    limit: int,
    offset: int,
) -> InventorySheetRemediationAuditTrailResponse:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise InventorySheetRemediationAuditTrailError(
            code="invalid_date_range",
            message="date_from must be <= date_to",
            field="date_from",
            status_code=422,
        )

    base_query = _build_filtered_query(
        material_id=material_id,
        issue_code=issue_code,
        changed_by=changed_by,
        date_from=date_from,
        date_to=date_to,
        operation_status=operation_status,
    )

    all_rows = (
        await db.execute(
            base_query.order_by(Inventory_sheet_remediation_audit_events.changed_at.desc())
        )
    ).scalars().all()

    page_rows = all_rows[offset : offset + limit]
    events = [_as_event(row) for row in page_rows]

    filters = InventorySheetRemediationAuditTrailFilters(
        material_id=material_id,
        issue_code=issue_code,
        changed_by=changed_by,
        date_from=date_from.isoformat() if date_from is not None else None,
        date_to=date_to.isoformat() if date_to is not None else None,
        operation_status=operation_status,
        limit=limit,
        offset=offset,
    )

    return InventorySheetRemediationAuditTrailResponse(
        source="backend",
        report_type="inventory_sheet_remediation_audit_trail",
        generated_at=datetime.now(timezone.utc).isoformat(),
        summary=_build_summary(all_rows, len(events)),
        filters=filters,
        events=events,
        warnings=[],
    )
