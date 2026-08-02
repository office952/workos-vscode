/**
 * MaterializedOpsGraph — Capacity Batch 15/17 clarity · Batch 18 OR-09 labels.
 *
 * READ-ONLY admin/operator surface over already-materialized V2 operational
 * tasks. Prefer fixture FIX-DEC009-MAT-01 (order 973010 / plan 12).
 *
 * Consumes Batch 17 Track B `read_clarity` / `ops_graph_read_clarity` when
 * present; falls back to raw envelope fields + local gap labels otherwise.
 * OR-09: prefer `identity.ops_display_label` so EUR/ml commercial phrasing
 * from template provenance does not read as client price / Capacity unit.
 *
 * MUST NOT: start / stop / assign / complete · Employee Mobile · POST materialize.
 * Null / owner-accepted gaps render as "—" — never invented zeros or assignment.
 * MUST NOT: Pricing / CostEngine / invent unit conversion.
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
  type EmployeeEligibilityReadModelResponse,
  type ExecutionPlanResponse,
  type ExecutionPlanV2MaterializationAuditResponse,
  type ExecutionRealityResponse,
  type OpsGraphNullClassification,
  type OpsGraphTaskReadClarity,
  type PlannedTaskRow,
  type TaskEligibilityRow,
} from "@/api/execution";
import FlowBreadcrumb from "@/components/workos/FlowBreadcrumb";
import { ExecutionPlanStatesStrip } from "@/components/execution/ExecutionPlanStatesStrip";
import OpsGraphFrozenTechnicalMaterials from "@/components/workos/OpsGraphFrozenTechnicalMaterials";
import {
  MetricTile,
  DataTableWrapper,
  OwnerGoNotice,
  chromeBanner,
} from "@/components/workos/design-system";
import { useDashboardStats } from "@/hooks/useDashboardStats";
import {
  OPS_GRAPH_DISPLAY_ORDER_NOTE,
  sortTasksByDependencyDisplayOrder,
} from "@/lib/opsGraphDisplayOrder";

/** Canonical Batch 15 fixture — display default only; not invented data. */
export const FIX_DEC009_MAT_01_ORDER_ID = 973010;
export const FIX_DEC009_MAT_01_LABEL = "FIX-DEC009-MAT-01";

type GapKind =
  | "minutes"
  | "planning_source"
  | "machine_code"
  | "workcenter"
  | "assignee"
  | "unit"
  | "backend";

const GAP_LABEL: Record<GapKind, string> = {
  minutes: "min",
  planning_source: "plan-src",
  machine_code: "mach-code",
  workcenter: "WC",
  assignee: "assignee",
  unit: "unit",
  backend: "warn",
};

function displayText(value: string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  return value;
}

function displayMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value}`;
}

function shortTaskRef(taskId: string): string {
  return taskId.split(":").slice(-1)[0] ?? taskId;
}

/** Display-only soften when read_clarity.ops_display_label is absent (OR-09). */
const COMMERCIAL_EUR_ML_PAREN = /\s*\([^)]*EUR\s*\/\s*ml[^)]*\)/gi;

function softenCommercialEurMlLabel(raw: string): string {
  const softened = raw
    .replace(COMMERCIAL_EUR_ML_PAREN, "")
    .replace(/\s{2,}/g, " ")
    .replace(/^[\s\-—]+|[\s\-—]+$/g, "")
    .trim();
  return softened || raw;
}

function opsGraphTaskLabel(task: PlannedTaskRow): {
  display: string;
  provenance: string;
  commercialPhrasing: boolean;
  title?: string;
} {
  const rc = task.read_clarity;
  const rawCandidate =
    rc?.identity.label ?? task.display_name ?? task.name ?? "";
  const raw = rawCandidate.trim() || "—";
  const clarity = rc?.identity.label_clarity;
  const fromClarity = rc?.identity.ops_display_label?.trim();
  const display =
    fromClarity || (raw !== "—" ? softenCommercialEurMlLabel(raw) : raw);
  const commercialPhrasing =
    clarity?.commercial_unit_phrasing_present ?? /EUR\s*\/\s*ml/i.test(raw);
  const title = commercialPhrasing
    ? clarity?.note ??
      `Template provenance: ${raw} — EUR/ml phrasing is not client price, not Capacity metadata, not task.unit. Upstream rename = Product System Owner.`
    : undefined;
  return { display, provenance: raw, commercialPhrasing, title };
}

function isAbsentClass(c: OpsGraphNullClassification | undefined): boolean {
  return (
    c === "owner_accepted_risk" ||
    c === "unknown" ||
    c === "blocked_pending_owner_truth" ||
    c === "not_required"
  );
}

function honestyDisplay(field: { value: unknown; classification: OpsGraphNullClassification } | undefined): string {
  if (!field) return "—";
  if (isAbsentClass(field.classification)) return "—";
  if (field.value === null || field.value === undefined || field.value === "") return "—";
  return String(field.value);
}

function taskGapsFromClarity(rc: OpsGraphTaskReadClarity): { kinds: GapKind[]; detail: string[] } {
  const kinds: GapKind[] = [];
  const detail: string[] = [];
  const push = (kind: GapKind, field: { classification: OpsGraphNullClassification; note?: string; owner_lock?: string }, label: string) => {
    if (!isAbsentClass(field.classification) && field.classification !== "present") return;
    if (field.classification === "present") return;
    kinds.push(kind);
    detail.push(
      [label, field.classification, field.owner_lock, field.note].filter(Boolean).join(" · "),
    );
  };
  push("minutes", rc.estimated_time_minutes, "estimated_time_minutes");
  push("planning_source", rc.planning_minutes_source, "planning_minutes_source");
  push("machine_code", rc.machine_code, "machine_code");
  push("workcenter", rc.workcenter, "workcenter");
  push("assignee", rc.assigned_employee_id, "assigned_employee_id");
  push("unit", rc.unit, "unit");
  for (const w of rc.warnings.active_warnings ?? []) {
    if (!w) continue;
    if (!kinds.includes("backend")) kinds.push("backend");
    if (!detail.includes(w)) detail.push(w);
  }
  return { kinds, detail };
}

function taskGapsLocal(task: PlannedTaskRow): { kinds: GapKind[]; detail: string[] } {
  const kinds: GapKind[] = [];
  const detail: string[] = [];

  const warnings = task.warnings ?? [];
  const wcNotRequired = warnings.includes("WORKCENTER_NOT_REQUIRED");
  if (task.estimated_time_minutes === null || task.estimated_time_minutes === undefined) {
    kinds.push("minutes");
    detail.push(
      "Durată de planificare indisponibilă — standardul de timp nu este încă definit (nu înseamnă 0 minute).",
    );
  }
  if (task.planning_minutes_source === null || task.planning_minutes_source === undefined) {
    kinds.push("planning_source");
    detail.push("planning_minutes_source=null (source_missing)");
  }
  if (task.machine_code === null || task.machine_code === undefined || task.machine_code === "") {
    kinds.push("machine_code");
    detail.push("machine_code=null (owner-accepted CAP-012)");
  }
  if (
    !wcNotRequired &&
    (task.workcenter === null || task.workcenter === undefined || task.workcenter === "")
  ) {
    kinds.push("workcenter");
    detail.push(
      "Workcenter neconfigurat — nu există încă o asociere operațională canonică pentru acest task.",
    );
  }
  if (task.assigned_employee_id === null || task.assigned_employee_id === undefined) {
    kinds.push("assignee");
    detail.push("assigned_employee_id=null (HR out of stage)");
  }
  for (const w of task.warnings ?? []) {
    if (!w) continue;
    if (!kinds.includes("backend")) kinds.push("backend");
    if (!detail.includes(w)) detail.push(w);
  }
  return { kinds, detail };
}

function taskGaps(task: PlannedTaskRow): { kinds: GapKind[]; detail: string[] } {
  if (task.read_clarity) return taskGapsFromClarity(task.read_clarity);
  return taskGapsLocal(task);
}

function parseOrderId(raw: string | null): number {
  if (!raw) return FIX_DEC009_MAT_01_ORDER_ID;
  const n = Number(raw);
  if (!Number.isInteger(n) || n <= 0) return FIX_DEC009_MAT_01_ORDER_ID;
  return n;
}

function eligibilitySummary(row: TaskEligibilityRow | undefined): {
  label: string;
  title: string;
} {
  if (!row) {
    return {
      label: "—",
      title: "Eligibility read model unavailable for this task.",
    };
  }
  const status = row.eligibility_status;
  if (status === "ready" || status === "ready_with_warnings") {
    const n = row.eligible_employee_count;
    return {
      label: `Eligibili: ${n}`,
      title:
        "Angajații corespund cerințelor operaționale configurate pentru acest task. Read-only — no assignment.",
    };
  }
  if (status === "blocked_no_matching_employee") {
    return {
      label: "Niciun eligibil",
      title:
        "Niciun angajat eligibil — nu există momentan un angajat activ cu toate competențele configurate.",
    };
  }
  if (
    status === "blocked_missing_workcenter" ||
    status === "blocked_ambiguous_workcenter" ||
    status === "blocked_missing_requirements"
  ) {
    return {
      label: "Elig. blocată",
      title:
        "Eligibilitate blocată — taskul nu are încă un workcenter sau un set complet de cerințe operaționale.",
    };
  }
  if (status === "not_required") {
    return { label: "N/A", title: "Workcenter/eligibility not required for this task." };
  }
  return { label: status, title: (row.blockers ?? []).join(" · ") || status };
}

function materializePhaseLabel(args: {
  materializeState: string;
  auditStatus: string | null | undefined;
  hasOps: boolean;
}): { envelope: string; furtherPost: string } {
  const audit = args.auditStatus ?? "";
  const already =
    audit.includes("already_materialized") ||
    (args.hasOps && audit === "");
  return {
    envelope: already
      ? "already materialized (envelope)"
      : args.hasOps
        ? "ops present"
        : "not materialized",
    furtherPost:
      args.materializeState === "OPEN"
        ? "further POST open"
        : "further POST blocked (DEC-009)",
  };
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
  const [eligibility, setEligibility] =
    useState<EmployeeEligibilityReadModelResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [orderInput, setOrderInput] = useState(String(orderId));
  const [expandedEligibility, setExpandedEligibility] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [planResult, auditResult, realityResult, eligResult] = await Promise.allSettled([
        executionApi.getExecutionPlan(orderId),
        executionApi.getExecutionPlanV2MaterializationAudit(orderId),
        executionApi.getReality(orderId),
        executionApi.getEmployeeEligibilityReadModel(orderId),
      ]);

      if (planResult.status === "rejected") {
        throw planResult.reason instanceof Error
          ? planResult.reason
          : new Error("plan_load_failed");
      }

      setPlan(planResult.value);
      setAudit(auditResult.status === "fulfilled" ? auditResult.value : null);
      setReality(realityResult.status === "fulfilled" ? realityResult.value : null);
      setEligibility(eligResult.status === "fulfilled" ? eligResult.value : null);
    } catch (e) {
      setPlan(null);
      setAudit(null);
      setReality(null);
      setEligibility(null);
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
  const planClarity = plan?.ops_graph_read_clarity ?? null;
  const taskCount =
    planClarity?.operational_tasks_count ??
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
  const phase = materializePhaseLabel({
    materializeState,
    auditStatus: audit?.materialization_status,
    hasOps: hasOperationalTasks,
  });
  const executionActive = false; // RO surface — no sessions/start/complete on this page.
  const usesTrackBClarity = Boolean(planClarity) || tasks.some((t) => Boolean(t.read_clarity));
  const commercialLabelCount = useMemo(() => {
    const fromPlan = planClarity?.label_policy?.commercial_unit_phrasing_task_count;
    if (typeof fromPlan === "number") return fromPlan;
    return tasks.filter((t) => opsGraphTaskLabel(t).commercialPhrasing).length;
  }, [planClarity, tasks]);

  const eligibilityByTask = useMemo(() => {
    const map = new Map<string, TaskEligibilityRow>();
    for (const row of eligibility?.tasks ?? []) {
      if (row.task_key) map.set(row.task_key, row);
    }
    return map;
  }, [eligibility]);

  /** Display order = dependency/topo; SEQ column still shows original sequence_index. */
  const sortedTasks = useMemo(
    () => sortTasksByDependencyDisplayOrder(tasks),
    [tasks],
  );

  const sequenceNote = useMemo(() => {
    if (planClarity?.sequence) {
      const seq = planClarity.sequence;
      const observed = seq.observed_indices ?? [];
      const gaps = seq.gaps ?? [];
      if (gaps.length === 0) {
        return seq.note ?? `sequence_index ${observed.join(", ") || "—"} (contiguous)`;
      }
      return (
        seq.note ??
        `sequence_index ${observed.join(", ")} · gaps ${gaps.join(", ")} absent (not invented)`
      );
    }
    const seqs = sortedTasks
      .map((t) => t.sequence_index)
      .filter((n): n is number => typeof n === "number");
    if (seqs.length === 0) return null;
    const min = Math.min(...seqs);
    const max = Math.max(...seqs);
    const present = new Set(seqs);
    const missing: number[] = [];
    for (let i = min; i <= max; i += 1) {
      if (!present.has(i)) missing.push(i);
    }
    if (missing.length === 0) {
      return `sequence_index ${min}–${max} (contiguous)`;
    }
    return `sequence_index ${seqs.join(", ")} · gaps ${missing.join(", ")} absent (not invented)`;
  }, [planClarity, sortedTasks]);

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
          { label: "Execution", to: "/execution" },
          { label: "Ops graph (RO)", active: true },
        ]}
      />

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-wo-info" />
          <div>
            <h1 className="text-[18px] font-bold text-wo-text-primary">
              Ops graph
            </h1>
            <p className="text-[11px] text-wo-text-muted">
              Operator / Admin read-only · no execution active
            </p>
          </div>
          <span
            className="text-[10px] text-wo-text-muted bg-wo-surface-inset border border-wo-border-subtle px-2 py-0.5 rounded"
            data-testid="ops-graph-ro-badge"
          >
            RO
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
          Identity
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
          <span className="border border-wo-border-subtle rounded px-1.5 py-0.5 bg-wo-surface-inset">
            execution={executionActive ? "active" : "not active"}
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
        operationalBlocked={materializeState !== "OPEN" && !hasOperationalTasks}
      />

      {!hasOperationalTasks && (
        <OwnerGoNotice
          detail="Further POST materialize remains DEC-009 gated. This screen only reads already-materialized operational_tasks[] — no sessions, no start/stop/assign/complete."
          compact
        />
      )}

      <div
        className={`rounded-lg px-3 py-2 space-y-1.5 ${chromeBanner.neutral}`}
        data-testid="ops-graph-capacity-strip"
      >
        <div className="flex items-center gap-2">
          <Gauge className="w-3.5 h-3.5 text-wo-info shrink-0" />
          <p className="text-[11px] font-semibold text-wo-text-primary">
            {hasOperationalTasks
              ? "Operational planning truth (read-only)"
              : "DEC-009 / Capacity (read-only)"}
          </p>
        </div>
        <p className="text-[10px] text-wo-text-secondary" data-testid="ops-graph-dec009-state">
          {hasOperationalTasks
            ? `envelope=${phase.envelope} · further materialize gated`
            : `DEC-009=${dec009} · ${phase.furtherPost} · envelope=${phase.envelope}`}
          {audit?.materialization_status
            ? ` · audit=${audit.materialization_status}`
            : ""}
        </p>
        <p className="text-[10px] text-wo-text-muted">
          {hasOperationalTasks
            ? "Duratele sunt folosite pentru planificarea capacității. Nu reprezintă prețul clientului și nici timpul efectiv lucrat."
            : (preMat?.summary ??
              batch04?.preMaterializeSummary ??
              "Capacity checklist from dashboard-stats when available.")}
        </p>
        <p className="text-[10px] text-wo-text-dim" data-testid="ops-graph-accepted-risks">
          Gaps: workcenter neconfigurat / durată indisponibilă remain null — never
          invented zeros
          {usesTrackBClarity ? " · Track B read_clarity" : ""}.
        </p>
        {commercialLabelCount > 0 && (
          <p
            className="text-[10px] text-wo-text-muted"
            data-testid="ops-graph-or09-label-note"
            title={planClarity?.label_policy?.note}
          >
            Label note (OR-09): {commercialLabelCount} task label(s) had commercial
            EUR/ml phrasing in template provenance — ops-graph shows process wording
            only (not client price / not Capacity unit). Hover task name for raw
            label.
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="ops-graph-metrics">
        <MetricTile label="Ops tasks" value={loading ? "…" : taskCount} variant="default" />
        <MetricTile
          label="Sessions"
          value={loading ? "…" : sessionsCount === null ? "—" : sessionsCount}
          variant="default"
        />
        <MetricTile
          label="Actuals"
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

      {!loading && !error && plan && (
        <OpsGraphFrozenTechnicalMaterials
          projection={plan.frozen_technical_materials}
        />
      )}

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
            <p className="text-[12px] text-wo-text-muted">Loading operational plan…</p>
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
            No operational_tasks in envelope for order {orderId}.
          </p>
          <p className="text-[11px] text-wo-text-dim mt-1">
            Plan id {plan.id} — envelope may be empty or not yet materialized.
          </p>
        </div>
      )}

      {sortedTasks.length > 0 && (
        <>
          <DataTableWrapper
            title="Operational tasks"
            subtitle={`${sortedTasks.length} ops · ${OPS_GRAPH_DISPLAY_ORDER_NOTE}${
              sequenceNote ? ` · ${sequenceNote}` : ""
            }`}
            density="compact"
          >
            <p
              className="px-3 pt-2 text-[10px] text-wo-text-muted"
              data-testid="ops-graph-display-order-note"
            >
              {OPS_GRAPH_DISPLAY_ORDER_NOTE}
            </p>
            <div className="overflow-x-auto" data-testid="ops-graph-task-list">
              <table className="w-full text-[12px]">
                <thead className="bg-wo-surface-inset border-b border-wo-border-strong">
                  <tr className="text-left text-wo-text-muted uppercase text-[10px] tracking-wide">
                    <th
                      className="px-3 py-2 font-semibold"
                      title="Original source sequence_index — not remapped to display rank"
                    >
                      SEQ
                    </th>
                    <th className="px-3 py-2 font-semibold">Status</th>
                    <th className="px-3 py-2 font-semibold">Task</th>
                    <th className="px-3 py-2 font-semibold">Process</th>
                    <th className="px-3 py-2 font-semibold">Type</th>
                    <th className="px-3 py-2 font-semibold">Code</th>
                    <th className="px-3 py-2 font-semibold">WC</th>
                    <th className="px-3 py-2 font-semibold text-right">Min</th>
                    <th className="px-3 py-2 font-semibold">Depends</th>
                    <th className="px-3 py-2 font-semibold">Gaps</th>
                    <th className="px-3 py-2 font-semibold">Elig.</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedTasks.map((task) => {
                    const rc = task.read_clarity;
                    const gaps = taskGaps(task);
                    const elig = eligibilityByTask.get(task.task_id);
                    const eligUi = eligibilitySummary(elig);
                    const seq =
                      rc?.identity.sequence_index ?? task.sequence_index ?? "—";
                    const status =
                      rc?.lifecycle.display_label ??
                      displayText(rc?.lifecycle.value ?? task.operational_status);
                    const taskLabel = opsGraphTaskLabel(task);
                    const shortCode =
                      rc?.identity.short_code ?? shortTaskRef(task.task_id);
                    const process =
                      rc?.identity.process_type ?? displayText(task.process_type);
                    const machineType = rc
                      ? honestyDisplay(rc.machine_type)
                      : displayText(task.machine_type);
                    const machineCode = rc
                      ? honestyDisplay(rc.machine_code)
                      : displayText(task.machine_code);
                    const workcenter = rc
                      ? honestyDisplay(rc.workcenter)
                      : displayText(task.workcenter);
                    const minutes = rc
                      ? honestyDisplay(rc.estimated_time_minutes)
                      : displayMinutes(task.estimated_time_minutes);
                    const depends =
                      rc?.depends_on.short_codes?.length
                        ? rc.depends_on.short_codes.join(", ")
                        : (task.depends_on_task_ids ?? []).length === 0
                          ? "—"
                          : (task.depends_on_task_ids ?? [])
                              .map((d) => shortTaskRef(d))
                              .join(", ");

                    return (
                      <tr
                        key={task.task_id}
                        className="border-b border-wo-border-strong last:border-b-0 align-top"
                        data-testid={`ops-graph-task-row-${task.task_id}`}
                      >
                        <td className="px-3 py-2 text-wo-text-muted tabular-nums">
                          {seq}
                        </td>
                        <td
                          className="px-3 py-2 font-mono text-[11px] text-wo-text-secondary"
                          title={rc?.lifecycle.note ?? "plan lifecycle — not actuals"}
                        >
                          {status}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex flex-col gap-0.5">
                            <span
                              className="text-wo-text-primary font-semibold"
                              title={taskLabel.title}
                              data-testid={`ops-graph-task-label-${task.task_id}`}
                              data-label-provenance={
                                taskLabel.commercialPhrasing
                                  ? taskLabel.provenance
                                  : undefined
                              }
                            >
                              {taskLabel.display}
                            </span>
                            <span className="text-[10px] font-mono text-wo-text-muted">
                              {shortCode}
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-2 text-wo-text-secondary">
                          {process}
                        </td>
                        <td
                          className="px-3 py-2 font-mono text-[11px] text-wo-text-secondary"
                          title={
                            rc?.display_hints.machine_column ??
                            "machine_type (catalog class — not instance assignment)"
                          }
                        >
                          {machineType}
                        </td>
                        <td
                          className="px-3 py-2 font-mono text-[11px] text-wo-text-muted"
                          title={
                            rc?.display_hints.machine_code_column ??
                            "machine_code (instance) — null = unassigned"
                          }
                          data-testid={`ops-graph-machine-code-${task.task_id}`}
                        >
                          {machineCode}
                        </td>
                        <td
                          className="px-3 py-2 font-mono text-[11px] text-wo-text-muted"
                          title={
                            workcenter === "—"
                              ? "Workcenter neconfigurat — nu există încă o asociere operațională canonică pentru acest task."
                              : "Canonical workcenter (frozen)"
                          }
                          data-testid={`ops-graph-workcenter-${task.task_id}`}
                        >
                          {workcenter}
                        </td>
                        <td
                          className="px-3 py-2 text-right tabular-nums text-wo-text-muted"
                          title={
                            minutes === "—"
                              ? "Durată de planificare indisponibilă — standardul de timp nu este încă definit. Aceasta nu înseamnă 0 minute."
                              : "Planning minutes (capacity) — not client price / not actuals"
                          }
                          data-testid={`ops-graph-minutes-${task.task_id}`}
                        >
                          {minutes}
                        </td>
                        <td className="px-3 py-2 text-[10px] font-mono text-wo-text-muted">
                          {depends || "—"}
                        </td>
                        <td className="px-3 py-2">
                          {gaps.kinds.length === 0 ? (
                            <span className="text-wo-text-dim">—</span>
                          ) : (
                            <span
                              className="inline-block px-1.5 py-0.5 text-[9px] rounded border border-wo-warning/40 bg-wo-warning-muted text-wo-warning"
                              title={gaps.detail.join(" · ")}
                              data-testid={`ops-graph-gaps-${task.task_id}`}
                            >
                              {gaps.kinds.map((k) => GAP_LABEL[k]).join(" · ")}
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-2" data-testid={`ops-graph-elig-${task.task_id}`}>
                          <button
                            type="button"
                            className="text-left text-[10px] font-semibold text-wo-text-secondary hover:text-wo-text-primary"
                            title={eligUi.title}
                            onClick={() =>
                              setExpandedEligibility((cur) =>
                                cur === task.task_id ? null : task.task_id,
                              )
                            }
                          >
                            {eligUi.label}
                          </button>
                          {expandedEligibility === task.task_id && elig && (
                            <div className="mt-1 text-[10px] text-wo-text-muted space-y-0.5 max-w-[220px]">
                              <p className="font-mono">{elig.eligibility_status}</p>
                              {(elig.blockers ?? []).length > 0 && (
                                <p>blockers: {elig.blockers.join(", ")}</p>
                              )}
                              {(elig.eligible_employees ?? []).slice(0, 6).map((e) => (
                                <p key={e.employee_id} className="font-mono">
                                  #{e.employee_id} {e.display_name}
                                  {e.matched_workcenter ? ` · ${e.matched_workcenter}` : ""}
                                </p>
                              ))}
                              {(elig.eligible_employees ?? []).length === 0 && (
                                <p>{eligUi.title}</p>
                              )}
                              <p className="text-wo-text-dim">
                                Read-only — no Asignează / claim / start.
                              </p>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {sequenceNote && (
              <p
                className="px-3 py-2 text-[10px] text-wo-text-muted border-t border-wo-border-subtle"
                data-testid="ops-graph-sequence-note"
              >
                {sequenceNote}
              </p>
            )}
          </DataTableWrapper>

          <div
            className="rounded-lg border border-wo-border-strong bg-wo-surface-raised px-3 py-3 space-y-2"
            data-testid="ops-graph-dependency-strip"
          >
            <p className="text-[11px] font-semibold text-wo-text-primary">
              Dependency order
            </p>
            <ol className="flex flex-col gap-1">
              {sortedTasks.map((task) => {
                const rc = task.read_clarity;
                const code =
                  rc?.identity.source_operation_code ??
                  rc?.identity.short_code ??
                  task.source_operation_code ??
                  task.technical_name ??
                  shortTaskRef(task.task_id);
                const deps =
                  rc?.depends_on.short_codes?.length
                    ? rc.depends_on.short_codes.join(" · ")
                    : (task.depends_on_task_ids ?? []).length === 0
                      ? "(root)"
                      : (task.depends_on_task_ids ?? [])
                          .map((d) => shortTaskRef(d))
                          .join(" · ");
                return (
                  <li
                    key={`dep-${task.task_id}`}
                    className="flex flex-wrap items-baseline gap-2 text-[10px] font-mono text-wo-text-secondary"
                  >
                    <span className="text-wo-text-muted w-6 tabular-nums">
                      {rc?.identity.sequence_index ?? task.sequence_index ?? "—"}
                    </span>
                    <span className="text-wo-text-primary">{code}</span>
                    <span className="text-wo-text-dim">←</span>
                    <span>{deps}</span>
                  </li>
                );
              })}
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
            <p className="font-semibold">
              Audit warnings ({audit?.warnings.length}) — backend, not invented
            </p>
            <p className="font-mono text-wo-text-secondary">
              {(audit?.warnings ?? []).join(" · ")}
            </p>
          </div>
        </div>
      )}

      <p className="text-[10px] text-wo-text-dim" data-testid="ops-graph-readonly-footer">
        Read-only. No start/stop/assign/complete. Sessions/actuals from audit.guards +
        GET reality only. Sources: GET /execution/plan/{"{id}"} (Track B read_clarity),
        GET /execution/plan-v2/from-order/{"{id}"}/materialization-audit, GET
        /execution/reality/{"{id}"}, dashboard-stats DEC-009 strip.
      </p>
    </div>
  );
}
