"""Manual procurement readiness MVP tests."""

from __future__ import annotations

import json
import uuid

import pytest
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.material_planning_service import (
    CATEGORY_PROJECT_CRITICAL,
    CATEGORY_STANDARD_LOW_COST,
    IMPACT_CAN_BLOCK,
    derive_material_planning_items,
)
from services.material_procurement_status_service import (
    STATUS_AVAILABLE,
    STATUS_AWAITING_ADVANCE,
    STATUS_NOT_CHECKED,
    STATUS_ORDERED,
    STATUS_RECEIVED,
    STATUS_SUGGEST_REPLENISH,
    STATUS_TO_ORDER,
    apply_procurement_statuses,
    is_material_status_blocking,
    material_items_by_task,
    update_material_procurement_status,
)
from services.task_readiness_service import (
    READINESS_WAITING_MATERIAL,
    READINESS_WAITING_PREDECESSOR,
    evaluate_all_task_readiness,
)

from tests.test_task_readiness_dependencies import _build_volumetric_tasks
from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_employee,
    _user,
)


def _enriched_with_status(tasks, statuses):
    items = derive_material_planning_items(tasks, product_context="TPL-VOLUMETRIC-LETTERS")
    enriched = apply_procurement_statuses(items, statuses)
    return enriched, material_items_by_task(enriched)


def test_default_procurement_status_is_not_checked():
    tasks = _build_volumetric_tasks(sandu_id=4)
    enriched, _ = _enriched_with_status(tasks, {})
    assert all(item["procurement_status"] == STATUS_NOT_CHECKED for item in enriched)


def test_not_checked_does_not_block():
    tasks = _build_volumetric_tasks(sandu_id=4)
    enriched, by_task = _enriched_with_status(tasks, {})
    readiness = evaluate_all_task_readiness(
        tasks,
        [],
        employee_id=4,
        material_by_task=by_task,
    )
    assert readiness["T-006"]["readiness_status"] == READINESS_WAITING_PREDECESSOR
    assert all(not is_material_status_blocking(item) for item in enriched)


def test_standard_low_cost_stock_does_not_block():
    tasks = _build_volumetric_tasks(sandu_id=4)
    statuses = {
        "LED_FIXING_CONSUMABLES": {
            "status": STATUS_TO_ORDER,
            "note": "test",
            "affected_task_ids": ["T-006"],
        }
    }
    enriched, by_task = _enriched_with_status(tasks, statuses)
    consumable = next(item for item in enriched if item["code"] == "LED_FIXING_CONSUMABLES")
    assert consumable["category"] == CATEGORY_STANDARD_LOW_COST
    assert is_material_status_blocking(consumable) is False
    readiness = evaluate_all_task_readiness(
        tasks,
        [
            {
                "task_id": "T-005",
                "employee_id": 9,
                "started_at": "2026-06-12T08:00:00+00:00",
                "ended_at": "2026-06-12T09:00:00+00:00",
                "completed_by_employee_id": 9,
            }
        ],
        employee_id=4,
        material_by_task=by_task,
    )
    assert readiness["T-006"]["readiness_status"] != READINESS_WAITING_MATERIAL


def test_suggest_replenish_does_not_block():
    tasks = _build_volumetric_tasks(sandu_id=4)
    statuses = {
        "PLEXI_FACE": {"status": STATUS_SUGGEST_REPLENISH, "note": "", "affected_task_ids": ["T-002"]},
    }
    enriched, by_task = _enriched_with_status(tasks, statuses)
    plexi = next(item for item in enriched if item["code"] == "PLEXI_FACE")
    assert plexi["category"] == CATEGORY_PROJECT_CRITICAL
    assert is_material_status_blocking(plexi) is False


def test_project_critical_awaiting_advance_can_block():
    tasks = _build_volumetric_tasks(sandu_id=4)
    statuses = {
        "LED_MODULE": {
            "status": STATUS_AWAITING_ADVANCE,
            "note": "Se comandă după avans.",
            "affected_task_ids": ["T-006"],
        }
    }
    enriched, by_task = _enriched_with_status(tasks, statuses)
    led = next(item for item in enriched if item["code"] == "LED_MODULE")
    assert led["readiness_impact"] == IMPACT_CAN_BLOCK
    assert is_material_status_blocking(led) is True


def test_to_order_can_block():
    tasks = _build_volumetric_tasks(sandu_id=4)
    statuses = {
        "LED_MODULE": {"status": STATUS_TO_ORDER, "note": "Comandă urgentă", "affected_task_ids": ["T-006"]},
    }
    enriched, _ = _enriched_with_status(tasks, statuses)
    led = next(item for item in enriched if item["code"] == "LED_MODULE")
    assert is_material_status_blocking(led) is True


def test_ordered_can_block_until_received_or_available():
    tasks = _build_volumetric_tasks(sandu_id=4)
    statuses = {
        "LED_MODULE": {"status": STATUS_ORDERED, "note": "Comandat", "affected_task_ids": ["T-006"]},
    }
    enriched, _ = _enriched_with_status(tasks, statuses)
    led = next(item for item in enriched if item["code"] == "LED_MODULE")
    assert is_material_status_blocking(led) is True


def test_received_does_not_block():
    tasks = _build_volumetric_tasks(sandu_id=4)
    statuses = {
        "LED_MODULE": {"status": STATUS_RECEIVED, "note": "", "affected_task_ids": ["T-006"]},
    }
    enriched, _ = _enriched_with_status(tasks, statuses)
    led = next(item for item in enriched if item["code"] == "LED_MODULE")
    assert is_material_status_blocking(led) is False


def test_available_does_not_block():
    tasks = _build_volumetric_tasks(sandu_id=4)
    statuses = {
        "LED_MODULE": {"status": STATUS_AVAILABLE, "note": "", "affected_task_ids": ["T-006"]},
    }
    enriched, by_task = _enriched_with_status(tasks, statuses)
    readiness = evaluate_all_task_readiness(
        tasks,
        [
            {
                "task_id": "T-005",
                "employee_id": 9,
                "started_at": "2026-06-12T08:00:00+00:00",
                "ended_at": "2026-06-12T09:00:00+00:00",
                "completed_by_employee_id": 9,
            }
        ],
        employee_id=4,
        material_by_task=by_task,
    )
    assert readiness["T-006"]["readiness_status"] == "eligible"


def test_dependencies_have_priority_over_material():
    tasks = _build_volumetric_tasks(sandu_id=4)
    statuses = {
        "LED_MODULE": {
            "status": STATUS_AWAITING_ADVANCE,
            "note": "Se comandă după avans.",
            "affected_task_ids": ["T-006"],
        }
    }
    _, by_task = _enriched_with_status(tasks, statuses)
    readiness = evaluate_all_task_readiness(tasks, [], employee_id=4, material_by_task=by_task)
    assert readiness["T-006"]["readiness_status"] == READINESS_WAITING_PREDECESSOR
    assert readiness["T-006"].get("material_warning")


def test_t006_predecessor_missing_led_awaiting_advance_stays_predecessor():
    tasks = _build_volumetric_tasks(sandu_id=4)
    statuses = {
        "LED_MODULE": {
            "status": STATUS_AWAITING_ADVANCE,
            "note": "Se comandă după avans.",
            "affected_task_ids": ["T-006"],
        }
    }
    _, by_task = _enriched_with_status(tasks, statuses)
    readiness = evaluate_all_task_readiness(tasks, [], employee_id=4, material_by_task=by_task)
    assert readiness["T-006"]["readiness_status"] == READINESS_WAITING_PREDECESSOR


def test_t006_predecessor_done_led_awaiting_advance_becomes_waiting_material():
    tasks = _build_volumetric_tasks(sandu_id=4)
    statuses = {
        "LED_MODULE": {
            "status": STATUS_AWAITING_ADVANCE,
            "note": "Se comandă după avans.",
            "affected_task_ids": ["T-006"],
        }
    }
    _, by_task = _enriched_with_status(tasks, statuses)
    reality = [
        {
            "task_id": "T-005",
            "employee_id": 9,
            "started_at": "2026-06-12T08:00:00+00:00",
            "ended_at": "2026-06-12T09:00:00+00:00",
            "completed_by_employee_id": 9,
        }
    ]
    readiness = evaluate_all_task_readiness(
        tasks,
        reality,
        employee_id=4,
        material_by_task=by_task,
    )
    assert readiness["T-006"]["readiness_status"] == READINESS_WAITING_MATERIAL
    assert readiness["T-006"]["is_startable"] is False
    assert readiness["T-006"]["readiness_reasons"][0]["code"] == "material_procurement_block"


@pytest.fixture
def procurement_fixture(db_fixture, db_session):
    user_id = f"proc-{uuid.uuid4().hex[:8]}"
    order_id = 9600 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        worker = await _seed_employee(db_session, user_id=user_id, name="Proc Worker")
        tasks = _build_volumetric_tasks(sandu_id=worker.id)
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-PROC-{order_id}",
                snapshot_version=1,
                tasks_json=json.dumps(tasks),
                total_estimated_time_minutes=300,
            )
        )
        db_session.add(
            ExecutionReality(
                order_id=order_id,
                order_code=f"ORD-PROC-{order_id}",
                tasks_json="[]",
                total_actual_time_minutes=0,
            )
        )
        await db_session.commit()
        return worker.id

    worker_id = db_fixture.run(_setup())
    employee_client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    admin_client = _client_for(db_fixture, _user(f"admin-proc-{uuid.uuid4().hex[:6]}", "admin"))
    yield employee_client, admin_client, order_id, worker_id, user_id, db_fixture
    _cleanup_overrides()


def test_patch_operator_status_works(procurement_fixture):
    _, admin, order_id, _, _, _ = procurement_fixture
    response = admin.patch(
        f"/api/v1/operator/orders/{order_id}/material-procurement/LED_MODULE",
        json={
            "status": STATUS_AWAITING_ADVANCE,
            "note": "Se comandă după avans.",
            "affected_task_ids": ["T-006"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["material_code"] == "LED_MODULE"
    assert body["material_item"]["procurement_status"] == STATUS_AWAITING_ADVANCE
    assert body["production_planning_summary"]["awaiting_advance_items"] >= 1


def test_employee_mobile_cannot_patch(procurement_fixture):
    _, _, order_id, _, user_id, db_fixture = procurement_fixture
    employee_only = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    response = employee_only.patch(
        f"/api/v1/operator/orders/{order_id}/material-procurement/LED_MODULE",
        json={"status": STATUS_TO_ORDER, "note": "hack"},
    )
    assert response.status_code == 403
    _cleanup_overrides()


def test_invalid_material_code_returns_404(procurement_fixture):
    _, admin, order_id, _, _, _ = procurement_fixture
    response = admin.patch(
        f"/api/v1/operator/orders/{order_id}/material-procurement/NOT_A_REAL_CODE",
        json={"status": STATUS_TO_ORDER, "note": "missing"},
    )
    assert response.status_code == 404


def test_employee_payload_has_no_commercial_fields(procurement_fixture):
    _, admin, order_id, _, user_id, db_fixture = procurement_fixture
    admin.patch(
        f"/api/v1/operator/orders/{order_id}/material-procurement/LED_MODULE",
        json={
            "status": STATUS_AWAITING_ADVANCE,
            "note": "Se comandă după avans.",
            "affected_task_ids": ["T-006"],
        },
    )
    employee_only = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    body = employee_only.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint").json()
    _cleanup_overrides()
    raw = json.dumps(body).lower()
    for forbidden in ("unit_cost", "price", "margin", "markup", "payroll", "supplier"):
        assert forbidden not in raw


def test_operator_blueprint_includes_production_planning_summary(procurement_fixture):
    _, admin, order_id, _, _, _ = procurement_fixture
    body = admin.get(f"/api/v1/operator/orders/{order_id}/production-blueprint").json()
    assert "production_planning_summary" in body
    summary = body["production_planning_summary"]
    assert "eligible_tasks" in summary
    assert "waiting_material_tasks" in summary
    assert "suggested_next_action" in summary


def test_no_inventory_reservation_or_deduction():
    import services.material_procurement_status_service as mod

    source = open(mod.__file__, encoding="utf-8").read().lower()
    assert "inventory_deduction" not in source
    assert "reservation" not in source
