import { useCallback, useEffect, useState } from "react";
import {
  listAvailableEmployeeMobileTasks,
  type EmployeeMobileTaskDTO,
} from "@/api/employeeMobileTasks";

export function useEmployeeMobileV2AvailableTasks() {
  const [tasks, setTasks] = useState<EmployeeMobileTaskDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listAvailableEmployeeMobileTasks();
      setTasks(rows);
    } catch (err) {
      setTasks([]);
      setError(err instanceof Error ? err.message : "Nu am putut încărca taskurile disponibile.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { tasks, loading, error, reload };
}
