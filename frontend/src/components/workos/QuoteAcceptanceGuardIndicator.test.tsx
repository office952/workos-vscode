/**
 * BUILD 12 — Tests for QuoteAcceptanceGuardIndicator component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QuoteAcceptanceGuardIndicator } from './QuoteAcceptanceGuardIndicator';

// Mock the API
vi.mock('@/api/orders', () => ({
  getQuoteAcceptanceGuard: vi.fn(),
}));

import { getQuoteAcceptanceGuard } from '@/api/orders';
const mockGetGuard = vi.mocked(getQuoteAcceptanceGuard);

describe('QuoteAcceptanceGuardIndicator', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders load button initially', () => {
    render(<QuoteAcceptanceGuardIndicator quoteId={5} />);
    expect(screen.getByTestId('load-acceptance-guard-btn')).toBeInTheDocument();
  });

  it('shows loading state when button clicked', async () => {
    mockGetGuard.mockImplementation(
      () => new Promise<Awaited<ReturnType<typeof getQuoteAcceptanceGuard>>>(() => {})
    );
    render(<QuoteAcceptanceGuardIndicator quoteId={5} />);
    fireEvent.click(screen.getByTestId('load-acceptance-guard-btn'));
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('displays eligible status with guards', async () => {
    mockGetGuard.mockResolvedValue({
      quote_id: 5,
      overall_status: 'eligible',
      guards: [
        {
          guard: 'quote_status',
          status: 'eligible',
          detail: 'Quote status is accepted',
        },
        {
          guard: 'document_snapshot',
          status: 'eligible',
          detail: 'Approved document snapshot available',
          snapshot_id: 3,
        },
        {
          guard: 'product_readiness',
          status: 'eligible',
          detail: 'Product readiness OK',
        },
      ],
    });

    render(<QuoteAcceptanceGuardIndicator quoteId={5} />);
    fireEvent.click(screen.getByTestId('load-acceptance-guard-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('guard-results')).toBeInTheDocument();
    });

    expect(screen.getByText('Eligibil')).toBeInTheDocument();
    expect(screen.getByTestId('guard-item-quote_status')).toBeInTheDocument();
    expect(screen.getByTestId('guard-item-document_snapshot')).toBeInTheDocument();
    expect(screen.getByTestId('guard-item-product_readiness')).toBeInTheDocument();
  });

  it('displays blocked status', async () => {
    mockGetGuard.mockResolvedValue({
      quote_id: 5,
      overall_status: 'blocked',
      guards: [
        {
          guard: 'quote_status',
          status: 'blocked',
          detail: "Quote status 'draft' is not eligible for order conversion",
          required_status: ['accepted', 'priced', 'sent'],
        },
      ],
    });

    render(<QuoteAcceptanceGuardIndicator quoteId={5} />);
    fireEvent.click(screen.getByTestId('load-acceptance-guard-btn'));

    await waitFor(() => {
      expect(screen.getByText('Blocat')).toBeInTheDocument();
    });
  });

  it('displays needs_acknowledgement status with warning', async () => {
    mockGetGuard.mockResolvedValue({
      quote_id: 5,
      overall_status: 'needs_acknowledgement',
      guards: [
        {
          guard: 'document_snapshot',
          status: 'warning',
          detail: 'No approved document snapshot found — acknowledgement required',
          requires_acknowledgement: true,
        },
      ],
    });

    render(<QuoteAcceptanceGuardIndicator quoteId={5} />);
    fireEvent.click(screen.getByTestId('load-acceptance-guard-btn'));

    await waitFor(() => {
      expect(screen.getByText('Necesită confirmare')).toBeInTheDocument();
    });
    expect(screen.getByText(/Necesită confirmare explicită/)).toBeInTheDocument();
  });

  it('displays error message on API failure', async () => {
    mockGetGuard.mockRejectedValue(new Error('Quote not found'));

    render(<QuoteAcceptanceGuardIndicator quoteId={999} />);
    fireEvent.click(screen.getByTestId('load-acceptance-guard-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toBeInTheDocument();
    });
    expect(screen.getByText(/Quote not found/)).toBeInTheDocument();
  });
});