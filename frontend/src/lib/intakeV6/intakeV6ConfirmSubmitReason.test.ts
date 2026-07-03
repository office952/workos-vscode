import { describe, expect, it } from "vitest";
import {
  resolveConfirmChecklistProgress,
  resolveConfirmSubmitDisabledReason,
} from "./intakeV6ConfirmSubmitReason";

describe("intakeV6ConfirmSubmitReason", () => {
  it("counts checklist progress with boundary item", () => {
    expect(
      resolveConfirmChecklistProgress({
        finishSetupComplete: true,
        operatorConfirmationComplete: true,
        confirmInternalDraft: true,
        draftBoundaryAcknowledged: false,
        showDraftBoundaryItem: true,
      }),
    ).toEqual({ done: 2, total: 3 });
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
