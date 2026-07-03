"""Intake V3 guarded commercial quote draft creation — first real Quote write, no order/execution/inventory."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from services.intake_v3_preview_fixtures import INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_LINKAGE_JSON_KEY,
    INTAKE_V3_SOURCE_MODULE,
    intake_v3_linkage_code,
    parse_intake_v3_linkage_from_notes,
)

MINIMAL_WORKSPACE_PAYLOAD = {
    "client_request": {
        "client_name": "Draft quote test",
        "request_code": "DQ-TEST-001",
        "job_title": "Draft quote test",
    },
    "product_selection": {"template_code": "TPL-VOLUMETRIC-LETTERS", "pilot_scope": True},
    "material_intent": {"inventory_mutation_allowed": False, "estimate_status": "not_started"},
    "production_handoff": {"preview_only": True},
    "employee_preview_seed": {"non_executable": True, "preview_tasks": []},
}


def _valid_request(workspace_id: str, **overrides) -> dict:
    payload = {
        "owner_decision": {
            "decision_status": "approved",
            "decision_reason": "Owner approved draft quote creation from Intake V3.",
            "approval_checkbox": True,
        },
        "expected_workspace_id": workspace_id,
        "expected_bridge_status": "disabled_by_policy",
        "expected_enablement_status": "owner_approval_required",
        "confirm_create_draft_only": True,
        "confirm_no_order": True,
        "confirm_no_execution": True,
        "confirm_no_inventory": True,
    }
    if overrides:
        owner_override = overrides.pop("owner_decision", None)
        if owner_override is not None:
            payload["owner_decision"] = owner_override
        payload.update(overrides)
    return payload


def _seed_hub_workspace(auth_client) -> str:
    response = auth_client.post(
        "/api/v1/intake-v3/workspaces/seed-from-scenario",
        json={"scenario": INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL, "title": "Guarded quote test"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_draft_quote(auth_client, workspace_id: str, **request_overrides):
    return auth_client.post(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/create-draft-quote",
        json=_valid_request(workspace_id, **request_overrides),
    )


class TestGuardedDraftQuoteValidation:
    @pytest.mark.asyncio
    async def test_missing_owner_decision_blocks_creation(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        quotes_before = await db_session.scalar(select(func.count()).select_from(Quotes))
        response = _create_draft_quote(
            auth_client,
            workspace_id,
            owner_decision={
                "decision_status": "rejected",
                "decision_reason": "",
                "approval_checkbox": False,
            },
        )
        assert response.status_code == 422
        quotes_after = await db_session.scalar(select(func.count()).select_from(Quotes))
        assert quotes_after == quotes_before

    @pytest.mark.asyncio
    async def test_approval_checkbox_false_blocks_creation(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        quotes_before = await db_session.scalar(select(func.count()).select_from(Quotes))
        response = _create_draft_quote(
            auth_client,
            workspace_id,
            owner_decision={
                "decision_status": "approved",
                "decision_reason": "Owner approved draft quote creation from Intake V3.",
                "approval_checkbox": False,
            },
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "OWNER_DECISION_REQUIRED"
        quotes_after = await db_session.scalar(select(func.count()).select_from(Quotes))
        assert quotes_after == quotes_before

    @pytest.mark.asyncio
    async def test_incomplete_workspace_blocks_creation(self, auth_client, db_session):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Incomplete", "payload": MINIMAL_WORKSPACE_PAYLOAD},
        )
        assert create.status_code == 201
        workspace_id = create.json()["id"]
        quotes_before = await db_session.scalar(select(func.count()).select_from(Quotes))
        response = _create_draft_quote(auth_client, workspace_id)
        assert response.status_code == 422
        assert response.json()["detail"]["error"] in {
            "WORKSPACE_INCOMPLETE",
            "READINESS_CHAIN_INCOMPLETE",
        }
        quotes_after = await db_session.scalar(select(func.count()).select_from(Quotes))
        assert quotes_after == quotes_before


class TestGuardedDraftQuoteCreation:
    @pytest.mark.asyncio
    async def test_complete_workspace_creates_draft_quote_only(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        quotes_before = await db_session.scalar(select(func.count()).select_from(Quotes))

        response = _create_draft_quote(auth_client, workspace_id)
        assert response.status_code == 201, response.text
        payload = response.json()
        assert payload["quote_created"] is True
        assert payload["quote_status"] == "draft"
        assert payload["source_module"] == INTAKE_V3_SOURCE_MODULE
        assert payload["source_workspace_id"] == workspace_id
        assert payload["order_created"] is False
        assert payload["execution_plan_created"] is False
        assert payload["inventory_mutated"] is False
        assert payload["requires_pricing_review"] is True
        assert payload["cost_engine_called"] is False

        quotes_after = await db_session.scalar(select(func.count()).select_from(Quotes))
        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert quotes_after == quotes_before + 1
        assert orders_after == orders_before
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_snapshot_attached_in_notes(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        response = _create_draft_quote(auth_client, workspace_id)
        assert response.status_code == 201
        quote_id = response.json()["quote_id"]
        quote = await db_session.get(Quotes, quote_id)
        assert quote is not None
        assert quote.intake_code == intake_v3_linkage_code(workspace_id)
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        assert linkage is not None
        assert linkage["source_module"] == INTAKE_V3_SOURCE_MODULE
        assert linkage["source_workspace_id"] == workspace_id
        snapshot = linkage["snapshot"]
        assert snapshot["raw_analysis_not_production_truth"] is True
        assert "confirmed_production_model_snapshot" in snapshot["sections"]
        assert snapshot["sections"]["raw_svg_analysis_reference"]["not_production_truth"] is True
        assert snapshot["holes_not_letters"] is True

    @pytest.mark.asyncio
    async def test_owner_decision_attached(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        response = _create_draft_quote(auth_client, workspace_id)
        assert response.status_code == 201
        quote = await db_session.get(Quotes, response.json()["quote_id"])
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        owner = linkage["owner_decision"]
        assert owner["decision_status"] == "approved"
        assert owner["decision_reason"]
        assert owner["owner_user_id"] == "test-user-id"
        assert owner["approved_workspace_id"] == workspace_id
        assert owner["approval_checkbox"] is True

    @pytest.mark.asyncio
    async def test_duplicate_creation_blocked(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        first = _create_draft_quote(auth_client, workspace_id)
        assert first.status_code == 201
        second = _create_draft_quote(auth_client, workspace_id)
        assert second.status_code == 422
        assert second.json()["detail"]["error"] == "DUPLICATE_QUOTE_FOR_WORKSPACE"
        linkage_quotes = await db_session.scalar(
            select(func.count())
            .select_from(Quotes)
            .where(Quotes.intake_code == intake_v3_linkage_code(workspace_id))
        )
        assert linkage_quotes == 1


class TestGuardedDraftQuoteEndpoint:
    def test_endpoint_requires_valid_request_body(self, auth_client):
        workspace_id = _seed_hub_workspace(auth_client)
        response = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/create-draft-quote",
            json={"owner_decision": {"decision_status": "approved", "decision_reason": "x", "approval_checkbox": True}},
        )
        assert response.status_code == 422

    def test_regression_readiness_endpoints_still_read_only(self, auth_client):
        workspace_id = _seed_hub_workspace(auth_client)
        before = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        before_updated = before.json()["updated_at"]

        readiness = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/real-quote-creation-enablement-readiness"
        )
        assert readiness.status_code == 200
        assert readiness.json()["readiness"]["can_create_quote_now"] is False

        after = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert after.json()["updated_at"] == before_updated

    def test_notes_json_roundtrip(self):
        notes = json.dumps(
            {
                "human_summary": "test",
                INTAKE_V3_LINKAGE_JSON_KEY: {"source_module": INTAKE_V3_SOURCE_MODULE},
            }
        )
        parsed = parse_intake_v3_linkage_from_notes(notes)
        assert parsed["source_module"] == INTAKE_V3_SOURCE_MODULE
