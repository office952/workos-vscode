import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDashboardStats } from "@/hooks/useDashboardStats";
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

/* ─── KPI Card ─── */
function KPICardLarge({
  label,
  value,
  unit,
  trend,
  trendValue,
  status,
  icon,
}: {
  label: string;
  value: number;
  unit: string;
  trend: "up" | "down" | "stable";
  trendValue: number;
  status: "good" | "warning" | "critical";
  icon: React.ReactNode;
}) {
  const statusStyles = {
    good: {
      border: "border-wo-border-subtle",
      bg: "bg-wo-surface-raised",
      value: "text-wo-text-primary",
      iconColor: "text-green-400",
    },
    warning: {
      border: "border-amber-900/40",
      bg: "bg-wo-surface-raised",
      value: "text-amber-300",
      iconColor: "text-amber-400",
    },
    critical: {
      border: "border-red-900/40",
      bg: "bg-wo-surface-raised",
      value: "text-red-300",
      iconColor: "text-red-400",
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

  return (
    <div
      className={`rounded-lg border p-4 transition-all duration-300 ${style.border} ${style.bg}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className={style.iconColor}>{icon}</span>
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
      <p className={`text-3xl font-bold ${style.value}`}>
        {value}
        {unit && <span className="text-lg ml-0.5 opacity-60">{unit}</span>}
      </p>
      <p className="text-xs text-wo-text-muted mt-1.5 font-medium">{label}</p>
    </div>
  );
}

/* ─── Summary Bar ─── */
function SummaryBar({
  total,
  active,
  blocked,
  completed,
}: {
  total: number;
  active: number;
  blocked: number;
  completed: number;
}) {
  const waiting = Math.max(0, total - active - blocked - completed);
  const segments = [
    { label: "Finalizate", count: completed, color: "bg-green-500" },
    { label: "Active", count: active, color: "bg-blue-500" },
    { label: "Blocate", count: blocked, color: "bg-red-500" },
    { label: "Așteptare", count: waiting, color: "bg-slate-600" },
  ];

  return (
    <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-wo-text-primary">
          Sumar Producție
        </h3>
        <span className="text-xs text-wo-text-muted">{total} job-uri total</span>
      </div>

      {/* Progress bar */}
      <div className="h-2.5 rounded-full bg-wo-border-subtle overflow-hidden flex mb-3">
        {segments.map(
          (seg) =>
            seg.count > 0 && (
              <div
                key={seg.label}
                className={`${seg.color} transition-all duration-700`}
                style={{ width: `${(seg.count / Math.max(total, 1)) * 100}%` }}
              />
            )
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 flex-wrap">
        {segments.map((seg) => (
          <div key={seg.label} className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-sm ${seg.color}`} />
            <span className="text-xs text-wo-text-muted">
              {seg.label}:{" "}
              <span className="text-wo-text-primary font-medium">{seg.count}</span>
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
      border: "border-red-900/50",
      bg: "bg-red-950/20",
      badge: "bg-red-500/15 text-red-400 border-red-500/30",
    },
    medium: {
      border: "border-amber-900/50",
      bg: "bg-amber-950/15",
      badge: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    },
    low: {
      border: "border-blue-900/50",
      bg: "bg-blue-950/15",
      badge: "bg-blue-500/15 text-blue-400 border-blue-500/30",
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
        </div>
        {job.isBlocked && (
          <XCircle className="w-4 h-4 text-red-400 shrink-0" />
        )}
        {!job.isBlocked && job.isLate && (
          <Clock className="w-4 h-4 text-amber-400 shrink-0" />
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
}: {
  name: string;
  load: number;
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

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-wo-text-muted w-20 truncate">{name}</span>
      <div className="flex-1 bg-wo-border-subtle rounded-full h-2 overflow-hidden">
        <div
          className={`h-2 rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${load}%` }}
        />
      </div>
      <span className={`text-xs font-mono font-medium w-9 text-right ${textColor}`}>
        {load}%
      </span>
    </div>
  );
}

/* ─── Main Dashboard ─── */
export default function Dashboard() {
  const navigate = useNavigate();
  const {
    kpis,
    jobs,
    capacity,
    alerts,
    source,
    loading,
    lastUpdate,
    refresh,
  } = useDashboardStats(30000);

  const [showAllRisks, setShowAllRisks] = useState(false);

  // Derived data
  const activeJobs = jobs.filter((j) => j.status === "in_progress");
  const blockedJobs = jobs.filter((j) => j.isBlocked);
  const completedJobs = jobs.filter((j) => j.status === "completed");
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

  // KPI mapping
  const getKPI = (code: string) =>
    kpis.find((k) => k.code === code) || {
      value: 0,
      unit: "",
      trend: "stable" as const,
      trendValue: 0,
      status: "good" as const,
      label: "",
      code: "",
    };

  const sortedActiveJobs = [...activeJobs].sort((a, b) => {
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

  return (
    <div className="space-y-4 max-w-[1600px] mx-auto">
      {/* Status Header */}
      <StatusHeader
        source={source}
        loading={loading}
        lastUpdate={lastUpdate}
        onRefresh={refresh}
      />

      {/* Quick Actions */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[11px] text-wo-text-muted font-medium mr-1">Acțiuni rapide:</span>
        <button
          onClick={() => navigate("/intake")}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded-md bg-blue-600/20 border border-blue-700/40 text-blue-300 hover:bg-blue-600/30 hover:border-blue-600/60 transition-colors"
        >
          <Plus className="w-3 h-3" />
          Cerere Nouă
        </button>
        <button
          onClick={() => navigate("/quotes")}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded-md bg-emerald-600/20 border border-emerald-700/40 text-emerald-300 hover:bg-emerald-600/30 hover:border-emerald-600/60 transition-colors"
        >
          <FileText className="w-3 h-3" />
          Oferte
        </button>
        <button
          onClick={() => navigate("/orders")}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded-md bg-amber-600/20 border border-amber-700/40 text-amber-300 hover:bg-amber-600/30 hover:border-amber-600/60 transition-colors"
        >
          <ShoppingCart className="w-3 h-3" />
          Comenzi
        </button>
        <button
          onClick={() => navigate("/shop-floor")}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded-md bg-purple-600/20 border border-purple-700/40 text-purple-300 hover:bg-purple-600/30 hover:border-purple-600/60 transition-colors"
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

      {/* KPI Cards — 5 key metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <KPICardLarge
          {...getKPI("KPI_ACTIVE_JOBS")}
          label="Job-uri Active"
          icon={<Activity className="w-5 h-5" />}
        />
        <KPICardLarge
          {...getKPI("KPI_BLOCKED_JOBS")}
          label="Blocate"
          icon={<XCircle className="w-5 h-5" />}
        />
        <KPICardLarge
          {...getKPI("KPI_OTIF")}
          label="OTIF"
          icon={<CheckCircle2 className="w-5 h-5" />}
        />
        <KPICardLarge
          {...getKPI("KPI_THROUGHPUT")}
          label="Throughput Azi"
          icon={<Zap className="w-5 h-5" />}
        />
        <KPICardLarge
          {...getKPI("KPI_MACHINE_UTIL")}
          label="Utilizare Utilaje"
          icon={<Gauge className="w-5 h-5" />}
        />
      </div>

      {/* Summary Bar */}
      <SummaryBar
        total={jobs.length}
        active={activeJobs.length}
        blocked={blockedJobs.length}
        completed={completedJobs.length}
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
                  Riscuri Livrare
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
                Job-uri Active
              </h3>
              <span className="text-xs bg-blue-500/15 text-blue-400 px-1.5 py-0.5 rounded-full font-medium">
                {activeJobs.length}
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
                Niciun job activ
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
            <div className="flex items-center gap-2 mb-3">
              <Gauge className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-wo-text-primary">
                Capacitate Azi
              </h3>
            </div>

            <div className="space-y-2.5">
              {capacity.map((c) => (
                <CapacityItem
                  key={c.workcenterId}
                  name={c.workcenterName}
                  load={c.loadToday}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}