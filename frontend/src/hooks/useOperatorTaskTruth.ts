import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchOperatorTaskTruth,
  type OperatorTaskTruthResponse,
  type OperatorTaskTruthTask,
} from "@/api/operatorTaskTruth";
import { indexOperatorTaskTruth } from "@/lib/operatorTaskPresentation";

export type UseOperatorTaskTruthResult = {
  data: OperatorTaskTruthResponse | null;
  tasksById: Record<string, OperatorTaskTruthTask>;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
};

/**
 * Canonical operator task-truth fetch for a single order.
 * Parent surfaces own the call — children receive indexed tasks via props.
 */
export function useOperatorTaskTruth(
  orderId: number | null | undefined,
): UseOperatorTaskTruthResult {
  const [data, setData] = useState<OperatorTaskTruthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (orderId == null || orderId <= 0) {
      setData(null);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetchOperatorTaskTruth(orderId);
      setData(response);
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Eroare task-truth");
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  const tasksById = useMemo(
    () => (data ? indexOperatorTaskTruth(data.tasks) : {}),
    [data],
  );

  return { data, tasksById, loading, error, refresh: load };
}
