import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Orders from "./Orders";
import type { Order } from "@/lib/mockData";
import { executionApi, PlanGenerationError } from "@/api/execution";

const mockNavigate = vi.fn();
const mockRefresh = vi.fn();
const mockUseBackendData = vi.fn();

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => mockUseBackendData(),
}));

const lockedOrder: Order = {
  id: "ORD-VOL-001",
  dbId: 501,
  quoteId: "Q-VOL-001",
  client: "Volumetric Client",
  contactPerson: "Operator",
  status: "locked",
  productSummary: "Litere volumetrice LED",
  totalAmount: 5950,
  createdAt: "2026-06-01T00:00:00Z",
  lockedAt: "2026-06-01T01:00:00Z",
  promisedDelivery: "2026-06-15",
  jobId: "",
  paymentStatus: "pending",
  snapshotVersion: 1,
  notes: "",
};

function renderOrderDetail() {
  mockUseBackendData.mockReturnValue({
    orders: [lockedOrder],
    loading: false,
    error: null,
    source: "db",
    sourcesDetail: { orders: "db" },
    refresh: mockRefresh,
  });

  return render(
    <MemoryRouter initialEntries={["/orders/ORD-VOL-001"]}>
      <Routes>
        <Route path="/orders/:orderId?" element={<Orders />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Orders execution dispatch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRefresh.mockResolvedValue(undefined);
    vi.spyOn(executionApi, "getObservability").mockResolvedValue({
      order_id: 501,
      order_code: "ORD-VOL-001",
      status: "OK",
      reasons: [],
      has_order: true,
      has_plan: false,
      has_reality: false,
      plan_total_estimated_minutes: null,
      reality_total_actual_minutes: null,
      delta_minutes: null,
      delta_pct: null,
      thresholds: {
        warning_time_delta_pct: null,
        critical_time_delta_pct: null,
        warning_time_delta_minutes: null,
        critical_time_delta_minutes: null,
        is_active: false,
        source: "backend",
      },
      observed_at: "2026-06-01T00:00:00Z",
    });
  });

  it("shows generate execution plan action for locked order without plan", async () => {
    renderOrderDetail();

    expect(await screen.findByTestId("order-execution-dispatch-panel")).toBeInTheDocument();
    expect(screen.getByTestId("order-execution-plan-missing")).toHaveTextContent(
      /Planul de execuție nu a fost generat/i
    );
    expect(screen.getByTestId("order-generate-execution-plan-action")).toHaveTextContent(
      /Generează taskuri producție/i
    );
  });

  it("generates plan and shows open execution CTA", async () => {
    vi.spyOn(executionApi, "generatePlan").mockResolvedValue({
      id: 1,
      order_id: 501,
      order_code: "ORD-VOL-001",
      snapshot_version: 1,
      tasks: [{ task_id: "T-001", name: "Debitare față", layer_id: "l1", process_type: "cnc_routing", machine_type: "", estimated_time_minutes: 45, quantity: 1 }],
      total_estimated_time_minutes: 45,
    });

    renderOrderDetail();
    fireEvent.click(await screen.findByTestId("order-generate-execution-plan-action"));

    await waitFor(() => {
      expect(executionApi.generatePlan).toHaveBeenCalledWith(501);
      expect(screen.getByTestId("order-view-execution-cta")).toBeInTheDocument();
      expect(screen.queryByTestId("order-open-execution-action")).toBeNull();
    });
  });

  it("shows existing plan message on duplicate generation", async () => {
    vi.spyOn(executionApi, "generatePlan").mockRejectedValue(
      new PlanGenerationError("plan_already_exists", 409, "Plan existent", null, 9, null)
    );

    renderOrderDetail();
    fireEvent.click(await screen.findByTestId("order-generate-execution-plan-action"));

    await waitFor(() => {
      expect(screen.getByTestId("order-execution-plan-error")).toHaveTextContent(/există deja/i);
    });
  });
});
