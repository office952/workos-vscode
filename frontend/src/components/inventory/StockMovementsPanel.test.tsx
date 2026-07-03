/**
 * Tests for StockMovementsPanel — BUILD 16: Inventory Operational Loop.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import StockMovementsPanel from "./StockMovementsPanel";
import * as api from "@/api/inventoryDeduction";

vi.mock("@/api/inventoryDeduction");

const mockMovements: api.StockMovement[] = [
  {
    id: 1,
    material_id: 100,
    source_type: "execution_reality",
    source_id: 10,
    order_id: 1,
    task_id: null,
    quantity: 5,
    unit: "kg",
    movement_type: "consumption",
    old_stock: 50,
    new_stock: 45,
    performed_by: "operator",
    performed_at: "2026-05-18T10:30:00Z",
    reason: "Deducere operațională",
  },
  {
    id: 2,
    material_id: 101,
    source_type: "stock_movement_reversal",
    source_id: 1,
    order_id: 1,
    task_id: null,
    quantity: 5,
    unit: "kg",
    movement_type: "reversal",
    old_stock: 45,
    new_stock: 50,
    performed_by: "operator",
    performed_at: "2026-05-18T09:15:00Z",
    reason: "Restituire operațională",
  },
  {
    id: 3,
    material_id: 102,
    source_type: "manual_adjustment",
    source_id: 99,
    order_id: null,
    task_id: null,
    quantity: 0,
    unit: "kg",
    movement_type: "adjustment",
    old_stock: 10,
    new_stock: 10,
    performed_by: "operator",
    performed_at: "2026-05-18T08:00:00Z",
    reason: "No-op",
  },
];

describe("StockMovementsPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    vi.mocked(api.getRecentMovements).mockImplementation(
      () => new Promise<api.MovementsResponse>(() => {})
    );
    render(<StockMovementsPanel />);
    expect(screen.getByText(/Se încarcă/)).toBeInTheDocument();
  });

  it("shows empty state when no movements exist", async () => {
    vi.mocked(api.getRecentMovements).mockResolvedValue({
      movements: [],
      total: 0,
    });
    render(<StockMovementsPanel />);
    await waitFor(() => {
      expect(screen.getByText(/Nicio mișcare de stoc/)).toBeInTheDocument();
    });
  });

  it("renders movement rows correctly", async () => {
    vi.mocked(api.getRecentMovements).mockResolvedValue({
      movements: mockMovements,
      total: 2,
    });
    render(<StockMovementsPanel />);
    await waitFor(() => {
      expect(screen.getByText("ID #1")).toBeInTheDocument();
      expect(screen.getByText("ID #2")).toBeInTheDocument();
      expect(screen.getByText("ID #3")).toBeInTheDocument();
    });
    // Check stock transitions
    expect(screen.getByText("50 → 45")).toBeInTheDocument();
    expect(screen.getByText("45 → 50")).toBeInTheDocument();
    expect(screen.getByText("10 → 10")).toBeInTheDocument();
  });

  it("shows delta sign from stock transition", async () => {
    vi.mocked(api.getRecentMovements).mockResolvedValue({
      movements: mockMovements,
      total: 3,
    });
    render(<StockMovementsPanel />);
    await waitFor(() => {
      expect(screen.getByText("-5 kg")).toBeInTheDocument();
      expect(screen.getByText("+5 kg")).toBeInTheDocument();
      expect(screen.getByText("0 kg")).toBeInTheDocument();
    });
  });

  it("keeps distinct movement labels", async () => {
    vi.mocked(api.getRecentMovements).mockResolvedValue({
      movements: mockMovements,
      total: 3,
    });
    render(<StockMovementsPanel />);
    await waitFor(() => {
      expect(screen.getByText("Consum producție")).toBeInTheDocument();
      expect(screen.getByText("Restituire")).toBeInTheDocument();
      expect(screen.getByText("Mișcare stoc")).toBeInTheDocument();
    });
  });

  it("shows order IDs", async () => {
    vi.mocked(api.getRecentMovements).mockResolvedValue({
      movements: mockMovements,
      total: 3,
    });
    render(<StockMovementsPanel />);
    await waitFor(() => {
      const orderLabels = screen.getAllByText("Cmd #1");
      expect(orderLabels.length).toBe(2);
    });
  });

  it("refreshes on button click", async () => {
    vi.mocked(api.getRecentMovements).mockResolvedValue({
      movements: mockMovements,
      total: 2,
    });
    render(<StockMovementsPanel />);
    await waitFor(() => {
      expect(screen.getByText("ID #1")).toBeInTheDocument();
    });
    // Click refresh
    fireEvent.click(screen.getByTitle("Reîncarcă"));
    await waitFor(() => {
      expect(api.getRecentMovements).toHaveBeenCalledTimes(2);
    });
  });

  it("shows error message on API failure", async () => {
    vi.mocked(api.getRecentMovements).mockRejectedValue(new Error("Server error"));
    render(<StockMovementsPanel />);
    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeInTheDocument();
    });
  });

  it("calls getRecentMovements with limit 30", async () => {
    vi.mocked(api.getRecentMovements).mockResolvedValue({
      movements: [],
      total: 0,
    });
    render(<StockMovementsPanel />);
    await waitFor(() => {
      expect(api.getRecentMovements).toHaveBeenCalledWith(30);
    });
  });
});