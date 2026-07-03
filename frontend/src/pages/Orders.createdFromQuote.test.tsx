import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Orders from "./Orders";
import type { Order } from "@/lib/mockData";
import { executionApi } from "@/api/execution";
import { operationalRegistryApi } from "@/api/operationalRegistry";

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

vi.mock("@/api/orders", () => ({
  getOrderDocumentSnapshotReference: vi.fn(async () => ({
    order_id: 99902,
    order_code: "ORD-1781588189-8",
    has_document_snapshot: false,
    reference: null,
  })),
}));

/** Shape captured from GET /api/v1/entities/orders?code=ORD-1781588189-8 */
const createdFromQuoteOrder: Order = {
  id: "ORD-1781588189-8",
  dbId: 99902,
  quoteId: "Q-1781588171",
  client: "SC SPALA VASELE SRL",
  contactPerson: "Operator",
  status: "locked",
  productSummary: "",
  totalAmount: 1412.15,
  createdAt: "2026-06-16T08:36:29.473136+00:00",
  lockedAt: "2026-06-16T08:36:29.473136+00:00",
  promisedDelivery: "",
  jobId: "",
  paymentStatus: "" as Order["paymentStatus"],
  snapshotVersion: 1,
  notes: "",
  readinessSnapshot: {
    source: "backend",
    snapshot_type: "product_readiness_at_order_acceptance",
    snapshot_at: "2026-06-16T08:36:29.473136+00:00",
    readiness_result: {
      entity_type: "blueprint",
      entity_id: "blueprint:6",
      overall_status: "needs_review",
      ready_for_quote: true,
      contract_version: "2026-05-15",
      policy: { authority: "backend" },
      source: "backend",
    },
    warnings_acknowledged: false,
  },
};

const intakeV6ConvertedOrder: Order = {
  id: "ORD-IV6-1782495298-11",
  dbId: 6,
  quoteId: "Q-V6-IV6-9E83BD8F-1782492520",
  client: "Unknown Client",
  contactPerson: "Operator",
  status: "locked",
  productSummary: "",
  totalAmount: 8698.6,
  createdAt: "2026-06-26T17:34:58.909400+00:00",
  lockedAt: "2026-06-26T17:34:58.909400+00:00",
  promisedDelivery: "",
  jobId: "",
  paymentStatus: "pending",
  snapshotVersion: 1,
  notes: "",
  readinessSnapshot: {
    source: "intake_v6_guarded_convert",
    snapshot_type: "intake_v6_accepted_quote_at_order_creation",
    snapshot_at: "2026-06-26T17:34:58.909400+00:00",
    quote_status: "accepted",
    requires_production_handoff_build: true,
    execution_plan_created: false,
    inventory_mutated: false,
    no_execution_plan_created: true,
  },
};

function renderOrderDetail(initialEntry = "/orders/ORD-1781588189-8") {
  mockUseBackendData.mockReturnValue({
    orders: [createdFromQuoteOrder],
    loading: false,
    error: null,
    source: "db",
    sourcesDetail: { orders: "db" },
    refresh: mockRefresh,
  });

  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/orders/:orderId?" element={<Orders />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Orders created from volumetric quote", () => {
  const mixedOrders: Order[] = [
    createdFromQuoteOrder,
    {
      ...createdFromQuoteOrder,
      id: "ORD-DEV-SFA-RUN",
      dbId: 99901,
      status: "in_production" as Order["status"],
      paymentStatus: "" as Order["paymentStatus"],
    },
  ];

  function renderOrdersList(initialEntry = "/orders/ORD-1781588189-8") {
    mockUseBackendData.mockReturnValue({
      orders: mixedOrders,
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { orders: "db" },
      refresh: mockRefresh,
    });

    return render(
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/orders/:orderId?" element={<Orders />} />
        </Routes>
      </MemoryRouter>
    );
  }

  beforeEach(() => {
    vi.clearAllMocks();
    mockRefresh.mockResolvedValue(undefined);

    vi.spyOn(executionApi, "getObservability").mockResolvedValue({
      order_id: 99902,
      order_code: "ORD-1781588189-8",
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
      observed_at: "2026-06-16T08:36:29.473136+00:00",
    });

    vi.spyOn(operationalRegistryApi, "listFieldInstallationTeams").mockResolvedValue({
      items: [],
      total: 0,
      installation_ref: "ORDER-99902",
    });
    vi.spyOn(operationalRegistryApi, "listActiveEmployees").mockResolvedValue({
      items: [
        {
          id: 1,
          name: "Calin Cimpean",
          status: "active",
          skill_codes: ["SK_FIELD_INSTALLER"],
          workcenter_codes: ["WC_FIELD_INSTALLATION"],
          resource_codes: [],
          employee_code: "EMP-001",
          email: null,
          phone: null,
          department: null,
          role: null,
          hire_date: null,
          notes: null,
        },
      ],
      total: 1,
    });
    vi.spyOn(operationalRegistryApi, "getOperationMapping").mockResolvedValue({
      operation_code: "field_installation",
      required_skill_codes: ["SK_FIELD_INSTALLER"],
      allowed_workcenter_codes: ["WC_FIELD_INSTALLATION"],
      allowed_resource_codes: [],
      authorization_mode: "hybrid",
      default_resource_code: null,
      product_system_aliases: [],
      authorized_employee_ids: [],
      notes: null,
    });
  });

  it("renders order detail without white screen for quote-converted locked order", async () => {
    mockUseBackendData.mockReturnValue({
      orders: [
        {
          ...createdFromQuoteOrder,
          totalAmount: 7060,
          baseCurrency: "RON",
          commercialCurrencyHandoff: {
            commercial_currency: "EUR",
            base_currency: "RON",
            commercial_total_eur: 1412,
            commercial_total_eur_raw: 1412.15,
            exchange_rate_eur_ron: 5,
            base_total_ron: 7060,
          },
        },
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { orders: "db" },
      refresh: mockRefresh,
    });

    render(
      <MemoryRouter initialEntries={["/orders/ORD-1781588189-8"]}>
        <Routes>
          <Route path="/orders/:orderId?" element={<Orders />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByTestId("order-detail-selected")).toBeInTheDocument();
    expect(screen.getByTestId("order-value-display")).toBeInTheDocument();
    expect(screen.getAllByText(/7\.060,00 RON/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/1\.412,00 EUR/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("ORD-1781588189-8").length).toBeGreaterThan(0);
    expect(screen.getAllByText("SC SPALA VASELE SRL").length).toBeGreaterThan(0);
    expect(screen.getByText(/needs_review/i)).toBeInTheDocument();
    expect(screen.getByTestId("order-execution-dispatch-panel")).toBeInTheDocument();
    expect(screen.getByTestId("order-document-governance-panel")).toBeInTheDocument();
  });

  it("renders mixed order list with legacy in_production status", async () => {
    mockUseBackendData.mockReturnValue({
      orders: [
        createdFromQuoteOrder,
        {
          ...createdFromQuoteOrder,
          id: "ORD-DEV-SFA-RUN",
          dbId: 99901,
          status: "in_production" as Order["status"],
        },
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { orders: "db" },
      refresh: mockRefresh,
    });

    render(
      <MemoryRouter initialEntries={["/orders/ORD-1781588189-8"]}>
        <Routes>
          <Route path="/orders/:orderId?" element={<Orders />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByTestId("order-detail-selected")).toBeInTheDocument();
    expect(screen.getByText("ORD-DEV-SFA-RUN")).toBeInTheDocument();
  });

  it("renders V6 converted order detail without legacy readiness_result shape", async () => {
    mockUseBackendData.mockReturnValue({
      orders: [intakeV6ConvertedOrder],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { orders: "db" },
      refresh: mockRefresh,
    });

    render(
      <MemoryRouter initialEntries={["/orders/ORD-IV6-1782495298-11"]}>
        <Routes>
          <Route path="/orders/:orderId?" element={<Orders />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByTestId("order-detail-selected")).toBeInTheDocument();
    expect(screen.getByText("ORD-IV6-1782495298-11")).toBeInTheDocument();
    expect(screen.getByText(/accepted/i)).toBeInTheDocument();
    expect(screen.getByText(/required/i)).toBeInTheDocument();
    expect(screen.getByText(/not created/i)).toBeInTheDocument();
    expect(screen.getByText(/not mutated/i)).toBeInTheDocument();
  });

  it("shows controlled not-found message for unknown order code", async () => {
    renderOrderDetail("/orders/ORD-DOES-NOT-EXIST");

    expect(await screen.findByTestId("order-not-found")).toBeInTheDocument();
    expect(screen.queryByTestId("order-detail-selected")).toBeNull();
  });

  it("shows pending payment badge when paymentStatus is empty string", async () => {
    renderOrderDetail();

    expect(await screen.findByTestId("order-detail-selected")).toBeInTheDocument();
    expect(screen.getAllByText("Neplătit").length).toBeGreaterThan(0);
  });

  it("survives employee without workcenter_codes in field installation panel", async () => {
    vi.spyOn(operationalRegistryApi, "listActiveEmployees").mockResolvedValue({
      items: [
        {
          id: 99,
          name: "No WC Employee",
          status: "active",
          skill_codes: ["SK_FIELD_INSTALLER"],
          workcenter_codes: undefined as unknown as string[],
          resource_codes: [],
          employee_code: "EMP-099",
          email: null,
          phone: null,
          department: null,
          role: null,
          hire_date: null,
          notes: null,
        },
      ],
      total: 1,
    });

    vi.spyOn(operationalRegistryApi, "createFieldInstallationTeam").mockResolvedValue({
      id: 1,
      installation_ref: "ORDER-99902",
      order_id: 99902,
      status: "draft",
      site_address: null,
      notes: null,
      member_count: 0,
      members: [],
      members_present: [],
      reporting_ready: false,
      started_at: null,
      ended_at: null,
      client_observations: null,
      completion_photos: [],
      warnings: [],
    });

    renderOrderDetail();
    expect(await screen.findByTestId("order-detail-selected")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Creează echipă montaj teren/i)).toBeInTheDocument();
    });
  });
});
