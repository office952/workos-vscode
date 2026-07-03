from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from io import StringIO
from typing import Any

from schemas.inventory import (
    InventorySheetQualityAuditResponse,
    InventorySheetRemediationAuditTrailResponse,
)

CSV_INJECTION_PREFIXES = ("=", "+", "-", "@")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def safe_csv_cell(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        text = _json_compact(value)
    elif isinstance(value, datetime):
        text = value.isoformat()
    else:
        text = str(value)

    if text.startswith(CSV_INJECTION_PREFIXES):
        return f"'{text}"
    return text


def _to_csv(headers: list[str], rows: list[list[Any]]) -> str:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([safe_csv_cell(value) for value in row])
    return buffer.getvalue()


def export_sheet_quality_audit_csv(report: InventorySheetQualityAuditResponse) -> str:
    headers = [
        "material_id",
        "material_code",
        "material_name",
        "category",
        "status",
        "issue_code",
        "message",
        "recommended_action",
        "would_block_intake_assist",
        "exported_at",
    ]

    exported_at = _now_iso()
    rows = [
        [
            item.material_id,
            item.material_code,
            item.material_name,
            item.category,
            item.status,
            item.issue_code,
            item.message,
            item.recommended_action,
            item.would_block_intake_assist,
            exported_at,
        ]
        for item in report.items
    ]
    return _to_csv(headers, rows)


def export_sheet_quality_audit_json(report: InventorySheetQualityAuditResponse) -> dict[str, Any]:
    exported_at = _now_iso()
    return {
        "source": "backend",
        "export_type": "inventory_sheet_quality_audit",
        "format": "json",
        "exported_at": exported_at,
        "filters": report.filters.model_dump(mode="json"),
        "data": report.model_dump(mode="json"),
    }


def export_sheet_remediation_audit_trail_csv(
    report: InventorySheetRemediationAuditTrailResponse,
) -> str:
    headers = [
        "audit_event_id",
        "material_id",
        "issue_code",
        "changed_by",
        "changed_at",
        "operation_status",
        "source",
        "reason",
        "old_values_json",
        "new_values_json",
        "validation_result_before_json",
        "validation_result_after_json",
        "exported_at",
    ]

    exported_at = _now_iso()
    rows = [
        [
            event.audit_event_id,
            event.material_id,
            event.issue_code,
            event.changed_by,
            event.changed_at,
            event.operation_status,
            event.source,
            event.reason,
            event.old_values,
            event.new_values,
            event.validation_result_before,
            event.validation_result_after,
            exported_at,
        ]
        for event in report.events
    ]
    return _to_csv(headers, rows)


def export_sheet_remediation_audit_trail_json(
    report: InventorySheetRemediationAuditTrailResponse,
) -> dict[str, Any]:
    exported_at = _now_iso()
    return {
        "source": "backend",
        "export_type": "inventory_sheet_remediation_audit_trail",
        "format": "json",
        "exported_at": exported_at,
        "filters": report.filters.model_dump(mode="json"),
        "data": report.model_dump(mode="json"),
    }
