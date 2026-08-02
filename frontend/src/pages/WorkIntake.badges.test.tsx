import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import WorkIntake from "./WorkIntake";
import type { IntakeRequest } from "@/lib/mockData";

const mockNavigate = vi.fn();
const mockUseBackendData = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>(
    "react-router-dom",
  );
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => mockUseBackendData(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    user: { role: "admin", name: "Test Admin" },
    isAuthenticated: true,
  }),
}));

vi.mock("@/components/workos/NewIntakeDialog", () => ({
  default: () => null,
}));

vi.mock("@/lib/dataStore", () => ({
  createDraftQuoteFromIntake: vi.fn(),
  updateIntakeStatus: vi.fn(),
}));

vi.mock("@/lib/intakePersistence", () => ({
  patchIntakeByCode: vi.fn(),
}));

vi.mock("@/lib/commercialSpineNavigation", () => ({
  navigateToQuoteDetail: vi.fn(),
}));

function baseIntake(overrides: Partial<IntakeRequest>): IntakeRequest {
  return {
    id: "IR-TEST",
    client: "Client",
    contactPerson: "—",
    channel: "email",
    productFamily: "",
    description: "desc",
    dimensions: "—",
    quantity: 1,
    status: "new",
    assignedTo: "—",
    createdAt: "2026-06-07T00:00:00Z",
    updatedAt: "2026-06-07T00:00:00Z",
    notes: "",
    priority: "normal",
    deliveryType: "delivery_standard",
    identity: { type: "temp", tempRef: "TEMP-IR-TEST" },
    ...overrides,
  };
}

function renderWorkIntake() {
  return render(
    <MemoryRouter>
      <WorkIntake />
    </MemoryRouter>,
  );
}

describe("WorkIntake design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders without crashing and shows SourceBadge for live db", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [baseIntake({ id: "WI-001" })],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });

    renderWorkIntake();
    expect(screen.getByText("Live DB")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Cereri" })).toBeInTheDocument();
  });

  it("shows Live DB (gol) when intakes source is empty", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [],
      loading: false,
      error: null,
      source: "empty",
      sourcesDetail: { intakes: "empty" },
      refresh: vi.fn(),
    });

    renderWorkIntake();
    expect(screen.getByText("Live DB (gol)")).toBeInTheDocument();
  });

  it("shows Mock Data when intakes source is mock", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [baseIntake({ id: "WI-MOCK" })],
      loading: false,
      error: null,
      source: "mock",
      sourcesDetail: { intakes: "mock" },
      refresh: vi.fn(),
    });

    renderWorkIntake();
    expect(screen.getByText("Mock Data")).toBeInTheDocument();
  });

  it("renders ready_for_quote intake status with emerald semantic badge", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "WI-READY",
          status: "ready_for_quote",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });

    renderWorkIntake();
    const row = screen.getByTestId("work-intake-row-WI-READY");
    const badge = within(row).getByText("Gata pt. Ofertă");
    expect(badge).toHaveAttribute("data-status-domain", "intake");
    expect(badge).toHaveAttribute("data-status-tone", "emerald");
  });

  it("renders needs_info intake status with amber semantic badge", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "WI-NEEDS",
          status: "needs_info",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });

    renderWorkIntake();
    const row = screen.getByTestId("work-intake-row-WI-NEEDS");
    const badge = within(row).getByText("Lipsă Info");
    expect(badge).toHaveAttribute("data-status-tone", "amber");
    expect(badge.className).toMatch(/amber/);
  });

  it("falls back safely for unknown intake status in list row", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "WI-UNK",
          status: "mystery_status" as IntakeRequest["status"],
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });

    expect(() => renderWorkIntake()).not.toThrow();
    const badge = screen.getByText("Mystery Status");
    expect(badge).toHaveAttribute("data-status-tone", "slate");
  });

  it("shows detail panel status badge after selecting a row", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "WI-DETAIL",
          status: "ready_for_quote",
          client: "Detail Client",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });

    renderWorkIntake();
    fireEvent.click(screen.getByTestId("work-intake-row-WI-DETAIL"));

    const detail = screen.getByTestId("work-intake-detail-panel");
    expect(detail).toBeInTheDocument();
    expect(detail).toHaveTextContent("Detail Client");
    expect(detail.querySelector('[data-status="ready_for_quote"]')).toBeTruthy();
  });
});
