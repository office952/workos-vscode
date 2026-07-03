/**
 * Admin API client for Workcenter Rates registry.
 *
 * Consumes:
 *   GET    /api/admin/workcenter-rates
 *   GET    /api/admin/workcenter-rates/{code}
 *   PATCH  /api/admin/workcenter-rates/{code}
 */
import { getAPIBaseURL } from "../lib/config";

const base = () => `${getAPIBaseURL()}/api/admin/workcenter-rates`;

export interface WorkcenterRateDTO {
  id: number;
  code: string;
  label: string;
  rate_per_hour?: number | null;
  rate_per_linear_meter?: number | null;
  rate_basis: string;
  currency: string;
  status: string;
  is_active: boolean;
  approval_reference?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface WorkcenterRatePatchPayload {
  rate_per_hour?: number | null;
  rate_per_linear_meter?: number | null;
  rate_basis?: string;
  status?: string;
  is_active?: boolean;
  approval_reference?: string | null;
  label?: string;
  notes?: string | null;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      const candidate = body?.detail ?? body?.message;
      if (typeof candidate === "string") {
        detail = candidate;
      } else if (candidate != null) {
        detail = JSON.stringify(candidate);
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(`HTTP ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const workcenterRatesAdminApi = {
  async list(): Promise<WorkcenterRateDTO[]> {
    const res = await fetch(base(), { credentials: "include" });
    return handleResponse<WorkcenterRateDTO[]>(res);
  },

  async get(code: string): Promise<WorkcenterRateDTO> {
    const res = await fetch(`${base()}/${encodeURIComponent(code)}`, {
      credentials: "include",
    });
    return handleResponse<WorkcenterRateDTO>(res);
  },

  async patch(
    code: string,
    payload: WorkcenterRatePatchPayload
  ): Promise<WorkcenterRateDTO> {
    const res = await fetch(`${base()}/${encodeURIComponent(code)}`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse<WorkcenterRateDTO>(res);
  },
};
