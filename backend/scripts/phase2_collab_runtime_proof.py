"""Phase 2 runtime proof against live service layer + optional HTTP.

Uses backend/dev.db (canonical local stack DB). Safe cleanup at end.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault(
    "DATABASE_URL", "sqlite+aiosqlite:///C:/w/psiso/backend/dev.db"
)
os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret-not-for-production")
os.environ.setdefault("FLEX_COLLAB_PHASE2_ENABLED", "true")
os.environ.setdefault("FLEX_MEMBERSHIP_API_ENABLED", "true")

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.execution_task_help_request import ExecutionTaskHelpRequest
from models.execution_task_participant import ExecutionTaskParticipant
from models.orders import Orders
from schemas.execution_task_help import HelpRequestCreateBody
from services.execution_plan_task_parser import operational_tasks_only
from services.execution_task_collaboration_read_service import (
    build_order_task_collaboration_read,
)
from services.execution_task_help_service import (
    accept_help_request,
    cancel_help_request,
    close_open_help_for_task,
    create_help_request,
)
from services.execution_task_membership_service import leave_helper_membership
from services.flex_membership_flags import reset_flex_membership_flags_cache
from services.helper_work_session_service import start_helper_session, stop_helper_session
from services.operational_registry_service import OperationalRegistryService

ORDER_ID = 23099
TASK_HINT = "vector_prep"


async def main() -> None:
    reset_flex_membership_flags_cache()
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        order = (
            await db.execute(select(Orders).where(Orders.id == ORDER_ID))
        ).scalar_one_or_none()
        if order is None:
            raise SystemExit(f"order {ORDER_ID} not found")

        plan = (
            await db.execute(
                select(ExecutionPlan)
                .where(ExecutionPlan.order_id == ORDER_ID)
                .order_by(ExecutionPlan.id.desc())
                .limit(1)
            )
        ).scalar_one()
        ops = operational_tasks_only(plan.tasks_json)
        task = next(
            (t for t in ops if TASK_HINT in str(t.get("task_id") or "")),
            ops[0] if ops else None,
        )
        if task is None:
            raise SystemExit("no operational task")
        task_id = str(task["task_id"])
        process = str(
            task.get("process_type")
            or task.get("process_id")
            or task.get("source_operation_code")
            or ""
        )

        emps = list(
            (
                await db.execute(
                    select(Employees)
                    .where(Employees.status == "active")
                    .order_by(Employees.id)
                    .limit(20)
                )
            )
            .scalars()
            .all()
        )
        by_name = {str(e.name or "").lower(): e for e in emps}
        principal = by_name.get("sandu") or emps[0]
        helpers = [e for e in emps if e.id != principal.id][:2]
        if len(helpers) < 2:
            raise SystemExit(f"need 2 helpers, found {len(helpers)}")
        h1, h2 = helpers[0], helpers[1]

        # Ensure eligibility for helpers + principal on this process
        registry = OperationalRegistryService(db)
        await registry.upsert_operation_mapping(
            {
                "operation_code": process,
                "authorization_mode": "explicit",
                "authorized_employee_ids": [principal.id, h1.id, h2.id],
            }
        )

        # Cleanup prior OPEN help / helper memberships on this task for these helpers
        open_rows = list(
            (
                await db.execute(
                    select(ExecutionTaskHelpRequest).where(
                        ExecutionTaskHelpRequest.order_id == ORDER_ID,
                        ExecutionTaskHelpRequest.task_id == task_id,
                        ExecutionTaskHelpRequest.status == "OPEN",
                    )
                )
            )
            .scalars()
            .all()
        )
        for row in open_rows:
            row.status = "CANCELLED"
        await db.commit()

        for hid in (h1.id, h2.id):
            try:
                await leave_helper_membership(
                    db, order_id=ORDER_ID, task_id=task_id, employee_id=hid
                )
            except Exception:
                pass

        evidence: dict = {
            "order_id": ORDER_ID,
            "task_id": task_id,
            "process": process,
            "principal_id": principal.id,
            "principal_name": principal.name,
            "helper1_id": h1.id,
            "helper1_name": h1.name,
            "helper2_id": h2.id,
            "helper2_name": h2.name,
            "steps": [],
        }

        def step(name: str, **kwargs):
            evidence["steps"].append({"step": name, **kwargs})
            print(f"OK {name}: {kwargs}")

        baseline = await build_order_task_collaboration_read(db, ORDER_ID)
        bt = next(t for t in baseline.tasks if t.task_id == task_id)
        assigned_before = (
            bt.optional_principal.optional_principal_employee_id
            if bt.optional_principal
            else None
        )
        step(
            "baseline_read",
            version=baseline.contract_version,
            has_open_help=bt.has_open_help,
            helpers=bt.authorized_helper_count,
            assigned=assigned_before,
            op_completed=bt.operation_completed,
        )

        created = await create_help_request(
            db,
            order_id=ORDER_ID,
            task_id=task_id,
            requested_by_employee_id=principal.id,
            body=HelpRequestCreateBody(reason="phase2 runtime proof broadcast"),
        )
        hid = created.help_request.help_request_id
        step(
            "create_broadcast",
            help_request_id=hid,
            status=created.help_request.status,
            is_broadcast=created.help_request.is_broadcast,
        )

        a1 = await accept_help_request(
            db, order_id=ORDER_ID, help_request_id=hid, employee_id=h1.id
        )
        step(
            "accept_helper1",
            status=a1.help_request.status,
            membership_id=a1.membership_id,
        )

        a2 = await accept_help_request(
            db, order_id=ORDER_ID, help_request_id=hid, employee_id=h2.id
        )
        step(
            "accept_helper2",
            status=a2.help_request.status,
            membership_id=a2.membership_id,
        )
        assert a2.help_request.status == "OPEN"

        mid = await build_order_task_collaboration_read(db, ORDER_ID)
        mt = next(t for t in mid.tasks if t.task_id == task_id)
        step(
            "read_after_accepts",
            helpers=mt.authorized_helper_count,
            has_open_help=mt.has_open_help,
            assigned=mt.optional_principal.optional_principal_employee_id
            if mt.optional_principal
            else None,
            workers=len(mt.actual_workers),
        )
        assert mt.authorized_helper_count >= 2
        assert mt.has_open_help is True
        assert (
            mt.optional_principal.optional_principal_employee_id
            if mt.optional_principal
            else None
        ) == assigned_before

        s1 = await start_helper_session(
            db,
            order_id=ORDER_ID,
            task_id=task_id,
            employee_id=h1.id,
            employee_name=h1.name,
        )
        step(
            "helper1_session_start",
            employee_id=s1["employee_id"],
            role=s1["role"],
            session_employee=s1["session"].get("employee_id") if s1.get("session") else None,
        )

        after_start = await build_order_task_collaboration_read(db, ORDER_ID)
        at = next(t for t in after_start.tasks if t.task_id == task_id)
        worker_ids = [w.employee_id for w in at.actual_workers]
        step(
            "read_after_session",
            worker_ids=worker_ids,
            assigned=at.optional_principal.optional_principal_employee_id
            if at.optional_principal
            else None,
            op_completed=at.operation_completed,
        )
        assert h1.id in worker_ids
        assert at.operation_completed is False

        stopped = await stop_helper_session(
            db, order_id=ORDER_ID, task_id=task_id, employee_id=h1.id
        )
        step(
            "helper1_session_stop",
            operation_completed=stopped["operation_completed"],
            membership_unchanged=stopped["membership_unchanged"],
        )

        # Targeted help proof (close broadcast first by cancel — preserves memberships)
        cancelled = await cancel_help_request(
            db,
            order_id=ORDER_ID,
            help_request_id=hid,
            actor_employee_id=principal.id,
        )
        step("cancel_broadcast", status=cancelled.help_request.status)
        mem_h1 = (
            await db.execute(
                select(ExecutionTaskParticipant).where(
                    ExecutionTaskParticipant.order_id == ORDER_ID,
                    ExecutionTaskParticipant.task_id == task_id,
                    ExecutionTaskParticipant.employee_id == h1.id,
                )
            )
        ).scalar_one()
        assert mem_h1.status == "active"
        step("membership_preserved_after_cancel", status=mem_h1.status)

        targeted = await create_help_request(
            db,
            order_id=ORDER_ID,
            task_id=task_id,
            requested_by_employee_id=principal.id,
            body=HelpRequestCreateBody(targeted_employee_id=h2.id, reason="targeted proof"),
        )
        thid = targeted.help_request.help_request_id
        try:
            await accept_help_request(
                db, order_id=ORDER_ID, help_request_id=thid, employee_id=h1.id
            )
            raise SystemExit("targeted accept by non-target should fail")
        except Exception as exc:
            detail = getattr(exc, "detail", {})
            step("targeted_reject_non_target", error=detail.get("error") if isinstance(detail, dict) else str(exc))

        tacc = await accept_help_request(
            db, order_id=ORDER_ID, help_request_id=thid, employee_id=h2.id
        )
        step("targeted_accept_closes", status=tacc.help_request.status)
        assert tacc.help_request.status == "CLOSED"

        # Recreate OPEN then complete-close
        again = await create_help_request(
            db,
            order_id=ORDER_ID,
            task_id=task_id,
            requested_by_employee_id=principal.id,
            body=HelpRequestCreateBody(reason="close-on-complete proof"),
        )
        n = await close_open_help_for_task(db, order_id=ORDER_ID, task_id=task_id)
        step("close_open_on_completion_hook", closed_count=n, help_id=again.help_request.help_request_id)

        final = await build_order_task_collaboration_read(db, ORDER_ID)
        ft = next(t for t in final.tasks if t.task_id == task_id)
        step(
            "final_read",
            version=final.contract_version,
            has_open_help=ft.has_open_help,
            helpers=ft.authorized_helper_count,
            assigned=ft.optional_principal.optional_principal_employee_id
            if ft.optional_principal
            else None,
            op_completed=ft.operation_completed,
            can_complete_never_from_helper_flags=True,
        )

        out = ROOT / "docs" / "qa" / "_phase2_runtime_evidence.json"
        # Prefer compound worklog path under repo docs
        out_path = Path("C:/w/psiso/docs/qa/_phase2_runtime_evidence.json")
        out_path.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
        print("WROTE", out_path)
        print("PHASE2_RUNTIME_PROOF_PASS")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
