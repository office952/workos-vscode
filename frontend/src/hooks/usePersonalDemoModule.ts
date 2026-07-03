import { useMemo } from "react";
import { useOperationalEmployees } from "@/hooks/useOperationalEmployees";
import type { Advance, EmployeeDocument, InternalAlert, EmployeeRecord } from "@/lib/employeeRecordsData";
import {
  buildDemoAdvancesForEmployees,
  buildDemoAlertsForEmployees,
  buildDemoDocumentsForEmployees,
  buildEmployeeRecordsFromOperational,
} from "@/lib/operationalEmployeeRecords";

export interface PersonalDemoModuleState {
  employeeRecords: EmployeeRecord[];
  documents: EmployeeDocument[];
  advances: Advance[];
  alerts: InternalAlert[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/** Live operational employee population + deterministic demo HR module metadata. */
export function usePersonalDemoModule(): PersonalDemoModuleState {
  const { employees, loading, error, refresh } = useOperationalEmployees();

  const employeeRecords = useMemo(
    () => buildEmployeeRecordsFromOperational(employees),
    [employees]
  );

  const documents = useMemo(
    () => buildDemoDocumentsForEmployees(employeeRecords),
    [employeeRecords]
  );

  const advances = useMemo(
    () => buildDemoAdvancesForEmployees(employeeRecords),
    [employeeRecords]
  );

  const alerts = useMemo(
    () => buildDemoAlertsForEmployees(employeeRecords),
    [employeeRecords]
  );

  return {
    employeeRecords,
    documents,
    advances,
    alerts,
    loading,
    error,
    refresh,
  };
}
