import { describe, expect, it } from "vitest";
import {
  artworkFinishStatusLabelRo,
  electricalAssemblyStatusLabelRo,
  finishLetterCardStatusLabelRo,
  isOwnerDecisionStatus,
  layerConfirmationStateLabelRo,
  layerStatusIconLabelRo,
  looksLikeRawInternalToken,
  operatorGatePathLabelRo,
  operatorReadinessLabelRo,
  operatorStatusSemanticRo,
  resolveOperatorStatusSemantic,
  segmentedAssemblyStatusLabelRo,
  workspaceReadyAggregateLabelRo,
} from "./intakeV6OperatorVocabulary";

describe("intakeV6OperatorVocabulary", () => {
  it("maps OWNER_GATE_REQUIRED to Decizie administrator", () => {
    expect(operatorReadinessLabelRo("OWNER_GATE_REQUIRED")).toBe(
      operatorStatusSemanticRo("owner_decision"),
    );
    expect(isOwnerDecisionStatus("OWNER_GATE_REQUIRED")).toBe(true);
  });

  it("maps LOCAL_CONFIGURATION_REQUIRED to Necesită confirmare", () => {
    expect(operatorReadinessLabelRo("LOCAL_CONFIGURATION_REQUIRED")).toBe(
      operatorStatusSemanticRo("needs_operator"),
    );
  });

  it("maps gate paths without exposing raw keys in primary labels", () => {
    expect(operatorGatePathLabelRo("mounting_method_status")).toBe("Metodă de montaj");
    expect(operatorGatePathLabelRo("cable_passage_status")).toBe("Trecere cablu");
    expect(operatorGatePathLabelRo("electrical_interface_status")).toBe("Interfață electrică");
  });

  it("detects raw internal tokens", () => {
    expect(looksLikeRawInternalToken("OWNER_GATE_REQUIRED")).toBe(true);
    expect(looksLikeRawInternalToken(operatorStatusSemanticRo("owner_decision"))).toBe(false);
  });

  it("keeps Propunere distinct from Necesită confirmare", () => {
    expect(operatorStatusSemanticRo("proposal")).toBe("Propunere");
    expect(operatorStatusSemanticRo("needs_operator")).toBe("Necesită confirmare");
    expect(resolveOperatorStatusSemantic("PROPOSED")).toBe("proposal");
    expect(resolveOperatorStatusSemantic("UNCONFIRMED")).toBe("needs_operator");
  });

  it("maps Finisaje card statuses without OK/Lipsă", () => {
    expect(finishLetterCardStatusLabelRo("ok")).toBe("Confirmat");
    expect(finishLetterCardStatusLabelRo("warning")).toBe("Lipsă date");
    expect(finishLetterCardStatusLabelRo(null)).toBeNull();
  });

  it("maps artwork finish statuses", () => {
    expect(artworkFinishStatusLabelRo({ confirmed: true, stepOneConfirmed: false }).label).toBe(
      "Confirmat",
    );
    expect(artworkFinishStatusLabelRo({ confirmed: false, stepOneConfirmed: true }).label).toBe(
      "Necesită confirmare",
    );
    expect(artworkFinishStatusLabelRo({ confirmed: false, stepOneConfirmed: false }).label).toBe(
      "Necesită confirmare",
    );
  });

  it("maps Page 1 confirmation text vs icon aria distinctly", () => {
    expect(layerConfirmationStateLabelRo("pending")).toBe("Propunere");
    expect(layerStatusIconLabelRo("pending")).toBe("Necesită confirmare");
    expect(layerConfirmationStateLabelRo("confirmed")).toBe("Confirmat");
  });

  it("maps segmented and electrical assembly badges", () => {
    expect(segmentedAssemblyStatusLabelRo("PROPOSED")).toBe("Propunere");
    expect(segmentedAssemblyStatusLabelRo("CONFIRMED")).toBe("Confirmat");
    expect(electricalAssemblyStatusLabelRo("CONFIRMED")).toBe("Confirmat");
    expect(electricalAssemblyStatusLabelRo("DRAFT")).toBe("Necesită confirmare");
  });

  it("maps workspace ready aggregate away from Totul OK", () => {
    expect(workspaceReadyAggregateLabelRo()).toBe("Pregătit");
  });

  it("keeps UNCONFIRMED supply option as Neconfirmat via readiness map", () => {
    expect(operatorReadinessLabelRo("UNCONFIRMED")).toBe("Neconfirmat");
  });

  it("unknown status has safe fallback without leaking OWNER_GATE", () => {
    expect(operatorReadinessLabelRo("OWNER_GATE_FOO_BAR")).toBe("Decizie administrator");
  });
});

describe("intakeV6OperatorVocabulary page1 handoff", () => {
  it("builds Romanian handoff messages", async () => {
    const {
      page1HandoffReadyMessage,
      page1HandoffPendingMessage,
      page1HandoffBlockedMessage,
      operatorGuardedLabelRo,
    } = await import("./intakeV6OperatorVocabulary");
    expect(page1HandoffReadyMessage()).toMatch(/Pagina 2/);
    expect(page1HandoffPendingMessage(2)).toMatch(/2 elemente/);
    expect(page1HandoffBlockedMessage()).toMatch(/blocante/);
    expect(operatorGuardedLabelRo()).toBe("Avertizare");
  });
});
