"""Single-step Intake V6 handoff into offer with backend-priced totals."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.auth import UserResponse
from schemas.intake_v6 import IntakeV6CreateDraftQuoteRequest
from services.intake_v6_commercial_quote_service import (
    create_or_reuse_guarded_draft_quote_from_intake_v6_workspace,
)
from services.intake_v6_priced_quote_write_service import write_intake_v6_priced_quote_totals


async def handoff_intake_v6_workspace_to_offer(
    db: AsyncSession,
    workspace_id: str,
    *,
    client_analysis_hash: str,
    expected_total_gross: float,
    expected_pricing_hash: str | None,
    operator_confirmation: bool,
    current_user: UserResponse,
) -> dict[str, Any]:
    draft_request = IntakeV6CreateDraftQuoteRequest(
        confirm_create_draft_only=True,
        confirm_no_order=True,
        confirm_no_execution=True,
        confirm_no_inventory=True,
        confirm_internal_draft_quote=True,
        decision_reason="Single-step Intake V6 offer handoff.",
        client_analysis_hash=client_analysis_hash,
    )

    draft_quote = await create_or_reuse_guarded_draft_quote_from_intake_v6_workspace(
        db,
        workspace_id,
        draft_request,
        current_user,
    )

    operator_identifier = current_user.email or current_user.name or str(current_user.id)
    write_result = await write_intake_v6_priced_quote_totals(
        db,
        workspace_id,
        quote_id=draft_quote.quote_id,
        expected_total_gross=expected_total_gross,
        expected_pricing_hash=expected_pricing_hash,
        operator_confirmation=operator_confirmation,
        operator_identifier=operator_identifier,
    )

    return {
        "status": write_result.get("status"),
        "quote_created": draft_quote.quote_created,
        "quote_id": draft_quote.quote_id,
        "quote_code": draft_quote.quote_code,
        "quote_status": write_result.get("status") == "V6_PRICED_QUOTE_WRITTEN" and "priced" or draft_quote.quote_status,
        "source_workspace_id": workspace_id,
        "commercial_totals": write_result.get("commercial_totals"),
        "line_items": write_result.get("line_items") or [],
        "pricing_trace": write_result.get("pricing_trace") or {},
        "blockers": write_result.get("blockers") or [],
        "warnings": write_result.get("warnings") or [],
        "can_create_quote_snapshot": bool(write_result.get("can_create_quote_snapshot")),
        "next_route": f"/quotes/{draft_quote.quote_code}",
    }