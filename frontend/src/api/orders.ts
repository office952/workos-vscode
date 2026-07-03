/**
 * Orders API Integration
 * 
 * Provides TypeScript interfaces and functions for interacting with the backend Orders API.
 * Includes:
 * - Order readiness snapshot visibility
 * - Order creation from quotes
 * - Order status and snapshot immutability
 */

import type { OrderEntity } from '@/lib/api';

const API_BASE = '/api/v1/entities';

/**
 * Fetch a single order by ID
 * Includes readiness_snapshot if available
 */
export async function getOrderById(orderId: number): Promise<OrderEntity> {
  const response = await fetch(`${API_BASE}/orders/${orderId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch order ${orderId}: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch all orders
 * Each order includes readiness_snapshot if available
 */
export async function listOrders(): Promise<OrderEntity[]> {
  const response = await fetch(`${API_BASE}/orders`);
  if (!response.ok) {
    throw new Error(`Failed to fetch orders: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Create an order from a priced quote
 * Snapshots the product readiness state at order acceptance time
 * 
 * @param quoteId - ID of the priced quote to convert
 * @param acknowledgeReadinessWarnings - Whether to acknowledge any readiness warnings (default: false)
 * @param readinessWarningAcknowledgementReason - Optional reason for acknowledging warnings
 */
export async function createOrderFromQuote(
  quoteId: number,
  acknowledgeReadinessWarnings: boolean = false,
  readinessWarningAcknowledgementReason?: string
): Promise<OrderEntity> {
  const response = await fetch(`${API_BASE}/orders/from-quote/${quoteId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      acknowledge_readiness_warnings: acknowledgeReadinessWarnings,
      readiness_warning_acknowledgement_reason: readinessWarningAcknowledgementReason || null,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(`Failed to create order: ${error.error || response.statusText}`);
  }
  return response.json();
}

/**
 * Get order readiness snapshot details
 * Returns null if order was created without a readiness snapshot
 */
export function getReadinessSnapshot(order: OrderEntity) {
  return order.readiness_snapshot || null;
}

/**
 * Check if order has a readiness snapshot
 */
export function hasReadinessSnapshot(order: OrderEntity): boolean {
  return order.readiness_snapshot !== null && order.readiness_snapshot !== undefined;
}

// ---------------------------------------------------------------------------
// BUILD 12: Document Snapshot Reference + Quote Acceptance Guard
// ---------------------------------------------------------------------------

/**
 * Document snapshot reference for an order
 */
export interface OrderDocumentSnapshotReference {
  id: number;
  order_id: number;
  quote_id: number;
  quote_output_snapshot_id: number;
  snapshot_code: string | null;
  snapshot_status_at_acceptance: string;
  snapshot_version: number | null;
  snapshot_content_hash: string | null;
  source_template_id: number | null;
  source_template_code: string | null;
  source_dossier_id: number | null;
  source_dossier_version: number | null;
  source_trace_json: Record<string, unknown> | null;
  governance_status_at_acceptance: string;
  accepted_at: string | null;
  accepted_by: string | null;
  created_at: string | null;
  notes: string | null;
}

export interface OrderDocumentSnapshotReferenceResponse {
  order_id: number;
  has_document_snapshot: boolean;
  reference: OrderDocumentSnapshotReference | null;
}

/**
 * Quote acceptance guard result
 */
export interface QuoteAcceptanceGuardItem {
  guard: string;
  status: 'eligible' | 'blocked' | 'warning' | 'info';
  detail: string;
  snapshot_id?: number;
  requires_acknowledgement?: boolean;
  blockers?: Array<Record<string, unknown>>;
  warnings?: Array<Record<string, unknown>>;
  required_status?: string[];
}

export interface QuoteAcceptanceGuardResponse {
  quote_id: number;
  overall_status: 'eligible' | 'blocked' | 'needs_acknowledgement';
  guards: QuoteAcceptanceGuardItem[];
}

/**
 * Get document snapshot reference for an order
 */
export async function getOrderDocumentSnapshotReference(
  orderId: number
): Promise<OrderDocumentSnapshotReferenceResponse> {
  const response = await fetch(`${API_BASE}/orders/${orderId}/document-snapshot-reference`);
  if (!response.ok) {
    throw new Error(`Failed to fetch document snapshot reference: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Evaluate quote acceptance guard (readiness + document snapshot eligibility)
 * Non-blocking: always returns 200 with status info.
 */
export async function getQuoteAcceptanceGuard(
  quoteId: number
): Promise<QuoteAcceptanceGuardResponse> {
  const response = await fetch(`${API_BASE}/orders/quote-acceptance-guard/${quoteId}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Quote not found');
    }
    throw new Error(`Failed to evaluate quote acceptance guard: ${response.statusText}`);
  }
  return response.json();
}
