"""Labor Cost Rate Snapshot Authority — historical-safe freeze proofs.

Isolated DB only. Never mutates QA fixture 880750.
No payroll, no commercial pricing, no MachineRun labor cost.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text

from models.actual_cost_policy import ActualLaborCostLine, RoleSkillLaborCostPolicy
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from services.actual_cost_policy_runtime_service import ActualCostPolicyRuntimeService
from services.controlled_task_session_service import (
    end_controlled_task_session,
    start_controlled_task_session,
)
from services.profitability_actual_labor_input_service import (
    build_profitability_actual_labor_input,
)


TASK = "t_rate_snap"
QA_ORDER_ID = 880750


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    yield
    monkeypatch.delenv("WORKOS_PHASE_B_RESOURCE_GUARDS", raising=False)


def _envelope(ops: list[dict]) -> str:
    return json.dumps(
        {
            "source": "order_snapshot_v2",
            "planned_tasks": [
                {"task_key": o["task_id"], "canonical_task_type": "led_assembly"} for o in ops
            ],
            "execution_tasks_created": True,
            "operational_tasks": ops,
            "dependency_edges": [],
        }
    )


async def _seed_order(db, order_id: int) -> None:
    db.add(
        Orders(
            id=order_id,
            code=f"ORD-RATE-{order_id}",
            client_name="Rate Snapshot",
            status="in_production",
        )
    )
    await db.commit()


async def _seed_emp(db, *, name: str, role: str) -> Employees:
    emp = Employees(
        name=name, role=role, status="active", employee_type="productive"
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    return emp


async def _seed_plan(db, *, order_id: int, ops: list[dict]) -> ExecutionPlan:
    row = ExecutionPlan(
        order_id=order_id,
        order_code=f"ORD-RATE-{order_id}",
        snapshot_version=1,
        tasks_json=_envelope(ops),
        total_estimated_time_minutes=60,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def _add_policy(
    db,
    *,
    role_code: str,
    rate: float,
    effective_from: datetime,
    effective_to: datetime | None = None,
    skill_code: str | None = None,
    currency: str = "RON",
) -> RoleSkillLaborCostPolicy:
    row = RoleSkillLaborCostPolicy(
        role_code=role_code,
        skill_code=skill_code,
        standard_internal_rate=rate,
        rate_unit="hour",
        currency=currency,
        effective_from=effective_from,
        effective_to=effective_to,
        active=True,
        provenance="test_rate_snapshot",
        reason="controlled scenario",
        created_by="test",
        version=1,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def _closed_session(
    db,
    *,
    order_id: int,
    employee_id: int,
    start: datetime,
    minutes: int,
    task_id: str = TASK,
) -> dict:
    await start_controlled_task_session(
        db,
        order_id=order_id,
        task_id=task_id,
        employee_id=employee_id,
        actor_mode="supervisor",
        clock=lambda: start,
    )
    end = await end_controlled_task_session(
        db,
        order_id=order_id,
        task_id=task_id,
        employee_id=employee_id,
        actor_mode="supervisor",
        clock=lambda: start + timedelta(minutes=minutes),
    )
    await db.commit()
    return end


async def _lines(db, order_id: int) -> list[ActualLaborCostLine]:
    return list(
        (
            await db.execute(
                select(ActualLaborCostLine).where(ActualLaborCostLine.order_id == order_id)
            )
        )
        .scalars()
        .all()
    )


@pytest.mark.asyncio
async def test_01_single_session_stable_rate(db_session):
    order_id = 924101
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session, role_code="operator", rate=60.0, effective_from=t0 - timedelta(days=10)
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=t0, minutes=60
    )
    out = await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    assert out["created"] == 1
    lines = await _lines(db_session, order_id)
    assert len(lines) == 1
    assert lines[0].rate_used == 60.0
    assert lines[0].currency == "RON"
    assert lines[0].duration_seconds == 3600
    assert lines[0].labor_cost_amount == 60.0  # 3600 * 60 / 3600
    assert lines[0].role_code == "operator"
    assert lines[0].freeze_status == "frozen"


@pytest.mark.asyncio
async def test_02_multi_session_same_employee_sums(db_session):
    order_id = 924102
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 1, 9, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session, role_code="operator", rate=60.0, effective_from=t0 - timedelta(days=1)
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=t0, minutes=30
    )
    await _closed_session(
        db_session,
        order_id=order_id,
        employee_id=emp.id,
        start=t0 + timedelta(hours=2),
        minutes=30,
    )
    await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    lines = await _lines(db_session, order_id)
    assert len(lines) == 2
    total = round(sum(float(l.labor_cost_amount) for l in lines), 4)
    assert total == 60.0  # two half-hours at 60/h


@pytest.mark.asyncio
async def test_03_multi_employee_sums(db_session):
    order_id = 924103
    await _seed_order(db_session, order_id)
    a = await _seed_emp(db_session, name="A", role="operator")
    b = await _seed_emp(db_session, name="B", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK, "assigned_employee_id": a.id}],
    )
    t0 = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session, role_code="operator", rate=60.0, effective_from=t0 - timedelta(days=1)
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=a.id, start=t0, minutes=60
    )
    # Pointer swap (not Phase E) to author second employee closed session.
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    data = json.loads(plan.tasks_json)
    data["operational_tasks"][0]["assigned_employee_id"] = b.id
    plan.tasks_json = json.dumps(data)
    await db_session.commit()
    await _closed_session(
        db_session,
        order_id=order_id,
        employee_id=b.id,
        start=t0 + timedelta(hours=2),
        minutes=60,
    )
    await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    lines = await _lines(db_session, order_id)
    assert len(lines) == 2
    assert {l.employee_id for l in lines} == {a.id, b.id}
    assert round(sum(float(l.labor_cost_amount) for l in lines), 4) == 120.0


@pytest.mark.asyncio
async def test_04_and_11_12_rate_change_after_freeze_no_reprice(db_session):
    order_id = 924104
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 1, 11, 0, 0, tzinfo=timezone.utc)
    p1 = await _add_policy(
        db_session,
        role_code="operator",
        rate=60.0,
        effective_from=t0 - timedelta(days=5),
        effective_to=t0 + timedelta(days=1),
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=t0, minutes=60
    )
    await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    before = (await _lines(db_session, order_id))[0]
    assert before.rate_used == 60.0
    amount_before = before.labor_cost_amount
    policy_id_before = before.policy_id

    # New rate for future work + mutate old policy row (hostile edit).
    await _add_policy(
        db_session,
        role_code="operator",
        rate=999.0,
        effective_from=t0 + timedelta(days=2),
    )
    p1 = (
        await db_session.execute(
            select(RoleSkillLaborCostPolicy).where(RoleSkillLaborCostPolicy.id == p1.id)
        )
    ).scalar_one()
    p1.standard_internal_rate = 1.0
    await db_session.commit()

    # Re-finalize must not rewrite frozen line.
    out = await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    assert out["created"] == 0
    assert out["existing"] == 1
    after = (await _lines(db_session, order_id))[0]
    assert after.rate_used == 60.0
    assert after.labor_cost_amount == amount_before
    assert after.policy_id == policy_id_before


@pytest.mark.asyncio
async def test_05_role_change_after_work_does_not_reprice(db_session):
    order_id = 924105
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session, role_code="operator", rate=60.0, effective_from=t0 - timedelta(days=1)
    )
    await _add_policy(
        db_session, role_code="senior", rate=120.0, effective_from=t0 - timedelta(days=1)
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=t0, minutes=60
    )
    # Role change BEFORE finalize — work-time role_code on session must win.
    emp.role = "senior"
    await db_session.commit()
    await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    line = (await _lines(db_session, order_id))[0]
    assert line.role_code == "operator"
    assert line.rate_used == 60.0
    assert line.labor_cost_amount == 60.0


@pytest.mark.asyncio
async def test_06_skill_snapshot_not_repriced_by_plan_change(db_session):
    order_id = 924106
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[
            {
                "task_id": TASK,
                "assigned_employee_id": emp.id,
                "skill_code": "led_basic",
            }
        ],
    )
    t0 = datetime(2026, 8, 1, 13, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session,
        role_code="operator",
        skill_code="led_basic",
        rate=50.0,
        effective_from=t0 - timedelta(days=1),
    )
    await _add_policy(
        db_session,
        role_code="operator",
        skill_code="led_advanced",
        rate=200.0,
        effective_from=t0 - timedelta(days=1),
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=t0, minutes=60
    )
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    data = json.loads(plan.tasks_json)
    data["operational_tasks"][0]["skill_code"] = "led_advanced"
    plan.tasks_json = json.dumps(data)
    await db_session.commit()

    await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    line = (await _lines(db_session, order_id))[0]
    assert line.skill_code == "led_basic"
    assert line.rate_used == 50.0


@pytest.mark.asyncio
async def test_07_rate_change_between_sessions(db_session):
    order_id = 924107
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK, "assigned_employee_id": emp.id}],
    )
    boundary = datetime(2026, 8, 2, 0, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session,
        role_code="operator",
        rate=60.0,
        effective_from=boundary - timedelta(days=10),
        effective_to=boundary,
    )
    await _add_policy(
        db_session,
        role_code="operator",
        rate=90.0,
        effective_from=boundary,
    )
    s1 = boundary - timedelta(hours=3)
    s2 = boundary + timedelta(hours=3)
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=s1, minutes=60
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=s2, minutes=60
    )
    await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    lines = await _lines(db_session, order_id)
    assert len(lines) == 2
    rates = sorted(float(l.rate_used) for l in lines)
    assert rates == [60.0, 90.0]
    amounts = sorted(float(l.labor_cost_amount) for l in lines)
    assert amounts == [60.0, 90.0]


@pytest.mark.asyncio
async def test_08_inactive_employee_history_stable(db_session):
    order_id = 924108
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 1, 14, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session, role_code="operator", rate=60.0, effective_from=t0 - timedelta(days=1)
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=t0, minutes=60
    )
    emp.status = "inactive"
    emp.role = "senior"  # also change role after work
    await db_session.commit()
    await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    line = (await _lines(db_session, order_id))[0]
    assert line.employee_id == emp.id
    assert line.role_code == "operator"
    assert line.rate_used == 60.0


@pytest.mark.asyncio
async def test_09_10_restart_and_repeat_finalize_deterministic(db_session):
    order_id = 924109
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 1, 15, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session, role_code="operator", rate=72.0, effective_from=t0 - timedelta(days=1)
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=t0, minutes=30
    )
    svc = ActualCostPolicyRuntimeService(db_session)
    await svc.finalize_labor_lines(order_id)
    await db_session.commit()
    first = (await _lines(db_session, order_id))[0]
    await svc.finalize_labor_lines(order_id)
    await db_session.commit()
    second = (await _lines(db_session, order_id))[0]
    assert first.id == second.id
    assert first.labor_cost_amount == second.labor_cost_amount == 36.0
    assert first.rate_used == second.rate_used == 72.0


@pytest.mark.asyncio
async def test_13_machine_run_not_in_labor_cost(db_session):
    order_id = 924113
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[
            {
                "task_id": TASK,
                "assigned_employee_id": emp.id,
                "machine_id": "M-1",
            }
        ],
    )
    t0 = datetime(2026, 8, 1, 16, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session, role_code="operator", rate=60.0, effective_from=t0 - timedelta(days=1)
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=t0, minutes=60
    )
    await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    lines = await _lines(db_session, order_id)
    assert len(lines) == 1
    assert lines[0].labor_cost_amount == 60.0  # employee hour only


@pytest.mark.asyncio
async def test_14_15_16_boundaries_payroll_commercial_labor_input(db_session):
    order_id = 924114
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    emp.cost_lunar_firma = 99999.0
    emp.monthly_internal_pay_amount = 88888.0
    await db_session.commit()
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[
            {
                "task_id": TASK,
                "assigned_employee_id": emp.id,
                "estimated_time_minutes": 999,
            }
        ],
    )
    t0 = datetime(2026, 8, 1, 17, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session, role_code="operator", rate=60.0, effective_from=t0 - timedelta(days=1)
    )
    end = await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=t0, minutes=60
    )
    assert end["commercial_mutated"] is False
    labor_in = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor_in["totals"]["total_employee_minutes"] == 60
    assert labor_in["monetary_rates_included"] is False

    await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    await db_session.commit()
    line = (await _lines(db_session, order_id))[0]
    assert line.labor_cost_amount == 60.0  # not from salary fields
    # Planned minutes untouched
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    assert json.loads(plan.tasks_json)["operational_tasks"][0]["estimated_time_minutes"] == 999
    # Session timestamps unchanged
    reality = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one()
    sess = json.loads(reality.tasks_json)[0]
    assert sess["started_at"]
    assert sess["ended_at"]
    assert sess["role_code"] == "operator"
    assert emp.cost_lunar_firma == 99999.0
    assert emp.monthly_internal_pay_amount == 88888.0


@pytest.mark.asyncio
async def test_20_qa_untouched(db_session):
    before = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM orders WHERE id = :oid"), {"oid": QA_ORDER_ID}
        )
    ).scalar()
    order_id = 924120
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="operator")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 1, 18, 0, 0, tzinfo=timezone.utc)
    await _add_policy(
        db_session, role_code="operator", rate=60.0, effective_from=t0 - timedelta(days=1)
    )
    await _closed_session(
        db_session, order_id=order_id, employee_id=emp.id, start=t0, minutes=10
    )
    await ActualCostPolicyRuntimeService(db_session).finalize_labor_lines(order_id)
    after = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM orders WHERE id = :oid"), {"oid": QA_ORDER_ID}
        )
    ).scalar()
    assert before == after


@pytest.mark.asyncio
async def test_session_start_snapshots_role_code(db_session):
    order_id = 924121
    await _seed_order(db_session, order_id)
    emp = await _seed_emp(db_session, name="A", role="assembler")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK, "assigned_employee_id": emp.id, "skill_code": "s1"}],
    )
    t0 = datetime(2026, 8, 1, 19, 0, 0, tzinfo=timezone.utc)
    await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0,
    )
    await db_session.commit()
    reality = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one()
    sess = json.loads(reality.tasks_json)[0]
    assert sess["role_code"] == "assembler"
    assert sess["skill_code"] == "s1"
    assert sess["actual_cost_policy_runtime_v1"] is True
