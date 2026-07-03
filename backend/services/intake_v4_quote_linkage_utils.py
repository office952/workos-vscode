"""Intake V4 quote linkage helpers — shared keys, no IV3 service imports."""

from __future__ import annotations

from typing import Any

from services.intake_v3_quote_linkage_utils import (
    ACCEPT_DECISION_JSON_KEY,
    CONVERT_DECISION_JSON_KEY,
    IV3_ACCEPTED_STATUS,
    PRICING_REVIEW_JSON_KEY,
    get_accept_decision_record,
    get_convert_decision_record,
    get_pricing_review_record,
    is_pricing_review_completed,
)
from services.intake_v4_commercial_quote_service import (
    INTAKE_V4_LINKAGE_CODE_PREFIX,
    INTAKE_V6_LINKAGE_CODE_PREFIX,
    INTAKE_V4_LINKAGE_JSON_KEY,
)

INTAKE_V4_ORDER_LINKAGE_JSON_KEY = "intake_v4_order_linkage_v1"
OWNER_APPROVAL_JSON_KEY = "owner_approval_v1"
V4_ACCEPTED_STATUS = IV3_ACCEPTED_STATUS


def is_iv4_quote(quote) -> bool:
    code = getattr(quote, "intake_code", None)
    return bool(code and str(code).startswith((INTAKE_V4_LINKAGE_CODE_PREFIX, INTAKE_V6_LINKAGE_CODE_PREFIX)))


def get_v4_owner_approval_record(linkage: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(linkage, dict):
        return None
    record = linkage.get(OWNER_APPROVAL_JSON_KEY)
    return record if isinstance(record, dict) else None


def owner_approval_analysis_hash(record: dict[str, Any] | None) -> str | None:
    if not isinstance(record, dict):
        return None
    value = record.get("analysis_hash")
    return value if isinstance(value, str) and value else None


def is_v4_owner_approval_valid(
    linkage: dict[str, Any] | None,
    workspace_analysis_hash: str | None,
) -> tuple[bool, bool, bool]:
    """Return (exists, valid, stale)."""
    record = get_v4_owner_approval_record(linkage)
    if not record or not record.get("approved"):
        return False, False, False
    expected = owner_approval_analysis_hash(record)
    if workspace_analysis_hash and expected and workspace_analysis_hash != expected:
        return True, False, True
    return True, True, False


def is_v4_accept_completed(linkage: dict[str, Any] | None, quote_status: str | None = None) -> bool:
    record = get_accept_decision_record(linkage)
    if record and record.get("status") == "approved":
        return True
    if quote_status == V4_ACCEPTED_STATUS and isinstance(linkage, dict):
        return bool(linkage.get("priced_draft") or is_pricing_review_completed(linkage))
    return False


def is_v4_convert_completed(linkage: dict[str, Any] | None) -> bool:
    record = get_convert_decision_record(linkage)
    return bool(record and record.get("status") == "approved" and record.get("order_created"))


def snapshot_analysis_hash_from_linkage(linkage: dict[str, Any] | None) -> str | None:
    if not isinstance(linkage, dict):
        return None
    snapshot = linkage.get("snapshot")
    if not isinstance(snapshot, dict):
        return None
    ws_snap = snapshot.get("workspace_payload_snapshot")
    if not isinstance(ws_snap, dict):
        return None
    svg_source = ws_snap.get("svg_source")
    if not isinstance(svg_source, dict):
        return None
    file_hash = svg_source.get("file_hash")
    return file_hash if isinstance(file_hash, str) and file_hash else None


def linkage_workspace_id(linkage: dict[str, Any] | None) -> str | None:
    if not isinstance(linkage, dict):
        return None
    snapshot = linkage.get("snapshot")
    if isinstance(snapshot, dict):
        ws_id = snapshot.get("source_workspace_id")
        if isinstance(ws_id, str) and ws_id:
            return ws_id
    ws_id = linkage.get("source_workspace_id")
    return ws_id if isinstance(ws_id, str) and ws_id else None


def template_code_from_linkage(linkage: dict[str, Any] | None) -> str | None:
    if not isinstance(linkage, dict):
        return None
    snapshot = linkage.get("snapshot")
    if isinstance(snapshot, dict):
        code = snapshot.get("template_code")
        if isinstance(code, str) and code:
            return code
    quote_input = linkage.get("quote_input_payload")
    if isinstance(quote_input, dict):
        code = quote_input.get("productCode") or quote_input.get("template_code")
        if isinstance(code, str) and code:
            return code
    return None


__all__ = [
    "ACCEPT_DECISION_JSON_KEY",
    "CONVERT_DECISION_JSON_KEY",
    "INTAKE_V4_LINKAGE_JSON_KEY",
    "INTAKE_V4_ORDER_LINKAGE_JSON_KEY",
    "OWNER_APPROVAL_JSON_KEY",
    "PRICING_REVIEW_JSON_KEY",
    "V4_ACCEPTED_STATUS",
    "get_pricing_review_record",
    "is_iv4_quote",
    "is_pricing_review_completed",
    "is_v4_accept_completed",
    "is_v4_convert_completed",
    "is_v4_owner_approval_valid",
    "linkage_workspace_id",
    "owner_approval_analysis_hash",
    "snapshot_analysis_hash_from_linkage",
    "template_code_from_linkage",
]
