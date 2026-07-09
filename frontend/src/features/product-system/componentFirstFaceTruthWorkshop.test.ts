import { describe, expect, it } from "vitest";
import {
  buildFaceReadinessSummary,
  FACE_COMPONENT_TEMPLATE_CODE,
  FACE_DOES_NOT_OWN,
  FACE_DOES_NOT_OWN_CONFIRMED,
  FACE_DOWNSTREAM_OUTPUTS,
  FACE_MATERIAL_FAMILY_DECISIONS,
  FACE_NESTING_BASIS_RULE,
  FACE_OWNER_TRUTH_FIELDS,
  FACE_READINESS_SUMMARY,
  FACE_THICKNESS_DECISIONS,
  FACE_TRUTH_WORKSHOP_FIELDS,
  getFaceDownstreamOutput,
  getFaceTruthField,
} from "./componentFirstFaceTruthWorkshop";

describe("componentFirstFaceTruthWorkshop", () => {
  it("uses TPL-COMP-LETTER-FACE_v1 as component code", () => {
    expect(FACE_COMPONENT_TEMPLATE_CODE).toBe("TPL-COMP-LETTER-FACE_v1");
    expect(getFaceTruthField("component_identity")?.value).toBe("TPL-COMP-LETTER-FACE_v1");
  });

  it("FACE owns substrate and geometry fields", () => {
    expect(FACE_OWNER_TRUTH_FIELDS.some((f) => f.includes("substrat"))).toBe(true);
    expect(FACE_OWNER_TRUTH_FIELDS.some((f) => f.includes("geometrie"))).toBe(true);
    expect(FACE_OWNER_TRUTH_FIELDS.some((f) => f.includes("grosime"))).toBe(true);
    expect(FACE_OWNER_TRUTH_FIELDS.some((f) => f.includes("mp_face_area"))).toBe(true);
    expect(FACE_OWNER_TRUTH_FIELDS.some((f) => f.includes("face_perimeter_length_m"))).toBe(true);
    expect(FACE_OWNER_TRUTH_FIELDS.some((f) => f.includes("face_piece_boxes"))).toBe(true);
  });

  it("source layer role includes Vector Litere", () => {
    const field = getFaceTruthField("source_layer_role");
    expect(field?.value).toBe("Vector Litere");
    expect(field?.status).toBe("owner_confirmed");
  });

  it("owner confirmed Plexiglas for FACE standard", () => {
    const plexi = FACE_MATERIAL_FAMILY_DECISIONS.find((d) => d.materialFamily.includes("Plexiglas"));
    expect(plexi?.allowedForFaceStandard).toBe(true);
    expect(plexi?.status).toBe("owner_confirmed");
  });

  it("owner rejected Forex and ACM for FACE standard", () => {
    const forex = FACE_MATERIAL_FAMILY_DECISIONS.find((d) => d.materialFamily === "Forex");
    const acm = FACE_MATERIAL_FAMILY_DECISIONS.find((d) => d.materialFamily.includes("ACM"));
    expect(forex?.allowedForFaceStandard).toBe(false);
    expect(acm?.allowedForFaceStandard).toBe(false);
  });

  it("Plexiglas default thickness is 3 mm with 5/10 optional", () => {
    const plexi = FACE_THICKNESS_DECISIONS.find((d) => d.materialFamily.includes("Plexiglas"));
    expect(plexi?.defaultThicknessMm).toBe(3);
    expect(plexi?.optionalThicknessesMm).toEqual([5, 10]);
  });

  it("nesting basis is bounding/out-of-box per piece", () => {
    expect(FACE_NESTING_BASIS_RULE).toMatch(/bounding\/out-of-box/i);
    expect(getFaceTruthField("material_nesting_basis")?.status).toBe("owner_confirmed");
  });

  it("downstream outputs include mp_face_area for FINISH", () => {
    const output = getFaceDownstreamOutput("mp_face_area");
    expect(output).not.toBeNull();
    expect(output?.consumerComponent).toBe("FINISH");
    expect(output?.status).toBe("owner_confirmed");
  });

  it("downstream outputs include face_perimeter_length_m for RETURN-CANT", () => {
    const output = getFaceDownstreamOutput("face_perimeter_length_m");
    expect(output).not.toBeNull();
    expect(output?.consumerComponent).toBe("RETURN-CANT");
    expect(output?.status).toBe("owner_confirmed");
  });

  it("downstream outputs include face_piece_boxes and face_material_usage_area_m2", () => {
    expect(getFaceDownstreamOutput("face_piece_boxes")?.status).toBe("owner_confirmed");
    expect(getFaceDownstreamOutput("face_material_usage_area_m2")?.status).toBe("owner_confirmed");
    expect(FACE_DOWNSTREAM_OUTPUTS.length).toBeGreaterThanOrEqual(5);
  });

  it("FACE does not own cant finish", () => {
    expect(FACE_DOES_NOT_OWN.some((item) => /cant.*Stock|Oracal|RAL/i.test(item))).toBe(true);
  });

  it("FACE does not own face vinyl or print/laminate application", () => {
    expect(FACE_DOES_NOT_OWN.some((item) => /vinyl/i.test(item))).toBe(true);
    expect(FACE_DOES_NOT_OWN.some((item) => /print.*lamin/i.test(item))).toBe(true);
  });

  it("does-not-own table owner confirmed", () => {
    expect(FACE_DOES_NOT_OWN_CONFIRMED).toBe(true);
  });

  it("readyForPricing remains false", () => {
    expect(FACE_READINESS_SUMMARY.readyForPricing).toBe(false);
    expect(buildFaceReadinessSummary().readyForPricing).toBe(false);
  });

  it("Product Truth live write remains blocked", () => {
    expect(FACE_READINESS_SUMMARY.productTruthLiveWriteBlocked).toBe(true);
  });

  it("ProductDefinition bridge remains blocked", () => {
    expect(FACE_READINESS_SUMMARY.productDefinitionBridgeBlocked).toBe(true);
  });

  it("FINISH workshop remains blocked as separate slice", () => {
    expect(FACE_READINESS_SUMMARY.finishWorkshopBlocked).toBe(true);
    expect(buildFaceReadinessSummary().blockedFinishEntryCount).toBeGreaterThan(0);
  });

  it("material and thickness fields are owner_confirmed after owner answers", () => {
    expect(getFaceTruthField("material_family_options")?.status).toBe("owner_confirmed");
    expect(getFaceTruthField("material_thickness_options")?.status).toBe("owner_confirmed");
    expect(getFaceTruthField("face_perimeter_output")?.status).toBe("owner_confirmed");
    expect(getFaceTruthField("cut_process")?.status).toBe("owner_confirmed");
    expect(FACE_TRUTH_WORKSHOP_FIELDS.length).toBeGreaterThanOrEqual(9);
  });
});
