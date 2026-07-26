"""Sold-scope materialization tests — filtered planned_tasks → operational_tasks only."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from models.execution_plan import ExecutionPlan
from services.execution_plan_v2_materialize_service import materialize_execution_plan_v2_operational_tasks
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview
from tests.execution_sold_scope_fixtures import offer_scope, snapshot_with_scope
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot

_SCOPED_OID = lambda: 287000 + int(uuid.uuid4().hex[:6], 16) % 1000000


def _task_keys(items: list[dict]) -> set[str]:
    return {str(item.get("task_key") or item.get("task_id") or item.get("source_task_key")) for item in items}


def _module_codes(tasks: list[dict]) -> set[str]:
    return {code for code in (t.get("source_module_code") for t in tasks) if code}


async def _seed_persisted_scoped_plan(
    db_session,
    *,
    runtime: list[str] | None = None,
    use_legacy: bool = False,
    order_id: int | None = None,
):
    oid = order_id or _SCOPED_OID()
    if use_legacy:
        scope = snapshot_with_scope(offer_scope=None)
    else:
        scope = snapshot_with_scope(offer_scope=offer_scope(runtime=runtime or []))
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=oid,
        snapshot_v2_json=scope.model_dump_json(),
    )
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    persist = await create_execution_plan_v2_from_order(db_session, order.id)
    return order, preview, persist


async def _load_envelope(db_session, order_id: int) -> dict:
    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one()
    return json.loads(plan.tasks_json)


# ---------------------------------------------------------------------------
# Legacy / full product unchanged
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_legacy_full_product_materialization_unchanged(db_session):
    order, preview, _persist = await _seed_persisted_scoped_plan(db_session, use_legacy=True)
    preview_keys = _task_keys([t.model_dump() for t in preview.planned_tasks])
    assert "linked_logo_apply" in preview_keys
    result = await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    operational_keys = _task_keys(envelope["operational_tasks"])
    assert result.status == "materialized"
    assert operational_keys == preview_keys
    assert len(envelope["operational_tasks"]) == len(envelope["planned_tasks"])


# ---------------------------------------------------------------------------
# Subset materialization
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_face_only_materializes_face_runtime_tasks(db_session):
    order, preview, _persist = await _seed_persisted_scoped_plan(
        db_session, runtime=["debitare_fata"]
    )
    assert _task_keys([t.model_dump() for t in preview.planned_tasks]) == {
        "vector_prep",
        "cnc_face_cut",
    }
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    keys = _task_keys(envelope["operational_tasks"])
    assert keys == {"vector_prep", "cnc_face_cut"}
    assert _module_codes(envelope["operational_tasks"]) == {"debitare_fata"}


@pytest.mark.asyncio
async def test_return_cant_only_materializes_cant_runtime_tasks(db_session):
    order, preview, _persist = await _seed_persisted_scoped_plan(
        db_session, runtime=["modelare_cant"]
    )
    assert _task_keys([t.model_dump() for t in preview.planned_tasks]) == {
        "vector_prep",
        "return_profile_forming",
        "return_face_bonding",
    }
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    keys = _task_keys(envelope["operational_tasks"])
    assert keys == {"vector_prep", "return_profile_forming", "return_face_bonding"}


@pytest.mark.asyncio
async def test_back_only_materializes_back_runtime_tasks(db_session):
    order, preview, _persist = await _seed_persisted_scoped_plan(
        db_session, runtime=["debitare_spate"]
    )
    assert _task_keys([t.model_dump() for t in preview.planned_tasks]) == {
        "vector_prep",
        "cnc_back_cut",
    }
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    assert _task_keys(envelope["operational_tasks"]) == {"vector_prep", "cnc_back_cut"}


@pytest.mark.asyncio
async def test_face_plus_return_cant_materializes_union_only(db_session):
    order, preview, _persist = await _seed_persisted_scoped_plan(
        db_session, runtime=["debitare_fata", "modelare_cant"]
    )
    expected = {
        "vector_prep",
        "cnc_face_cut",
        "return_profile_forming",
        "return_face_bonding",
    }
    assert _task_keys([t.model_dump() for t in preview.planned_tasks]) == expected
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    assert _task_keys(envelope["operational_tasks"]) == expected


@pytest.mark.asyncio
async def test_unsold_tasks_not_materialized(db_session):
    order, preview, _persist = await _seed_persisted_scoped_plan(
        db_session, runtime=["debitare_fata"]
    )
    keys = _task_keys([t.model_dump() for t in preview.planned_tasks])
    assert "led_installation" not in keys
    assert "cnc_back_cut" not in keys
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    runtime_keys = _task_keys(envelope["operational_tasks"])
    assert "led_installation" not in runtime_keys
    assert "cnc_back_cut" not in runtime_keys


# ---------------------------------------------------------------------------
# Blocked / idempotent / parity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_blocked_plan_does_not_materialize_runtime_tasks(db_session):
    oid = _SCOPED_OID()
    scope = snapshot_with_scope(offer_scope=offer_scope(runtime=[]))
    order = await _seed_v2_order_with_snapshot(
        db_session,
        order_id=oid,
        snapshot_v2_json=scope.model_dump_json(),
    )
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.status == "blocked_missing_sold_scope"
    with pytest.raises(HTTPException):
        await create_execution_plan_v2_from_order(db_session, order.id)
    from services.execution_plan_v2_materialize_service import ExecutionPlanV2MaterializePlanNotFound

    with pytest.raises(ExecutionPlanV2MaterializePlanNotFound):
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)


@pytest.mark.asyncio
async def test_blocked_preview_status_in_envelope_rejects_materialize(db_session):
    order, _preview, _persist = await _seed_persisted_scoped_plan(
        db_session, runtime=["debitare_fata"]
    )
    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order.id))
    ).scalar_one()
    envelope = json.loads(plan.tasks_json)
    envelope["preview_status"] = "blocked_missing_sold_scope"
    envelope["planned_tasks"] = []
    plan.tasks_json = json.dumps(envelope)
    await db_session.commit()
    with pytest.raises(HTTPException) as exc:
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert exc.value.status_code == 422
    assert "blocked_missing_sold_scope" in exc.value.detail["blockers"]


@pytest.mark.asyncio
async def test_materialization_is_idempotent(db_session):
    order, _preview, _persist = await _seed_persisted_scoped_plan(
        db_session, runtime=["debitare_fata"]
    )
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    with pytest.raises(HTTPException) as exc:
        await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_preview_persist_runtime_task_keys_match(db_session):
    order, preview, _persist = await _seed_persisted_scoped_plan(
        db_session, runtime=["debitare_fata", "modelare_cant"]
    )
    envelope_before = await _load_envelope(db_session, order.id)
    planned_keys = sorted(_task_keys(envelope_before["planned_tasks"]))
    preview_keys = sorted(t.task_key for t in preview.planned_tasks)
    assert planned_keys == preview_keys
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope_after = await _load_envelope(db_session, order.id)
    runtime_keys = sorted(_task_keys(envelope_after["operational_tasks"]))
    assert runtime_keys == preview_keys


# ---------------------------------------------------------------------------
# Identity preservation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_component_module_operation_identity_preserved(db_session):
    order, _preview, _persist = await _seed_persisted_scoped_plan(
        db_session, runtime=["debitare_fata"]
    )
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    planned_by_key = {t["task_key"]: t for t in envelope["planned_tasks"]}
    for operational in envelope["operational_tasks"]:
        planned = planned_by_key[operational["task_id"]]
        assert operational["source_module_code"] == planned.get("source_module_code")
        assert operational["source_component_code"] == planned.get("source_component_code")
        assert operational["source_operation_code"] == planned.get("source_operation_code")
        assert operational["process_id"] == (planned.get("source_operation_code") or "")
        assert operational["source_task_rule_code"] == planned.get("source_task_rule_code")


@pytest.mark.asyncio
async def test_linked_segment_identity_preserved_for_full_product(db_session):
    order, preview, _persist = await _seed_persisted_scoped_plan(db_session, use_legacy=True)
    assert "linked_logo_apply" in _task_keys([t.model_dump() for t in preview.planned_tasks])
    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order.id))
    ).scalar_one()
    envelope = json.loads(plan.tasks_json)
    for planned in envelope["planned_tasks"]:
        if planned["task_key"] == "linked_logo_apply":
            planned["source_component_code"] = "linked_segment:logo_instance_001::comp_face"
            break
    plan.tasks_json = json.dumps(envelope)
    await db_session.commit()
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    envelope = await _load_envelope(db_session, order.id)
    linked = next(t for t in envelope["operational_tasks"] if t["task_id"] == "linked_logo_apply")
    assert linked["source_component_code"] == "linked_segment:logo_instance_001::comp_face"
    assert linked["linked_segment_key"] == "logo_instance_001"


# ---------------------------------------------------------------------------
# No forbidden upstream calls
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_resolver_or_aggregate_calls(db_session, monkeypatch):
    called = {"resolver": False, "aggregate": False}

    def _resolver(*args, **kwargs):
        called["resolver"] = True
        raise AssertionError("resolve_offer_scope must not run during materialization")

    async def _aggregate(*args, **kwargs):
        called["aggregate"] = True
        raise AssertionError("build_for_workspace must not run during materialization")

    monkeypatch.setattr("services.offer_scope_resolver_service.resolve_offer_scope", _resolver)
    monkeypatch.setattr(
        "services.product_aggregate_service.ProductAggregateService.build_for_workspace",
        _aggregate,
    )

    order, _preview, _persist = await _seed_persisted_scoped_plan(
        db_session, runtime=["debitare_fata"]
    )
    await materialize_execution_plan_v2_operational_tasks(db_session, order.id)
    assert called == {"resolver": False, "aggregate": False}


def test_linked_segment_key_helper_unit():
    from services.execution_plan_task_parser import _linked_segment_key_from_component_ref

    assert _linked_segment_key_from_component_ref("linked_segment:logo_instance_001::comp_face") == "logo_instance_001"
    assert _linked_segment_key_from_component_ref("comp_face::logo_instance_002") == "logo_instance_002"
    assert _linked_segment_key_from_component_ref(None) is None
