"""Tests for Order Snapshot V2 convert (Step 9.2)."""

from __future__ import annotations

import ast
import hashlib
import json
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from services.intake_v3_quote_linkage_utils import CONVERT_DECISION_JSON_KEY
from services.intake_v4_quote_linkage_utils import V4_ACCEPTED_STATUS
from services.intake_v6_commercial_quote_service import INTAKE_V6_LINKAGE_JSON_KEY
from services.intake_v6_quote_to_order_service import accept_v6_quote, convert_v6_quote_to_order
from services.order_snapshot_v2_convert_service import (
    FORBIDDEN_IMPORT_SUBSTRINGS,
    convert_accepted_quote_snapshot_v2_to_order,
)
from tests.test_quote_snapshot_v2_accept_gate import (
    _insert_snapshot,
    _seed_v6_quote,
    _test_user,
    _valid_accept_body,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


@pytest.fixture(autouse=True)
def no_workspace_critical_blockers(monkeypatch):
    async def _empty(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "services.intake_v6_quote_to_order_service._collect_accept_critical_blockers",
        _empty,
    )


def _valid_convert_body(**overrides) -> dict:
    body = {
        "convert_reason": "Convert accepted snapshot v2 quote to locked order.",
        "reviewer_confirmation": True,
        "confirm_quote_accepted": True,
        "confirm_pricing_review_completed": True,
        "confirm_create_order_only": True,
        "confirm_no_execution_plan": True,
        "confirm_no_execution_tasks": True,
        "confirm_no_inventory": True,
        "confirm_production_separate": True,
    }
    body.update(overrides)
    return body


async def _accept_v2_quote(db, quote, workspace_id, **snapshot_kwargs):
    await _insert_snapshot(
        db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        **snapshot_kwargs,
    )
    await accept_v6_quote(
        db,
        quote.id,
        _valid_accept_body(),
        _test_user(),
    )
    refreshed = await db.get(Quotes, quote.id)
    assert refreshed is not None
    assert refreshed.accepted_snapshot_v2_id is not None
    return refreshed


@pytest.mark.asyncio
async def test_convert_success_creates_locked_order(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )

    assert result["converted"] is True
    assert result["order_created"] is True
    order = await volumetric_v2_db.get(Orders, result["order_id"])
    assert order is not None
    assert order.status == "locked"
    assert order.quote_snapshot_v2_id == accepted.accepted_snapshot_v2_id


@pytest.mark.asyncio
async def test_total_amount_from_snapshot_not_grand_total(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=999.0)
    accepted = await _accept_v2_quote(
        volumetric_v2_db,
        quote,
        workspace_id,
        commercial_total=2400.0,
    )

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )

    order = await volumetric_v2_db.get(Orders, result["order_id"])
    refreshed_quote = await volumetric_v2_db.get(Quotes, accepted.id)
    assert float(order.total_amount) == 2400.0
    assert float(refreshed_quote.grand_total or 0) == 999.0
    assert float(order.total_amount) != float(refreshed_quote.grand_total or 0)


@pytest.mark.asyncio
async def test_snapshot_line_items_null_on_v2_order(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )

    order = await volumetric_v2_db.get(Orders, result["order_id"])
    assert order.snapshot_line_items is None
    assert order.snapshot_v2_json is not None


@pytest.mark.asyncio
async def test_convert_does_not_create_execution_plan(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)

    plans_before = await volumetric_v2_db.scalar(select(func.count()).select_from(ExecutionPlan))
    await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )
    plans_after = await volumetric_v2_db.scalar(select(func.count()).select_from(ExecutionPlan))
    assert plans_after == plans_before


@pytest.mark.asyncio
async def test_duplicate_convert_rejected(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)

    await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )

    with pytest.raises(HTTPException) as exc:
        await convert_v6_quote_to_order(
            volumetric_v2_db,
            accepted.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "ORDER_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_convert_quote_not_found(volumetric_v2_db):
    with pytest.raises(HTTPException) as exc:
        await convert_accepted_quote_snapshot_v2_to_order(
            volumetric_v2_db,
            999999,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "QUOTE_NOT_FOUND"


@pytest.mark.asyncio
async def test_convert_snapshot_v2_record_not_found(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    quote.status = V4_ACCEPTED_STATUS
    quote.accepted_snapshot_v2_id = 999999
    await volumetric_v2_db.commit()

    with pytest.raises(HTTPException) as exc:
        await convert_accepted_quote_snapshot_v2_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "SNAPSHOT_V2_NOT_FOUND"


@pytest.mark.asyncio
async def test_convert_quote_not_accepted(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
    )
    quote.accepted_snapshot_v2_id = snapshot.id
    quote.status = "draft"
    await volumetric_v2_db.commit()

    with pytest.raises(HTTPException) as exc:
        await convert_accepted_quote_snapshot_v2_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "QUOTE_NOT_ACCEPTED"


@pytest.mark.asyncio
async def test_convert_missing_accepted_snapshot_v2_id(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    quote.status = V4_ACCEPTED_STATUS
    await volumetric_v2_db.commit()

    with pytest.raises(HTTPException) as exc:
        await convert_accepted_quote_snapshot_v2_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "MISSING_ACCEPTED_SNAPSHOT_V2"


async def _manual_accepted_v2_quote(db, quote, snapshot):
    """Mark quote accepted with snapshot FK without running accept gate."""
    quote.status = V4_ACCEPTED_STATUS
    quote.accepted_snapshot_v2_id = snapshot.id
    await db.commit()
    await db.refresh(quote)
    return quote


@pytest.mark.asyncio
async def test_convert_hard_blocked_readiness_rejected(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        readiness="blocked_forbidden_path",
    )
    await _manual_accepted_v2_quote(volumetric_v2_db, quote, snapshot)

    with pytest.raises(HTTPException) as exc:
        await convert_v6_quote_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "SNAPSHOT_READINESS_BLOCKED"


@pytest.mark.asyncio
async def test_convert_snapshot_not_frozen(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        status="draft",
    )
    quote.status = V4_ACCEPTED_STATUS
    quote.accepted_snapshot_v2_id = snapshot.id
    await volumetric_v2_db.commit()

    with pytest.raises(HTTPException) as exc:
        await convert_accepted_quote_snapshot_v2_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "SNAPSHOT_NOT_FROZEN"


@pytest.mark.asyncio
async def test_convert_snapshot_hash_mismatch(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
    )
    quote.status = V4_ACCEPTED_STATUS
    quote.accepted_snapshot_v2_id = snapshot.id
    snapshot.content_hash = "deadbeefdeadbeefdeadbeefdeadbeef"
    await volumetric_v2_db.commit()

    with pytest.raises(HTTPException) as exc:
        await convert_accepted_quote_snapshot_v2_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "SNAPSHOT_HASH_MISMATCH"


@pytest.mark.asyncio
async def test_convert_snapshot_quote_id_mismatch(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    other_quote, _, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=other_quote.id,
        workspace_id=workspace_id,
    )
    quote.status = V4_ACCEPTED_STATUS
    quote.accepted_snapshot_v2_id = snapshot.id
    await volumetric_v2_db.commit()

    with pytest.raises(HTTPException) as exc:
        await convert_accepted_quote_snapshot_v2_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "SNAPSHOT_QUOTE_MISMATCH"


@pytest.mark.asyncio
async def test_convert_commercial_total_zero_blocked(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        commercial_total=0.0,
    )
    await _manual_accepted_v2_quote(volumetric_v2_db, quote, snapshot)

    with pytest.raises(HTTPException) as exc:
        await convert_v6_quote_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "SNAPSHOT_COMMERCIAL_TOTAL_MISSING"


@pytest.mark.asyncio
async def test_convert_internal_snapshot_missing(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
    )
    parsed = QuoteSnapshotV2.model_validate_json(snapshot.snapshot_json)
    parsed.estimated_internal_cost_snapshot = None
    snapshot.snapshot_json = parsed.model_dump_json()
    snapshot.content_hash = hashlib.sha256(snapshot.snapshot_json.encode()).hexdigest()[:32]
    await volumetric_v2_db.commit()
    await _manual_accepted_v2_quote(volumetric_v2_db, quote, snapshot)

    with pytest.raises(HTTPException) as exc:
        await convert_v6_quote_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] in {"SNAPSHOT_INTERNAL_MISSING", "SNAPSHOT_JSON_INVALID"}


@pytest.mark.asyncio
async def test_convert_commercial_snapshot_missing(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
    )
    parsed = QuoteSnapshotV2.model_validate_json(snapshot.snapshot_json)
    parsed.commercial_price_proposal_snapshot = None
    snapshot.snapshot_json = parsed.model_dump_json()
    snapshot.content_hash = hashlib.sha256(snapshot.snapshot_json.encode()).hexdigest()[:32]
    await volumetric_v2_db.commit()

    with pytest.raises(HTTPException) as exc:
        await accept_v6_quote(
            volumetric_v2_db,
            quote.id,
            _valid_accept_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] in {
        "SNAPSHOT_COMMERCIAL_MISSING",
        "SNAPSHOT_ACCEPT_BLOCKED",
        "SNAPSHOT_JSON_INVALID",
    }


@pytest.mark.asyncio
async def test_partial_snapshot_without_accept_gate_blocked(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        readiness="partial_with_owner_decisions",
        owner_decisions=[
            {
                "code": "DEBITARE_SPATE_BASIS_ML_VS_M2",
                "label": "Debitare spate basis",
                "source": "commercial_price_proposal",
            }
        ],
    )
    quote.status = V4_ACCEPTED_STATUS
    quote.accepted_snapshot_v2_id = snapshot.id
    await volumetric_v2_db.commit()

    with pytest.raises(HTTPException) as exc:
        await convert_accepted_quote_snapshot_v2_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "PARTIAL_SNAPSHOT_ACCEPT_GATE_MISSING"


@pytest.mark.asyncio
async def test_partial_snapshot_with_accept_gate_converts(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        readiness="partial_with_owner_decisions",
        owner_decisions=[
            {
                "code": "DEBITARE_SPATE_BASIS_ML_VS_M2",
                "label": "Debitare spate basis",
                "source": "commercial_price_proposal",
            }
        ],
    )
    await accept_v6_quote(
        volumetric_v2_db,
        quote.id,
        _valid_accept_body(confirm_owner_decisions_acknowledged=True),
        _test_user(),
    )

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        quote.id,
        _valid_convert_body(),
        _test_user(),
    )
    assert result["converted"] is True


@pytest.mark.asyncio
async def test_ron_currency_uses_commercial_total(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(
        volumetric_v2_db,
        quote,
        workspace_id,
        commercial_total=1750.0,
    )

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )

    order = await volumetric_v2_db.get(Orders, result["order_id"])
    payload = OrderSnapshotV2.model_validate_json(order.snapshot_v2_json)
    assert payload.accepted_currency == "RON"
    assert float(order.total_amount) == 1750.0
    assert payload.accepted_commercial_total == 1750.0


@pytest.mark.asyncio
async def test_non_ron_currency_blocked(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
    )
    parsed = QuoteSnapshotV2.model_validate_json(snapshot.snapshot_json)
    parsed.commercial_price_proposal_snapshot.currency = "EUR"
    snapshot.snapshot_json = parsed.model_dump_json()
    snapshot.content_hash = hashlib.sha256(snapshot.snapshot_json.encode()).hexdigest()[:32]
    await volumetric_v2_db.commit()

    await accept_v6_quote(
        volumetric_v2_db,
        quote.id,
        _valid_accept_body(),
        _test_user(),
    )

    with pytest.raises(HTTPException) as exc:
        await convert_v6_quote_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "ORDER_CONVERT_CURRENCY_POLICY_REQUIRED"


@pytest.mark.asyncio
async def test_order_snapshot_v2_json_policy_fields(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )

    order = await volumetric_v2_db.get(Orders, result["order_id"])
    payload = OrderSnapshotV2.model_validate_json(order.snapshot_v2_json)
    assert payload.no_reprice_policy is True
    assert payload.execution_plan_source == "order_snapshot_v2"
    assert payload.execution_plan_created is False
    assert payload.quote_snapshot_v2_id == accepted.accepted_snapshot_v2_id
    assert payload.commercial_price_proposal_snapshot is not None
    assert payload.estimated_internal_cost_snapshot is not None


@pytest.mark.asyncio
async def test_convert_persists_quote_snapshot_v2_id_fk(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )

    order = await volumetric_v2_db.get(Orders, result["order_id"])
    assert order.quote_snapshot_v2_id == accepted.accepted_snapshot_v2_id


@pytest.mark.asyncio
async def test_convert_updates_linkage_convert_decision(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )

    refreshed = await volumetric_v2_db.get(Quotes, accepted.id)
    notes = json.loads(refreshed.notes)
    convert_record = notes[INTAKE_V6_LINKAGE_JSON_KEY][CONVERT_DECISION_JSON_KEY]
    assert convert_record["order_created"] is True
    assert convert_record["order_id"] == result["order_id"]
    assert convert_record["quote_snapshot_v2_id"] == accepted.accepted_snapshot_v2_id


@pytest.mark.asyncio
async def test_accepted_commercial_total_separate_from_internal(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(
        volumetric_v2_db,
        quote,
        workspace_id,
        commercial_total=1500.0,
        internal_total=620.0,
    )

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )

    order = await volumetric_v2_db.get(Orders, result["order_id"])
    payload = OrderSnapshotV2.model_validate_json(order.snapshot_v2_json)
    assert payload.accepted_commercial_total == 1500.0
    assert payload.estimated_internal_total == 620.0
    assert payload.accepted_commercial_total != payload.estimated_internal_total


@pytest.mark.asyncio
async def test_legacy_path_without_v2_id_uses_legacy_errors(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    quote.status = V4_ACCEPTED_STATUS
    await volumetric_v2_db.commit()

    with pytest.raises(HTTPException) as exc:
        await convert_v6_quote_to_order(
            volumetric_v2_db,
            quote.id,
            _valid_convert_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "FINAL_PRICE_MISSING"
    assert exc.value.detail["error"] != "MISSING_ACCEPTED_SNAPSHOT_V2"


def _forbidden_convert_imports() -> set[str]:
    path = Path(__file__).resolve().parents[1] / "services" / "order_snapshot_v2_convert_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
    return modules


def test_convert_service_does_not_import_quote_orchestrator():
    modules = _forbidden_convert_imports()
    assert not any("quote_orchestrator" in mod for mod in modules)


def test_convert_service_does_not_import_cost_engine():
    modules = _forbidden_convert_imports()
    assert not any("cost_engine" in mod for mod in modules)


def test_convert_service_does_not_import_aggregate_cost_bom_price_bridge():
    modules = _forbidden_convert_imports()
    assert not any("aggregate_cost_bom_price_bridge" in mod for mod in modules)


def test_convert_service_declares_forbidden_import_guard():
    assert "quote_orchestrator" in FORBIDDEN_IMPORT_SUBSTRINGS
    assert "cost_engine_service" in FORBIDDEN_IMPORT_SUBSTRINGS
    assert "aggregate_cost_bom_price_bridge" in FORBIDDEN_IMPORT_SUBSTRINGS


@pytest.mark.asyncio
async def test_convert_confirmations_required(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)

    with pytest.raises(HTTPException) as exc:
        await convert_v6_quote_to_order(
            volumetric_v2_db,
            accepted.id,
            _valid_convert_body(reviewer_confirmation=False),
            _test_user(),
        )
    assert exc.value.detail["error"] == "CONFIRMATIONS_REQUIRED"


@pytest.mark.asyncio
async def test_convert_result_includes_order_snapshot_v2_convert_block(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )

    convert_block = result.get("order_snapshot_v2_convert") or {}
    assert convert_block.get("status") == "converted"
    assert convert_block.get("order_id") == result["order_id"]
    assert convert_block.get("accepted_commercial_total") == 1500.0


@pytest.mark.asyncio
async def test_v2_branch_delegates_before_legacy_order_create():
    import inspect

    from services.intake_v6_quote_to_order_service import convert_v6_quote_to_order

    source = inspect.getsource(convert_v6_quote_to_order)
    delegate_pos = source.index("convert_accepted_quote_snapshot_v2_to_order")
    create_pos = source.index("orders_service.create")
    assert delegate_pos < create_pos
