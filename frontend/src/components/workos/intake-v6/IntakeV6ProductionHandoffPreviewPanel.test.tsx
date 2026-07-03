import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { IntakeV6ProductionHandoffPreviewResponse } from "@/lib/intakeV6/intakeV6Api";
import IntakeV6ProductionHandoffPreviewPanel from "./IntakeV6ProductionHandoffPreviewPanel";

function previewWithJobs(): IntakeV6ProductionHandoffPreviewResponse {
  return {
    workspace_id: "ws-test",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    handoff_mode: "preview_only",
    stock_consumption: false,
    creates_execution_tasks: false,
    creates_stock_reservations: false,
    quote_estimate_only: true,
    production_notes: [],
    material_jobs: [
      {
        job_key: "return_profile_material",
        display_name: "Cant / volum calculat",
        quantity_basis: "perimeter_with_waste",
        quantity: 15.47,
        priced_quantity: 18.56,
        waste_percent: 20,
        unit: "ml",
        source: "intake_v6_material_breakdown",
        confidence: "estimate_fallback_perimeter",
        creates_stock_reservation: false,
        quote_estimate_only: true,
        warnings: [],
      },
      {
        job_key: "led_modules_install",
        display_name: "Module LED",
        quantity_basis: "led_modules_perimeter_pitch_estimate",
        quantity: 47,
        unit: "buc",
        source: "intake_v6_material_breakdown",
        confidence: "estimate_formula",
        creates_stock_reservation: false,
        quote_estimate_only: true,
        warnings: [],
      },
      {
        job_key: "psu_electrical",
        display_name: "Sursă LED 12V",
        quantity_basis: "psu_configuration_quote_estimate",
        quantity: 1,
        unit: "buc",
        source: "intake_v6_material_breakdown",
        confidence: "estimate_formula",
        creates_stock_reservation: false,
        quote_estimate_only: true,
        warnings: [],
      },
    ],
    operation_groups: [],
    task_seed_preview: [],
    blockers: [],
    warnings: [],
    summary: { material_jobs_count: 3 },
  };
}

describe("IntakeV6ProductionHandoffPreviewPanel", () => {
  it("shows operator-friendly basis labels instead of raw tokens", () => {
    render(<IntakeV6ProductionHandoffPreviewPanel preview={previewWithJobs()} loading={false} />);

    expect(screen.queryByText("perimeter_with_waste")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-handoff-basis-return_profile_material")).toHaveTextContent(
      "Cant / volum pentru preț (+20% pierdere)",
    );
    expect(screen.getByTestId("intake-v6-handoff-basis-led_modules_install")).toHaveTextContent(
      "Module LED — estimare după perimetru",
    );
    expect(screen.queryByText("led_modules_perimeter_pitch_estimate")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-handoff-basis-psu_electrical")).toHaveTextContent(
      "Sursă LED — estimare ofertă",
    );
    expect(screen.queryByText("psu_configuration_quote_estimate")).not.toBeInTheDocument();
  });

  it("keeps numeric quantities unchanged", () => {
    render(<IntakeV6ProductionHandoffPreviewPanel preview={previewWithJobs()} loading={false} />);
    expect(screen.getByText(/Module LED — 47 buc/)).toBeInTheDocument();
    expect(screen.getByText(/Sursă LED 12V — 1 buc/)).toBeInTheDocument();
    expect(screen.getByText(/15\.47 ml/)).toBeInTheDocument();
  });
});