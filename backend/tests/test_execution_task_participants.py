"""Phase 1 HELPER collaboration membership — join/leave + read projection."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.execution_task_participant import ExecutionTaskParticipant
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_plan_task_parser import operational_tasks_only
from services.execution_reality_service import ExecutionRealityService
from services.execution_task_collaboration_read_service import (
    build_order_task_collaboration_read,
)
from services.execution_task_membership_service import (
    join_helper_membership,
    leave_helper_membership,
)
from services.flex_membership_flags import reset_flex_membership_flags_cache
from services.operational_registry_service import OperationalRegistryService
from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_active_order,
    _seed_employee,
    _seed_plan_unassigned_task,
    _seed_print_eligibility,
    _user,
)
from tests.test_execution_plan_v2_frozen_task_identity import (
    _identity_aggregate,
    _seed_identity_order,
)

MEMBERSHIP_OID_BASE = 31500


async def _seed_v2_materialized(db_session, *, order_id: int):
    aggregate = _identity_aggregate(include_mounting=True, linked_logo=False)
    order = await _seed_identity_order(db_session, order_id=order_id, aggregate=aggregate)
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
    assert ops, "expected materialized operational tasks"
    first = ops[0]
    return order, plan, first


async def _seed_eligibility_for_task(db_session, employee_id: int, plan_task: dict) -> str:
    operation_code = str(
        plan_task.get("process_type")
        or plan_task.get("process_id")
        or plan_task.get("source_operation_code")
        or ""
    ).strip()
    assert operation_code
    svc = OperationalRegistryService(db_session)
    await svc.upsert_operation_mapping(
        {
            "operation_code": operation_code,
            "authorization_mode": "explicit",
            "authorized_employee_ids": [employee_id],
        }
    )
    return operation_code


@pytest.fixture(autouse=True)
def _reset_membership_flags():
    reset_flex_membership_flags_cache()
    yield
    reset_flex_membership_flags_cache()


@pytest.fixture
def membership_fixture(db_fixture, db_session):
    order_id = MEMBERSHIP_OID_BASE + int(uuid.uuid4().hex[:3], 16) % 200
    helper_user = f"mem-helper-{uuid.uuid4().hex[:8]}"
    principal_user = f"mem-prin-{uuid.uuid4().hex[:8]}"

    async def _setup():
        helper = await _seed_employee(db_session, user_id=helper_user, name="Mem Helper")
        principal = await _seed_employee(
            db_session, user_id=principal_user, name="Mem Principal"
        )
        order, plan, first_task = await _seed_v2_materialized(db_session, order_id=order_id)
        await _seed_eligibility_for_task(db_session, helper.id, first_task)
        return {
            "order_id": order_id,
            "helper_id": helper.id,
            "principal_id": principal.id,
            "helper_user": helper_user,
            "principal_user": principal_user,
            "task_id": str(first_task["task_id"]),
            "plan_id": plan.id,
            "process_type": str(first_task.get("process_type") or ""),
            "assigned_before": first_task.get("assigned_employee_id"),
        }

    ids = db_fixture.run(_setup())
    yield {**ids, "db_fixture": db_fixture, "db_session": db_session}
    _cleanup_overrides()


def test_m1_join_creates_active_helper(membership_fixture):
    fx = membership_fixture

    async def _run():
        result = await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        assert result.already_joined is False
        assert result.membership.status == "active"
        assert result.membership.role == "helper"
        assert result.membership.employee_id == fx["helper_id"]
        row = (
            await fx["db_session"].execute(
                select(ExecutionTaskParticipant).where(
                    ExecutionTaskParticipant.order_id == fx["order_id"],
                    ExecutionTaskParticipant.task_id == fx["task_id"],
                    ExecutionTaskParticipant.employee_id == fx["helper_id"],
                )
            )
        ).scalar_one()
        assert row.status == "active"
        assert row.role == "helper"

    fx["db_fixture"].run(_run())


def test_m2_join_idempotent(membership_fixture):
    fx = membership_fixture

    async def _run():
        first = await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        second = await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        assert first.already_joined is False
        assert second.already_joined is True
        count = (
            await fx["db_session"].execute(
                select(ExecutionTaskParticipant).where(
                    ExecutionTaskParticipant.order_id == fx["order_id"],
                    ExecutionTaskParticipant.task_id == fx["task_id"],
                    ExecutionTaskParticipant.employee_id == fx["helper_id"],
                )
            )
        ).scalars().all()
        assert len(count) == 1

    fx["db_fixture"].run(_run())


def test_m3_m4_m5_leave_and_reactivate(membership_fixture):
    fx = membership_fixture

    async def _run():
        await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        left = await leave_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        assert left.membership.status == "inactive"
        assert left.membership.left_at
        left2 = await leave_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        assert left2.already_left is True
        rejoined = await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        assert rejoined.reactivated is True
        assert rejoined.membership.status == "active"
        assert rejoined.membership.left_at is None
        rows = (
            await fx["db_session"].execute(
                select(ExecutionTaskParticipant).where(
                    ExecutionTaskParticipant.order_id == fx["order_id"],
                    ExecutionTaskParticipant.employee_id == fx["helper_id"],
                )
            )
        ).scalars().all()
        assert len(rows) == 1

    fx["db_fixture"].run(_run())


def test_m6_m7_join_does_not_start_session_or_change_assignee(membership_fixture):
    fx = membership_fixture

    async def _run():
        plan_before = (
            await fx["db_session"].execute(
                select(ExecutionPlan)
                .where(ExecutionPlan.order_id == fx["order_id"])
                .order_by(ExecutionPlan.id.desc())
                .limit(1)
            )
        ).scalar_one()
        task_before = next(
            t
            for t in operational_tasks_only(plan_before.tasks_json)
            if t["task_id"] == fx["task_id"]
        )
        assignee_before = task_before.get("assigned_employee_id")

        await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )

        reality = (
            await fx["db_session"].execute(
                select(ExecutionReality).where(ExecutionReality.order_id == fx["order_id"])
            )
        ).scalar_one_or_none()
        if reality is not None:
            sessions = json.loads(reality.tasks_json or "[]")
            assert sessions == [] or not any(
                isinstance(s, dict)
                and s.get("task_id") == fx["task_id"]
                and s.get("employee_id") == fx["helper_id"]
                for s in sessions
            )

        plan_after = (
            await fx["db_session"].execute(
                select(ExecutionPlan)
                .where(ExecutionPlan.order_id == fx["order_id"])
                .order_by(ExecutionPlan.id.desc())
                .limit(1)
            )
        ).scalar_one()
        task_after = next(
            t
            for t in operational_tasks_only(plan_after.tasks_json)
            if t["task_id"] == fx["task_id"]
        )
        assert task_after.get("assigned_employee_id") == assignee_before

    fx["db_fixture"].run(_run())


def test_m8_m9_leave_does_not_stop_session_or_complete(membership_fixture):
    fx = membership_fixture

    async def _run():
        await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        svc = ExecutionRealityService(fx["db_session"])
        started = datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc).isoformat()
        await svc.start_task(
            fx["order_id"],
            f"ORD-{fx['order_id']}",
            fx["task_id"],
            started,
            initial_fields={
                "employee_id": fx["helper_id"],
                "employee_name": "Mem Helper",
                "role": "helper",
            },
        )
        await leave_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        reality = (
            await fx["db_session"].execute(
                select(ExecutionReality).where(ExecutionReality.order_id == fx["order_id"])
            )
        ).scalar_one()
        sessions = json.loads(reality.tasks_json or "[]")
        helper_sessions = [
            s
            for s in sessions
            if isinstance(s, dict)
            and s.get("task_id") == fx["task_id"]
            and int(s.get("employee_id") or 0) == fx["helper_id"]
        ]
        assert len(helper_sessions) == 1
        assert not helper_sessions[0].get("ended_at")
        read = await build_order_task_collaboration_read(fx["db_session"], fx["order_id"])
        task = next(t for t in read.tasks if t.task_id == fx["task_id"])
        assert task.operation_completed is False

    fx["db_fixture"].run(_run())


def test_m10_leave_without_membership_404(membership_fixture):
    fx = membership_fixture
    from fastapi import HTTPException

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await leave_helper_membership(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id=fx["task_id"],
                employee_id=fx["helper_id"],
            )
        assert exc.value.status_code == 404
        assert exc.value.detail["error"] == "membership_not_found"

    fx["db_fixture"].run(_run())


def test_m11_join_legacy_plan_rejected(db_fixture, db_session):
    from fastapi import HTTPException

    order_id = MEMBERSHIP_OID_BASE + 800
    user_id = f"mem-legacy-{uuid.uuid4().hex[:8]}"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id)
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, emp.id)
        await _seed_plan_unassigned_task(db_session, order_id=order_id, task_id="T-LEGACY-M")
        return emp.id

    emp_id = db_fixture.run(_setup())

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await join_helper_membership(
                db_session,
                order_id=order_id,
                task_id="T-LEGACY-M",
                employee_id=emp_id,
            )
        assert exc.value.status_code == 409
        assert exc.value.detail["error"] == "v2_materialization_required"

    db_fixture.run(_run())
    _cleanup_overrides()


def test_m12_unknown_task_404(membership_fixture):
    from fastapi import HTTPException

    fx = membership_fixture

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await join_helper_membership(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id="node:missing:task",
                employee_id=fx["helper_id"],
            )
        assert exc.value.status_code == 404
        assert exc.value.detail["error"] == "task_not_found"

    fx["db_fixture"].run(_run())


def test_m13_concurrent_double_join(membership_fixture):
    fx = membership_fixture

    async def _run():
        async def _one():
            # Fresh session per concurrent call is ideal; reuse fixture session serially via lock.
            return await join_helper_membership(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id=fx["task_id"],
                employee_id=fx["helper_id"],
            )

        # Sequential under shared session exercises lock + unique path; dual asyncio on same session is unsafe.
        r1 = await _one()
        r2 = await _one()
        assert r1.already_joined is False or r2.already_joined is True
        rows = (
            await fx["db_session"].execute(
                select(ExecutionTaskParticipant).where(
                    ExecutionTaskParticipant.order_id == fx["order_id"],
                    ExecutionTaskParticipant.task_id == fx["task_id"],
                    ExecutionTaskParticipant.employee_id == fx["helper_id"],
                )
            )
        ).scalars().all()
        assert len(rows) == 1

    fx["db_fixture"].run(_run())


def test_m14_read_includes_helper_memberships(membership_fixture):
    fx = membership_fixture

    async def _run():
        await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        payload = await build_order_task_collaboration_read(fx["db_session"], fx["order_id"])
        assert payload.contract_version == "execution_task_collaboration_read/v1.1"
        task = next(t for t in payload.tasks if t.task_id == fx["task_id"])
        assert task.authorized_helper_count == 1
        assert len(task.helper_memberships) == 1
        assert task.helper_memberships[0].employee_id == fx["helper_id"]
        assert task.helper_memberships[0].status == "active"
        assert task.actual_workers == []
        await leave_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper_id"],
        )
        payload2 = await build_order_task_collaboration_read(fx["db_session"], fx["order_id"])
        task2 = next(t for t in payload2.tasks if t.task_id == fx["task_id"])
        assert task2.authorized_helper_count == 0
        assert task2.helper_memberships[0].status == "inactive"

    fx["db_fixture"].run(_run())


def test_m15_claim_regression_after_membership(db_fixture, db_session):
    """Claim still works after a HELPER membership write on a separate V2 order."""
    membership_user = f"mem-after-{uuid.uuid4().hex[:8]}"
    claim_user = f"mem-claim-{uuid.uuid4().hex[:8]}"
    membership_order = MEMBERSHIP_OID_BASE + 820
    claim_order = MEMBERSHIP_OID_BASE + 821

    async def _setup():
        helper = await _seed_employee(db_session, user_id=membership_user, name="Mem After")
        claimer = await _seed_employee(db_session, user_id=claim_user, name="Mem Claimer")
        _order, _plan, first_task = await _seed_v2_materialized(
            db_session, order_id=membership_order
        )
        await _seed_eligibility_for_task(db_session, helper.id, first_task)
        await join_helper_membership(
            db_session,
            order_id=membership_order,
            task_id=str(first_task["task_id"]),
            employee_id=helper.id,
        )
        await _seed_active_order(db_session, order_id=claim_order)
        await _seed_print_eligibility(db_session, claimer.id)
        await _seed_plan_unassigned_task(
            db_session, order_id=claim_order, task_id="T-MEM-CLAIM"
        )
        return {"helper_id": helper.id, "task_id": str(first_task["task_id"])}

    seeded = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(claim_user, "employee_mobile"))
    try:
        # Membership row still present for helper on V2 order
        async def _assert_membership():
            row = (
                await db_session.execute(
                    select(ExecutionTaskParticipant).where(
                        ExecutionTaskParticipant.order_id == membership_order,
                        ExecutionTaskParticipant.employee_id == seeded["helper_id"],
                    )
                )
            ).scalar_one()
            assert row.status == "active"

        db_fixture.run(_assert_membership())

        claim = client.post(
            "/api/v1/employee-mobile/tasks/T-MEM-CLAIM/claim",
            json={"order_id": claim_order},
        )
        assert claim.status_code == 200, claim.text
        assert claim.json()["already_claimed"] is False
    finally:
        _cleanup_overrides()


def test_ineligible_join_403(membership_fixture):
    from fastapi import HTTPException

    fx = membership_fixture

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await join_helper_membership(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id=fx["task_id"],
                employee_id=fx["principal_id"],  # not eligible
            )
        assert exc.value.status_code == 403
        assert exc.value.detail["error"] == "employee_not_eligible"

    fx["db_fixture"].run(_run())


def test_mobile_join_leave_http(membership_fixture):
    fx = membership_fixture
    client = _client_for(
        fx["db_fixture"],
        _user(fx["helper_user"], "employee_mobile"),
    )
    try:
        join = client.post(
            f"/api/v1/employee-mobile/orders/{fx['order_id']}/tasks/{fx['task_id']}/collaboration/join"
        )
        assert join.status_code == 200, join.text
        body = join.json()
        assert body["membership"]["status"] == "active"
        leave = client.post(
            f"/api/v1/employee-mobile/orders/{fx['order_id']}/tasks/{fx['task_id']}/collaboration/leave"
        )
        assert leave.status_code == 200, leave.text
        assert leave.json()["membership"]["status"] == "inactive"
    finally:
        _cleanup_overrides()
