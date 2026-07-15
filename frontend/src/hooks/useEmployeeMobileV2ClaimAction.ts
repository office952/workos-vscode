import { useCallback, useState } from "react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileClaimResult } from "@/api/employeeMobileTasks";
import {
  employeeMobileClaimTaskKey,
  executeEmployeeMobileClaim,
  mapEmployeeMobileClaimError,
} from "@/lib/employeeMobileV2ClaimAction";

export function useEmployeeMobileV2ClaimAction() {
  const [pendingKey, setPendingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isPending = useCallback(
    (task: Pick<EmployeeMobileTaskDTO, "order_id" | "task_id">) =>
      pendingKey === employeeMobileClaimTaskKey(task),
    [pendingKey],
  );

  const claimTask = useCallback(
    async (
      task: EmployeeMobileTaskDTO,
      onSuccess?: (result: EmployeeMobileClaimResult, task: EmployeeMobileTaskDTO) => void | Promise<void>,
    ) => {
      const key = employeeMobileClaimTaskKey(task);
      setPendingKey(key);
      setError(null);
      try {
        const result = await executeEmployeeMobileClaim(task);
        await onSuccess?.(result, task);
        return result;
      } catch (err) {
        const message = mapEmployeeMobileClaimError(err);
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
    claimTask,
    isPending,
    pendingKey,
    error,
    clearError,
  };
}
