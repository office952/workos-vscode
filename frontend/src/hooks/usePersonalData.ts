import { useEffect, useState, useCallback } from "react";
import { employeesApi, type EmployeeDTO } from "@/api/costEngine";
import { isMockEnabled } from "@/lib/mockGuard";
import {
  personalMembers as mockPersonal,
  type PersonalMember,
  type PersonalRole,
  type PersonalStatus,
} from "@/lib/mockData";

type PersonalSource = "db" | "mock" | "empty" | "error" | "loading";

interface PersonalDataState {
  members: PersonalMember[];
  loading: boolean;
  error: string | null;
  source: PersonalSource;
  refresh: () => Promise<void>;
}

/**
 * Map an EmployeeDTO from the backend to the PersonalMember shape used by the UI.
 */
function mapEmployeeToMember(emp: EmployeeDTO): PersonalMember {
  // Map employee_type / role to PersonalRole
  const roleMap: Record<string, PersonalRole> = {
    operator: "operator",
    team_lead: "team_lead",
    technician: "technician",
    manager: "manager",
    apprentice: "apprentice",
  };
  const role: PersonalRole =
    roleMap[(emp.role ?? "operator").toLowerCase()] ?? "operator";

  // Map status to PersonalStatus
  const statusMap: Record<string, PersonalStatus> = {
    active: "active",
    on_leave: "on_leave",
    sick: "sick",
    training: "training",
    inactive: "on_leave",
  };
  const status: PersonalStatus =
    statusMap[(emp.status ?? "active").toLowerCase()] ?? "active";

  // Parse skills array
  const skills: string[] = Array.isArray(emp.skills)
    ? emp.skills
    : [];

  // Parse machines array for workcenter info
  const machines: string[] = Array.isArray(emp.machines)
    ? emp.machines
    : [];

  return {
    id: `EMP-${String(emp.id).padStart(2, "0")}`,
    name: emp.name,
    role,
    status,
    workcenterId: machines[0] ?? "general",
    workcenterName: emp.department ?? "General",
    skills,
    currentTaskId: null,
    currentJobId: null,
    shiftStart: status === "active" ? "06:00" : "—",
    shiftEnd: status === "active" ? "14:00" : "—",
    hoursToday: status === "active" ? 4.0 : 0,
    tasksCompletedToday: 0,
    tasksCompletedWeek: 0,
    avgTaskDurationMin: 0,
    qualityScore: emp.valid_for_cost_engine ? 90 : 75,
    phone: emp.observatii ?? "—",
    hireDate: emp.data_angajare ?? "2024-01-01",
  };
}

export function usePersonalData(): PersonalDataState {
  const mockEnabled = isMockEnabled();
  const [members, setMembers] = useState<PersonalMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<PersonalSource>("loading");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await employeesApi.list({ limit: 500 });
      if (res.items && res.items.length > 0) {
        setMembers(res.items.map(mapEmployeeToMember));
        setSource("db");
      } else if (mockEnabled) {
        // DB is empty — fall back to mock
        setMembers(mockPersonal);
        setSource("mock");
      } else {
        setMembers([]);
        setSource("empty");
      }
    } catch (err) {
      if (mockEnabled) {
        console.warn("[usePersonalData] API failed, using mock data", err);
        setMembers(mockPersonal);
        setSource("mock");
      } else {
        console.warn("[usePersonalData] API failed, mock disabled", err);
        setMembers([]);
        setSource("error");
      }
      setError(err instanceof Error ? err.message : "Eroare necunoscută");
    } finally {
      setLoading(false);
    }
  }, [mockEnabled]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { members, loading, error, source, refresh: fetchData };
}