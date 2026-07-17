"""Build 4A — Frozen Modular Graph read-only preview endpoints.

No freeze persist, no Order create, no ExecutionPlan persist, no task materialization.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from models.orders import Orders
from schemas.frozen_modular_graph import FrozenModularGraphPreview
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from services.frozen_modular_graph_service import (
    build_frozen_modular_graph_from_v2,
    classify_order14_compatibility,
)
from services.quote_snapshot_v2_service import QuoteSnapshotV2Service
from services.template_architecture_scope import require_canonical_template_code

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-frozen-modular-graph"],
    dependencies=[Depends(get_current_user)],
)


class FrozenGraphFromWorkspaceRequest(BaseModel):
    workspace_id: str | None = None
    quote_id: str | None = None
    quote_input: dict[str, Any] | None = None
    currency: str = Field(default="RON", min_length=3, max_length=3)


class FrozenGraphFromSnapshotRequest(BaseModel):
    """Pass an already-built QuoteSnapshotV2 / OrderSnapshotV2 JSON (in-memory)."""

    snapshot: dict[str, Any]
    source_kind: str | None = None


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.post(
    "/frozen-modular-graph/preview/{template_code}",
    response_model=FrozenModularGraphPreview,
)
async def post_frozen_modular_graph_preview(
    template_code: str,
    body: FrozenGraphFromWorkspaceRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> FrozenModularGraphPreview:
    """
    Build QuoteSnapshotV2 preview in-memory, then normalize to FrozenModularGraph.

    Uses existing QuoteSnapshotV2Service.build_preview (documented no-write).
    Never calls freeze, accept, order convert, plan persist, or materialize.
    """
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
                canonical_template_code=identity.canonical_template_code,
            ),
        )
    request = body or FrozenGraphFromWorkspaceRequest()
    service = QuoteSnapshotV2Service(db)
    snapshot = await service.build_preview(
        identity.canonical_template_code,
        workspace_id=request.workspace_id,
        quote_id=request.quote_id,
        quote_input=request.quote_input,
        currency=request.currency,
    )
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "frozen_modular_graph_preview_not_found",
                template_code=template_code,
                workspace_id=request.workspace_id,
            ),
        )
    return build_frozen_modular_graph_from_v2(snapshot, source_kind="quote_snapshot_v2")


@router.post(
    "/frozen-modular-graph/from-snapshot",
    response_model=FrozenModularGraphPreview,
)
async def post_frozen_modular_graph_from_snapshot(
    body: FrozenGraphFromSnapshotRequest,
) -> FrozenModularGraphPreview:
    """Normalize a caller-supplied V2 snapshot JSON. Zero DB access."""
    raw = body.snapshot
    try:
        if raw.get("quote_snapshot_v2_id") is not None or raw.get("order_id") is not None:
            snap: QuoteSnapshotV2 | OrderSnapshotV2 | dict[str, Any] = OrderSnapshotV2.model_validate(raw)
            kind = body.source_kind or "order_snapshot_v2"
        else:
            snap = QuoteSnapshotV2.model_validate(raw)
            kind = body.source_kind or "quote_snapshot_v2"
    except Exception:
        snap = raw
        kind = body.source_kind
    return build_frozen_modular_graph_from_v2(snap, source_kind=kind)


@router.get(
    "/frozen-modular-graph/from-order/{order_id}",
    response_model=FrozenModularGraphPreview,
)
async def get_frozen_modular_graph_from_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> FrozenModularGraphPreview:
    """
    Read existing orders.snapshot_v2_json only. No plan create, no materialize.

    Rejects V1-only orders unless explicitly classified (422).
    """
    order = await db.get(Orders, order_id)
    if order is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope("order_not_found", order_id=order_id),
        )
    raw = getattr(order, "snapshot_v2_json", None)
    if not raw:
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "order_snapshot_v2_required",
                order_id=order_id,
                compatibility=classify_order14_compatibility(
                    has_order=True,
                    has_execution_plan=False,
                    has_v2_json=False,
                )
                if order_id == 14
                else {"mode": "legacy_v1_line_items"},
                message="Build 4A reads OrderSnapshotV2 only; V1 line items are not reinterpreted",
            ),
        )
    try:
        snapshot = OrderSnapshotV2.model_validate_json(raw) if isinstance(raw, str) else OrderSnapshotV2.model_validate(raw)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=_error_envelope("order_snapshot_v2_invalid", order_id=order_id, detail=str(exc)),
        ) from exc
    return build_frozen_modular_graph_from_v2(snapshot, source_kind="order_snapshot_v2")


@router.get("/frozen-modular-graph/order-14-compatibility")
async def get_order14_compatibility(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Read-only health-anchor classification for Order 14. No writes."""
    from sqlalchemy import select

    from models.execution_plan import ExecutionPlan

    order = await db.get(Orders, 14)
    if order is None:
        return classify_order14_compatibility(
            has_order=False, has_execution_plan=False, has_v2_json=False
        )
    has_v2 = bool(getattr(order, "snapshot_v2_json", None))
    result = await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == 14).limit(1))
    plan = result.scalar_one_or_none()
    return classify_order14_compatibility(
        has_order=True,
        has_execution_plan=plan is not None,
        has_v2_json=has_v2,
    )
