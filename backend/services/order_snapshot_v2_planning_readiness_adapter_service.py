"""OrderSnapshotV2 → planning/readiness input adapter (W5-T03).

V2 orders derive preparation readiness from frozen OrderSnapshotV2 only.
Legacy orders use an explicit isolated snapshot_line_items path.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.execution_plan_v2_frozen_task_identity import FROZEN_TASK_IDENTITY_VERSION
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.order_snapshot_v2_planning_readiness import (
    PLANNING_READINESS_CONTRACT_VERSION,
    PREPARATION_READINESS_KEYS,
    OrderSnapshotV2PlanningReadinessInput,
    ReadinessAuthoritySource,
)
from services.execution_plan_v2_guard_service import order_has_v2_snapshot_fields
from services.task_preparation_readiness_service import extract_quote_input_from_snapshot


def _parse_json_object(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _order_row_is_v2(row: dict[str, Any]) -> bool:
    class _Row:
        quote_snapshot_v2_id = row.get("quote_snapshot_v2_id")
        snapshot_v2_json = row.get("snapshot_v2_json")

    return order_has_v2_snapshot_fields(_Row())


def _raise_fail_closed(*, error: str, message: str, order_id: int) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error": error,
            "message": message,
            "order_id": order_id,
            "readiness_authority": "BLOCKED_MISSING_ORDER_SNAPSHOT_V2",
            "planning_readiness_contract": PLANNING_READINESS_CONTRACT_VERSION,
        },
    )


def _parse_frozen_snapshot(
    *,
    order_id: int,
    snapshot_v2_json: Any,
) -> OrderSnapshotV2:
    raw = snapshot_v2_json
    if raw is None:
        _raise_fail_closed(
            error="ORDER_SNAPSHOT_V2_MISSING",
            message="V2 order requires frozen snapshot_v2_json.",
            order_id=order_id,
        )
    if isinstance(raw, str):
        text_raw = raw.strip()
        if not text_raw:
            _raise_fail_closed(
                error="ORDER_SNAPSHOT_V2_MISSING",
                message="V2 order snapshot_v2_json is empty.",
                order_id=order_id,
            )
        try:
            payload = json.loads(text_raw)
        except json.JSONDecodeError as exc:
            _raise_fail_closed(
                error="ORDER_SNAPSHOT_V2_CORRUPT",
                message=f"snapshot_v2_json is not valid JSON: {exc}",
                order_id=order_id,
            )
    elif isinstance(raw, dict):
        payload = raw
    else:
        _raise_fail_closed(
            error="ORDER_SNAPSHOT_V2_CORRUPT",
            message=f"snapshot_v2_json has unexpected type '{type(raw).__name__}'.",
            order_id=order_id,
        )

    if not isinstance(payload, dict):
        _raise_fail_closed(
            error="ORDER_SNAPSHOT_V2_CORRUPT",
            message="snapshot_v2_json must deserialize to an object.",
            order_id=order_id,
        )
    try:
        return OrderSnapshotV2.model_validate(payload)
    except ValidationError as exc:
        _raise_fail_closed(
            error="ORDER_SNAPSHOT_V2_CORRUPT",
            message=f"snapshot_v2_json failed schema validation: {exc}",
            order_id=order_id,
        )


def _extract_preparation_from_frozen_snapshot(snapshot: OrderSnapshotV2) -> dict[str, Any]:
    """Map frozen product-definition canonical values to preparation gate input."""
    preparation: dict[str, Any] = {}
    pd = snapshot.product_definition_snapshot
    if pd is not None:
        canonical = dict(pd.canonical_values or {})
        for key in PREPARATION_READINESS_KEYS:
            if key in canonical and canonical[key] not in (None, ""):
                preparation[key] = canonical[key]
        geometry = dict(pd.geometry_inputs or {})
        if "vector_file" in geometry and geometry["vector_file"] not in (None, ""):
            preparation["vector_file"] = geometry["vector_file"]
    return preparation


def _build_v2_readiness_input(
    *,
    order_id: int,
    snapshot: OrderSnapshotV2,
    quote_snapshot_v2_id: int | None,
) -> OrderSnapshotV2PlanningReadinessInput:
    return OrderSnapshotV2PlanningReadinessInput(
        authority_source="FROZEN_ORDER_SNAPSHOT_V2",
        order_id=order_id,
        snapshot_code=snapshot.snapshot_code,
        content_hash=snapshot.content_hash,
        quote_snapshot_v2_id=quote_snapshot_v2_id or snapshot.quote_snapshot_v2_id,
        frozen_task_identity_version=FROZEN_TASK_IDENTITY_VERSION,
        preparation_input=_extract_preparation_from_frozen_snapshot(snapshot),
    )


def _build_legacy_readiness_input(
    *,
    order_id: int,
    snapshot_line_items: Any,
) -> OrderSnapshotV2PlanningReadinessInput:
    legacy_snapshot = _parse_json_object(snapshot_line_items)
    preparation = extract_quote_input_from_snapshot(legacy_snapshot)
    return OrderSnapshotV2PlanningReadinessInput(
        authority_source="LEGACY_ORDER_INPUT",
        order_id=order_id,
        preparation_input=preparation,
    )


async def load_order_planning_readiness_input(
    db: AsyncSession,
    order_id: int,
) -> dict[str, Any]:
    """Load planning/readiness preparation input with explicit authority routing."""
    row = (
        await db.execute(
            text(
                "SELECT snapshot_v2_json, quote_snapshot_v2_id, snapshot_line_items "
                "FROM orders WHERE id = :oid LIMIT 1"
            ),
            {"oid": order_id},
        )
    ).mappings().first()
    if not row:
        return {}

    row_dict = dict(row)
    if _order_row_is_v2(row_dict):
        snapshot = _parse_frozen_snapshot(
            order_id=order_id,
            snapshot_v2_json=row_dict.get("snapshot_v2_json"),
        )
        readiness = _build_v2_readiness_input(
            order_id=order_id,
            snapshot=snapshot,
            quote_snapshot_v2_id=row_dict.get("quote_snapshot_v2_id"),
        )
        return readiness.as_quote_input_compat()

    readiness = _build_legacy_readiness_input(
        order_id=order_id,
        snapshot_line_items=row_dict.get("snapshot_line_items"),
    )
    return readiness.as_quote_input_compat()


async def load_order_planning_readiness_contract(
    db: AsyncSession,
    order_id: int,
) -> OrderSnapshotV2PlanningReadinessInput | None:
    """Structured adapter output for diagnostics and tests."""
    row = (
        await db.execute(
            text(
                "SELECT snapshot_v2_json, quote_snapshot_v2_id, snapshot_line_items "
                "FROM orders WHERE id = :oid LIMIT 1"
            ),
            {"oid": order_id},
        )
    ).mappings().first()
    if not row:
        return None

    row_dict = dict(row)
    if _order_row_is_v2(row_dict):
        snapshot = _parse_frozen_snapshot(
            order_id=order_id,
            snapshot_v2_json=row_dict.get("snapshot_v2_json"),
        )
        return _build_v2_readiness_input(
            order_id=order_id,
            snapshot=snapshot,
            quote_snapshot_v2_id=row_dict.get("quote_snapshot_v2_id"),
        )

    return _build_legacy_readiness_input(
        order_id=order_id,
        snapshot_line_items=row_dict.get("snapshot_line_items"),
    )


def readiness_authority_from_quote_input(quote_input: dict[str, Any] | None) -> ReadinessAuthoritySource:
    authority = str((quote_input or {}).get("_planning_readiness_authority") or "").strip()
    if authority in {
        "FROZEN_ORDER_SNAPSHOT_V2",
        "LEGACY_ORDER_INPUT",
        "BLOCKED_MISSING_ORDER_SNAPSHOT_V2",
    }:
        return authority  # type: ignore[return-value]
    return "LEGACY_ORDER_INPUT"
