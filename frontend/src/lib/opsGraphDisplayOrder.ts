/**
 * Ops-graph display ordering — Capacity Owner GO (topo readability).
 *
 * Default operator reading order = dependency / topological execution order.
 * Original sequence_index (SEQ) is NEVER remapped to 1..N — it stays on each
 * task as source reference for the UI column.
 *
 * Display-only. Does not mutate envelopes, invent deps, or touch Pricing/HR.
 */

export type OpsGraphOrderableTask = {
  task_id: string;
  sequence_index?: number | null;
  depends_on_task_ids?: string[] | null;
  read_clarity?: {
    identity?: {
      sequence_index?: number | null;
    } | null;
  } | null;
};

function sourceSequenceIndex(task: OpsGraphOrderableTask): number {
  const fromClarity = task.read_clarity?.identity?.sequence_index;
  if (typeof fromClarity === "number" && Number.isFinite(fromClarity)) {
    return fromClarity;
  }
  if (typeof task.sequence_index === "number" && Number.isFinite(task.sequence_index)) {
    return task.sequence_index;
  }
  return Number.MAX_SAFE_INTEGER;
}

function compareBySourceSeqThenId(a: OpsGraphOrderableTask, b: OpsGraphOrderableTask): number {
  const sa = sourceSequenceIndex(a);
  const sb = sourceSequenceIndex(b);
  if (sa !== sb) return sa - sb;
  return a.task_id.localeCompare(b.task_id);
}

/**
 * Kahn topological sort. Tie-break ready set by original source SEQ, then task_id.
 * Unknown dependency ids (outside the task set) are ignored.
 * Cycles / leftovers append by source SEQ (honest fallback; SEQ values unchanged).
 */
export function sortTasksByDependencyDisplayOrder<T extends OpsGraphOrderableTask>(
  tasks: T[],
): T[] {
  if (tasks.length <= 1) return [...tasks];

  const byId = new Map<string, T>();
  for (const task of tasks) {
    byId.set(task.task_id, task);
  }
  const ids = tasks.map((t) => t.task_id);

  const indegree = new Map<string, number>();
  const dependents = new Map<string, string[]>();
  for (const id of ids) {
    indegree.set(id, 0);
    dependents.set(id, []);
  }

  for (const task of tasks) {
    const deps = task.depends_on_task_ids ?? [];
    for (const depId of deps) {
      if (!byId.has(depId)) continue;
      indegree.set(task.task_id, (indegree.get(task.task_id) ?? 0) + 1);
      dependents.get(depId)!.push(task.task_id);
    }
  }

  const ready: string[] = ids
    .filter((id) => (indegree.get(id) ?? 0) === 0)
    .sort((a, b) => compareBySourceSeqThenId(byId.get(a)!, byId.get(b)!));

  const ordered: T[] = [];
  const placed = new Set<string>();

  while (ready.length > 0) {
    const id = ready.shift()!;
    if (placed.has(id)) continue;
    placed.add(id);
    ordered.push(byId.get(id)!);

    for (const childId of dependents.get(id) ?? []) {
      const next = (indegree.get(childId) ?? 1) - 1;
      indegree.set(childId, next);
      if (next === 0 && !placed.has(childId)) {
        ready.push(childId);
        ready.sort((a, b) => compareBySourceSeqThenId(byId.get(a)!, byId.get(b)!));
      }
    }
  }

  if (ordered.length < tasks.length) {
    const leftovers = ids
      .filter((id) => !placed.has(id))
      .map((id) => byId.get(id)!)
      .sort(compareBySourceSeqThenId);
    for (const task of leftovers) {
      ordered.push(task);
    }
  }

  return ordered;
}

export function sourceSequenceIndexForDisplay(task: OpsGraphOrderableTask): number | "—" {
  const n = sourceSequenceIndex(task);
  return n === Number.MAX_SAFE_INTEGER ? "—" : n;
}

export const OPS_GRAPH_DISPLAY_ORDER_NOTE =
  "Display order: dependency order · SEQ: original source sequence (not remapped)";
