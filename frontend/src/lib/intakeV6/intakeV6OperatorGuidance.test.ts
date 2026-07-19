import { describe, expect, it } from "vitest";
import type { IntakeV6WorkspaceState } from "./intakeV6Contracts";
import { initialIntakeV6WorkspaceState } from "./intakeV6WorkspaceReducer";
import {
  buildGuidanceDrawerToggleLabel,
  buildGuidanceStickySummaryTitle,
  buildIntakeV6OperatorGuidanceModel,
  normalizeGuidanceNextAction,
} from "./intakeV6OperatorGuidance";

const syncedPayload = {
  svg_source: { file_hash: "hash-a", upload_status: "analyzed" },
  svg_analysis_json: { layers: [] },
  layer_role_setup: { confirmation_status: "incomplete", layers: [] },
};

function baseState(overrides: Partial<IntakeV6WorkspaceState> = {}): IntakeV6WorkspaceState {
  return {
    ...initialIntakeV6WorkspaceState,
    phase: "svg_ready",
    currentStep: "layers",
    analyzerStatus: "ready",
    localFileHash: "hash-a",
    unsavedAnalysis: false,
    layerChips: [
      { layerKey: "a", status: "pending" },
      { layerKey: "b", status: "pending" },
    ],
    workspace: {
      id: "ws-1",
      workspace_code: "IV6-TEST",
      title: "Test",
      template_code: "TPL-VOLUMETRIC-LETTERS",
      status: "draft",
      readiness_status: "layer_roles_incomplete",
      updated_at: "2026-07-19T12:00:00Z",
      payload: { ...syncedPayload },
    },
    ...overrides,
  } as IntakeV6WorkspaceState;
}

describe("normalizeGuidanceNextAction", () => {
  it("strips analyzer phrasing from composition prompts", () => {
    expect(
      normalizeGuidanceNextAction("Confirmă compoziția produsului propusă de analyzer."),
    ).toBe("Confirmă compoziția produsului.");
  });
});

describe("buildIntakeV6OperatorGuidanceModel", () => {
  it("answers next action on Page 1 when roles incomplete", () => {
    const guidance = buildIntakeV6OperatorGuidanceModel({
      state: baseState(),
      canContinueFromAnalyzer: false,
    });
    expect(guidance.whereAmI).toBe("Straturi");
    expect(guidance.statusLabel).toBe("Straturi incomplete");
    expect(guidance.nextAction).toMatch(/rol/i);
    expect(guidance.canContinue).toBe(false);
    expect(guidance.countsLabel).toMatch(/blocant/i);
  });

  it("marks ready when analyzer continue is allowed", () => {
    const guidance = buildIntakeV6OperatorGuidanceModel({
      state: baseState({
        layerChips: [
          { layerKey: "a", status: "confirmed" },
          { layerKey: "b", status: "confirmed" },
        ],
        workspace: {
          id: "ws-1",
          workspace_code: "IV6-TEST",
          title: "Test",
          template_code: "TPL-VOLUMETRIC-LETTERS",
          status: "draft",
          readiness_status: "product_composition_not_confirmed",
          updated_at: "2026-07-19T12:00:00Z",
          payload: {
            ...syncedPayload,
            layer_role_setup: { confirmation_status: "complete", layers: [] },
          },
        },
      } as Partial<IntakeV6WorkspaceState>),
      canContinueFromAnalyzer: true,
    });
    expect(guidance.canContinue).toBe(true);
    expect(guidance.nextAction).toBeNull();
    expect(guidance.statusLabel).toBe("Pregătit");
  });

  it("tracks review progress and composition next action without analyzer leak", () => {
    const guidance = buildIntakeV6OperatorGuidanceModel({
      state: baseState({
        currentStep: "review",
        workspace: {
          id: "ws-1",
          workspace_code: "IV6-TEST",
          title: "Test",
          template_code: "TPL-VOLUMETRIC-LETTERS",
          status: "draft",
          readiness_status: "product_composition_not_confirmed",
          updated_at: "2026-07-19T12:00:00Z",
          payload: {
            ...syncedPayload,
            layer_role_setup: { confirmation_status: "complete", layers: [] },
            offer_scope: { mode: "full_product" },
            offer_scope_confirmed: { confirmed: true },
            finish_setup: { confirmed: true },
            product_composition_confirmed: { confirmed: false },
          },
        },
      } as Partial<IntakeV6WorkspaceState>),
      canContinueFromAnalyzer: true,
    });
    expect(guidance.whereAmI).toBe("Configurare");
    expect(guidance.statusLabel).toBe("Configurare incompletă");
    expect(guidance.progressTotal).toBe(3);
    expect(guidance.progressDone).toBe(2);
    expect(guidance.progressLabel).toBe("2 / 3 confirmări");
    expect(guidance.nextAction).toMatch(/compoziț/i);
    expect(guidance.nextAction).not.toMatch(/analyzer/i);
  });

  it("uses confirm disabled reason as next action", () => {
    const guidance = buildIntakeV6OperatorGuidanceModel({
      state: baseState({ currentStep: "confirm" } as Partial<IntakeV6WorkspaceState>),
      canContinueFromAnalyzer: true,
      confirmChecklist: { done: 1, total: 2 },
      confirmCanSubmit: false,
      confirmDisabledReason: "Bifează confirmarea operatorului.",
    });
    expect(guidance.whereAmI).toBe("Confirmare");
    expect(guidance.nextAction).toMatch(/operatorului/i);
    expect(guidance.progressLabel).toBe("1 / 2 confirmări");
  });

  it("uses sticky attention inventory as the single count source", () => {
    const guidance = buildIntakeV6OperatorGuidanceModel({
      state: baseState({ currentStep: "review" } as Partial<IntakeV6WorkspaceState>),
      canContinueFromAnalyzer: true,
      attentionIssues: [
        {
          id: "composition",
          severity: "blocker",
          message: "Compoziția produsului nu este confirmată.",
        },
        {
          id: "seg",
          severity: "warning",
          message: "Există o propunere de fundal din mai multe panouri.",
        },
        {
          id: "tariff",
          severity: "warning",
          message: "Linii fără tarif: glue",
        },
      ],
      informationIssues: [
        {
          id: "info-1",
          severity: "information",
          message: "Detaliu tehnic intern.",
        },
      ],
    });
    expect(guidance.blockerCount).toBe(1);
    expect(guidance.warningCount).toBe(2);
    expect(guidance.informationCount).toBe(1);
    expect(guidance.countsLabel).toBe("1 blocant · 2 avertizări");
    expect(guidance.stickySummaryTitle).toBe(
      buildGuidanceStickySummaryTitle(1, 2),
    );
    expect(guidance.drawerToggleLabel).toBe(
      buildGuidanceDrawerToggleLabel(1, 2, 1),
    );
    expect(guidance.stickySummaryTitle).toEqual(expect.stringContaining("1 blocant"));
    expect(guidance.drawerToggleLabel).toMatch(/1 informație/);
  });
});

describe("guidance count labels", () => {
  it("keeps sticky and drawer language aligned", () => {
    expect(buildGuidanceStickySummaryTitle(3, 1)).toBe(
      "Configurarea necesită atenție · 3 blocante · 1 avertizare",
    );
    expect(buildGuidanceDrawerToggleLabel(3, 1, 4)).toBe(
      "3 blocante · 1 avertizare · 4 informații",
    );
  });

  it("handles zero blockers warning-only", () => {
    expect(buildGuidanceStickySummaryTitle(0, 2)).toBe(
      "Configurarea necesită atenție · 2 avertizări",
    );
  });
});
