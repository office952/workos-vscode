/**
 * Admin API client for the Inventory Materials registry.
 *
 * Consumes real backend endpoints:
 *   GET    /api/admin/inventory-materials
 *   GET    /api/admin/inventory-materials/{code}
 *   GET    /api/admin/inventory-materials/{code}/price-history
 *   PATCH  /api/admin/inventory-materials/{code}
 *
 * Rules:
 *   - No mock data.
 *   - No cost computation in the UI.
 *   - unit_cost = acquisition/production cost only. NOT commercial price.
 *   - Source metadata is verification reference, not price truth.
 */
import { getAPIBaseURL } from '../lib/config';

const base = () => `${getAPIBaseURL()}/api/admin/inventory-materials`;

// ── Types ─────────────────────────────────────────────────────────────────────

export interface InventoryMaterialDTO {
  id: number;
  code: string;
  name: string;
  category?: string | null;
  subcategory?: string | null;
  unit: string;
  stock_current?: number | null;
  stock_min?: number | null;
  stock_max?: number | null;
  unit_cost?: number | null;
  currency?: string | null;
  vat_percent?: number | null;
  valid_from?: string | null;
  supplier?: string | null;
  supplier_id?: number | null;
  source_name?: string | null;
  source_url?: string | null;
  source_checked_at?: string | null;
  source_notes?: string | null;
  source_review_status?: string | null;
  source_reviewed_at?: string | null;
  source_reviewed_by?: string | null;
  status?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PriceHistoryEntryDTO {
  id: number;
  material_id?: number | null;
  material_code?: string | null;
  unit_cost?: number | null;
  currency?: string | null;
  vat_percent?: number | null;
  valid_from?: string | null;
  old_unit_cost?: number | null;
  new_unit_cost?: number | null;
  old_currency?: string | null;
  new_currency?: string | null;
  old_vat_percent?: number | null;
  new_vat_percent?: number | null;
  old_valid_from?: string | null;
  new_valid_from?: string | null;
  old_supplier?: string | null;
  new_supplier?: string | null;
  change_reason?: string | null;
  changed_by?: string | null;
  changed_at?: string | null;
  created_at?: string | null;
  snapshot_source?: string | null;
}

export interface SourceReviewAuditEntryDTO {
  id: number;
  material_id?: number | null;
  material_code?: string | null;
  old_status?: string | null;
  new_status?: string | null;
  old_source_checked_at?: string | null;
  new_source_checked_at?: string | null;
  old_source_url?: string | null;
  new_source_url?: string | null;
  old_source_name?: string | null;
  new_source_name?: string | null;
  old_source_notes?: string | null;
  new_source_notes?: string | null;
  reason?: string | null;
  actor?: string | null;
  created_at?: string | null;
}

export interface CategoryCleanupPreviewEntryDTO {
  material_id: number;
  code: string;
  name: string;
  current_category?: string | null;
  suggested_category?: string | null;
  current_subcategory?: string | null;
  suggested_subcategory?: string | null;
  issue_type?: string | null;
  issues?: string[];
  reason?: string | null;
  would_change?: boolean;
  safe_to_apply?: boolean;
  product_system_blocked?: boolean;
  product_system_reasons?: string[];
}

export interface InventoryMaterialPatchPayload {
  unit_cost?: number | null;
  currency?: string | null;
  vat_percent?: number | null;
  valid_from?: string | null;
  status?: string | null;
  supplier?: string | null;
  supplier_id?: number | null;
  source_name?: string | null;
  source_url?: string | null;
  source_checked_at?: string | null;
  source_notes?: string | null;
  source_review_status?: string | null;
  source_reviewed_at?: string | null;
  source_reviewed_by?: string | null;
  name?: string | null;
  subcategory?: string | null;
  change_reason?: string | null;
  snapshot_source?: string;
}

export interface InventoryMaterialsPolicyDTO {
  canonical_categories: string[];
  recommended_subcategories: Record<string, string[]>;
  required_pricing_fields: string[];
  price_governed_fields: string[];
  source_review_policy: {
    statuses: string[];
    accepted_override_requires_notes: boolean;
  };
  product_system_gate_rules: {
    requires_ready_for_pricing: boolean;
    requires_active_status: boolean;
    rejects_archived: boolean;
    requires_category_normalized: boolean;
    requires_unit: boolean;
    requires_source_review_ok: boolean;
    informational_only: boolean;
  };
  stale_source_days: number;
  warnings: string[];
  category_policy: {
    accepted: string[];
    recommended_subcategories: Record<string, string[]>;
  };
  source_review: {
    stale_after_days: number;
    override_token: string;
  };
  productsystem_gate: {
    informational_only: boolean;
    activates_product_001: boolean;
    connects_cost_engine: boolean;
  };
}

// ── Helpers ───────────────────────────────────────────────────────────────────

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

// ── API ───────────────────────────────────────────────────────────────────────

export const inventoryMaterialsAdminApi = {
  async policy(): Promise<InventoryMaterialsPolicyDTO> {
    const res = await fetch(`${base()}/policy`, { credentials: 'include' });
    return handleResponse<InventoryMaterialsPolicyDTO>(res);
  },

  async list(statusFilter?: string): Promise<InventoryMaterialDTO[]> {
    const qs = statusFilter && statusFilter !== 'all' ? `?status=${encodeURIComponent(statusFilter)}` : '';
    const res = await fetch(`${base()}${qs}`, { credentials: 'include' });
    return handleResponse<InventoryMaterialDTO[]>(res);
  },

  async get(code: string): Promise<InventoryMaterialDTO> {
    const res = await fetch(`${base()}/${encodeURIComponent(code)}`, {
      credentials: 'include',
    });
    return handleResponse<InventoryMaterialDTO>(res);
  },

  async priceHistory(code: string, limit = 50): Promise<PriceHistoryEntryDTO[]> {
    const res = await fetch(
      `${base()}/${encodeURIComponent(code)}/price-history?limit=${limit}`,
      { credentials: 'include' },
    );
    return handleResponse<PriceHistoryEntryDTO[]>(res);
  },

  async sourceReviewAudit(code: string, limit = 100): Promise<SourceReviewAuditEntryDTO[]> {
    const res = await fetch(
      `${base()}/${encodeURIComponent(code)}/source-review-audit?limit=${limit}`,
      { credentials: 'include' },
    );
    return handleResponse<SourceReviewAuditEntryDTO[]>(res);
  },

  async categoryCleanupPreview(limit = 500): Promise<CategoryCleanupPreviewEntryDTO[]> {
    const res = await fetch(
      `${base()}/category-cleanup/preview?limit=${limit}`,
      { credentials: 'include' },
    );
    return handleResponse<CategoryCleanupPreviewEntryDTO[]>(res);
  },

  async patch(
    code: string,
    payload: InventoryMaterialPatchPayload,
  ): Promise<InventoryMaterialDTO> {
    const res = await fetch(`${base()}/${encodeURIComponent(code)}`, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<InventoryMaterialDTO>(res);
  },
};
