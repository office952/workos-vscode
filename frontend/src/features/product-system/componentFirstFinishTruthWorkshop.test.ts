import { describe, expect, it } from "vitest";
import {
  buildFinishReadinessSummary,
  FINISH_AWAITING_OWNER_CHAT,
  FINISH_BOUNDARY_REAFFIRMATION,
  FINISH_COMPONENT_TEMPLATE_CODE,
  FINISH_DANGEROUS_ACTIONS,
  FINISH_DOES_NOT_OWN,
  FINISH_DOES_NOT_OWN_CANT,
  FINISH_FACE_DEPENDENCY_INPUTS,
  FINISH_IDENTITY,
  FINISH_OWNER_QUESTIONS_PENDING,
  FINISH_OWNS,
  FINISH_QUANTITY_BASIS_QUESTIONS,
  FINISH_READINESS_SUMMARY,
  FINISH_VARIANT_ENTRIES,
  getFinishVariantById,
} from "./componentFirstFinishTruthWorkshop";

describe("componentFirstFinishTruthWorkshop", () => {
  it("defines FINISH identity as readonly workshop", () => {
    expect(FINISH_COMPONENT_TEMPLATE_CODE).toBe("TPL-COMP-LETTER-FINISH_v1");
    expect(FINISH_IDENTITY.componentRole).toBe("FINISH");
    expect(FINISH_IDENTITY.offerable).toBe(false);
    expect(FINISH_IDENTITY.standaloneQuoteable).toBe(false);
    expect(FINISH_IDENTITY.workIntakeExposed).toBe(false);
    expect(FINISH_IDENTITY.pricingActive).toBe(false);
    expect(FINISH_IDENTITY.productTruthLiveWrite).toBe(false);
    expect(FINISH_IDENTITY.pricingRegistryWrite).toBe(false);
  });

  it("FINISH owns face/artwork surface application", () => {
    expect(FINISH_OWNS.some((item) => /suprafață față|față/i.test(item))).toBe(true);
    expect(FINISH_OWNS.some((item) => /artwork|Vector Logo/i.test(item))).toBe(true);
    expect(FINISH_OWNS.some((item) => /Oracal|vinyl/i.test(item))).toBe(true);
    expect(FINISH_OWNS.some((item) => /print|lamin/i.test(item))).toBe(true);
  });

  it("FINISH does not own FACE material or RETURN-CANT", () => {
    expect(FINISH_DOES_NOT_OWN.some((item) => /Plexiglas|substrat|MAT-ACP/i.test(item))).toBe(true);
    expect(FINISH_DOES_NOT_OWN.some((item) => /RETURN-CANT|cant/i.test(item))).toBe(true);
    expect(FINISH_DOES_NOT_OWN.some((item) => /100 lei.*RAL|RAL.*100/i.test(item))).toBe(true);
    expect(FINISH_DOES_NOT_OWN_CANT).toBe(true);
  });

  it("FINISH does not own pricing registry authority", () => {
    expect(FINISH_DOES_NOT_OWN.some((item) => /Pricing Registry/i.test(item))).toBe(true);
  });

  it("includes required surface variants", () => {
    const ids = FINISH_VARIANT_ENTRIES.map((v) => v.id);
    expect(ids).toContain("face_oracal_641");
    expect(ids).toContain("face_oracal_651");
    expect(ids).toContain("face_oracal_8500");
    expect(ids).toContain("face_print_laminate");
    expect(ids).toContain("artwork_print_laminate");
    expect(ids).toContain("artwork_print_only");
    expect(ids).toContain("artwork_cut_vinyl");
    expect(ids).toContain("artwork_translucent_vinyl");
    expect(ids).toContain("artwork_none_raw_plexi");
    expect(FINISH_VARIANT_ENTRIES.length).toBe(9);
  });

  it("consumes FACE outputs including mp_face_area", () => {
    expect(FINISH_FACE_DEPENDENCY_INPUTS.some((d) => d.inputKey === "mp_face_area")).toBe(true);
    expect(FINISH_FACE_DEPENDENCY_INPUTS.some((d) => d.inputKey === "face_material_usage_area_m2")).toBe(true);
    expect(FINISH_FACE_DEPENDENCY_INPUTS.some((d) => d.inputKey === "face_piece_boxes")).toBe(true);
    expect(FINISH_FACE_DEPENDENCY_INPUTS.some((d) => d.inputKey === "source_layer_role")).toBe(true);
  });

  it("quantity basis remains owner_input_required", () => {
    expect(FINISH_QUANTITY_BASIS_QUESTIONS.every((q) => q.status === "owner_input_required")).toBe(true);
    expect(getFinishVariantById("face_oracal_641")?.quantityBasisStatus).toBe("owner_input_required");
  });

  it("variants remain blocked — no registry activation", () => {
    const blocked = FINISH_VARIANT_ENTRIES.filter((v) => v.activationStatus === "blocked");
    expect(blocked.length).toBe(9);
    expect(FINISH_READINESS_SUMMARY.pricingActive).toBe(false);
    expect(FINISH_READINESS_SUMMARY.pricingRegistryWrite).toBe(false);
    expect(buildFinishReadinessSummary().blockedVariantCount).toBeGreaterThan(0);
  });

  it("all variants pending owner confirm in questions prep mode", () => {
    expect(FINISH_VARIANT_ENTRIES.every((v) => v.ownerStatus === "owner_input_required")).toBe(true);
    expect(getFinishVariantById("artwork_none_raw_plexi")?.ownerStatus).toBe("owner_input_required");
  });

  it("surfaces owner questions A–E awaiting chat", () => {
    expect(FINISH_OWNER_QUESTIONS_PENDING.map((q) => q.questionId)).toEqual(["A", "B", "C", "D", "E"]);
    expect(FINISH_OWNER_QUESTIONS_PENDING.filter((q) => q.status === "owner_input_required").length).toBeGreaterThan(
      3,
    );
    expect(FINISH_AWAITING_OWNER_CHAT).toBe(true);
  });

  it("reaffirms boundary without cant or FACE material ownership", () => {
    expect(FINISH_BOUNDARY_REAFFIRMATION.some((b) => /RETURN-CANT|cant/i.test(b))).toBe(true);
    expect(FINISH_BOUNDARY_REAFFIRMATION.some((b) => /MAT-ACP-FATA-LITERE|FACE base/i.test(b))).toBe(true);
    expect(FINISH_BOUNDARY_REAFFIRMATION.some((b) => /100 lei/i.test(b))).toBe(true);
  });

  it("lists dangerous actions that must not appear in UI", () => {
    expect(FINISH_DANGEROUS_ACTIONS).toContain("Activate");
    expect(FINISH_DANGEROUS_ACTIONS).toContain("Write Product Truth");
    expect(FINISH_DANGEROUS_ACTIONS.length).toBeGreaterThanOrEqual(5);
  });
});
