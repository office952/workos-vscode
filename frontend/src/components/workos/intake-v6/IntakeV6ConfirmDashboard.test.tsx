import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import IntakeV6ConfirmDashboard from "./IntakeV6ConfirmDashboard";
import { buildIntakeV6ConfirmSummary } from "@/lib/intakeV6/intakeV6ConfirmSummary";

const basePayload = {
  finish_setup: {
    face_finish_type: "none",
    illuminated: false,
  },
} as Record<string, unknown>;

const materialBreakdown = {
  workspace_id: "ws",
  template_code: "TPL-VOLUMETRIC-LETTERS",
  breakdown_scope: "quote_estimate",
  stock_consumption: false,
  nesting_rows: [],
  material_rows: [],
  consumable_rows: [],
  totals: {},
  warnings: [],
} as never;

function renderDashboard(payload: Record<string, unknown>) {
  const summary = buildIntakeV6ConfirmSummary({
    payload,
    layerCount: 1,
    materialBreakdown,
    nestingPreview: null,
  });
  render(
    <IntakeV6ConfirmDashboard
      summary={summary}
      handoffPreview={null}
      fatalBlockers={[]}
      reviewWarnings={[]}
      nestingPreview={null}
    />,
  );
}

describe("IntakeV6ConfirmDashboard — F7E A-F4 ACM recap honesty", () => {
  it("does not render an ACM line when no ACM/support component exists", () => {
    renderDashboard(basePayload);
    expect(screen.queryByTestId("intake-v6-confirm-acm-inclusion")).not.toBeInTheDocument();
  });

  it("lists the ACM component with an honest 'not yet priced' state instead of silently omitting it", () => {
    renderDashboard({
      ...basePayload,
      product_composition_recommendation: {
        composition_items: [
          { component_role: "support_panel", template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" },
        ],
      },
    });

    const line = screen.getByTestId("intake-v6-confirm-acm-inclusion");
    expect(line).toHaveTextContent(/nu este încă inclus în ofertă/i);
  });

  it("lists the ACM component as actively priced when it contributes to the commercial preview", () => {
    renderDashboard({
      ...basePayload,
      finish_setup: {
        ...(basePayload.finish_setup as Record<string, unknown>),
        mounting_solution: { template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" },
        applied_content: "letters",
      },
      product_composition_recommendation: {
        composition_items: [
          { component_role: "support_panel", template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" },
        ],
      },
    });

    const line = screen.getByTestId("intake-v6-confirm-acm-inclusion");
    expect(line).toHaveTextContent(/inclus activ în ofertă/i);
  });
});
