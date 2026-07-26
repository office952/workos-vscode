import { useCallback, useState } from "react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  employeeMobileStartTaskKey,
  executeEmployeeMobileStart,
  mapEmployeeMobileStartError,
  type EmployeeMobileStartResponse,
} from "@/lib/employeeMobileV2StartAction";

export function useEmployeeMobileV2StartAction() {
  const [pendingKey, setPendingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isPending = useCallback(
    (task: Pick<EmployeeMobileTaskDTO, "order_id" | "task_id">) =>
      pendingKey === employeeMobileStartTaskKey(task),
    [pendingKey],
  );

  const startTask = useCallback(
    async (
      task: EmployeeMobileTaskDTO,
      onSuccess?: (result: EmployeeMobileStartResponse, task: EmployeeMobileTaskDTO) => void | Promise<void>,
    ) => {
      const key = employeeMobileStartTaskKey(task);
      setPendingKey(key);
      setError(null);
      try {
        const result = await executeEmployeeMobileStart(task);
        await onSuccess?.(result, task);
        return result;
      } catch (err) {
        const message = mapEmployeeMobileStartError(err);
        setError(message);
        throw err;
      } finally {
        setPendingKey((current) => (current === key ? null : current));
      }
    },
    [],
  );

  const clearError = useCallback(() => setError(null), []);

  return {
    startTask,
    isPending,
    pendingKey,
    error,
    clearError,
  };
}
