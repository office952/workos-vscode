import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDashboardStats } from "@/hooks/useDashboardStats";
import {
  CapacityNotice,
  BoundaryBadge,
  chromeBanner,
} from "@/components/workos/design-system";
import type {
  KPIMetricKind,
  KPIValue,
  OperationalDataGaps,
  OperationalTruth,
} from "@/lib/mockData";
import {
  readDashboardBannerAcknowledged,
  readDashboardGapsAcknowledged,
  writeDashboardBannerAcknowledged,
  writeDashboardGapsAcknowledged,
} from "@/lib/dashboardHonestyDisclosure";
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
  Users,
} from "lucide-react";

/** Drop snake_case-only internal formula tokens from honesty list (keep human notices). */
function isHumanReadableNotice(notice: string): boolean {
  const trimmed = notice.trim();
  if (!trimmed) return false;
  if (/\s/.test(trimmed)) return true;
  return !/^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$/i.test(trimmed);
}

const QUICK_ACTION_CLASS =
  "inline-flex items-center gap-1.5 rounded-md border border-wo-border-strong bg-wo-surface-raised px-3 py-1.5 text-[11px] font-medium text-wo-text-secondary transition-colors hover:bg-wo-hover hover:text-wo-text-primary";

const QUICK_ACTION_PRIMARY_CLASS =
  "inline-flex items-center gap-1.5 rounded-md border border-wo-info/40 bg-wo-info-muted px-3 py-1.5 text-[11px] font-medium text-wo-info transition-colors hover:bg-wo-hover";

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
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-wo-success opacity-40" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-wo-success" />
            </span>
            <span className="text-sm text-wo-success font-medium" data-testid="dashboard-data-source">
              Date disponibile
            </span>
            <Database className="w-3.5 h-3.5 text-wo-success/70" />
          </div>
        ) : source === "mock" ? (
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-wo-warning" />
            <span className="text-sm text-wo-warning font-medium">Demo</span>
            <HardDrive className="w-3.5 h-3.5 text-wo-warning/70" />
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-wo-text-dim animate-pulse" />
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
    className: "border-wo-info/30 bg-wo-info-muted text-wo-info",
  },
  planned: {
    label: "planificat",
    className: "border-wo-border-strong bg-wo-surface-inset text-wo-text-secondary",
  },
  derived: {
    label: "derivat",
    className: "border-wo-border-strong bg-wo-surface-inset text-wo-text-secondary",
  },
  proxy: {
    label: "proxy",
    className: "border-wo-warning/30 bg-wo-warning-muted text-wo-warning",
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
  showGapNoise = true,
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
  /** When false, kind badges stay; verbose Gap: lines collapse. */
  showGapNoise?: boolean;
}) {
  const statusStyles = {
    good: {
      border: "border-wo-border-subtle",
      bg: "bg-wo-surface-raised",
      value: "text-wo-text-primary",
      iconColor: "text-wo-success",
    },
    warning: {
      border: "border-wo-warning/35",
      bg: "bg-wo-surface-raised",
      value: "text-wo-warning",
      iconColor: "text-wo-warning",
    },
    critical: {
      border: "border-wo-error/35",
      bg: "bg-wo-surface-raised",
      value: "text-wo-error",
      iconColor: "text-wo-error",
    },
  };

  const style = statusStyles[status];

  const TrendIcon =
    trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const trendColor =
    trend === "up"
      ? status === "critical" || status === "warning"
        ? "text-wo-error"
        : "text-wo-success"
      : trend === "down"
        ? status === "critical" || status === "warning"
          ? "text-wo-success"
          : "text-wo-error"
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
      {showGapNoise && explanation && (
        <p className="text-[10px] text-wo-text-muted/80 mt-1 leading-snug line-clamp-2">
          {explanation}
        </p>
      )}
      {showGapNoise && gapNote && (
        <p
          className="text-[10px] text-wo-warning mt-1 leading-snug line-clamp-2"
          data-testid="kpi-gap-note"
        >
          Gap: {gapNote}
        </p>
      )}
      {!showGapNoise && gapNote && (
        <p className="text-[10px] text-wo-text-muted mt-1" data-testid="kpi-gap-collapsed">
          Gap ascuns — eticheta {kindMeta?.label?.toUpperCase() || "KIND"} rămâne
        </p>
      )}
    </div>
  );
}

/* ─── Truth notices ─── */
function OperationalTruthBanner({
  truth,
  acknowledged,
  onAcknowledge,
  onExpand,
}: {
  truth: OperationalTruth | null;
  acknowledged: boolean;
  onAcknowledge: () => void;
  onExpand: () => void;
}) {
  if (!truth) return null;
  const rawNotices = truth.notices?.length
    ? truth.notices
    : [
        "Utilaj calendar/shift: date indisponibile — afișăm load planificat 0–100 pe workcenter.",
      ];
  const notices = rawNotices.filter(isHumanReadableNotice).slice(0, 3);

  if (acknowledged) {
    return (
      <div
        className={`flex flex-wrap items-center justify-between gap-2 rounded-lg px-3 py-2 ${chromeBanner.warning}`}
        data-testid="dashboard-operational-truth"
        data-collapsed="true"
        role="note"
      >
        <div className="flex items-center gap-2 min-w-0">
          <Info className="w-3.5 h-3.5 shrink-0 text-wo-warning" />
          <p className="text-[11px] font-medium text-wo-text-primary truncate">
            Adevăr operațional — citit
          </p>
          {truth.calendarShiftUtilAvailable ? (
            <span className="rounded border border-wo-success/40 bg-wo-success-muted px-1.5 py-0.5 text-[10px] text-wo-success">
              util% = planned / shift WC
            </span>
          ) : (
            <span className="rounded border border-wo-warning/40 bg-wo-warning-muted px-1.5 py-0.5 text-[10px] text-wo-warning">
              fără util calendar/shift
            </span>
          )}
          <span className="font-mono text-[10px] text-wo-text-muted hidden sm:inline">
            P {truth.plannedMinutesTotal ?? 0}m · A {truth.actualMinutesTotal ?? 0}m
          </span>
        </div>
        <button
          type="button"
          onClick={onExpand}
          className="text-[11px] font-semibold text-wo-info hover:underline"
          data-testid="dashboard-honesty-banner-expand"
        >
          Arată detalii
        </button>
      </div>
    );
  }

  return (
    <div
      className={`rounded-lg px-4 py-3 space-y-2 ${chromeBanner.warning}`}
      data-testid="dashboard-operational-truth"
      data-collapsed="false"
      role="note"
    >
      <div className="flex items-center gap-2 flex-wrap">
        <Info className="w-4 h-4 shrink-0 text-wo-warning" />
        <h3 className="text-xs font-semibold text-wo-text-primary">
          Adevăr operațional (Dashboard)
        </h3>
        {truth.calendarShiftUtilAvailable ? (
          <span className="rounded border border-wo-success/40 bg-wo-success-muted px-1.5 py-0.5 text-[10px] text-wo-success">
            util% = planned / shift WC
          </span>
        ) : (
          <span className="rounded border border-wo-warning/40 bg-wo-surface-raised px-1.5 py-0.5 text-[10px] text-wo-warning">
            fără util calendar/shift
          </span>
        )}
      </div>
      <ul className="space-y-1">
        {notices.map((n) => (
          <li
            key={n}
            className="flex gap-1.5 text-[11px] leading-snug text-wo-text-secondary"
          >
            <span className="shrink-0 text-wo-warning">•</span>
            <span>{n}</span>
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-3 pt-1 font-mono text-[10px] text-wo-text-muted">
        <span>Planificat: {truth.plannedMinutesTotal ?? 0} min</span>
        <span className="text-wo-info">
          Actual: {truth.actualMinutesTotal ?? 0} min
        </span>
        <span className="text-wo-error">
          Overrun: {truth.overrunMinutesTotal ?? 0} min
        </span>
        <span>Fereastră throughput: {truth.throughputWindow}</span>
      </div>
      <div className="flex justify-end pt-1">
        <button
          type="button"
          onClick={onAcknowledge}
          className="rounded-md border border-wo-warning/50 bg-wo-surface-raised px-2.5 py-1 text-[11px] font-semibold text-wo-text-primary hover:bg-wo-hover"
          data-testid="dashboard-honesty-banner-ack"
        >
          Am înțeles
        </button>
      </div>
    </div>
  );
}

/* ─── Operational data gaps (Pricing / Cost Intern / Capacity) ─── */
function OperationalDataGapsPanel({ gaps }: { gaps?: OperationalDataGaps | null }) {
  if (!gaps) return null;
  const rows = [
    {
      key: "pricing",
      title: "Pricing rates",
      href: "/inventory/pricing",
      icon: BarChart3,
      domain: "pricing" as const,
      block: gaps.pricing,
    },
    {
      key: "costIntern",
      title: "Cost Intern",
      href: "/employees",
      icon: Users,
      domain: "hr" as const,
      block: gaps.costIntern,
    },
    {
      key: "capacity",
      title: "Capacity",
      href: "/utilaje",
      icon: Gauge,
      domain: "machines" as const,
      block: gaps.capacity,
    },
  ].filter((r) => r.block);

  if (!rows.length) return null;

  return (
    <div
      className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-4 py-3 space-y-2"
      data-testid="dashboard-data-gaps"
      role="region"
      aria-label="Operational data gaps"
    >
      <div className="flex items-center gap-2 flex-wrap">
        <AlertTriangle className="w-4 h-4 text-wo-warning shrink-0" />
        <h3 className="text-xs font-semibold text-wo-text-primary">
          Gap-uri date operaționale
        </h3>
        <span className="text-[10px] text-wo-text-muted">
          Material ≠ regulă comercială ≠ cost intern ≠ capacitate
        </span>
      </div>
      <ul className="space-y-2">
        {rows.map(({ key, title, href, icon: Icon, domain, block }) => {
          const needed = Boolean(block?.ownerDataNeeded ?? block?.unknown);
          return (
            <li
              key={key}
              className="flex flex-col gap-1 rounded-md border border-wo-border-subtle/80 px-3 py-2"
              data-testid={`dashboard-data-gap-${key}`}
            >
              <div className="flex items-center gap-2 flex-wrap">
                <Icon className="w-3.5 h-3.5 text-wo-text-muted shrink-0" />
                <span className="text-[11px] font-semibold text-wo-text-primary">{title}</span>
                <BoundaryBadge domain={domain} compact />
                <span
                  className={`rounded px-1.5 py-0.5 text-[10px] font-medium border ${
                    needed
                      ? "border-wo-warning/35 bg-wo-warning-muted text-wo-warning"
                      : "border-wo-success/35 bg-wo-success-muted text-wo-success"
                  }`}
                >
                  {needed ? "Owner data needed" : "OK"}
                </span>
                <Link
                  to={href}
                  className="ml-auto text-[10px] font-medium text-wo-info hover:underline"
                >
                  Deschide
                </Link>
              </div>
              <p className="text-[11px] leading-snug text-wo-text-muted">{block?.notice}</p>
            </li>
          );
        })}
      </ul>
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
    { label: "Finalizate", count: completed, color: "bg-wo-success", tone: "actual" },
    { label: "În execuție", count: inExecution, color: "bg-wo-info", tone: "actual" },
    { label: "Blocate", count: blocked, color: "bg-wo-error", tone: "blocked" },
    { label: "Planificate", count: planned, color: "bg-wo-text-dim", tone: "planned" },
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
            <span className="text-wo-warning font-medium border border-wo-warning/40 bg-wo-warning-muted rounded px-1.5 py-0.5">
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
      border: "border-wo-error/35",
      bg: "bg-wo-error-muted",
      badge: "border-wo-error/35 bg-wo-surface-raised text-wo-error",
    },
    medium: {
      border: "border-wo-warning/35",
      bg: "bg-wo-warning-muted",
      badge: "border-wo-warning/35 bg-wo-surface-raised text-wo-warning",
    },
    low: {
      border: "border-wo-info/35",
      bg: "bg-wo-info-muted",
      badge: "border-wo-info/35 bg-wo-surface-raised text-wo-info",
    },
  };

  const style =
    riskStyles[job.riskLevel as keyof typeof riskStyles] || riskStyles.low;

  const progressColor =
    job.progress >= 60
      ? "bg-wo-success"
      : job.progress >= 30
        ? "bg-wo-info"
        : "bg-wo-warning";

  return (
    <div className={`rounded-lg border p-3.5 transition-all ${style.border} ${style.bg}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-wo-info font-medium">
            {job.id}
          </span>
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold uppercase ${style.badge}`}
          >
            {job.riskLevel}
          </span>
          {job.isBlocked && (
            <span className="rounded border border-wo-error/35 bg-wo-surface-raised px-1.5 py-0.5 text-[10px] font-semibold uppercase text-wo-error">
              blocked
            </span>
          )}
          {!job.isBlocked && job.isLate && (
            <span className="rounded border border-wo-warning/35 bg-wo-surface-raised px-1.5 py-0.5 text-[10px] font-semibold uppercase text-wo-warning">
              late
            </span>
          )}
        </div>
        {job.isBlocked && (
          <XCircle className="h-4 w-4 shrink-0 text-wo-error" />
        )}
        {!job.isBlocked && job.isLate && (
          <Clock className="h-4 w-4 shrink-0 text-wo-warning" />
        )}
      </div>

      <p className="text-sm text-wo-text-primary font-medium truncate">
        {job.client}
      </p>
      <p className="text-xs text-wo-text-muted truncate mt-0.5">{job.product}</p>

      {job.riskReason && (
        <p className="text-xs text-wo-error/90 mt-1.5 italic">
          {job.riskReason}
        </p>
      )}

      <div className="flex items-center gap-2 mt-2.5">
        <div className="flex-1 bg-wo-border-subtle rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-1.5 rounded-full transition-all duration-700 ${progressColor}`}
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
          className={`text-[11px] ${job.isLate ? "text-wo-error font-medium" : "text-wo-text-muted"}`}
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
    urgent: "bg-wo-error",
    high: "bg-wo-warning",
    normal: "bg-wo-info",
    low: "bg-wo-text-dim",
  };

  return (
    <div className="flex items-center gap-3 py-2.5 px-3 rounded-md hover:bg-wo-hover transition-colors group">
      <span
        className={`w-1.5 h-8 rounded-full shrink-0 ${priorityColors[job.priority as keyof typeof priorityColors] || "bg-wo-text-dim"}`}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-wo-info">{job.id}</span>
          <span className="text-sm text-wo-text-primary truncate">{job.client}</span>
          <span className="text-[9px] uppercase tracking-wide px-1 py-0.5 rounded border border-wo-info/30 text-wo-info bg-wo-info-muted">
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
              className="bg-wo-info h-1.5 rounded-full transition-all duration-700"
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
    critical: "border-l-wo-error bg-wo-error-muted",
    warning: "border-l-wo-warning bg-wo-warning-muted",
    info: "border-l-wo-info bg-wo-info-muted",
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
      ? "bg-wo-error"
      : load >= 75
        ? "bg-wo-warning"
        : "bg-wo-info";
  const textColor =
    load >= 90
      ? "text-wo-error"
      : load >= 75
        ? "text-wo-warning"
        : "text-wo-text-secondary";
  const hasOverrun = (overrunMinutes ?? 0) > 0;

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="text-xs text-wo-text-muted w-20 truncate" title={name}>
          {name}
        </span>
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
        <span className="text-wo-info">A {actualMinutes ?? 0}m</span>
        {hasOverrun && (
          <span className="text-wo-error">OV +{overrunMinutes}m</span>
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

/** Show bars only when derived load > 0 — zero-load rows collapse to a gap summary (no invented util %). */
function hasVisibleCapacityLoad(c: { loadToday: number }): boolean {
  return c.loadToday > 0;
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
  const [bannerAcknowledged, setBannerAcknowledged] = useState(
    readDashboardBannerAcknowledged,
  );
  const [gapsAcknowledged, setGapsAcknowledged] = useState(
    readDashboardGapsAcknowledged,
  );
  const showGapNoise = !gapsAcknowledged;

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

  const { activeCapacity, quietCapacityCount } = useMemo(() => {
    const active = capacity.filter(hasVisibleCapacityLoad);
    return {
      activeCapacity: active,
      quietCapacityCount: Math.max(0, capacity.length - active.length),
    };
  }, [capacity]);

  return (
    <div className="space-y-5 max-w-[1600px] mx-auto pb-6">
      {/* 1. Status + honesty */}
      <StatusHeader
        source={source}
        loading={loading}
        lastUpdate={lastUpdate}
        onRefresh={refresh}
      />

      <OperationalTruthBanner
        truth={operationalTruth}
        acknowledged={bannerAcknowledged}
        onAcknowledge={() => {
          writeDashboardBannerAcknowledged(true);
          setBannerAcknowledged(true);
        }}
        onExpand={() => {
          writeDashboardBannerAcknowledged(false);
          setBannerAcknowledged(false);
        }}
      />

      {/* Keep operational gaps (Pricing / Cost Intern / Capacity) */}
      <OperationalDataGapsPanel gaps={operationalTruth?.dataGaps} />

      <div
        className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-wo-border-subtle bg-wo-surface-inset px-3 py-2"
        data-testid="dashboard-honesty-gap-toggle"
      >
        <p className="text-[11px] text-wo-text-muted">
          Etichetele ACTUAL / PROXY / DERIVAT rămân pe carduri.
          {showGapNoise
            ? " Textul Gap detaliat e vizibil (mod audit)."
            : " Zgomotul Gap e pliat pentru tură."}
        </p>
        <button
          type="button"
          onClick={() => {
            const next = !gapsAcknowledged;
            writeDashboardGapsAcknowledged(next);
            setGapsAcknowledged(next);
          }}
          className="text-[11px] font-semibold text-wo-info hover:underline"
          data-testid="dashboard-honesty-gaps-ack"
        >
          {showGapNoise ? "Am înțeles — pliază Gap" : "Arată Gap-uri"}
        </button>
      </div>

      {/* 2. Primary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <KPICardLarge
          {...activeKpi}
          label={activeKpi.label || "Job-uri în pipeline"}
          icon={<Activity className="w-5 h-5" />}
          showGapNoise={showGapNoise}
        />
        <KPICardLarge
          {...blockedKpi}
          label={blockedKpi.label || "Blocate (execuție)"}
          icon={<XCircle className="w-5 h-5" />}
          showGapNoise={showGapNoise}
        />
        <KPICardLarge
          {...otifKpi}
          label={otifKpi.label || "OTIF (proxy)"}
          icon={<CheckCircle2 className="w-5 h-5" />}
          showGapNoise={showGapNoise}
        />
        <KPICardLarge
          {...throughputKpi}
          label={throughputKpi.label || "Throughput azi (UTC)"}
          icon={<Zap className="w-5 h-5" />}
          showGapNoise={showGapNoise}
        />
        <KPICardLarge
          {...utilKpi}
          label={utilKpi.label || "Load planificat WC"}
          icon={<Gauge className="w-5 h-5" />}
          showGapNoise={showGapNoise}
        />
      </div>

      {/* 3. Quick actions — token primary + neutral */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[11px] text-wo-text-muted font-medium mr-1">Acțiuni rapide:</span>
        <button
          onClick={() => navigate("/intake")}
          className={QUICK_ACTION_PRIMARY_CLASS}
        >
          <Plus className="w-3 h-3" />
          Cerere Nouă
        </button>
        <button onClick={() => navigate("/quotes")} className={QUICK_ACTION_CLASS}>
          <FileText className="w-3 h-3" />
          Oferte
        </button>
        <button onClick={() => navigate("/orders")} className={QUICK_ACTION_CLASS}>
          <ShoppingCart className="w-3 h-3" />
          Comenzi
        </button>
        <button onClick={() => navigate("/shop-floor")} className={QUICK_ACTION_CLASS}>
          <Factory className="w-3 h-3" />
          Shop Floor
        </button>
        <button onClick={() => navigate("/reports")} className={QUICK_ACTION_CLASS}>
          <BarChart3 className="w-3 h-3" />
          Rapoarte
        </button>
      </div>

      {/* Summary Bar */}
      <SummaryBar
        planned={plannedJobs.length}
        inExecution={inExecutionJobs.length}
        blocked={blockedJobs.length}
        completed={completedJobs.length}
        late={lateJobs.length}
      />

      {/* 4. Secondary lists / workcenters */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* LEFT: Risk + Active Jobs */}
        <div className="lg:col-span-2 space-y-4">
          {/* Delivery Risk */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-wo-warning" />
                <h3 className="text-sm font-semibold text-wo-text-primary">
                  Riscuri livrare
                </h3>
                {riskyJobs.length > 0 && (
                  <span className="text-xs border border-wo-error/30 bg-wo-error-muted text-wo-error px-1.5 py-0.5 rounded-full font-medium">
                    {riskyJobs.length}
                  </span>
                )}
              </div>
              {riskyJobs.length > 4 && (
                <button
                  onClick={() => setShowAllRisks(!showAllRisks)}
                  className="flex items-center gap-1 text-xs text-wo-info hover:underline transition-colors"
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
                <CheckCircle2 className="w-8 h-8 text-wo-success/50 mx-auto mb-2" />
                <p className="text-sm text-wo-text-muted">
                  Niciun risc de livrare detectat
                </p>
              </div>
            )}
          </div>

          {/* Active Jobs */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-wo-info" />
              <h3 className="text-sm font-semibold text-wo-text-primary">
                În execuție (actual)
              </h3>
              <span className="text-xs border border-wo-info/30 bg-wo-info-muted text-wo-info px-1.5 py-0.5 rounded-full font-medium">
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
              <AlertTriangle className="w-4 h-4 text-wo-error" />
              <h3 className="text-sm font-semibold text-wo-text-primary">Alerte</h3>
              {activeAlerts.length > 0 && (
                <span className="text-xs border border-wo-error/30 bg-wo-error-muted text-wo-error px-1.5 py-0.5 rounded-full font-medium">
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
                <CheckCircle2 className="w-6 h-6 text-wo-success/50 mx-auto mb-1.5" />
                <p className="text-xs text-wo-text-muted">Nicio alertă activă</p>
              </div>
            )}
          </div>

          {/* Capacity — keep Owner gap; quiet zero-signal rows */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="w-4 h-4 text-wo-info" />
              <h3 className="text-sm font-semibold text-wo-text-primary">
                Util% shift pe workcenter
              </h3>
            </div>
            <p className="text-[10px] text-wo-text-muted mb-2 leading-snug">
              planned_min / ore shift (Company Calendar) · clamp 0–100 · nu HR hours · nu tarif client
            </p>
            <div className="mb-3">
              <CapacityNotice
                compact
                message="Capacity / planned load — nu pricing comercial, nu CostEngine."
              />
            </div>
            {operationalTruth?.calendarShiftUtilAvailable ? (
              <div
                className="mb-3 rounded border border-wo-success/30 bg-wo-success-muted px-2 py-1.5 text-[10px] text-wo-success"
                data-testid="capacity-calendar-active"
              >
                Calendar/shift activ — util% = planned load / ore shift pe WC (warnings non-blocking).
              </div>
            ) : (
              <div
                className={`mb-3 rounded px-2 py-1.5 text-[10px] ${chromeBanner.warning}`}
                data-testid="capacity-calendar-gap"
              >
                Utilaj calendar/shift: date indisponibile — nu inventăm util %.
              </div>
            )}

            <div className="space-y-2.5" data-testid="dashboard-capacity-list">
              {activeCapacity.length > 0 ? (
                activeCapacity.map((c) => (
                  <CapacityItem
                    key={c.workcenterId}
                    name={c.workcenterName}
                    load={c.loadToday}
                    plannedMinutes={c.plannedMinutes}
                    actualMinutes={c.actualMinutes}
                    overrunMinutes={c.overrunMinutes}
                  />
                ))
              ) : (
                <p className="text-[11px] text-wo-text-muted py-2">
                  Niciun workcenter cu planned load &gt; 0 în luna curentă (util% 0% e onest, nu inventat).
                </p>
              )}
              {quietCapacityCount > 0 && (
                <p
                  className="text-[10px] text-wo-text-muted border-t border-wo-border-subtle pt-2 mt-1"
                  data-testid="dashboard-capacity-quiet-summary"
                >
                  {quietCapacityCount} workcentere cu planned load 0% — idle pe shift model, nu inventăm utilizare.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
