/**
 * BUILD 18 — RealityQualityBadge Tests.
 *
 * Tests:
 *   - Renders valid badge for valid reality
 *   - Renders invalid badge with reason for invalid reality
 *   - Shows stock reconciliation warning when required
 *   - Shows invalidate button for users with permission
 *   - Hides invalidate button for users without permission
 *   - Shows restore button for invalid reality with permission
 *   - Hides restore button when stock_reconciliation_required
 *   - Invalidation dialog requires reason
 *   - Successful invalidation updates badge
 *   - Successful restoration updates badge
 *   - Compact mode hides action buttons
 *   - Loading state shows placeholder
 *   - Error state shows error badge
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import RealityQualityBadge from "./RealityQualityBadge";
import * as api from "@/api/executionRealityQuality";

vi.mock("@/api/executionRealityQuality");

// Mock permissions hook
const mockCan = vi.fn();
vi.mock("@/hooks/useCurrentPermissions", () => ({
  useCurrentPermissions: () => ({
    can: mockCan,
    role: "admin",
    isAdmin: true,
    canViewNav: () => true,
  }),
}));

const validStatus: api.QualityStatus = {
  reality_id: 1,
  order_id: 100,
  order_code: "CMD-0100",
  is_invalid: false,
  invalidated_at: null,
  invalidated_by: null,
  invalid_reason: null,
  stock_reconciliation_required: false,
  stock_deducted: false,
  restored_at: null,
  restored_by: null,
  restored_reason: null,
  warnings: [],
};

const invalidStatus: api.QualityStatus = {
  reality_id: 1,
  order_id: 100,
  order_code: "CMD-0100",
  is_invalid: true,
  invalidated_at: "2026-05-18T10:00:00Z",
  invalidated_by: "admin@workos.test",
  invalid_reason: "Date incorecte introduse de operator",
  stock_reconciliation_required: false,
  stock_deducted: false,
  restored_at: null,
  restored_by: null,
  restored_reason: null,
  warnings: ["Reality invalidată — exclusă din rapoarte și deduceri stoc"],
};

const invalidWithReconciliation: api.QualityStatus = {
  ...invalidStatus,
  stock_reconciliation_required: true,
  stock_deducted: true,
  warnings: [
    "Reality invalidată — exclusă din rapoarte și deduceri stoc",
    "Reconciliere stoc necesară: stocul a fost dedus înainte de invalidare",
  ],
};

const restoredStatus: api.QualityStatus = {
  ...validStatus,
  restored_at: "2026-05-18T12:00:00Z",
  restored_by: "admin@workos.test",
  restored_reason: "Datele au fost verificate",
};

describe("RealityQualityBadge", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCan.mockReturnValue(true); // Admin has all permissions by default
  });

  it("renders valid badge for valid reality", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(validStatus);
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Validă")).toBeInTheDocument();
    });
  });

  it("renders invalid badge with reason for invalid reality", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(invalidStatus);
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("INVALIDATĂ")).toBeInTheDocument();
      expect(screen.getByText(/Date incorecte/)).toBeInTheDocument();
    });
  });

  it("shows stock reconciliation warning when required", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(invalidWithReconciliation);
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Reconciliere stoc necesară")).toBeInTheDocument();
    });
  });

  it("shows invalidate button for users with permission", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(validStatus);
    mockCan.mockImplementation((p: string) => p === "reality.invalidate");
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Invalidează Reality")).toBeInTheDocument();
    });
  });

  it("hides invalidate button for users without permission", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(validStatus);
    mockCan.mockReturnValue(false);
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Validă")).toBeInTheDocument();
    });
    expect(screen.queryByText("Invalidează Reality")).not.toBeInTheDocument();
  });

  it("shows restore button for invalid reality with permission", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(invalidStatus);
    mockCan.mockImplementation((p: string) => p === "reality.restore_valid");
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Restaurează")).toBeInTheDocument();
    });
  });

  it("hides restore button when stock_reconciliation_required", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(invalidWithReconciliation);
    mockCan.mockReturnValue(true);
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("INVALIDATĂ")).toBeInTheDocument();
    });
    expect(screen.queryByText("Restaurează")).not.toBeInTheDocument();
  });

  it("invalidation dialog requires reason", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(validStatus);
    mockCan.mockReturnValue(true);
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Invalidează Reality")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Invalidează Reality"));
    await waitFor(() => {
      expect(screen.getByText("Confirmă Invalidarea")).toBeInTheDocument();
    });
    // Button should be disabled without reason
    const confirmBtn = screen.getByText("Confirmă Invalidarea");
    expect(confirmBtn).toBeDisabled();
  });

  it("successful invalidation updates badge", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(validStatus);
    vi.mocked(api.invalidateReality).mockResolvedValue(invalidStatus);
    mockCan.mockReturnValue(true);

    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Invalidează Reality")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Invalidează Reality"));
    await waitFor(() => {
      expect(screen.getByText("Confirmă Invalidarea")).toBeInTheDocument();
    });

    // Enter reason
    const textarea = screen.getByPlaceholderText("Descrieți motivul invalidării...");
    fireEvent.change(textarea, { target: { value: "Test invalidation reason" } });

    // Confirm
    fireEvent.click(screen.getByText("Confirmă Invalidarea"));
    await waitFor(() => {
      expect(screen.getByText("INVALIDATĂ")).toBeInTheDocument();
    });
  });

  it("successful restoration updates badge", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(invalidStatus);
    vi.mocked(api.restoreReality).mockResolvedValue(restoredStatus);
    mockCan.mockReturnValue(true);

    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Restaurează")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Restaurează"));
    await waitFor(() => {
      expect(screen.getByText("Confirmă Restaurarea")).toBeInTheDocument();
    });

    // Enter reason
    const textarea = screen.getByPlaceholderText("Descrieți motivul restaurării...");
    fireEvent.change(textarea, { target: { value: "Verified data is correct" } });

    // Confirm
    fireEvent.click(screen.getByText("Confirmă Restaurarea"));
    await waitFor(() => {
      expect(screen.getByText("Validă")).toBeInTheDocument();
    });
  });

  it("compact mode hides action buttons", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(validStatus);
    mockCan.mockReturnValue(true);
    render(<RealityQualityBadge realityId={1} compact />);
    await waitFor(() => {
      expect(screen.getByText("Validă")).toBeInTheDocument();
    });
    expect(screen.queryByText("Invalidează Reality")).not.toBeInTheDocument();
  });

  it("loading state shows placeholder", () => {
    vi.mocked(api.getQualityStatus).mockImplementation(
      () => new Promise<api.QualityStatus>(() => {}) // Never resolves
    );
    render(<RealityQualityBadge realityId={1} />);
    expect(screen.getByText("Se verifică...")).toBeInTheDocument();
  });

  it("error state shows error badge", async () => {
    vi.mocked(api.getQualityStatus).mockRejectedValue(new Error("Network error"));
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Eroare calitate")).toBeInTheDocument();
    });
  });

  it("shows auth/session badge for 401", async () => {
    vi.mocked(api.getQualityStatus).mockRejectedValue({
      status: 401,
      message: "Authentication credentials were not provided",
    });
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Sesiune expirată")).toBeInTheDocument();
    });
    expect(screen.queryByText("Eroare calitate")).not.toBeInTheDocument();
  });

  it("shows empty-state badge for 404", async () => {
    vi.mocked(api.getQualityStatus).mockRejectedValue({
      status: 404,
      message: "reality_not_found",
    });
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Fără status calitate")).toBeInTheDocument();
    });
    expect(screen.queryByText("Eroare calitate")).not.toBeInTheDocument();
  });

  it("shows restoration info for previously-restored reality", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(restoredStatus);
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText(/Restaurată/)).toBeInTheDocument();
      expect(screen.getByText(/Datele au fost verificate/)).toBeInTheDocument();
    });
  });

  it("shows warnings from quality status", async () => {
    vi.mocked(api.getQualityStatus).mockResolvedValue(invalidStatus);
    render(<RealityQualityBadge realityId={1} />);
    await waitFor(() => {
      expect(screen.getByText(/exclusă din rapoarte/)).toBeInTheDocument();
    });
  });
});