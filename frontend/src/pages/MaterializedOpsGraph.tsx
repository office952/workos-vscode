/**
 * MaterializedOpsGraph — Capacity Batch 15 Track B.
 *
 * READ-ONLY admin/operator surface over already-materialized V2 operational
 * tasks. Prefer fixture FIX-DEC009-MAT-01 (order 973010 / plan 12).
 *
 * MUST NOT: start / stop / assign / complete · Employee Mobile · POST materialize.
 * Null / owner-accepted gaps render as "—" + warning chips — never invented zeros.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Gauge,
  Info,
  Network,
  RefreshCw,
} from "lucide-react";
import {
  executionApi,
  type ExecutionPlanResponse,
  type ExecutionPlanV2MaterializationAuditResponse,
  type ExecutionRealityResponse,
  type PlannedTaskRow,
} from "@/api/execution";
import FlowBreadcrumb from "@/components/workos/FlowBreadcrumb";
import { ExecutionPlanStatesStrip } from "@/components/execution/ExecutionPlanStatesStrip";
import {
  MetricTile,
  DataTableWrapper,
  OwnerGoNotice,
  chromeBanner,
} from "@/components/workos/design-system";
import { useDashboardStats } from "@/hooks/useDashboardStats";

/** Canonical Batch 15 fixture — display default only; not invented data. */
export const FIX_DEC009_MAT_01_ORDER_ID = 973010;
export const FIX_DEC009_MAT_01_LABEL = "FIX-DEC009-MAT-01";

function displayText(value: string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  return value;
}

function displayMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value}`;
}

function nullFieldWarnings(task: PlannedTaskRow): string[] {
  const out: string[] = [];
  if (task.estimated_time_minutes === null || task.estimated_time_minutes === undefined) {
    out.push("estimated_time_minutes=null");
  }
  if (task.planning_minutes_source === null || task.planning_minutes_source === undefined) {
    out.push("planning_minutes_source=null");
  }
  if (task.machine_code === null || task.machine_code === undefined || task.machine_code === "") {
    out.push("machine_code=null (owner-accepted / CAP-012 gap)");
  }
  if (task.workcenter === null || task.workcenter === undefined || task.workcenter === "") {
    out.push("workcenter=null (F7 OD1 owner-accepted)");
  }
  if (task.assigned_employee_id === null || task.assigned_employee_id === undefined) {
    out.push("assigned_employee_id=null");
  }
  for (const w of task.warnings ?? []) {
    if (w && !out.includes(w)) out.push(w);
  }
  return out;
}

function parseOrderId(raw: string | null): number {
  if (!raw) return FIX_DEC009_MAT_01_ORDER_ID;
  const n = Number(raw);
  if (!Number.isInteger(n) || n <= 0) return FIX_DEC009_MAT_01_ORDER_ID;
  return n;
}

export default function MaterializedOpsGraph() {
  const [searchParams, setSearchParams] = useSearchParams();
  const orderId = parseOrderId(searchParams.get("orderId"));
  const { capacityModel, operationalTruth } = useDashboardStats();
  const preMat = capacityModel?.preMaterializeChecklist;
  const batch04 = operationalTruth?.capacityBatch04;
  const dec009 = preMat?.dec009 ?? batch04?.dec009 ?? "—";
  const materializeState = preMat?.materialize ?? batch04?.materialize ?? "BLOCKED";

  const [plan, setPlan] = useState<ExecutionPlanResponse | null>(null);
  const [audit, setAudit] = useState<ExecutionPlanV2MaterializationAuditResponse | null>(null);
  const [reality, setReality] = useState<ExecutionRealityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [orderInput, setOrderInput] = useState(String(orderId));

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [planResult, auditResult, realityResult] = await Promise.allSettled([
        executionApi.getExecutionPlan(orderId),
        executionApi.getExecutionPlanV2MaterializationAudit(orderId),
        executionApi.getReality(orderId),
      ]);

      if (planResult.status === "rejected") {
        throw planResult.reason instanceof Error
          ? planResult.reason
          : new Error("plan_load_failed");
      }

      setPlan(planResult.value);
      setAudit(auditResult.status === "fulfilled" ? auditResult.value : null);
      setReality(realityResult.status === "fulfilled" ? realityResult.value : null);

      if (auditResult.status === "rejected" && realityResult.status === "rejected") {
        // Plan alone is enough for the ops list; soft-warn via banner below.
      }
    } catch (e) {
      setPlan(null);
      setAudit(null);
      setReality(null);
      setError(e instanceof Error ? e.message : "unknown error");
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setOrderInput(String(orderId));
  }, [orderId]);

  const tasks = plan?.tasks ?? [];
  const taskCount =
    plan?.operational_tasks_count ??
    audit?.operational_tasks_in_envelope_count ??
    tasks.length;
  /** Sessions: only assert 0 when audit loaded and guards.creates_sessions is false. */
  const sessionsCount =
    audit == null
      ? null
      : audit.guards?.creates_sessions === true
        ? null
        : 0;
  /** Actuals: reality null (404) or empty tasks ⇒ 0 observed rows — not invented plan metrics. */
  const actualsCount = reality?.tasks?.length ?? 0;
  const actualsLabel =
    reality === null && !loading && plan != null ? 0 : actualsCount;
  const hasOperationalTasks = taskCount > 0;
  const isFixture =
    orderId === FIX_DEC009_MAT_01_ORDER_ID ||
    plan?.order_code === "ORD-FIX-DEC009-MAT-01";

  const sortedTasks = useMemo(() => {
    return [...tasks].sort((a, b) => {
      const sa = a.sequence_index ?? Number.MAX_SAFE_INTEGER;
      const sb = b.sequence_index ?? Number.MAX_SAFE_INTEGER;
      if (sa !== sb) return sa - sb;
      return a.task_id.localeCompare(b.task_id);
    });
  }, [tasks]);

  const applyOrderId = () => {
    const next = parseOrderId(orderInput.trim());
    setSearchParams(next === FIX_DEC009_MAT_01_ORDER_ID ? {} : { orderId: String(next) });
  };

  const isAuthError =
    error &&
    (error.includes("401") ||
      error.includes("403") ||
      error.toLowerCase().includes("unauthorized") ||
      error.toLowerCase().includes("forbidden") ||
      error.toLowerCase().includes("auth"));
  const isNetworkError =
    error &&
    (error.includes("fetch") ||
      error.includes("network") ||
      error.includes("ECONNREFUSED") ||
      error.includes("Failed to fetch"));

  return (
    <div className="space-y-4" data-testid="materialized-ops-graph-page">
      <FlowBreadcrumb
        items={[
          { label: "Comenzi", to: "/orders" },
          { label: "Producție", to: "/execution" },
          { label: "Ops graph (read-only)", active: true },
        ]}
      />

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-wo-info" />
          <h1 className="text-[18px] font-bold text-wo-text-primary">
            Materialized operational task graph
          </h1>
          <span className="text-[10px] text-wo-text-muted bg-wo-surface-inset border border-wo-border-subtle px-2 py-0.5 rounded-full">
            read-only
          </span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Link
            to="/execution"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium rounded-md bg-wo-surface-raised hover:bg-wo-hover text-wo-text-primary border border-wo-border-strong transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Execution
          </Link>
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold rounded-md border border-wo-info/40 bg-wo-info-muted text-wo-info hover:bg-wo-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            data-testid="ops-graph-refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      <div
        className={`rounded-lg px-3 py-2 space-y-2 ${chromeBanner.neutral}`}
        data-testid="ops-graph-fixture-identity"
      >
        <p className="text-[11px] font-semibold text-wo-text-primary">
          Fixture / order identity (GET plan + audit — no invent)
        </p>
        <div className="flex flex-wrap gap-2 text-[10px] font-mono text-wo-text-secondary">
          <span className="border border-wo-border-subtle rounded px-1.5 py-0.5 bg-wo-surface-inset">
            fixture={isFixture ? FIX_DEC009_MAT_01_LABEL : "—"}
          </span>
          <span className="border border-wo-border-subtle rounded px-1.5 py-0.5 bg-wo-surface-inset">
            order_id={plan?.order_id ?? orderId}
          </span>
          <span className="border border-wo-border-subtle rounded px-1.5 py-0.5 bg-wo-surface-inset">
            plan_id={plan?.id ?? audit?.execution_plan_id ?? "—"}
          </span>
          <span className="border border-wo-border-subtle rounded px-1.5 py-0.5 bg-wo-surface-inset">
            order_code={displayText(plan?.order_code ?? audit?.order_code)}
          </span>
          <span className="border border-wo-border-subtle rounded px-1.5 py-0.5 bg-wo-surface-inset">
            snapshot={displayText(audit?.source_snapshot_code)}
          </span>
        </div>
        <form
          className="flex flex-wrap items-center gap-2 pt-1"
          onSubmit={(e) => {
            e.preventDefault();
            applyOrderId();
          }}
        >
          <label className="text-[10px] text-wo-text-muted" htmlFor="ops-graph-order-id">
            orderId
          </label>
          <input
            id="ops-graph-order-id"
            data-testid="ops-graph-order-input"
            value={orderInput}
            onChange={(e) => setOrderInput(e.target.value)}
            className="w-28 rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1 text-[11px] font-mono text-wo-text-primary"
          />
          <button
            type="submit"
            className="px-2.5 py-1 text-[11px] font-semibold rounded border border-wo-border-strong bg-wo-surface-raised text-wo-text-primary hover:bg-wo-hover"
          >
            Load
          </button>
          <button
            type="button"
            data-testid="ops-graph-load-fixture"
            onClick={() => {
              setOrderInput(String(FIX_DEC009_MAT_01_ORDER_ID));
              setSearchParams({});
            }}
            className="px-2.5 py-1 text-[11px] font-semibold rounded border border-wo-info/40 bg-wo-info-muted text-wo-info hover:bg-wo-hover"
          >
            Fixture 973010
          </button>
        </form>
      </div>

      <ExecutionPlanStatesStrip
        hasPreview
        hasDraftPlan={Boolean(plan)}
        hasOperationalTasks={hasOperationalTasks}
        operationalBlocked={materializeState !== "OPEN"}
      />

      <OwnerGoNotice
        detail="POST materialize rămâne gated (DEC-009). Acest ecran doar citește operational_tasks[] deja materializate — fără sessions, fără Employee Mobile, fără start/stop/assign/complete."
        compact
      />

      <div
        className={`rounded-lg px-3 py-2 space-y-1.5 ${chromeBanner.neutral}`}
        data-testid="ops-graph-capacity-strip"
      >
        <div className="flex items-center gap-2">
          <Gauge className="w-3.5 h-3.5 text-wo-info shrink-0" />
          <p className="text-[11px] font-semibold text-wo-text-primary">
            Capacity / DEC-009 strip (read-only)
          </p>
        </div>
        <p className="text-[10px] text-wo-text-muted" data-testid="ops-graph-dec009-state">
          DEC-009={dec009} · materialize={materializeState} · audit=
          {displayText(audit?.materialization_status)} · dry_run=
          {displayText(audit?.dry_run_status)}
        </p>
        <p className="text-[10px] text-wo-text-muted">
          {preMat?.summary ??
            batch04?.preMaterializeSummary ??
            "DEC-009 / capacity checklist from dashboard-stats when available."}
          {" · "}
          Employee Mobile:{" "}
          {audit?.guards?.employee_mobile_scope === true ? "in scope" : "out of scope"}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="ops-graph-metrics">
        <MetricTile label="Operational tasks" value={loading ? "…" : taskCount} variant="default" />
        <MetricTile
          label="Sessions"
          value={loading ? "…" : sessionsCount === null ? "—" : sessionsCount}
          variant="default"
        />
        <MetricTile
          label="Actuals (reality rows)"
          value={loading ? "…" : actualsLabel}
          variant="default"
        />
        <MetricTile
          label="DEC-009"
          value={loading ? "…" : String(dec009)}
          variant="default"
          className="border-t-2 border-t-wo-warning"
        />
      </div>

      {error && (
        <div
          className={`rounded-lg px-4 py-3 text-[12px] ${
            isAuthError ? chromeBanner.warning : chromeBanner.error
          }`}
          data-testid="ops-graph-error"
        >
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <div className="space-y-1">
              <p className="font-semibold">
                {isAuthError
                  ? "Autentificare necesară"
                  : isNetworkError
                    ? "Backend indisponibil"
                    : "Eroare la încărcarea ops graph"}
              </p>
              <p className="text-[11px] opacity-80">{error}</p>
            </div>
          </div>
        </div>
      )}

      {loading && !plan && !error && (
        <div
          className="flex items-center justify-center h-48"
          data-testid="ops-graph-loading"
        >
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-wo-info mx-auto mb-2" />
            <p className="text-[12px] text-wo-text-muted">Se încarcă planul operațional…</p>
          </div>
        </div>
      )}

      {!loading && !error && plan && tasks.length === 0 && (
        <div
          className="bg-wo-surface-raised border border-wo-border-strong rounded-lg px-6 py-10 text-center"
          data-testid="ops-graph-empty"
        >
          <Activity className="w-8 h-8 text-wo-text-dim mx-auto mb-2" />
          <p className="text-[13px] text-wo-text-muted">
            Niciun operational_task în envelope pentru order {orderId}.
          </p>
          <p className="text-[11px] text-wo-text-dim mt-1">
            Plan id {plan.id} — materialize poate fi încă blocked / nematerializat.
          </p>
        </div>
      )}

      {sortedTasks.length > 0 && (
        <>
          <DataTableWrapper
            title="Operational tasks (list / graph order)"
            subtitle={`${sortedTasks.length} ops · sequence_index + depends_on`}
            density="compact"
          >
            <div className="overflow-x-auto" data-testid="ops-graph-task-list">
              <table className="w-full text-[12px]">
                <thead className="bg-wo-surface-inset border-b border-wo-border-strong">
                  <tr className="text-left text-wo-text-muted uppercase text-[10px] tracking-wide">
                    <th className="px-3 py-2 font-semibold">#</th>
                    <th className="px-3 py-2 font-semibold">Task</th>
                    <th className="px-3 py-2 font-semibold">Process</th>
                    <th className="px-3 py-2 font-semibold">Machine</th>
                    <th className="px-3 py-2 font-semibold">WC</th>
                    <th className="px-3 py-2 font-semibold text-right">Min</th>
                    <th className="px-3 py-2 font-semibold">Depends</th>
                    <th className="px-3 py-2 font-semibold">Null / warnings</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedTasks.map((task) => {
                    const warns = nullFieldWarnings(task);
                    return (
                      <tr
                        key={task.task_id}
                        className="border-b border-wo-border-strong last:border-b-0 align-top"
                        data-testid={`ops-graph-task-row-${task.task_id}`}
                      >
                        <td className="px-3 py-2 text-wo-text-muted tabular-nums">
                          {task.sequence_index ?? "—"}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex flex-col gap-0.5">
                            <span className="text-wo-text-primary font-semibold">
                              {displayText(task.display_name ?? task.name)}
                            </span>
                            <span className="text-[10px] font-mono text-wo-text-muted break-all">
                              {task.task_id}
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-2 text-wo-text-secondary">
                          {displayText(task.process_type)}
                        </td>
                        <td className="px-3 py-2 font-mono text-[11px] text-wo-text-secondary">
                          {displayText(task.machine_code ?? task.machine_type)}
                        </td>
                        <td className="px-3 py-2 font-mono text-[11px] text-wo-text-muted">
                          {displayText(task.workcenter)}
                        </td>
                        <td className="px-3 py-2 text-right tabular-nums text-wo-text-muted">
                          {displayMinutes(task.estimated_time_minutes)}
                        </td>
                        <td className="px-3 py-2 text-[10px] font-mono text-wo-text-muted">
                          {(task.depends_on_task_ids ?? []).length === 0
                            ? "—"
                            : (task.depends_on_task_ids ?? [])
                                .map((d) => d.split(":").slice(-1)[0] ?? d)
                                .join(", ")}
                        </td>
                        <td className="px-3 py-2">
                          {warns.length === 0 ? (
                            <span className="text-wo-text-dim">—</span>
                          ) : (
                            <div className="flex flex-wrap gap-1">
                              {warns.map((w) => (
                                <span
                                  key={w}
                                  className="inline-block px-1.5 py-0.5 text-[9px] rounded border border-wo-warning/40 bg-wo-warning-muted text-wo-warning"
                                >
                                  {w}
                                </span>
                              ))}
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </DataTableWrapper>

          <div
            className="rounded-lg border border-wo-border-strong bg-wo-surface-raised px-3 py-3 space-y-2"
            data-testid="ops-graph-dependency-strip"
          >
            <p className="text-[11px] font-semibold text-wo-text-primary">
              Dependency strip (sequence · depends_on)
            </p>
            <ol className="flex flex-col gap-1.5">
              {sortedTasks.map((task) => (
                <li
                  key={`dep-${task.task_id}`}
                  className="flex flex-wrap items-baseline gap-2 text-[10px] font-mono text-wo-text-secondary"
                >
                  <span className="text-wo-text-muted w-6 tabular-nums">
                    {task.sequence_index ?? "—"}
                  </span>
                  <span className="text-wo-text-primary">
                    {task.source_operation_code ??
                      task.technical_name ??
                      task.task_id.split(":").slice(-1)[0]}
                  </span>
                  <span className="text-wo-text-dim">←</span>
                  <span>
                    {(task.depends_on_task_ids ?? []).length === 0
                      ? "(root)"
                      : (task.depends_on_task_ids ?? [])
                          .map((d) => d.split(":").slice(-1)[0] ?? d)
                          .join(" · ")}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        </>
      )}

      {(audit?.warnings?.length ?? 0) > 0 && (
        <div
          className={`flex items-start gap-2 px-3 py-2 rounded-lg ${chromeBanner.info}`}
          data-testid="ops-graph-audit-warnings"
        >
          <Info className="w-3.5 h-3.5 text-wo-info mt-0.5 shrink-0" />
          <div className="text-[10px] space-y-1">
            <p className="font-semibold">Audit warnings (backend)</p>
            <div className="flex flex-wrap gap-1">
              {audit?.warnings.map((w) => (
                <span
                  key={w}
                  className="inline-block px-1.5 py-0.5 rounded border border-wo-info/35 bg-wo-info-muted text-wo-info font-mono"
                >
                  {w}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      <p className="text-[10px] text-wo-text-dim italic" data-testid="ops-graph-readonly-footer">
        Read-only visibility. No start/stop/assign/complete controls. No Employee Mobile
        implication. Sessions/actuals shown from audit.guards + GET reality only — never
        invented. Sources: GET /execution/plan/{"{id}"}, GET
        /execution/plan-v2/from-order/{"{id}"}/materialization-audit, GET
        /execution/reality/{"{id}"}, dashboard-stats capacity strip.
      </p>
    </div>
  );
}
