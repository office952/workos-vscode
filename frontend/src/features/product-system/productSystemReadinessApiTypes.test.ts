import { describe, expect, it } from "vitest";
import type { ProductTemplateAvailabilityItem } from "@/lib/api";

function parseAvailabilityItem(raw: Record<string, unknown>): ProductTemplateAvailabilityItem {
  return raw as ProductTemplateAvailabilityItem;
}

describe("productSystemReadinessApiTypes", () => {
  it("parses additive readiness and capabilities fields", () => {
    const item = parseAvailabilityItem({
      template_id: 1,
      template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      db_active: true,
      quote_offerable: true,
      runtime_module: false,
      is_parent: true,
      has_modules: true,
      parent_codes: [],
      module_codes: [],
      status: "offerable",
      status_reason: "owner_valid_parent_template",
      product_system_role: "offerable_product",
      display_group: "active_products",
      importance_rank: 10,
      owner_decision_required: false,
      readiness_reason: "x",
      ui_label: "x",
      ui_description: "x",
      parent_product_codes: [],
      child_module_codes: [],
      shared_with_product_codes: [],
      composition_modules: [],
      shared_component_contracts: [],
      capabilities: {
        root_offerable: true,
        linked_child_offerable: false,
        internal_only: false,
      },
      readiness: {
        technical: { status: "TECHNICALLY_READY", blockers: [] },
        pricing: { status: "PRICING_INCOMPLETE", blockers: [] },
        execution: { status: "EXECUTION_INCOMPLETE", blockers: [] },
        commercial: { status: "OFFERABLE", blockers: [] },
        rollup: "BLOCKED",
      },
    });
    expect(item.readiness?.rollup).toBe("BLOCKED");
    expect(item.capabilities?.root_offerable).toBe(true);
  });

  it("tolerates unknown blocker codes without throwing", () => {
    const blockers = [
      {
        code: "FUTURE_BLOCKER_CODE",
        dimension: "pricing",
        severity: "blocking",
        owner: "pricing",
        message: "future",
      },
    ];
    expect(() =>
      parseAvailabilityItem({
        template_id: 1,
        template_code: "TPL-X",
        readiness: {
          technical: { status: "DRAFT", blockers },
          pricing: { status: "PRICING_INCOMPLETE", blockers },
          execution: { status: "EXECUTION_INCOMPLETE", blockers: [] },
          commercial: { status: "INTERNAL_ONLY", blockers: [] },
          rollup: "BLOCKED",
        },
      }),
    ).not.toThrow();
  });
});
