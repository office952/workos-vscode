"""Tests for canonical operator task truth read model (W6-T01)."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from sqlalchemy import select
from schemas.operator_task_truth import (
    CANONICAL_FROZEN_IDENTITY_FIELDS,
    OPERATOR_TASK_TRUTH_VERSION,
)
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from tests.test_execution_owner_decision_production_release_guard import (
    NONBLOCKING,
    PRODUCTION_BLOCKERS,
    _build_snapshot_with_owner_decisions,
)
from tests.test_execution_plan_v2_frozen_task_identity import (
    ACM_TEMPLATE,
    IDENTITY_OID_BASE,
    MOUNTING_NODE,
    ROOT_NODE,
    TEMPLATE,
    _identity_aggregate,
    _seed_identity_order,
    _seed_v2_order_with_snapshot,
)

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from tests.test_employee_mobile_tasks import _cleanup_overrides, _client_for, _delete_order_execution_fixture, _user

TRUTH_OID_BASE = 24000


async def _delete_truth_order_fixture(db_session, *, order_id: int) -> None:
    """Remove operator truth order rows so shared pytest DB does not bleed."""
    from sqlalchemy import delete, select
    from models.quote_snapshot_v2 import QuoteSnapshotV2Record

    order = (
        await db_session.execute(select(Orders).where(Orders.id == order_id))
    ).scalar_one_or_none()
    qsn_id = order.quote_snapshot_v2_id if order else None

    await db_session.execute(delete(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    await db_session.execute(delete(Orders).where(Orders.id == order_id))
    if qsn_id is not None:
        await db_session.execute(
            delete(QuoteSnapshotV2Record).where(QuoteSnapshotV2Record.id == qsn_id)
        )
    await db_session.commit()


@pytest.fixture
def truth_client(db_fixture):
    client = _client_for(db_fixture, _user("admin-truth", role="admin"))
    yield client
    _cleanup_overrides()


@pytest.fixture
def operator_client(db_fixture):
    client = _client_for(db_fixture, _user("operator-truth", role="operator"))
    yield client
    _cleanup_overrides()


async def _seed_v2_plan_with_identity(
    db_session,
    *,
    order_id: int,
    linked_logo: bool = False,
    owner_codes: list[str] | None = None,
) -> Orders:
    aggregate = _identity_aggregate(include_mounting=True, linked_logo=linked_logo)
    if owner_codes is not None:
        snapshot_json = _build_snapshot_with_owner_decisions(
            owner_codes,
            quote_id=order_id,
            quote_snapshot_v2_id=order_id,
        )
        order = await _seed_v2_order_with_snapshot(
            db_session,
            order_id=order_id,
            snapshot_v2_json=snapshot_json,
        )
    else:
        order = await _seed_identity_order(
            db_session,
            order_id=order_id,
            aggregate=aggregate,
        )
    await create_execution_plan_v2_from_order(db_session, order_id)
    await materialize_execution_plan_v2_operational_tasks(db_session, order_id)
    await db_session.refresh(order)
    return order


def _get_truth(client: TestClient, order_id: int) -> dict:
    res = client.get(f"/api/v1/operator/orders/{order_id}/task-truth")
    assert res.status_code == 200, res.text
    return res.json()


@pytest.mark.asyncio
async def test_v2_returns_canonical_contract(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 1
    await _seed_v2_plan_with_identity(db_session, order_id=order_id)
    body = _get_truth(truth_client, order_id)
    assert body["contract_version"] == OPERATOR_TASK_TRUTH_VERSION
    assert body["readiness_authority"] == "FROZEN_ORDER_SNAPSHOT_V2"
    assert body["task_identity_version"] == "frozen_task_identity/v1"
    assert body["legacy_order"] is False
    assert len(body["tasks"]) >= 1


@pytest.mark.asyncio
async def test_frozen_identity_survives_http_serialization(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 2
    await _seed_v2_plan_with_identity(db_session, order_id=order_id, linked_logo=True)
    body = _get_truth(truth_client, order_id)
    root = next(
        t
        for t in body["tasks"]
        if t["identity"]["source_graph_node_id"] == ROOT_NODE
    )
    assert root["identity"]["identity_source"] == "frozen_task_identity/v1"
    assert root["identity"]["component_role"] == "root_product"
    assert root["identity"]["component_template_code"] == TEMPLATE
    assert root["identity"]["deterministic_task_key"]
    assert root["identity"]["source_operation_code"]


@pytest.mark.asyncio
async def test_mounting_and_logo_identities(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 3
    await _seed_v2_plan_with_identity(db_session, order_id=order_id, linked_logo=True)
    body = _get_truth(truth_client, order_id)
    mounting = next(
        (
            t
            for t in body["tasks"]
            if t["identity"]["component_role"] == "mounting_panel"
        ),
        None,
    )
    assert mounting is not None
    assert mounting["identity"]["component_template_code"] == ACM_TEMPLATE
    assert mounting["identity"]["source_graph_node_id"] == MOUNTING_NODE

    logo = next(
        (
            t
            for t in body["tasks"]
            if t["identity"].get("logo_segment_key") == "logo_instance_001"
        ),
        None,
    )
    assert logo is not None
    assert "Logo segment" in (logo["identity"].get("component_label") or "")


@pytest.mark.asyncio
async def test_production_release_blocked_reflects_on_tasks(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 4
    await _seed_v2_plan_with_identity(
        db_session,
        order_id=order_id,
        owner_codes=list(PRODUCTION_BLOCKERS),
    )
    body = _get_truth(truth_client, order_id)
    assert body["production_release_blocked"] is True
    assert body["production_release_status"] == "RELEASE_BLOCKED_OWNER_DECISIONS"
    assert len(body["owner_decisions_summary"]) >= 3
    sample = body["tasks"][0]
    assert sample["runtime"]["production_release_blocked"] is True
    assert sample["runtime"]["production_release_scope"] == "ORDER_SCOPE"
    assert sample["runtime"]["is_startable"] is False


@pytest.mark.asyncio
async def test_nonblocking_internal_decisions_do_not_block_release(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 5
    codes = list(PRODUCTION_BLOCKERS) + [NONBLOCKING[0]]
    await _seed_v2_plan_with_identity(db_session, order_id=order_id, owner_codes=codes)
    body = _get_truth(truth_client, order_id)
    nonblocking = [
        item
        for item in body["owner_decisions_summary"]
        if item["code"] == NONBLOCKING[0]
    ]
    assert nonblocking
    assert nonblocking[0]["blocking"] is False


@pytest.mark.asyncio
async def test_operator_role_hides_internal_cost(operator_client, db_session):
    order_id = TRUTH_OID_BASE + 6
    await _seed_v2_plan_with_identity(db_session, order_id=order_id)
    body = _get_truth(operator_client, order_id)
    assert body["role_capabilities"]["can_view_internal_cost"] is False
    assert body["internal_cost_summary"]["visibility"] == "restricted"
    assert body["internal_cost_summary"].get("estimated_total_internal_cost") is None


@pytest.mark.asyncio
async def test_manager_role_receives_internal_cost(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 7
    await _seed_v2_plan_with_identity(db_session, order_id=order_id)
    body = _get_truth(truth_client, order_id)
    assert body["role_capabilities"]["can_view_internal_cost"] is True
    assert body["internal_cost_summary"]["visibility"] == "available"
    assert body["internal_cost_summary"]["estimated_total_internal_cost"] == 620.0
    assert body["internal_cost_summary"]["accepted_commercial_total"] == 1500.0


@pytest.mark.asyncio
async def test_legacy_order_explicit_classification(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 8
    tasks = [
        {
            "task_id": "LEGACY-T1",
            "name": "Legacy Print",
            "display_name": "Legacy Print",
            "process_type": "print",
            "machine_type": "PRINTER",
            "estimated_time_minutes": 10,
        }
    ]
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-{order_id}",
            snapshot_version=1,
            tasks_json=json.dumps(tasks),
            total_estimated_time_minutes=10,
        )
    )
    order = Orders(
        id=order_id,
        code=f"ORD-{order_id}",
        status="active",
        client_name="Legacy Client",
    )
    db_session.add(order)
    await db_session.commit()

    body = _get_truth(truth_client, order_id)
    assert body["legacy_order"] is True
    assert body["readiness_authority"] == "LEGACY_READ_MODEL_EXPLICIT"
    assert body["task_identity_version"] is None
    assert body["tasks"][0]["identity"]["identity_source"] == "legacy_plan_task"
    assert body["tasks"][0]["authority"]["legacy_fallback_active"] is True


@pytest.mark.asyncio
async def test_corrupt_v2_snapshot_fail_closed(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 9
    try:
        await _seed_v2_order_with_snapshot(
            db_session,
            order_id=order_id,
            snapshot_v2_json="{not-valid-json",
        )
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-{order_id}",
                snapshot_version=1,
                tasks_json=json.dumps(
                    [
                        {
                            "task_id": "T-CORRUPT",
                            "name": "Task",
                            "process_type": "print",
                            "machine_type": "PRINTER",
                            "estimated_time_minutes": 1,
                        }
                    ]
                ),
                total_estimated_time_minutes=1,
            )
        )
        await db_session.commit()
        res = truth_client.get(f"/api/v1/operator/orders/{order_id}/task-truth")
        assert res.status_code == 422
        detail = res.json()["detail"]
        assert detail["error"] == "ORDER_SNAPSHOT_V2_CORRUPT"
    finally:
        await _delete_truth_order_fixture(db_session, order_id=order_id)


@pytest.mark.asyncio
async def test_task_id_matches_mutation_contract(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 10
    await _seed_v2_plan_with_identity(db_session, order_id=order_id)
    body = _get_truth(truth_client, order_id)
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    from services.execution_plan_task_parser import operational_tasks_only

    operational = operational_tasks_only(plan.tasks_json)
    truth_ids = {t["identity"]["task_id"] for t in body["tasks"]}
    plan_ids = {str(t.get("task_id")) for t in operational}
    assert truth_ids == plan_ids


@pytest.mark.asyncio
async def test_response_model_schema_preserves_identity_fields():
    from schemas.operator_task_truth import OperatorTaskTruthResponse, TaskIdentityTruth

    props = TaskIdentityTruth.model_json_schema()["properties"]
    for field in (
        "component_role",
        "component_template_code",
        "source_operation_code",
        "source_task_rule_code",
        "logo_segment_key",
        "identity_source",
    ):
        assert field in props

    top = OperatorTaskTruthResponse.model_json_schema()["properties"]
    for field in (
        "contract_version",
        "production_release_status",
        "owner_decisions_summary",
        "role_capabilities",
        "internal_cost_summary",
        "tasks",
    ):
        assert field in top


@pytest.mark.asyncio
async def test_repeated_reads_stable_task_count(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 11
    await _seed_v2_plan_with_identity(db_session, order_id=order_id, linked_logo=True)
    first = _get_truth(truth_client, order_id)
    second = _get_truth(truth_client, order_id)
    assert len(first["tasks"]) == len(second["tasks"])
    assert {t["identity"]["task_id"] for t in first["tasks"]} == {
        t["identity"]["task_id"] for t in second["tasks"]
    }


@pytest.mark.asyncio
async def test_readiness_composed_without_frontend_authority(truth_client, db_session):
    order_id = TRUTH_OID_BASE + 12
    await _seed_v2_plan_with_identity(db_session, order_id=order_id)
    body = _get_truth(truth_client, order_id)
    task = body["tasks"][0]
    assert "readiness_status" in task["runtime"]
    assert "is_startable" in task["runtime"]
    assert task["authority"]["readiness_source"] == "task_readiness_service"
