/** Plan-level operational readiness — mirrors backend Step 9.3.4.c fields. */

export type OperationalReadinessStatus =
  | "no_execution_plan"
  | "invalid_tasks_json"
  | "legacy_operational_ready"
  | "v2_not_materialized"
  | "v2_operational_ready"
  | "v2_operational_empty"
  | "blocked_task_graph"
  | "unknown_format";

export interface ExecutionOperationalReadinessFields {
  operational_readiness_status?: OperationalReadinessStatus | string;
  operational_tasks_count?: number;
  operational_readiness_blockers?: string[];
  operational_readiness_next_action?: string | null;
  operational_tasks_materialized?: boolean;
  plan_format?: string;
  execution_tasks_created?: boolean;
}

const READY_STATUSES = new Set<string>([
  "legacy_operational_ready",
  "v2_operational_ready",
]);

const STATUS_LABELS: Record<string, string> = {
  no_execution_plan: "No execution plan",
  invalid_tasks_json: "Invalid plan tasks",
  legacy_operational_ready: "Operational tasks ready (legacy)",
  v2_not_materialized: "Operational tasks not materialized",
  v2_operational_ready: "Operational tasks ready",
  v2_operational_empty: "Operational tasks empty after materialization",
  blocked_task_graph: "Operational task graph blocked",
  unknown_format: "Unrecognized plan format",
};

export function operationalReadinessLabel(
  status: string | undefined | null,
): string | null {
  if (!status) return null;
  return STATUS_LABELS[status] ?? status;
}

export function isOperationalReadinessReady(
  status: string | undefined | null,
): boolean {
  return !!status && READY_STATUSES.has(status);
}

export function operationalReadinessBadgeClasses(
  status: string | undefined | null,
): string {
  if (!status) {
    return "bg-slate-800/60 text-slate-400 border-slate-700";
  }
  if (READY_STATUSES.has(status)) {
    return "bg-emerald-900/30 text-emerald-300 border-emerald-800";
  }
  if (status === "v2_not_materialized" || status === "v2_operational_empty") {
    return "bg-amber-900/30 text-amber-300 border-amber-800";
  }
  return "bg-red-900/30 text-red-300 border-red-800";
}
