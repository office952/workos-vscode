import { getAPIBaseURL } from '../lib/config';

const base = () => `${getAPIBaseURL()}/api/admin/commercial-markup-policies`;

export interface CommercialMarkupPolicy {
  id: number;
  scope_type: 'global' | 'category' | 'subcategory' | 'material';
  scope_value: string;
  markup_type: 'percent' | 'fixed' | 'hybrid';
  markup_percent?: number | null;
  markup_fixed?: number | null;
  currency?: string | null;
  min_margin_amount?: number | null;
  rounding_mode: 'none' | 'nearest_0_10' | 'nearest_0_50' | 'nearest_1' | 'nearest_5';
  applies_to: 'material_cost' | 'production_cost' | 'composite_cost';
  status: 'draft' | 'active' | 'archived';
  priority: number;
  notes?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CommercialMarkupPolicyConfig {
  scope_types: string[];
  markup_types: string[];
  rounding_modes: string[];
  applies_to: string[];
  statuses: string[];
  conflict_resolution: string;
  separation_notice: string;
  no_write_notice: string;
}

export interface MarkupWarning {
  code: string;
  message: string;
}

export interface AppliedPolicy {
  id: number;
  scope_type: string;
  scope_value: string;
  markup_type: string;
  markup_percent?: number | null;
  markup_fixed?: number | null;
  currency?: string | null;
  rounding_mode: string;
  applies_to: string;
  priority: number;
  status: string;
}

export interface CommercialMarkupDryRunRequest {
  material_code: string;
  quantity?: number;
}

export interface CommercialMarkupDryRunResult {
  material_code: string;
  material_name?: string;
  quantity: number;
  unit_cost?: number | null;
  currency?: string | null;
  vat_percent?: number | null;
  vat_mode: 'excluded' | 'included';
  base_cost_total?: number | null;
  applied_policy?: AppliedPolicy | null;
  markup_amount?: number | null;
  commercial_unit_price?: number | null;
  commercial_total_price?: number | null;
  warnings: MarkupWarning[];
  no_write_guarantee: boolean;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      const candidate = body?.detail ?? body?.message;
      if (typeof candidate === 'string') {
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

export const commercialMarkupPoliciesAdminApi = {
  async list(status?: string): Promise<CommercialMarkupPolicy[]> {
    const qs = status ? `?status=${encodeURIComponent(status)}` : '';
    const res = await fetch(`${base()}${qs}`, { credentials: 'include' });
    return handleResponse<CommercialMarkupPolicy[]>(res);
  },

  async config(): Promise<CommercialMarkupPolicyConfig> {
    const res = await fetch(`${base()}/config`, { credentials: 'include' });
    return handleResponse<CommercialMarkupPolicyConfig>(res);
  },

  async dryRun(payload: CommercialMarkupDryRunRequest): Promise<CommercialMarkupDryRunResult> {
    const res = await fetch(`${base()}/dry-run`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<CommercialMarkupDryRunResult>(res);
  },
};