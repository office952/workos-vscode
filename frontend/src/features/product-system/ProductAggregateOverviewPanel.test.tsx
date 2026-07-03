import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ProductAggregate } from "@/api/productAggregate";
import { ProductAggregateOverviewPanel } from "./ProductAggregateOverviewPanel";

const volumetricAggregate: ProductAggregate = {
  aggregate_version: "1.0.0",
  template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  template_id: 1,
  family_id: "litere_volumetrice",
  family_name: "Litere volumetrice",
  status: "active",
  business_name_ro: "Litere volumetrice luminoase",
  modules: {
    required: [
      {
        module_code: "modelare_cant",
        child_template_code: "TPL-VOLUM-ALUMINIU_v1",
        relation_type: "required_module",
      },
    ],
    optional: [
      {
        module_code: "structura_suport",
        child_template_code: "TPL-METAL-PREMOUNT-STRUCTURE_v1",
        relation_type: "optional_addon",
      },
    ],
  },
  components: [
    {
      component_id: "comp_face_litere",
      label_ro: "VIZUAL FAȚĂ",
      provenance: "dossier",
      source_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    },
    {
      component_id: "comp_lateral_litere",
      label_ro: "VOLUM ALUMINIU",
      provenance: "dossier",
      source_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    },
    {
      component_id: "comp_spate_litere",
      label_ro: "CAPAC SPATE",
      provenance: "dossier",
      source_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    },
    {
      component_id: "comp_led_litere",
      label_ro: "SISTEM LED",
      provenance: "dossier",
      source_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    },
    {
      component_id: "comp_finisaj_litere",
      label_ro: "FINISAJ",
      provenance: "dossier",
      source_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    },
  ],
  materials: [],
  operations: [],
  conflicts: [],
  warnings: [
    {
      code: "PARENT_COMPONENTS_EMPTY",
      severity: "warning",
      message: "Parent template has no direct components.",
    },
  ],
  provenance_summary: {
    parent: { components: 0, operations: 1, materials: 2 },
    dossier: { components: 5, operation_keys: 12, material_keys: 11 },
    linked_modules: { required: 1, optional: 1, child_templates: 2 },
    aggregate_totals: { components: 5, materials: 10, operations: 8 },
  },
};

describe("ProductAggregateOverviewPanel", () => {
  it("shows five aggregate components", () => {
    render(<ProductAggregateOverviewPanel aggregate={volumetricAggregate} />);
    expect(screen.getByTestId("aggregate-component-comp_face_litere")).toBeInTheDocument();
    expect(screen.getByTestId("aggregate-component-comp_finisaj_litere")).toBeInTheDocument();
    expect(screen.queryByText(/comp_auto_1/i)).not.toBeInTheDocument();
  });

  it("shows required and optional linked modules", () => {
    render(<ProductAggregateOverviewPanel aggregate={volumetricAggregate} />);
    expect(screen.getByTestId("aggregate-module-required-TPL-VOLUM-ALUMINIU_v1")).toBeInTheDocument();
    expect(screen.getByTestId("aggregate-module-optional-TPL-METAL-PREMOUNT-STRUCTURE_v1")).toBeInTheDocument();
  });

  it("shows PARENT_COMPONENTS_EMPTY warning", () => {
    render(<ProductAggregateOverviewPanel aggregate={volumetricAggregate} />);
    expect(screen.getByTestId("aggregate-warnings-PARENT_COMPONENTS_EMPTY")).toBeInTheDocument();
    expect(screen.getByTestId("aggregate-parent-empty-message")).toBeInTheDocument();
  });

  it("shows dossier provenance badge on a component", () => {
    render(<ProductAggregateOverviewPanel aggregate={volumetricAggregate} />);
    expect(screen.getAllByTestId("provenance-dossier").length).toBeGreaterThan(0);
  });

  it("shows fallback banner when aggregate unavailable", () => {
    render(
      <ProductAggregateOverviewPanel
        fallbackMessage="ProductAggregate unavailable; falling back to legacy template display."
        showLegacyFallbackNote
      />
    );
    expect(screen.getByTestId("product-aggregate-fallback-banner")).toBeInTheDocument();
  });
});

describe("productAggregateDisplay helpers", () => {
  it("prefers aggregate when draft only has comp_auto_1", async () => {
    const { shouldPreferAggregateDisplay } = await import("./productAggregateDisplay");
    const draftComponents = [
      {
        component_id: "comp_auto_1",
        type: "STRUCTURA" as const,
        name: "Componentă auto-generată (revizuiește)",
        operations: [],
        materials: [],
        _legacy: true,
        _needs_review: true,
      },
    ];
    expect(shouldPreferAggregateDisplay(draftComponents, volumetricAggregate)).toBe(true);
  });
});
