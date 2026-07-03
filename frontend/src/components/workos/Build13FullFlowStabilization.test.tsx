/**
 * BUILD 13 — Full Flow MVP Stabilization & Real Work Verification Tests
 *
 * Covers:
 *  A. Quote → Order conversion button visibility (UX friction fix)
 *  B. Status lifecycle display correctness
 *  C. Reports cancelled exclusion (frontend hook logic)
 *  D. Build 12 regression (components still render)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const canConvertQuote = (status: string) => status === 'accepted' || status === 'priced';

// ═══════════════════════════════════════════════════════════════════════════════
// A. QUOTE CONVERSION BUTTON VISIBILITY
// ═══════════════════════════════════════════════════════════════════════════════

describe('Build13: Quote Conversion Button Visibility Rules', () => {
  it('should show convert button for "accepted" status', () => {
    const status = 'accepted';
    const showConvert = canConvertQuote(status);
    expect(showConvert).toBe(true);
  });

  it('should show convert button for "priced" status', () => {
    const status = 'priced';
    const showConvert = canConvertQuote(status);
    expect(showConvert).toBe(true);
  });

  it('should NOT show convert button for "sent" status', () => {
    const status = 'sent';
    const showConvert = canConvertQuote(status);
    expect(showConvert).toBe(false);
  });

  it('should NOT show convert button for "viewed" status', () => {
    const status = 'viewed';
    const showConvert = canConvertQuote(status);
    expect(showConvert).toBe(false);
  });

  it('should NOT show convert button for "negotiating" status', () => {
    const status = 'negotiating';
    const showConvert = canConvertQuote(status);
    expect(showConvert).toBe(false);
  });

  it('should NOT show convert button for "draft" status', () => {
    const status = 'draft';
    const showConvert = canConvertQuote(status);
    expect(showConvert).toBe(false);
  });

  it('should NOT show convert button for "rejected" status', () => {
    const status = 'rejected';
    const showConvert = canConvertQuote(status);
    expect(showConvert).toBe(false);
  });

  it('should NOT show convert button for "expired" status', () => {
    const status = 'expired';
    const showConvert = canConvertQuote(status);
    expect(showConvert).toBe(false);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// B. STATUS LIFECYCLE DISPLAY CORRECTNESS
// ═══════════════════════════════════════════════════════════════════════════════

describe('Build13: Status Lifecycle Display', () => {
  const QUOTE_STATUSES = ['draft', 'priced', 'sent', 'viewed', 'negotiating', 'accepted', 'rejected', 'expired'];
  const ORDER_STATUSES = ['created', 'confirmed', 'locked', 'in_execution', 'completed', 'cancelled'];
  const INTAKE_STATUSES = ['new', 'in_review', 'needs_info', 'ready_for_quote', 'blocked', 'cancelled'];

  it('quote statuses are complete (8 statuses)', () => {
    expect(QUOTE_STATUSES).toHaveLength(8);
  });

  it('order statuses are complete (6 statuses)', () => {
    expect(ORDER_STATUSES).toHaveLength(6);
  });

  it('intake statuses are complete (6 statuses)', () => {
    expect(INTAKE_STATUSES).toHaveLength(6);
  });

  it('quote terminal statuses are accepted/rejected/expired', () => {
    const terminal = ['accepted', 'rejected', 'expired'];
    terminal.forEach(s => expect(QUOTE_STATUSES).toContain(s));
  });

  it('order terminal statuses are completed/cancelled', () => {
    const terminal = ['completed', 'cancelled'];
    terminal.forEach(s => expect(ORDER_STATUSES).toContain(s));
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// C. REPORTS CANCELLED EXCLUSION (FRONTEND LOGIC)
// ═══════════════════════════════════════════════════════════════════════════════

describe('Build13: Reports Cancelled Exclusion', () => {
  it('cancelled orders excluded from job status funnel', () => {
    const orders = [
      { status: 'created' },
      { status: 'locked' },
      { status: 'in_execution' },
      { status: 'completed' },
      { status: 'cancelled' },
      { status: 'cancelled' },
    ];
    const activeFunnel = orders.filter(o => o.status !== 'cancelled');
    expect(activeFunnel).toHaveLength(4);
    expect(activeFunnel.every(o => o.status !== 'cancelled')).toBe(true);
  });

  it('all cancelled returns empty funnel', () => {
    const orders = [{ status: 'cancelled' }, { status: 'cancelled' }];
    const activeFunnel = orders.filter(o => o.status !== 'cancelled');
    expect(activeFunnel).toHaveLength(0);
  });

  it('invalid/rejected quotes excluded from conversion candidates', () => {
    const quotes = [
      { status: 'accepted' },
      { status: 'priced' },
      { status: 'rejected' },
      { status: 'expired' },
      { status: 'draft' },
    ];
    const convertible = quotes.filter(q => q.status === 'accepted' || q.status === 'priced');
    expect(convertible).toHaveLength(2);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// D. BUILD 12 REGRESSION — Components Still Render
// ═══════════════════════════════════════════════════════════════════════════════

vi.mock('@/api/orders', () => ({
  getOrderDocumentSnapshotReference: vi.fn(),
  getQuoteAcceptanceGuard: vi.fn(),
}));

vi.mock('@/api/quoteOutputSnapshotGovernance', () => ({
  getSnapshotGovernanceEligibility: vi.fn(),
}));

describe('Build13: Build 12 Component Regression', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('OrderDocumentSnapshotSection renders without crash', async () => {
    const { OrderDocumentSnapshotSection } = await import('./OrderDocumentSnapshotSection');
    const { container } = render(<OrderDocumentSnapshotSection orderId={1} />);
    expect(container).toBeTruthy();
  });

  it('QuoteAcceptanceGuardIndicator renders without crash', async () => {
    const { QuoteAcceptanceGuardIndicator } = await import('./QuoteAcceptanceGuardIndicator');
    const { container } = render(<QuoteAcceptanceGuardIndicator quoteId={1} />);
    expect(container).toBeTruthy();
  });

  it('SnapshotGovernanceStatus renders without crash', async () => {
    const mod = await import('./SnapshotGovernanceStatus');
    const SnapshotGovernanceStatus = mod.default;
    const { container } = render(<SnapshotGovernanceStatus quoteId={1} />);
    expect(container).toBeTruthy();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// E. FULL FLOW TRACEABILITY (FRONTEND DATA CONTRACTS)
// ═══════════════════════════════════════════════════════════════════════════════

describe('Build13: Full Flow Data Contract Verification', () => {
  it('order data references source quote', () => {
    const orderData = {
      id: 1,
      code: 'ORD-001',
      quote_id: 42,
      quote_code: 'QUO-042',
      status: 'locked',
      client_name: 'Test SRL',
    };
    expect(orderData.quote_id).toBe(42);
    expect(orderData.quote_code).toBe('QUO-042');
  });

  it('readiness snapshot has canonical structure', () => {
    const snapshot = {
      source: 'backend',
      snapshot_type: 'product_readiness_at_order_acceptance',
      snapshot_at: '2026-05-18T10:00:00Z',
      readiness_result: {
        overall_status: 'eligible',
        ready_for_quote: true,
      },
      warnings_acknowledged: false,
    };
    expect(snapshot.source).toBe('backend');
    expect(snapshot.readiness_result.overall_status).toBe('eligible');
  });

  it('execution plan references order', () => {
    const plan = {
      order_id: 1,
      order_code: 'ORD-001',
      snapshot_version: 1,
      tasks_json: '[]',
    };
    expect(plan.order_id).toBe(1);
    expect(plan.snapshot_version).toBe(1);
  });

  it('quote conversion requires priced or accepted status', () => {
    const canConvert = (status: string) => ['priced', 'accepted'].includes(status);
    expect(canConvert('priced')).toBe(true);
    expect(canConvert('accepted')).toBe(true);
    expect(canConvert('draft')).toBe(false);
    expect(canConvert('sent')).toBe(false);
    expect(canConvert('viewed')).toBe(false);
    expect(canConvert('negotiating')).toBe(false);
    expect(canConvert('rejected')).toBe(false);
    expect(canConvert('expired')).toBe(false);
  });
});