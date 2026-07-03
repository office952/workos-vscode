import { useCallback, useEffect, useState } from "react";
import { employeesApi, type EmployeeDTO } from "@/api/costEngine";

export interface OperationalEmployeesState {
  employees: EmployeeDTO[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Live operational employee list — same source as `/employees`.
 * HR/Pontaj/Plăți/Avansuri demo modules attach metadata to this population.
 */
export function useOperationalEmployees(): OperationalEmployeesState {
  const [employees, setEmployees] = useState<EmployeeDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await employeesApi.list({ limit: 500, sort: "name" });
      setEmployees(res.items ?? []);
    } catch (err) {
      setEmployees([]);
      setError(err instanceof Error ? err.message : "Nu s-au putut încărca angajații.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { employees, loading, error, refresh };
}
