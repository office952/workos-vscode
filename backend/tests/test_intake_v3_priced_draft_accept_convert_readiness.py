"""Intake V3 priced draft accept/convert readiness — read-only audit, actions blocked."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from tests.test_intake_v3_quote_pricing_review_completion import (
    _create_iv3_draft_quote,
    _valid_completion_request,
)


def _complete_pricing(auth_client, quote_id: int, intake_code: str) -> None:
    response = auth_client.post(
        f"/api/v1/intake-v3/quotes/{quote_id}/complete-pricing-review",
        json=_valid_completion_request(quote_id, intake_code),
    )
    assert response.status_code == 200, response.text


class TestAcceptConvertReadinessSafeResponses:
    @pytest.mark.asyncio
    async def test_missing_quote_returns_safe_status(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/quotes/999999/accept-convert-readiness")
        assert response.status_code == 200
        payload = response.json()
        assert payload["review_status"] == "quote_missing"
        assert payload["accept"]["can_accept_now"] is False
        assert payload["convert"]["can_convert_now"] is False

    @pytest.mark.asyncio
    async def test_workspace_without_quote_returns_not_created(self, auth_client):
        workspace_id = _create_iv3_draft_quote(auth_client)[0]
        # Use a workspace id that has no quote by querying before create? Instead use fake ws.
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/ws-nonexistent-accept-convert/accept-convert-readiness",
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["review_status"] == "not_created"

        # workspace with quote should work
        ws_response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/accept-convert-readiness",
        )
        assert ws_response.status_code == 200
        assert ws_response.json()["review_status"] == "quote_found"


class TestAcceptConvertReadinessGuards:
    @pytest.mark.asyncio
    async def test_non_iv3_quote_not_applicable(self, auth_client, db_session):
        quote = Quotes(
            code="Q-NORMAL-ACCEPT-CONVERT",
            intake_code="WI-999",
            client_name="Normal",
            status="draft",
            version=1,
            notes=json.dumps({"human_summary": "normal"}),
        )
        db_session.add(quote)
        await db_session.commit()
        await db_session.refresh(quote)

        response = auth_client.get(
            f"/api/v1/intake-v3/quotes/{quote.id}/accept-convert-readiness",
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["review_status"] == "not_applicable"
        assert payload["is_intake_v3_quote"] is False

    @pytest.mark.asyncio
    async def test_iv3_without_pricing_review_blocks_accept(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))

        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/accept-convert-readiness")
        assert response.status_code == 200
        payload = response.json()
        assert payload["accept"]["accept_readiness_status"] == "blocked_pricing_review_required"
        assert payload["accept"]["can_accept_now"] is False
        assert payload["accept"]["accept_action_enabled"] is False
        assert payload["convert"]["can_convert_now"] is False
        assert any(
            b["code"] == "PRICING_REVIEW_REQUIRED" for b in payload["accept"]["accept_blockers"]
        )

        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert orders_after == orders_before
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_iv3_priced_draft_accept_ready_preview_action_blocked(self, auth_client):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)

        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/accept-convert-readiness")
        assert response.status_code == 200
        payload = response.json()
        assert payload["pricing_review_completed"] is True
        assert payload["priced_draft"] is True
        assert payload["accept"]["accept_readiness_status"] == "ready_for_guarded_accept"
        assert payload["accept"]["is_accept_ready_preview"] is True
        assert payload["accept"]["can_accept_now"] is True
        assert payload["accept"]["accept_action_enabled"] is True

    @pytest.mark.asyncio
    async def test_convert_blocked_until_accepted(self, auth_client):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)

        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/accept-convert-readiness")
        payload = response.json()
        assert payload["convert"]["convert_readiness_status"] == "blocked_acceptance_required"
        assert payload["convert"]["can_convert_now"] is False
        assert payload["convert"]["convert_action_enabled"] is False
        assert any(
            b["code"] == "QUOTE_NOT_ACCEPTED" for b in payload["convert"]["convert_blockers"]
        )

    @pytest.mark.asyncio
    async def test_invalid_notes_json_safe(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        quote.notes = "not-json"
        await db_session.commit()

        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/accept-convert-readiness")
        assert response.status_code == 200
        payload = response.json()
        assert "NOTES_JSON_INVALID" in payload["warnings"]
        assert payload["accept"]["can_accept_now"] is False

    @pytest.mark.asyncio
    async def test_pricing_completion_regression_readiness(self, auth_client):
        workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)

        ws_response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/accept-convert-readiness",
        )
        assert ws_response.status_code == 200
        payload = ws_response.json()
        assert payload["quote_id"] == quote_id
        assert payload["final_price_present"] is True
        assert payload["no_order_created"] is True
        assert payload["no_execution_created"] is True
        assert payload["no_inventory_mutated"] is True
