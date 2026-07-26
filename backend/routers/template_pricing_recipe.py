"""Template Pricing Studio recipe endpoint + AI operational default overrides."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from data.ai_operational_defaults_v1 import AI_OPERATIONAL_DEFAULTS, SOURCE_PRECEDENCE
from dependencies.auth import get_current_user
from schemas.template_pricing_recipe import TemplatePricingRecipeResponse
from services.ai_operational_defaults import (
    disable_override,
    load_overrides,
    save_override,
)
from services.template_architecture_scope import require_canonical_template_code
from services.template_pricing_recipe_service import TemplatePricingRecipeService

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-template-pricing"],
    dependencies=[Depends(get_current_user)],
)


class AiDefaultOverrideBody(BaseModel):
    value: float = Field(..., description="Configurable AI default value")


class AiDefaultDisableBody(BaseModel):
    disable: bool = True


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get(
    "/templates/{template_code}/pricing",
    response_model=TemplatePricingRecipeResponse,
)
async def get_template_pricing_recipe(
    template_code: str,
    workspace_id: str | None = Query(
        default=None,
        description="Optional workspace id reserved for future payload-aware preview",
    ),
    db: AsyncSession = Depends(get_db),
) -> TemplatePricingRecipeResponse:
    """Compose template recipe + catalog resolution. Read-only; no rate invention."""
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
                canonical_template_code=identity.canonical_template_code,
                resolution_type=identity.resolution_type,
            ),
        )

    canonical = identity.canonical_template_code
    service = TemplatePricingRecipeService(db)
    recipe = await service.build_recipe(canonical, workspace_id=workspace_id)
    if recipe is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "template_pricing_recipe_not_found",
                template_code=template_code,
            ),
        )
    return recipe


@router.get("/ai-operational-defaults")
async def list_ai_operational_defaults() -> dict[str, Any]:
    """List typed AI operational defaults + current overrides (no catalog writes)."""
    overrides = load_overrides()
    items = []
    for d in AI_OPERATIONAL_DEFAULTS:
        items.append(
            {
                "decision_id": d.decision_id,
                "domain": d.domain,
                "target_code": d.target_code,
                "display_name_ro": d.display_name_ro,
                "unit": d.unit,
                "default_value": d.default_value,
                "resolved_value": float(overrides.get(d.decision_id, d.default_value)),
                "minimum": d.minimum,
                "maximum": d.maximum,
                "confidence": d.confidence,
                "rationale_ro": d.rationale_ro,
                "configurable": d.configurable,
                "has_override": d.decision_id in overrides,
                "decision_source": "AI_DECISION",
                "applies_to_templates": list(d.applies_to_templates),
            }
        )
    return {
        "schema_version": "1.0.0",
        "precedence": list(SOURCE_PRECEDENCE),
        "overrides": overrides,
        "items": items,
    }


@router.put("/ai-operational-defaults/{decision_id}")
async def put_ai_operational_default(
    decision_id: str,
    body: AiDefaultOverrideBody,
) -> dict[str, Any]:
    """Configure an AI default override (JSON file — no DB migration)."""
    try:
        overrides = save_override(decision_id, body.value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=_error_envelope(str(exc))) from exc
    return {
        "ok": True,
        "decision_id": decision_id,
        "value": overrides.get(decision_id, body.value),
        "overrides": overrides,
        "decision_source": "AI_DECISION",
    }


@router.delete("/ai-operational-defaults/{decision_id}")
async def delete_ai_operational_default(decision_id: str) -> dict[str, Any]:
    """Remove override — restore registry default."""
    overrides = disable_override(decision_id)
    return {"ok": True, "decision_id": decision_id, "overrides": overrides}
