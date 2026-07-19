import { describe, expect, it } from "vitest";
import {
  INTAKE_V6_CONFIRM_STATUS_TITLE,
  buildIntakeV6ConfirmConsolidatedStatus,
} from "./intakeV6ConfirmConsolidatedStatus";

const baseInput = {
  loading: false,
  fetchError: null,
  finishSetupIncomplete: false,
  effectiveHandoffAllowed: true,
  bindingBlockers: [] as string[],
  allFatalBlockers: [] as string[],
  artworkNeedsDecision: false,
  reviewWarnings: [] as string[],
  containsMissingPrices: false,
  operatorConfirmationComplete: true,
  confirmInternalDraft: true,
  confirmDraftBoundary: true,
  showHandoffCheckboxes: true,
  checklistProgress: { done: 3, total: 3 },
  modularPendingCount: 0,
};

describe("buildIntakeV6ConfirmConsolidatedStatus", () => {
  it("returns informational loading state", () => {
    const status = buildIntakeV6ConfirmConsolidatedStatus({
      ...baseInput,
      loading: true,
    });

    expect(status.tier).toBe("informational");
    expect(status.title).toBe(INTAKE_V6_CONFIRM_STATUS_TITLE);
    expect(status.headline).toMatch(/verific/i);
  });

  it("returns blocked state when finish setup is incomplete", () => {
    const status = buildIntakeV6ConfirmConsolidatedStatus({
      ...baseInput,
      finishSetupIncomplete: true,
    });

    expect(status.tier).toBe("blocked");
    expect(status.indicatorLabel).toBe("Blocant");
    expect(status.observations.some((item) => /finisaje/i.test(item))).toBe(true);
  });

  it("returns attention state when operator confirmation is missing", () => {
    const status = buildIntakeV6ConfirmConsolidatedStatus({
      ...baseInput,
      operatorConfirmationComplete: false,
      confirmInternalDraft: false,
      checklistProgress: { done: 1, total: 3 },
    });

    expect(status.tier).toBe("attention");
    expect(status.indicatorLabel).toBe("Avertizare");
    expect(status.observations.some((item) => /Confirmă finisajele/i.test(item))).toBe(true);
  });

  it("returns ready state when checklist is complete and handoff is allowed", () => {
    const status = buildIntakeV6ConfirmConsolidatedStatus(baseInput);

    expect(status.tier).toBe("ready");
    expect(status.indicatorLabel).toBe("Pregătit");
    expect(status.headline).toMatch(/Pregătit pentru confirmare/i);
  });

  it("limits observations to three items", () => {
    const status = buildIntakeV6ConfirmConsolidatedStatus({
      ...baseInput,
      effectiveHandoffAllowed: false,
      allFatalBlockers: ["blocker_a", "blocker_b", "blocker_c", "blocker_d"],
      containsMissingPrices: true,
      modularPendingCount: 2,
      operatorConfirmationComplete: false,
      confirmInternalDraft: false,
      confirmDraftBoundary: false,
      showHandoffCheckboxes: true,
    });

    expect(status.observations.length).toBeLessThanOrEqual(3);
  });
});
