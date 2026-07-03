"""
Dashboard Stats API — aggregates real DB data for the frontend Dashboard page.

Provides:
  GET /api/v1/dashboard-stats  →  KPIs, job summaries, capacity, alerts, events
"""

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from models.orders import Orders
from models.quotes import Quotes
from models.intake_requests import Intake_requests
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.execution_plan_task_parser import operational_tasks_only

router = APIRouter(
    prefix="/api/v1/dashboard-stats",
    tags=["dashboard-stats"],
    dependencies=[Depends(get_current_user)],
)


def _safe_json_parse(val):
    """Safely parse execution_reality.tasks_json (flat session list)."""
    if not val:
        return []
    import json
    try:
        parsed = json.loads(val)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _plan_operational_tasks(tasks_json: str | None) -> list:
    """Operational plan tasks via shared parser — V2 envelope safe, no planned_tasks fallback."""
    return operational_tasks_only(tasks_json)


def _task_workcenter_label(task: dict) -> str:
    return str(
        task.get("workcenter")
        or task.get("machine_type")
        or task.get("workcenter_code")
        or "Unknown"
    )


def _task_operation_label(task: dict) -> str:
    op = task.get("operation_code") or task.get("process_type") or task.get("process_id")
    return str(op) if op else "—"


def _task_estimated_minutes(task: dict) -> float:
    raw = task.get("estimated_minutes")
    if raw is None:
        raw = task.get("estimated_time_minutes")
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


@router.get("")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate real DB data into the shape the Dashboard frontend expects."""

    # ── Fetch all orders ──
    res = await db.execute(select(Orders).order_by(Orders.id.asc()))
    orders = list(res.scalars().all())

    # ── Fetch all quotes ──
    res_q = await db.execute(select(Quotes).order_by(Quotes.id.asc()))
    quotes = list(res_q.scalars().all())

    # ── Fetch all intakes ──
    res_i = await db.execute(select(Intake_requests).order_by(Intake_requests.id.asc()))
    intakes = list(res_i.scalars().all())

    # ── Fetch execution plans ──
    res_p = await db.execute(select(ExecutionPlan))
    plans = list(res_p.scalars().all())
    plans_by_order = {p.order_id: p for p in plans}

    # ── Fetch execution realities ──
    res_r = await db.execute(select(ExecutionReality))
    realities = list(res_r.scalars().all())
    realities_by_order = {r.order_id: r for r in realities}

    # ── Compute KPIs ──
    order_statuses = Counter(o.status for o in orders)
    active_statuses = {"created", "confirmed", "locked", "in_execution"}
    active_jobs = sum(order_statuses.get(s, 0) for s in active_statuses)
    blocked_jobs = sum(1 for o in orders if o.status == "in_execution" and o.id in realities_by_order
                       and _has_blocked_tasks(realities_by_order[o.id]))
    completed_jobs = order_statuses.get("completed", 0)

    # Throughput: completed orders (proxy for jobs completed today)
    throughput_today = completed_jobs

    # OTIF: percentage of completed orders that were delivered on time
    on_time = 0
    total_with_deadline = 0
    for o in orders:
        if o.status == "completed" and o.promised_delivery:
            total_with_deadline += 1
            # Simple check: if order was completed, assume on-time unless we have reality data
            if o.id in realities_by_order:
                reality = realities_by_order[o.id]
                if reality.total_actual_time_minutes and o.id in plans_by_order:
                    plan = plans_by_order[o.id]
                    if reality.total_actual_time_minutes <= plan.total_estimated_time_minutes * 1.1:
                        on_time += 1
                    # else: late
                else:
                    on_time += 1  # No data = assume on time
            else:
                on_time += 1
    otif_pct = round((on_time / total_with_deadline * 100) if total_with_deadline > 0 else 0)

    # Machine utilization: derive from execution plans/realities
    total_planned = sum(p.total_estimated_time_minutes for p in plans)
    total_actual = sum(r.total_actual_time_minutes for r in realities if r.total_actual_time_minutes)
    machine_util = round((total_actual / total_planned * 100) if total_planned > 0 else 0)

    # Average lead time (days) from order creation to completion
    lead_times = []
    for o in orders:
        if o.status == "completed" and o.created_at and o.updated_at:
            delta = (o.updated_at - o.created_at).total_seconds() / 86400
            if delta > 0:
                lead_times.append(delta)
    avg_lead_time = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0

    # Revenue: sum of total_amount for all orders
    total_revenue = sum(float(o.total_amount or 0) for o in orders)

    # Rework rate: orders that went back from in_execution (proxy - use 0 if no data)
    rework_rate = 0.0

    # Queue time: average time orders spend in 'created' or 'confirmed' status
    queue_times = []
    for o in orders:
        if o.status in active_statuses and o.created_at:
            now = datetime.now(timezone.utc)
            created = o.created_at if o.created_at.tzinfo else o.created_at.replace(tzinfo=timezone.utc)
            delta_min = (now - created).total_seconds() / 60
            queue_times.append(delta_min)
    avg_queue = round(sum(queue_times) / len(queue_times)) if queue_times else 0

    kpis = [
        {"code": "KPI_ACTIVE_JOBS", "label": "Active Jobs", "value": active_jobs, "unit": "",
         "trend": "stable", "trendValue": 0, "status": "good" if active_jobs < 12 else "warning"},
        {"code": "KPI_BLOCKED_JOBS", "label": "Blocked", "value": blocked_jobs, "unit": "",
         "trend": "stable", "trendValue": 0,
         "status": "critical" if blocked_jobs >= 3 else "warning" if blocked_jobs >= 1 else "good"},
        {"code": "KPI_THROUGHPUT", "label": "Throughput Today", "value": throughput_today, "unit": "jobs",
         "trend": "stable", "trendValue": 0,
         "status": "good" if throughput_today >= 3 else "warning"},
        {"code": "KPI_OTIF", "label": "OTIF", "value": otif_pct, "unit": "%",
         "trend": "stable", "trendValue": 0,
         "status": "good" if otif_pct >= 90 else "warning" if otif_pct >= 80 else "critical"},
        {"code": "KPI_REWORK_RATE", "label": "Rework Rate", "value": rework_rate, "unit": "%",
         "trend": "stable", "trendValue": 0,
         "status": "good" if rework_rate < 3 else "warning" if rework_rate < 6 else "critical"},
        {"code": "KPI_MACHINE_UTIL", "label": "Machine Util.", "value": machine_util, "unit": "%",
         "trend": "stable", "trendValue": 0,
         "status": "good" if machine_util >= 50 else "warning"},
        {"code": "KPI_LEAD_TIME", "label": "Avg Lead Time", "value": avg_lead_time, "unit": "days",
         "trend": "stable", "trendValue": 0,
         "status": "good" if avg_lead_time <= 3 else "warning" if avg_lead_time <= 4 else "critical"},
        {"code": "KPI_QUEUE_TIME", "label": "Avg Queue", "value": avg_queue, "unit": "min",
         "trend": "stable", "trendValue": 0,
         "status": "good" if avg_queue <= 45 else "warning" if avg_queue <= 60 else "critical"},
    ]

    # ── Build execution jobs list from orders ──
    execution_jobs = []
    for o in orders:
        if o.status in ("cancelled",):
            continue
        plan = plans_by_order.get(o.id)
        reality = realities_by_order.get(o.id)

        # Map order status to job status
        status_map = {
            "created": "pending",
            "confirmed": "scheduled",
            "locked": "scheduled",
            "in_execution": "in_progress",
            "completed": "completed",
        }
        job_status = status_map.get(o.status, "pending")

        # Compute progress
        progress = 0
        ops_completed = 0
        ops_total = 0
        current_op = "—"
        current_wc = "—"

        if plan:
            tasks = _plan_operational_tasks(plan.tasks_json)
            ops_total = len(tasks)
            if reality:
                reality_tasks = _safe_json_parse(reality.tasks_json)
                completed_task_ids = {t.get("task_id") for t in reality_tasks if t.get("ended_at")}
                ops_completed = len(completed_task_ids)
                # Find current task (started but not ended)
                for rt in reality_tasks:
                    if rt.get("started_at") and not rt.get("ended_at"):
                        # Find matching plan task
                        for pt in tasks:
                            if pt.get("task_id") == rt.get("task_id"):
                                current_op = _task_operation_label(pt)
                                current_wc = _task_workcenter_label(pt)
                                break
                progress = round((ops_completed / ops_total * 100) if ops_total > 0 else 0)
            elif o.status == "completed":
                progress = 100
                ops_completed = ops_total

        is_blocked = False
        risk_level = "none"
        risk_reason = None
        if reality:
            reality_tasks = _safe_json_parse(reality.tasks_json)
            for rt in reality_tasks:
                if rt.get("blocked"):
                    is_blocked = True
                    risk_level = "high"
                    risk_reason = rt.get("block_reason", "Blocat")
                    break

        is_late = False
        if o.promised_delivery and o.status not in ("completed", "cancelled"):
            try:
                promised = datetime.fromisoformat(o.promised_delivery.replace("Z", "+00:00")) if "T" in o.promised_delivery else datetime.strptime(o.promised_delivery, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > promised:
                    is_late = True
                    if risk_level == "none":
                        risk_level = "medium"
                        risk_reason = "Termen depășit"
            except Exception:
                pass

        execution_jobs.append({
            "id": o.job_id or f"JOB-{o.id:04d}",
            "orderId": o.code,
            "client": o.client_name,
            "product": o.product_summary or "—",
            "productType": "general",
            "status": job_status,
            "priority": "normal",
            "promisedAt": o.promised_delivery or "—",
            "productionDeadline": o.promised_delivery or "—",
            "currentOperation": current_op,
            "currentWorkcenter": current_wc,
            "progress": progress,
            "isLate": is_late,
            "isBlocked": is_blocked,
            "riskLevel": risk_level,
            "riskReason": risk_reason,
            "operationsTotal": ops_total,
            "operationsCompleted": ops_completed,
        })

    # ── Capacity load (derived from execution plans) ──
    workcenters = {}
    for p in plans:
        tasks = _plan_operational_tasks(p.tasks_json)
        for t in tasks:
            wc = _task_workcenter_label(t)
            if wc not in workcenters:
                workcenters[wc] = {"total_min": 0, "completed_min": 0}
            workcenters[wc]["total_min"] += _task_estimated_minutes(t)

    for r in realities:
        tasks = _safe_json_parse(r.tasks_json)
        for t in tasks:
            if t.get("ended_at") and t.get("started_at"):
                # Find workcenter from plan
                order_plan = plans_by_order.get(r.order_id)
                if order_plan:
                    plan_tasks = _plan_operational_tasks(order_plan.tasks_json)
                    for pt in plan_tasks:
                        if pt.get("task_id") == t.get("task_id"):
                            wc = _task_workcenter_label(pt)
                            if wc in workcenters:
                                workcenters[wc]["completed_min"] += t.get("actual_minutes", 0)

    capacity_load = []
    for wc_name, data in workcenters.items():
        load = round((data["completed_min"] / data["total_min"] * 100) if data["total_min"] > 0 else 0)
        capacity_load.append({
            "workcenterId": f"wc_{wc_name.lower().replace(' ', '_').replace('/', '_')}",
            "workcenterName": wc_name,
            "loadToday": min(load, 100),
            "load7d": min(load, 100),
            "load30d": min(load, 100),
            "availableToday": max(100 - load, 0),
        })

    # If no capacity data from plans, provide default workcenters
    if not capacity_load:
        default_wcs = ["Print", "Laminare", "Cut / Plotter", "CNC", "Metal / Sudură", "Asamblare", "Electric", "Ambalare"]
        for wc in default_wcs:
            capacity_load.append({
                "workcenterId": f"wc_{wc.lower().replace(' ', '_').replace('/', '_')}",
                "workcenterName": wc,
                "loadToday": 0,
                "load7d": 0,
                "load30d": 0,
                "availableToday": 100,
            })

    # ── Alerts (derived from execution data) ──
    alerts = []
    alert_id = 1
    for o in orders:
        if o.status == "in_execution":
            reality = realities_by_order.get(o.id)
            if reality:
                reality_tasks = _safe_json_parse(reality.tasks_json)
                for rt in reality_tasks:
                    if rt.get("blocked"):
                        alerts.append({
                            "id": f"ALR-{alert_id:03d}",
                            "severity": "critical",
                            "code": "ALRT_TASK_BLOCKED",
                            "message": f"{o.code} — {rt.get('block_reason', 'Task blocat')}",
                            "entityType": "job",
                            "entityId": o.job_id or f"JOB-{o.id:04d}",
                            "jobId": o.job_id,
                            "workcenterId": None,
                            "machineId": None,
                            "triggeredAt": rt.get("blocked_at", datetime.now(timezone.utc).isoformat()),
                            "resolvedAt": None,
                        })
                        alert_id += 1

        # Late delivery alert
        if o.promised_delivery and o.status not in ("completed", "cancelled"):
            try:
                promised = datetime.fromisoformat(o.promised_delivery.replace("Z", "+00:00")) if "T" in o.promised_delivery else datetime.strptime(o.promised_delivery, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > promised:
                    alerts.append({
                        "id": f"ALR-{alert_id:03d}",
                        "severity": "warning",
                        "code": "ALRT_DEADLINE_RISK",
                        "message": f"{o.code} ({o.client_name}) — termen depășit",
                        "entityType": "job",
                        "entityId": o.job_id or f"JOB-{o.id:04d}",
                        "jobId": o.job_id,
                        "workcenterId": None,
                        "machineId": None,
                        "triggeredAt": datetime.now(timezone.utc).isoformat(),
                        "resolvedAt": None,
                    })
                    alert_id += 1
            except Exception:
                pass

    # ── Throughput trend (last 7 days from order completion dates) ──
    now = datetime.now(timezone.utc)
    throughput_trend = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%b %d")
        count = 0
        for o in orders:
            if o.status == "completed" and o.updated_at:
                updated = o.updated_at if o.updated_at.tzinfo else o.updated_at.replace(tzinfo=timezone.utc)
                if updated.date() == day.date():
                    count += 1
        throughput_trend.append({"date": day_str, "value": count})

    # ── Recent events (from order/quote activity) ──
    events = []
    evt_id = 1
    all_entities = []
    for o in orders:
        if o.updated_at:
            all_entities.append(("Orders", o.code, o.status, o.updated_at, o.client_name))
    for q in quotes:
        if q.updated_at:
            all_entities.append(("Quotes", q.code, q.status, q.updated_at, q.client_name))
    for i in intakes:
        if i.updated_at:
            all_entities.append(("WI", i.code, i.status, i.updated_at, i.client_name))

    all_entities.sort(key=lambda x: x[3] if x[3] else datetime.min, reverse=True)
    for etype, code, status, updated, client in all_entities[:10]:
        ts = updated.strftime("%H:%M") if updated else "—"
        events.append({
            "id": f"EVT-{evt_id:03d}",
            "type": f"{status.upper()}",
            "module": etype,
            "entityId": code,
            "message": f"{code} ({client}) — {status}",
            "timestamp": ts,
        })
        evt_id += 1

    return {
        "kpis": kpis,
        "executionJobs": execution_jobs,
        "capacityLoad": capacity_load,
        "alerts": alerts,
        "throughputTrend": throughput_trend,
        "recentEvents": events,
        "source": "db",
        "orderCount": len(orders),
        "quoteCount": len(quotes),
        "intakeCount": len(intakes),
    }


def _has_blocked_tasks(reality: ExecutionReality) -> bool:
    """Check if a reality record has any blocked tasks."""
    tasks = _safe_json_parse(reality.tasks_json)
    return any(t.get("blocked") for t in tasks)