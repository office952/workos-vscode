import { describe, expect, it } from "vitest";
import {
  resolveConfirmChecklistProgress,
  resolveConfirmSubmitDisabledReason,
} from "./intakeV6ConfirmSubmitReason";

describe("intakeV6ConfirmSubmitReason", () => {
  it("counts checklist progress with composition and boundary item", () => {
    expect(
      resolveConfirmChecklistProgress({
        compositionConfirmed: true,
        finishSetupComplete: true,
        operatorConfirmationComplete: true,
        confirmInternalDraft: true,
        draftBoundaryAcknowledged: false,
        showDraftBoundaryItem: true,
      }),
    ).toEqual({ done: 3, total: 4 });
  });

  it("keeps composition incomplete visible in checklist progress", () => {
    expect(
      resolveConfirmChecklistProgress({
        compositionConfirmed: false,
        finishSetupComplete: true,
        operatorConfirmationComplete: false,
        confirmInternalDraft: false,
        draftBoundaryAcknowledged: false,
        showDraftBoundaryItem: false,
      }),
    ).toEqual({ done: 1, total: 3 });
  });

  it("prefers firstBlocker when workspace is not ready for quote preview", () => {
    expect(
      resolveConfirmSubmitDisabledReason({
        hasResult: false,
        submitting: false,
        finishSetupIncomplete: false,
        bindingBlockers: [],
        handoffAllowed: true,
        operatorConfirmationComplete: false,
        confirmInternalDraft: false,
        confirmDraftBoundary: false,
        showHandoffCheckboxes: false,
        isReadyForQuotePreview: false,
        firstBlocker: "Confirmă compoziția produsului în pasul Review.",
        formatBlocker: (code) => code,
      }),
    ).toMatch(/compoziția produsului/i);
  });

  it("returns explicit disabled reason for missing operator confirmation", () => {
    expect(
      resolveConfirmSubmitDisabledReason({
        hasResult: false,
        submitting: false,
        finishSetupIncomplete: false,
        bindingBlockers: [],
        handoffAllowed: true,
        operatorConfirmationComplete: false,
        confirmInternalDraft: false,
        confirmDraftBoundary: false,
        showHandoffCheckboxes: true,
        isReadyForQuotePreview: true,
        firstBlocker: null,
        formatBlocker: (code) => code,
      }),
    ).toBe("Bifează confirmarea operatorului pentru draft intern.");
  });
});
