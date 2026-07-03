"""Intake V3 geometry metrics snapshot — persistence and consumer integration tests."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from models.stock_movements import StockMovement
from schemas.intake_v3 import GEOMETRY_METRICS_SNAPSHOT_VERSION
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


class TestGeometryMetricsSafeResponses:
    @pytest.mark.asyncio
    async def test_missing_workspace_returns_not_found(self, auth_client, db_session):
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        response = auth_client.get("/api/v1/intake-v3/workspaces/999999/geometry-metrics-snapshot")
        assert response.status_code == 404
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_missing_quote_returns_not_found(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/quotes/999999/geometry-metrics-snapshot")
        assert response.status_code == 404


class TestGeometryMetricsNonIv3:
    @pytest.mark.asyncio
    async def test_non_iv3_order_safe_response(self, auth_client, db_session):
        order = Orders(
            code="ORD-NON-IV3-GEO",
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

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order.id}/geometry-metrics-snapshot")
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3"] is False
        assert payload["creates_execution_tasks"] is False
        assert payload["mutates_inventory"] is False
        assert payload["costengine_used"] is False


class TestGeometryMetricsHubCounts:
    @pytest.mark.asyncio
    async def test_hub_fixture_counts(self, auth_client):
        workspace_id, _, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-metrics-snapshot",
        )
        assert response.status_code == 200, response.text
        snapshot = response.json()["snapshot"]
        assert snapshot is not None
        assert snapshot["schema_version"] == GEOMETRY_METRICS_SNAPSHOT_VERSION
        assert snapshot["counts"]["real_letter_count"] == 18
        assert snapshot["counts"]["cut_contour_count"] == 27
        assert snapshot["counts"]["inner_hole_count"] == 9
        assert snapshot["holes_not_letters"] is True
        assert snapshot["counts"]["real_letter_count"] != snapshot["counts"]["inner_hole_count"]


class TestGeometryMetricsPersistence:
    @pytest.mark.asyncio
    async def test_snapshot_persisted_in_quote_linkage(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/geometry-metrics-snapshot")
        assert response.status_code == 200
        assert response.json()["snapshot"]["schema_version"] == GEOMETRY_METRICS_SNAPSHOT_VERSION
        quote = await db_session.get(Quotes, quote_id)
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        sections = linkage.get("snapshot", {}).get("sections", {})
        assert "geometry_metrics_snapshot" in sections


class TestGeometryMetricsPerimetersNotInvented:
    @pytest.mark.asyncio
    async def test_perimeters_missing_with_warning(self, auth_client):
        workspace_id, _, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-metrics-snapshot",
        )
        snapshot = response.json()["snapshot"]
        assert snapshot["perimeters"]["face_cutting_perimeter_ml"] is None
        assert snapshot["perimeters"]["return_material_perimeter_ml"] is None
        assert snapshot["perimeters"]["bevel_perimeter_ml"] is None
        codes = [item["code"] for item in snapshot["warnings"]]
        assert "perimeter_missing" in codes
        assert snapshot["confidence"] in {"partial", "medium", "low"}


class TestGeometryMetricsEstimatedArea:
    @pytest.mark.asyncio
    async def test_area_estimated_from_dimensions(self, auth_client):
        workspace_id, _, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-metrics-snapshot",
        )
        snapshot = response.json()["snapshot"]
        assert snapshot["dimensions"]["width_mm"] == pytest.approx(9250.0)
        assert snapshot["dimensions"]["height_mm"] == pytest.approx(550.0)
        assert snapshot["areas"]["estimated_area_m2"] == pytest.approx(5.0875, rel=1e-3)
        assert snapshot["dimensions"]["bounding_box_source"] == "confirmed_dimensions"


class TestGeometryMetricsConsumers:
    @pytest.mark.asyncio
    async def test_material_breakdown_uses_geometry_snapshot(self, auth_client):
        workspace_id, quote_id, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        assert response.status_code == 200
        geometry = response.json()["geometry_summary"]
        assert geometry["real_letters_count"] == 18
        assert geometry["source"] in {"geometry_metrics_snapshot", "confirmed_production_model_snapshot"}

    @pytest.mark.asyncio
    async def test_production_readiness_sees_geometry_status(self, auth_client):
        order_id, _, _, _ = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        assert response.status_code == 200
        data = response.json()["available_data"]
        assert data["geometry_snapshot_available"] is True
        assert data["geometry_status"] in {"geometry_partial", "geometry_complete", "geometry_missing"}

    @pytest.mark.asyncio
    async def test_task_dry_run_consumes_geometry_snapshot(self, auth_client):
        order_id, _, _, _ = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-task-dry-run")
        assert response.status_code == 200
        payload = response.json()
        assert payload["creates_execution_tasks"] is False
        assert all(task["will_create_real_task"] is False for task in payload["candidate_tasks"])


class TestGeometryMetricsNoSideEffects:
    @pytest.mark.asyncio
    async def test_no_execution_inventory_or_status_mutations(self, auth_client, db_session):
        order_id, quote_id, _, workspace_id = _prepare_converted_iv3_order(auth_client)
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))
        order_before = await db_session.get(Orders, order_id)
        quote_before = await db_session.get(Quotes, quote_id)
        order_status = order_before.status
        quote_status = quote_before.status

        endpoints = [
            f"/api/v1/intake-v3/orders/{order_id}/geometry-metrics-snapshot",
            f"/api/v1/intake-v3/quotes/{quote_id}/geometry-metrics-snapshot",
            f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-metrics-snapshot",
        ]
        for url in endpoints:
            response = auth_client.get(url)
            assert response.status_code == 200, response.text

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        order_after = await db_session.get(Orders, order_id)
        quote_after = await db_session.get(Quotes, quote_id)
        assert plans_after == plans_before
        assert movements_after == movements_before
        assert order_after.status == order_status
        assert quote_after.status == quote_status

    @pytest.mark.asyncio
    async def test_quote_linkage_contains_geometry_snapshot_after_draft_quote(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        quote = await db_session.get(Quotes, quote_id)
        linkage = parse_intake_v3_linkage_from_notes(quote.notes)
        sections = linkage.get("snapshot", {}).get("sections", {})
        assert "geometry_metrics_snapshot" in sections
        assert sections["geometry_metrics_snapshot"]["schema_version"] == GEOMETRY_METRICS_SNAPSHOT_VERSION
