import { describe, expect, it } from "vitest";

import {
  buildOperatorBlockerBannerDisplay,
} from "./intakeV6OperatorBlockerBannerDisplay";
import { buildReviewHandoffSurfacing } from "./intakeV6QuoteHandoffReadiness";
import {
  buildIntakeV6OperatorPath,
  buildIntakeV6OperatorSearch,
} from "./intakeV6OperatorRoutes";
import { resolveIntakeV6ReviewTabs } from "./intakeV6ProductPlugin";

const onlyOperatorConfirmationHandoff = {
  workspace_id: "ws",
  handoff_allowed: false,
  can_create_internal_draft_quote: false,
  status_label: "QUOTE_HANDOFF_BLOCKED" as const,
  blockers: ["operator_confirmation_missing"],
  fatal_blockers: ["operator_confirmation_missing"],
  review_warnings: [],
  requires_operator_confirmation: true,
  operator_confirmation_complete: false,
  client_send_allowed: false,
  accept_allowed: false,
  convert_to_order_allowed: false,
  production_allowed: false,
  preview_only: true,
};

describe("step-scoped confirmation banner + Vector Logo copy", () => {
  it("Step 2 primary blocker count is 0 when only operator_confirmation_missing", () => {
    const surfacing = buildReviewHandoffSurfacing({
      handoff: onlyOperatorConfirmationHandoff,
      currentStep: "review",
    });
    const display = buildOperatorBlockerBannerDisplay({ surfacing });
    expect(display.show).toBe(false);
    expect(display.blockerCount).toBe(0);
    expect(display.summaryTitle).not.toMatch(/blochează Confirmarea/i);
  });

  it("technical diagnostics alone do not inflate Step 2 primary blocker count", () => {
    const surfacing = buildReviewHandoffSurfacing({
      handoff: {
        ...onlyOperatorConfirmationHandoff,
        handoff_allowed: true,
        can_create_internal_draft_quote: true,
        fatal_blockers: [],
        blockers: [],
        operator_confirmation_complete: true,
        diagnostic_warnings: [
          "canonical_unresolved_warning:DOSSIER_METADATA_ONLY: x",
          "canonical_unresolved_warning:TEMPLATE_IDENTITY: y",
        ],
      },
      currentStep: "review",
    });
    const display = buildOperatorBlockerBannerDisplay({ surfacing });
    expect(display.blockerCount).toBe(0);
  });

  it("Step 2 finisaje tab hint uses Vector Logo not artwork", () => {
    const tabs = resolveIntakeV6ReviewTabs("TPL-VOLUMETRIC-LETTERS_v2");
    const finisaje = tabs.find((tab) => tab.id === "finisaje");
    expect(finisaje?.hint).toMatch(/Vector Logo/i);
    expect(finisaje?.hint).not.toMatch(/artwork/i);
  });

  it("builds query strings without double-encoding", () => {
    const search = buildIntakeV6OperatorSearch({
      step: "confirm",
      hydrationProof: "final",
    });
    expect(search).toBe("?step=confirm&hydrationProof=final");
    expect(search).not.toMatch(/%3D|%26/);
    const path = buildIntakeV6OperatorPath("ws-1", "/intake-v6/operator");
    expect(`${path}${search}`).toBe(
      "/intake-v6/ws-1/operator?step=confirm&hydrationProof=final",
    );
  });

  it("rejects passing an entire query as a single search-param key", () => {
    // Characterization: wrong pattern that produced ?step%3Dconfirm%26hydrationProof%3Dfinal
    const wrong = new URLSearchParams();
    wrong.set("step=confirm&hydrationProof=final", "");
    expect(wrong.toString()).toMatch(/%3D|%26/);
    expect(buildIntakeV6OperatorSearch({ step: "confirm", hydrationProof: "final" })).not.toMatch(
      /%3D|%26/,
    );
  });
});
