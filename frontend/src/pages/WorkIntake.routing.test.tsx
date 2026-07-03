import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import WorkIntake from "./WorkIntake";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";
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

describe("WorkIntake list selection and routing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBackendData.mockReturnValue({
      intakes: [],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });
  });

  it("selects request on card click and shows detail panel without navigating", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "WI-E2E-COMMERCIAL-WARN-001",
          client: "E2E Commercial Spine Client (WARN)",
          productFamily: "litere_volumetrice",
          confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
          status: "ready_for_quote",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });

    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    expect(
      screen.getByText("Selectează o cerere pentru detalii")
    ).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("work-intake-row-WI-E2E-COMMERCIAL-WARN-001"));

    expect(mockNavigate).not.toHaveBeenCalled();
    const panel = screen.getByTestId("work-intake-detail-panel");
    expect(
      within(panel).getByText("E2E Commercial Spine Client (WARN)")
    ).toBeInTheDocument();
    expect(within(panel).getByText("WI-E2E-COMMERCIAL-WARN-001")).toBeInTheDocument();
  });

  it("navigates to Intake V6 only via explicit primary edit button", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "IR-MQ47AGDG",
          productFamily: "litere_volumetrice",
          confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
          status: "in_review",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });

    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByTestId("work-intake-row-IR-MQ47AGDG"));
    expect(mockNavigate).not.toHaveBeenCalled();

    fireEvent.click(screen.getByTestId("work-intake-primary-edit"));

    expect(mockNavigate).toHaveBeenCalledWith("/intake-v6/IR-MQ47AGDG/operator");
    expect(
      screen.getByRole("button", { name: /Deschide Intake V6/i })
    ).toBeInTheDocument();
  });

  it("navigates to legacy intake only via explicit primary edit button", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "WI-3321",
          productFamily: "Casete Luminoase",
          status: "in_review",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });

    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByTestId("work-intake-row-WI-3321"));
    expect(mockNavigate).not.toHaveBeenCalled();

    fireEvent.click(screen.getByTestId("work-intake-primary-edit"));

    expect(mockNavigate).toHaveBeenCalledWith("/intake/WI-3321");
    expect(
      screen.getByRole("button", { name: /Instrumentează Comanda/i })
    ).toBeInTheDocument();
  });

  it("does not navigate when clicking chevron area on card (selection only)", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "IR-CHEVRON",
          client: "Chevron Client",
          productFamily: "litere_volumetrice",
          confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
          status: "in_review",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });

    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    const row = screen.getByTestId("work-intake-row-IR-CHEVRON");
    fireEvent.click(row);

    expect(mockNavigate).not.toHaveBeenCalled();
    expect(
      within(screen.getByTestId("work-intake-detail-panel")).getByRole("heading", {
        name: "Chevron Client",
      })
    ).toBeInTheDocument();
  });
});
