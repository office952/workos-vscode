"""Intake V3 guarded convert to order — Order only, no Execution/Inventory."""

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
from tests.test_intake_v3_guarded_accept_flow import (
    _complete_pricing,
    _create_iv3_draft_quote,
    _valid_accept_request,
)
from tests.test_intake_v3_quote_pricing_review_completion import _valid_completion_request


def _valid_convert_request(quote_id: int, intake_code: str, **overrides) -> dict:
    payload = {
        "expected_quote_id": quote_id,
        "expected_intake_code": intake_code,
        "convert_decision": "approved",
        "convert_reason": "Accepted Intake V3 quote approved for order creation.",
        "conversion_source": "operator",
        "reviewer_confirmation": True,
        "confirm_quote_accepted": True,
        "confirm_pricing_review_completed": True,
        "confirm_create_order_only": True,
        "confirm_no_execution_plan": True,
        "confirm_no_execution_tasks": True,
        "confirm_no_inventory": True,
        "confirm_production_separate": True,
    }
    payload.update(overrides)
    return payload


def _accept_iv3_quote(auth_client, quote_id: int, intake_code: str) -> None:
    response = auth_client.post(
        f"/api/v1/intake-v3/quotes/{quote_id}/accept",
        json=_valid_accept_request(quote_id, intake_code),
    )
    assert response.status_code == 200, response.text


def _prepare_accepted_iv3_quote(auth_client) -> tuple[int, str]:
    _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
    _complete_pricing(auth_client, quote_id, intake_code)
    _accept_iv3_quote(auth_client, quote_id, intake_code)
    return quote_id, intake_code


class TestGuardedConvertSafeResponses:
    @pytest.mark.asyncio
    async def test_missing_quote_blocks(self, auth_client, db_session):
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        response = auth_client.post(
            "/api/v1/intake-v3/quotes/999999/convert-to-order",
            json=_valid_convert_request(999999, "IV3-WS-999"),
        )
        assert response.status_code == 404
        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        assert orders_after == orders_before

    @pytest.mark.asyncio
    async def test_convert_state_missing_quote(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/quotes/999999/convert-to-order-state")
        assert response.status_code == 200
        payload = response.json()
        assert payload["review_status"] == "quote_missing"
        assert payload["can_convert_now"] is False


class TestGuardedConvertValidation:
    @pytest.mark.asyncio
    async def test_non_iv3_quote_blocks(self, auth_client, db_session):
        quote = Quotes(
            code="Q-NORMAL-CONVERT",
            intake_code="WI-999",
            client_name="Normal",
            status="accepted",
            version=1,
            notes=json.dumps({"human_summary": "normal"}),
        )
        db_session.add(quote)
        await db_session.commit()
        await db_session.refresh(quote)

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote.id}/convert-to-order",
            json=_valid_convert_request(quote.id, "WI-999"),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "NOT_IV3_QUOTE"

    @pytest.mark.asyncio
    async def test_priced_draft_not_accepted_blocks(self, auth_client, db_session):
        _, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "QUOTE_NOT_ACCEPTED"

        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        assert orders_after == orders_before

    @pytest.mark.asyncio
    async def test_missing_confirmations_blocks(self, auth_client, db_session):
        quote_id, intake_code = _prepare_accepted_iv3_quote(auth_client)
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code, confirm_create_order_only=False),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "CONFIRMATIONS_REQUIRED"

        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        assert orders_after == orders_before

    @pytest.mark.asyncio
    async def test_invalid_notes_json_blocks(self, auth_client, db_session):
        quote_id, intake_code = _prepare_accepted_iv3_quote(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        quote.notes = "not-json"
        await db_session.commit()

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "NOTES_JSON_INVALID"


class TestGuardedConvertSuccess:
    @pytest.mark.asyncio
    async def test_accepted_quote_converts_with_confirmations(self, auth_client, db_session):
        quote_id, intake_code = _prepare_accepted_iv3_quote(auth_client)
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))

        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["converted"] is True
        assert payload["quote_status"] == "accepted"
        assert payload["order_status"] == "locked"
        assert payload["order_created"] is True
        assert payload["execution_plan_created"] is False
        assert payload["execution_task_created"] is False
        assert payload["inventory_mutated"] is False
        assert payload["production_started"] is False
        assert payload["can_start_production_now"] is False

        quote = await db_session.get(Quotes, quote_id)
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        assert linkage is not None
        assert linkage.get("convert_decision", {}).get("status") == "approved"
        assert linkage.get("accept_decision") is not None
        assert linkage.get("snapshot") is not None

        order = await db_session.get(Orders, payload["order_id"])
        assert order is not None
        assert order.quote_id == quote_id
        assert order.status == "locked"
        assert order.notes is not None

        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert orders_after == orders_before + 1
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_duplicate_convert_blocks(self, auth_client, db_session):
        quote_id, intake_code = _prepare_accepted_iv3_quote(auth_client)
        first = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert first.status_code == 200
        orders_after_first = await db_session.scalar(select(func.count()).select_from(Orders))

        second = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert second.status_code == 422
        assert second.json()["detail"]["error"] in {"CONVERT_ALREADY_COMPLETED", "ORDER_ALREADY_EXISTS"}

        orders_after_second = await db_session.scalar(select(func.count()).select_from(Orders))
        assert orders_after_second == orders_after_first

    @pytest.mark.asyncio
    async def test_readiness_reflects_converted_state(self, auth_client):
        quote_id, intake_code = _prepare_accepted_iv3_quote(auth_client)
        convert_response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert convert_response.status_code == 200

        readiness = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/accept-convert-readiness")
        assert readiness.status_code == 200
        payload = readiness.json()
        assert payload["order_exists"] is True
        assert payload["convert"]["convert_readiness_status"] == "converted_to_order"
        assert payload["convert"]["can_convert_now"] is False

    @pytest.mark.asyncio
    async def test_convert_state_after_success(self, auth_client):
        quote_id, intake_code = _prepare_accepted_iv3_quote(auth_client)
        auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        state = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order-state")
        assert state.status_code == 200
        payload = state.json()
        assert payload["review_status"] == "converted_to_order"
        assert payload["convert_completed"] is True
        assert payload["existing_order_id"] is not None

    @pytest.mark.asyncio
    async def test_workspace_convert_endpoint(self, auth_client):
        workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        _accept_iv3_quote(auth_client, quote_id, intake_code)
        response = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 200
        assert response.json()["order_status"] == "locked"

    @pytest.mark.asyncio
    async def test_accepted_state_ready_before_convert(self, auth_client):
        quote_id, intake_code = _prepare_accepted_iv3_quote(auth_client)
        state = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order-state")
        assert state.status_code == 200
        payload = state.json()
        assert payload["review_status"] == "ready_for_guarded_convert"
        assert payload["can_convert_now"] is True
