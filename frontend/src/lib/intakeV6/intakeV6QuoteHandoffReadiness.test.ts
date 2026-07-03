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
  it("formats artwork undecided blocker", () => {
    expect(formatQuoteHandoffBlocker("artwork_execution_undecided:Layer_x0020_1")).toMatch(
      /Layer_x0020_1/,
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
    expect(warnings[0]).toMatch(/Vector neclasificat/);
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
      allArtworkFinishesConfirmed: false,
    });
    expect(surfacing.showBanner).toBe(true);
    expect(surfacing.reasons.join(" ")).toMatch(/Artwork neconfirmat/i);
    expect(surfacing.reasons.join(" ")).toMatch(/tarif/i);
    expect(surfacing.actions.join(" ")).toMatch(/Confirm artwork/i);
    expect(surfacing.actions.join(" ")).toMatch(/Confirmarea finală/i);
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
    expect(surfacing.reasons.join(" ")).toMatch(/Artwork confirmat/i);
    expect(surfacing.reasons.join(" ")).toMatch(/vector rezidual/i);
    expect(surfacing.actions.join(" ")).toMatch(/stratul\/sursa SVG/i);
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
    expect(display.secondary).toMatch(/Handoff ofertă necesită verificări finale/i);
  });
});