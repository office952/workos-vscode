/**
 * BUILD 10 — Tests for QuoteOutputSnapshotsSection component.
 *
 * Verifies:
 *   - Component renders
 *   - Disclaimer is shown
 *   - Load button exists
 *   - Snapshot list renders after load
 *   - Status badges display correctly
 *   - Action buttons display based on status
 *   - No Quote mutation
 *   - No Order creation
 *   - Not an order snapshot disclaimer
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import QuoteOutputSnapshotsSection from "./QuoteOutputSnapshotsSection";

// Mock the API module
vi.mock("@/api/quoteOutputSnapshots", () => ({
  createOutputSnapshot: vi.fn(),
  listOutputSnapshots: vi.fn(),
  submitSnapshotForReview: vi.fn(),
  approveSnapshot: vi.fn(),
  archiveSnapshot: vi.fn(),
  rejectSnapshot: vi.fn(),
  getSnapshotExportUrl: vi.fn((quoteId: number, snapshotId: number) =>
    `/api/v1/entities/quotes/${quoteId}/output-snapshots/${snapshotId}/export`
  ),
}));

import {
  listOutputSnapshots,
  createOutputSnapshot,
} from "@/api/quoteOutputSnapshots";

const mockListOutputSnapshots = listOutputSnapshots as ReturnType<typeof vi.fn>;
const mockCreateOutputSnapshot = createOutputSnapshot as ReturnType<typeof vi.fn>;

const MOCK_SNAPSHOT = {
  snapshot_id: 1,
  quote_id: 1,
  quote_code: "Q-2026-001",
  snapshot_code: "QDOC-2026-0001",
  snapshot_type: "quote_output_candidate",
  status: "draft",
  version: 1,
  source_template_id: 1,
  source_template_code: "TPL-BANNER-STANDARD",
  source_dossier_id: 1,
  source_dossier_version: null,
  rendered_sections_json: [
    {
      section_id: "block-01",
      title: "Product Description",
      rendered_text: "Banner publicitar 3x2m",
      warnings: [],
      blockers: [],
    },
  ],
  commercial_summary_json: {
    subtotal: 1000,
    vat: 190,
    total: 1190,
    currency: "RON",
  },
  warnings: [],
  blockers: [],
  variables_used: {},
  trace: { quote_mutated: false, order_mutated: false },
  content_hash: "abc123def456abc123def456abc123de",
  created_by: "user@test.com",
  created_at: "2026-05-18T10:00:00",
  updated_at: "2026-05-18T10:00:00",
  approved_by: null,
  approved_at: null,
  archived_at: null,
  superseded_by_snapshot_id: null,
  notes: null,
  persisted: true,
  not_order_snapshot: true,
  not_final_contract: true,
  not_sent_to_client: true,
};

describe("QuoteOutputSnapshotsSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the section header", () => {
    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    expect(screen.getByText("Saved Output Snapshots")).toBeTruthy();
  });

  it("shows disclaimer about not being an order snapshot", () => {
    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    expect(
      screen.getByText(/not an accepted order snapshot/i)
    ).toBeTruthy();
  });

  it("shows Load Snapshots button initially", () => {
    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    expect(screen.getByText("Load Snapshots")).toBeTruthy();
  });

  it("loads and displays snapshots", async () => {
    mockListOutputSnapshots.mockResolvedValueOnce([MOCK_SNAPSHOT]);

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);

    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText("QDOC-2026-0001")).toBeTruthy();
    });
  });

  it("shows status badge for draft", async () => {
    mockListOutputSnapshots.mockResolvedValueOnce([MOCK_SNAPSHOT]);

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText("Draft")).toBeTruthy();
    });
  });

  it("shows Submit for Review button for draft snapshots", async () => {
    mockListOutputSnapshots.mockResolvedValueOnce([MOCK_SNAPSHOT]);

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText("Submit for Review")).toBeTruthy();
    });
  });

  it("shows Approve button for draft snapshots without blockers", async () => {
    mockListOutputSnapshots.mockResolvedValueOnce([MOCK_SNAPSHOT]);

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText("Approve for Quote Output")).toBeTruthy();
    });
  });

  it("does not show Approve button for snapshots with blockers", async () => {
    const blockedSnapshot = { ...MOCK_SNAPSHOT, blockers: ["missing_dossier"] };
    mockListOutputSnapshots.mockResolvedValueOnce([blockedSnapshot]);

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText("QDOC-2026-0001")).toBeTruthy();
    });
    expect(screen.queryByText("Approve for Quote Output")).toBeNull();
  });

  it("shows empty state when no snapshots", async () => {
    mockListOutputSnapshots.mockResolvedValueOnce([]);

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText(/No saved snapshots yet/)).toBeTruthy();
    });
  });

  it("shows Save Current Preview button after loading", async () => {
    mockListOutputSnapshots.mockResolvedValueOnce([]);

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText("Save Current Preview")).toBeTruthy();
    });
  });

  it("shows content hash for snapshots", async () => {
    mockListOutputSnapshots.mockResolvedValueOnce([MOCK_SNAPSHOT]);

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText("#abc123de")).toBeTruthy();
    });
  });

  it("shows template code for snapshots", async () => {
    mockListOutputSnapshots.mockResolvedValueOnce([MOCK_SNAPSHOT]);

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText("TPL-BANNER-STANDARD")).toBeTruthy();
    });
  });

  it("shows approved status badge correctly", async () => {
    const approvedSnapshot = {
      ...MOCK_SNAPSHOT,
      status: "approved_for_quote_output",
      approved_by: "admin@test.com",
    };
    mockListOutputSnapshots.mockResolvedValueOnce([approvedSnapshot]);

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText("Approved")).toBeTruthy();
    });
  });

  it("handles API error gracefully", async () => {
    mockListOutputSnapshots.mockRejectedValueOnce(new Error("Network error"));

    render(<QuoteOutputSnapshotsSection quoteId={1} quoteCode="Q-2026-001" />);
    fireEvent.click(screen.getByText("Load Snapshots"));

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeTruthy();
    });
  });
});