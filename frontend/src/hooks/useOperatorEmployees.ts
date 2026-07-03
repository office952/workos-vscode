import { useCallback, useEffect, useState } from "react";
import {
  operationalRegistryApi,
  type OperationResourceMapping,
  type RegistryEmployee,
} from "@/api/operationalRegistry";
import {
  listActiveRegistryEmployees,
  type OperatorEmployeeOption,
  toOperatorEmployeeOption,
} from "@/lib/operatorEmployeeEligibility";
import { resolveMappingFromList } from "@/features/operational-registry/operationResolution";
import type { OperatorTask } from "@/lib/mockData";

type RegistrySource = "db" | "error" | "loading";

interface UseOperatorEmployeesState {
  employees: OperatorEmployeeOption[];
  loading: boolean;
  error: string | null;
  source: RegistrySource;
  getMappingForTask: (task: OperatorTask | null) => OperationResourceMapping | null;
  refresh: () => Promise<void>;
}

export function useOperatorEmployees(
  taskForEligibility: OperatorTask | null = null
): UseOperatorEmployeesState {
  const [rawEmployees, setRawEmployees] = useState<RegistryEmployee[]>([]);
  const [mappings, setMappings] = useState<OperationResourceMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<RegistrySource>("loading");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [empRes, mapRes] = await Promise.all([
        operationalRegistryApi.listEmployees(),
        operationalRegistryApi.listOperationMappings().catch(() => ({ items: [], total: 0 })),
      ]);
      setRawEmployees(listActiveRegistryEmployees(empRes.items));
      setMappings(mapRes.items);
      setSource("db");
    } catch (err) {
      setRawEmployees([]);
      setMappings([]);
      setSource("error");
      setError(err instanceof Error ? err.message : "Eroare registry");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const getMappingForTask = useCallback(
    (task: OperatorTask | null): OperationResourceMapping | null => {
      if (!task?.operationCode) return null;
      return resolveMappingFromList(task.operationCode, mappings).mapping;
    },
    [mappings]
  );

  const mapping = getMappingForTask(taskForEligibility);
  const employees = rawEmployees.map((e) =>
    toOperatorEmployeeOption(e, taskForEligibility, mapping)
  );

  return {
    employees,
    loading,
    error,
    source,
    getMappingForTask,
    refresh: fetchData,
  };
}
