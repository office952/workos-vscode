"""Guard financial snapshot fields on locked / V2 orders (Slice 10.1)."""

from __future__ import annotations

from typing import Any, Mapping

from fastapi import HTTPException

ORDER_FINANCIAL_FIELDS_IMMUTABLE = "ORDER_FINANCIAL_FIELDS_IMMUTABLE"

FINANCIAL_IMMUTABLE_FIELDS = frozenset(
    {"total_amount", "snapshot_line_items", "snapshot_version"}
)

FROZEN_ORDER_STATUSES = frozenset({"locked", "in_execution", "completed"})


def order_financial_fields_frozen(order) -> bool:
    """True when commercial snapshot on the order must not be mutated via PUT."""
    locked_at = getattr(order, "locked_at", None)
    if locked_at is not None and str(locked_at).strip():
        return True

    snapshot_v2_json = getattr(order, "snapshot_v2_json", None)
    if snapshot_v2_json is not None:
        if isinstance(snapshot_v2_json, str):
            if snapshot_v2_json.strip():
                return True
        elif snapshot_v2_json:
            return True

    status = getattr(order, "status", None)
    if status in FROZEN_ORDER_STATUSES:
        return True

    return False


def blocked_financial_fields(update_data: Mapping[str, Any]) -> list[str]:
    return sorted(field for field in FINANCIAL_IMMUTABLE_FIELDS if field in update_data)


def assert_order_financial_fields_mutable(order, update_data: Mapping[str, Any]) -> None:
    """Raise HTTP 422 when a frozen order receives financial field updates."""
    if not order_financial_fields_frozen(order):
        return

    blocked = blocked_financial_fields(update_data)
    if not blocked:
        return

    raise HTTPException(
        status_code=422,
        detail={
            "error": ORDER_FINANCIAL_FIELDS_IMMUTABLE,
            "message": "Financial snapshot fields cannot be modified on locked or V2 orders.",
            "blocked_fields": blocked,
            "order_id": getattr(order, "id", None),
            "order_status": getattr(order, "status", None),
        },
    )
