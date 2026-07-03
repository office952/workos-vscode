"""Intake V3 read-only procurement preview tests."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.quotes import Quotes
from models.stock_movements import StockMovement
from services.intake_v3_procurement_preview_service import classify_procurement_decision
from schemas.intake_v3 import IntakeV3MaterialAvailabilityMatch, IntakeV3MaterialAvailabilityQuantity, IntakeV3MaterialAvailabilityRow, IntakeV3ProcurementSourceHint
from tests.test_intake_v3_guarded_convert_to_order import (
    _accept_iv3_quote,
    _complete_pricing,
    _create_iv3_draft_quote,
    _valid_convert_request,
)
from tests.test_intake_v3_material_quantity_breakdown import _inject_geometry_metrics_async


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


def _availability_row(
    material_key: str,
    *,
    availability_status: str,
    tracking_class: str = "stock_tracked",
    shortage: float | None = None,
    registry_code: str | None = None,
) -> IntakeV3MaterialAvailabilityRow:
    return IntakeV3MaterialAvailabilityRow(
        material_key=material_key,
        display_name=material_key,
        category="sheet",
        registry_code=registry_code,
        material_intent=material_key,
        tracking_class=tracking_class,
        availability_status=availability_status,
        recommended_action="manual_check",
        match=IntakeV3MaterialAvailabilityMatch(
            match_strategy="code" if registry_code else "none",
            confidence="high" if registry_code else "low",
            inventory_code=registry_code,
        ),
        quantity=IntakeV3MaterialAvailabilityQuantity(
            required=2.0,
            required_unit="m2" if material_key != "led_modules" else "buc",
            required_with_waste=2.4 if material_key != "led_modules" else 120.0,
            available=0.5 if shortage else 10.0,
            available_unit="m2" if material_key != "led_modules" else "buc",
            shortage=shortage,
            unit_comparison="compatible" if shortage is not None else "not_applicable",
        ),
    )


class TestProcurementPreviewClassification:
    def test_available_maps_to_no_action(self):
        row = _availability_row("plexiglas_face", availability_status="available")
        decision = classify_procurement_decision(row, IntakeV3ProcurementSourceHint())
        assert decision["procurement_status"] == "no_action"
        assert decision["decision_required"] is False

    def test_major_shortage_maps_to_owner_decision(self):
        row = _availability_row(
            "plexiglas_face",
            availability_status="shortage",
            shortage=1.4,
            registry_code="MAT-ACP-FATA-LITERE",
        )
        decision = classify_procurement_decision(row, IntakeV3ProcurementSourceHint(unit_cost_hint=16.0))
        assert decision["procurement_status"] == "owner_decision_required"
        assert decision["advance_recommended"] is True
        assert decision["recommended_action"] == "purchase_after_owner_approval"

    def test_led_shortage_maps_to_purchase_recommended(self):
        row = _availability_row(
            "led_modules",
            availability_status="shortage",
            shortage=50.0,
            registry_code="MAT-LED-MODULE",
        )
        decision = classify_procurement_decision(row, IntakeV3ProcurementSourceHint(unit_cost_hint=0.5))
        assert decision["procurement_status"] == "purchase_recommended"
        assert decision["decision_owner"] == "procurement"

    def test_indirect_consumable_policy(self):
        row = _availability_row(
            "mounting_cables",
            availability_status="indirect_consumable",
            tracking_class="indirect_consumable",
        )
        decision = classify_procurement_decision(row, IntakeV3ProcurementSourceHint())
        assert decision["procurement_status"] == "indirect_consumable"
        assert decision["is_indirect_consumable"] is True


class TestProcurementPreviewEndpoints:
    @pytest.mark.asyncio
    async def test_missing_order_returns_not_found(self, auth_client, db_session):
        movements_before = await db_session.scalar(select(func.count()).select_from(StockMovement))
        response = auth_client.get("/api/v1/intake-v3/orders/999999/procurement-preview")
        assert response.status_code == 404
        movements_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        assert movements_after == movements_before

    @pytest.mark.asyncio
    async def test_non_iv3_order_safe_response(self, auth_client, db_session):
        order = Orders(
            code="ORD-NORMAL-PP",
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
        response = auth_client.get(f"/api/v1/intake-v3/orders/{order.id}/procurement-preview")
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3"] is False
        assert payload["boundary"]["creates_purchase_order"] is False
        assert payload["boundary"]["mutates_inventory"] is False

    @pytest.mark.asyncio
    async def test_major_material_shortage_owner_decision(self, auth_client, db_session):
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
                    "source_name": "Baduc",
                    "source_url": "https://example.com/acp",
                    "source_review_status": "stale",
                    "unit_cost": 16.0,
                    "currency": "EUR",
                }
            ],
        )
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/procurement-preview",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        face = next(row for row in payload["rows"] if row["material_key"] == "plexiglas_face")
        assert face["procurement_status"] == "owner_decision_required"
        assert face["advance_recommended"] is True
        assert face["source_hint"]["source_name"] == "Baduc"
        assert payload["boundary"]["creates_purchase_order"] is False

    @pytest.mark.asyncio
    async def test_led_shortage_purchase_recommended(self, auth_client, db_session):
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
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/procurement-preview")
        payload = response.json()
        led = next(row for row in payload["rows"] if row["material_key"] == "led_modules")
        assert led["procurement_status"] == "purchase_recommended"
        assert payload["boundary"]["creates_supplier_order"] is False

    @pytest.mark.asyncio
    async def test_indirect_consumable_rows(self, auth_client):
        workspace_id, _, _ = _create_iv3_draft_quote(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/procurement-preview",
        )
        payload = response.json()
        indirect = [row for row in payload["rows"] if row["is_indirect_consumable"]]
        assert len(indirect) >= 4
        assert all(row["procurement_status"] == "indirect_consumable" for row in indirect)

    @pytest.mark.asyncio
    async def test_endpoint_by_order(self, auth_client, db_session):
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
            f"/api/v1/intake-v3/orders/{order_payload['order_id']}/procurement-preview",
        )
        assert response.status_code == 200
        assert response.json()["order_id"] == order_payload["order_id"]


class TestProcurementPreviewIntegrations:
    @pytest.mark.asyncio
    async def test_production_readiness_consumes_procurement(self, auth_client, db_session):
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
        payload = response.json()
        assert payload["available_data"]["procurement_preview_available"] is True
        assert payload["available_data"]["procurement_owner_decision_required_count"] >= 1
        assert "procurement_owner_decision_required" in payload["warnings"]

    @pytest.mark.asyncio
    async def test_production_task_dry_run_consumes_procurement(self, auth_client, db_session):
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
        payload = response.json()
        assert payload["procurement_preview_available"] is True
        assert payload["procurement_owner_decision_required_count"] >= 1
        warning_codes = [item["code"] for item in payload["warnings"]]
        assert "procurement_owner_decision_required" in warning_codes
        assert payload["can_generate_real_tasks_now"] is False


class TestProcurementPreviewNoSideEffects:
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
            f"/api/v1/intake-v3/workspaces/{workspace_id}/procurement-preview",
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
