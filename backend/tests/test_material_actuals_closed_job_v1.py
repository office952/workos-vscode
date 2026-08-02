"""F4 — Canonical material actuals + closed-job profitability proof."""

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
from services.material_actuals_service import (
    REASON_PLANNED_BOM_REJECTED,
    REASON_RESERVATION_REJECTED,
    REASON_UNRELATED_RETURN,
    MaterialActualsService,
)
from services.profitability_actual_read_model_service import ProfitabilityActualReadModelService
from tests._db_fixture import IsolatedDBFixture

ORDER_ID = 880041  # QA-only controlled complete fixture (never 973019)

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

    fix = IsolatedDBFixture(prefix="f4_material_actuals_")
    fix.setup()
    yield fix
    fix.teardown()


async def _seed_complete_job(session, *, with_material: bool = True, with_labor: bool = True):
    now = datetime.now(timezone.utc)
    session.add(
        Orders(
            id=ORDER_ID,
            code=f"QA-F4-{ORDER_ID}",
            client_name="F4 Controlled Client",
            status="in_production",
            snapshot_v2_json=json.dumps(
                {
                    "accepted_commercial_total": 1000.0,
                    "accepted_currency": "RON",
                    "estimated_internal_total": 600.0,
                    "estimated_internal_cost_snapshot": {
                        "estimated_material_cost": 200.0,
                        "estimated_operation_cost": 400.0,
                    },
                }
            ),
        )
    )
    session.add(
        ExecutionPlan(
            order_id=ORDER_ID,
            order_code=f"QA-F4-{ORDER_ID}",
            snapshot_version=1,
            total_estimated_time_minutes=60.0,
            tasks_json=json.dumps(
                [{"task_id": "LED", "task_type": "operational", "title": "LED"}]
            ),
        )
    )
    session.add(
        ExecutionReality(
            order_id=ORDER_ID,
            order_code=f"QA-F4-{ORDER_ID}",
            tasks_json=json.dumps(
                [
                    {
                        "task_id": "LED",
                        "session_id": "sess-f4-1",
                        "employee_id": 701,
                        "started_at": (now - timedelta(hours=1)).isoformat(),
                        "ended_at": now.isoformat(),
                        "duration_seconds": 3600,
                        "actual_cost_policy_runtime_v1": True,
                    }
                ]
            ),
        )
    )
    session.add(
        Employees(
            id=701,
            name="F4 Fixture Operator",
            role="operator",
            status="active",
            employee_type="productive",
        )
    )
    session.add(
        Inventory_materials(
            id=501,
            code="F4-MAT-001",
            name="F4 Acrylic Sheet",
            unit="buc",
            stock_current=100.0,
            unit_cost=25.0,
            currency="RON",
            status="active",
        )
    )
    if with_labor:
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
                provenance="qa_f4_fixture",
                reason="controlled complete fixture",
                created_by="qa",
                version=1,
            )
        )
    await session.flush()
    if with_material:
        await MaterialActualsService(session).record_issue(
            order_id=ORDER_ID,
            material_id=501,
            quantity=2.0,
            unit="buc",
            actor_id="qa-manager",
            idempotency_key=f"f4-issue-{ORDER_ID}",
            task_id="LED",
        )
    if with_labor:
        await ActualCostPolicyRuntimeService(session).finalize_labor_lines(ORDER_ID)
    await session.commit()


@pytest.mark.asyncio
async def test_planned_bom_and_reservation_rejected(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        session.add(
            Inventory_materials(
                id=501, code="X", name="X", unit="buc", stock_current=10, unit_cost=1, currency="RON"
            )
        )
        await session.commit()
        svc = MaterialActualsService(session)
        with pytest.raises(HTTPException) as bom:
            await svc.record_issue(
                order_id=1,
                material_id=501,
                quantity=1,
                unit="buc",
                actor_id="a",
                idempotency_key="bom-1",
                source_type="planned_bom",
            )
        assert bom.value.detail["error"] == REASON_PLANNED_BOM_REJECTED
        with pytest.raises(HTTPException) as res:
            await svc.record_issue(
                order_id=1,
                material_id=501,
                quantity=1,
                unit="buc",
                actor_id="a",
                idempotency_key="res-1",
                source_type="reservation",
            )
        assert res.value.detail["error"] == REASON_RESERVATION_REJECTED


@pytest.mark.asyncio
async def test_issue_freeze_idempotency_return_scrap_and_close(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_complete_job(session)

        mat = (
            await session.execute(select(Inventory_materials).where(Inventory_materials.id == 501))
        ).scalar_one()
        assert float(mat.stock_current) == 98.0
        mat.unit_cost = 999.0  # catalog change must not rewrite frozen movement
        await session.commit()

        basis = await MaterialActualsService(session).material_actual_basis(ORDER_ID)
        assert basis["available"] is True
        assert basis["value"] == 50.0  # 2 * 25 frozen

        again = await MaterialActualsService(session).record_issue(
            order_id=ORDER_ID,
            material_id=501,
            quantity=2.0,
            unit="buc",
            actor_id="qa-manager",
            idempotency_key=f"f4-issue-{ORDER_ID}",
        )
        assert again["status"] == "material_actual_idempotent_replay"

        issue = (
            await session.execute(
                select(StockMovement).where(StockMovement.idempotency_key == f"f4-issue-{ORDER_ID}")
            )
        ).scalar_one()
        ret = await MaterialActualsService(session).record_return(
            order_id=ORDER_ID,
            reverses_movement_id=issue.id,
            quantity=1.0,
            actor_id="qa-manager",
            idempotency_key="f4-return-1",
        )
        assert ret["status"] == "recorded"
        basis2 = await MaterialActualsService(session).material_actual_basis(ORDER_ID)
        assert basis2["value"] == 25.0

        with pytest.raises(HTTPException) as unrelated:
            await MaterialActualsService(session).record_return(
                order_id=ORDER_ID,
                reverses_movement_id=999999,
                quantity=1.0,
                actor_id="qa-manager",
                idempotency_key="f4-return-bad",
            )
        assert unrelated.value.detail["error"] == REASON_UNRELATED_RETURN

        scrap = await MaterialActualsService(session).record_scrap(
            order_id=ORDER_ID,
            material_id=501,
            quantity=1.0,
            unit="buc",
            actor_id="qa-manager",
            idempotency_key="f4-scrap-1",
            scrap_reason="edge waste",
        )
        assert scrap["distinct_from_consumption"] is True
        basis3 = await MaterialActualsService(session).material_actual_basis(ORDER_ID)
        # Remaining issue 25 (frozen) + scrap frozen at post-catalog 999.
        assert basis3["value"] == 25.0 + 999.0

        runtime = ActualCostPolicyRuntimeService(session)
        ready = await runtime.closure_readiness(ORDER_ID)
        assert ready["ready"] is True
        closed = await runtime.close_job(ORDER_ID, "qa-manager", {"authorized": True})
        assert closed.status == "closed"
        closed2 = await runtime.close_job(ORDER_ID, "qa-manager", {"authorized": True})
        assert closed2.status == "closed"

        model = await ProfitabilityActualReadModelService(session).build(ORDER_ID)
        assert model["actual_cost_truth"]["actual_cost_status"] == "closed_job_operational_actual"
        assert model["profitability_result"]["actual_margin"]["amount"]["available"] is True
        assert model["profitability_result"]["actual_margin"]["provisional"] is False

        await runtime.reopen_job(ORDER_ID, "qa-manager", "rework material scrap")
        model2 = await ProfitabilityActualReadModelService(session).build(ORDER_ID)
        assert model2["profitability_result"]["actual_margin"]["amount"]["available"] is False
        assert model2["actual_cost_truth"]["execution_closure_status"] == "reopened"

        # Reclose after readiness
        closed3 = await runtime.close_job(ORDER_ID, "qa-manager", {"authorized": True})
        assert closed3.status == "closed"
        model3 = await ProfitabilityActualReadModelService(session).build(ORDER_ID)
        assert model3["profitability_result"]["actual_margin"]["amount"]["available"] is True

        # Commercial snapshot unchanged
        order = (await session.execute(select(Orders).where(Orders.id == ORDER_ID))).scalar_one()
        snap = json.loads(order.snapshot_v2_json)
        assert snap["accepted_commercial_total"] == 1000.0


@pytest.mark.asyncio
async def test_close_rejected_without_material_or_labor(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_complete_job(session, with_material=False, with_labor=True)
        runtime = ActualCostPolicyRuntimeService(session)
        ready = await runtime.closure_readiness(ORDER_ID)
        assert ready["ready"] is False
        assert ready["reason"] == "actual_material_cost_missing"

        await _clear(session)
        await _seed_complete_job(session, with_material=True, with_labor=False)
        # labor finalize skipped — no lines
        ready2 = await runtime.closure_readiness(ORDER_ID)
        assert ready2["ready"] is False
        assert ready2["reason"] == "actual_labor_cost_incomplete"


@pytest.mark.asyncio
async def test_unit_mismatch_and_missing_valuation(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        session.add(
            Inventory_materials(
                id=502,
                code="NOVAL",
                name="No valuation",
                unit="m",
                stock_current=10,
                unit_cost=None,
                currency=None,
            )
        )
        await session.commit()
        with pytest.raises(HTTPException) as unit_err:
            await MaterialActualsService(session).record_issue(
                order_id=1,
                material_id=502,
                quantity=1,
                unit="buc",
                actor_id="a",
                idempotency_key="unit-mismatch",
            )
        assert unit_err.value.detail["error"] == "material_unit_mismatch"

        session.add(
            Inventory_materials(
                id=503,
                code="NOVAL2",
                name="No valuation 2",
                unit="buc",
                stock_current=10,
                unit_cost=None,
                currency="RON",
            )
        )
        await session.commit()
        out = await MaterialActualsService(session).record_issue(
            order_id=2,
            material_id=503,
            quantity=1,
            unit="buc",
            actor_id="a",
            idempotency_key="missing-val",
        )
        assert out["material_cost_status"] == "incomplete"
        basis = await MaterialActualsService(session).material_actual_basis(2)
        assert basis["available"] is False
        assert basis["reason"] == "material_valuation_unavailable"
