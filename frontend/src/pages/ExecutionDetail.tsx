/**
 * ExecutionDetail — Sprint #12 (observability) + Sprint #30 (plan gate).
 *
 * Observabilitate (read-only) peste:
 *   GET /api/v1/execution/observability/{order_id}
 *   GET /api/v1/execution/alerts/{order_id}
 *
 * Poarta de generare plan (Sprint #30) — singura acțiune de scriere din
 * această pagină:
 *   POST /api/v1/execution/plan/from-order/{order_id}
 *
 * Reguli stricte:
 *   - Butonul "Generează plan" apare DOAR când observability.has_plan = false.
 *   - După succes, pagina se reîncarcă (observability + alerts) pentru a
 *     reflecta starea reală — nu se face update optimist în UI.
 *   - Pe eroare, codul structurat al backend-ului (snapshot_incomplete /
 *     plan_already_exists / order_not_found) este afișat explicit, împreună
 *     cu câmpul problematic (ex. snapshot.product_definition.quantity).
 *     UI nu încearcă să „repare" snapshot-ul și nu face fallback tăcut.
 *   - Pragurile și valorile lipsă rămân „—" / „NECONFIRMAT" — niciodată 0.
 */

import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  AlertTriangle,
  ActivitySquare,
  RefreshCw,
  Info,
  PlayCircle,
  CheckCircle2,
} from "lucide-react";
import {
  executionApi,
  PlanGenerationError,
  RealityActionError,
  type AlertsResponse,
  type ExecutionPlanResponse,
  type ExecutionRealityResponse,
  type ExecutionStatus,
  type ObservabilityReport,
  type PlannedTaskRow,
  type RealityTaskRow,
} from "@/api/execution";
import { useGateEvaluation } from "@/hooks/useGateEvaluation";
import { useProductSystemPreview } from "@/hooks/useProductSystemPreview";
import { GateVerdictCard } from "@/components/execution/GateVerdictCard";
import { ProductSystemPreviewPanel } from "@/components/execution/ProductSystemPreviewPanel";
import StockDeductionPanel from "@/components/inventory/StockDeductionPanel";
import { operationalRegistryApi, type OperationResourceMapping } from "@/api/operationalRegistry";
import { OperationRegistryMappingBadge } from "@/features/operational-registry/OperationRegistryMappingBadge";
import RealityQualityBadge from "@/components/workos/RealityQualityBadge";
import {
  fetchOperatorTaskTruth,
  type OperatorTaskTruthResponse,
  type OperatorTaskTruthTask,
} from "@/api/operatorTaskTruth";
import { OperatorProductionReleaseSummary } from "@/components/workos/OperatorProductionReleaseSummary";
import { OperatorOwnerDecisionDetailsPanel } from "@/components/workos/OperatorOwnerDecisionDetailsPanel";
import { OperatorStructuredActionError } from "@/components/workos/OperatorStructuredActionError";
import {
  operationalReadinessBadgeClasses,
  operationalReadinessLabel,
} from "@/lib/executionOperationalReadinessDisplay";
import { ProfitabilityAnalysisPanel } from "@/components/execution/ProfitabilityAnalysisPanel";
import { ProfitabilityActualReadPanel } from "@/components/execution/ProfitabilityActualReadPanel";
import { PostJobTruthPanel } from "@/components/execution/PostJobTruthPanel";
import { ExecutionClosurePanel } from "@/components/execution/ExecutionClosurePanel";
import { OperatorTaskIdentityPresentation } from "@/components/workos/OperatorTaskIdentityPresentation";
import {
  indexOperatorTaskTruth,
  taskTruthReadinessFromRuntime,
  type TaskTruthReadiness,
} from "@/lib/operatorTaskPresentation";
import {
  fetchOrderTaskCollaborationRead,
  type OrderTaskCollaborationReadDTO,
} from "@/api/collaboration";
import OperatorTaskCollaborationPanel from "@/components/workos/collaboration/OperatorTaskCollaborationPanel";
import { isFlexCollabUiEnabled } from "@/lib/flexCollabUiFlag";
import { resolveExecutionNextAction } from "@/lib/executionNextAction";
import ExecutionFlowStrip from "@/components/workos/ExecutionFlowStrip";
import ExecutionFlowNextStep from "@/components/workos/ExecutionFlowNextStep";
import { executionDetailNextStepHint } from "@/lib/executionFlowUi";

// Human-readable labels for plan-generation failure codes coming from the
// backend. We keep the raw code visible alongside so the operator (and QA)
// can always map the Romanian message back to the contract.
const PLAN_ERROR_LABELS: Record<string, string> = {
  order_not_found: "Comanda nu a fost găsită.",
  plan_already_exists: "Există deja un plan pentru această comandă.",
  snapshot_incomplete:
    "Snapshot-ul comenzii este incomplet sau în format vechi — planul nu poate fi generat până când Comanda nu este regenerată dintr-o ofertă cotată (Quote priced → Order) cu structura canonică (product_definition + cost_result).",
  plan_persist_failed:
    "Backend-ul a eșuat la salvarea planului. Verifică log-urile serverului.",
  unknown: "Eroare necunoscută la generarea planului.",
};

// Human-readable labels for reality-capture failure codes. Raw backend code
// is always rendered alongside so the operator can map to the contract.
const REALITY_ERROR_LABELS: Record<string, string> = {
  order_id_invalid: "ID comandă invalid.",
  order_code_invalid: "Cod comandă invalid.",
  task_id_invalid: "ID task invalid.",
  timestamp_missing: "Timestamp lipsă.",
  timestamp_invalid: "Timestamp invalid (format ISO-8601 așteptat).",
  timestamp_before_start: "Timestamp-ul de final este înainte de start.",
  tasks_json_invalid: "Structura realității este coruptă pe server.",
  tasks_json_not_list: "Structura realității este coruptă pe server.",
  task_already_started: "Task-ul este deja pornit (în curs).",
  task_already_ended: "Task-ul este deja încheiat.",
  reality_not_initialised:
    "Nu există încă reality pentru această comandă. Pornește un task pentru a iniția.",
  task_not_started: "Task-ul nu a fost pornit. Pornește-l înainte de a-l închide.",
  task_missing_start: "Task-ul nu are timestamp de start — stare inconsistentă.",
  order_not_found: "Comanda nu a fost găsită.",
  task_not_ready: "Task-ul nu este pregătit pentru start — verifică readiness.",
  production_release_blocked:
    "Pornire blocată — decizii owner de producție nerezolvate la nivel de comandă.",
  ORDER_SNAPSHOT_V2_MISSING: "Snapshot V2 lipsă pentru această comandă.",
  ORDER_SNAPSHOT_V2_CORRUPT: "Snapshot V2 corupt — contactați administratorul.",
  unknown: "Eroare necunoscută la înregistrarea realității.",
};

// Derive the runtime status of a task by joining plan + reality.
type RealityTaskStatus = "not_started" | "in_progress" | "completed";

function computeTaskStatus(
  taskId: string,
  reality: ExecutionRealityResponse | null,
): { status: RealityTaskStatus; observation: RealityTaskRow | null } {
  if (!reality) return { status: "not_started", observation: null };
  // Find LAST observation for this task_id (backend allows multiple only if
  // previous ones are ended; the in-progress guard is enforced server-side).
  const observations = reality.tasks.filter((t) => t.task_id === taskId);
  if (observations.length === 0) {
    return { status: "not_started", observation: null };
  }
  const last = observations[observations.length - 1];
  if (last.ended_at === null) {
    return { status: "in_progress", observation: last };
  }
  return { status: "completed", observation: last };
}

function computeActualMinutes(obs: RealityTaskRow | null): number | null {
  if (!obs || obs.ended_at === null) return null;
  try {
    const s = new Date(obs.started_at).getTime();
    const e = new Date(obs.ended_at).getTime();
    if (!Number.isFinite(s) || !Number.isFinite(e)) return null;
    const delta = (e - s) / 60000;
    return delta >= 0 ? Math.round(delta * 100) / 100 : null;
  } catch {
    return null;
  }
}

function statusBadgeCls(status: ExecutionStatus): string {
  switch (status) {
    case "OK":
      return "bg-emerald-50 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-700";
    case "WARNING":
      return "bg-amber-50 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-700";
    case "CRITICAL":
      return "bg-red-50 dark:bg-red-900/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-700";
    case "UNCONFIRMED":
    default:
      return "bg-muted/60 text-muted-foreground border-slate-600";
  }
}

function statusLabel(status: ExecutionStatus): string {
  if (status === "UNCONFIRMED") return "NECONFIRMAT";
  return status;
}

function fmtMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(1)} min`;
}

function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(2)}%`;
}

function fmtNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(1);
}

function fmtDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("ro-RO");
  } catch {
    return value;
  }
}

// Translate reason codes from backend into operator-readable Romanian.
// Keeps the exact code visible next to the label so nothing is lost.
const REASON_LABELS: Record<string, string> = {
  within_thresholds: "În limite",
  minutes_over_warning: "Depășire minute peste pragul de warning",
  minutes_over_critical: "Depășire minute peste pragul critic",
  pct_over_warning: "Depășire procentuală peste pragul de warning",
  pct_over_critical: "Depășire procentuală peste pragul critic",
  work_against_zero_plan: "Lucru înregistrat fără plan",
  order_missing: "Comanda lipsește",
  plan_missing: "Planul lipsește",
  reality_missing: "Realitatea lipsește",
  data_incomplete: "Date incomplete",
  config_missing: "Configurație lipsă",
  config_inactive: "Configurație inactivă",
  unclassified: "Neclasificat",
};

function ReasonBadge({ code }: { code: string }) {
  const label = REASON_LABELS[code] ?? code;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded border bg-muted/60 text-muted-foreground border-border">
      <span>{label}</span>
      <span className="text-muted-foreground">[{code}]</span>
    </span>
  );
}

export default function ExecutionDetail() {
  const { order_id } = useParams<{ order_id: string }>();
  const parsedId = order_id ? Number.parseInt(order_id, 10) : NaN;
  const isValidId = Number.isInteger(parsedId) && parsedId > 0;

  const [obs, setObs] = useState<ObservabilityReport | null>(null);
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string | null>(null);

  // Plan-generation gate (Sprint #30). These NEVER touch the observability /
  // alerts responses — they only control the call and surface the error.
  const [planSubmitting, setPlanSubmitting] = useState(false);
  const [planError, setPlanError] = useState<PlanGenerationError | null>(null);
  const [planSuccessAt, setPlanSuccessAt] = useState<string | null>(null);

  // Reality capture (Sprint #36). Plan + reality are fetched separately so
  // the operator can see per-task state. `reality = null` is the canonical
  // "no reality captured yet" state returned by the backend as 404 +
  // reality_not_found. NEVER invented by the UI.
  const [plan, setPlan] = useState<ExecutionPlanResponse | null>(null);
  const [reality, setReality] = useState<ExecutionRealityResponse | null>(null);
  const [realityLoading, setRealityLoading] = useState(false);
  const [realityError, setRealityError] = useState<string | null>(null);
  const [realityActionTaskId, setRealityActionTaskId] = useState<string | null>(null);
  const [realityActionError, setRealityActionError] =
    useState<RealityActionError | null>(null);
  const [realityActionAt, setRealityActionAt] = useState<string | null>(null);
  const [taskTruthByTaskId, setTaskTruthByTaskId] = useState<
    Record<string, OperatorTaskTruthTask>
  >({});
  const [taskTruthResponse, setTaskTruthResponse] = useState<OperatorTaskTruthResponse | null>(
    null,
  );
  const [ownerDetailsOpen, setOwnerDetailsOpen] = useState(false);
  const [overrideReasonByTaskId, setOverrideReasonByTaskId] = useState<
    Record<string, string>
  >({});

  // Reality loader — split from the main observability load so we can
  // refetch it independently after start/end actions without reflashing
  // the whole page state.
  const loadRealityOnly = useCallback(
    async (orderId: number) => {
      setRealityLoading(true);
      try {
        const r = await executionApi.getReality(orderId);
        setReality(r);
      } catch (e) {
        const msg = e instanceof Error ? e.message : "unknown error";
        setRealityError(msg);
      } finally {
        setRealityLoading(false);
      }
    },
    [],
  );

  const load = useCallback(async () => {
    if (!isValidId) {
      setError(`ID de comandă invalid: "${order_id}"`);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    setRealityError(null);
    try {
      const [o, a] = await Promise.all([
        executionApi.getObservability(parsedId),
        executionApi.getAlerts(parsedId),
      ]);
      setObs(o);
      setAlerts(a);
      setLastRefreshed(new Date().toLocaleTimeString("ro-RO"));

      // Only fetch plan + reality when observability confirms a plan exists.
      // If the plan is absent, there is no contract of task_ids the UI can
      // act on — we explicitly skip the fetch rather than guessing.
      if (o.has_plan) {
        try {
          const p = await executionApi.getExecutionPlan(parsedId);
          setPlan(p);
        } catch (e) {
          const msg = e instanceof Error ? e.message : "unknown error";
          setRealityError(msg);
          setPlan(null);
        }
        try {
          const truth = await fetchOperatorTaskTruth(parsedId);
          setTaskTruthResponse(truth);
          setTaskTruthByTaskId(indexOperatorTaskTruth(truth.tasks));
        } catch {
          setTaskTruthResponse(null);
          setTaskTruthByTaskId({});
        }
        await loadRealityOnly(parsedId);
      } else {
        setPlan(null);
        setReality(null);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "unknown error";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [isValidId, parsedId, order_id, loadRealityOnly]);

  const refreshTaskTruth = useCallback(async () => {
    if (!isValidId) return;
    try {
      const truth = await fetchOperatorTaskTruth(parsedId);
      setTaskTruthResponse(truth);
      setTaskTruthByTaskId(indexOperatorTaskTruth(truth.tasks));
    } catch {
      setTaskTruthResponse(null);
      setTaskTruthByTaskId({});
    }
  }, [isValidId, parsedId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-4">
      <ExecutionFlowStrip
        active="executie"
        orderExecutionPath={
          isValidId && parsedId != null ? `/execution/${parsedId}` : null
        }
      />
      <ExecutionFlowNextStep
        hint={executionDetailNextStepHint(isValidId ? parsedId : null)}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link
            to="/execution"
            className="inline-flex items-center gap-1 text-[12px] text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Execuție
          </Link>
          <span className="text-wo-text-dim">/</span>
          <Link
            to="/orders"
            className="inline-flex items-center gap-1 text-[12px] text-muted-foreground hover:text-foreground"
          >
            Comenzi
          </Link>
          <span className="text-wo-text-dim">/</span>
          <ActivitySquare className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h1 className="text-[18px] font-bold text-foreground">
            Detaliu execuție
          </h1>
          {obs && (
            <span className="text-[11px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
              {obs.order_code} · #{obs.order_id}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {lastRefreshed && (
            <span className="text-[11px] text-muted-foreground">
              Ultima reîmprospătare: {lastRefreshed}
            </span>
          )}
          <button
            onClick={() => void load()}
            disabled={loading || !isValidId}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium rounded-md bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-muted-foreground text-white transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800/60 rounded-md px-4 py-3 text-[12px] text-red-600 dark:text-red-300">
          Eroare la încărcarea datelor: {error}
        </div>
      )}

      {loading && !obs && !error && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <p className="text-[12px] text-muted-foreground">Se încarcă observabilitatea...</p>
          </div>
        </div>
      )}

      {obs && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Observability panel */}
          <section className="bg-wo-surface-raised border border-wo-border-strong rounded-lg">
            <header className="flex items-center justify-between px-4 py-3 border-b border-wo-border-strong">
              <div className="flex items-center gap-2">
                <ActivitySquare className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <h2 className="text-[13px] font-bold text-foreground uppercase tracking-wide">
                  Observabilitate
                </h2>
              </div>
              <span
                className={`inline-block px-2.5 py-0.5 text-[11px] font-bold rounded border ${statusBadgeCls(obs.status)}`}
              >
                {statusLabel(obs.status)}
              </span>
            </header>
            <div className="p-4 space-y-4">
              {obs.status === "UNCONFIRMED" && (
                <div className="flex items-start gap-2 bg-muted/40 border border-border rounded-md px-3 py-2">
                  <Info className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
                  <p className="text-[12px] text-muted-foreground">
                    <strong>NECONFIRMAT</strong> — date incomplete. Backend-ul
                    nu are suficiente informații pentru a clasifica această
                    comandă.
                  </p>
                </div>
              )}

              {/* Explicit empty-state callouts — operator must see WHY actions
                  are unavailable. No silent absences. */}
              {!obs.has_plan && (
                <div
                  role="alert"
                  className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 dark:border-amber-800/60 dark:bg-amber-900/20"
                >
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
                  <div className="text-[12px] text-amber-900 dark:text-amber-200">
                    <p className="font-semibold">Nu există execution plan</p>
                    <p className="mt-0.5 text-amber-800/90 dark:text-amber-300/80">
                      Nu s-a generat un plan de execuție pentru această comandă.
                      Acțiunile sunt indisponibile până la generarea planului.
                    </p>
                  </div>
                </div>
              )}
              {!obs.has_reality && (
                <div
                  role="alert"
                  className="flex items-start gap-2 bg-muted/40 border border-border rounded-md px-3 py-2"
                >
                  <Info className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
                  <div className="text-[12px] text-muted-foreground">
                    <p className="font-semibold">Nu există execution reality</p>
                    <p className="text-muted-foreground mt-0.5">
                      Nu s-au înregistrat date reale de execuție pentru această
                      comandă. Raportarea de divergență este indisponibilă până
                      la existența datelor reale.
                    </p>
                  </div>
                </div>
              )}

              {/* Presence grid */}
              <div className="grid grid-cols-3 gap-2 text-[11px]">
                <div className="bg-card rounded px-2.5 py-2 border border-border">
                  <p className="text-muted-foreground uppercase text-[9px] tracking-wide">Comandă</p>
                  <p className={`mt-1 font-semibold ${obs.has_order ? "text-blue-600 dark:text-blue-300" : "text-muted-foreground"}`}>
                    {obs.has_order ? "prezent" : "lipsă"}
                  </p>
                </div>
                <div className="bg-card rounded px-2.5 py-2 border border-border">
                  <p className="text-muted-foreground uppercase text-[9px] tracking-wide">Plan</p>
                  <p className={`mt-1 font-semibold ${obs.has_plan ? "text-blue-600 dark:text-blue-300" : "text-muted-foreground"}`}>
                    {obs.has_plan ? "prezent" : "lipsă"}
                  </p>
                </div>
                <div className="bg-card rounded px-2.5 py-2 border border-border">
                  <p className="text-muted-foreground uppercase text-[9px] tracking-wide">Realitate</p>
                  <p className={`mt-1 font-semibold ${obs.has_reality ? "text-blue-600 dark:text-blue-300" : "text-muted-foreground"}`}>
                    {obs.has_reality ? "prezent" : "lipsă"}
                  </p>
                </div>
              </div>

              {/* Totals */}
              <div className="grid grid-cols-3 gap-2 text-[11px]">
                <div className="bg-card rounded px-2.5 py-2 border border-border">
                  <p className="text-muted-foreground uppercase text-[9px] tracking-wide">Planificat</p>
                  <p className="mt-1 text-foreground font-semibold tabular-nums">
                    {fmtMinutes(obs.plan_total_estimated_minutes)}
                  </p>
                </div>
                <div className="bg-card rounded px-2.5 py-2 border border-border">
                  <p className="text-muted-foreground uppercase text-[9px] tracking-wide">Actual</p>
                  <p className="mt-1 text-foreground font-semibold tabular-nums">
                    {fmtMinutes(obs.reality_total_actual_minutes)}
                  </p>
                </div>
                <div className="bg-card rounded px-2.5 py-2 border border-border">
                  <p className="text-muted-foreground uppercase text-[9px] tracking-wide">Δ (minute / %)</p>
                  <p className="mt-1 text-foreground font-semibold tabular-nums">
                    {fmtNumber(obs.delta_minutes)}
                    <span className="text-muted-foreground"> / </span>
                    {fmtPct(obs.delta_pct)}
                  </p>
                </div>
              </div>

              {/* Reasons */}
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1.5">
                  Motive
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {obs.reasons.length === 0 ? (
                    <span className="text-[11px] text-muted-foreground">—</span>
                  ) : (
                    obs.reasons.map((r) => <ReasonBadge key={r} code={r} />)
                  )}
                </div>
              </div>

              {/* Thresholds from backend response — NEVER hardcoded. */}
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1.5">
                  Praguri aplicate
                  <span className="ml-1 text-wo-text-dim normal-case">
                    (sursa: {obs.thresholds.source}
                    {obs.thresholds.is_active ? "" : ", inactivă"})
                  </span>
                </p>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="flex justify-between bg-card rounded px-2.5 py-1.5 border border-border">
                    <span className="text-muted-foreground">Warning (min)</span>
                    <span className="text-muted-foreground tabular-nums">
                      {fmtNumber(obs.thresholds.warning_time_delta_minutes)}
                    </span>
                  </div>
                  <div className="flex justify-between bg-card rounded px-2.5 py-1.5 border border-border">
                    <span className="text-muted-foreground">Warning (%)</span>
                    <span className="text-muted-foreground tabular-nums">
                      {fmtNumber(obs.thresholds.warning_time_delta_pct)}
                    </span>
                  </div>
                  <div className="flex justify-between bg-card rounded px-2.5 py-1.5 border border-border">
                    <span className="text-muted-foreground">Critical (min)</span>
                    <span className="text-muted-foreground tabular-nums">
                      {fmtNumber(obs.thresholds.critical_time_delta_minutes)}
                    </span>
                  </div>
                  <div className="flex justify-between bg-card rounded px-2.5 py-1.5 border border-border">
                    <span className="text-muted-foreground">Critical (%)</span>
                    <span className="text-muted-foreground tabular-nums">
                      {fmtNumber(obs.thresholds.critical_time_delta_pct)}
                    </span>
                  </div>
                </div>
              </div>

              <p className="text-[10px] text-wo-text-dim italic">
                Observat la: {fmtDateTime(obs.observed_at)}
              </p>
            </div>
          </section>

          {/* Alerts panel */}
          <section className="bg-wo-surface-raised border border-wo-border-strong rounded-lg">
            <header className="flex items-center justify-between px-4 py-3 border-b border-wo-border-strong">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                <h2 className="text-[13px] font-bold text-foreground uppercase tracking-wide">
                  Alerte
                </h2>
                {alerts && (
                  <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">
                    {alerts.alerts.length}
                  </span>
                )}
              </div>
              {alerts && (
                <span
                  className={`inline-block px-2.5 py-0.5 text-[11px] font-bold rounded border ${statusBadgeCls(alerts.status)}`}
                >
                  {statusLabel(alerts.status)}
                </span>
              )}
            </header>
            <div className="p-4">
              {!alerts ? (
                <p className="text-[12px] text-muted-foreground">Se încarcă alertele...</p>
              ) : alerts.status === "UNCONFIRMED" ? (
                <div className="flex items-start gap-2 bg-muted/40 border border-border rounded-md px-3 py-2">
                  <Info className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
                  <p className="text-[12px] text-muted-foreground">
                    <strong>NECONFIRMAT</strong> — date incomplete. Nu se poate
                    emite nicio alertă.
                  </p>
                </div>
              ) : alerts.alerts.length === 0 ? (
                <p className="text-[12px] text-muted-foreground">Nicio alertă activă.</p>
              ) : (
                <ul className="space-y-3">
                  {alerts.alerts.map((a, idx) => (
                    <li
                      key={`${a.order_id}-${a.metric}-${idx}`}
                      className="bg-card border border-border rounded-md p-3 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className={`inline-block px-2 py-0.5 text-[11px] font-bold rounded border ${statusBadgeCls(a.severity)}`}
                        >
                          {a.severity}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {fmtDateTime(a.created_at)}
                        </span>
                      </div>
                      <div className="text-[12px] text-foreground">
                        <ReasonBadge code={a.reason} />
                      </div>
                      <div className="grid grid-cols-4 gap-2 text-[11px]">
                        <div className="bg-wo-surface-inset rounded px-2 py-1.5 border border-border">
                          <p className="text-muted-foreground uppercase text-[9px]">Metric</p>
                          <p className="text-muted-foreground font-semibold">{a.metric}</p>
                        </div>
                        <div className="bg-wo-surface-inset rounded px-2 py-1.5 border border-border">
                          <p className="text-muted-foreground uppercase text-[9px]">Așteptat</p>
                          <p className="text-muted-foreground font-semibold tabular-nums">
                            {fmtNumber(a.expected_value)}
                          </p>
                        </div>
                        <div className="bg-wo-surface-inset rounded px-2 py-1.5 border border-border">
                          <p className="text-muted-foreground uppercase text-[9px]">Actual</p>
                          <p className="text-muted-foreground font-semibold tabular-nums">
                            {fmtNumber(a.actual_value)}
                          </p>
                        </div>
                        <div className="bg-wo-surface-inset rounded px-2 py-1.5 border border-border">
                          <p className="text-muted-foreground uppercase text-[9px]">Δ</p>
                          <p className="text-muted-foreground font-semibold tabular-nums">
                            {fmtNumber(a.delta)}
                          </p>
                        </div>
                      </div>
                      {a.reasons_all.length > 1 && (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {a.reasons_all.map((r) => (
                            <ReasonBadge key={r} code={r} />
                          ))}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>
        </div>
      )}

      {/* Acțiuni operaționale — Sprint #30 plan-generation gate. The button
          appears ONLY when the backend reports has_plan=false; it forwards
          the structured error code from the backend (snapshot_incomplete,
          plan_already_exists, ...) without interpretation or silent retry. */}
      {obs && (
        <section className="bg-wo-surface-raised border border-wo-border-strong rounded-lg">
          <header className="flex items-center gap-2 px-4 py-3 border-b border-wo-border-strong">
            <ActivitySquare className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-[13px] font-bold text-foreground uppercase tracking-wide">
              Acțiuni operaționale
            </h2>
          </header>
          <div className="p-4 space-y-3">
            {!obs.has_plan && (
              <div className="space-y-3">
                <div className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 dark:border-amber-800/60 dark:bg-amber-900/20">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
                  <div className="text-[12px] text-amber-900 dark:text-amber-200">
                    <p className="font-semibold">
                      Planul de execuție nu este generat
                    </p>
                    <p className="mt-0.5 text-amber-800/90 dark:text-amber-300/80">
                      Generarea planului este condiționată de un snapshot
                      canonical (product_definition + cost_result) salvat pe
                      comandă. Backend-ul este singura autoritate: dacă
                      snapshot-ul este incomplet sau în format vechi,
                      generarea va fi respinsă explicit.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    data-testid="execution-plan-generate-action"
                    onClick={async () => {
                      if (!isValidId) return;
                      setPlanSubmitting(true);
                      setPlanError(null);
                      setPlanSuccessAt(null);
                      try {
                        await executionApi.generatePlan(parsedId);
                        setPlanSuccessAt(new Date().toLocaleTimeString("ro-RO"));
                        // Reload observability + alerts so has_plan flips to
                        // true based on backend truth, not an optimistic update.
                        await load();
                      } catch (e) {
                        if (e instanceof PlanGenerationError) {
                          setPlanError(e);
                        } else {
                          const msg = e instanceof Error ? e.message : "unknown error";
                          setPlanError(
                            new PlanGenerationError(
                              "unknown",
                              0,
                              msg,
                              null,
                              null,
                              null,
                            ),
                          );
                        }
                      } finally {
                        setPlanSubmitting(false);
                      }
                    }}
                    disabled={planSubmitting || !isValidId}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold rounded-md bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-muted-foreground text-white transition-colors"
                  >
                    <PlayCircle
                      className={`w-3.5 h-3.5 ${planSubmitting ? "animate-pulse" : ""}`}
                    />
                    {planSubmitting
                      ? "Se generează planul..."
                      : "Generează plan de execuție"}
                  </button>
                  <span className="text-[11px] text-muted-foreground">
                    POST /api/v1/execution/plan/from-order/{parsedId}
                  </span>
                </div>
                {planError && (
                  <div
                    role="alert"
                    className="bg-red-900/20 border border-red-800/60 rounded-md px-3 py-2 space-y-1"
                  >
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0" />
                      <p className="text-[12px] font-semibold text-red-200">
                        {PLAN_ERROR_LABELS[planError.code] ??
                          PLAN_ERROR_LABELS.unknown}
                      </p>
                    </div>
                    <div className="text-[11px] text-red-600 dark:text-red-300/80 pl-6 space-y-0.5">
                      <p>
                        <span className="text-red-600 dark:text-red-400">HTTP {planError.httpStatus}</span>{" "}
                        <span className="text-muted-foreground">·</span>{" "}
                        <code className="text-red-600 dark:text-red-300">{planError.code}</code>
                      </p>
                      {planError.field && (
                        <p>
                          Câmp snapshot lipsă:{" "}
                          <code className="text-red-600 dark:text-red-300">{planError.field}</code>
                        </p>
                      )}
                      {planError.existingPlanId !== null && (
                        <p>
                          Plan existent:{" "}
                          <code className="text-red-600 dark:text-red-300">#{planError.existingPlanId}</code>
                        </p>
                      )}
                      {planError.message && planError.message !== planError.code && (
                        <p className="text-muted-foreground">
                          Mesaj backend:{" "}
                          <code className="text-muted-foreground">{planError.message}</code>
                        </p>
                      )}
                    </div>
                  </div>
                )}
                {planSuccessAt && !planError && (
                  <div className="flex items-center gap-2 bg-emerald-900/20 border border-emerald-800/60 rounded-md px-3 py-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                    <p className="text-[12px] text-emerald-200">
                      Plan generat la {planSuccessAt}. Datele de observabilitate
                      au fost reîmprospătate din backend.
                    </p>
                  </div>
                )}
              </div>
            )}

            {obs.has_plan && plan && (
              <div className="space-y-3">
                <OperatorProductionReleaseSummary
                  truth={taskTruthResponse}
                  onOpenDetails={() => setOwnerDetailsOpen(true)}
                />
                {ownerDetailsOpen ? (
                  <OperatorOwnerDecisionDetailsPanel
                    truth={taskTruthResponse}
                    defaultOpen
                    orderId={parsedId}
                    onResolved={refreshTaskTruth}
                  />
                ) : null}
              </div>
            )}

            {obs.has_plan && plan && (
              <RealityCapturePanel
                orderId={parsedId}
                plan={plan}
                reality={reality}
                loading={realityLoading}
                error={realityError}
                actionInFlightTaskId={realityActionTaskId}
                actionError={realityActionError}
                lastActionAt={realityActionAt}
                taskTruthByTaskId={taskTruthByTaskId}
                overrideReasonByTaskId={overrideReasonByTaskId}
                onOverrideReasonChange={(taskId, reason) => {
                  setOverrideReasonByTaskId((prev) => ({
                    ...prev,
                    [taskId]: reason,
                  }));
                }}
                onStartTask={async (taskId, options) => {
                  setRealityActionTaskId(taskId);
                  setRealityActionError(null);
                  try {
                    await executionApi.startTask(
                      parsedId,
                      taskId,
                      new Date().toISOString(),
                      {
                        overrideReadiness: options?.overrideReadiness,
                        overrideReason: options?.overrideReason,
                      },
                    );
                    setRealityActionAt(
                      new Date().toLocaleTimeString("ro-RO"),
                    );
                    // Refetch backend truth — no optimistic UI.
                    await loadRealityOnly(parsedId);
                    await load(); // observability may flip has_reality=true
                    try {
                      const truth = await fetchOperatorTaskTruth(parsedId);
                      setTaskTruthResponse(truth);
                      setTaskTruthByTaskId(indexOperatorTaskTruth(truth.tasks));
                    } catch {
                      /* keep prior truth */
                    }
                  } catch (e) {
                    if (e instanceof RealityActionError) {
                      setRealityActionError(e);
                    } else {
                      const msg =
                        e instanceof Error ? e.message : "unknown error";
                      setRealityActionError(
                        new RealityActionError(
                          "unknown",
                          "unknown",
                          0,
                          msg,
                          null,
                          null,
                        ),
                      );
                    }
                  } finally {
                    setRealityActionTaskId(null);
                  }
                }}
                onEndTask={async (taskId) => {
                  setRealityActionTaskId(taskId);
                  setRealityActionError(null);
                  try {
                    await executionApi.endTask(
                      parsedId,
                      taskId,
                      new Date().toISOString(),
                    );
                    setRealityActionAt(
                      new Date().toLocaleTimeString("ro-RO"),
                    );
                    await loadRealityOnly(parsedId);
                    await load();
                  } catch (e) {
                    if (e instanceof RealityActionError) {
                      setRealityActionError(e);
                    } else {
                      const msg =
                        e instanceof Error ? e.message : "unknown error";
                      setRealityActionError(
                        new RealityActionError(
                          "unknown",
                          "unknown",
                          0,
                          msg,
                          null,
                          null,
                        ),
                      );
                    }
                  } finally {
                    setRealityActionTaskId(null);
                  }
                }}
              />
            )}

            {obs.has_plan && obs.has_reality && (
              <p className="text-[12px] text-muted-foreground">
                Planul și realitatea sunt ambele prezente. Acțiunile rămân
                valide exclusiv prin endpoint-urile backend-ului; UI-ul nu
                calculează, nu prezice și nu modifică realitatea în memoria
                clientului.
              </p>
            )}
          </div>
        </section>
      )}

      {/* Wave 4 — closure readiness first; then post-job / profitability truth */}
      {obs && isValidId && <ExecutionClosurePanel orderId={parsedId} />}

      {/* Post-job truth — actuals, reconciliation, profitability coverage */}
      {obs && isValidId && (
        <PostJobTruthPanel orderId={parsedId} />
      )}

      {obs && isValidId && (
        <>
          <ProfitabilityActualReadPanel orderId={parsedId} />
          <div
            className="rounded-md border border-amber-300/50 bg-amber-50/80 px-3 py-2 dark:border-amber-700/40 dark:bg-amber-950/20"
            data-testid="profitability-analysis-legacy-label"
          >
            <p className="text-[11px] font-semibold text-amber-900 dark:text-amber-200">
              Legacy — ProfitabilityAnalysis
            </p>
            <p className="text-[10px] text-amber-800/90 dark:text-amber-300/80">
              Panou vechi, încă montat pentru comparație. Nu este autoritatea Actual Cost /
              Job Closure. Costurile și marjele reale rămân indisponibile până la decizia Owner.
            </p>
          </div>
          <ProfitabilityAnalysisPanel orderId={parsedId} />
        </>
      )}

      {/* BUILD 18 — Reality Quality Badge (Data Quality & Invalid Reality Marker) */}
      {obs && isValidId && obs.has_reality && reality && (
        <section className="bg-card border border-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-foreground mb-3">
            Calitate Date Reality
          </h3>
          <RealityQualityBadge realityId={reality.id} />
        </section>
      )}

      {/* S16 — Stock Deduction Panel (BUILD 16: Inventory Operational Loop) */}
      {obs && isValidId && obs.has_reality && (
        <section className="bg-card border border-border rounded-lg p-4">
          <StockDeductionPanel orderId={parsedId} />
        </section>
      )}

      {/* S30 — Gate Evaluation + ProductSystem Preview (read-only visibility) */}
      {obs && isValidId && (
        <GatePreviewSection orderId={parsedId} />
      )}

      <p className="text-[10px] text-wo-text-dim italic">
        Toate valorile provin din backend. UI nu calculează, nu prezice și nu
        substituie valori lipsă.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// GatePreviewSection — S30 read-only visibility.
//
// Displays the gate evaluation result and ProductSystem execution preview.
// Pure read-only: GET only, no mutations, no forms, no POST/PUT/PATCH/DELETE.
// ---------------------------------------------------------------------------
function GatePreviewSection({ orderId }: { orderId: number }) {
  const gate = useGateEvaluation(orderId);
  const preview = useProductSystemPreview(orderId);

  // Loading state
  if (gate.loading && !gate.data) {
    return (
      <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
        <div className="flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500"></div>
          <p className="text-[12px] text-muted-foreground">
            Se încarcă evaluarea gate / ProductSystem preview...
          </p>
        </div>
      </div>
    );
  }

  // Error state (gate endpoint failed)
  if (gate.error && !gate.data) {
    return (
      <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
        <div className="flex items-start gap-2 bg-red-900/20 border border-red-800/60 rounded-md px-3 py-2">
          <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
          <div className="text-[12px] text-red-600 dark:text-red-300">
            <p className="font-semibold">Gate evaluation indisponibilă</p>
            <p className="text-[11px] text-red-600 dark:text-red-300/70 mt-0.5">
              {gate.error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // No data available
  if (!gate.data) return null;

  const handleRefresh = () => {
    void gate.refresh();
    void preview.refresh();
  };

  return (
    <div className="space-y-4">
      {/* Gate verdict */}
      <GateVerdictCard
        gate={gate.data}
        loading={gate.loading}
        onRefresh={handleRefresh}
      />

      {/* ProductSystem preview */}
      {preview.data && (
        <ProductSystemPreviewPanel preview={preview.data} />
      )}

      {/* Preview loading */}
      {preview.loading && !preview.data && (
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500"></div>
            <p className="text-[12px] text-muted-foreground">
              Se încarcă ProductSystem preview...
            </p>
          </div>
        </div>
      )}

      {/* Preview error */}
      {preview.error && (
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
          <div className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 dark:border-amber-800/60 dark:bg-amber-900/20">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <div className="text-[12px] text-amber-900 dark:text-amber-300">
              <p className="font-semibold">ProductSystem preview indisponibil</p>
              <p className="mt-0.5 text-[11px] text-amber-800/90 dark:text-amber-300/70">
                {preview.error}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// RealityCapturePanel — Sprint #36.
//
// Operator action surface for the canonical reality-capture flow:
//   - Start task   -> POST /api/v1/execution/reality/start-task
//   - Complete task -> POST /api/v1/execution/reality/end-task
//
// Strict rules enforced by this component:
//   - Task list is taken from the PLAN contract (planned source of truth).
//     The UI never invents task_ids. A task shown here exists in the plan.
//   - Per-task action buttons reflect backend status only:
//       * not_started -> "Start" visible, "Complete" disabled
//       * in_progress -> "Start" disabled, "Complete" visible
//       * completed   -> both disabled with a completed badge
//   - No optimistic UI: every click awaits backend response, then the
//     parent refetches both reality and observability.
//   - When reality is absent, the panel still lists plan tasks and shows
//     the canonical empty-state callout (NOT a red error).
//   - Backend-rejected actions (duplicate start, end-before-start, etc.)
//     surface the structured backend code + detail verbatim.
// ---------------------------------------------------------------------------
interface RealityCapturePanelProps {
  orderId: number;
  plan: ExecutionPlanResponse;
  reality: ExecutionRealityResponse | null;
  loading: boolean;
  error: string | null;
  actionInFlightTaskId: string | null;
  actionError: RealityActionError | null;
  lastActionAt: string | null;
  taskTruthByTaskId: Record<string, OperatorTaskTruthTask>;
  overrideReasonByTaskId: Record<string, string>;
  onOverrideReasonChange: (taskId: string, reason: string) => void;
  onStartTask: (
    taskId: string,
    options?: { overrideReadiness?: boolean; overrideReason?: string },
  ) => Promise<void>;
  onEndTask: (taskId: string) => Promise<void>;
}

function RealityCapturePanel(props: RealityCapturePanelProps) {
  const {
    orderId,
    plan,
    reality,
    loading,
    error,
    actionInFlightTaskId,
    actionError,
    lastActionAt,
    taskTruthByTaskId,
    overrideReasonByTaskId,
    onOverrideReasonChange,
    onStartTask,
    onEndTask,
  } = props;

  const [registryMappings, setRegistryMappings] = useState<OperationResourceMapping[]>([]);
  const collabUiEnabled = isFlexCollabUiEnabled();
  const [collabRead, setCollabRead] = useState<OrderTaskCollaborationReadDTO | null>(null);
  const [collabError, setCollabError] = useState<string | null>(null);

  const reloadCollab = useCallback(async () => {
    if (!collabUiEnabled) {
      setCollabRead(null);
      setCollabError(null);
      return;
    }
    try {
      const payload = await fetchOrderTaskCollaborationRead(orderId);
      setCollabRead(payload);
      setCollabError(null);
    } catch (e) {
      setCollabError(
        e instanceof Error ? e.message : "Nu am putut încărca colaborarea.",
      );
    }
  }, [collabUiEnabled, orderId]);

  useEffect(() => {
    let cancelled = false;
    operationalRegistryApi
      .listOperationMappings()
      .then((res) => {
        if (!cancelled) setRegistryMappings(res.items);
      })
      .catch(() => {
        if (!cancelled) setRegistryMappings([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    void reloadCollab();
  }, [reloadCollab, lastActionAt]);

  const totalActual =
    reality && Number.isFinite(reality.total_actual_time_minutes)
      ? reality.total_actual_time_minutes
      : null;

  return (
    <section className="space-y-3 pt-2 border-t border-wo-border-strong">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ActivitySquare className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <h3 className="text-[13px] font-bold text-foreground uppercase tracking-wide">
            Înregistrare execuție reală
          </h3>
          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">
            {plan.tasks.length} task-uri în plan
          </span>
          {plan.operational_readiness_status ? (
            <span
              className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded border ${operationalReadinessBadgeClasses(plan.operational_readiness_status)}`}
              data-testid="execution-plan-operational-readiness"
              title={plan.operational_readiness_status}
            >
              {operationalReadinessLabel(plan.operational_readiness_status)}
            </span>
          ) : null}
          {plan.prepared_by_user_id ? (
            <span className="text-[10px] text-muted-foreground">
              Instrumentare: {plan.prepared_by_user_id}
            </span>
          ) : null}
        </div>
        {lastActionAt && (
          <span className="text-[11px] text-emerald-600 dark:text-emerald-400">
            Ultima acțiune: {lastActionAt}
          </span>
        )}
      </div>

      {!reality && !loading && !error && (
        <div
          role="status"
          className="flex items-start gap-2 bg-muted/40 border border-border rounded-md px-3 py-2"
        >
          <Info className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
          <p className="text-[12px] text-muted-foreground">
            Execution reality nu a fost încă înregistrată. Pornește un task
            pentru a iniția realitatea pe această comandă.
          </p>
        </div>
      )}

      {error && (
        <div className="bg-red-900/20 border border-red-800/60 rounded-md px-3 py-2 text-[11px] text-red-600 dark:text-red-300">
          Eroare la încărcarea realității: <code>{error}</code>
        </div>
      )}

      {actionError && (
        <OperatorStructuredActionError
          error={{
            code: actionError.rawCode,
            rawCode: actionError.rawCode,
            httpStatus: actionError.httpStatus,
            message: actionError.message,
            detail: actionError.detail,
            blockers: actionError.blockers,
            readinessLabel: actionError.readinessLabel,
            raw: actionError.raw,
          }}
          testId="execution-structured-start-error"
        />
      )}

      {(() => {
        const next = resolveExecutionNextAction(
          plan.tasks,
          reality,
          taskTruthByTaskId,
        );
        const tone =
          next.kind === "blocked"
            ? "border-amber-200 bg-amber-50 text-amber-950 dark:border-amber-800/50 dark:bg-amber-950/25 dark:text-amber-100"
            : next.kind === "idle"
              ? "border-wo-border-subtle bg-wo-surface-raised text-wo-text-secondary"
              : "border-blue-200 bg-blue-50 text-blue-950 dark:border-blue-800/50 dark:bg-blue-950/25 dark:text-blue-100";
        return (
          <div
            className={`rounded-lg border px-3 py-2.5 space-y-1 ${tone}`}
            data-testid="execution-next-action"
            data-next-kind={next.kind}
          >
            <p className="text-[10px] font-semibold uppercase tracking-wide opacity-80">
              Decizie operator — first fold
            </p>
            {next.kind === "start" || next.kind === "complete" || next.kind === "blocked" ? (
              <p className="text-[13px] font-semibold" data-testid="execution-next-action-label">
                {next.kind === "start"
                  ? `Start: ${next.label}`
                  : next.kind === "complete"
                    ? `Complete: ${next.label}`
                    : `Blocat: ${next.label}`}
              </p>
            ) : null}
            <p className="text-[11px] opacity-90">{next.hint}</p>
            {next.kind === "blocked" && next.blockedBy.length > 0 ? (
              <p className="text-[11px] font-medium" data-testid="execution-next-action-blocked-by">
                Blocat de: {next.blockedBy.join(", ")}
              </p>
            ) : null}
          </div>
        );
      })()}

      <div className="bg-wo-surface-inset border border-border rounded-md overflow-hidden">
        <table className="w-full text-[12px]">
          <thead className="bg-card text-muted-foreground uppercase text-[10px] tracking-wide">
            <tr>
              <th className="text-left px-3 py-2">Task</th>
              <th className="text-left px-3 py-2">Proces / Mașină</th>
              <th className="text-right px-3 py-2">Planificat</th>
              <th className="text-right px-3 py-2">Actual</th>
              <th className="text-left px-3 py-2">Status</th>
              <th className="text-right px-3 py-2">Acțiuni</th>
            </tr>
          </thead>
          <tbody>
            {plan.tasks.map((t: PlannedTaskRow) => {
              const { status, observation } = computeTaskStatus(
                t.task_id,
                reality,
              );
              const actualMin = computeActualMinutes(observation);
              const inFlight = actionInFlightTaskId === t.task_id;
              const truth = taskTruthByTaskId[t.task_id];
              const collabTask = collabRead?.tasks.find(
                (item) => item.task_id === t.task_id,
              );
              const completeBlockedByCollab =
                collabUiEnabled &&
                collabTask?.can_complete_operation === false;
              const readiness: TaskTruthReadiness | undefined = truth
                ? taskTruthReadinessFromRuntime(truth.runtime)
                : undefined;
              const startBlockedByReadiness =
                status === "not_started" && readiness?.is_startable === false;
              const readinessMessage =
                (readiness?.readiness_reasons?.[0] as { message?: string } | undefined)
                  ?.message ||
                (readiness?.blocking_reasons?.[0] as { message?: string } | undefined)
                  ?.message ||
                readiness?.readiness_label;
              const overrideReason = overrideReasonByTaskId[t.task_id] ?? "";
              const canOverrideStart =
                startBlockedByReadiness && overrideReason.trim().length >= 3;
              const statusLabel: Record<RealityTaskStatus, string> = {
                not_started: "Nu a pornit",
                in_progress: "În curs",
                completed: "Finalizat",
              };
              const statusCls: Record<RealityTaskStatus, string> = {
                not_started:
                  "bg-muted/60 text-muted-foreground border-slate-600",
                in_progress:
                  "bg-amber-50 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-700",
                completed:
                  "bg-emerald-50 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-700",
              };

              return (
                <tr
                  key={t.task_id}
                  className="border-t border-border hover:bg-card/40"
                >
                  <td className="px-3 py-2">
                    <OperatorTaskIdentityPresentation
                      truth={truth}
                      fallbackOperationName={t.name}
                      fallbackTaskId={t.task_id}
                      showDiagnostics
                      testId={`execution-task-identity-${t.task_id}`}
                    />
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">
                    <code className="text-[11px] text-muted-foreground">
                      {t.process_type}
                    </code>
                    <span className="mx-1 text-wo-text-dim">·</span>
                    <code className="text-[11px] text-muted-foreground">
                      {t.machine_type}
                    </code>
                    {t.process_type && (
                      <OperationRegistryMappingBadge
                        operationCode={t.process_type}
                        mappings={registryMappings}
                      />
                    )}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-foreground">
                    {fmtMinutes(t.estimated_time_minutes)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {actualMin === null ? (
                      <span className="text-muted-foreground">—</span>
                    ) : (
                      <span className="text-foreground">
                        {actualMin.toFixed(1)} min
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`inline-block px-2 py-0.5 text-[10px] font-bold rounded border ${statusCls[status]}`}
                    >
                      {statusLabel[status]}
                    </span>
                    {observation?.started_at && (
                      <div className="text-[10px] text-muted-foreground mt-0.5">
                        Start: {fmtDateTime(observation.started_at)}
                      </div>
                    )}
                    {observation?.ended_at && (
                      <div className="text-[10px] text-muted-foreground">
                        End: {fmtDateTime(observation.ended_at)}
                      </div>
                    )}
                    {startBlockedByReadiness && readinessMessage ? (
                      <div className="text-[10px] text-amber-600 dark:text-amber-400/90 mt-1 max-w-[220px]">
                        {readinessMessage}
                      </div>
                    ) : null}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="inline-flex flex-col items-end gap-1">
                      {startBlockedByReadiness ? (
                        <input
                          type="text"
                          value={overrideReason}
                          onChange={(e) =>
                            onOverrideReasonChange(t.task_id, e.target.value)
                          }
                          placeholder="Motiv override (min. 3 car.)"
                          className="w-[180px] rounded border border-amber-800/60 bg-background px-2 py-1 text-[10px] text-foreground placeholder:text-muted-foreground"
                        />
                      ) : null}
                      <div className="inline-flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() =>
                          void onStartTask(t.task_id, {
                            overrideReadiness: canOverrideStart,
                            overrideReason: canOverrideStart
                              ? overrideReason.trim()
                              : undefined,
                          })
                        }
                        disabled={
                          inFlight ||
                          status === "in_progress" ||
                          status === "completed" ||
                          (startBlockedByReadiness && !canOverrideStart)
                        }
                        className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-semibold rounded bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-muted-foreground text-white transition-colors"
                        title={
                          startBlockedByReadiness && !canOverrideStart
                            ? readinessMessage || "Task nepregătit"
                            : undefined
                        }
                      >
                        <PlayCircle
                          className={`w-3 h-3 ${inFlight && status === "not_started" ? "animate-pulse" : ""}`}
                        />
                        Start
                      </button>
                      <button
                        type="button"
                        onClick={() => void onEndTask(t.task_id)}
                        disabled={
                          inFlight ||
                          status !== "in_progress" ||
                          completeBlockedByCollab
                        }
                        className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-semibold rounded bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-muted-foreground text-white transition-colors"
                        title={
                          completeBlockedByCollab
                            ? "Complete permis doar când can_complete_operation este true"
                            : undefined
                        }
                      >
                        <CheckCircle2
                          className={`w-3 h-3 ${inFlight && status === "in_progress" ? "animate-pulse" : ""}`}
                        />
                        Complete
                      </button>
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot className="bg-card text-[11px]">
            <tr className="border-t border-border">
              <td
                colSpan={2}
                className="px-3 py-2 text-muted-foreground uppercase text-[10px] tracking-wide"
              >
                Total
              </td>
              <td className="px-3 py-2 text-right tabular-nums text-foreground">
                {plan.total_estimated_time_minutes.toFixed(1)} min
              </td>
              <td className="px-3 py-2 text-right tabular-nums">
                {totalActual === null ? (
                  <span className="text-muted-foreground">—</span>
                ) : (
                  <span className="text-foreground">
                    {totalActual.toFixed(1)} min
                  </span>
                )}
              </td>
              <td colSpan={2} className="px-3 py-2 text-right text-[10px] text-muted-foreground">
                POST /reality/start-task · /end-task (order #{orderId})
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <p className="text-[10px] text-wo-text-dim italic">
        Acțiunile sunt executate pe backend. După fiecare acțiune, UI-ul
        reîncarcă realitatea — nu există optimistic success.
      </p>

      {collabUiEnabled ? (
        <div
          className="space-y-2 pt-2 border-t border-wo-border-strong"
          data-testid="execution-collaboration-section"
        >
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-[12px] font-bold text-muted-foreground uppercase tracking-wide">
              Colaborare flex (ajutor / helpers / sesiuni)
            </h4>
            <button
              type="button"
              className="text-[10px] text-muted-foreground hover:text-foreground underline"
              onClick={() => void reloadCollab()}
            >
              Reîncarcă colaborarea
            </button>
          </div>
          {collabError ? (
            <p className="text-[11px] text-rose-300" role="alert">
              {collabError}
            </p>
          ) : null}
          {(collabRead?.tasks || []).map((task) => (
            <OperatorTaskCollaborationPanel
              key={task.task_id}
              orderId={orderId}
              task={task}
              onChanged={reloadCollab}
              testIdPrefix="execution-collab"
            />
          ))}
          {collabRead && collabRead.tasks.length === 0 ? (
            <p className="text-[11px] text-muted-foreground">
              Niciun task operațional în proiecția de colaborare.
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}