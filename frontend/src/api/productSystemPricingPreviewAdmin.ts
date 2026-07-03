import { getAPIBaseURL } from '../lib/config';

const base = () => `${getAPIBaseURL()}/api/admin/productsystem`;

export interface PricingPreviewWarning {
  code: string;
  message: string;
}

export interface PricingPreviewAppliedPolicy {
  policy_id: number;
  scope_type: string;
  scope_value: string;
  markup_type: string;
  markup_percent?: number | null;
  markup_fixed?: number | null;
  priority: number;
  currency?: string | null;
  rounding_mode?: string | null;
  applies_to?: string | null;
  status?: string | null;
}

export interface ProductSystemPricingPreviewRequest {
  material_code: string;
  quantity?: number;
  vat_percent?: number | null;
  include_vat?: boolean;
  requested_scope?: string | null;
  notes?: string | null;
}

export interface ProductSystemPricingPreviewResult {
  material_code: string;
  material_name?: string | null;
  material_status?: string | null;
  quantity: number;
  unit?: string | null;
  currency?: string | null;
  unit_cost?: number | null;
  base_cost_total?: number | null;
  applied_markup_policy?: PricingPreviewAppliedPolicy | null;
  markup_amount?: number | null;
  commercial_unit_price_ex_vat?: number | null;
  commercial_total_ex_vat?: number | null;
  vat_percent?: number | null;
  vat_amount?: number | null;
  commercial_total_inc_vat?: number | null;
  warnings: PricingPreviewWarning[];
  blockers: PricingPreviewWarning[];
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

export const productSystemPricingPreviewAdminApi = {
  async runProductSystemPricingPreview(
    payload: ProductSystemPricingPreviewRequest,
  ): Promise<ProductSystemPricingPreviewResult> {
    const res = await fetch(`${base()}/pricing-preview`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<ProductSystemPricingPreviewResult>(res);
  },
};