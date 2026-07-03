"""
BUILD 8 — Product System Output Blocks Render Preview Router.

Endpoints:
  POST /api/v1/product-system/output-blocks/render-preview
  GET  /api/v1/entities/quotes/{quote_id}/output-blocks-preview

Purpose:
  Read-only rendering of Output Blocks as preview.
  No persistence, no mutation, no side effects.

Guarantees:
  - No Quote created or modified.
  - No Order created or modified.
  - No ProductTemplate mutated.
  - No BlueprintDossier mutated.
  - No Inventory mutated.
  - No ExecutionTask created.
  - No snapshot created.
  - Response always includes persisted=false.
  - Response always includes trace.changed_entities=[].
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from models.quotes import Quotes
from models.product_templates import Product_templates
from models.product_blueprint_dossier import ProductBlueprintDossier
from services.output_blocks_renderer_service import OutputBlocksRendererService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["product-system-output-blocks"],
    dependencies=[Depends(get_current_user)],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class QuoteContextSchema(BaseModel):
    quote_id: Optional[int] = None
    client_name: str = "Client preview"
    quantity: int = 1
    dimensions: Dict[str, Any] = Field(default_factory=dict)
    selected_options: Dict[str, Any] = Field(default_factory=dict)


class RenderPreviewRequest(BaseModel):
    template_id: Optional[int] = None
    dossier_id: Optional[int] = None
    document_type: str = "offer"
    audience: str = "client"
    block_types: Optional[List[str]] = None
    quote_context: Optional[QuoteContextSchema] = None
    render_mode: str = "preview"


class RenderedBlockSchema(BaseModel):
    block_id: str = ""
    block_type: str = ""
    title: str = ""
    approval_status: str = "draft"
    rendered_text: str = ""
    variables_used: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)


class RenderPreviewTraceSchema(BaseModel):
    source: str = "output-blocks-render-preview"
    no_persist: bool = True
    changed_entities: List[str] = Field(default_factory=list)
    live_changes_affect_accepted_orders: bool = False


class RenderPreviewResponse(BaseModel):
    persisted: bool = False
    template_id: Optional[int] = None
    dossier_id: Optional[int] = None
    document_type: str = ""
    audience: str = ""
    render_mode: str = "preview"
    blocks: List[RenderedBlockSchema] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    trace: RenderPreviewTraceSchema = Field(default_factory=RenderPreviewTraceSchema)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/product-system/output-blocks/render-preview",
    response_model=RenderPreviewResponse,
    summary="Render Output Blocks preview (read-only, no persist)",
    description=(
        "Renders Output Blocks from a product template's blueprint dossier "
        "as a preview. Does not create, modify, or persist any entity."
    ),
)
async def render_preview(
    body: RenderPreviewRequest,
    db: AsyncSession = Depends(get_db),
) -> RenderPreviewResponse:
    """Output Blocks render preview — read-only, no persist."""
    if not body.template_id and not body.dossier_id:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "template_id_or_dossier_id_required",
                "persisted": False,
                "trace": {"source": "output-blocks-render-preview", "changed_entities": []},
            },
        )

    service = OutputBlocksRendererService(db)
    quote_ctx = body.quote_context.model_dump() if body.quote_context else {}

    result = await service.render_preview(
        template_id=body.template_id,
        dossier_id=body.dossier_id,
        document_type=body.document_type,
        audience=body.audience,
        block_types=body.block_types,
        quote_context=quote_ctx,
        render_mode=body.render_mode,
    )

    # Map specific blockers to HTTP codes
    if "template_not_found" in result.blockers:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "template_not_found",
                "template_id": body.template_id,
                "persisted": False,
                "trace": result.trace,
            },
        )

    return RenderPreviewResponse(**result.to_dict())


@router.get(
    "/api/v1/entities/quotes/{quote_id}/output-blocks-preview",
    response_model=RenderPreviewResponse,
    summary="Quote Output Blocks preview (read-only bridge)",
    description=(
        "Read-only bridge: renders Output Blocks for a quote's linked template. "
        "Does not modify the quote, create snapshots, or replace commercial documents."
    ),
)
async def quote_output_blocks_preview(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> RenderPreviewResponse:
    """Quote bridge — read-only Output Blocks preview."""
    # Load quote read-only
    query = select(Quotes).where(Quotes.id == quote_id)
    result = await db.execute(query)
    quote_obj = result.scalar_one_or_none()

    if not quote_obj:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "quote_not_found",
                "quote_id": quote_id,
                "persisted": False,
                "trace": {"source": "output-blocks-render-preview", "changed_entities": []},
            },
        )

    # Extract template_id from quote
    template_id = None

    # Try product_snapshot_json for template link
    product_snapshot = None
    if hasattr(quote_obj, "product_snapshot_json") and quote_obj.product_snapshot_json:
        try:
            raw = quote_obj.product_snapshot_json
            product_snapshot = json.loads(raw) if isinstance(raw, str) else raw
            template_id = product_snapshot.get("template_id") or product_snapshot.get("id")
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    # Try items_json for template link
    if not template_id and hasattr(quote_obj, "items_json") and quote_obj.items_json:
        try:
            raw = quote_obj.items_json
            items = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(items, list) and items:
                template_id = items[0].get("template_id")
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    if not template_id:
        # No template link found — report explicitly
        return RenderPreviewResponse(
            persisted=False,
            template_id=None,
            dossier_id=None,
            document_type="offer",
            audience="client",
            render_mode="preview",
            blocks=[],
            warnings=["template_link_missing: quote has no linked product template"],
            blockers=[],
            trace=RenderPreviewTraceSchema(),
        )

    # Build quote context from quote data
    quote_context: Dict[str, Any] = {
        "quote_id": quote_id,
        "client_name": getattr(quote_obj, "client_name", None) or "Client",
        "quantity": 1,
        "dimensions": {},
        "selected_options": {},
    }

    # Try to extract quantity/dimensions from product_snapshot
    if product_snapshot:
        quote_context["quantity"] = product_snapshot.get("quantity", 1)
        dims = product_snapshot.get("dimensions") or product_snapshot.get("quote_input", {}).get("dimensions", {})
        if dims:
            quote_context["dimensions"] = dims

    service = OutputBlocksRendererService(db)
    render_result = await service.render_preview(
        template_id=int(template_id),
        document_type="offer",
        audience="client",
        quote_context=quote_context,
        render_mode="preview",
    )

    return RenderPreviewResponse(**render_result.to_dict())