"""Intake V3 production task generation dry-run — read-only contract tests."""

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
    _valid_convert_request,
)


def _convert_iv3_quote(auth_client, quote_id: int, intake_code: str) -> dict:
    response = auth_client.post(
        f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
        json=_valid_convert_request(quote_id, intake_code),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _prepare_converted_iv3_order(auth_client) -> tuple[int, int, str, str]:
    workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
    _complete_pricing(auth_client, quote_id, intake_code)
    _accept_iv3_quote(auth_client, quote_id, intake_code)
    payload = _convert_iv3_quote(auth_client, quote_id, intake_code)
    return payload["order_id"], quote_id, intake_code, workspace_id


async def _strip_confirmed_model_async(db_session, quote_id: int) -> None:
    quote = await db_session.get(Quotes, quote_id)
    assert quote is not None
    linkage = parse_intake_v3_linkage_from_notes(quote.notes)
    assert linkage is not None
    snapshot = linkage.setdefault("snapshot", {})
    sections = snapshot.setdefault("sections", {})
    sections.pop("confirmed_production_model_snapshot", None)
    workspace_payload = sections.get("workspace_payload_snapshot")
    if isinstance(workspace_payload, dict):
        workspace_payload.pop("confirmed_production_model", None)
    notes_payload = json.loads(quote.notes)
    notes_payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
    quote.notes = json.dumps(notes_payload)
    await db_session.commit()


class TestProductionTaskDryRunSafeResponses:
    @pytest.mark.asyncio
    async def test_missing_order_returns_not_found(self, auth_client, db_session):
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))

        response = auth_client.get("/api/v1/intake-v3/orders/999999/production-task-dry-run")
        assert response.status_code == 404

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        assert plans_after == plans_before
        assert movements_after == movements_before

    @pytest.mark.asyncio
    async def test_missing_quote_returns_not_found(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/quotes/999999/production-task-dry-run")
        assert response.status_code == 404


class TestProductionTaskDryRunNonIv3:
    @pytest.mark.asyncio
    async def test_non_iv3_order_returns_non_iv3_response(self, auth_client, db_session):
        order = Orders(
            code="ORD-NON-IV3-DRYRUN",
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

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order.id}/production-task-dry-run")
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3"] is False
        assert payload["creates_execution_plan"] is False
        assert payload["creates_execution_tasks"] is False
        assert payload["mutates_inventory"] is False
        assert payload["starts_production"] is False
        assert payload["can_generate_real_tasks_now"] is False


class TestProductionTaskDryRunIv3ConvertedOrder:
    @pytest.mark.asyncio
    async def test_converted_order_returns_candidate_groups(self, auth_client, db_session):
        order_id, _, _, _ = _prepare_converted_iv3_order(auth_client)
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-task-dry-run")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["is_intake_v3"] is True
        assert payload["dry_run_scope"] == "production_task_generation_preview_only"
        assert payload["summary"]["candidate_groups_count"] > 0
        assert payload["summary"]["candidate_tasks_count"] > 0
        assert payload["creates_execution_plan"] is False
        assert payload["creates_execution_tasks"] is False
        assert payload["can_generate_real_tasks_now"] is False

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_hub_fixture_respects_18_27_9(self, auth_client):
        order_id, _, _, _ = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-task-dry-run")
        assert response.status_code == 200
        payload = response.json()
        cnc_face = next(
            task
            for task in payload["candidate_tasks"]
            if task["candidate_task_id"] == "dryrun-cnc-face-cutting"
        )
        letters_input = next(item for item in cnc_face["inputs_preview"] if item["label"] == "Real letters")
        holes_input = next(item for item in cnc_face["inputs_preview"] if item["label"] == "Holes (not letters)")
        contours_input = next(
            item for item in cnc_face["inputs_preview"] if item["label"] == "Closed contours"
        )
        assert letters_input["value"] == 18
        assert contours_input["value"] == 27
        assert holes_input["value"] == 9


class TestProductionTaskDryRunBlockers:
    @pytest.mark.asyncio
    async def test_missing_production_readiness_warns_on_draft_quote(self, auth_client):
        workspace_id, _, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-task-dry-run",
        )
        assert response.status_code == 200
        codes = [item["code"] for item in response.json()["warnings"]]
        assert "missing_production_readiness" in codes or "missing_order" in codes

    @pytest.mark.asyncio
    async def test_missing_confirmed_model_blocks(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _strip_confirmed_model_async(db_session, quote_id)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/production-task-dry-run")
        assert response.status_code == 200
        payload = response.json()
        blocker_codes = [item["code"] for item in payload["blockers"]]
        assert "missing_confirmed_production_model" in blocker_codes
        assert payload["summary"]["candidate_tasks_count"] == 0

    @pytest.mark.asyncio
    async def test_missing_material_breakdown_warns_not_blocks(self, auth_client):
        workspace_id, _, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-task-dry-run",
        )
        assert response.status_code == 200
        payload = response.json()
        warning_codes = [item["code"] for item in payload["warnings"]]
        assert "missing_material_breakdown" in warning_codes or payload["material_breakdown_available"] is True
        assert payload["creates_execution_tasks"] is False


class TestProductionTaskDryRunDependencies:
    @pytest.mark.asyncio
    async def test_candidate_task_dependencies_exist(self, auth_client):
        order_id, _, _, _ = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-task-dry-run")
        assert response.status_code == 200
        payload = response.json()
        deps = payload["dependencies"]
        assert len(deps) > 0
        from_ids = {item["from_candidate_task_id"] for item in deps}
        to_ids = {item["to_candidate_task_id"] for item in deps}
        assert "dryrun-cnc-face-cutting" in to_ids or "dryrun-cnc-file-preparation" in from_ids
        assert "dryrun-stretch-wrap-and-delivery-mounting-package" in to_ids or any(
            "stretch-wrap" in task_id for task_id in to_ids
        )


class TestProductionTaskDryRunNoSideEffects:
    @pytest.mark.asyncio
    async def test_no_execution_inventory_side_effects(self, auth_client, db_session):
        order_id, quote_id, _, _ = _prepare_converted_iv3_order(auth_client)
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))
        order_before = await db_session.get(Orders, order_id)
        quote_before = await db_session.get(Quotes, quote_id)
        assert order_before is not None and quote_before is not None
        order_status_before = order_before.status
        quote_status_before = quote_before.status

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-task-dry-run")
        assert response.status_code == 200

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        order_after = await db_session.get(Orders, order_id)
        quote_after = await db_session.get(Quotes, quote_id)
        assert plans_after == plans_before
        assert movements_after == movements_before
        assert order_after.status == order_status_before
        assert quote_after.status == quote_status_before


class TestProductionTaskDryRunEndpoints:
    @pytest.mark.asyncio
    async def test_endpoint_by_quote_works(self, auth_client):
        order_id, quote_id, _, _ = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/production-task-dry-run")
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3"] is True
        assert payload["quote_id"] == quote_id
        assert payload["order_id"] == order_id

    @pytest.mark.asyncio
    async def test_endpoint_by_workspace_works(self, auth_client):
        order_id, quote_id, _, workspace_id = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-task-dry-run",
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3"] is True
        assert payload["source_type"] == "workspace"
        assert payload["order_id"] == order_id
        assert payload["quote_id"] == quote_id

    @pytest.mark.asyncio
    async def test_all_candidate_tasks_are_preview_only(self, auth_client):
        order_id, _, _, _ = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-task-dry-run")
        payload = response.json()
        for task in payload["candidate_tasks"]:
            assert task["will_create_real_task"] is False
