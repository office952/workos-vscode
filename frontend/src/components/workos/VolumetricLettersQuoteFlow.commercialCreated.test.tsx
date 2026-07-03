import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import VolumetricLettersQuoteFlow from "./VolumetricLettersQuoteFlow";

const mockPriceQuote = vi.fn();
const mockSimulate = vi.fn();
const mockOnCreated = vi.fn();
const mockOnOpenCreatedQuote = vi.fn();

vi.mock("@/lib/api", () => ({
  productTemplatesApi: {
    list: vi.fn().mockResolvedValue([
      {
        id: 1,
        template_code: "TPL-VOLUMETRIC-LETTERS",
        name: "Litere volumetrice",
        active: true,
      },
    ]),
  },
  intakesApi: {
    list: vi.fn().mockResolvedValue([{ id: 99, code: "WI-E2E-LINK-001" }]),
  },
}));

vi.mock("@/lib/activeTemplateScope", () => ({
  filterActiveTemplatesForQuote: (rows: unknown[]) => rows,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE: "TPL-VOLUMETRIC-LETTERS",
}));

vi.mock("@/api/quotes", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/quotes")>();
  return {
    ...actual,
    priceQuote: (...args: unknown[]) => mockPriceQuote(...args),
  };
});

vi.mock("@/api/costSimulation", () => ({
  costSimulationApi: {
    simulate: (...args: unknown[]) => mockSimulate(...args),
  },
}));

const COMPLETE_VOLUMETRIC_SPEC: IntakeProductSpec = {
  text: "BT",
  width_mm: 4800,
  height_mm: 600,
  depth_mm: 80,
  return_depth_mm: 80,
  letter_face_area_m2: 2.88,
  letter_perimeter_m: 18,
  letter_count: 9,
  paint_tube_count: 3,
  selected_psu_watts: 100,
  mounting_system: "direct_wall",
  mounting_template_enabled: true,
  mounting_template_area_m2: 2.88,
  paint_ral_code: "RAL 9005",
  return_color: "white",
  face_vinyl_enabled: false,
  lighting_system_type: "led_strip",
  led_strip_density: "60_led_per_m",
  light_color: "warm",
  psu_configuration: [100],
};

function renderFlow() {
  return render(
    <MemoryRouter>
      <VolumetricLettersQuoteFlow
        onClose={() => undefined}
        onCreated={mockOnCreated}
        onOpenCreatedQuote={mockOnOpenCreatedQuote}
        preferredTemplateCode="TPL-VOLUMETRIC-LETTERS"
        initialProductSpec={COMPLETE_VOLUMETRIC_SPEC}
        initialClientName="Linkage Client"
        intakeRequestId="WI-E2E-LINK-001"
        intakeDbId={99}
        openedFromIntake
      />
    </MemoryRouter>
  );
}

describe("VolumetricLettersQuoteFlow commercial created UX", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSimulate.mockResolvedValue({
      persisted: false,
      template_id: 1,
      template_code: "TPL-VOLUMETRIC-LETTERS",
      cost_engine_version: "test",
      status: "simulated",
      blockers: [],
      blocked_reasons: [],
      warnings: [],
      cost_result: { total_cost: 800 },
      component_breakdown: [],
      trace: {
        source: "test",
        no_persist: true,
        used_template_snapshot: true,
        used_costengine_formulas: true,
        changed_entities: [],
      },
      readiness: {
        ready_for_quote: true,
        blockers: [],
        warnings: [],
        quote_gate: { can_create_commercial_quote: true },
      },
      snapshot: {
        price: { net: 1000, gross: 1190, final: 1190 },
        pricing: { margin_pct: 25, vat_pct: 19, discount_pct: 0 },
      },
    });
    mockPriceQuote.mockResolvedValue({
      quote_id: 501,
      quote_code: "Q-WI-LINK-001",
      snapshot: {
        price: { net: 1000, gross: 1190, final: 1190 },
        pricing: { margin_pct: 25, vat_pct: 19, discount_pct: 0 },
        status: "priced",
        blocked_reasons: [],
        cost_result: { total_cost: 800, breakdown: [] },
        product_definition: {},
      },
    });
  });

  it("shows quote code and Deschide oferta after commercial create", async () => {
    renderFlow();

    await waitFor(() => {
      expect(screen.getByText("Cum vrei să calculezi?")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Am geometria"));

    await waitFor(() => {
      expect(screen.getByTestId("action-calculate-preliminary")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("action-calculate-preliminary"));

    await waitFor(() => {
      expect(screen.getByText("Creează ofertă comercială")).toBeEnabled();
    });

    fireEvent.click(screen.getByText("Creează ofertă comercială"));

    await waitFor(() => {
      expect(screen.getByTestId("volumetric-commercial-created")).toBeInTheDocument();
    });

    expect(screen.getByText(/Q-WI-LINK-001/)).toBeInTheDocument();
    expect(mockOnCreated).toHaveBeenCalledWith({
      quoteId: 501,
      quoteCode: "Q-WI-LINK-001",
    });

    mockOnOpenCreatedQuote.mockClear();
    fireEvent.click(screen.getByTestId("volumetric-open-created-quote"));
    expect(mockOnOpenCreatedQuote).toHaveBeenCalledWith({
      quoteId: 501,
      quoteCode: "Q-WI-LINK-001",
    });
    expect(mockOnCreated).toHaveBeenCalledTimes(1);
  });

  it("falls back to onCreated when onOpenCreatedQuote is absent", async () => {
    render(
      <MemoryRouter>
        <VolumetricLettersQuoteFlow
          onClose={() => undefined}
          onCreated={mockOnCreated}
          preferredTemplateCode="TPL-VOLUMETRIC-LETTERS"
          initialProductSpec={COMPLETE_VOLUMETRIC_SPEC}
          initialClientName="Linkage Client"
          intakeRequestId="WI-E2E-LINK-001"
          intakeDbId={99}
          openedFromIntake
        />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Cum vrei să calculezi?")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Am geometria"));
    await waitFor(() => {
      expect(screen.getByTestId("action-calculate-preliminary")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("action-calculate-preliminary"));
    await waitFor(() => {
      expect(screen.getByText("Creează ofertă comercială")).toBeEnabled();
    });
    fireEvent.click(screen.getByText("Creează ofertă comercială"));
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-open-created-quote")).toBeInTheDocument();
    });

    mockOnCreated.mockClear();
    fireEvent.click(screen.getByTestId("volumetric-open-created-quote"));
    expect(mockOnCreated).toHaveBeenCalledWith({
      quoteId: 501,
      quoteCode: "Q-WI-LINK-001",
    });
  });

  it("does not call open handler before commercial quote is created", async () => {
    renderFlow();
    await waitFor(() => {
      expect(screen.getByText("Cum vrei să calculezi?")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("volumetric-open-created-quote")).not.toBeInTheDocument();
    expect(mockOnOpenCreatedQuote).not.toHaveBeenCalled();
  });
});
