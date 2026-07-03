"""Early guard: V2 orders must not use the legacy execution plan endpoint."""

from __future__ import annotations

from fastapi import HTTPException


def order_has_v2_snapshot_fields(order) -> bool:
    quote_snapshot_v2_id = getattr(order, "quote_snapshot_v2_id", None)
    if quote_snapshot_v2_id is not None:
        return True
    snapshot_v2_json = getattr(order, "snapshot_v2_json", None)
    if snapshot_v2_json is None:
        return False
    if isinstance(snapshot_v2_json, str):
        return bool(snapshot_v2_json.strip())
    return bool(snapshot_v2_json)


def raise_if_legacy_plan_blocked_for_v2_order(order) -> None:
    if not order_has_v2_snapshot_fields(order):
        return
    raise HTTPException(
        status_code=422,
        detail={
            "error": "EXECUTION_PLAN_V2_REQUIRED",
            "message": "V2 orders require the dedicated execution plan v2 preview/create path.",
        },
    )
