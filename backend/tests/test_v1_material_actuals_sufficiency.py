"""V1 material actuals sufficiency — frozen StockMovement authority for Profitability."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import delete, select

from models.execution_plan import ExecutionPlan
from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.stock_movements import StockMovement
from services.inventory_stock_adjustment_service import InventoryStockAdjustmentService
from services.material_actuals_service import (
    REASON_PLANNED_BOM_REJECTED,
    MaterialActualsService,
)
from services.profitability_actual_material_input_service import (
    MATERIAL_INPUT_CONTRACT,
    build_profitability_actual_material_input,
)
from services.profitability_actual_read_model_service import ProfitabilityActualReadModelService
from tests._db_fixture import IsolatedDBFixture

ORDER_ID = 880051

_TABLES = [
    StockMovement,
    ExecutionPlan,
    Inventory_materials,
    Orders,
]


async def _clear(session) -> None:
    for table in _TABLES:
        await session.execute(delete(table))
    await session.commit()


@pytest.fixture(scope="module")
def db_fixture():
    import models.execution_plan  # noqa: F401
    import models.inventory_materials  # noqa: F401
    import models.orders  # noqa: F401
    import models.stock_movements  # noqa: F401

    fix = IsolatedDBFixture(prefix="v1_mat_actuals_")
    fix.setup()
    yield fix
    fix.teardown()


async def _seed_order_plan(session, *, order_id: int = ORDER_ID) -> None:
    session.add(
        Orders(
            id=order_id,
            code=f"QA-MAT-{order_id}",
            client_name="Material Sufficiency Client",
            status="in_production",
            snapshot_v2_json=json.dumps(
                {
                    "accepted_commercial_total": 500.0,
                    "accepted_currency": "EUR",
                }
            ),
        )
    )
    session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"QA-MAT-{order_id}",
            snapshot_version=1,
            total_estimated_time_minutes=30.0,
            tasks_json=json.dumps(
                {
                    "format": "v2_envelope",
                    "operational_tasks": [
                        {"task_id": "FACE", "task_type": "operational"},
                        {"task_id": "RETURN", "task_type": "operational"},
                    ],
                }
            ),
        )
    )


async def _seed_materials(session) -> None:
    session.add_all(
        [
            Inventory_materials(
                id=601,
                code="PLEXI-3MM-CLR",
                name="Plexiglas 3mm",
                unit="buc",
                stock_current=100.0,
                unit_cost=25.0,
                currency="RON",
                status="active",
            ),
            Inventory_materials(
                id=602,
                code="ORACAL-641-BLACK",
                name="Oracal 641 Black",
                unit="m",
                stock_current=200.0,
                unit_cost=6.5,
                currency="RON",
                status="active",
            ),
            Inventory_materials(
                id=603,
                code="ALU-RETURN-60",
                name="Aluminum return 60mm",
                unit="m",
                stock_current=50.0,
                unit_cost=12.0,
                currency="RON",
                status="active",
            ),
        ]
    )


@pytest.mark.asyncio
async def test_single_material_frozen_input(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_order_plan(session)
        await _seed_materials(session)
        await session.commit()

        svc = MaterialActualsService(session)
        await svc.record_issue(
            order_id=ORDER_ID,
            material_id=601,
            quantity=2.0,
            unit="buc",
            actor_id="qa",
            idempotency_key="mat-single-1",
            task_id="FACE",
        )
        await session.commit()

        # Live catalog change must not reprice historical issue.
        mat = (
            await session.execute(select(Inventory_materials).where(Inventory_materials.id == 601))
        ).scalar_one()
        mat.unit_cost = 999.0
        await session.commit()

        payload = await build_profitability_actual_material_input(session, order_id=ORDER_ID)
        assert payload["contract"] == MATERIAL_INPUT_CONTRACT
        assert payload["status"] == "ok"
        assert payload["planned_bom_included"] is False
        assert payload["commercial_price_used"] is False
        assert payload["live_catalog_repriced"] is False
        assert payload["labor_included"] is False
        assert payload["machine_run_included"] is False
        assert payload["totals"]["total_material_cost"] == 50.0
        assert payload["totals"]["currency"] == "RON"
        assert len(payload["lines"]) == 1
        line = payload["lines"][0]
        assert line["material_id"] == 601
        assert line["material_code"] == "PLEXI-3MM-CLR"
        assert line["task_id"] == "FACE"
        assert line["quantity"] == 2.0
        assert line["rate_used"] == 25.0
        assert line["total_cost"] == 50.0


@pytest.mark.asyncio
async def test_multi_material_and_oracal_distinct(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_order_plan(session)
        await _seed_materials(session)
        await session.commit()

        svc = MaterialActualsService(session)
        await svc.record_issue(
            order_id=ORDER_ID,
            material_id=601,
            quantity=1.0,
            unit="buc",
            actor_id="qa",
            idempotency_key="mat-m1",
            task_id="FACE",
        )
        await svc.record_issue(
            order_id=ORDER_ID,
            material_id=602,
            quantity=3.0,
            unit="m",
            actor_id="qa",
            idempotency_key="mat-m2",
            task_id="FACE",
        )
        await svc.record_issue(
            order_id=ORDER_ID,
            material_id=603,
            quantity=2.0,
            unit="m",
            actor_id="qa",
            idempotency_key="mat-m3",
            task_id="RETURN",
        )
        await session.commit()

        payload = await build_profitability_actual_material_input(session, order_id=ORDER_ID)
        assert payload["status"] == "ok"
        codes = {line["material_code"] for line in payload["lines"]}
        assert codes == {"PLEXI-3MM-CLR", "ORACAL-641-BLACK", "ALU-RETURN-60"}
        assert payload["totals"]["total_material_cost"] == round(25.0 + 3 * 6.5 + 2 * 12.0, 4)
        assert len(payload["lines"]) == 3


@pytest.mark.asyncio
async def test_same_material_multiple_tasks_no_merge_loss(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_order_plan(session)
        await _seed_materials(session)
        await session.commit()

        svc = MaterialActualsService(session)
        await svc.record_issue(
            order_id=ORDER_ID,
            material_id=602,
            quantity=1.0,
            unit="m",
            actor_id="qa",
            idempotency_key="mat-t1",
            task_id="FACE",
        )
        await svc.record_issue(
            order_id=ORDER_ID,
            material_id=602,
            quantity=2.0,
            unit="m",
            actor_id="qa",
            idempotency_key="mat-t2",
            task_id="RETURN",
        )
        await session.commit()

        payload = await build_profitability_actual_material_input(session, order_id=ORDER_ID)
        assert len(payload["lines"]) == 2
        by_task = {line["task_id"]: line for line in payload["lines"]}
        assert by_task["FACE"]["quantity"] == 1.0
        assert by_task["RETURN"]["quantity"] == 2.0
        assert payload["totals"]["total_material_cost"] == round(3 * 6.5, 4)


@pytest.mark.asyncio
async def test_quantity_correction_via_return(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_order_plan(session)
        await _seed_materials(session)
        await session.commit()

        svc = MaterialActualsService(session)
        issue = await svc.record_issue(
            order_id=ORDER_ID,
            material_id=601,
            quantity=4.0,
            unit="buc",
            actor_id="qa",
            idempotency_key="mat-corr-issue",
            task_id="FACE",
        )
        await session.commit()
        movement = (
            await session.execute(
                select(StockMovement).where(StockMovement.id == issue["movement_id"])
            )
        ).scalar_one()
        await svc.record_return(
            order_id=ORDER_ID,
            reverses_movement_id=movement.id,
            quantity=1.0,
            actor_id="qa",
            idempotency_key="mat-corr-return",
        )
        await session.commit()

        payload = await build_profitability_actual_material_input(session, order_id=ORDER_ID)
        assert payload["status"] == "ok"
        assert payload["totals"]["total_material_cost"] == 75.0  # 3 * 25
        face = next(line for line in payload["lines"] if line["task_id"] == "FACE")
        assert face["quantity"] == 3.0


@pytest.mark.asyncio
async def test_legacy_stock_reversal_excluded_from_basis(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_order_plan(session)
        await _seed_materials(session)
        await session.commit()

        svc = MaterialActualsService(session)
        issue = await svc.record_issue(
            order_id=ORDER_ID,
            material_id=601,
            quantity=2.0,
            unit="buc",
            actor_id="qa",
            idempotency_key="mat-rev-issue",
        )
        await session.commit()
        mid = issue["movement_id"]

        await InventoryStockAdjustmentService(session).reverse_movement(
            mid, performed_by="qa", reason="correction"
        )

        basis = await MaterialActualsService(session).material_actual_basis(ORDER_ID)
        assert basis["available"] is False
        assert basis["reason"] == "material_movement_missing"

        payload = await build_profitability_actual_material_input(session, order_id=ORDER_ID)
        assert payload["status"] == "incomplete"


@pytest.mark.asyncio
async def test_planned_bom_rejected(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_order_plan(session)
        await _seed_materials(session)
        await session.commit()

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            await MaterialActualsService(session).record_issue(
                order_id=ORDER_ID,
                material_id=601,
                quantity=1.0,
                unit="buc",
                actor_id="qa",
                idempotency_key="mat-planned",
                source_type="planned_bom",
            )
        assert exc.value.detail["error"] == REASON_PLANNED_BOM_REJECTED


@pytest.mark.asyncio
async def test_missing_cost_fail_closed(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_order_plan(session)
        session.add(
            Inventory_materials(
                id=701,
                code="NO-COST",
                name="No cost material",
                unit="buc",
                stock_current=10.0,
                unit_cost=None,
                currency=None,
                status="missing_price",
            )
        )
        await session.commit()

        await MaterialActualsService(session).record_issue(
            order_id=ORDER_ID,
            material_id=701,
            quantity=1.0,
            unit="buc",
            actor_id="qa",
            idempotency_key="mat-nocost",
        )
        await session.commit()

        payload = await build_profitability_actual_material_input(session, order_id=ORDER_ID)
        assert payload["status"] == "incomplete"
        assert payload["reason"] == "material_valuation_unavailable"
        assert payload["totals"]["total_material_cost"] is None


@pytest.mark.asyncio
async def test_profitability_rm_embeds_material_input(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_order_plan(session)
        await _seed_materials(session)
        await session.commit()
        await MaterialActualsService(session).record_issue(
            order_id=ORDER_ID,
            material_id=601,
            quantity=1.0,
            unit="buc",
            actor_id="qa",
            idempotency_key="mat-rm-1",
            task_id="FACE",
        )
        await session.commit()

        model = await ProfitabilityActualReadModelService(session).build(ORDER_ID)
        mi = model["actual_operational_truth"]["material_input"]
        assert mi is not None
        assert mi["status"] == "ok"
        assert mi["totals"]["total_material_cost"] == 25.0
        assert model["actual_cost_truth"]["material_input"]["contract"] == MATERIAL_INPUT_CONTRACT
        assert model["actual_cost_truth"]["actual_material_cost"]["available"] is True
        assert model["actual_cost_truth"]["actual_material_cost"]["value"] == 25.0


@pytest.mark.asyncio
async def test_restart_durability_from_db(db_fixture):
    async with db_fixture.session_maker() as session:
        await _clear(session)
        await _seed_order_plan(session)
        await _seed_materials(session)
        await session.commit()
        await MaterialActualsService(session).record_issue(
            order_id=ORDER_ID,
            material_id=601,
            quantity=2.0,
            unit="buc",
            actor_id="qa",
            idempotency_key="mat-dur-1",
        )
        await session.commit()

    async with db_fixture.session_maker() as session2:
        payload = await build_profitability_actual_material_input(session2, order_id=ORDER_ID)
        assert payload["status"] == "ok"
        assert payload["totals"]["total_material_cost"] == 50.0
