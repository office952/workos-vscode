"""FLEX-01 read-only execution task collaboration projection tests."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.auth import UserResponse
from services.execution_reality_service import ExecutionRealityService
from services.execution_task_collaboration_read_service import (
    build_order_task_collaboration_read,
    derive_operation_completion_truth,
    project_task_collaboration_read,
)
from services.task_work_session_service import build_work_session_observation

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
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


def _plan_task(
    *,
    task_id: str = "T-FLEX-01",
    assigned_employee_id: int | None = None,
    assignment_source: str | None = None,
) -> dict:
    task = {
        "task_id": task_id,
        "name": "Asamblare 40 litere",
        "display_name": "Asamblare 40 litere",
        "process_id": "assembly",
        "process_type": "assembly",
    }
    if assigned_employee_id is not None:
        task["assigned_employee_id"] = assigned_employee_id
    if assignment_source is not None:
        task["assignment_source"] = assignment_source
    return task


def _session(
    *,
    task_id: str,
    employee_id: int,
    employee_name: str,
    started_at: str,
    ended_at: str | None = None,
    completed_by_employee_id: int | None = None,
    role: str = "primary",
) -> dict:
    entry = build_work_session_observation(
        task_id=task_id,
        employee_id=employee_id,
        employee_name=employee_name,
        started_at_iso=started_at,
        role=role,
    )
    if ended_at:
        entry["ended_at"] = ended_at
        entry["duration_minutes"] = 30
        entry["status"] = "completed" if completed_by_employee_id else "ended"
    if completed_by_employee_id is not None:
        entry["completed_by_employee_id"] = completed_by_employee_id
    return entry


def _project(
    *,
    assigned_employee_id: int | None,
    sessions: list[dict],
    assignment_source: str | None = None,
) -> dict:
    projection = project_task_collaboration_read(
        task_id="T-FLEX-01",
        plan_task=_plan_task(
            assigned_employee_id=assigned_employee_id,
            assignment_source=assignment_source,
        ),
        sessions=sessions,
        employee_names={
            10: "Principal Ten",
            20: "Worker Twenty",
            30: "Worker Thirty",
        },
    )
    return projection.model_dump()


class TestScenarioAPrincipalWithoutSession:
    def test_principal_without_session(self):
        body = _project(assigned_employee_id=10, sessions=[])
        principal = body["optional_principal"]
        assert principal["optional_principal_employee_id"] == 10
        assert principal["principal_has_started"] is False
        assert body["actual_workers"] == []
        assert body["operation_completed"] is False


class TestScenarioBWorkerWithoutPrincipal:
    def test_worker_without_principal(self):
        body = _project(
            assigned_employee_id=None,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=20,
                    employee_name="Worker Twenty",
                    started_at="2026-07-15T08:00:00+00:00",
                )
            ],
        )
        assert body["optional_principal"]["optional_principal_employee_id"] is None
        assert body["optional_principal"]["principal_has_started"] is False
        assert len(body["actual_workers"]) == 1
        assert body["actual_workers"][0]["employee_id"] == 20


class TestScenarioCPrincipalStartsWork:
    def test_principal_starts_work(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=10,
                    employee_name="Principal Ten",
                    started_at="2026-07-15T08:00:00+00:00",
                )
            ],
            assignment_source="employee_claim",
        )
        principal = body["optional_principal"]
        assert principal["optional_principal_employee_id"] == 10
        assert principal["principal_has_started"] is True
        assert principal["optional_principal_source"] == "employee_claim"
        assert len(body["actual_workers"]) == 1
        assert body["actual_workers"][0]["is_optional_principal"] is True


class TestScenarioDPrincipalPlusHelper:
    def test_principal_plus_helper(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=10,
                    employee_name="Principal Ten",
                    started_at="2026-07-15T08:00:00+00:00",
                ),
                _session(
                    task_id="T-FLEX-01",
                    employee_id=20,
                    employee_name="Worker Twenty",
                    started_at="2026-07-15T08:10:00+00:00",
                    role="helper",
                ),
            ],
        )
        assert body["has_multiple_actual_workers"] is True
        worker_ids = {worker["employee_id"] for worker in body["actual_workers"]}
        assert worker_ids == {10, 20}
        helpers = [worker for worker in body["actual_workers"] if worker["employee_id"] == 20]
        assert helpers[0]["is_optional_principal"] is False


class TestScenarioEMultipleWorkersWithoutPrincipal:
    def test_multiple_workers_without_principal(self):
        body = _project(
            assigned_employee_id=None,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=20,
                    employee_name="Worker Twenty",
                    started_at="2026-07-15T08:00:00+00:00",
                ),
                _session(
                    task_id="T-FLEX-01",
                    employee_id=30,
                    employee_name="Worker Thirty",
                    started_at="2026-07-15T08:05:00+00:00",
                ),
            ],
        )
        assert body["optional_principal"]["optional_principal_employee_id"] is None
        assert body["has_multiple_actual_workers"] is True
        assert len(body["actual_workers"]) == 2


class TestScenarioFMultipleSessionsSameWorker:
    def test_multiple_sessions_same_worker(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=20,
                    employee_name="Worker Twenty",
                    started_at="2026-07-15T08:00:00+00:00",
                    ended_at="2026-07-15T08:30:00+00:00",
                ),
                _session(
                    task_id="T-FLEX-01",
                    employee_id=20,
                    employee_name="Worker Twenty",
                    started_at="2026-07-15T09:00:00+00:00",
                ),
            ],
        )
        assert len(body["actual_workers"]) == 1
        worker = body["actual_workers"][0]
        assert worker["session_count"] == 2
        assert worker["individual_work_time_minutes"] == 30.0
        assert len(worker["worker_sessions"]) == 2


class TestScenarioGActiveAndClosedSessions:
    def test_active_and_closed_sessions(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=10,
                    employee_name="Principal Ten",
                    started_at="2026-07-15T08:00:00+00:00",
                ),
                _session(
                    task_id="T-FLEX-01",
                    employee_id=20,
                    employee_name="Worker Twenty",
                    started_at="2026-07-15T07:00:00+00:00",
                    ended_at="2026-07-15T07:30:00+00:00",
                ),
            ],
        )
        active_ids = {worker["employee_id"] for worker in body["active_workers"]}
        completed_ids = {
            worker["employee_id"] for worker in body["completed_session_workers"]
        }
        assert active_ids == {10}
        assert completed_ids == {20}
        assert {worker["employee_id"] for worker in body["actual_workers"]} == {10, 20}
        assert body["operation_completed"] is False


class TestScenarioHAllSessionsStopped:
    def test_all_sessions_stopped_without_explicit_completion(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=10,
                    employee_name="Principal Ten",
                    started_at="2026-07-15T08:00:00+00:00",
                    ended_at="2026-07-15T08:30:00+00:00",
                ),
                _session(
                    task_id="T-FLEX-01",
                    employee_id=20,
                    employee_name="Worker Twenty",
                    started_at="2026-07-15T08:10:00+00:00",
                    ended_at="2026-07-15T08:40:00+00:00",
                ),
            ],
        )
        assert body["active_workers"] == []
        assert len(body["actual_workers"]) == 2
        assert body["all_sessions_closed"] is True
        assert body["operation_completed"] is False
        assert body["operation_completion_source"] == "session_stop_without_explicit_completion"
        assert body["derived_session_status"] == "done"
        assert body["legacy_or_derived_task_status"] == "done"


class TestScenarioIOperationCompleteWithSessions:
    def test_operation_complete_with_explicit_session_completion(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=10,
                    employee_name="Principal Ten",
                    started_at="2026-07-15T08:00:00+00:00",
                    ended_at="2026-07-15T08:30:00+00:00",
                    completed_by_employee_id=10,
                ),
            ],
        )
        assert body["operation_completed"] is True
        assert body["operation_completion_source"] == "all_sessions_explicitly_completed"
        assert body["derived_session_status"] == "done"
        assert body["all_sessions_closed"] is True


class TestScenario3OneStoppedSessionNotComplete:
    def test_one_stopped_session_operation_not_complete(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=10,
                    employee_name="Principal Ten",
                    started_at="2026-07-15T08:00:00+00:00",
                    ended_at="2026-07-15T08:30:00+00:00",
                ),
            ],
        )
        assert body["all_sessions_closed"] is True
        assert body["operation_completed"] is False
        assert body["operation_completion_source"] == "session_stop_without_explicit_completion"


class TestScenario4MultipleStoppedSessionsNotComplete:
    def test_multiple_stopped_sessions_operation_not_complete(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=10,
                    employee_name="Principal Ten",
                    started_at="2026-07-15T08:00:00+00:00",
                    ended_at="2026-07-15T08:30:00+00:00",
                ),
                _session(
                    task_id="T-FLEX-01",
                    employee_id=20,
                    employee_name="Worker Twenty",
                    started_at="2026-07-15T08:10:00+00:00",
                    ended_at="2026-07-15T08:40:00+00:00",
                ),
            ],
        )
        assert body["all_sessions_closed"] is True
        assert body["has_multiple_actual_workers"] is True
        assert body["operation_completed"] is False


class TestScenario6LegacyStatusSeparated:
    def test_legacy_done_does_not_imply_operation_completed(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=10,
                    employee_name="Principal Ten",
                    started_at="2026-07-15T08:00:00+00:00",
                    ended_at="2026-07-15T08:30:00+00:00",
                ),
            ],
        )
        assert body["legacy_or_derived_task_status"] == "done"
        assert body["operation_completed"] is False


class TestScenario7HelperStopDoesNotCompleteOperation:
    def test_helper_stopped_principal_still_active(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=10,
                    employee_name="Principal Ten",
                    started_at="2026-07-15T08:00:00+00:00",
                ),
                _session(
                    task_id="T-FLEX-01",
                    employee_id=20,
                    employee_name="Worker Twenty",
                    started_at="2026-07-15T08:10:00+00:00",
                    ended_at="2026-07-15T08:40:00+00:00",
                    role="helper",
                ),
            ],
        )
        assert body["operation_completed"] is False
        assert body["operation_completion_source"] == "active_sessions_remain"


def test_derive_operation_completion_truth_blocker_cases():
    stopped = _session(
        task_id="T-FLEX-01",
        employee_id=10,
        employee_name="Principal Ten",
        started_at="2026-07-15T08:00:00+00:00",
        ended_at="2026-07-15T08:30:00+00:00",
    )
    completed, source = derive_operation_completion_truth([stopped])
    assert completed is False
    assert source == "session_stop_without_explicit_completion"

    explicit = _session(
        task_id="T-FLEX-01",
        employee_id=10,
        employee_name="Principal Ten",
        started_at="2026-07-15T08:00:00+00:00",
        ended_at="2026-07-15T08:30:00+00:00",
        completed_by_employee_id=10,
    )
    completed, source = derive_operation_completion_truth([explicit])
    assert completed is True
    assert source == "all_sessions_explicitly_completed"


class TestScenario5ExplicitOperationCompleteAllWorkers:
    def test_all_workers_explicitly_completed(self):
        body = _project(
            assigned_employee_id=10,
            sessions=[
                _session(
                    task_id="T-FLEX-01",
                    employee_id=10,
                    employee_name="Principal Ten",
                    started_at="2026-07-15T08:00:00+00:00",
                    ended_at="2026-07-15T08:30:00+00:00",
                    completed_by_employee_id=10,
                ),
                _session(
                    task_id="T-FLEX-01",
                    employee_id=20,
                    employee_name="Worker Twenty",
                    started_at="2026-07-15T08:10:00+00:00",
                    ended_at="2026-07-15T08:40:00+00:00",
                    completed_by_employee_id=20,
                    role="helper",
                ),
            ],
        )
        assert body["operation_completed"] is True
        assert body["operation_completion_source"] == "all_sessions_explicitly_completed"


class TestScenarioJBackwardCompatibility:
    def test_projection_does_not_require_new_persistence_fields(self):
        body = _project(assigned_employee_id=10, sessions=[])
        assert "optional_principal" in body
        assert "actual_workers" in body
        assert "participants_json" not in body


@pytest.fixture
def flex_order_fixture(db_fixture, db_session):
    order_id = 9200 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        primary = await _seed_employee(db_session, user_id=f"flex-primary-{uuid.uuid4().hex[:6]}")
        helper = await _seed_employee(db_session, user_id=f"flex-helper-{uuid.uuid4().hex[:6]}")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=primary.id,
            task_id="T-FLEX-DB",
        )
        return {
            "order_id": order_id,
            "primary_id": primary.id,
            "helper_id": helper.id,
        }

    ids = db_fixture.run(_setup())
    yield {**ids, "db_fixture": db_fixture, "db_session": db_session}
    _cleanup_overrides()


def test_build_order_task_collaboration_read_integration(flex_order_fixture):
    db_session = flex_order_fixture["db_session"]
    order_id = flex_order_fixture["order_id"]
    primary_id = flex_order_fixture["primary_id"]
    helper_id = flex_order_fixture["helper_id"]

    async def _run():
        svc = ExecutionRealityService(db_session)
        start_primary = datetime(2026, 7, 15, 8, 0, tzinfo=timezone.utc).isoformat()
        start_helper = datetime(2026, 7, 15, 8, 10, tzinfo=timezone.utc).isoformat()
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-FLEX-DB",
            start_primary,
            initial_fields={
                "employee_id": primary_id,
                "employee_name": "Primary Worker",
                "role": "primary",
            },
        )
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-FLEX-DB",
            start_helper,
            initial_fields={
                "employee_id": helper_id,
                "employee_name": "Helper Worker",
                "role": "helper",
            },
        )
        payload = await build_order_task_collaboration_read(db_session, order_id)
        assert payload.contract_version == "execution_task_collaboration_read/v1.2"
        task = next(item for item in payload.tasks if item.task_id == "T-FLEX-DB")
        assert task.optional_principal.optional_principal_employee_id == primary_id
        assert task.has_multiple_actual_workers is True
        assert len(task.active_workers) == 2
        assert task.operation_completed is False

    flex_order_fixture["db_fixture"].run(_run())


def test_task_collaboration_read_endpoint(flex_order_fixture):
    order_id = flex_order_fixture["order_id"]
    client = _client_for(flex_order_fixture["db_fixture"], _user("operator-flex", "operator"))
    response = client.get(f"/api/v1/operator/orders/{order_id}/task-collaboration-read")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "execution_task_collaboration_read/v1.2"
    assert body["order_id"] == order_id
    assert len(body["tasks"]) == 1
    assert body["tasks"][0]["task_id"] == "T-FLEX-DB"
    assert "legacy_or_derived_task_status" in body["tasks"][0]
    assert "operation_completion_source" in body["tasks"][0]


def test_mobile_claim_behavior_unchanged_after_read_model(db_fixture, db_session):
    user_id = f"flex-claim-{uuid.uuid4().hex[:8]}"
    order_id = 9300 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Claimer Flex")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, emp.id)
        await _seed_plan_unassigned_task(
            db_session,
            order_id=order_id,
            task_id="T-CLAIM-FLEX",
        )
        return emp.id

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        claim = client.post(
            "/api/v1/employee-mobile/tasks/T-CLAIM-FLEX/claim",
            json={"order_id": order_id},
        )
        assert claim.status_code == 200, claim.text
        assert claim.json()["already_claimed"] is False
    finally:
        _cleanup_overrides()
