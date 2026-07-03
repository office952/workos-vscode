import type { ComponentProps } from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import QuoteWizard from "./QuoteWizard";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

vi.mock("@/lib/api", () => ({
  productTemplatesApi: {
    list: vi.fn().mockResolvedValue([
      {
        id: 1,
        template_code: "TPL-VOLUMETRIC-LETTERS",
        name: "Litere volumetrice",
      },
      {
        id: 2,
        template_code: "TPL-ACP-LIGHT-ROUTED",
        name: "ACP Light",
      },
    ]),
  },
  intakesApi: {
    list: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock("@/lib/activeTemplateScope", () => ({
  filterActiveTemplatesForQuote: (rows: unknown[]) => rows,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE: "TPL-VOLUMETRIC-LETTERS",
}));

function renderWizard(
  props: Partial<ComponentProps<typeof QuoteWizard>> = {}
) {
  return render(
    <MemoryRouter>
      <QuoteWizard
        open
        onClose={() => undefined}
        preferredTemplateCode={TPL_VOLUMETRIC_LETTERS}
        initialProductSpec={{
          width_mm: 4800,
          height_mm: 600,
          return_depth_mm: 60,
          letter_face_area_m2: 2.88,
          letter_perimeter_m: 18,
          letter_count: 9,
        }}
        initialClientName="TEST Product001 smoke"
        intakeRequestId="WI-SMOKE-P001"
        openedFromIntake
        {...props}
      />
    </MemoryRouter>
  );
}

describe("QuoteWizard volumetric routing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders VolumetricLettersQuoteFlow for TPL-VOLUMETRIC-LETTERS", async () => {
    renderWizard();
    await waitFor(() => {
      expect(screen.getByText("Cum vrei să calculezi?")).toBeInTheDocument();
    });
    expect(screen.getByText("Pornesc de la vector")).toBeInTheDocument();
    expect(screen.getByText("Am geometria")).toBeInTheDocument();
    expect(screen.getByText("Estimare rapidă")).toBeInTheDocument();
  });

  it("shows Finisaje și folii with RAL return and Oracal 8500 face vinyl", async () => {
    renderWizard({
      initialProductSpec: {
        width_mm: 1200,
        height_mm: 400,
        return_depth_mm: 80,
        return_finish_system: "RAL",
        return_ral_code: "9010",
        return_ral_name: "Alb pur",
        return_ral_preview_hex: "#F7F9EF",
        face_vinyl_enabled: true,
        face_vinyl_series: "8500",
        face_vinyl_code: "010",
        face_vinyl_name: "White translucent",
        face_finish_type: "oracal_8500",
        letter_perimeter_m: 12,
        letter_face_area_m2: 2,
        letter_count: 8,
      },
    });
    await waitFor(() => {
      expect(screen.getByTestId("quote-finish-display")).toBeInTheDocument();
    });
    expect(screen.getByText("Finisaje și folii")).toBeInTheDocument();
    expect(screen.getByTestId("quote-finish-display-return-detail")).toHaveTextContent(/9010/);
    expect(screen.getByTestId("quote-finish-display-return-approx-note")).toBeInTheDocument();
    expect(screen.getByTestId("quote-finish-display-face-label")).toHaveTextContent(
      /8500 translucent/i
    );
    expect(screen.getByTestId("quote-finish-display-face-detail")).toHaveTextContent(/8500-010/);
  });

  it("renders generic wizard modal for non-volumetric template", async () => {
    render(
      <MemoryRouter>
        <QuoteWizard
          open
          onClose={() => undefined}
          preferredTemplateCode="TPL-ACP-LIGHT-ROUTED"
        />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Ofertă nouă")).toBeInTheDocument();
    });
    expect(screen.queryByText("Cum vrei să calculezi?")).not.toBeInTheDocument();
  });

  it("does not crash when productSpec is missing", async () => {
    renderWizard({ initialProductSpec: null });
    await waitFor(() => {
      expect(screen.getByText("Cum vrei să calculezi?")).toBeInTheDocument();
    });
  });

  it("shows intake geometry values in active fields", async () => {
    renderWizard();
    await waitFor(() => {
      expect(screen.getByDisplayValue("4800")).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue("600")).toBeInTheDocument();
    expect(screen.getAllByDisplayValue("2.88").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByDisplayValue("18")).toBeInTheDocument();
    expect(screen.getByDisplayValue("9")).toBeInTheDocument();
  });
});
