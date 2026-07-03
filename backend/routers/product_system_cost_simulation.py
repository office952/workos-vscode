"""
BUILD 7 — Product System Cost Simulation Router.

Endpoint:
  POST /api/v1/product-system/simulate-cost

Purpose:
  Read-only cost simulation. Reuses existing CostEngine + QuoteOrchestrator
  logic without creating or modifying any business entity.

Guarantees:
  - No Quote created.
  - No Order created.
  - No ProductTemplate mutated.
  - No Dossier mutated.
  - No Inventory mutated.
  - No ExecutionTask created.
  - Response always includes persisted=false.
  - Response always includes trace proving no mutation.

Auth: get_current_user dependency (same as all ProductSystem endpoints).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from services.product_system_cost_simulation_service import (
    ProductSystemCostSimulationService,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-cost-simulation"],
    dependencies=[Depends(get_current_user)],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class SimulationContextSchema(BaseModel):
    source: str = "manual_preview"
    reason: str = "cost preview"


class CostSimulationRequest(BaseModel):
    template_id: int
    quantity: int = Field(default=1, ge=1)
    quote_input: Dict[str, Any] = Field(default_factory=dict)
    pricing: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)
    intake_id: Optional[int] = Field(
        default=None,
        description="Optional intake id for vector/file readiness context",
    )
    simulation_context: SimulationContextSchema = Field(
        default_factory=SimulationContextSchema
    )


class CostSimulationTraceSchema(BaseModel):
    source: str = "product-system-cost-simulation"
    no_persist: bool = True
    used_template_snapshot: bool = True
    used_costengine_formulas: bool = True
    changed_entities: list = Field(default_factory=list)


class CostSimulationResponse(BaseModel):
    simulation_id: Optional[Any] = None
    persisted: bool = False
    template_id: int
    template_code: str = ""
    cost_engine_version: str = "v1"
    readiness: Dict[str, Any] = Field(default_factory=dict)
    cost_result: Dict[str, Any] = Field(default_factory=dict)
    component_breakdown: list = Field(default_factory=list)
    linked_module_results: list = Field(default_factory=list)
    warnings: list = Field(default_factory=list)
    blockers: list = Field(default_factory=list)
    status: str = "simulated"
    blocked_reasons: list = Field(default_factory=list)
    trace: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/simulate-cost",
    response_model=CostSimulationResponse,
    summary="Simulate cost for a product template (read-only, no persist)",
    description=(
        "Runs the same cost calculation logic used by the pricing flow, "
        "but without creating or modifying any business entity. "
        "Returns a structured cost breakdown with readiness information."
    ),
)
async def simulate_cost(
    body: CostSimulationRequest,
    db: AsyncSession = Depends(get_db),
) -> CostSimulationResponse:
    """Cost simulation endpoint — read-only, no persist."""
    service = ProductSystemCostSimulationService(db)

    result = await service.simulate(
        template_id=body.template_id,
        quantity=body.quantity,
        quote_input=body.quote_input,
        pricing=body.pricing,
        options=body.options,
        simulation_context=body.simulation_context.model_dump(),
        intake_id=body.intake_id,
    )

    # Map error status to HTTP codes
    if result.status == "error" and "template_not_found" in result.blockers:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "template_not_found",
                "template_id": body.template_id,
                "persisted": False,
                "trace": result.trace,
            },
        )

    return CostSimulationResponse(**result.to_dict())