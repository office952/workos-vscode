import type { PlannedTaskRow, RealityTaskRow } from "@/api/execution";
import type { OperatorTaskTruthTask } from "@/api/operatorTaskTruth";
import { taskPrimaryLabel } from "@/lib/operatorTaskPresentation";

export type RealityTaskStatus = "not_started" | "in_progress" | "completed";

export type ExecutionNextAction =
  | {
      kind: "start";
      taskId: string;
      label: string;
      hint: string;
    }
  | {
      kind: "complete";
      taskId: string;
      label: string;
      hint: string;
    }
  | {
      kind: "blocked";
      taskId: string;
      label: string;
      hint: string;
      blockedBy: string[];
    }
  | {
      kind: "idle";
      hint: string;
    };

function statusOf(
  taskId: string,
  reality: { tasks: RealityTaskRow[] } | null,
): RealityTaskStatus {
  const obs = reality?.tasks.find((t) => t.task_id === taskId);
  if (!obs) return "not_started";
  if (obs.ended_at) return "completed";
  if (obs.started_at) return "in_progress";
  return "not_started";
}

function blockedByNames(truth: OperatorTaskTruthTask | undefined): string[] {
  if (!truth) return [];
  const fromObjects = (truth.runtime.blocking_tasks ?? [])
    .map((b) => {
      if (b && typeof b === "object") {
        const name = (b as { name?: unknown }).name;
        if (typeof name === "string" && name.trim()) return name.trim();
      }
      return null;
    })
    .filter((n): n is string => Boolean(n));
  if (fromObjects.length > 0) return fromObjects;
  return (truth.runtime.blocking_task_ids ?? []).filter(
    (id): id is string => typeof id === "string" && id.trim().length > 0,
  );
}

/**
 * First-fold operator decision: next Start / Complete / blocked-by.
 */
export function resolveExecutionNextAction(
  planTasks: PlannedTaskRow[],
  reality: { tasks: RealityTaskRow[] } | null,
  truthByTaskId: Record<string, OperatorTaskTruthTask>,
): ExecutionNextAction {
  for (const t of planTasks) {
    const status = statusOf(t.task_id, reality);
    const truth = truthByTaskId[t.task_id];
    const label = truth ? taskPrimaryLabel(truth.identity) : t.name || t.task_id;

    if (status === "in_progress") {
      return {
        kind: "complete",
        taskId: t.task_id,
        label,
        hint: "Task în curs — Complete este următoarea acțiune.",
      };
    }
  }

  for (const t of planTasks) {
    const status = statusOf(t.task_id, reality);
    if (status !== "not_started") continue;
    const truth = truthByTaskId[t.task_id];
    const label = truth ? taskPrimaryLabel(truth.identity) : t.name || t.task_id;
    const productionBlocked = truth?.runtime.production_release_blocked === true;
    const startable = truth ? truth.runtime.is_startable === true : true;
    const blocked = truth?.runtime.is_blocked === true || !startable || productionBlocked;

    if (!blocked) {
      return {
        kind: "start",
        taskId: t.task_id,
        label,
        hint: "Următorul task pornibil — folosește Start din tabel.",
      };
    }

    const blockers = blockedByNames(truth);
    return {
      kind: "blocked",
      taskId: t.task_id,
      label,
      hint: productionBlocked
        ? "Pornire blocată de decizii owner de producție."
        : "Următorul task din plan este blocat operațional.",
      blockedBy: blockers,
    };
  }

  return {
    kind: "idle",
    hint: "Niciun task Start/Complete disponibil — plan finalizat sau fără task-uri.",
  };
}
