import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { TemplateCompositionAuthoringPanel } from "./TemplateCompositionAuthoringPanel";

vi.mock("@/api/productTemplateModuleLinks", () => ({
  productTemplateModuleLinksApi: {
    list: vi.fn(async () => ({
      items: [
        {
          id: 42,
          parent_template_id: 1,
          parent_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
          module_template_id: 2,
          module_template_code: "TPL-VOLUM-ALUMINIU_v1",
          relation_type: "required_child",
          trigger_field: "always",
          trigger_value_json: "{}",
          input_mapping_json: "{}",
          default_values_json: null,
          pricing_mode: "separate_quote_line",
          execution_mode: "linked_child_work",
          active: true,
          notes: null,
          usage_mode: "linked_child",
          instance_schema_id: null,
        },
      ],
      total: 1,
      skip: 0,
      limit: 500,
    })),
    update: vi.fn(),
    create: vi.fn(),
  },
}));

vi.mock("@/api/productTemplateComponentContracts", () => ({
  patchComponentContractLink: vi.fn(),
}));

describe("TemplateCompositionAuthoringPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lists composition links with aluminiu child visible", async () => {
    render(
      <TemplateCompositionAuthoringPanel
        parentTemplateCode="TPL-VOLUMETRIC-LETTERS_v2"
        parentTemplateId={1}
      />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("composition-link-42")).toHaveTextContent("TPL-VOLUM-ALUMINIU_v1");
    });
    expect(screen.getByTestId("composition-relation-42")).toBeTruthy();
  });
});
