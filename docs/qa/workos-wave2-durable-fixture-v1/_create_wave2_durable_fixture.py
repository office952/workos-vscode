"""Create ONE durable Wave 2 QA fixture in local backend/dev.db.

Canonical service path used:
  ProductDefinition preview shape
  → ProductAggregate (alias collapse + ORR stamp)
  → CPP/EIC preview snapshots
  → Quote Snapshot V2 record (frozen/accepted readiness)
  → Order + Order Snapshot V2 JSON
  → ExecutionPlan V2 preview
  → ExecutionPlan V2 persist draft (idempotent)
  → materialization audit GET

FORBIDDEN in this script:
  POST materialize / operational_tasks writes
  assignment / sessions / scheduling
  touching protected orders 880811 / 973019
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret-not-for-production")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.product_definition import (
    ProductDefinitionOperationRole,
    ProductDefinitionPreview,
    ProductDefinitionSourceContext,
)
from services.execution_plan_v2_materialization_audit_service import (
    build_execution_plan_v2_materialization_audit_by_order_id,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview
from services.operation_workcenter_resolution_service import (
    apply_workcenter_resolution_to_aggregate,
    load_orr_mappings,
)
from services.product_process_aggregate_bridge import collapse_operational_alias_rules
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

OUT_DIR = Path(__file__).resolve().parent
EVIDENCE = OUT_DIR / "fixture-evidence.json"

# Durable fixed QA identity — outside protected baselines.
OID = 880750
PROTECTED = {880811, 973019}
TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
COMMERCIAL_TOTAL = 1925.0
INTERNAL_TOTAL = 780.0
FIXTURE_NAME = "WAVE2-DURABLE-QA-880750"


def _rule(
    name: str,
    priced: str,
    seq: int,
    deps: list[str] | None = None,
    task_type: str = "process",
) -> ProductAggregateTaskRule:
    return ProductAggregateTaskRule(
        task_name=name,
        task_type=task_type,
        priced_operation=priced,
        sequence=seq,
        depends_on_process_ids=list(deps or []),
        provenance="derived",
    )


def _op(
    code: str,
    label: str,
    *,
    workcenter: str | None = None,
    status: str | None = None,
    source: str | None = None,
) -> ProductAggregateOperation:
    return ProductAggregateOperation(
        operation_code=code,
        label=label,
        workcenter=workcenter,
        workcenter_resolution_status=status,
        workcenter_mapping_source=source,
        priced=True,
        provenance="derived",
    )


def _rich_rules() -> list[ProductAggregateTaskRule]:
    return [
        _rule("svg_geometry_analysis", "svg_geometry_analysis", 0, task_type="READINESS_GATE"),
        _rule("vector_prep", "vector_prep", 1),
        _rule("cnc_face_cut", "face_cnc_cut", 2),
        _rule("back_cut", "back_cut", 3),
        _rule("return_profile_forming", "side_forming", 4),
        _rule("RETURN_PROFILE_MACHINE_FORMING", "RETURN_PROFILE_MACHINE_FORMING", 4),
        _rule(
            "return_face_bonding",
            "return_face_bonding",
            5,
            deps=["face_cnc_cut", "side_forming"],
        ),
        _rule("RETURN_PROFILE_FACE_BONDING", "RETURN_PROFILE_FACE_BONDING", 5),
        _rule("painting", "painting", 7, deps=["return_face_bonding"]),
        _rule("PAINTING", "PAINTING", 7),
        _rule("led_install_letters", "led_install_letters", 8, deps=["back_cut"]),
        _rule("electrical_letters", "electrical_letters", 9, deps=["led_install_letters"]),
        _rule(
            "assembly_letters",
            "assembly_letters",
            10,
            deps=[
                "return_face_bonding",
                "painting",
                "back_cut",
                "led_install_letters",
                "electrical_letters",
            ],
        ),
        _rule(
            "vinyl_application",
            "vinyl_application",
            11,
            deps=["return_face_bonding", "assembly_letters"],
        ),
        _rule("mounting_template_cnc_cut", "mounting_template_cnc_cut", 12, deps=["vector_prep"]),
        _rule(
            "qc_letters",
            "qc_letters",
            13,
            deps=["assembly_letters", "vinyl_application"],
        ),
        _rule("packaging", "packaging_letters", 14, deps=["qc_letters"]),
    ]


def _operations() -> list[ProductAggregateOperation]:
    return [
        _op("svg_geometry_analysis", "SVG Geometry Analysis", status="not_required"),
        _op("vector_prep", "Vector Prep"),
        _op("face_cnc_cut", "Face CNC Cut"),
        _op("back_cut", "Back CNC Cut"),
        _op("side_forming", "Side Forming"),
        _op("RETURN_PROFILE_MACHINE_FORMING", "Return Profile Machine Forming (alias)"),
        _op("return_face_bonding", "Return Face Bonding"),
        _op("RETURN_PROFILE_FACE_BONDING", "Return Profile Face Bonding (alias)"),
        _op("painting", "Painting"),
        _op("PAINTING", "Painting module (alias)"),
        _op("led_install_letters", "LED Install"),
        _op("electrical_letters", "Electrical"),
        _op("assembly_letters", "Assembly Letters"),
        _op("vinyl_application", "Vinyl Application"),
        _op("mounting_template_cnc_cut", "Mounting Template CNC"),
        _op("qc_letters", "QC Letters"),
        _op("packaging_letters", "Packaging"),
        # DEC-002: BOM metadata only — not a task_rule.
        _op("premount_bar_preparation", "Premount bar preparation"),
    ]


def _product_definition() -> ProductDefinitionPreview:
    parent_ops = [
        op
        for op in _operations()
        if op.operation_code
        and not str(op.operation_code).isupper()
        and op.operation_code
        not in {"premount_bar_preparation", "svg_geometry_analysis"}
    ]
    return ProductDefinitionPreview(
        template_code=TEMPLATE,
        source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
        operation_roles=[
            ProductDefinitionOperationRole(
                operation_code=op.operation_code,
                label=op.label or op.operation_code,
                workcenter=op.workcenter,
            )
            for op in parent_ops
        ],
        canonical_values={
            "paint_ral_code": "ral9016",
            "face_finish_type": "oracal_651",
            "lighting_system_type": "led_modules",
            "mounting_template_required": True,
            "wave2_durable_fixture": FIXTURE_NAME,
        },
    )


async def _build_aggregate(db: AsyncSession) -> ProductAggregate:
    collapsed = collapse_operational_alias_rules(_rich_rules())
    agg = ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=_operations(),
        task_contract=ProductAggregateTaskContract(
            task_rules=collapsed,
            notes=[
                "wave2_durable_qa",
                "operational_alias_collapse=dec003_dec004",
                "premount_bom_only=dec002",
                "svg_non_operational=dec001",
            ],
            process_graph_source="wave2_durable_qa",
        ),
    )
    mappings = await load_orr_mappings(db)
    return apply_workcenter_resolution_to_aggregate(agg, mappings)


def _sha(raw: str | bytes | None) -> str:
    if raw is None:
        return ""
    data = raw.encode() if isinstance(raw, str) else raw
    return hashlib.sha256(data).hexdigest()


async def _baseline(db: AsyncSession, oid: int) -> dict:
    order = await db.get(Orders, oid)
    if order is None:
        return {"order_id": oid, "present": False}
    raw = order.snapshot_v2_json or ""
    snap = json.loads(raw) if raw else {}
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == oid))
    ).scalar_one_or_none()
    return {
        "order_id": oid,
        "present": True,
        "code": order.code,
        "total_amount": order.total_amount,
        "quote_snapshot_v2_id": order.quote_snapshot_v2_id,
        "accepted_commercial_total": snap.get("accepted_commercial_total"),
        "snapshot_sha256_prefix": _sha(raw)[:8],
        "plan_id": getattr(plan, "id", None),
    }


async def main() -> None:
    assert OID not in PROTECTED
    assert os.environ["APP_ENV"] == "development"
    assert os.environ["ENVIRONMENT"] == "development"
    assert "dev.db" in os.environ["DATABASE_URL"]

    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        before = {
            "880811": await _baseline(db, 880811),
            "973019": await _baseline(db, 973019),
        }

        existing = await db.get(Orders, OID)
        created_order = False
        if existing is not None:
            order = existing
        else:
            agg = await _build_aggregate(db)
            pd = _product_definition()
            rec = QuoteSnapshotV2Record(
                snapshot_code=f"QSN2-WAVE2-{OID}",
                snapshot_version="1.0.0",
                version=1,
                template_code=TEMPLATE,
                status="frozen",
                readiness="ready_for_owner_review",
                snapshot_json="{}",
                content_hash=f"wave2{OID:08d}hashwave2hashwave2",
            )
            db.add(rec)
            await db.flush()

            order_snap = OrderSnapshotV2(
                quote_id=OID,
                quote_snapshot_v2_id=rec.id,
                snapshot_code=f"QSN2-WAVE2-{OID}",
                content_hash=f"wave2{OID:08d}hashwave2hashwave2ha",
                product_definition_snapshot=pd,
                product_aggregate_snapshot=agg,
                commercial_price_proposal_snapshot=_commercial_preview(total=COMMERCIAL_TOTAL),
                estimated_internal_cost_snapshot=_internal_preview(total=INTERNAL_TOTAL),
                accepted_commercial_total=COMMERCIAL_TOTAL,
                accepted_currency="RON",
                estimated_internal_total=INTERNAL_TOTAL,
            )
            snap_json = order_snap.model_dump_json()
            rec.snapshot_json = snap_json
            rec.content_hash = _sha(snap_json)[:32]

            order = Orders(
                id=OID,
                code=f"ORD-WAVE2-QA-{OID}",
                client_name="Wave2 Durable QA Fixture",
                status="locked",
                total_amount=COMMERCIAL_TOTAL,
                quote_id=OID,
                quote_snapshot_v2_id=rec.id,
                snapshot_v2_json=snap_json,
                readiness_snapshot={
                    "execution_plan_created": False,
                    "no_execution_plan_created": True,
                    "wave2_durable_fixture": FIXTURE_NAME,
                    "dec009": "A",
                },
                notes=json.dumps(
                    {
                        "fixture": FIXTURE_NAME,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "purpose": "FINALIZATION_WAVE_2 durable QA runtime/UI proof",
                        "materialization": "CLOSED",
                    }
                ),
            )
            db.add(order)
            await db.commit()
            await db.refresh(order)
            created_order = True

        preview = await build_execution_plan_v2_preview(db, order.id)
        first = await create_execution_plan_v2_from_order(db, order.id)
        second = await create_execution_plan_v2_from_order(db, order.id)
        plan = (
            await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order.id))
        ).scalar_one()
        env = json.loads(plan.tasks_json) if isinstance(plan.tasks_json, str) else plan.tasks_json
        audit = await build_execution_plan_v2_materialization_audit_by_order_id(db, order.id)

        planned = list(preview.planned_tasks or [])
        priced = {
            str(t.source_operation_code or "").lower()
            for t in planned
            if t.source_operation_code
        }
        vinyl = next((t for t in planned if str(t.source_operation_code) == "vinyl_application"), None)
        vinyl_deps = list(getattr(vinyl, "depends_on_task_keys", None) or []) if vinyl else []
        wc_map = {
            str(t.source_operation_code): {
                "workcenter": getattr(getattr(t, "machine_requirement", None), "workcenter", None),
                "mapping_source": getattr(
                    getattr(t, "machine_requirement", None), "mapping_source", None
                ),
                "resolution_status": getattr(
                    getattr(t, "machine_requirement", None), "resolution_status", None
                ),
                "estimated_minutes": t.estimated_minutes,
            }
            for t in planned
            if t.source_operation_code
        }

        after = {
            "880811": await _baseline(db, 880811),
            "973019": await _baseline(db, 973019),
        }

        evidence = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "non_production": {
                "APP_ENV": os.environ["APP_ENV"],
                "ENVIRONMENT": os.environ["ENVIRONMENT"],
                "DATABASE_URL": os.environ["DATABASE_URL"],
                "db_file": str((BACKEND / "dev.db").resolve()),
                "host": "127.0.0.1",
            },
            "fixture_name": FIXTURE_NAME,
            "created_order": created_order,
            "order_id": order.id,
            "order_code": order.code,
            "quote_id": order.quote_id,
            "quote_snapshot_v2_id": order.quote_snapshot_v2_id,
            "snapshot_code": json.loads(order.snapshot_v2_json or "{}").get("snapshot_code"),
            "snapshot_sha256": _sha(order.snapshot_v2_json),
            "accepted_commercial_total": json.loads(order.snapshot_v2_json or "{}").get(
                "accepted_commercial_total"
            ),
            "execution_plan_id": plan.id,
            "persist_first": {
                "execution_plan_id": first.execution_plan_id,
                "status": first.status,
            },
            "persist_second": {
                "execution_plan_id": second.execution_plan_id,
                "status": second.status,
            },
            "idempotent": first.execution_plan_id == second.execution_plan_id,
            "preview": {
                "status": preview.status,
                "no_write": preview.no_write,
                "execution_tasks_created": preview.execution_tasks_created,
                "planned_tasks": len(planned),
                "planned_operations": len(preview.planned_operations or []),
            },
            "envelope": {
                "execution_tasks_created": env.get("execution_tasks_created"),
                "operational_tasks_count": len(env.get("operational_tasks") or []),
                "planned_tasks_count": len(env.get("planned_tasks") or []),
            },
            "audit": {
                "post_materialize_allowed": audit.guards.post_materialize_allowed,
                "operational_tasks_in_envelope_count": audit.operational_tasks_in_envelope_count,
                "materialization_status": getattr(audit, "materialization_status", None)
                or getattr(audit, "status", None),
                "candidate_ops": sorted(
                    {
                        str(c.source_operation_code or "").lower()
                        for c in (audit.materializable_task_candidates or [])
                        if c.source_operation_code
                    }
                ),
            },
            "ownership": {
                "alias_ops_absent_from_planned": {
                    "return_profile_face_bonding": "return_profile_face_bonding" not in priced,
                    "return_profile_machine_forming": "return_profile_machine_forming"
                    not in priced,
                    "PAINTING": "PAINTING" not in {
                        str(t.source_operation_code or "") for t in planned
                    },
                },
                "parent_ops_present": {
                    "side_forming": "side_forming" in priced,
                    "return_face_bonding": "return_face_bonding" in priced,
                    "painting": "painting" in priced,
                },
            },
            "foil_dag": {
                "vinyl_present": vinyl is not None,
                "vinyl_depends_on_task_keys": vinyl_deps,
            },
            "workcenters": wc_map,
            "protected_baselines_before": before,
            "protected_baselines_after": after,
            "protected_unchanged": before == after,
            "dec009": "A",
            "materialize_called": False,
        }
        EVIDENCE.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
        print(json.dumps(evidence, indent=2, default=str))

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
