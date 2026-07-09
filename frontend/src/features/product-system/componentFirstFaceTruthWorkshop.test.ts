import { describe, expect, it } from "vitest";
import {
  buildFaceReadinessSummary,
  FACE_COMPONENT_TEMPLATE_CODE,
  FACE_DOES_NOT_OWN,
  FACE_DOWNSTREAM_OUTPUTS,
  FACE_OWNER_TRUTH_FIELDS,
  FACE_READINESS_SUMMARY,
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
    expect(FACE_OWNER_TRUTH_FIELDS.some((f) => f.includes("perimetru"))).toBe(true);
  });

  it("source layer role includes Vector Litere", () => {
    const field = getFaceTruthField("source_layer_role");
    expect(field?.value).toBe("Vector Litere");
    expect(field?.status).toBe("owner_confirmed");
  });

  it("downstream outputs include mp_face_area for FINISH", () => {
    const output = getFaceDownstreamOutput("mp_face_area");
    expect(output).not.toBeNull();
    expect(output?.consumerComponent).toBe("FINISH");
    expect(output?.quantityBasis).toBe("mp_face_area");
    expect(FACE_DOWNSTREAM_OUTPUTS.some((o) => o.outputKey === "mp_face_area")).toBe(true);
  });

  it("downstream outputs include perimeter for RETURN-CANT", () => {
    const output = getFaceDownstreamOutput("face_perimeter");
    expect(output).not.toBeNull();
    expect(output?.consumerComponent).toBe("RETURN-CANT");
    expect(FACE_DOWNSTREAM_OUTPUTS.some((o) => o.outputKey === "face_perimeter")).toBe(true);
  });

  it("FACE does not own cant finish", () => {
    expect(FACE_DOES_NOT_OWN.some((item) => /cant.*Stock|Oracal|RAL/i.test(item))).toBe(true);
    expect(FACE_DOES_NOT_OWN.some((item) => /finisaj cant/i.test(item))).toBe(true);
  });

  it("FACE does not own face vinyl or print/laminate application", () => {
    expect(FACE_DOES_NOT_OWN.some((item) => /vinyl/i.test(item))).toBe(true);
    expect(FACE_DOES_NOT_OWN.some((item) => /print.*lamin/i.test(item))).toBe(true);
  });

  it("FACE does not own pricing rates", () => {
    expect(FACE_DOES_NOT_OWN.some((item) => /rate preț|EUR/i.test(item))).toBe(true);
  });

  it("readyForPricing remains false", () => {
    expect(FACE_READINESS_SUMMARY.readyForPricing).toBe(false);
    expect(buildFaceReadinessSummary().readyForPricing).toBe(false);
  });

  it("Product Truth live write remains blocked", () => {
    expect(FACE_READINESS_SUMMARY.productTruthLiveWriteBlocked).toBe(true);
    expect(buildFaceReadinessSummary().productTruthLiveWriteBlocked).toBe(true);
  });

  it("ProductDefinition bridge remains blocked", () => {
    expect(FACE_READINESS_SUMMARY.productDefinitionBridgeBlocked).toBe(true);
    expect(buildFaceReadinessSummary().productDefinitionBridgeBlocked).toBe(true);
  });

  it("FINISH remains blocked until FACE boundary is stable", () => {
    expect(FACE_READINESS_SUMMARY.finishWorkshopBlocked).toBe(true);
    expect(buildFaceReadinessSummary().blockedFinishEntryCount).toBeGreaterThan(0);
  });

  it("has expected truth workshop fields with statuses", () => {
    expect(FACE_TRUTH_WORKSHOP_FIELDS.length).toBeGreaterThanOrEqual(8);
    expect(getFaceTruthField("geometry_source")?.status).toBe("partial_confirmed");
    expect(getFaceTruthField("material_family_options")?.status).toBe("owner_input_required");
    expect(getFaceTruthField("material_thickness_options")?.mustNotInvent).toBe(true);
  });
});
