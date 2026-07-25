import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { IntakeV6CncOperationDryRunCandidate } from "@/lib/intakeV6/intakeV6Api";
import IntakeV6CncOperationPreviewSection from "./IntakeV6CncOperationPreviewSection";

function cncCandidate(
  overrides: Partial<IntakeV6CncOperationDryRunCandidate> & Pick<IntakeV6CncOperationDryRunCandidate, "operation_key" | "title">,
): IntakeV6CncOperationDryRunCandidate {
  return {
    candidate_key: overrides.operation_key,
    title: overrides.title,
    operation_key: overrides.operation_key,
    operation_type: "cnc_cutting",
    quantity: overrides.quantity ?? 13.62,
    unit: overrides.unit ?? "linear_meter",
    passes: overrides.passes ?? 1,
    owner_pass_override: overrides.owner_pass_override ?? false,
    basis_label: overrides.basis_label ?? "Perimetru tăiere față",
    pricing_status: overrides.pricing_status ?? "missing_rate",
    mapping_gaps: overrides.mapping_gaps ?? [],
    consumes_stock_now: false,
    creates_task_now: false,
    source: "operation_rows",
    warnings: overrides.warnings ?? [],
    ...overrides,
  };
}

describe("IntakeV6CncOperationPreviewSection", () => {
  it("shows face cut and face bevel separately with operation_rows source", () => {
    render(
      <IntakeV6CncOperationPreviewSection
        cncTaskSource="operation_rows"
        compatMappingUsed={false}
        candidates={[
          cncCandidate({
            operation_key: "cnc_face_cutting_plexiglas_3mm",
            title: "Debitare CNC față plexiglas 3mm PMMA - opal",
          }),
          cncCandidate({
            operation_key: "cnc_face_bevel_plexiglas_3mm",
            title: "Șanfren CNC față plexiglas 3mm PMMA - opal",
          }),
        ]}
        testIdPrefix="test-cnc"
      />,
    );

    expect(screen.getByTestId("test-cnc-source")).toHaveTextContent("operation_rows");
    expect(screen.getByTestId("test-cnc-row-cnc_face_cutting_plexiglas_3mm")).toBeInTheDocument();
    expect(screen.getByTestId("test-cnc-row-cnc_face_bevel_plexiglas_3mm")).toBeInTheDocument();
    expect(screen.queryByText("sheet_nesting_role_split_quote_estimate")).not.toBeInTheDocument();
  });

  it("shows backing cut passes and ml-pass equivalent for Forex 10 mm", () => {
    render(
      <IntakeV6CncOperationPreviewSection
        cncTaskSource="operation_rows"
        candidates={[
          cncCandidate({
            operation_key: "cnc_backing_cutting_forex_10mm",
            title: "Debitare CNC spate Forex 10 mm",
            passes: 5,
            owner_pass_override: true,
            operation_equivalent_quantity: 68.1055,
          }),
        ]}
        testIdPrefix="test-cnc"
      />,
    );

    expect(screen.getByTestId("test-cnc-passes-cnc_backing_cutting_forex_10mm")).toHaveTextContent("5");
    expect(screen.getByTestId("test-cnc-equiv-cnc_backing_cutting_forex_10mm")).toHaveTextContent("68.11 m-pass");
  });

  it("shows missing-rate message not fake zero cost", () => {
    render(
      <IntakeV6CncOperationPreviewSection
        cncTaskSource="operation_rows"
        candidates={[
          cncCandidate({
            operation_key: "cnc_face_cutting_plexiglas_3mm",
            title: "Debitare CNC față plexiglas 3mm PMMA - opal",
            pricing_status: "missing_rate",
            estimated_cost: null,
          }),
        ]}
        testIdPrefix="test-cnc"
      />,
    );

    expect(screen.getByTestId("test-cnc-pricing-cnc_face_cutting_plexiglas_3mm")).toHaveTextContent(
      "Preț operație neconfigurat",
    );
    expect(screen.queryByText("0 EUR")).not.toBeInTheDocument();
  });
});