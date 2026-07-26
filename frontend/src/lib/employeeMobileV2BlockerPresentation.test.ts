import { describe, expect, it } from "vitest";
import {
  buildEmployeeMobileV2BlockerPresentation,
  MANAGER_ESCALATION_TEXT,
} from "@/lib/employeeMobileV2BlockerPresentation";
import { BLOCKER_FIXTURE_TASKS } from "@/lib/employeeMobileV2BlockerFixtures";

describe("employeeMobileV2BlockerPresentation", () => {
  it("shows Pregătit for ready assigned task", () => {
    const view = buildEmployeeMobileV2BlockerPresentation(BLOCKER_FIXTURE_TASKS.readyAssigned);
    expect(view.primaryLabel).toBe("Pregătit");
    expect(view.canStartFromBackend).toBe(true);
    expect(view.showProductionBadge).toBe(false);
  });

  it("shows production block and manager escalation", () => {
    const view = buildEmployeeMobileV2BlockerPresentation(BLOCKER_FIXTURE_TASKS.productionBlocked);
    expect(view.primaryLabel).toBe("Blocat pentru producție");
    expect(view.showProductionBadge).toBe(true);
    expect(view.showManagerEscalation).toBe(true);
    expect(view.managerEscalationText).toBe(MANAGER_ESCALATION_TEXT);
    expect(view.categories.productie.length).toBeGreaterThan(0);
  });

  it("renders predecessor block separately from production", () => {
    const view = buildEmployeeMobileV2BlockerPresentation(BLOCKER_FIXTURE_TASKS.predecessorBlocked);
    expect(view.primaryLabel).toBe("În așteptarea altei operații");
    expect(view.categories.pregatire.length).toBeGreaterThan(0);
    expect(view.categories.productie).toHaveLength(0);
  });

  it("renders material block separately", () => {
    const view = buildEmployeeMobileV2BlockerPresentation(BLOCKER_FIXTURE_TASKS.materialBlocked);
    expect(view.primaryLabel).toBe("Materiale lipsă");
    expect(view.categories.materiale.length).toBeGreaterThan(0);
  });

  it("renders assignment conflict separately", () => {
    const view = buildEmployeeMobileV2BlockerPresentation(BLOCKER_FIXTURE_TASKS.ownedByOther);
    expect(view.primaryLabel).toBe("Alocat altui coleg");
    expect(view.categories.alocare.length).toBeGreaterThan(0);
  });

  it("represents available but not startable without equating claimability", () => {
    const view = buildEmployeeMobileV2BlockerPresentation(
      BLOCKER_FIXTURE_TASKS.availableNotStartable,
    );
    expect(view.canStartFromBackend).toBe(false);
    expect(view.primaryLabel).toBe("În așteptarea altei operații");
  });

  it("does not mislabel in-progress task as blocked defect", () => {
    const view = buildEmployeeMobileV2BlockerPresentation(BLOCKER_FIXTURE_TASKS.inProgress);
    expect(view.primaryLabel).toBe("În lucru");
    expect(view.activeSessionLabel).toBeTruthy();
    expect(view.canStartFromBackend).toBe(false);
    expect(view.canStartExplanation).toContain("deja în lucru");
  });

  it("shows final state for completed task", () => {
    const view = buildEmployeeMobileV2BlockerPresentation(BLOCKER_FIXTURE_TASKS.completed);
    expect(view.primaryLabel).toBe("Finalizat");
  });

  it("collects diagnostic codes from backend fields only", () => {
    const view = buildEmployeeMobileV2BlockerPresentation(BLOCKER_FIXTURE_TASKS.materialBlocked);
    expect(view.diagnosticCodes).toContain("material_procurement_block");
    expect(view.diagnosticCodes).toContain("readiness_status:waiting_material");
  });

  it("does not calculate is_startable locally", () => {
    const task = { ...BLOCKER_FIXTURE_TASKS.readyAssigned, is_startable: false };
    const view = buildEmployeeMobileV2BlockerPresentation(task);
    expect(view.canStartFromBackend).toBe(false);
  });
});
