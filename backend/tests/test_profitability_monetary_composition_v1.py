"""Profitability Monetary Composition V1 — revenue − labor − material; machine/other N/A."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
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
from services.material_actuals_service import MaterialActualsService
from services.profitability_actual_read_model_service import (
    REASON_CURRENCY_MISMATCH_NO_FX,
    REASON_MACHINE_NA_FOR_V1,
    REASON_OTHER_DIRECT_NA_FOR_V1,
    ProfitabilityActualReadModelService,
)
from tests._db_fixture import IsolatedDBFixture

ORDER_ID = 880071

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

    fix = IsolatedDBFixture(prefix="v1_profit_mon_")
    fix.setup()
    yield fix
    fix.teardown()


async def _seed_job(
    session,
    *,
    order_id: int = ORDER_ID,
    revenue_currency: str = "RON",
    labor_currency: str = "RON",
    material_currency: str = "RON",
    revenue: float = 1000.0,
    close: bool = True,
) -> None:
    now = datetime.now(timezone.utc)
    session.add(
        Orders(
            id=order_id,
            code=f"QA-PM-{order_id}",
            client_name="Monetary V1",
            status="in_production",
            snapshot_v2_json=json.dumps(
                {
                    "accepted_commercial_total": revenue,
                    "accepted_currency": revenue_currency,
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
            order_id=order_id,
            order_code=f"QA-PM-{order_id}",
            snapshot_version=1,
            total_estimated_time_minutes=60.0,
            tasks_json=json.dumps(
                [{"task_id": "FACE", "task_type": "operational", "machine_id": 1}]
            ),
        )
    )
    session.add(
        Employees(id=901, name="Worker", status="active", employee_type="productive", role="operator")
    )
    session.add(
        RoleSkillLaborCostPolicy(
            role_code="operator",
            skill_code=None,
            standard_internal_rate=60.0,
            rate_unit="hour",
            currency=labor_currency,
            effective_from=now - timedelta(days=30),
            effective_to=None,
            active=True,
            provenance="qa_monetary_v1",
            reason="controlled monetary composition fixture",
            created_by="qa",
            version=1,
        )
    )
    session.add(
        Inventory_materials(
            id=801,
            code="PLEXI",
            name="Plexi",
            unit="buc",
            stock_current=50.0,
            unit_cost=25.0,
            currency=material_currency,
            status="active",
        )
    )
    session.add(
        ExecutionReality(
            order_id=order_id,
            order_code=f"QA-PM-{order_id}",
            tasks_json=json.dumps(
                [
                    {
                        "task_id": "FACE",
                        "session_id": "s1",
                        "employee_id": 901,
                        "started_at": (now - timedelta(hours=1)).isoformat(),
                        "ended_at": now.isoformat(),
                        "duration_seconds": 3600,
                        "status": "ended",
                        "role_code": "operator",
                        "actual_cost_policy_runtime_v1": True,
                    }
                ]
            ),
        )
    )
    await session.commit()

    await MaterialActualsService(session).record_issue(
        order_id=order_id,
        material_id=801,
        quantity=2.0,
        unit="buc",
        actor_id="qa",
        idempotency_key=f"pm-issue-{order_id}",
        task_id="FACE",
    )
    await session.commit()

    runtime = ActualCostPolicyRuntimeService(session)
    await runtime.finalize_labor_lines(order_id)
    await session.commit()
    if close:
        await runtime.close_job(order_id, "qa", {"authorized": True})
        await session.commit()


@pytest.mark.asyncio
async def test_positive_contribution_same_currency(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_job(session, revenue=1000.0)
        model = await ProfitabilityActualReadModelService(session).build(ORDER_ID)
        mv = model["monetary_v1"]
        assert mv["scope_status"] == "COMPLETE_FOR_V1_SCOPE"
        assert mv["machine"]["status"] == "N_A_FOR_V1"
        assert mv["other_direct"]["status"] == "N_A_FOR_V1"
        assert mv["na_represented_as_zero"] is False
        assert mv["fx_required"] is False
        # labor 60 RON/h * 1h = 60; material 50
        assert mv["known_actual_cost"]["available"] is True
        assert mv["known_actual_cost"]["value"] == pytest.approx(110.0)
        assert mv["known_contribution"]["available"] is True
        assert mv["known_contribution"]["value"] == pytest.approx(890.0)
        assert model["profitability_result"]["completeness"] == "complete_for_v1_scope"


@pytest.mark.asyncio
async def test_negative_contribution(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_job(session, order_id=880072, revenue=50.0)
        model = await ProfitabilityActualReadModelService(session).build(880072)
        assert model["monetary_v1"]["known_contribution"]["value"] == pytest.approx(-60.0)


@pytest.mark.asyncio
async def test_eur_revenue_ron_costs_fail_closed(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_job(
            session,
            order_id=880073,
            revenue_currency="EUR",
            labor_currency="RON",
            material_currency="RON",
            revenue=1000.0,
        )
        model = await ProfitabilityActualReadModelService(session).build(880073)
        mv = model["monetary_v1"]
        assert mv["scope_status"] == "BLOCKED_CURRENCY"
        assert mv["fx_required"] is True
        assert mv["known_contribution"]["available"] is False
        assert mv["known_contribution"]["reason"] == REASON_CURRENCY_MISMATCH_NO_FX
        # Cost total still available in RON (labor+material same currency)
        assert mv["known_actual_cost"]["available"] is True
        assert model["actual_cost_truth"]["machine_actual_cost"]["reason"] == REASON_MACHINE_NA_FOR_V1
        assert model["actual_cost_truth"]["other_actual_cost"]["reason"] == REASON_OTHER_DIRECT_NA_FOR_V1


@pytest.mark.asyncio
async def test_historical_stability_after_live_rate_changes(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_job(session, order_id=880074)
        before = await ProfitabilityActualReadModelService(session).build(880074)
        p0 = before["monetary_v1"]["known_contribution"]["value"]

        mat = (
            await session.execute(select(Inventory_materials).where(Inventory_materials.id == 801))
        ).scalar_one()
        mat.unit_cost = 999.0
        policy = (
            await session.execute(select(RoleSkillLaborCostPolicy))
        ).scalars().first()
        policy.standard_internal_rate = 999.0
        await session.commit()

        after = await ProfitabilityActualReadModelService(session).build(880074)
        assert after["monetary_v1"]["known_contribution"]["value"] == p0
        assert after["monetary_v1"]["materials"]["amount"] == before["monetary_v1"]["materials"]["amount"]


@pytest.mark.asyncio
async def test_na_not_zero_and_machine_run_declared(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_job(session, order_id=880075)
        model = await ProfitabilityActualReadModelService(session).build(880075)
        assert model["monetary_v1"]["machine"]["value"] is None
        assert model["monetary_v1"]["machine"]["represented_as_zero"] is False
        assert model["monetary_v1"]["other_direct"]["represented_as_zero"] is False
        assert model["actual_cost_truth"]["cost_category_applicability"]["machine"][
            "operational_machine_declared"
        ] is True


@pytest.mark.asyncio
async def test_open_job_not_final(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_job(session, order_id=880076, close=False)
        model = await ProfitabilityActualReadModelService(session).build(880076)
        assert model["monetary_v1"]["scope_status"] == "INCOMPLETE_INPUTS"
        assert model["monetary_v1"]["known_contribution"]["available"] is False
