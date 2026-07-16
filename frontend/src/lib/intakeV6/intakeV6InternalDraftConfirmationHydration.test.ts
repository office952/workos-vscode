import { describe, expect, it } from "vitest";

import {
  reconcileLocalConfirmationWithPersisted,
  resolveConfirmationCheckboxChecked,
  resolveInternalDraftConfirmationHydration,
  restoreConfirmationAfterFailedPut,
  shouldApplyConfirmationSnapshot,
} from "./intakeV6InternalDraftConfirmationHydration";

describe("intakeV6InternalDraftConfirmationHydration", () => {
  it("hydrates checked when finish_setup.internal_draft_quote_confirmed is true", () => {
    const h = resolveInternalDraftConfirmationHydration({
      hasFinishSetup: true,
      finishSetupConfirmed: true,
      hasHandoffPreview: false,
      handoffOperatorComplete: undefined,
      previewLoading: true,
      saving: false,
    });
    expect(h.resolved).toBe(true);
    expect(h.confirmed).toBe(true);
    expect(h.disableInteraction).toBe(true);
  });

  it("during preview refresh prefers finish_setup over stale handoff true", () => {
    const h = resolveInternalDraftConfirmationHydration({
      hasFinishSetup: true,
      finishSetupConfirmed: false,
      hasHandoffPreview: true,
      handoffOperatorComplete: true,
      previewLoading: true,
      saving: false,
    });
    expect(h.resolved).toBe(true);
    expect(h.confirmed).toBe(false);
    expect(h.disableInteraction).toBe(true);
  });

  it("hydrates unchecked when finish_setup confirmation is false", () => {
    const h = resolveInternalDraftConfirmationHydration({
      hasFinishSetup: true,
      finishSetupConfirmed: false,
      hasHandoffPreview: false,
      handoffOperatorComplete: undefined,
      previewLoading: false,
      saving: false,
    });
    expect(h.resolved).toBe(true);
    expect(h.confirmed).toBe(false);
  });

  it("prefers handoff operator_confirmation_complete when preview is loaded", () => {
    const h = resolveInternalDraftConfirmationHydration({
      hasFinishSetup: true,
      finishSetupConfirmed: false,
      hasHandoffPreview: true,
      handoffOperatorComplete: true,
      previewLoading: false,
      saving: false,
    });
    expect(h.confirmed).toBe(true);
  });

  it("marks hydration unresolved while neither finish_setup nor handoff is available", () => {
    const h = resolveInternalDraftConfirmationHydration({
      hasFinishSetup: false,
      finishSetupConfirmed: undefined,
      hasHandoffPreview: false,
      handoffOperatorComplete: undefined,
      previewLoading: true,
      saving: false,
    });
    expect(h.resolved).toBe(false);
    expect(h.disableInteraction).toBe(true);
    // Unresolved must not be treated as settled unchecked truth for UI "done" signals.
    expect(resolveConfirmationCheckboxChecked({ hydration: h, localConfirmed: false })).toBe(false);
  });

  it("hard-reload path: persisted true reconciles local false to true", () => {
    expect(
      reconcileLocalConfirmationWithPersisted({
        saving: false,
        localConfirmed: false,
        persistedConfirmed: true,
        hydrationResolved: true,
      }),
    ).toBe(true);
  });

  it("route remount path: persisted true stays true after reconcile", () => {
    expect(
      reconcileLocalConfirmationWithPersisted({
        saving: false,
        localConfirmed: true,
        persistedConfirmed: true,
        hydrationResolved: true,
      }),
    ).toBe(true);
  });

  it("backend reset to false updates reconciled local state", () => {
    expect(
      reconcileLocalConfirmationWithPersisted({
        saving: false,
        localConfirmed: true,
        persistedConfirmed: false,
        hydrationResolved: true,
      }),
    ).toBe(false);
  });

  it("upstream finish save reset (persisted false) clears checkbox", () => {
    const h = resolveInternalDraftConfirmationHydration({
      hasFinishSetup: true,
      finishSetupConfirmed: false,
      hasHandoffPreview: true,
      handoffOperatorComplete: false,
      previewLoading: false,
      saving: false,
    });
    expect(h.confirmed).toBe(false);
    expect(
      reconcileLocalConfirmationWithPersisted({
        saving: false,
        localConfirmed: true,
        persistedConfirmed: h.confirmed,
        hydrationResolved: h.resolved,
      }),
    ).toBe(false);
  });

  it("optimistic user click true is kept while saving (not overwritten by stale false)", () => {
    expect(
      reconcileLocalConfirmationWithPersisted({
        saving: true,
        localConfirmed: true,
        persistedConfirmed: false,
        hydrationResolved: true,
      }),
    ).toBe(true);
  });

  it("failed PUT restores last persisted false (no false success)", () => {
    expect(
      restoreConfirmationAfterFailedPut({
        hasHandoffPreview: true,
        handoffOperatorComplete: false,
        hasFinishSetup: true,
        finishSetupConfirmed: false,
      }),
    ).toBe(false);
  });

  it("failed PUT restores last persisted true", () => {
    expect(
      restoreConfirmationAfterFailedPut({
        hasHandoffPreview: true,
        handoffOperatorComplete: true,
        hasFinishSetup: true,
        finishSetupConfirmed: true,
      }),
    ).toBe(true);
  });

  it("stale response generation cannot overwrite newer persisted truth", () => {
    expect(
      shouldApplyConfirmationSnapshot({
        saving: false,
        responseGeneration: 3,
        latestGeneration: 5,
      }),
    ).toBe(false);
    expect(
      shouldApplyConfirmationSnapshot({
        saving: false,
        responseGeneration: 5,
        latestGeneration: 5,
      }),
    ).toBe(true);
  });

  it("autosync remount: snapshot apply blocked while saving", () => {
    expect(
      shouldApplyConfirmationSnapshot({
        saving: true,
        responseGeneration: 2,
        latestGeneration: 2,
      }),
    ).toBe(false);
  });

  it("operator_confirmation_missing matches unchecked when resolved false", () => {
    const h = resolveInternalDraftConfirmationHydration({
      hasFinishSetup: true,
      finishSetupConfirmed: false,
      hasHandoffPreview: true,
      handoffOperatorComplete: false,
      previewLoading: false,
      saving: false,
    });
    // fatal operator_confirmation_missing is expected when confirmed is false
    expect(h.confirmed).toBe(false);
    expect(h.resolved).toBe(true);
  });

  it("can_create eligibility aligns with persisted confirmation true", () => {
    const h = resolveInternalDraftConfirmationHydration({
      hasFinishSetup: true,
      finishSetupConfirmed: true,
      hasHandoffPreview: true,
      handoffOperatorComplete: true,
      previewLoading: false,
      saving: false,
    });
    // Quote eligibility (can_create) requires confirmation complete — mirrored here
    expect(h.confirmed).toBe(true);
  });

  it("does not invent confirmation when sources are missing", () => {
    expect(
      restoreConfirmationAfterFailedPut({
        hasHandoffPreview: false,
        handoffOperatorComplete: undefined,
        hasFinishSetup: false,
        finishSetupConfirmed: undefined,
      }),
    ).toBe(false);
  });
});
