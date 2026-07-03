/**
 * Manager/admin employee request review — status-only, no side-effect flags.
 */
import { throwEmployeeRequestApiError } from "@/api/employeeRequestErrors";
import type { EmployeeRequestStatus, EmployeeRequestType } from "@/api/employeeMobileRequests";
import { getAPIBaseURL } from "@/lib/config";

const base = () => `${getAPIBaseURL()}/api/v1/employee-requests/review`;

export interface EmployeeRequestReviewDTO {
  id: number;
  employee_id: number;
  request_type: EmployeeRequestType;
  status: EmployeeRequestStatus;
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

export interface EmployeeRequestReviewActionPayload {
  review_note?: string;
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
    await throwEmployeeRequestApiError(res, "review");
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export async function listEmployeeRequestsForReview(): Promise<EmployeeRequestReviewDTO[]> {
  return request<EmployeeRequestReviewDTO[]>("");
}

export async function getEmployeeRequestForReview(
  id: number,
): Promise<EmployeeRequestReviewDTO> {
  return request<EmployeeRequestReviewDTO>(`/${id}`);
}

export async function approveEmployeeRequest(
  id: number,
  reviewNote?: string,
): Promise<EmployeeRequestReviewDTO> {
  const payload: EmployeeRequestReviewActionPayload = {};
  if (reviewNote?.trim()) {
    payload.review_note = reviewNote.trim();
  }
  return request<EmployeeRequestReviewDTO>(`/${id}/approve`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function rejectEmployeeRequest(
  id: number,
  reviewNote?: string,
): Promise<EmployeeRequestReviewDTO> {
  const payload: EmployeeRequestReviewActionPayload = {};
  if (reviewNote?.trim()) {
    payload.review_note = reviewNote.trim();
  }
  return request<EmployeeRequestReviewDTO>(`/${id}/reject`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export const employeeRequestReviewApi = {
  list: listEmployeeRequestsForReview,
  get: getEmployeeRequestForReview,
  approve: approveEmployeeRequest,
  reject: rejectEmployeeRequest,
};
