import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { OperatorTaskTruthResponse } from "@/api/operatorTaskTruth";
import { OperatorProductionReleaseSummary } from "./OperatorProductionReleaseSummary";
import { OperatorOwnerDecisionDetailsPanel } from "./OperatorOwnerDecisionDetailsPanel";

function blockedTruth(): OperatorTaskTruthResponse {
  return {
    contract_version: "operator_task_truth/v1",
    order_id: 23150,
    readiness_authority: "FROZEN_ORDER_SNAPSHOT_V2",
    production_release_policy: "ORDER_AND_PLAN_ALLOWED_TASK_START_BLOCKED",
    production_release_status: "RELEASE_BLOCKED_OWNER_DECISIONS",
    production_release_blocked: true,
    owner_decisions_summary: [
      {
        code: "INTERNAL_SABLON_FOREX_COST",
        label: "Cost șablon Forex — decizie owner necesară înainte de producție",
        category: "production_blocking",
        blocking: true,
        frozen_status: "present",
        operational_status: "unresolved",
        scope: "order",
        required_action: "resolve_owner_decision",
        acknowledgement_sufficient: false,
        requires_resolution: true,
        can_resolve: false,
        has_resolution_note: false,
      },
      {
        code: "INTERNAL_AMBALARE_RULE",
        label: "Regulă ambalare — analiză internă",
        category: "nonblocking_internal_analysis",
        blocking: false,
        frozen_status: "present",
        operational_status: "unresolved",
        scope: "order",
        acknowledgement_sufficient: false,
        requires_resolution: false,
        can_resolve: false,
        has_resolution_note: false,
      },
    ],
    role_capabilities: {
      can_resolve_owner_decisions: false,
      can_view_internal_cost: false,
      can_view_owner_decision_notes: false,
    },
    tasks: [],
    generated_at: "2026-07-15T00:00:00Z",
    legacy_order: false,
  };
}

describe("Operator production blocker UI", () => {
  it("renders blocked order-level release strip", () => {
    render(<OperatorProductionReleaseSummary truth={blockedTruth()} />);
    expect(screen.getByTestId("operator-production-release-status")).toHaveTextContent(
      /Productie blocata/i,
    );
    expect(screen.getByTestId("operator-production-blocker-count")).toHaveTextContent(
      /decizie/i,
    );
  });

  it("lists blocking decisions before nonblocking section", () => {
    render(<OperatorOwnerDecisionDetailsPanel truth={blockedTruth()} defaultOpen />);
    expect(screen.getByTestId("owner-decisions-blocking-section")).toBeTruthy();
    expect(screen.getByTestId("owner-decisions-nonblocking-section")).toBeTruthy();
    expect(screen.getByTestId("owner-decision-row-INTERNAL_SABLON_FOREX_COST")).toBeTruthy();
    expect(screen.getByTestId("owner-decision-row-INTERNAL_AMBALARE_RULE")).toBeTruthy();
  });

  it("hides resolver note metadata for operator role", () => {
    render(<OperatorOwnerDecisionDetailsPanel truth={blockedTruth()} defaultOpen />);
    expect(screen.queryByText(/Nota rezolvare: prezenta/)).toBeNull();
    expect(screen.getAllByText(/nu este disponibila pentru rolul curent/i).length).toBeGreaterThan(0);
  });

  it("shows manager resolver metadata when allowed", () => {
    const managerTruth = {
      ...blockedTruth(),
      role_capabilities: {
        can_resolve_owner_decisions: true,
        can_view_internal_cost: true,
        can_view_owner_decision_notes: true,
      },
      owner_decisions_summary: blockedTruth().owner_decisions_summary.map((d) => ({
        ...d,
        can_resolve: d.blocking,
      })),
    };
    render(<OperatorOwnerDecisionDetailsPanel truth={managerTruth} defaultOpen />);
    expect(screen.getAllByText(/Poate rezolva:/).length).toBeGreaterThan(0);
  });
});
