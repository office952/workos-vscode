import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import type { OperatorTaskTruthResponse } from "@/api/operatorTaskTruth";
import { OperatorOwnerDecisionDetailsPanel } from "./OperatorOwnerDecisionDetailsPanel";

const resolveMock = vi.fn();

vi.mock("@/api/executionOwnerDecisionRelease", () => ({
  resolveOwnerDecision: (...args: unknown[]) => resolveMock(...args),
  RESOLUTION_NOTE_MIN_LENGTH: 3,
  resolutionErrorHeadline: (err: { message: string }) => err.message,
  OwnerDecisionResolutionError: class extends Error {},
}));

function managerBlockedTruth(): OperatorTaskTruthResponse {
  const blocking = [
    {
      code: "INTERNAL_SABLON_FOREX_COST",
      label: "Cost sablon Forex",
      category: "production_blocking",
      blocking: true,
      frozen_status: "present",
      operational_status: "unresolved",
      scope: "order",
      required_action: "resolve_owner_decision",
      acknowledgement_sufficient: false,
      requires_resolution: true,
      can_resolve: true,
      has_resolution_note: false,
    },
    {
      code: "INTERNAL_MONTAJ_RULE",
      label: "Regula montaj",
      category: "production_blocking",
      blocking: true,
      frozen_status: "present",
      operational_status: "unresolved",
      scope: "order",
      required_action: "resolve_owner_decision",
      acknowledgement_sufficient: false,
      requires_resolution: true,
      can_resolve: true,
      has_resolution_note: false,
    },
    {
      code: "INTERNAL_CONSUMABLES_RULE",
      label: "Regula consumabile",
      category: "production_blocking",
      blocking: true,
      frozen_status: "present",
      operational_status: "unresolved",
      scope: "order",
      required_action: "resolve_owner_decision",
      acknowledgement_sufficient: false,
      requires_resolution: true,
      can_resolve: true,
      has_resolution_note: false,
    },
  ];
  return {
    contract_version: "operator_task_truth/v1",
    order_id: 23150,
    readiness_authority: "FROZEN_ORDER_SNAPSHOT_V2",
    production_release_policy: "ORDER_AND_PLAN_ALLOWED_TASK_START_BLOCKED",
    production_release_status: "RELEASE_BLOCKED_OWNER_DECISIONS",
    production_release_blocked: true,
    owner_decisions_summary: [
      ...blocking,
      {
        code: "INTERNAL_AMBALARE_RULE",
        label: "Ambalare",
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
      can_resolve_owner_decisions: true,
      can_view_internal_cost: true,
      can_view_owner_decision_notes: true,
    },
    tasks: [],
    generated_at: "2026-07-15T00:00:00Z",
    legacy_order: false,
  };
}

describe("Operator owner decision resolution UI", () => {
  beforeEach(() => {
    resolveMock.mockReset();
  });

  it("shows resolve form for manager on blocking decisions only", () => {
    render(
      <OperatorOwnerDecisionDetailsPanel
        truth={managerBlockedTruth()}
        defaultOpen
        orderId={23150}
        onResolved={async () => {}}
      />,
    );
    expect(screen.getByTestId("owner-decision-resolve-form-INTERNAL_SABLON_FOREX_COST")).toBeTruthy();
    expect(screen.queryByTestId("owner-decision-resolve-form-INTERNAL_AMBALARE_RULE")).toBeNull();
  });

  it("operator truth has no resolve forms without mutation props", () => {
    const operatorTruth = {
      ...managerBlockedTruth(),
      role_capabilities: {
        can_resolve_owner_decisions: false,
        can_view_internal_cost: false,
        can_view_owner_decision_notes: false,
      },
      owner_decisions_summary: managerBlockedTruth().owner_decisions_summary.map((d) => ({
        ...d,
        can_resolve: false,
      })),
    };
    render(<OperatorOwnerDecisionDetailsPanel truth={operatorTruth} defaultOpen />);
    expect(screen.queryByTestId(/owner-decision-resolve-form-/)).toBeNull();
  });

  it("submits resolve endpoint with note and refreshes after success", async () => {
    const onResolved = vi.fn(async () => {});
    resolveMock.mockResolvedValue({
      order_id: 23150,
      code: "INTERNAL_SABLON_FOREX_COST",
      operational_status: "resolved",
      release_status: "RELEASE_BLOCKED_OWNER_DECISIONS",
      idempotent: false,
      audit_event_id: "odr-abc",
    });

    render(
      <OperatorOwnerDecisionDetailsPanel
        truth={managerBlockedTruth()}
        defaultOpen
        orderId={23150}
        onResolved={onResolved}
      />,
    );

    const note = screen.getByTestId("owner-decision-resolve-note-INTERNAL_SABLON_FOREX_COST");
    fireEvent.change(note, { target: { value: "Forex confirmat de manager." } });
    fireEvent.click(screen.getByTestId("owner-decision-resolve-submit-INTERNAL_SABLON_FOREX_COST"));

    await waitFor(() => {
      expect(resolveMock).toHaveBeenCalledWith(23150, "INTERNAL_SABLON_FOREX_COST", {
        status: "resolved",
        note: "Forex confirmat de manager.",
      });
      expect(onResolved).toHaveBeenCalled();
    });
  });

  it("disables submit until note meets backend minimum", () => {
    render(
      <OperatorOwnerDecisionDetailsPanel
        truth={managerBlockedTruth()}
        defaultOpen
        orderId={23150}
        onResolved={async () => {}}
      />,
    );
    const submit = screen.getByTestId(
      "owner-decision-resolve-submit-INTERNAL_SABLON_FOREX_COST",
    ) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);
    fireEvent.change(
      screen.getByTestId("owner-decision-resolve-note-INTERNAL_SABLON_FOREX_COST"),
      { target: { value: "ab" } },
    );
    expect(submit.disabled).toBe(true);
    fireEvent.change(
      screen.getByTestId("owner-decision-resolve-note-INTERNAL_SABLON_FOREX_COST"),
      { target: { value: "abc" } },
    );
    expect(submit.disabled).toBe(false);
  });
});
