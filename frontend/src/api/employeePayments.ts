/**
 * Employee internal payments API — situation read + payment recording.
 */
import { getAPIBaseURL } from "@/lib/config";

const base = () => `${getAPIBaseURL()}/api/v1/employee-payments`;

export type PaymentSlotKey = "15" | "30";
export type ApiPaymentStatus = "unpaid" | "partial" | "paid" | "missing_base";

export interface PaymentBreakdownDTO {
  base_amount: number;
  attendance_adjustment: number;
  overtime_amount: number;
  advances_debts_deduction: number;
  existing_payments: number;
  suggested_deduction?: number;
}

export interface PaymentHistoryItemDTO {
  id: number;
  amount_paid: number;
  payment_date: string;
  status: string;
  notes?: string | null;
  created_at?: string | null;
  cancelled?: boolean;
}

export interface PaymentSlotSituationDTO {
  slot: string;
  period_start: string;
  period_end: string;
  expected_amount: number;
  paid_amount: number;
  remaining_amount: number;
  status: ApiPaymentStatus;
  breakdown: PaymentBreakdownDTO;
  warnings: string[];
  history: PaymentHistoryItemDTO[];
}

export interface EmployeePaymentEmployeeDTO {
  employee_id: number;
  employee_name: string;
  salary_monthly: number | null;
  salary_amount: number | null;
  monthly_internal_pay_amount?: number | null;
  currency: string;
  base_source: string;
  warnings: string[];
  attendance_label: string;
  advances_debts_label: string;
  monthly_expected_amount: number;
  monthly_paid_amount: number;
  monthly_remaining_amount: number;
  missing_pay_base: boolean;
  slots: Record<PaymentSlotKey, PaymentSlotSituationDTO>;
}

export interface PaymentSituationSummaryDTO {
  expected_total: number;
  paid_total: number;
  remaining_total: number;
  unpaid_count: number;
  partial_count: number;
  paid_count: number;
}

export interface PaymentSituationDTO {
  year: number;
  month: number;
  currency: string;
  summary: PaymentSituationSummaryDTO;
  employees: EmployeePaymentEmployeeDTO[];
}

export interface PaymentRecordCreatePayload {
  employee_id: number;
  year: number;
  month: number;
  slot: PaymentSlotKey;
  amount_paid: number;
  payment_date: string;
  notes?: string;
}

export interface PaymentRecordDTO {
  id: number;
  employee_id: number;
  employee_name?: string | null;
  year: number;
  month: number;
  slot: string;
  amount_paid: number;
  payment_date: string;
  status: string;
  notes?: string | null;
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
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const employeePaymentsApi = {
  getSituation(year: number, month: number): Promise<PaymentSituationDTO> {
    return request<PaymentSituationDTO>(`/situation?year=${year}&month=${month}`);
  },

  createPayment(payload: PaymentRecordCreatePayload): Promise<PaymentRecordDTO> {
    return request<PaymentRecordDTO>("", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  cancelPayment(recordId: number, reason?: string): Promise<PaymentRecordDTO> {
    return request<PaymentRecordDTO>(`/${recordId}/cancel`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  },
};
