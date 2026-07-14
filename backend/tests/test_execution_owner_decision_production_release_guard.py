"""Tests for execution owner-decision production release guard (W5-T01)."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from schemas.auth import UserResponse
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.quote_snapshot_v2 import QuoteSnapshotOwnerDecision
from services.execution_owner_decision_production_release_service import (
    OWNER_DECISION_RESOLUTIONS_KEY,
    assert_production_release_allowed,
    evaluate_production_release,
    resolve_owner_decision_for_order,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.task_start_gate_service import assert_task_startable
from tests.test_execution_plan_v2_preview import (
    _build_order_snapshot_v2_json,
    _sample_aggregate,
    _sample_product_definition,
)
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from tests.test_employee_mobile_tasks import _cleanup_overrides, _client_for, _user

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

GUARD_OID_BASE = 20500

PRODUCTION_BLOCKERS = (
    "INTERNAL_SABLON_FOREX_COST",
    "INTERNAL_MONTAJ_RULE",
    "INTERNAL_CONSUMABLES_RULE",
)

NONBLOCKING = (
    "INTERNAL_AMBALARE_RULE",
    "OVERHEAD_ALLOCATION_PENDING",
)


def _owner_decision(code: str, *, label: str | None = None) -> QuoteSnapshotOwnerDecision:
    return QuoteSnapshotOwnerDecision(
        code=code,
        label=label or code.replace("_", " ").title(),
        source="estimated_internal_cost",
        module_code="test_module",
        detail="test detail",
    )


def _build_snapshot_with_owner_decisions(
    codes: list[str],
    *,
    quote_id: int = 1,
    quote_snapshot_v2_id: int = 1,
) -> str:
    decisions = [_owner_decision(code) for code in codes]
    snapshot = OrderSnapshotV2(
        quote_id=quote_id,
        quote_snapshot_v2_id=quote_snapshot_v2_id,
        snapshot_code="OSN2-GUARD-001",
        content_hash="abc123def456abc123def456abc123de",
        product_definition_snapshot=_sample_product_definition(),
        product_aggregate_snapshot=_sample_aggregate(include_task_rules=True),
        commercial_price_proposal_snapshot=_commercial_preview(total=1500.0),
        estimated_internal_cost_snapshot=_internal_preview(total=620.0),
        owner_decisions_snapshot=decisions,
        accepted_commercial_total=1500.0,
        accepted_currency="RON",
        estimated_internal_total=620.0,
    )
    return snapshot.model_dump_json()


def _simple_plan_tasks() -> list[dict]:
    return [
        {
            "task_id": "T-GUARD",
            "task_name": "Guard Test Task",
            "task_type": "assembly",
            "depends_on_task_ids": [],
        }
    ]


async def _seed_guard_order(
    db_session,
    *,
    order_id: int,
    owner_codes: list[str],
    with_plan: bool = True,
) -> Orders:
    snapshot_json = _build_snapshot_with_owner_decisions(
        owner_codes,
        quote_id=order_id,
        quote_snapshot_v2_id=order_id,
    )
    order = Orders(
        id=order_id,
        code=f"ORD-GUARD-{order_id}",
        quote_id=order_id,
        quote_code=f"QT-GUARD-{order_id}",
        client_name="Guard Client",
        status="locked",
        total_amount=1500.0,
        snapshot_line_items=None,
        quote_snapshot_v2_id=order_id,
        snapshot_v2_json=snapshot_json,
        readiness_snapshot={"execution_plan_created": False, "no_execution_plan_created": True},
    )
    db_session.add(order)
    if with_plan:
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=order.code,
                snapshot_version=1,
                tasks_json=json.dumps(_simple_plan_tasks()),
                total_estimated_time_minutes=60,
            )
        )
    await db_session.commit()
    await db_session.refresh(order)
    return order


def _admin_user() -> UserResponse:
    return UserResponse(
        id="admin-guard-1",
        name="Guard Admin",
        email="guard-admin@test.local",
        role="admin",
    )


def _operator_user() -> UserResponse:
    return UserResponse(
        id="op-guard-1",
        name="Guard Operator",
        email="guard-op@test.local",
        role="operator",
    )


@pytest.mark.asyncio
async def test_plan_creation_allowed_with_unresolved_production_decisions(db_session):
    from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot

    order_id = GUARD_OID_BASE + 1
    snapshot_json = _build_snapshot_with_owner_decisions(
        list(PRODUCTION_BLOCKERS),
        quote_id=order_id,
        quote_snapshot_v2_id=order_id,
    )
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=order_id,
        snapshot_v2_json=snapshot_json,
    )
    before_snapshot = order.snapshot_v2_json
    result = await create_execution_plan_v2_from_order(db_session, order.id)
    assert result.execution_plan_id is not None
    await db_session.refresh(order)
    assert order.snapshot_v2_json == before_snapshot


@pytest.mark.asyncio
async def test_task_start_blocked_with_all_production_blockers(db_session):
    order_id = GUARD_OID_BASE + 2
    await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=list(PRODUCTION_BLOCKERS),
    )
    with pytest.raises(HTTPException) as exc:
        await assert_task_startable(db_session, order_id=order_id, task_id="T-GUARD")
    assert exc.value.status_code == 409
    detail = exc.value.detail
    assert detail["code"] == "production_release_blocked"
    assert detail["release_status"] == "RELEASE_BLOCKED_OWNER_DECISIONS"
    blocker_codes = {item["code"] for item in detail["blockers"]}
    assert blocker_codes == set(PRODUCTION_BLOCKERS)


@pytest.mark.asyncio
async def test_internal_analysis_decisions_do_not_block(db_session):
    order_id = GUARD_OID_BASE + 3
    await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=list(NONBLOCKING),
    )
    evaluation = await assert_production_release_allowed(db_session, order_id)
    assert evaluation.release_status == "RELEASE_ALLOWED"
    gate = await assert_task_startable(db_session, order_id=order_id, task_id="T-GUARD")
    assert gate["readiness"]["is_startable"] is True


@pytest.mark.asyncio
async def test_structured_blocker_codes_preserved(db_session):
    order_id = GUARD_OID_BASE + 4
    await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=["INTERNAL_MONTAJ_RULE"],
    )
    with pytest.raises(HTTPException) as exc:
        await assert_production_release_allowed(db_session, order_id)
    blocker = exc.value.detail["blockers"][0]
    assert blocker["code"] == "INTERNAL_MONTAJ_RULE"
    assert blocker["requires_resolution"] is True
    assert blocker["acknowledgement_sufficient"] is False
    assert blocker["scope"] == "order"


@pytest.mark.asyncio
async def test_order_snapshot_unchanged_after_blocked_start(db_session):
    order_id = GUARD_OID_BASE + 5
    order = await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=["INTERNAL_SABLON_FOREX_COST"],
    )
    before = order.snapshot_v2_json
    with pytest.raises(HTTPException):
        await assert_task_startable(db_session, order_id=order_id, task_id="T-GUARD")
    refreshed = (
        await db_session.get(Orders, order_id)
    )
    assert refreshed.snapshot_v2_json == before


@pytest.mark.asyncio
async def test_resolution_state_stored_separately(db_session):
    order_id = GUARD_OID_BASE + 6
    order = await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=["INTERNAL_CONSUMABLES_RULE"],
    )
    before_snapshot = order.snapshot_v2_json
    result = await resolve_owner_decision_for_order(
        db_session,
        order_id=order_id,
        code="INTERNAL_CONSUMABLES_RULE",
        status="resolved",
        note="Consumabile confirmate de owner.",
        current_user=_admin_user(),
    )
    assert result.operational_status == "resolved"
    refreshed = await db_session.get(Orders, order_id)
    assert refreshed.snapshot_v2_json == before_snapshot
    readiness = refreshed.readiness_snapshot or {}
    assert OWNER_DECISION_RESOLUTIONS_KEY in readiness
    entry = readiness[OWNER_DECISION_RESOLUTIONS_KEY]["decisions"]["INTERNAL_CONSUMABLES_RULE"]
    assert entry["operational_status"] == "resolved"
    assert entry["resolution_note"] == "Consumabile confirmate de owner."


@pytest.mark.asyncio
async def test_authorized_resolution_unlocks_release(db_session):
    order_id = GUARD_OID_BASE + 7
    await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=["INTERNAL_SABLON_FOREX_COST"],
    )
    await resolve_owner_decision_for_order(
        db_session,
        order_id=order_id,
        code="INTERNAL_SABLON_FOREX_COST",
        status="resolved",
        note="Forex cost confirmat.",
        current_user=_admin_user(),
    )
    evaluation = await assert_production_release_allowed(db_session, order_id)
    assert evaluation.release_status == "RELEASE_ALLOWED"
    gate = await assert_task_startable(db_session, order_id=order_id, task_id="T-GUARD")
    assert gate["readiness"]["is_startable"] is True


@pytest.mark.asyncio
async def test_unauthorized_resolution_rejected(db_session):
    order_id = GUARD_OID_BASE + 8
    await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=["INTERNAL_MONTAJ_RULE"],
    )
    with pytest.raises(HTTPException) as exc:
        await resolve_owner_decision_for_order(
            db_session,
            order_id=order_id,
            code="INTERNAL_MONTAJ_RULE",
            status="resolved",
            note="Operator nu poate rezolva.",
            current_user=_operator_user(),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_repeated_resolution_idempotent(db_session):
    order_id = GUARD_OID_BASE + 9
    await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=["INTERNAL_MONTAJ_RULE"],
    )
    first = await resolve_owner_decision_for_order(
        db_session,
        order_id=order_id,
        code="INTERNAL_MONTAJ_RULE",
        status="resolved",
        note="Montaj confirmat.",
        current_user=_admin_user(),
    )
    second = await resolve_owner_decision_for_order(
        db_session,
        order_id=order_id,
        code="INTERNAL_MONTAJ_RULE",
        status="resolved",
        note="Montaj confirmat.",
        current_user=_admin_user(),
    )
    assert first.idempotent is False
    assert second.idempotent is True
    order = await db_session.get(Orders, order_id)
    history = order.readiness_snapshot[OWNER_DECISION_RESOLUTIONS_KEY]["audit_history"]
    assert len(history) == 1


@pytest.mark.asyncio
async def test_repeated_blocked_start_deterministic(db_session):
    order_id = GUARD_OID_BASE + 10
    await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=["INTERNAL_SABLON_FOREX_COST"],
    )
    with pytest.raises(HTTPException) as first:
        await assert_production_release_allowed(db_session, order_id)
    with pytest.raises(HTTPException) as second:
        await assert_production_release_allowed(db_session, order_id)
    assert first.value.detail == second.value.detail


@pytest.fixture
def guard_http_fixture(db_fixture, db_session):
    order_id = GUARD_OID_BASE + 80 + int(uuid.uuid4().hex[:6], 16) % 10000

    async def _setup():
        await _seed_guard_order(
            db_session,
            order_id=order_id,
            owner_codes=["INTERNAL_SABLON_FOREX_COST"],
        )

    db_fixture.run(_setup())
    yield {"order_id": order_id, "db_fixture": db_fixture}
    _cleanup_overrides()


def test_legacy_execution_start_route_guarded(guard_http_fixture):
    client = _client_for(
        guard_http_fixture["db_fixture"],
        _user(f"exec-{uuid.uuid4().hex[:6]}", "operator"),
    )
    response = client.post(
        "/api/v1/execution/reality/start-task",
        json={
            "order_id": guard_http_fixture["order_id"],
            "task_id": "T-GUARD",
            "timestamp": "2026-07-15T10:00:00+00:00",
        },
    )
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "production_release_blocked"


def test_operator_task_action_route_guarded(guard_http_fixture):
    client = _client_for(
        guard_http_fixture["db_fixture"],
        _user(f"op-{uuid.uuid4().hex[:6]}", "operator"),
    )
    response = client.post(
        "/api/v1/operator/task-action",
        json={
            "order_id": guard_http_fixture["order_id"],
            "task_id": "T-GUARD",
            "action": "start",
            "timestamp": "2026-07-15T10:00:00+00:00",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "production_release_blocked"


def test_employee_mobile_start_route_guarded(guard_http_fixture):
    user_id = f"mob-{uuid.uuid4().hex[:6]}"
    order_id = guard_http_fixture["order_id"]

    async def _setup_mobile():
        from tests.test_employee_mobile_tasks import _seed_employee as seed_emp

        async with guard_http_fixture["db_fixture"].session_maker() as db_session:
            employee = await seed_emp(
                db_session,
                user_id=user_id,
                name="Mobile Guard Worker",
            )
            plan = (
                await db_session.execute(
                    select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
                )
            ).scalar_one()
            tasks = json.loads(plan.tasks_json)
            tasks[0]["assigned_employee_id"] = employee.id
            plan.tasks_json = json.dumps(tasks)
            order = await db_session.get(Orders, order_id)
            order.status = "in_production"
            await db_session.commit()

    guard_http_fixture["db_fixture"].run(_setup_mobile())

    client = _client_for(
        guard_http_fixture["db_fixture"],
        _user(user_id, "employee_mobile"),
    )
    response = client.patch(
        "/api/v1/employee-mobile/tasks/T-GUARD/start",
        json={"order_id": guard_http_fixture["order_id"]},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "production_release_blocked"


@pytest.mark.asyncio
async def test_partial_7h_remains_after_operational_resolution(db_session):
    order_id = GUARD_OID_BASE + 11
    snapshot_json = _build_snapshot_with_owner_decisions(
        ["INTERNAL_SABLON_FOREX_COST", "INTERNAL_AMBALARE_RULE"],
        quote_id=order_id,
        quote_snapshot_v2_id=order_id,
    )
    order = Orders(
        id=order_id,
        code=f"ORD-PARTIAL-{order_id}",
        client_name="Partial Client",
        status="locked",
        total_amount=1500.0,
        quote_snapshot_v2_id=order_id,
        snapshot_v2_json=snapshot_json,
        readiness_snapshot={},
    )
    db_session.add(order)
    await db_session.commit()

    frozen = evaluate_production_release(order)
    assert "INTERNAL_AMBALARE_RULE" in frozen.nonblocking_decision_codes

    await resolve_owner_decision_for_order(
        db_session,
        order_id=order_id,
        code="INTERNAL_SABLON_FOREX_COST",
        status="resolved",
        note="Forex rezolvat.",
        current_user=_admin_user(),
    )
    refreshed = await db_session.get(Orders, order_id)
    snapshot = OrderSnapshotV2.model_validate_json(refreshed.snapshot_v2_json)
    codes = {item.code for item in snapshot.owner_decisions_snapshot}
    assert "INTERNAL_AMBALARE_RULE" in codes
    assert "INTERNAL_SABLON_FOREX_COST" in codes


@pytest.mark.asyncio
async def test_mixed_blockers_only_production_block(db_session):
    order_id = GUARD_OID_BASE + 12
    await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=["INTERNAL_MONTAJ_RULE", "OVERHEAD_ALLOCATION_PENDING"],
    )
    with pytest.raises(HTTPException) as exc:
        await assert_production_release_allowed(db_session, order_id)
    codes = {item["code"] for item in exc.value.detail["blockers"]}
    assert codes == {"INTERNAL_MONTAJ_RULE"}


@pytest.mark.asyncio
async def test_acknowledged_insufficient_for_production_blocker(db_session):
    order_id = GUARD_OID_BASE + 13
    await _seed_guard_order(
        db_session,
        order_id=order_id,
        owner_codes=["INTERNAL_CONSUMABLES_RULE"],
    )
    await resolve_owner_decision_for_order(
        db_session,
        order_id=order_id,
        code="INTERNAL_CONSUMABLES_RULE",
        status="acknowledged",
        note="Doar confirmat, nu rezolvat complet.",
        current_user=_admin_user(),
    )
    with pytest.raises(HTTPException) as exc:
        await assert_production_release_allowed(db_session, order_id)
    assert exc.value.detail["release_status"] == "RELEASE_BLOCKED_OWNER_DECISIONS"


@pytest.mark.asyncio
async def test_legacy_order_without_v2_snapshot_allowed(db_session):
    order_id = GUARD_OID_BASE + 14
    quote = Quotes(
        code=f"QT-LEG-{order_id}",
        intake_code="IR-LEG",
        client_name="Legacy",
        status="accepted",
        version=1,
    )
    db_session.add(quote)
    await db_session.flush()
    db_session.add(
        Orders(
            id=order_id,
            code=f"ORD-LEG-{order_id}",
            quote_id=quote.id,
            quote_code=quote.code,
            client_name="Legacy",
            status="locked",
            snapshot_version=1,
            snapshot_line_items=json.dumps({"quote_input": {}}),
        )
    )
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-LEG-{order_id}",
            snapshot_version=1,
            tasks_json=json.dumps(_simple_plan_tasks()),
            total_estimated_time_minutes=60,
        )
    )
    await db_session.commit()
    evaluation = await assert_production_release_allowed(db_session, order_id)
    assert evaluation.release_status == "RELEASE_ALLOWED"


def test_production_release_status_endpoint(guard_http_fixture):
    client = _client_for(
        guard_http_fixture["db_fixture"],
        _user(f"status-{uuid.uuid4().hex[:6]}", "operator"),
    )
    response = client.get(
        f"/api/v1/execution/orders/{guard_http_fixture['order_id']}/production-release-status"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["release_status"] == "RELEASE_BLOCKED_OWNER_DECISIONS"
    assert body["policy"] == "ORDER_AND_PLAN_ALLOWED_TASK_START_BLOCKED"


def test_resolve_endpoint_unlocks_start(guard_http_fixture):
    db_fixture = guard_http_fixture["db_fixture"]
    order_id = guard_http_fixture["order_id"]

    admin_client = _client_for(db_fixture, _user(f"adm-{uuid.uuid4().hex[:6]}", "admin"))
    resolve_resp = admin_client.post(
        f"/api/v1/execution/orders/{order_id}/owner-decisions/INTERNAL_SABLON_FOREX_COST/resolve",
        json={"status": "resolved", "note": "Forex confirmat prin API."},
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["release_status"] == "RELEASE_ALLOWED"

    op_client = _client_for(db_fixture, _user(f"op2-{uuid.uuid4().hex[:6]}", "operator"))
    start_resp = op_client.post(
        "/api/v1/execution/reality/start-task",
        json={
            "order_id": order_id,
            "task_id": "T-GUARD",
            "timestamp": "2026-07-15T11:00:00+00:00",
        },
    )
    assert start_resp.status_code == 200
