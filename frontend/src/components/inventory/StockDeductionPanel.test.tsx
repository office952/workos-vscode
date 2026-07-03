/**
 * Tests for StockDeductionPanel — BUILD 16: Inventory Operational Loop.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import StockDeductionPanel from "./StockDeductionPanel";
import * as api from "@/api/inventoryDeduction";

vi.mock("@/api/inventoryDeduction");

const mockStatus: api.DeductionStatusResponse = {
  order_id: 1,
  reality_exists: true,
  reality_id: 10,
  rows: [
    {
      index: 0,
      material_id: 100,
      material_name: "Oțel inox 304",
      quantity: 5,
      unit: "kg",
      status: "eligible",
      current_stock: 50,
      message: "Eligibil pentru deducere",
    },
    {
      index: 1,
      material_id: null,
      material_name: "Manoperă sudură",
      quantity: 2,
      unit: "ore",
      status: "not_linked",
      current_stock: null,
      message: "Rând observațional",
    },
    {
      index: 2,
      material_id: 101,
      material_name: "Aluminiu 6061",
      quantity: 10,
      unit: "kg",
      status: "already_deducted",
      current_stock: 40,
      message: "Deja dedus",
    },
  ],
  summary: {
    total: 3,
    eligible: 1,
    not_linked: 1,
    already_deducted: 1,
  },
};

const mockDeductionResult: api.DeductionResponse = {
  order_id: 1,
  reality_id: 10,
  total_rows: 3,
  deducted_count: 1,
  skipped_count: 1,
  blocked_count: 0,
  rows: [
    {
      material_index: 0,
      status: "deducted",
      material_id: 100,
      material_name: "Oțel inox 304",
      quantity: 5,
      unit: "kg",
      old_stock: 50,
      new_stock: 45,
      message: "Dedus cu succes",
    },
  ],
};

describe("StockDeductionPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    vi.mocked(api.getDeductionStatus).mockImplementation(
      () => new Promise<api.DeductionStatusResponse>(() => {})
    );
    render(<StockDeductionPanel orderId={1} />);
    expect(screen.getByText(/Se verifică eligibilitatea/)).toBeInTheDocument();
  });

  it("shows no-reality message when reality does not exist", async () => {
    vi.mocked(api.getDeductionStatus).mockResolvedValue({
      order_id: 1,
      reality_exists: false,
      rows: [],
      summary: { total: 0, eligible: 0, not_linked: 0, already_deducted: 0 },
    });
    render(<StockDeductionPanel orderId={1} />);
    await waitFor(() => {
      expect(screen.getByText(/Nu există ExecutionReality/)).toBeInTheDocument();
    });
  });

  it("renders material rows with correct statuses", async () => {
    vi.mocked(api.getDeductionStatus).mockResolvedValue(mockStatus);
    render(<StockDeductionPanel orderId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Oțel inox 304")).toBeInTheDocument();
      expect(screen.getByText("Manoperă sudură")).toBeInTheDocument();
      expect(screen.getByText("Aluminiu 6061")).toBeInTheDocument();
    });
    // Check status labels
    expect(screen.getByText("Eligibil")).toBeInTheDocument();
    expect(screen.getByText("Observațional")).toBeInTheDocument();
    expect(screen.getByText("Dedus")).toBeInTheDocument();
  });

  it("shows deduct-all button with eligible count", async () => {
    vi.mocked(api.getDeductionStatus).mockResolvedValue(mockStatus);
    render(<StockDeductionPanel orderId={1} />);
    await waitFor(() => {
      expect(screen.getByText(/Deduce toate eligibile \(1\)/)).toBeInTheDocument();
    });
  });

  it("calls deductMaterials on deduct-all click", async () => {
    vi.mocked(api.getDeductionStatus).mockResolvedValue(mockStatus);
    vi.mocked(api.deductMaterials).mockResolvedValue(mockDeductionResult);
    render(<StockDeductionPanel orderId={1} />);
    await waitFor(() => {
      expect(screen.getByText(/Deduce toate eligibile/)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText(/Deduce toate eligibile/));
    await waitFor(() => {
      expect(api.deductMaterials).toHaveBeenCalledWith(1, {
        reason: "Deducere operațională din ExecutionReality",
      });
    });
  });

  it("calls deductMaterials with specific index on row deduct click", async () => {
    vi.mocked(api.getDeductionStatus).mockResolvedValue(mockStatus);
    vi.mocked(api.deductMaterials).mockResolvedValue(mockDeductionResult);
    render(<StockDeductionPanel orderId={1} />);
    await waitFor(() => {
      expect(screen.getByText("Deduce")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Deduce"));
    await waitFor(() => {
      expect(api.deductMaterials).toHaveBeenCalledWith(1, {
        material_indices: [0],
        reason: "Deducere individuală din ExecutionReality",
      });
    });
  });

  it("shows result feedback after successful deduction", async () => {
    vi.mocked(api.getDeductionStatus).mockResolvedValue(mockStatus);
    vi.mocked(api.deductMaterials).mockResolvedValue(mockDeductionResult);
    render(<StockDeductionPanel orderId={1} />);
    await waitFor(() => {
      expect(screen.getByText(/Deduce toate eligibile/)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText(/Deduce toate eligibile/));
    await waitFor(() => {
      expect(screen.getByText(/1 deduse, 1 omise, 0 blocate/)).toBeInTheDocument();
    });
  });

  it("shows no-reality fallback on API failure (status remains null)", async () => {
    vi.mocked(api.getDeductionStatus).mockRejectedValue(new Error("Network error"));
    render(<StockDeductionPanel orderId={1} />);
    await waitFor(() => {
      // When API fails, status is null so the no-reality message is shown
      expect(screen.getByText(/Nu există ExecutionReality/)).toBeInTheDocument();
    });
  });

  it("shows summary counts correctly", async () => {
    vi.mocked(api.getDeductionStatus).mockResolvedValue(mockStatus);
    render(<StockDeductionPanel orderId={1} />);
    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument(); // total
    });
  });
});