import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import VolumetricLettersQuoteFlow from "./VolumetricLettersQuoteFlow";
import { isVolumetricWorkIntakeHandoffCommercialMode } from "@/lib/volumetricQuoteFlowState";
import { computeCommercialPreviewBreakdown } from "@/lib/volumetricCommercialPreview";

const mockSimulate = vi.fn();
const mockPriceQuote = vi.fn();

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
    list: vi.fn().mockResolvedValue([{ id: 99, code: "IR-HANDOFF-001" }]),
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

function formatMoneyForTest(val: number, currency = "RON") {
  return `${val.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${currency}`;
}

const HANDOFF_SIMULATION_RESPONSE = {
  persisted: false,
  template_id: 1,
  template_code: "TPL-VOLUMETRIC-LETTERS",
  cost_engine_version: "test",
  status: "simulated",
  blockers: [],
  blocked_reasons: [],
  warnings: [],
  cost_result: { total_cost: 768.68 },
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
    price: { net: 960.85, gross: 1143.41, final: 1143.41 },
    pricing: { margin_pct: 25, vat_pct: 19, discount_pct: 0 },
  },
};

/** Spec that passes WorkIntake V2 verification stage (handoff ready). */
export const V2_HANDOFF_READY_SPEC: IntakeProductSpec = {
  intake_input_pathway: "vector",
  text: "STORE",
  vector_file_name: "lleexxaa.svg",
  vector_file_selected_at: "2026-06-07T10:00:00Z",
  vector_file_size_bytes: 1200,
  vector_parse_status: "parsed",
  vector_analysis_status: "analyzed",
  vector_detected_layers: [
    {
      id: "l1",
      label: "Litere",
      element_count: 9,
      suggested_role: "letters",
      confirmed_role: "letters",
    },
  ],
  vector_detected_layer_count: 1,
  vector_primary_letters_layer_id: "l1",
  vector_primary_letters_layer_name: "Litere",
  vector_layer_mapping_confirmed: true,
  geometry_confirmed_for_file_name: "lleexxaa.svg",
  vector_geometry_analyzed: true,
  letter_perimeter_m: 18.58,
  letter_face_area_m2: 2.88,
  letter_count: 9,
  width_mm: 4800,
  height_mm: 600,
  return_depth_mm: 80,
  visual_chamfer_included: true,
  illumination_family: "front_lit",
  return_color: "white",
  return_finish_system: "standard",
  face_vinyl_enabled: false,
  lighting_system_type: "led_modules",
  led_module_power_w: 1.44,
  light_color: "warm",
  psu_configuration: [160, 160],
  psu_allocation_status: "ok",
  psu_total_capacity_watts: 320,
  required_psu_watts: 308.02,
  total_led_watts: 267.84,
  mounting_system: "direct_wall",
  mounting_template_enabled: true,
  mounting_template_area_m2: 2.88,
};

function renderHandoffFlow(
  spec: IntakeProductSpec = V2_HANDOFF_READY_SPEC,
  extra: { openedFromIntake?: boolean } = { openedFromIntake: true }
) {
  return render(
    <MemoryRouter>
      <VolumetricLettersQuoteFlow
        onClose={() => undefined}
        preferredTemplateCode="TPL-VOLUMETRIC-LETTERS"
        initialProductSpec={spec}
        initialClientName="Handoff Client"
        intakeRequestId="IR-HANDOFF-001"
        intakeDbId={99}
        openedFromIntake={extra.openedFromIntake ?? true}
      />
    </MemoryRouter>
  );
}

describe("isVolumetricWorkIntakeHandoffCommercialMode", () => {
  it("is true for V2-ready spec opened from intake", () => {
    expect(
      isVolumetricWorkIntakeHandoffCommercialMode({
        openedFromIntake: true,
        templateCode: "TPL-VOLUMETRIC-LETTERS",
        productSpec: V2_HANDOFF_READY_SPEC,
      })
    ).toBe(true);
  });

  it("is false when opened directly without intake", () => {
    expect(
      isVolumetricWorkIntakeHandoffCommercialMode({
        openedFromIntake: false,
        templateCode: "TPL-VOLUMETRIC-LETTERS",
        productSpec: V2_HANDOFF_READY_SPEC,
      })
    ).toBe(false);
  });

  it("is false for incomplete intake spec even when openedFromIntake", () => {
    expect(
      isVolumetricWorkIntakeHandoffCommercialMode({
        openedFromIntake: true,
        templateCode: "TPL-VOLUMETRIC-LETTERS",
        productSpec: { width_mm: 1000, height_mm: 500 },
      })
    ).toBe(false);
  });
});

describe("VolumetricLettersQuoteFlow handoff commercial mode", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSimulate.mockResolvedValue(HANDOFF_SIMULATION_RESPONSE);
    mockPriceQuote.mockResolvedValue({
      quote_id: 42,
      quote_code: "Q-HANDOFF-001",
      snapshot: HANDOFF_SIMULATION_RESPONSE.snapshot,
    });
  });

  it("hides method selector and shows handoff banner + spec panel", async () => {
    renderHandoffFlow();
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-handoff-commercial-banner")).toBeInTheDocument();
    });
    expect(screen.queryByText("Cum vrei să calculezi?")).not.toBeInTheDocument();
    expect(screen.getByTestId("volumetric-handoff-spec-panel")).toBeInTheDocument();
    expect(
      screen.getByText("Specificație confirmată în WorkIntake V2")
    ).toBeInTheDocument();
  });

  it("shows multi-unit PSU plan and hides main PSU dropdown", async () => {
    renderHandoffFlow();
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-handoff-psu-plan")).toBeInTheDocument();
    });
    const psuPanel = screen.getByTestId("volumetric-handoff-psu-plan");
    expect(within(psuPanel).getByText("2 × 160 W")).toBeInTheDocument();
    expect(screen.queryByTestId("volumetric-psu-select-field")).not.toBeInTheDocument();
    expect(screen.getByTestId("volumetric-handoff-psu-costengine-note")).toBeInTheDocument();
  });

  it("does not show editable geometry fields by default", async () => {
    renderHandoffFlow();
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-handoff-spec-panel")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("volumetric-geometry-fields")).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue("4800")).not.toBeInTheDocument();
  });

  it("keeps commercial pricing fields editable", async () => {
    renderHandoffFlow();
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-commercial-pricing")).toBeInTheDocument();
    });
    const margin = screen.getByDisplayValue("25");
    expect(margin).not.toHaveAttribute("readOnly");
    fireEvent.change(margin, { target: { value: "30" } });
    expect(screen.getByDisplayValue("30")).toBeInTheDocument();
  });

  it("uses clarified commercial pricing labels", async () => {
    renderHandoffFlow();
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-commercial-pricing")).toBeInTheDocument();
    });
    expect(screen.getByText("Adaos comercial %")).toBeInTheDocument();
    expect(screen.queryByText("Marjă %")).not.toBeInTheDocument();
    expect(screen.getByText("Cost estimat producție")).toBeInTheDocument();
    expect(screen.queryByText("Total estimat")).not.toBeInTheDocument();
  });

  it("shows commercial preview breakdown after simulation", async () => {
    renderHandoffFlow();
    await waitFor(() => {
      expect(screen.getByTestId("action-calculate-preliminary")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("action-calculate-preliminary"));

    await waitFor(() => {
      expect(screen.getByTestId("volumetric-commercial-preview-breakdown")).toBeInTheDocument();
    });

    const expected25 = computeCommercialPreviewBreakdown({
      productionCost: 768.68,
      marginPct: 25,
      discountPct: 0,
      vatPct: 19,
    });
    expect(screen.getByTestId("volumetric-preview-total-with-vat")).toHaveTextContent(
      formatMoneyForTest(expected25!.totalWithVat)
    );
    expect(screen.getByTestId("volumetric-preview-vat")).toHaveTextContent("19");
  });

  it("updates preview total when margin changes from 25% to 50%", async () => {
    renderHandoffFlow();
    await waitFor(() => {
      expect(screen.getByTestId("action-calculate-preliminary")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("action-calculate-preliminary"));
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-preview-total-with-vat")).toBeInTheDocument();
    });

    const totalAt25 = computeCommercialPreviewBreakdown({
      productionCost: 768.68,
      marginPct: 25,
      discountPct: 0,
      vatPct: 19,
    })!.totalWithVat;

    fireEvent.change(screen.getByDisplayValue("25"), { target: { value: "50" } });

    await waitFor(() => {
      const totalAt50 = computeCommercialPreviewBreakdown({
        productionCost: 768.68,
        marginPct: 50,
        discountPct: 0,
        vatPct: 19,
      })!.totalWithVat;
      expect(totalAt50).toBeGreaterThan(totalAt25);
      expect(screen.getByTestId("volumetric-preview-total-with-vat")).toHaveTextContent(
        formatMoneyForTest(totalAt50)
      );
    });
  });

  it("shows discount lines when discount is greater than zero", async () => {
    renderHandoffFlow();
    await waitFor(() => {
      expect(screen.getByTestId("action-calculate-preliminary")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("action-calculate-preliminary"));
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-commercial-preview-breakdown")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("volumetric-preview-discount")).not.toBeInTheDocument();

    fireEvent.change(screen.getByDisplayValue("0"), { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByTestId("volumetric-preview-discount")).toBeInTheDocument();
      expect(screen.getByTestId("volumetric-preview-subtotal")).toBeInTheDocument();
    });

    const preview = computeCommercialPreviewBreakdown({
      productionCost: 768.68,
      marginPct: 25,
      discountPct: 10,
      vatPct: 19,
    });
    expect(screen.getByTestId("volumetric-preview-subtotal")).toHaveTextContent(
      formatMoneyForTest(preview!.subtotalBeforeVat)
    );
  });

  it("keeps quote creation payload fields unchanged", async () => {
    renderHandoffFlow();
    await waitFor(() => {
      expect(screen.getByTestId("action-calculate-preliminary")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("action-calculate-preliminary"));
    await waitFor(() => {
      expect(screen.getByText("Creează ofertă comercială")).toBeEnabled();
    });

    fireEvent.click(screen.getByText("Creează ofertă comercială"));

    await waitFor(() => {
      expect(mockPriceQuote).toHaveBeenCalled();
    });

    const payload = mockPriceQuote.mock.calls[0]?.[0] as {
      pricing?: { margin_pct?: number; vat_pct?: number; discount_pct?: number };
    };
    expect(payload.pricing).toEqual({
      margin_pct: 25,
      vat_pct: 19,
      discount_pct: 0,
    });
  });

  it("advanced override is collapsed and requires reason before edits", async () => {
    renderHandoffFlow();
    await waitFor(() => {
      expect(screen.getByTestId("volumetric-advanced-technical-override")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("volumetric-technical-override-warning")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("volumetric-technical-override-toggle"));
    expect(screen.getByTestId("volumetric-technical-override-reason")).toBeInTheDocument();
    expect(screen.queryByTestId("volumetric-geometry-fields")).not.toBeInTheDocument();

    fireEvent.change(screen.getByTestId("volumetric-technical-override-reason"), {
      target: { value: "Ajustare comercială perimetru" },
    });
    expect(screen.getByTestId("volumetric-technical-override-warning")).toHaveTextContent(
      /nu actualizează automat WorkIntake V2/i
    );
    expect(screen.getByTestId("volumetric-geometry-fields")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-psu-select-field")).toBeInTheDocument();
  });
});

describe("VolumetricLettersQuoteFlow legacy direct open", () => {
  it("keeps method selector for direct open without handoff-ready spec", async () => {
    render(
      <MemoryRouter>
        <VolumetricLettersQuoteFlow
          onClose={() => undefined}
          preferredTemplateCode="TPL-VOLUMETRIC-LETTERS"
          initialProductSpec={{
            width_mm: 4800,
            height_mm: 600,
            return_depth_mm: 60,
            letter_face_area_m2: 2.88,
            letter_perimeter_m: 18,
            letter_count: 9,
          }}
          openedFromIntake={false}
        />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Cum vrei să calculezi?")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("volumetric-handoff-commercial-banner")).not.toBeInTheDocument();
    expect(screen.getByDisplayValue("4800")).toBeInTheDocument();
  });

  it("keeps legacy flow when openedFromIntake but spec not V2-ready", async () => {
    renderHandoffFlow(
      {
        width_mm: 4800,
        height_mm: 600,
        return_depth_mm: 80,
        letter_face_area_m2: 2.88,
        letter_perimeter_m: 18,
        letter_count: 9,
        selected_psu_watts: 100,
      },
      { openedFromIntake: true }
    );
    await waitFor(() => {
      expect(screen.getByText("Cum vrei să calculezi?")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("volumetric-handoff-spec-panel")).not.toBeInTheDocument();
  });
});
