"""Phase 2 collaboration — help lifecycle, pools, helper sessions, capabilities."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import select, text

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.execution_task_help_request import ExecutionTaskHelpRequest
from models.execution_task_participant import ExecutionTaskParticipant
from schemas.execution_task_help import HelpRequestCreateBody
from services.execution_plan_task_parser import operational_tasks_only
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_reality_service import ExecutionRealityService
from services.execution_task_collaboration_read_service import (
    build_order_task_collaboration_read,
)
from services.execution_task_help_service import (
    accept_help_request,
    cancel_help_request,
    close_help_request,
    close_open_help_for_task,
    create_help_request,
    decline_help_request,
)
from services.execution_task_membership_service import (
    join_helper_membership,
    leave_helper_membership,
)
from services.flex_membership_flags import (
    reset_flex_membership_flags_cache,
)
from services.helper_work_session_service import start_helper_session, stop_helper_session
from services.employee_mobile_tasks_service import (
    list_available_tasks,
    list_help_opportunity_tasks,
    list_my_tasks,
)
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

PHASE2_OID_BASE = 32500


def _unique_order_id() -> int:
    return PHASE2_OID_BASE + (int(uuid.uuid4().hex[:8], 16) % 50_000)


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
    return order, plan, ops[0]


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
def _reset_flags(monkeypatch):
    monkeypatch.setenv("FLEX_COLLAB_PHASE2_ENABLED", "true")
    monkeypatch.setenv("FLEX_MEMBERSHIP_API_ENABLED", "true")
    reset_flex_membership_flags_cache()
    yield
    reset_flex_membership_flags_cache()


@pytest.fixture
def phase2_fixture(db_fixture, db_session):
    order_id = _unique_order_id()
    principal_user = f"p2-prin-{uuid.uuid4().hex[:8]}"
    helper1_user = f"p2-h1-{uuid.uuid4().hex[:8]}"
    helper2_user = f"p2-h2-{uuid.uuid4().hex[:8]}"
    ineligible_user = f"p2-x-{uuid.uuid4().hex[:8]}"

    async def _setup():
        principal = await _seed_employee(
            db_session, user_id=principal_user, name="P2 Principal"
        )
        helper1 = await _seed_employee(db_session, user_id=helper1_user, name="P2 Helper1")
        helper2 = await _seed_employee(db_session, user_id=helper2_user, name="P2 Helper2")
        ineligible = await _seed_employee(
            db_session, user_id=ineligible_user, name="P2 Ineligible"
        )
        order, plan, first_task = await _seed_v2_materialized(db_session, order_id=order_id)
        # One mapping with all eligible helpers (upsert replaces authorized list).
        operation_code = str(
            first_task.get("process_type")
            or first_task.get("process_id")
            or first_task.get("source_operation_code")
            or ""
        ).strip()
        svc = OperationalRegistryService(db_session)
        await svc.upsert_operation_mapping(
            {
                "operation_code": operation_code,
                "authorization_mode": "explicit",
                "authorized_employee_ids": [helper1.id, helper2.id, principal.id],
            }
        )
        return {
            "order_id": order_id,
            "task_id": str(first_task["task_id"]),
            "plan_id": plan.id,
            "principal_id": principal.id,
            "helper1_id": helper1.id,
            "helper2_id": helper2.id,
            "ineligible_id": ineligible.id,
            "principal_user": principal_user,
            "helper1_user": helper1_user,
            "helper2_user": helper2_user,
            "ineligible_user": ineligible_user,
            "process_type": operation_code,
        }

    ids = db_fixture.run(_setup())
    yield {**ids, "db_fixture": db_fixture, "db_session": db_session}
    _cleanup_overrides()


def test_h1_create_broadcast_open(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        result = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(reason="need hands"),
        )
        assert result.action == "create"
        assert result.help_request.status == "OPEN"
        assert result.help_request.is_broadcast is True
        assert result.help_request.targeted_employee_id is None

    fx["db_fixture"].run(_run())


def test_h2_create_targeted(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        result = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(targeted_employee_id=fx["helper1_id"]),
        )
        assert result.help_request.is_broadcast is False
        assert result.help_request.targeted_employee_id == fx["helper1_id"]

    fx["db_fixture"].run(_run())


def test_h3_duplicate_open_rejected(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        with pytest.raises(HTTPException) as exc:
            await create_help_request(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id=fx["task_id"],
                requested_by_employee_id=fx["principal_id"],
                body=HelpRequestCreateBody(),
            )
        assert exc.value.status_code == 409
        assert exc.value.detail["error"] == "help_already_open"

    fx["db_fixture"].run(_run())


def test_h4_broadcast_multi_accept(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        created = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        hid = created.help_request.help_request_id
        a1 = await accept_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=hid,
            employee_id=fx["helper1_id"],
        )
        assert a1.help_request.status == "OPEN"
        assert a1.membership_id is not None
        a2 = await accept_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=hid,
            employee_id=fx["helper2_id"],
        )
        assert a2.help_request.status == "OPEN"
        rows = (
            await fx["db_session"].execute(
                select(ExecutionTaskParticipant).where(
                    ExecutionTaskParticipant.order_id == fx["order_id"],
                    ExecutionTaskParticipant.task_id == fx["task_id"],
                    ExecutionTaskParticipant.status == "active",
                )
            )
        ).scalars().all()
        assert {r.employee_id for r in rows} == {fx["helper1_id"], fx["helper2_id"]}
        assert all(r.join_source == "help_accept" for r in rows)

    fx["db_fixture"].run(_run())


def test_h5_targeted_accept_closes(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        created = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(targeted_employee_id=fx["helper1_id"]),
        )
        hid = created.help_request.help_request_id
        with pytest.raises(HTTPException) as exc:
            await accept_help_request(
                fx["db_session"],
                order_id=fx["order_id"],
                help_request_id=hid,
                employee_id=fx["helper2_id"],
            )
        assert exc.value.status_code == 403
        accepted = await accept_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=hid,
            employee_id=fx["helper1_id"],
        )
        assert accepted.help_request.status == "CLOSED"

    fx["db_fixture"].run(_run())


def test_h6_targeted_decline(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        created = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(targeted_employee_id=fx["helper1_id"]),
        )
        declined = await decline_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=created.help_request.help_request_id,
            employee_id=fx["helper1_id"],
        )
        assert declined.help_request.status == "DECLINED"

    fx["db_fixture"].run(_run())


def test_h7_cancel_preserves_membership(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        created = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        hid = created.help_request.help_request_id
        await accept_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=hid,
            employee_id=fx["helper1_id"],
        )
        cancelled = await cancel_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=hid,
            actor_employee_id=fx["principal_id"],
        )
        assert cancelled.help_request.status == "CANCELLED"
        row = (
            await fx["db_session"].execute(
                select(ExecutionTaskParticipant).where(
                    ExecutionTaskParticipant.order_id == fx["order_id"],
                    ExecutionTaskParticipant.employee_id == fx["helper1_id"],
                )
            )
        ).scalar_one()
        assert row.status == "active"

    fx["db_fixture"].run(_run())


def test_h8_explicit_close_and_completion_closes_open(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        created = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        closed = await close_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=created.help_request.help_request_id,
            actor_employee_id=fx["principal_id"],
        )
        assert closed.help_request.status == "CLOSED"
        created2 = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        n = await close_open_help_for_task(
            fx["db_session"], order_id=fx["order_id"], task_id=fx["task_id"]
        )
        assert n >= 1
        row = (
            await fx["db_session"].execute(
                select(ExecutionTaskHelpRequest).where(
                    ExecutionTaskHelpRequest.id == created2.help_request.help_request_id
                )
            )
        ).scalar_one()
        assert row.status == "CLOSED"

    fx["db_fixture"].run(_run())


def test_h9_accept_after_closed_rejected(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        created = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        await cancel_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=created.help_request.help_request_id,
            actor_employee_id=fx["principal_id"],
        )
        with pytest.raises(HTTPException) as exc:
            await accept_help_request(
                fx["db_session"],
                order_id=fx["order_id"],
                help_request_id=created.help_request.help_request_id,
                employee_id=fx["helper1_id"],
            )
        assert exc.value.detail["error"] == "help_not_open"

    fx["db_fixture"].run(_run())


def test_h10_accept_idempotent_and_reactivate(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        created = await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        hid = created.help_request.help_request_id
        first = await accept_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=hid,
            employee_id=fx["helper1_id"],
        )
        second = await accept_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=hid,
            employee_id=fx["helper1_id"],
        )
        assert second.membership_already_active is True
        await leave_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
        )
        third = await accept_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            help_request_id=hid,
            employee_id=fx["helper1_id"],
        )
        assert third.membership_reactivated is True

    fx["db_fixture"].run(_run())


def test_h11_manager_add_and_self_join_without_help(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        mgr = await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
            joined_by_employee_id=fx["principal_id"],
            join_source="manager_add",
        )
        assert mgr.membership.join_source == "manager_add"
        self_join = await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper2_id"],
            join_source="self_join",
        )
        assert self_join.membership.join_source == "self_join"
        open_help = (
            await fx["db_session"].execute(
                select(ExecutionTaskHelpRequest).where(
                    ExecutionTaskHelpRequest.order_id == fx["order_id"],
                    ExecutionTaskHelpRequest.status == "OPEN",
                )
            )
        ).scalars().all()
        assert open_help == []

    fx["db_fixture"].run(_run())


def test_p1_help_pool_visibility(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        eligible = await list_help_opportunity_tasks(fx["db_session"], fx["helper1_id"])
        assert any(
            int(t["order_id"]) == fx["order_id"] and str(t["task_id"]) == fx["task_id"]
            for t in eligible
        )
        ineligible = await list_help_opportunity_tasks(
            fx["db_session"], fx["ineligible_id"]
        )
        assert not any(
            int(t["order_id"]) == fx["order_id"] and str(t["task_id"]) == fx["task_id"]
            for t in ineligible
        )

    fx["db_fixture"].run(_run())


def test_p2_helper_my_tasks_no_claim_no_complete(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
        )
        mine = await list_my_tasks(fx["db_session"], fx["helper1_id"])
        match = next(
            t
            for t in mine
            if int(t["order_id"]) == fx["order_id"] and str(t["task_id"]) == fx["task_id"]
        )
        assert match["visible_as_helper"] is True
        assert match["visible_as_principal"] is False
        assert match["can_claim"] is False
        assert match["can_complete_operation"] is False
        assert match["can_start_helper_work"] is True

    fx["db_fixture"].run(_run())


def test_s1_helper_session_requires_membership(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await start_helper_session(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id=fx["task_id"],
                employee_id=fx["helper1_id"],
                employee_name="H1",
            )
        assert exc.value.status_code == 403
        await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
        )
        started = await start_helper_session(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
            employee_name="H1",
        )
        assert started["action"] == "helper_session_start"
        assert started["session"]["employee_id"] == fx["helper1_id"]
        assert started["role"] == "helper"

    fx["db_fixture"].run(_run())


def test_s2_simultaneous_sessions_and_stop_own(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        for eid, name in (
            (fx["helper1_id"], "H1"),
            (fx["helper2_id"], "H2"),
        ):
            await join_helper_membership(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id=fx["task_id"],
                employee_id=eid,
            )
            await start_helper_session(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id=fx["task_id"],
                employee_id=eid,
                employee_name=name,
            )
        with pytest.raises(HTTPException) as exc:
            await start_helper_session(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id=fx["task_id"],
                employee_id=fx["helper1_id"],
                employee_name="H1",
            )
        assert exc.value.detail["error"] == "helper_session_already_active"

        stopped = await stop_helper_session(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
        )
        assert stopped["operation_completed"] is False
        assert stopped["membership_unchanged"] is True
        mem = (
            await fx["db_session"].execute(
                select(ExecutionTaskParticipant).where(
                    ExecutionTaskParticipant.employee_id == fx["helper1_id"],
                    ExecutionTaskParticipant.order_id == fx["order_id"],
                )
            )
        ).scalar_one()
        assert mem.status == "active"
        # Helper2 still active
        reality = (
            await fx["db_session"].execute(
                select(ExecutionReality).where(ExecutionReality.order_id == fx["order_id"])
            )
        ).scalar_one()
        import json

        sessions = [
            e
            for e in json.loads(reality.tasks_json or "[]")
            if isinstance(e, dict) and str(e.get("task_id")) == fx["task_id"]
        ]
        active_h2 = [
            s
            for s in sessions
            if int(s.get("employee_id") or 0) == fx["helper2_id"]
            and not s.get("ended_at")
        ]
        assert active_h2

        # Assignment unchanged on plan
        plan = (
            await fx["db_session"].execute(
                select(ExecutionPlan)
                .where(ExecutionPlan.order_id == fx["order_id"])
                .order_by(ExecutionPlan.id.desc())
                .limit(1)
            )
        ).scalar_one()
        task = next(
            t
            for t in operational_tasks_only(plan.tasks_json)
            if str(t.get("task_id")) == fx["task_id"]
        )
        assert task.get("assigned_employee_id") in (None, fx["principal_id"])

    fx["db_fixture"].run(_run())


def test_s3_legacy_no_id_session_not_own(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
        )
        svc = ExecutionRealityService(fx["db_session"])
        now = datetime.now(timezone.utc).isoformat()
        await svc.start_task(
            fx["order_id"],
            f"ORD-{fx['order_id']}",
            fx["task_id"],
            now,
            initial_fields={"employee_name": "legacy", "source": "legacy"},
        )
        started = await start_helper_session(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
            employee_name="H1",
        )
        assert started["session"]["employee_id"] == fx["helper1_id"]

    fx["db_fixture"].run(_run())


def test_s4_helper_session_does_not_grant_principal_complete(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
        )
        await start_helper_session(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
            employee_name="H1",
        )
        mine = await list_my_tasks(fx["db_session"], fx["helper1_id"])
        match = next(
            t
            for t in mine
            if int(t["order_id"]) == fx["order_id"] and str(t["task_id"]) == fx["task_id"]
        )
        assert match["visible_as_helper"] is True
        assert match["visible_as_principal"] is False
        assert match["can_complete_operation"] is False
        assert match["can_stop_own_session"] is True
        from services.employee_mobile_tasks_service import complete_my_task

        with pytest.raises(HTTPException) as exc:
            await complete_my_task(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id=fx["task_id"],
                employee_id=fx["helper1_id"],
            )
        assert exc.value.status_code == 403

    fx["db_fixture"].run(_run())


def test_r1_collab_read_open_help(phase2_fixture):
    fx = phase2_fixture

    async def _run():
        await create_help_request(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            requested_by_employee_id=fx["principal_id"],
            body=HelpRequestCreateBody(),
        )
        payload = await build_order_task_collaboration_read(
            fx["db_session"], fx["order_id"]
        )
        assert payload.contract_version == "execution_task_collaboration_read/v1.2"
        task = next(t for t in payload.tasks if t.task_id == fx["task_id"])
        assert task.has_open_help is True
        assert len(task.open_help_requests) == 1

    fx["db_fixture"].run(_run())


def test_r2_phase2_flag_blocks_help_writes(phase2_fixture, monkeypatch):
    fx = phase2_fixture
    monkeypatch.setenv("FLEX_COLLAB_PHASE2_ENABLED", "false")
    reset_flex_membership_flags_cache()

    async def _run():
        with pytest.raises(HTTPException) as exc:
            await create_help_request(
                fx["db_session"],
                order_id=fx["order_id"],
                task_id=fx["task_id"],
                requested_by_employee_id=fx["principal_id"],
                body=HelpRequestCreateBody(),
            )
        assert exc.value.status_code == 503
        # Phase 1 membership still works
        joined = await join_helper_membership(
            fx["db_session"],
            order_id=fx["order_id"],
            task_id=fx["task_id"],
            employee_id=fx["helper1_id"],
        )
        assert joined.membership.status == "active"
        pool = await list_help_opportunity_tasks(fx["db_session"], fx["helper1_id"])
        assert pool == []

    fx["db_fixture"].run(_run())


def test_r3_claim_pool_still_guards_other_session(db_fixture, db_session):
    """Principal available/claim retains _has_active_session_by_other."""
    claim_user = f"p2-claim-{uuid.uuid4().hex[:8]}"
    other_user = f"p2-other-{uuid.uuid4().hex[:8]}"
    order_id = _unique_order_id() + 90000

    async def _setup():
        claimer = await _seed_employee(db_session, user_id=claim_user, name="Claimer")
        other = await _seed_employee(db_session, user_id=other_user, name="Other")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, claimer.id)
        await _seed_print_eligibility(db_session, other.id)
        await _seed_plan_unassigned_task(db_session, order_id=order_id, task_id="T-P2-CLAIM")
        svc = ExecutionRealityService(db_session)
        now = datetime.now(timezone.utc).isoformat()
        await svc.start_task(
            order_id,
            f"ORD-{order_id}",
            "T-P2-CLAIM",
            now,
            initial_fields={
                "employee_id": other.id,
                "employee_name": "Other",
            },
        )
        return {"claimer_id": claimer.id}

    seeded = db_fixture.run(_setup())

    async def _check():
        available = await list_available_tasks(db_session, seeded["claimer_id"])
        match = [
            t
            for t in available
            if int(t["order_id"]) == order_id and str(t["task_id"]) == "T-P2-CLAIM"
        ]
        # Guard: task with another active session must not appear as claimable.
        assert match == []

    db_fixture.run(_check())
    _cleanup_overrides()
