/**
 * Pure helpers for ExecutionPlan V2 Step 9B readiness honesty.
 * Values come from backend preview/audit — UI never invents readiness.
 */

export interface PlannedTaskLike {
  source_operation_code?: string | null;
  depends_on_task_keys?: string[];
  machine_requirement?: { workcenter?: string | null } | null;
  estimated_minutes?: number | null;
  warnings?: string[];
}

export interface PlannedOperationLike {
  operation_code: string;
  workcenter?: string | null;
}

export interface MaterializationAuditLike {
  execution_plan_id?: number;
  materialization_status?: string;
  operational_tasks_in_envelope_count?: number;
  planned_task_count?: number;
  operation_count?: number;
  guards?: { post_materialize_allowed?: boolean };
}

export function deriveOrphanOperations(
  operations: PlannedOperationLike[],
  tasks: PlannedTaskLike[],
): PlannedOperationLike[] {
  const sourced = new Set(
    tasks
      .map((task) => task.source_operation_code)
      .filter((code): code is string => typeof code === "string" && code.length > 0),
  );
  return operations.filter((op) => !sourced.has(op.operation_code));
}

export function countMissingWorkcenters(tasks: PlannedTaskLike[]): number {
  return tasks.filter((task) => !task.machine_requirement?.workcenter).length;
}

export function countMissingMinutes(tasks: PlannedTaskLike[]): number {
  return tasks.filter((task) => task.estimated_minutes == null).length;
}

export function hasOperationalTasksInEnvelope(audit: MaterializationAuditLike | null): boolean {
  return (audit?.operational_tasks_in_envelope_count ?? 0) > 0;
}

/** Session Start/Stop only when ops exist AND materialize gate still allows further operational work. */
export function allowExecutionSessionActions(audit: MaterializationAuditLike | null): boolean {
  if (!hasOperationalTasksInEnvelope(audit)) return false;
  return audit?.guards?.post_materialize_allowed === true;
}

export function planLifecycleLabel(args: {
  hasPreview: boolean;
  audit: MaterializationAuditLike | null;
  persistStatus?: string | null;
}): {
  draftLabel: string;
  materializationLabel: string;
  nextStepLabel: string;
} {
  const materialized = hasOperationalTasksInEnvelope(args.audit);
  const draftPersisted =
    args.audit?.execution_plan_id != null ||
    (typeof args.persistStatus === "string" &&
      args.persistStatus !== "not_persisted" &&
      args.persistStatus.length > 0);

  if (materialized) {
    return {
      draftLabel: "Plan operațional (envelope)",
      materializationLabel: "MATERIALIZED_IN_ENVELOPE",
      nextStepLabel: "Taskurile operaționale există în envelope — sesiunile rămân blocate fără Owner GO.",
    };
  }

  if (!args.hasPreview) {
    return {
      draftLabel: "Plan lipsă",
      materializationLabel: "NOT_MATERIALIZED",
      nextStepLabel: "Nu există previzualizare ExecutionPlan V2 pentru această comandă.",
    };
  }

  return {
    draftLabel: draftPersisted ? "Plan de execuție — draft persistat" : "Plan de execuție — draft / previzualizare",
    materializationLabel: "NOT_MATERIALIZED",
    nextStepLabel:
      "Taskurile operaționale nu au fost create. Lansarea în producție este blocată până la rezolvarea deciziilor operaționale.",
  };
}
