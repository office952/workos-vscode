"""
Execution router — WorkOS Execution Layer v1.

Exposes the six canonical endpoints required by the sprint:

    POST /api/v1/execution/plan/from-order/{order_id}
    GET  /api/v1/execution/plan/{order_id}
    POST /api/v1/execution/reality/start-task
    POST /api/v1/execution/reality/end-task
    GET  /api/v1/execution/reality/{order_id}
    GET  /api/v1/execution/divergence/{order_id}

Hard constraints enforced here:
  - The router does NOT import CostEngine / QuoteOrchestrator /
    ProductSystemService / ProductTemplate / MaterialRate.
  - The router does NOT recalculate prices or costs.
  - Missing data is surfaced as structured HTTP 422 errors.
"""

from __future__ import annotations

import json
import os
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from services.divergence_service import DivergenceService
from services.execution_alert_service import ExecutionAlertService
from services.execution_observability_service import ExecutionObservabilityService
from services.execution_plan_gate_service import (
    GateRegistryReadError,
    RegistrySnapshot,
    classify_writer_http_status,
    evaluate_gate,
)
from schemas.auth import UserResponse
from services.ops_graph_frozen_technical_materials import (
    attach_frozen_technical_materials_to_plan_payload,
)
from services.execution_ops_graph_read_clarity import (
    apply_ops_graph_read_clarity_to_plan_payload,
)
from services.execution_plan_operational_readiness_service import (
    evaluate_execution_plan_operational_readiness,
    readiness_result_to_api_fields,
)
from services.execution_plan_task_parser import parse_tasks_json_raw
from services.execution_plan_v2_guard_service import raise_if_legacy_plan_blocked_for_v2_order
from services.execution_plan_service import (
    ExecutionPlanService,
    SnapshotIncompleteError,
)
from services.execution_task_assignment_service import assign_plan_task
from services.execution_task_instructions_service import update_plan_task_instructions
from services.production_document_handoff_service import (
    attach_documents_to_planned_tasks,
    load_eligible_intake_documents_for_plan,
)
from services.volumetric_execution_dispatch import parse_snapshot_dict
from services.volumetric_return_task_taxonomy_service import (
    apply_volumetric_return_taxonomy_to_plan_tasks,
)
from services.volumetric_conditional_plan_tasks_service import (
    apply_volumetric_conditional_plan_from_snapshot,
    finalize_volumetric_plan_dependencies,
)
from services.execution_reality_service import (
    ExecutionRealityService,
    RealityInputError,
)
from services.product_system_execution_output_service import (
    ProductSystemExecutionPreviewService,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/execution",
    tags=["execution"],
    dependencies=[Depends(get_current_user)],
)


# ---------- Schemas ----------
class StartTaskRequest(BaseModel):
    order_id: int
    task_id: str
    timestamp: str
    override_readiness: bool = False
    override_reason: Optional[str] = None


class EndTaskRequest(BaseModel):
    order_id: int
    task_id: str
    timestamp: str


# ---------- Helpers ----------
async def _get_order_or_404(db: AsyncSession, order_id: int) -> Orders:
    stmt = select(Orders).where(Orders.id == order_id)
    res = await db.execute(stmt)
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})
    return row


async def _get_plan_or_404(db: AsyncSession, order_id: int) -> ExecutionPlan:
    stmt = select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
    res = await db.execute(stmt)
    rows = list(res.scalars().all())
    if not rows:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})
    return sorted(rows, key=lambda r: r.id)[-1]


async def _get_reality_or_404(db: AsyncSession, order_id: int) -> ExecutionReality:
    stmt = select(ExecutionReality).where(ExecutionReality.order_id == order_id)
    res = await db.execute(stmt)
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "reality_not_found"})
    return row


def _plan_row_to_dict(row: ExecutionPlan) -> dict:
    parsed = parse_tasks_json_raw(row.tasks_json)
    tasks = list(parsed.operational_tasks)
    readiness = evaluate_execution_plan_operational_readiness(row)
    payload = {
        "id": row.id,
        "order_id": row.order_id,
        "order_code": row.order_code,
        "snapshot_version": row.snapshot_version,
        "tasks": tasks,
        "total_estimated_time_minutes": row.total_estimated_time_minutes,
        "prepared_by_user_id": getattr(row, "prepared_by_user_id", None),
        **readiness_result_to_api_fields(readiness),
    }
    if parsed.format == "v2_envelope":
        payload["plan_format"] = "v2_envelope"
        payload["execution_tasks_created"] = bool(
            parsed.envelope.get("execution_tasks_created") if parsed.envelope else False
        )
    # Batch 17 Track B — display-only honesty metadata for ops-graph RO review.
    # Does not mutate tasks_json / invent minutes / WC / machine_code / unit.
    return apply_ops_graph_read_clarity_to_plan_payload(payload)


def _reality_row_to_dict(row: ExecutionReality) -> dict:
    try:
        tasks = json.loads(row.tasks_json) if row.tasks_json else []
    except (TypeError, ValueError):
        tasks = []
    try:
        materials = json.loads(row.materials_json) if row.materials_json else []
    except (TypeError, ValueError):
        materials = []
    return {
        "id": row.id,
        "order_id": row.order_id,
        "order_code": row.order_code,
        "tasks": tasks,
        "materials": materials,
        "total_actual_time_minutes": row.total_actual_time_minutes,
    }


# ---------- Gate helpers ----------
async def _read_codes(db: AsyncSession, primary_sql: str, fallback_sql: str) -> Optional[list]:
    """Read canonical codes from an M1/M2 registry table.

    Tries `public.<table>` first (Postgres prod), falls back to `<table>`
    (SQLite / test DBs). Returns None when neither query succeeds, which the
    gate interprets as "registry unavailable" rather than a hard 500.
    """
    from sqlalchemy import text as _sql_text

    for sql in (primary_sql, fallback_sql):
        try:
            rows = (await db.execute(_sql_text(sql))).all()
            return [r[0] for r in rows]
        except Exception:  # noqa: BLE001 - table may not exist in this DB
            # PostgreSQL aborts the current transaction on SQL errors
            # (e.g. missing schema/table). Roll back so the fallback query
            # can run in a clean transaction.
            try:
                await db.rollback()
            except Exception:
                pass
            continue
    return None


async def _load_registry_snapshot(db: AsyncSession) -> RegistrySnapshot:
    """Read-only probe of live M1/M2 registries for the gate.

    Uses raw SQL (the same pattern as services.foundation_registries) so we do
    not introduce any new ORM model. Reads code columns only. Never writes.
    When the M1 tables are unavailable (e.g. SQLite test DB without Foundation
    Registries seeded), the registries are reported as unavailable in
    trace_source; the gate still runs deterministically.
    """
    skills = await _read_codes(
        db,
        "SELECT skill_code FROM public.skills",
        "SELECT skill_code FROM skills",
    )
    workcenters = await _read_codes(
        db,
        "SELECT workcenter_code FROM public.workcenters",
        "SELECT workcenter_code FROM workcenters",
    )
    roles = await _read_codes(
        db,
        "SELECT role_code FROM public.roles",
        "SELECT role_code FROM roles",
    )

    return RegistrySnapshot(
        skills=skills,
        workcenters=workcenters,
        roles=roles,
        product_system_available=settings.registry_productsystem_live,
        materials_registry_available=settings.registry_materials_live,
        machines_registry_available=settings.registry_machines_live,
    )


async def _plan_already_exists(db: AsyncSession, order_id: int) -> bool:
    stmt = select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none() is not None


# ---------- Gate endpoint (pure read-only pre-flight) ----------
@router.get("/plan/gate/{order_id}")
async def gate_plan_from_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Execution Plan Generation Gate — P1 pre-flight (read-only).

    Spec: /workspace/docs/spec/spec__execution_plan_generation_gate.md §19.1
    """
    logger.info(f"GET /api/v1/execution/plan/gate/{order_id}")
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})

    order = await _get_order_or_404(db, order_id)
    plan_exists = await _plan_already_exists(db, order_id)

    try:
        registries = await _load_registry_snapshot(db)
    except GateRegistryReadError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "REGISTRY_READ_FAILURE",
                    "message": "Gate could not read Foundation Registries.",
                    "details": {
                        "registry": exc.registry,
                        "gate_spec_version": "spec__execution_plan_generation_gate.md v1",
                    },
                }
            },
        )

    # _load_registry_snapshot may perform rollback when probing missing
    # registry tables; ensure ORM attributes are loaded in async context
    # before passing row to synchronous gate evaluator.
    await db.refresh(order)

    # S30 wiring: when ProductSystem is live, obtain preview and pass to gate
    productsystem_preview = None
    if registries.product_system_available:
        try:
            preview_service = ProductSystemExecutionPreviewService(db)
            productsystem_preview = await preview_service.preview_for_execution(
                order_id
            )
        except Exception as exc:
            # Graceful degradation: if preview service fails, gate proceeds
            # without preview — WRN-01 will NOT be emitted (flag is true),
            # but BLK-* from ProductSystem won't be available either.
            logger.warning(
                "ProductSystem preview unavailable for order %d: %s — "
                "gate proceeds without preview (graceful degradation)",
                order_id,
                exc,
            )

    evaluation = evaluate_gate(
        order_row=order,
        registries=registries,
        plan_already_exists=plan_exists,
        productsystem_preview=productsystem_preview,
    )
    return evaluation.to_dict()


# ---------- Plan endpoints ----------
def _gate_writer_strict_mode_enabled() -> bool:
    """P1 writer-amendment controlled by config flag.

    spec__execution_plan_generation_gate.md §11.3 mandates that warning-to-
    blocker lifecycle be controlled by config flags, not by code rewrites.
    In P1 the gate is LIVE as a read-only endpoint (always on) but the
    writer amendment that converts a non-structural gate failure into HTTP
    412 is gated behind ``settings.gate_writer_strict`` so legacy callers
    remain byte-compatible until the full operationalization train
    (M19/M22/M24) ships. See acceptance checklist §23 "config flag /
    registry-availability probe".

    Reads from ``settings.gate_writer_strict`` (bool, default True since
    Phase 8 activation 2026-05-09). Falls back to env var
    ``GATE_WRITER_STRICT`` for backward compatibility.
    """
    # Primary: read from Settings (pydantic-settings, supports env override)
    if hasattr(settings, "gate_writer_strict"):
        return bool(settings.gate_writer_strict)
    # Fallback: raw env var (legacy path, pre-Phase 8)
    return os.environ.get("GATE_WRITER_STRICT", "").strip() in ("1", "true", "TRUE", "yes")


@router.post("/plan/from-order/{order_id}", status_code=201)
async def create_plan_from_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    _user=Depends(require_permission("execution.plan_generate")),
):
    logger.info(f"POST /api/v1/execution/plan/from-order/{order_id}")
    order = await _get_order_or_404(db, order_id)
    raise_if_legacy_plan_blocked_for_v2_order(order)

    # --- Gate pre-flight (additive, non-breaking per spec §19.2) ---
    # Only enforce when the writer-strict flag is on. When off we preserve
    # the v1 legacy HTTP surface exactly: 201 / 409 / 422.
    if _gate_writer_strict_mode_enabled():
        plan_exists = await _plan_already_exists(db, order_id)
        try:
            registries = await _load_registry_snapshot(db)
        except GateRegistryReadError as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": "REGISTRY_READ_FAILURE",
                        "message": "Gate could not read Foundation Registries.",
                        "details": {
                            "registry": exc.registry,
                            "gate_spec_version": "spec__execution_plan_generation_gate.md v1",
                        },
                    }
                },
            )
        # Registry probe may rollback to recover from missing public.* tables.
        # Refresh the row so evaluate_gate() does not trigger lazy loads from
        # an expired instance in a sync context.
        await db.refresh(order)
        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=plan_exists,
        )
        if not evaluation.can_generate:
            http_status = classify_writer_http_status(evaluation)
            envelope = evaluation.to_dict()
            if http_status == 409:
                existing_stmt = select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
                existing_res = await db.execute(existing_stmt)
                existing_row = existing_res.scalar_one_or_none()
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "plan_already_exists",
                        "plan_id": existing_row.id if existing_row is not None else None,
                        "gate_envelope": envelope,
                    },
                )
            if http_status == 422:
                first = evaluation.blockers[0] if evaluation.blockers else {}
                details = first.get("details", {}) if isinstance(first, dict) else {}
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "snapshot_incomplete",
                        "field": details.get("field", ""),
                        "message": first.get("message", "snapshot_incomplete"),
                        "gate_envelope": envelope,
                    },
                )
            raise HTTPException(
                status_code=412,
                detail={
                    "error": {
                        "code": "GATE_PRECONDITION_FAILED",
                        "message": "Execution plan generation blocked by the pre-flight gate.",
                        "details": {"gate_envelope": envelope},
                    }
                },
            )

    # Legacy v1 behaviour: writer enforces snapshot-only structural check.
    svc = ExecutionPlanService()
    try:
        dto = svc.from_order(order)
    except SnapshotIncompleteError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "snapshot_incomplete", "field": e.field_path, "message": e.message},
        )

    # Defensive duplicate-check (write-once invariant).
    stmt = select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail={"error": "plan_already_exists", "plan_id": existing.id},
        )

    task_dicts = [t.to_dict() for t in dto.tasks]

    snapshot_dict = parse_snapshot_dict(order.snapshot_line_items)
    task_dicts, conditional_summary = apply_volumetric_conditional_plan_from_snapshot(
        task_dicts,
        snapshot_dict,
        set_face_vinyl_instructions=True,
    )
    if conditional_summary.get("applied"):
        dto.total_estimated_time_minutes = float(
            conditional_summary["total_estimated_time_minutes"]
        )

    task_dicts, _ = apply_volumetric_return_taxonomy_to_plan_tasks(
        task_dicts,
        set_owner_instructions=True,
    )
    task_dicts = finalize_volumetric_plan_dependencies(task_dicts)
    if conditional_summary.get("removed_process_ids"):
        logger.info(
            "Volumetric conditional plan filter order_id=%s removed=%s face_vinyl=%s",
            order_id,
            conditional_summary.get("removed_process_ids"),
            conditional_summary.get("face_vinyl_action"),
        )
    eligible_documents = await load_eligible_intake_documents_for_plan(db, order_id=order.id)
    task_dicts = attach_documents_to_planned_tasks(task_dicts, eligible_documents)

    prepared_by_user_id: Optional[str] = None
    if current_user is not None and current_user.id:
        uid = str(current_user.id).strip()
        if uid:
            prepared_by_user_id = uid

    row = ExecutionPlan(
        order_id=dto.order_id,
        order_code=dto.order_code,
        snapshot_version=dto.snapshot_version,
        tasks_json=json.dumps(task_dicts),
        total_estimated_time_minutes=dto.total_estimated_time_minutes,
        prepared_by_user_id=prepared_by_user_id,
    )

    readiness_snapshot = getattr(order, "readiness_snapshot", None)
    if isinstance(readiness_snapshot, dict):
        patched_readiness_snapshot = dict(readiness_snapshot)
        patched_readiness_snapshot["execution_plan_created"] = True
        patched_readiness_snapshot["no_execution_plan_created"] = False
        order.readiness_snapshot = patched_readiness_snapshot

    db.add(row)
    try:
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to persist execution plan: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail={"error": "plan_persist_failed"})
    await db.refresh(row)
    return _plan_row_to_dict(row)


@router.get("/plan/{order_id}")
async def get_plan(order_id: int, db: AsyncSession = Depends(get_db)):
    row = await _get_plan_or_404(db, order_id)
    payload = _plan_row_to_dict(row)
    # Display-only: attach allowlisted frozen technical materials from Order snapshot.
    # Does not mutate plan envelope, tasks, material_inputs, or snapshot.
    try:
        order = await _get_order_or_404(db, order_id)
        snapshot_v2_json = getattr(order, "snapshot_v2_json", None)
    except HTTPException:
        snapshot_v2_json = None
    return attach_frozen_technical_materials_to_plan_payload(payload, snapshot_v2_json)


class AssignPlanTaskRequest(BaseModel):
    assigned_employee_id: int


@router.patch("/plan/{order_id}/tasks/{task_id}/assign")
async def assign_plan_task_to_employee(
    order_id: int,
    task_id: str,
    body: AssignPlanTaskRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.task_assign")),
):
    """Persist assigned_employee_id on a planned task in execution_plan.tasks_json."""
    return await assign_plan_task(
        db,
        order_id=order_id,
        task_id=task_id,
        assigned_employee_id=body.assigned_employee_id,
        allow_reassign=True,
        assignment_source="manager_assign",
    )


class UpdatePlanTaskInstructionsRequest(BaseModel):
    instructions: str = ""


@router.patch("/plan/{order_id}/tasks/{task_id}/instructions")
async def update_plan_task_instructions_endpoint(
    order_id: int,
    task_id: str,
    body: UpdatePlanTaskInstructionsRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.task_assign")),
):
    """Persist optional manual execution instructions on a planned task."""
    return await update_plan_task_instructions(
        db,
        order_id=order_id,
        task_id=task_id,
        instructions=body.instructions,
    )


# ---------- Reality endpoints ----------
@router.post("/reality/start-task")
async def start_task(
    req: StartTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    _user=Depends(require_permission("execution.task_start")),
):
    from services.task_start_gate_service import assert_task_startable

    order = await _get_order_or_404(db, req.order_id)
    gate = await assert_task_startable(
        db,
        order_id=req.order_id,
        task_id=req.task_id,
        employee_id=None,
        override_readiness=req.override_readiness,
        override_reason=req.override_reason,
        override_user_id=str(current_user.id or ""),
        override_user_name=str(current_user.name or ""),
        override_user_role=str(current_user.role or ""),
    )
    initial_fields: dict[str, Any] = {}
    if gate.get("override_metadata"):
        initial_fields.update(gate["override_metadata"])

    normalized_initial_fields: dict[str, Any] | None = None
    if initial_fields:
        normalized_initial_fields = initial_fields

    svc = ExecutionRealityService(db)
    try:
        row = await svc.start_task(
            order_id=order.id,
            order_code=order.code,
            task_id=req.task_id,
            timestamp=req.timestamp,
            initial_fields=normalized_initial_fields,
        )
    except RealityInputError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "reality_input_invalid", "code": e.code, "detail": e.detail},
        )
    return _reality_row_to_dict(row)


@router.post("/reality/end-task")
async def end_task(
    req: EndTaskRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.task_complete")),
):
    # Validate order exists but don't touch it.
    await _get_order_or_404(db, req.order_id)
    svc = ExecutionRealityService(db)
    try:
        row = await svc.end_task(
            order_id=req.order_id,
            task_id=req.task_id,
            timestamp=req.timestamp,
        )
    except RealityInputError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "reality_input_invalid", "code": e.code, "detail": e.detail},
        )
    return _reality_row_to_dict(row)


@router.get("/reality/{order_id}")
async def get_reality(order_id: int, db: AsyncSession = Depends(get_db)):
    row = await _get_reality_or_404(db, order_id)
    return _reality_row_to_dict(row)


# ---------- Materials Capture endpoints (BUILD SET 3B) ----------
# OBSERVATIONAL ONLY — does NOT update inventory, cost engine, or order.

class MaterialRow(BaseModel):
    material_id: Optional[str] = None
    material_name: Optional[str] = None
    quantity: float
    unit: str
    task_id: Optional[str] = None
    reported_by_employee_id: Optional[int] = None
    reported_by_employee_name: Optional[str] = None
    consumption_notes: Optional[str] = None
    reported_at: Optional[str] = None


class AddMaterialsRequest(BaseModel):
    materials: list[MaterialRow]


class UpdateMaterialRequest(BaseModel):
    material_id: Optional[str] = None
    material_name: Optional[str] = None
    quantity: float
    unit: str
    task_id: Optional[str] = None
    reported_by_employee_id: Optional[int] = None
    reported_by_employee_name: Optional[str] = None
    consumption_notes: Optional[str] = None
    reported_at: Optional[str] = None


@router.post("/reality/{order_id}/materials", status_code=201)
async def add_materials(
    order_id: int,
    req: AddMaterialsRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.materials_add")),
):
    """Add consumed materials to an order's ExecutionReality.

    Observational only — does NOT update inventory or cost engine.
    """
    logger.info(f"POST /api/v1/execution/reality/{order_id}/materials — {len(req.materials)} rows")
    svc = ExecutionRealityService(db)
    try:
        row = await svc.add_materials(
            order_id=order_id,
            materials=[m.model_dump() for m in req.materials],
        )
    except RealityInputError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "material_validation_failed", "code": e.code, "detail": e.detail},
        )
    materials = json.loads(row.materials_json) if row.materials_json else []
    return {"order_id": order_id, "materials": materials, "total_count": len(materials)}


@router.get("/reality/{order_id}/materials")
async def get_materials(order_id: int, db: AsyncSession = Depends(get_db)):
    """Get all captured materials for an order's ExecutionReality."""
    svc = ExecutionRealityService(db)
    try:
        materials = await svc.get_materials(order_id)
    except RealityInputError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "reality_input_invalid", "code": e.code, "detail": e.detail},
        )
    return {"order_id": order_id, "materials": materials, "total_count": len(materials)}


@router.put("/reality/{order_id}/materials/{material_index}")
async def update_material(
    order_id: int,
    material_index: int,
    req: UpdateMaterialRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.materials_update")),
):
    """Update a single material row by index.

    Observational only — does NOT update inventory or cost engine.
    """
    logger.info(f"PUT /api/v1/execution/reality/{order_id}/materials/{material_index}")
    svc = ExecutionRealityService(db)
    try:
        row = await svc.update_material(
            order_id=order_id,
            material_index=material_index,
            updated=req.model_dump(),
        )
    except RealityInputError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "material_validation_failed", "code": e.code, "detail": e.detail},
        )
    materials = json.loads(row.materials_json) if row.materials_json else []
    return {"order_id": order_id, "materials": materials, "total_count": len(materials)}


@router.delete("/reality/{order_id}/materials/{material_index}")
async def remove_material(
    order_id: int,
    material_index: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.materials_delete")),
):
    """Remove a material row by index.

    Observational only — does NOT update inventory or cost engine.
    """
    logger.info(f"DELETE /api/v1/execution/reality/{order_id}/materials/{material_index}")
    svc = ExecutionRealityService(db)
    try:
        row = await svc.remove_material(
            order_id=order_id,
            material_index=material_index,
        )
    except RealityInputError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "material_validation_failed", "code": e.code, "detail": e.detail},
        )
    materials = json.loads(row.materials_json) if row.materials_json else []
    return {"order_id": order_id, "materials": materials, "total_count": len(materials)}


# ---------- Divergence endpoint (read-only) ----------
@router.get("/divergence/{order_id}")
async def get_divergence(order_id: int, db: AsyncSession = Depends(get_db)):
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    svc = DivergenceService(db)
    report = await svc.compare(order_id)
    return report.to_dict()


# ---------- Observability endpoints (Sprint #11, read-only) ----------
# These endpoints NEVER write to Orders / ExecutionPlan / ExecutionReality.
# They derive classification and alerts on demand from the existing rows.

@router.get("/observability/{order_id}")
async def get_observability(order_id: int, db: AsyncSession = Depends(get_db)):
    """Return OK / WARNING / CRITICAL / UNCONFIRMED for an order.

    Read-only. Missing data -> UNCONFIRMED with explicit reasons.
    """
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    svc = ExecutionObservabilityService(db)
    report = await svc.observe(order_id)
    return report.to_dict()


@router.get("/alerts/{order_id}")
async def get_alerts(order_id: int, db: AsyncSession = Depends(get_db)):
    """Return derived alert read-models for an order.

    Empty list when status is OK or UNCONFIRMED. No persistence.
    """
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    obs_report = await ExecutionObservabilityService(db).observe(order_id)
    alerts = ExecutionAlertService().build_alerts(obs_report)
    return {
        "order_id": order_id,
        "order_code": obs_report.order_code,
        "status": obs_report.status,
        "alerts": alerts,
    }


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Read-only dashboard over every order.

    Columns per row:
      - order_id, order_code
      - plan_status: "present" | "absent"
      - reality_status: "present" | "absent"
      - divergence_status: OK | WARNING | CRITICAL | UNCONFIRMED
      - alert_severity: same as divergence_status when WARNING/CRITICAL, else null
      - planned_time, actual_time, delta_time (nullable when data missing)

    Missing data surfaces explicitly; no 0 fallback.
    """
    stmt = select(Orders).order_by(Orders.id.asc())
    res = await db.execute(stmt)
    orders = list(res.scalars().all())

    obs_svc = ExecutionObservabilityService(db)
    alert_svc = ExecutionAlertService()
    rows = []
    for o in orders:
        obs = await obs_svc.observe(o.id)
        alerts = alert_svc.build_alerts(obs)
        alert_severity = alerts[0]["severity"] if alerts else None
        rows.append(
            {
                "order_id": o.id,
                "order_code": o.code,
                "plan_status": "present" if obs.has_plan else "absent",
                "reality_status": "present" if obs.has_reality else "absent",
                "divergence_status": obs.status,
                "alert_severity": alert_severity,
                "planned_time": obs.plan_total_estimated_minutes,
                "actual_time": obs.reality_total_actual_minutes,
                "delta_time": obs.delta_minutes,
            }
        )
    return {"rows": rows, "total": len(rows)}