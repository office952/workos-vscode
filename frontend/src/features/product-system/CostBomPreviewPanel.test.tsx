import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CostBomPreviewPanel } from "@/features/product-system/CostBomPreviewPanel";

vi.mock("@/features/product-system/useCostBomPreviewData", () => ({
  useCostBomPreviewData: () => ({
    preview: {
      preview_version: "1.1.0",
      template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      bom_status: "partial",
      production_mode: "internal_production",
      source_context: {
        template_code: "TPL-VOLUMETRIC-LETTERS_v2",
        uses_parent_bom_as_structural_truth: false,
      },
      active_modules: [
        {
          module_code: "debitare_fata",
          state: "always_on",
          included_in_cost_bom: true,
        },
      ],
      inactive_modules: [],
      costable_components: [{}],
      costable_materials: [{}, {}],
      costable_operations: [{}],
      skipped_items: [{ item_type: "module", item_key: "electrica_logo", reason: "future_reserved", detail: "" }],
      missing_pricing: [{ item_type: "material", code: "MAT-X", reason: "missing" }],
      missing_geometry: ["sistem_led:selected_psu_watts"],
      pricing_blockers: [],
      missing_inventory_materials: [],
      unused_inventory_candidates: ["MAT-VINYL-PRINT"],
      legacy_inventory_references: [],
      externalization_requirements: [
        {
          code: "EXT_POWDER_COATING_RAL",
          label: "RAL",
          selected_now: false,
          production_mode: "external_service_possible",
          creates_external_task_now: false,
        },
      ],
      reseller_requirements: [{ product_code: "RESELL-X" }],
      warnings: ["TRIGGER_FIELD_MISMATCH"],
      notes: [],
    },
    status: "ready",
    error: null,
    isLoading: false,
  }),
}));

describe("CostBomPreviewPanel", () => {
  it("shows v2_aggregate source and read-only banner", () => {
    render(<CostBomPreviewPanel templateCode="TPL-VOLUMETRIC-LETTERS_v2" />);
    expect(screen.getByTestId("cost-bom-preview-panel")).toBeInTheDocument();
    expect(screen.getByTestId("cost-bom-read-only-banner")).toHaveTextContent(/Nu este quote priced/i);
    expect(screen.getByTestId("cost-bom-source-line")).toHaveTextContent(/source: v2_aggregate/);
    expect(screen.getByTestId("cost-bom-source-line")).toHaveTextContent(/aggregate_cost_source: true/);
    expect(screen.getByTestId("cost-bom-reprice-guard")).toHaveTextContent(/quote_reprice_allowed: false/i);
  });

  it("shows bom status and counts", () => {
    render(<CostBomPreviewPanel templateCode="TPL-VOLUMETRIC-LETTERS_v2" />);
    expect(screen.getByTestId("cost-bom-status")).toHaveTextContent("partial");
    expect(screen.getByTestId("cost-bom-counts")).toHaveTextContent("Costable materials");
  });

  it("shows externalization as metadata only", () => {
    render(<CostBomPreviewPanel templateCode="TPL-VOLUMETRIC-LETTERS_v2" />);
    expect(screen.getByTestId("cost-bom-externalization-metadata")).toHaveTextContent(/metadata only/i);
    expect(screen.getByTestId("cost-bom-externalization-metadata")).toHaveTextContent(/selected_now=false/i);
  });
});
