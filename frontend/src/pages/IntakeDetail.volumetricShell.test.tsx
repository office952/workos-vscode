import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import IntakeDetail from "./IntakeDetail";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

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

vi.mock("@/api/intakeAssist", () => ({
  getMaterialSheetAssist: vi.fn().mockResolvedValue({
    status: "ok",
    data: { items: [], assist_available: false, blockers: [] },
  }),
  listProductTemplateAssist: vi.fn().mockResolvedValue({
    status: "ok",
    data: { items: [] },
  }),
  lookupFiscalProvider: vi.fn(),
  suggestProductTemplates: vi.fn().mockResolvedValue({
    status: "ok",
    data: { suggestions: [] },
  }),
}));

vi.mock("@/lib/api", () => ({
  intakesApi: {
    list: vi.fn().mockResolvedValue([]),
    update: vi.fn(),
  },
}));

vi.mock("@/components/workos/Product001IntakeSpecEditor", () => ({
  default: () => <div data-testid="product-form">Product spec editor</div>,
}));

vi.mock("@/components/workos/VolumetricLettersQuoteFlow", () => ({
  default: () => (
    <div data-testid="volumetric-quote-embedded">Quote simulation</div>
  ),
}));

const volumetricIntake = {
  id: "WI-SMOKE-P001",
  client: "TEST Product001 smoke",
  contactPerson: "Smoke Validator",
  channel: "email" as const,
  productFamily: "litere_volumetrice",
  description: "TEST Product001 smoke",
  dimensions: "",
  quantity: 1,
  status: "ready_for_quote" as const,
  assignedTo: "Smoke Validator",
  createdAt: "2026-06-01T00:00:00",
  updatedAt: "2026-06-01T00:00:00",
  notes: "",
  priority: "low" as const,
  deliveryType: "courier" as const,
  identity: { type: "temp" as const, tempRef: "TEMP-WI-SMOKE-P001" },
  confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
  productSpec: {
    width_mm: 4800,
    height_mm: 600,
    depth_mm: 60,
    letter_face_area_m2: 2.88,
    letter_perimeter_m: 18,
    letter_count: 9,
  },
  dbId: 1,
};

const totemIntake = {
  id: "WI-3320",
  client: "MOL",
  contactPerson: "Radu Ionescu",
  channel: "email" as const,
  productFamily: "Totemuri / Pyloni",
  description: "Totem LED",
  dimensions: "5000x800x400mm",
  quantity: 1,
  status: "in_review" as const,
  assignedTo: "Maria C.",
  createdAt: "2026-04-05T09:00:00",
  updatedAt: "2026-04-07T05:45:00",
  notes: "",
  priority: "high" as const,
  deliveryType: "delivery_install" as const,
  identity: { type: "fiscal" as const, tempRef: "TMP-1", cui: "14399840" },
  confirmedTemplateCode: null,
  dbId: 2,
};

function renderDetail(id: string) {
  return render(
    <MemoryRouter initialEntries={[`/intake/${id}`]}>
      <Routes>
        <Route path="/intake/:id" element={<IntakeDetail />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("IntakeDetail volumetric dedicated shell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBackendData.mockReturnValue({
      intakes: [volumetricIntake],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
  });

  it("routes confirmed TPL-VOLUMETRIC-LETTERS to VolumetricLettersIntakePage", async () => {
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-intake-page")).toBeInTheDocument();
    });
  });

  it("renders compact request context", async () => {
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-request-context")).toBeInTheDocument();
    });
    const context = screen.getByTestId("volumetric-request-context");
    expect(context).toHaveTextContent("TEST Product001 smoke");
    expect(context).toHaveTextContent("Smoke Validator");
  });

  it("renders Product001IntakeSpecEditor", async () => {
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(screen.getByTestId("product-form")).toBeInTheDocument();
    });
  });

  it("hides BackendAssistSection after template confirmation", async () => {
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-intake-page")).toBeInTheDocument();
    });
    expect(
      screen.queryByText(/Asistență Intake — Contract Backend/i)
    ).not.toBeInTheDocument();
  });

  it("shows terrain N/A for courier delivery", async () => {
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(screen.getByTestId("terrain-na")).toBeInTheDocument();
    });
    expect(screen.getByTestId("terrain-na")).toHaveTextContent(/Teren:.*N\/A/i);
  });

  it("does not render totem macara fields on volumetric courier path", async () => {
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-intake-page")).toBeInTheDocument();
    });
    expect(screen.queryByText(/macara/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Tip suprafață montaj/i)).not.toBeInTheDocument();
  });

  it("shows terrain section for install delivery", async () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        {
          ...volumetricIntake,
          deliveryType: "delivery_install" as const,
        },
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(document.getElementById("intake-section-terrain")).toBeTruthy();
    });
    expect(screen.queryByTestId("terrain-na")).not.toBeInTheDocument();
  });

  it("renders unified workspace tabs", async () => {
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-workspace-tabs")).toBeInTheDocument();
    });
    expect(screen.getByTestId("volumetric-tab-spec")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-tab-quote")).toBeInTheDocument();
  });

  it("embeds VolumetricLettersQuoteFlow on quote tab without /quotes navigation", async () => {
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-tab-quote")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("volumetric-tab-quote"));
    expect(screen.getByTestId("volumetric-quote-panel")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-quote-embedded")).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalledWith("/quotes", expect.anything());
  });

  it("hides CUI identity section as primary workflow", async () => {
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-intake-page")).toBeInTheDocument();
    });
    expect(screen.queryByText(/Identificare Client/i)).not.toBeInTheDocument();
  });

  it("shows status conflict warning when stored status is ahead", async () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        {
          ...volumetricIntake,
          status: "ready_for_quote" as const,
          confirmedTemplateCode: null,
          productSpec: null,
        },
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderDetail("WI-SMOKE-P001");
    await waitFor(() => {
      expect(screen.getByTestId("status-readiness-conflict")).toBeInTheDocument();
    });
  });

  it("keeps generic path for non-volumetric intake", async () => {
    mockUseBackendData.mockReturnValue({
      intakes: [totemIntake],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderDetail("WI-3320");
    await waitFor(() => {
      expect(screen.queryByTestId("volumetric-intake-page")).not.toBeInTheDocument();
    });
    expect(screen.getByText(/Identificare Client/i)).toBeInTheDocument();
  });
});
