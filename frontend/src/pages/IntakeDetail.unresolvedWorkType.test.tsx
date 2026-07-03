import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import IntakeDetail from "./IntakeDetail";
import {
  STAGE0_INSTALL_NEUTRAL_NOTE,
  STAGE0_WORK_TYPE_GUIDANCE,
} from "@/lib/intakeGateStages";

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

vi.mock("@/api/productFamilies", () => ({
  productFamiliesApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 1,
          family_id: "litere_volumetrice",
          label: "Litere volumetrice",
          active: true,
        },
      ],
      total: 1,
      skip: 0,
      limit: 500,
    }),
  },
}));

vi.mock("@/lib/api", () => ({
  intakesApi: {
    list: vi.fn().mockResolvedValue([{ id: 99 }]),
    update: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock("@/components/workos/Product001IntakeSpecEditor", () => ({
  default: () => <div data-testid="product-form">Product spec editor</div>,
}));

const genericIntake = {
  id: "IR-GENERIC-TEST",
  client: "Generic Client",
  contactPerson: "—",
  channel: "email" as const,
  productFamily: "",
  description: "Draft generic unresolved",
  dimensions: "—",
  quantity: 1,
  status: "new" as const,
  assignedTo: "—",
  createdAt: "2026-06-07T00:00:00Z",
  updatedAt: "2026-06-07T00:00:00Z",
  notes: "",
  priority: "normal" as const,
  deliveryType: "delivery_standard" as const,
  identity: { type: "temp" as const, tempRef: "TEMP-IR-GENERIC-TEST" },
  productSpec: null,
  confirmedTemplateCode: null,
  confirmedTemplateName: null,
  siteAudit: null,
  dbId: 99,
};

const genericInstallIntake = {
  ...genericIntake,
  id: "IR-GENERIC-INSTALL",
  deliveryType: "delivery_install" as const,
};

function renderIntake(code: string) {
  render(
    <MemoryRouter initialEntries={[`/intake/${code}`]}>
      <Routes>
        <Route path="/intake/:id" element={<IntakeDetail />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("IntakeDetail unresolved generic draft", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBackendData.mockReturnValue({
      intakes: [genericIntake, genericInstallIntake],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
  });

  it("shows unresolved work type section instead of servicii_montaj label", () => {
    renderIntake("IR-GENERIC-TEST");

    expect(screen.getByTestId("unresolved-work-type-section")).toBeInTheDocument();
    expect(screen.getByTestId("unresolved-work-type-guidance")).toBeInTheDocument();
    expect(screen.getByText(/Tipul lucrării nu este ales încă/i)).toBeInTheDocument();
    expect(
      within(screen.getByTestId("unresolved-work-type-guidance")).getByText(
        STAGE0_WORK_TYPE_GUIDANCE
      )
    ).toBeInTheDocument();
    expect(screen.getByText("Nespecificat")).toBeInTheDocument();
    expect(screen.getByTestId("choose-work-type-cta")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Alege tip lucrare/i })).toBeInTheDocument();
    expect(screen.queryByTestId("intake-pathway-selector")).not.toBeInTheDocument();
    expect(screen.queryByTestId("vector-intake-fast-ask")).not.toBeInTheDocument();
    expect(screen.queryByText("servicii_montaj")).not.toBeInTheDocument();
    expect(screen.queryByText("Servicii montaj")).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-form")).not.toBeInTheDocument();
  });

  it("does not show terrain audit section", () => {
    renderIntake("IR-GENERIC-TEST");
    expect(screen.queryByTestId("intake-audit-teren-section")).not.toBeInTheDocument();
    expect(screen.queryByText(/Mergi la teren/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Teren:/i)).not.toBeInTheDocument();
  });

  it("does not show CUI/SmartBill identity panel", () => {
    renderIntake("IR-GENERIC-TEST");
    expect(screen.queryByTestId("intake-identity-section")).not.toBeInTheDocument();
    expect(screen.queryByText(/Identitate Fiscală/i)).not.toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/Introdu CUI/i)).not.toBeInTheDocument();
  });

  it("does not show quote handoff or action map blockers", () => {
    renderIntake("IR-GENERIC-TEST");
    expect(screen.queryByTestId("intake-action-summary")).not.toBeInTheDocument();
    expect(screen.queryByText(/Confirmă template/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Deschide ofertare preliminară/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Marchează Gata pt. Ofertă/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Template produs — neconfirmat/i)).not.toBeInTheDocument();
  });

  it("shows neutral install note when delivery includes montaj", () => {
    renderIntake("IR-GENERIC-INSTALL");
    expect(screen.getByTestId("delivery-stage-note")).toBeInTheDocument();
    expect(screen.getByText(STAGE0_INSTALL_NEUTRAL_NOTE)).toBeInTheDocument();
    expect(
      screen.queryByText(/necesită audit teren complet/i)
    ).not.toBeInTheDocument();
  });

  it("opens work type picker on primary CTA click", async () => {
    renderIntake("IR-GENERIC-TEST");
    expect(screen.queryByTestId("work-type-picker")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("choose-work-type-cta"));
    expect(screen.getByTestId("unresolved-work-type-picker")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("work-type-picker")).toBeInTheDocument();
    });
  });
});
