"""F6 — Controlled multi-type actual-cost pilot (isolated service families).

Proves operationally distinct families without inventing ProductDefinition truth:
  F6-LED   — buc LED modules + PSU, electrical task
  F6-ACM   — mp ACM sheet + buc fasteners, cut/v-groove tasks
  F6-PROFILE — ml profile + adhesive, forming/bonding tasks

Product-linked end-to-end families remain PILOT_COVERAGE_BLOCKED until
Owner-authorized materialization of frozen product orders.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

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
from services.material_actuals_service import MaterialActualsService
from services.profitability_actual_read_model_service import (
    REASON_MACHINE_ACTUAL_NOT_CAPTURED,
    REASON_MACHINE_NOT_APPLICABLE,
    ProfitabilityActualReadModelService,
)
from tests._db_fixture import IsolatedDBFixture

FAMILIES: dict[str, dict[str, Any]] = {
    "F6-LED": {
        "order_id": 880061,
        "tasks": [{"task_id": "LED_WIRE", "task_type": "operational", "title": "LED wiring"}],
        "materials": [
            {"id": 701, "code": "F6-LED-MOD", "unit": "buc", "unit_cost": 12.0, "qty": 4.0},
            {"id": 702, "code": "F6-PSU", "unit": "buc", "unit_cost": 80.0, "qty": 1.0},
        ],
        "machine_on_task": False,
        "expected_material": 4 * 12.0 + 80.0,
    },
    "F6-ACM": {
        "order_id": 880062,
        "tasks": [
            {"task_id": "CUT_ACM", "task_type": "operational", "title": "Cut ACM"},
            {
                "task_id": "V_GROOVE",
                "task_type": "operational",
                "title": "V-groove",
                "machine_id": 9001,  # declares applicability without inventing usage
            },
        ],
        "materials": [
            {"id": 711, "code": "F6-ACM-SHEET", "unit": "mp", "unit_cost": 95.0, "qty": 2.5},
            {"id": 712, "code": "F6-FASTENER", "unit": "buc", "unit_cost": 1.5, "qty": 20.0},
        ],
        "machine_on_task": True,
        "expected_material": 2.5 * 95.0 + 20 * 1.5,
    },
    "F6-PROFILE": {
        "order_id": 880063,
        "tasks": [
            {"task_id": "FORM_PROFILE", "task_type": "operational", "title": "Form profile"},
            {"task_id": "BOND", "task_type": "operational", "title": "Bond"},
        ],
        "materials": [
            {"id": 721, "code": "F6-ALU-ML", "unit": "ml", "unit_cost": 18.0, "qty": 6.0},
            {"id": 722, "code": "F6-ADHESIVE", "unit": "buc", "unit_cost": 25.0, "qty": 2.0},
        ],
        "machine_on_task": False,
        "expected_material": 6 * 18.0 + 2 * 25.0,
    },
}

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

    fix = IsolatedDBFixture(prefix="f6_multi_type_")
    fix.setup()
    yield fix
    fix.teardown()


async def _seed_family(session, family_key: str) -> dict[str, Any]:
    fam = FAMILIES[family_key]
    order_id = int(fam["order_id"])
    now = datetime.now(timezone.utc)
    session.add(
        Orders(
            id=order_id,
            code=f"QA-{family_key}-{order_id}",
            client_name=f"F6 {family_key}",
            status="in_production",
            snapshot_v2_json=json.dumps(
                {
                    "accepted_commercial_total": 5000.0,
                    "accepted_currency": "RON",
                    "estimated_internal_total": 2000.0,
                    "estimated_internal_cost_snapshot": {
                        "estimated_material_cost": 800.0,
                        "estimated_operation_cost": 1200.0,
                    },
                    "f6_family": family_key,
                }
            ),
        )
    )
    session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"QA-{family_key}",
            snapshot_version=1,
            total_estimated_time_minutes=90.0,
            tasks_json=json.dumps(fam["tasks"]),
        )
    )
    primary = fam["tasks"][0]["task_id"]
    machine_id = None
    if fam.get("machine_on_task"):
        for task in fam["tasks"]:
            if task.get("machine_id") not in (None, "", 0):
                machine_id = task["machine_id"]
                break
    reality_task: dict[str, Any] = {
        "task_id": primary,
        "session_id": f"sess-{family_key}",
        "employee_id": 901,
        "started_at": (now - timedelta(hours=1)).isoformat(),
        "ended_at": now.isoformat(),
        "duration_seconds": 3600,
        "actual_cost_policy_runtime_v1": True,
    }
    if machine_id is not None:
        reality_task["machine_id"] = machine_id
    session.add(
        ExecutionReality(
            order_id=order_id,
            order_code=f"QA-{family_key}",
            tasks_json=json.dumps([reality_task]),
        )
    )
    if (
        await session.execute(select(Employees).where(Employees.id == 901))
    ).scalar_one_or_none() is None:
        session.add(
            Employees(
                id=901,
                name="F6 Pilot Operator",
                role="operator",
                status="active",
                employee_type="productive",
            )
        )
    if (
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
                provenance="qa_f6",
                reason="f6 multi-type pilot",
                created_by="qa",
                version=1,
            )
        )
    for mat in fam["materials"]:
        session.add(
            Inventory_materials(
                id=mat["id"],
                code=mat["code"],
                name=mat["code"],
                unit=mat["unit"],
                stock_current=1000.0,
                unit_cost=mat["unit_cost"],
                currency="RON",
                status="active",
            )
        )
    await session.flush()
    svc = MaterialActualsService(session)
    movement_ids: list[int] = []
    for idx, mat in enumerate(fam["materials"]):
        out = await svc.record_issue(
            order_id=order_id,
            material_id=mat["id"],
            quantity=float(mat["qty"]),
            unit=mat["unit"],
            actor_id="f6-mgr",
            idempotency_key=f"f6-{family_key}-issue-{idx}",
            task_id=primary,
        )
        movement_ids.append(int(out["movement_id"]))
    await ActualCostPolicyRuntimeService(session).finalize_labor_lines(order_id)
    await session.commit()
    return {"order_id": order_id, "movement_ids": movement_ids, "family": fam}


@pytest.mark.asyncio
async def test_f6_three_operational_families_close_and_isolate(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        seeded = {}
        for key in ("F6-LED", "F6-ACM", "F6-PROFILE"):
            seeded[key] = await _seed_family(session, key)

        svc = MaterialActualsService(session)
        runtime = ActualCostPolicyRuntimeService(session)
        profit = ProfitabilityActualReadModelService(session)

        # Cross-job isolation of material totals
        for key, meta in seeded.items():
            basis = await svc.material_actual_basis(meta["order_id"])
            assert basis["available"] is True
            assert basis["value"] == pytest.approx(FAMILIES[key]["expected_material"])

        # ACM declares machine applicability without inventing cost
        model_acm = await profit.build(seeded["F6-ACM"]["order_id"])
        machine = model_acm["actual_cost_truth"]["machine_actual_cost"]
        assert machine["applicability"] == "applicable_optional"
        assert machine["available"] is False
        assert machine["value"] is None
        assert machine["reason"] == REASON_MACHINE_ACTUAL_NOT_CAPTURED

        model_led = await profit.build(seeded["F6-LED"]["order_id"])
        assert (
            model_led["actual_cost_truth"]["machine_actual_cost"]["reason"]
            == REASON_MACHINE_NOT_APPLICABLE
        )
        assert (
            model_led["actual_cost_truth"]["other_actual_cost"]["applicability"]
            == "not_applicable"
        )

        # Close LED family; catalog change must not rewrite freeze
        led_id = seeded["F6-LED"]["order_id"]
        assert (await runtime.closure_readiness(led_id))["ready"] is True
        await runtime.close_job(led_id, "f6-mgr", {"authorized": True})
        mat = (
            await session.execute(select(Inventory_materials).where(Inventory_materials.id == 701))
        ).scalar_one()
        mat.unit_cost = 999.0
        await session.commit()
        closed_model = await profit.build(led_id)
        assert closed_model["profitability_result"]["actual_margin"]["amount"]["available"] is True
        assert closed_model["actual_cost_truth"]["actual_material_cost"]["value"] == pytest.approx(
            FAMILIES["F6-LED"]["expected_material"]
        )

        # Closed-job guards
        with pytest.raises(HTTPException) as blocked:
            await svc.record_issue(
                order_id=led_id,
                material_id=701,
                quantity=1.0,
                unit="buc",
                actor_id="f6-mgr",
                idempotency_key="f6-led-closed-issue",
            )
        assert blocked.value.detail["error"] == REASON_EXECUTION_CLOSED_MUTATION_BLOCKED

        # Reopen + scrap + reclose
        await runtime.reopen_job(led_id, "f6-mgr", "f6 pilot correction")
        reopened = await profit.build(led_id)
        assert reopened["profitability_result"]["actual_margin"]["amount"]["available"] is False
        scrap = await svc.record_scrap(
            order_id=led_id,
            material_id=701,
            quantity=1.0,
            unit="buc",
            actor_id="f6-mgr",
            idempotency_key="f6-led-scrap",
            scrap_reason="pilot scrap",
        )
        assert scrap["status"] == "recorded"
        await runtime.close_job(led_id, "f6-mgr", {"authorized": True})
        reclosed = await profit.build(led_id)
        assert reclosed["profitability_result"]["actual_margin"]["amount"]["available"] is True

        # PROFILE partial return + ACM full return path
        profile_id = seeded["F6-PROFILE"]["order_id"]
        first_move = seeded["F6-PROFILE"]["movement_ids"][0]
        await svc.record_return(
            order_id=profile_id,
            reverses_movement_id=first_move,
            quantity=2.0,
            actor_id="f6-mgr",
            idempotency_key="f6-profile-partial-return",
        )
        basis_profile = await svc.material_actual_basis(profile_id)
        assert basis_profile["value"] == pytest.approx(
            FAMILIES["F6-PROFILE"]["expected_material"] - 2 * 18.0
        )

        acm_id = seeded["F6-ACM"]["order_id"]
        acm_move = seeded["F6-ACM"]["movement_ids"][0]
        qty = float(FAMILIES["F6-ACM"]["materials"][0]["qty"])
        await svc.record_return(
            order_id=acm_id,
            reverses_movement_id=acm_move,
            quantity=qty,
            actor_id="f6-mgr",
            idempotency_key="f6-acm-full-return",
        )
        # remaining ACM material = fasteners only
        assert (await svc.material_actual_basis(acm_id))["value"] == pytest.approx(20 * 1.5)

        # Commercial snapshots unchanged
        for key, meta in seeded.items():
            order = (
                await session.execute(select(Orders).where(Orders.id == meta["order_id"]))
            ).scalar_one()
            snap = json.loads(order.snapshot_v2_json)
            assert snap["accepted_commercial_total"] == 5000.0
            assert snap["f6_family"] == key


@pytest.mark.asyncio
async def test_f6_unit_mismatch_and_bom_rejected(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        session.add(
            Inventory_materials(
                id=731,
                code="F6-UNIT",
                name="Unit mat",
                unit="ml",
                stock_current=10,
                unit_cost=5.0,
                currency="RON",
                status="active",
            )
        )
        await session.commit()
        svc = MaterialActualsService(session)
        with pytest.raises(HTTPException) as unit_err:
            await svc.record_issue(
                order_id=1,
                material_id=731,
                quantity=1,
                unit="buc",
                actor_id="a",
                idempotency_key="f6-unit",
            )
        assert unit_err.value.detail["error"] == "material_unit_mismatch"
        with pytest.raises(HTTPException) as bom:
            await svc.record_issue(
                order_id=1,
                material_id=731,
                quantity=1,
                unit="ml",
                actor_id="a",
                idempotency_key="f6-bom",
                source_type="planned_bom",
            )
        assert bom.value.detail["error"] == "planned_bom_not_actual"
