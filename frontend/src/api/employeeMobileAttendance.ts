/**
 * Employee-mobile self-only attendance — read-only, no client employee_id.
 */
import { throwEmployeeRequestApiError } from "@/api/employeeRequestErrors";
import type { AttendanceEventDTO, AttendanceEventType } from "@/api/employeeAttendance";
import { getAPIBaseURL } from "@/lib/config";

const base = () => `${getAPIBaseURL()}/api/v1/employee-mobile/attendance`;

export interface SelfAttendanceListParams {
  start_date?: string;
  end_date?: string;
  event_type?: AttendanceEventType;
}

async function request<T>(params?: Record<string, string>): Promise<T> {
  const q = params ? `?${new URLSearchParams(params).toString()}` : "";
  const res = await fetch(`${base()}${q}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    await throwEmployeeRequestApiError(res, "self");
  }

  return res.json() as Promise<T>;
}

export async function listMyAttendanceEvents(
  params: SelfAttendanceListParams = {},
): Promise<AttendanceEventDTO[]> {
  const query: Record<string, string> = {};
  if (params.start_date) query.start_date = params.start_date;
  if (params.end_date) query.end_date = params.end_date;
  if (params.event_type) query.event_type = params.event_type;
  return request<AttendanceEventDTO[]>(Object.keys(query).length ? query : undefined);
}

export const employeeMobileAttendanceApi = {
  list: listMyAttendanceEvents,
};
