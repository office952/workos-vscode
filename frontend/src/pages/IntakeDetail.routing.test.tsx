import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import IntakeDetail from "./IntakeDetail";
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
    productSpec: null,
    confirmedTemplateCode: null,
    confirmedTemplateName: null,
    siteAudit: null,
    dbId: 1,
    ...overrides,
  };
}

function renderRoute(code: string) {
  render(
    <MemoryRouter initialEntries={[`/intake/${code}`]}>
      <Routes>
        <Route path="/intake/:id" element={<IntakeDetail />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("IntakeDetail routing states", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Not Found for missing intake", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderRoute("IR-MISSING");
    expect(screen.getByTestId("intake-not-found")).toBeInTheDocument();
    expect(
      screen.getByText(/nu există sau nu a fost găsită/i)
    ).toBeInTheDocument();
  });

  it("renders unresolved generic state for empty product_family without crashing on null dimensions", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "IR-TEST-GENERIC",
          productFamily: "",
          dimensions: null as unknown as string,
          description: "API test generic",
          client: "Test",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderRoute("IR-TEST-GENERIC");
    expect(screen.getByTestId("unresolved-work-type-section")).toBeInTheDocument();
    expect(screen.getByText("Nespecificat")).toBeInTheDocument();
    expect(screen.queryByTestId("product-form")).not.toBeInTheDocument();
  });

  it("routes litere_volumetrice intake to volumetric workspace", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "IR-MQ3C869E",
          productFamily: "litere_volumetrice",
          description: "Volumetric draft",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderRoute("IR-MQ3C869E");
    expect(screen.getByTestId("product-form")).toBeInTheDocument();
  });

  it("routes legacy family to generic detail without volumetric editor", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "WI-3321",
          productFamily: "Casete Luminoase",
          description: "Caseta luminoasa",
          dimensions: "3000x1000x150mm",
          status: "in_review",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderRoute("WI-3321");
    expect(screen.queryByTestId("product-form")).not.toBeInTheDocument();
    expect(screen.getByText("WI-3321")).toBeInTheDocument();
  });

  it("routes confirmed volumetric template to modular workspace", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "WI-SMOKE-P001",
          productFamily: "litere_volumetrice",
          confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
          status: "ready_for_quote",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderRoute("WI-SMOKE-P001");
    expect(screen.getByTestId("product-form")).toBeInTheDocument();
  });
});
