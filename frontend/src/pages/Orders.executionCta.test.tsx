import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Orders from "./Orders";
import type { Order } from "@/lib/mockData";
import { executionApi } from "@/api/execution";

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

const lockedOrderWithPlan: Order = {
  id: "ORD-1781201059-1",
  dbId: 1,
  quoteId: "QT-E2E-COMMERCIAL-001",
  client: "E2E Commercial Spine Client",
  contactPerson: "E2E Validator",
  status: "locked",
  productSummary: "Litere volumetrice LED",
  totalAmount: 1104.33,
  createdAt: "2026-06-01T00:00:00Z",
  lockedAt: "2026-06-01T01:00:00Z",
  promisedDelivery: "2026-06-15",
  jobId: "",
  paymentStatus: "pending",
  snapshotVersion: 1,
  notes: "",
};

const lockedOrderNoPlan: Order = {
  ...lockedOrderWithPlan,
  id: "ORD-NO-PLAN",
  dbId: 502,
};

function renderOrderDetail(
  order: Order,
  backendState: {
    source: "db" | "mixed" | "mock" | "empty" | "error";
    sourcesDetail?: Record<string, string>;
  }
) {
  mockUseBackendData.mockReturnValue({
    orders: [order],
    loading: false,
    error: null,
    source: backendState.source,
    sourcesDetail: backendState.sourcesDetail ?? {},
    refresh: mockRefresh,
  });

  return render(
    <MemoryRouter initialEntries={[`/orders/${order.id}`]}>
      <Routes>
        <Route path="/orders/:orderId?" element={<Orders />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Orders execution CTA live source guard (sourcesDetail.orders)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRefresh.mockResolvedValue(undefined);
  });

  it("enables Vezi Execuția when orders source is db but aggregate is mixed and plan exists", async () => {
    vi.spyOn(executionApi, "getObservability").mockResolvedValue({
      order_id: 1,
      order_code: "ORD-1781201059-1",
      status: "OK",
      reasons: [],
      has_order: true,
      has_plan: true,
      has_reality: false,
      plan_total_estimated_minutes: 120,
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

    renderOrderDetail(lockedOrderWithPlan, {
      source: "mixed",
      sourcesDetail: {
        intakes: "db",
        quotes: "db",
        orders: "db",
        materials: "db",
        suppliers: "db",
      },
    });

    const cta = await screen.findByTestId("order-view-execution-cta");
    expect(cta).not.toBeDisabled();
    expect(
      screen.queryByTestId("order-execution-live-source-warning")
    ).not.toBeInTheDocument();
    expect(await screen.findByTestId("order-execution-dispatch-panel")).toBeInTheDocument();
    expect(screen.getByTestId("order-execution-plan-exists")).toBeInTheDocument();
    expect(screen.queryByTestId("order-generate-execution-plan-action")).toBeNull();
    expect(screen.queryByTestId("order-open-execution-action")).toBeNull();
    expect(screen.getAllByTestId("order-view-execution-cta")).toHaveLength(1);

    fireEvent.click(cta);
    expect(mockNavigate).toHaveBeenCalledWith("/execution/1");
  });

  it("blocks execution navigation when orders source is not db", async () => {
    vi.spyOn(executionApi, "getObservability").mockResolvedValue({
      order_id: 1,
      order_code: "ORD-1781201059-1",
      status: "OK",
      reasons: [],
      has_order: true,
      has_plan: true,
      has_reality: false,
      plan_total_estimated_minutes: 120,
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

    renderOrderDetail(lockedOrderWithPlan, {
      source: "mixed",
      sourcesDetail: {
        quotes: "db",
        orders: "empty",
      },
    });

    await screen.findByTestId("order-execution-live-source-warning");
    expect(screen.queryByTestId("order-execution-dispatch-panel")).toBeNull();
    expect(screen.queryByTestId("order-view-execution-cta")).toBeNull();
  });

  it("shows generate plan CTA when live orders and no execution plan yet", async () => {
    vi.spyOn(executionApi, "getObservability").mockResolvedValue({
      order_id: 502,
      order_code: "ORD-NO-PLAN",
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

    renderOrderDetail(lockedOrderNoPlan, {
      source: "mixed",
      sourcesDetail: {
        orders: "db",
        quotes: "db",
      },
    });

    expect(await screen.findByTestId("order-execution-dispatch-panel")).toBeInTheDocument();
    expect(screen.getByTestId("order-execution-plan-missing")).toHaveTextContent(
      /Planul de execuție nu a fost generat/i
    );
    expect(screen.getByTestId("order-generate-execution-plan-action")).not.toBeDisabled();
    expect(screen.queryByTestId("order-view-execution-cta")).toBeNull();
    expect(screen.queryByTestId("order-open-execution-action")).toBeNull();
  });
});
