"""TE2E-028B isolated live proof — NEW order only; never mutates 8/9/10 or 972901."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.product_definition import (
    ProductDefinitionOperationRole,
    ProductDefinitionPreview,
    ProductDefinitionSourceContext,
)
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview
from services.formula_handlers import FormulaId
from services.post_job_truth_service import PostJobTruthService
from services.product_aggregate_planning_duration_service import (
    apply_planning_duration_resolution,
)
from services.product_aggregate_service import ProductAggregateService
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
OID = 972910
LETTER_COUNT = 5
EXPECTED_MINUTES = 10.0
COMMERCIAL_TOTAL = 1888.0
DB_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")


async def _ref_plan(db: AsyncSession, order_id: int) -> None:
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    print(
        f"REF order={order_id} plan_id={getattr(plan, 'id', None)} "
        f"total_min={getattr(plan, 'total_estimated_time_minutes', None)}"
    )


async def main() -> None:
    engine = create_async_engine(DB_URL, future=True)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        for oid in (92402, 92403, 972901):
            await _ref_plan(db, oid)

        svc = ProductAggregateService(db)
        agg = await svc.build(TEMPLATE)
        if agg is None:
            raise SystemExit(f"Aggregate missing for {TEMPLATE}")

        agg = apply_planning_duration_resolution(agg, {"letter_count": LETTER_COUNT})
        ops = {o.operation_code: o for o in (agg.operations or [])}
        vp = ops.get("vector_prep")
        print(
            "AGG vector_prep",
            None
            if not vp
            else (
                vp.estimated_minutes,
                vp.planning_duration_mode,
                vp.planning_duration_formula_id,
                vp.planning_minutes_source,
            ),
        )
        if not vp or vp.estimated_minutes != EXPECTED_MINUTES:
            raise SystemExit(
                f"Expected vector_prep={EXPECTED_MINUTES}, got {getattr(vp, 'estimated_minutes', None)}"
            )
        if vp.planning_duration_formula_id != FormulaId.COUNT_BASED_TIME.value:
            raise SystemExit("Expected count_based_time duration formula")

        existing = await db.get(Orders, OID)
        if existing is not None:
            plans = (
                await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == OID))
            ).scalars().all()
            for p in plans:
                await db.delete(p)
            await db.delete(existing)
            await db.commit()

        rec = QuoteSnapshotV2Record(
            snapshot_code=f"QSN2-TE2E028B-LIVE-{OID}",
            snapshot_version="1.0.0",
            version=1,
            template_code=TEMPLATE,
            status="frozen",
            readiness="ready_for_owner_review",
            snapshot_json="{}",
            content_hash="te2e028blive",
        )
        db.add(rec)
        await db.flush()

        pd = ProductDefinitionPreview(
            template_code=TEMPLATE,
            source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
            operation_roles=[
                ProductDefinitionOperationRole(
                    operation_code=o.operation_code,
                    label=o.label,
                    workcenter=o.workcenter,
                )
                for o in (agg.operations or [])[:50]
            ],
            geometry_inputs={"letter_count": LETTER_COUNT},
            canonical_values={"letter_count": LETTER_COUNT},
        )
        snap = OrderSnapshotV2(
            quote_id=OID,
            quote_snapshot_v2_id=int(rec.id),
            snapshot_code=f"OSN2-TE2E028B-LIVE-{OID}",
            content_hash=("te2e028blive" + "0" * 20)[:32],
            product_definition_snapshot=pd,
            product_aggregate_snapshot=agg,
            commercial_price_proposal_snapshot=_commercial_preview(total=COMMERCIAL_TOTAL),
            estimated_internal_cost_snapshot=_internal_preview(total=620.0),
            accepted_commercial_total=COMMERCIAL_TOTAL,
            accepted_currency="RON",
            estimated_internal_total=620.0,
        )
        order = Orders(
            id=OID,
            code=f"ORD-TE2E028B-LOCAL-{OID}",
            client_name="LOCAL_TEST_FIXTURE TE2E-028B Formula Duration",
            status="locked",
            total_amount=COMMERCIAL_TOTAL,
            quote_id=OID,
            quote_snapshot_v2_id=int(rec.id),
            snapshot_v2_json=snap.model_dump_json(),
            readiness_snapshot={
                "execution_plan_created": False,
                "no_execution_plan_created": True,
                "local_test_fixture": True,
                "te2e_028b": True,
                "retention": "dev_ephemeral",
            },
        )
        db.add(order)
        await db.commit()

        preview = await build_execution_plan_v2_preview(db, OID)
        vp_task = next(
            t for t in preview.planned_tasks if t.source_operation_code == "vector_prep"
        )
        print(
            "PREVIEW",
            preview.status,
            "vector_prep",
            vp_task.estimated_minutes,
            vp_task.planning_minutes_source,
        )

        persist = await create_execution_plan_v2_from_order(db, OID)
        await materialize_execution_plan_v2_operational_tasks(db, OID)
        await db.commit()

        plan = (
            await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == OID))
        ).scalar_one()
        env = json.loads(plan.tasks_json)
        vp_op = next(
            t
            for t in env.get("operational_tasks", [])
            if t.get("source_operation_code") == "vector_prep"
        )
        print(
            "PLAN id",
            plan.id,
            "vector_prep",
            vp_op.get("estimated_time_minutes"),
            vp_op.get("planning_minutes_source"),
        )

        truth = await PostJobTruthService(db).build_for_order(OID)
        body = truth.model_dump(mode="json")
        vp_row = next(
            o
            for o in body["reconciliation"]["operations"]
            if o.get("planned_minutes", {}).get("value") == EXPECTED_MINUTES
        )
        print(
            "POSTJOB write_back",
            body["write_back_performed"],
            "vector_prep planned",
            vp_row["planned_minutes"],
            "actual",
            vp_row["actual_minutes"]["presence"],
            "state",
            vp_row["reconciliation_state"],
            "commercial",
            order.total_amount,
        )

        for oid in (92402, 92403, 972901):
            await _ref_plan(db, oid)

        print(
            "FIXTURE",
            json.dumps(
                {
                    "label": "LOCAL_TEST_FIXTURE",
                    "order_id": OID,
                    "plan_id": plan.id,
                    "template": TEMPLATE,
                    "operation": "vector_prep",
                    "formula_id": FormulaId.COUNT_BASED_TIME.value,
                    "inputs": {"letter_count": LETTER_COUNT},
                    "expected_minutes": EXPECTED_MINUTES,
                    "commercial_total": COMMERCIAL_TOTAL,
                    "retention": "dev_ephemeral",
                    "ui_path": f"/execution/{OID}",
                },
                ensure_ascii=False,
            ),
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
