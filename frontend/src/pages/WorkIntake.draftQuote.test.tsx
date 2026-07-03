import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import WorkIntake from "./WorkIntake";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";
import type { IntakeRequest } from "@/lib/mockData";

const mockNavigate = vi.fn();
const mockUseBackendData = vi.fn();
const mockCreateDraftQuote = vi.fn();
const mockNavigateToQuoteDetail = vi.fn();

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
  createDraftQuoteFromIntake: (...args: unknown[]) => mockCreateDraftQuote(...args),
  updateIntakeStatus: vi.fn(),
}));

vi.mock("@/lib/intakePersistence", () => ({
  patchIntakeByCode: vi.fn(),
}));

vi.mock("@/lib/commercialSpineNavigation", () => ({
  navigateToQuoteDetail: (...args: unknown[]) => mockNavigateToQuoteDetail(...args),
}));

function baseIntake(overrides: Partial<IntakeRequest>): IntakeRequest {
  return {
    id: "IR-MQ51B998",
    client: "Client",
    contactPerson: "—",
    channel: "email",
    productFamily: "litere_volumetrice",
    description: "desc",
    dimensions: "5000x952",
    quantity: 1,
    status: "ready_for_quote",
    assignedTo: "operator",
    createdAt: "2026-06-07T00:00:00Z",
    updatedAt: "2026-06-07T00:00:00Z",
    notes: "ok",
    priority: "normal",
    deliveryType: "delivery_standard",
    identity: { type: "temp", tempRef: "TEMP-IR-MQ51B998" },
    confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
    ...overrides,
  };
}

describe("WorkIntake draft quote CTA", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBackendData.mockReturnValue({
      intakes: [baseIntake({})],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn().mockResolvedValue(undefined),
    });
  });

  it("creates draft quote and navigates to quote detail", async () => {
    mockCreateDraftQuote.mockResolvedValue({ ok: true, quoteCode: "QT-NEW-001" });

    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText("IR-MQ51B998"));
    fireEvent.click(screen.getByTestId("work-intake-create-draft-quote"));

    await waitFor(() => {
      expect(mockCreateDraftQuote).toHaveBeenCalled();
      expect(mockNavigateToQuoteDetail).toHaveBeenCalledWith(
        mockNavigate,
        "QT-NEW-001"
      );
    });
  });

  it("opens existing draft when backend reports duplicate", async () => {
    mockCreateDraftQuote.mockResolvedValue({
      ok: true,
      quoteCode: "QT-EXISTING-001",
      openedExisting: true,
    });

    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText("IR-MQ51B998"));
    fireEvent.click(screen.getByTestId("work-intake-create-draft-quote"));

    await waitFor(() => {
      expect(mockNavigateToQuoteDetail).toHaveBeenCalledWith(
        mockNavigate,
        "QT-EXISTING-001"
      );
    });
  });

  it("shows controlled error when draft creation fails", async () => {
    mockCreateDraftQuote.mockResolvedValue({
      ok: false,
      error: "IntakeRequest status invalid",
    });

    render(
      <MemoryRouter>
        <WorkIntake />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText("IR-MQ51B998"));
    fireEvent.click(screen.getByTestId("work-intake-create-draft-quote"));

    await waitFor(() => {
      expect(screen.getByTestId("work-intake-draft-quote-error")).toHaveTextContent(
        /status invalid/i
      );
    });
    expect(mockNavigateToQuoteDetail).not.toHaveBeenCalled();
  });
});
