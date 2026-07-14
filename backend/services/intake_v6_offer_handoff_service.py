"""Single-step Intake V6 handoff into offer with backend-priced totals."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.auth import UserResponse
from schemas.intake_v6 import IntakeV6CreateDraftQuoteRequest
from services.intake_v6_commercial_quote_service import (
    create_or_reuse_guarded_draft_quote_from_intake_v6_workspace,
)
from services.intake_v6_priced_quote_write_service import (
    V6_PRICED_QUOTE_WRITTEN,
    write_intake_v6_priced_quote_totals,
)
from services.intake_v6_snapshot_authoritative_offer_service import (
    V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT,
    V6_OFFER_FROM_SNAPSHOT_WRITTEN,
    has_frozen_quote_snapshot_v2,
    write_intake_v6_offer_from_frozen_snapshot_v2,
)

_SNAPSHOT_OFFER_SUCCESS_STATUSES = frozenset(
    {V6_OFFER_FROM_SNAPSHOT_WRITTEN, V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT}
)


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
    use_snapshot_authority = await has_frozen_quote_snapshot_v2(
        db,
        quote_id=draft_quote.quote_id,
        workspace_id=workspace_id,
    )
    if use_snapshot_authority:
        write_result = await write_intake_v6_offer_from_frozen_snapshot_v2(
            db,
            workspace_id,
            quote_id=draft_quote.quote_id,
            expected_total_gross=expected_total_gross,
            operator_confirmation=operator_confirmation,
            operator_identifier=operator_identifier,
        )
    else:
        write_result = await write_intake_v6_priced_quote_totals(
            db,
            workspace_id,
            quote_id=draft_quote.quote_id,
            expected_total_gross=expected_total_gross,
            expected_pricing_hash=expected_pricing_hash,
            operator_confirmation=operator_confirmation,
            operator_identifier=operator_identifier,
        )

    write_status = write_result.get("status")
    if write_status in _SNAPSHOT_OFFER_SUCCESS_STATUSES:
        quote_status = "priced"
    elif write_status == V6_PRICED_QUOTE_WRITTEN:
        quote_status = "priced"
    else:
        quote_status = draft_quote.quote_status

    return {
        "status": write_status,
        "quote_created": draft_quote.quote_created,
        "quote_id": draft_quote.quote_id,
        "quote_code": draft_quote.quote_code,
        "quote_status": quote_status,
        "source_workspace_id": workspace_id,
        "commercial_totals": write_result.get("commercial_totals"),
        "line_items": write_result.get("line_items") or [],
        "pricing_trace": write_result.get("pricing_trace") or {},
        "blockers": write_result.get("blockers") or [],
        "warnings": write_result.get("warnings") or [],
        "can_create_quote_snapshot": bool(write_result.get("can_create_quote_snapshot")),
        "commercial_authority_source": write_result.get("commercial_authority_source"),
        "snapshot_v2": write_result.get("snapshot_v2"),
        "snapshot_authoritative_offer": use_snapshot_authority,
        "next_route": f"/quotes/{draft_quote.quote_code}",
    }
