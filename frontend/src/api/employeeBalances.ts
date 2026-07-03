/**
 * Internal employee balance ledger API — advances, loans, retentions.
 */
import { getAPIBaseURL } from "@/lib/config";

const base = () => `${getAPIBaseURL()}/api/v1/employee-balances`;

export type BalanceTransactionType =
  | "advance"
  | "loan"
  | "retention"
  | "repayment"
  | "compensation"
  | "adjustment";

export type BalanceTransactionStatus = "active" | "settled" | "cancelled";

export interface BalanceTransactionDTO {
  id: number;
  employee_id: number;
  transaction_date: string;
  transaction_type: BalanceTransactionType;
  amount: number;
  currency: string;
  status: BalanceTransactionStatus;
  notes?: string | null;
  source: string;
  created_at?: string | null;
  updated_at?: string | null;
  employee_name?: string | null;
  signed_amount: number;
}

export interface BalanceTransactionPayload {
  employee_id: number;
  transaction_date: string;
  transaction_type: BalanceTransactionType;
  amount: number;
  currency?: string;
  status?: BalanceTransactionStatus;
  notes?: string | null;
  source?: string;
}

export interface BalanceEmployeeSummaryDTO {
  employee_id: number;
  employee_name: string;
  active_balance: number;
  advance_total: number;
  loan_total: number;
  retention_total: number;
  repayment_total: number;
  compensation_total: number;
  transaction_count: number;
}

export interface BalanceTotalsDTO {
  active_balance: number;
  advance_total: number;
  loan_total: number;
  retention_total: number;
  repayment_total: number;
  compensation_total: number;
  transaction_count: number;
}

export interface BalanceSummaryDTO {
  currency: string;
  totals: BalanceTotalsDTO;
  employees: BalanceEmployeeSummaryDTO[];
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
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
      if (typeof detail !== "string") detail = JSON.stringify(detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const employeeBalancesApi = {
  summary: () => request<BalanceSummaryDTO>("/summary"),

  listTransactions: (params?: {
    employee_id?: number;
    status?: BalanceTransactionStatus;
    transaction_type?: BalanceTransactionType;
    start_date?: string;
    end_date?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.employee_id != null) q.set("employee_id", String(params.employee_id));
    if (params?.status) q.set("status", params.status);
    if (params?.transaction_type) q.set("transaction_type", params.transaction_type);
    if (params?.start_date) q.set("start_date", params.start_date);
    if (params?.end_date) q.set("end_date", params.end_date);
    const qs = q.toString();
    return request<BalanceTransactionDTO[]>(`/transactions${qs ? `?${qs}` : ""}`);
  },

  createTransaction: (payload: BalanceTransactionPayload) =>
    request<BalanceTransactionDTO>("/transactions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateTransaction: (id: number, payload: Partial<BalanceTransactionPayload>) =>
    request<BalanceTransactionDTO>(`/transactions/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  cancelTransaction: (id: number) =>
    request<BalanceTransactionDTO>(`/transactions/${id}/cancel`, { method: "POST" }),
};
