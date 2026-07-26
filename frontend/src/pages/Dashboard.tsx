import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDashboardStats } from "@/hooks/useDashboardStats";
import { CapacityNotice } from "@/components/workos/design-system";
import type { KPIMetricKind, KPIValue, OperationalTruth } from "@/lib/mockData";
import {
  AlertTriangle,
  Activity,
  Zap,
  Database,
  HardDrive,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  ChevronUp,
  Gauge,
  Plus,
  FileText,
  ShoppingCart,
  Factory,
  BarChart3,
  Info,
} from "lucide-react";

/* ─── Status Header ─── */
function StatusHeader({
  source,
  loading,
  lastUpdate,
  onRefresh,
}: {
  source: string;
  loading: boolean;
  lastUpdate: Date;
  onRefresh: () => void;
}) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5 bg-wo-surface-raised border border-wo-border-subtle rounded-lg">
      <div className="flex items-center gap-3">
        {source === "db" ? (
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
            </span>
            <span className="text-sm text-green-400 font-medium" data-testid="dashboard-data-source">
              Date disponibile
            </span>
            <Database className="w-3.5 h-3.5 text-green-400/60" />
          </div>
        ) : source === "mock" ? (
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span className="text-sm text-amber-400 font-medium">Demo</span>
            <HardDrive className="w-3.5 h-3.5 text-amber-400/60" />
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-500 animate-pulse" />
            <span className="text-sm text-wo-text-muted">Conectare...</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <span className="text-xs text-wo-text-muted font-mono">
          {lastUpdate.toLocaleTimeString("ro-RO", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-1.5 rounded-md hover:bg-wo-hover transition-colors disabled:opacity-50"
        >
          <RefreshCw
            className={`w-4 h-4 text-wo-text-muted ${loading ? "animate-spin" : ""}`}
          />
        </button>
      </div>
    </div>
  );
}

const KIND_BADGE: Record<
  KPIMetricKind,
  { label: string; className: string }
> = {
  actual: {
    label: "actual",
    className:
      "border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-500/30 dark:bg-blue-500/15 dark:text-blue-300",
  },
  planned: {
    label: "planificat",
    className:
      "border-slate-200 bg-slate-100 text-slate-700 dark:border-slate-500/30 dark:bg-slate-500/15 dark:text-slate-300",
  },
  derived: {
    label: "derivat",
    className:
      "border-cyan-200 bg-cyan-50 text-cyan-700 dark:border-cyan-500/30 dark:bg-cyan-500/15 dark:text-cyan-300",
  },
  proxy: {
    label: "proxy",
    className:
      "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/15 dark:text-amber-300",
  },
  placeholder: {
    label: "gap",
    className: "bg-wo-hover text-wo-text-muted border-wo-border-subtle",
  },
};

/* ─── KPI Card ─── */
function KPICardLarge({
  label,
  value,
  unit,
  trend,
  trendValue,
  status,
  icon,
  kind,
  explanation,
  gapNote,
  window,
}: {
  label: string;
  value: number;
  unit: string;
  trend: "up" | "down" | "stable";
  trendValue: number;
  status: "good" | "warning" | "critical";
  icon: React.ReactNode;
  kind?: KPIMetricKind;
  explanation?: string;
  gapNote?: string;
  window?: string;
}) {
  const statusStyles = {
    good: {
      border: "border-wo-border-subtle",
      bg: "bg-wo-surface-raised",
      value: "text-wo-text-primary",
      iconColor: "text-green-600 dark:text-green-400",
    },
    warning: {
      border: "border-amber-200 dark:border-amber-900/40",
      bg: "bg-wo-surface-raised",
      value: "text-amber-800 dark:text-amber-300",
      iconColor: "text-amber-600 dark:text-amber-400",
    },
    critical: {
      border: "border-red-200 dark:border-red-900/40",
      bg: "bg-wo-surface-raised",
      value: "text-red-700 dark:text-red-300",
      iconColor: "text-red-600 dark:text-red-400",
    },
  };

  const style = statusStyles[status];

  const TrendIcon =
    trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const trendColor =
    trend === "up"
      ? status === "critical" || status === "warning"
        ? "text-red-400"
        : "text-green-400"
      : trend === "down"
        ? status === "critical" || status === "warning"
          ? "text-green-400"
          : "text-red-400"
        : "text-wo-text-muted";

  // Defensive display for % KPIs: never render absurd values like 56596%.
  // Backend is the source of truth; this only caps presentation.
  const displayValue =
    unit === "%"
      ? value > 100
        ? ">100"
        : value < 0
          ? "0"
          : value
      : value;

  const kindMeta = kind ? KIND_BADGE[kind] : null;

  return (
    <div
      className={`rounded-lg border p-4 transition-all duration-300 ${style.border} ${style.bg}`}
      title={explanation || gapNote || undefined}
      data-kpi-kind={kind || "unknown"}
      data-kpi-window={window || ""}
    >
      <div className="flex items-center justify-between mb-2">
        <span className={style.iconColor}>{icon}</span>
        <div className="flex items-center gap-1.5">
          {kindMeta && (
            <span
              className={`text-[9px] uppercase tracking-wide px-1.5 py-0.5 rounded border font-semibold ${kindMeta.className}`}
            >
              {kindMeta.label}
            </span>
          )}
          {trendValue !== 0 && (
            <div className={`flex items-center gap-0.5 ${trendColor}`}>
              <TrendIcon className="w-3.5 h-3.5" />
              <span className="text-xs font-medium">
                {trendValue > 0 ? "+" : ""}
                {trendValue}
              </span>
            </div>
          )}
        </div>
      </div>
      <p className={`text-3xl font-bold ${style.value}`}>
        {displayValue}
        {unit && <span className="text-lg ml-0.5 opacity-60">{unit}</span>}
      </p>
      <p className="text-xs text-wo-text-muted mt-1.5 font-medium">{label}</p>
      {explanation && (
        <p className="text-[10px] text-wo-text-muted/80 mt-1 leading-snug line-clamp-2">
          {explanation}
        </p>
      )}
      {gapNote && (
        <p
          className="text-[10px] text-amber-400/90 mt-1 leading-snug line-clamp-2"
          data-testid="kpi-gap-note"
        >
          Gap: {gapNote}
        </p>
      )}
    </div>
  );
}

/* ─── Truth notices ─── */
function OperationalTruthBanner({ truth }: { truth: OperationalTruth | null }) {
  if (!truth) return null;
  const notices = truth.notices?.length
    ? truth.notices
    : [
        "Utilaj calendar/shift: date indisponibile — afișăm load planificat 0–100 pe workcenter.",
      ];

  return (
    <div
      className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 space-y-2 dark:border-amber-800/40 dark:bg-amber-950/20"
      data-testid="dashboard-operational-truth"
      role="note"
    >
      <div className="flex items-center gap-2">
        <Info className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <h3 className="text-xs font-semibold text-amber-900 dark:text-amber-200">
          Adevăr operațional (Dashboard)
        </h3>
        {!truth.calendarShiftUtilAvailable && (
          <span className="rounded border border-amber-300 bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-800 dark:border-amber-600/40 dark:bg-amber-900/30 dark:text-amber-300">
            fără util calendar/shift
          </span>
        )}
      </div>
      <ul className="space-y-1">
        {notices.slice(0, 3).map((n) => (
          <li
            key={n}
            className="flex gap-1.5 text-[11px] leading-snug text-amber-900/90 dark:text-amber-100/80"
          >
            <span className="shrink-0 text-amber-600 dark:text-amber-500">•</span>
            <span>{n}</span>
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-3 pt-1 font-mono text-[10px] text-wo-text-muted">
        <span>Planificat: {truth.plannedMinutesTotal ?? 0} min</span>
        <span className="text-blue-700 dark:text-blue-300">
          Actual: {truth.actualMinutesTotal ?? 0} min
        </span>
        <span className="text-red-700 dark:text-red-300">
          Overrun: {truth.overrunMinutesTotal ?? 0} min
        </span>
        <span>Fereastră throughput: {truth.throughputWindow}</span>
      </div>
    </div>
  );
}

/* ─── Summary Bar — mutually exclusive buckets ─── */
function SummaryBar({
  planned,
  inExecution,
  blocked,
  completed,
  late,
}: {
  planned: number;
  inExecution: number;
  blocked: number;
  completed: number;
  late: number;
}) {
  const total = planned + inExecution + blocked + completed;
  const segments = [
    { label: "Finalizate", count: completed, color: "bg-green-500", tone: "actual" },
    { label: "În execuție", count: inExecution, color: "bg-blue-500", tone: "actual" },
    { label: "Blocate", count: blocked, color: "bg-red-500", tone: "blocked" },
    { label: "Planificate", count: planned, color: "bg-slate-500", tone: "planned" },
  ];

  return (
    <div
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4"
      data-testid="dashboard-summary-bar"
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-wo-text-primary">
            Sumar producție — planificat / actual / blocat
          </h3>
          <p className="text-[10px] text-wo-text-muted mt-0.5">
            Segmente exclusive: planificate (pending/scheduled) · în execuție · blocate · finalizate
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-wo-text-muted">
          <span>{total} job-uri</span>
          {late > 0 && (
            <span className="text-amber-400 font-medium border border-amber-700/40 rounded px-1.5 py-0.5">
              {late} late
            </span>
          )}
        </div>
      </div>

      <div className="h-2.5 rounded-full bg-wo-border-subtle overflow-hidden flex mb-3">
        {segments.map(
          (seg) =>
            seg.count > 0 && (
              <div
                key={seg.label}
                className={`${seg.color} transition-all duration-700`}
                style={{ width: `${(seg.count / Math.max(total, 1)) * 100}%` }}
                title={`${seg.label} (${seg.tone}): ${seg.count}`}
              />
            )
        )}
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        {segments.map((seg) => (
          <div key={seg.label} className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-sm ${seg.color}`} />
            <span className="text-xs text-wo-text-muted">
              {seg.label}:{" "}
              <span className="text-wo-text-primary font-medium">{seg.count}</span>
              <span className="text-[10px] text-wo-text-muted/70 ml-1">({seg.tone})</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Risk Card ─── */
function RiskCard({
  job,
}: {
  job: {
    id: string;
    client: string;
    product: string;
    riskLevel: string;
    riskReason: string | null;
    progress: number;
    isLate: boolean;
    isBlocked: boolean;
    promisedAt: string;
    currentOperation: string;
  };
}) {
  const riskStyles = {
    high: {
      border: "border-red-200 dark:border-red-900/50",
      bg: "bg-red-50 dark:bg-red-950/20",
      badge:
        "border-red-200 bg-red-100 text-red-700 dark:border-red-500/30 dark:bg-red-500/15 dark:text-red-400",
    },
    medium: {
      border: "border-amber-200 dark:border-amber-900/50",
      bg: "bg-amber-50 dark:bg-amber-950/15",
      badge:
        "border-amber-200 bg-amber-100 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/15 dark:text-amber-400",
    },
    low: {
      border: "border-blue-200 dark:border-blue-900/50",
      bg: "bg-blue-50 dark:bg-blue-950/15",
      badge:
        "border-blue-200 bg-blue-100 text-blue-700 dark:border-blue-500/30 dark:bg-blue-500/15 dark:text-blue-400",
    },
  };

  const style =
    riskStyles[job.riskLevel as keyof typeof riskStyles] || riskStyles.low;

  return (
    <div className={`rounded-lg border p-3.5 transition-all ${style.border} ${style.bg}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-blue-300 font-medium">
            {job.id}
          </span>
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold uppercase ${style.badge}`}
          >
            {job.riskLevel}
          </span>
          {job.isBlocked && (
            <span className="rounded border border-red-200 bg-red-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-300">
              blocked
            </span>
          )}
          {!job.isBlocked && job.isLate && (
            <span className="rounded border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-300">
              late
            </span>
          )}
        </div>
        {job.isBlocked && (
          <XCircle className="h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
        )}
        {!job.isBlocked && job.isLate && (
          <Clock className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
        )}
      </div>

      <p className="text-sm text-wo-text-primary font-medium truncate">
        {job.client}
      </p>
      <p className="text-xs text-wo-text-muted truncate mt-0.5">{job.product}</p>

      {job.riskReason && (
        <p className="text-xs text-red-300/70 mt-1.5 italic">
          {job.riskReason}
        </p>
      )}

      <div className="flex items-center gap-2 mt-2.5">
        <div className="flex-1 bg-wo-border-subtle rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-1.5 rounded-full transition-all duration-700 ${
              job.progress >= 60
                ? "bg-green-500"
                : job.progress >= 30
                  ? "bg-blue-500"
                  : "bg-amber-500"
            }`}
            style={{ width: `${job.progress}%` }}
          />
        </div>
        <span className="text-xs text-wo-text-muted font-mono w-8 text-right">
          {job.progress}%
        </span>
      </div>

      <div className="flex items-center justify-between mt-2">
        <span className="text-[11px] text-wo-text-muted">
          {job.currentOperation !== "—" ? job.currentOperation : "În așteptare"}
        </span>
        <span
          className={`text-[11px] ${job.isLate ? "text-red-400 font-medium" : "text-wo-text-muted"}`}
        >
          {job.promisedAt}
        </span>
      </div>
    </div>
  );
}

/* ─── Active Job Row ─── */
function ActiveJobRow({
  job,
}: {
  job: {
    id: string;
    client: string;
    product: string;
    progress: number;
    currentOperation: string;
    currentWorkcenter: string;
    priority: string;
    operationsCompleted: number;
    operationsTotal: number;
  };
}) {
  const priorityColors = {
    urgent: "bg-red-500",
    high: "bg-amber-500",
    normal: "bg-blue-500",
    low: "bg-slate-500",
  };

  return (
    <div className="flex items-center gap-3 py-2.5 px-3 rounded-md hover:bg-wo-hover transition-colors group">
      <span
        className={`w-1.5 h-8 rounded-full shrink-0 ${priorityColors[job.priority as keyof typeof priorityColors] || "bg-slate-500"}`}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-blue-300">{job.id}</span>
          <span className="text-sm text-wo-text-primary truncate">{job.client}</span>
          <span className="text-[9px] uppercase tracking-wide px-1 py-0.5 rounded border border-blue-500/30 text-blue-300 bg-blue-500/10">
            actual
          </span>
        </div>
        <p className="text-xs text-wo-text-muted truncate mt-0.5">
          {job.currentOperation !== "—"
            ? `${job.currentOperation} · ${job.currentWorkcenter}`
            : job.product}
        </p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <div className="w-20">
          <div className="w-full bg-wo-border-subtle rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-blue-500 h-1.5 rounded-full transition-all duration-700"
              style={{ width: `${job.progress}%` }}
            />
          </div>
        </div>
        <span className="text-xs text-wo-text-secondary font-mono w-8 text-right font-medium">
          {job.progress}%
        </span>
      </div>
    </div>
  );
}

/* ─── Alert Item ─── */
function AlertItemSimple({
  alert,
}: {
  alert: {
    id: string;
    severity: string;
    message: string;
    triggeredAt: string;
  };
}) {
  const severityStyles = {
    critical: "border-l-red-500 bg-red-950/15",
    warning: "border-l-amber-500 bg-amber-950/15",
    info: "border-l-blue-500 bg-blue-950/15",
  };

  const style =
    severityStyles[alert.severity as keyof typeof severityStyles] ||
    severityStyles.info;

  return (
    <div className={`border-l-2 rounded-r-md px-3 py-2 ${style}`}>
      <p className="text-xs text-wo-text-primary leading-relaxed">
        {alert.message}
      </p>
    </div>
  );
}

/* ─── Capacity Bar ─── */
function CapacityItem({
  name,
  load,
  plannedMinutes,
  actualMinutes,
  overrunMinutes,
}: {
  name: string;
  load: number;
  plannedMinutes?: number;
  actualMinutes?: number;
  overrunMinutes?: number;
}) {
  const barColor =
    load >= 90
      ? "bg-red-500"
      : load >= 75
        ? "bg-amber-500"
        : "bg-blue-500";
  const textColor =
    load >= 90
      ? "text-red-400"
      : load >= 75
        ? "text-amber-400"
        : "text-wo-text-secondary";
  const hasOverrun = (overrunMinutes ?? 0) > 0;

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="text-xs text-wo-text-muted w-20 truncate">{name}</span>
        <div className="flex-1 bg-wo-border-subtle rounded-full h-2 overflow-hidden">
          <div
            className={`h-2 rounded-full transition-all duration-700 ${barColor}`}
            style={{ width: `${Math.min(100, Math.max(0, load))}%` }}
          />
        </div>
        <span className={`text-xs font-mono font-medium w-9 text-right ${textColor}`}>
          {load}%
        </span>
      </div>
      <div className="flex items-center gap-2 pl-[5.5rem] text-[10px] text-wo-text-muted font-mono">
        <span>P {plannedMinutes ?? 0}m</span>
        <span className="text-blue-300/80">A {actualMinutes ?? 0}m</span>
        {hasOverrun && (
          <span className="text-red-300/90">OV +{overrunMinutes}m</span>
        )}
      </div>
    </div>
  );
}

function emptyKPI(code: string): KPIValue {
  return {
    code,
    label: "",
    value: 0,
    unit: "",
    trend: "stable",
    trendValue: 0,
    status: "good",
  };
}

/* ─── Main Dashboard ─── */
export default function Dashboard() {
  const navigate = useNavigate();
  const {
    kpis,
    jobs,
    capacity,
    alerts,
    operationalTruth,
    source,
    loading,
    lastUpdate,
    refresh,
  } = useDashboardStats(30000);

  const [showAllRisks, setShowAllRisks] = useState(false);

  // Mutually exclusive production buckets (no double-count blocked∩active)
  const blockedJobs = jobs.filter((j) => j.isBlocked);
  const blockedIds = new Set(blockedJobs.map((j) => j.id));
  const inExecutionJobs = jobs.filter(
    (j) => j.status === "in_progress" && !blockedIds.has(j.id),
  );
  const completedJobs = jobs.filter((j) => j.status === "completed");
  const plannedJobs = jobs.filter(
    (j) =>
      (j.status === "pending" || j.status === "scheduled") &&
      !blockedIds.has(j.id),
  );
  const lateJobs = jobs.filter((j) => j.isLate && j.status !== "completed");
  const riskyJobs = jobs
    .filter((j) => j.riskLevel !== "none" || j.isLate || j.isBlocked)
    .sort((a, b) => {
      const riskOrder: Record<string, number> = {
        high: 0,
        medium: 1,
        low: 2,
        none: 3,
      };
      return (riskOrder[a.riskLevel] ?? 3) - (riskOrder[b.riskLevel] ?? 3);
    });

  const activeAlerts = alerts.filter((a) => !a.resolvedAt);
  const visibleRisks = showAllRisks ? riskyJobs : riskyJobs.slice(0, 4);

  const getKPI = (code: string): KPIValue =>
    kpis.find((k) => k.code === code) || emptyKPI(code);

  const sortedActiveJobs = [...inExecutionJobs].sort((a, b) => {
    const priorityOrder: Record<string, number> = {
      urgent: 0,
      high: 1,
      normal: 2,
      low: 3,
    };
    return (
      (priorityOrder[a.priority] ?? 3) - (priorityOrder[b.priority] ?? 3)
    );
  });

  const utilKpi = getKPI("KPI_MACHINE_UTIL");
  const throughputKpi = getKPI("KPI_THROUGHPUT");
  const otifKpi = getKPI("KPI_OTIF");
  const activeKpi = getKPI("KPI_ACTIVE_JOBS");
  const blockedKpi = getKPI("KPI_BLOCKED_JOBS");

  return (
    <div className="space-y-4 max-w-[1600px] mx-auto">
      {/* Status Header */}
      <StatusHeader
        source={source}
        loading={loading}
        lastUpdate={lastUpdate}
        onRefresh={refresh}
      />

      <OperationalTruthBanner truth={operationalTruth} />

      {/* Quick Actions */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[11px] text-wo-text-muted font-medium mr-1">Acțiuni rapide:</span>
        <button
          onClick={() => navigate("/intake")}
          className="inline-flex items-center gap-1.5 rounded-md border border-blue-200 bg-blue-50 px-3 py-1.5 text-[11px] font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:border-blue-700/40 dark:bg-blue-600/20 dark:text-blue-300 dark:hover:border-blue-600/60 dark:hover:bg-blue-600/30"
        >
          <Plus className="w-3 h-3" />
          Cerere Nouă
        </button>
        <button
          onClick={() => navigate("/quotes")}
          className="inline-flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-[11px] font-medium text-emerald-700 transition-colors hover:bg-emerald-100 dark:border-emerald-700/40 dark:bg-emerald-600/20 dark:text-emerald-300 dark:hover:border-emerald-600/60 dark:hover:bg-emerald-600/30"
        >
          <FileText className="w-3 h-3" />
          Oferte
        </button>
        <button
          onClick={() => navigate("/orders")}
          className="inline-flex items-center gap-1.5 rounded-md border border-amber-200 bg-amber-50 px-3 py-1.5 text-[11px] font-medium text-amber-800 transition-colors hover:bg-amber-100 dark:border-amber-700/40 dark:bg-amber-600/20 dark:text-amber-300 dark:hover:border-amber-600/60 dark:hover:bg-amber-600/30"
        >
          <ShoppingCart className="w-3 h-3" />
          Comenzi
        </button>
        <button
          onClick={() => navigate("/shop-floor")}
          className="inline-flex items-center gap-1.5 rounded-md border border-purple-200 bg-purple-50 px-3 py-1.5 text-[11px] font-medium text-purple-700 transition-colors hover:bg-purple-100 dark:border-purple-700/40 dark:bg-purple-600/20 dark:text-purple-300 dark:hover:border-purple-600/60 dark:hover:bg-purple-600/30"
        >
          <Factory className="w-3 h-3" />
          Shop Floor
        </button>
        <button
          onClick={() => navigate("/reports")}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded-md bg-cyan-600/20 border border-cyan-700/40 text-cyan-300 hover:bg-cyan-600/30 hover:border-cyan-600/60 transition-colors"
        >
          <BarChart3 className="w-3 h-3" />
          Rapoarte
        </button>
      </div>

      {/* KPI Cards — 5 key metrics with honest labels */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <KPICardLarge
          {...activeKpi}
          label={activeKpi.label || "Job-uri în pipeline"}
          icon={<Activity className="w-5 h-5" />}
        />
        <KPICardLarge
          {...blockedKpi}
          label={blockedKpi.label || "Blocate (execuție)"}
          icon={<XCircle className="w-5 h-5" />}
        />
        <KPICardLarge
          {...otifKpi}
          label={otifKpi.label || "OTIF (proxy)"}
          icon={<CheckCircle2 className="w-5 h-5" />}
        />
        <KPICardLarge
          {...throughputKpi}
          label={throughputKpi.label || "Throughput azi (UTC)"}
          icon={<Zap className="w-5 h-5" />}
        />
        <KPICardLarge
          {...utilKpi}
          label={utilKpi.label || "Load planificat WC"}
          icon={<Gauge className="w-5 h-5" />}
        />
      </div>

      {/* Summary Bar */}
      <SummaryBar
        planned={plannedJobs.length}
        inExecution={inExecutionJobs.length}
        blocked={blockedJobs.length}
        completed={completedJobs.length}
        late={lateJobs.length}
      />

      {/* Main Content — 2 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* LEFT: Risk + Active Jobs */}
        <div className="lg:col-span-2 space-y-4">
          {/* Delivery Risk */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-semibold text-wo-text-primary">
                  Riscuri livrare
                </h3>
                {riskyJobs.length > 0 && (
                  <span className="text-xs bg-red-500/15 text-red-400 px-1.5 py-0.5 rounded-full font-medium">
                    {riskyJobs.length}
                  </span>
                )}
              </div>
              {riskyJobs.length > 4 && (
                <button
                  onClick={() => setShowAllRisks(!showAllRisks)}
                  className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >
                  {showAllRisks ? "Ascunde" : `Vezi toate (${riskyJobs.length})`}
                  {showAllRisks ? (
                    <ChevronUp className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5" />
                  )}
                </button>
              )}
            </div>

            {riskyJobs.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {visibleRisks.map((job) => (
                  <RiskCard key={job.id} job={job} />
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle2 className="w-8 h-8 text-green-500/40 mx-auto mb-2" />
                <p className="text-sm text-wo-text-muted">
                  Niciun risc de livrare detectat
                </p>
              </div>
            )}
          </div>

          {/* Active Jobs */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-wo-text-primary">
                În execuție (actual)
              </h3>
              <span className="text-xs bg-blue-500/15 text-blue-400 px-1.5 py-0.5 rounded-full font-medium">
                {inExecutionJobs.length}
              </span>
              <span className="text-[10px] text-wo-text-muted">
                fără blocate — vezi segmentul Blocate
              </span>
            </div>

            {sortedActiveJobs.length > 0 ? (
              <div className="space-y-0.5">
                {sortedActiveJobs.map((job) => (
                  <ActiveJobRow key={job.id} job={job} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-wo-text-muted text-center py-6">
                Niciun job în execuție (neblocat)
              </p>
            )}
          </div>
        </div>

        {/* RIGHT: Alerts + Capacity */}
        <div className="space-y-4">
          {/* Alerts */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <h3 className="text-sm font-semibold text-wo-text-primary">Alerte</h3>
              {activeAlerts.length > 0 && (
                <span className="text-xs bg-red-500/15 text-red-400 px-1.5 py-0.5 rounded-full font-medium">
                  {activeAlerts.length}
                </span>
              )}
            </div>

            {activeAlerts.length > 0 ? (
              <div className="space-y-2">
                {activeAlerts.map((alert) => (
                  <AlertItemSimple key={alert.id} alert={alert} />
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <CheckCircle2 className="w-6 h-6 text-green-500/40 mx-auto mb-1.5" />
                <p className="text-xs text-wo-text-muted">Nicio alertă activă</p>
              </div>
            )}
          </div>

          {/* Capacity */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-wo-text-primary">
                Load planificat pe workcenter
              </h3>
            </div>
            <p className="text-[10px] text-wo-text-muted mb-2 leading-snug">
              Clamp 0–100 · actual_min / planned_min · nu utilizare pe ture/calendar
            </p>
            <div className="mb-3">
              <CapacityNotice
                compact
                message="Capacity / load planificat — nu pricing comercial."
              />
            </div>
            <div
              className="mb-3 rounded border border-amber-200 bg-amber-50 px-2 py-1.5 text-[10px] text-amber-900 dark:border-amber-800/30 dark:bg-amber-950/15 dark:text-amber-200/90"
              data-testid="capacity-calendar-gap"
            >
              Utilaj calendar/shift: date indisponibile — afișăm load planificat 0–100 pe workcenter
            </div>

            <div className="space-y-2.5">
              {capacity.map((c) => (
                <CapacityItem
                  key={c.workcenterId}
                  name={c.workcenterName}
                  load={c.loadToday}
                  plannedMinutes={c.plannedMinutes}
                  actualMinutes={c.actualMinutes}
                  overrunMinutes={c.overrunMinutes}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
