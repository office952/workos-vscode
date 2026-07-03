"""Intake V3 layer role confirmation propagation — workspace vs quote snapshot freshness."""

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
    intake_v3_linkage_code,
    parse_intake_v3_linkage_from_notes,
)
from tests.test_intake_v3_geometry_metrics_snapshot import _prepare_converted_iv3_order
from tests.test_intake_v3_guarded_convert_to_order import (
    _accept_iv3_quote,
    _complete_pricing,
    _valid_convert_request,
)
from tests.test_intake_v3_layer_role_confirmation import (
    LAYERED_SVG,
    _confirm_layers,
    _seed_and_upload,
)
from tests.test_intake_v3_quote_pricing_review_completion import _create_iv3_draft_quote
from tests.test_intake_v3_real_commercial_quote_creation import _create_draft_quote
from tests.test_intake_v3_svg_upload_analysis import _upload_svg


def _reconfirm_litere_ignore(auth_client, workspace_id: str) -> None:
    response = auth_client.put(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
        json={
            "layers": [
                {"layer_key": "LITERE", "confirmed_role": "ignore", "confirmation_state": "ignored"},
                {"layer_key": "SPATE", "confirmed_role": "backing", "confirmation_state": "confirmed"},
                {"layer_key": "CANT", "confirmed_role": "return", "confirmation_state": "confirmed"},
                {"layer_key": "GOLURI", "confirmed_role": "inner_hole", "confirmation_state": "confirmed"},
                {"layer_key": "UNKNOWN", "confirmed_role": "ignore", "confirmation_state": "ignored"},
            ]
        },
    )
    assert response.status_code == 200, response.text


def _create_quote_after_confirm(auth_client) -> tuple[str, int]:
    workspace_id = _seed_and_upload(auth_client)
    _confirm_layers(auth_client, workspace_id)
    create = _create_draft_quote(auth_client, workspace_id)
    assert create.status_code == 201, create.text
    return workspace_id, create.json()["quote_id"]


class TestPropagationSafeResponses:
    @pytest.mark.asyncio
    async def test_missing_workspace_returns_not_found(self, auth_client, db_session):
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        response = auth_client.get(
            "/api/v1/intake-v3/workspaces/999999/layer-role-confirmation/propagation",
        )
        assert response.status_code == 404
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_missing_quote_returns_not_found(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/quotes/999999/layer-role-confirmation/propagation")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_non_iv3_order_safe_response(self, auth_client, db_session):
        order = Orders(
            code="ORD-NON-IV3-LRP",
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

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order.id}/layer-role-confirmation/propagation")
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3"] is False
        assert payload["boundary"]["creates_execution_tasks"] is False
        assert payload["boundary"]["costengine_used"] is False


class TestPropagationFreshSnapshot:
    @pytest.mark.asyncio
    async def test_quote_snapshot_fresh_after_quote_creation(self, auth_client):
        workspace_id, quote_id = _create_quote_after_confirm(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/quotes/{quote_id}/layer-role-confirmation/propagation",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["is_intake_v3"] is True
        assert payload["is_snapshot_stale"] is False
        assert payload["effective_source"] in {"workspace_live", "quote_linkage_snapshot"}
        assert payload["changed_layers"] == []
        assert payload["downstream_uses_effective_source"] is True
        assert payload["workspace_id"] == workspace_id


class TestPropagationStaleSnapshot:
    @pytest.mark.asyncio
    async def test_workspace_reconfirm_marks_quote_snapshot_stale(self, auth_client, db_session):
        workspace_id, quote_id = _create_quote_after_confirm(auth_client)
        quote_before = await db_session.get(Quotes, quote_id)
        status_before = quote_before.status
        subtotal_before = float(quote_before.subtotal or 0)
        total_before = float(quote_before.grand_total or 0)

        _reconfirm_litere_ignore(auth_client, workspace_id)

        response = auth_client.get(
            f"/api/v1/intake-v3/quotes/{quote_id}/layer-role-confirmation/propagation",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["is_snapshot_stale"] is True
        assert payload["stale_reason"] in {
            "workspace_confirmation_newer_than_quote_snapshot",
            "layer_roles_changed",
        }
        changed_keys = {item["layer_key"] for item in payload["changed_layers"]}
        assert "LITERE" in changed_keys
        assert payload["downstream_uses_effective_source"] is True

        quote_after = await db_session.get(Quotes, quote_id)
        await db_session.refresh(quote_after)
        assert quote_after.status == status_before
        assert float(quote_after.subtotal or 0) == subtotal_before
        assert float(quote_after.grand_total or 0) == total_before

    @pytest.mark.asyncio
    async def test_order_read_detects_stale_via_workspace(self, auth_client):
        workspace_id, quote_id = _create_quote_after_confirm(auth_client)
        intake_code = intake_v3_linkage_code(workspace_id)
        _complete_pricing(auth_client, quote_id, intake_code)
        _accept_iv3_quote(auth_client, quote_id, intake_code)
        convert = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert convert.status_code == 200, convert.text
        order_id = convert.json()["order_id"]

        _reconfirm_litere_ignore(auth_client, workspace_id)

        response = auth_client.get(
            f"/api/v1/intake-v3/orders/{order_id}/layer-role-confirmation/propagation",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["is_snapshot_stale"] is True
        assert payload["effective_source"] == "workspace_live"
        assert payload["can_refresh_quote_snapshot"] is False


class TestPropagationDownstream:
    @pytest.mark.asyncio
    async def test_material_breakdown_uses_effective_source_and_stale_warning(self, auth_client):
        workspace_id, quote_id = _create_quote_after_confirm(auth_client)
        _reconfirm_litere_ignore(auth_client, workspace_id)
        response = auth_client.get(
            f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["layer_role_confirmation_effective_source"] == "workspace_live"
        assert payload["layer_role_confirmation_snapshot_stale"] is True
        warning_codes = {item["code"] for item in payload["warnings"]}
        assert "quote_layer_role_snapshot_stale" in warning_codes
        assert payload["includes_operations_cost"] is False
        assert payload["includes_labor_cost"] is False

    @pytest.mark.asyncio
    async def test_path_perimeter_uses_effective_source(self, auth_client):
        workspace_id, quote_id = _create_quote_after_confirm(auth_client)
        _reconfirm_litere_ignore(auth_client, workspace_id)
        response = auth_client.get(
            f"/api/v1/intake-v3/quotes/{quote_id}/geometry-path-perimeter-classification",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["layer_role_confirmation_effective_source"] == "workspace_live"
        assert payload["layer_role_confirmation_snapshot_stale"] is True
        classification = payload["path_perimeter_classification"]
        assert classification is not None

    @pytest.mark.asyncio
    async def test_production_readiness_exposes_stale_status(self, auth_client):
        workspace_id, quote_id = _create_quote_after_confirm(auth_client)
        _reconfirm_litere_ignore(auth_client, workspace_id)
        response = auth_client.get(
            f"/api/v1/intake-v3/quotes/{quote_id}/order-production-readiness",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        available = payload["available_data"]
        assert available["layer_role_confirmation_snapshot_stale"] is True
        assert available["layer_role_confirmation_effective_source"] == "workspace_live"
        assert "quote_layer_role_snapshot_stale" in payload["warnings"]

    @pytest.mark.asyncio
    async def test_task_dry_run_exposes_stale_status(self, auth_client):
        workspace_id, quote_id = _create_quote_after_confirm(auth_client)
        _reconfirm_litere_ignore(auth_client, workspace_id)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/production-task-dry-run")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["layer_role_confirmation_snapshot_stale"] is True
        assert payload["downstream_uses_effective_source"] is True
        assert payload["creates_execution_tasks"] is False
        assert payload["would_create_execution_tasks"] is False


class TestPropagationRefresh:
    @pytest.mark.asyncio
    async def test_refresh_updates_technical_snapshot_only(self, auth_client, db_session):
        workspace_id, quote_id = _create_quote_after_confirm(auth_client)
        quote_before = await db_session.get(Quotes, quote_id)
        status_before = quote_before.status
        subtotal_before = float(quote_before.subtotal or 0)
        total_before = float(quote_before.grand_total or 0)
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))

        _reconfirm_litere_ignore(auth_client, workspace_id)

        refresh = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/layer-role-confirmation/refresh-technical-snapshot",
        )
        assert refresh.status_code == 200, refresh.text
        refresh_payload = refresh.json()
        assert refresh_payload["is_snapshot_stale"] is False
        assert refresh_payload["modifies_quote_status"] is False
        assert refresh_payload["modifies_quote_pricing"] is False
        assert refresh_payload["creates_execution_tasks"] is False
        assert refresh_payload["mutates_inventory"] is False

        quote_after = await db_session.get(Quotes, quote_id)
        await db_session.refresh(quote_after)
        assert quote_after.status == status_before
        assert float(quote_after.subtotal or 0) == subtotal_before
        assert float(quote_after.grand_total or 0) == total_before

        linkage = parse_intake_v3_linkage_from_notes(quote_after.notes)
        sections = linkage["snapshot"]["sections"]
        litere_layers = [
            layer
            for layer in sections["layer_role_confirmation_snapshot"]["layers"]
            if layer["layer_key"] == "LITERE"
        ]
        assert litere_layers[0]["confirmed_role"] == "ignore"

        propagation = auth_client.get(
            f"/api/v1/intake-v3/quotes/{quote_id}/layer-role-confirmation/propagation",
        )
        assert propagation.json()["is_snapshot_stale"] is False

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        assert plans_after == plans_before
        assert movements_after == movements_before

    @pytest.mark.asyncio
    async def test_refresh_blocked_for_accepted_quote(self, auth_client):
        order_id, quote_id, _, workspace_id = _prepare_converted_iv3_order(auth_client)
        _upload_svg(auth_client, workspace_id, "layers.svg", LAYERED_SVG)
        _confirm_layers(auth_client, workspace_id)
        response = auth_client.post(
            f"/api/v1/intake-v3/quotes/{quote_id}/layer-role-confirmation/refresh-technical-snapshot",
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] in {
            "accepted_quote_refresh_blocked",
            "converted_quote_refresh_blocked",
        }
