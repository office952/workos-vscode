/**
 * Operator task identity presentation (W6-T02).
 * Renders backend-provided identity only — no task-key or name parsing.
 */
import type {
  OperatorTaskTruthTask,
  TaskIdentityTruth,
  TaskRuntimeTruth,
} from "@/api/operatorTaskTruth";

/** Fallback labels when backend omits component_label. Mirrors backend role map + repo terms. */
export const COMPONENT_ROLE_LABEL_FALLBACK: Record<string, string> = {
  root_product: "Produs principal",
  mounting_panel: "Panou suport",
  premount_structure: "Structură premontaj",
  volum_aluminum: "Cant / volum aluminiu",
  linked_segment: "Segment legat",
};

export type TaskTruthReadiness = {
  is_startable: boolean;
  is_blocked: boolean;
  readiness_label?: string | null;
  readiness_reasons: Array<Record<string, unknown>>;
  blocking_reasons: Array<Record<string, unknown>>;
};

export function indexOperatorTaskTruth(
  tasks: OperatorTaskTruthTask[],
): Record<string, OperatorTaskTruthTask> {
  const out: Record<string, OperatorTaskTruthTask> = {};
  for (const task of tasks) {
    out[task.identity.task_id] = task;
  }
  return out;
}

export function resolveTaskTruth(
  byTaskId: Record<string, OperatorTaskTruthTask>,
  taskId: string,
): OperatorTaskTruthTask | undefined {
  return byTaskId[taskId];
}

export function isLegacyTaskIdentity(identity: TaskIdentityTruth): boolean {
  return (
    identity.identity_source === "legacy_plan_task" ||
    identity.identity_classification === "LEGACY_NAME_BASED_IDENTITY"
  );
}

export function isPartialLogoIdentity(identity: TaskIdentityTruth): boolean {
  return Boolean(identity.logo_segment_key) || identity.component_role === "linked_segment";
}

export function componentLabelFromBackend(identity: TaskIdentityTruth): string | null {
  const backend = identity.component_label?.trim();
  if (backend) return backend;
  const role = identity.component_role?.trim();
  if (role && COMPONENT_ROLE_LABEL_FALLBACK[role]) {
    return COMPONENT_ROLE_LABEL_FALLBACK[role];
  }
  if (isLegacyTaskIdentity(identity)) {
    return "Componentă legacy";
  }
  return null;
}

export function componentRoleBadgeLabel(identity: TaskIdentityTruth): string | null {
  if (isLegacyTaskIdentity(identity)) return "Legacy";
  const role = identity.component_role?.trim();
  if (!role) return null;
  return role.replace(/_/g, " ");
}

export function taskPrimaryLabel(identity: TaskIdentityTruth): string {
  const label = identity.display_label?.trim();
  if (label) return label;
  return identity.task_id;
}

export function taskTruthReadinessFromRuntime(runtime: TaskRuntimeTruth): TaskTruthReadiness {
  return {
    is_startable: runtime.is_startable === true,
    is_blocked: runtime.is_blocked === true,
    readiness_label: runtime.readiness_label,
    readiness_reasons: runtime.readiness_reasons ?? [],
    blocking_reasons: runtime.blocking_reasons ?? [],
  };
}

export function firstReadinessMessage(readiness: TaskTruthReadiness): string | null {
  const fromReason = readiness.readiness_reasons?.[0];
  if (fromReason && typeof fromReason.message === "string" && fromReason.message.trim()) {
    return fromReason.message;
  }
  const fromBlock = readiness.blocking_reasons?.[0];
  if (fromBlock && typeof fromBlock.message === "string" && fromBlock.message.trim()) {
    return fromBlock.message;
  }
  return readiness.readiness_label?.trim() || null;
}

export function diagnosticTaskKey(identity: TaskIdentityTruth): string {
  return identity.deterministic_task_key?.trim() || identity.task_id;
}

export function identitySourceLabel(identity: TaskIdentityTruth): string {
  return identity.identity_source;
}
