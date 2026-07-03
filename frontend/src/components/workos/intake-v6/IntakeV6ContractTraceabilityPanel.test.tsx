import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import IntakeV6ContractTraceabilityPanel from "./IntakeV6ContractTraceabilityPanel";

describe("IntakeV6ContractTraceabilityPanel", () => {
  it("shows current values and downstream impact for relevant bindings", () => {
    render(
      <IntakeV6ContractTraceabilityPanel
        loading={false}
        error={null}
        templateCode="TPL-VOLUMETRIC-LETTERS_v2"
        variant="review"
        source={{
          svg_source: { file_name: "letters.svg" },
          quote_geometry: { width_mm: 1200, letter_count: 8 },
          finish_setup: { mounting_system: "steel_bars" },
        }}
        contract={{
          summary: { template_code: "TPL-VOLUMETRIC-LETTERS_v2" },
          modules: [],
          trigger_alignments: [],
          valid_combinations: [],
          invalid_combinations: [],
          orphan_fields_audit: [],
          notes: [],
          field_bindings: [
            {
              canonical_key: "vector_file",
              workspace_path: "svg_source.file_name",
              label_ro: "Fișier SVG",
              required: true,
              field_role: "geometry_input",
              module_codes: ["geometry_svg"],
            },
            {
              canonical_key: "mounting_system",
              workspace_path: "finish_setup.mounting_system",
              label_ro: "Sistem montaj",
              required: true,
              field_role: "module_activation",
              module_codes: ["structura_suport"],
            },
          ],
          downstream_linkages: [
            {
              module_code: "geometry_svg",
              pricing_inputs: ["letter_count"],
              execution_task_outputs: [],
              inventory_material_roles: [],
            },
            {
              module_code: "structura_suport",
              pricing_inputs: ["premount_bar_linear_meter"],
              execution_task_outputs: ["premount_bar_preparation"],
              inventory_material_roles: ["MAT-PREMOUNT-BAR-STEEL"],
            },
          ],
        }}
      />,
    );

    expect(screen.getByTestId("intake-v6-contract-traceability-review")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-contract-traceability-value-vector_file")).toHaveTextContent("letters.svg");
    expect(screen.getByTestId("intake-v6-contract-traceability-value-mounting_system")).toHaveTextContent("steel_bars");
    expect(screen.getByTestId("intake-v6-contract-traceability-row-mounting_system")).toHaveTextContent(/pricing: 1/i);
    expect(screen.getByTestId("intake-v6-contract-traceability-row-mounting_system")).toHaveTextContent(/taskuri: 1/i);
    expect(screen.getByTestId("intake-v6-contract-traceability-row-mounting_system")).toHaveTextContent(/inventar: 1/i);
  });
});