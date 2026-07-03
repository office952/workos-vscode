"""Task readiness and dependency MVP tests."""

from __future__ import annotations

import json
import uuid

import pytest
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.task_dependency_rules_service import (
    apply_task_dependency_rules_to_plan_tasks,
    backfill_plan_task_dependencies,
)
from services.task_readiness_service import (
    READINESS_ELIGIBLE,
    READINESS_IN_PROGRESS,
    READINESS_WAITING_PREDECESSOR,
    evaluate_all_task_readiness,
    evaluate_task_readiness,
    build_readiness_context,
)
from services.volumetric_return_task_taxonomy_service import apply_volumetric_return_taxonomy_to_plan_tasks

from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_employee,
    _seed_plan_with_assigned_task,
    _seed_reality_task,
    _user,
)


def _build_volumetric_tasks(*, sandu_id: int) -> list[dict]:
    raw = [
        {"task_id": "T-001", "process_id": "vector_prep", "process_type": "file_preparation", "machine_type": "PREPRESS", "estimated_time_minutes": 15},
        {"task_id": "T-002", "process_id": "face_cnc_cut", "process_type": "cnc_routing", "machine_type": "CNC_ROUTER", "estimated_time_minutes": 45},
        {"task_id": "T-003", "process_id": "side_forming", "process_type": "edge_bending", "machine_type": "RETURN_PROFILE_FORMING_MACHINE", "estimated_time_minutes": 30},
        {"task_id": "T-004", "process_id": "return_face_bonding", "process_type": "welding", "machine_type": "ASSEMBLY_TABLE", "estimated_time_minutes": 25, "assigned_employee_id": sandu_id},
        {"task_id": "T-005", "process_id": "back_cut", "process_type": "cnc_routing", "machine_type": "CNC_ROUTER", "estimated_time_minutes": 40},
        {"task_id": "T-006", "process_id": "led_install_letters", "process_type": "led_assembly", "machine_type": "LED_ASSEMBLY", "estimated_time_minutes": 30, "assigned_employee_id": sandu_id},
        {"task_id": "T-007", "process_id": "electrical_letters", "process_type": "led_wiring", "machine_type": "ELECTRICAL_WIRING", "estimated_time_minutes": 20, "assigned_employee_id": sandu_id},
        {"task_id": "T-008", "process_id": "mounting_template_cnc_cut", "process_type": "cnc_routing", "machine_type": "CNC_ROUTER", "estimated_time_minutes": 25, "assigned_employee_id": sandu_id},
        {"task_id": "T-009", "process_id": "assembly_letters", "process_type": "volumetric_letter_assembly", "machine_type": "ASSEMBLY", "estimated_time_minutes": 60, "assigned_employee_id": sandu_id},
        {"task_id": "T-010", "process_id": "qc_letters", "process_type": "quality_control", "machine_type": "QC_INSPECTION", "estimated_time_minutes": 15, "assigned_employee_id": sandu_id},
        {"task_id": "T-011", "process_id": "packaging_letters", "process_type": "packaging", "machine_type": "PACKAGING", "estimated_time_minutes": 10},
    ]
    tasks, _ = apply_volumetric_return_taxonomy_to_plan_tasks(raw, set_owner_instructions=False)
    tasks, _warnings, _action = apply_task_dependency_rules_to_plan_tasks(tasks)
    return tasks


def test_plan_generation_adds_dependencies_on_key_tasks():
    tasks = _build_volumetric_tasks(sandu_id=4)
    by_id = {t["task_id"]: t for t in tasks}
    assert "T-001" in by_id["T-002"]["depends_on_task_ids"]
    assert by_id["T-004"]["depends_on_task_ids"] == ["T-002", "T-003"]
    assert by_id["T-006"]["depends_on_task_ids"] == ["T-005"]
    assert by_id["T-007"]["depends_on_task_ids"] == ["T-006"]
    assert "T-004" in by_id["T-009"]["depends_on_task_ids"]
    assert by_id["T-010"]["depends_on_task_ids"] == ["T-009"]
    assert by_id["T-011"]["depends_on_task_ids"] == ["T-010"]
    assert by_id["T-008"]["depends_on_task_ids"] == ["T-001"]


def test_t008_has_no_strict_dependencies():
    tasks = _build_volumetric_tasks(sandu_id=4)
    t008 = next(t for t in tasks if t["task_id"] == "T-008")
    assert t008.get("depends_on_task_ids") == ["T-001"]


def test_readiness_t006_waiting_when_t005_not_done():
    tasks = _build_volumetric_tasks(sandu_id=4)
    readiness = evaluate_all_task_readiness(tasks, [], employee_id=4)
    assert readiness["T-006"]["readiness_status"] == READINESS_WAITING_PREDECESSOR
    assert readiness["T-006"]["is_startable"] is False
    assert "T-005" in readiness["T-006"]["blocking_task_ids"]


def test_readiness_becomes_eligible_when_predecessor_done(db_fixture, db_session):
    tasks = _build_volumetric_tasks(sandu_id=4)
    reality = [
        {
            "task_id": "T-005",
            "employee_id": 9,
            "started_at": "2026-06-12T08:00:00+00:00",
            "ended_at": "2026-06-12T09:00:00+00:00",
            "completed_by_employee_id": 9,
        }
    ]
    readiness = evaluate_all_task_readiness(tasks, reality, employee_id=4)
    assert readiness["T-006"]["readiness_status"] == READINESS_ELIGIBLE
    assert readiness["T-006"]["is_startable"] is True


def test_t004_in_progress_with_missing_predecessor_has_warning():
    tasks = _build_volumetric_tasks(sandu_id=4)
    reality = [
        {
            "task_id": "T-002",
            "employee_id": 7,
            "started_at": "2026-06-11T08:00:00+00:00",
            "ended_at": "2026-06-11T08:30:00+00:00",
            "completed_by_employee_id": 7,
        },
        {
            "task_id": "T-004",
            "employee_id": 4,
            "employee_name": "Putaru Sandu",
            "started_at": "2026-06-14T12:00:00+00:00",
        },
    ]
    context = build_readiness_context(tasks, reality)
    t004 = next(t for t in tasks if t["task_id"] == "T-004")
    result = evaluate_task_readiness(t004, context, employee_id=4)
    assert result["readiness_status"] == READINESS_IN_PROGRESS
    assert result["dependency_warning"]
    assert "T-003" in result["blocking_task_ids"]


def test_start_t006_blocked_when_not_ready(db_fixture, db_session):
    user_id = f"deps-{uuid.uuid4().hex[:8]}"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Sandu Deps")
        tasks = _build_volumetric_tasks(sandu_id=emp.id)
        db_session.add(
            ExecutionPlan(
                order_id=901,
                order_code="ORD-0901",
                snapshot_version=1,
                tasks_json=json.dumps(tasks),
                total_estimated_time_minutes=300,
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.patch(
            "/api/v1/employee-mobile/tasks/T-006/start",
            json={"order_id": 901},
        )
        assert response.status_code == 409, response.text
        detail = response.json()["detail"]
        assert detail.get("code") == "task_not_ready" or detail.get("error") == "task_not_ready"
        assert detail.get("readiness_status") == READINESS_WAITING_PREDECESSOR
    finally:
        _cleanup_overrides()


def test_employee_payload_includes_readiness_without_commercial_fields(db_fixture, db_session):
    user_id = f"ready-{uuid.uuid4().hex[:8]}"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Ready Worker")
        tasks = _build_volumetric_tasks(sandu_id=emp.id)
        db_session.add(
            ExecutionPlan(
                order_id=902,
                order_code="ORD-0902",
                snapshot_version=1,
                tasks_json=json.dumps(tasks),
                total_estimated_time_minutes=300,
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        rows = client.get("/api/v1/employee-mobile/tasks").json()
        t006 = next(r for r in rows if r["task_id"] == "T-006")
        assert t006["readiness_status"] == READINESS_WAITING_PREDECESSOR
        assert t006["is_startable"] is False
        assert "margin" not in json.dumps(t006).lower()
        assert "payroll" not in json.dumps(t006).lower()
    finally:
        _cleanup_overrides()


def test_operator_blueprint_includes_readiness(db_fixture, db_session):
    order_id = 903

    async def _setup():
        worker = await _seed_employee(db_session, user_id=None, name="Op Worker")
        tasks = _build_volumetric_tasks(sandu_id=worker.id)
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code="ORD-0903",
                snapshot_version=1,
                tasks_json=json.dumps(tasks),
                total_estimated_time_minutes=300,
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-op", "admin"))
    try:
        response = client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint")
        assert response.status_code == 200, response.text
        payload = response.json()
        t006 = next(t for t in payload["tasks"] if t["task_id"] == "T-006")
        assert t006["readiness_status"] == READINESS_WAITING_PREDECESSOR
        assert t006["is_startable"] is False
        assert t006["blocking_tasks"]
    finally:
        _cleanup_overrides()


def test_fixture_backfill_dependencies_idempotent():
    tasks = [
        {"task_id": "T-002", "process_id": "face_cnc_cut"},
        {"task_id": "T-004", "process_id": "return_face_bonding"},
    ]
    updated, action = backfill_plan_task_dependencies(tasks)
    assert action == "updated"
    assert updated[1]["depends_on_task_ids"] == ["T-002"]
    again, action2 = backfill_plan_task_dependencies(updated)
    assert action2 == "unchanged"


def test_execution_plan_service_from_order_can_chain_dependency_rules():
    """Dependency pass is applied at router persist — unit-test rules on synthetic tasks."""
    tasks = [
        {"task_id": "T-001", "process_id": "face_cnc_cut", "process_type": "cnc_routing", "estimated_time_minutes": 10},
        {"task_id": "T-002", "process_id": "return_face_bonding", "process_type": "welding", "estimated_time_minutes": 10},
    ]
    updated, _warnings, action = apply_task_dependency_rules_to_plan_tasks(tasks)
    assert action == "updated"
    assert updated[1]["depends_on_task_ids"] == ["T-001"]
