/**
 * BUILD 12 — Tests for OrderDocumentSnapshotSection component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OrderDocumentSnapshotSection } from './OrderDocumentSnapshotSection';

// Mock the API
vi.mock('@/api/orders', () => ({
  getOrderDocumentSnapshotReference: vi.fn(),
}));

import { getOrderDocumentSnapshotReference } from '@/api/orders';
const mockGetRef = vi.mocked(getOrderDocumentSnapshotReference);

describe('OrderDocumentSnapshotSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders load button initially', () => {
    render(<OrderDocumentSnapshotSection orderId={1} />);
    expect(screen.getByTestId('load-document-snapshot-btn')).toBeInTheDocument();
  });

  it('shows loading state when button clicked', async () => {
    mockGetRef.mockImplementation(
      () => new Promise<Awaited<ReturnType<typeof getOrderDocumentSnapshotReference>>>(() => {})
    ); // never resolves
    render(<OrderDocumentSnapshotSection orderId={1} />);
    fireEvent.click(screen.getByTestId('load-document-snapshot-btn'));
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('displays reference details when snapshot exists', async () => {
    mockGetRef.mockResolvedValue({
      order_id: 1,
      has_document_snapshot: true,
      reference: {
        id: 10,
        order_id: 1,
        quote_id: 5,
        quote_output_snapshot_id: 3,
        snapshot_code: 'SNAP-001',
        snapshot_status_at_acceptance: 'approved_for_quote_output',
        snapshot_version: 2,
        snapshot_content_hash: 'abc123',
        source_template_id: 1,
        source_template_code: 'TPL-BANNER',
        source_dossier_id: 7,
        source_dossier_version: 1,
        source_trace_json: { quote_snapshot_mutated: false },
        governance_status_at_acceptance: 'eligible',
        accepted_at: '2026-05-18T10:00:00Z',
        accepted_by: 'user@test.com',
        created_at: '2026-05-18T10:00:00Z',
        notes: null,
      },
    });

    render(<OrderDocumentSnapshotSection orderId={1} />);
    fireEvent.click(screen.getByTestId('load-document-snapshot-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('snapshot-reference-details')).toBeInTheDocument();
    });

    expect(screen.getByText('SNAP-001')).toBeInTheDocument();
    expect(screen.getByText('approved_for_quote_output')).toBeInTheDocument();
    expect(screen.getByText('eligible')).toBeInTheDocument();
    expect(screen.getByText('TPL-BANNER')).toBeInTheDocument();
  });

  it('displays no-snapshot message when reference is missing', async () => {
    mockGetRef.mockResolvedValue({
      order_id: 1,
      has_document_snapshot: false,
      reference: null,
    });

    render(<OrderDocumentSnapshotSection orderId={1} />);
    fireEvent.click(screen.getByTestId('load-document-snapshot-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('no-snapshot-message')).toBeInTheDocument();
    });
  });

  it('displays error message on API failure', async () => {
    mockGetRef.mockRejectedValue(new Error('Network error'));

    render(<OrderDocumentSnapshotSection orderId={1} />);
    fireEvent.click(screen.getByTestId('load-document-snapshot-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toBeInTheDocument();
    });
    expect(screen.getByText(/Network error/)).toBeInTheDocument();
  });
});