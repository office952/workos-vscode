"""Isolated Golden Letters V1 E2E final proof runner (live sqlite / services).

Creates a disposable Intake V6 workspace from intake_v6_golden_gradi,
forces EUR-safe mounting (no Forex sell template), optional Oracal face finish,
then walks dry-run → handoff → snapshot → accept → convert → EP preview.

Does not push, does not mutate historical golden id 4888fddb-..., does not
activate Capacity / Phase E / ACM expansion features.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
EVIDENCE = REPO / "docs" / "qa" / "workos-v1-golden-letters-e2e-final-proof"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "intake_v6_golden_gradi"
HISTORICAL_GOLDEN_ID = "4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1"

sys.path.insert(0, str(ROOT))

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ENVIRONMENT", "development")
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./dev.db"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_payload() -> dict:
    payload = json.loads((FIXTURE_DIR / "workspace_payload.golden.json").read_text(encoding="utf-8"))
    payload = deepcopy(payload)
    payload["svg_analysis_json"] = json.loads(
        (FIXTURE_DIR / "svg_analysis_json.json").read_text(encoding="utf-8")
    )
    finish = payload.setdefault("finish_setup", {})
    # Preferred Golden PASS path: no Forex mounting template.
    finish["mounting_template_enabled"] = False
    finish["mounting_template_material_type"] = None
    finish["mounting_template_area_m2"] = None
    finish["mounting_scope"] = "none"
    finish["site_installation_included"] = False
    # Schema allows only product_system_template | installation_template; disable Forex via flags.
    finish["mounting_solution"] = {
        "kind": "installation_template",
        "template_code": None,
        "configuration": {},
    }
    # EUR-native priced finish (commercial currency truth proven path).
    finish["face_finish_type"] = "oracal_8500"
    finish["face_oracal_code"] = "070"
    finish["face_oracal_name"] = "Black"
    finish["face_vinyl_roll_width_mm"] = 1000
    # Snapshot-authoritative V1 freeze applies VAT only on 7G base (no live Adaos).
    # Keep markup/discount at 0 so quote columns match frozen CPP + VAT (Golden PASS path).
    commercial_inputs = finish.setdefault("commercial_inputs", {})
    if isinstance(commercial_inputs, dict):
        commercial_inputs["markup_percent"] = 0.0
        commercial_inputs["discount_percent"] = 0.0
        commercial_inputs["manual_adjustment_ron"] = 0.0
        commercial_inputs["vat_percent"] = 21.0
    for group in finish.get("letter_group_finishes") or []:
        if not isinstance(group, dict):
            continue
        group["face_finish_type"] = "oracal_8500"
        group["face_oracal_code"] = "070"
        group["face_oracal_name"] = "Black"
        group["face_vinyl_roll_width_mm"] = 1000
        group["confirmed"] = True
    finish["confirmed"] = True
    finish["internal_draft_quote_confirmed"] = True
    payload["client"] = {
        "client_name": "Golden Letters E2E Final Proof",
        "job_title": "GOLDEN-LETTERS-V1-FINAL",
        "width_mm": None,
        "height_mm": None,
    }
    payload["source"] = "golden_letters_e2e_final_proof_v1"
    return payload


async def _run() -> dict:
    from models.intake_v6_workspace import IntakeV6WorkspaceRecord
    from core.database import db_manager
    from schemas.auth import UserResponse
    from services.intake_v6_priced_quote_dry_run_service import build_intake_v6_priced_quote_dry_run
    from services.intake_v6_offer_handoff_service import handoff_intake_v6_workspace_to_offer
    from services.intake_v6_quote_snapshot_v2_service import create_v6_quote_snapshot_v2
    from services.intake_v6_quote_to_order_service import accept_v6_quote, convert_v6_quote_to_order
    from services.intake_v6_workspace_service import confirm_job_product_truth_for_workspace
    from services.product_truth_job_confirm_service import (
        commercial_freeze_allowed,
        get_job_revision_metadata,
    )
    from schemas.product_truth_job_confirm import ConfirmJobProductTruthRequest

    report: dict = {
        "started_at": _utc(),
        "verdict": "IN_PROGRESS",
        "first_broken_boundary": None,
        "workspace_id": None,
        "workspace_code": None,
        "steps": {},
    }

    payload = _load_payload()
    workspace_id = str(uuid.uuid4())
    assert workspace_id != HISTORICAL_GOLDEN_ID
    workspace_code = f"IV6-GOLD-FINAL-{workspace_id[:8].upper()}"
    report["workspace_id"] = workspace_id
    report["workspace_code"] = workspace_code
    report["selected_configuration"] = {
        "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "face_finish_type": payload["finish_setup"]["face_finish_type"],
        "return_finish_type": payload["finish_setup"].get("return_finish_type"),
        "return_depth_mm": payload["finish_setup"].get("return_depth_mm"),
        "backing_mode": payload["finish_setup"].get("backing_mode"),
        "illuminated": payload["finish_setup"].get("illuminated"),
        "lighting_system_type": payload["finish_setup"].get("lighting_system_type"),
        "mounting_template_enabled": payload["finish_setup"].get("mounting_template_enabled"),
        "mounting_scope": payload["finish_setup"].get("mounting_scope"),
        "mounting_template_material_type": payload["finish_setup"].get("mounting_template_material_type"),
    }

    user = UserResponse(
        id="golden-e2e-final",
        email="golden-e2e@localhost",
        name="Golden E2E",
        role="admin",
        last_login=None,
    )
    analysis_hash = (
        ((payload.get("svg_source") or {}).get("file_hash"))
        or ((payload.get("path_geometry_summary") or {}).get("sanitization") or {}).get("source_content_hash")
    )

    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        db.add(
            IntakeV6WorkspaceRecord(
                id=workspace_id,
                workspace_code=workspace_code,
                title="Golden Letters E2E Final Proof",
                template_code="TPL-VOLUMETRIC-LETTERS_v2",
                payload_json=json.dumps(payload, ensure_ascii=False),
                status="ready_for_quote_preview",
                readiness_status="ready_for_quote_preview",
            )
        )
        await db.commit()
        report["steps"]["workspace_seed"] = {"ok": True, "analysis_hash": analysis_hash}

        # Operator ConfirmJobProductTruth — required for Snapshot V2 freeze.
        try:
            confirm = await confirm_job_product_truth_for_workspace(
                db,
                workspace_id,
                ConfirmJobProductTruthRequest(
                    expected_revision=0,
                    root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
                ),
                user,
            )
            # Reload payload for freeze check
            from sqlalchemy import select

            rec = (
                await db.execute(
                    select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id)
                )
            ).scalar_one()
            payload_after = json.loads(rec.payload_json or "{}")
            meta = get_job_revision_metadata(payload_after) or {}
            freeze_ok = commercial_freeze_allowed(payload_after)
            report["steps"]["product_truth_confirm"] = {
                "ok": True,
                "write_performed": confirm.get("write_performed"),
                "confirmation_state": (confirm.get("metadata") or {}).get("confirmation_state")
                if isinstance(confirm.get("metadata"), dict)
                else getattr(confirm.get("metadata"), "confirmation_state", None),
                "revision": meta.get("revision"),
                "content_hash": meta.get("content_hash"),
                "commercial_freeze_allowed": freeze_ok,
            }
            if not freeze_ok or str(meta.get("confirmation_state") or "") != "confirmed":
                report["verdict"] = "FAIL_REPAIR_REQUIRED"
                report["first_broken_boundary"] = "Product Truth confirm"
                report["ended_at"] = _utc()
                return report
        except Exception as exc:  # noqa: BLE001
            report["steps"]["product_truth_confirm"] = {"ok": False, "error": str(exc)}
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Product Truth confirm"
            report["ended_at"] = _utc()
            return report

        # ProductDefinition + Aggregate (Golden config only — no architecture audit).
        try:
            from services.product_definition_builder_service import ProductDefinitionBuilderService
            from services.product_aggregate_service import ProductAggregateService

            pd = await ProductDefinitionBuilderService(db).build_preview(
                "TPL-VOLUMETRIC-LETTERS_v2", workspace_id=workspace_id
            )
            agg = await ProductAggregateService(db).build_for_workspace(
                "TPL-VOLUMETRIC-LETTERS_v2", workspace_id
            )
            report["steps"]["product_definition"] = {
                "ok": pd is not None,
                "product_truth_job_revision": getattr(pd, "product_truth_job_revision", None),
                "product_truth_content_hash": getattr(pd, "product_truth_content_hash", None),
                "component_count": len(getattr(pd, "components", None) or getattr(pd, "component_instances", None) or [])
                if pd is not None
                else None,
            }
            report["steps"]["product_aggregate"] = {
                "ok": agg is not None,
                "keys": list(agg.keys())[:30] if isinstance(agg, dict) else type(agg).__name__,
            }
        except Exception as exc:  # noqa: BLE001
            report["steps"]["product_definition"] = {"ok": False, "error": str(exc)}
            report["steps"]["product_aggregate"] = {"ok": False, "error": str(exc)}

        dry = await build_intake_v6_priced_quote_dry_run(db, workspace_id)
        totals = dry.get("commercial_totals") or {}
        lines = dry.get("commercial_line_items") or []
        report["steps"]["cpp_dry_run"] = {
            "pricing_status": dry.get("pricing_status"),
            "authority": dry.get("commercial_authority_status"),
            "currency": totals.get("currency"),
            "total_gross": totals.get("total_gross"),
            "subtotal_net": totals.get("subtotal_net"),
            "vat_amount": totals.get("vat_amount"),
            "line_count": len(lines) if isinstance(lines, list) else None,
            "line_codes": [
                (li.get("code") or li.get("pricing_rule_code") or li.get("description"))
                for li in (lines if isinstance(lines, list) else [])
            ][:40],
            "blockers": [b.get("code") for b in (dry.get("blockers") or [])],
            "can_write_quote_totals": dry.get("can_write_quote_totals"),
        }
        if dry.get("pricing_status") != "V6_PRICED_DRY_RUN_READY" or totals.get("currency") != "EUR":
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "CPP / official commercial dry-run"
            report["ended_at"] = _utc()
            return report
        if totals.get("total_gross") is None:
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "CPP complete_offer_total null"
            report["ended_at"] = _utc()
            return report

        finish_codes = [
            c
            for c in report["steps"]["cpp_dry_run"]["line_codes"]
            if c and ("oracal" in str(c).lower() or "finisaje" in str(c).lower())
        ]
        report["steps"]["cpp_dry_run"]["finish_line_codes"] = finish_codes
        if not finish_codes:
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "selected finish not priced in CPP"
            report["ended_at"] = _utc()
            return report

        try:
            handoff = await handoff_intake_v6_workspace_to_offer(
                db,
                workspace_id,
                client_analysis_hash=analysis_hash,
                expected_total_gross=float(totals["total_gross"]),
                expected_pricing_hash=None,
                operator_confirmation=True,
                current_user=user,
            )
            report["steps"]["handoff"] = {
                "status": handoff.get("status"),
                "quote_id": handoff.get("quote_id"),
                "quote_code": handoff.get("quote_code"),
                "blockers": handoff.get("blockers"),
                "commercial_totals": handoff.get("commercial_totals"),
            }
            quote_id = handoff.get("quote_id")
        except Exception as exc:  # noqa: BLE001
            detail = getattr(exc, "detail", None)
            report["steps"]["handoff"] = {
                "ok": False,
                "error": str(exc),
                "detail": detail,
            }
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Quote handoff"
            report["ended_at"] = _utc()
            return report
        if not quote_id:
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Quote handoff"
            report["ended_at"] = _utc()
            return report

        snap = await create_v6_quote_snapshot_v2(
            db,
            quote_id=int(quote_id),
            workspace_id=workspace_id,
            operator_confirmation=True,
            expected_grand_total=float(totals["total_gross"]),
            expected_pricing_hash=None,
            created_by=user.email,
        )
        report["steps"]["snapshot_v2"] = {
            "status": snap.get("status"),
            "snapshot_id": snap.get("snapshot_id") or snap.get("id"),
            "blockers": snap.get("blockers"),
        }
        if snap.get("blockers"):
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Quote Snapshot V2"
            report["ended_at"] = _utc()
            return report

        # Pricing review + owner approval (canonical V6 spine) before accept.
        try:
            from services.intake_v6_quote_to_order_service import (
                complete_v6_pricing_review,
                persist_v6_owner_approval,
            )

            review = await complete_v6_pricing_review(
                db,
                int(quote_id),
                {
                    "reviewer_confirmation": True,
                    "confirm_quote_stays_draft": True,
                    "confirm_no_order": True,
                    "confirm_no_execution": True,
                    "confirm_no_inventory": True,
                    "pricing_review_reason": "Golden Letters E2E final proof pricing review.",
                    "client_analysis_hash": analysis_hash,
                },
                user,
            )
            report["steps"]["pricing_review"] = {
                "ok": True,
                "pricing_review_completed": review.get("pricing_review_completed"),
                "pricing_totals_source": review.get("pricing_totals_source"),
            }
            approval = await persist_v6_owner_approval(
                db,
                int(quote_id),
                {
                    "decision_reason": "Golden Letters E2E final proof owner approval.",
                    "acknowledged_no_execution_tasks": True,
                    "acknowledged_no_stock_consumption": True,
                    "client_analysis_hash": analysis_hash,
                },
                user,
            )
            report["steps"]["owner_approval"] = {
                "ok": True,
                "keys": list(approval.keys())[:20] if isinstance(approval, dict) else type(approval).__name__,
            }
        except Exception as exc:  # noqa: BLE001 — proof runner records boundary
            detail = getattr(exc, "detail", None)
            report["steps"]["pricing_review"] = {"ok": False, "error": str(exc), "detail": detail}
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Pricing review / owner approval"
            report["ended_at"] = _utc()
            return report

        try:
            from tests.test_quote_snapshot_v2_accept_gate import _valid_accept_body

            accept_body = _valid_accept_body(confirm_owner_decisions_acknowledged=True)
        except Exception:
            accept_body = {
                "accept_reason": "golden_letters_e2e_final_proof",
                "reviewer_confirmation": True,
                "confirm_pricing_review_completed": True,
                "confirm_no_order": True,
                "confirm_no_execution": True,
                "confirm_no_inventory": True,
                "confirm_convert_separate": True,
                "confirm_owner_decisions_acknowledged": True,
            }

        try:
            accept = await accept_v6_quote(db, int(quote_id), accept_body, user)
            report["steps"]["accept"] = {
                "status": accept.get("status") if isinstance(accept, dict) else str(type(accept)),
                "accepted": accept.get("accepted") if isinstance(accept, dict) else None,
                "blockers": accept.get("blockers") if isinstance(accept, dict) else None,
            }
        except Exception as exc:  # noqa: BLE001
            detail = getattr(exc, "detail", None)
            report["steps"]["accept"] = {"ok": False, "error": str(exc), "detail": detail}
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Quote accept"
            report["ended_at"] = _utc()
            return report
        if isinstance(accept, dict) and (accept.get("blockers") or accept.get("accepted") is False):
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Quote accept"
            report["ended_at"] = _utc()
            return report

        try:
            convert = await convert_v6_quote_to_order(
                db,
                int(quote_id),
                {
                    "convert_reason": "golden_letters_e2e_final_proof",
                    "reviewer_confirmation": True,
                    "confirm_quote_accepted": True,
                    "confirm_pricing_review_completed": True,
                    "confirm_create_order_only": True,
                    "confirm_no_execution_plan": True,
                    "confirm_no_execution_tasks": True,
                    "confirm_no_inventory": True,
                    "confirm_production_separate": True,
                },
                user,
            )
            report["steps"]["convert"] = {
                "converted": convert.get("converted"),
                "order_id": convert.get("order_id"),
                "order_code": convert.get("order_code"),
                "blockers": convert.get("blockers"),
                "order_snapshot_v2_convert": convert.get("order_snapshot_v2_convert"),
            }
            order_id = convert.get("order_id")
        except Exception as exc:  # noqa: BLE001
            detail = getattr(exc, "detail", None)
            report["steps"]["convert"] = {"ok": False, "error": str(exc), "detail": detail}
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Order convert"
            report["ended_at"] = _utc()
            return report
        if not convert.get("converted") or not order_id:
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Order convert"
            report["ended_at"] = _utc()
            return report

        # ExecutionPlan V2: preview → persist → materialize operational_tasks[].
        try:
            from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview
            from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
            from services.execution_plan_v2_materialize_service import (
                materialize_execution_plan_v2_operational_tasks,
            )
            from models.execution_plan import ExecutionPlan
            from services.execution_plan_task_parser import operational_tasks_only

            from services.dec009_materialize_gate import (
                close_materialize_pilot_gate,
                open_wave3_controlled_materialize_target,
                register_golden_pilot_materialize_target,
            )

            preview = await build_execution_plan_v2_preview(db, int(order_id))
            persist = await create_execution_plan_v2_from_order(
                db, int(order_id), prepared_by_user_id=user.id
            )
            plan_id = getattr(persist, "execution_plan_id", None)
            if plan_id is None:
                raise RuntimeError("ExecutionPlan persist did not return execution_plan_id")
            # DEC-009=B: temporarily register this Golden order as sole next-dry target
            # (in-process). Restore Wave3 target afterward so live gate is not left open
            # on a disposable Golden order.
            register_golden_pilot_materialize_target(
                order_id=int(order_id),
                plan_id=int(plan_id),
                fixture_id=f"FIX-GOLDEN-LETTERS-E2E-FINAL-{order_id}",
            )
            try:
                mat = await materialize_execution_plan_v2_operational_tasks(db, int(order_id))
            finally:
                try:
                    open_wave3_controlled_materialize_target()
                except Exception:
                    close_materialize_pilot_gate()
            plan_row = (
                await db.execute(
                    select(ExecutionPlan)
                    .where(ExecutionPlan.order_id == int(order_id))
                    .order_by(ExecutionPlan.id.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            tasks = operational_tasks_only(plan_row.tasks_json if plan_row else None)
            report["steps"]["execution_plan"] = {
                "ok": True,
                "preview_status": getattr(preview, "status", None),
                "persist_status": getattr(persist, "persist_status", None)
                or getattr(persist, "status", None),
                "execution_plan_id": plan_id,
                "dec009_registered_fixture": f"FIX-GOLDEN-LETTERS-E2E-FINAL-{order_id}",
                "materialize": {
                    "status": getattr(mat, "status", None) if not isinstance(mat, dict) else mat.get("status"),
                    "operational_task_count": getattr(mat, "operational_tasks_count", None)
                    if not isinstance(mat, dict)
                    else mat.get("operational_task_count"),
                },
                "operational_task_count": len(tasks),
                "task_codes": [
                    (t.get("operation_code") or t.get("code") or t.get("task_key") or t.get("task_id"))
                    for t in tasks
                ][:40],
                "task_ids": [t.get("task_id") for t in tasks if t.get("task_id")][:20],
            }
            if not tasks:
                report["verdict"] = "FAIL_REPAIR_REQUIRED"
                report["first_broken_boundary"] = "ExecutionPlan operational_tasks empty"
                report["ended_at"] = _utc()
                return report
        except Exception as exc:  # noqa: BLE001
            detail = getattr(exc, "detail", None)
            report["steps"]["execution_plan"] = {"ok": False, "error": str(exc), "detail": detail}
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "ExecutionPlan"
            report["ended_at"] = _utc()
            return report

        # Assignment + controlled session → labor actual (first task with eligible employee).
        try:
            from datetime import timedelta

            from services.controlled_employee_assignment_service import (
                assign_operational_task_controlled,
            )
            from services.controlled_task_session_service import (
                end_controlled_task_session,
                start_controlled_task_session,
            )
            from services.employee_eligibility_read_model_service import (
                build_employee_eligibility_read_model,
            )

            eligibility = await build_employee_eligibility_read_model(db, int(order_id))
            task_rows = []
            if isinstance(eligibility, dict):
                task_rows = eligibility.get("tasks") or eligibility.get("task_rows") or []
                if not task_rows and isinstance(eligibility.get("read_model"), dict):
                    task_rows = eligibility["read_model"].get("tasks") or []
            chosen_task_id = None
            chosen_employee_id = None
            for row in task_rows if isinstance(task_rows, list) else []:
                if not isinstance(row, dict):
                    continue
                elig = row.get("eligible_employees") or []
                if elig and row.get("task_id"):
                    chosen_task_id = str(row["task_id"])
                    chosen_employee_id = int(elig[0]["employee_id"])
                    break
            if not chosen_task_id or not chosen_employee_id:
                # Fallback: try each operational task via assignment until one accepts.
                from models.employees import Employees

                emps = list(
                    (
                        await db.execute(
                            select(Employees).where(Employees.status == "active").order_by(Employees.id.asc())
                        )
                    ).scalars().all()
                )
                last_err = None
                for t in tasks:
                    tid = str(t.get("task_id") or "")
                    if not tid:
                        continue
                    for emp in emps:
                        try:
                            assign = await assign_operational_task_controlled(
                                db,
                                order_id=int(order_id),
                                task_id=tid,
                                assigned_employee_id=int(emp.id),
                                actor_user_id=user.id,
                            )
                            chosen_task_id = tid
                            chosen_employee_id = int(emp.id)
                            report["steps"]["assignment"] = {
                                "ok": True,
                                "task_id": tid,
                                "employee_id": int(emp.id),
                                "mode": "fallback_scan",
                                "result_keys": list(assign.keys())[:20] if isinstance(assign, dict) else None,
                            }
                            break
                        except Exception as scan_exc:  # noqa: BLE001
                            last_err = scan_exc
                            continue
                    if chosen_task_id:
                        break
                if not chosen_task_id:
                    raise RuntimeError(f"No eligible employee/task pair: {last_err}")
            else:
                assign = await assign_operational_task_controlled(
                    db,
                    order_id=int(order_id),
                    task_id=chosen_task_id,
                    assigned_employee_id=chosen_employee_id,
                    actor_user_id=user.id,
                )
                report["steps"]["assignment"] = {
                    "ok": True,
                    "task_id": chosen_task_id,
                    "employee_id": chosen_employee_id,
                    "mode": "eligibility_read_model",
                    "result_keys": list(assign.keys())[:20] if isinstance(assign, dict) else None,
                }

            start_at = datetime.now(timezone.utc).replace(microsecond=0)
            clock_state = {"t": start_at}

            def _clock() -> datetime:
                return clock_state["t"]

            started = await start_controlled_task_session(
                db,
                order_id=int(order_id),
                task_id=chosen_task_id,
                employee_id=chosen_employee_id,
                actor_user_id=user.id,
                actor_mode="supervisor",
                clock=_clock,
            )
            clock_state["t"] = start_at + timedelta(minutes=40)
            ended = await end_controlled_task_session(
                db,
                order_id=int(order_id),
                task_id=chosen_task_id,
                employee_id=chosen_employee_id,
                actor_user_id=user.id,
                actor_mode="supervisor",
                clock=_clock,
            )
            report["steps"]["session"] = {
                "ok": True,
                "started": {
                    k: started.get(k)
                    for k in ("session_id", "status", "already_active")
                    if isinstance(started, dict)
                },
                "ended": {
                    k: ended.get(k)
                    for k in ("session_id", "duration_minutes", "already_ended", "task_auto_completed")
                    if isinstance(ended, dict)
                },
            }
            report["steps"]["labor_actual"] = {
                "ok": True,
                "duration_minutes": ended.get("duration_minutes") if isinstance(ended, dict) else None,
                "employee_id": chosen_employee_id,
                "task_id": chosen_task_id,
            }
        except Exception as exc:  # noqa: BLE001
            detail = getattr(exc, "detail", None)
            report["steps"]["assignment"] = report["steps"].get("assignment") or {
                "ok": False,
                "error": str(exc),
                "detail": detail,
            }
            if "session" not in report["steps"]:
                report["steps"]["session"] = {"ok": False, "error": str(exc), "detail": detail}
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Assignment / Session / Labor actual"
            report["ended_at"] = _utc()
            return report

        # Material actual via canonical MaterialActualsService.record_issue.
        try:
            from models.inventory_materials import Inventory_materials
            from services.material_actuals_service import MaterialActualsService

            materials = list(
                (
                    await db.execute(
                        select(Inventory_materials)
                        .where(Inventory_materials.unit_cost.is_not(None))
                        .where(Inventory_materials.stock_current.is_not(None))
                        .order_by(Inventory_materials.id.asc())
                    )
                ).scalars().all()
            )
            material = next(
                (m for m in materials if float(m.stock_current or 0) >= 0.25 and float(m.unit_cost or 0) > 0),
                None,
            )
            if material is None:
                report["steps"]["material_actual"] = {
                    "ok": False,
                    "status": "NOT_APPLICABLE",
                    "reason": "no inventory material with positive stock + unit_cost",
                }
                report["verdict"] = "FAIL_REPAIR_REQUIRED"
                report["first_broken_boundary"] = "Material actual"
                report["ended_at"] = _utc()
                return report
            qty = 0.25
            issued = await MaterialActualsService(db).record_issue(
                order_id=int(order_id),
                material_id=int(material.id),
                quantity=qty,
                unit=str(material.unit or "buc"),
                actor_id=user.email,
                idempotency_key=f"golden-e2e-final:{order_id}:{material.id}",
                task_id=str(chosen_task_id or tasks[0].get("task_id")),
                source_type="manual_material_actual",
                source_id=int(order_id),
                reason="Golden Letters E2E final proof isolated material actual",
            )
            await db.commit()
            report["steps"]["material_actual"] = {
                "ok": True,
                "material_id": int(material.id),
                "quantity": qty,
                "unit_cost": float(material.unit_cost),
                "issue": issued,
            }
        except Exception as exc:  # noqa: BLE001
            report["steps"]["material_actual"] = {"ok": False, "error": str(exc)}
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Material actual"
            report["ended_at"] = _utc()
            return report

        report["steps"]["machine_run"] = {
            "status": "NOT_APPLICABLE",
            "reason": "Golden Letters primary path does not require MachineRun monetary proof for V1",
        }

        # Profitability final read (Policy A).
        try:
            from services.profitability_analysis_service import ProfitabilityAnalysisService

            analysis = await ProfitabilityAnalysisService(db).analyze_order(int(order_id))
            payload = analysis.model_dump() if hasattr(analysis, "model_dump") else (
                analysis if isinstance(analysis, dict) else {"repr": str(analysis)}
            )
            report["steps"]["profitability"] = {
                "ok": True,
                "keys": list(payload.keys())[:40] if isinstance(payload, dict) else None,
                "summary": {
                    k: payload.get(k)
                    for k in list(payload.keys())[:30]
                    if isinstance(payload, dict)
                },
            }
        except Exception as exc:  # noqa: BLE001
            report["steps"]["profitability"] = {"ok": False, "error": str(exc)}
            report["verdict"] = "FAIL_REPAIR_REQUIRED"
            report["first_broken_boundary"] = "Profitability"
            report["ended_at"] = _utc()
            return report

        report["verdict"] = "PARTIAL_CHAIN_OK_UI_AND_EVIDENCE_REMAIN"
        report["quote_id"] = quote_id
        report["order_id"] = order_id
        report["ended_at"] = _utc()
        return report


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    report = asyncio.run(_run())
    out = EVIDENCE / "golden_chain_run.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": report.get("verdict"), "first_broken_boundary": report.get("first_broken_boundary"), "workspace_id": report.get("workspace_id"), "out": str(out)}, ensure_ascii=False))
    return 0 if report.get("verdict") in {"PASS", "PARTIAL_CHAIN_OK_CONTINUE_ACTUALS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
