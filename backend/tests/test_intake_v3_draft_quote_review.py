"""Intake V3 draft quote review + pricing handoff — read-only post-create audit."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from services.intake_v3_draft_quote_review_service import parse_intake_v3_quote_notes
from services.intake_v3_real_commercial_quote_creation_service import intake_v3_linkage_code
from tests.test_intake_v3_real_commercial_quote_creation import (
    _create_draft_quote,
    _seed_hub_workspace,
)


class TestDraftQuoteReviewNotCreated:
    @pytest.mark.asyncio
    async def test_review_returns_not_created_before_draft_quote(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        quotes_before = await db_session.scalar(select(func.count()).select_from(Quotes))
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/draft-quote-review",
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["review_status"] == "not_created"
        assert payload["is_intake_v3_quote"] is False
        assert payload["requires_pricing_review"] is True
        assert payload["can_accept_quote"] is False
        assert payload["can_convert_to_order"] is False
        assert "No Intake V3 draft quote" in payload["message"]

        quotes_after = await db_session.scalar(select(func.count()).select_from(Quotes))
        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert quotes_after == quotes_before
        assert orders_after == orders_before
        assert plans_after == plans_before


class TestDraftQuoteReviewDetected:
    @pytest.mark.asyncio
    async def test_review_detects_intake_v3_quote(self, auth_client):
        workspace_id = _seed_hub_workspace(auth_client)
        create = _create_draft_quote(auth_client, workspace_id)
        assert create.status_code == 201

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/draft-quote-review",
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["review_status"] == "quote_found"
        assert payload["is_intake_v3_quote"] is True
        assert payload["source_workspace_id"] == workspace_id
        assert payload["quote_status"] == "draft"
        assert payload["intake_code"] == intake_v3_linkage_code(workspace_id)


class TestDraftQuoteSnapshotSummary:
    @pytest.mark.asyncio
    async def test_snapshot_summary_parses_notes(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        create = _create_draft_quote(auth_client, workspace_id)
        quote_id = create.json()["quote_id"]
        quote = await db_session.get(Quotes, quote_id)
        assert quote is not None

        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/draft-review")
        assert response.status_code == 200
        summary = response.json()["snapshot_summary"]
        assert summary["owner_decision_present"] is True
        assert summary["confirmed_model_present"] is True
        assert summary["finish_variation_present"] is True
        assert summary["raw_analysis_not_production_truth"] is True
        assert summary["holes_not_letters"] is True


class TestDraftQuotePricingHandoff:
    @pytest.mark.asyncio
    async def test_pricing_handoff_requires_review(self, auth_client):
        workspace_id = _seed_hub_workspace(auth_client)
        create = _create_draft_quote(auth_client, workspace_id)
        quote_id = create.json()["quote_id"]

        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/draft-review")
        handoff = response.json()["pricing_handoff"]
        assert handoff["requires_pricing_review"] is True
        assert handoff["final_price_present"] is False
        assert handoff["cost_engine_called"] is False
        assert handoff["pricing_handoff_status"] == "requires_review"


class TestDraftQuoteConversionGuard:
    @pytest.mark.asyncio
    async def test_conversion_guard_blocks_accept_and_order(self, auth_client):
        workspace_id = _seed_hub_workspace(auth_client)
        create = _create_draft_quote(auth_client, workspace_id)
        quote_id = create.json()["quote_id"]

        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/draft-review")
        payload = response.json()
        assert payload["can_accept_quote"] is False
        assert payload["can_convert_to_order"] is False
        guard = payload["conversion_guard"]
        assert guard["can_accept_quote"] is False
        assert guard["can_convert_to_order"] is False
        assert "REQUIRES_PRICING_REVIEW" in guard["conversion_blockers"]


class TestDraftQuoteInvalidNotes:
    @pytest.mark.asyncio
    async def test_invalid_notes_json_handled_safely(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        create = _create_draft_quote(auth_client, workspace_id)
        quote_id = create.json()["quote_id"]
        quote = await db_session.get(Quotes, quote_id)
        assert quote is not None
        quote.notes = "not-json"
        await db_session.commit()

        linkage, warnings = parse_intake_v3_quote_notes(quote.notes)
        assert linkage is None
        assert any(w.code == "NOTES_JSON_INVALID" for w in warnings)

        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/draft-review")
        assert response.status_code == 200
        payload = response.json()
        assert payload["review_status"] == "not_applicable"
        assert any(w["code"] == "NOTES_JSON_INVALID" for w in payload["warnings"])


class TestDraftQuoteNormalQuoteUnaffected:
    @pytest.mark.asyncio
    async def test_normal_quote_not_applicable(self, auth_client, db_session):
        quote = Quotes(
            code="Q-NORMAL-TEST",
            intake_code="WI-12345",
            client_name="Normal Client",
            status="priced",
            version=1,
            grand_total=100.0,
            notes=json.dumps({"human_summary": "Normal quote"}),
        )
        db_session.add(quote)
        await db_session.commit()
        await db_session.refresh(quote)

        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote.id}/draft-review")
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3_quote"] is False
        assert payload["review_status"] == "not_applicable"
        assert payload["conversion_guard"]["can_accept_quote"] is True
        assert payload["conversion_guard"]["can_convert_to_order"] is True


class TestDraftQuoteReadOnlySideEffects:
    @pytest.mark.asyncio
    async def test_read_only_endpoint_does_not_write(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        _create_draft_quote(auth_client, workspace_id)
        quotes_before = await db_session.scalar(select(func.count()).select_from(Quotes))
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/draft-quote-review",
        )
        assert response.status_code == 200

        quotes_after = await db_session.scalar(select(func.count()).select_from(Quotes))
        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert quotes_after == quotes_before
        assert orders_after == orders_before
        assert plans_after == plans_before
