import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import WorkIntake from "./WorkIntake";
import type { IntakeRequest } from "@/lib/mockData";

const mockNavigate = vi.fn();
const mockUseBackendData = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>(
    "react-router-dom"
  );
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => mockUseBackendData(),
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

function baseIntake(index: number, overrides: Partial<IntakeRequest> = {}): IntakeRequest {
  const n = String(index).padStart(3, "0");
  return {
    id: `WI-PAGE-${n}`,
    client: `Client ${index}`,
    contactPerson: "—",
    channel: "email",
    productFamily: "litere_volumetrice",
    description: `Descriere ${index}`,
    dimensions: "100x100mm",
    quantity: 1,
    status: "in_review",
    assignedTo: "op",
    createdAt: "2026-06-07T00:00:00Z",
    updatedAt: "2026-06-07T00:00:00Z",
    notes: "note",
    priority: "normal",
    deliveryType: "delivery_standard",
    identity: { type: "temp", tempRef: `TEMP-WI-PAGE-${n}` },
    ...overrides,
  };
}

function mockManyIntakes(count: number) {
  return Array.from({ length: count }, (_, i) => baseIntake(i + 1));
}

describe("WorkIntake list pagination and sticky layout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBackendData.mockReturnValue({
      intakes: mockManyIntakes(39),
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });
  });

  it("renders sticky detail panel wrapper on large layout", () => {
    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    const panel = screen.getByTestId("work-intake-detail-panel");
    expect(panel.className).toMatch(/lg:sticky/);
    expect(panel.className).toMatch(/lg:max-h-\[calc\(100vh-2rem\)\]/);
    expect(panel.className).toMatch(/lg:overflow-y-auto/);
    expect(screen.getByTestId("work-intake-list-layout")).toBeInTheDocument();
  });

  it("shows first page subset and pagination labels for 39 requests", () => {
    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    expect(screen.getByTestId("work-intake-row-WI-PAGE-001")).toBeInTheDocument();
    expect(screen.getByTestId("work-intake-row-WI-PAGE-010")).toBeInTheDocument();
    expect(screen.queryByTestId("work-intake-row-WI-PAGE-011")).not.toBeInTheDocument();

    expect(screen.getByTestId("work-intake-pagination-range")).toHaveTextContent(
      "1–10 din 39"
    );
    expect(screen.getByTestId("work-intake-pagination-page")).toHaveTextContent(
      "Pagina 1 din 4"
    );
    expect(screen.getByTestId("work-intake-pagination-prev")).toBeDisabled();
    expect(screen.getByTestId("work-intake-pagination-next")).not.toBeDisabled();
  });

  it("navigates pages with Anterior and Următor", () => {
    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByTestId("work-intake-pagination-next"));
    expect(screen.getByTestId("work-intake-pagination-page")).toHaveTextContent(
      "Pagina 2 din 4"
    );
    expect(screen.getByTestId("work-intake-pagination-range")).toHaveTextContent(
      "11–20 din 39"
    );
    expect(screen.getByTestId("work-intake-row-WI-PAGE-011")).toBeInTheDocument();
    expect(screen.queryByTestId("work-intake-row-WI-PAGE-010")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("work-intake-pagination-prev"));
    expect(screen.getByTestId("work-intake-pagination-page")).toHaveTextContent(
      "Pagina 1 din 4"
    );
  });

  it("resets to page 1 when search filter changes", () => {
    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByTestId("work-intake-pagination-next"));
    expect(screen.getByTestId("work-intake-pagination-page")).toHaveTextContent(
      "Pagina 2 din 4"
    );

    fireEvent.change(screen.getByPlaceholderText(/caută client/i), {
      target: { value: "Client 1" },
    });

    expect(screen.getByTestId("work-intake-pagination-page")).toHaveTextContent(
      "Pagina 1 din"
    );
  });

  it("selects request on another page without navigating away", () => {
    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByTestId("work-intake-pagination-next"));
    fireEvent.click(screen.getByTestId("work-intake-row-WI-PAGE-015"));

    expect(mockNavigate).not.toHaveBeenCalled();
    const panel = screen.getByTestId("work-intake-detail-panel");
    expect(within(panel).getByRole("heading", { name: "Client 15" })).toBeInTheDocument();
  });

  it("clears selection when filtered results no longer include selected request", () => {
    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByTestId("work-intake-row-WI-PAGE-003"));
    expect(
      within(screen.getByTestId("work-intake-detail-panel")).getByRole("heading", {
        name: "Client 3",
      })
    ).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/caută client/i), {
      target: { value: "Client 99" },
    });

    expect(
      screen.getByText("Selectează o cerere pentru detalii")
    ).toBeInTheDocument();
  });
});
