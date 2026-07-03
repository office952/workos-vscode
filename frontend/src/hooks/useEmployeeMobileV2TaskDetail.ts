import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchEmployeeMobileTaskByOrder,
  type EmployeeMobileTaskDTO,
} from "@/api/employeeMobileTasks";
import { useEmployeeMobileV2AvailableTasks } from "@/hooks/useEmployeeMobileV2AvailableTasks";
import { useEmployeeMobileV2Tasks } from "@/hooks/useEmployeeMobileV2Tasks";
import {
  EMPLOYEE_MOBILE_TASK_NOT_ACCESSIBLE_MESSAGE,
  resolveEmployeeMobileV2Task,
} from "@/lib/resolveEmployeeMobileV2Task";

export function useEmployeeMobileV2TaskDetail(
  taskId: string | undefined,
  orderId: number | null,
) {
  const {
    tasks: myTasks,
    loading: myLoading,
    error: myError,
    reload: reloadMy,
  } = useEmployeeMobileV2Tasks();
  const {
    tasks: availableTasks,
    loading: availableLoading,
    error: availableError,
    reload: reloadAvailable,
  } = useEmployeeMobileV2AvailableTasks();

  const [fetchedTask, setFetchedTask] = useState<EmployeeMobileTaskDTO | null>(null);
  const [fetchLoading, setFetchLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const listResolved = useMemo(
    () =>
      resolveEmployeeMobileV2Task({
        taskId,
        orderId,
        myTasks,
        availableTasks,
      }),
    [taskId, orderId, myTasks, availableTasks],
  );

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
      const message = err instanceof Error ? err.message : "Nu am putut încărca taskul.";
      setFetchError(message || EMPLOYEE_MOBILE_TASK_NOT_ACCESSIBLE_MESSAGE);
    } finally {
      setFetchLoading(false);
    }
  }, [orderId, taskId]);

  useEffect(() => {
    if (!taskId || orderId == null || myLoading || availableLoading) {
      return;
    }
    void loadFromEndpoint();
  }, [taskId, orderId, myLoading, availableLoading, loadFromEndpoint]);

  const task =
    orderId != null && fetchedTask
      ? fetchedTask
      : listResolved ?? fetchedTask;
  const loading =
    myLoading || availableLoading || (orderId != null && taskId ? fetchLoading : false);
  const error = myError || availableError || fetchError;

  const reload = useCallback(async () => {
    await Promise.all([reloadMy(), reloadAvailable()]);
    if (taskId && orderId != null) {
      await loadFromEndpoint();
    }
  }, [reloadMy, reloadAvailable, taskId, orderId, loadFromEndpoint]);

  return {
    task,
    loading,
    error,
    reload,
    myTasks,
    availableTasks,
  };
}
