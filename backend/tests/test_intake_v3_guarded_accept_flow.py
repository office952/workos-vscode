"""Intake V3 guarded accept flow — priced draft to accepted, no Order/Execution/Inventory."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_LINKAGE_JSON_KEY,
    parse_intake_v3_linkage_from_notes,
)
from tests.test_intake_v3_quote_pricing_review_completion import (
    _create_iv3_draft_quote,
    _valid_completion_request,
)


def _valid_accept_request(quote_id: int, intake_code: str, **overrides) -> dict:
    payload = {
        "expected_quote_id": quote_id,
        "expected_intake_code": intake_code,
        "accept_decision": "approved",
        "accept_reason": "Client/owner approved the priced Intake V3 draft quote.",
        "acceptance_source": "operator",
        "reviewer_confirmation": True,
        "confirm_pricing_review_completed": True,
        "confirm_quote_stays_commercial": True,
        "confirm_no_order": True,
        "confirm_no_execution": True,
        "confirm_no_inventory": True,
        "confirm_convert_separate": True,
    }
    payload.update(overrides)
    return payload


def _complete_pricing(auth_client, quote_id: int, intake_code: str) -> None:
    response = auth_client.post(
        f"/api/v1/intake-v3/quotes/{quote_id}/complete-pricing-review",
        json=_valid_completion_request(quote_id, intake_code),
    )
    assert response.status_code == 200, response.text


class TestGuardedAcceptSafeResponses:
    @pytest.mark.asyncio
    async def test_missing_quote_blocks(self, auth_client, db_session):
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        response = auth_client.post(
            "/api/v1/intake-v3/quotes/999999/accept",
            json=_valid_accept_request(999999, "IV3-WS-999"),
        )
        assert response.status_code == 404
        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        assert orders_after == orders_before

    @pytest.mark.asyncio
    async def test_accept_state_missing_quote(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/quotes/999999/accept-state")
        assert response.status_code == 200
        payload = response.json()
        assert payload["review_status"] == "quote_missing"
        assert payload["can_accept_now"] is False


class TestGuardedAcceptValidation:
    @pytest.mark.asyncio
    async def test_non_iv3_quote_blocks(self, auth_client, db_session):
        quote = Quotes(
            code="Q-NORMAL-ACCEPT",
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
            f"/api/v1/intake-v3/quotes/{quote.id}/accept",
            json=_valid_accept_request(quote.id, "WI-999"),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "NOT_IV3_QUOTE"
        assert quote.status == "draft"

    @pytest.mark.asyncio
    async def test_unpriced_draft_blocks(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        status_before = quote.status

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "PRICING_REVIEW_REQUIRED"

        await db_session.refresh(quote)
        assert quote.status == status_before

    @pytest.mark.asyncio
    async def test_missing_confirmations_blocks(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        quote = await db_session.get(Quotes, quote_id)

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code, confirm_no_order=False),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "CONFIRMATIONS_REQUIRED"

        await db_session.refresh(quote)
        assert quote.status == "draft"

    @pytest.mark.asyncio
    async def test_invalid_notes_json_blocks(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        quote = await db_session.get(Quotes, quote_id)
        quote.notes = "not-json"
        await db_session.commit()

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "NOTES_JSON_INVALID"

        await db_session.refresh(quote)
        assert quote.status == "draft"


class TestGuardedAcceptSuccess:
    @pytest.mark.asyncio
    async def test_priced_draft_accepts_with_confirmations(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)

        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["accepted"] is True
        assert payload["quote_status_before"] == "draft"
        assert payload["quote_status_after"] == "accepted"
        assert payload["order_created"] is False
        assert payload["execution_plan_created"] is False
        assert payload["execution_task_created"] is False
        assert payload["inventory_mutated"] is False
        assert payload["can_convert_now"] is False
        assert payload["convert_action_enabled"] is False

        quote = await db_session.get(Quotes, quote_id)
        assert quote.status == "accepted"
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        assert linkage is not None
        assert linkage.get("accept_decision", {}).get("status") == "approved"
        assert linkage.get("snapshot") is not None
        assert linkage.get("pricing_review") is not None

        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert orders_after == orders_before
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_duplicate_accept_blocks(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        first = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert first.status_code == 200

        second = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert second.status_code == 422
        assert second.json()["detail"]["error"] == "ACCEPT_ALREADY_COMPLETED"

    @pytest.mark.asyncio
    async def test_readiness_reflects_accepted_state(self, auth_client):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        accept_response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert accept_response.status_code == 200

        readiness = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/accept-convert-readiness")
        assert readiness.status_code == 200
        payload = readiness.json()
        assert payload["accept"]["accept_readiness_status"] == "accepted"
        assert payload["accept"]["can_accept_now"] is False
        assert payload["accept"]["accept_action_enabled"] is False
        assert payload["convert"]["convert_readiness_status"] == "ready_for_guarded_convert"
        assert payload["convert"]["can_convert_now"] is True
        assert payload["convert"]["convert_action_enabled"] is True

    @pytest.mark.asyncio
    async def test_accept_state_after_success(self, auth_client):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        state = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/accept-state")
        assert state.status_code == 200
        payload = state.json()
        assert payload["review_status"] == "accepted"
        assert payload["accept_completed"] is True
        assert payload["can_accept_now"] is False

    @pytest.mark.asyncio
    async def test_workspace_accept_endpoint(self, auth_client):
        workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        response = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 200
        assert response.json()["quote_status_after"] == "accepted"


class TestGuardedAcceptTransitionValidation:
    @pytest.mark.asyncio
    async def test_draft_to_accepted_uses_lifecycle_chain(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 200
        quote = await db_session.get(Quotes, quote_id)
        assert quote.status == "accepted"
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        assert linkage["accept_decision"]["quote_status_before"] == "draft"
        assert linkage["accept_decision"]["quote_status_after"] == "accepted"

    @pytest.mark.asyncio
    async def test_missing_snapshot_blocks(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        quote = await db_session.get(Quotes, quote_id)
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        linkage.pop("snapshot", None)
        notes_payload = json.loads(quote.notes)
        notes_payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
        quote.notes = json.dumps(notes_payload)
        await db_session.commit()

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "SNAPSHOT_MISSING"
