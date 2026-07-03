"""Intake V3 manual pricing review completion — priced draft, no CostEngine/order/execution/inventory."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_LINKAGE_JSON_KEY,
    intake_v3_linkage_code,
    parse_intake_v3_linkage_from_notes,
)
from tests.test_intake_v3_real_commercial_quote_creation import (
    _create_draft_quote,
    _seed_hub_workspace,
)


def _valid_completion_request(quote_id: int, intake_code: str, **overrides) -> dict:
    payload = {
        "pricing_method": "manual_review",
        "currency": "EUR",
        "subtotal": 1000.0,
        "discount_amount": 0.0,
        "vat_percent": 21.0,
        "vat_amount": 210.0,
        "total": 1210.0,
        "pricing_review_reason": "Manual pricing completed after reviewing Intake V3 snapshot.",
        "reviewer_confirmation": True,
        "confirm_quote_stays_draft": True,
        "confirm_no_order": True,
        "confirm_no_execution": True,
        "confirm_no_inventory": True,
        "expected_quote_id": quote_id,
        "expected_intake_code": intake_code,
    }
    payload.update(overrides)
    return payload


def _create_iv3_draft_quote(auth_client) -> tuple[str, int, str]:
    workspace_id = _seed_hub_workspace(auth_client)
    response = _create_draft_quote(auth_client, workspace_id)
    assert response.status_code == 201, response.text
    payload = response.json()
    return workspace_id, payload["quote_id"], intake_v3_linkage_code(workspace_id)


class TestPricingReviewStateBeforeCompletion:
    @pytest.mark.asyncio
    async def test_state_before_completion(self, auth_client):
        workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/pricing-review-state")
        assert response.status_code == 200
        payload = response.json()
        assert payload["review_status"] == "pending_review"
        assert payload["requires_pricing_review"] is True
        assert payload["pricing_review_completed"] is False
        assert payload["can_complete_pricing_review"] is True
        assert payload["intake_code"] == intake_code

        ws_response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/pricing-review-state",
        )
        assert ws_response.status_code == 200
        assert ws_response.json()["quote_id"] == quote_id


class TestPricingReviewValidation:
    @pytest.mark.asyncio
    async def test_missing_confirmation_blocks(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        quotes_before = await db_session.scalar(select(func.count()).select_from(Quotes))

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/complete-pricing-review",
            json=_valid_completion_request(
                quote_id,
                intake_code,
                reviewer_confirmation=False,
            ),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "CONFIRMATIONS_REQUIRED"
        quotes_after = await db_session.scalar(select(func.count()).select_from(Quotes))
        assert quotes_after == quotes_before

    @pytest.mark.asyncio
    async def test_invalid_totals_block(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        original_total = quote.grand_total

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/complete-pricing-review",
            json=_valid_completion_request(quote_id, intake_code, total=999.0),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "INVALID_TOTALS"

        await db_session.refresh(quote)
        assert quote.grand_total == original_total

    @pytest.mark.asyncio
    async def test_non_iv3_quote_blocked(self, auth_client, db_session):
        quote = Quotes(
            code="Q-NORMAL-PRICING",
            intake_code="WI-999",
            client_name="Normal",
            status="draft",
            version=1,
            notes=json.dumps({"human_summary": "normal"}),
        )
        db_session.add(quote)
        await db_session.commit()
        await db_session.refresh(quote)

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote.id}/complete-pricing-review",
            json=_valid_completion_request(quote.id, "WI-999"),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "NOT_IV3_QUOTE"

    @pytest.mark.asyncio
    async def test_missing_snapshot_blocks(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        assert linkage is not None
        linkage.pop("snapshot", None)
        notes_payload = json.loads(quote.notes)
        notes_payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
        quote.notes = json.dumps(notes_payload)
        await db_session.commit()

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/complete-pricing-review",
            json=_valid_completion_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "SNAPSHOT_MISSING"


class TestPricingReviewCompletion:
    @pytest.mark.asyncio
    async def test_complete_manual_pricing_review(self, auth_client, db_session):
        workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))

        response = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/complete-pricing-review",
            json=_valid_completion_request(quote_id, intake_code),
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["pricing_review_completed"] is True
        assert payload["quote_status"] == "draft"
        assert payload["requires_pricing_review"] is False
        assert payload["priced_draft"] is True
        assert payload["cost_engine_called"] is False
        assert payload["order_created"] is False
        assert payload["execution_plan_created"] is False
        assert payload["inventory_mutated"] is False
        assert payload["can_accept_quote"] is False
        assert payload["can_convert_to_order"] is False
        assert payload["total"] == 1210.0

        quote = await db_session.get(Quotes, quote_id)
        assert quote.status == "draft"
        assert quote.grand_total == 1210.0
        assert quote.subtotal == 1000.0
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        assert linkage["requires_pricing_review"] is False
        assert linkage["pricing_review"]["status"] == "completed"
        assert linkage["pricing_review"]["cost_engine_called"] is False

        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert orders_after == orders_before
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_duplicate_completion_blocked(self, auth_client):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        first = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/complete-pricing-review",
            json=_valid_completion_request(quote_id, intake_code),
        )
        assert first.status_code == 200

        second = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/complete-pricing-review",
            json=_valid_completion_request(quote_id, intake_code, total=1500.0, vat_amount=315.0),
        )
        assert second.status_code == 422
        assert second.json()["detail"]["error"] == "PRICING_REVIEW_ALREADY_COMPLETED"

    @pytest.mark.asyncio
    async def test_draft_quote_review_reflects_completion(self, auth_client):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        complete = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/complete-pricing-review",
            json=_valid_completion_request(quote_id, intake_code),
        )
        assert complete.status_code == 200

        review = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/draft-review")
        assert review.status_code == 200
        payload = review.json()
        assert payload["requires_pricing_review"] is False
        assert payload["pricing_review_completed"] is True
        assert payload["priced_draft"] is True
        assert payload["pricing_handoff"]["final_price_present"] is True
        assert payload["pricing_handoff"]["pricing_handoff_status"] == "completed"

    @pytest.mark.asyncio
    async def test_accept_convert_still_blocked_after_completion(self, auth_client):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/complete-pricing-review",
            json=_valid_completion_request(quote_id, intake_code),
        )
        review = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/draft-review")
        payload = review.json()
        assert payload["can_accept_quote"] is False
        assert payload["can_convert_to_order"] is False
        assert "INTAKE_V3_ACCEPT_CONVERT_SEPARATE_FLOW" in payload["conversion_blockers"]
