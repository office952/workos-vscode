import React from "react";
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Minus,
  ArrowRight,
  Shield,
  Ban,
  Activity,
  Zap,
  Info,
} from "lucide-react";
import type { AlertSeverity, JobStatus, TaskStatus } from "@/lib/mockData";

// ---- STATUS BADGE ----
const jobStatusConfig: Record<JobStatus, { label: string; className: string }> = {
  pending: { label: "Pending", className: "bg-slate-700/60 text-slate-300 border-slate-600" },
  ready: { label: "Ready", className: "bg-blue-900/40 text-blue-300 border-blue-700" },
  scheduled: { label: "Scheduled", className: "bg-purple-900/40 text-purple-300 border-purple-700" },
  in_progress: { label: "Running", className: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  blocked: { label: "Blocked", className: "bg-red-900/40 text-red-300 border-red-700" },
  partially_completed: { label: "Partial", className: "bg-amber-900/40 text-amber-300 border-amber-700" },
  completed: { label: "Done", className: "bg-emerald-900/50 text-emerald-200 border-emerald-600" },
  cancelled: { label: "Cancelled", className: "bg-slate-800/60 text-slate-400 border-slate-600" },
};

const taskStatusConfig: Record<TaskStatus, { label: string; className: string }> = {
  created: { label: "Created", className: "bg-slate-700/60 text-slate-300 border-slate-600" },
  assigned: { label: "Assigned", className: "bg-blue-900/40 text-blue-300 border-blue-700" },
  in_progress: { label: "Running", className: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  paused: { label: "Paused", className: "bg-amber-900/40 text-amber-300 border-amber-700" },
  blocked: { label: "Blocked", className: "bg-red-900/40 text-red-300 border-red-700" },
  done: { label: "Done", className: "bg-emerald-900/50 text-emerald-200 border-emerald-600" },
  cancelled: { label: "Cancelled", className: "bg-slate-800/60 text-slate-400 border-slate-600" },
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  const cfg = jobStatusConfig[status];
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold rounded border ${cfg.className}`}>
      {status === "in_progress" && <Activity className="w-3 h-3" />}
      {status === "blocked" && <Ban className="w-3 h-3" />}
      {status === "completed" && <CheckCircle2 className="w-3 h-3" />}
      {cfg.label}
    </span>
  );
}

export function TaskStatusBadge({ status }: { status: TaskStatus }) {
  const cfg = taskStatusConfig[status];
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold rounded border ${cfg.className}`}>
      {status === "in_progress" && <Activity className="w-3 h-3" />}
      {status === "paused" && <Clock className="w-3 h-3" />}
      {status === "blocked" && <Ban className="w-3 h-3" />}
      {status === "done" && <CheckCircle2 className="w-3 h-3" />}
      {cfg.label}
    </span>
  );
}

// ---- PRIORITY BADGE ----
const priorityConfig: Record<string, { label: string; className: string }> = {
  urgent: { label: "URGENT", className: "bg-red-600 text-white" },
  high: { label: "HIGH", className: "bg-amber-600 text-white" },
  normal: { label: "NORMAL", className: "bg-slate-600 text-slate-200" },
  low: { label: "LOW", className: "bg-slate-700 text-slate-400" },
};

export function PriorityBadge({ priority }: { priority: string }) {
  const cfg = priorityConfig[priority] || priorityConfig.normal;
  return <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded ${cfg.className}`}>{cfg.label}</span>;
}

// ---- SEVERITY BADGE ----
const severityConfig: Record<AlertSeverity, { icon: React.ReactNode; className: string; borderClass: string }> = {
  critical: { icon: <XCircle className="w-3.5 h-3.5" />, className: "text-red-400", borderClass: "border-l-red-500" },
  warning: { icon: <AlertTriangle className="w-3.5 h-3.5" />, className: "text-amber-400", borderClass: "border-l-amber-500" },
  info: { icon: <Info className="w-3.5 h-3.5" />, className: "text-blue-400", borderClass: "border-l-blue-500" },
};

export function AlertItem({ alert }: { alert: { id: string; severity: AlertSeverity; message: string; triggeredAt: string; code: string } }) {
  const cfg = severityConfig[alert.severity];
  return (
    <div className={`flex items-start gap-2 px-3 py-2 bg-wo-surface-raised border-l-2 ${cfg.borderClass} rounded-r`}>
      <span className={`mt-0.5 ${cfg.className}`}>{cfg.icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-[12px] text-wo-text-primary leading-tight">{alert.message}</p>
        <p className="text-[10px] text-slate-500 mt-0.5">{alert.code} · {new Date(alert.triggeredAt).toLocaleTimeString("ro-RO", { hour: "2-digit", minute: "2-digit" })}</p>
      </div>
    </div>
  );
}

// ---- KPI CARD ----
export function KPICard({
  label,
  value,
  unit,
  trend,
  trendValue,
  status,
}: {
  label: string;
  value: number;
  unit: string;
  trend: "up" | "down" | "stable";
  trendValue: number;
  status: "good" | "warning" | "critical";
}) {
  const statusBorder = status === "critical" ? "border-t-red-500" : status === "warning" ? "border-t-amber-500" : "border-t-emerald-500";
  const trendColor = trend === "up" ? (status === "good" ? "text-emerald-400" : "text-red-400") : trend === "down" ? (status === "good" ? "text-red-400" : "text-emerald-400") : "text-slate-500";
  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;

  return (
    <div className={`bg-wo-surface-raised border border-wo-border-strong border-t-2 ${statusBorder} rounded-lg px-4 py-3`}>
      <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">{label}</p>
      <div className="flex items-end gap-2 mt-1">
        <span className="text-2xl font-bold text-slate-100">{value}</span>
        {unit && <span className="text-[12px] text-slate-400 mb-0.5">{unit}</span>}
      </div>
      <div className={`flex items-center gap-1 mt-1 ${trendColor}`}>
        <TrendIcon className="w-3 h-3" />
        <span className="text-[11px] font-medium">{trendValue > 0 ? "+" : ""}{trendValue}{unit === "%" ? "pp" : ""}</span>
      </div>
    </div>
  );
}

// ---- MACHINE CARD ----
export function MachineCard({
  machine,
}: {
  machine: {
    id: string;
    name: string;
    status: string;
    currentJobId: string | null;
    currentOperationCode: string | null;
    currentOperator: string | null;
    runtimeMinutes: number;
    utilizationPct: number;
    queueCount: number;
  };
}) {
  const statusColors: Record<string, string> = {
    running: "bg-emerald-500",
    idle: "bg-slate-500",
    maintenance: "bg-red-500",
    offline: "bg-slate-700",
    changeover: "bg-amber-500",
  };
  const dotColor = statusColors[machine.status] || "bg-slate-500";

  return (
    <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-2 h-2 rounded-full ${dotColor} animate-pulse`} />
        <span className="text-[12px] font-semibold text-wo-text-primary truncate">{machine.name}</span>
      </div>
      {machine.status === "running" ? (
        <>
          <p className="text-[11px] text-slate-400">
            <span className="text-emerald-400 font-mono">{machine.currentOperationCode}</span> · {machine.currentJobId}
          </p>
          <p className="text-[11px] text-slate-500 mt-0.5">Operator: {machine.currentOperator}</p>
          <div className="flex items-center justify-between mt-2">
            <span className="text-[10px] text-slate-500">Runtime: {machine.runtimeMinutes}min</span>
            <span className="text-[10px] text-slate-500">Util: {machine.utilizationPct}%</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1 mt-1">
            <div className="bg-emerald-500 h-1 rounded-full transition-all" style={{ width: `${machine.utilizationPct}%` }} />
          </div>
        </>
      ) : machine.status === "maintenance" ? (
        <div className="flex items-center gap-1 mt-1">
          <AlertTriangle className="w-3 h-3 text-red-400" />
          <span className="text-[11px] text-red-400">Mentenanță</span>
        </div>
      ) : (
        <div className="flex items-center gap-1 mt-1">
          <Clock className="w-3 h-3 text-slate-500" />
          <span className="text-[11px] text-slate-500">Idle — {machine.queueCount} în coadă</span>
        </div>
      )}
      {machine.queueCount > 0 && (
        <p className="text-[10px] text-slate-500 mt-1">Coadă: {machine.queueCount} job(s)</p>
      )}
    </div>
  );
}

// ---- PROGRESS BAR ----
export function ProgressBar({ value, max = 100, size = "sm" }: { value: number; max?: number; size?: "sm" | "md" }) {
  const pct = Math.min((value / max) * 100, 100);
  const color = pct >= 80 ? "bg-emerald-500" : pct >= 40 ? "bg-blue-500" : "bg-amber-500";
  const h = size === "md" ? "h-2" : "h-1";
  return (
    <div className={`w-full bg-slate-700 rounded-full ${h}`}>
      <div className={`${color} ${h} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
    </div>
  );
}

// ---- MODULE NODE ----
export function ModuleNodeCard({
  node,
  isLast,
}: {
  node: {
    shortName: string;
    name: string;
    description: string;
    truthOwns: string;
    status: string;
    activeCount: number;
    statusCounts: { ok: number; warning: number; error: number };
  };
  isLast: boolean;
}) {
  const statusDot =
    node.status === "processing"
      ? "bg-blue-500 animate-pulse"
      : node.status === "error"
        ? "bg-red-500"
        : node.status === "active"
          ? "bg-emerald-500"
          : "bg-slate-500";

  return (
    <div className="flex items-center">
      <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4 w-[180px] hover:border-blue-600/50 transition-colors">
        <div className="flex items-center gap-2 mb-2">
          <span className={`w-2.5 h-2.5 rounded-full ${statusDot}`} />
          <span className="text-[14px] font-bold text-slate-100">{node.shortName}</span>
        </div>
        <p className="text-[11px] text-slate-300 font-medium">{node.name}</p>
        <p className="text-[10px] text-slate-500 mt-1">{node.description}</p>
        <div className="flex items-center gap-2 mt-3">
          <span className="flex items-center gap-0.5 text-[10px]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="text-slate-400">{node.statusCounts.ok}</span>
          </span>
          <span className="flex items-center gap-0.5 text-[10px]">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span className="text-slate-400">{node.statusCounts.warning}</span>
          </span>
          <span className="flex items-center gap-0.5 text-[10px]">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
            <span className="text-slate-400">{node.statusCounts.error}</span>
          </span>
        </div>
        <p className="text-[10px] text-slate-500 mt-1">
          {node.status === "idle"
            ? "Neverificat"
            : node.status === "error"
              ? "Eroare verificare"
              : node.status === "processing"
                ? "Parțial / atenție"
                : `${node.activeCount} verificări`}
        </p>
      </div>
      {!isLast && (
        <div className="flex items-center px-1">
          <ArrowRight className="w-4 h-4 text-slate-600" />
        </div>
      )}
    </div>
  );
}

// ---- SECTION HEADER ----
export function SectionHeader({ title, count, icon }: { title: string; count?: number; icon?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      {icon && <span className="text-slate-400">{icon}</span>}
      <h3 className="text-[14px] font-semibold text-wo-text-primary">{title}</h3>
      {count !== undefined && (
        <span className="text-[11px] font-medium text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">{count}</span>
      )}
    </div>
  );
}

// ---- CAPACITY BAR ----
export function CapacityBar({ label, value }: { label: string; value: number }) {
  const color = value >= 90 ? "bg-red-500" : value >= 75 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="flex items-center gap-3">
      <span className="text-[11px] text-slate-400 w-24 truncate">{label}</span>
      <div className="flex-1 bg-slate-700 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${value}%` }} />
      </div>
      <span className={`text-[11px] font-mono font-medium ${value >= 90 ? "text-red-400" : value >= 75 ? "text-amber-400" : "text-slate-300"}`}>
        {value}%
      </span>
    </div>
  );
}

// ---- EMPTY STATE ----
export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-8 text-slate-500 text-[13px]">
      <Shield className="w-4 h-4 mr-2" />
      {message}
    </div>
  );
}