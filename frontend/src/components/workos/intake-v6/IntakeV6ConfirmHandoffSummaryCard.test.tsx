import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import IntakeV6ConfirmHandoffSummaryCard from "./IntakeV6ConfirmHandoffSummaryCard";
import type { IntakeV6QuoteHandoffPreviewResponse } from "@/lib/intakeV6/intakeV6Api";

function baseHandoff(
  overrides: Partial<IntakeV6QuoteHandoffPreviewResponse> = {},
): IntakeV6QuoteHandoffPreviewResponse {
  return {
    workspace_id: "ws-1",
    workspace_readiness_status: "ready_for_quote_preview",
    handoff_allowed: true,
    status_label: "HANDOFF_ALLOWED",
    blockers: [],
    can_create_internal_draft_quote: true,
    requires_operator_confirmation: false,
    operator_confirmation_complete: true,
    fatal_blockers: [],
    review_warnings: [],
    diagnostic_warnings: [],
    client_send_allowed: true,
    accept_allowed: true,
    convert_to_order_allowed: true,
    production_allowed: true,
    preview_only: true,
    ...overrides,
  };
}

describe("IntakeV6ConfirmHandoffSummaryCard", () => {
  it("shows diagnostic warnings in nonblocking technical section only", () => {
    render(
      <IntakeV6ConfirmHandoffSummaryCard
        handoffPreview={baseHandoff({
          diagnostic_warnings: [
            "canonical_unresolved_warning:DOSSIER_METADATA_ONLY: Blueprint dossier available for inspection only.",
          ],
          review_warnings: [
            "canonical_unresolved_warning:TRIGGER_FIELD_MISMATCH: metal_support_required vs mounting_system",
          ],
        })}
      />,
    );

    expect(screen.getByTestId("intake-v6-confirm-diagnostic-warnings-above-fold")).toBeInTheDocument();
    expect(screen.getByText(/Detalii tehnice \(nu blochează\)/i)).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-confirm-review-warnings-above-fold")).toBeInTheDocument();
    expect(screen.getByText(/Atenționări review/i)).toBeInTheDocument();
    expect(screen.getByText(/DOSSIER_METADATA_ONLY/i)).toBeInTheDocument();
    expect(screen.getByText(/TRIGGER_FIELD_MISMATCH/i)).toBeInTheDocument();
  });

  it("hides diagnostic section when empty", () => {
    render(<IntakeV6ConfirmHandoffSummaryCard handoffPreview={baseHandoff()} />);
    expect(screen.queryByTestId("intake-v6-confirm-diagnostic-warnings-above-fold")).not.toBeInTheDocument();
  });
});
