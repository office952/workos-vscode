/**
 * Internal employee attendance API — default present + exception events.
 */
import { getAPIBaseURL } from "@/lib/config";
import { formatApiErrorResponse } from "@/lib/apiError";

const base = () => `${getAPIBaseURL()}/api/v1/employee-attendance`;

export type AttendanceEventType =
  | "absent"
  | "leave"
  | "sick"
  | "partial"
  | "overtime"
  | "correction";

export type AttendanceEventStatus = "planned" | "approved" | "confirmed" | "cancelled";

export interface AttendanceEventDTO {
  id: number;
  employee_id: number;
  start_date: string;
  end_date: string;
  event_type: AttendanceEventType;
  event_status: AttendanceEventStatus;
  hours_override?: number | null;
  hours_delta?: number | null;
  notes?: string | null;
  source: string;
  created_at?: string | null;
  updated_at?: string | null;
  employee_name?: string | null;
}

export interface AttendanceEventPayload {
  employee_id: number;
  start_date: string;
  end_date?: string | null;
  event_type: AttendanceEventType;
  event_status?: AttendanceEventStatus;
  hours_override?: number | null;
  hours_delta?: number | null;
  notes?: string | null;
  source?: string;
}

export interface AttendanceEmployeeSummaryDTO {
  employee_id: number;
  employee_name: string;
  standard_work_days: number;
  standard_hours: number;
  present_days: number;
  absent_days: number;
  leave_days: number;
  sick_days: number;
  partial_days: number;
  overtime_hours: number;
  total_hours: number;
  event_count: number;
  planned_event_count?: number;
  approved_event_count?: number;
  confirmed_event_count?: number;
  cancelled_event_count?: number;
}

export interface AttendanceMonthSummaryDTO {
  year: number;
  month: number;
  standard_work_hours_per_day: number;
  employees: AttendanceEmployeeSummaryDTO[];
}

export type AttendanceEffectStatus = "pending" | "applied" | "conflict" | "cancelled";

export interface AttendanceEffectDTO {
  id: number;
  employee_request_id: number;
  employee_id: number;
  request_type: string;
  effect_type: string;
  status: AttendanceEffectStatus;
  date_start?: string | null;
  date_end?: string | null;
  hours?: number | null;
  generated_by_user_id: string;
  generated_at?: string | null;
  applied_at?: string | null;
  applied_by_user_id?: string | null;
  source: string;
  notes?: string | null;
  conflict_reason?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AttendanceEffectApplyResultDTO {
  effect_id: number;
  employee_request_id: number;
  employee_id: number;
  effect_status: string;
  attendance_event_id: number;
  already_applied: boolean;
}

export interface AttendanceEffectGenerationCandidateDTO {
  employee_request_id: number;
  employee_id: number;
  employee_name: string;
  request_type: string;
  status: string;
  title?: string | null;
  reason?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  has_effect: boolean;
  effect_id?: number | null;
  effect_status?: string | null;
}

export interface AttendanceEffectGenerateResultDTO extends AttendanceEffectDTO {
  already_exists: boolean;
}

export interface AttendanceEffectGenerationCandidateParams {
  employee_id?: number;
  request_type?: string;
  start_date?: string;
  end_date?: string;
  include_existing?: boolean;
}

export interface AttendanceEffectListParams {
  status?: AttendanceEffectStatus;
  employee_id?: number;
  request_id?: number;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${base()}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    ...init,
  });
  if (!res.ok) {
    const detail = await formatApiErrorResponse(res);
    throw new Error(detail);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export async function listAttendanceEvents(params: {
  start_date: string;
  end_date: string;
  employee_id?: number;
}): Promise<AttendanceEventDTO[]> {
  const q = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
  });
  if (params.employee_id != null) {
    q.set("employee_id", String(params.employee_id));
  }
  return request<AttendanceEventDTO[]>(`/events?${q.toString()}`);
}

export async function createAttendanceEvent(
  payload: AttendanceEventPayload
): Promise<AttendanceEventDTO> {
  return request<AttendanceEventDTO>("/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateAttendanceEvent(
  id: number,
  payload: Partial<AttendanceEventPayload>
): Promise<AttendanceEventDTO> {
  return request<AttendanceEventDTO>(`/events/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteAttendanceEvent(id: number): Promise<void> {
  await request<void>(`/events/${id}`, { method: "DELETE" });
}

export async function getAttendanceSummary(
  year: number,
  month: number
): Promise<AttendanceMonthSummaryDTO> {
  const q = new URLSearchParams({
    year: String(year),
    month: String(month),
  });
  return request<AttendanceMonthSummaryDTO>(`/summary?${q.toString()}`);
}

export async function listAttendanceEffects(
  params: AttendanceEffectListParams = {},
): Promise<AttendanceEffectDTO[]> {
  const q = new URLSearchParams();
  if (params.status) q.set("status", params.status);
  if (params.employee_id != null) q.set("employee_id", String(params.employee_id));
  if (params.request_id != null) q.set("request_id", String(params.request_id));
  const suffix = q.toString() ? `?${q.toString()}` : "";
  return request<AttendanceEffectDTO[]>(`/effects${suffix}`);
}

export async function getAttendanceEffect(effectId: number): Promise<AttendanceEffectDTO> {
  return request<AttendanceEffectDTO>(`/effects/${effectId}`);
}

export async function applyAttendanceEffect(
  effectId: number,
): Promise<AttendanceEffectApplyResultDTO> {
  return request<AttendanceEffectApplyResultDTO>(`/effects/${effectId}/apply`, {
    method: "POST",
  });
}

export async function listAttendanceEffectGenerationCandidates(
  params: AttendanceEffectGenerationCandidateParams = {},
): Promise<AttendanceEffectGenerationCandidateDTO[]> {
  const q = new URLSearchParams();
  if (params.employee_id != null) q.set("employee_id", String(params.employee_id));
  if (params.request_type) q.set("request_type", params.request_type);
  if (params.start_date) q.set("start_date", params.start_date);
  if (params.end_date) q.set("end_date", params.end_date);
  if (params.include_existing) q.set("include_existing", "true");
  const suffix = q.toString() ? `?${q.toString()}` : "";
  return request<AttendanceEffectGenerationCandidateDTO[]>(`/effects/generation-candidates${suffix}`);
}

export async function generateAttendanceEffect(
  employeeRequestId: number,
): Promise<AttendanceEffectGenerateResultDTO> {
  return request<AttendanceEffectGenerateResultDTO>("/effects/generate", {
    method: "POST",
    body: JSON.stringify({ employee_request_id: employeeRequestId }),
  });
}

export const employeeAttendanceApi = {
  listEvents: listAttendanceEvents,
  createEvent: createAttendanceEvent,
  updateEvent: updateAttendanceEvent,
  deleteEvent: deleteAttendanceEvent,
  summary: getAttendanceSummary,
  listEffects: listAttendanceEffects,
  getEffect: getAttendanceEffect,
  applyEffect: applyAttendanceEffect,
  listGenerationCandidates: listAttendanceEffectGenerationCandidates,
  generateEffect: generateAttendanceEffect,
};
