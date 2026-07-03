import { describe, expect, it } from "vitest";
import {
  deriveAggregateCostSource,
  deriveCostPreviewSource,
  deriveParityStatus,
  isVolumetricAggregateTemplate,
  type CostBomPreview,
} from "@/api/costBomPreview";

function samplePreview(overrides: Partial<CostBomPreview> = {}): CostBomPreview {
  return {
    preview_version: "1.1.0",
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    bom_status: "ready",
    production_mode: "internal_production",
    source_context: {
      template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      uses_parent_bom_as_structural_truth: false,
    },
    active_modules: [],
    inactive_modules: [],
    costable_components: [],
    costable_materials: [],
    costable_operations: [],
    skipped_items: [],
    missing_pricing: [],
    missing_geometry: [],
    pricing_blockers: [],
    missing_inventory_materials: [],
    unused_inventory_candidates: [],
    legacy_inventory_references: [],
    externalization_requirements: [],
    reseller_requirements: [],
    warnings: [],
    notes: [],
    ...overrides,
  };
}

describe("costBomPreview helpers", () => {
  it("identifies volumetric v2 aggregate template", () => {
    expect(isVolumetricAggregateTemplate("TPL-VOLUMETRIC-LETTERS_v2")).toBe(true);
    expect(isVolumetricAggregateTemplate("TPL-OTHER")).toBe(false);
  });

  it("derives v2_aggregate source for volumetric v2", () => {
    expect(deriveCostPreviewSource("TPL-VOLUMETRIC-LETTERS_v2")).toBe("v2_aggregate");
    expect(deriveCostPreviewSource("TPL-OTHER")).toBe("legacy_or_other");
  });

  it("derives aggregate_cost_source from parent BOM flag", () => {
    expect(deriveAggregateCostSource(samplePreview())).toBe(true);
    expect(
      deriveAggregateCostSource(
        samplePreview({
          source_context: {
            template_code: "TPL-VOLUMETRIC-LETTERS_v2",
            uses_parent_bom_as_structural_truth: true,
          },
        }),
      ),
    ).toBe(false);
  });

  it("derives parity_status from bom_status and blockers", () => {
    expect(deriveParityStatus(samplePreview())).toBe("aligned");
    expect(deriveParityStatus(samplePreview({ bom_status: "partial" }))).toBe("partial");
    expect(deriveParityStatus(samplePreview({ bom_status: "blocked" }))).toBe("blocked");
    expect(
      deriveParityStatus(
        samplePreview({
          pricing_blockers: [
            {
              blocker_code: "MISSING_PRICE",
              item_type: "material",
              code: "MAT-X",
              reason: "missing",
            },
          ],
        }),
      ),
    ).toBe("partial");
  });
});
