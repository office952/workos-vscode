/**
 * CostEngine + Employees + Recurring Payments API wrappers.
 *
 * These consume the real backend REST endpoints (FastAPI) at
 *   /api/v1/entities/employees
 *   /api/v1/entities/recurring-payments
 *   /api/v1/cost-engine/config
 *   /api/v1/cost-engine/base-config
 *
 * Frontend does NOT compute costs. It only reads/writes canonical data.
 * All derived fields (cost_ora_calculat, valid_for_cost_engine,
 * average_labour_hour_cost, overhead_hour_cost, ...) come from the backend.
 */
import { getAPIBaseURL } from '../lib/config';
import { formatApiErrorResponse } from '../lib/apiError';

const apiBase = () => `${getAPIBaseURL()}/api/v1`;

// ============================================================
// Types (mirror backend Pydantic responses — no extra logic)
// ============================================================
export interface EmployeeDTO {
  id: number;
  name: string;
  role?: string | null;
  department?: string | null;
  status: string;
  employee_type: string;
  user_id?: string | null;
  auth_email?: string | null;
  auth_role?: string | null;
  is_linked_to_user?: boolean;
  has_mobile_access?: boolean;
  cost_lunar_firma?: number | null;
  monthly_internal_pay_amount?: number | null;
  ore_lucru_luna?: number | null;
  ore_productive_luna?: number | null;
  cost_ora_calculat?: number | null;
  valid_for_cost_engine: boolean;
  skills?: string[] | null;
  machines?: string[] | null;
  data_angajare?: string | null;
  observatii?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface EmployeeListDTO {
  items: EmployeeDTO[];
  total: number;
  skip: number;
  limit: number;
}

export interface EmployeePayload {
  name: string;
  role?: string | null;
  department?: string | null;
  status?: string | null;
  employee_type?: string | null;
  cost_lunar_firma?: number | null;
  monthly_internal_pay_amount?: number | null;
  ore_lucru_luna?: number | null;
  ore_productive_luna?: number | null;
  skills?: string[] | null;
  machines?: string[] | null;
  data_angajare?: string | null;
  observatii?: string | null;
}

export interface RecurringPaymentDTO {
  id: number;
  name: string;
  category: string;
  amount?: number | null;
  currency: string;
  periodicity: string;
  supplier?: string | null;
  due_day?: number | null;
  status: string;
  include_in_overhead: boolean;
  include_in_machine_cost: boolean;
  linked_machine_id?: string | null;
  observatii?: string | null;
  monthly_equivalent?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface RecurringPaymentListDTO {
  items: RecurringPaymentDTO[];
  total: number;
  skip: number;
  limit: number;
}

export interface RecurringPaymentPayload {
  name: string;
  category?: string;
  amount?: number | null;
  currency?: string;
  periodicity?: string;
  supplier?: string | null;
  due_day?: number | null;
  status?: string;
  include_in_overhead?: boolean;
  include_in_machine_cost?: boolean;
  linked_machine_id?: string | null;
  observatii?: string | null;
}

export interface CostEngineConfigDTO {
  id: number;
  moneda_implicita: string;
  ore_productive_luna_firma?: number | null;
  overhead_profile_name: string;
  metoda_overhead: string;
  cost_ora_manopera_default?: number | null;
  allow_manual_override: boolean;
}

export interface CostEngineConfigPayload {
  moneda_implicita?: string;
  ore_productive_luna_firma?: number | null;
  overhead_profile_name?: string;
  metoda_overhead?: string;
  cost_ora_manopera_default?: number | null;
  allow_manual_override?: boolean;
}

export interface CostEngineBaseConfigDTO {
  currency: string;
  total_productive_hours_month: number;
  average_labour_hour_cost: number;
  monthly_overhead_cost: number;
  overhead_hour_cost: number;
  valid: boolean;
  warnings: string[];
  overhead_profile_name?: string | null;
  metoda_overhead?: string | null;
  cost_ora_manopera_default?: number | null;
  allow_manual_override?: boolean | null;
}

// ============================================================
// Low-level fetch helper
// ============================================================
async function request<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers ?? {}),
    },
    ...init,
  });
  if (!res.ok) {
    const detail = await formatApiErrorResponse(res);
    throw new Error(detail);
  }
  if (res.status === 204) {
    return undefined as unknown as T;
  }
  return (await res.json()) as T;
}

// ============================================================
// Employees API
// ============================================================
export const employeesApi = {
  list: (opts: { skip?: number; limit?: number; sort?: string } = {}) => {
    const params = new URLSearchParams();
    if (opts.skip !== undefined) params.set('skip', String(opts.skip));
    if (opts.limit !== undefined) params.set('limit', String(opts.limit));
    if (opts.sort) params.set('sort', opts.sort);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request<EmployeeListDTO>(`/entities/employees${qs}`);
  },
  get: (id: number) => request<EmployeeDTO>(`/entities/employees/${id}`),
  create: (data: EmployeePayload) =>
    request<EmployeeDTO>(`/entities/employees`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<EmployeePayload>) =>
    request<EmployeeDTO>(`/entities/employees/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  remove: (id: number) =>
    request<{ message: string; id: number }>(`/entities/employees/${id}`, {
      method: 'DELETE',
    }),
};

// ============================================================
// Recurring payments API
// ============================================================
export const recurringPaymentsApi = {
  list: (opts: { skip?: number; limit?: number; sort?: string } = {}) => {
    const params = new URLSearchParams();
    if (opts.skip !== undefined) params.set('skip', String(opts.skip));
    if (opts.limit !== undefined) params.set('limit', String(opts.limit));
    if (opts.sort) params.set('sort', opts.sort);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request<RecurringPaymentListDTO>(`/entities/recurring-payments${qs}`);
  },
  get: (id: number) =>
    request<RecurringPaymentDTO>(`/entities/recurring-payments/${id}`),
  create: (data: RecurringPaymentPayload) =>
    request<RecurringPaymentDTO>(`/entities/recurring-payments`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<RecurringPaymentPayload>) =>
    request<RecurringPaymentDTO>(`/entities/recurring-payments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  remove: (id: number) =>
    request<{ message: string; id: number }>(
      `/entities/recurring-payments/${id}`,
      { method: 'DELETE' }
    ),
};

// ============================================================
// CostEngine config API
// ============================================================
export const costEngineApi = {
  getConfig: () => request<CostEngineConfigDTO>(`/cost-engine/config`),
  updateConfig: (data: CostEngineConfigPayload) =>
    request<CostEngineConfigDTO>(`/cost-engine/config`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  getBaseConfig: () =>
    request<CostEngineBaseConfigDTO>(`/cost-engine/base-config`),
};