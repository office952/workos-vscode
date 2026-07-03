/**
 * BUILD 11 — Tests for SnapshotGovernanceStatus component.
 *
 * Verifies:
 *   - Initial load button renders
 *   - Loading state displays
 *   - Eligible status displays correctly
 *   - Blocked status with blockers
 *   - Needs_review status with conflicts
 *   - Missing status
 *   - Error state on API failure
 *   - Metadata flags display
 *   - Read-only disclaimer
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SnapshotGovernanceStatus from "./SnapshotGovernanceStatus";

// Mock the API module
vi.mock("../../api/quoteOutputSnapshotGovernance", () => ({
  getSnapshotEligibility: vi.fn(),
}));

import { getSnapshotEligibility } from "../../api/quoteOutputSnapshotGovernance";
const mockFetch = vi.mocked(getSnapshotEligibility);

function makeEligibilityResponse(
  overrides: Partial<Awaited<ReturnType<typeof getSnapshotEligibility>>> = {}
): Awaited<ReturnType<typeof getSnapshotEligibility>> {
  return {
    quote_id: 100,
    eligibility_status: "eligible",
    reasons: [],
    approved_snapshot_id: null,
    approved_snapshot_code: null,
    approved_snapshot_version: null,
    conflict_snapshot_ids: [],
    blockers: [],
    warnings: [],
    source_metadata_present: false,
    source_template_id: null,
    source_template_code: null,
    source_dossier_id: null,
    source_dossier_version: null,
    source_output_block_versions: [],
    total_snapshots: 1,
    snapshots_by_status: { approved: 1 },
    governance_version: "0.1.0",
    read_only: true,
    no_order_mutation: true,
    no_quote_status_change: true,
    no_order_creation: true,
    no_contract_generation: true,
    no_send_to_client: true,
    ...overrides,
  };
}

describe("SnapshotGovernanceStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders initial load button", () => {
    render(<SnapshotGovernanceStatus quoteId={100} />);
    expect(screen.getByTestId("governance-load-btn")).toBeTruthy();
    expect(screen.getByText("Evaluează Eligibilitate")).toBeTruthy();
  });

  it("shows loading state when evaluating", async () => {
    // Never resolves during test
    mockFetch.mockImplementation(
      () => new Promise<Awaited<ReturnType<typeof getSnapshotEligibility>>>(() => {})
    );

    render(<SnapshotGovernanceStatus quoteId={100} />);
    fireEvent.click(screen.getByTestId("governance-load-btn"));

    await waitFor(() => {
      expect(screen.getByText(/Se evaluează eligibilitatea/)).toBeTruthy();
    });
  });

  it("displays eligible status correctly", async () => {
    mockFetch.mockResolvedValue(
      makeEligibilityResponse({
        eligibility_status: "eligible",
        total_snapshots: 2,
        snapshots_by_status: { approved: 1, draft: 1 },
      })
    );

    render(<SnapshotGovernanceStatus quoteId={100} />);
    fireEvent.click(screen.getByTestId("governance-load-btn"));

    await waitFor(() => {
      expect(screen.getByText("Eligibil")).toBeTruthy();
    });
  });

  it("displays blocked status with blockers", async () => {
    mockFetch.mockResolvedValue(
      makeEligibilityResponse({
        eligibility_status: "blocked",
        blockers: ["No approved snapshot found", "No rendered content"],
        total_snapshots: 1,
        snapshots_by_status: { draft: 1 },
      })
    );

    render(<SnapshotGovernanceStatus quoteId={100} />);
    fireEvent.click(screen.getByTestId("governance-load-btn"));

    await waitFor(() => {
      expect(screen.getByText("Blocat")).toBeTruthy();
    });
    expect(screen.getByText(/No approved snapshot found/)).toBeTruthy();
    expect(screen.getByText(/No rendered content/)).toBeTruthy();
  });

  it("displays needs_review status with conflict", async () => {
    mockFetch.mockResolvedValue(
      makeEligibilityResponse({
        eligibility_status: "needs_review",
        warnings: ["Multiple approved snapshots detected"],
        conflict_snapshot_ids: [10, 11],
        total_snapshots: 3,
        snapshots_by_status: { approved: 2, draft: 1 },
      })
    );

    render(<SnapshotGovernanceStatus quoteId={100} />);
    fireEvent.click(screen.getByTestId("governance-load-btn"));

    await waitFor(() => {
      expect(screen.getByText(/Necesită Verificare/)).toBeTruthy();
    });
    expect(
      screen.getByText(/Multiple approved snapshots detected/)
    ).toBeTruthy();
  });

  it("displays missing status", async () => {
    mockFetch.mockResolvedValue(
      makeEligibilityResponse({
        eligibility_status: "missing",
        blockers: ["No snapshot candidates exist for this quote"],
        total_snapshots: 0,
        snapshots_by_status: {},
      })
    );

    render(<SnapshotGovernanceStatus quoteId={100} />);
    fireEvent.click(screen.getByTestId("governance-load-btn"));

    await waitFor(() => {
      expect(screen.getByText("Lipsă")).toBeTruthy();
    });
  });

  it("displays error state on API failure", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));

    render(<SnapshotGovernanceStatus quoteId={100} />);
    fireEvent.click(screen.getByTestId("governance-load-btn"));

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeTruthy();
    });
  });

  it("displays approved snapshot metadata", async () => {
    mockFetch.mockResolvedValue(
      makeEligibilityResponse({
        eligibility_status: "eligible",
        approved_snapshot_id: 42,
        approved_snapshot_code: "QDOC-2026-0042",
        approved_snapshot_version: 3,
        source_metadata_present: true,
        source_template_code: "TPL-BANNER",
        source_dossier_id: 7,
        total_snapshots: 2,
        snapshots_by_status: { approved: 1, draft: 1 },
      })
    );

    render(<SnapshotGovernanceStatus quoteId={100} />);
    fireEvent.click(screen.getByTestId("governance-load-btn"));

    await waitFor(() => {
      expect(screen.getByText("Eligibil")).toBeTruthy();
    });
    // Check approved snapshot section renders
    expect(screen.getByText("Snapshot Aprobat")).toBeTruthy();
    expect(screen.getByText(/QDOC-2026-0042/)).toBeTruthy();
    expect(screen.getByText(/TPL-BANNER/)).toBeTruthy();
    expect(screen.getByText(/Metadate sursă:/)).toBeTruthy();
  });

  it("shows read-only governance footer", async () => {
    mockFetch.mockResolvedValue(
      makeEligibilityResponse({
        eligibility_status: "eligible",
        governance_version: "0.1.0",
      })
    );

    render(<SnapshotGovernanceStatus quoteId={100} />);
    fireEvent.click(screen.getByTestId("governance-load-btn"));

    await waitFor(() => {
      expect(screen.getByText("Eligibil")).toBeTruthy();
    });
    expect(screen.getByText(/Read-only/)).toBeTruthy();
    expect(screen.getByText(/No mutations/)).toBeTruthy();
  });
});