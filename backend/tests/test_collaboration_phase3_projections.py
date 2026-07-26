"""Phase 3 thin capability / viewer-scoped collaboration read projections."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from models.execution_plan import ExecutionPlan
from schemas.execution_task_help import HelpRequestCreateBody
from services.execution_plan_task_parser import operational_tasks_only
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_task_collaboration_read_service import (
    apply_viewer_collaboration_capabilities,
    build_order_task_collaboration_read,
    project_task_collaboration_read,
)
from services.execution_task_help_service import create_help_request
from services.execution_task_membership_service import join_helper_membership
from services.employee_mobile_tasks_service import list_my_tasks
from services.flex_membership_flags import reset_flex_membership_flags_cache
from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_employee,
    _user,
)
from tests.test_execution_plan_v2_frozen_task_identity import (
    _identity_aggregate,
    _seed_identity_order,
)


@pytest.fixture(autouse=True)
def _reset_flags(monkeypatch):
    monkeypatch.setenv("FLEX_COLLAB_PHASE2_ENABLED", "true")
    monkeypatch.setenv("FLEX_MEMBERSHIP_API_ENABLED", "true")
    reset_flex_membership_flags_cache()
    yield
    reset_flex_membership_flags_cache()


@pytest.fixture
def phase3_caps(db_fixture, db_session):
    order_id = 32600 + (int(uuid.uuid4().hex[:8], 16) % 40_000)

    async def _setup():
        principal = await _seed_employee(
            db_session, user_id=f"p3-prin-{uuid.uuid4().hex[:6]}", name="P3 Principal"
        )
        helper = await _seed_employee(
            db_session, user_id=f"p3-help-{uuid.uuid4().hex[:6]}", name="P3 Helper"
        )
        aggregate = _identity_aggregate(include_mounting=True, linked_logo=False)
        await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
        await create_execution_plan_v2_from_order(db_session, order_id)
        await materialize_execution_plan_v2_operational_tasks(db_session, order_id)
        plan = (
            await db_session.execute(
                select(ExecutionPlan)
                .where(ExecutionPlan.order_id == order_id)
                .order_by(ExecutionPlan.id.desc())
                .limit(1)
            )
        ).scalar_one()
        ops = operational_tasks_only(plan.tasks_json)
        assert ops
        task = ops[0]
        task_id = str(task["task_id"])
        from services.execution_plan_task_parser import (
            load_operational_tasks_from_plan_json,
            serialize_operational_tasks_to_plan_json,
        )

        ops_list, parsed = load_operational_tasks_from_plan_json(plan.tasks_json)
        for row in ops_list:
            if isinstance(row, dict) and str(row.get("task_id")) == task_id:
                row["assigned_employee_id"] = int(principal.id)
                row["assignment_source"] = "manager_assign"
        plan.tasks_json = serialize_operational_tasks_to_plan_json(parsed, ops_list)
        await db_session.commit()
        await db_session.refresh(plan)
        return {
            "principal_id": principal.id,
            "helper_id": helper.id,
            "principal_user_id": principal.user_id,
            "task_id": task_id,
        }

    ids = db_fixture.run(_setup())
    yield {
        **ids,
        "order_id": order_id,
        "db_fixture": db_fixture,
        "db_session": db_session,
    }
    _cleanup_overrides()


def test_apply_viewer_capabilities_principal_can_request(phase3_caps):
    fx = phase3_caps
    projected = project_task_collaboration_read(
        task_id=fx["task_id"],
        plan_task={
            "task_id": fx["task_id"],
            "display_name": "Caps",
            "assigned_employee_id": fx["principal_id"],
        },
        sessions=[],
        employee_names={fx["principal_id"]: "P3 Principal", fx["helper_id"]: "P3 Helper"},
        helper_memberships=[],
        open_help_requests=[],
    )
    filled = apply_viewer_collaboration_capabilities(
        projected,
        viewer_employee_id=fx["principal_id"],
        sessions=[],
        phase2_enabled=True,
    )
    assert filled.visible_as_principal is True
    assert filled.visible_as_helper is False
    assert filled.can_request_help is True
    assert filled.can_cancel_help is False
    assert filled.can_accept_help is False
    assert filled.can_complete_operation is True
    assert filled.can_start_helper_work is False


def test_apply_viewer_capabilities_helper_after_accept(phase3_caps):
    fx = phase3_caps

    async def _run():
        created = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
            join_source="help_accept",
            skip_eligibility=True,
        )
        payload = await build_order_task_collaboration_read(
            fx["db_session"],
            fx["order_id"],
            viewer_employee_id=fx["helper_id"],
        )
        task = next(t for t in payload.tasks if t.task_id == fx["task_id"])
        assert task.visible_as_helper is True
        assert task.visible_as_principal is False
        assert task.can_request_help is False
        assert task.can_complete_operation is False
        assert task.can_start_helper_work is True
        assert task.can_accept_help is False
        assert task.can_cancel_help is False

        principal_view = await build_order_task_collaboration_read(
            fx["db_session"],
            fx["order_id"],
            viewer_employee_id=fx["principal_id"],
        )
        ptask = next(t for t in principal_view.tasks if t.task_id == fx["task_id"])
        assert ptask.can_request_help is True
        assert ptask.can_cancel_help is True
        assert ptask.has_open_help is True
        assert created.help_request.status == "OPEN"

    fx["db_fixture"].run(_run())


def test_mobile_my_tasks_request_cancel_caps(phase3_caps):
    fx = phase3_caps

    async def _run():
        await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        mine = await list_my_tasks(fx["db_session"], fx["principal_id"])
        match = next(
            t
            for t in mine
            if int(t["order_id"]) == fx["order_id"] and str(t["task_id"]) == fx["task_id"]
        )
        assert match["can_request_help"] is True
        assert match["can_cancel_help"] is True

        helper_mine = await list_my_tasks(fx["db_session"], fx["helper_id"])
        assert not any(
            int(t["order_id"]) == fx["order_id"] and str(t["task_id"]) == fx["task_id"]
            for t in helper_mine
        )

    fx["db_fixture"].run(_run())


def test_collab_read_endpoint_fills_viewer_from_auth(phase3_caps):
    fx = phase3_caps
    client = _client_for(fx["db_fixture"], _user(str(fx["principal_user_id"]), "operator"))
    try:
        response = client.get(
            f"/api/v1/operator/orders/{fx['order_id']}/task-collaboration-read"
        )
        assert response.status_code == 200, response.text
        body = response.json()
        task = next(t for t in body["tasks"] if t["task_id"] == fx["task_id"])
        assert task["can_request_help"] is True
        assert task["visible_as_principal"] is True
        assert task["can_complete_operation"] is True
    finally:
        _cleanup_overrides()
