import { useCallback, useState } from "react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  employeeMobileRuntimeTaskKey,
  executeEmployeeMobileComplete,
  mapEmployeeMobileRuntimeError,
  type EmployeeMobileCompleteResponse,
} from "@/lib/employeeMobileV2RuntimeAction";

export function useEmployeeMobileV2RuntimeAction() {
  const [pendingKey, setPendingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isPending = useCallback(
    (task: Pick<EmployeeMobileTaskDTO, "order_id" | "task_id">) =>
      pendingKey === employeeMobileRuntimeTaskKey(task),
    [pendingKey],
  );

  const completeTask = useCallback(
    async (
      task: EmployeeMobileTaskDTO,
      onSuccess?: (result: EmployeeMobileCompleteResponse, task: EmployeeMobileTaskDTO) => void | Promise<void>,
    ) => {
      const key = employeeMobileRuntimeTaskKey(task);
      setPendingKey(key);
      setError(null);
      try {
        const result = await executeEmployeeMobileComplete(task);
        await onSuccess?.(result, task);
        return result;
      } catch (err) {
        const message = mapEmployeeMobileRuntimeError(err);
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
    completeTask,
    isPending,
    pendingKey,
    error,
    clearError,
  };
}
