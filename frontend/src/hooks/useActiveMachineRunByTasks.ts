/**
 * Bounded active-MachineRun lookups for task rows.
 * One GET by-task per unique (plan_id, task_key); shared in-memory cache per page mount.
 * Acceptable at current Ops-Graph / ExecutionDetail scale (~10–20 tasks).
 */
import { useEffect, useMemo, useRef, useState } from "react";
import {
  getActiveMachineRunByTask,
  type ActiveMachineRunByTask,
} from "@/api/machineRuns";
import { candidateSelectionKey } from "@/lib/machineRunUi";

export type TaskLookupRef = {
  execution_plan_id: number;
  task_key: string;
};

export type ActiveMachineRunLookupMap = Map<string, ActiveMachineRunByTask | null>;

export function useActiveMachineRunByTasks(
  refs: TaskLookupRef[],
  enabled: boolean,
): {
  byKey: ActiveMachineRunLookupMap;
  loading: boolean;
  requestCount: number;
  taskCount: number;
} {
  const uniqueRefs = useMemo(() => {
    const seen = new Set<string>();
    const out: TaskLookupRef[] = [];
    for (const r of refs) {
      if (!r.execution_plan_id || !r.task_key) continue;
      const k = candidateSelectionKey(r.execution_plan_id, r.task_key);
      if (seen.has(k)) continue;
      seen.add(k);
      out.push(r);
    }
    return out;
  }, [refs]);

  const cacheRef = useRef<ActiveMachineRunLookupMap>(new Map());
  const [byKey, setByKey] = useState<ActiveMachineRunLookupMap>(() => new Map());
  const [loading, setLoading] = useState(false);
  const [requestCount, setRequestCount] = useState(0);

  const refsKey = uniqueRefs
    .map((r) => candidateSelectionKey(r.execution_plan_id, r.task_key))
    .join("|");

  useEffect(() => {
    if (!enabled || uniqueRefs.length === 0) {
      setByKey(new Map());
      setLoading(false);
      setRequestCount(0);
      return;
    }

    let cancelled = false;
    const missing = uniqueRefs.filter(
      (r) =>
        !cacheRef.current.has(
          candidateSelectionKey(r.execution_plan_id, r.task_key),
        ),
    );

    const applyKnown = () => {
      const next = new Map<string, ActiveMachineRunByTask | null>();
      for (const r of uniqueRefs) {
        const k = candidateSelectionKey(r.execution_plan_id, r.task_key);
        if (cacheRef.current.has(k)) {
          next.set(k, cacheRef.current.get(k) ?? null);
        }
      }
      setByKey(next);
    };

    if (missing.length === 0) {
      applyKnown();
      setLoading(false);
      setRequestCount(0);
      return;
    }

    setLoading(true);
    setRequestCount(missing.length);
    applyKnown();

    void (async () => {
      await Promise.all(
        missing.map(async (r) => {
          const k = candidateSelectionKey(r.execution_plan_id, r.task_key);
          try {
            const result = await getActiveMachineRunByTask(
              r.execution_plan_id,
              r.task_key,
            );
            cacheRef.current.set(k, result.membership);
          } catch {
            // Lookup failure → no chip (avoid fake membership).
            cacheRef.current.set(k, null);
          }
        }),
      );
      if (cancelled) return;
      applyKnown();
      setLoading(false);
    })();

    return () => {
      cancelled = true;
    };
    // refsKey encodes uniqueRefs identity for this mount batch.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional key
  }, [enabled, refsKey]);

  return {
    byKey,
    loading,
    requestCount,
    taskCount: uniqueRefs.length,
  };
}
