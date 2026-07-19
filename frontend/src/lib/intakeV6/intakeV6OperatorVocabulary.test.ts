import { describe, expect, it } from "vitest";
import {
  isOwnerDecisionStatus,
  looksLikeRawInternalToken,
  operatorGatePathLabelRo,
  operatorReadinessLabelRo,
} from "./intakeV6OperatorVocabulary";

describe("intakeV6OperatorVocabulary", () => {
  it("maps OWNER_GATE_REQUIRED to Romanian owner decision", () => {
    expect(operatorReadinessLabelRo("OWNER_GATE_REQUIRED")).toBe(
      "Necesită confirmarea administratorului",
    );
    expect(isOwnerDecisionStatus("OWNER_GATE_REQUIRED")).toBe(true);
  });

  it("maps LOCAL_CONFIGURATION_REQUIRED", () => {
    expect(operatorReadinessLabelRo("LOCAL_CONFIGURATION_REQUIRED")).toBe(
      "Necesită configurare locală",
    );
  });

  it("maps gate paths without exposing raw keys in primary labels", () => {
    expect(operatorGatePathLabelRo("mounting_method_status")).toBe("Metodă de montaj");
    expect(operatorGatePathLabelRo("cable_passage_status")).toBe("Trecere cablu");
    expect(operatorGatePathLabelRo("electrical_interface_status")).toBe("Interfață electrică");
  });

  it("detects raw internal tokens", () => {
    expect(looksLikeRawInternalToken("OWNER_GATE_REQUIRED")).toBe(true);
    expect(looksLikeRawInternalToken("Necesită confirmarea administratorului")).toBe(false);
  });
});
