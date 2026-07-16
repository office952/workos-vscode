import { describe, expect, it } from "vitest";

import {
  buildReviewHandoffSurfacing,
  collectArtworkUndecidedWarnings,
  formatQuoteHandoffBlocker,
  hasArtworkNeedsDecisionWarning,
  resolveQuoteHandoffUiStatus,
  resolveReviewReadinessDisplay,
  resolveWorkspaceSummaryBadgeLabel,
} from "./intakeV6QuoteHandoffReadiness";

describe("intakeV6QuoteHandoffReadiness", () => {
  it("formats Vector Logo undecided blocker", () => {
    expect(formatQuoteHandoffBlocker("artwork_execution_undecided:Layer_x0020_1")).toMatch(
      /Layer_x0020_1/,
    );
    expect(formatQuoteHandoffBlocker("artwork_execution_undecided:Layer_x0020_1")).toMatch(
      /Vector Logo/i,
    );
  });

  it("surfaces fetch failure instead of infinite loading", () => {
    const ui = resolveQuoteHandoffUiStatus(null, {
      loading: false,
      fetchError: "Failed to fetch",
    });
    expect(ui.label).toBe("Previzualizare handoff indisponibilă");
    expect(ui.debugLabel).toBe("HANDOFF_PREVIEW_UNAVAILABLE");
    expect(ui.tone).toBe("warn");
    expect(ui.handoffAllowed).toBe(false);
  });

  it("marks internal draft review state as handoff allowed with warning tone", () => {
    const ui = resolveQuoteHandoffUiStatus({
      workspace_id: "ws",
      handoff_allowed: true,
      can_create_internal_draft_quote: true,
      status_label: "READY_FOR_INTERNAL_DRAFT_REVIEW",
      blockers: ["artwork_execution_undecided:Layer_x0020_1"],
      fatal_blockers: [],
      review_warnings: ["artwork_execution_undecided:Layer_x0020_1"],
      requires_operator_confirmation: true,
      operator_confirmation_complete: false,
      client_send_allowed: false,
      accept_allowed: false,
      convert_to_order_allowed: false,
      production_allowed: false,
      preview_only: true,
    });
    expect(ui.label).toBe("Draft intern: pregătit pentru review");
    expect(ui.debugLabel).toBe("READY_FOR_INTERNAL_DRAFT_REVIEW");
    expect(ui.handoffAllowed).toBe(true);
  });

  it("does not label blocked state as workspace ready badge", () => {
    const badge = resolveWorkspaceSummaryBadgeLabel("ready_for_quote_preview", {
      workspace_id: "ws",
      workspace_readiness_status: "ready_for_quote_preview",
      handoff_allowed: false,
      can_create_internal_draft_quote: false,
      status_label: "QUOTE_HANDOFF_BLOCKED",
      blockers: ["finish_setup_not_confirmed"],
      fatal_blockers: ["finish_setup_not_confirmed"],
      review_warnings: [],
      requires_operator_confirmation: true,
      operator_confirmation_complete: false,
      client_send_allowed: false,
      accept_allowed: false,
      convert_to_order_allowed: false,
      production_allowed: false,
      preview_only: true,
    });
    expect(badge.label).toBe("Handoff către ofertă reală: blocat");
    expect(badge.label).not.toBe("ready_for_quote_preview");
  });

  it("collects artwork undecided warnings", () => {
    const warnings = collectArtworkUndecidedWarnings([
      "artwork_execution_undecided:Layer_x0020_1",
      "finish_setup_not_confirmed",
    ]);
    expect(warnings).toHaveLength(1);
    expect(warnings[0]).toMatch(/Layer_x0020_1/);
  });

  it("collects unclassified vector review warning", () => {
    const warnings = collectArtworkUndecidedWarnings([
      "unclassified_vector_artwork_requires_decision",
      "finish_setup_not_confirmed",
    ]);
    expect(warnings).toHaveLength(1);
    expect(warnings[0]).toMatch(/Perimetru vector rezidual|Vector Logo/i);
    expect(hasArtworkNeedsDecisionWarning(["unclassified_vector_artwork_requires_decision"])).toBe(true);
  });

  it("builds review surfacing for blocked handoff with artwork and missing prices", () => {
    const surfacing = buildReviewHandoffSurfacing({
      handoff: {
        workspace_id: "ws",
        handoff_allowed: false,
        can_create_internal_draft_quote: false,
        status_label: "QUOTE_HANDOFF_BLOCKED",
        blockers: ["operator_confirmation_missing", "unclassified_vector_artwork_requires_decision"],
        fatal_blockers: ["operator_confirmation_missing"],
        review_warnings: ["unclassified_vector_artwork_requires_decision"],
        requires_operator_confirmation: true,
        operator_confirmation_complete: false,
        client_send_allowed: false,
        accept_allowed: false,
        convert_to_order_allowed: false,
        production_allowed: false,
        preview_only: true,
      },
      containsMissingPrices: true,
      allArtworkProductConfigured: false,
      currentStep: "confirm",
    });
    expect(surfacing.showBanner).toBe(true);
    expect(surfacing.reasons.join(" ")).toMatch(/Vector Logo necesită decizie/i);
    expect(surfacing.reasons.join(" ")).toMatch(/tarif/i);
    expect(surfacing.actions.join(" ")).toMatch(/execuția Vector Logo|Vector Logo/i);
    expect(surfacing.actions.join(" ")).toMatch(/checkbox|Confirmare finală|draft intern/i);
  });

  it("uses residual vector copy when artwork rows are confirmed", () => {
    const surfacing = buildReviewHandoffSurfacing({
      handoff: {
        workspace_id: "ws",
        handoff_allowed: true,
        can_create_internal_draft_quote: true,
        status_label: "READY_FOR_INTERNAL_DRAFT_REVIEW",
        blockers: ["unclassified_vector_artwork_requires_decision"],
        fatal_blockers: [],
        review_warnings: ["unclassified_vector_artwork_requires_decision"],
        requires_operator_confirmation: true,
        operator_confirmation_complete: true,
        client_send_allowed: false,
        accept_allowed: false,
        convert_to_order_allowed: false,
        production_allowed: false,
        preview_only: true,
      },
      allArtworkFinishesConfirmed: true,
    });
    expect(surfacing.showBanner).toBe(true);
    expect(surfacing.reasons.join(" ")).toMatch(/Perimetru vector rezidual|Vector Logo/i);
    expect(surfacing.reasons.join(" ")).toMatch(/perimetru|SVG/i);
    expect(surfacing.actions.join(" ")).toMatch(/Vector Logo/i);
    expect(surfacing.actions.join(" ")).not.toMatch(/Logo 1\/2/);
  });

  it("aligns review readiness copy when workspace is ready but handoff is blocked", () => {
    const display = resolveReviewReadinessDisplay("ready_for_quote_preview", {
      workspace_id: "ws",
      handoff_allowed: false,
      can_create_internal_draft_quote: false,
      status_label: "QUOTE_HANDOFF_BLOCKED",
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
    });
    expect(display.primary).toBe("Date tehnice pregătite pentru preview");
    expect(display.secondary).toMatch(/Pasul 3|Confirmarea finală/i);
    expect(display.secondary).not.toMatch(/Product Truth confirmat/i);
  });

  it("does not hardcode Logo 1/2 in residual copy for N Vector Logos", () => {
    const surfacing = buildReviewHandoffSurfacing({
      handoff: {
        workspace_id: "ws",
        handoff_allowed: true,
        can_create_internal_draft_quote: true,
        status_label: "READY_FOR_INTERNAL_DRAFT_REVIEW",
        blockers: [],
        fatal_blockers: [],
        review_warnings: ["unclassified_vector_artwork_requires_decision"],
        requires_operator_confirmation: true,
        operator_confirmation_complete: true,
        client_send_allowed: false,
        accept_allowed: false,
        convert_to_order_allowed: false,
        production_allowed: false,
        preview_only: true,
      },
      allArtworkProductConfigured: true,
    });
    const text = `${surfacing.reasons.join(" ")} ${surfacing.actions.join(" ")}`;
    expect(text).not.toMatch(/Logo 1\/2/);
    expect(text).not.toMatch(/logo_instance_001/);
    expect(text).toMatch(/Vector Logo/i);
  });

  describe("step-scoped operator_confirmation_missing", () => {
    const onlyOperatorConfirmationHandoff = {
      workspace_id: "ws",
      handoff_allowed: false,
      can_create_internal_draft_quote: false,
      status_label: "QUOTE_HANDOFF_BLOCKED",
      blockers: ["operator_confirmation_missing"],
      fatal_blockers: ["operator_confirmation_missing"],
      review_warnings: [],
      diagnostic_warnings: [
        "canonical_unresolved_warning:DOSSIER_METADATA_ONLY: x",
      ],
      requires_operator_confirmation: true,
      operator_confirmation_complete: false,
      client_send_allowed: false,
      accept_allowed: false,
      convert_to_order_allowed: false,
      production_allowed: false,
      preview_only: true,
    } as const;

    it("hides operator_confirmation_missing from Step 1 primary blockers", () => {
      const surfacing = buildReviewHandoffSurfacing({
        handoff: onlyOperatorConfirmationHandoff,
        currentStep: "layers",
      });
      expect(surfacing.showBanner).toBe(false);
      expect(surfacing.reasons.join(" ")).not.toMatch(/Handoff-ul către ofertă/i);
      expect(surfacing.reasons.join(" ")).not.toMatch(/confirmă pentru continuare/i);
      expect(surfacing.nextStepGuidance ?? "").toMatch(/Pasul 3/i);
    });

    it("hides operator_confirmation_missing from Step 2 primary blockers", () => {
      const surfacing = buildReviewHandoffSurfacing({
        handoff: onlyOperatorConfirmationHandoff,
        currentStep: "review",
      });
      expect(surfacing.showBanner).toBe(false);
      expect(surfacing.reasons.join(" ")).not.toMatch(/Handoff-ul către ofertă/i);
      expect(surfacing.nextStepGuidance).toMatch(/Confirmarea finală se efectuează în Pasul 3/i);
    });

    it("shows operator_confirmation_missing as actionable primary on Step 3", () => {
      const surfacing = buildReviewHandoffSurfacing({
        handoff: onlyOperatorConfirmationHandoff,
        currentStep: "confirm",
      });
      expect(surfacing.showBanner).toBe(true);
      expect(surfacing.reasons.join(" ")).toMatch(/confirmă pentru continuare|Confirmare/i);
      expect(surfacing.actions.join(" ")).toMatch(/Confirmare|checkbox|confirmă/i);
    });

    it("keeps genuine Step 2 product blockers red when present alongside operator confirmation", () => {
      const surfacing = buildReviewHandoffSurfacing({
        handoff: {
          ...onlyOperatorConfirmationHandoff,
          blockers: ["operator_confirmation_missing", "layer_roles_incomplete"],
          fatal_blockers: ["operator_confirmation_missing", "layer_roles_incomplete"],
        },
        currentStep: "review",
      });
      expect(surfacing.showBanner).toBe(true);
      expect(surfacing.reasons.join(" ")).toMatch(/rolurile layerelor|Product Truth/i);
      expect(surfacing.reasons.join(" ")).not.toMatch(/confirmă pentru continuare/i);
    });

    it("does not treat TRIGGER review warnings as Step 2 fatal blockers", () => {
      const surfacing = buildReviewHandoffSurfacing({
        handoff: {
          ...onlyOperatorConfirmationHandoff,
          handoff_allowed: true,
          can_create_internal_draft_quote: true,
          status_label: "READY_FOR_INTERNAL_DRAFT_REVIEW",
          blockers: [],
          fatal_blockers: [],
          review_warnings: [
            "canonical_unresolved_warning:TRIGGER_FIELD_MISMATCH: mounting_system",
          ],
          operator_confirmation_complete: true,
          requires_operator_confirmation: false,
        },
        currentStep: "review",
      });
      expect(surfacing.showBanner).toBe(false);
    });

    it("clears Step 3 primary blocker when operator confirmation is complete", () => {
      const surfacing = buildReviewHandoffSurfacing({
        handoff: {
          ...onlyOperatorConfirmationHandoff,
          handoff_allowed: true,
          can_create_internal_draft_quote: true,
          status_label: "READY_FOR_INTERNAL_DRAFT_REVIEW",
          blockers: [],
          fatal_blockers: [],
          operator_confirmation_complete: true,
          requires_operator_confirmation: false,
        },
        currentStep: "confirm",
      });
      expect(surfacing.showBanner).toBe(false);
    });

    it("suppresses false-red handoff banner while preview is still loading on Step 2", () => {
      const surfacing = buildReviewHandoffSurfacing({
        handoff: null,
        handoffOptions: { loading: true },
        currentStep: "review",
      });
      expect(surfacing.showBanner).toBe(false);
      expect(surfacing.nextStepGuidance).toBeNull();
    });

    it("still surfaces Step 2 banner when handoff preview fetch fails permanently", () => {
      const surfacing = buildReviewHandoffSurfacing({
        handoff: null,
        handoffOptions: { loading: false, fetchError: "network" },
        currentStep: "review",
      });
      expect(surfacing.showBanner).toBe(true);
      expect(surfacing.reasons.join(" ")).toMatch(/Handoff-ul către ofertă/i);
    });
  });
});
