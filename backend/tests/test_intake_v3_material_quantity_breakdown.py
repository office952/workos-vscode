"""Intake V3 material quantity / geometry / material cost breakdown — read-only tests."""

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


def _prepare_converted_iv3_order(auth_client) -> tuple[int, int, str, str]:
    workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
    _complete_pricing(auth_client, quote_id, intake_code)
    _accept_iv3_quote(auth_client, quote_id, intake_code)
    payload = _convert_iv3_quote(auth_client, quote_id, intake_code)
    return payload["order_id"], quote_id, intake_code, workspace_id


async def _inject_geometry_metrics_async(db_session, quote_id: int, metrics: dict) -> None:
    quote = await db_session.get(Quotes, quote_id)
    assert quote is not None
    linkage = parse_intake_v3_linkage_from_notes(quote.notes)
    assert linkage is not None
    snapshot = linkage.setdefault("snapshot", {})
    sections = snapshot.setdefault("sections", {})
    sections["geometry_metrics_snapshot"] = metrics
    notes_payload = json.loads(quote.notes)
    notes_payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
    quote.notes = json.dumps(notes_payload)
    await db_session.commit()


class TestMaterialBreakdownSafeResponses:
    @pytest.mark.asyncio
    async def test_missing_order_returns_not_found(self, auth_client, db_session):
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))

        response = auth_client.get("/api/v1/intake-v3/orders/999999/material-breakdown")
        assert response.status_code == 404

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        assert plans_after == plans_before
        assert movements_after == movements_before

    @pytest.mark.asyncio
    async def test_missing_quote_returns_not_found(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/quotes/999999/material-breakdown")
        assert response.status_code == 404


class TestMaterialBreakdownNonIv3:
    @pytest.mark.asyncio
    async def test_non_iv3_order_returns_non_iv3_response(self, auth_client, db_session):
        order = Orders(
            code="ORD-NORMAL-MB",
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

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order.id}/material-breakdown")
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3"] is False
        assert payload["costengine_used"] is False
        assert payload["inventory_mutation_allowed"] is False
        assert payload["includes_operations_cost"] is False
        assert payload["includes_labor_cost"] is False


class TestMaterialBreakdownHubGeometry:
    @pytest.mark.asyncio
    async def test_hub_workspace_geometry_counts(self, auth_client):
        workspace_id, quote_id, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/material-breakdown",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        geometry = payload["geometry_summary"]
        assert geometry["real_letters_count"] == 18
        assert geometry["closed_contours_count"] == 27
        assert geometry["holes_count"] == 9
        assert geometry["real_letters_count"] != geometry["holes_count"]

    @pytest.mark.asyncio
    async def test_perimeters_read_from_snapshot_when_present(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(
            db_session,
            quote_id,
            {
                "letter_perimeter_m": 47.235,
                "return_material_perimeter_ml": 47.235,
                "cut_perimeter_m": 52.0,
                "bevel_perimeter_m": 10.0,
                "letter_face_area_m2": 3.181,
                "backing_area_m2": 3.181,
                "vinyl_area_m2": 3.181,
            },
        )
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        assert response.status_code == 200, response.text
        geometry = response.json()["geometry_summary"]
        assert geometry["total_letter_perimeter_ml"] == pytest.approx(47.235)
        assert geometry["return_material_perimeter_ml"] == pytest.approx(47.235)
        assert geometry["cutting_perimeter_ml"] == pytest.approx(52.0)
        assert geometry["bevel_perimeter_ml"] == pytest.approx(10.0)

    @pytest.mark.asyncio
    async def test_missing_perimeters_return_warnings(self, auth_client):
        workspace_id, _, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/material-breakdown",
        )
        assert response.status_code == 200
        codes = [item["code"] for item in response.json()["warnings"]]
        assert "missing_geometry_perimeters" in codes
        aluminum = next(
            row for row in response.json()["material_rows"] if row["material_key"] == "aluminum_return"
        )
        assert aluminum["quantity_quality"] == "missing"


class TestMaterialBreakdownQuantityRows:
    @pytest.mark.asyncio
    async def test_plexiglas_quantity_row(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(
            db_session,
            quote_id,
            {"letter_face_area_m2": 2.5},
        )
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        row = next(r for r in response.json()["material_rows"] if r["material_key"] == "plexiglas_face")
        assert row["unit"] == "m2"
        assert row["quantity_source"] == "face_area_m2"
        assert row["quantity"] == pytest.approx(2.5)
        assert row["waste_percent"] == 20.0
        assert row["quantity_with_waste"] == pytest.approx(3.0)

    @pytest.mark.asyncio
    async def test_forex_backing_quantity_row(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(
            db_session,
            quote_id,
            {"backing_area_m2": 1.25},
        )
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        row = next(r for r in response.json()["material_rows"] if r["material_key"] == "forex_backing")
        assert row["unit"] == "m2"
        assert row["quantity_source"] == "backing_area_m2"

    @pytest.mark.asyncio
    async def test_vinyl_row_included_for_hub_finish(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(
            db_session,
            quote_id,
            {"vinyl_area_m2": 1.0},
        )
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        row = next(r for r in response.json()["material_rows"] if r["material_key"] == "face_vinyl")
        assert row["included"] is True

    @pytest.mark.asyncio
    async def test_aluminum_return_uses_return_perimeter(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(
            db_session,
            quote_id,
            {"return_material_perimeter_ml": 12.5},
        )
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        row = next(r for r in response.json()["material_rows"] if r["material_key"] == "aluminum_return")
        assert row["unit"] == "ml"
        assert row["quantity"] == pytest.approx(12.5)
        assert row["quantity_with_waste"] == pytest.approx(15.0)

    @pytest.mark.asyncio
    async def test_led_rows_from_snapshot_or_warning(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        codes = [item["code"] for item in response.json()["warnings"]]
        assert "missing_led_count" in codes

        await _inject_geometry_metrics_async(
            db_session,
            quote_id,
            {"led_module_count": 120, "psu_count": 2},
        )
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        led = next(r for r in response.json()["material_rows"] if r["material_key"] == "led_modules")
        psu = next(r for r in response.json()["material_rows"] if r["material_key"] == "led_power_supply")
        assert led["quantity"] == pytest.approx(120.0)
        assert psu["quantity"] == pytest.approx(2.0)


class TestMaterialBreakdownCosts:
    @pytest.mark.asyncio
    async def test_cost_rows_use_fallback_and_compute(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(
            db_session,
            quote_id,
            {
                "letter_face_area_m2": 1.0,
                "backing_area_m2": 1.0,
                "return_material_perimeter_ml": 10.0,
            },
        )
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        payload = response.json()
        plexi_cost = next(r for r in payload["cost_rows"] if r["material_key"] == "plexiglas_face")
        assert plexi_cost["price_source"] in {"owner_confirmed_fallback", "pricing_registry", "material_registry"}
        assert plexi_cost["unit_price"] is not None
        assert plexi_cost["material_cost"] == pytest.approx(plexi_cost["quantity_with_waste"] * plexi_cost["unit_price"])

    @pytest.mark.asyncio
    async def test_missing_price_does_not_crash(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(
            db_session,
            quote_id,
            {"letter_face_area_m2": 1.0},
        )
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_totals_exclude_operations_labor_markup_profit(self, auth_client):
        workspace_id, _, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/material-breakdown",
        )
        payload = response.json()
        assert payload["includes_operations_cost"] is False
        assert payload["includes_labor_cost"] is False
        assert payload["includes_markup"] is False
        assert payload["includes_profit"] is False
        assert payload["breakdown_scope"] == "materials_only_informative"
        keys = {row["material_key"] for row in payload["cost_rows"]}
        assert "labor" not in keys
        assert "operations" not in keys


class TestMaterialBreakdownNoSideEffects:
    @pytest.mark.asyncio
    async def test_no_execution_inventory_side_effects(self, auth_client, db_session):
        order_id, quote_id, _, _ = _prepare_converted_iv3_order(auth_client)
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/material-breakdown")
        assert response.status_code == 200, response.text
        assert response.json()["is_intake_v3"] is True

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        assert plans_after == plans_before
        assert movements_after == movements_before

    @pytest.mark.asyncio
    async def test_order_endpoint_after_guarded_convert(self, auth_client, db_session):
        order_id, quote_id, intake_code, workspace_id = _prepare_converted_iv3_order(auth_client)
        order_response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/material-breakdown")
        quote_response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        workspace_response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/material-breakdown",
        )
        assert order_response.status_code == 200
        assert quote_response.status_code == 200
        assert workspace_response.status_code == 200
        assert order_response.json()["geometry_summary"]["real_letters_count"] == 18
        assert order_response.json()["quote_id"] == quote_id
        assert order_response.json()["order_id"] == order_id
        assert intake_code.startswith("IV3-")
