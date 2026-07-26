"""
Dashboard Stats API — aggregates real DB data for the frontend Dashboard page.

Provides:
  GET /api/v1/dashboard-stats  →  KPIs, job summaries, capacity, alerts, events

G7 operational truth:
  - KPIs carry kind / window / explanation / gapNote so the UI never implies
    calendar/shift util, commercial pricing, or invented completeness.
  - Workcenter load stays mean planned-load completion clamped 0–100.
  - Throughput "today" is UTC calendar day of order.updated_at.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
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

# Shared operator-facing notices (capacity / util boundary — not pricing).
NOTICE_CALENDAR_SHIFT_GAP = (
    "Utilaj calendar/shift: date indisponibile — afișăm load planificat 0–100 pe workcenter "
    "(nu utilizare pe ture/calendar)."
)
NOTICE_CAPACITY_NOT_PRICING = (
    "Capacitate / load planificat — nu pricing comercial, nu cost orar utilaj → tarif client."
)
NOTICE_OTIF_PROXY = (
    "OTIF este proxy slab: fără realitate/deadline clar, comenzile finalizate sunt tratate ca on-time."
)
NOTICE_THROUGHPUT_UTC = (
    "Throughput azi = comenzi completed cu updated_at în ziua calendaristică UTC curentă."
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


def _clamp_pct(value: float) -> int:
    """Bound a percentage to the closed interval [0, 100]."""
    return max(0, min(100, round(value)))


def _kpi(
    *,
    code: str,
    label: str,
    value: float | int,
    unit: str,
    status: str,
    kind: str,
    window: str,
    explanation: str,
    gap_note: str | None = None,
    trend: str = "stable",
    trend_value: float | int = 0,
) -> dict:
    """Build a KPI payload with operational-truth metadata for the frontend."""
    payload = {
        "code": code,
        "label": label,
        "value": value,
        "unit": unit,
        "trend": trend,
        "trendValue": trend_value,
        "status": status,
        "kind": kind,  # actual | planned | derived | proxy | placeholder
        "window": window,
        "explanation": explanation,
    }
    if gap_note:
        payload["gapNote"] = gap_note
    return payload


def _aggregate_workcenter_minutes(
    plans: list,
    realities: list,
    plans_by_order: dict,
) -> dict[str, dict[str, float]]:
    """
    Per-workcenter planned vs completed minutes from operational plan tasks
    and finished reality sessions. Used by capacity bars and machine util KPI.
    """
    workcenters: dict[str, dict[str, float]] = {}
    for p in plans:
        tasks = _plan_operational_tasks(p.tasks_json)
        for t in tasks:
            wc = _task_workcenter_label(t)
            if wc not in workcenters:
                workcenters[wc] = {"total_min": 0.0, "completed_min": 0.0}
            workcenters[wc]["total_min"] += _task_estimated_minutes(t)

    for r in realities:
        tasks = _safe_json_parse(r.tasks_json)
        for t in tasks:
            if not (t.get("ended_at") and t.get("started_at")):
                continue
            order_plan = plans_by_order.get(r.order_id)
            if not order_plan:
                continue
            plan_tasks = _plan_operational_tasks(order_plan.tasks_json)
            for pt in plan_tasks:
                if pt.get("task_id") == t.get("task_id"):
                    wc = _task_workcenter_label(pt)
                    if wc in workcenters:
                        try:
                            actual = float(t.get("actual_minutes") or 0)
                        except (TypeError, ValueError):
                            actual = 0.0
                        workcenters[wc]["completed_min"] += actual
                    break
    return workcenters


def _machine_util_pct(workcenters: dict[str, dict[str, float]]) -> int:
    """
    Machine util KPI as mean workcenter planned-load completion, each WC
    clamped to [0, 100].

    Not wall-clock capacity util (no shift calendar). Prefer this over the
    former global Σactual/Σplanned×100 overrun ratio, which exploded to
    values like 56596% when estimates were sparse.
    """
    loads: list[int] = []
    for data in workcenters.values():
        total = data.get("total_min") or 0
        if total <= 0:
            continue
        completed = data.get("completed_min") or 0
        loads.append(_clamp_pct((completed / total) * 100))
    if not loads:
        return 0
    return round(sum(loads) / len(loads))


def _throughput_today_count(orders: list, now: datetime | None = None) -> int:
    """Count orders completed with updated_at on the current UTC calendar day."""
    ref = now or datetime.now(timezone.utc)
    count = 0
    for o in orders:
        if o.status != "completed" or not o.updated_at:
            continue
        updated = o.updated_at if o.updated_at.tzinfo else o.updated_at.replace(tzinfo=timezone.utc)
        if updated.date() == ref.date():
            count += 1
    return count


def _build_capacity_load(workcenters: dict[str, dict[str, float]]) -> list[dict]:
    """Capacity bars: planned-load 0–100 + planned/actual/overrun minutes (honest labels)."""
    capacity_load: list[dict] = []
    for wc_name, data in workcenters.items():
        planned = float(data.get("total_min") or 0)
        actual = float(data.get("completed_min") or 0)
        load = _clamp_pct((actual / planned * 100) if planned > 0 else 0)
        overrun = max(0.0, actual - planned)
        capacity_load.append({
            "workcenterId": f"wc_{wc_name.lower().replace(' ', '_').replace('/', '_')}",
            "workcenterName": wc_name,
            "loadToday": load,  # legacy key — semantics: planned-load %, not calendar today
            "load7d": load,
            "load30d": load,
            "availableToday": max(100 - load, 0),
            "plannedMinutes": round(planned, 1),
            "actualMinutes": round(actual, 1),
            "overrunMinutes": round(overrun, 1),
            "loadKind": "planned_load",
            "loadLabel": "Load planificat 0–100",
            "window": "lifetime_plan_vs_finished_sessions",
            "explanation": (
                "completed_min / planned_min pe workcenter, clamp 0–100. "
                "Nu este utilizare pe calendar/ture."
            ),
        })
    return capacity_load


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

    # Shared workcenter aggregation for capacity + machine util KPI
    workcenters = _aggregate_workcenter_minutes(plans, realities, plans_by_order)

    # ── Compute KPIs ──
    order_statuses = Counter(o.status for o in orders)
    active_statuses = {"created", "confirmed", "locked", "in_execution"}
    active_jobs = sum(order_statuses.get(s, 0) for s in active_statuses)
    blocked_jobs = sum(1 for o in orders if o.status == "in_execution" and o.id in realities_by_order
                       and _has_blocked_tasks(realities_by_order[o.id]))

    # Throughput Today: completed orders whose updated_at falls on UTC today
    # (not lifetime completed count — that mislabeled "Today" and inflated the KPI).
    throughput_today = _throughput_today_count(orders)

    # OTIF: percentage of completed orders that were delivered on time (weak proxy)
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
    otif_pct = _clamp_pct((on_time / total_with_deadline * 100) if total_with_deadline > 0 else 0)

    # Machine util: mean workcenter planned-load (0–100), not global overrun ratio
    machine_util = _machine_util_pct(workcenters)

    # Average lead time (days) from order creation to completion
    lead_times = []
    for o in orders:
        if o.status == "completed" and o.created_at and o.updated_at:
            delta = (o.updated_at - o.created_at).total_seconds() / 86400
            if delta > 0:
                lead_times.append(delta)
    avg_lead_time = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0

    # Rework rate: no durable rework signal in DB — keep explicit placeholder
    rework_rate = 0.0

    # Queue time: average age of orders still in pre-execution / active pipeline
    queue_times = []
    for o in orders:
        if o.status in active_statuses and o.created_at:
            now = datetime.now(timezone.utc)
            created = o.created_at if o.created_at.tzinfo else o.created_at.replace(tzinfo=timezone.utc)
            delta_min = (now - created).total_seconds() / 60
            queue_times.append(delta_min)
    avg_queue = round(sum(queue_times) / len(queue_times)) if queue_times else 0

    planned_min_total = round(sum(d.get("total_min") or 0 for d in workcenters.values()), 1)
    actual_min_total = round(sum(d.get("completed_min") or 0 for d in workcenters.values()), 1)
    overrun_min_total = round(max(0.0, actual_min_total - planned_min_total), 1)

    kpis = [
        _kpi(
            code="KPI_ACTIVE_JOBS",
            label="Job-uri în pipeline",
            value=active_jobs,
            unit="",
            status="good" if active_jobs < 12 else "warning",
            kind="actual",
            window="open_orders",
            explanation=(
                "Comenzi cu status created/confirmed/locked/in_execution "
                "(pipeline operațional, nu doar în execuție pe hall)."
            ),
        ),
        _kpi(
            code="KPI_BLOCKED_JOBS",
            label="Blocate (execuție)",
            value=blocked_jobs,
            unit="",
            status="critical" if blocked_jobs >= 3 else "warning" if blocked_jobs >= 1 else "good",
            kind="actual",
            window="in_execution_with_blocked_tasks",
            explanation="Comenzi in_execution cu cel puțin un task reality.blocked=true.",
        ),
        _kpi(
            code="KPI_THROUGHPUT",
            label="Throughput azi (UTC)",
            value=throughput_today,
            unit="jobs",
            status="good" if throughput_today >= 3 else "warning",
            kind="actual",
            window="utc_calendar_today",
            explanation=NOTICE_THROUGHPUT_UTC,
        ),
        _kpi(
            code="KPI_OTIF",
            label="OTIF (proxy)",
            value=otif_pct,
            unit="%",
            status="good" if otif_pct >= 90 else "warning" if otif_pct >= 80 else "critical",
            kind="proxy",
            window="completed_with_promised_delivery",
            explanation=NOTICE_OTIF_PROXY,
            gap_note="Nu există semnal OTIF durabil pe livrare reală vs promised_delivery.",
        ),
        _kpi(
            code="KPI_REWORK_RATE",
            label="Rework Rate",
            value=rework_rate,
            unit="%",
            status="good" if rework_rate < 3 else "warning" if rework_rate < 6 else "critical",
            kind="placeholder",
            window="none",
            explanation="Placeholder — nu există semnal durable de rework în DB.",
            gap_note="Valoare 0 nu înseamnă zero rework; datele lipsesc.",
        ),
        _kpi(
            code="KPI_MACHINE_UTIL",
            label="Load planificat WC",
            value=machine_util,
            unit="%",
            status="good" if machine_util >= 50 else "warning",
            kind="derived",
            window="lifetime_plan_vs_finished_sessions",
            explanation=(
                "Media pe workcenter a (actual_min / planned_min), fiecare WC clamp 0–100. "
                "NU este utilizare utilaj pe calendar/ture."
            ),
            gap_note=NOTICE_CALENDAR_SHIFT_GAP,
        ),
        _kpi(
            code="KPI_LEAD_TIME",
            label="Lead time mediu",
            value=avg_lead_time,
            unit="days",
            status="good" if avg_lead_time <= 3 else "warning" if avg_lead_time <= 4 else "critical",
            kind="derived",
            window="completed_created_to_updated",
            explanation="Medie zile între created_at și updated_at pentru comenzi completed.",
        ),
        _kpi(
            code="KPI_QUEUE_TIME",
            label="Vârstă medie coadă",
            value=avg_queue,
            unit="min",
            status="good" if avg_queue <= 45 else "warning" if avg_queue <= 60 else "critical",
            kind="derived",
            window="open_pipeline_age",
            explanation=(
                "Vârsta medie (minute) a comenzilor încă în pipeline "
                "(created→in_execution), de la created_at până acum."
            ),
        ),
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

    # ── Capacity load (same workcenter aggregation as machine util KPI) ──
    capacity_load = _build_capacity_load(workcenters)

    # If no capacity data from plans, provide default workcenters (zero load — honest empty)
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
                "plannedMinutes": 0,
                "actualMinutes": 0,
                "overrunMinutes": 0,
                "loadKind": "planned_load",
                "loadLabel": "Load planificat 0–100",
                "window": "no_plan_data",
                "explanation": "Fără planuri operaționale — load 0 (nu înseamnă idle calendar).",
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
        throughput_trend.append({"date": day_str, "value": count, "window": "utc_calendar_day"})

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
        "operationalTruth": {
            "plannedMinutesTotal": planned_min_total,
            "actualMinutesTotal": actual_min_total,
            "overrunMinutesTotal": overrun_min_total,
            "throughputWindow": "utc_calendar_today",
            "workcenterLoadKind": "planned_load_0_100",
            "calendarShiftUtilAvailable": False,
            "notices": [
                NOTICE_CALENDAR_SHIFT_GAP,
                NOTICE_CAPACITY_NOT_PRICING,
                NOTICE_THROUGHPUT_UTC,
                NOTICE_OTIF_PROXY,
            ],
            "boundaries": {
                "pricing": "Dashboard does not compute or display client tariffs.",
                "hrCost": "No HR cost → client tariff on Dashboard.",
                "machines": "Load is planned-load %, not machine hourly rate.",
                "executionPlan": "Reads ExecutionPlan/Reality only — no materialization.",
                "productSystem": "No ProductDefinition / ProductAggregate ownership.",
            },
        },
    }


def _has_blocked_tasks(reality: ExecutionReality) -> bool:
    """Check if a reality record has any blocked tasks."""
    tasks = _safe_json_parse(reality.tasks_json)
    return any(t.get("blocked") for t in tasks)
