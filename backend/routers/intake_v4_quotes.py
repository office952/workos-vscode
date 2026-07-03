"""Intake V4 quote-level commercial spine endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from schemas.intake_v4 import (
    IntakeV4AcceptQuoteRequest,
    IntakeV4CommercialSpineStateResponse,
    IntakeV4CompletePricingReviewRequest,
    IntakeV4ConvertToOrderRequest,
    IntakeV4OwnerApprovalRequest,
)
from services.intake_v4_quote_to_order_service import (
    accept_v4_quote,
    complete_v4_pricing_review,
    convert_v4_quote_to_order,
    get_v4_commercial_spine_state,
    persist_v4_owner_approval,
)

router = APIRouter(
    prefix="/api/v1/intake-v4",
    tags=["intake-v4-quotes"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/quotes/{quote_id}/commercial-spine-state", response_model=IntakeV4CommercialSpineStateResponse)
async def get_quote_commercial_spine_state(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4CommercialSpineStateResponse:
    return IntakeV4CommercialSpineStateResponse.model_validate(
        await get_v4_commercial_spine_state(db, quote_id=quote_id)
    )


@router.get(
    "/workspaces/{workspace_id}/commercial-spine-state",
    response_model=IntakeV4CommercialSpineStateResponse,
)
async def get_workspace_commercial_spine_state(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> IntakeV4CommercialSpineStateResponse:
    return IntakeV4CommercialSpineStateResponse.model_validate(
        await get_v4_commercial_spine_state(db, workspace_id=workspace_id)
    )


@router.post("/quotes/{quote_id}/complete-pricing-review")
async def complete_quote_pricing_review(
    quote_id: int,
    request: IntakeV4CompletePricingReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await complete_v4_pricing_review(db, quote_id, request.model_dump(), current_user)


@router.post("/quotes/{quote_id}/owner-approval")
async def post_quote_owner_approval(
    quote_id: int,
    request: IntakeV4OwnerApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await persist_v4_owner_approval(db, quote_id, request.model_dump(), current_user)


@router.post("/quotes/{quote_id}/accept")
async def accept_quote(
    quote_id: int,
    request: IntakeV4AcceptQuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await accept_v4_quote(db, quote_id, request.model_dump(), current_user)


@router.post("/quotes/{quote_id}/convert-to-order")
async def convert_quote_to_order(
    quote_id: int,
    request: IntakeV4ConvertToOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await convert_v4_quote_to_order(db, quote_id, request.model_dump(), current_user)
