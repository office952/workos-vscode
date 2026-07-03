import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { TemplateDownstreamLinkagePanel } from "./TemplateDownstreamLinkagePanel";

vi.mock("@/lib/intakeV6/useModularFormContract", () => ({
  useModularFormContract: () => ({
    contract: {
      summary: {
        template_code: "TPL-VOLUMETRIC-LETTERS_v2",
        active_module_count: 2,
      },
      modules: [],
      field_bindings: [
        {
          canonical_key: "vector_file",
          workspace_path: "svg_source.file_name",
          label_ro: "Fișier SVG",
          field_role: "geometry_input",
          module_codes: ["geometry_svg"],
        },
        {
          canonical_key: "letter_count",
          workspace_path: "quote_geometry.letter_count",
          label_ro: "Număr litere",
          field_role: "geometry_input",
          module_codes: ["geometry_svg"],
        },
        {
          canonical_key: "mounting_system",
          workspace_path: "finish_setup.mounting_system",
          label_ro: "Sistem montaj",
          field_role: "module_activation",
          module_codes: ["structura_suport"],
        },
      ],
      trigger_alignments: [
        {
          module_code: "structura_suport",
          module_link_trigger_field: "metal_support_required",
          canonical_intake_field: "finish_setup.mounting_system",
        },
      ],
      downstream_linkages: [
        {
          module_code: "geometry_svg",
          inventory_material_roles: [],
          pricing_inputs: ["letter_perimeter_m"],
          execution_task_outputs: [],
          workcenter_routing_status: "linked",
          machine_linkage_status: "not_applicable",
          employee_assignment_status: "not_applicable",
        },
      ],
    },
    loading: false,
    error: null,
    templateCode: "TPL-VOLUMETRIC-LETTERS_v2",
  }),
}));

vi.mock("@/lib/activeTemplateScope", () => ({
  resolveRuntimeTemplateCode: (code: string | null | undefined) => code ?? "",
  isOwnerValidActiveTemplate: () => true,
}));

describe("TemplateDownstreamLinkagePanel", () => {
  it("shows step 1 svg analyzer bindings for intake-v6", () => {
    render(
      <TemplateDownstreamLinkagePanel
        templateCode="TPL-VOLUMETRIC-LETTERS_v2"
        variant="intake-v6"
      />,
    );

    expect(screen.getByTestId("template-downstream-linkage-intake-v6")).toBeInTheDocument();
    expect(screen.getByTestId("template-downstream-linkage-svg-bindings-intake-v6")).toHaveTextContent(/pasul 1/i);
    expect(screen.getByTestId("template-downstream-linkage-svg-binding-vector_file")).toHaveTextContent(/fișier svg/i);
    expect(screen.getByTestId("template-downstream-linkage-svg-binding-letter_count")).toHaveTextContent(/număr litere/i);
    expect(screen.getByTestId("template-downstream-linkage-trigger-structura_suport")).toHaveTextContent(/mounting_system/i);
    expect(screen.getByTestId("template-downstream-linkage-trigger-structura_suport")).toHaveTextContent(
      /Support and mounting are separate decisions/i,
    );
    expect(screen.getByTestId("template-downstream-linkage-trigger-structura_suport")).toHaveTextContent(
      /before Product Truth payload/i,
    );
  });
});