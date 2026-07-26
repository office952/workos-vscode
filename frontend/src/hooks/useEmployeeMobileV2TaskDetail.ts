import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchEmployeeMobileTaskByOrder,
  type EmployeeMobileTaskDTO,
} from "@/api/employeeMobileTasks";
import { useEmployeeMobileV2TaskTruthContext } from "@/contexts/EmployeeMobileV2TaskTruthContext";
import {
  EMPLOYEE_MOBILE_TASK_NOT_ACCESSIBLE_MESSAGE,
  resolveEmployeeMobileV2Task,
} from "@/lib/resolveEmployeeMobileV2Task";
import { findTruthTaskById } from "@/lib/employeeMobileV2TaskTruth";
import { mapMobileTaskErrorMessage } from "@/lib/employeeMobileV2TaskErrors";

export function useEmployeeMobileV2TaskDetail(
  taskId: string | undefined,
  orderId: number | null,
) {
  const {
    view,
    loading: truthLoading,
    error: truthError,
    reload: reloadTruth,
  } = useEmployeeMobileV2TaskTruthContext();

  const myTasks = view?.assignedTasks ?? [];
  const availableTasks = view?.availableTasks ?? [];

  const [fetchedTask, setFetchedTask] = useState<EmployeeMobileTaskDTO | null>(null);
  const [fetchLoading, setFetchLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const listResolved = useMemo(() => {
    if (view && taskId && orderId != null) {
      const fromTruth = findTruthTaskById(view, taskId, orderId);
      if (fromTruth) return fromTruth;
    }
    return resolveEmployeeMobileV2Task({
      taskId,
      orderId,
      myTasks,
      availableTasks,
    });
  }, [view, taskId, orderId, myTasks, availableTasks]);

  const loadFromEndpoint = useCallback(async () => {
    if (!taskId || orderId == null) {
      setFetchedTask(null);
      setFetchError(null);
      return;
    }
    setFetchLoading(true);
    setFetchError(null);
    try {
      const row = await fetchEmployeeMobileTaskByOrder(orderId, taskId);
      setFetchedTask(row);
    } catch (err) {
      setFetchedTask(null);
      const message = mapMobileTaskErrorMessage(err);
      setFetchError(message || EMPLOYEE_MOBILE_TASK_NOT_ACCESSIBLE_MESSAGE);
    } finally {
      setFetchLoading(false);
    }
  }, [orderId, taskId]);

  useEffect(() => {
    if (!taskId || orderId == null || truthLoading) {
      return;
    }
    void loadFromEndpoint();
  }, [taskId, orderId, truthLoading, loadFromEndpoint]);

  const task =
    orderId != null && fetchedTask
      ? fetchedTask
      : listResolved ?? fetchedTask;
  const loading = truthLoading || (orderId != null && taskId ? fetchLoading : false);
  const error = truthError || fetchError;

  const reload = useCallback(async (options?: { background?: boolean }) => {
    await reloadTruth(options);
    if (taskId && orderId != null) {
      if (options?.background) {
        try {
          const row = await fetchEmployeeMobileTaskByOrder(orderId, taskId);
          setFetchedTask(row);
        } catch {
          // preserve action feedback on background refresh failure
        }
      } else {
        await loadFromEndpoint();
      }
    }
  }, [reloadTruth, taskId, orderId, loadFromEndpoint]);

  return {
    task,
    loading,
    error,
    reload,
    myTasks,
    availableTasks,
  };
}
