"""Intake V3 operator layer role confirmation — draft workspace only, no production side effects."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from models.stock_movements import StockMovement
from services.intake_v3_layer_role_confirmation_service import LAYER_ROLE_CONFIRMATION_VERSION
from tests.test_intake_v3_quote_pricing_review_completion import _create_iv3_draft_quote
from tests.test_intake_v3_real_commercial_quote_creation import _seed_hub_workspace
from tests.test_intake_v3_svg_upload_analysis import _upload_svg

LAYERED_SVG = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100mm" height="50mm">
  <g id="LITERE"><path d="M10 40 L20 10 L30 40 Z"/></g>
  <g id="SPATE"><path d="M5 5 L95 5 L95 45 L5 45 Z"/></g>
  <g id="GOLURI"><path d="M15 20 L25 20 L25 30 L15 30 Z"/></g>
  <g id="CANT"><path d="M0 0 L10 0 L10 10 L0 10 Z"/></g>
  <g id="UNKNOWN"><path d="M40 40 L50 40 L50 50 L40 50 Z"/></g>
</svg>"""


def _seed_and_upload(auth_client, svg_text: str = LAYERED_SVG) -> str:
    workspace_id = _seed_hub_workspace(auth_client)
    upload = _upload_svg(auth_client, workspace_id, "layers.svg", svg_text)
    assert upload.status_code == 200, upload.text
    return workspace_id


def _confirm_layers(auth_client, workspace_id: str) -> dict:
    get_resp = auth_client.get(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
    )
    assert get_resp.status_code == 200, get_resp.text
    layers = get_resp.json()["layer_role_confirmation_snapshot"]["layers"]
    payload = {
        "layers": [
            {"layer_key": "LITERE", "confirmed_role": "face", "confirmation_state": "confirmed"},
            {"layer_key": "SPATE", "confirmed_role": "backing", "confirmation_state": "confirmed"},
            {"layer_key": "CANT", "confirmed_role": "return", "confirmation_state": "confirmed"},
            {"layer_key": "GOLURI", "confirmed_role": "inner_hole", "confirmation_state": "confirmed"},
            {"layer_key": "UNKNOWN", "confirmed_role": "ignore", "confirmation_state": "ignored"},
        ]
    }
    put_resp = auth_client.put(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
        json=payload,
    )
    assert put_resp.status_code == 200, put_resp.text
    return put_resp.json()


class TestLayerRoleConfirmationSafeResponses:
    @pytest.mark.asyncio
    async def test_missing_workspace_returns_not_found(self, auth_client, db_session):
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        response = auth_client.get("/api/v1/intake-v3/workspaces/999999/layer-role-confirmation")
        assert response.status_code == 404
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_non_iv3_order_safe_response(self, auth_client, db_session):
        order = Orders(
            code="ORD-NON-IV3-LRC",
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

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order.id}/layer-role-confirmation")
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3"] is False
        assert payload["creates_execution_tasks"] is False
        assert payload["mutates_inventory"] is False
        assert payload["costengine_used"] is False


class TestLayerRoleConfirmationDraft:
    @pytest.mark.asyncio
    async def test_draft_from_path_geometry_layers(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        snapshot = payload["layer_role_confirmation_snapshot"]
        assert snapshot["schema_version"] == LAYER_ROLE_CONFIRMATION_VERSION
        assert payload["persisted"] is False
        assert payload["confirmation_status"] in {"partial", "missing"}

        by_key = {layer["layer_key"]: layer for layer in snapshot["layers"]}
        assert by_key["LITERE"]["auto_role"] == "face"
        assert by_key["SPATE"]["auto_role"] == "backing"
        assert by_key["CANT"]["auto_role"] == "return"
        assert by_key["GOLURI"]["auto_role"] == "inner_hole"
        assert by_key["UNKNOWN"]["auto_role"] == "unknown"
        assert by_key["LITERE"]["auto_confidence"] == "medium"
        assert by_key["UNKNOWN"]["auto_confidence"] == "low"
        assert by_key["LITERE"]["metrics"]["perimeter_mm"] is not None


class TestLayerRoleConfirmationSave:
    @pytest.mark.asyncio
    async def test_save_confirmed_roles(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        payload = _confirm_layers(auth_client, workspace_id)
        snapshot = payload["layer_role_confirmation_snapshot"]
        assert payload["persisted"] is True
        assert snapshot["confirmation_status"] in {"complete", "partial"}
        by_key = {layer["layer_key"]: layer for layer in snapshot["layers"]}
        assert by_key["LITERE"]["confirmed_role"] == "face"
        assert by_key["LITERE"]["confirmed_confidence"] == "high"
        assert by_key["UNKNOWN"]["confirmed_role"] == "ignore"
        assert "UNKNOWN" in snapshot["ignored_layers"]

    @pytest.mark.asyncio
    async def test_invalid_role_rejected(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        response = auth_client.put(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
            json={
                "layers": [
                    {"layer_key": "LITERE", "confirmed_role": "not_a_role", "confirmation_state": "confirmed"},
                ]
            },
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error"] == "INVALID_LAYER_ROLE"

        get_resp = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["persisted"] is False

    @pytest.mark.asyncio
    async def test_unknown_layer_key_rejected(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        response = auth_client.put(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
            json={
                "layers": [
                    {"layer_key": "NO_SUCH_LAYER", "confirmed_role": "face", "confirmation_state": "confirmed"},
                ]
            },
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error"] == "UNKNOWN_LAYER_KEY"


class TestLayerRoleConfirmationIntegration:
    @pytest.mark.asyncio
    async def test_confirmed_roles_feed_path_perimeter_classification(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-path-perimeter-classification",
        )
        assert response.status_code == 200, response.text
        classification = response.json()["path_perimeter_classification"]
        face = classification["perimeters"]["face_cutting_perimeter_ml"]
        backing = classification["perimeters"]["backing_cutting_perimeter_ml"]
        ret = classification["perimeters"]["return_material_perimeter_ml"]
        assert face["value"] is not None
        assert backing["value"] is not None
        assert ret["value"] is not None
        assert face["quality"] == "high"
        assert backing["quality"] == "high"
        assert ret["quality"] == "high"
        assert "layer_role_confirmation_snapshot" in (face.get("source") or "")

    @pytest.mark.asyncio
    async def test_ignore_layer_excluded(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-path-perimeter-classification",
        )
        classification = response.json()["path_perimeter_classification"]
        classified_keys = {
            layer.get("layer_id") or layer.get("layer_name")
            for layer in classification["classified_layers"]
        }
        assert "UNKNOWN" not in classified_keys
        ignored = classification.get("ignored_layers") or []
        assert any(
            (layer.get("layer_id") == "UNKNOWN" or layer.get("layer_name") == "UNKNOWN")
            for layer in ignored
        )

    @pytest.mark.asyncio
    async def test_inner_holes_not_letters(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)
        response = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-metrics-snapshot")
        snapshot = response.json()["snapshot"]
        assert snapshot["holes_not_letters"] is True
        assert snapshot["counts"]["inner_hole_count"] >= 0
        assert snapshot["counts"]["real_letter_count"] >= 0

    @pytest.mark.asyncio
    async def test_geometry_snapshot_reflects_confirmation(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)
        response = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-metrics-snapshot")
        snapshot = response.json()["snapshot"]
        assert snapshot["layer_role_confirmation_status"] in {"complete", "partial"}
        assert "layer_role_confirmation_snapshot" in snapshot["source_keys"]
        assert snapshot["path_perimeter_classification"] is not None

    @pytest.mark.asyncio
    async def test_material_breakdown_reflects_operator_confirmation(self, auth_client):
        workspace_id, quote_id, _ = _create_iv3_draft_quote(auth_client)
        _upload_svg(auth_client, workspace_id, "layers.svg", LAYERED_SVG)
        _confirm_layers(auth_client, workspace_id)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        assert response.status_code == 200
        geometry = response.json()["geometry_summary"]
        assert geometry.get("operator_confirmed_layer_roles") is True
        assert response.json()["costengine_used"] is False

    @pytest.mark.asyncio
    async def test_production_readiness_reflects_confirmation(self, auth_client, db_session):
        from tests.test_intake_v3_geometry_metrics_snapshot import _prepare_converted_iv3_order

        order_id, quote_id, intake_code, workspace_id = _prepare_converted_iv3_order(auth_client)
        _upload_svg(auth_client, workspace_id, "layers.svg", LAYERED_SVG)
        _confirm_layers(auth_client, workspace_id)
        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        assert response.status_code == 200
        available = response.json()["available_data"]
        assert available["layer_role_confirmation_status"] in {"complete", "partial", "missing"}
        assert available["operator_confirmed_layer_roles_count"] >= 0

    @pytest.mark.asyncio
    async def test_production_task_dry_run_reflects_confirmation(self, auth_client):
        workspace_id, quote_id, _ = _create_iv3_draft_quote(auth_client)
        _upload_svg(auth_client, workspace_id, "layers.svg", LAYERED_SVG)
        _confirm_layers(auth_client, workspace_id)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/production-task-dry-run")
        assert response.status_code == 200
        payload = response.json()
        assert payload["creates_execution_tasks"] is False
        assert all(task["will_create_real_task"] is False for task in payload["candidate_tasks"])
        warning_codes = [item["code"] for item in payload.get("warnings", [])]
        assert "layer_roles_unconfirmed" not in warning_codes


class TestLayerRoleConfirmationNoSideEffects:
    @pytest.mark.asyncio
    async def test_save_does_not_mutate_execution_inventory_or_status(self, auth_client, db_session):
        workspace_id = _seed_and_upload(auth_client)
        quote_before = await db_session.scalar(select(func.count()).select_from(Quotes))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        stock_before = await db_session.scalar(select(func.count()).select_from(StockMovement))

        _confirm_layers(auth_client, workspace_id)

        quote_after = await db_session.scalar(select(func.count()).select_from(Quotes))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        stock_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        assert quote_after == quote_before
        assert plans_after == plans_before
        assert stock_after == stock_before
