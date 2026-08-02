"""F5 — Broaden canonical actual-cost coverage beyond single fixture."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select

from models.actual_cost_policy import (
    ActualLaborCostLine,
    ExecutionJobClosure,
    RoleSkillLaborCostPolicy,
)
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.stock_movements import StockMovement
from services.actual_cost_policy_runtime_service import ActualCostPolicyRuntimeService
from services.closed_job_mutation_guard import REASON_EXECUTION_CLOSED_MUTATION_BLOCKED
from services.material_actuals_service import (
    REASON_PLANNED_BOM_REJECTED,
    REASON_RESERVATION_REJECTED,
    MaterialActualsService,
)
from services.profitability_actual_read_model_service import (
    REASON_MACHINE_NOT_APPLICABLE,
    ProfitabilityActualReadModelService,
)
from tests._db_fixture import IsolatedDBFixture

JOB_A = 880051
JOB_B = 880052

_TABLES = [
    ExecutionJobClosure,
    ActualLaborCostLine,
    RoleSkillLaborCostPolicy,
    StockMovement,
    ExecutionReality,
    ExecutionPlan,
    Inventory_materials,
    Employees,
    Orders,
]


async def _clear(session) -> None:
    for table in _TABLES:
        await session.execute(delete(table))
    await session.commit()


@pytest.fixture(scope="module")
def db_fixture():
    import models.actual_cost_policy  # noqa: F401
    import models.employees  # noqa: F401
    import models.execution_plan  # noqa: F401
    import models.execution_reality  # noqa: F401
    import models.inventory_materials  # noqa: F401
    import models.orders  # noqa: F401
    import models.stock_movements  # noqa: F401

    fix = IsolatedDBFixture(prefix="f5_actual_cost_")
    fix.setup()
    yield fix
    fix.teardown()


async def _seed_job(session, order_id: int, *, with_labor: bool = True) -> None:
    now = datetime.now(timezone.utc)
    session.add(
        Orders(
            id=order_id,
            code=f"QA-F5-{order_id}",
            client_name="F5 Client",
            status="in_production",
            snapshot_v2_json=json.dumps(
                {
                    "accepted_commercial_total": 2000.0,
                    "accepted_currency": "RON",
                    "estimated_internal_total": 900.0,
                    "estimated_internal_cost_snapshot": {
                        "estimated_material_cost": 300.0,
                        "estimated_operation_cost": 600.0,
                    },
                }
            ),
        )
    )
    session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"QA-F5-{order_id}",
            snapshot_version=1,
            total_estimated_time_minutes=60.0,
            tasks_json=json.dumps(
                [{"task_id": "CUT", "task_type": "operational", "title": "Cut"}]
            ),
        )
    )
    session.add(
        ExecutionReality(
            order_id=order_id,
            order_code=f"QA-F5-{order_id}",
            tasks_json=json.dumps(
                [
                    {
                        "task_id": "CUT",
                        "session_id": f"sess-{order_id}",
                        "employee_id": 801,
                        "started_at": (now - timedelta(hours=1)).isoformat(),
                        "ended_at": now.isoformat(),
                        "duration_seconds": 3600,
                        "actual_cost_policy_runtime_v1": True,
                    }
                ]
            ),
        )
    )
    if (
        await session.execute(select(Employees).where(Employees.id == 801))
    ).scalar_one_or_none() is None:
        session.add(
            Employees(
                id=801,
                name="F5 Operator",
                role="operator",
                status="active",
                employee_type="productive",
            )
        )
    if with_labor and (
        await session.execute(select(RoleSkillLaborCostPolicy).limit(1))
    ).scalar_one_or_none() is None:
        session.add(
            RoleSkillLaborCostPolicy(
                role_code="operator",
                skill_code=None,
                standard_internal_rate=60.0,
                rate_unit="hour",
                currency="RON",
                effective_from=now - timedelta(days=30),
                effective_to=None,
                active=True,
                provenance="qa_f5",
                reason="f5 coverage",
                created_by="qa",
                version=1,
            )
        )
    await session.flush()
    if with_labor:
        await ActualCostPolicyRuntimeService(session).finalize_labor_lines(order_id)


@pytest.mark.asyncio
async def test_multi_material_partial_and_full_return_scrap_isolation(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        session.add_all(
            [
                Inventory_materials(
                    id=601,
                    code="F5-A",
                    name="Sheet A",
                    unit="buc",
                    stock_current=100,
                    unit_cost=10.0,
                    currency="RON",
                    status="active",
                ),
                Inventory_materials(
                    id=602,
                    code="F5-B",
                    name="Sheet B",
                    unit="buc",
                    stock_current=100,
                    unit_cost=40.0,
                    currency="RON",
                    status="active",
                ),
            ]
        )
        await _seed_job(session, JOB_A)
        await _seed_job(session, JOB_B)
        await session.commit()

        svc = MaterialActualsService(session)
        a1 = await svc.record_issue(
            order_id=JOB_A,
            material_id=601,
            quantity=4.0,
            unit="buc",
            actor_id="mgr",
            idempotency_key="f5-a-issue-1",
        )
        a2 = await svc.record_issue(
            order_id=JOB_A,
            material_id=602,
            quantity=1.0,
            unit="buc",
            actor_id="mgr",
            idempotency_key="f5-a-issue-2",
        )
        assert a1["status"] == "recorded" and a2["status"] == "recorded"
        # Partial consume already recorded; partial return of first material
        issue_a = (
            await session.execute(
                select(StockMovement).where(StockMovement.idempotency_key == "f5-a-issue-1")
            )
        ).scalar_one()
        await svc.record_return(
            order_id=JOB_A,
            reverses_movement_id=issue_a.id,
            quantity=1.0,
            actor_id="mgr",
            idempotency_key="f5-a-ret-partial",
        )
        await svc.record_scrap(
            order_id=JOB_A,
            material_id=601,
            quantity=1.0,
            unit="buc",
            actor_id="mgr",
            idempotency_key="f5-a-scrap",
            scrap_reason="edge waste",
        )
        basis_a = await svc.material_actual_basis(JOB_A)
        # consumption net: (4-1)*10 + 40 + scrap 10 = 30+40+10 = 80
        assert basis_a["available"] is True
        assert basis_a["value"] == 80.0

        # Full return path on job B
        b_issue = await svc.record_issue(
            order_id=JOB_B,
            material_id=601,
            quantity=2.0,
            unit="buc",
            actor_id="mgr",
            idempotency_key="f5-b-issue",
        )
        mov_b = (
            await session.execute(
                select(StockMovement).where(StockMovement.id == b_issue["movement_id"])
            )
        ).scalar_one()
        await svc.record_return(
            order_id=JOB_B,
            reverses_movement_id=mov_b.id,
            quantity=2.0,
            actor_id="mgr",
            idempotency_key="f5-b-ret-full",
        )
        basis_b = await svc.material_actual_basis(JOB_B)
        assert basis_b["available"] is True
        assert basis_b["value"] == 0.0

        # Cross-job isolation
        assert (await svc.material_actual_basis(JOB_A))["value"] == 80.0

        # Catalog change after freeze does not rewrite A history
        mat = (
            await session.execute(select(Inventory_materials).where(Inventory_materials.id == 602))
        ).scalar_one()
        mat.unit_cost = 999.0
        await session.commit()
        assert (await svc.material_actual_basis(JOB_A))["value"] == 80.0

        # Idempotent re-read
        again = await svc.material_actual_basis(JOB_A)
        assert again["value"] == 80.0


@pytest.mark.asyncio
async def test_closed_job_blocks_mutations_until_reopen(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        session.add(
            Inventory_materials(
                id=601,
                code="F5-A",
                name="Sheet A",
                unit="buc",
                stock_current=100,
                unit_cost=10.0,
                currency="RON",
                status="active",
            )
        )
        await _seed_job(session, JOB_A)
        await session.commit()
        svc = MaterialActualsService(session)
        await svc.record_issue(
            order_id=JOB_A,
            material_id=601,
            quantity=2.0,
            unit="buc",
            actor_id="mgr",
            idempotency_key="f5-close-issue",
        )
        runtime = ActualCostPolicyRuntimeService(session)
        assert (await runtime.closure_readiness(JOB_A))["ready"] is True
        await runtime.close_job(JOB_A, "mgr", {"authorized": True})
        await session.commit()

        model = await ProfitabilityActualReadModelService(session).build(JOB_A)
        assert model["profitability_result"]["actual_margin"]["amount"]["available"] is True
        cats = model["actual_cost_truth"]["cost_category_applicability"]
        assert cats["machine"]["status"] == "not_applicable"
        assert cats["machine"]["reason"] == REASON_MACHINE_NOT_APPLICABLE
        assert cats["other_direct"]["status"] == "not_applicable"
        assert cats["execution"]["final_margin_available"] is True

        with pytest.raises(HTTPException) as blocked_issue:
            await svc.record_issue(
                order_id=JOB_A,
                material_id=601,
                quantity=1.0,
                unit="buc",
                actor_id="mgr",
                idempotency_key="f5-closed-issue",
            )
        assert blocked_issue.value.status_code == 409
        assert blocked_issue.value.detail["error"] == REASON_EXECUTION_CLOSED_MUTATION_BLOCKED

        issue = (
            await session.execute(
                select(StockMovement).where(StockMovement.idempotency_key == "f5-close-issue")
            )
        ).scalar_one()
        with pytest.raises(HTTPException) as blocked_return:
            await svc.record_return(
                order_id=JOB_A,
                reverses_movement_id=issue.id,
                quantity=1.0,
                actor_id="mgr",
                idempotency_key="f5-closed-return",
            )
        assert blocked_return.value.detail["error"] == REASON_EXECUTION_CLOSED_MUTATION_BLOCKED

        with pytest.raises(HTTPException) as blocked_scrap:
            await svc.record_scrap(
                order_id=JOB_A,
                material_id=601,
                quantity=1.0,
                unit="buc",
                actor_id="mgr",
                idempotency_key="f5-closed-scrap",
                scrap_reason="late scrap",
            )
        assert blocked_scrap.value.detail["error"] == REASON_EXECUTION_CLOSED_MUTATION_BLOCKED

        await runtime.reopen_job(JOB_A, "mgr", "correct material after inspection")
        model_open = await ProfitabilityActualReadModelService(session).build(JOB_A)
        assert model_open["profitability_result"]["actual_margin"]["amount"]["available"] is False
        assert model_open["actual_cost_truth"]["execution_closure_status"] == "reopened"

        allowed = await svc.record_scrap(
            order_id=JOB_A,
            material_id=601,
            quantity=1.0,
            unit="buc",
            actor_id="mgr",
            idempotency_key="f5-after-reopen-scrap",
            scrap_reason="post-reopen scrap",
        )
        assert allowed["status"] == "recorded"
        await runtime.close_job(JOB_A, "mgr", {"authorized": True})
        model_reclose = await ProfitabilityActualReadModelService(session).build(JOB_A)
        assert model_reclose["profitability_result"]["actual_margin"]["amount"]["available"] is True

        order = (await session.execute(select(Orders).where(Orders.id == JOB_A))).scalar_one()
        assert json.loads(order.snapshot_v2_json)["accepted_commercial_total"] == 2000.0


@pytest.mark.asyncio
async def test_rejects_bom_reservation_and_unclassified_other_cost_contract(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        session.add(
            Inventory_materials(
                id=601,
                code="F5-A",
                name="Sheet A",
                unit="buc",
                stock_current=10,
                unit_cost=5.0,
                currency="RON",
                status="active",
            )
        )
        await session.commit()
        svc = MaterialActualsService(session)
        with pytest.raises(HTTPException) as bom:
            await svc.record_issue(
                order_id=1,
                material_id=601,
                quantity=1,
                unit="buc",
                actor_id="a",
                idempotency_key="f5-bom",
                source_type="planned_bom",
            )
        assert bom.value.detail["error"] == REASON_PLANNED_BOM_REJECTED
        with pytest.raises(HTTPException) as res:
            await svc.record_issue(
                order_id=1,
                material_id=601,
                quantity=1,
                unit="buc",
                actor_id="a",
                idempotency_key="f5-res",
                source_type="reservation",
            )
        assert res.value.detail["error"] == REASON_RESERVATION_REJECTED

        # Machine/other contracts: no WC-rate invention on empty tasks
        cats = ProfitabilityActualReadModelService._machine_cost_category([])
        assert cats["applicability"] == "not_applicable"
        declared = ProfitabilityActualReadModelService._machine_cost_category(
            [{"task_id": "X", "machine_id": 12}]
        )
        assert declared["applicability"] == "applicable_optional"
        assert declared["status"] == "unavailable"
        assert declared["available"] is False
        assert declared["value"] is None
