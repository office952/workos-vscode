import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
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

const baseOrder: Order = {
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

function renderOrders(initialEntry = "/orders") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/orders/:orderId?" element={<Orders />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Orders design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRefresh.mockResolvedValue(undefined);
  });

  it("renders SourceBadge using sourcesDetail.orders over aggregate source", () => {
    mockUseBackendData.mockReturnValue({
      orders: [baseOrder],
      loading: false,
      error: null,
      source: "mixed",
      sourcesDetail: { orders: "db", quotes: "mock" },
      refresh: mockRefresh,
    });

    renderOrders();
    const badge = screen.getByText("Live DB");
    expect(badge).toHaveAttribute("data-source", "db");
    expect(badge).not.toHaveAttribute("data-source", "mixed");
  });

  it("renders Mock Data when orders source is mock", () => {
    mockUseBackendData.mockReturnValue({
      orders: [baseOrder],
      loading: false,
      error: null,
      source: "mock",
      sourcesDetail: { orders: "mock" },
      refresh: mockRefresh,
    });

    renderOrders();
    expect(screen.getByText("Mock Data")).toHaveAttribute("data-source", "mock");
  });

  it("empty live orders do not show mock/demo source badge", () => {
    mockUseBackendData.mockReturnValue({
      orders: [],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { orders: "db" },
      refresh: mockRefresh,
    });

    renderOrders();
    expect(screen.queryByText("Mock Data")).not.toBeInTheDocument();
    expect(screen.queryByText("Demo")).not.toBeInTheDocument();
    expect(screen.getByText("Live DB")).toBeInTheDocument();
  });

  it("renders order status badge with design-system domain and preserved RO label", () => {
    mockUseBackendData.mockReturnValue({
      orders: [{ ...baseOrder, status: "in_execution" }],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { orders: "db" },
      refresh: mockRefresh,
    });

    renderOrders();
    const badge = document.querySelector('[data-status="in_execution"][data-status-domain="order"]');
    expect(badge).toBeTruthy();
    expect(badge).toHaveTextContent("În Execuție");
    expect(badge).toHaveAttribute("data-status-tone", "emerald");
  });

  it("keeps execution CTA visible when plan exists on live orders source", async () => {
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

    mockUseBackendData.mockReturnValue({
      orders: [baseOrder],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { orders: "db" },
      refresh: mockRefresh,
    });

    renderOrders(`/orders/${baseOrder.id}`);
    const cta = await screen.findByTestId("order-view-execution-cta");
    expect(cta).not.toBeDisabled();

    fireEvent.click(cta);
    expect(mockNavigate).toHaveBeenCalledWith("/execution/1");
  });

  it("shows design-system status badge in selected order detail panel", () => {
    mockUseBackendData.mockReturnValue({
      orders: [baseOrder],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { orders: "db" },
      refresh: mockRefresh,
    });

    renderOrders();
    fireEvent.click(screen.getByText(baseOrder.id));

    const detail = screen.getByTestId("order-detail-selected");
    const badge = within(detail).getByText("Înghețat");
    expect(badge).toHaveAttribute("data-status-domain", "order");
    expect(badge).toHaveAttribute("data-status-tone", "violet");
  });
});
