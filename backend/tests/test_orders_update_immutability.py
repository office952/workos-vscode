"""Contract tests for order financial immutability on PUT /orders/{id} and PUT /orders/batch."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from models.orders import Orders
from schemas.order_snapshot_v2 import OrderSnapshotV2
from tests.test_execution_flow import _complete_snapshot_dict
from tests.test_execution_plan_v2_preview import _build_order_snapshot_v2_json

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SLICE_10_1_PATHS = (
    BACKEND_ROOT / "services" / "order_immutability_service.py",
    BACKEND_ROOT / "routers" / "orders.py",
    Path(__file__).resolve(),
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
)

_IMMUT_OID_BASE = 19700


def _forbidden_imports_in_paths() -> set[str]:
    found: set[str] = set()
    for path in SLICE_10_1_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                    if part in node.module:
                        found.add(node.module)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                        if part in alias.name:
                            found.add(alias.name)
    return found


async def _seed_locked_v2_order(db_session, *, order_id: int) -> Orders:
    snapshot_json = _build_order_snapshot_v2_json(
        quote_id=order_id,
        quote_snapshot_v2_id=1,
    )
    order = Orders(
        id=order_id,
        code=f"ORD-IMMUT-V2-{order_id}",
        client_name="Immutability V2 Client",
        status="locked",
        locked_at="2026-06-30T10:00:00+00:00",
        total_amount=1500.0,
        snapshot_version=1,
        quote_id=order_id,
        quote_snapshot_v2_id=1,
        snapshot_v2_json=snapshot_json,
        notes="original notes",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


async def _seed_unlocked_legacy_order(db_session, *, order_id: int) -> Orders:
    order = Orders(
        id=order_id,
        code=f"ORD-IMMUT-OPEN-{order_id}",
        client_name="Open Legacy Client",
        status="confirmed",
        total_amount=100.0,
        notes="legacy open",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


async def _seed_locked_legacy_order(db_session, *, order_id: int) -> Orders:
    order = Orders(
        id=order_id,
        code=f"ORD-IMMUT-LEG-{order_id}",
        client_name="Locked Legacy Client",
        status="locked",
        locked_at="2026-06-30T09:00:00+00:00",
        total_amount=1398.25,
        snapshot_version=1,
        snapshot_line_items=json.dumps(_complete_snapshot_dict()),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


def _put(auth_client, order_id: int, payload: dict):
    return auth_client.put(f"/api/v1/entities/orders/{order_id}", json=payload)


def _batch_put(auth_client, items: list[dict]):
    return auth_client.put(
        "/api/v1/entities/orders/batch",
        json={"items": items},
    )


def _batch_item(order_id: int, updates: dict) -> dict:
    return {"id": order_id, "updates": updates}


def _assert_immutable_response(resp) -> None:
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["error"] == "ORDER_FINANCIAL_FIELDS_IMMUTABLE"
    assert detail["blocked_fields"]


@pytest.mark.asyncio
async def test_locked_v2_total_amount_blocked(db_session, auth_client):
    order = await _seed_locked_v2_order(db_session, order_id=_IMMUT_OID_BASE + 1)
    resp = _put(auth_client, order.id, {"total_amount": 9999.0})
    _assert_immutable_response(resp)
    assert "total_amount" in resp.json()["detail"]["blocked_fields"]


@pytest.mark.asyncio
async def test_locked_v2_snapshot_line_items_blocked(db_session, auth_client):
    order = await _seed_locked_v2_order(db_session, order_id=_IMMUT_OID_BASE + 2)
    resp = _put(auth_client, order.id, {"snapshot_line_items": '{"tampered": true}'})
    _assert_immutable_response(resp)
    assert "snapshot_line_items" in resp.json()["detail"]["blocked_fields"]


@pytest.mark.asyncio
async def test_locked_v2_snapshot_version_blocked(db_session, auth_client):
    order = await _seed_locked_v2_order(db_session, order_id=_IMMUT_OID_BASE + 3)
    resp = _put(auth_client, order.id, {"snapshot_version": 99})
    _assert_immutable_response(resp)
    assert "snapshot_version" in resp.json()["detail"]["blocked_fields"]


@pytest.mark.asyncio
async def test_locked_v2_notes_allowed(db_session, auth_client):
    order = await _seed_locked_v2_order(db_session, order_id=_IMMUT_OID_BASE + 4)
    before_snapshot = order.snapshot_v2_json
    before_payload = OrderSnapshotV2.model_validate_json(before_snapshot)
    before_commercial = before_payload.accepted_commercial_total

    resp = _put(auth_client, order.id, {"notes": "operator follow-up note"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["notes"] == "operator follow-up note"
    assert body["total_amount"] == 1500.0

    refreshed = await db_session.get(Orders, order.id)
    assert refreshed.snapshot_v2_json == before_snapshot
    after_payload = OrderSnapshotV2.model_validate_json(refreshed.snapshot_v2_json)
    assert after_payload.accepted_commercial_total == before_commercial


@pytest.mark.asyncio
async def test_unlocked_legacy_total_amount_allowed(db_session, auth_client):
    order = await _seed_unlocked_legacy_order(db_session, order_id=_IMMUT_OID_BASE + 5)
    resp = _put(auth_client, order.id, {"total_amount": 250.0})
    assert resp.status_code == 200
    assert resp.json()["total_amount"] == 250.0


@pytest.mark.asyncio
async def test_locked_legacy_financial_fields_blocked(db_session, auth_client):
    order = await _seed_locked_legacy_order(db_session, order_id=_IMMUT_OID_BASE + 6)
    resp = _put(auth_client, order.id, {"total_amount": 1.0})
    _assert_immutable_response(resp)


@pytest.mark.asyncio
async def test_locked_legacy_notes_allowed(db_session, auth_client):
    order = await _seed_locked_legacy_order(db_session, order_id=_IMMUT_OID_BASE + 7)
    before_line_items = order.snapshot_line_items
    resp = _put(auth_client, order.id, {"notes": "legacy note update"})
    assert resp.status_code == 200
    assert resp.json()["notes"] == "legacy note update"

    refreshed = await db_session.get(Orders, order.id)
    assert refreshed.snapshot_line_items == before_line_items
    assert refreshed.total_amount == 1398.25


def test_no_forbidden_imports_in_slice_paths():
    assert _forbidden_imports_in_paths() == set()


# --- Batch PUT /orders/batch (Slice 10.1 extension) ---

_BATCH_OID_BASE = 19800


@pytest.mark.asyncio
async def test_batch_locked_v2_total_amount_blocked(db_session, auth_client):
    order = await _seed_locked_v2_order(db_session, order_id=_BATCH_OID_BASE + 1)
    resp = _batch_put(auth_client, [_batch_item(order.id, {"total_amount": 9999.0})])
    _assert_immutable_response(resp)
    assert "total_amount" in resp.json()["detail"]["blocked_fields"]
    assert resp.json()["detail"]["order_id"] == order.id


@pytest.mark.asyncio
async def test_batch_locked_v2_snapshot_line_items_blocked(db_session, auth_client):
    order = await _seed_locked_v2_order(db_session, order_id=_BATCH_OID_BASE + 2)
    resp = _batch_put(
        auth_client,
        [_batch_item(order.id, {"snapshot_line_items": '{"tampered": true}'})],
    )
    _assert_immutable_response(resp)
    assert "snapshot_line_items" in resp.json()["detail"]["blocked_fields"]


@pytest.mark.asyncio
async def test_batch_locked_v2_snapshot_version_blocked(db_session, auth_client):
    order = await _seed_locked_v2_order(db_session, order_id=_BATCH_OID_BASE + 3)
    resp = _batch_put(auth_client, [_batch_item(order.id, {"snapshot_version": 99})])
    _assert_immutable_response(resp)
    assert "snapshot_version" in resp.json()["detail"]["blocked_fields"]


@pytest.mark.asyncio
async def test_batch_locked_v2_notes_allowed(db_session, auth_client):
    order = await _seed_locked_v2_order(db_session, order_id=_BATCH_OID_BASE + 4)
    before_snapshot = order.snapshot_v2_json
    before_payload = OrderSnapshotV2.model_validate_json(before_snapshot)
    before_commercial = before_payload.accepted_commercial_total

    resp = _batch_put(auth_client, [_batch_item(order.id, {"notes": "batch note update"})])
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["notes"] == "batch note update"
    assert body[0]["total_amount"] == 1500.0

    refreshed = await db_session.get(Orders, order.id)
    assert refreshed.snapshot_v2_json == before_snapshot
    after_payload = OrderSnapshotV2.model_validate_json(refreshed.snapshot_v2_json)
    assert after_payload.accepted_commercial_total == before_commercial


@pytest.mark.asyncio
async def test_batch_unlocked_legacy_total_amount_allowed(db_session, auth_client):
    order = await _seed_unlocked_legacy_order(db_session, order_id=_BATCH_OID_BASE + 5)
    resp = _batch_put(auth_client, [_batch_item(order.id, {"total_amount": 250.0})])
    assert resp.status_code == 200
    assert resp.json()[0]["total_amount"] == 250.0


@pytest.mark.asyncio
async def test_batch_mixed_locked_and_unlocked_financial_fail_closed(db_session, auth_client):
    locked = await _seed_locked_v2_order(db_session, order_id=_BATCH_OID_BASE + 6)
    unlocked = await _seed_unlocked_legacy_order(db_session, order_id=_BATCH_OID_BASE + 7)
    locked_before_total = locked.total_amount
    unlocked_before_total = unlocked.total_amount

    resp = _batch_put(
        auth_client,
        [
            _batch_item(unlocked.id, {"total_amount": 500.0}),
            _batch_item(locked.id, {"total_amount": 8888.0}),
        ],
    )
    _assert_immutable_response(resp)
    assert resp.json()["detail"]["error"] == "ORDER_FINANCIAL_FIELDS_IMMUTABLE"

    refreshed_locked = await db_session.get(Orders, locked.id)
    refreshed_unlocked = await db_session.get(Orders, unlocked.id)
    assert refreshed_locked.total_amount == locked_before_total
    assert refreshed_unlocked.total_amount == unlocked_before_total


@pytest.mark.asyncio
async def test_batch_locked_v2_financial_block_preserves_snapshot(db_session, auth_client):
    order = await _seed_locked_v2_order(db_session, order_id=_BATCH_OID_BASE + 8)
    before_snapshot = order.snapshot_v2_json
    before_payload = OrderSnapshotV2.model_validate_json(before_snapshot)
    before_commercial = before_payload.accepted_commercial_total

    resp = _batch_put(auth_client, [_batch_item(order.id, {"total_amount": 7777.0})])
    _assert_immutable_response(resp)

    refreshed = await db_session.get(Orders, order.id)
    assert refreshed.snapshot_v2_json == before_snapshot
    after_payload = OrderSnapshotV2.model_validate_json(refreshed.snapshot_v2_json)
    assert after_payload.accepted_commercial_total == before_commercial
    assert refreshed.total_amount == 1500.0


def test_batch_route_has_no_price_endpoint_reference():
    router_source = (BACKEND_ROOT / "routers" / "orders.py").read_text(encoding="utf-8")
    batch_section = router_source.split("@router.put(\"/batch\"")[1].split("@router.put(\"/{id}\"")[0]
    assert "/price" not in batch_section
