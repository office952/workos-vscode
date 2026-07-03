"""Material planning hints foundation tests."""

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
    IMPACT_CHECKLIST_ONLY,
    IMPACT_NO_TASK_BLOCK,
    IMPACT_SUGGEST_REPLENISH,
    POLICY_BUY_AFTER_ADVANCE,
    derive_material_planning_items,
    derive_task_material_hints,
    employee_safe_material_hints_for_task,
    summarize_material_planning,
)
from services.task_readiness_service import READINESS_WAITING_PREDECESSOR, evaluate_all_task_readiness

from tests.test_task_readiness_dependencies import _build_volumetric_tasks
from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_employee,
    _user,
)


def test_derives_items_for_volumetric_template():
    tasks = _build_volumetric_tasks(sandu_id=4)
    items = derive_material_planning_items(tasks, product_context="TPL-VOLUMETRIC-LETTERS")
    codes = {item["code"] for item in items}
    assert "PLEXI_FACE" in codes
    assert "ALU_RETURN_PROFILE" in codes
    assert "FOREX_BACKING_10MM" in codes
    assert "LED_MODULE" in codes
    assert "LED_POWER_SUPPLY" in codes
    assert "MOUNTING_PROFILE_OR_BARS" in codes
    assert len(items) >= 10


def test_t002_has_plexi_face():
    tasks = _build_volumetric_tasks(sandu_id=4)
    hints = derive_task_material_hints(tasks)
    t002 = hints["T-002"]
    assert any(item["code"] == "PLEXI_FACE" for item in t002)


def test_t003_has_alu_return_profile():
    tasks = _build_volumetric_tasks(sandu_id=4)
    hints = derive_task_material_hints(tasks)
    assert any(item["code"] == "ALU_RETURN_PROFILE" for item in hints["T-003"])


def test_t005_has_forex_backing():
    tasks = _build_volumetric_tasks(sandu_id=4)
    hints = derive_task_material_hints(tasks)
    assert any(item["code"] == "FOREX_BACKING_10MM" for item in hints["T-005"])


def test_t006_has_led_module_and_fixing_consumables():
    tasks = _build_volumetric_tasks(sandu_id=4)
    hints = derive_task_material_hints(tasks)
    codes = {item["code"] for item in hints["T-006"]}
    assert "LED_MODULE" in codes
    assert "LED_FIXING_CONSUMABLES" in codes


def test_t007_has_power_supply_and_electrical_consumables():
    tasks = _build_volumetric_tasks(sandu_id=4)
    hints = derive_task_material_hints(tasks)
    codes = {item["code"] for item in hints["T-007"]}
    assert "LED_POWER_SUPPLY" in codes
    assert "ELECTRICAL_CONSUMABLES" in codes


def test_t008_has_mounting_profile_and_consumables():
    tasks = _build_volumetric_tasks(sandu_id=4)
    hints = derive_task_material_hints(tasks)
    codes = {item["code"] for item in hints["T-008"]}
    assert "MOUNTING_PROFILE_OR_BARS" in codes
    assert "MOUNTING_CONSUMABLES" in codes


def test_small_consumables_not_can_block():
    tasks = _build_volumetric_tasks(sandu_id=4)
    items = derive_material_planning_items(tasks)
    small = [
        item
        for item in items
        if item["code"]
        in (
            "ASSEMBLY_ADHESIVE",
            "LED_FIXING_CONSUMABLES",
            "ELECTRICAL_CONSUMABLES",
            "MOUNTING_CONSUMABLES",
            "ASSEMBLY_CONSUMABLES",
            "PACKAGING_CONSUMABLES",
        )
    ]
    assert small
    assert all(item["readiness_impact"] != IMPACT_CAN_BLOCK for item in small)
    assert all(
        item["readiness_impact"] in (IMPACT_SUGGEST_REPLENISH, IMPACT_CHECKLIST_ONLY, IMPACT_NO_TASK_BLOCK)
        for item in small
    )


def test_project_critical_can_have_buy_after_advance():
    tasks = _build_volumetric_tasks(sandu_id=4)
    items = derive_material_planning_items(tasks)
    critical = [item for item in items if item["category"] == CATEGORY_PROJECT_CRITICAL]
    assert critical
    assert any(item["procurement_policy"] == POLICY_BUY_AFTER_ADVANCE for item in critical)


def test_summarize_material_planning_counts():
    tasks = _build_volumetric_tasks(sandu_id=4)
    items = derive_material_planning_items(tasks)
    summary = summarize_material_planning(items)
    assert summary["project_critical_count"] >= 4
    assert summary["suggest_replenishment_count"] >= 3
    assert summary["checklist_count"] >= 1
    assert summary["has_procurement_sensitive_items"] is True


def test_employee_safe_hints_aggregate_consumables():
    tasks = _build_volumetric_tasks(sandu_id=4)
    hints = derive_task_material_hints(tasks)["T-006"]
    safe = employee_safe_material_hints_for_task(hints)
    assert len(safe) <= 2
    assert any(h["name"] == "Module LED" for h in safe)
    raw = json.dumps(safe).lower()
    for forbidden in ("unit_cost", "price", "margin", "supplier", '"cost"'):
        assert forbidden not in raw


def test_readiness_t006_still_waiting_predecessor_with_material_hints():
    tasks = _build_volumetric_tasks(sandu_id=4)
    readiness = evaluate_all_task_readiness(tasks, [], employee_id=4)
    hints = derive_task_material_hints(tasks)
    assert readiness["T-006"]["readiness_status"] == READINESS_WAITING_PREDECESSOR
    assert hints["T-006"]


@pytest.fixture
def material_blueprint_fixture(db_fixture, db_session):
    user_id = f"mat-plan-{uuid.uuid4().hex[:8]}"
    order_id = 9500 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        worker = await _seed_employee(db_session, user_id=user_id, name="Material Worker")
        tasks = _build_volumetric_tasks(sandu_id=worker.id)
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-MAT-{order_id}",
                snapshot_version=1,
                tasks_json=json.dumps(tasks),
                total_estimated_time_minutes=300,
            )
        )
        db_session.add(
            ExecutionReality(
                order_id=order_id,
                order_code=f"ORD-MAT-{order_id}",
                tasks_json="[]",
                total_actual_time_minutes=0,
            )
        )
        await db_session.commit()
        return worker.id

    worker_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    yield client, order_id, worker_id, user_id, db_fixture
    _cleanup_overrides()


def test_employee_blueprint_includes_material_hints_no_commercial(material_blueprint_fixture):
    client, order_id, _, _, _ = material_blueprint_fixture
    body = client.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint").json()
    t006 = next(t for t in body["tasks"] if t["task_id"] == "T-006")
    assert t006["readiness_status"] == READINESS_WAITING_PREDECESSOR
    assert t006["material_hints"]
    raw = json.dumps(body).lower()
    for forbidden in ("unit_cost", "price", "margin", "markup", "payroll", "supplier"):
        assert forbidden not in raw


def test_operator_blueprint_includes_material_summary(material_blueprint_fixture):
    client, order_id, _, _, db_fixture = material_blueprint_fixture
    admin = _client_for(db_fixture, _user(f"admin-mat-{uuid.uuid4().hex[:6]}", "admin"))
    response = admin.get(f"/api/v1/operator/orders/{order_id}/production-blueprint")
    assert response.status_code == 200
    body = response.json()
    assert body["material_planning_summary"]["project_critical_count"] >= 1
    t005 = next(t for t in body["tasks"] if t["task_id"] == "T-005")
    assert any(
        item["code"] == "FOREX_BACKING_10MM" for item in t005.get("material_planning_items") or []
    )


def test_no_inventory_deduction_or_reservation_import():
    import services.material_planning_service as mod

    source = open(mod.__file__, encoding="utf-8").read().lower()
    assert "inventory_deduction" not in source
    assert "reservation" not in source
