"""Intake V4 order-bound task generation readiness — read-only, no ExecutionTask."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from schemas.intake_v4 import FUTURE_GENERATION_CONTRACT_VERSION
from seeds.seed_build4_templates import seed_build4_templates
from services.intake_v4_commercial_quote_service import (
    INTAKE_V4_LINKAGE_JSON_KEY,
    intake_v4_linkage_code,
    parse_intake_v4_linkage_from_notes,
)
from services.intake_v4_order_bound_task_readiness_service import (
    build_intake_v4_order_bound_task_readiness,
)
from tests.test_intake_v4_commercial_quote import (
    _draft_quote_body,
    _seed_ready_workspace,
)
from tests.test_intake_v4_task_generation_dry_run import (
    _DEFAULT_PRICING,
    _complete_payload,
)


@pytest.fixture(scope="module")
def seeded_db(db_fixture):
    asyncio.get_event_loop().run_until_complete(seed_build4_templates())
    return db_fixture


@pytest.fixture
def v4_client(seeded_db):
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse
    from fastapi.testclient import TestClient

    async def _override_get_db():
        async with seeded_db.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


async def _run_readiness(
    workspace_id: str,
    payload_dict: dict,
    *,
    db=None,
    pricing: dict | None = None,
    quote=None,
    order=None,
    has_execution_plan: bool = False,
):
    from services.intake_v4_workspace_service import _parse_payload

    payload = _parse_payload(payload_dict)
    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as mock_pricing, patch(
        "services.intake_v4_order_bound_task_readiness_service.check_existing_quote_for_intake_v4_workspace",
        new_callable=AsyncMock,
    ) as mock_quote, patch(
        "services.intake_v4_order_bound_task_readiness_service.check_existing_order_for_iv3_quote",
        new_callable=AsyncMock,
    ) as mock_order, patch(
        "services.intake_v4_order_bound_task_readiness_service._order_has_execution_plan",
        new_callable=AsyncMock,
    ) as mock_plan:
        mock_pricing.return_value = pricing if pricing is not None else _DEFAULT_PRICING
        if db is None:
            mock_quote.return_value = quote
            mock_order.return_value = order
            mock_plan.return_value = has_execution_plan
        return await build_intake_v4_order_bound_task_readiness(
            db,  # type: ignore[arg-type]
            workspace_id,
            payload_dict,
            payload,
        )


class TestOrderBoundReadinessEndpoint:
    def test_endpoint_returns_readiness_mode(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["readiness_mode"] == "order_bound_task_generation_readiness"
        assert body["order_bound_readiness"] is True
        assert body["creates_execution_tasks"] is False
        assert body["writes_to_production"] is False
        assert body["stock_consumption"] is False
        assert body["dry_run_only"] is True
        assert body["can_generate_real_tasks"] is False
        assert body["owner_confirmation_required"] is True
        assert body["future_generation_contract"]["contract_version"] == FUTURE_GENERATION_CONTRACT_VERSION
        assert body["idempotency_summary"]["entries_count"] >= 0

    @pytest.mark.asyncio
    async def test_endpoint_does_not_create_execution_plan(self, v4_client, db_session):
        before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan)) or 0
        workspace_id = _seed_ready_workspace(v4_client)
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        assert response.status_code == 200
        after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan)) or 0
        assert after == before


class TestOrderBoundReadinessBlockers:
    @pytest.mark.asyncio
    async def test_workspace_without_quote_blocks_quote_missing(self):
        result = await _run_readiness("ws-no-quote", _complete_payload())
        codes = {b.code for b in result.blockers if b.severity == "blocking"}
        assert "quote_missing" in codes
        assert "order_missing" in codes
        assert result.can_generate_real_tasks is False
        assert result.can_generate_reason in codes

    @pytest.mark.asyncio
    async def test_unsupported_template_safe(self):
        payload = _complete_payload()
        payload["product_binding"] = {"template_code": "TPL-ACM-CASSETTED-PANEL"}
        result = await _run_readiness("ws-acm", payload)
        codes = {b.code for b in result.blockers if b.severity == "blocking"}
        assert "template_out_of_scope" in codes

    @pytest.mark.asyncio
    async def test_analysis_boundary_blockers_propagate(self):
        payload = _complete_payload(confirmed=False)
        result = await _run_readiness("ws-finish", payload)
        codes = {b.code for b in result.blockers if b.severity == "blocking"}
        assert "finish_setup_not_confirmed" in codes

    @pytest.mark.asyncio
    async def test_idempotency_summary_present(self):
        result = await _run_readiness("ws-idem", _complete_payload())
        assert "entries_count" in result.idempotency_summary
        assert result.idempotency_summary["entries_count"] >= 1

    @pytest.mark.asyncio
    async def test_no_stock_consumption_flag(self):
        result = await _run_readiness("ws-stock", _complete_payload())
        assert result.stock_consumption is False

    def test_quote_requires_pricing_review_blocker(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        quote_resp = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert quote_resp.status_code == 201

        readiness = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        assert readiness.status_code == 200
        body = readiness.json()
        assert body["linked_quote"]["exists"] is True
        assert body["linked_quote"]["requires_pricing_review"] is True
        blocker_codes = {b["code"] for b in body["blockers"] if b["severity"] == "blocking"}
        assert "requires_pricing_review" in blocker_codes
        assert "quote_not_accepted" in blocker_codes
        assert "order_missing" in blocker_codes

    @pytest.mark.asyncio
    async def test_quote_snapshot_hash_mismatch(self, v4_client, db_session):
        workspace_id = _seed_ready_workspace(v4_client)
        quote_resp = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert quote_resp.status_code == 201
        quote_id = quote_resp.json()["quote_id"]

        quote = await db_session.get(Quotes, quote_id)
        assert quote is not None
        notes = json.loads(quote.notes)
        linkage = notes[INTAKE_V4_LINKAGE_JSON_KEY]
        linkage["snapshot"]["workspace_payload_snapshot"]["svg_source"]["file_hash"] = "b" * 64
        notes[INTAKE_V4_LINKAGE_JSON_KEY] = linkage
        quote.notes = json.dumps(notes)
        await db_session.commit()

        readiness = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        assert readiness.status_code == 200
        blocker_codes = {b["code"] for b in readiness.json()["blockers"] if b["severity"] == "blocking"}
        assert "quote_snapshot_hash_mismatch" in blocker_codes

    @pytest.mark.asyncio
    async def test_order_missing_with_quote(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        readiness = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        body = readiness.json()
        assert body["linked_order"]["exists"] is False
        assert "order_missing" in {b["code"] for b in body["blockers"]}

    @pytest.mark.asyncio
    async def test_order_wrong_status_blocks(self, v4_client, db_session):
        workspace_id = _seed_ready_workspace(v4_client)
        quote_resp = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        quote_id = quote_resp.json()["quote_id"]

        order = Orders(
            code="ORD-IV4-PENDING",
            quote_id=quote_id,
            quote_code=quote_resp.json()["quote_code"],
            client_name="Test Client",
            status="pending",
        )
        db_session.add(order)
        await db_session.commit()

        readiness = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        blocker_codes = {b["code"] for b in readiness.json()["blockers"] if b["severity"] == "blocking"}
        assert "order_status_not_ready_for_production" in blocker_codes

    @pytest.mark.asyncio
    async def test_order_with_execution_plan_blocks(self, v4_client, db_session):
        workspace_id = _seed_ready_workspace(v4_client)
        quote_resp = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        quote_id = quote_resp.json()["quote_id"]

        order = Orders(
            code="ORD-IV4-LOCKED",
            quote_id=quote_id,
            quote_code=quote_resp.json()["quote_code"],
            client_name="Test Client",
            status="locked",
            snapshot_version=1,
        )
        db_session.add(order)
        await db_session.flush()
        db_session.add(
            ExecutionPlan(
                order_id=order.id,
                order_code=order.code,
                snapshot_version=1,
                tasks_json="[]",
                total_estimated_time_minutes=0.0,
            )
        )
        await db_session.commit()

        readiness = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        body = readiness.json()
        assert body["linked_order"]["has_execution_plan"] is True
        assert "order_already_has_execution_plan" in {
            b["code"] for b in body["blockers"] if b["severity"] == "blocking"
        }

    @pytest.mark.asyncio
    async def test_dry_run_no_candidates_blocks(self):
        payload = _complete_payload()
        payload.pop("svg_analysis_json", None)
        payload["path_geometry_summary"] = {"parse_status": "pending"}
        result = await _run_readiness("ws-empty-dry", payload)
        codes = {b.code for b in result.blockers if b.severity == "blocking"}
        assert (
            "dry_run_no_task_candidates" in codes
            or "missing_svg_analysis_json" in codes
            or "missing_svg_analysis" in codes
        )

    @pytest.mark.asyncio
    async def test_owner_confirmation_required_blocker(self):
        result = await _run_readiness("ws-owner", _complete_payload())
        assert result.owner_confirmation_required is True
        assert "owner_confirmation_required" in {b.code for b in result.blockers}

    @pytest.mark.asyncio
    async def test_future_generation_contract_present(self):
        result = await _run_readiness("ws-contract", _complete_payload())
        contract = result.future_generation_contract
        assert contract.contract_version == FUTURE_GENERATION_CONTRACT_VERSION
        assert contract.target_entity == "Order"
        assert contract.would_create_execution_tasks is False
        assert contract.would_write_execution_plan is False
        assert contract.next_action_enabled is False

    def test_does_not_touch_cost_engine(self):
        import services.intake_v4_order_bound_task_readiness_service as svc

        source = open(svc.__file__, encoding="utf-8").read()
        assert "CostEngine" not in source
        assert "cost_engine" not in source

    def test_does_not_touch_v2_v3_services(self):
        import services.intake_v4_order_bound_task_readiness_service as svc

        source = open(svc.__file__, encoding="utf-8").read()
        assert "intake_v2" not in source
        assert "intake_v3_workspace_service" not in source


class TestParseIntakeV4Linkage:
    def test_parse_linkage_from_notes(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        quote_resp = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        quote_row = v4_client.get(f"/api/v1/entities/quotes/{quote_resp.json()['quote_id']}")
        linkage = parse_intake_v4_linkage_from_notes(quote_row.json()["notes"])
        assert linkage is not None
        assert linkage["source_workspace_id"] == workspace_id
        assert intake_v4_linkage_code(workspace_id) == f"IV4-{workspace_id}"
