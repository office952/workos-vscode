/**
 * Employee-mobile self-only requests — no client employee_id authority.
 */
import { throwEmployeeRequestApiError } from "@/api/employeeRequestErrors";
import { getAPIBaseURL } from "@/lib/config";

const base = () => `${getAPIBaseURL()}/api/v1/employee-mobile/requests`;

export const EMPLOYEE_REQUEST_TYPES = [
  "leave",
  "day_off",
  "time_off",
  "advance",
  "attendance_correction",
  "equipment",
  "issue_report",
  "other",
] as const;

export type EmployeeRequestType = (typeof EMPLOYEE_REQUEST_TYPES)[number];

export type EmployeeRequestStatus =
  | "draft"
  | "submitted"
  | "approved"
  | "rejected"
  | "cancelled";

export const CANCELLABLE_REQUEST_STATUSES: EmployeeRequestStatus[] = ["draft", "submitted"];

export interface EmployeeRequestDTO {
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
}

/** Create payload — never includes employee_id, status, or review fields. */
export interface EmployeeRequestCreatePayload {
  request_type: EmployeeRequestType;
  title?: string;
  description?: string;
  reason?: string;
  start_date?: string;
  end_date?: string;
  amount?: number;
  currency?: string;
}

export type EmployeeRequestFormState = {
  request_type: EmployeeRequestType;
  title: string;
  description: string;
  reason: string;
  start_date: string;
  end_date: string;
  amount: string;
  currency: string;
};

export const EMPTY_EMPLOYEE_REQUEST_FORM: EmployeeRequestFormState = {
  request_type: "leave",
  title: "",
  description: "",
  reason: "",
  start_date: "",
  end_date: "",
  amount: "",
  currency: "RON",
};

export function buildEmployeeRequestCreatePayload(
  form: EmployeeRequestFormState,
): EmployeeRequestCreatePayload {
  const payload: EmployeeRequestCreatePayload = {
    request_type: form.request_type,
    title: form.title.trim(),
  };

  const description = form.description.trim();
  if (description) payload.description = description;

  const reason = form.reason.trim();
  if (reason) payload.reason = reason;

  if (form.start_date) payload.start_date = form.start_date;
  if (form.end_date) payload.end_date = form.end_date;

  if (form.request_type === "advance") {
    const amount = Number(form.amount);
    if (Number.isFinite(amount) && amount > 0) {
      payload.amount = amount;
      payload.currency = form.currency.trim() || "RON";
    }
  }

  return payload;
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
    await throwEmployeeRequestApiError(res, "self");
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export async function listEmployeeRequests(): Promise<EmployeeRequestDTO[]> {
  return request<EmployeeRequestDTO[]>("");
}

export async function createEmployeeRequest(
  payload: EmployeeRequestCreatePayload,
): Promise<EmployeeRequestDTO> {
  return request<EmployeeRequestDTO>("", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function cancelEmployeeRequest(id: number): Promise<EmployeeRequestDTO> {
  return request<EmployeeRequestDTO>(`/${id}/cancel`, {
    method: "PATCH",
  });
}

export const employeeMobileRequestsApi = {
  list: listEmployeeRequests,
  create: createEmployeeRequest,
  cancel: cancelEmployeeRequest,
};
