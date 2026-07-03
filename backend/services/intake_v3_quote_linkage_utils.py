"""Shared Intake V3 quote linkage helpers — no service-layer imports."""

from __future__ import annotations

from typing import Any

PRICING_REVIEW_JSON_KEY = "pricing_review"
ACCEPT_DECISION_JSON_KEY = "accept_decision"
CONVERT_DECISION_JSON_KEY = "convert_decision"
IV3_ACCEPTED_STATUS = "accepted"
IV3_ORDER_LINKAGE_JSON_KEY = "intake_v3_order_linkage_v1"
IV3_ORDER_STATUS_LOCKED = "locked"


def get_pricing_review_record(linkage: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(linkage, dict):
        return None
    record = linkage.get(PRICING_REVIEW_JSON_KEY)
    return record if isinstance(record, dict) else None


def is_pricing_review_completed(linkage: dict[str, Any] | None) -> bool:
    record = get_pricing_review_record(linkage)
    if record and record.get("status") == "completed":
        return True
    if isinstance(linkage, dict) and linkage.get("requires_pricing_review") is False:
        priced_draft = linkage.get("priced_draft")
        if priced_draft is True or record is not None:
            return True
    return False


def get_accept_decision_record(linkage: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(linkage, dict):
        return None
    record = linkage.get(ACCEPT_DECISION_JSON_KEY)
    return record if isinstance(record, dict) else None


def is_iv3_accept_completed(linkage: dict[str, Any] | None, quote_status: str | None = None) -> bool:
    record = get_accept_decision_record(linkage)
    if record and record.get("status") == "approved":
        return True
    if quote_status == IV3_ACCEPTED_STATUS and isinstance(linkage, dict):
        return bool(linkage.get("priced_draft") or is_pricing_review_completed(linkage))
    return False


def get_convert_decision_record(linkage: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(linkage, dict):
        return None
    record = linkage.get(CONVERT_DECISION_JSON_KEY)
    return record if isinstance(record, dict) else None


def is_iv3_convert_completed(linkage: dict[str, Any] | None) -> bool:
    record = get_convert_decision_record(linkage)
    return bool(record and record.get("status") == "approved" and record.get("order_created"))
