"""Tests for OrderSnapshotV2 planning/readiness adapter (W5-T03)."""

from __future__ import annotations

import ast
import inspect
import json
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from schemas.order_snapshot_v2 import OrderSnapshotV2
from services.order_snapshot_v2_planning_readiness_adapter_service import (
    load_order_planning_readiness_contract,
    load_order_planning_readiness_input,
    readiness_authority_from_quote_input,
)
from services.task_readiness_service import (
    READINESS_WAITING_TEMPLATE_DECISION,
    evaluate_all_task_readiness,
)
from services.task_start_gate_service import assert_task_startable, load_order_quote_input
from tests.test_execution_owner_decision_production_release_guard import (
    NONBLOCKING,
    PRODUCTION_BLOCKERS,
    _build_snapshot_with_owner_decisions,
    _simple_plan_tasks,
)
from tests.test_execution_plan_v2_preview import (
    _build_order_snapshot_v2_json,
    _sample_product_definition,
    _seed_v2_order_with_snapshot,
)
from tests.test_task_readiness_dependencies import _build_volumetric_tasks

ADAPTER_OID_BASE = 22000
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _snapshot_with_preparation_canonical(
    *,
    quote_id: int,
    quote_snapshot_v2_id: int,
    preparation: dict,
) -> str:
    from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview
    from tests.test_execution_plan_v2_preview import _sample_aggregate

    pd = _sample_product_definition()
    pd.canonical_values.update(preparation)
    snapshot = OrderSnapshotV2(
        quote_id=quote_id,
        quote_snapshot_v2_id=quote_snapshot_v2_id,
        snapshot_code="OSN2-PLAN-001",
        content_hash="planhashplanhashplanhashplanhashpl",
        product_definition_snapshot=pd,
        product_aggregate_snapshot=_sample_aggregate(include_task_rules=True),
        commercial_price_proposal_snapshot=_commercial_preview(total=1500.0),
        estimated_internal_cost_snapshot=_internal_preview(total=620.0),
        accepted_commercial_total=1500.0,
        accepted_currency="RON",
        estimated_internal_total=620.0,
    )
    return snapshot.model_dump_json()


@pytest.mark.asyncio
async def test_v2_order_uses_frozen_snapshot_authority(db_session):
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=ADAPTER_OID_BASE + 1,
        snapshot_v2_json=_snapshot_with_preparation_canonical(
            quote_id=ADAPTER_OID_BASE + 1,
            quote_snapshot_v2_id=ADAPTER_OID_BASE + 1,
            preparation={
                "mounting_template_material_type": "paper",
                "mounting_template_area_m2": 1.5,
            },
        ),
    )
    payload = await load_order_planning_readiness_input(db_session, order.id)
    assert payload["_planning_readiness_authority"] == "FROZEN_ORDER_SNAPSHOT_V2"
    assert payload["mounting_template_material_type"] == "paper"
    assert payload["mounting_template_area_m2"] == 1.5


@pytest.mark.asyncio
async def test_v2_order_never_reads_legacy_snapshot_line_items(db_session):
    order_id = ADAPTER_OID_BASE + 2
    snapshot_json = _snapshot_with_preparation_canonical(
        quote_id=order_id,
        quote_snapshot_v2_id=order_id,
        preparation={"mounting_template_material_type": "forex", "mounting_template_area_m2": 2.0},
    )
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=order_id,
        snapshot_v2_json=snapshot_json,
    )
    order.snapshot_line_items = json.dumps(
        {
            "quote_input": {
                "mounting_template_material_type": "paper",
                "mounting_template_area_m2": 99.0,
            }
        }
    )
    await db_session.commit()

    payload = await load_order_planning_readiness_input(db_session, order_id)
    assert payload["mounting_template_material_type"] == "forex"
    assert payload["mounting_template_area_m2"] == 2.0


@pytest.mark.asyncio
async def test_missing_v2_snapshot_fails_closed(db_session):
    order_id = ADAPTER_OID_BASE + 3
    order = Orders(
        id=order_id,
        code=f"ORD-ADAPTER-{order_id}",
        client_name="Adapter Client",
        status="locked",
        total_amount=1500.0,
        quote_snapshot_v2_id=order_id,
        snapshot_v2_json=None,
        snapshot_line_items=json.dumps({"quote_input": {"mounting_template_material_type": "paper"}}),
    )
    db_session.add(order)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await load_order_planning_readiness_input(db_session, order_id)
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == "ORDER_SNAPSHOT_V2_MISSING"


@pytest.mark.asyncio
async def test_corrupt_v2_snapshot_fails_closed(db_session):
    order_id = ADAPTER_OID_BASE + 4
    order = Orders(
        id=order_id,
        code=f"ORD-ADAPTER-{order_id}",
        client_name="Adapter Client",
        status="locked",
        total_amount=1500.0,
        quote_snapshot_v2_id=order_id,
        snapshot_v2_json="{not-valid-json",
    )
    db_session.add(order)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await load_order_planning_readiness_input(db_session, order_id)
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == "ORDER_SNAPSHOT_V2_CORRUPT"


@pytest.mark.asyncio
async def test_legacy_order_uses_isolated_legacy_path(db_session):
    order_id = ADAPTER_OID_BASE + 5
    order = Orders(
        id=order_id,
        code=f"ORD-LEGACY-{order_id}",
        client_name="Legacy Client",
        status="locked",
        total_amount=1500.0,
        snapshot_version=1,
        snapshot_line_items=json.dumps(
            {
                "quote_input": {
                    "mounting_template_material_type": "paper",
                    "mounting_template_area_m2": 3.0,
                }
            }
        ),
    )
    db_session.add(order)
    await db_session.commit()

    payload = await load_order_planning_readiness_input(db_session, order_id)
    assert payload["_planning_readiness_authority"] == "LEGACY_ORDER_INPUT"
    assert payload["mounting_template_material_type"] == "paper"


@pytest.mark.asyncio
async def test_v2_preparation_gates_use_frozen_canonical_values(db_session):
    order_id = ADAPTER_OID_BASE + 6
    await _seed_v2_order_with_snapshot(
        db_session,
        order_id=order_id,
        snapshot_v2_json=_snapshot_with_preparation_canonical(
            quote_id=order_id,
            quote_snapshot_v2_id=order_id,
            preparation={
                "mounting_template_enabled": True,
                "mounting_template_material_type": "paper",
                "mounting_template_area_m2": 2.5,
            },
        ),
    )
    tasks = _build_volumetric_tasks(sandu_id=4)
    reality = [
        {
            "task_id": "T-001",
            "employee_id": 9,
            "started_at": "2026-06-12T08:00:00+00:00",
            "ended_at": "2026-06-12T08:30:00+00:00",
        }
    ]
    quote_input = await load_order_quote_input(db_session, order_id)
    readiness = evaluate_all_task_readiness(
        tasks,
        reality,
        employee_id=4,
        quote_input=quote_input,
    )
    assert readiness["T-008"]["readiness_status"] == READINESS_WAITING_TEMPLATE_DECISION


@pytest.mark.asyncio
async def test_owner_decision_guard_unchanged_with_adapter(db_session):
    order_id = ADAPTER_OID_BASE + 7
    snapshot_json = _build_snapshot_with_owner_decisions(PRODUCTION_BLOCKERS, quote_id=order_id)
    order = Orders(
        id=order_id,
        code=f"ORD-GUARD-{order_id}",
        quote_id=order_id,
        client_name="Guard",
        status="locked",
        total_amount=1500.0,
        quote_snapshot_v2_id=order_id,
        snapshot_v2_json=snapshot_json,
    )
    db_session.add(order)
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-GUARD-{order_id}",
            snapshot_version=1,
            tasks_json=json.dumps(_simple_plan_tasks()),
            total_estimated_time_minutes=60,
        )
    )
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await assert_task_startable(db_session, order_id=order_id, task_id="T-GUARD")
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "production_release_blocked"


@pytest.mark.asyncio
async def test_internal_analysis_decisions_nonblocking_with_adapter(db_session):
    order_id = ADAPTER_OID_BASE + 8
    snapshot_json = _build_snapshot_with_owner_decisions(NONBLOCKING, quote_id=order_id)
    order = Orders(
        id=order_id,
        code=f"ORD-NB-{order_id}",
        quote_id=order_id,
        client_name="NB",
        status="locked",
        total_amount=1500.0,
        quote_snapshot_v2_id=order_id,
        snapshot_v2_json=snapshot_json,
    )
    db_session.add(order)
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-NB-{order_id}",
            snapshot_version=1,
            tasks_json=json.dumps(_simple_plan_tasks()),
            total_estimated_time_minutes=60,
        )
    )
    await db_session.commit()

    result = await assert_task_startable(db_session, order_id=order_id, task_id="T-GUARD")
    assert result["readiness"]["is_startable"] is True


@pytest.mark.asyncio
async def test_repeated_readiness_reads_deterministic(db_session):
    order_id = ADAPTER_OID_BASE + 9
    await _seed_v2_order_with_snapshot(
        db_session,
        order_id=order_id,
        snapshot_v2_json=_snapshot_with_preparation_canonical(
            quote_id=order_id,
            quote_snapshot_v2_id=order_id,
            preparation={"mounting_template_material_type": "forex", "mounting_template_area_m2": 1.1},
        ),
    )
    one = await load_order_planning_readiness_input(db_session, order_id)
    two = await load_order_planning_readiness_input(db_session, order_id)
    assert one == two


@pytest.mark.asyncio
async def test_adapter_contract_exposes_frozen_identity_version(db_session):
    order_id = ADAPTER_OID_BASE + 10
    await _seed_v2_order_with_snapshot(db_session, order_id=order_id)
    contract = await load_order_planning_readiness_contract(db_session, order_id)
    assert contract is not None
    assert contract.authority_source == "FROZEN_ORDER_SNAPSHOT_V2"
    assert contract.frozen_task_identity_version == "frozen_task_identity/v1"


def test_adapter_service_does_not_reference_snapshot_line_items_for_v2_routing():
    path = BACKEND_ROOT / "services" / "order_snapshot_v2_planning_readiness_adapter_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    legacy_fn = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_build_legacy_readiness_input":
            legacy_fn = node
            break
    assert legacy_fn is not None
    legacy_source = ast.get_source_segment(path.read_text(encoding="utf-8"), legacy_fn) or ""
    assert "snapshot_line_items" in legacy_source

    v2_fn = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_extract_preparation_from_frozen_snapshot":
            v2_fn = node
            break
    assert v2_fn is not None
    v2_source = ast.get_source_segment(path.read_text(encoding="utf-8"), v2_fn) or ""
    assert "snapshot_line_items" not in v2_source
    assert "canonical_values" in v2_source


def test_task_start_gate_load_order_quote_input_delegates_to_adapter():
    source = inspect.getsource(load_order_quote_input)
    assert "load_order_planning_readiness_input" in source
    assert "snapshot_line_items" not in source


def test_readiness_authority_helper_defaults_legacy():
    assert readiness_authority_from_quote_input({}) == "LEGACY_ORDER_INPUT"
    assert (
        readiness_authority_from_quote_input({"_planning_readiness_authority": "FROZEN_ORDER_SNAPSHOT_V2"})
        == "FROZEN_ORDER_SNAPSHOT_V2"
    )
