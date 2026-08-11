"""Deterministic synthetic Atoms demo seed for an isolated demo SQLite DB.

Wipe-and-rebuild is owned by scripts/demo-bootstrap.ps1.
This module NEVER targets backend/dev.db (fail-closed via demo.db_guard).

Does NOT run run_golden_letters_e2e_final_proof_v1.py.
Extracts finish/payload semantics from intake_v6_golden_gradi only.
Skips seed_operational_workforce_registry (real-name / pay leakage).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from demo.db_guard import DemoDbGuardError, ensure_demo_database_url_env  # noqa: E402

FIXTURE_DIR = _BACKEND_ROOT / "tests" / "fixtures" / "intake_v6_golden_gradi"
HISTORICAL_GOLDEN_ID = "4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1"

DEMO_WORKSPACE_COMPLETE_ID = "d0e10001-0000-4000-8000-000000000001"
DEMO_WORKSPACE_DRAFT_ID = "d0e10002-0000-4000-8000-000000000002"
DEMO_WORKSPACE_COMPLETE_CODE = "DEMO-INTAKE-LETTERS-001"
DEMO_WORKSPACE_DRAFT_CODE = "DEMO-INTAKE-DRAFT-001"
DEMO_QUOTE_CODE = "DEMO-QUOTE-EUR-001"
DEMO_ORDER_CODE = "DEMO-ORDER-001"

logger = logging.getLogger("seed_atoms_demo_v1")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_letters_payload(*, client_name: str, job_title: str, source: str) -> dict:
    payload = json.loads((FIXTURE_DIR / "workspace_payload.golden.json").read_text(encoding="utf-8"))
    payload = deepcopy(payload)
    payload["svg_analysis_json"] = json.loads(
        (FIXTURE_DIR / "svg_analysis_json.json").read_text(encoding="utf-8")
    )
    finish = payload.setdefault("finish_setup", {})
    finish["mounting_template_enabled"] = False
    finish["mounting_template_material_type"] = None
    finish["mounting_template_area_m2"] = None
    finish["mounting_scope"] = "none"
    finish["site_installation_included"] = False
    finish["mounting_solution"] = {
        "kind": "installation_template",
        "template_code": None,
        "configuration": {},
    }
    finish["face_finish_type"] = "oracal_8500"
    finish["face_oracal_code"] = "070"
    finish["face_oracal_name"] = "Black"
    finish["face_vinyl_roll_width_mm"] = 1000
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
        "client_name": client_name,
        "job_title": job_title,
        "width_mm": None,
        "height_mm": None,
    }
    payload["source"] = source
    return payload


async def _run_registry_seeds_without_workforce() -> dict[str, Any]:
    """Compose existing seed_sync_all steps minus real-name workforce registry."""
    from scripts.seed_sync_all import SEED_PIPELINE

    results: dict[str, Any] = {}
    for name, seed_fn in SEED_PIPELINE:
        if name == "operational_workforce_registry":
            results[name] = {"skipped": True, "reason": "synthetic_demo_employees_only"}
            continue
        if name == "cleanup_retired_product_templates":
            # Fresh demo DB may lack legacy audit tables probed by cleanup; skip safely.
            results[name] = {"skipped": True, "reason": "demo_fresh_db_skip_retired_cleanup"}
            continue
        t0 = time.perf_counter()
        print(f"[seed_atoms_demo] registry >>> {name}", flush=True)
        stats = await seed_fn()
        results[name] = {**(stats or {}), "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2)}
        print(f"[seed_atoms_demo] registry <<< {name}: {stats}", flush=True)

    try:
        from seeds.seed_intake_v6_unified_pricing import seed_intake_v6_unified_pricing

        t0 = time.perf_counter()
        stats = await seed_intake_v6_unified_pricing()
        results["intake_v6_unified_pricing"] = {
            **(stats or {}),
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    except Exception as exc:  # noqa: BLE001
        results["intake_v6_unified_pricing"] = {"ok": False, "error": str(exc)}
        logger.warning("seed_intake_v6_unified_pricing failed (continuing): %s", exc)

    return results


async def _seed_company_commercial_settings(db) -> dict[str, Any]:
    """Explicit demo FX + VAT — never rely on Settings GET inventing 5.0."""
    from services.company_commercial_settings_service import (
        DEFAULT_EUR_TO_RON_RATE,
        DEFAULT_VAT_PCT,
        CompanyCommercialSettingsService,
        ensure_eur_to_ron_column_explicit,
    )

    await ensure_eur_to_ron_column_explicit(db)
    data = await CompanyCommercialSettingsService(db).update_settings(
        default_vat_pct=DEFAULT_VAT_PCT,
        eur_to_ron_rate=DEFAULT_EUR_TO_RON_RATE,
    )
    return {
        "default_vat_pct": data["default_vat_pct"],
        "eur_to_ron_rate": data["eur_to_ron_rate"],
        "demo_fx_explicitly_seeded": True,
    }


async def _seed_synthetic_clients(db) -> list[dict[str, Any]]:
    from models.clients import Clients
    from sqlalchemy import select

    specs = [
        ("DEMO-CLIENT-001", "Demo Client Alpha", "company", "demo-alpha@example.invalid", True),
        ("DEMO-CLIENT-002", "Demo Client Beta", "company", "demo-beta@example.invalid", True),
        ("DEMO-CLIENT-003", "Demo Client Gamma Incomplete", "person", None, False),
        ("DEMO-CLIENT-004", "Demo Client Delta", "company", "demo-delta@example.invalid", True),
    ]
    out: list[dict[str, Any]] = []
    for temp_ref, name, identity, email, complete in specs:
        existing = (
            await db.execute(select(Clients).where(Clients.temp_ref == temp_ref))
        ).scalar_one_or_none()
        if existing is None:
            row = Clients(
                name=name,
                identity_type=identity,
                temp_ref=temp_ref,
                email=email,
                contact_person="Demo Contact" if complete else None,
                phone=None,
                address=None,
                city="Demo City" if complete else None,
                notes="SYNTHETIC_ATOMS_DEMO — not a real client",
            )
            db.add(row)
            await db.flush()
            out.append({"temp_ref": temp_ref, "id": row.id, "name": name})
        else:
            out.append({"temp_ref": temp_ref, "id": existing.id, "name": existing.name})
    await db.commit()
    return out


async def _seed_synthetic_employees(db) -> list[dict[str, Any]]:
    """Synthetic operators + registry eligibility — no real names, no pay amounts."""
    from copy import deepcopy

    from models.employees import Employees
    from seeds.seed_operational_workforce_registry import (
        OPERATION_MAPPINGS,
        REAL_RESOURCES,
    )
    from services.employees import EmployeesService
    from services.operational_registry_service import OperationalRegistryService
    from sqlalchemy import select

    # Cover CNC / cant / assembly / LED / vinyl letter ops without real identities.
    demo_employees = [
        {
            "code": "DEMO-EMP-CNC-001",
            "name": "Demo Operator CNC",
            "role": "Demo CNC Operator",
            "skill_codes": [
                "SK_CNC_OPERATOR",
                "SK_CNC_PREP",
                "SK_LETTER_CANT_OPERATOR",
                "SK_CUTTER_OPERATOR",
            ],
            "workcenter_codes": ["WC_CNC_ROUTING", "WC_LETTER_FORMING", "WC_CUT"],
            "resource_codes": ["MCH-CNC-4020", "MCH-CNC-CANT-LITERE", "MCH-CUTTER-PLOTTER"],
        },
        {
            "code": "DEMO-EMP-ASSEMBLY-001",
            "name": "Demo Assembler",
            "role": "Demo Assembler",
            "skill_codes": [
                "SK_ASSEMBLY",
                "SK_VINYL_APPLICATOR",
                "SK_ELECTRICIAN",
                "SK_FIELD_INSTALLER",
                "SK_LETTER_MODELING",
                "SK_LOCKSMITH",
            ],
            "workcenter_codes": [
                "WC_ASSEMBLY",
                "WC_LED_ASSEMBLY",
                "WC_VINYL_APPLICATION",
                "WC_FIELD_INSTALLATION",
                "WC_METAL_FAB",
                "WC_LETTER_FORMING",
            ],
            "resource_codes": [
                "WA-ASSEMBLY-01",
                "WA-ASSEMBLY-02",
                "MCH-CNC-CANT-LITERE",
                "MCH-RIGID-FILM-LAMINATOR",
            ],
        },
        {
            "code": "DEMO-EMP-FINISH-001",
            "name": "Demo Finisher",
            "role": "Demo Finisher",
            "skill_codes": [
                "SK_VINYL_APPLICATOR",
                "SK_ASSEMBLY",
                "SK_PRINT_OPERATOR",
                "SK_LAMINATOR_OPERATOR",
                "SK_GRAPHIC_DESIGN",
                "SK_QUOTING",
            ],
            "workcenter_codes": [
                "WC_VINYL_APPLICATION",
                "WC_ASSEMBLY",
                "WC_PRINT",
                "WC_LAMINATE",
                "WC_PREPRESS",
            ],
            "resource_codes": [
                "MCH-EPSON-60800",
                "MCH-LAMINATOR-XPRO",
                "MCH-RIGID-FILM-LAMINATOR",
                "WA-ASSEMBLY-01",
            ],
        },
    ]

    emp_svc = EmployeesService(db)
    reg_svc = OperationalRegistryService(db)
    name_to_id: dict[str, int] = {}
    out: list[dict[str, Any]] = []

    for spec in demo_employees:
        existing = (
            await db.execute(select(Employees).where(Employees.name == spec["name"]))
        ).scalar_one_or_none()
        payload = {
            "name": spec["name"],
            "role": spec["role"],
            "department": "Demo Atelier",
            "status": "active",
            "employee_type": "productive",
            "cost_lunar_firma": None,
            "monthly_internal_pay_amount": None,
            "salary_currency": "RON",
            "salary_period": "monthly",
            "observatii": spec["code"],
            "skills": json.dumps(spec["skill_codes"], ensure_ascii=False),
            "machines": json.dumps(spec["resource_codes"], ensure_ascii=False),
        }
        if existing is None:
            row = await emp_svc.create(payload)
        else:
            row = await emp_svc.update(existing.id, payload)
        await reg_svc.set_employee_authorizations(
            row.id,
            skill_codes=spec["skill_codes"],
            workcenter_codes=spec["workcenter_codes"],
            resource_codes=spec["resource_codes"],
        )
        name_to_id[spec["name"]] = int(row.id)
        out.append({"code": spec["code"], "id": int(row.id), "name": spec["name"]})

    for res in REAL_RESOURCES:
        demo_res = deepcopy(res)
        demo_res["name"] = f"Demo {res['name']}"
        demo_res["description"] = "SYNTHETIC_ATOMS_DEMO resource"
        await reg_svc.upsert_resource(demo_res)

    # Map every operation to all demo productive employees (eligibility for Letters UX).
    all_demo_ids = list(name_to_id.values())
    for mapping in OPERATION_MAPPINGS:
        payload = dict(mapping)
        payload.pop("authorized_employee_names", None)
        payload["authorized_employee_ids"] = list(all_demo_ids)
        await reg_svc.upsert_operation_mapping(payload)

    await db.commit()
    return out


async def _upsert_workspace(
    db,
    *,
    workspace_id: str,
    workspace_code: str,
    title: str,
    payload: dict,
    status: str,
) -> None:
    from models.intake_v6_workspace import IntakeV6WorkspaceRecord
    from sqlalchemy import select

    assert workspace_id != HISTORICAL_GOLDEN_ID
    existing = (
        await db.execute(
            select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id)
        )
    ).scalar_one_or_none()
    body = json.dumps(payload, ensure_ascii=False)
    if existing is None:
        db.add(
            IntakeV6WorkspaceRecord(
                id=workspace_id,
                workspace_code=workspace_code,
                title=title,
                template_code="TPL-VOLUMETRIC-LETTERS_v2",
                payload_json=body,
                status=status,
                readiness_status=status,
            )
        )
    else:
        existing.workspace_code = workspace_code
        existing.title = title
        existing.payload_json = body
        existing.status = status
        existing.readiness_status = status
    await db.commit()


async def _seed_complete_commercial_chain(db, summary: dict[str, Any]) -> None:
    from schemas.auth import UserResponse
    from schemas.product_truth_job_confirm import ConfirmJobProductTruthRequest
    from services.intake_v6_offer_handoff_service import handoff_intake_v6_workspace_to_offer
    from services.intake_v6_priced_quote_dry_run_service import build_intake_v6_priced_quote_dry_run
    from services.intake_v6_quote_snapshot_v2_service import create_v6_quote_snapshot_v2
    from services.intake_v6_quote_to_order_service import (
        accept_v6_quote,
        complete_v6_pricing_review,
        convert_v6_quote_to_order,
        persist_v6_owner_approval,
    )
    from services.intake_v6_workspace_service import confirm_job_product_truth_for_workspace
    from sqlalchemy import select

    from models.intake_v6_workspace import IntakeV6WorkspaceRecord

    user = UserResponse(
        id="atoms-demo-admin",
        email="atoms-demo@example.invalid",
        name="Atoms Demo Admin",
        role="admin",
        last_login=None,
    )
    workspace_id = DEMO_WORKSPACE_COMPLETE_ID
    rec = (
        await db.execute(
            select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id)
        )
    ).scalar_one()
    payload = json.loads(rec.payload_json or "{}")
    analysis_hash = (
        ((payload.get("svg_source") or {}).get("file_hash"))
        or ((payload.get("path_geometry_summary") or {}).get("sanitization") or {}).get(
            "source_content_hash"
        )
    )

    await confirm_job_product_truth_for_workspace(
        db,
        workspace_id,
        ConfirmJobProductTruthRequest(
            expected_revision=0,
            root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        ),
        user,
    )

    dry = await build_intake_v6_priced_quote_dry_run(db, workspace_id)
    totals = dry.get("commercial_totals") or {}
    if dry.get("pricing_status") != "V6_PRICED_DRY_RUN_READY" or totals.get("currency") != "EUR":
        raise RuntimeError(f"CPP dry-run not EUR-ready: {dry.get('pricing_status')} {totals}")
    if totals.get("total_gross") is None:
        raise RuntimeError("CPP complete_offer_total null")

    handoff = await handoff_intake_v6_workspace_to_offer(
        db,
        workspace_id,
        client_analysis_hash=analysis_hash,
        expected_total_gross=float(totals["total_gross"]),
        expected_pricing_hash=None,
        operator_confirmation=True,
        current_user=user,
    )
    quote_id = handoff.get("quote_id")
    if not quote_id:
        raise RuntimeError(f"Handoff failed: {handoff}")

    try:
        from models.quotes import Quotes

        q = await db.get(Quotes, int(quote_id))
        if q is not None:
            q.code = DEMO_QUOTE_CODE
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not set DEMO quote code: %s", exc)

    snap = await create_v6_quote_snapshot_v2(
        db,
        quote_id=int(quote_id),
        workspace_id=workspace_id,
        operator_confirmation=True,
        expected_grand_total=float(totals["total_gross"]),
        expected_pricing_hash=None,
        created_by=user.email,
    )
    if snap.get("blockers"):
        raise RuntimeError(f"Snapshot blockers: {snap.get('blockers')}")

    await complete_v6_pricing_review(
        db,
        int(quote_id),
        {
            "reviewer_confirmation": True,
            "confirm_quote_stays_draft": True,
            "confirm_no_order": True,
            "confirm_no_execution": True,
            "confirm_no_inventory": True,
            "pricing_review_reason": "Atoms demo synthetic pricing review.",
            "client_analysis_hash": analysis_hash,
        },
        user,
    )
    await persist_v6_owner_approval(
        db,
        int(quote_id),
        {
            "decision_reason": "Atoms demo synthetic owner approval.",
            "acknowledged_no_execution_tasks": True,
            "acknowledged_no_stock_consumption": True,
            "client_analysis_hash": analysis_hash,
        },
        user,
    )

    accept_body = {
        "accept_reason": "atoms_demo_v1",
        "reviewer_confirmation": True,
        "confirm_pricing_review_completed": True,
        "confirm_no_order": True,
        "confirm_no_execution": True,
        "confirm_no_inventory": True,
        "confirm_convert_separate": True,
        "confirm_owner_decisions_acknowledged": True,
    }
    accept = await accept_v6_quote(db, int(quote_id), accept_body, user)
    if isinstance(accept, dict) and (accept.get("blockers") or accept.get("accepted") is False):
        raise RuntimeError(f"Accept failed: {accept}")

    convert = await convert_v6_quote_to_order(
        db,
        int(quote_id),
        {
            "convert_reason": "atoms_demo_v1",
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
    order_id = convert.get("order_id")
    if not convert.get("converted") or not order_id:
        raise RuntimeError(f"Convert failed: {convert}")

    try:
        from models.orders import Orders

        order = await db.get(Orders, int(order_id))
        if order is not None:
            order.code = DEMO_ORDER_CODE
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not set DEMO order code: %s", exc)

    summary["quote"] = {
        "id": int(quote_id),
        "code_target": DEMO_QUOTE_CODE,
        "currency": totals.get("currency"),
        "total_gross": totals.get("total_gross"),
        "subtotal_net": totals.get("subtotal_net"),
        "vat_amount": totals.get("vat_amount"),
        "runtime_code": handoff.get("quote_code"),
    }
    summary["order"] = {
        "id": int(order_id),
        "code_target": DEMO_ORDER_CODE,
        "runtime_code": convert.get("order_code"),
    }

    await _seed_execution_actuals(db, user=user, order_id=int(order_id), summary=summary)


async def _seed_execution_actuals(db, *, user, order_id: int, summary: dict[str, Any]) -> None:
    from models.execution_plan import ExecutionPlan
    from services.dec009_materialize_gate import (
        close_materialize_pilot_gate,
        open_wave3_controlled_materialize_target,
        register_golden_pilot_materialize_target,
    )
    from services.execution_plan_task_parser import operational_tasks_only
    from services.execution_plan_v2_materialize_service import (
        materialize_execution_plan_v2_operational_tasks,
    )
    from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
    from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview
    from sqlalchemy import select

    await build_execution_plan_v2_preview(db, int(order_id))
    persist = await create_execution_plan_v2_from_order(
        db, int(order_id), prepared_by_user_id=user.id
    )
    plan_id = getattr(persist, "execution_plan_id", None)
    if plan_id is None:
        raise RuntimeError("ExecutionPlan persist missing id")

    register_golden_pilot_materialize_target(
        order_id=int(order_id),
        plan_id=int(plan_id),
        fixture_id=f"FIX-ATOMS-DEMO-{order_id}",
    )
    try:
        await materialize_execution_plan_v2_operational_tasks(db, int(order_id))
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
    summary["execution"] = {
        "plan_id": int(plan_id),
        "operational_task_count": len(tasks),
        "task_ids": [t.get("task_id") for t in tasks if t.get("task_id")][:20],
    }
    if not tasks:
        summary["execution"]["warning"] = "no_operational_tasks"
        return

    from models.employees import Employees
    from models.inventory_materials import Inventory_materials
    from services.controlled_employee_assignment_service import assign_operational_task_controlled
    from services.controlled_task_session_service import (
        end_controlled_task_session,
        start_controlled_task_session,
    )
    from services.material_actuals_service import MaterialActualsService
    from services.profitability_actual_read_model_service import (
        ProfitabilityActualReadModelService,
    )

    emps = list(
        (
            await db.execute(
                select(Employees).where(Employees.status == "active").order_by(Employees.id.asc())
            )
        )
        .scalars()
        .all()
    )
    chosen_task_id = None
    chosen_employee_id = None
    for t in tasks:
        tid = str(t.get("task_id") or "")
        if not tid:
            continue
        for emp in emps:
            try:
                await assign_operational_task_controlled(
                    db,
                    order_id=int(order_id),
                    task_id=tid,
                    assigned_employee_id=int(emp.id),
                    actor_user_id=user.id,
                )
                chosen_task_id = tid
                chosen_employee_id = int(emp.id)
                break
            except Exception:
                continue
        if chosen_task_id:
            break

    if not chosen_task_id or not chosen_employee_id:
        summary["assignment"] = {"ok": False, "error": "no_eligible_pair"}
        return

    start_at = datetime.now(timezone.utc).replace(microsecond=0)
    clock_state = {"t": start_at}

    def _clock() -> datetime:
        return clock_state["t"]

    await start_controlled_task_session(
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
    summary["assignment"] = {
        "ok": True,
        "task_id": chosen_task_id,
        "employee_id": chosen_employee_id,
        "session_minutes": ended.get("duration_minutes") if isinstance(ended, dict) else 40,
    }

    try:
        # Prefer Oracal 8500 (Letters finish); otherwise any priced material.
        preferred = (
            await db.execute(
                select(Inventory_materials).where(Inventory_materials.code == "MAT-ORACAL-8500")
            )
        ).scalar_one_or_none()
        materials = list(
            (
                await db.execute(
                    select(Inventory_materials)
                    .where(Inventory_materials.unit_cost.is_not(None))
                    .order_by(Inventory_materials.id.asc())
                )
            )
            .scalars()
            .all()
        )
        material = preferred if preferred is not None else (materials[0] if materials else None)
        if material is not None:
            if material.unit_cost is None or float(material.unit_cost) <= 0:
                material.unit_cost = 20.0
                material.currency = material.currency or "EUR"
            material.stock_current = max(float(material.stock_current or 0), 10.0)
            await db.commit()
            await db.refresh(material)
        if material is None:
            summary["material_actual"] = {"ok": False, "error": "no_priced_material"}
        else:
            issued = await MaterialActualsService(db).record_issue(
                order_id=int(order_id),
                material_id=int(material.id),
                quantity=0.25,
                unit=str(material.unit or "buc"),
                actor_id=user.email,
                idempotency_key=f"atoms-demo:{order_id}:{material.id}",
                task_id=str(chosen_task_id),
                source_type="manual_material_actual",
                source_id=int(order_id),
                reason="Atoms demo synthetic material actual",
            )
            await db.commit()
            summary["material_actual"] = {
                "ok": True,
                "material_id": int(material.id),
                "material_code": getattr(material, "code", None),
                "quantity": 0.25,
                "unit_cost": float(material.unit_cost),
                "issue_keys": list(issued.keys())[:20] if isinstance(issued, dict) else None,
            }
    except Exception as exc:  # noqa: BLE001
        summary["material_actual"] = {"ok": False, "error": str(exc)}

    try:
        rm = await ProfitabilityActualReadModelService(db).build(int(order_id))
        summary["profitability"] = {
            "ok": True,
            "keys": list(rm.keys())[:30] if isinstance(rm, dict) else type(rm).__name__,
            "labor_cost_status": (rm or {}).get("labor_cost_status") if isinstance(rm, dict) else None,
            "known_actual_cost": (rm or {}).get("known_actual_cost") if isinstance(rm, dict) else None,
        }
    except Exception as exc:  # noqa: BLE001
        summary["profitability"] = {"ok": False, "error": str(exc)}


async def run_atoms_demo_seed() -> dict[str, Any]:
    db_path = ensure_demo_database_url_env()
    summary: dict[str, Any] = {
        "started_at": _utc(),
        "demo_db_path": str(db_path),
        "verdict": "IN_PROGRESS",
    }

    import models  # noqa: F401 — register metadata (includes intake_v6)
    from core.database import Base, db_manager

    await db_manager.ensure_initialized()
    # Fresh demo DB: ensure ORM tables exist even if create_tables short-circuits
    # after init_db (runtime create_all excludes Alembic-owned; full metadata
    # create_all fills gaps for models not yet covered by applied migrations).
    try:
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # noqa: BLE001
        logger.warning("metadata.create_all: %s", exc)

    summary["registry"] = await _run_registry_seeds_without_workforce()

    # Re-ensure after registries (some seeds open their own sessions).
    try:
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # noqa: BLE001
        logger.warning("metadata.create_all (post-registry): %s", exc)

    async with db_manager.async_session_maker() as db:
        summary["commercial_settings"] = await _seed_company_commercial_settings(db)
        summary["clients"] = await _seed_synthetic_clients(db)
        summary["employees"] = await _seed_synthetic_employees(db)

        complete_payload = _load_letters_payload(
            client_name="Demo Client Alpha",
            job_title="DEMO-LETTERS-COMPLETE",
            source="atoms_demo_v1",
        )
        await _upsert_workspace(
            db,
            workspace_id=DEMO_WORKSPACE_COMPLETE_ID,
            workspace_code=DEMO_WORKSPACE_COMPLETE_CODE,
            title="Demo Letters Complete (Atoms)",
            payload=complete_payload,
            status="ready_for_quote_preview",
        )

        draft_payload = _load_letters_payload(
            client_name="Demo Client Gamma Incomplete",
            job_title="DEMO-LETTERS-DRAFT",
            source="atoms_demo_v1_draft",
        )
        draft_payload["finish_setup"]["confirmed"] = False
        draft_payload["finish_setup"]["internal_draft_quote_confirmed"] = False
        await _upsert_workspace(
            db,
            workspace_id=DEMO_WORKSPACE_DRAFT_ID,
            workspace_code=DEMO_WORKSPACE_DRAFT_CODE,
            title="Demo Letters Draft (Atoms)",
            payload=draft_payload,
            status="draft",
        )
        summary["intake"] = {
            "complete": {
                "id": DEMO_WORKSPACE_COMPLETE_ID,
                "code": DEMO_WORKSPACE_COMPLETE_CODE,
            },
            "draft": {
                "id": DEMO_WORKSPACE_DRAFT_ID,
                "code": DEMO_WORKSPACE_DRAFT_CODE,
            },
        }

        await _seed_complete_commercial_chain(db, summary)

    summary["verdict"] = "PASS"
    summary["ended_at"] = _utc()
    summary["synthetic"] = True
    summary["historical_golden_mutated"] = False
    return summary


async def _main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        ensure_demo_database_url_env()
    except DemoDbGuardError as exc:
        print(f"[seed_atoms_demo] GUARD_FAIL: {exc}", flush=True)
        return 2

    try:
        summary = await run_atoms_demo_seed()
    except Exception as exc:  # noqa: BLE001
        logger.exception("seed_atoms_demo FAILED: %s", exc)
        print(f"[seed_atoms_demo] FAILED: {exc}", flush=True)
        return 1

    out_path = _BACKEND_ROOT / "demo" / "last_seed_summary.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
    print(f"[seed_atoms_demo] wrote {out_path}", flush=True)
    print("[seed_atoms_demo] OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
