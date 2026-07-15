"""MOBILE-T01 — canonical employee mobile task read model tests."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi import HTTPException
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from schemas.execution_plan_v2_frozen_task_identity import FROZEN_TASK_IDENTITY_VERSION
from services.employee_mobile_task_truth_service import resolve_operational_plan_tasks
from services.employee_mobile_tasks_service import _load_enriched_tasks, list_available_tasks, list_my_tasks

from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_active_order,
    _seed_employee,
    _seed_plan_unassigned_task,
    _seed_plan_with_assigned_task,
    _seed_print_eligibility,
    _user,
)

ROOT_NODE = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2"
MOUNTING_NODE = "node:mounting_panel:TPL-ACM-CASSETTED-PANEL_v2"


def _v2_envelope(*, operational: list | None = None, execution_tasks_created: bool = True) -> str:
    envelope: dict = {
        "source": "order_snapshot_v2",
        "planned_tasks": [{"task_key": "vector_prep", "label": "Vector Prep"}],
        "execution_tasks_created": execution_tasks_created,
    }
    if operational is not None:
        envelope["operational_tasks"] = operational
    return json.dumps(envelope)


def _frozen_operational_task(
    task_id: str,
    *,
    role: str = "root_product",
    graph_node: str = ROOT_NODE,
    logo_segment: str | None = None,
    assigned_employee_id: int | None = None,
    process_override: dict | None = None,
) -> dict:
    frozen: dict = {
        "contract_version": FROZEN_TASK_IDENTITY_VERSION,
        "deterministic_task_key": task_id,
        "source_graph_node_id": graph_node,
        "source_component_role": role,
        "source_template_code": "TPL-VOLUMETRIC-LETTERS",
        "identity_classification": "FULL_FROZEN_COMPONENT_IDENTITY",
        "operation_scope": "ROOT_PRODUCT",
    }
    if logo_segment:
        frozen["source_segment_key"] = logo_segment
        frozen["source_component_instance_id"] = "inst-logo-001"
    task = {
        "task_id": task_id,
        "display_name": "Vector Prep",
        "process_type": "vector_prep",
        "process_id": "vector_prep",
        "sequence_index": 0,
        "frozen_identity": frozen,
    }
    if assigned_employee_id is not None:
        task["assigned_employee_id"] = assigned_employee_id
    if process_override:
        task.update(process_override)
    return task


async def _seed_v2_order(
    db_session,
    *,
    order_id: int,
    tasks_json: str,
) -> None:
    quote = Quotes(
        code=f"QT-{order_id:04d}",
        intake_code=f"IR-{order_id:04d}",
        client_name="Frozen Client",
        status="accepted",
        version=1,
    )
    db_session.add(quote)
    await db_session.flush()
    db_session.add(
        Orders(
            id=order_id,
            code=f"ORD-{order_id:04d}",
            quote_id=quote.id,
            quote_code=quote.code,
            client_name="Frozen Client",
            status="in_production",
        )
    )
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-{order_id:04d}",
            snapshot_version=2,
            tasks_json=tasks_json,
            total_estimated_time_minutes=60,
        )
    )
    await db_session.commit()


def test_resolve_operational_plan_tasks_parses_v2_envelope():
    task_id = f"{ROOT_NODE}:vector_prep"
    operational = [_frozen_operational_task(task_id)]
    resolved = resolve_operational_plan_tasks(
        _v2_envelope(operational=operational),
        order_id=23099,
        order=None,
    )
    assert resolved.canonical_v2 is True
    assert resolved.legacy_mode is False
    assert len(resolved.tasks) == 1
    assert resolved.tasks[0]["task_id"] == task_id


def test_resolve_operational_plan_tasks_legacy_list_explicit():
    legacy = json.dumps(
        [
            {
                "task_id": "T-LEG",
                "name": "Legacy",
                "process_type": "print",
            }
        ]
    )
    resolved = resolve_operational_plan_tasks(legacy, order_id=1, order=None)
    assert resolved.legacy_mode is True
    assert resolved.canonical_v2 is False
    assert resolved.tasks[0]["task_id"] == "T-LEG"


def test_v2_missing_operational_tasks_fail_closed():
    order = Orders(id=23099, quote_snapshot_v2_id=1, snapshot_v2_json="{}")
    with pytest.raises(HTTPException) as exc:
        resolve_operational_plan_tasks(
            _v2_envelope(operational=[], execution_tasks_created=True),
            order_id=23099,
            order=order,
            fail_closed=True,
        )
    assert exc.value.detail["error"] == "MOBILE_V2_TASK_ENVELOPE_MISSING"


def test_v2_corrupt_envelope_fail_closed():
    order = Orders(id=23099, quote_snapshot_v2_id=1, snapshot_v2_json="{}")
    with pytest.raises(HTTPException) as exc:
        resolve_operational_plan_tasks(
            "{not-json",
            order_id=23099,
            order=order,
            fail_closed=True,
        )
    assert exc.value.detail["error"] == "MOBILE_V2_TASK_ENVELOPE_CORRUPT"


@pytest.mark.asyncio
async def test_load_enriched_tasks_v2_returns_non_empty(db_session):
    order_id = 23000 + int(uuid.uuid4().hex[:4], 16) % 500
    task_id = f"{ROOT_NODE}:vector_prep"
    mounting_id = f"{MOUNTING_NODE}:panel_cut"
    logo_id = f"{ROOT_NODE}:logo_apply"
    operational = [
        _frozen_operational_task(task_id),
        _frozen_operational_task(
            mounting_id,
            role="mounting_panel",
            graph_node=MOUNTING_NODE,
        ),
        _frozen_operational_task(task_id=logo_id, logo_segment="logo_instance_001"),
    ]
    await _seed_v2_order(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(operational=operational),
    )
    enriched, _ = await _load_enriched_tasks(db_session)
    order_tasks = [t for t in enriched if t["order_id"] == order_id]
    assert len(order_tasks) == 3
    root = next(t for t in order_tasks if t["task_id"] == task_id)
    assert root["contract_version"] == "employee_mobile_task_truth/v1"
    assert root["legacy_mode"] is False
    assert root["deterministic_task_key"] == task_id
    assert root["component_role"] == "root_product"
    assert root["identity_source"] == "frozen_task_identity/v1"
    mounting = next(t for t in order_tasks if t["task_id"] == mounting_id)
    assert mounting["component_role"] == "mounting_panel"
    logo = next(t for t in order_tasks if t["task_id"] == logo_id)
    assert logo["logo_segment_label"] is not None


@pytest.mark.asyncio
async def test_assigned_projection_filters_canonically(db_session):
    order_id = 23100 + int(uuid.uuid4().hex[:4], 16) % 500
    user_id = f"v2-own-{uuid.uuid4().hex[:6]}"
    other_id = f"v2-oth-{uuid.uuid4().hex[:6]}"
    task_id = f"{ROOT_NODE}:vector_prep"
    other_task = f"{ROOT_NODE}:cnc_back_cut"

    async def _setup():
        owner = await _seed_employee(db_session, user_id=user_id, name="V2 Owner")
        other = await _seed_employee(db_session, user_id=other_id, name="V2 Other")
        operational = [
            _frozen_operational_task(task_id, assigned_employee_id=owner.id),
            _frozen_operational_task(other_task, assigned_employee_id=other.id),
        ]
        await _seed_v2_order(
            db_session,
            order_id=order_id,
            tasks_json=_v2_envelope(operational=operational),
        )
        return owner.id

    emp_id = await _setup()
    rows = await list_my_tasks(db_session, emp_id)
    scoped = [r for r in rows if r["order_id"] == order_id]
    assert len(scoped) == 1
    assert scoped[0]["task_id"] == task_id
    assert scoped[0]["is_assigned_to_current_employee"] is True


@pytest.mark.asyncio
async def test_available_projection_filters_canonically(db_session):
    order_id = 23200 + int(uuid.uuid4().hex[:4], 16) % 500
    user_id = f"v2-avail-{uuid.uuid4().hex[:6]}"
    task_id = f"{ROOT_NODE}:vector_prep"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="V2 Claimer")
        await _seed_print_eligibility(db_session, emp.id)
        operational = [
            _frozen_operational_task(
                task_id,
                process_override={"process_type": "print", "process_id": "print"},
            )
        ]
        await _seed_v2_order(
            db_session,
            order_id=order_id,
            tasks_json=_v2_envelope(operational=operational),
        )
        return emp.id

    emp_id = await _setup()
    rows = await list_available_tasks(db_session, emp_id)
    scoped = [r for r in rows if r["order_id"] == order_id]
    assert len(scoped) == 1
    assert scoped[0]["task_id"] == task_id
    assert scoped[0]["is_available_for_claim"] is True
    assert scoped[0].get("claimable") is True


def test_v2_list_endpoint_non_empty(db_fixture, db_session):
    order_id = 23300 + int(uuid.uuid4().hex[:6], 16) % 500
    user_id = f"v2-api-{uuid.uuid4().hex[:6]}"
    task_id = f"{ROOT_NODE}:vector_prep"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="V2 API")
        operational = [_frozen_operational_task(task_id, assigned_employee_id=emp.id)]
        await _seed_v2_order(
            db_session,
            order_id=order_id,
            tasks_json=_v2_envelope(operational=operational),
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/tasks")
        assert response.status_code == 200, response.text
        rows = response.json()
        assert len(rows) >= 1
        match = next((r for r in rows if r["task_id"] == task_id), None)
        assert match is not None
        assert match["deterministic_task_key"] == task_id
        assert match["identity_source"] == "frozen_task_identity/v1"
        assert match["contract_version"] == "employee_mobile_task_truth/v1"
    finally:
        _cleanup_overrides()


def test_truth_endpoint_contract(db_fixture, db_session):
    order_id = 23400 + int(uuid.uuid4().hex[:6], 16) % 500
    user_id = f"v2-truth-{uuid.uuid4().hex[:6]}"
    task_id = f"{ROOT_NODE}:vector_prep"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Truth User")
        operational = [_frozen_operational_task(task_id, assigned_employee_id=emp.id)]
        await _seed_v2_order(
            db_session,
            order_id=order_id,
            tasks_json=_v2_envelope(operational=operational),
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/tasks/truth")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["contract_version"] == "employee_mobile_task_truth/v1"
        assert body["summary"]["total_tasks"] >= 1
        assert body["capabilities"]["can_resolve_owner_decisions"] is False
        assert body["capabilities"]["can_view_internal_cost"] is False
    finally:
        _cleanup_overrides()


def test_legacy_list_still_supported(db_fixture, db_session):
    user_id = f"legacy-{uuid.uuid4().hex[:6]}"
    order_id = 23500 + int(uuid.uuid4().hex[:4], 16) % 500

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Legacy User")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=emp.id,
            task_id="T-LEGACY-1",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/tasks")
        assert response.status_code == 200, response.text
        rows = response.json()
        assert any(r["task_id"] == "T-LEGACY-1" for r in rows)
        legacy_row = next(r for r in rows if r["task_id"] == "T-LEGACY-1")
        assert legacy_row.get("legacy_mode") is True
    finally:
        _cleanup_overrides()
