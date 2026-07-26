"""TE2E-028A isolated live proof — NEW order only; never mutates 92402/92403."""

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
from services.post_job_truth_service import PostJobTruthService
from services.product_aggregate_service import ProductAggregateService
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
OID = 972901
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
        for oid in (92402, 92403):
            await _ref_plan(db, oid)

        svc = ProductAggregateService(db)
        agg = await svc.build(TEMPLATE)
        if agg is None:
            raise SystemExit(f"Aggregate missing for {TEMPLATE}")

        ops = {o.operation_code: o for o in (agg.operations or [])}
        qc = ops.get("qc_letters")
        print(
            "AGG qc_letters",
            None if not qc else (qc.estimated_minutes, qc.calculation_type),
        )
        static_nonzero = [
            (c, o.estimated_minutes, o.calculation_type)
            for c, o in ops.items()
            if o.estimated_minutes is not None and o.estimated_minutes > 0
        ]
        print("AGG static_nonzero_count", len(static_nonzero), static_nonzero[:8])

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
            snapshot_code=f"QSN2-TE2E028A-LIVE-{OID}",
            snapshot_version="1.0.0",
            version=1,
            template_code=TEMPLATE,
            status="frozen",
            readiness="ready_for_owner_review",
            snapshot_json="{}",
            content_hash="te2e028alive",
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
        )
        snap = OrderSnapshotV2(
            quote_id=OID,
            quote_snapshot_v2_id=int(rec.id),
            snapshot_code=f"OSN2-TE2E028A-LIVE-{OID}",
            content_hash=("te2e028alive" + "0" * 20)[:32],
            product_definition_snapshot=pd,
            product_aggregate_snapshot=agg,
            commercial_price_proposal_snapshot=_commercial_preview(total=1500.0),
            estimated_internal_cost_snapshot=_internal_preview(total=620.0),
            accepted_commercial_total=1500.0,
            accepted_currency="RON",
            estimated_internal_total=620.0,
        )
        order = Orders(
            id=OID,
            code=f"ORD-TE2E028A-LIVE-{OID}",
            client_name="TE2E-028A LIVE PROOF — TEST FIXTURE",
            status="locked",
            total_amount=1500.0,
            quote_id=OID,
            quote_snapshot_v2_id=int(rec.id),
            snapshot_v2_json=snap.model_dump_json(),
            readiness_snapshot={
                "execution_plan_created": False,
                "no_execution_plan_created": True,
                "te2e028a_fixture": True,
            },
        )
        db.add(order)
        await db.commit()

        preview = await build_execution_plan_v2_preview(db, OID)
        with_minutes = [
            (t.source_operation_code, t.estimated_minutes, t.planning_minutes_source)
            for t in preview.planned_tasks
            if t.estimated_minutes is not None
        ]
        print(
            "PREVIEW",
            preview.status,
            "tasks",
            len(preview.planned_tasks),
            "with_minutes",
            with_minutes,
        )

        persist = await create_execution_plan_v2_from_order(db, OID)
        await materialize_execution_plan_v2_operational_tasks(db, OID)
        await db.commit()

        plan = (
            await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == OID))
        ).scalar_one()
        env = json.loads(plan.tasks_json)
        ops_m = [
            (
                t.get("source_operation_code"),
                t.get("estimated_time_minutes"),
                t.get("planning_minutes_source"),
            )
            for t in env.get("operational_tasks", [])
            if t.get("estimated_time_minutes") is not None
        ]
        print("PLAN id", plan.id, "ops_with_minutes", ops_m)

        truth = await PostJobTruthService(db).build_for_order(OID)
        body = truth.model_dump(mode="json")
        present_plan = [
            o
            for o in body["reconciliation"]["operations"]
            if o["planned_minutes"]["presence"] == "present"
        ]
        missing_plan = [
            o
            for o in body["reconciliation"]["operations"]
            if o["planned_minutes"]["presence"] == "missing"
        ]
        print(
            "POSTJOB write_back",
            body["write_back_performed"],
            "planned_present",
            len(present_plan),
            "planned_missing",
            len(missing_plan),
            "commercial",
            order.total_amount,
        )
        if present_plan:
            sample = present_plan[0]
            print(
                "POSTJOB sample",
                sample.get("task_name"),
                sample["planned_minutes"],
                sample["reconciliation_state"],
                sample["actual_minutes"]["presence"],
            )

        for oid in (92402, 92403):
            await _ref_plan(db, oid)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
