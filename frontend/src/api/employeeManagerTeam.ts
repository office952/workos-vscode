/**
 * Manager team read-only workspace — server-side direct-report scope.
 */
import { throwEmployeeRequestApiError } from "@/api/employeeRequestErrors";
import type { AttendanceEventType } from "@/api/employeeAttendance";
import { getAPIBaseURL } from "@/lib/config";

const base = () => `${getAPIBaseURL()}/api/v1/employee-mobile/manager`;

export interface ManagerTeamAttendanceEventDTO {
  id: number;
  employee_id: number;
  employee_name: string;
  start_date: string;
  end_date: string;
  event_type: AttendanceEventType | string;
  event_status: string;
  hours_override?: number | null;
  hours_delta?: number | null;
  notes?: string | null;
  source: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ManagerTeamRequestDTO {
  id: number;
  employee_id: number;
  request_type: string;
  status: string;
  title?: string | null;
  description?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  amount?: number | null;
  currency?: string | null;
  reason?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  reviewed_by_user_id?: string | null;
  review_note?: string | null;
  employee_name: string;
  employee_department?: string | null;
  employee_operational_role?: string | null;
  employee_status: string;
}

export interface ManagerTeamAttendanceListParams {
  start_date?: string;
  end_date?: string;
  employee_id?: number;
  event_type?: AttendanceEventType | string;
}

export interface ManagerTeamRequestsListParams {
  status?: string;
  request_type?: string;
  employee_id?: number;
  start_date?: string;
  end_date?: string;
}

async function request<T>(path: string, params?: Record<string, string>): Promise<T> {
  const q = params && Object.keys(params).length ? `?${new URLSearchParams(params).toString()}` : "";
  const res = await fetch(`${base()}${path}${q}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    await throwEmployeeRequestApiError(res, "manager-team");
  }

  return res.json() as Promise<T>;
}

function buildQuery(params: Record<string, string | number | undefined>): Record<string, string> {
  const query: Record<string, string> = {};
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      query[key] = String(value);
    }
  }
  return query;
}

export async function listManagerTeamAttendance(
  params: ManagerTeamAttendanceListParams = {},
): Promise<ManagerTeamAttendanceEventDTO[]> {
  return request<ManagerTeamAttendanceEventDTO[]>(
    "/team-attendance",
    buildQuery(params),
  );
}

export async function listManagerTeamRequests(
  params: ManagerTeamRequestsListParams = {},
): Promise<ManagerTeamRequestDTO[]> {
  return request<ManagerTeamRequestDTO[]>("/team-requests", buildQuery(params));
}

export const employeeManagerTeamApi = {
  listAttendance: listManagerTeamAttendance,
  listRequests: listManagerTeamRequests,
};
