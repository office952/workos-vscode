import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

const smokeIntake = {
  id: "WI-SMOKE-P001",
  client: "TEST Product001 smoke",
  contactPerson: "Smoke Validator",
  channel: "email" as const,
  productFamily: "litere_volumetrice",
  description: "TEST Product001 smoke - Work Intake prefill validation only",
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

function renderDetail() {
  return render(
    <MemoryRouter initialEntries={["/intake/WI-SMOKE-P001"]}>
      <Routes>
        <Route path="/intake/:id" element={<IntakeDetail />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("IntakeDetail visibility and routing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBackendData.mockReturnValue({
      intakes: [smokeIntake],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
  });

  it("renders unified volumetric workspace with tabs", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-workspace-tabs")).toBeInTheDocument();
    });
    expect(screen.getByTestId("volumetric-tab-spec")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-tab-quote")).toBeInTheDocument();
  });

  it("renders product form when confirmed_template_code is volumetric", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("product-form")).toBeInTheDocument();
    });
  });

  it("falls back to product form from product_family litere_volumetrice", async () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        {
          ...smokeIntake,
          confirmedTemplateCode: null,
        },
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("product-form")).toBeInTheDocument();
    });
  });

  it("shows embedded quote flow on quote tab", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-tab-quote")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("volumetric-tab-quote"));
    expect(screen.getByTestId("volumetric-quote-embedded")).toBeInTheDocument();
  });

  it("shows disabled mark-ready reasons when prerequisites missing", async () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        {
          ...smokeIntake,
          status: "in_review",
          assignedTo: "—",
        },
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("readiness-gate-panel")).toBeInTheDocument();
    });
    expect(screen.getByTestId("action-mark-ready")).toBeDisabled();
    expect(
      within(screen.getByTestId("readiness-gate-panel")).getByText(
        /Persoană asignată — lipsă/i
      )
    ).toBeInTheDocument();
    expect(screen.getByTestId("staged-readiness-groups")).toBeInTheDocument();
  });
});
