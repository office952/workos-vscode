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
  FINISH_READY_FOR_PRICING,
  FINISH_VARIANT_ENTRIES,
  FINISH_WORKSHOP_STATUS,
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
    expect(FINISH_READY_FOR_PRICING).toBe(false);
    expect(FINISH_WORKSHOP_STATUS).toBe("partial_confirmed");
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

  it("includes required surface variants", () => {
    expect(FINISH_VARIANT_ENTRIES.length).toBe(9);
    expect(FINISH_VARIANT_ENTRIES.every((v) => v.ownerStatus === "owner_confirmed")).toBe(true);
  });

  it("face finish quantity basis is mp_face_area owner-confirmed", () => {
    const faceBasis = FINISH_QUANTITY_BASIS_QUESTIONS.find((q) => q.questionKey === "face_finish_quantity_basis");
    expect(faceBasis?.status).toBe("owner_confirmed");
    expect(faceBasis?.proposedBasis).toBe("mp_face_area");
    expect(getFinishVariantById("face_oracal_641")?.quantityBasis).toBe("mp_face_area");
    expect(getFinishVariantById("face_oracal_641")?.quantityBasisStatus).toBe("owner_confirmed");
    const materialArea = FINISH_FACE_DEPENDENCY_INPUTS.find((d) => d.inputKey === "face_material_usage_area_m2");
    expect(materialArea?.status).toBe("evidence_only");
  });

  it("artwork finish uses mp_artwork_area when geometry exists", () => {
    const artworkBasis = FINISH_QUANTITY_BASIS_QUESTIONS.find((q) => q.questionKey === "artwork_finish_quantity_basis");
    expect(artworkBasis?.status).toBe("owner_confirmed");
    expect(getFinishVariantById("artwork_print_laminate")?.quantityBasis).toBe("mp_artwork_area");
  });

  it("variants remain activation-blocked — no registry activation", () => {
    expect(FINISH_VARIANT_ENTRIES.every((v) => v.activationStatus === "blocked")).toBe(true);
    expect(FINISH_READINESS_SUMMARY.pricingActive).toBe(false);
    expect(FINISH_READINESS_SUMMARY.pricingRegistryWrite).toBe(false);
    expect(FINISH_READINESS_SUMMARY.readyForPricing).toBe(false);
    expect(buildFinishReadinessSummary().ownerConfirmedVariantCount).toBe(9);
  });

  it("owner questions A–E are owner_confirmed after apply", () => {
    expect(FINISH_OWNER_QUESTIONS_PENDING.every((q) => q.status === "owner_confirmed")).toBe(true);
    expect(FINISH_AWAITING_OWNER_CHAT).toBe(false);
  });

  it("reaffirms boundary without cant or FACE material ownership", () => {
    expect(FINISH_BOUNDARY_REAFFIRMATION.some((b) => /RETURN-CANT|cant/i.test(b))).toBe(true);
    expect(FINISH_BOUNDARY_REAFFIRMATION.some((b) => /MAT-ACP-FATA-LITERE|FACE base/i.test(b))).toBe(true);
    expect(FINISH_BOUNDARY_REAFFIRMATION.some((b) => /100 lei/i.test(b))).toBe(true);
  });

  it("lists dangerous actions that must not appear in UI", () => {
    expect(FINISH_DANGEROUS_ACTIONS).toContain("Activate");
    expect(FINISH_DANGEROUS_ACTIONS).toContain("Write Product Truth");
  });
});
