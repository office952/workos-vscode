"""Intake V3 read-only material availability preview tests."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.quotes import Quotes
from models.stock_movements import StockMovement
from services.intake_v3_material_availability_service import (
    compare_required_vs_available,
    match_breakdown_material_to_inventory,
    normalize_material_unit,
)
from tests.test_intake_v3_material_quantity_breakdown import _inject_geometry_metrics_async
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


async def _seed_materials(db_session, rows: list[dict]) -> None:
    for row in rows:
        existing = await db_session.scalar(
            select(Inventory_materials).where(Inventory_materials.code == row["code"])
        )
        if existing is not None:
            for key, value in row.items():
                setattr(existing, key, value)
        else:
            db_session.add(Inventory_materials(**row))
    await db_session.commit()


class TestMaterialAvailabilityUnitHelpers:
    def test_normalize_material_unit_aliases(self):
        assert normalize_material_unit("mp") == "m2"
        assert normalize_material_unit("buc") == "buc"
        assert normalize_material_unit("placa") == "placa"

    def test_compare_incompatible_units_manual_check(self):
        material = Inventory_materials(
            code="MAT-TEST-BUC",
            name="Test buc material",
            unit="buc",
            stock_current=100.0,
            status="active",
        )
        available, shortage, comparison, _ = compare_required_vs_available(5.0, "m2", material)
        assert available is None
        assert shortage is None
        assert comparison == "incompatible"

    def test_ambiguous_match(self):
        candidates = [
            Inventory_materials(code="A", name="Same Name", unit="m2", stock_current=1.0),
            Inventory_materials(code="B", name="Same Name", unit="m2", stock_current=2.0),
        ]
        _, match, warnings = match_breakdown_material_to_inventory(
            registry_code=None,
            display_name="Same Name",
            candidates=candidates,
        )
        assert match.match_strategy == "ambiguous"
        assert "ambiguous_inventory_match" in warnings


class TestMaterialAvailabilitySafeResponses:
    @pytest.mark.asyncio
    async def test_missing_order_returns_not_found(self, auth_client, db_session):
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))

        response = auth_client.get("/api/v1/intake-v3/orders/999999/material-availability")
        assert response.status_code == 404

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        assert plans_after == plans_before
        assert movements_after == movements_before

    @pytest.mark.asyncio
    async def test_non_iv3_order_returns_non_iv3_response(self, auth_client, db_session):
        order = Orders(
            code="ORD-NORMAL-MA",
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

        response = auth_client.get(f"/api/v1/intake-v3/orders/{order.id}/material-availability")
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3"] is False
        assert payload["boundary"]["read_only"] is True
        assert payload["boundary"]["mutates_inventory"] is False
        assert payload["boundary"]["costengine_used"] is False


class TestMaterialAvailabilityMatching:
    @pytest.mark.asyncio
    async def test_exact_code_match_available(self, auth_client, db_session):
        workspace_id, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _seed_materials(
            db_session,
            [
                {
                    "code": "MAT-ACP-FATA-LITERE",
                    "name": "ACP fata litere",
                    "unit": "m2",
                    "stock_current": 9999.0,
                    "status": "active",
                }
            ],
        )
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/material-availability",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        face = next(row for row in payload["rows"] if row["material_key"] == "plexiglas_face")
        assert face["match"]["match_strategy"] == "code"
        assert face["match"]["confidence"] == "high"
        assert face["availability_status"] == "available"
        assert payload["boundary"]["reserves_inventory"] is False

    @pytest.mark.asyncio
    async def test_exact_code_match_shortage(self, auth_client, db_session):
        workspace_id, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(db_session, quote_id, {"letter_face_area_m2": 2.5})
        await _seed_materials(
            db_session,
            [
                {
                    "code": "MAT-ACP-FATA-LITERE",
                    "name": "ACP fata litere",
                    "unit": "m2",
                    "stock_current": 0.0,
                    "status": "active",
                }
            ],
        )
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/material-availability",
        )
        payload = response.json()
        face = next(row for row in payload["rows"] if row["material_key"] == "plexiglas_face")
        assert face["availability_status"] == "shortage"
        assert face["quantity"]["shortage"] is not None
        assert face["quantity"]["shortage"] > 0

    @pytest.mark.asyncio
    async def test_no_match_manual_check(self, auth_client):
        workspace_id, _, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/material-availability",
        )
        payload = response.json()
        face = next(row for row in payload["rows"] if row["material_key"] == "plexiglas_face")
        assert face["availability_status"] in {"no_match", "manual_check", "shortage", "available"}
        if face["match"]["match_strategy"] == "none":
            assert face["availability_status"] == "no_match"

    @pytest.mark.asyncio
    async def test_indirect_consumable_policy_rows(self, auth_client):
        workspace_id, _, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/material-availability",
        )
        payload = response.json()
        indirect = [row for row in payload["rows"] if row["tracking_class"] == "indirect_consumable"]
        assert len(indirect) >= 4
        assert all(row["availability_status"] == "indirect_consumable" for row in indirect)

    @pytest.mark.asyncio
    async def test_led_module_shortage(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(db_session, quote_id, {"led_module_count": 120})
        await _seed_materials(
            db_session,
            [
                {
                    "code": "MAT-LED-MODULE",
                    "name": "LED module",
                    "unit": "buc",
                    "stock_current": 0.0,
                    "status": "active",
                }
            ],
        )
        response = auth_client.get(
            f"/api/v1/intake-v3/quotes/{quote_id}/material-availability",
        )
        payload = response.json()
        led = next(row for row in payload["rows"] if row["material_key"] == "led_modules")
        assert led["quantity"]["required_unit"] == "buc"
        assert led["availability_status"] == "shortage"

    @pytest.mark.asyncio
    async def test_endpoint_by_quote(self, auth_client, db_session):
        _, quote_id, _ = _create_iv3_draft_quote(auth_client)
        await _seed_materials(
            db_session,
            [
                {
                    "code": "MAT-ORACAL-651",
                    "name": "Oracal 651",
                    "unit": "m2",
                    "stock_current": 50.0,
                    "status": "active",
                }
            ],
        )
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-availability")
        assert response.status_code == 200
        assert response.json()["quote_id"] == quote_id

    @pytest.mark.asyncio
    async def test_endpoint_by_order(self, auth_client, db_session):
        workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        _accept_iv3_quote(auth_client, quote_id, intake_code)
        order_payload = _convert_iv3_quote(auth_client, quote_id, intake_code)
        await _seed_materials(
            db_session,
            [
                {
                    "code": "MAT-SPATE-PVC-LITERE",
                    "name": "Forex spate",
                    "unit": "m2",
                    "stock_current": 20.0,
                    "status": "active",
                }
            ],
        )
        response = auth_client.get(
            f"/api/v1/intake-v3/orders/{order_payload['order_id']}/material-availability",
        )
        assert response.status_code == 200
        assert response.json()["order_id"] == order_payload["order_id"]


class TestMaterialAvailabilityIntegrations:
    @pytest.mark.asyncio
    async def test_production_readiness_consumes_availability(self, auth_client, db_session):
        workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(db_session, quote_id, {"letter_face_area_m2": 2.5})
        _complete_pricing(auth_client, quote_id, intake_code)
        _accept_iv3_quote(auth_client, quote_id, intake_code)
        order_payload = _convert_iv3_quote(auth_client, quote_id, intake_code)
        await _seed_materials(
            db_session,
            [
                {
                    "code": "MAT-ACP-FATA-LITERE",
                    "name": "ACP fata litere",
                    "unit": "m2",
                    "stock_current": 0.0,
                    "status": "active",
                }
            ],
        )
        response = auth_client.get(
            f"/api/v1/intake-v3/orders/{order_payload['order_id']}/production-readiness",
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["available_data"]["material_availability_available"] is True
        assert payload["available_data"]["material_shortage_rows_count"] >= 1
        assert "material_shortage_detected" in payload["warnings"]

    @pytest.mark.asyncio
    async def test_production_task_dry_run_consumes_availability(self, auth_client, db_session):
        workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        await _inject_geometry_metrics_async(db_session, quote_id, {"letter_face_area_m2": 2.5})
        _complete_pricing(auth_client, quote_id, intake_code)
        _accept_iv3_quote(auth_client, quote_id, intake_code)
        order_payload = _convert_iv3_quote(auth_client, quote_id, intake_code)
        await _seed_materials(
            db_session,
            [
                {
                    "code": "MAT-ACP-FATA-LITERE",
                    "name": "ACP fata litere",
                    "unit": "m2",
                    "stock_current": 0.0,
                    "status": "active",
                }
            ],
        )
        response = auth_client.get(
            f"/api/v1/intake-v3/orders/{order_payload['order_id']}/production-task-dry-run",
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["material_availability_available"] is True
        assert payload["material_shortage_rows_count"] >= 1
        warning_codes = [item["code"] for item in payload["warnings"]]
        assert "material_shortage_detected" in warning_codes


class TestMaterialAvailabilityNoSideEffects:
    @pytest.mark.asyncio
    async def test_no_inventory_or_workflow_side_effects(self, auth_client, db_session):
        workspace_id, quote_id, intake_code = _create_iv3_draft_quote(auth_client)
        _complete_pricing(auth_client, quote_id, intake_code)
        quote_before = await db_session.get(Quotes, quote_id)
        assert quote_before is not None
        quote_status_before = quote_before.status
        quote_total_before = quote_before.grand_total

        inventory_before = await db_session.scalar(select(func.count()).select_from(Inventory_materials))
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/material-availability",
        )
        assert response.status_code == 200

        quote_after = await db_session.get(Quotes, quote_id)
        assert quote_after is not None
        assert quote_after.status == quote_status_before
        assert quote_after.grand_total == quote_total_before

        inventory_after = await db_session.scalar(select(func.count()).select_from(Inventory_materials))
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))

        assert inventory_after == inventory_before
        assert movements_after == movements_before
        assert plans_after == plans_before
