import { describe, expect, it } from "vitest";
import { buildWorkspaceHeaderStatus, shouldShowIntakeV6SmartBanner } from "./intakeV6WorkspaceHeaderStatus";
import type { IntakeV6WorkspaceState } from "./intakeV6Contracts";

const baseState = {
  phase: "svg_ready",
  currentStep: "review",
  analyzerStatus: "idle",
  layerChips: [
    { layerKey: "a", status: "confirmed" },
    { layerKey: "b", status: "confirmed" },
  ],
  workspace: { payload: { svg_analysis_json: {} } },
  svg: { fileName: "test.svg", fileSizeBytes: 100 },
} as IntakeV6WorkspaceState;

describe("intakeV6WorkspaceHeaderStatus", () => {
  it("builds Pregătit from workspace layer chips", () => {
    const status = buildWorkspaceHeaderStatus(baseState);
    expect(status.label).toBe("Pregătit");
    expect(status.details.find((row) => row.id === "layers")?.value).toBe("2/2 confirmate");
  });

  it("counts pending layers as actions on layers step", () => {
    const status = buildWorkspaceHeaderStatus({
      ...baseState,
      currentStep: "layers",
      layerChips: [
        { layerKey: "a", status: "confirmed" },
        { layerKey: "b", status: "pending" },
      ],
    } as IntakeV6WorkspaceState);
    expect(status.label).toBe("1 acțiune necesară");
    expect(status.actions.some((action) => action.id === "jump-layers")).toBe(true);
  });

  it("merges review overlay for operator confirmation", () => {
    const status = buildWorkspaceHeaderStatus(
      { ...baseState, currentStep: "confirm" } as IntakeV6WorkspaceState,
      {
        operatorConfirmationMissing: true,
        artworkTotal: 2,
        artworkConfirmed: 2,
      },
    );
    expect(status.label).toBe("1 acțiune necesară");
    expect(status.details.find((row) => row.id === "operator")?.value).toBe("Lipsă date");
  });

  it("hides smart banner blocker duplicate on review step", () => {
    expect(shouldShowIntakeV6SmartBanner(baseState, null)).toBe(false);
    expect(shouldShowIntakeV6SmartBanner(baseState, "Blocaj confirmare")).toBe(false);
    expect(
      shouldShowIntakeV6SmartBanner({ ...baseState, currentStep: "confirm" } as IntakeV6WorkspaceState, "Blocaj confirmare"),
    ).toBe(true);
  });
});
