import { describe, expect, it } from "vitest";

import { isAnalysisReadyForReview } from "./intakeV6AnalysisIdentity";
import { canAccessIntakeV6Step, canContinueFromReviewStep, getIntakeV6FirstBlocker, isOfferScopeConfirmed, isOfferScopeValid } from "./intakeV6Readiness";
import { initialIntakeV6WorkspaceState } from "./intakeV6WorkspaceReducer";

const syncedWorkspace = {
  id: "ws-1",
  workspace_code: "IV6-1",
  title: "Test",
  template_code: "TPL-VOLUMETRIC-LETTERS",
  status: "draft",
  readiness_status: "ready_for_quote_preview",
  updated_at: "2026-06-20T12:00:00Z",
  payload: {
    svg_source: { file_hash: "hash-a", upload_status: "analyzed" },
    svg_analysis_json: { layers: [] },
    layer_role_setup: { confirmation_status: "complete", layers: [] },
    finish_setup: { confirmed: true },
    product_composition_confirmed: { confirmed: true },
  },
};

describe("intakeV6Readiness boundary", () => {
  it("blocks review when analysis is not persisted and synced", () => {
    const state = {
      ...initialIntakeV6WorkspaceState,
      analyzerStatus: "ready" as const,
      localFileHash: "hash-b",
      unsavedAnalysis: true,
      workspace: syncedWorkspace,
    };
    expect(canAccessIntakeV6Step(state, "review")).toBe(false);
    expect(getIntakeV6FirstBlocker(state)).toMatch(/salvată|schimbat/i);
  });

  it("allows review when persisted hash matches local hash", () => {
    const state = {
      ...initialIntakeV6WorkspaceState,
      analyzerStatus: "ready" as const,
      localFileHash: "hash-a",
      unsavedAnalysis: false,
      workspace: syncedWorkspace,
    };
    expect(isAnalysisReadyForReview(state)).toBe(true);
    expect(canAccessIntakeV6Step(state, "review")).toBe(true);
  });

  it("blocks confirm until product composition is confirmed", () => {
    const state = {
      ...initialIntakeV6WorkspaceState,
      currentStep: "review" as const,
      workspace: {
        ...syncedWorkspace,
        readiness_status: "product_composition_not_confirmed",
        payload: {
          ...syncedWorkspace.payload,
          product_composition_confirmed: { confirmed: false },
        },
      },
    };

    expect(canContinueFromReviewStep(state)).toBe(false);
    expect(getIntakeV6FirstBlocker(state)).toMatch(/compoziția produsului/i);
  });

  it("treats missing offer_scope as legacy full product", () => {
    expect(isOfferScopeConfirmed(syncedWorkspace.payload)).toBe(true);
    expect(isOfferScopeValid(syncedWorkspace.payload)).toBe(true);
  });

  it("blocks invalid empty subset scope", () => {
    const payload = {
      offer_scope: {
        contract_version: "offer_scope_contract/v1",
        mode: "component_subset",
        sold_modules: [],
      },
      offer_scope_confirmed: { confirmed: true },
    };
    expect(isOfferScopeValid(payload)).toBe(false);
    expect(isOfferScopeConfirmed(payload)).toBe(false);
  });

  it("accepts LIGHTING and ELECTRICAL subset codes", () => {
    const payload = {
      offer_scope: {
        contract_version: "offer_scope_contract/v1",
        mode: "component_subset",
        sold_modules: ["LIGHTING", "ELECTRICAL"],
      },
      offer_scope_confirmed: { confirmed: true },
    };
    expect(isOfferScopeValid(payload)).toBe(true);
    expect(isOfferScopeConfirmed(payload)).toBe(true);
  });
});