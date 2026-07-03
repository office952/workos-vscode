/**
 * Inventory Deduction API client — BUILD 16: Inventory Operational Loop.
 *
 * Controlled stock deduction from ExecutionReality material consumption.
 * Read-only status + explicit deduction action + audit trail.
 *
 * Strict rules:
 *   - Deduction is NEVER automatic — requires explicit operator POST.
 *   - Free-text rows (no material_id) are observational only.
 *   - Duplicate deductions are idempotent (blocked by backend).
 *   - Insufficient stock blocks the specific row.
 */

import { getAPIBaseURL } from '../lib/config';

const getAPIBase = () => `${getAPIBaseURL()}/api/v1/inventory/deduction`;

// ---------------------------------------------------------------------------
// Types — mirror backend contract exactly.
// ---------------------------------------------------------------------------

export interface DeductionRowStatus {
  index: number;
  material_id?: number | null;
  material_name: string;
  quantity?: number | null;
  unit?: string | null;
  status: 'eligible' | 'not_linked' | 'already_deducted' | 'insufficient_stock' | 'material_not_found';
  current_stock?: number | null;
  message: string;
}

export interface DeductionStatusResponse {
  order_id: number;
  reality_exists: boolean;
  reality_id?: number;
  rows: DeductionRowStatus[];
  summary: {
    total: number;
    eligible: number;
    not_linked: number;
    already_deducted: number;
  };
}

export interface DeductionRowResult {
  material_index: number;
  status: 'deducted' | 'not_linked' | 'already_deducted' | 'insufficient_stock' | 'material_not_found' | 'invalid_quantity' | 'invalid_index';
  material_id?: number | null;
  material_name?: string | null;
  quantity?: number | null;
  unit?: string | null;
  old_stock?: number | null;
  new_stock?: number | null;
  message: string;
}

export interface DeductionResponse {
  order_id: number;
  reality_id: number;
  total_rows: number;
  deducted_count: number;
  skipped_count: number;
  blocked_count: number;
  rows: DeductionRowResult[];
}

export interface StockMovement {
  id: number;
  material_id: number;
  source_type: string;
  source_id: number;
  order_id: number | null;
  task_id: string | null;
  quantity: number;
  unit: string;
  movement_type: string;
  old_stock: number;
  new_stock: number;
  performed_by: string;
  performed_at: string | null;
  reason: string | null;
  idempotency_key?: string;
}

export interface MovementsResponse {
  order_id?: number;
  movements: StockMovement[];
  total: number;
}

// ---------------------------------------------------------------------------
// API methods
// ---------------------------------------------------------------------------

/**
 * Get deduction eligibility status for all material rows in an ExecutionReality.
 * Read-only — does not mutate anything.
 */
export async function getDeductionStatus(orderId: number): Promise<DeductionStatusResponse> {
  const res = await fetch(`${getAPIBase()}/status/${orderId}`, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail?.error || `Status check failed: ${res.status}`);
  }
  return res.json();
}

/**
 * Explicitly deduct linked materials from inventory.
 * Requires operator action — never automatic.
 */
export async function deductMaterials(
  orderId: number,
  options?: { reason?: string; material_indices?: number[] }
): Promise<DeductionResponse> {
  const res = await fetch(`${getAPIBase()}/deduct/${orderId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      reason: options?.reason || null,
      material_indices: options?.material_indices || null,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail?.error || `Deduction failed: ${res.status}`);
  }
  return res.json();
}

/**
 * Get all stock movements for a specific order (audit trail).
 */
export async function getMovementsForOrder(orderId: number): Promise<MovementsResponse> {
  const res = await fetch(`${getAPIBase()}/movements/${orderId}`, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch movements: ${res.status}`);
  }
  return res.json();
}

/**
 * Get recent stock movements across all orders (global audit trail).
 */
export async function getRecentMovements(limit: number = 50): Promise<MovementsResponse> {
  const res = await fetch(`${getAPIBase()}/movements/recent?limit=${limit}`, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch recent movements: ${res.status}`);
  }
  return res.json();
}