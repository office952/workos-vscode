"""Intake V3 order production readiness — read-only audit, no Execution/Inventory."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from models.stock_movements import StockMovement
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_LINKAGE_JSON_KEY,
    parse_intake_v3_linkage_from_notes,
)
from tests.test_intake_v3_guarded_convert_to_order import (
    _accept_iv3_quote,
    _complete_pricing,
    _create_iv3_draft_quote,
    _prepare_accepted_iv3_quote,
    _valid_convert_request,
)


def _convert_iv3_quote(auth_client, quote_id: int, intake_code: str) -> dict:
    response = auth_client.post(
        f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
        json=_valid_convert_request(quote_id, intake_code),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _prepare_converted_iv3_order(auth_client) -> tuple[int, int, str]:
    quote_id, intake_code = _prepare_accepted_iv3_quote(auth_client)
    payload = _convert_iv3_quote(auth_client, quote_id, intake_code)
    return payload["order_id"], quote_id, intake_code


class TestOrderProductionReadinessSafeResponses:
    @pytest.mark.asyncio
    async def test_missing_order_returns_not_found(self, auth_client, db_session):
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))

        response = auth_client.get("/api/v1/intake-v3/orders/999999/production-readiness")
        assert response.status_code == 404

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        assert plans_after == plans_before
        assert movements_after == movements_before

    @pytest.mark.asyncio
    async def test_missing_quote_for_readiness_returns_missing_order_blocker(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/quotes/999999/order-production-readiness")
        assert response.status_code == 404


class TestOrderProductionReadinessNonIv3:
    @pytest.mark.asyncio
    async def test_non_iv3_order_returns_not_iv3_order(self, auth_client, db_session):
        order = Orders(
            code="ORD-NORMAL-PR",
            client_name="Normal",
            status="locked",
            payment_status="pending",
            total_amount=100.0,
            notes=json.dumps({"human_summary": "normal order"}),
            snapshot_line_items=json.dumps({"source": "manual"}),
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order.id}/production-readiness")
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3_order"] is False
        assert payload["production_readiness_status"] == "not_iv3_order"
        assert payload["can_start_production_now"] is False
        assert payload["can_generate_execution_plan_now"] is False


class TestOrderProductionReadinessIv3Converted:
    @pytest.mark.asyncio
    async def test_iv3_converted_order_readiness_success(self, auth_client, db_session):
        order_id, quote_id, _ = _prepare_converted_iv3_order(auth_client)
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["is_intake_v3_order"] is True
        assert payload["created_from_guarded_convert"] is True
        assert payload["order_status"] == "locked"
        assert payload["quote_id"] == quote_id
        assert payload["production_readiness_status"] == "ready_for_handoff_preview"
        assert payload["ready_for_handoff_preview"] is True
        assert payload["can_generate_execution_plan_now"] is False
        assert payload["can_generate_execution_tasks_now"] is False
        assert payload["can_mutate_inventory_now"] is False
        assert payload["can_start_production_now"] is False
        assert payload["available_data"]["has_confirmed_model"] is True
        assert payload["available_data"]["has_finish_assignments"] is True
        assert payload["handoff_preview"]["production_model_summary"]["real_letters_count"] == 18

        quote_response = auth_client.get(
            f"/api/v1/intake-v3/quotes/{quote_id}/order-production-readiness",
        )
        assert quote_response.status_code == 200
        assert quote_response.json()["order_id"] == order_id

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        assert plans_after == plans_before
        assert movements_after == movements_before

    @pytest.mark.asyncio
    async def test_iv3_order_without_quote_id_blocks(self, auth_client, db_session):
        order_id, _, _ = _prepare_converted_iv3_order(auth_client)
        order = await db_session.get(Orders, order_id)
        order.quote_id = None
        await db_session.commit()

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        assert response.status_code == 200
        payload = response.json()
        codes = {item["code"] for item in payload["missing_requirements"]}
        assert "missing_quote_id" in codes
        assert payload["ready_for_handoff_preview"] is False

    @pytest.mark.asyncio
    async def test_missing_confirmed_production_model_blocks(self, auth_client, db_session):
        order_id, quote_id, _ = _prepare_converted_iv3_order(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        assert linkage is not None
        sections = linkage["snapshot"]["sections"]
        sections["confirmed_production_model_snapshot"] = None
        notes_payload = json.loads(quote.notes)
        notes_payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
        quote.notes = json.dumps(notes_payload)
        await db_session.commit()

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        payload = response.json()
        assert payload["production_readiness_status"] == "missing_confirmed_production_model"
        assert payload["ready_for_handoff_preview"] is False
        assert any(
            item["code"] == "missing_confirmed_production_model"
            for item in payload["missing_requirements"]
        )

    @pytest.mark.asyncio
    async def test_missing_finish_assignments_blocks(self, auth_client, db_session):
        order_id, quote_id, _ = _prepare_converted_iv3_order(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        sections = linkage["snapshot"]["sections"]
        sections["finish_assignment_snapshot"] = None
        workspace_payload = sections.get("workspace_payload_snapshot")
        if isinstance(workspace_payload, dict):
            workspace_payload["finish_assignment"] = None
            workspace_payload["letter_group_finish_assignments"] = []
            workspace_payload["letter_finish_assignments"] = []
        notes_payload = json.loads(quote.notes)
        notes_payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
        quote.notes = json.dumps(notes_payload)
        await db_session.commit()

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        payload = response.json()
        assert payload["production_readiness_status"] == "missing_finish_assignments"
        assert any(item["code"] == "missing_finish_assignments" for item in payload["missing_requirements"])

    @pytest.mark.asyncio
    async def test_missing_accept_decision_blocks(self, auth_client, db_session):
        order_id, quote_id, _ = _prepare_converted_iv3_order(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        linkage.pop("accept_decision", None)
        notes_payload = json.loads(quote.notes)
        notes_payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
        quote.notes = json.dumps(notes_payload)
        await db_session.commit()

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        payload = response.json()
        assert payload["production_readiness_status"] == "missing_accept_decision"
        assert any(item["code"] == "missing_accept_decision" for item in payload["missing_requirements"])

    @pytest.mark.asyncio
    async def test_missing_convert_decision_blocks(self, auth_client, db_session):
        order_id, quote_id, _ = _prepare_converted_iv3_order(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        linkage.pop("convert_decision", None)
        notes_payload = json.loads(quote.notes)
        notes_payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
        quote.notes = json.dumps(notes_payload)
        order = await db_session.get(Orders, order_id)
        order_linkage = {
            "source_module": "intake_v3",
            "created_from_guarded_convert": False,
        }
        order.notes = json.dumps({"intake_v3_order_linkage_v1": order_linkage})
        order.snapshot_line_items = json.dumps(
            {"source_module": "intake_v3", "intake_v3_order_linkage_v1": order_linkage}
        )
        await db_session.commit()

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        payload = response.json()
        assert payload["production_readiness_status"] == "missing_convert_decision"
        assert any(item["code"] == "missing_convert_decision" for item in payload["missing_requirements"])

    @pytest.mark.asyncio
    async def test_invalid_quote_notes_json_blocks(self, auth_client, db_session):
        order_id, quote_id, _ = _prepare_converted_iv3_order(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        quote.notes = "not-json"
        await db_session.commit()

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        payload = response.json()
        assert payload["ready_for_handoff_preview"] is False
        assert any(item["code"] == "invalid_quote_notes_json" for item in payload["missing_requirements"])

    @pytest.mark.asyncio
    async def test_task_generation_preview_returns_candidate_groups_only(self, auth_client, db_session):
        order_id, _, _ = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        payload = response.json()
        contract = payload["task_generation_preview_contract"]
        assert contract["would_generate_execution_plan"] is False
        assert contract["would_generate_tasks_preview_only"] is True
        assert len(contract["candidate_task_groups"]) > 0
        assert contract["requires_future_build"] is True

        tasks_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        tasks_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert tasks_after == tasks_before

    @pytest.mark.asyncio
    async def test_material_readiness_preview_returns_materials_expected_only(self, auth_client, db_session):
        order_id, _, _ = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        payload = response.json()
        contract = payload["material_readiness_preview_contract"]
        assert contract["would_check_materials_preview_only"] is True
        assert len(contract["materials_expected"]) > 0
        assert contract["inventory_mutation_allowed"] is False
        assert contract["material_cost_breakdown"] == "future_build"

        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        assert movements_after == movements_before

    @pytest.mark.asyncio
    async def test_accept_convert_readiness_reflects_production_fields(self, auth_client):
        order_id, quote_id, intake_code = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/accept-convert-readiness")
        payload = response.json()
        assert payload["order_id"] == order_id
        assert payload["production_readiness_status"] == "ready_for_handoff_preview"
        assert payload["ready_for_handoff_preview"] is True
        assert payload["can_start_production_now"] is False

        workspace_id = payload["source_workspace_id"]
        if workspace_id:
            ws_response = auth_client.get(
                f"/api/v1/intake-v3/workspaces/{workspace_id}/order-production-readiness",
            )
            assert ws_response.status_code == 200
            assert ws_response.json()["order_id"] == order_id
