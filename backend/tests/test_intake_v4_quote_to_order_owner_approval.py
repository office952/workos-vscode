"""Intake V4 quote → order commercial spine — pricing review, owner approval, accept, convert."""

from __future__ import annotations

import asyncio
import json
from concurrent import futures

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from services.intake_v4_commercial_quote_service import (
    INTAKE_V4_LINKAGE_JSON_KEY,
    parse_intake_v4_linkage_from_notes,
)
from services.intake_v4_quote_linkage_utils import (
    INTAKE_V4_ORDER_LINKAGE_JSON_KEY,
    OWNER_APPROVAL_JSON_KEY,
    V4_ACCEPTED_STATUS,
)
from tests.test_intake_v4_commercial_quote import (
    _draft_quote_body,
    _get_persisted_file_hash,
    _seed_ready_workspace,
)

# Real priced-quote totals for pytest — not sent via pricing-review API.
REAL_QUOTE_SUBTOTAL = 5000.0
REAL_QUOTE_VAT_PCT = 21.0
REAL_QUOTE_VAT_AMOUNT = 1050.0
REAL_QUOTE_GRAND_TOTAL = 6050.0
FORBIDDEN_PLACEHOLDER_TOTAL = 1210.0


def _valid_pricing_review_request(
    v4_client,
    workspace_id: str,
    quote_id: int,
    intake_code: str,
    **overrides,
) -> dict:
    payload = {
        "pricing_review_reason": "Pricing review completed using quote totals from QuoteWizard.",
        "reviewer_confirmation": True,
        "confirm_quote_stays_draft": True,
        "confirm_no_order": True,
        "confirm_no_execution": True,
        "confirm_no_inventory": True,
        "expected_quote_id": quote_id,
        "expected_intake_code": intake_code,
        "client_analysis_hash": _get_persisted_file_hash(v4_client, workspace_id),
    }
    payload.update(overrides)
    return payload


def _apply_real_quote_pricing(seeded_db, quote_id: int) -> None:
    async def _run() -> None:
        async with seeded_db.session_maker() as session:
            quote = await session.get(Quotes, quote_id)
            assert quote is not None
            quote.subtotal = REAL_QUOTE_SUBTOTAL
            quote.discount = 0.0
            quote.discount_pct = 0.0
            quote.total_before_vat = REAL_QUOTE_SUBTOTAL
            quote.vat = REAL_QUOTE_VAT_PCT
            quote.grand_total = REAL_QUOTE_GRAND_TOTAL
            line_items = json.loads(quote.line_items or "[]")
            if isinstance(line_items, list) and line_items:
                line_items[0]["unit_price"] = REAL_QUOTE_SUBTOTAL
                line_items[0]["total"] = REAL_QUOTE_SUBTOTAL
                quote.line_items = json.dumps(line_items)
            await session.commit()

    with futures.ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(asyncio.run, _run()).result()


def _valid_owner_approval_request(v4_client, workspace_id: str, **overrides) -> dict:
    payload = {
        "decision_reason": "Reviewed V4 quote and production handoff for order conversion.",
        "acknowledged_no_execution_tasks": True,
        "acknowledged_no_stock_consumption": True,
        "acknowledged_warnings": [],
        "client_analysis_hash": _get_persisted_file_hash(v4_client, workspace_id),
    }
    payload.update(overrides)
    return payload


def _valid_accept_request(quote_id: int, intake_code: str, **overrides) -> dict:
    payload = {
        "expected_quote_id": quote_id,
        "expected_intake_code": intake_code,
        "accept_decision": "approved",
        "accept_reason": "Owner approved V4 priced draft quote.",
        "acceptance_source": "intake_v4_operator",
        "reviewer_confirmation": True,
        "confirm_pricing_review_completed": True,
        "confirm_no_order": True,
        "confirm_no_execution": True,
        "confirm_no_inventory": True,
        "confirm_convert_separate": True,
    }
    payload.update(overrides)
    return payload


def _valid_convert_request(quote_id: int, intake_code: str, **overrides) -> dict:
    payload = {
        "expected_quote_id": quote_id,
        "expected_intake_code": intake_code,
        "convert_decision": "approved",
        "convert_reason": "Convert accepted V4 quote to locked order snapshot.",
        "conversion_source": "intake_v4_operator",
        "reviewer_confirmation": True,
        "confirm_quote_accepted": True,
        "confirm_pricing_review_completed": True,
        "confirm_create_order_only": True,
        "confirm_no_execution_plan": True,
        "confirm_no_execution_tasks": True,
        "confirm_no_inventory": True,
        "confirm_production_separate": True,
    }
    payload.update(overrides)
    return payload


def _create_iv4_draft_quote(v4_client) -> tuple[str, int, str]:
    workspace_id = _seed_ready_workspace(v4_client)
    response = v4_client.post(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
        json=_draft_quote_body(v4_client, workspace_id),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return workspace_id, body["quote_id"], f"IV4-{workspace_id}"


def _complete_v4_pricing(
    v4_client,
    seeded_db,
    workspace_id: str,
    quote_id: int,
    intake_code: str,
) -> None:
    _apply_real_quote_pricing(seeded_db, quote_id)
    response = v4_client.post(
        f"/api/v1/intake-v4/quotes/{quote_id}/complete-pricing-review",
        json=_valid_pricing_review_request(v4_client, workspace_id, quote_id, intake_code),
    )
    assert response.status_code == 200, response.text


def _owner_approval(v4_client, workspace_id: str, quote_id: int) -> None:
    response = v4_client.post(
        f"/api/v1/intake-v4/quotes/{quote_id}/owner-approval",
        json=_valid_owner_approval_request(v4_client, workspace_id),
    )
    assert response.status_code == 200, response.text


def _accept_v4_quote(v4_client, quote_id: int, intake_code: str) -> None:
    response = v4_client.post(
        f"/api/v1/intake-v4/quotes/{quote_id}/accept",
        json=_valid_accept_request(quote_id, intake_code),
    )
    assert response.status_code == 200, response.text


def _prepare_accepted_iv4_quote(v4_client, seeded_db) -> tuple[str, int, str]:
    workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
    _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
    _owner_approval(v4_client, workspace_id, quote_id)
    _accept_v4_quote(v4_client, quote_id, intake_code)
    return workspace_id, quote_id, intake_code


@pytest.fixture(scope="module")
def seeded_db(db_fixture):
    import asyncio

    from seeds.seed_build4_templates import seed_build4_templates

    asyncio.get_event_loop().run_until_complete(seed_build4_templates())
    return db_fixture


@pytest.fixture
def v4_client(seeded_db):
    from fastapi.testclient import TestClient

    from core.database import get_db
    from dependencies.auth import get_current_user
    from main import app
    from schemas.auth import UserResponse

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


class TestV4PricingReviewCompletion:
    def test_complete_pricing_review_valid_iv4(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _apply_real_quote_pricing(seeded_db, quote_id)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/complete-pricing-review",
            json=_valid_pricing_review_request(v4_client, workspace_id, quote_id, intake_code),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["pricing_review_completed"] is True
        assert body["requires_pricing_review"] is False
        assert body["pricing_totals_source"] == "quote_columns"
        assert body["creates_execution_tasks"] is False

        quote_row = v4_client.get(f"/api/v1/entities/quotes/{quote_id}")
        assert quote_row.status_code == 200
        quote = quote_row.json()
        linkage = json.loads(quote["notes"])[INTAKE_V4_LINKAGE_JSON_KEY]
        assert linkage["requires_pricing_review"] is False
        assert linkage["pricing_review"]["status"] == "completed"
        assert linkage["pricing_review"]["pricing_totals_source"] == "quote_columns"
        assert float(linkage["pricing_review"]["total"]) == REAL_QUOTE_GRAND_TOTAL
        assert float(quote["grand_total"]) == REAL_QUOTE_GRAND_TOTAL
        assert float(quote["grand_total"]) != FORBIDDEN_PLACEHOLDER_TOTAL

    def test_complete_pricing_review_blocks_unpriced_quote(self, v4_client):
        _, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/complete-pricing-review",
            json={
                "pricing_review_reason": "Should fail — quote not priced.",
                "reviewer_confirmation": True,
                "confirm_quote_stays_draft": True,
                "confirm_no_order": True,
                "confirm_no_execution": True,
                "confirm_no_inventory": True,
                "expected_quote_id": quote_id,
                "expected_intake_code": intake_code,
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "QUOTE_NOT_PRICED"

    def test_complete_pricing_review_rejects_ui_totals(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _apply_real_quote_pricing(seeded_db, quote_id)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/complete-pricing-review",
            json={
                **_valid_pricing_review_request(v4_client, workspace_id, quote_id, intake_code),
                "subtotal": 1000.0,
                "total": FORBIDDEN_PLACEHOLDER_TOTAL,
                "vat_amount": 210.0,
                "vat_percent": 21.0,
            },
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "extra_forbidden" in str(detail).lower() or detail.get("error") == "PLACEHOLDER_TOTALS_NOT_ALLOWED"

    @pytest.mark.asyncio
    async def test_complete_pricing_review_without_v4_linkage_fails(self, v4_client, db_session):
        quote = Quotes(
            code="Q-NO-LINKAGE-V4",
            intake_code="IV4-ws-missing-link",
            client_name="No linkage",
            status="draft",
            version=1,
            notes=json.dumps({"human_summary": "no v4 linkage"}),
        )
        db_session.add(quote)
        await db_session.commit()
        await db_session.refresh(quote)

        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote.id}/complete-pricing-review",
            json={
                "pricing_review_reason": "should fail without linkage",
                "reviewer_confirmation": True,
                "confirm_quote_stays_draft": True,
                "confirm_no_order": True,
                "confirm_no_execution": True,
                "confirm_no_inventory": True,
                "expected_quote_id": quote.id,
                "expected_intake_code": quote.intake_code,
            },
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        if isinstance(detail, dict):
            assert detail["error"] == "NOT_IV4_QUOTE"
        else:
            pytest.fail(f"Expected NOT_IV4_QUOTE, got {detail!r}")

    @pytest.mark.asyncio
    async def test_complete_pricing_review_iv3_quote_fails(self, v4_client, db_session):
        quote = Quotes(
            code="Q-IV3-NOT-V4",
            intake_code="IV3-WS-999",
            client_name="IV3",
            status="draft",
            version=1,
            notes=json.dumps({INTAKE_V4_LINKAGE_JSON_KEY: {"requires_pricing_review": True}}),
        )
        db_session.add(quote)
        await db_session.commit()
        await db_session.refresh(quote)

        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote.id}/complete-pricing-review",
            json={
                "pricing_review_reason": "should fail",
                "reviewer_confirmation": True,
                "confirm_quote_stays_draft": True,
                "confirm_no_order": True,
                "confirm_no_execution": True,
                "confirm_no_inventory": True,
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "NOT_IV4_QUOTE"

    def test_complete_pricing_review_preserves_v4_snapshot(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        before = v4_client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        before_linkage = json.loads(before["notes"])[INTAKE_V4_LINKAGE_JSON_KEY]
        before_snapshot = before_linkage["snapshot"]

        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)

        after = v4_client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        after_linkage = json.loads(after["notes"])[INTAKE_V4_LINKAGE_JSON_KEY]
        assert after_linkage["snapshot"] == before_snapshot


class TestV4OwnerApproval:
    def test_owner_approval_persisted(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/owner-approval",
            json=_valid_owner_approval_request(v4_client, workspace_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["owner_approval_persisted"] is True
        assert body["owner_approval_valid"] is True
        assert body["creates_execution_tasks"] is False

        quote = v4_client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        linkage = json.loads(quote["notes"])[INTAKE_V4_LINKAGE_JSON_KEY]
        assert linkage[OWNER_APPROVAL_JSON_KEY]["approved"] is True

    def test_owner_approval_without_ack_flags_fails(self, v4_client):
        workspace_id, quote_id, _ = _create_iv4_draft_quote(v4_client)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/owner-approval",
            json=_valid_owner_approval_request(
                v4_client,
                workspace_id,
                acknowledged_no_execution_tasks=False,
            ),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "CONFIRMATIONS_REQUIRED"

    def test_owner_approval_stale_on_analysis_hash_change(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
        _owner_approval(v4_client, workspace_id, quote_id)

        quote = v4_client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        notes = json.loads(quote["notes"])
        linkage = notes[INTAKE_V4_LINKAGE_JSON_KEY]
        linkage[OWNER_APPROVAL_JSON_KEY]["analysis_hash"] = "deadbeef" * 8
        notes[INTAKE_V4_LINKAGE_JSON_KEY] = linkage
        v4_client.put(
            f"/api/v1/entities/quotes/{quote_id}",
            json={"notes": json.dumps(notes)},
        )

        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "OWNER_APPROVAL_STALE"

    @pytest.mark.asyncio
    async def test_owner_approval_does_not_create_order_or_tasks(self, v4_client, seeded_db, db_session):
        workspace_id, quote_id, _ = _create_iv4_draft_quote(v4_client)
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))

        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, f"IV4-{workspace_id}")
        _owner_approval(v4_client, workspace_id, quote_id)

        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert orders_after == orders_before
        assert plans_after == plans_before


class TestV4AcceptQuote:
    def test_accept_blocks_pricing_review_incomplete(self, v4_client):
        _, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "PRICING_REVIEW_REQUIRED"

    def test_accept_blocks_owner_approval_missing(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "OWNER_APPROVAL_MISSING"

    def test_accept_blocks_owner_approval_stale(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
        _owner_approval(v4_client, workspace_id, quote_id)

        quote = v4_client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        notes = json.loads(quote["notes"])
        linkage = notes[INTAKE_V4_LINKAGE_JSON_KEY]
        linkage[OWNER_APPROVAL_JSON_KEY]["analysis_hash"] = "cafebabe" * 8
        notes[INTAKE_V4_LINKAGE_JSON_KEY] = linkage
        v4_client.put(
            f"/api/v1/entities/quotes/{quote_id}",
            json={"notes": json.dumps(notes)},
        )

        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "OWNER_APPROVAL_STALE"

    def test_accept_blocks_analysis_hash_mismatch(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
        _owner_approval(v4_client, workspace_id, quote_id)

        quote = v4_client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        notes = json.loads(quote["notes"])
        linkage = notes[INTAKE_V4_LINKAGE_JSON_KEY]
        linkage["snapshot"]["workspace_payload_snapshot"]["svg_source"]["file_hash"] = "f" * 64
        notes[INTAKE_V4_LINKAGE_JSON_KEY] = linkage
        v4_client.put(
            f"/api/v1/entities/quotes/{quote_id}",
            json={"notes": json.dumps(notes)},
        )

        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/accept",
            json=_valid_accept_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "ANALYSIS_HASH_MISMATCH"

    def test_accept_valid_sets_accepted_status(self, v4_client, seeded_db):
        _, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        quote = v4_client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        assert quote["status"] == V4_ACCEPTED_STATUS
        linkage = json.loads(quote["notes"])[INTAKE_V4_LINKAGE_JSON_KEY]
        assert linkage["accept_decision"]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_accept_does_not_create_order(self, v4_client, seeded_db, db_session):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
        _owner_approval(v4_client, workspace_id, quote_id)
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        _accept_v4_quote(v4_client, quote_id, intake_code)
        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        assert orders_after == orders_before


class TestV4ConvertToOrder:
    def test_convert_blocks_quote_not_accepted(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
        _owner_approval(v4_client, workspace_id, quote_id)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "QUOTE_NOT_ACCEPTED"

    def test_convert_blocks_pricing_review_incomplete(self, v4_client):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _owner_approval(v4_client, workspace_id, quote_id)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] in {
            "QUOTE_NOT_ACCEPTED",
            "PRICING_REVIEW_REQUIRED",
        }

    @pytest.mark.asyncio
    async def test_convert_blocks_owner_approval_missing(self, v4_client, seeded_db, db_session):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
        quote = await db_session.get(Quotes, quote_id)
        notes = json.loads(quote.notes)
        linkage = notes[INTAKE_V4_LINKAGE_JSON_KEY]
        linkage["accept_decision"] = {
            "status": "approved",
            "accepted_at": "2026-01-01T00:00:00+00:00",
            "order_created": False,
        }
        notes[INTAKE_V4_LINKAGE_JSON_KEY] = linkage
        quote.notes = json.dumps(notes)
        quote.status = V4_ACCEPTED_STATUS
        await db_session.commit()

        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "OWNER_APPROVAL_MISSING"

    def test_convert_blocks_duplicate_order(self, v4_client, seeded_db):
        _, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        first = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert first.status_code == 200, first.text
        second = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert second.status_code == 422
        assert second.json()["detail"]["error"] == "ORDER_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_convert_creates_exactly_one_order(self, v4_client, seeded_db, db_session):
        _, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 200, response.text
        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        assert orders_after == orders_before + 1

    def test_convert_preserves_quote_id_on_order(self, v4_client, seeded_db):
        _, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 200, response.text
        order_id = response.json()["order_id"]
        order = v4_client.get(f"/api/v1/entities/orders/{order_id}").json()
        assert order["quote_id"] == quote_id

    def test_order_contains_v4_frozen_snapshot(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 200, response.text
        order_id = response.json()["order_id"]
        order = v4_client.get(f"/api/v1/entities/orders/{order_id}").json()
        snapshot = json.loads(order["snapshot_line_items"])
        assert snapshot["source_intake_version"] == "V4"
        assert snapshot["source_workspace_id"] == workspace_id
        assert snapshot["source_quote_id"] == quote_id
        assert snapshot["no_execution_plan_created"] is True
        assert INTAKE_V4_ORDER_LINKAGE_JSON_KEY in snapshot
        assert snapshot["owner_approval_snapshot"]["approved"] is True
        assert snapshot["pricing_review_snapshot"]["status"] == "completed"
        assert float(snapshot["pricing_review_snapshot"]["total"]) == REAL_QUOTE_GRAND_TOTAL
        assert float(snapshot["pricing_review_snapshot"]["total"]) != FORBIDDEN_PLACEHOLDER_TOTAL
        assert snapshot["pricing_review_snapshot"]["pricing_totals_source"] == "quote_columns"
        assert str(FORBIDDEN_PLACEHOLDER_TOTAL) not in json.dumps(snapshot)

    def test_convert_order_snapshot_never_contains_placeholder_totals(self, v4_client, seeded_db):
        _, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 200, response.text
        order = v4_client.get(f"/api/v1/entities/orders/{response.json()['order_id']}").json()
        snapshot = json.loads(order["snapshot_line_items"])
        assert float(snapshot["pricing_review_snapshot"]["total"]) == REAL_QUOTE_GRAND_TOTAL
        assert str(FORBIDDEN_PLACEHOLDER_TOTAL) not in json.dumps(snapshot)

    @pytest.mark.asyncio
    async def test_convert_does_not_create_execution_plan(self, v4_client, seeded_db, db_session):
        _, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 200, response.text
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_convert_does_not_write_tasks_json(self, v4_client, seeded_db, db_session):
        _, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        response = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert response.status_code == 200, response.text
        order_id = response.json()["order_id"]
        plan_count = await db_session.scalar(
            select(func.count()).select_from(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
        assert plan_count == 0


class TestV4ReadinessAfterSpine:
    def test_readiness_sees_pricing_review_completed(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["pricing_review"]["completed"] is True
        blocker_codes = [b["code"] for b in body["blockers"]]
        assert "requires_pricing_review" not in blocker_codes

    def test_readiness_sees_owner_approval_valid(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        _complete_v4_pricing(v4_client, seeded_db, workspace_id, quote_id, intake_code)
        _owner_approval(v4_client, workspace_id, quote_id)
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        body = response.json()
        assert body["owner_approval"]["exists"] is True
        assert body["owner_approval"]["valid"] is True
        assert body["owner_confirmation_required"] is False
        blocker_codes = [b["code"] for b in body["blockers"]]
        assert "owner_confirmation_required" not in blocker_codes

    def test_readiness_sees_quote_accepted(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        body = response.json()
        assert body["linked_quote"]["status"] == V4_ACCEPTED_STATUS
        blocker_codes = [b["code"] for b in body["blockers"]]
        assert "quote_not_accepted" not in blocker_codes

    def test_readiness_sees_linked_order(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        convert = v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        assert convert.status_code == 200, convert.text
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        body = response.json()
        assert body["linked_order"]["exists"] is True
        assert body["v4_order_conversion"]["converted"] is True
        assert body["v4_order_conversion"]["order_id"] == convert.json()["order_id"]

    def test_readiness_keeps_can_generate_real_tasks_false(self, v4_client, seeded_db):
        workspace_id, quote_id, intake_code = _prepare_accepted_iv4_quote(v4_client, seeded_db)
        v4_client.post(
            f"/api/v1/intake-v4/quotes/{quote_id}/convert-to-order",
            json=_valid_convert_request(quote_id, intake_code),
        )
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        body = response.json()
        assert body["can_generate_real_tasks"] is False
        assert body["creates_execution_tasks"] is False

    @pytest.mark.asyncio
    async def test_readiness_does_not_write(self, v4_client, db_session):
        workspace_id, quote_id, intake_code = _create_iv4_draft_quote(v4_client)
        orders_before = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness",
        )
        assert response.status_code == 200, response.text
        orders_after = await db_session.scalar(select(func.count()).select_from(Orders))
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert orders_after == orders_before
        assert plans_after == plans_before
